"""Check the Validation Gate against the statements it has to judge.

Run with:  uv run python .claude/scripts/check_validation_gate/

Needs a filled Warehouse — `uv run python -m veritas.ingestion` first — because the
bounded-read rule asks the engine to plan a statement, and an engine with no tables
refuses every one of them.

**A package rather than a file**, by
[R8](../../docs/plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25):
one module per Gate rule, added with the Sub-step that adds the rule. The three checks
grown by the method this one inherits are each well over a thousand lines and none of
them was ever *decided* to be a monolith; each became one by having a rule added five
or six times. The command stays one command, which is the part that matters — Python
runs a directory holding a `__main__.py`, so this is invoked the way the flat scripts
beside it are and reads the same in a review.

This file is the runner: the rule list, the report, and the exit code. **The order
below is the Gate's own**, because the ordering is a claim the Gate makes — each rule
runs before every rule that needs more than it does — and a check that read them in a
different order would be checking a different Gate.

  * `read_only` — Sub-step 5.1. Parseable, one statement, a read, bounded.

The four still to come are `traces` (5.2), `restricted` (5.3), `route` (5.4) and
`access` (5.5).
"""

import read_only
from probes import problems, warehouse


def main() -> int:
    with warehouse() as adapter:
        print(f"  Warehouse: {adapter.database_path}")
        reports = [read_only.check(adapter)]

    for report in reports:
        report.print()

    print()
    if problems:
        print(f"FAIL — {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        "PASS — the Validation Gate refuses what it cannot read, what is more than "
        "one statement, what is not a read, and what the planner expects to scan past "
        "the ceiling; and it allows an ordinary question"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
