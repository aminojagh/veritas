# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**Last updated:** 2026-07-23 — review feedback folded in; framework relocated under `.claude/`
**Steps completed:** none committed yet. Step 000 (framework) is closed and ready for the first commit; Step 001 Sub-step 1.1 done, 1.2 next.

---

## Resume here

- **Active Step:** 001 — Design the Target State
  ([plan](../plan/step-001-target-state-design.md)).
- **Next Sub-step:** 1.2 — verify data availability (FX, instruments/prices,
  synthetic activity), producing `.claude/docs/design/data-availability.md`.
- **Awaiting Amino:** the first commit of the Step 000 + Step 001 work so far.
  All Domain Language — Sections A through D and the System measures — is now
  `agreed`.
- **Not yet started:** any implementation. Gated on the Target State becoming
  `agreed`, which is gated on Sub-step 1.2.

---

## Summary

A designed project with no implementation. The development framework is in place
and the Target State is written, so there is now a fixed point to build toward:
a natural-language analytics copilot over a brokerage warehouse, whose answers
are grounded in a certified Semantic Layer and checked by a deterministic
Validation Gate.

Nothing is built yet. No warehouse, no Semantic Layer, no application.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. Zero dependencies so far. |
| Development framework | ✅ working | `CLAUDE.md`, `.claude/docs/` tree, five skills in `.claude/skills/`. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only, passes. |
| Glossary | ✅ working | Process Language + all Domain Language (Sections A through D, plus the System measures) `agreed` (2026-07-23). |
| Target State | ◐ partial | Written; terms `agreed`, but the document stays `proposed` until Sub-step 1.2 confirms its data sources. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✗ none | Sub-step 1.2 — the gate that finalizes the Target State. |
| Founding ADRs | ✗ none | Sub-step 1.3, after the Target State is `agreed`. |
| Warehouse | ✗ none | — |
| Semantic Layer | ✗ none | — |
| Ingestion | ✗ none | — |
| Retrieval | ✗ none | — |
| Copilot | ✗ none | — |
| Validation Gate | ✗ none | — |
| Interface | ✗ none | — |
| Observability | ✗ none | — |
| Evaluation | ✗ none | — |
| Containerization | ✗ none | — |

## Repository layout

```
veritas/
├── CLAUDE.md                  # operating agreement (root: Claude Code auto-loads it)
├── final_proposal_target.md   # source job description — captured into .claude/docs/design/product-brief.md, removable
├── pyproject.toml, uv.lock, .python-version, .gitignore
└── .claude/
    ├── skills/                # 5 framework skills
    ├── scripts/verify_framework.py
    └── docs/
        ├── glossary.md
        ├── debt-ledger.md
        ├── design/{target-state,current-state,product-brief}.md
        ├── adr/
        ├── plan/
        └── reviews/
```

## Known gaps

All implementation. The Domain Language is now `agreed`, so the earlier approval
block is lifted. The remaining gate is the **data-availability check** (Sub-step
1.2): the Target State stays `proposed` until its sources are confirmed, and the
Glossary rule forbids building against a `proposed` design.

One design question is deliberately deferred *into* that check rather than
guessed: the instrument/price data source (FX is settled — Frankfurter,
key-free). Which embedding and re-ranking models to use is deferred to the
retrieval Step.

## Open debt

1 open — see [debt-ledger.md](../debt-ledger.md).

- **DEBT-001** — framework rules rely on discipline, not enforcement.
