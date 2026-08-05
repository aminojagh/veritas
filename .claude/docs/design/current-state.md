# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**Last updated:** 2026-08-05 — Step 001 closed and committed; Step 002 planned, approved, and awaiting its first commit. Still no implementation code.
**Steps completed:** Step 000 (framework) and Step 001, fully committed. Step 000 and Sub-step 1.1 in `6281e6b`, Sub-step 1.2 in `4b48a46`, Sub-step 1.3 in `9c5b060`.

---

## Resume here

- **Active Step:** 002 — Build the Warehouse and fill it
  ([plan](../plan/step-002-warehouse-and-ingestion.md)), **approved 2026-08-05**
  along with all six rulings in it. Step 001
  ([plan](../plan/step-001-target-state-design.md)) is **done**, all three
  Sub-steps committed, the last in `9c5b060`.
- **Next Sub-step:** 2.1 — create the Warehouse behind its adapter:
  `veritas/warehouse/` holding the Warehouse Adapter and the ten-table star
  schema, empty, plus `.claude/scripts/check_warehouse.py`. `uv add duckdb` is
  the first dependency this project takes. Start it once the planning documents
  below are committed.
- **Awaiting Amino: the commit** of the Step 002 planning changes. Nothing is
  blocked on a decision — every question the plan raised was ruled on the same
  day and recorded in
  [Rulings](../plan/step-002-warehouse-and-ingestion.md#rulings):
  1. **`Execution Price` is `agreed`** and required — Glossary Section B, with a
     Section C row against `Market Price`. Column `fct_trade.execution_price`.
  2. **No `dim_date`.** The date axis is `trade_date` / `settlement_date`;
     `target-state.md`'s Warehouse row was corrected.
  3. **Hand-authored DDL inside the adapter is allowed**, with the reasoning and
     four worked examples now a dated clarification in
     [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md#clarification-2026-08-05--what-the-sqlglot-commitment-forbids).
  4. **dlt lands raw; the adapter builds the star schema.** Second decision in
     ADR-0004, due in Sub-step 2.2.
  5. **Check scripts, no pytest** this Step.
  6. **2.4 is a pre-agreed split point** — if 2.1–2.3 grow under review, it
     becomes Step 003 rather than being squeezed.
- **Obligations recorded for later Steps**, so they are not rediscovered:
  `README.md` must list every credential Veritas touches
  ([Target State](target-state.md#what-credential-free-means)), and two Ledger
  entries fire on the same pass — [DEBT-002](../debt-ledger.md) on the
  reproducibility claim, [DEBT-008](../debt-ledger.md) on the access-control
  claim.
- **Not yet started:** any implementation. The design gate is fully open.

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
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Zero dependencies** — all three scripts are stdlib-only. |
| Development framework | ✅ working | `CLAUDE.md`, `.claude/docs/` tree, five skills in `.claude/skills/`. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only (documents exist, links resolve, skills load, interpreter pinned), passes. |
| Language check | ✅ working | `.claude/scripts/check_language.py` — content rules: component names registered, no `proposed` term in code, abbreviations resolvable. Passes. Parses code with `ast` so it checks identifiers, not prose. Partial payment of [DEBT-001](../debt-ledger.md). |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`. Sub-step 1.2 added `Market Price`, `Adjusted Close`, `Quotation Currency`; narrowed `Instrument`; renamed `dim_fx_rate` → `fct_fx_rate` and registered `fct_instrument_price`. Step 002 planning added `Execution Price` and its Section C row against `Market Price`. |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified, rulings R1–R3 applied. One correction 2026-08-05: no date dimension in the Warehouse row. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — 288 KB: real 2025 FX Rates and three real price series, plus the dated probe record. Committed on purpose: it is what makes the check reproduce without network access. |
| Founding ADRs | ✅ working | Three ADRs in `.claude/docs/adr/`, all **`accepted`** 2026-08-03: 0001 Semantic Layer as the retrieval corpus, 0002 DuckDB behind an adapter, 0003 Validation Gate as deterministic code. Every cost in each is classified *accepted* / *debt* / *extension*. A fourth — snapshot-and-replay — was deferred to the ingestion Step ([DEBT-002](../debt-ledger.md)), and is now due as ADR-0004 in Sub-step 2.2. ADR-0002 carries a dated clarification (2026-08-05) on what its sqlglot commitment forbids; its status stays `accepted`. |
| Warehouse | ✗ none | — |
| Semantic Layer | ✗ none | — |
| Ingestion | ✗ none | — |
| Retrieval | ✗ none | — |
| Orchestrator | ✗ none | — |
| Validation Gate | ✗ none | — |
| App | ✗ none | — |
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
    │   ├── verify_framework.py        # structure: docs, links, skills, interpreter
    │   ├── check_language.py          # content: Glossary + writing conventions
    │   └── check_data_availability.py
    └── docs/
        ├── glossary.md
        ├── debt-ledger.md
        ├── extension-register.md
        ├── design/{target-state,current-state,product-brief,data-availability}.md
        ├── adr/
        ├── plan/
        └── reviews/
```

## Known gaps

All implementation. The design gate is fully open: the data-availability check
passed, rulings R1–R3 are applied, and the founding ADRs are written. Nothing
blocks Step 002.

The component-name gap found in Sub-step 1.3 is **closed**: all nine Target State
components are now registered Glossary terms, two of them renamed in the process
(`Copilot` → `Orchestrator`, `Interface` → `App`). Every directory Step 002
creates has a name that was agreed before the directory existed, which is the
order Non-Negotiable #1 exists to produce. `check_language.py` enforces it from
here on.

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

## Open debt and extensions

**5 open debt** — see [debt-ledger.md](../debt-ledger.md) — plus 1 accepted
permanently and 2 moved out. **5 open extensions** — see
[extension-register.md](../extension-register.md).

The split is new as of 2026-08-04. Debt means the current code is *wrong,
cheaply*; an extension means it is *right for this scope* and the full system
needs more. The test that settles it: does the trigger fire inside this project's
life? Three Sub-step 1.3 entries failed that test and moved.

- **DEBT-001** — framework rules rely on discipline, not enforcement.
- **DEBT-002** — market prices depend on an unofficial endpoint; the
  snapshot-and-replay mitigation must land with the ingestion pipeline.
- **DEBT-003** — no Market Price vendor, so single bonds and options are out of
  scope; a paid vendor is a future setup step.
- **DEBT-004** — the FX-date distinction moves the number by only 0.08%, too
  little to be a reliable evaluation signal; must be addressed when the Gold
  Question Set is built.
- **DEBT-005** — moved to EXT-002. Was never debt: the slice has one schema,
  authored once, so drift cannot occur here.
- **DEBT-006** — **accepted permanently.** No ad-hoc exploration; Veritas is a
  metrics copilot, not a database browser. Now a Target State non-goal.
- **DEBT-007** — moved to EXT-003. Hand-authored YAML is the *better* choice at
  slice scale, not a shortcut.
- **DEBT-008** — narrowed to what can fire here: the README and App must
  not overstate what application-layer access enforcement guarantees. The
  engineering moved to EXT-001.

[DEBT-001](../debt-ledger.md)'s trigger **fired** in Sub-step 1.3 — a framework
rule agreed in 1.2 was broken in 1.3. Partially paid by `check_language.py` and
by new rules in `CLAUDE.md`; the hook layer is still unpaid.
