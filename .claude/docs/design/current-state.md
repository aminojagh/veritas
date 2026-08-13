# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**Last updated:** 2026-08-13 — Sub-step 2.5 committed; Sub-step 2.6 built and awaiting Amino's review. **The Warehouse is full: all ten tables of Glossary Section B hold rows, every Certified Metric can return a number, and the adapter seam is now checked in both the halves ADR-0002 named.**
**Steps completed:** Step 000 (framework) and Step 001, fully committed; **Step 002 is built end to end, all six Sub-steps**, five of them committed. Step 000 and Sub-step 1.1 in `6281e6b`, Sub-step 1.2 in `4b48a46`, Sub-step 1.3 in `9c5b060`, Step 002 planning in `57e8aee`, Sub-step 2.1 in `5a061a7`, the R16 plan amendment in `cd5e7dd`, Sub-step 2.2 in `0fc5a34`, Sub-step 2.3 in `a58ef91`, Sub-step 2.4 in `13b99bb`, Sub-step 2.5 in `ce2961a`. **Sub-step 2.6 is uncommitted** and is what this session leaves for him.

---

## Resume here

- **Active Step:** 002 — Build the Warehouse and fill it
  ([plan](../plan/step-002-warehouse-and-ingestion.md)), approved 2026-08-05.
  **All six Sub-steps are built.** 2.1 (`5a061a7`), 2.2 (`0fc5a34`), 2.3
  (`a58ef91`), 2.4 (`13b99bb`) and 2.5 (`ce2961a`) are committed on `main` and
  approved; **2.6 is built and uncommitted**. The verification commands of each
  pass and their output is in the
  [review](../reviews/step-002-warehouse-and-ingestion.md). **The plan is closed
  out at `in review`** and becomes `done` when 2.6 lands — nothing in the Step is
  outstanding besides that one commit.
