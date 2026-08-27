"""Sub-step 5.1's rules: a statement is read at all, is one statement, is a read, and
stays inside the scan ceiling.

The first of the five modules
[R8](../../docs/plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)
lays out, one per Gate rule. It covers three things beyond putting probes in front of
the Gate, and each is a claim the plan makes that would otherwise be prose:

  * **The rules that need nothing consult nothing.** Every read-only shape is judged a
    second time through a Gate whose Warehouse raises on contact. The plan's ordering
    argument is that a rule needing nothing *"still returns the right verdict on a day
    the corpus will not load or the Warehouse will not open"* — and *"an error is not a
    rejection: a caller can act on 'this statement writes to the Warehouse' and cannot
    act on 'the Gate did not get far enough to say.'"*
  * **Why the order is a safety property.** `EXPLAIN` does not neuter a string holding
    two statements: the engine plans the first and executes the rest. That is performed
    on a throwaway table in an in-memory Warehouse rather than asserted, because a
    footgun described in a docstring is a footgun somebody reorders the rules past.
  * **The planner's estimate is really being read.** If the plan format moves under
    this project, `estimated_scan_rows` returns zero and the bounded-read rule silently
    allows everything — a rule that fails **open**. One positive control against a real
    table's real row count is what makes that loud.

It also holds the payment probes for
[DEBT-016](../../docs/debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type),
which this Sub-step fires and pays.
"""

import tempfile
from pathlib import Path

from probes import (
    REJECTED,
    Probe,
    Report,
    judge_probes,
    problems,
)

from veritas.validation import (
    SCAN_CEILING,
    RejectionReason,
    ValidationGate,
    trusted_rewrite_names,
)
from veritas.warehouse import WarehouseAdapter, WarehouseError

# A table this check creates and destroys, in an in-memory Warehouse that never
# touches the real one. Named so that a reader who finds it anywhere else knows a
# probe leaked.
THROWAWAY_TABLE = "gate_probe"

# The largest factor by which the engine's estimate may differ from the true row
# count before the positive control below calls it a finding. An estimate is an
# estimate and is allowed to be one; what this catches is the estimate not being read
# at all, which shows up as zero. Both numbers are printed either way.
ESTIMATE_TOLERANCE = 2

# The two statements the measurement below runs to show what the estimate does and
# does not count. They are here rather than inline because the cross-product probe
# judges the same string, and two copies of a probe statement can drift apart.
CROSS_PRODUCT = "SELECT * FROM fct_trade AS left_side, fct_trade AS right_side"
COUNTED_FROM_METADATA = "SELECT count(*) FROM fct_trade"
ORDINARY_QUESTION = "SELECT count(*) FROM fct_trade WHERE fct_trade.trade_side = 'buy'"

# This module's four rules, by the names `ValidationGate.rules()` gives them. Named
# here because that list grows: every Sub-step of Step 005 appends to it, and the
# positive control below asks whether **these** rules allowed a statement, not whether
# the whole Gate did.
THESE_RULES = ("parses", "one statement", "a read", "bounded")

