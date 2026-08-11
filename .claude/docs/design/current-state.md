# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**Last updated:** 2026-08-11 — Sub-step 2.4 reviewed and **approved**; its one open question ruled on as [R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11). **The real half of Ingestion is complete: every Market Price in the Warehouse can now be converted to a Reporting Currency.**
**Steps completed:** Step 000 (framework) and Step 001, fully committed; Step 002 is in flight, **four of its five Sub-steps built and approved**. Step 000 and Sub-step 1.1 in `6281e6b`, Sub-step 1.2 in `4b48a46`, Sub-step 1.3 in `9c5b060`, Step 002 planning in `57e8aee`, Sub-step 2.1 in `5a061a7`, the R16 plan amendment in `cd5e7dd`, Sub-step 2.2 in `0fc5a34`, Sub-step 2.3 in `a58ef91`, **Sub-step 2.4 in `13b99bb`** — squashed onto `main` from the `worktree-substep-2-4-fx-rate` branch, carrying the implementation, its review, and the R19/R20 edits together. The worktree is gone and the working tree is clean, so **nothing is uncommitted**.

---

## Resume here

- **Active Step:** 002 — Build the Warehouse and fill it
  ([plan](../plan/step-002-warehouse-and-ingestion.md)), approved 2026-08-05.
  **All four built Sub-steps are committed on `main`** — 2.1 (`5a061a7`), 2.2
  (`0fc5a34`), 2.3 (`a58ef91`), 2.4 (`13b99bb`); the verification commands of
  each pass and their output is in the
  [review](../reviews/step-002-warehouse-and-ingestion.md).
