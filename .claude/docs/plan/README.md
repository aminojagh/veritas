# Plans

One file per **Step**: `step-NNN-<slug>.md`. At most one has `Status: active`.

A Step is a vertical slice from Current State toward Target State that leaves
the project working end-to-end. It contains 1–5 Sub-steps, each exactly one
commit. See the `planning-a-step` skill.

Plans are not deleted when finished — they become the record of what was
attempted versus what shipped, which is where the Step Review gets its honesty.

| Step | Title | Sub-steps | Status |
|---|---|---|---|
| [000](step-000-framework-scaffolding.md) | Development framework scaffolding | 1 | done |
| [001](step-001-target-state-design.md) | Design the Target State | 3 | done |

Statuses: `active` · `in review` · `done` · `abandoned` (with a note on why —
an abandoned Step usually means the Target State moved).
