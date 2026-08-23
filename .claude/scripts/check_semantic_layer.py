"""Check the Semantic Layer against the Warehouse its expressions compute over.

Run with:  uv run python .claude/scripts/check_semantic_layer.py

Needs a filled Warehouse — `uv run python -m veritas.ingestion` first — because a
published expression that has never been executed is a claim rather than a metric.

A corpus cannot be proved by running it, only by running what it claims. Eleven
checks do that. Five are the ones
[Sub-step 4.1](../docs/plan/step-004-semantic-layer.md#41--publish-the-semantic-entry-format-on-one-metric-definition)
names; the sixth is Non-Negotiable #1 applied to the one place this corpus can coin
a domain noun by accident. Checks 7 to 11 arrived with
[Sub-step 4.2](../docs/plan/step-004-semantic-layer.md#42--write-the-remaining-metric-definitions),
which is where the corpus stopped being one entry: two are that Sub-step's own
bullets, two are what the shape
[R8](../docs/plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)
decided has to be checked for, and the eleventh is what keeps a claim in that ruling
reproducible.

  1. Every file under `semantic/` loads, and every field the format names is
     present. The loader is what enforces this — its dataclasses *are* the field
     list, so there is no second copy to drift — and this script's job is to turn a
     refusal into a named problem instead of a traceback.

  2. Every Metric Definition's `name` is a Glossary Section B term whose *Lives in*
     cell says `semantic/metrics/`. Read out of the Glossary rather than listed
     here, for the reason `check_warehouse.py` derives its table set the same way: a
     list typed here would only prove that two files agree with each other. This is
     the check that mechanises
     [R1](../docs/plan/step-004-semantic-layer.md#r1--cash-balance-becomes-a-certified-metric--approved-by-amino-2026-08-21),
     which was found by hand — `Cash Balance` is a Certified Metric whose registered
     home was a Warehouse table, so writing its Metric Definition fails this check
     until the Glossary row is amended.

  3. The published expression is **pasted verbatim** into a query built from the
     entry's own route, certified filters and date column, executed through the
     Warehouse Adapter, and returns a number. Pasted rather than rebuilt: a check that re-derives the
     expression proves the rebuild, not the file
     ([C1](../docs/design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)).
     The date column is what makes this more than "the SQL runs": the same metric is
     asked twice more with a period filter on it, either side of one date, and the
     two halves must add up to the whole.

  4. That number equals the one `check_warehouse.py` computes for itself, in SQL
     that never reads `semantic/`
     ([R2](../docs/plan/step-004-semantic-layer.md#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21)).
     **Twice**: once over the whole Warehouse, which checks the arithmetic, and once
     over one period, which checks the date predicate — the two are separate
     mistakes and the second is invisible to a check that only ever asks for a
     total. A metric with no independent counterpart figure gets the weaker claim —
     *it executes and returns a number* — and is printed as such rather than sharing
     a word with the metrics that were actually compared.

  5. The declared Reporting Currency appears in one of the Join Paths the entry
     names, as a string literal in the join condition's parse tree. It is written in
     two places on purpose: C1 forbids a template the loader fills in, so the
     currency is inside the Join Path text where a reviewer reads it, and this check
     is what makes the duplication safe. The rule runs the other way too — a metric
     whose unit is not money must state no currency at all.

  6. An expression that does not parse **fails the run**, rather than being skipped —
     [C6](../docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)'s
     echo in a Step that builds no Gate. Two probes give the rule teeth on every
     run, because a rule that has only ever seen valid input reads the same whether
     it works or does nothing, and they run against a composed metric as well as a
     plain one because a composition is a second reader path.

  7. Every [Glossary Section C](../docs/glossary.md#c-distinctions-we-must-not-blur)
     pair whose both sides are Certified Metrics returns **two different numbers from
     the published expressions**. `check_warehouse.py --distinctions` proves the data
     separates them; this proves the Semantic Layer does, which is a different claim.

  8. A metric's route is a route: every Join Path it names exists, starts at a table
     the route has already reached, arrives somewhere new, and has a condition that
     never reaches forward to a table nobody joined.

  9. The three expressions the Sub-step 3.2 spike measured are **exactly** what
     `semantic/metrics/` publishes, which is
     [R4](../docs/plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)'s
     pin: the spike stays pointed at its own literals so its dated verdict keeps its
     inputs, and this assertion is what stops that verdict quietly becoming about
     expressions the project no longer uses.

 10. A metric that derives from another adds up metrics that exist, are not itself,
     do not derive further, and carry the same unit and currency.

 11. Every widening cast in the corpus is load-bearing, shown by executing the
     expression without it and expecting the engine to refuse. A cast nobody can see
     the need for is a cast somebody eventually removes.

Exits non-zero if any check fails.
"""

import re
import sys
from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import sqlglot
from sqlglot import exp

CLAUDE_DIR = Path(__file__).resolve().parent.parent  # <repo>/.claude
REPO_ROOT = CLAUDE_DIR.parent                        # <repo>
GLOSSARY = CLAUDE_DIR / "docs" / "glossary.md"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CLAUDE_DIR / "scripts"))

