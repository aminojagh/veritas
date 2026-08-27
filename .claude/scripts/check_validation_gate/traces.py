"""Sub-step 5.2's rule: every metric expression traces to a Certified Metric.

The second of the five modules
[R8](../../docs/plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)
lays out, and the first that reads the corpus. It puts four things in front of the
Gate:

  * **The shapes Sub-step 3.2 measured**, re-judged through the Gate rather than
    through the spike's own tracer — table aliases, an output alias, a derived table,
    a Common Table Expression (CTE), a Dimension Definition applied to a metric, and
    the Shadow Metrics that must be refused. The spike proved a tracer could tell
    them apart; these prove the **Gate** does, reading `semantic/metrics/` rather
    than three Python literals.
  * **All nine Certified Metrics**, one probe each, built from the corpus on disk.
    The spike pinned three. A tracer that recognises three of nine metrics is a Gate
    that rejects two thirds of the questions Veritas exists to answer.
  * **The two rejections that are not Shadow Metrics** — a statement that aggregates
    nothing, and one the optimizer will not resolve. Both are reachable and both are
    their own bar on the chart.
  * **Why the corpus is canonicalised through the Gate's own reader.** `Position
    Change` traces only because of that, and the measurement below is what stops the
    reason being a sentence nobody can check.

**Every probe is judged by the whole Gate, not by the tracing rule alone**, which is
why two of the spike's shapes come back refused by an earlier rule: a `UNION` is not
a single `SELECT`, and a statement over a table the Warehouse does not have is a
statement the planner will not size. Both are declared with the reason they actually
return. Judging the rule in isolation would have hidden that, and what a caller gets
is the Gate's verdict, not the rule's.
"""

import time

from probes import (
    ALLOWED,
    REJECTED,
    Probe,
    Report,
    check_the_statements_are_the_spikes,
    judge_probes,
    problems,
)

from veritas.semantic import load_semantic_layer
from veritas.validation import (
    ANALYST,
    RejectionReason,
    ValidationGate,
    canonical,
    certified_forms,
    metric_expressions,
)
from veritas.warehouse import WarehouseAdapter

import sqlglot  # noqa: E402 — after `probes` sets sys.path, like the modules beside it
from veritas.validation import DIALECT  # noqa: E402

