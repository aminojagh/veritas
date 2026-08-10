# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**Last updated:** 2026-08-10 — Sub-step 2.2 built and verified, awaiting Amino's review and commit. **The Warehouse now holds real data.**
**Steps completed:** Step 000 (framework) and Step 001, fully committed; Step 002 is in flight, **one of its five Sub-steps committed and a second built**. Step 000 and Sub-step 1.1 in `6281e6b`, Sub-step 1.2 in `4b48a46`, Sub-step 1.3 in `9c5b060`, Step 002 planning in `57e8aee`, Sub-step 2.1 in `5a061a7`, the R16 plan amendment in `cd5e7dd`.

---

## Resume here

- **Active Step:** 002 — Build the Warehouse and fill it
  ([plan](../plan/step-002-warehouse-and-ingestion.md)), approved 2026-08-05.
  **Sub-step 2.1 is committed** (`5a061a7`); both its verification commands pass
  and their output is in the
  [review](../reviews/step-002-warehouse-and-ingestion.md).
- **The plan was amended and approved on 2026-08-10
  ([R16](../plan/step-002-warehouse-and-ingestion.md#r16--the-original-sub-step-22-splits-into-three--approved-by-amino-2026-08-10)).**
  The original Sub-step 2.2 split into three — one table per Sub-step — and
  [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
  fired, moving the sqlglot spike out of Step 002 and into a future Step 003.
  Step 002 now has five Sub-steps: 2.1 `schema` ✅, 2.2 `dim_instrument` ✅ built,
  2.3 `fct_instrument_price`, 2.4 `fct_fx_rate`, 2.5 synthetic activity.
- **Awaiting Amino: the review and commit of Sub-step 2.2, and a ruling on
  [ADR-0004](../adr/0004-snapshot-and-replay-and-where-dlt-stops.md), which is
  `proposed`.** One judgement call in it is the one to check first: **2.2 reads
  Yahoo's `meta` block**, which the plan's shorthand did not list among its
  sources. Neither NASDAQ Trader file carries a currency column and the SEC file
  carries only a name and a key, so `quotation_currency` — and therefore the whole
  `GBp` trap — has no other source. `data-availability.md` already said so:
  *"Non-US Instruments (SAP.DE, VOD.L, 7203.T) come from the price source's own
  metadata, which returns exchange, currency and instrument type per symbol."*
  Sub-step 2.3 still loads the Market Price series; 2.2 reads only the metadata
  half of the same snapshot.
- Everything
  raised on 2026-08-05 and 2026-08-06 has been ruled on and applied — recorded as
  [R11–R15](../plan/step-002-warehouse-and-ingestion.md#r11r15--five-rulings-from-aminos-review-of-the-snapshot-design-2026-08-06)
  and argued in the [Step Review](../reviews/step-002-warehouse-and-ingestion.md).
  In short: `Cost Basis` and `Snapshot` registered and built, Snapshots are
  **end-of-day** and **dense over trading days**, the simulator will emit
  **transfers but not corporate actions**, [DEBT-010](../debt-ledger.md) was
  **paid** rather than deferred, and the two excluded halves went to
  [EXT-006](../extension-register.md#ext-006--position-change-attribution) and
  [EXT-007](../extension-register.md#ext-007--corporate-actions).
- **One spelling set is open to amendment, not blocking:** the `movement_type`
  values frozen by the new `CHECK` constraints. Free to change while the tables are
  empty, not free after **2.5** generates the Movements that fill them — see
  [DEBT-010](../debt-ledger.md).
- The four questions Sub-step 2.1 raised earlier were ruled on the same day and
  are recorded as
  [R7–R10](../plan/step-002-warehouse-and-ingestion.md#r7r10--four-rulings-from-writing-the-data-definition-language-ddl-2026-08-05):
  `Instrument Symbol`, `Denomination Currency` and `Trade Side` are registered
  and `agreed`; the instrument-type values were swept so the `Dimension
  Definition` row matches the narrowed `Instrument` row.
- **Next Sub-step:** 2.3 — load `fct_instrument_price` from Yahoo by
  snapshot-and-replay, and **pay [DEBT-002](../debt-ledger.md)** under its first
  trigger. Four things 2.2 leaves it:
  1. **The snapshots it needs already exist.** `data/snapshots/ingestion/` holds a
     full chart response per traded Instrument, fetched in 2.2 for the `meta`
     block. 2.3 reads the `timestamp` and `indicators` halves of the same files
     and needs no new fetch — one file, two halves, one Sub-step each.
  2. **The minor-unit factor is already declared and landed.**
     `MINOR_UNIT_CURRENCIES` in `veritas/ingestion/universe.py` carries
     `minor_units_per_major: 100`, and it reaches the Warehouse as
     `raw.minor_unit_currency`. 2.2 used only the code half; **2.3 must divide
     every `GBp` price by that factor** or the 100x error lands in the fact table
     rather than the dimension, where no constraint catches it.
  3. **Adding a source is a resource plus a build script.** Append to
     `FETCHED_TABLES` in `veritas/ingestion/__main__.py`, add
     `veritas/warehouse/builds/fct_instrument_price.sql`, and add its name to
     `BUILDS`. Nothing else changes — and the build SQL must stay inside
     `veritas/warehouse/`, which is what keeps [DEBT-009](../debt-ledger.md)
     unfired.
  4. `--sources` **must verify the loaded price window is split-free** for every
     held Instrument — a day-over-day ratio large enough to be a corporate action
     rather than a market move. R14 excluded corporate actions from the slice on
     the assumption that no loaded series contains one, and this is what turns
     that assumption into a check
     ([EXT-007](../extension-register.md#ext-007--corporate-actions)). **This is
     the assertion most likely to fail on first run** and to force a symbol swap
     in `TRADED_INSTRUMENTS`.
- **What Sub-step 2.5 must now implement rather than decide** (all settled as
  R12–R14; this was Sub-step 2.3 before the R16 split): Snapshots are end-of-day;
  dense, one row per subject on every date the
  Warehouse holds a Market Price for; and the simulator emits a handful of
  transfers so a Snapshot delta and a sum of Trades genuinely disagree somewhere.
  Two checks fall out of these and belong in `--distinctions`: every
  `snapshot_date` must exist in `fct_instrument_price.price_date`, and at least one
  account must show a Position Change that no Trade explains.
- **Also live from 2.1:** [DEBT-009](../debt-ledger.md) — the seam scan checks
  `duckdb` imports but not the DuckDB-specific function names ADR-0002 named
  alongside them.
- **Obligations recorded for later Steps**, so they are not rediscovered:
  `README.md` must list every credential Veritas touches
  ([Target State](target-state.md#what-credential-free-means)), and two Ledger
  entries fire on the same pass — [DEBT-002](../debt-ledger.md) on the
  reproducibility claim, [DEBT-008](../debt-ledger.md) on the access-control
  claim.

---

## Summary

A fully designed project with one component built and a second under way. The framework is in place and
the Target State is `agreed`, so there is a fixed point to build toward: a
natural-language analytics copilot over a brokerage warehouse, whose answers are
grounded in a certified Semantic Layer and checked by a deterministic Validation
Gate.

Every data source that design assumes has been verified obtainable, key-free, and
is snapshotted into the repository. **The Warehouse exists and has begun to
fill.** The ten-table star schema of Glossary Section B sits behind the Warehouse
Adapter — the only module in the repository that imports `duckdb` — and one of its
ten tables now holds real data: `dim_instrument`, nineteen Instruments across four
types and four Quotation Currencies, loaded offline from committed snapshots.
The other nine are empty. Nothing above Ingestion is built: no Semantic Layer, no
Retrieval, no application.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Two declared dependencies**: `duckdb==1.5.5` (2.1) and `dlt==1.29.1` (2.2). dlt brings roughly forty transitive packages, among them `sqlglot==30.15.0` — which is now installed a Step earlier than anything planned to use it, and makes [DEBT-009](../debt-ledger.md) cheaper to repay. The three framework check scripts remain stdlib-only. |
| Development framework | ✅ working | `CLAUDE.md`, `.claude/docs/` tree, five skills in `.claude/skills/`. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only (documents exist, links resolve, skills load, interpreter pinned), passes. |
| Language check | ✅ working | `.claude/scripts/check_language.py` — content rules: component names registered, no `proposed` term in code, abbreviations resolvable. Passes. Parses code with `ast` so it checks identifiers, not prose. Partial payment of [DEBT-001](../debt-ledger.md). |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`, **87 registered terms**. Sub-step 1.2 added `Market Price`, `Adjusted Close`, `Quotation Currency`; narrowed `Instrument`; renamed `dim_fx_rate` → `fct_fx_rate` and registered `fct_instrument_price`. Step 002 planning added `Execution Price` and its Section C row against `Market Price`. Sub-step 2.1 added `Instrument Symbol`, `Trade Side` and `Denomination Currency` (R7–R9), a Section C row for the last against `Quotation Currency`, and swept the `Dimension Definition` instrument-type values to match the narrowed `Instrument` row (R10); Amino's 2026-08-06 review added `Cost Basis` and its Section C row against `Execution Price`, and registered `Snapshot` (R11–R12). |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified, rulings R1–R3 applied. One correction 2026-08-05: no date dimension in the Warehouse row. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — 288 KB: real 2025 FX Rates and three real price series, plus the dated probe record. Committed on purpose: it is what makes the check reproduce without network access. |
| Founding ADRs | ✅ working | Three ADRs in `.claude/docs/adr/`, all **`accepted`** 2026-08-03: 0001 Semantic Layer as the retrieval corpus, 0002 DuckDB behind an adapter, 0003 Validation Gate as deterministic code. Every cost in each is classified *accepted* / *debt* / *extension*. A fourth — snapshot-and-replay — was deferred to the ingestion Step ([DEBT-002](../debt-ledger.md)), and is now due as ADR-0004 in Sub-step 2.2. ADR-0002 carries a dated clarification (2026-08-05) on what its sqlglot commitment forbids; its status stays `accepted`. |
| Warehouse | ✅ working | `veritas/warehouse/schema.sql` — the ten tables of Glossary Section B, empty. Monetary columns are `DECIMAL(18, 6)`, FX Rates `DECIMAL(18, 8)`; **no floating-point column exists** and `check_warehouse.py` fails the run if one appears. Foreign keys declared and enforced. Snapshot grain is one row per subject per date, enforced by the primary key. No `dim_date` (R2). |
| Warehouse Adapter | ✅ working | `veritas/warehouse/adapter.py` — the only module in the repository that imports `duckdb`, which is now checked rather than promised. `create_schema`, `tables`, `columns`, `row_count`, `execute`, `query`, plus the `in_memory()` constructor for throwaway databases. Assembles no SQL text from any argument: introspection goes through `information_schema` with a bound parameter, row counts through the relational API. Hardcoded database path and no error handling, both licensed in writing by [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md). |
| Warehouse check | ✅ working | `.claude/scripts/check_warehouse.py` — four checks always, plus `--sources`: the table set matches Glossary Section B *read from the Glossary*, no floating-point columns, fourteen constraint rejections fire against an in-memory Warehouse with a seven-row positive control, and no `duckdb` import outside `veritas/warehouse/`. `--rebuild` recreates the database; `--sources` (added 2.2) checks the loaded data, including a **richness** assertion that the traded universe is thick enough for Sub-step 2.5 — every instrument type present, at least two Instruments of each, at least three Quotation Currencies, one normalised from a minor unit. The two are mutually exclusive — together they only prove an empty table is empty. Grows in 2.3, 2.4 (`--sources`) and 2.5 (`--distinctions`). |
| Semantic Layer | ✗ none | — |
| Ingestion | ◐ partial | `veritas/ingestion/` — the pipeline and **one of its four sources**. `uv run python -m veritas.ingestion` builds the Warehouse end-to-end from a clean clone with **no network**; `--refresh` is the only mode that opens a socket, and a refresh that fails part-way names the snapshots it had already rewritten. dlt lands five `raw` tables, the adapter builds `dim_instrument` from them. Market Prices (2.3), FX Rates (2.4) and the synthetic half (2.5) are absent. |
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
├── data/
│   ├── snapshots/             # committed source data + dated probe record
│   │   └── ingestion/         # 2.6 MB, 22 files — ingestion's own snapshots (2.2)
│   └── veritas.duckdb         # the Warehouse — gitignored, rebuilt by ingestion
├── veritas/
│   ├── warehouse/
│   │   ├── adapter.py         # the Warehouse Adapter — the only duckdb importer
│   │   ├── schema.sql         # the ten-table star schema, hand-authored
│   │   └── builds/            # hand-authored raw→star SQL, one file per table
│   │       └── dim_instrument.sql
│   └── ingestion/
│       ├── __main__.py        # the entry point: replay by default, --refresh
│       ├── universe.py        # the 19 traded Instruments + two vocabulary maps
│       ├── snapshots.py       # snapshot-and-replay — the only socket in the package
│       └── sources.py         # NASDAQ Trader · SEC · Yahoo metadata, parsed for dlt
└── .claude/
    ├── skills/                # 5 framework skills
    ├── scripts/
    │   ├── verify_framework.py        # structure: docs, links, skills, interpreter
    │   ├── check_language.py          # content: Glossary + writing conventions
    │   ├── check_warehouse.py         # schema vs Glossary, constraints, adapter seam
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

**Everything above Ingestion**, and nine of the Warehouse's ten tables are still
at zero rows. Sub-step 2.3 fills `fct_instrument_price`, 2.4 fills `fct_fx_rate`
and 2.5 the six client-activity tables. Nothing blocks any of them.

**No number in the Warehouse is aggregatable yet.** `dim_instrument` is a
dimension: it names nineteen Instruments and says what currency each is quoted in.
Not one Market Price, FX Rate or Trade exists, so every Certified Metric still
returns nothing. That is the expected shape after 2.2 and it is worth stating
plainly, because "the Warehouse holds real data" could otherwise be read as more
than it is.

One thing 2.1 chose not to settle remains on the Ledger:
[DEBT-009](../debt-ledger.md) — the adapter seam scan checks `duckdb` imports but
not the DuckDB-specific function names ADR-0002 also named. **Its trigger came
close in 2.2 and did not fire**: the raw-to-star SQL lives in
`veritas/warehouse/builds/` rather than in `veritas/ingestion/`, so there is still
no component outside the adapter emitting SQL. [DEBT-010](../debt-ledger.md) was
**paid in 2.1** and both `movement_type` columns now carry a `CHECK`.

**The cost-basis gap is closed** (2026-08-06). This section previously read that
Realised and Unrealised P&L *"can both be expressed as a weighted average of
Execution Prices over `fct_trade`, so no column is needed"*. Amino's review asked
whether the snapshot design leaves any promised question unanswerable, and walking
all eight Certified Metrics against the ten tables showed that sentence was wrong:
the fold is valid only if a Position opened inside the loaded window, never went
flat and rebuilt, and was never touched by a transfer — the last being the very
thing `fct_position_snapshot` exists because it cannot promise. It is also unsafe
under a Dimension Definition filter, which would narrow `fct_trade` to the asked
period and build the basis from that period's buys alone. `Cost Basis` is now a
registered term and a column. `Realised P&L` needed no schema change — it is a
ledger posting, so it lands in `fct_accounting_movement` as a `movement_type`,
which is why [DEBT-010](../debt-ledger.md) was amended the same day.

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

**6 open debt** — see [debt-ledger.md](../debt-ledger.md) — plus **1 paid**, 1
accepted permanently and 2 moved out. **7 open extensions** — see
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
- **DEBT-009** — the adapter seam scan checks `duckdb` imports but not the
  DuckDB-specific function names ADR-0002 named alongside them. Fires when the
  first component outside the adapter emits SQL.
- **DEBT-010** — **paid 2026-08-06**, in the Sub-step that opened it. Both
  `movement_type` columns now carry a `CHECK`, and the two lists differ:
  `realised P&L` is accounting-only, `deposit` is cash-only. It was paid rather
  than deferred because its justification — *"nothing consumes the values yet"* —
  had been falsified by `Realised P&L` landing there.
- **EXT-006** — attributing a `Position Change` to its cause (Trade, transfer,
  corporate action). Opened 2026-08-06 against the `fct_position_snapshot` seam.
  The metric as registered promises the change, not the cause, so the slice is
  right as built; a reconciliation agent is what needs more.
- **EXT-007** — corporate actions. Opened 2026-08-06. In the full MVP's scope, but
  as something it must not *break* on rather than something it builds: Veritas
  reads a warehouse it did not populate, and a real one already records splits.

[DEBT-001](../debt-ledger.md)'s trigger **fired** in Sub-step 1.3 — a framework
rule agreed in 1.2 was broken in 1.3. Partially paid by `check_language.py` and
by new rules in `CLAUDE.md`; the hook layer is still unpaid.