from veritas.semantic import (  # noqa: E402
    MetricDefinition,
    SemanticEntryError,
    SemanticLayer,
    load_semantic_layer,
)
from veritas.warehouse import DATABASE_PATH, WarehouseAdapter  # noqa: E402
# E402 is "module-level import not at top of file". Both imports have to come after
# the sys.path lines above, or the script cannot find the package when run from
# anywhere. The comment marks those specific lines as deliberate and suppresses
# nothing else — the same note `check_validation_feasibility.py` carries.

from check_warehouse import (  # noqa: E402
    METRIC_HOME,
    REPORTING_CURRENCY,
    account_value,
    cash_balance,
    gross_revenue,
    net_revenue,
    position_change,
    realised_pnl,
    trade_count,
    traded_notional,
    unrealised_pnl,
)
# The other half of check 4. Every figure is imported rather than reimplemented
# for the reason the spike imports `unportable_functions`: a second copy would
# answer the question about the copy, and would go on answering it after the
# original changed. What must not happen is the arrow pointing the other way —
# `check_warehouse.py` reading `semantic/` would make both sides compute the same
# wrong number and agree, which is R2's whole subject.

from check_validation_feasibility import CERTIFIED_EXPRESSIONS  # noqa: E402
# The three expressions the Sub-step 3.2 spike measured, as Python literals. Check 9
# pins them to the corpus rather than re-pointing the spike at it, which is
# [R4](../docs/plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21).

# Every Certified Metric and the function that produces its second, independently
# written figure. Sub-step 4.2 filled this table out to all nine: a metric absent
# from here would still have to execute and return a number, but nothing would be
# checking that the number is the right one, and check 4 says which it got rather
# than letting one word cover both.
INDEPENDENT_FIGURES = {
    "Gross Revenue": gross_revenue,
    "Net Revenue": net_revenue,
    "Traded Notional": traded_notional,
    "Trade Count": trade_count,
    "Cash Balance": cash_balance,
    "Account Value": account_value,
    "Unrealised P&L": unrealised_pnl,
    "Realised P&L": realised_pnl,
    "Position Change": position_change,
}

# The `unit` value that makes a metric monetary, and therefore the one value that
# obliges it to state a Reporting Currency — registered as something *"every
# monetary metric must state"*. `count` and `quantity` are the other two in the
# corpus and neither has a currency to state.
MONEY = "money"

# The Glossary Section C pairs whose **both** sides are Certified Metrics, with the
# Glossary's own words for why each matters. `check_warehouse.py --distinctions`
# proves the *data* separates these; check 7 proves the published expressions do,
# which is a different claim and the one that matters for a corpus whose whole
# purpose is keeping them apart.
#
# The other Section C rows are absent because they are not pairs of metrics: Trade
# Date against Settlement Date is one metric under two date predicates, Client
# against Account is a grouping, and the rest are columns.
SECTION_C_PAIRS = (
    ("Gross Revenue", "Net Revenue",
     "reporting gross as net overstates what the business keeps"),
    ("Cash Balance", "Account Value",
     "a Client with no cash and equities has a Cash Balance of zero"),
    ("Realised P&L", "Unrealised P&L",
     "one is banked, one is a market opinion"),
    ("Traded Notional", "Trade Count",
     "one large trade and a thousand small ones are opposite answers"),
)

# How far apart two sides of a Section C pair must be before "a different number"
# means anything to a reader. The same value as `check_warehouse.py`'s
# MIN_DISTINCTION_GAP and deliberately not the same rule — that one is the floor
# for the loaded data separating a pair, this one is the floor for the published
# expressions separating it. They are free to move apart, and neither reads the
# other. It applies only where both sides carry the same unit: a money figure and
# a count are different numbers by construction, and a percentage between them
# would be arithmetic with no meaning.
MIN_DISTINCTION_GAP = Decimal("0.005")

# The engine the queries are read in. The same one they are executed in, because a
# statement checked in one dialect and run in another is two statements.
DIALECT = "duckdb"

# The cell position the "Lives in" column sits at once a leading pipe has made
# cells[0] the empty string. `METRIC_HOME` — where Section B says a Certified Metric
# lives — is imported above rather than spelled again, because two readers of one
# Glossary column agreeing by coincidence is how they stop agreeing.
LIVES_IN_COLUMN = 3

# The two halves the period split asks for. SQL operators rather than anything read
# out of an entry: the date *column* comes from the Metric Definition, and how it is
# compared is this file's own.
BEFORE = "<"
FROM_THEN = ">="

# The widening cast four published expressions carry, and the pattern that takes it
# back out again. Check 11 executes the uncast expression and expects the engine to
# refuse it, which is what keeps the cast a **measurement** rather than a habit: a
# reader who thinks it is tidiness can see, on every run, what removing it costs.
# The same shape `check_validation_feasibility.py` uses for `Traded Notional`, which
# is the one metric DEBT-015 predicted and the only one it named.
WIDENING_CAST = re.compile(r"CAST\((.+?) AS DECIMAL\(38, 6\)\)")

# The teeth of check 6, run on every run against expressions written here rather
# than against whatever the corpus happens to contain. Each is pasted into the real
# Gross Revenue entry and assembled by the same function the corpus goes through, so
# what is probed is the code path rather than a copy of it. Without them a clean run
# reads the same either way — whether the rule refuses unparseable SQL or whether it
# never looked.
PARSE_PROBES = (
    ("an unclosed call", "sum(fct_trade.commission", False),
    ("nothing at all", "", False),
)

problems: list[str] = []