# The shapes Sub-step 3.2 measured, in the order that review reports them: the
# certified forms first, then the ones that must not trace, then the two the Gate
# refuses before the tracer sees them.
#
# The statements are the spike's, character for character, so that a shape whose
# verdict moves between the spike's tracer and the Gate is visible as a difference
# rather than hidden by a rewrite. What is new here is the **reason** each rejection
# comes back with, which the spike had no taxonomy to declare.
#
# That claim is **checked** rather than asserted here, by
# `probes.check_the_statements_are_the_spikes`, which reads the spike's source text.
# It was a comment in this file while `restricted.py` beside it checked the same claim
# about its own probes, and
# [R14](../../docs/plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27)
# is where either-both-or-neither was settled on both.
#
# Every statement here is a string literal inside `.claude/scripts/`, one of
# `check_warehouse.py`'s scanned roots, so the dialect scan reads each one it can
# parse. Like `read_only.py` beside it, this file passes that scan **without claiming
# an exemption**.
PROBES = (
    Probe(
        name="bare",
        sql="SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) "
            "FROM fct_trade "
            "JOIN fct_fx_rate "
            "  ON fct_fx_rate.rate_date = fct_trade.trade_date "
            " AND fct_fx_rate.from_currency = fct_trade.denomination_currency "
            " AND fct_fx_rate.to_currency = 'EUR'",
        verdict=ALLOWED,
        why="the Metric Definition's own expression, with no rewriting at all — if "
            "this does not trace, nothing else can",
    ),
    Probe(
        name="aliased",
        sql="SELECT sum(billed.commission * rate.fx_rate) AS revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=ALLOWED,
        why="table aliases and an output alias — what a generator writes by default, "
            "and what defeats matching the text",
    ),
    Probe(
        name="derived table",
        sql="SELECT sum(converted.commission * converted.fx_rate) AS revenue "
            "FROM ( "
            "  SELECT billed.commission, rate.fx_rate "
            "  FROM fct_trade AS billed "
            "  JOIN fct_fx_rate AS rate "
            "    ON rate.rate_date = billed.trade_date "
            "   AND rate.from_currency = billed.denomination_currency "
            "   AND rate.to_currency = 'EUR' "
            ") AS converted",
        verdict=ALLOWED,
        why="the conversion done in a subquery and aggregated outside it, so the "
            "certified expression is split across a boundary — merge_subqueries is "
            "the trusted rewrite that puts it back together",
    ),
    Probe(
        name="common table expression",
        sql="WITH converted AS ( "
            "  SELECT billed.commission AS commission, rate.fx_rate AS fx_rate "
            "  FROM fct_trade AS billed "
            "  JOIN fct_fx_rate AS rate "
            "    ON rate.rate_date = billed.trade_date "
            "   AND rate.from_currency = billed.denomination_currency "
            "   AND rate.to_currency = 'EUR' "
            ") "
            "SELECT sum(converted.commission * converted.fx_rate) AS revenue "
            "FROM converted",
        verdict=ALLOWED,
        why="the same split, written the way a model that has read a style guide "
            "writes it",
    ),
    Probe(
        name="net revenue",
        sql="SELECT sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=ALLOWED,
        why="a second certified expression over the same tables, so the Gate is "
            "shown to pick between metrics rather than to recognise one",
    ),
    Probe(
        name="net revenue by region",
        sql="SELECT client.client_region AS client_region, "
            "       sum((billed.commission - billed.rebate - billed.fee) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN dim_account AS account "
            "  ON account.account_id = billed.account_id "
            "JOIN dim_client AS client "
            "  ON client.client_id = account.client_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR' "
            "GROUP BY client.client_region "
            "ORDER BY client.client_region",
        verdict=ALLOWED,
        why="a Dimension Definition applied to a metric — a grouping column sitting "
            "beside the metric in the projection. It has to be allowed, and the rule "
            "that allows it is that a projection with no aggregate in it is not a "
            "metric expression",
    ),
    Probe(
        name="traded notional",
        sql="SELECT sum(CAST(billed.quantity AS DECIMAL(38, 6)) "
            "           * billed.execution_price * rate.fx_rate) AS traded_notional "
            "FROM fct_trade AS billed "
            "JOIN dim_instrument AS instrument "
            "  ON instrument.instrument_id = billed.instrument_id "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = instrument.quotation_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=ALLOWED,
        why="the widening cast survives the round trip through the optimizer, and "
            "the metric converts out of the Instrument's Quotation Currency — a "
            "different route through fct_fx_rate for the same table",
    ),
    Probe(
        name="commuted subtraction",
        sql="SELECT sum((billed.commission - billed.fee - billed.rebate) "
            "           * rate.fx_rate) AS net_revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=REJECTED,
        reasons=(RejectionReason.SHADOW_METRIC,),
        why="Net Revenue with two of its three terms swapped. The same number, a "
            "different tree, and a rejection C1 chose deliberately: the alternative "
            "is a Gate that decides for itself which rewrites preserve meaning",
    ),
    Probe(
        name="commuted multiplication",
        sql="SELECT sum(rate.fx_rate * billed.commission) AS revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=REJECTED,
        reasons=(RejectionReason.SHADOW_METRIC,),
        why="Gross Revenue with its two factors written the other way round — the "
            "smallest edit that stops a certified expression being recognised, and "
            "the cheapest illustration of what C1's pasteable form buys",
    ),
    Probe(
        name="open-coded net revenue",
        sql="SELECT sum(billed.commission * rate.fx_rate) "
            "     - sum(billed.rebate * rate.fx_rate) "
            "     - sum(billed.fee * rate.fx_rate) AS revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=REJECTED,
        reasons=(RejectionReason.SHADOW_METRIC,),
        why="the Shadow Metric the Glossary defines: Net Revenue's number built "
            "inline out of three separate sums instead of drawn from the Semantic "
            "Layer. The right answer, computed the way Veritas exists to prevent",
    ),
    Probe(
        name="unconverted commission",
        sql="SELECT sum(billed.commission) AS revenue FROM fct_trade AS billed",
        verdict=REJECTED,
        reasons=(RejectionReason.SHADOW_METRIC,),
        why="revenue computed inline from commission with the conversion left out — "
            "a Section C pair arriving as a query rather than as a mistake in a "
            "build script",
    ),
    Probe(
        name="rebate silently dropped",
        sql="SELECT sum((billed.commission - billed.fee) * rate.fx_rate) AS revenue "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=REJECTED,
        reasons=(RejectionReason.SHADOW_METRIC,),
        why="the near miss: Net Revenue's shape with one of its three terms missing. "
            "Neither Gross nor Net, and a number that answers no question at all",
    ),
    Probe(
        name="notional, wrong currency",
        sql="SELECT sum(CAST(billed.quantity AS DECIMAL(38, 6)) "
            "           * billed.execution_price * rate.fx_rate) AS traded_notional "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=ALLOWED,
        why="Traded Notional's certified expression converted out of the wrong "
            "currency column. Nothing in the projection differs, so it traces and "
            "the Gate allows it — this is "
            "[DEBT-014](../../docs/debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject) "
            "standing open, and its verdict flips to rejected in Sub-step 5.4. A "
            "probe declaring `allowed` is what makes the debt a measurement instead "
            "of a memory",
    ),
    Probe(
        name="certified beside shadow",
        sql="SELECT sum(billed.commission * rate.fx_rate) AS revenue, "
            "       sum(billed.rebate) AS rebates "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=REJECTED,
        reasons=(RejectionReason.SHADOW_METRIC,),
        why="Gross Revenue and an inline sum of rebates, side by side in one "
            "projection. **This is the probe for the word *every*.** Written as "
            "*some*, the rule would allow this on the strength of the certified "
            "half and hand back an answer with an uncertified column in it. The "
            "spike's demonstration of the same hole was the half-certified union, "
            "which the Gate now refuses one rule earlier — so without this probe "
            "the strictness of that word would go unmeasured here",
    ),
    Probe(
        name="half-certified union",
        sql="SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) AS revenue "
            "FROM fct_trade "
            "JOIN fct_fx_rate "
            "  ON fct_fx_rate.rate_date = fct_trade.trade_date "
            " AND fct_fx_rate.from_currency = fct_trade.denomination_currency "
            " AND fct_fx_rate.to_currency = 'EUR' "
            "UNION ALL "
            "SELECT sum(fct_trade.commission) AS revenue FROM fct_trade",
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_READ,),
        why="a certified branch and a Shadow Metric branch in one statement. The "
            "spike's tracer had to read every scope to catch it; the Gate never gets "
            "that far, because a UNION is not a single SELECT — the refusal "
            "[R12](../../docs/plan/step-005-validation-gate.md#r12--aminos-rulings-on-the-51-review--decided-2026-08-26) "
            "confirmed as deliberate. The tracer still reads every scope, and the "
            "spike is where that stays measured",
    ),
    Probe(
        name="unknown table",
        sql="SELECT sum(ledger.commission) AS revenue "
            "FROM fct_revenue_ledger AS ledger",
        verdict=REJECTED,
        reasons=(RejectionReason.UNBOUNDED_SCAN,),
        why="a table no schema knows. sqlglot resolves it without objecting, so the "
            "spike could measure the expression failing to match; the Gate refuses "
            "it one rule earlier, because a planner asked to size a statement over a "
            "table that is not there will not answer. That is the honest verdict the "
            "bounded-read rule can reach, and it is the behaviour `gate.py` declared "
            "in Sub-step 5.1",
    ),
    Probe(
        name="no metric expression",
        sql="SELECT fct_trade.trade_id, fct_trade.commission FROM fct_trade",
        verdict=REJECTED,
        reasons=(RejectionReason.NO_METRIC_EXPRESSION,),
        why="a statement that projects columns and aggregates nothing. *Every metric "
            "expression traces* is trivially true of a statement holding none, so "
            "without its own reason this would be a vacuous pass — half of what the "
            "spike achieved by accident",
    ),
    Probe(
        name="unresolvable",
        sql="SELECT [x * 2 FOR x IN [1, 2, 3]] AS doubled",
        verdict=REJECTED,
        reasons=(RejectionReason.UNRESOLVABLE,),
        why="a DuckDB list comprehension: the engine plans it happily and sqlglot's "
            "optimizer will not resolve the name the comprehension binds. Proof that "
            "'parses' and 'resolves' are two different things a Gate must not "
            "confuse, and that the second is reachable rather than defensive",
    ),
)


