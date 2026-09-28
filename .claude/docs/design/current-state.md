# Current State

**What exists in this repository right now.** Reality only — never intent, never
plans. If this file and the repository disagree, this file is wrong. It points at the
code rather than describing it; how each part came to be is in git.

## Resume here

- **Veritas is being redesigned.** The route is the
  [Redesign Roadmap](../plan/redesign-roadmap.md): take its first item that is not
  `done` and whose dependencies are. R0 and R1 are `done`; next is **R2 — frame the
  problem**.
- **Awaiting Amino:** [ADR-0006](../adr/0006-every-certified-metric-follows-one-stated-book-convention.md)
  and [ADR-0007](../adr/0007-evaluation-scores-within-a-tolerance-and-picks-defaults-by-measurement.md)
  are `proposed`. Both hold reasons that lived in the deleted `docs/decisions.md`.
- No Step is active, so there is no plan or review under `plan/` or `reviews/`.

## What is built

Every component of the [Target State](target-state.md#components) exists, and a
question typed into the App comes back as a Grounded Answer.

| Component | Lives in | Proved by |
|---|---|---|
| **Warehouse** | `veritas/warehouse/` — the adapter, `schema.sql`, one build per table in `builds/` | `.claude/scripts/check_warehouse.py` |
| **Ingestion** | `veritas/ingestion/`; snapshots in `data/snapshots/` | `uv run python -m veritas.ingestion`, offline; `check_warehouse.py --sources --distinctions`; `check_data_availability.py` |
| **Semantic Layer** | `semantic/` — metrics, dimensions, joins, ambiguous; read by `veritas/semantic/` | `.claude/scripts/check_semantic_layer.py` |
| **Retrieval** | `veritas/retrieval/` | `tests/test_retrieval.py` |
| **Orchestrator** | `veritas/orchestrator/`; model calls through `veritas/llm/` | `tests/test_rewrite.py`, `tests/test_orchestrator.py`, `tests/test_llm.py` |
| **Validation Gate** | `veritas/validation/` | `tests/test_gate.py`, `.claude/scripts/check_validation_gate/`, `check_validation_feasibility.py` |
| **App** | `veritas/app/` | `tests/test_app.py` |
| **Observability** | `veritas/observability/`, `grafana/` | `tests/test_observability.py` |
| **Evaluation** | `veritas/evaluation/`; the Gold Question Set in `data/gold/` | `tests/test_evaluation.py`, `tests/test_gold.py` |

Around them:

- **Containers** — `Dockerfile` and `docker-compose.yml` run the App, Postgres and
  Grafana; `tests/test_container.py`.
- **`README.md`** — the public face; `tests/test_readme.py` holds its credential list
  and its access-control sentence to the code and to ADR-0002.
- **The framework** — `CLAUDE.md` and `.claude/skills/`; `tests/test_framework.py`,
  `tests/test_links.py` and `tests/test_language.py` check that the documents hang
  together.

`uv run pytest` runs every test; those needing a running service or a live model
skip and say why. The check scripts in `.claude/scripts/` run one at a time, each
with `uv run python`, and the Warehouse must be built first. `tests/test_framework.py`
lists which remain.

## The working record

- [Glossary](../glossary.md) — the domain and process language.
- [Target State](target-state.md) — the capstone's design, `agreed`, and still the
  fixed point until the redesign replaces it.
- [Product Brief](product-brief.md) — the full system the capstone is a slice of.
- [ADRs](../adr/) — the decisions that are expensive to reverse, as they stand.
- [Debt Ledger](../debt-ledger.md) and [Extension Register](../extension-register.md)
  — what is open: shortcuts in the code, and what the full system needs beyond it.

## Known gaps

The Ledger and the Register are the list. The two that shape the redesign most:
[DEBT-023](../debt-ledger.md#debt-023--two-proving-systems-run-side-by-side) — the
product checks still live in `.claude/scripts/` beside `tests/` — and
[DEBT-024](../debt-ledger.md#debt-024--docstrings-argue-why-they-were-built-as-they-are)
— the product code's docstrings still argue why it was built as it is.