- **Next, in this order:**
  1. **Amino reviews and commits Sub-step 2.6** — see the
     [review entry](../reviews/step-002-warehouse-and-ingestion.md#sub-step-26--scan-for-duckdb-specific-function-names-outside-the-adapter).
     It pays [DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect),
     whose trigger he ruled fired on 2026-08-13
     ([R21](../plan/step-002-warehouse-and-ingestion.md#r21--debt-009-has-fired-and-is-paid-as-sub-step-26--ruled-by-amino-2026-08-13)),
     and it was to land as its own commit after 2.5 — which it does.
  2. **Then Step 002 is finished and Step 003 gets planned**, using
     `planning-a-step`. Its shape is already fixed by
     [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved):
     the sqlglot spike that proves — or disproves — the Validation Gate's
     parse-tree claim, whose approved 2026-08-05 wording is preserved verbatim
     under [Deferred to Step 003](../plan/step-002-warehouse-and-ingestion.md#deferred-to-step-003--prove-the-validation-gates-parse-tree-claim).
  - **Do not plan Step 003 before 2.6 is committed**; the route to the Target State
    is discovered one Step at a time.
- **Three things Sub-step 2.6 leaves for the reviewer to push on**, all argued in
  its review section under *Look at this sceptically*: `generate_series` is not
  standard SQL and the scan does not flag it, because sqlglot files it as
  dialect-neutral; `DIALECT_PROBES` is exempt from the scan it feeds, because the
  probes are real DuckDB SQL living in a scanned file; and `sqlglot` was promoted
  from a transitive dependency to a declared one, which the plan text did not ask
  for.
- **The four decisions 2.5 put to Amino were all approved on 2026-08-13**, and two
  of them left something behind:
  1. **A Snapshot is written on the dates *every* Instrument has a Market Price**
     — the intersection, argued under
     [which dates a Snapshot is written on](../reviews/step-002-warehouse-and-ingestion.md#the-decision-this-sub-step-had-to-make-which-dates-a-snapshot-is-written-on).
     Approved. **The dates it drops are now
     [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes):**
     the choice is right given a sparse price table, and the sparse price table is
     the shortcut. An "as of" question about a dropped date has no answer, and the
     absence reads as a zero.
  2. **Cost Basis uses average cost**, not first-in-first-out. Approved as a
     documented behaviour rather than a silent one — see 4 below.
  3. **`fct_accounting_movement.amount` carries magnitudes, positive**, where
     `fct_cash_movement.amount` is signed from the Account's side. Approved. **This
     is the one edit 2.5 made to a file 2.1 committed** — a comment beside the
     column in `schema.sql`.
  4. **Realised P&L is gross of Commission**, which is recognised separately as the
     broker's revenue. Approved. Together with 2 and 1, it is owed a **user-facing**
     home: [DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews)
     records that decisions moving a number a reader will see currently live only
     in Step Reviews, which are the internal record. Paid at the final
     documentation pass, with [DEBT-008](../debt-ledger.md).
- **Two defects were found on review and fixed, both in the same class.** A
  transfer moved a fraction of a share where every Trade is a whole lot, and
  nothing checked it — `--distinctions` now runs `check_lots` over `fct_trade` and
  `fct_position_snapshot`, and it was made to fail before being trusted. And the
  `Cost Basis` / `Execution Price` figure fell back to a Cost Basis when no last
  fill existed, which is a total standing in for a per-unit price. Both are written
  up in the review's changes section; row counts did not move, three Position-side
  figures did.
- **No new Glossary term was coined, and that was checked rather than assumed.**
  The `simulated_*` raw tables follow the source-prefix convention every raw table
  already uses, with the simulator as the source, and the word is already the
  Glossary's own: the `Ingestion` row says *"synthetic Trades, Cash Movements and
  Positions from a seeded simulator"*. If `Simulator` should be a registered
  Section A component, 2.5 is the Sub-step that should have raised it.
- **One new debt: [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level).**
  `Execution Price` against `Market Price` separates every individual Trade and
  nearly cancels across a whole book, because fills sit either side of the close.
  Not a defect in the simulator — introducing a bias to make the total diverge
  would be shaping data to pass our own check — but a constraint on what a gold
  question may ask. Same shape as [DEBT-004](../debt-ledger.md), different cause,
  same trigger: the Gold Question Set.
- **Both Ledger entries that wait on the Gold Question Set now have figures
  measured on the full window** rather than on the spike's three series. DEBT-004's
  FX-date effect is 0.0409% and DEBT-011's is 0.03%; `--distinctions` prints both
  on every run and says whether they clear DEBT-004's 1% line.
- **What is settled and needs no revisiting.** Everything raised on 2026-08-05,
  2026-08-06 and 2026-08-11 has been ruled on and applied — recorded as
  [R7–R10](../plan/step-002-warehouse-and-ingestion.md#r7r10--four-rulings-from-writing-the-data-definition-language-ddl-2026-08-05),
  [R11–R15](../plan/step-002-warehouse-and-ingestion.md#r11r15--five-rulings-from-aminos-review-of-the-snapshot-design-2026-08-06)
  and R16–R20. In short: `Cost Basis`, `Snapshot`, `Instrument Symbol`,
  `Denomination Currency` and `Trade Side` registered and built; Snapshots are
  **end-of-day** and **dense**; the simulator emits **transfers but not corporate
  actions**; `FX Rate` covers the derived cross-rate
  ([R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11));
  [ADR-0004](../adr/0004-snapshot-and-replay-and-where-dlt-stops.md) is `accepted`
  ([R17](../plan/step-002-warehouse-and-ingestion.md#r17--adr-0004-is-accepted--approved-by-amino-2026-08-11));
  a measurement is dated evidence and lives in a review
  ([R18](../plan/step-002-warehouse-and-ingestion.md#r18--a-measurement-is-dated-evidence-and-lives-in-a-review--approved-by-amino-2026-08-11),
  now a [writing convention in CLAUDE.md](../../../CLAUDE.md#writing-conventions));
  and `verify_framework.py` checks anchors as well as files
  ([R20](../plan/step-002-warehouse-and-ingestion.md#r20--verify_frameworkpy-checks-anchors-not-just-files--approved-by-amino-2026-08-11)).
  The two halves excluded from the slice went to
  [EXT-006](../extension-register.md#ext-006--position-change-attribution) and
  [EXT-007](../extension-register.md#ext-007--corporate-actions).
- **The `movement_type` spellings are now frozen in practice.**
  [DEBT-010](../debt-ledger.md) noted they were free to change while the tables
  were empty. 2.5 filled them, so changing one now means regenerating the client
  side — which is one command, but it is no longer free.
- **What Step 003 inherits.** The sqlglot spike deferred by
  [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
  now has the real data it was moved in order to run against. Its third question
  needs a query computing revenue inline from `commission` to return a *different
  number* from the certified expression against a real warehouse: the 32.59%
  between Gross and Net Revenue is that difference. **Its first bullet — `uv add
  sqlglot` — is already done**, in 2.6, which needed the library for the dialect
  scan. And its fourth question, on DuckDB → BigQuery retargeting, is what tells us
  whether that scan should stay name-based at all.
- **[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect),
  opened in 2.1, is paid — that is what 2.6 is.** The seam scan checked `duckdb`
  imports and not the DuckDB-specific function names ADR-0002 named alongside them;
  it now checks both. The name list is subtracted out of `sqlglot`'s own dialect
  tables rather than typed, three probes prove the scan's teeth on every run, and
  both ingestion modules were mutated with a dialect name and made to fail.
- **Obligations recorded for later Steps**, so they are not rediscovered:
  `README.md` must list every credential Veritas touches
  ([Target State](target-state.md#what-credential-free-means)), and
  [DEBT-008](../debt-ledger.md) fires on the same pass, on the access-control
  claim. [DEBT-002](../debt-ledger.md) was **paid in 2.3** and no longer waits for
  the README — but it constrains what the README may say: *reproducible from
  committed snapshots*, never *reproducible from Yahoo*.

---

## Summary

A fully designed project with two of its nine components built. The framework is
in place and the Target State is `agreed`, so there is a fixed point to build
toward: a natural-language analytics copilot over a brokerage warehouse, whose
answers are grounded in a certified Semantic Layer and checked by a deterministic
Validation Gate.

Every data source that design assumes has been verified obtainable, key-free, and
is snapshotted into the repository. **The Warehouse is full.** The ten-table star
schema of Glossary Section B sits behind the Warehouse Adapter — the only module in
the repository that imports `duckdb`, and the only place a DuckDB-specific function
name appears, both of which are now checked rather than promised — and all ten
tables hold rows. Three are
real: `dim_instrument`, nineteen Instruments across four types and four Quotation
Currencies; `fct_instrument_price`, two years of daily Market Prices covering all
nineteen; and `fct_fx_rate`, every ordered pair of those four currencies on every
calendar date of a window that covers the prices. Seven are synthetic, from a
seeded simulator that prices every Trade off a Market Price the Warehouse already
holds and converts through a real FX Rate: Clients, Accounts, Trades, both movement
ledgers, and dense Position and Cash Balance Snapshots. **One command builds all
ten offline from committed snapshots with no socket opened, and two runs are
byte-identical.**

**Every Certified Metric can now return a number** — all eight of them — and every
pair in Glossary Section C is two measurably different numbers on the loaded data.
The row counts, windows and Section C figures are dated evidence in the
[Step Review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-25--generate-seeded-synthetic-client-activity),
because a `--refresh` moves them. Nothing above Ingestion is built: no Semantic
Layer, no Retrieval, no application.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Three declared dependencies**: `duckdb` (2.1), `dlt` (2.2) and `sqlglot` (2.6). dlt brings roughly forty transitive packages, sqlglot among them — 2.6 promoted it to a declared dependency because `check_warehouse.py` now imports it, and a transitive dependency is one someone else's release notes can remove. `uv add sqlglot` installed nothing: the locked version did not move. The three stdlib-only check scripts — `verify_framework.py`, `check_language.py`, `check_data_availability.py` — are still stdlib-only; `check_warehouse.py` is the one that imports third-party code, and now imports two libraries rather than one. |
| Development framework | ✅ working | `CLAUDE.md`, `.claude/docs/` tree, five skills in `.claude/skills/`. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only (documents exist, links resolve, skills load, interpreter pinned), passes. **Links now include their `#anchor`** ([R20](../plan/step-002-warehouse-and-ingestion.md#r20--verify_frameworkpy-checks-anchors-not-just-files--approved-by-amino-2026-08-11), 2026-08-11): the fragment used to be split off and discarded, so a link to a renamed heading passed, and same-document `#anchor` links were not checked at all. It reports a `dead anchor` distinct from a `dead link` and prints how many links and anchors it checked. Verified by making it fail against a temporary document with two dead anchors, in the [Sub-step 2.4 changes-on-review section](../reviews/step-002-warehouse-and-ingestion.md#changes-made-on-review--2026-08-11-sub-step-24). Scope is `.claude/docs/**` plus `CLAUDE.md`; `README.md` is outside it. |
| Language check | ✅ working | `.claude/scripts/check_language.py` — content rules: component names registered, no `proposed` term in code, abbreviations resolvable. Passes. Parses code with `ast` so it checks identifiers, not prose. Partial payment of [DEBT-001](../debt-ledger.md). |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`, **88 registered terms** as counted by `check_language.py`. **The most recent change is an amendment rather than a registration, so the count is unchanged**: `FX Rate`, clarified 2026-08-11 under [R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11), now says in its own words that a euro-side pair *is* a published ECB reference rate while a pair between two non-euro currencies is the ratio of that date's two published rates — both are FX Rates, and a rate of any other origin is not one. The most recent *addition* is not a Domain Language term but an abbreviation: **NYSE** — New York Stock Exchange — **approved 2026-08-11**, added when R18 moved the reasoning about NASDAQ Trader's second file out of a code comment and into the Step Review, where the abbreviation checker reads it. The same ruling rewrote the `Adjusted Close` / `Market Price` Section C row so its 95.5% divergence figure is dated evidence with the command that reproduces it rather than a standing claim. Sub-step 1.2 added `Market Price`, `Adjusted Close`, `Quotation Currency`; narrowed `Instrument`; renamed `dim_fx_rate` → `fct_fx_rate` and registered `fct_instrument_price`. Step 002 planning added `Execution Price` and its Section C row against `Market Price`. Sub-step 2.1 added `Instrument Symbol`, `Trade Side` and `Denomination Currency` (R7–R9), a Section C row for the last against `Quotation Currency`, and swept the `Dimension Definition` instrument-type values to match the narrowed `Instrument` row (R10); Amino's 2026-08-06 review added `Cost Basis` and its Section C row against `Execution Price`, and registered `Snapshot` (R11–R12). |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified, rulings R1–R3 applied. One correction 2026-08-05: no date dimension in the Warehouse row. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — real 2025 FX Rates and three real price series, plus the dated probe record, owned by `check_data_availability.py`. `data/snapshots/ingestion/` beside it is the pipeline's own, one file per source and one per traded Instrument, rewritten only by `--refresh`. Both committed on purpose: they are what make the checks reproduce without network access. |
| Founding ADRs | ✅ working | Four ADRs in `.claude/docs/adr/`, all **`accepted`**. The first three on 2026-08-03: 0001 Semantic Layer as the retrieval corpus, 0002 DuckDB behind an adapter, 0003 Validation Gate as deterministic code. The fourth — snapshot-and-replay, and where dlt stops — was deferred to the ingestion Step ([DEBT-002](../debt-ledger.md)), written in Sub-step 2.2 and **accepted 2026-08-11** (R17). Every cost in each is classified *accepted* / *debt* / *extension*. ADR-0002 carries a dated clarification (2026-08-05) on what its sqlglot commitment forbids; its status stays `accepted`. |
| Warehouse | ✅ working | `veritas/warehouse/schema.sql` — the ten tables of Glossary Section B, **all ten populated**. Monetary columns are `DECIMAL(18, 6)`, FX Rates `DECIMAL(18, 8)`; **no floating-point column exists** and `check_warehouse.py` fails the run if one appears. Foreign keys declared and enforced. Snapshot grain is one row per subject per date, enforced by the primary key. No `dim_date` (R2). The two movement tables carry **opposite sign conventions** and the schema says so beside each column: cash is signed from the Account's side, accounting carries magnitudes so that Net Revenue = Σcommission − Σrebate − Σfee is literally true. |
| Warehouse Adapter | ✅ working | `veritas/warehouse/adapter.py` — the only module in the repository that imports `duckdb`, which is now checked rather than promised. `create_schema`, `tables`, `columns`, `row_count`, `execute`, `query`, plus the `in_memory()` constructor for throwaway databases. Assembles no SQL text from any argument: introspection goes through `information_schema` with a bound parameter, row counts through the relational API. Hardcoded database path and no error handling, both licensed in writing by [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md). |
| Warehouse check | ✅ working | `.claude/scripts/check_warehouse.py` — four checks always, plus `--sources`: the table set matches Glossary Section B *read from the Glossary*, no floating-point columns, fourteen constraint rejections fire against an in-memory Warehouse with a seven-row positive control, and **the adapter seam holds in both the halves [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md) named** — no `duckdb` import outside `veritas/warehouse/`, and no DuckDB-specific function name in the SQL any module out there emits. The dialect half (2.6) reads every string literal sqlglot parses as a statement and names any function call standard SQL does not have; which names those are is subtracted out of sqlglot's own dialect tables rather than typed, so the list tracks the library. Three probes run every time — standard SQL clean, `strftime` named, `list_aggregate` named — and a probe reading wrong fails the run. `--rebuild` recreates the database; `--sources` checks the loaded data, one function per star table. For `dim_instrument` (2.2): normalisation, the declared universe, every raw table non-empty, and a **richness** assertion that the universe is thick enough for 2.5. For `fct_instrument_price` (2.3): every price is **re-derived from the committed snapshots in Python** and compared row-for-row against what the SQL built, three named wrong readings are shown to change real rows, and no day-over-day move exceeds 1.5. For `fct_fx_rate` (2.4): every rate is re-derived the same way, two named wrong readings are shown to change real rows, **every Market Price has a rate in its own Quotation Currency on its own date**, and a currency converted through another and back is unchanged within the rounding its stored scale forces. **`--distinctions` (2.5)** adds four more: every client-activity row is exactly what the simulator produces from the same seed, **every quantity is a whole lot of its own Instrument** (added on review, 2026-08-13, after a transfer moved a fraction of a share and nothing objected), every Snapshot is markable and at least one Position Change is one no Trade explains, and **every Glossary Section C pair is printed as two numbers with how far apart they are** — a pair that has collapsed fails the run. `--rebuild` is mutually exclusive with both — together they only prove an empty table is empty. |
| Semantic Layer | ✗ none | — |
| Ingestion | ✅ working | `veritas/ingestion/` — **both halves**: four real sources and the seeded simulator. `uv run python -m veritas.ingestion` builds all ten tables end-to-end from a clean clone with **no network**, and two consecutive runs produce byte-identical output. `--refresh` is the only mode that opens a socket; a refresh that fails part-way names the snapshots it had already rewritten, and one that succeeds reports how many it rewrote and how many were distinct — **failing the run if a source was fetched twice**. **Two phases, in an order that cannot be reversed:** dlt lands the real sources in `raw` and the adapter builds three star tables from them; then `simulator.py` *reads those three through the adapter*, generates the client side as a pure function of them and a seed, and a second dlt load plus seven more build scripts lands it. No two connections are ever open at once. The pipeline refuses to complete on four silent-shortness conditions, two of them added in 2.5: a Position with no Market Price on its own Snapshot date, and a monetary amount whose Denomination Currency has no FX Rate on its own date. |
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
│   │       ├── dim_instrument.sql        # ─┐ the real half, built first
│   │       ├── fct_instrument_price.sql  #  │
│   │       ├── fct_fx_rate.sql           # ─┘
│   │       ├── dim_client.sql            # ─┐ the synthetic half; dim_client.sql
│   │       ├── dim_account.sql           #  │ carries the reasoning for all seven
│   │       ├── fct_trade.sql             #  │
│   │       ├── fct_cash_movement.sql     #  │
│   │       ├── fct_accounting_movement.sql  │
│   │       ├── fct_position_snapshot.sql #  │
│   │       └── fct_balance_snapshot.sql  # ─┘
│   └── ingestion/
│       ├── __main__.py        # the entry point: replay by default, --refresh
│       ├── universe.py        # the 19 traded Instruments + two vocabulary maps
│       ├── snapshots.py       # snapshot-and-replay — the only socket in the package
│       ├── sources.py         # NASDAQ Trader · SEC · Yahoo metadata and bars, for dlt
│       └── simulator.py       # the seeded simulator — reads the real tables,
│                              # generates the client side as a pure function
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

**Everything above Ingestion.** The Warehouse itself has no gaps left: all ten
tables hold rows, and the two components below the Semantic Layer are done.

**Every Certified Metric can now return a number**, which was the claim Step 002
existed to make true and had narrowed three times on the way. After 2.2 nothing
aggregatable existed. After 2.3 there were real Market Prices in four Quotation
Currencies with no way to total them. After 2.4 every price converted, but every
metric the Glossary registers is about *client activity* and not one Trade
existed. 2.5 closed the last gap: all eight are computable, and
`check_warehouse.py --distinctions` computes seven of them as a side effect of
measuring the Section C pairs.

**What that does not mean.** A metric returning a number is not a metric being
*asked for* — there is no Semantic Layer, so no Metric Definition is written down,
certified, or retrievable, and nothing turns a question into SQL. The arithmetic
exists; the machine that chooses it does not.

**Two Section C pairs are real but small at book level**, and both are on the
Ledger against the Gold Question Set rather than fixed in the data:
[DEBT-004](../debt-ledger.md) (the FX half of Trade Date against Settlement Date)
and [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level)
(Execution Price against Market Price). Neither is a defect in the simulator —
making either diverge would mean shaping the data to pass our own check — and both
are constraints on what a gold question may ask. `--distinctions` prints both
figures on every run.

The one thing 2.1 chose not to settle is now settled.
[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect)
— the adapter seam scan checked `duckdb` imports but not the DuckDB-specific
function names ADR-0002 also named — **fired and was paid in 2.6**. Amino ruled the
trigger fired on 2026-08-13
([R21](../plan/step-002-warehouse-and-ingestion.md#r21--debt-009-has-fired-and-is-paid-as-sub-step-26--ruled-by-amino-2026-08-13)):
it reads *"the first component outside the adapter emits SQL"*, and two modules
outside `veritas/warehouse/` hold SQL text — `__main__.py` since 2.2 and
`simulator.py` since 2.5. Both are standard SQL with no dialect-specific name in
them, which is what the entry was *about*, but it is not what the sentence said, and
rewording a trigger to keep an entry unfired is the move Non-Negotiable #2 exists to
prevent.

**Both modules still scan clean, and that is now a result rather than an
assertion.** All ten star-schema build scripts live in `veritas/warehouse/builds/`,
so every dialect-specific name the pipeline uses is inside the licensed directory:
`make_timestamp` from 2.3, `generate_series` over dates and `ASOF JOIN` from 2.4,
and nothing new from 2.5, whose seven builds are projections and casts.

**What the scan does not cover**, so nobody reads the seam as fully mechanical: SQL
assembled at run time is not a literal and is invisible to it — that is the
Validation Gate's subject, not a static scan's — and a name sqlglot files as
dialect-neutral passes even where it is not standard SQL, `generate_series` being
the example this project already uses. Both are argued in the
[2.6 review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-26--scan-for-duckdb-specific-function-names-outside-the-adapter).

[DEBT-010](../debt-ledger.md) was **paid in 2.1** and both `movement_type` columns
now carry a `CHECK`; [DEBT-002](../debt-ledger.md) was **paid in 2.3**, under its
first trigger.

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

**7 open debt** — see [debt-ledger.md](../debt-ledger.md) — plus **3 paid**, 1
accepted permanently and 2 moved out. **8 open extensions** — see
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
- **DEBT-009** — **paid 2026-08-13** in Sub-step 2.6, under the trigger Amino ruled
  had fired the same day. The seam scan now checks the DuckDB-specific function
  names ADR-0002 named alongside the imports, with the name list derived from
  sqlglot rather than typed. Two boundaries are stated rather than closed:
  run-time-assembled SQL is invisible to a static scan, and the list is exactly as
  good as sqlglot's dialect tables.
- **DEBT-010** — **paid 2026-08-06**, in the Sub-step that opened it. Both
  `movement_type` columns now carry a `CHECK`, and the two lists differ:
  `realised P&L` is accounting-only, `deposit` is cash-only. It was paid rather
  than deferred because its justification — *"nothing consumes the values yet"* —
  had been falsified by `Realised P&L` landing there. 2.5 has now written rows
  using every one of the spellings, so amending one is a regeneration rather than
  a one-line edit.
- **DEBT-011** — opened 2026-08-11 in Sub-step 2.5. `Execution Price` against
  `Market Price` separates every Trade and cancels across a book. Fires on the
  Gold Question Set, like DEBT-004 and for the same reason: a gold question that
  turns on the pair must be scoped narrowly enough that the two differ by more
  than the comparison's tolerance, or be left out with the limitation stated.
- **DEBT-012** — opened 2026-08-13 on Amino's approval of the Snapshot calendar.
  `fct_instrument_price` is sparse per Instrument, so the calendar has to be the
  intersection and the dates it drops carry no Snapshot at all. An "as of"
  question about one of them returns nothing, which is indistinguishable from an
  Account holding nothing. Fires on the first "as of" date chosen by anything
  other than the calendar itself.
- **DEBT-013** — opened 2026-08-13, also on Amino's instruction. The decisions that
  move a number a reader will see — average-cost Cost Basis, Realised P&L gross of
  Commission, the Snapshot calendar, the two sign conventions — are argued in Step
  Reviews, which `CLAUDE.md` designates the internal working record. A user-facing
  decision register is owed at the final documentation pass, with DEBT-008.
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
- **EXT-008** — the two data checks run in continuous integration. Opened
  2026-08-13 on Amino's question about where they belong. `check_warehouse.py` and
  `check_data_availability.py` check the **data**, where `verify_framework.py` and
  `check_language.py` check the way we work — and nothing runs any of them except a
  person remembering to. An extension rather than debt: the scripts are right as
  they stand and this repository has no pipeline to put them in, so the trigger
  could only fire if we chose to make it fire.

[DEBT-001](../debt-ledger.md)'s trigger **fired** in Sub-step 1.3 — a framework
rule agreed in 1.2 was broken in 1.3. Partially paid by `check_language.py` and
by new rules in `CLAUDE.md`; the hook layer is still unpaid.