def certified_probes(gate: ValidationGate) -> tuple[Probe, ...]:
    """One probe per Certified Metric, built from the corpus on disk.

    The spike pinned three expressions and measured those. Nine are certified, and a
    Gate that recognises three of them rejects two thirds of the questions Veritas
    exists to answer — so each metric is asked, in the simplest statement that
    computes it: its own expression over its own `from_table`, joined along its own
    Join Paths, with its own certified filters.

    That statement is built from the Metric Definition's fields rather than written
    out here, which is what makes this nine probes and not nine more literals to keep
    in step with `semantic/`. A tenth Metric Definition is a tenth probe with no edit
    to this file.
    """
    layer = gate.semantic
    built = []
    for name, metric in sorted(layer.metrics.items()):
        route = " ".join(
            f"JOIN {layer.join_paths[join_path].to_table} "
            f"ON {layer.join_paths[join_path].on}"
            for join_path in metric.join_paths
        )
        where = " WHERE " + " AND ".join(metric.filters) if metric.filters else ""
        built.append(
            Probe(
                name=name,
                sql=f"SELECT {metric.expression} AS answer "
                    f"FROM {metric.from_table} {route}{where}",
                verdict=ALLOWED,
                why=f"{name} is certified, so the statement that computes it the way "
                    f"its own Metric Definition says has to be allowed",
            )
        )
    return tuple(built)


