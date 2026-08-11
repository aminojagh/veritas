# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**Last updated:** 2026-08-11 — Sub-step 2.3 built, verified, and **reviewed and approved by Amino**; awaiting his commit. **The Warehouse now holds numbers that can be aggregated.**
**Steps completed:** Step 000 (framework) and Step 001, fully committed; Step 002 is in flight, **two of its five Sub-steps committed and a third built**. Step 000 and Sub-step 1.1 in `6281e6b`, Sub-step 1.2 in `4b48a46`, Sub-step 1.3 in `9c5b060`, Step 002 planning in `57e8aee`, Sub-step 2.1 in `5a061a7`, the R16 plan amendment in `cd5e7dd`, Sub-step 2.2 in `0fc5a34`.

---

## Resume here

- **Active Step:** 002 — Build the Warehouse and fill it
  ([plan](../plan/step-002-warehouse-and-ingestion.md)), approved 2026-08-05.
  **Sub-steps 2.1 (`5a061a7`) and 2.2 (`0fc5a34`) are committed**; the
  verification commands of each pass and their output is in the
  [review](../reviews/step-002-warehouse-and-ingestion.md).
- **The plan was amended and approved on 2026-08-10
  ([R16](../plan/step-002-warehouse-and-ingestion.md#r16--the-original-sub-step-22-splits-into-three--approved-by-amino-2026-08-10)).**
  The original Sub-step 2.2 split into three — one table per Sub-step — and
  [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
  fired, moving the sqlglot spike out of Step 002 and into a future Step 003.
  Step 002 now has five Sub-steps: 2.1 `schema` ✅, 2.2 `dim_instrument` ✅,
  2.3 `fct_instrument_price` ✅ built, 2.4 `fct_fx_rate`, 2.5 synthetic activity.
- **Awaiting Amino: the commit of Sub-step 2.3, and nothing else.** It was
  reviewed and approved on 2026-08-11 in two passes — two rulings, two rewrites,
  a widening of the second ruling and one Term Proposal approved — and all of it
  is applied. See
  [Changes made on review — 2026-08-11](../reviews/step-002-warehouse-and-ingestion.md#changes-made-on-review--2026-08-11).
  **No question is open.** Everything changed since the Sub-step was built is
  comment and document text; the four verification commands were re-run afterwards
  and produce the output the review records.
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
- **What to look at first in 2.3:** the three judgement calls in the
  [review](../reviews/step-002-warehouse-and-ingestion.md) — the `read_source`
  cache (a defect fix whose failure path is the one thing not exercised), the
  decision to store Yahoo's float32 artifacts verbatim (`213.309998`, not
  `213.31`), and the 1.5 corporate-action threshold. The first two were rewritten
  on 2026-08-11 at Amino's request: the seam argument is now spelled out from the
  beginning, and the float32 choice is argued from one worked example.
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
- **Next Sub-step:** 2.4 — load `fct_fx_rate` from Frankfurter, the last real
  source. Four things 2.3 leaves it:
  1. **Adding a source is still a resource plus a build script**, and 2.3 is the
     second worked example. Append to `FETCHED_TABLES` in
     `veritas/ingestion/__main__.py`, add
     `veritas/warehouse/builds/fct_fx_rate.sql`, add its name to `BUILDS`, and add
     a `check_...` function to `check_warehouse.py --sources`. Nothing else
     changes — and the build SQL must stay inside `veritas/warehouse/`, which is
     what keeps [DEBT-009](../debt-ledger.md) unfired.
  2. **2.4 is the natural place to run `--refresh` once, deliberately.** No
     Sub-step has run it since the cache landed in `read_source`, so the claim
     that a refresh fetches each source once rather than twice is argued and not
     executed. Frankfurter is a source with no snapshot yet, so 2.4 has to open a
     socket anyway — and doing it once, on purpose, is what closes the one gap
     2.3 hands over.
  3. **Fill FX Rates forward** across weekends and the six European Central Bank
     (ECB) holidays, and send a descriptive User-Agent — Frankfurter returns HTTP
     403 to the default `Python-urllib`. Both are already in the plan; the second
     is already how `snapshots.fetch` behaves.
  4. **The price window is 2024-08-08 to 2026-08-10.** `frankfurter-2025.json`
     covers 2025 only, so 2.4 chooses whether to widen the FX window to match the
     prices or to narrow what 2.5 may use. The Section C distinction between Trade
     Date and Settlement Date needs a rate on both dates of every Trade, so this
     is a decision about 2.5's usable window rather than a loading detail.
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
  exchange calendars, and 2.3's data makes the gap concrete: **521 dates carry a
  price for at least one Instrument, 452 for all nineteen.** A Snapshot on one of
  the 69 dates in between marks some Positions against a price and others against
  nothing. `check_warehouse.py --sources` prints both numbers on every run so the
  choice is made deliberately rather than discovered.
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

A fully designed project with one component built and a second under way. The framework is in place and
the Target State is `agreed`, so there is a fixed point to build toward: a
natural-language analytics copilot over a brokerage warehouse, whose answers are
grounded in a certified Semantic Layer and checked by a deterministic Validation
Gate.

Every data source that design assumes has been verified obtainable, key-free, and
is snapshotted into the repository. **The Warehouse exists and is half filled with
real market data.** The ten-table star schema of Glossary Section B sits behind
the Warehouse Adapter — the only module in the repository that imports `duckdb` —
and two of its ten tables now hold real data: `dim_instrument`, nineteen
Instruments across four types and four Quotation Currencies, and
`fct_instrument_price`, 9,549 daily Market Prices covering all nineteen of them
from 2024-08-08 to 2026-08-10. Both load offline from committed snapshots, with no
socket opened. The other eight are empty. Nothing above Ingestion is built: no
Semantic Layer, no Retrieval, no application.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Two declared dependencies**: `duckdb==1.5.5` (2.1) and `dlt==1.29.1` (2.2). dlt brings roughly forty transitive packages, among them `sqlglot==30.15.0` — which is now installed a Step earlier than anything planned to use it, and makes [DEBT-009](../debt-ledger.md) cheaper to repay. The three framework check scripts remain stdlib-only. |
| Development framework | ✅ working | `CLAUDE.md`, `.claude/docs/` tree, five skills in `.claude/skills/`. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only (documents exist, links resolve, skills load, interpreter pinned), passes. |
| Language check | ✅ working | `.claude/scripts/check_language.py` — content rules: component names registered, no `proposed` term in code, abbreviations resolvable. Passes. Parses code with `ast` so it checks identifiers, not prose. Partial payment of [DEBT-001](../debt-ledger.md). |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`, **88 registered terms** as counted by `check_language.py`. The most recent is not a Domain Language term but an abbreviation: **NYSE** — New York Stock Exchange — **approved 2026-08-11**, added when R18 moved the reasoning about NASDAQ Trader's second file out of a code comment and into the Step Review, where the abbreviation checker reads it. The same ruling rewrote the `Adjusted Close` / `Market Price` Section C row so its 95.5% divergence figure is dated evidence with the command that reproduces it rather than a standing claim. Sub-step 1.2 added `Market Price`, `Adjusted Close`, `Quotation Currency`; narrowed `Instrument`; renamed `dim_fx_rate` → `fct_fx_rate` and registered `fct_instrument_price`. Step 002 planning added `Execution Price` and its Section C row against `Market Price`. Sub-step 2.1 added `Instrument Symbol`, `Trade Side` and `Denomination Currency` (R7–R9), a Section C row for the last against `Quotation Currency`, and swept the `Dimension Definition` instrument-type values to match the narrowed `Instrument` row (R10); Amino's 2026-08-06 review added `Cost Basis` and its Section C row against `Execution Price`, and registered `Snapshot` (R11–R12). |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified, rulings R1–R3 applied. One correction 2026-08-05: no date dimension in the Warehouse row. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — 288 KB: real 2025 FX Rates and three real price series, plus the dated probe record. Committed on purpose: it is what makes the check reproduce without network access. |
| Founding ADRs | ✅ working | Four ADRs in `.claude/docs/adr/`, all **`accepted`**. The first three on 2026-08-03: 0001 Semantic Layer as the retrieval corpus, 0002 DuckDB behind an adapter, 0003 Validation Gate as deterministic code. The fourth — snapshot-and-replay, and where dlt stops — was deferred to the ingestion Step ([DEBT-002](../debt-ledger.md)), written in Sub-step 2.2 and **accepted 2026-08-11** (R17). Every cost in each is classified *accepted* / *debt* / *extension*. ADR-0002 carries a dated clarification (2026-08-05) on what its sqlglot commitment forbids; its status stays `accepted`. |
| Warehouse | ✅ working | `veritas/warehouse/schema.sql` — the ten tables of Glossary Section B, empty. Monetary columns are `DECIMAL(18, 6)`, FX Rates `DECIMAL(18, 8)`; **no floating-point column exists** and `check_warehouse.py` fails the run if one appears. Foreign keys declared and enforced. Snapshot grain is one row per subject per date, enforced by the primary key. No `dim_date` (R2). |
| Warehouse Adapter | ✅ working | `veritas/warehouse/adapter.py` — the only module in the repository that imports `duckdb`, which is now checked rather than promised. `create_schema`, `tables`, `columns`, `row_count`, `execute`, `query`, plus the `in_memory()` constructor for throwaway databases. Assembles no SQL text from any argument: introspection goes through `information_schema` with a bound parameter, row counts through the relational API. Hardcoded database path and no error handling, both licensed in writing by [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md). |
| Warehouse check | ✅ working | `.claude/scripts/check_warehouse.py` — four checks always, plus `--sources`: the table set matches Glossary Section B *read from the Glossary*, no floating-point columns, fourteen constraint rejections fire against an in-memory Warehouse with a seven-row positive control, and no `duckdb` import outside `veritas/warehouse/`. `--rebuild` recreates the database; `--sources` checks the loaded data, one function per star table. For `dim_instrument` (2.2): normalisation, the declared universe, every raw table non-empty, and a **richness** assertion that the universe is thick enough for 2.5. For `fct_instrument_price` (2.3): every price is **re-derived from the committed snapshots in Python** and compared row-for-row against what the SQL built, three named wrong readings are shown to change real rows, and no day-over-day move exceeds 1.5. `--rebuild` and `--sources` are mutually exclusive — together they only prove an empty table is empty. Grows in 2.4 (`--sources`) and 2.5 (`--distinctions`). |
| Semantic Layer | ✗ none | — |
| Ingestion | ◐ partial | `veritas/ingestion/` — the pipeline and **two of its four sources**. `uv run python -m veritas.ingestion` builds the Warehouse end-to-end from a clean clone with **no network**, and two consecutive runs produce identical output. `--refresh` is the only mode that opens a socket; a refresh that fails part-way names the snapshots it had already rewritten, and `read_source` caches so a source is fetched once per run however many resources read it (**this caching is verified by reading, not by running — see the 2.3 review**). dlt lands six `raw` tables; the adapter builds `dim_instrument` and `fct_instrument_price` from them. FX Rates (2.4) and the synthetic half (2.5) are absent. |
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
│   │       ├── dim_instrument.sql
│   │       └── fct_instrument_price.sql
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

**Everything above Ingestion**, and eight of the Warehouse's ten tables are still
at zero rows. Sub-step 2.4 fills `fct_fx_rate` and 2.5 the six client-activity
tables. Nothing blocks either of them.

**No Certified Metric returns a number yet, and the reason has changed.** After
2.2 it was that nothing aggregatable existed at all. After 2.3 the Warehouse holds
9,549 Market Prices — real, checked, aggregatable — but every metric the Glossary
registers is about *client activity*: Traded Notional, Gross and Net Revenue,
Realised and Unrealised P&L. Not one Trade, Position or Cash Movement exists, so a
metric still returns nothing. What 2.3 bought is the price side of every mark:
after 2.5, a Position has something real to be marked against. Worth stating
plainly, because "the Warehouse holds real market data" is true and is not the
same claim as "the Warehouse can answer a question".

**No FX Rate exists**, so nothing can yet be converted to a Reporting Currency —
which is 2.4, and is why prices in four Quotation Currencies is not yet a book
anyone can total.

One thing 2.1 chose not to settle remains on the Ledger:
[DEBT-009](../debt-ledger.md) — the adapter seam scan checks `duckdb` imports but
not the DuckDB-specific function names ADR-0002 also named. **Its trigger came
close again in 2.3 and again did not fire**: `fct_instrument_price.sql` lives in
`veritas/warehouse/builds/` beside `dim_instrument.sql`, so there is still no
component outside the adapter emitting SQL. The build does now use a
DuckDB-specific function — `make_timestamp`, chosen over the portable-looking
`to_timestamp` precisely because the latter's result depends on a session setting
— which is the first concrete example of what repaying that debt would have to
scan for. It sits inside the adapter's directory, so it is licensed. [DEBT-010](../debt-ledger.md) was **paid in
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

**The wrong-number traps are now defended in the Warehouse itself, not only in the
spike.** `check_data_availability.py` measured two of them on three probe series;
`check_warehouse.py --sources` now measures them on everything loaded, by
re-deriving all 9,549 prices from the snapshots in Python and reporting what each
wrong reading would have changed: `Adjusted Close` instead of the unadjusted close
moves **5,416 of 9,549 rows (57%)**, pence carried across as pounds moves **1,006
(11%)**. A third trap was found by writing this Sub-step rather than inherited from
the spike — reading a bar's timestamp as a Coordinated Universal Time (UTC) date
instead of the exchange's own moves **1,075 rows (11%)** and would have booked
every currency-pair price one day early. A fourth gotcha is recorded in
[data-availability.md](data-availability.md): Frankfurter returns HTTP 403 to
the default `Python-urllib` User-Agent, which reads as "blocked" when the fix is
one header — 2.4's problem, and already how `snapshots.fetch` behaves.

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
