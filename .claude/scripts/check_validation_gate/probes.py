"""Shared probe machinery for the Validation Gate check: the adapter, the probe
record, and the report every rule module writes into.

Run the check with:  uv run python .claude/scripts/check_validation_gate/

The container is
[R8](../../docs/plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)'s:
a runner, this module, and one module per rule added with the Sub-step that adds the
rule. The three checks grown by the method this one inherits are each well over a
thousand lines — `wc -l .claude/scripts/*.py` prints where they have got to — and none
of them was ever decided to be a monolith. Splitting a package that does not exist
costs nothing.

**The method is the spike's.** A Gate is a judge, and a judge is tested by putting
cases in front of it: every probe declares the verdict this Sub-step measured for it,
so *"rejected"* is never left to a reader to interpret as good or bad news. A probe
whose verdict changes in **either** direction fails the run.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SCRIPTS_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from veritas.validation import (  # noqa: E402 — after sys.path, like the checks beside it
    RejectionReason,
    ValidationGate,
)
from veritas.warehouse import DATABASE_PATH, WarehouseAdapter  # noqa: E402

# Every problem any rule module found. One list so the runner can report the count
# and set the exit code in one place, the way the check scripts beside this one do.
problems: list[str] = []

ALLOWED = "allowed"
REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Probe:
    """One statement, the verdict this Sub-step measured for it, and why it is here.

    `reasons` is the Rejection Reason members the probe must come back with, so a
    rejection for the wrong reason fails as loudly as no rejection at all — the
    taxonomy is what Observability groups by, and a rule that rejects everything
    passes every rejection probe.

    `ceiling` judges the probe under a scan ceiling of its own. That is how the
    bounded-read rule is given teeth without a query big enough to trip the real
    ceiling: the rule under test is the comparison, and a probe that had to build a
    million-row scan would be measuring the Warehouse's size instead.
    """

    name: str
    sql: str
    verdict: str
    why: str
    reasons: tuple[RejectionReason, ...] = ()
    ceiling: int | None = None


@dataclass(slots=True)
class Report:
    """What one rule module found: lines to print, and problems to fail on.

    Printed rather than asserted, because Non-Negotiable #4 asks for a committed
    command whose **output** a review can quote, and the numbers in that output are
    half of what a review quotes.
    """

    heading: str
    lines: list[str] = field(default_factory=list)

    def say(self, line: str) -> None:
        self.lines.append(line)

    def print(self) -> None:
        print()
        print(f"  {self.heading}")
        for line in self.lines:
            print(f"    {line}")


def judge_probes(
    gate: ValidationGate, probes: tuple[Probe, ...], report: Report
) -> None:
    """Put every probe in front of the Gate and compare the verdict with the declared one.

    The Gate is rebuilt with the probe's own ceiling where it declares one, rather
    than the ceiling being reached into and changed: a `ValidationGate` is frozen, and
    a check that mutated the thing under test would be measuring something else.
    """
    for probe in probes:
        judged = (
            gate if probe.ceiling is None else ValidationGate(gate.warehouse, probe.ceiling)
        )
        outcome = judged.judge(probe.sql)
        verdict = ALLOWED if outcome.allowed else REJECTED
        reasons = tuple(outcome.reasons)
        ceiling = "" if probe.ceiling is None else f", ceiling {probe.ceiling}"
        report.say(
            f"{verdict:9} {probe.name:24} "
            f"{', '.join(reason.value for reason in reasons) or '—'}{ceiling}"
        )
        if verdict != probe.verdict:
            problems.append(
                f"{probe.name!r} was measured as {probe.verdict} and came back "
                f"{verdict} — {probe.why}\n      {probe.sql}\n      {outcome.explanation}"
            )
            continue
        if reasons != probe.reasons:
            problems.append(
                f"{probe.name!r} was rejected for "
                f"{[r.value for r in reasons]} where it was measured as "
                f"{[r.value for r in probe.reasons]} — a rejection for the wrong "
                f"reason is a mislabelled bar on the chart ADR-0003 sold determinism "
                f"on\n      {probe.sql}"
            )


def warehouse() -> WarehouseAdapter:
    """The built Warehouse, or a refusal that says how to build it.

    The Gate's bounded-read rule asks the engine to plan a statement, so this check
    needs a Warehouse with the star schema in it for the same reason
    `check_semantic_layer.py` does.
    """
    if not DATABASE_PATH.exists():
        raise SystemExit(
            f"no Warehouse at {DATABASE_PATH.relative_to(REPO_ROOT)} — run "
            f"`uv run python -m veritas.ingestion` first"
        )
    return WarehouseAdapter()