def check_the_corpus_is_the_one_on_disk(gate: ValidationGate, report: Report) -> None:
    """Print what the Gate traces to, and where it read it.

    The corpus is the finding as much as the verdicts are: which expressions count as
    certified is the whole content of *"every metric expression traces to a Certified
    Metric"*. The spike prints its three pinned literals; this prints what the loader
    returned, so the two can be read side by side and the difference between them is
    visible rather than assumed.
    """
    schema = gate.warehouse.columns_by_table()
    corpus = certified_forms(
        {name: metric.expression for name, metric in gate.semantic.metrics.items()},
        schema,
    )
    report.say(
        f"corpus: {len(corpus)} Certified Metrics, read from semantic/metrics/ "
        f"through veritas.semantic.loader — not Python literals (R2)"
    )
    if len(corpus) != len(gate.semantic.metrics):
        problems.append(
            f"the corpus holds {len(gate.semantic.metrics)} Certified Metrics and "
            f"canonicalises to {len(corpus)} forms — two metrics sharing one form "
            f"means a statement traces to whichever the dict kept, and the Gate "
            f"would report a metric the question never asked for"
        )


def check_symmetric_canonicalisation_is_load_bearing(
    gate: ValidationGate, report: Report
) -> None:
    """Measure how many Certified Metrics need the corpus read the Gate's way.

    `certified_form` resolves a certified expression through the same `resolve` a
    statement goes through, rather than parsing it on its own. The reason is a
    finding: `qualify` gives the projection of a nested `SELECT` an output alias, so a
    corpus canonicalised by parsing alone differs from the statement computing it by
    one `AS "quantity"` — and `Position Change`, the one expression shape the spike
    never measured, traces to nothing.

    This runs the rejected alternative and prints which metrics it loses. It fails the
    run when it loses none, because at that point the paragraph above has stopped
    being true and a comment nothing checks is how a reason quietly becomes wrong.
    """
    schema = gate.warehouse.columns_by_table()
    expressions = {
        name: metric.expression for name, metric in gate.semantic.metrics.items()
    }
    symmetric = certified_forms(expressions, schema)
    # The alternative: canonicalise the corpus by parsing each expression on its own,
    # which is what `check_validation_feasibility.py` did while every expression it
    # held was flat arithmetic.
    parsed_alone = {
        canonical(sqlglot.parse_one(expression, dialect=DIALECT)): name
        for name, expression in expressions.items()
    }
    # Keyed by **form**, not by name: both corpora hold all nine names, and the whole
    # question is whether the form a statement resolves to is a key the corpus holds.
    lost = sorted(
        name for form, name in symmetric.items() if form not in parsed_alone
    )
    report.say(
        f"corpus canonicalised through the Gate's own reader: "
        f"{len(lost)} of {len(expressions)} Certified Metrics would not trace if it "
        f"were parsed alone{' — ' + ', '.join(lost) if lost else ''}"
    )
    if not lost:
        problems.append(
            "no Certified Metric depends on the corpus being canonicalised through "
            "`resolve`, so `certified_form`'s docstring is claiming a reason that no "
            "longer applies — either an expression changed or the rewrites did, and "
            "the explanation has to move with them"
        )


