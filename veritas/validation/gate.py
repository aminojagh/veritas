"""The Validation Gate — the deterministic checks a generated query passes before it
executes.

[ADR-0003](../../.claude/docs/adr/0003-validation-gate-is-deterministic-code.md)
decided what this is: code over a parse tree, and *"no LLM participates in the
decision to allow or reject a query."*
[Step 003](../../.claude/docs/design/validation-feasibility.md) spent five Sub-steps
measuring whether that is possible on this schema and this data, and returned **GO**.
This module is the thing that was measured for.

**Five rules, and Sub-step 5.1 ships the first three plus the fourth's cost bound.**
The [Target State's flow](../../.claude/docs/design/target-state.md#flow) names what
`VALIDATE` decides; the [Step 005 plan](../../.claude/docs/plan/step-005-validation-gate.md#what-the-gate-must-decide)
puts them in the order a statement meets them. What is here now is everything that
needs neither the Semantic Layer nor a certified metric: can this be read at all, is
it one statement, is it a read, and will it stay inside the scan ceiling.

**The order is a safety property, not a speed one.** Two things depend on it.

  * A rule that needs nothing returns the right verdict on a day the corpus will not
    load or the Warehouse will not open. `check_validation_gate` proves that by
    judging every read-only shape through a Gate whose Warehouse raises on contact:
    an error is not a rejection, and a caller can act on *"this statement writes"*
    where it cannot act on *"the Gate did not get far enough to say."*
  * The bounded-read rule hands the engine the caller's own text. DuckDB executes
    every statement after the first in such a string **even under `EXPLAIN`** — see
    `WarehouseAdapter.estimated_scan_rows`, and the probe that drops a throwaway
    table to prove it. So the single-statement rule is not merely cheaper than the
    bounded-read rule; running it second would be a hole.

**The Gate stops at the first rule that rejects.** A statement that does not parse
has no tree for a later rule to read, and a rejected outcome names the rules that
actually ran, so nothing has to be inferred from a verdict's silence.

**The Gate never executes the statement it judges** — not even to size it.
`VALIDATE` is step 5 of the flow and `EXECUTE` is step 6, and a Gate that runs the
query it just approved is a Gate with no boundary.
"""

from collections.abc import Callable
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.merge_subqueries import merge_subqueries
from sqlglot.optimizer.qualify import qualify

from veritas.validation.outcome import RejectionReason, ValidationGateOutcome
from veritas.warehouse import WarehouseAdapter, WarehouseError

# The engine every statement is read in: the Warehouse's own, so the Gate parses a
# statement the way the engine that would run it does. The same choice, for the same
# reason, as `check_warehouse.py`'s dialect scan and the spike.
DIALECT = "duckdb"

# The optimizer rewrites the Gate trusts, and no more —
# [C5](../../.claude/docs/design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
# in one place, *"so that widening it is a visible decision rather than a default"*.
# sqlglot's own `optimize()` runs fourteen; these two are what Sub-step 3.2 measured
# the tracer to need, and each is a rewrite trusted to preserve meaning between the
# statement a reviewer reads and the statement the Gate judges.
#
# They are the callables rather than their names, so that the names a
# `Validation Gate outcome` reports are taken off them and there is no second list to
# drift. **No rule in this Sub-step applies one**: 5.1 refuses a statement for its
# shape, and a shape survives no rewriting. They are declared here now because 5.2's
# tracer is what runs them, and a constant C5 requires to be in one place is a place
# that should not move once a rule depends on it.
TRUSTED_REWRITES = (qualify, merge_subqueries)

# The most rows the planner may expect a single question to read from tables.
#
# A **policy**, not a measurement: it is what Veritas is willing to spend on one
# question, so it is a round number chosen and stated rather than derived from the
# Warehouse that happens to be loaded. Nothing in this file goes stale when the data
# grows. What a reader wants beside it — how much headroom the loaded Warehouse
# actually leaves — is printed by `.claude/scripts/check_validation_gate/` on every
# run, which is where a figure a later run can move belongs.
#
# The [Target State](../../.claude/docs/design/target-state.md#extension-path-to-the-full-proposal)
# is what this becomes on the way out of the slice: *"swap DuckDB's estimate for
# BigQuery dry-run bytes-billed"*, where the same ceiling is spelled in bytes.
SCAN_CEILING = 1_000_000


