"""Check the Semantic Layer against the Warehouse its expressions compute over.

Run with:  uv run python .claude/scripts/check_semantic_layer.py

Needs a filled Warehouse — `uv run python -m veritas.ingestion` first — because a
published expression that has never been executed is a claim rather than a metric.

A corpus cannot be proved by running it, only by running what it claims. Six checks
do that. Five are the ones
[Sub-step 4.1](../docs/plan/step-004-semantic-layer.md#41--publish-the-semantic-entry-format-on-one-metric-definition)
names; the sixth is Non-Negotiable #1 applied to the one place this corpus can coin
a domain noun by accident.

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
     entry's own Join Path and date column, executed through the Warehouse Adapter,
     and returns a number. Pasted rather than rebuilt: a check that re-derives the
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

  5. The declared Reporting Currency appears in the Join Path the entry names, as a
     string literal in the join condition's parse tree. It is written in two places
     on purpose: C1 forbids a template the loader fills in, so the currency is
     inside the Join Path text where a reviewer reads it, and this check is what
     makes the duplication safe.

  6. An expression that does not parse **fails the run**, rather than being skipped —
     [C6](../docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)'s
     echo in a Step that builds no Gate. Two probes give the rule teeth on every
     run, because a rule that has only ever seen valid input reads the same whether
     it works or does nothing.

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
    JoinPath,
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

from check_warehouse import REPORTING_CURRENCY, gross_revenue  # noqa: E402
# The other half of check 4. `gross_revenue` is imported rather than reimplemented
# for the reason the spike imports `unportable_functions`: a second copy would
# answer the question about the copy, and would go on answering it after the
# original changed. What must not happen is the arrow pointing the other way —
# `check_warehouse.py` reading `semantic/` would make both sides compute the same
# wrong number and agree, which is R2's whole subject.

# Every Certified Metric this file can put a second, independently written figure
# next to, and the function that produces it. A metric absent from here still has
# to execute and return a number; it just has nothing to be checked against, and
# check 4 says which it got rather than letting one word cover both.
INDEPENDENT_FIGURES = {
    "Gross Revenue": gross_revenue,
}

# The engine the queries are read in. The same one they are executed in, because a
# statement checked in one dialect and run in another is two statements.
DIALECT = "duckdb"

# Where Glossary Section B says a Certified Metric lives, and the cell position the
# "Lives in" column sits at once a leading pipe has made cells[0] the empty string.
# Both match `check_warehouse.py`'s reader of the same table.
METRIC_HOME = "semantic/metrics/"
LIVES_IN_COLUMN = 3

# The two halves the period split asks for. SQL operators rather than anything read
# out of an entry: the date *column* comes from the Metric Definition, and how it is
# compared is this file's own.
BEFORE = "<"
FROM_THEN = ">="

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

    Only one direction is checked here. *Every Section B metric has a Metric
    Definition* is the bar Sub-step 4.2 sets for itself, and asserting it now would
    fail on the eight metrics 4.2 is for.
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


def source(join: JoinPath) -> str:
    """The `FROM ... JOIN ... ON ...` the Join Path certifies, as written."""
    return f"FROM {join.from_table} JOIN {join.to_table} ON {join.on}"


def executable_query(
    metric: MetricDefinition, join: JoinPath, comparison: str | None = None
) -> str:
    """One Metric Definition, as the statement that computes it.

    The expression goes in **verbatim**. Everything around it comes from the entry's
    own two C2 fields — the Join Path it names and, when a half is asked for, the
    date column a period filter keys on, compared against a bound parameter.

    What this assembles for `Gross Revenue` is the shape the Sub-step 3.2 spike's
    `bare` probe writes out by hand — the spike had to, because no Semantic Layer
    existed yet to publish one. Whether the two are still the *same text* is not
    asserted here: that is
    [R4](../docs/plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)'s
    pin, which lands in Sub-step 4.2 once all three of the expressions the spike
    measured are published.
    """
    period = f" WHERE {metric.date_column} {comparison} ?" if comparison else ""
    return f"SELECT {metric.expression} {source(join)}{period}"


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
    """Checks 2 and 5, plus the one cross-reference check 3 cannot run without."""
    certified = certified_metric_terms()
    print(f"  Glossary Section B names {len(certified)} terms living in "
          f"{METRIC_HOME}")

    for metric in layer.metrics.values():
        if metric.name not in certified:
            problems.append(
                f"Metric Definition {metric.name!r} is not a Glossary Section B term "
                f"whose 'Lives in' cell says {METRIC_HOME} — register the term, or "
                f"amend its row, before certifying a computation under that name"
            )

        join = layer.join_paths.get(metric.join_path)
        if join is None:
            problems.append(
                f"Metric Definition {metric.name!r} names Join Path "
                f"{metric.join_path!r}, which no file under semantic/joins/ "
                f"publishes — so the route the expression is computed over is one "
                f"the corpus does not certify"
            )
            continue

        literals = {
            literal.this
            for literal in sqlglot.parse_one(join.on, dialect=DIALECT).find_all(
                exp.Literal
            )
            if literal.is_string
        }
        if metric.reporting_currency not in literals:
            problems.append(
                f"Metric Definition {metric.name!r} declares reporting_currency "
                f"{metric.reporting_currency!r}, and Join Path {join.name!r} "
                f"converts to {sorted(literals) or 'nothing'} — the currency is "
                f"written in both places because C1 forbids a template, and the two "
                f"have drifted apart"
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

    for metric in layer.metrics.values():
        join = layer.join_paths.get(metric.join_path)
        if join is None:
            continue  # already reported by check_entries

        print()
        print(f"  {metric.name}  v{metric.version}  ·  {metric.unit} in "
              f"{metric.reporting_currency}  ·  {metric.grain}")
        print(f"      expression   {metric.expression}")
        print(f"      join path    {join.name} — {join.from_table} → {join.to_table}")
        print(f"      date column  {metric.date_column}")

        whole = executable_query(metric, join)
        print(f"      query        {whole}")
        if not reads_as_a_query(whole):
            problems.append(
                f"{metric.name!r}: the query its published expression assembles into "
                f"does not parse, so nothing below was executed. A parse failure is "
                f"a rejection, never a skip\n      {whole}"
            )
            continue

        total = one_number(warehouse, whole)
        if total is None:
            continue
        print(f"      returns      {total:,.2f} {metric.reporting_currency}")

        independently = INDEPENDENT_FIGURES.get(metric.name)
        if independently is None:
            print(f"      compared     nothing — check_warehouse.py computes no "
                  f"independent figure for this metric, so all that is claimed here "
                  f"is that the expression executes and returns a number")
        elif metric.reporting_currency != REPORTING_CURRENCY:
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
                    f"{total:,.2f} {metric.reporting_currency} and "
                    f"check_warehouse.py's independent SQL returns {theirs:,.2f}. "
                    f"One of the two is wrong, and neither file is entitled to "
                    f"assume it is the other one"
                )
                # The period comparison below is the *date predicate* check, and it
                # can only say that once the arithmetic agrees. Asked now it would
                # disagree too and report the same defect a second time under a
                # heading that names the wrong cause.
                independently = None

        check_period_split(warehouse, metric, join, total, independently)


def check_period_split(
    warehouse: WarehouseAdapter,
    metric: MetricDefinition,
    join: JoinPath,
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
        f"{source(join)}",
    )
    if dates is None:
        return
    ((earliest, latest),) = dates
    boundary = earliest + (latest - earliest) // 2

    halves: list[Decimal | int] = []
    for comparison in (BEFORE, FROM_THEN):
        half = one_number(
            warehouse, executable_query(metric, join, comparison), [boundary]
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
    the run has already failed. What is probed here is the other branch, on the real
    entry with its expression replaced, through the same assembly.
    """
    print()
    print("  parse rule — an expression that does not parse fails the run")
    for metric in layer.metrics.values():
        join = layer.join_paths.get(metric.join_path)
        if join is None:
            continue
        for description, expression, expected in PARSE_PROBES:
            broken = replace(metric, expression=expression)
            verdict = reads_as_a_query(executable_query(broken, join))
            print(f"    {'reads' if verdict else 'refuses'}  {description}: "
                  f"{expression!r}")
            if verdict != expected:
                problems.append(
                    f"the parse rule {'accepted' if verdict else 'refused'} "
                    f"{description} ({expression!r}), pasted into {metric.name!r}'s "
                    f"query — so it is not the rule this check reports it to be"
                )
        return  # one entry is enough: the rule is about the reader, not the corpus


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
