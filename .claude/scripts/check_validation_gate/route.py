"""Sub-step 5.4's rule: the metric is computed across its own joins, over its own period.

The fourth of the five modules
[R8](../../docs/plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)
lays out, and the one that pays
[DEBT-014](../../docs/debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject).
The entry's repayment condition is a test rather than an intention — *"that Sub-step is
not done until `notional through the wrong currency` is rejected by the Gate"* — and
this file is where that test is run.

**Both halves of the entry are measured here, not argued.** The Ledger's own status note
of 2026-08-20 says the date half *"is argued rather than measured, and the Sub-step that
pays this entry owes a probe for it."* So the two Section C pairs are **executed**, and
the run prints the two numbers each produces side by side:

  * `Traded Notional` through the Trade's Denomination Currency against the Instrument's
    Quotation Currency — the currency pair, which the spike has printed since Step 003;
  * `Gross Revenue` over a period keyed on Settlement Date against the same period keyed
    on Trade Date — the date pair, which nothing had executed before this Sub-step.

A rejection is only worth having if the thing rejected returns a different number, and
these are the numbers.

**Every date comes from the Snapshot calendar.**
[DEBT-012](../../docs/debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)'s
Trigger is *"the first 'as of' date chosen by anything but the Snapshot calendar"*, and a
probe that picked a period boundary out of the air would fire it. The two boundaries
below are read out of `fct_position_snapshot` on every run, which keeps the arm unfired
the way [R7 of Step 004](../../docs/plan/step-004-semantic-layer.md#r7--the-date-axis-defers-debt-012s-trigger-rather-than-avoiding-it--approved-by-amino-2026-08-21)
did — and it means the period moves when the loaded window moves, so the figures printed
here are a dated measurement rather than a constant.

**The hole this module declared is closed, and the pair that declared it stays.** A
Metric Definition carries three fields that say which rows its expression is computed
over; Sub-step 5.4 read two of them and
[DEBT-020](../../docs/debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters)
was the third, `filters`. For one Sub-step `Realised P&L` with its `movement_type`
predicate dropped was declared **allowed** here on purpose, which carried the cost
DEBT-014 was opened about — this file passed while demonstrating a wrong answer — and
[R15](../../docs/plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28)
ruled that Sub-step 5.5 pays it rather than the Grounding Step the Trigger names. It
does: the probe is `rejected`, its control is still `allowed`, and
`check_the_filter_gap` goes on running both halves so the entry stays a measurement
after it is paid.

**What Sub-step 5.5 moved in this module, and why the moves are the finding.** The route
rule gained two more sources of permission — an axis's `routes` and the Access Profile's
route — and one more reading, the certified filters. So `net revenue by region` is
allowed **by this rule** where 5.4 refused it, which is `by region` becoming an axis a
query can reach; and the three probes that are on their metric's route are refused by the
**Gate** where 5.4 allowed them, because they carry no access predicate and nothing here
can give them one without moving the spike's dated statements. Every one of those is a
declared verdict rather than a discovery, which is what the declarations were for.

**Two statements are the spike's and are read out of its text rather than copied.**
`probes.spike_statements` parses `check_validation_feasibility.py` with `ast` and takes
the `sql=` literals off the parse tree, which is
[R14](../../docs/plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27).
`traces.py` already holds those two character for character and checks that claim on
every run; a third copy here would be a third thing to keep in step, so this module reads
the one the spike compiled. What that costs is that the two are not string literals in
this file and so are invisible to `check_warehouse.py`'s dialect scan — they are read by
it in the spike, which is where they are written down.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from probes import (
    ALLOWED,
    REJECTED,
    Probe,
    Report,
    certified_statement,
    judge_probes,
    problems,
    rule_named,
    spike_statements,
)

from veritas.validation import (
    ANALYST,
    AccessProfile,
    RejectionReason,
    Reading,
    TracerRefused,
    ValidationGate,
    date_columns_filtered,
    grouped_columns,
    read,
    resolve,
    route_of,
)
from veritas.warehouse import WarehouseAdapter

# How long the period the two date probes ask about is. A **definition**, not a
# measurement: a quarter is the period the Glossary's own worked example asks for —
# *"Net Revenue by region last quarter"* — and it is written in days because the
# Snapshot calendar is a list of dates and nothing here needs month arithmetic. Which
# two dates a quarter turns into is read from that calendar on every run.
QUARTER = timedelta(days=91)

# How far apart two figures must be before "a different number" means anything to a
# reader, and the same value and the same reasoning as
# `check_validation_feasibility.py`'s `MIN_GAP`: two numbers differing in the sixth
# decimal place are technically distinct and tell nobody anything, so a rejection that
# separates only those is a rejection nobody is better off for. Deliberately a second
# constant rather than an import — the spike is a dated measurement and this is a live
# check, and the two are free to move apart.
MIN_GAP = Decimal("0.005")


@dataclass(frozen=True, slots=True)
class RouteProbe(Probe):
    """A probe, plus what this rule's own reading of it should find.

    `off_route` is True when the statement's joins and the Metric Definition's disagree
    in either direction; `stray_dates` is True when a WHERE clause keys on a date column
    the metric is not certified over. Both are declared separately from `verdict` for the
    reason `restricted.py`'s `reaches` is: a shape refused by an earlier rule still has a
    route, and the reading that would have caught it should not go unmeasured because
    something else got there first.
    """

    off_route: bool = False
    stray_dates: bool = False


def from_the_spike(name: str) -> str:
    """One of the spike's claim-1 statements, by name, read out of its source text.

    A `SystemExit` rather than a `KeyError` when the name has gone, and for the reason
    `spike_statements` raises one: this module's probe would otherwise vanish quietly,
    and a check that measures nothing passes.
    """
    statements = spike_statements("PROBES")
    if name not in statements:
        raise SystemExit(
            f"check_validation_feasibility.py no longer holds a claim-1 probe named "
            f"{name!r}, so this module cannot judge the shape it exists to judge"
        )
    return statements[name]


# The route probes. Statements whose route is wrong first, then the shapes that are on
# their metric's route.
#
# **None of these five is scoped**, because none of them was written to be: they are the
# spike's statements and this Sub-step's, and both predate the rule that requires an
# Access Profile's predicate. Since Sub-step 5.5 that rule refuses every one of them that
# gets past this one, so the three on their metric's route are declared `rejected` for
# `missing access predicate` — the Gate's verdict, not this rule's, and
# `check_this_rule_ran` and `check_the_route_reading` below are what keep the two
# separate. Rewriting them to carry the predicate is not available: two are read out of
# the spike's source text, where they are a dated measurement that must not move.
PROBES = (
    RouteProbe(
        name="notional through the wrong currency",
        sql=from_the_spike("notional through the wrong currency"),
        verdict=REJECTED,
        reasons=(RejectionReason.UNCERTIFIED_ROUTE,),
        off_route=True,
        why="**the probe DEBT-014 was opened about.** `Traded Notional`'s certified "
            "expression, converted out of the Trade's Denomination Currency instead of "
            "the Instrument's Quotation Currency. Nothing in the projection differs, so "
            "the tracing rule traces it and allows it — the Ledger entry's own "
            "diagnosis — and this rule is the only thing between that statement and an "
            "answer that is wrong by the margin `check_the_numbers_differ` prints below",
    ),
    RouteProbe(
        name="a cross product, certified metric",
        sql="SELECT sum(billed.commission * rate.fx_rate) AS gross_revenue "
            "FROM fct_trade AS billed, fct_trade AS again "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=REJECTED,
        reasons=(RejectionReason.UNCERTIFIED_ROUTE,),
        off_route=True,
        why="the blind spot `read_only.py` declared and could not close. The planner's "
            "estimate counts rows read off a table and a join makes its rows instead of "
            "reading them, so a cross product is inside the scan ceiling; 5.1's "
            "cross-product probe was refused for computing no metric at all, and that "
            "module's own comment said *a cross product that computed a certified one "
            "would still be allowed here*. This is that statement, and a join with no "
            "condition is a join no Semantic Entry certifies",
    ),
    RouteProbe(
        name="a count with a multiplying join",
        sql="SELECT count(billed.trade_id) AS trades "
            "FROM fct_trade AS billed "
            "JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.trade_date "
            " AND rate.from_currency = billed.denomination_currency "
            " AND rate.to_currency = 'EUR'",
        verdict=REJECTED,
        reasons=(RejectionReason.UNCERTIFIED_ROUTE,),
        off_route=True,
        why="`Trade Count` is `count(fct_trade.trade_id)` over `fct_trade` and joins "
            "nothing, and this joins the FX Rate table to it. The projection is the "
            "certified one, the conversion is pointless on a count, and the join is the "
            "kind that quietly multiplies rows — the shape where *the arithmetic is "
            "certified and the rows are not* costs nothing to write and is the reason "
            "C2 exists. It is here because a metric with an **empty** `join_paths` is "
            "the case a rule written as *are the certified joins present* would pass "
            "vacuously",
    ),
    RouteProbe(
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
        reasons=(RejectionReason.MISSING_ACCESS_PREDICATE,),
        why="the Glossary's own worked example, and the probe Sub-step 5.4 declared "
            "here so that 5.5 moving it would be a measurement. It was refused by "
            "**this** rule, on two joins to `dim_client` no entry named; 5.5 added the "
            "Join Paths and the `routes` field that certify them, and this rule now "
            "allows it — `check_the_route_reading` prints `on` for it and "
            "`check_this_rule_ran` counts it as passed on. What refuses it now is the "
            "access predicate it does not carry, which is a different rule and a "
            "different sentence",
    ),
    RouteProbe(
        name="traded notional",
        sql=from_the_spike("traded notional"),
        verdict=REJECTED,
        reasons=(RejectionReason.MISSING_ACCESS_PREDICATE,),
        why="the same metric as the first probe, converted the way its Metric "
            "Definition says: through `dim_instrument` to the Quotation Currency. The "
            "positive control the first probe needs — one join different, and **this "
            "rule** reaches the opposite verdict on it, which `check_the_route_reading` "
            "and `check_this_rule_ran` are what show now that the Gate does not. It is "
            "the spike's statement, read out of the spike's source, so it cannot be "
            "given the access predicate Sub-step 5.5 requires without moving a dated "
            "measurement",
    ),
)


def statement_for(gate: ValidationGate, name: str, with_filters: bool) -> str:
    """The simplest statement that computes one Certified Metric and is allowed to run.

    `probes.certified_statement` is where the construction lives, as of Sub-step 5.5:
    this file, `traces.py` and `access.py` all build it, and it stopped being three
    lines the day a statement also had to carry the access route and the access
    predicate. What is left here is the name this module calls it by.

    `with_filters=False` is the one caller that wants the statement the corpus does
    **not** certify, and it exists for DEBT-020's pair alone.
    """
    return certified_statement(gate, name, ANALYST, with_filters=with_filters)


def filter_probes(gate: ValidationGate) -> tuple[RouteProbe, ...]:
    """The hole Sub-step 5.4 found and Sub-step 5.5 closed:
    [DEBT-020](../../docs/debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters).

    A Metric Definition carries **three** fields that pin down which rows its expression
    is computed over — `join_paths`, `date_column` and `filters` — and 5.4 read two of
    them. So `Realised P&L` with its certified `movement_type` predicate dropped computed
    the certified expression, across the certified route, over four movement types
    instead of one, and was **allowed**.

    **The pair is kept and its first half flipped**, which is what the entry was declared
    for. For one Sub-step the probe below declared `allowed` on purpose and this file
    passed while demonstrating a wrong answer — the cost DEBT-014 was opened about,
    carried openly under
    [R15](../../docs/plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28).
    It is now `rejected`, its control is still `allowed`, and `check_the_filter_gap`
    goes on printing the two numbers so the entry stays a measurement after it is paid.
    `access.py`'s third mutation is what shows the flip is a rule rather than a renamed
    probe: delete the comparison and the statement comes back.
    """
    return (
        RouteProbe(
            name="Realised P&L with its filter dropped",
            sql=statement_for(gate, "Realised P&L", with_filters=False),
            verdict=REJECTED,
            reasons=(RejectionReason.MISSING_CERTIFIED_FILTER,),
            why="**DEBT-020, paid.** The certified expression across the certified "
                "route, scoped to the permitted region, with "
                "`movement_type = 'realised P&L'` left out — so it would sum "
                "commission, fee, rebate and realised P&L and call the total Realised "
                "P&L. Every other rule the Gate has passes it, and this rule is the one "
                "that refuses it: `filters` is the third field C2 put on a Metric "
                "Definition, and reading it is the whole of the repayment",
        ),
        RouteProbe(
            name="Realised P&L as its entry says",
            sql=statement_for(gate, "Realised P&L", with_filters=True),
            verdict=ALLOWED,
            why="the same metric with its certified filter in place — the control that "
                "makes the probe above a rule rather than a statement about "
                "`Realised P&L` being unjudgeable. One conjunct apart, opposite "
                "verdicts",
        ),
    )


def check_the_filter_gap(gate: ValidationGate, report: Report) -> None:
    """Execute both halves of DEBT-020 and print what the rule that reads `filters` is
    worth.

    The same method as `check_the_numbers_differ` and, since Sub-step 5.5, the same
    conclusion: two numbers that justify a rejection the Gate makes. While the entry
    stood open these two measured a rejection it did **not** make, and the figures are
    the reason it had to start — a rule is only worth having if the thing it refuses
    returns a different answer, and a gap nobody has run is a claim.

    It goes on running after the payment rather than being deleted with it, and it fails
    the run if the two stop being apart. A paid entry whose evidence was thrown away is
    an entry nobody can re-check, and this rule's probe would then be a name rather than
    a measurement.
    """
    certified = total(
        gate.warehouse.query(statement_for(gate, "Realised P&L", with_filters=True))
    )
    unfiltered = total(
        gate.warehouse.query(statement_for(gate, "Realised P&L", with_filters=False))
    )
    difference = gap(certified, unfiltered)
    report.say(
        f"DEBT-020: Realised P&L is {certified:.2f} with its certified filter and "
        f"{unfiltered:.2f} with it dropped — {difference:.2f}% apart, and the Gate "
        f"now allows only the first"
    )
    if difference < MIN_GAP:
        problems.append(
            f"Realised P&L returns the same number with and without its certified "
            f"filter ({difference:.6f}% apart), so DEBT-020 has stopped costing "
            f"anything on this data and the entry should be re-read rather than carried"
        )


def shapes(gate: ValidationGate) -> tuple[RouteProbe, ...]:
    """Every shape this module puts in front of the Gate, in the order it reports them.

    Three families, and they are one tuple so that no check below can read a different
    set from the one `judge_probes` declared verdicts for: the statements written down
    in `PROBES`, the period pair built from the Snapshot calendar, and the DEBT-020 pair
    built from the corpus.
    """
    return PROBES + period_probes(gate.warehouse) + filter_probes(gate)


def period_probes(warehouse: WarehouseAdapter) -> tuple[RouteProbe, ...]:
    """The date half, over a period read from the Snapshot calendar.

    Two statements that differ in one identifier. Both compute `Gross Revenue`'s
    certified expression across its certified Join Path; one keys the period on
    `fct_trade.trade_date`, which is what the Metric Definition certifies, and the other
    on `fct_trade.settlement_date`, which is the other half of a
    [Glossary Section C](../../docs/glossary.md#c-distinctions-we-must-not-blur) pair.

    The statement is a template held as a **string literal** with the two dates
    substituted in, rather than assembled out of pieces, so that
    `check_warehouse.py`'s dialect scan still reads it: a quoted `'{start}'` parses as
    the string literal it will become. The dates cannot be bound parameters, because the
    bounded-read rule hands the statement to the planner and an unbound placeholder is a
    statement the planner will not plan.

    **Both halves carry the access route and the access predicate**, added in Sub-step
    5.5 along with the rule that requires them. The pair is the only one in this module
    whose positive half has to stay allowed by the **Gate** rather than only by this
    rule — it is what says the date rule is not refusing every question that names a
    period — so the two statements gained one join pair and one conjunct each, and go on
    differing in exactly one identifier. It moves the two figures printed below, because
    they are now the region the Access Profile permits rather than every region; both
    are read from the same run and the gap between them is the same gap.
    """
    start, end = snapshot_period(warehouse)
    template = (
        "SELECT sum(billed.commission * rate.fx_rate) AS gross_revenue "
        "FROM fct_trade AS billed "
        "JOIN fct_fx_rate AS rate "
        "  ON rate.rate_date = billed.trade_date "
        " AND rate.from_currency = billed.denomination_currency "
        " AND rate.to_currency = 'EUR' "
        "JOIN dim_account AS account "
        "  ON account.account_id = billed.account_id "
        "JOIN dim_client AS client "
        "  ON client.client_id = account.client_id "
        "WHERE client.client_region = '{region}' "
        "  AND billed.{keyed_on} BETWEEN '{start}' AND '{end}'"
    )
    template = template.replace("{region}", ANALYST.permitted_region)
    return (
        RouteProbe(
            name="a period keyed on Trade Date",
            sql=template.format(keyed_on="trade_date", start=start, end=end),
            verdict=ALLOWED,
            why="the period keyed on the column `Gross Revenue`'s Metric Definition "
                "names in `date_column`. It has to be allowed, or the rule below is "
                "refusing every question that names a period",
        ),
        RouteProbe(
            name="a period keyed on Settlement Date",
            sql=template.format(keyed_on="settlement_date", start=start, end=end),
            verdict=REJECTED,
            reasons=(RejectionReason.UNCERTIFIED_DATE_COLUMN,),
            stray_dates=True,
            why="the same statement, keyed on the other half of the Section C pair. "
                "Commission is earned on Trade Date and collected on Settlement Date, "
                "so this shifts revenue across the period boundary — and both columns "
                "sit on `fct_trade`, so the projection, the joins and the row count of "
                "the FROM clause are all identical. **This is the half DEBT-014's "
                "status note called argued rather than measured**, and the two numbers "
                "are printed below",
        ),
    )


def snapshot_period(warehouse: WarehouseAdapter) -> tuple[date, date]:
    """A quarter, as two dates the Snapshot calendar actually holds.

    The first Snapshot date, and the last one within a quarter of it. Read rather than
    written down, which is what keeps
    [DEBT-012](../../docs/debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)'s
    third arm unfired: *"the first 'as of' date chosen by anything but the Snapshot
    calendar"* is the Trigger, and neither of these was chosen by this file.

    `fct_position_snapshot` is the calendar `check_semantic_layer.py` holds both Snapshot
    tables to, so asking either gives the same answer and asking this one keeps the
    question in one place.
    """
    dates = [
        row[0]
        for row in warehouse.query(
            "SELECT DISTINCT snapshot_date FROM fct_position_snapshot "
            "ORDER BY snapshot_date"
        )
    ]
    if not dates:
        raise SystemExit(
            "fct_position_snapshot is empty, so there is no Snapshot calendar to read a "
            "period out of — run `uv run python -m veritas.ingestion` first"
        )
    start = dates[0]
    within = [held for held in dates if held <= start + QUARTER]
    return start, within[-1]


def rule_name(gate: ValidationGate, access_profile: AccessProfile) -> str:
    """This rule's name, read off the Gate's own rule list rather than typed here.

    `probes.rule_named` is where the reading lives, as of Sub-step 5.5: this file,
    `restricted.py` and `access.py` each need it and three near-copies of one lookup is
    three things to keep in step. What is left here is which rule this module is about.
    """
    return rule_named(gate, ValidationGate.routed, access_profile)


def total(rows: list[tuple[object, ...]]) -> Decimal:
    """The one figure a one-row, one-column probe returns.

    A `Decimal` all the way, never a float: the Warehouse stores money as
    `DECIMAL(18, 6)` for the reason ADR-0002 rejected SQLite, and a check that compared
    two monetary totals through binary floating point would be committing the error it
    is measuring.
    """
    if len(rows) != 1 or len(rows[0]) != 1:
        raise SystemExit(
            f"a probe meant to return one number returned {len(rows)} row(s) — the "
            f"comparison below has nothing to compare"
        )
    return Decimal(str(rows[0][0]))


def gap(left: Decimal, right: Decimal) -> Decimal:
    """How far apart two figures are, as a percentage of the larger."""
    largest = max(abs(left), abs(right))
    return Decimal(0) if not largest else abs(left - right) / largest * 100


def check_the_numbers_differ(warehouse: WarehouseAdapter, report: Report) -> None:
    """Execute both Section C pairs and print what each rejection is worth.

    **This is the whole reason the rule exists**, and neither half is asserted. A
    rejection of a statement that returns the same number as the certified one would be a
    rejection nobody is better off for, so both pairs are run and both gaps are printed;
    a pair that stops differing by more than `MIN_GAP` fails the run, because at that
    point this file is refusing a statement it can no longer show is wrong.

    The Gate never executes anything — `VALIDATE` is step 5 of the flow and `EXECUTE` is
    step 6. This is a check, it holds the adapter, and running the two statements is the
    only way the numbers exist.
    """
    start, end = snapshot_period(warehouse)
    report.say(
        f"Snapshot calendar: the period is {start} to {end}, both read from "
        f"fct_position_snapshot (DEBT-012's third arm stays unfired)"
    )

    pairs = (
        (
            "Traded Notional",
            "through the Quotation Currency",
            from_the_spike("traded notional"),
            "through the Denomination Currency",
            from_the_spike("notional through the wrong currency"),
        ),
        (
            "Gross Revenue",
            f"keyed on trade_date, {start} to {end}",
            probe_named(period_probes(warehouse), "a period keyed on Trade Date"),
            "keyed on settlement_date, same period",
            probe_named(
                period_probes(warehouse),
                "a period keyed on Settlement Date",
            ),
        ),
    )
    for metric, right_label, right_sql, wrong_label, wrong_sql in pairs:
        certified = total(warehouse.query(right_sql))
        off_route = total(warehouse.query(wrong_sql))
        difference = gap(certified, off_route)
        report.say(
            f"{metric}: {certified:.2f} {right_label} · {off_route:.2f} "
            f"{wrong_label} — {difference:.2f}% apart"
        )
        if difference < MIN_GAP:
            problems.append(
                f"the two ways of computing {metric} differ by {difference:.6f}%, which "
                f"is under {MIN_GAP}% — the Gate is refusing a statement this run can "
                f"no longer show returns a different answer, and a rejection that costs "
                f"a user a query and buys them nothing is worse than no rule"
            )


def probe_named(probes: tuple[RouteProbe, ...], name: str) -> str:
    """One probe's statement, by name, so the executed pair and the judged pair are one
    text."""
    for probe in probes:
        if probe.name == name:
            return probe.sql
    raise SystemExit(f"no probe named {name!r} — the pair above would compare nothing")


def check_the_route_reading(gate: ValidationGate, report: Report) -> None:
    """Read every probe's route beside its metric's, and compare both with what was
    declared.

    `judge_probes` reports what a caller gets. This reports what **this rule** reads, on
    every shape including the ones an earlier rule refuses — the joins the statement
    carries that nothing certifies, the certified joins it left out, and the date columns
    it filters on that its metric is not certified over.

    Neither reading is assumed. A statement declared off-route that reads as on-route is
    a hole; one declared on-route that reads as off-route is the false positive that
    makes a Gate unusable, and `net revenue by region` is here precisely because this
    Sub-step ships one of those knowingly.
    """
    schema = gate.warehouse.columns_by_table()
    report.say(
        f"{'route':<10}{'dates':<10}{'shape':<38}what this rule reads"
    )
    for probe in shapes(gate):
        try:
            resolved = resolve(probe.sql, schema)
            carried = route_of(probe.sql, schema)
            filtered = date_columns_filtered(resolved, schema)
            hit = gate.traced_metrics(read_for(gate, probe.sql))
        except TracerRefused as refusal:
            problems.append(
                f"the route {probe.name!r} takes could not be read ({refusal}) — its "
                f"reading is a refusal rather than the measurement declared here"
            )
            continue

        metrics = [gate.semantic.metrics[name] for name in hit]
        axes = gate.axes_sliced_by(grouped_columns(resolved))
        # **Permitted and required are two Routes since Sub-step 5.5**, and this reading
        # asks each of them the question it can answer: a join beyond what the corpus
        # permits — the metric's own route, the axes the statement slices by, and the
        # access route — is a join nothing certifies, and a join absent from what the
        # metric *requires* is one the statement dropped. Reading both against one Route
        # would report every scoped statement as missing the joins it was never obliged
        # to carry.
        permitted = gate.permitted_route(metrics, axes, schema) if hit else None
        required = gate.required_route(metrics, schema) if hit else None
        certified_dates = {
            tuple(metric.date_column.split(".", 1)) for metric in metrics
        }
        beyond = carried.joins_beyond(permitted) if permitted else []
        absent = required.joins_beyond(carried) if required else []
        stray = sorted(
            f"{table}.{column}" for table, column in filtered - certified_dates
        )
        off_route = bool(beyond or absent) or (
            required is not None and carried.from_tables != required.from_tables
        )

        detail = f"{', '.join(hit) or 'no certified metric'}"
        if beyond:
            detail += f" · {len(beyond)} join(s) nothing certifies"
        if absent:
            detail += f" · {len(absent)} certified join(s) absent"
        if stray:
            detail += f" · filtered on {', '.join(stray)}"
        report.say(
            f"{'OFF' if off_route else 'on':<10}{'STRAY' if stray else '—':<10}"
            f"{probe.name:<38}{detail}"
        )

        if probe.off_route != off_route:
            problems.append(
                f"{probe.name!r} was measured as "
                f"{'off' if probe.off_route else 'on'} its metric's route and reads as "
                f"{'off' if off_route else 'on'} it. {probe.why}"
            )
        if probe.stray_dates != bool(stray):
            problems.append(
                f"{probe.name!r} was measured as "
                f"{'filtering' if probe.stray_dates else 'not filtering'} on a date "
                f"column its metric does not certify and now "
                f"{'does' if stray else 'does not'}. {probe.why}"
            )


def read_for(gate: ValidationGate, sql: str) -> Reading:
    """One `Reading` of a statement, built the way `judge` builds one.

    This module asks the Gate what a statement traces to without asking it for a verdict,
    and `traced_metrics` takes the `Reading` because that is where the catalogue, the
    resolved tree and the corpus are read once per judgement. Building one here rather
    than calling a second entry point keeps this file reading exactly what the rule
    reads.
    """
    return read(
        sql,
        catalogue=gate.catalogue,
        certified_expressions={
            name: metric.expression for name, metric in gate.semantic.metrics.items()
        },
    )


def check_every_certified_metric_stays_on_its_route(
    gate: ValidationGate, rule: str, report: Report
) -> None:
    """All nine Certified Metrics, computed the way their own entries say, are allowed
    here.

    The positive control this rule needs: a rule that rejects everything passes every
    rejection probe above. Each metric's statement is built from its own `from_table`,
    its own `join_paths` and its own `filters` — `probes.certified_statement`, the same
    construction `traces.py` and `access.py` use, which is what makes this nine probes
    rather than nine more literals to keep in step with `semantic/`.

    **Since Sub-step 5.5 the statement is also scoped**, and that is what keeps this a
    control at the Gate's level rather than only at this rule's: an unscoped statement is
    refused one rule later, so nine unscoped probes would say nothing about whether *this*
    rule allows a certified metric. What is compared against them is `required_route` —
    the metric's own joins — because the access route is permission the statement takes
    and not an obligation the Metric Definition carries.

    What is printed is this rule's own reading rather than the verdict: how many joins
    each statement is required to carry, and how many it is permitted. `Position Change`
    is the one worth looking at — its own route is no joins at all and its expression
    holds a correlated subquery with a `FROM` and a `WHERE` of its own, so it is the
    metric that proves the route and the date readings walk every scope rather than only
    the outermost one.
    """
    ran = allowed = 0
    for name, metric in sorted(gate.semantic.metrics.items()):
        sql = certified_statement(gate, name, ANALYST)
        outcome = gate.judge(sql, ANALYST)
        if rule in outcome.rules:
            ran += 1
            allowed += outcome.allowed
        if not outcome.allowed:
            problems.append(
                f"{name} computed the way its own Metric Definition says is rejected by "
                f"the Gate at {outcome.rules[-1]!r}: {outcome.explanation}\n      {sql}"
            )
        schema = gate.warehouse.columns_by_table()
        required = gate.required_route([metric], schema)
        permitted = gate.permitted_route([metric], (), schema)
        report.say(
            f"{name:<20}{len(required.joins)} required · {len(permitted.joins)} "
            f"permitted join(s) · keyed on {metric.date_column} · "
            f"{len(metric.filters)} certified filter(s) · starts at "
            f"{', '.join(sorted(required.from_tables))}"
        )
    report.say(
        f"this rule ran on {ran} of {len(gate.semantic.metrics)} Certified Metrics and "
        f"allowed {allowed} of them"
    )
    if allowed != len(gate.semantic.metrics):
        problems.append(
            "this rule refused a Certified Metric computed exactly as its own entry "
            "says, so what it is enforcing is not what the corpus certifies"
        )


def check_this_rule_ran(gate: ValidationGate, rule: str, report: Report) -> None:
    """Which of the shapes above this rule decided, and which an earlier rule did.

    Two rules disagreeing about one statement is the clearest evidence they ask different
    questions, and the reverse matters as much: a probe written for this rule that is
    refused three rules earlier is measuring the earlier rule. The run says which rather
    than leaving it to be assumed.
    """
    judged = shapes(gate)
    decided = 0
    for probe in judged:
        outcome = gate.judge(probe.sql, ANALYST)
        if rule not in outcome.rules:
            problems.append(
                f"{probe.name!r} never reached {rule!r} — it was refused at "
                f"{outcome.rules[-1]!r}, so this module is measuring another rule"
            )
            continue
        decided += not outcome.allowed and outcome.rules[-1] == rule
    report.say(
        f"this rule ran on every one of the {len(judged)} shapes above and reached "
        f"the verdict on {decided} of them"
    )


def check(warehouse: WarehouseAdapter) -> Report:
    """Everything this module has to say, in one report."""
    report = Report("the metric's own route, and its own period")
    gate = ValidationGate(warehouse)
    rule = rule_name(gate, ANALYST)
    if not rule:
        problems.append(
            "the Gate's rule list holds no entry for `routed`, so nothing below is "
            "judging the rule this module exists to check"
        )
    check_the_numbers_differ(warehouse, report)
    check_the_filter_gap(gate, report)
    report.say("")
    judge_probes(gate, shapes(gate), report, ANALYST)
    report.say("")
    check_the_route_reading(gate, report)
    report.say("")
    check_every_certified_metric_stays_on_its_route(gate, rule, report)
    check_this_rule_ran(gate, rule, report)
    return report