# The six shapes read-only has to cover, then the parse failure C6 requires a rule
# for, then the boundedness cases, then the two statements **these** rules allow.
#
# Every probe here now declares `rejected`, and that is not a Gate refusing everything:
# the last two are refused by Sub-step 5.2's tracing rule, one rule past this module's
# four. `check_these_rules_allow_them` is what says so, by reading which rules ran
# rather than which verdict came back — because a Gate that rejects everything passes
# every rejection probe, and after 5.2 no statement this module can write is allowed
# end to end without also being a Certified Metric.
#
# Every statement here is a string literal inside `.claude/scripts/`, which is one of
# `check_warehouse.py`'s scanned roots, so the dialect scan Sub-step 2.6 built reads
# each one it can parse as a statement. Under
# [R3 of Step 003](../../docs/plan/step-003-validation-feasibility.md#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15)
# this file passes that scan **without claiming an exemption**.
PROBES = (
    Probe(
        name="drop a table",
        sql="DROP TABLE fct_trade",
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_READ,),
        why="Data Definition Language (DDL) — the shape everyone thinks of first, "
            "and the one a Gate that only looked for INSERT would pass",
    ),
    Probe(
        name="write to a table",
        sql="INSERT INTO fct_trade VALUES (1)",
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_READ,),
        why="a write to the Warehouse: the answer to a question must never change "
            "what the next question is answered from",
    ),
    Probe(
        name="write to the filesystem",
        sql="COPY (SELECT 1) TO 'leak.csv'",
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_READ,),
        why="the shape worth naming — it reads nothing it should not and writes the "
            "answer somewhere no reader of a Grounded Answer will ever see it, so "
            "read-only has to mean the filesystem as well as the Warehouse",
    ),
    Probe(
        name="engine introspection",
        sql="PRAGMA database_list",
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_READ,),
        why="not a query over the star schema at all — it asks the engine about "
            "itself, which is a question Veritas does not answer",
    ),
    Probe(
        name="a second database",
        sql="ATTACH 'elsewhere.duckdb'",
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_READ,),
        why="reaches outside the Warehouse entirely, so every rule that reads the "
            "live schema would be reading the wrong one",
    ),
    Probe(
        name="two statements",
        sql="SELECT 1; SELECT 2",
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_SINGLE_STATEMENT,),
        why="the shape a per-statement rule cannot see: each half is a read and the "
            "string is whatever its tail says. `sqlglot.parse_one` returns one Block "
            "node here, which is why the Gate parses with `parse`",
    ),
    Probe(
        name="a union",
        sql="SELECT 1 UNION SELECT 2",
        verdict=REJECTED,
        reasons=(RejectionReason.NOT_A_READ,),
        why="a read that is refused on purpose: nothing in `semantic/` needs a UNION, "
            "and fail-closed on a shape with no use costs a rejection message where "
            "the other reading costs a hole. Admitting it later is one isinstance "
            "and this probe's verdict flipping",
    ),
    Probe(
        name="not sql at all",
        sql="the quarterly revenue please",
        verdict=REJECTED,
        reasons=(RejectionReason.UNPARSEABLE,),
        why="C6, by a rule rather than by accident — the constraint the spike is "
            "measured to miss, where gibberish is refused because it yields no "
            "projections rather than because anything says so",
    ),
    Probe(
        name="over the ceiling",
        sql="SELECT * FROM fct_trade",
        verdict=REJECTED,
        reasons=(RejectionReason.UNBOUNDED_SCAN,),
        ceiling=10,
        why="the bounded read, given teeth by lowering the ceiling rather than by "
            "building a query big enough to trip the real one — the rule under test "
            "is the comparison, and the other way round measures the Warehouse's size",
    ),
    Probe(
        name="engine will not plan it",
        sql="SELECT nope FROM fct_trade",
        verdict=REJECTED,
        reasons=(RejectionReason.UNBOUNDED_SCAN,),
        why="a planner that will not say how much a statement reads has not said it "
            "is bounded. Expressible only because DEBT-016 was paid here: a bare "
            "`except Exception` would have called a broken adapter a bad query",
    ),
    Probe(
        name="a cross product",
        sql=CROSS_PRODUCT,
        verdict=REJECTED,
        reasons=(RejectionReason.NO_METRIC_EXPRESSION,),
        why="the bounded read's measured blind spot, declared rather than discovered: "
            "the estimate counts rows read off a table, and a join makes its rows "
            "instead of reading them, so this scans each side once and returns the "
            "square. `check_the_estimate_does_not_count` prints both numbers and "
            "`check_these_rules_allow_them` proves the bounded rule still passes it. "
            "**The rejection arrives from Sub-step 5.2's tracing rule, not from this "
            "module's**, and it does not close the blind spot: this statement selects "
            "columns, so it computes no metric — a cross product that computed a "
            "certified one would still be allowed here. Bounding that is the "
            "certified-route rule's job in Sub-step 5.4",
    ),
    Probe(
        name="an ordinary question",
        sql=ORDINARY_QUESTION,
        verdict=REJECTED,
        reasons=(RejectionReason.SHADOW_METRIC,),
        why="a question an analyst would call ordinary and the Semantic Layer does "
            "not certify: `Trade Count` is `count(fct_trade.trade_id)`, so `count(*)` "
            "is a paraphrase, and "
            "[C1](../../docs/design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes) "
            "chose a pasteable form over a Gate that decides which paraphrases are "
            "safe. Sub-step 5.1 declared this `allowed` because nothing then judged "
            "an expression; Sub-step 5.2's tracing rule is what refuses it. The "
            "positive control it used to be is now `check_these_rules_allow_them` "
            "below, and the nine Certified Metrics in `traces.py`",
    ),
)