def certified_metric_terms() -> set[str]:
    """The Glossary Section B terms whose *Lives in* cell names `semantic/metrics/`.

    Section B is *"what the data describes"*, and every Certified Metric is a
    quantity over that data — so a Metric Definition whose name is not one of these
    rows is either a term nobody registered or a term registered as living somewhere
    else. Section A also has rows pointing at `semantic/metrics/` — `Reporting
    Currency`, `Metric Definition` itself — which is why this reads one section
    rather than the file: they are not metrics, and accepting them as metric names
    would widen the check into meaninglessness.

    Both directions are checked, by `check_entries` below. Sub-step 4.1 could only
    check one — the other would have failed on the eight metrics 4.2 was for — and
    4.2 is the Sub-step whose own bar is that *every* Section B metric has a Metric
    Definition that returns a number.
    """
    text = GLOSSARY.read_text()
    section = re.search(r"^### B\. The warehouse\n(.*?)^### ", text, re.S | re.M)
    if not section:
        problems.append(
            "glossary.md: could not find the `### B. The warehouse` section, so "
            "nothing here knows which names are certified"
        )
        return set()

    terms: set[str] = set()
    for line in section.group(1).splitlines():
        cells = line.split("|")
        if len(cells) <= LIVES_IN_COLUMN or METRIC_HOME not in cells[LIVES_IN_COLUMN]:
            continue
        terms.add(cells[1].strip().strip("*").strip())
    return terms


def source(metric: MetricDefinition, layer: SemanticLayer) -> str:
    """The `FROM ... JOIN ... ON ...` a metric's route certifies, as written.

    The route starts at the table the entry names and joins each Join Path in the
    order the entry lists them. `Trade Count` lists none, so its route is one table
    and no join at all — which is why a Metric Definition carries `from_table`
    rather than reading the first table off its first Join Path.
    """
    sql = f"FROM {metric.from_table}"
    for name in metric.join_paths:
        join = layer.join_paths[name]
        sql += f" JOIN {join.to_table} ON {join.on}"
    return sql


def query_parts(
    metric: MetricDefinition, layer: SemanticLayer, comparison: str | None = None
) -> list[str]:
    """One statement per part of a metric — its own, then each it derives from.

    A metric that derives from nothing has one part and that part is the whole
    query. `Account Value` has two, because *"Cash Balance plus all Positions
    marked to market"* is rooted at two Snapshot tables that join on nothing
    without multiplying rows.

    **The period filter is applied to every part**, which is the reason the
    composition happens here rather than inside an expression. A scalar subquery
    written into `Account Value`'s own expression would not be reached by a `WHERE`
    on the outer query, so each half of a date range would carry the whole of the
    marked Positions and the two halves would add up to more than the total.
    """
    parts = []
    for part in [metric, *(layer.metrics[name] for name in metric.derives_from)]:
        predicates = list(part.filters)
        if comparison:
            predicates.append(f"{part.date_column} {comparison} ?")
        where = f" WHERE {' AND '.join(predicates)}" if predicates else ""
        parts.append(f"SELECT {part.expression} {source(part, layer)}{where}")
    return parts


def executable_query(
    metric: MetricDefinition, layer: SemanticLayer, comparison: str | None = None
) -> str:
    """One Metric Definition, as the statement that computes it.

    The expression goes in **verbatim**. Everything around it comes from the entry's
    own fields — the table it starts at, the Join Paths it names, the certified
    predicates it carries and, when a half is asked for, the date column a period
    filter keys on, compared against a bound parameter.

    What this assembles for `Gross Revenue` is the shape the Sub-step 3.2 spike's
    `bare` probe writes out by hand — the spike had to, because no Semantic Layer
    existed yet to publish one. That the two are still the same *text* is check 9.
    """
    parts = query_parts(metric, layer, comparison)
    if len(parts) == 1:
        return parts[0]
    return "SELECT " + " + ".join(f"({part})" for part in parts)


def bindings(metric: MetricDefinition) -> int:
    """How many bound parameters a period-filtered query for this metric takes.

    One per part, because every part carries its own `WHERE`.
    """
    return 1 + len(metric.derives_from)


def tables_named_in(condition: str) -> set[str]:
    """Every table a join condition qualifies a column with.

    A Join Path is a route between two tables and its condition may still name a
    third: the rate that converts a Traded Notional is keyed on the Instrument's
    Quotation Currency and on the *Trade's* date. That is legal SQL in a route
    that has already joined the Trade, and nonsense in one that has not, which is
    the difference `check_route` below exists to enforce.
    """
    parsed = sqlglot.parse_one(condition, dialect=DIALECT)
    return {column.table for column in parsed.find_all(exp.Column) if column.table}


def units(metric: MetricDefinition) -> str:
    """What a figure from this metric is denominated in, for printing beside it.

    The Reporting Currency where there is one, the `unit` where there is not: a
    count of Trades reads as `1,670 count` rather than as `1,670 EUR`, and the
    metrics that have no currency are exactly the ones where saying so matters.
    """
    return metric.reporting_currency or metric.unit


def route_as_read(metric: MetricDefinition, layer: SemanticLayer) -> str:
    """A metric's route as a reader would follow it, table to table.

    Printed rather than the Join Path names alone, because the names are the
    corpus's vocabulary and the tables are what a reviewer checks against the
    Glossary Section B row. A route with no joins prints its one table and says so.
    """
    tables = [metric.from_table]
    for name in metric.join_paths:
        tables.append(layer.join_paths[name].to_table)
    route = " → ".join(tables)
    if not metric.join_paths:
        return f"{route} — no join"
    return f"{route}  ({', '.join(metric.join_paths)})"