@dataclass(frozen=True, slots=True)
class Reading:
    """What the Gate has read off a statement, before any rule has judged it.

    Parsing happens once, here, rather than inside each rule: five rules that each
    call `sqlglot.parse` are five chances to parse with different settings, and the
    settings are the whole of what a parse tree means.

    `statements` is `None` exactly when sqlglot refused the string, and `refusal`
    carries what it said. That is
    [C6](../../.claude/docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)'s
    requirement made structural: a rule reads *"the parse failed"* as a fact it was
    handed, not as an empty list it has to interpret.
    """

    sql: str
    statements: tuple[exp.Expression, ...] | None = None
    refusal: str = ""

    @property
    def statement(self) -> exp.Expression:
        """The one statement, for the rules that run after the count has been checked."""
        assert self.statements is not None and len(self.statements) == 1
        return self.statements[0]


def read(sql: str) -> Reading:
    """Parse the statement, or record that it could not be parsed.

    `sqlglot.parse` rather than `parse_one`, and the difference is a rule: given
    `SELECT 1; SELECT 2` this version returns two statements where `parse_one`
    returns a single `Block` node that reads like one statement and is not one.
    A Gate built on `parse_one` would have to notice `Block` by name to refuse a
    multi-statement string, which is one library release away from silence.

    Empty segments come back as `None` — `sqlglot.parse("SELECT 1;;")` is a
    statement and a nothing — and are dropped, so a trailing semicolon is not a
    second statement and an empty string is no statements at all.
    """
    try:
        parsed = sqlglot.parse(sql, dialect=DIALECT)
    except sqlglot.errors.SqlglotError as refusal:
        return Reading(sql=sql, statements=None, refusal=str(refusal))
    return Reading(sql=sql, statements=tuple(s for s in parsed if s is not None))


# A rule returns the Rejection Reasons that fired and the sentence explaining them,
# or None when the statement passed it. Reasons rather than one reason because a
# single rule may find several things wrong at once — Sub-step 5.3's Restricted
# Column rule names every column it found rather than the first.
Rejected = tuple[tuple[RejectionReason, ...], str]
Rule = Callable[[Reading], Rejected | None]


def parses(reading: Reading) -> Rejected | None:
    """A statement sqlglot cannot read is rejected, by a rule.

    [C6](../../.claude/docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)
    exists because the spike fails closed *"incidentally"* — gibberish produces no
    projections, and a tracer that requires at least one projection to trace refuses
    it as a side effect. Sub-step 3.2's review measured exactly one mutation that
    survives that, *"for a reason no probe here is written to measure"*. A refusal
    that is a side effect of another rule is removed by changing that other rule,
    and nothing anywhere says so.
    """
    if reading.statements is None:
        return (RejectionReason.UNPARSEABLE,), (
            f"sqlglot could not read this as {DIALECT} SQL: {reading.refusal}"
        )
    return None


def one_statement(reading: Reading) -> Rejected | None:
    """Exactly one statement, or reject.

    Ordered ahead of every rule that hands the engine anything, because it is what
    makes doing so safe: `EXPLAIN (FORMAT json) SELECT 1; DROP TABLE t;` plans the
    first statement and executes the second. `WarehouseAdapter.estimated_scan_rows`
    carries that, and `check_validation_gate/read_only.py` performs it on a throwaway
    table every run rather than leaving it as a warning in a docstring.

    `statements or ()` reads a failed parse as no statements rather than crashing on
    it. The state cannot arise while `parses` runs first, and the fallback is not
    defensiveness for its own sake — it is what makes C6 **legible**: delete `parses`
    from the rule list and gibberish is still refused, by this rule, under the wrong
    Rejection Reason. That is the shape of failure C6 was written about, and the check
    catches it as a mislabelled reason rather than as a traceback.
    """
    statements = reading.statements or ()
    if len(statements) != 1:
        return (RejectionReason.NOT_A_SINGLE_STATEMENT,), (
            f"Veritas runs one statement per question and this string holds "
            f"{len(statements)}"
        )
    return None


def a_read(reading: Reading) -> Rejected | None:
    """The one statement is a `SELECT`, or reject.

    Stated as what is allowed rather than as a list of what is not, because a list
    of forbidden verbs is a list somebody has to keep up with: `DROP`, `INSERT`,
    `COPY`, `PRAGMA` and `ATTACH` are the shapes
    [5.1](../../.claude/docs/plan/step-005-validation-gate.md#the-six-shapes-read-only-has-to-cover)
    names, and `INSTALL`, `SET`, `EXPORT` and whatever the engine grows next are the
    ones it does not. Every one of them is refused here by not being a `SELECT`.

    `COPY (SELECT 1) TO 'leak.csv'` is the shape worth naming: it reads nothing it
    should not and writes the answer to the filesystem, where no reader of a Grounded
    Answer will ever see it. Read-only has to mean the Warehouse **and** the
    filesystem or it does not mean much.

    A `UNION` of two `SELECT`s is refused here too, and that is a decision rather than
    an oversight: nothing in `semantic/` needs one, and a Gate that fail-closes on a
    shape it has no use for costs a rejection message where the other reading costs a
    hole. Admitting it later is one `isinstance` and a probe.
    """
    statement = reading.statement
    if not isinstance(statement, exp.Select):
        return (RejectionReason.NOT_A_READ,), (
            f"Veritas runs SELECT statements and this is a "
            f"{statement.key.upper()} statement"
        )
    return None