class WarehouseThatWillNotOpen:
    """A stand-in for the Warehouse Adapter that raises the moment anything asks it
    anything.

    Not a mock of the adapter — it implements none of it. It exists to make one claim
    mechanical: the rules that need nothing **touch** nothing. A Gate built on this
    still returns the right verdict for every shape a read-only rule judges, and the
    day it stops doing so this check fails with the attribute that was reached for.
    """

    def __getattr__(self, name: str) -> object:
        raise AssertionError(
            f"a rule that needs no Warehouse reached for {name!r} — the read-only "
            f"rules must return a verdict on a day the Warehouse will not open, and "
            f"an error is not a rejection"
        )


def check_probes(gate: ValidationGate, report: Report) -> None:
    """Every probe, judged against the verdict this Sub-step measured for it."""
    judge_probes(gate, PROBES, report)


def check_rules_that_need_nothing(gate: ValidationGate, report: Report) -> None:
    """The probes decided before the bounded rule are decided without a Warehouse.

    Which probes those are is read off the real outcome — the rules that ran — rather
    than listed here, so a probe that starts needing the engine is noticed instead of
    being quietly re-listed. A probe that does reach the bounded rule is skipped: it
    is *supposed* to need a Warehouse, and asking it to work without one would be
    checking the opposite claim.
    """
    blind = ValidationGate(WarehouseThatWillNotOpen())  # type: ignore[arg-type]
    judged = 0
    for probe in PROBES:
        real = gate.judge(probe.sql)
        if "bounded" in real.rules:
            continue
        judged += 1
        blinded = blind.judge(probe.sql)
        # Against the real verdict rather than the declared one, so this reports only
        # what it is about — a rule that turned out to need a Warehouse. A probe whose
        # declared verdict has moved is `judge_probes`'s finding and is reported there,
        # once.
        if (blinded.allowed, blinded.reasons) != (real.allowed, real.reasons):
            problems.append(
                f"{probe.name!r} is decided before the bounded rule and came back "
                f"differently through a Warehouse that raises on contact — so a rule "
                f"that is supposed to need nothing needs one, and a caller loses the "
                f"verdict on the day it most needs it\n      {probe.sql}"
            )
    report.say(
        f"{judged} probe(s) reached the same verdict through a Warehouse that raises "
        f"on contact"
    )


def check_explain_executes_the_tail(report: Report) -> None:
    """`EXPLAIN` plans the first statement and executes the rest. Performed, not asserted.

    This is why `one_statement` is ordered ahead of `bounded` rather than beside it.
    Done to a throwaway table in an in-memory Warehouse, which is the fixture pattern
    `check_warehouse.py`'s fourteen constraint rejections already use: a claim about
    what an engine does is worth nothing until the engine has done it.
    """
    with WarehouseAdapter.in_memory() as throwaway:
        throwaway.execute("CREATE TABLE gate_probe (a INTEGER)")
        if THROWAWAY_TABLE not in throwaway.tables():
            problems.append(
                "the throwaway table was not created, so the probe below proves nothing"
            )
            return
        try:
            throwaway.estimated_scan_rows(f"SELECT 1; DROP TABLE {THROWAWAY_TABLE}")
        except WarehouseError:
            # Expected, and it is the second half of the finding: the engine hands
            # back the *last* statement's result, and a DROP returns no rows, so the
            # adapter has no plan to read. The refusal arrives after the damage.
            pass
        survived = THROWAWAY_TABLE in throwaway.tables()
    report.say(
        f"asking the engine to plan a two-statement string "
        f"{'left the table alone' if survived else 'dropped the table'} — "
        f"so the single-statement rule runs "
        f"{'before it by preference' if survived else 'before it or not at all'}"
    )
    if survived:
        problems.append(
            "asking the engine to plan `SELECT 1; DROP TABLE ...` left the table "
            "standing, so the reason this project orders the single-statement rule "
            "ahead of the bounded-read rule no longer holds. That is good news and it "
            "is still a finding: the docstrings in `estimated_scan_rows` and `gate.py` "
            "cite this measurement, and a citation to something that has stopped "
            "being true is worse than no citation"
        )