def every_part_reads_as_a_query(
    metric: MetricDefinition, layer: SemanticLayer
) -> bool:
    """Whether every part of a composed metric parses, not just the sum of them.

    The distinction is the whole of C6 for a composed metric. `SELECT (SELECT )
    + (SELECT sum(...) ...)` has a projection — the addition — so a rule that read
    only the assembled statement would find one and pass a query with an empty
    metric inside it. Each part is judged on its own.
    """
    return all(
        reads_as_a_query(part) for part in query_parts(metric, layer)
    )


def reads_as_a_query(sql: str) -> bool:
    """Whether sqlglot reads `sql` as a SELECT with something to select.

    Fails closed by a rule rather than by accident, which is exactly C6's
    complaint about the spike: *"a statement it cannot parse is refused ... the
    right outcome for the wrong reason"*. Here the refusal is the return value, and
    both of its branches are probed on every run.

    **The projection clause is not tidiness, and the probe below is what found
    that.** sqlglot reads `SELECT  FROM fct_trade JOIN ...` — an entry whose
    `expression` is the empty string — as a perfectly good `Select` carrying no
    projections at all. A rule that stopped at the type would have passed it on to
    the engine, which is the failure this function is named after wearing the
    opposite face: not a parse failure treated as a pass, but a pass with nothing
    in it.
    """
    try:
        parsed = sqlglot.parse_one(sql, dialect=DIALECT)
    except sqlglot.errors.SqlglotError:
        return False
    return isinstance(parsed, exp.Select) and bool(parsed.expressions)


def rows_from(
    warehouse: WarehouseAdapter, sql: str, parameters: list[object] | None = None
) -> list[tuple[object, ...]] | None:
    """Execute a query, or report the engine's refusal and carry on to the next one.

    Executing a published expression against the live schema is what gives
    [EXT-002](../docs/extension-register.md#ext-002--semantic-layer-drift-detection)'s
    purpose for free — a renamed column throws — and the throw is the finding. It is
    caught so that one broken entry names itself and the rest of the corpus still
    runs, rather than the first failure hiding the other eight.

    `Exception` is caught rather than the engine's own error class because this
    script may not name it: ADR-0002 puts the dialect inside the Warehouse Adapter,
    and an engine's exception types are part of its dialect. That is a real
    imprecision, on the Ledger as
    [DEBT-016](../docs/debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type),
    and it is kept to the two lines that actually execute SQL.
    """
    try:
        return warehouse.query(sql, parameters)
    except Exception as refusal:  # noqa: BLE001 — see DEBT-016 above
        problems.append(
            f"the engine refused the query below — {type(refusal).__name__}: "
            f"{refusal}\n      {sql}"
        )
        return None


def one_number(
    warehouse: WarehouseAdapter, sql: str, parameters: list[object] | None = None
) -> Decimal | int | None:
    """Execute a metric's query and return the single number it must come back as.

    Anything else — no rows, more than one column, a null, a value of a type that is
    not a number — is a problem rather than something to coerce. A float would be
    caught here too, and would be a finding in its own right: ADR-0002 rejected
    floating point for monetary aggregation, and the star schema holds no float
    column for one to come from.
    """
    rows = rows_from(warehouse, sql, parameters)
    if rows is None:
        return None
    match rows:
        case [(Decimal() | int() as value,)]:
            return value
        case _:
            problems.append(
                f"the query below did not come back as one number — it returned "
                f"{rows!r}\n      {sql}"
            )
            return None


def check_entries(layer: SemanticLayer) -> None:
    """Checks 2, 5, 8 and 10 — everything decidable without executing anything."""
    certified = certified_metric_terms()
    print(f"  Glossary Section B names {len(certified)} terms living in "
          f"{METRIC_HOME}")

    # Both directions, where Sub-step 4.1 could only check one. The bar Sub-step
    # 4.2 sets for itself is that *every* Section B metric has a Metric Definition
    # — the same bar Step 002 set for the Warehouse's ten tables — so an
    # unwritten metric has to fail the run rather than be noticed by a reader.
    unwritten = sorted(certified - set(layer.metrics))
    if unwritten:
        problems.append(
            f"Glossary Section B registers {unwritten} as living in {METRIC_HOME} "
            f"and no file there publishes them — a Certified Metric with no Metric "
            f"Definition is a name Retrieval can match and nothing can compute"
        )

    for metric in layer.metrics.values():
        if metric.name not in certified:
            problems.append(
                f"Metric Definition {metric.name!r} is not a Glossary Section B term "
                f"whose 'Lives in' cell says {METRIC_HOME} — register the term, or "
                f"amend its row, before certifying a computation under that name"
            )
        broken_route = route_problem(metric, layer)
        if broken_route:
            problems.append(broken_route)
        else:
            check_reporting_currency(metric, layer)
        check_derivation(metric, layer)


