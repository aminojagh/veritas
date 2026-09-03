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
| [002](step-002-warehouse-and-ingestion.md) | Build the Warehouse and fill it | 6 | done |
| [003](step-003-validation-feasibility.md) | Prove the Validation Gate's parse-tree claim | 5 | done |
| [004](step-004-semantic-layer.md) | Build the Semantic Layer | 5 | done |
| [005](step-005-validation-gate.md) | Build the Validation Gate | 5 | done |
| [006](step-006-retrieval-and-orchestrator.md) | Ask a question, get a Grounded Answer | 5 | done |
| [007](step-007-evaluation.md) | Evaluation: measure Veritas over a Gold Question Set | 4 | done |
| [008](step-008-observability.md) | Observability: record every question and chart it | 5 | active |

Statuses: `proposed` (written, not yet approved — no implementation may begin) ·
`active` · `in review` · `done` · `abandoned` (with a note on why — an abandoned
Step usually means the Target State moved).