def check_the_estimate_is_read(warehouse: WarehouseAdapter, report: Report) -> None:
    """The planner's estimate against a real row count, and the ceiling's headroom.

    Without this the bounded rule fails **open**: a plan format that moved would give
    `estimated_scan_rows` nothing to find, and nothing to find sums to zero, and zero
    is under every ceiling. The comparison is loose on purpose — an estimate is
    allowed to be an estimate — and tight enough to catch the number not being read.

    The headroom beside it is a measurement, so it is printed on every run rather than
    written into `gate.py`: `SCAN_CEILING` is a policy and stays a policy when the
    Warehouse grows.
    """
    counted = warehouse.row_count("fct_position_snapshot")
    estimated = warehouse.estimated_scan_rows("SELECT * FROM fct_position_snapshot")
    report.say(
        f"planner estimate {estimated} against {counted} rows actually in "
        f"fct_position_snapshot"
    )
    if not counted:
        problems.append(
            "fct_position_snapshot is empty, so the positive control below compares "
            "nothing — run `uv run python -m veritas.ingestion`"
        )
    elif not estimated or not (
        counted / ESTIMATE_TOLERANCE <= estimated <= counted * ESTIMATE_TOLERANCE
    ):
        problems.append(
            f"the engine's estimate for a full scan of fct_position_snapshot is "
            f"{estimated} where the table holds {counted} rows. The bounded-read rule "
            f"fails open when the estimate cannot be found: an unread plan sums to "
            f"zero and zero is under every ceiling"
        )
    biggest = max(warehouse.row_count(table) for table in warehouse.tables())
    report.say(
        f"scan ceiling {SCAN_CEILING} against a largest table of {biggest} rows — "
        f"headroom {SCAN_CEILING / biggest:.0f}x"
    )


def check_the_estimate_does_not_count(
    warehouse: WarehouseAdapter, report: Report
) -> None:
    """The two things the estimate leaves out, printed as numbers rather than prose.

    `estimated_scan_rows` sums what the plan says each table scan reads. Two ordinary
    statements fall outside that sum, and both are printed because both are figures a
    later plan format or a refreshed Warehouse can move — a limit described in a
    docstring stops being true without anything failing.

    Neither is a defect in the rule. The scan is the quantity the
    [Target State](../../docs/design/target-state.md#flow) bounds, and it is the
    quantity the BigQuery dry run this swaps for bills. What the numbers show is where
    the ceiling is not the whole answer, which is Sub-step 5.4's rule.
    """
    rows = warehouse.row_count("fct_trade")
    if not rows:
        problems.append(
            "fct_trade is empty, so the two figures below compare nothing — run "
            "`uv run python -m veritas.ingestion`"
        )
        return

    scanned = warehouse.estimated_scan_rows(CROSS_PRODUCT)
    report.say(
        f"a cross product of fct_trade with itself estimates {scanned} scanned "
        f"against {rows * rows} rows returned — the estimate counts what is read, "
        f"not what a join makes from it"
    )
    if scanned >= rows * rows:
        problems.append(
            f"the estimate for a cross product of fct_trade with itself is {scanned}, "
            f"which is no longer below the {rows * rows} rows it returns — the blind "
            f"spot this probe and Sub-step 5.1's review declare has changed shape. "
            f"Good news, and still a finding: the declaration is now wrong"
        )

    counted = warehouse.estimated_scan_rows(COUNTED_FROM_METADATA)
    report.say(
        f"{COUNTED_FROM_METADATA} estimates {counted} — a real answer off a table of "
        f"{rows} rows, and the same number an unread plan would give"
    )
    if counted:
        problems.append(
            f"`{COUNTED_FROM_METADATA}` now estimates {counted} rather than zero, so "
            f"Sub-step 5.1's review is wrong to say a zero estimate can be honest. "
            f"That makes a zero estimate a stronger signal than it was, which is a "
            f"reason to revisit the fail-open reasoning rather than to leave it"
        )