def fastest(work, runs: int = 15) -> float:
    """Milliseconds for the quickest of `runs` calls, after one to warm up.

    The **minimum** rather than the mean, which is the honest summary of a short
    timing: every source of noise here — the scheduler, another process, a cold cache
    — can only make a run slower, so the mean of a handful of runs reports the
    machine's mood and the minimum reports the work. Averaging produced a report in
    which the corpus rebuild looked slower than the whole judgement containing it.
    """
    work()
    best = float("inf")
    for _ in range(runs):
        started = time.perf_counter()
        work()
        best = min(best, time.perf_counter() - started)
    return best * 1000


def per_table_schema(warehouse: WarehouseAdapter) -> dict[str, dict[str, str]]:
    """The catalogue read one query per table — the shape `columns_by_table` replaced.

    Kept so the two can be compared rather than argued about, and for nothing else.
    """
    return {table: dict(warehouse.columns(table)) for table in warehouse.tables()}


def check_what_a_judgement_reads(gate: ValidationGate, report: Report) -> None:
    """What one judgement costs, and where it goes.

    A measurement, not a rule: the figures move with the machine and nothing here
    fails the run for being slow. It is printed because `ValidationGate`'s docstring
    argues the corpus is rebuilt on every judgement for correctness, and an argument
    for paying a cost should say what the cost is.

    The catalogue is timed both ways for the same reason. `columns_by_table` reads
    every table's columns in one query where the obvious shape is one query per table,
    and the Gate reads it on **every** judgement — so the difference between the two
    is on the hot path, and printing it is what stops the one-query shape being
    quietly undone as a tidy-up. That the two return the same mapping **is** checked:
    a faster catalogue that says something different is not the same catalogue.
    """
    schema = gate.warehouse.columns_by_table()
    expressions = {
        name: metric.expression for name, metric in gate.semantic.metrics.items()
    }
    statement = PROBES[1].sql

    report.say(
        f"one judgement, fastest of 15: "
        f"schema {fastest(gate.warehouse.columns_by_table):.0f} ms · "
        f"corpus {fastest(lambda: certified_forms(expressions, schema)):.0f} ms · "
        f"statement {fastest(lambda: metric_expressions(statement, schema)):.0f} ms · "
        f"whole Gate {fastest(lambda: gate.judge(statement, ANALYST)):.0f} ms"
    )
    same = per_table_schema(gate.warehouse) == schema
    report.say(
        f"the catalogue in one query against one query per table: "
        f"{fastest(gate.warehouse.columns_by_table):.0f} ms against "
        f"{fastest(lambda: per_table_schema(gate.warehouse)):.0f} ms, "
        f"same mapping: {same}"
    )
    if not same:
        problems.append(
            "`columns_by_table` and a per-table read of the same catalogue disagree, "
            "so the one-query shape is not the mapping `tables()` and `columns()` "
            "would have built and the Gate is qualified against something else"
        )


# The spike's claim-1 statements this module deliberately does not judge, and where the
# shape is covered instead. Declared rather than skipped silently: a shape that leaves
# this list without leaving the spike is coverage lost, and the check fails on it.
COVERED_ELSEWHERE = {
    "unparseable": "the Gate refuses it at `parses`, three rules earlier, and "
                   "`read_only.py` measures that shape with a statement of its own",
}


def check(warehouse: WarehouseAdapter) -> Report:
    """Everything this module has to say, in one report."""
    report = Report("every metric expression traces to a Certified Metric")
    gate = ValidationGate(warehouse, semantic=load_semantic_layer())
    check_the_statements_are_the_spikes(
        PROBES,
        constant="PROBES",
        label="claim-1",
        added_by="Sub-step 5.2",
        covered_elsewhere=COVERED_ELSEWHERE,
        report=report,
    )
    check_the_corpus_is_the_one_on_disk(gate, report)
    check_symmetric_canonicalisation_is_load_bearing(gate, report)
    judge_probes(gate, PROBES, report, ANALYST)
    report.say("")
    report.say("one probe per Certified Metric, built from semantic/metrics/:")
    judge_probes(gate, certified_probes(gate), report, ANALYST)
    report.say("")
    check_what_a_judgement_reads(gate, report)
    return report