def route_problem(metric: MetricDefinition, layer: SemanticLayer) -> str | None:
    """Check 8 — a metric's route is a route: it starts somewhere and stays joined.

    Three ways a list of Join Paths can be incoherent, and all three produce SQL
    the engine would refuse or, worse, answer wrongly:

      * a named Join Path no file publishes, so the route is one the corpus does
        not certify;
      * a Join Path that starts at a table the route has not reached yet, which is
        a join to nothing;
      * a Join Path whose condition names a table the route has not reached, which
        is the same fault one level down — and the reason this is checked at all is
        that a legitimate Join Path *does* name a third table:
        `instrument_to_fx_rate_on_quotation_currency` keys the rate on
        `fct_trade`'s date.

    **Returns the problem rather than reporting it**, and `check_entries` is the one
    caller that reports. Everything else downstream — the execution, the period
    split, the parse probes — has to know whether a metric assembles at all, and a
    predicate that appended as it answered would report one broken route once per
    caller. That is not hypothetical: it is what the mutation for this check
    produced before this function was split in two.
    """
    joined = [metric.from_table]
    for name in metric.join_paths:
        join = layer.join_paths.get(name)
        if join is None:
            return (
                f"Metric Definition {metric.name!r} names Join Path {name!r}, which "
                f"no file under semantic/joins/ publishes — so the route the "
                f"expression is computed over is one the corpus does not certify"
            )
        if join.from_table not in joined:
            return (
                f"Metric Definition {metric.name!r} joins {name!r}, which starts at "
                f"{join.from_table!r}, but its route has only reached {joined} — a "
                f"Join Path can only extend a route that has already arrived at the "
                f"table it starts from"
            )
        if join.to_table in joined:
            return (
                f"Metric Definition {metric.name!r} joins {name!r}, which arrives at "
                f"{join.to_table!r} — already in the route. A table joined twice "
                f"under one name makes every column that names it ambiguous"
            )
        reachable = [*joined, join.to_table]
        unreached = sorted(tables_named_in(join.on) - set(reachable))
        if unreached:
            return (
                f"Metric Definition {metric.name!r} joins {name!r}, whose condition "
                f"names {unreached} — tables its route has not joined. A join "
                f"condition may reach back to a table already in the route and "
                f"never forward to one that is not"
            )
        joined = reachable
    return None


def missing_parts(metric: MetricDefinition, layer: SemanticLayer) -> list[str]:
    """The metrics this one derives from that no file publishes."""
    return [name for name in metric.derives_from if name not in layer.metrics]


def assembles(metric: MetricDefinition, layer: SemanticLayer) -> bool:
    """Whether a query can be built for this metric at all.

    A route that does not hold and a part that does not exist are both reported by
    `check_entries`; this is what stops every later check reporting them again, or
    walking into the missing entry and raising instead of failing.
    """
    return route_problem(metric, layer) is None and not missing_parts(metric, layer)


def check_reporting_currency(metric: MetricDefinition, layer: SemanticLayer) -> None:
    """Check 5 — the declared Reporting Currency, and the metrics that have none.

    [`Reporting Currency`](../docs/glossary.md#a-the-system) is registered as *"the
    single currency a Grounded Answer is expressed in. Every **monetary** metric
    must state one"* — so the rule has two directions and this check takes both. A
    money metric with no currency is an answer whose units nobody knows; a count
    or a quantity *with* one is a fact invented by a field that had to be filled
    in.

    For a monetary metric the currency must also appear as a string literal in one
    of the Join Paths its route names. It is written in two places on purpose: C1
    forbids a template the loader fills in, so the currency is inside the Join Path
    text where a reviewer reads it, and this check is what makes the duplication
    safe.
    """
    monetary = metric.unit == MONEY
    if monetary and not metric.reporting_currency:
        problems.append(
            f"Metric Definition {metric.name!r} has unit {metric.unit!r} and states "
            f"no reporting_currency — a monetary metric that does not say which "
            f"currency it comes back in is a number with no units"
        )
        return
    if not monetary:
        if metric.reporting_currency:
            problems.append(
                f"Metric Definition {metric.name!r} has unit {metric.unit!r} and "
                f"states reporting_currency {metric.reporting_currency!r} — only a "
                f"monetary metric has one, and a count expressed in a currency is a "
                f"fact the field invented"
            )
        return

    literals: set[str] = set()
    for name in metric.join_paths:
        parsed = sqlglot.parse_one(layer.join_paths[name].on, dialect=DIALECT)
        literals |= {
            literal.this for literal in parsed.find_all(exp.Literal)
            if literal.is_string
        }
    if metric.reporting_currency not in literals:
        problems.append(
            f"Metric Definition {metric.name!r} declares reporting_currency "
            f"{metric.reporting_currency!r}, and the Join Paths on its route "
            f"convert to {sorted(literals) or 'nothing'} — the currency is written "
            f"in both places because C1 forbids a template, and the two have "
            f"drifted apart"
        )