def check_engine_refusal_is_named(warehouse: WarehouseAdapter, report: Report) -> None:
    """DEBT-016's payment, exercised in both directions.

    The entry's cost was a diagnosis rather than a verdict: *"an adapter that cannot
    open the Warehouse at all, prints as 'the engine refused the query below'"*. So
    both halves are probed — the engine refusing a caller's SQL is a `WarehouseError`
    with the engine's own exception kept as its cause, and a Warehouse that will not
    open is **not** one, because it fails in the constructor where no rule catches it.
    """
    try:
        warehouse.query("SELECT nope FROM fct_trade")
    except WarehouseError as refusal:
        report.say(
            f"the engine refusing a caller's SQL raises WarehouseError, caused by "
            f"{type(refusal.__cause__).__name__}"
        )
        if refusal.__cause__ is None:
            problems.append(
                "WarehouseError was raised without the engine's own exception as its "
                "cause, so a reader who needs the DuckDB class name can no longer get "
                "it by asking"
            )
    else:
        problems.append(
            "the engine accepted a column that does not exist, so the probe proves "
            "nothing"
        )

    with tempfile.TemporaryDirectory() as directory:
        not_a_database = Path(directory) / "not-a-database.duckdb"
        not_a_database.write_text("this is not a database\n")
        try:
            WarehouseAdapter(not_a_database).close()
        except WarehouseError:
            problems.append(
                "a Warehouse that will not open raised WarehouseError, so the type "
                "no longer separates the two things DEBT-016 was opened about: a "
                "query the engine refused, and a broken installation"
            )
        except Exception as failure:  # noqa: BLE001 — the point is that it is not ours
            report.say(
                f"a Warehouse that will not open raises {type(failure).__name__} from "
                f"the constructor, which no rule catches"
            )
        else:
            problems.append(
                "a file that is not a database opened as one, so the probe proves "
                "nothing"
            )


def check_these_rules_allow_them(gate: ValidationGate, report: Report) -> None:
    """The two statements this module's rules pass, and a later rule refuses.

    A Gate that rejects everything passes every rejection probe, so a rule module
    needs a statement its own rules **allow**. Both of the two here were declared
    `allowed` in Sub-step 5.1 and are rejected by Sub-step 5.2's tracing rule, which
    is the Gate getting stricter rather than either verdict being wrong — and it will
    keep happening, because every Sub-step of Step 005 appends a rule.

    So the control is written as the property it always meant: **none of this
    module's four rules rejected the statement.** `ValidationGate` stops at the first
    rejection and reports the rules that actually ran, which is exactly what makes
    that answerable — the field exists for a reader who *"wants to know what a verdict
    covers rather than assuming"*, and this is that reader. It survives 5.3, 5.4 and
    5.5 without an edit.
    """
    for sql in (CROSS_PRODUCT, ORDINARY_QUESTION):
        outcome = gate.judge(sql)
        ran = set(outcome.rules)
        missing = [rule for rule in THESE_RULES if rule not in ran]
        report.say(
            f"all {len(THESE_RULES)} rules here ran on `{sql[:44]}…` and none "
            f"rejected it — refused later by {', '.join(outcome.rules[len(THESE_RULES):]) or 'nothing'}"
            if not missing
            else f"`{sql[:44]}…` was stopped inside this module"
        )
        if missing:
            problems.append(
                f"`{sql}` was rejected by one of this module's own rules — it "
                f"reached {list(outcome.rules)} and never reached {missing}. These "
                f"two statements are the only evidence that the read-only, "
                f"single-statement and bounded rules are not simply refusing "
                f"everything put in front of them: {outcome.explanation}"
            )


def check(warehouse: WarehouseAdapter) -> Report:
    """Everything this module has to say, in one report."""
    report = Report("read-only, single, parseable, bounded")
    report.say(
        f"trusted rewrites: {', '.join(trusted_rewrite_names())} — "
        f"sqlglot's optimize() runs fourteen"
    )
    gate = ValidationGate(warehouse)
    check_probes(gate, report)
    check_these_rules_allow_them(gate, report)
    check_rules_that_need_nothing(gate, report)
    check_explain_executes_the_tail(report)
    check_the_estimate_is_read(warehouse, report)
    check_the_estimate_does_not_count(warehouse, report)
    check_engine_refusal_is_named(warehouse, report)
    return report
