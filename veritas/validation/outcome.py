"""The Validation Gate outcome and the Rejection Reason taxonomy — the data
contract, before it is a return value.

Both names are Glossary terms as of 2026-08-25
([R3](../../.claude/docs/plan/step-005-validation-gate.md#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)),
and they are here rather than in `gate.py` because three components that will never
import a rule still have to read a verdict: a `Grounded Answer` carries one, the
`App` renders one, and `Observability` charts *"Validation-Gate rejections by
reason"*. A contract only its producer can import is not a contract.

**The taxonomy is registered in code and enumerated here.**
[ADR-0003](../../.claude/docs/adr/0003-validation-gate-is-deterministic-code.md)
sells determinism partly on that taxonomy existing — an LLM validator *"cannot
produce the stable taxonomy of rejection reasons that 'Validation-Gate rejections
by reason' needs to be a real chart"* — so the members are a closed set a chart can
group by, not strings each rule invents. R3 is also where this Step declined to put
the members in the Glossary cell instead, because a vocabulary inside one table cell
read by a prose parse is
[DEBT-017](../../.claude/docs/debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell),
opened four days earlier and still open.

**The set is incomplete on purpose.** Sub-step 5.1 ships the rules that need neither
the corpus nor the schema, so it registers four members. Each later rule of
[Step 005](../../.claude/docs/plan/step-005-validation-gate.md) adds its own with the
Sub-step that adds the rule. A member with no rule behind it would be a chart
category nothing can ever fall into.
"""

from dataclasses import dataclass
from enum import StrEnum


class RejectionReason(StrEnum):
    """Why the Validation Gate refused a statement. One member per rule that can fire.

    A `StrEnum` so that a member survives the trip into a log line, a Postgres row
    and a Grafana filter as the word a person reads, while staying a member the Gate
    can enumerate. The value is the chart label; the name is the code identifier.
    """

    UNPARSEABLE = "unparseable"
    """sqlglot could not read the statement at all.

    [C6](../../.claude/docs/design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)
    is the constraint that requires this to be its own reason rather than a
    consequence of finding nothing in an empty tree. The spike fails closed
    *"incidentally"*, and Sub-step 3.2's review measured one mutation that passes
    *"for a reason no probe here is written to measure"*. A Gate whose refusal of
    gibberish is a side effect is a Gate whose refusal of gibberish can be removed
    by an unrelated change and nothing will notice.
    """

    NOT_A_SINGLE_STATEMENT = "not a single statement"
    """The string holds more or fewer than one statement.

    Separate from `NOT_A_READ` because the danger is different in kind. Every
    statement in `SELECT 1; DROP TABLE fct_trade;` reads fine on its own and the
    string is a write; worse, the engine executes the tail of such a string even
    when the head is wrapped in `EXPLAIN`, which is why this rule is ordered ahead
    of any rule that asks the engine anything. `WarehouseAdapter.estimated_scan_rows`
    carries the measurement.
    """

    NOT_A_READ = "not a read"
    """The one statement is something other than a `SELECT`.

    Covers a write to the Warehouse, a write to the filesystem, engine
    introspection, and attaching a second database — the shapes
    [Sub-step 5.1](../../.claude/docs/plan/step-005-validation-gate.md#the-six-shapes-read-only-has-to-cover)
    enumerates. They share a reason because they share a rule: the Gate does not ask
    what a statement would do, it asks whether it is the one kind of statement
    Veritas runs. What it *was* goes in the outcome's explanation, so a chart can
    group by the rule and a reader can still see the verb.
    """

    UNBOUNDED_SCAN = "unbounded scan"
    """The planner expects the statement to read more rows than the ceiling allows.

    The `Validation Gate`'s registered definition ends with *"cost bounded,
    read-only"*, and the [Target State](../../.claude/docs/design/target-state.md#flow)
    spells the first of those *"scan bounded"*.
    """


@dataclass(frozen=True, slots=True)
class ValidationGateOutcome:
    """The verdict: allowed or rejected, why, and what it was decided under.

    Frozen, because it is evidence. Between the Gate returning one and Observability
    charting it there is an Orchestrator and a Grounded Answer, and a verdict any of
    them can edit is a verdict none of them can be held to.

    `reasons` is empty exactly when `allowed` is true, and one rule may contribute
    several members — Sub-step 5.3's Restricted Column rule names every column it
    found rather than the first. `explanation` is the sentence a person reads;
    `reasons` is what a chart groups by. Both, because the
    [Target State's flow](../../.claude/docs/design/target-state.md#flow) says
    *"fail → explain the violation"* and ADR-0003 says the taxonomy has to be stable,
    and neither one does the other's job.

    `rules` names the rules that actually ran, in order, which is not the same as the
    rules that exist: the Gate stops at the first rule that rejects, so a statement
    refused as unparseable was never asked whether it was bounded. A reader who wants
    to know what a verdict covers reads this rather than assuming.

    `trusted_rewrites` is
    [C5](../../.claude/docs/design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
    reported rather than declared. The rewrites themselves are `gate.TRUSTED_REWRITES`,
    where they are the callables a rule can actually run; what reaches a chart is their
    names, taken off those callables so there is no second list to drift. A verdict
    reached under a wider rule set is a different verdict, which is why it travels with
    the verdict instead of being looked up later.
    """

    allowed: bool
    explanation: str = ""
    reasons: tuple[RejectionReason, ...] = ()
    rules: tuple[str, ...] = ()
    trusted_rewrites: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.allowed and self.reasons:
            raise ValueError(
                f"an allowed outcome carries no Rejection Reason, and this one "
                f"carries {list(self.reasons)}"
            )
        if not self.allowed and not self.reasons:
            raise ValueError(
                "a rejected outcome names at least one Rejection Reason, because "
                "'rejections by reason' is a chart and an unlabelled rejection is a "
                "bar with no name"
            )