def check_derivation(metric: MetricDefinition, layer: SemanticLayer) -> None:
    """Check 10 — a composed metric adds up metrics that exist and are commensurable.

    `derives_from` names the Certified Metrics whose value is **added** to this
    metric's own expression, which is how `Account Value` is *"Cash Balance plus all
    Positions marked to market"* without restating the certified Cash Balance
    expression. Four ways that can be a lie, and the fourth is the quiet one:

      * a part no file publishes — the metric cannot be computed at all;
      * a metric deriving from itself, which is an assembly that never terminates;
      * a part that itself derives, which this assembly does not walk. One level is
        what the corpus has, so one level is what is claimed and what is enforced;
      * a part in a different unit or a different currency. Adding a count to a
        money figure, or euros to dollars, produces a number rather than an error,
        and it is the failure a corpus about not blurring quantities can least
        afford to commit itself.
    """
    for name in metric.derives_from:
        part = layer.metrics.get(name)
        if part is None:
            problems.append(
                f"Metric Definition {metric.name!r} derives from {name!r}, which no "
                f"file under {METRIC_HOME} publishes — so the metric names a value "
                f"the corpus cannot produce"
            )
        elif part.name == metric.name:
            problems.append(
                f"Metric Definition {metric.name!r} derives from itself"
            )
        elif part.derives_from:
            problems.append(
                f"Metric Definition {metric.name!r} derives from {name!r}, which "
                f"itself derives from {list(part.derives_from)} — this assembly adds "
                f"one level and does not walk a chain, so the second level would be "
                f"silently dropped"
            )
        elif (part.unit, part.reporting_currency) != (
            metric.unit, metric.reporting_currency
        ):
            problems.append(
                f"Metric Definition {metric.name!r} is {metric.unit!r} in "
                f"{metric.reporting_currency or 'no currency'} and derives from "
                f"{name!r}, which is {part.unit!r} in "
                f"{part.reporting_currency or 'no currency'} — the two are added "
                f"together, and adding them would produce a number rather than an "
                f"error"
            )


def check_expressions(warehouse: WarehouseAdapter, layer: SemanticLayer) -> None:
    """Checks 3 and 4: every published expression executes, and agrees."""
    if not warehouse.row_count("fct_trade"):
        problems.append(
            "fct_trade is empty — run `uv run python -m veritas.ingestion` before "
            "checking the Semantic Layer, or every expression below returns null "
            "over no rows and this check passes vacuously"
        )
        return

    returned: dict[str, Decimal | int] = {}
    for metric in layer.metrics.values():
        if not assembles(metric, layer):
            continue  # already reported by check_entries

        print()
        print(f"  {metric.name}  v{metric.version}  ·  {metric.unit}"
              f"{' in ' + metric.reporting_currency if metric.reporting_currency else ''}"
              f"  ·  {metric.grain}")
        print(f"      expression   {metric.expression}")
        print(f"      route        {route_as_read(metric, layer)}")
        for predicate in metric.filters:
            print(f"      filter       {predicate}")
        for name in metric.derives_from:
            print(f"      plus         {name}, added to this expression")
        print(f"      date column  {metric.date_column}")

        whole = executable_query(metric, layer)
        print(f"      query        {whole}")
        if not every_part_reads_as_a_query(metric, layer):
            problems.append(
                f"{metric.name!r}: the query its published expression assembles into "
                f"does not parse, so nothing below was executed. A parse failure is "
                f"a rejection, never a skip\n      {whole}"
            )
            continue

        total = one_number(warehouse, whole)
        if total is None:
            continue
        returned[metric.name] = total
        print(f"      returns      {total:,.2f} {units(metric)}")

        independently = INDEPENDENT_FIGURES.get(metric.name)
        if independently is None:
            print(f"      compared     nothing — check_warehouse.py computes no "
                  f"independent figure for this metric, so all that is claimed here "
                  f"is that the expression executes and returns a number")
        elif metric.unit == MONEY and metric.reporting_currency != REPORTING_CURRENCY:
            problems.append(
                f"{metric.name!r} declares reporting_currency "
                f"{metric.reporting_currency!r} and check_warehouse.py computes its "
                f"figures in {REPORTING_CURRENCY!r} — two numbers in different "
                f"currencies agreeing would mean nothing, and disagreeing would "
                f"mean less"
            )
            independently = None
        else:
            theirs = independently(warehouse)
            print(f"      compared     check_warehouse.py computes "
                  f"{theirs:,.2f} from its own SQL — "
                  f"{'identical' if theirs == total else 'DIFFERENT'}")
            if theirs != total:
                problems.append(
                    f"{metric.name!r}: the published expression returns "
                    f"{total:,.2f} {units(metric)} and "
                    f"check_warehouse.py's independent SQL returns {theirs:,.2f}. "
                    f"One of the two is wrong, and neither file is entitled to "
                    f"assume it is the other one"
                )
                # The period comparison below is the *date predicate* check, and it
                # can only say that once the arithmetic agrees. Asked now it would
                # disagree too and report the same defect a second time under a
                # heading that names the wrong cause.
                independently = None

        check_period_split(warehouse, metric, layer, total, independently)

    check_distinction_pairs(layer, returned)
    check_widening_cast(warehouse, layer)


