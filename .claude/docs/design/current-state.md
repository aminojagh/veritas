# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**Last updated:** 2026-08-03 — Sub-step 1.2 closed; rulings R1–R3 applied; Target State now `agreed`
**Steps completed:** Step 000 (framework) and Step 001 Sub-step 1.1, both committed in `6281e6b`. Sub-step 1.2 done.

---

## Resume here

- **Active Step:** 001 — Design the Target State
  ([plan](../plan/step-001-target-state-design.md)).
- **Next Sub-step:** 1.3 — record the three founding ADRs: Semantic Layer as the
  retrieval corpus, DuckDB behind an adapter seam, and the Validation Gate as
  deterministic code rather than an LLM self-check. **Unblocked** — the Target
  State is `agreed`, so ADRs written against it will not need rewriting. A
  fourth ADR is a candidate: snapshot-and-replay for external data sources
  ([DEBT-002](../debt-ledger.md)), a pattern already proven by
  `check_data_availability.py`.
- **Awaiting Amino:** nothing. Rulings R1–R3 were given and applied; see
  [data-availability.md](data-availability.md#rulings).
- **Not yet started:** any implementation. The design gate is now fully open —
  Step 002 is the first Step that builds something.

---

## Summary

A fully designed project with no implementation. The framework is in place and
the Target State is `agreed`, so there is a fixed point to build toward: a
natural-language analytics copilot over a brokerage warehouse, whose answers are
grounded in a certified Semantic Layer and checked by a deterministic Validation
Gate.

Every data source that design assumes has been verified obtainable, key-free,
and is snapshotted into the repository. Nothing else is built — no warehouse, no
Semantic Layer, no application.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Zero dependencies** — both scripts are stdlib-only. |
| Development framework | ✅ working | `CLAUDE.md`, `.claude/docs/` tree, five skills in `.claude/skills/`. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only, passes. |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`. Sub-step 1.2 added `Market Price`, `Adjusted Close`, `Quotation Currency`; narrowed `Instrument`; renamed `dim_fx_rate` → `fct_fx_rate` and registered `fct_instrument_price`. |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified, rulings R1–R3 applied. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — 288 KB: real 2025 FX Rates and three real price series, plus the dated probe record. Committed on purpose: it is what makes the check reproduce without network access. |
| Founding ADRs | ✗ none | Sub-step 1.3 — now unblocked. |
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
├── data/snapshots/            # committed source data + dated probe record
└── .claude/
    ├── skills/                # 5 framework skills
    ├── scripts/
    │   ├── verify_framework.py
    │   └── check_data_availability.py
    └── docs/
        ├── glossary.md
        ├── debt-ledger.md
        ├── design/{target-state,current-state,product-brief,data-availability}.md
        ├── adr/
        ├── plan/
        └── reviews/
```

## Known gaps

All implementation. The design gate is fully open: the data-availability check
passed and rulings R1–R3 are applied, so nothing blocks Step 002 except Sub-step
1.3's ADRs.

Answered since Sub-step 1.1: the market-price source is **Yahoo's chart
endpoint**, key-free, covering equity/ETF/future/currency pair. Stooq, the
obvious alternative, serves an anti-bot page. Single bonds and options are
**out of scope** — no key-free source exists ([DEBT-003](../debt-ledger.md)).
Still deferred to the retrieval Step: which embedding and re-ranking models.

Two proven wrong-number traps are handled in `check_data_availability.py` but
not yet defended anywhere else, because there is nothing else: unadjusted
`Market Price` vs `Adjusted Close` (they differ on 95.5% of bars), and
pence-quoted (`GBp`) instruments. A third gotcha is recorded in
[data-availability.md](data-availability.md): Frankfurter returns HTTP 403 to
the default `Python-urllib` User-Agent, which reads as "blocked" when the fix is
one header.

## Open debt

4 open — see [debt-ledger.md](../debt-ledger.md).

- **DEBT-001** — framework rules rely on discipline, not enforcement.
- **DEBT-002** — market prices depend on an unofficial endpoint; the
  snapshot-and-replay mitigation must land with the ingestion pipeline.
- **DEBT-003** — no Market Price vendor, so single bonds and options are out of
  scope; a paid vendor is a future setup step.
- **DEBT-004** — the FX-date distinction moves the number by only 0.08%, too
  little to be a reliable evaluation signal; must be addressed when the Gold
  Question Set is built.