@dataclass(frozen=True, slots=True)
class ValidationGate:
    """The Gate. Built once with what its rules read, then asked for a verdict.

    It takes the Warehouse Adapter rather than a statement alone because
    [C4](../../.claude/docs/design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time)
    binds this Step: the Gate reads the live schema at run time and reads it
    *"through the Warehouse Adapter — which keeps it on the right side of ADR-0002's
    seam"*. Sub-step 5.1 uses the adapter for the planner's estimate only; 5.3 is
    where the column list arrives.

    The scan ceiling is a constructor argument rather than a constant read inside a
    rule so that a caller can say what it is willing to spend, and so that the rule
    can be given teeth without building a query big enough to trip the real one.
    """

    warehouse: WarehouseAdapter
    scan_ceiling: int = SCAN_CEILING

    def bounded(self, reading: Reading) -> Rejected | None:
        """The planner's estimate for what this will read, against the ceiling.

        The estimate comes from the engine through the adapter, never from this
        module: `EXPLAIN` is dialect, and `check_warehouse.py`'s seam scan fails the
        run on a `duckdb` import outside `veritas/warehouse/` — correctly.
        [R7](../../.claude/docs/plan/step-005-validation-gate.md#r7--the-bounded-read-uses-the-engines-estimate-if-the-adapter-can-reach-it--approved-by-amino-2026-08-25)
        put two rules up and said the measurement chooses between them; this is the
        engine's estimate, which Sub-step 5.1 found reachable in a machine-readable
        plan, so the parse-tree fallback R7 pre-approved was not needed.

        **An engine that will not plan the statement is a rejection, not a crash.**
        A query naming a column that does not exist is refused here rather than at
        execution, and it is refused as unbounded because that is the honest verdict
        this rule can reach: the planner would not say how much it reads. That
        distinction is only expressible because
        [DEBT-016](../../.claude/docs/debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)
        was paid in the same Sub-step — a `WarehouseError` is the engine refusing a
        caller's SQL, where a bare `Exception` here would have swallowed a broken
        adapter and called it a bad query.
        """
        try:
            scanned = self.warehouse.estimated_scan_rows(reading.statement.sql(DIALECT))
        except WarehouseError as refusal:
            return (RejectionReason.UNBOUNDED_SCAN,), (
                f"the engine would not plan this statement, so how much it reads is "
                f"unknown and an unknown scan is not a bounded one: {refusal}"
            )
        if scanned > self.scan_ceiling:
            return (RejectionReason.UNBOUNDED_SCAN,), (
                f"the planner expects to read {scanned} rows and the ceiling is "
                f"{self.scan_ceiling}"
            )
        return None

    def rules(self) -> tuple[tuple[str, Rule], ...]:
        """The rules, in the order a statement meets them.

        One list in one place, which is what lets the ordering argument in this
        module's docstring be something the code states rather than something the
        file happens to be. Each later Sub-step of Step 005 appends to it.
        """
        return (
            ("parses", parses),
            ("one statement", one_statement),
            ("a read", a_read),
            ("bounded", self.bounded),
        )

    def judge(self, sql: str) -> ValidationGateOutcome:
        """Allow or reject one statement, and say under what.

        Stops at the first rule that rejects: a statement that does not parse has no
        tree for the next rule to read, and there is nothing to gain from asking a
        rule a question it cannot answer. The outcome names the rules that ran, so a
        reader never has to infer what a verdict covered.
        """
        reading = read(sql)
        ran: list[str] = []
        for name, rule in self.rules():
            ran.append(name)
            rejected = rule(reading)
            if rejected is None:
                continue
            reasons, explanation = rejected
            return ValidationGateOutcome(
                allowed=False,
                explanation=explanation,
                reasons=reasons,
                rules=tuple(ran),
                trusted_rewrites=trusted_rewrite_names(),
            )
        return ValidationGateOutcome(
            allowed=True,
            explanation="",
            reasons=(),
            rules=tuple(ran),
            trusted_rewrites=trusted_rewrite_names(),
        )


def trusted_rewrite_names() -> tuple[str, ...]:
    """`TRUSTED_REWRITES` as the names a chart and a log line can carry.

    Taken off the callables rather than typed beside them, so C5's *"named in one
    place"* survives someone adding a third.
    """
    return tuple(rewrite.__name__ for rewrite in TRUSTED_REWRITES)