def check_period_split(
    warehouse: WarehouseAdapter,
    metric: MetricDefinition,
    layer: SemanticLayer,
    total: Decimal | int,
    independently: Callable[..., Decimal] | None,
) -> None:
    """The date column is a column, filtering on it partitions the metric, and it
    is the *right* column.

    C2 requires a Metric Definition to carry its date predicate, and a field nothing
    ever reads is carried in the weakest possible sense. So the same metric is asked
    twice more, either side of the midpoint of its own dates.

    Three claims come out of that, and the third is the one worth having:

      * the two halves add up to the whole, so `date_column` names a column on the
        joined tables and one that no row is missing;
      * neither half is empty, so the filter was actually exercised;
      * the later half equals what `check_warehouse.py` computes for the same
        window from its own opinion of which date a Trade's revenue falls on.

    Only the third can catch the Section C mistake. `settlement_date` in place of
    `trade_date` partitions just as neatly and totals identically — it moves Trades
    across the boundary, which is exactly what
    [Section C](../docs/glossary.md#c-distinctions-we-must-not-blur) says that pair
    does — so a check that asked only for the total would agree with itself all the
    way to the wrong answer. That is the failure
    [R2](../docs/plan/step-004-semantic-layer.md#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21)
    describes, and it needs two independently written period filters to see.
    """
    dates = rows_from(
        warehouse,
        f"SELECT min({metric.date_column}), max({metric.date_column}) "
        f"{source(metric, layer)}",
    )
    if dates is None:
        return
    ((earliest, latest),) = dates
    boundary = earliest + (latest - earliest) // 2

    halves: list[Decimal | int] = []
    for comparison in (BEFORE, FROM_THEN):
        half = one_number(
            warehouse,
            executable_query(metric, layer, comparison),
            [boundary] * bindings(metric),
        )
        if half is None:
            return
        halves.append(half)

    early, late = halves
    print(f"      period       {earliest} … {latest}, split at {boundary}: "
          f"{early:,.2f} + {late:,.2f} = {early + late:,.2f}")
    if early + late != total:
        problems.append(
            f"{metric.name!r}: filtered on {metric.date_column}, the two halves of "
            f"its own date range come to {early + late:,.2f} against {total:,.2f} "
            f"unfiltered. A period filter on the date predicate a Metric Definition "
            f"carries must partition the metric, not shrink it"
        )
    if not early or not late:
        problems.append(
            f"{metric.name!r}: splitting {metric.date_column} at {boundary} puts "
            f"everything on one side, so the period filter was never actually "
            f"exercised"
        )

    if independently is None:
        return
    theirs = independently(warehouse, boundary)
    print(f"      compared     check_warehouse.py computes {theirs:,.2f} from "
          f"{boundary} on — "
          f"{'identical' if theirs == late else 'DIFFERENT'}")
    if theirs != late:
        problems.append(
            f"{metric.name!r}: from {boundary} on, the published expression "
            f"filtered on {metric.date_column} returns {late:,.2f} and "
            f"check_warehouse.py's independent period filter returns {theirs:,.2f}. "
            f"The two totals agree, so this is the date predicate rather than the "
            f"arithmetic — a Glossary Section C pair, which is the whole reason C2 "
            f"asks a Metric Definition to carry one"
        )


def check_parse_rule(layer: SemanticLayer) -> None:
    """Check 6: the fail-closed rule, shown to have both of its answers.

    The positive control is the corpus itself — every expression above parsed, or
    the run has already failed. What is probed here is the other branch, on real
    entries with their expressions replaced, through the same assembly.

    **Two entries rather than one**, where Sub-step 4.1 needed only one. A composed
    metric assembles a second reader path, and it is the path where a rule that
    looked at the finished statement instead of at each part would pass an empty
    expression — so the probe runs on a metric that derives from nothing and on one
    that derives, and says which is which.
    """
    print()
    print("  parse rule — an expression that does not parse fails the run")
    for composed in (False, True):
        probed = next(
            (metric for metric in layer.metrics.values()
             if bool(metric.derives_from) == composed
             and assembles(metric, layer)),
            None,
        )
        if probed is None:
            continue
        shape = "composed of two metrics" if composed else "one expression"
        print(f"    in {probed.name!r} — {shape}")
        for description, expression, expected in PARSE_PROBES:
            broken = replace(probed, expression=expression)
            verdict = every_part_reads_as_a_query(broken, layer)
            print(f"      {'reads' if verdict else 'refuses'}  {description}: "
                  f"{expression!r}")
            if verdict != expected:
                problems.append(
                    f"the parse rule {'accepted' if verdict else 'refused'} "
                    f"{description} ({expression!r}), pasted into {probed.name!r}'s "
                    f"query — so it is not the rule this check reports it to be"
                )


def check_distinction_pairs(
    layer: SemanticLayer, returned: dict[str, Decimal | int]
) -> None:
    """Check 7: every Section C pair of Certified Metrics is two different numbers.

    `check_warehouse.py --distinctions` already proves the **data** separates these
    pairs. This proves the **published expressions** do, which is a different claim:
    a corpus whose whole purpose is keeping *"a correct program computing the wrong
    number"* from happening can separate them in the Warehouse and blur them in the
    Semantic Layer, and only this check would see it.

    Where the two sides share a unit the bar is a visible gap rather than
    inequality, because two figures differing in the sixth decimal place are
    distinct and tell a reader nothing. Where they do not — Traded Notional is money
    and Trade Count is a count — a percentage between them would be arithmetic with
    no meaning, so the bar is that they are different numbers at all, which is the
    most the pair can honestly claim.
    """
    print()
    print("  Section C — every pair of Certified Metrics, from the published "
          "expressions")
    for left_name, right_name, why in SECTION_C_PAIRS:
        if left_name not in returned or right_name not in returned:
            problems.append(
                f"Section C pair {left_name!r} / {right_name!r}: one side returned "
                f"no figure above, so the pair could not be compared — a pair the "
                f"corpus cannot compute is a distinction it cannot keep"
            )
            continue
        left, right = returned[left_name], returned[right_name]
        left_unit = layer.metrics[left_name].unit
        right_unit = layer.metrics[right_name].unit
        print(f"    {left_name} / {right_name} — \"{why}\"")
        print(f"      {left_name}: {left:,.2f} {units(layer.metrics[left_name])}")
        print(f"      {right_name}: {right:,.2f} {units(layer.metrics[right_name])}")
        if left_unit != right_unit:
            print(f"      different units, so the claim is only that they differ")
            if left == right:
                problems.append(
                    f"Section C pair {left_name!r} / {right_name!r} returned the "
                    f"same figure {left:,.2f} from two published expressions"
                )
            continue
        apart = (
            abs(left - right) / max(abs(left), abs(right))
            if max(abs(left), abs(right)) else Decimal("0")
        )
        print(f"      {apart:.2%} apart")
        if apart < MIN_DISTINCTION_GAP:
            problems.append(
                f"Section C pair {left_name!r} / {right_name!r} has collapsed in the "
                f"Semantic Layer: the published expressions return {left:,.2f} and "
                f"{right:,.2f}, {apart:.4%} apart against a "
                f"{MIN_DISTINCTION_GAP:.2%} floor. Two Certified Metrics a question "
                f"cannot tell apart are one metric under two names"
            )


