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
from dataclasses import replace

from probes import (
    ALLOWED,
    REJECTED,
    Probe,
    Report,
    check_the_statements_are_the_spikes,
    judge_probes,
    problems,
    rule_verdicts,
)

from veritas.semantic import load_semantic_layer
from veritas.validation import (
    ANALYST,
    RejectionReason,
    ValidationGate,
    canonical,
    certified_forms,
    metric_expressions,
    read,
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
        verdict=REJECTED,
        reasons=(RejectionReason.UNCERTIFIED_ROUTE,),
        why="a Dimension Definition applied to a metric — a grouping column sitting "
            "beside the metric in the projection. **This rule allows it**, and that is "
            "still what the probe is here to show: a projection with no aggregate in it "
            "is not a metric expression, so the grouping column does not have to trace. "
            "The rejection arrives from Sub-step 5.4's certified-route rule, two rules "
            "later, because the two joins that reach `dim_client` are named by no entry "
            "in `semantic/` — `by region` is a certified axis no query can reach until "
            "[5.5](../../docs/plan/step-005-validation-gate.md#55--the-gate-requires-the-access-profiles-predicate-admits-a-slice-route-and-pays-debt-020) "
            "adds the Join Paths and the `routes` field that certify them, and this "
            "verdict flips back there. `check_this_rules_verdicts` below is what says "
            "this rule allowed it",
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
        verdict=REJECTED,
        reasons=(RejectionReason.UNCERTIFIED_ROUTE,),
        why="Traded Notional's certified expression converted out of the wrong "
            "currency column. Nothing in the projection differs, so **this rule traces "
            "it and allows it** — which is "
            "[DEBT-014](../../docs/debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)'s "
            "own diagnosis, and is why the entry could not be paid by a better tracer. "
            "Sub-step 5.4's certified-route rule is what refuses it, two rules later, "
            "on the join: the statement reaches fct_fx_rate through the Trade's "
            "Denomination Currency and Traded Notional is certified through the "
            "Instrument's Quotation Currency. This declaration was `allowed` until "
            "that Sub-step, which is what made the debt a measurement rather than a "
            "memory; `route.py` prints how far apart the two numbers are",
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


class CountingWarehouse:
    """The Warehouse Adapter with a tally of how often the catalogue was read.

    Not a mock — it delegates every call to the real adapter and adds one integer. It
    exists to make
    [DEBT-019](../../docs/debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again)'s
    payment a measurement instead of a claim about how the code is written.
    """

    def __init__(self, warehouse: WarehouseAdapter) -> None:
        self.warehouse = warehouse
        self.catalogue_reads = 0

    def columns_by_table(self) -> dict[str, dict[str, str]]:
        self.catalogue_reads += 1
        return self.warehouse.columns_by_table()

    def __getattr__(self, name: str) -> object:
        return getattr(self.warehouse, name)


def check_one_judgement_reads_once(gate: ValidationGate, report: Report) -> None:
    """One judgement reads the catalogue once and resolves the statement once.

    [DEBT-019](../../docs/debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again)
    was opened in Sub-step 5.3 and paid in 5.4, and its argument was never speed:
    *"two rules judging one statement against two readings of a live catalogue can, in
    principle, disagree about what a `SELECT *` stands for — the tracing rule seeing one
    column list and the Restricted Column rule another — and a verdict assembled from
    two views of the Warehouse is a verdict about neither."* So what is checked is the
    **count**, not the milliseconds.

    Two readings, because the entry names two things that were repeated:

      * the catalogue, counted by an adapter that tallies the calls the Gate makes to it;
      * the resolution and the corpus, read off the `Reading`'s own memo after every rule
        has run. A `cached_property` puts its answer in the instance's `__dict__` the
        first time it is asked, so a key that is present after six rules is a key that
        was computed once and reused five times.

    The rules are run by hand over one `Reading` rather than through `judge`, for the one
    reason that `judge` does not hand its `Reading` back — and the point here is what
    that object holds when the rules have finished with it.
    """
    counted = CountingWarehouse(gate.warehouse)
    counting = replace(gate, warehouse=counted)  # type: ignore[arg-type]
    counting.judge(PROBES[1].sql, ANALYST)

    reading = read(
        PROBES[1].sql,
        catalogue=gate.catalogue,
        certified_expressions={
            name: metric.expression for name, metric in gate.semantic.metrics.items()
        },
    )
    ran = 0
    for _, rule in gate.rules(ANALYST):
        rule(reading)
        ran += 1
    memoised = sorted(
        key for key in ("schema", "resolved", "corpus") if key in vars(reading)
    )

    report.say(
        f"one judgement, {ran} rules: the catalogue was read "
        f"{counted.catalogue_reads} time(s), and the Reading holds one of each of "
        f"{', '.join(memoised)} (DEBT-019)"
    )
    if counted.catalogue_reads != 1:
        problems.append(
            f"one judgement read the Warehouse's catalogue {counted.catalogue_reads} "
            f"times. Once is the whole of DEBT-019's payment: rules judging one "
            f"statement against two readings of a live catalogue can disagree about "
            f"what a `SELECT *` stands for, and a verdict assembled from two views of "
            f"the Warehouse is a verdict about neither"
        )
    if memoised != ["corpus", "resolved", "schema"]:
        problems.append(
            f"after {ran} rules the Reading has memoised {memoised or 'nothing'} — a "
            f"parse-tree rule that stopped reading the shared resolution is a rule "
            f"judging a different tree from the ones beside it"
        )


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


def check_this_rules_verdicts(gate: ValidationGate, report: Report) -> None:
    """Which shapes this rule refused, and which a later rule refused after it passed
    them on.

    Three of the probes above are declared `rejected` and this rule is not what rejects
    them: `half-certified union` and `unknown table` are refused before it runs, and —
    since Sub-step 5.4 — `net revenue by region` and `notional, wrong currency` are
    refused by the certified-route rule **after** it runs and passes them on. Both of
    those two carry a `why` claiming this rule allowed the statement, and until 5.4 the
    Gate's verdict said so on its own. It no longer does, so the claim is measured here
    rather than left in prose.

    `notional, wrong currency` is the one to read: it is
    [DEBT-014](../../docs/debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)
    entire. The entry's diagnosis is that the projection is identical either way, which
    is exactly the statement *"this rule allowed it and the next one did not"* — and a
    check that only reported the Gate's rejection would have hidden the half of the
    finding that explains why the rule had to be added.
    """
    rule = ""
    for name, judged in gate.rules(ANALYST):
        if getattr(judged, "__func__", None) is ValidationGate.traces:
            rule = name
    if not rule:
        problems.append(
            "the Gate's rule list holds no entry for `traces`, so nothing above is "
            "judging the rule this module exists to check"
        )
        return
    refused, allowed, unseen = rule_verdicts(gate, PROBES, rule, ANALYST)
    later = [
        probe.name
        for probe in PROBES
        if probe.name in allowed and probe.verdict == REJECTED
    ]
    report.say(
        f"this rule ran on {len(refused) + len(allowed)} of {len(PROBES)} shapes and "
        f"refused {len(refused)}; {len(unseen)} were refused before it and "
        f"{len(later)} after it — {', '.join(later) or 'none'}"
    )
    if not allowed:
        problems.append(
            "this rule allowed none of the shapes it ran on, so nothing here separates "
            "it from a rule that refuses everything"
        )


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
    check_this_rules_verdicts(gate, report)
    report.say("")
    report.say("one probe per Certified Metric, built from semantic/metrics/:")
    judge_probes(gate, certified_probes(gate), report, ANALYST)
    report.say("")
    check_one_judgement_reads_once(gate, report)
    check_what_a_judgement_reads(gate, report)
    return report