- **The plan was amended and approved on 2026-08-10
  ([R16](../plan/step-002-warehouse-and-ingestion.md#r16--the-original-sub-step-22-splits-into-three--approved-by-amino-2026-08-10)).**
  The original Sub-step 2.2 split into three — one table per Sub-step — and
  [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
  fired, moving the sqlglot spike out of Step 002 and into a future Step 003.
  Step 002 now has five Sub-steps: 2.1 `schema` ✅, 2.2 `dim_instrument` ✅,
  2.3 `fct_instrument_price` ✅, 2.4 `fct_fx_rate` ✅ approved, 2.5 synthetic
  activity — the only one left.
- **Sub-step 2.4 is approved, and no question is open.** Four verification commands
  pass and their output is in the
  [Sub-step 2.4 section of the review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-24--load-fct_fx_rate-from-frankfurter).
- **The Glossary question is settled:
  [R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11).**
  `FX Rate` was registered as *"Real ECB reference rate between two currencies on a
  date"*, which read both ways once the table held all sixteen ordered pairs: twelve
  are rates the European Central Bank (ECB) published, and the four between two
  non-euro currencies are a **ratio of two** published rates. Amino ruled that the
  four **stay** and the definition is widened to say so. The Glossary row now
  separates the two cases and keeps the source exclusivity — *"a rate of any other
  origin is not one"*. **Nothing that executes changed**: the `WHERE` clause the
  review had costed was never written, `fct_fx_rate` still holds every ordered pair
  it held before the ruling, and the four verification commands were re-run to prove
  it — `check_warehouse.py --sources` prints the current row count. Two documents that restated the old
  wording came with it — the `fct_fx_rate` header in `schema.sql` and a
  paraphrase-in-quotes in `data-availability.md`. Applied under
  [Changes made on review — 2026-08-11 (Sub-step 2.4)](../reviews/step-002-warehouse-and-ingestion.md#changes-made-on-review--2026-08-11-sub-step-24).
- **One framework gap was found and closed in the same pass:
  [R20](../plan/step-002-warehouse-and-ingestion.md#r20--verify_frameworkpy-checks-anchors-not-just-files--approved-by-amino-2026-08-11).**
  Confirming that R19's own new links resolved revealed that
  `verify_framework.py` validated the file half of a link and threw the `#anchor`
  away. It now checks both, and was verified by being made to fail. **This is not
  payment against [DEBT-001](../debt-ledger.md)** — that entry's unpaid half is
  hooks enforcing *compliance*, and its own text already credits this script with
  checking that the documents are wired together. R20 makes an existing check
  honest; it does not add a new kind of enforcement.
- **What was looked at first in 2.4, and survived review:** the decision to store
  **all sixteen ordered currency pairs** rather than the four against the euro, and
  the fact that `fct_fx_rate.sql` reads two tables built before it — its currencies
  from `dim_instrument`, its window end from `fct_instrument_price` — with **no
  foreign key to enforce that order**. Both are argued in the review; the second is
  still the first item under *Look at this sceptically*, and is mitigated by comment
  in `BUILDS` rather than by structure.
- **A `--refresh` was run on 2026-08-11, and it moved figures 2.3 had measured.**
  This was the gap 2.3 handed over on purpose. Yahoo's `2y` range is relative to
  the moment it is asked, so the price window slid forward a day and dropped four
  at the front, and every count and trap size 2.3 recorded moved with it. **The 2.3
  review's numbers were not corrected** — they are dated evidence, true on
  2026-08-10, and carry the command that produced them. Everything below that
  quoted them as standing facts was. Which figures moved, and by how much, is the
  table in the review under *The refresh, and what it cost*.
- **[ADR-0004](../adr/0004-snapshot-and-replay-and-where-dlt-stops.md) is
  `accepted`**, dated 2026-08-11
  ([R17](../plan/step-002-warehouse-and-ingestion.md#r17--adr-0004-is-accepted--approved-by-amino-2026-08-11)).
  It was left `proposed` while the Sub-step that wrote it was committed and 2.3
  built on both of its decisions; Current State flagged the stale status rather
  than flipping it, and Amino settled it. Its Decision and Consequences are
  unchanged.
- **A measurement is dated evidence, and lives in a review**
  ([R18](../plan/step-002-warehouse-and-ingestion.md#r18--a-measurement-is-dated-evidence-and-lives-in-a-review--approved-by-amino-2026-08-11)),
  now a [writing convention in CLAUDE.md](../../../CLAUDE.md#writing-conventions).
  Any figure a later run could refute or resize is written as evidence — what was
  measured, when, under what settings, and the command that reproduces it — kept
  in the Step Review that produced it, with code, the Glossary and ADRs referring
  to it. **Two sweeps applied it:** ten run-contingent comments across five files,
  one of which had already been false since 2.2; then `schema.sql` and the
  Glossary's `Adjusted Close` row, which both carried the 95.5% divergence figure
  as a bare fact. No measurement remains in `veritas/` or `.claude/scripts/`.
- **The `read_source` cache is now checked rather than argued.** 2.3 could only
  reason that a refresh fetches each source once however many resources read it;
  `--refresh` now prints how many snapshots it rewrote and how many were distinct,
  and fails the run if any name appears twice. It reports `rewrote 23
  snapshot(s), 23 distinct`.
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
- **Next Sub-step:** 2.5 — the seeded synthetic client activity, and the last of
  Step 002. It is the only Sub-step that writes no real source: the six
  client-activity tables all come from the simulator. Four things 2.4 leaves it:
  1. **Every Section C conversion now has real rates behind it.** A Trade converts
     from its Denomination Currency, a Position marks at a Market Price and
     converts from its Quotation Currency, and Trade Date against Settlement Date
     selects a *different* rate — the second half of what the Glossary says that
     distinction moves.
  2. **2.5's Denomination Currencies must stay inside the four the Warehouse
     quotes in** (EUR, GBP, JPY, USD), or `fct_fx_rate` must be widened first. Its
     currency set is read from `dim_instrument.quotation_currency`, so a Trade
     billed in a currency no Instrument is quoted in would have no rate and its
     Gross Revenue could not reach a Reporting Currency. Nothing catches this
     today — the coverage assertion only walks Market Prices — and the natural
     place for the check is beside it, once a Trade exists to assert against.
  3. **The FX window ends on the same day as the price window** (both 2026-08-10)
     and starts eleven days before it. A Trade in the last two days of the window
     settles at T+2 past the last rate, so 2.5 keeps its Trades clear of the end
     or the window is widened.
  4. **Adding a source is a resource plus a build script**, now with three worked
     examples. The build SQL must stay inside `veritas/warehouse/`, which is what
     keeps [DEBT-009](../debt-ledger.md) unfired.
- **What Sub-step 2.5 must now implement rather than decide** (all settled as
  R12–R14; this was Sub-step 2.3 before the R16 split): Snapshots are end-of-day;
  dense, one row per subject on every date the
  Warehouse holds a Market Price for; and the simulator emits a handful of
  transfers so a Snapshot delta and a sum of Trades genuinely disagree somewhere.
  Two checks fall out of these and belong in `--distinctions`: every
  `snapshot_date` must exist in `fct_instrument_price.price_date`, and at least one
  account must show a Position Change that no Trade explains.
- **One thing 2.5 must now decide that R13 did not anticipate.** *"Every date the
  Warehouse holds a Market Price for"* has two readings once the table spans five
  exchange calendars: the dates on which *some* Instrument has a price, and the
  dates on which *every* Instrument does. They differ by dozens of dates, and a
  Snapshot on one of the dates in between marks some Positions against a price and
  others against nothing. `check_warehouse.py --sources` prints both numbers on
  every run so the choice is made deliberately rather than discovered.
- **Also live from 2.1:** [DEBT-009](../debt-ledger.md) — the seam scan checks
  `duckdb` imports but not the DuckDB-specific function names ADR-0002 named
  alongside them.
- **Obligations recorded for later Steps**, so they are not rediscovered:
  `README.md` must list every credential Veritas touches
  ([Target State](target-state.md#what-credential-free-means)), and
  [DEBT-008](../debt-ledger.md) fires on the same pass, on the access-control
  claim. [DEBT-002](../debt-ledger.md) was **paid in 2.3** and no longer waits for
  the README — but it constrains what the README may say: *reproducible from
  committed snapshots*, never *reproducible from Yahoo*.

---

## Summary

A fully designed project with one component built and a second nearly so. The framework is in place and
the Target State is `agreed`, so there is a fixed point to build toward: a
natural-language analytics copilot over a brokerage warehouse, whose answers are
grounded in a certified Semantic Layer and checked by a deterministic Validation
Gate.

Every data source that design assumes has been verified obtainable, key-free, and
is snapshotted into the repository. **The Warehouse exists and holds all the real
market data it will ever hold.** The ten-table star schema of Glossary Section B
sits behind the Warehouse Adapter — the only module in the repository that imports
`duckdb` — and three of its ten tables now hold real data: `dim_instrument`,
nineteen Instruments across four types and four Quotation Currencies;
`fct_instrument_price`, two years of daily Market Prices covering all nineteen of
them; and `fct_fx_rate`, every ordered pair of those four currencies on every
calendar date of a window that covers the prices. All three load offline from
committed snapshots, with no socket opened, and **every Market Price can now be
converted to a Reporting Currency** — the row counts and windows are dated evidence
in the [Step Review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-24--load-fct_fx_rate-from-frankfurter),
because a `--refresh` moves them. The other seven tables are empty and all seven
are Sub-step 2.5's. Nothing above Ingestion is built: no Semantic Layer, no
Retrieval, no application.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Two declared dependencies**: `duckdb==1.5.5` (2.1) and `dlt==1.29.1` (2.2). dlt brings roughly forty transitive packages, among them `sqlglot==30.15.0` — which is now installed a Step earlier than anything planned to use it, and makes [DEBT-009](../debt-ledger.md) cheaper to repay. The three framework check scripts remain stdlib-only. |
| Development framework | ✅ working | `CLAUDE.md`, `.claude/docs/` tree, five skills in `.claude/skills/`. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only (documents exist, links resolve, skills load, interpreter pinned), passes. **Links now include their `#anchor`** ([R20](../plan/step-002-warehouse-and-ingestion.md#r20--verify_frameworkpy-checks-anchors-not-just-files--approved-by-amino-2026-08-11), 2026-08-11): the fragment used to be split off and discarded, so a link to a renamed heading passed, and same-document `#anchor` links were not checked at all. It reports a `dead anchor` distinct from a `dead link` and prints how many links and anchors it checked. Verified by making it fail against a temporary document with two dead anchors, in the [Sub-step 2.4 changes-on-review section](../reviews/step-002-warehouse-and-ingestion.md#changes-made-on-review--2026-08-11-sub-step-24). Scope is `.claude/docs/**` plus `CLAUDE.md`; `README.md` is outside it. |
| Language check | ✅ working | `.claude/scripts/check_language.py` — content rules: component names registered, no `proposed` term in code, abbreviations resolvable. Passes. Parses code with `ast` so it checks identifiers, not prose. Partial payment of [DEBT-001](../debt-ledger.md). |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`, **88 registered terms** as counted by `check_language.py`. **The most recent change is an amendment rather than a registration, so the count is unchanged**: `FX Rate`, clarified 2026-08-11 under [R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11), now says in its own words that a euro-side pair *is* a published ECB reference rate while a pair between two non-euro currencies is the ratio of that date's two published rates — both are FX Rates, and a rate of any other origin is not one. The most recent *addition* is not a Domain Language term but an abbreviation: **NYSE** — New York Stock Exchange — **approved 2026-08-11**, added when R18 moved the reasoning about NASDAQ Trader's second file out of a code comment and into the Step Review, where the abbreviation checker reads it. The same ruling rewrote the `Adjusted Close` / `Market Price` Section C row so its 95.5% divergence figure is dated evidence with the command that reproduces it rather than a standing claim. Sub-step 1.2 added `Market Price`, `Adjusted Close`, `Quotation Currency`; narrowed `Instrument`; renamed `dim_fx_rate` → `fct_fx_rate` and registered `fct_instrument_price`. Step 002 planning added `Execution Price` and its Section C row against `Market Price`. Sub-step 2.1 added `Instrument Symbol`, `Trade Side` and `Denomination Currency` (R7–R9), a Section C row for the last against `Quotation Currency`, and swept the `Dimension Definition` instrument-type values to match the narrowed `Instrument` row (R10); Amino's 2026-08-06 review added `Cost Basis` and its Section C row against `Execution Price`, and registered `Snapshot` (R11–R12). |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified, rulings R1–R3 applied. One correction 2026-08-05: no date dimension in the Warehouse row. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — real 2025 FX Rates and three real price series, plus the dated probe record, owned by `check_data_availability.py`. `data/snapshots/ingestion/` beside it is the pipeline's own, one file per source and one per traded Instrument, rewritten only by `--refresh`. Both committed on purpose: they are what make the checks reproduce without network access. |
| Founding ADRs | ✅ working | Four ADRs in `.claude/docs/adr/`, all **`accepted`**. The first three on 2026-08-03: 0001 Semantic Layer as the retrieval corpus, 0002 DuckDB behind an adapter, 0003 Validation Gate as deterministic code. The fourth — snapshot-and-replay, and where dlt stops — was deferred to the ingestion Step ([DEBT-002](../debt-ledger.md)), written in Sub-step 2.2 and **accepted 2026-08-11** (R17). Every cost in each is classified *accepted* / *debt* / *extension*. ADR-0002 carries a dated clarification (2026-08-05) on what its sqlglot commitment forbids; its status stays `accepted`. |
| Warehouse | ✅ working | `veritas/warehouse/schema.sql` — the ten tables of Glossary Section B, empty. Monetary columns are `DECIMAL(18, 6)`, FX Rates `DECIMAL(18, 8)`; **no floating-point column exists** and `check_warehouse.py` fails the run if one appears. Foreign keys declared and enforced. Snapshot grain is one row per subject per date, enforced by the primary key. No `dim_date` (R2). |
| Warehouse Adapter | ✅ working | `veritas/warehouse/adapter.py` — the only module in the repository that imports `duckdb`, which is now checked rather than promised. `create_schema`, `tables`, `columns`, `row_count`, `execute`, `query`, plus the `in_memory()` constructor for throwaway databases. Assembles no SQL text from any argument: introspection goes through `information_schema` with a bound parameter, row counts through the relational API. Hardcoded database path and no error handling, both licensed in writing by [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md). |
| Warehouse check | ✅ working | `.claude/scripts/check_warehouse.py` — four checks always, plus `--sources`: the table set matches Glossary Section B *read from the Glossary*, no floating-point columns, fourteen constraint rejections fire against an in-memory Warehouse with a seven-row positive control, and no `duckdb` import outside `veritas/warehouse/`. `--rebuild` recreates the database; `--sources` checks the loaded data, one function per star table. For `dim_instrument` (2.2): normalisation, the declared universe, every raw table non-empty, and a **richness** assertion that the universe is thick enough for 2.5. For `fct_instrument_price` (2.3): every price is **re-derived from the committed snapshots in Python** and compared row-for-row against what the SQL built, three named wrong readings are shown to change real rows, and no day-over-day move exceeds 1.5. For `fct_fx_rate` (2.4): every rate is re-derived the same way, two named wrong readings are shown to change real rows, **every Market Price has a rate in its own Quotation Currency on its own date**, and a currency converted through another and back is unchanged within the rounding its stored scale forces. `--rebuild` and `--sources` are mutually exclusive — together they only prove an empty table is empty. Grows in 2.5 (`--distinctions`). |
| Semantic Layer | ✗ none | — |
| Ingestion | ◐ partial | `veritas/ingestion/` — the pipeline and **all four of its real sources**; only the synthetic half (2.5) is absent. `uv run python -m veritas.ingestion` builds the Warehouse end-to-end from a clean clone with **no network**, and two consecutive runs produce identical output. `--refresh` is the only mode that opens a socket; a refresh that fails part-way names the snapshots it had already rewritten, and one that succeeds reports how many it rewrote and how many were distinct — **failing the run if a source was fetched twice**, which is what turned 2.3's argument about the `read_source` cache into a check. dlt lands seven `raw` tables; the adapter builds `dim_instrument`, `fct_instrument_price` and `fct_fx_rate` from them, in that order, because the last takes its currencies and its window from the two before it. |
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
│   │   └── ingestion/         # ingestion's own snapshots — one per source, one
│   │                          # per traded Instrument; only --refresh writes here
│   └── veritas.duckdb         # the Warehouse — gitignored, rebuilt by ingestion
├── veritas/
│   ├── warehouse/
│   │   ├── adapter.py         # the Warehouse Adapter — the only duckdb importer
│   │   ├── schema.sql         # the ten-table star schema, hand-authored
│   │   └── builds/            # hand-authored raw→star SQL, one file per table
│   │       ├── dim_instrument.sql
│   │       ├── fct_instrument_price.sql
│   │       └── fct_fx_rate.sql
│   └── ingestion/
│       ├── __main__.py        # the entry point: replay by default, --refresh
│       ├── universe.py        # the 19 traded Instruments + two vocabulary maps
│       ├── snapshots.py       # snapshot-and-replay — the only socket in the package
│       └── sources.py         # NASDAQ Trader · SEC · Yahoo metadata and bars, for dlt
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

**Everything above Ingestion**, and seven of the Warehouse's ten tables are still
at zero rows. **All seven are Sub-step 2.5's**, and nothing blocks it.

**No Certified Metric returns a number yet, and the reason has narrowed twice.**
After 2.2 it was that nothing aggregatable existed at all. After 2.3 the Warehouse
held real, checked, aggregatable Market Prices — but in four Quotation Currencies
with no way to total them. After 2.4 that last obstacle is gone: every price
converts. What remains is the whole of the client side. Every metric the Glossary
registers is about *client activity* — Traded Notional, Gross and Net Revenue,
Realised and Unrealised P&L — and not one Trade, Position or Cash Movement exists,
so a metric still returns nothing. What 2.3 and 2.4 bought is both halves of every
mark: after 2.5, a Position has something real to be marked against **and** a
currency to be reported in. Worth stating plainly, because "the Warehouse holds
real market data" is true and is not the same claim as "the Warehouse can answer a
question".

One thing 2.1 chose not to settle remains on the Ledger:
[DEBT-009](../debt-ledger.md) — the adapter seam scan checks `duckdb` imports but
not the DuckDB-specific function names ADR-0002 also named. **Its trigger came
close again in 2.4 and again did not fire**: all three build scripts live in
`veritas/warehouse/builds/`, so there is still no component outside the adapter
emitting SQL. What has changed is the size of what repaying it would have to scan
for. 2.3 added one DuckDB-specific name, `make_timestamp`; 2.4 added two more,
`generate_series` over dates and `ASOF JOIN` — the latter being the Glossary's
fill-forward sentence written as an operator. All three sit inside the adapter's
directory, so all three are licensed. [DEBT-010](../debt-ledger.md) was **paid in
2.1** and both `movement_type` columns now carry a `CHECK`;
[DEBT-002](../debt-ledger.md) was **paid in 2.3**, under its first trigger.

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

**The wrong-number traps are defended in the Warehouse itself, not only in the
spike.** `check_data_availability.py` measured two of them on three probe series;
`check_warehouse.py --sources` measures **five** on everything loaded, by
re-deriving every price and every rate from the snapshots in Python and printing
what each wrong reading would have changed. How many rows each moves is a
measurement, so it lives in the Step Review with the command and the date, and the
check prints the current figure on every run. The five:

| Trap | Where it would land |
|---|---|
| `Adjusted Close` instead of the unadjusted close | `fct_instrument_price` — the Section C row for `Market Price` |
| A pence quote carried across as pounds | `fct_instrument_price` — a 100× error, `Quotation Currency` |
| A bar's timestamp read as a Coordinated Universal Time (UTC) date rather than the exchange's own | `fct_instrument_price` — every currency-pair price booked one day early. Found by writing 2.3, not inherited from the spike |
| Rates stored only for the dates the ECB published on | `fct_fx_rate` — every weekend and ECB-holiday Position converted at nothing |
| A published rate read upside down | `fct_fx_rate` — every conversion inverted |

A sixth gotcha is recorded in [data-availability.md](data-availability.md):
Frankfurter returns HTTP 403 to the default `Python-urllib` User-Agent, which reads
as "blocked" when the fix is one header. `snapshots.fetch` sends a descriptive one,
which is why 2.4 hit it nowhere.

## Open debt and extensions

**5 open debt** — see [debt-ledger.md](../debt-ledger.md) — plus **2 paid**, 1
accepted permanently and 2 moved out. **7 open extensions** — see
[extension-register.md](../extension-register.md).

The split is new as of 2026-08-04. Debt means the current code is *wrong,
cheaply*; an extension means it is *right for this scope* and the full system
needs more. The test that settles it: does the trigger fire inside this project's
life? Three Sub-step 1.3 entries failed that test and moved.

- **DEBT-001** — framework rules rely on discipline, not enforcement.
- **DEBT-002** — **paid 2026-08-10** in Sub-step 2.3, under its first trigger. The
  market-price pipeline was written and the snapshot was already behind it, so a
  clean clone builds the whole Warehouse with the network off. The dependency is
  mitigated rather than removed: the endpoint is still needed to *refresh*, and a
  stale snapshot is still silent.
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
  **Its assumption is now checked rather than asserted**: R14 excluded corporate
  actions on the ground that no loaded price series contains one, and
  `--sources` fails the run if any day-over-day ratio exceeds 1.5. The largest in
  the currently loaded window is 1.196.

[DEBT-001](../debt-ledger.md)'s trigger **fired** in Sub-step 1.3 — a framework
rule agreed in 1.2 was broken in 1.3. Partially paid by `check_language.py` and
by new rules in `CLAUDE.md`; the hook layer is still unpaid.