def check_widening_cast(
    warehouse: WarehouseAdapter, layer: SemanticLayer
) -> None:
    """Check 11: every widening cast in the corpus is shown to be load-bearing.

    Four of the nine published expressions carry `CAST(... AS DECIMAL(38, 6))`.
    Without it the engine computes the product in DECIMAL(18) and raises on
    overflow, so the cast is what makes the metric computable at all — and
    [DEBT-015](../docs/debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)
    is the Ledger entry about a dialect scan that cannot see it.

    A cast nobody can see the need for is a cast somebody eventually removes. So
    this runs the expression with the cast taken back out, on every run, and expects
    a refusal. **A cast whose removal changes nothing is the finding**, not the
    silence: it would mean the corpus carries an engine-specific width for no
    reason, which is a different and smaller problem than the one DEBT-015 names.
    """
    print()
    print("  widening cast — the expressions that do not run without one")
    for metric in layer.metrics.values():
        if not WIDENING_CAST.search(metric.expression) or not assembles(metric, layer):
            continue
        uncast = replace(
            metric, expression=WIDENING_CAST.sub(r"\1", metric.expression)
        )
        rows = None
        try:
            rows = warehouse.query(executable_query(uncast, layer))
        except Exception as refusal:  # noqa: BLE001 — see DEBT-016 above
            first_line = str(refusal).splitlines()[0]
            print(f"    refused  {metric.name}: {type(refusal).__name__}: "
                  f"{first_line}")
        if rows is not None:
            problems.append(
                f"{metric.name!r} carries a widening cast and the engine computes "
                f"its expression without one, returning {rows!r} — so the cast is a "
                f"width this corpus states for no reason a run can show"
            )


def check_spike_pin(layer: SemanticLayer) -> None:
    """Check 9: the three expressions the spike measured are what the corpus publishes.

    [R4](../docs/plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)
    keeps `check_validation_feasibility.py`'s certified expressions as Python
    literals rather than re-pointing the spike at `semantic/`, because
    `validation-feasibility.md` carries output from one dated run and *"evidence
    whose inputs move is not evidence"*. Pinning alone has the mirror-image failure —
    the go/no-go could end up being about expressions the project no longer uses —
    and this is the assertion that closes it.

    A divergence forces a decision rather than passing unnoticed in either
    direction: re-run the spike and update the verdict, or put the Metric Definition
    back.
    """
    print()
    print("  spike pin — the expressions the Sub-step 3.2 spike measured")
    for name, measured in sorted(CERTIFIED_EXPRESSIONS.items()):
        metric = layer.metrics.get(name)
        if metric is None:
            problems.append(
                f"the spike measured {name!r} and no file under {METRIC_HOME} "
                f"publishes it, so validation-feasibility.md's verdict is about an "
                f"expression the corpus does not have"
            )
            continue
        if metric.expression != measured:
            problems.append(
                f"{name!r}: the spike measured one expression and the Semantic Layer "
                f"publishes another, so the GO recorded in validation-feasibility.md "
                f"is about a statement this project no longer uses. Re-run the spike "
                f"and update the verdict, or put the Metric Definition back\n"
                f"      spike     {measured}\n"
                f"      published {metric.expression}"
            )
            continue
        print(f"    pinned   {name}")


def main() -> int:
    try:
        layer = load_semantic_layer()
    except SemanticEntryError as refusal:
        print(f"  {refusal}")
        print()
        print("FAIL — the Semantic Layer does not load, so nothing below ran")
        return 1

    print(f"  Semantic Layer: semantic/ — {len(layer.metrics)} Metric Definition(s), "
          f"{len(layer.join_paths)} Join Path(s)")
    check_entries(layer)

    with WarehouseAdapter() as warehouse:
        print(f"  Warehouse: {DATABASE_PATH.relative_to(REPO_ROOT)}")
        check_expressions(warehouse, layer)

    check_parse_rule(layer)
    check_spike_pin(layer)

    print()
    if problems:
        print(f"FAIL — {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("PASS — every published expression executes against the Warehouse, and "
          "every figure with a second opinion agrees with it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
