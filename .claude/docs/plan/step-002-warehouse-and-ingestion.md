# Step 002 — Build the Warehouse and fill it

- **Status:** active — written and **approved by Amino on 2026-08-05**, together
  with every ruling in [Rulings](#rulings). Sub-steps 2.1 (`5a061a7`) and 2.2
  (`0fc5a34`) are **committed**; 2.3 is built and awaiting review.
  **Amended 2026-08-10 — see [R16](#r16--the-original-sub-step-22-splits-into-three--approved-by-amino-2026-08-10):**
  the original Sub-step 2.2 splits into three, and [R6](#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
  fires, so the sqlglot spike leaves this Step. **The amendment was approved by
  Amino on 2026-08-10, and Sub-step 2.2 may begin.**
- **Goal:** Stand up the Warehouse — the star schema of
  [Glossary Section B](../glossary.md#b-the-warehouse), behind the Warehouse
  Adapter, holding real market data and seeded synthetic client activity — so
  every later Step has real columns and real numbers to work against.
- **Moves Current State by:** turning two of the ten `✗ none` component rows
  (Warehouse, Ingestion) into working ones, and turning the data-availability
  spike's findings into a committed pipeline that a clone can run offline.

## Why this Step

Three reasons, in order of force.

**1. Everything downstream quotes column names that do not exist yet.** A Metric
Definition is a SQL expression over warehouse tables; a Join Path is a certified
route between two of them; the Validation Gate decides whether a parse tree's
expressions trace to certified ones. None of these can be authored — let alone
verified — before the schema exists. This is dependency order rather than
layering: the Semantic Layer is not "the next layer up", it is a document set
that literally contains `fct_trade.commission`.

**2. The data-availability check proved the sources join; it built nothing.**
[`data-availability.md`](../design/data-availability.md) says of the join spike:
*"What this proves: the three sources genuinely join, and synthetic activity can
be made rich enough that each distinction is a different number rather than a
definitional nicety."* That work lives in
`.claude/scripts/check_data_availability.py`, which writes to no warehouse.
[DEBT-002](../debt-ledger.md)'s first trigger — *"The market-price ingestion
pipeline is written — the snapshot lands in the same Sub-step, not after it"* —
fires in this Step, and the repayment is the same work as the Sub-step.

**3. The single highest-risk assumption gets touched here rather than at the
end.** The Step 001 review's own handoff says so:

> **`sqlglot` is load-bearing and unproven here.** The Validation Gate's whole
> claim — deterministic, parse-tree-level checks — rests on being able to trace
> generated SQL expressions back to Certified Metrics. I believe this works but
> have not built it. It is the single highest-risk assumption in the design, so
> Step 002 should touch it early rather than leave it to the end.

Sub-step 2.4 was that touch, and it is deliberately a **spike** in the same shape
as Sub-step 1.2 — the least code that answers the question, plus a committed
script so the answer can be re-run.

**Amended 2026-08-10 — this reason no longer holds for Step 002, and saying so is
the point of writing it down.** [R6](#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
fired and the spike became Step 003, so reason 3 is now a reason for *Step 003*
and only reasons 1 and 2 justify this one. The handoff asked that Step 002 *"touch
it early rather than leave it to the end"*; the honest position after R6 is that
the touch slips by one Step, not to the end. **The cost of that slip is real** — if
the spike returns a no-go, ADR-0003 needs revisiting after Step 002's ingestion
work rather than during it. It is accepted rather than logged as debt because the
spike is *cheaper and better* against 2.5's real data than against the empty
Warehouse it would have had if run before ingestion, which is what R6's
alternative — a squeezed six-Sub-step Step — actually offered. Step 003 is the
next Step planned, so the slip is one Step and not an open-ended deferral.

---

## How the five Sub-steps divide the work

Two components, five commits — **one table per Sub-step across the real half**,
which is what [R16](#r16--the-original-sub-step-22-splits-into-three--approved-by-amino-2026-08-10)
changed.

```
veritas/warehouse/     ← 2.1   the adapter and the star schema (empty)   ✅ committed 5a061a7
veritas/ingestion/     ← 2.2   dim_instrument         NASDAQ Trader · SEC   ✅ committed 0fc5a34
                       ← 2.3   fct_instrument_price   Yahoo, by snapshot-and-replay   ✅ built
                       ← 2.4   fct_fx_rate            Frankfurter
                       ← 2.5   synthetic sources:     Trades · Cash · Positions · balances
```

**`veritas/ingestion/` and its entry point are created in 2.2 and extended by each
Sub-step after it.** After 2.2, `uv run python -m veritas.ingestion` already builds
a Warehouse end-to-end from a clean clone — the traded Instrument universe in,
nothing priced yet. 2.3 adds prices, 2.4 adds rates, 2.5 adds the activity. **No
Sub-step leaves a half-wired pipeline**; each adds a source to a pipeline that
already runs, and each is one more populated table in `check_warehouse.py`'s
listing.

**Why the real half and the synthetic half are separate Sub-steps at all.** The
Glossary's own definition of `Ingestion` splits at a semicolon: *"real FX Rates,
Market Prices and instrument reference data from key-free public sources,
snapshotted into the repository and replayed by default; **synthetic** Trades,
Cash Movements and Positions from a seeded simulator."* The two halves share a
destination and nothing else:

| | 2.2–2.4 — real | 2.5 — synthetic |
|---|---|---|
| Data comes from | external sources we do not control | a seeded generator we fully control |
| The hard part | replay, minor units, fill-forward, unadjusted close | making every Section C distinction a different number |
| Fails by | a wrong number arriving from outside | a right number that proves nothing |
| Depends on | 2.1 | 2.1 **and 2.2–2.4** — Positions are marked at Market Price and converted through FX Rate |

Every one of the five passes the sizing test with a conjunction-free commit
subject, and every adjacent pair passes `planning-a-step`'s test for splitting:
**Amino could reasonably approve one and reject the next.** A wrong Instrument
universe (2.2), a leaked Adjusted Close (2.3), a fill-forward that misses a
European Central Bank (ECB) holiday (2.4) and a too-calm simulation window (2.5)
are four unrelated failures with four unrelated fixes.

---

## Rulings

R1–R6 settled by Amino on 2026-08-05, before any code; R7–R10 on the same day,
during Sub-step 2.1; R11–R15 on 2026-08-06, from his review of it; **R16 on
2026-08-10**, with it; **R17–R18 on 2026-08-11**, from his review of Sub-step 2.3.
Recorded here so the Step is implemented against decisions rather than
assumptions.

### R1 — `Execution Price` → **approved and required**

Registered in [Glossary Section B](../glossary.md#b-the-warehouse) and given a
[Section C](../glossary.md#c-distinctions-we-must-not-blur) row against
`Market Price`. The `Trade` and `Traded Notional` rows, which both said "price",
now say `Execution Price`. The column is `fct_trade.execution_price`.

The collision it prevents: `Market Price` was registered as *"the unadjusted
closing price at which an Instrument traded on a date"* while the bare word
"price" carried the price a Trade actually filled at. Two numbers, one
unregistered word, about to become two columns.

### R2 — a date dimension → **rejected**

No `dim_date`. The date axis is the `trade_date` and `settlement_date` columns.
[`target-state.md`](../design/target-state.md) had listed a *"date"* dimension in
its Warehouse row and has been corrected, with the reason recorded in its status
block; the Glossary's `Dimension Definition` row already pointed at a column
(*"**by date** (`trade_date`, daily)"*), so the correction removes a
contradiction rather than making a choice.

### R3 — hand-authored DDL inside the adapter → **allowed, with the reasoning written down**

The reading was not obvious from ADR-0002's sentence, so it is now a dated
clarification inside the ADR itself rather than a line in this plan:
[ADR-0002 → *Clarification, 2026-08-05*](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md#clarification-2026-08-05--what-the-sqlglot-commitment-forbids).

In short: the commitment governs SQL that **code assembles**, not SQL a human
wrote once, and the alternative to a static `schema.sql` is not sqlglot-rendered
DDL — it is DDL built by string concatenation, which is worse against the same
concern. The accepted cost is that the schema does not retarget automatically;
the extension path writes a second DDL file by hand. Two consequences bind this
Step: `check_warehouse.py` runs the greppable signal ADR-0002 named, and the
adapter prefers constructs that assemble no SQL text even internally.

### R4 — dlt lands raw, the adapter builds the star schema → **approved**

dlt's DuckDB destination opens its own connection, which sits awkwardly against
*"reached **only** through the Warehouse Adapter; no component queries it
directly"*. Settled: **dlt lands raw source data in a `raw` schema; the adapter
executes the SQL that builds the star schema from it.** dlt does extract-and-load,
which is what it is for, and the star schema — the thing every Metric Definition
will quote — stays entirely inside the adapter. This is the second decision in
ADR-0004.

### R5 — evidence from check scripts, no pytest this Step → **approved**

Committed check scripts, the pattern Non-Negotiable #4 asks for and the one
`check_data_availability.py` already proves. pytest arrives with the first
component that has branching logic worth unit-testing, which is the Validation
Gate rather than the warehouse.

### R7–R10 — four rulings from writing the Data Definition Language (DDL), 2026-08-05

Raised during Sub-step 2.1 and settled the same day, before any of the four
reached a column name. Three are Term Proposals and one is a contradiction
between two `agreed` Glossary rows. All four were found the same way: by writing
the star schema and hitting a column with no word to name it — which is the order
Non-Negotiable #1 exists to produce, and the reason 2.1 comes before 2.2.

| | Question | Ruling |
|---|---|---|
| **R7** | The natural key `dim_instrument` needs, so Yahoo prices and NASDAQ/SEC reference rows have something to join on. No term named an Instrument's ticker. | **`Instrument Symbol`** → `dim_instrument.instrument_symbol`. It is what both reference sources call it — NASDAQ Trader's `Symbol` column and Yahoo's `symbol` field — so ingestion reads without a rename in it. |
| **R8** | The currency a monetary amount in a fact row is held in. Neither `Quotation Currency` (the Instrument's) nor `Reporting Currency` (the answer's), and needed by four tables. | **`Denomination Currency`** → `denomination_currency`. One term covering Trades, Cash Movements, Accounting Movements and Cash Balances. `Cash Currency` was rejected: an Accounting Movement is explicitly the entry recognised *"whether or not cash moved"*, so that word is wrong on one of the four tables and would need a second name — which is the synonym disease. A bare `currency` was rejected as the same mistake R1 had just fixed. |
| **R9** | How `fct_trade` records buy versus sell. The `Trade` row says an Account *"buys or sells"* but no term names which. | **`Trade Side`** → `fct_trade.trade_side`, values `buy`/`sell`, with `quantity` always positive. Chosen over a signed quantity, which adds no vocabulary but makes `Traded Notional`'s registered formula Σ(quantity × Execution Price) require an undocumented absolute value to stay correct. |
| **R10** | Two `agreed` rows disagreed on the instrument-type values. `Dimension Definition` said *"equity · bond · future · option"*; `Instrument`, narrowed 2026-08-03 by R1, says *"equity, ETF, future, or currency pair"*. | **The `Instrument` row wins.** The parenthetical was missed when R1 narrowed the universe — single bonds and options have no key-free Market Price source ([DEBT-003](../debt-ledger.md)). The `Dimension Definition` row was swept to match, so this removes a contradiction rather than making a choice, exactly as R2 did. |

### R11–R15 — five rulings from Amino's review of the snapshot design, 2026-08-06

Raised by one question — *given that snapshot tables answer "what was held" and
`fct_trade` answers "what was done", is any promised question unanswerable?* — and
all settled before Sub-step 2.1 was committed. The argument for each is in the
[Step Review](../reviews/step-002-warehouse-and-ingestion.md); this table is the
ruling only.

| | Question | Ruling |
|---|---|---|
| **R11** | `Unrealised P&L` is quantity × Market Price − Cost Basis, and no column held the third term. Store it, defer it as debt, or fold it out of `fct_trade`? | **Store it.** `Cost Basis` registered and added to `fct_position_snapshot`, signed, total rather than per unit, with `CHECK (quantity != 0 OR cost_basis = 0)`. The fold returns a plausible wrong number under a date filter, after a transfer, and after a round trip — three worked examples in the review. |
| **R12** | Is a Snapshot **end-of-day**? | **Yes**, and it is part of the `Snapshot` term rather than a loading detail: a Position marked at that date's closing Market Price must be the Position held at the close. Registering `Snapshot` was the same ruling — the word named two tables and a column and had never been defined. |
| **R13** | Are Snapshots **dense or sparse**, and on which calendar? | **Dense, over trading days only** — one row per subject per date on which the Warehouse holds a Market Price. Dense makes an "as of" question an equality join instead of a most-recent-row-at-or-before lookup, which is a Join Path the Orchestrator would have to get right every time. Trading days rather than calendar days, because a Saturday snapshot joins to no price. **Snapshot density and Market Price density are one decision, not two.** |
| **R14** | Does the simulator emit **non-trade Position movements**? | **Transfers yes, corporate actions no.** A handful of transfers makes the Section C pair *Position Change vs Trade* real in the data rather than merely asserted, and is what puts `cost_basis` under load. Corporate actions are excluded because `Market Price` is real data: a split inside the loaded window forces either corporate-action machinery or knowingly incoherent data, and the third option is `Adjusted Close`, which is an anti-pattern. **Sub-step 2.2's `--sources` must verify the price window is split-free rather than assume it**, and the excluded half is [EXT-007](../extension-register.md#ext-007--corporate-actions). |
| **R15** | `Realised P&L` had no home. Record the intention, or implement it? | **Implement it, by paying [DEBT-010](../debt-ledger.md) in the Sub-step that opened it.** Both `movement_type` columns now carry a `CHECK`, and the two lists differ: `realised P&L` is accounting-only, `deposit` is cash-only. The debt's own justification — *"nothing consumes the values yet"* — had been falsified by R11's walk, so annotating it would have left a dependency for 2.3 to notice or not. Three probes hold it. |

### R6 — the sqlglot spike (then numbered 2.4) is a pre-agreed split point → **approved**

If review-driven growth arrives in 2.1–2.3, **2.4 becomes Step 003** rather than
being squeezed into an over-full Step. *(The heading carries a clarifier added
2026-08-10: R16 renumbered the Sub-steps, so the "2.4" this ruling names is the
sqlglot spike, not the Frankfurter Sub-step that now holds that number. The ruling
itself is unchanged.)* Agreed in advance because the Step 001
closing note recorded that 1.3 was planned as three documents and shipped fifteen
files, and that *"the natural split, in hindsight, was 1.3 (the ADRs) and a
separate 1.4"* — an option that should have been offered at review and was not.
Offering it before the Step starts is the lesson applied.

**Fired 2026-08-10.** Growth arrived twice. Amino's 2026-08-06 review of Sub-step
2.1 added a column, two Glossary terms and the payment of
[DEBT-010](../debt-ledger.md), and grew the evidence script along the way — the
[Step Review](../reviews/step-002-warehouse-and-ingestion.md) records one such
increment as *"taking the constraint probe from eight rejections to ten and the
positive control from three seed rows to five"*, and
`uv run python .claude/scripts/check_warehouse.py` today prints fourteen refusals
against a seven-row positive control. R16 then turns one Sub-step into three.
Without R6, Step 002 would hold six Sub-steps, which
`planning-a-step` reads as two Steps: *"Six or more Sub-steps | This is two Steps;
ship the first."* So the spike leaves, exactly as pre-agreed. Its text is preserved
under [Not in this Step](#not-in-this-step) so Step 003's plan starts from it
rather than from memory — it is **not** planned here, because *"Never plan more
than one Step ahead."*

### R16 — the original Sub-step 2.2 splits into three → **approved by Amino 2026-08-10**

The original 2.2 carried, in one commit: a new package, a new entry point, a new
dependency, **three external sources**, three proven-necessary transforms, a
founding-tier ADR, the payment of [DEBT-002](../debt-ledger.md), and four new
assertions in `check_warehouse.py`. Its commit subject — *"Load real market data
into the Warehouse by snapshot-and-replay"* — passes the no-conjunction test only
because "real market data" hides three sources behind one noun phrase. That is the
symptom `planning-a-step` names: *"Commit message needs 'and' | Split it."*

**The split follows two lines the project had already drawn**, so it honours
boundaries rather than inventing them.

1. **The hedge boundary.** [`data-availability.md`](../design/data-availability.md)'s
   R3 update already separates the sources: snapshot-and-replay *"applies
   specifically to sources that are undocumented and unversioned — Yahoo — not to
   every external source; Frankfurter and the SEC are documented and stable, and
   snapshotting them is a reproducibility convenience rather than a hedge against
   disappearance."* One source carries the hedge and two do not. Bundling all three
   into one Sub-step made ADR-0004 argue a distinction that its own Sub-step
   erased; splitting them means the ADR is written in 2.2 against the stable
   sources and **cashed in 2.3** against the unstable one.
2. **The engine.** Sub-step 2.1 declared and enforced foreign keys, so
   `dim_instrument` must exist before `fct_instrument_price` accepts a row — the
   constraint probe already demonstrates the rejection. The order of 2.2 before 2.3
   is therefore not a preference; it is what the database permits.

`fct_fx_rate` is third because nothing constrains where it goes — it has no foreign
key to a dimension — and the Loop prefers *"the slice that removes the most
uncertainty"* early. The Step's uncertainty is concentrated in Yahoo, not in
Frankfurter.

**What this does not change:** every ruling R1–R15 stands, no Sub-step's content is
dropped, and the Step's Goal is untouched. Three commits now carry what one
carried, in the order the foreign keys allow.

### R17 — ADR-0004 is accepted → **approved by Amino 2026-08-11**

[ADR-0004](../adr/0004-snapshot-and-replay-and-where-dlt-stops.md) was written in
Sub-step 2.2 and left `proposed`; Sub-step 2.3 then built on both of its decisions
— every source read through one snapshot-and-replay mechanism, and dlt stopping at
`raw`. Current State flagged the stale status rather than flipping it, on the
ground that *"a status that Claude flips is not a decision anybody made"*. Amino
made it: the ADR is now **`accepted`**, dated 2026-08-11 in the ADR itself and in
[the ADR index](../adr/README.md). Nothing in its Decision or Consequences
changed — this ruling settles its status, not its content.

### R18 — a measurement is dated evidence, and lives in a review → **approved by Amino 2026-08-11**

Raised against `fct_instrument_price.sql`'s *"300 of the 521 bars in each currency
pair's snapshot fall on a different date under the two readings"*, then **widened
by Amino the same day** to every figure a later run could refute or resize, in any
file. The rule as it now stands: such a figure is written as evidence — what was
measured, when, under what settings, and the command that reproduces it — kept in
the Step Review that produced it, with code comments, the Glossary, ADRs and plans
**referring** to it rather than restating the number.

The rule and its reasoning live in
[CLAUDE.md](../../../CLAUDE.md#writing-conventions); this ruling records that it
was Amino's and when. Two sweeps followed: the ingestion code and
`check_warehouse.py` on the first pass, then `schema.sql`'s Adjusted Close figure
and the Glossary row behind it on the second — both recorded in the Sub-step 2.3
review under
[Changes made on review](../reviews/step-002-warehouse-and-ingestion.md#changes-made-on-review--2026-08-11).

---

## Sub-steps

### 2.1 — Create the Warehouse behind its adapter

The Warehouse Adapter and the star schema, empty. This is the seam
[ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md) exists to
protect, and its own words set the size: *"a seam is an interface plus one
trivial implementation… We are naming a boundary once, today, while there is
nothing on either side of it."*

- `veritas/warehouse/` — the Warehouse Adapter. Owns the DuckDB connection and
  the database path, and is **the only module in the repository that imports
  `duckdb`**. Behind it, everything is allowed to be crude: a hardcoded path, no
  pooling, no error handling. ADR-0002 permits exactly that, and only that.
- The star schema DDL for the ten tables Glossary Section B names:
  `dim_client`, `dim_account`, `dim_instrument`, `fct_trade`,
  `fct_cash_movement`, `fct_accounting_movement`, `fct_balance_snapshot`,
  `fct_position_snapshot`, `fct_fx_rate`, `fct_instrument_price`. Monetary
  columns are `DECIMAL`, never floating point — the reason ADR-0002 rejected
  SQLite (*"Monetary aggregation over floats in a project whose entire subject is
  quietly wrong numbers is not a trade worth making"*) applies to our own column
  types too. No `dim_date` (R2); `fct_trade.execution_price` (R1).
- `.claude/scripts/check_warehouse.py` — the committed evidence script for this
  Step, growing across 2.1–2.5. At 2.1 it lists every table with its columns and
  row count, and runs ADR-0002's greppable signal: **a `duckdb` import anywhere
  outside `veritas/warehouse/` fails the check** (R3).
- `uv add duckdb`.

**Verification:**

```bash
uv run python .claude/scripts/check_warehouse.py
uv run python .claude/scripts/check_language.py
```

The first lists ten tables at zero rows and reports the import scan clean. The
second is the one that matters most here: it is the first time it scans real
domain identifiers rather than three framework scripts, which is what makes this
Sub-step's Glossary compliance evidence rather than a claim.

### 2.2 — Load `dim_instrument` from NASDAQ Trader and the Securities and Exchange Commission (SEC)

The `Ingestion` seam, drawn against the sources that carry no hedge. Creates
`veritas/ingestion/` and its entry point.

- dlt lands NASDAQ Trader's symbol directory and the SEC's `company_tickers.json`
  in the `raw` schema; **the adapter executes the SQL that builds `dim_instrument`
  from it** (R4). This is where R4 stops being a ruling and becomes code, and it
  is why this Sub-step is first: the raw-versus-star boundary is easier to get
  right against sources with no snapshot logic layered over them.
- **Default is replay.** `data/snapshots/` is the input; `--refresh` re-hits the
  source and rewrites the snapshot, the only mode that needs a network. For these
  two sources that is a reproducibility convenience rather than a hedge — the
  distinction ADR-0004 records, and the reason 2.3 exists separately.
- **Normalise minor units** (`GBp` → `GBP`, a factor of 100) **before insert.**
  Sub-step 2.1 made this non-optional at the engine level: `quotation_currency`
  must equal its own upper case, so an unnormalised row is refused rather than
  quietly stored. It does **not** catch the `GBX` spelling.
- **ADR-0004 — snapshot-and-replay, and where dlt stops.** Deferred to this Step
  by name: *"this was considered as a fourth founding ADR and deferred to the
  ingestion Step, where the decision actually binds."* It carries both decisions:
  why snapshot-and-replay applies to Yahoo and not to Frankfurter or the SEC, and
  R4's raw-versus-star boundary. Written here because R4 becomes code here; its
  Yahoo half is what tells 2.3 what to build.
- `uv add dlt`.
- `check_warehouse.py --sources` — its first two assertions: no quotation currency
  survives into `dim_instrument` that is not already upper case, and every
  `Instrument Symbol` is present and unique.

[DEBT-002](../debt-ledger.md) is **not** paid here. Its subject is the Yahoo
endpoint and its first trigger is *"The market-price ingestion pipeline is
written — the snapshot lands in the same Sub-step, not after it"*, which is 2.3.

**Verification:**

```bash
uv run python -m veritas.ingestion
uv run python .claude/scripts/check_warehouse.py --sources
```

The first builds a Warehouse from a clean clone with no network. The second shows
`dim_instrument` populated with the other nine tables still at zero rows, and both
assertions holding.

### 2.3 — Load `fct_instrument_price` from Yahoo by snapshot-and-replay

The Sub-step [DEBT-002](../debt-ledger.md) was opened for, and the one carrying
this Step's real risk.

- dlt fetches Yahoo's chart endpoint into `raw`; the adapter builds
  `fct_instrument_price`. It loads **after** 2.2 because the foreign key to
  `dim_instrument` is declared and enforced.
- **Store the unadjusted close only**, never `Adjusted Close`. The trap is
  measured rather than theoretical: `check_data_availability.py` found the two
  differ on 95.5% of bars.
- The snapshots widen from the three probe series now in `data/snapshots/`
  (`yahoo-AAPL-5y.json`, `yahoo-SAP.DE-2y.json`, `yahoo-VOD.L-2y.json`) to the
  full traded Instrument universe, on the same code path a reviewer would run.
- **[DEBT-002](../debt-ledger.md) → `paid`**, by this Sub-step, under its first
  trigger.
- `--sources` grows by two: every `fct_instrument_price` row matches the
  snapshot's unadjusted close rather than its adjusted close, and **the loaded
  price window is split-free** for every held Instrument — a day-over-day ratio
  large enough to be a corporate action rather than a market move. R14 excluded
  corporate actions on the assumption that no loaded series contains one; this is
  what turns that assumption into a check
  ([EXT-007](../extension-register.md#ext-007--corporate-actions)).

**Verification:**

```bash
uv run python -m veritas.ingestion
uv run python .claude/scripts/check_warehouse.py --sources
```

Two populated tables, four assertions holding. It fails the run if any stops
holding, in the same spirit as `check_data_availability.py`.

### 2.4 — Load `fct_fx_rate` from Frankfurter

The last real source. Nothing constrains its position — it has no foreign key to
a dimension — so it comes after the Step's risk has been retired.

- dlt fetches Frankfurter into `raw`; the adapter builds `fct_fx_rate`. **Never
  Yahoo's `EURUSD=X`**, which would be a second source for one concept:
  *"Frankfurter is the only FX Rate source."*
- **Fill FX Rates forward** across weekends and the six European Central Bank
  (ECB) holidays — *"the FX Rate for a non-publishing date is the most recent
  published rate."*
- Send a descriptive User-Agent. Frankfurter returns HTTP 403 to the default
  `Python-urllib`, which reads as "blocked" when the fix is one header.
- `--sources` grows by one: every calendar date in the loaded window resolves to
  an FX Rate after fill-forward.

**Verification:**

```bash
uv run python -m veritas.ingestion
uv run python .claude/scripts/check_warehouse.py --sources
```

Three populated tables, five assertions holding — the whole real half of
`Ingestion`, replayable from a clean clone with no network.

### 2.5 — Generate seeded synthetic client activity

The second half of `Ingestion` — *"market data real, client activity synthetic —
never the reverse"* — added to the pipeline 2.2–2.4 built.

- A seeded simulator producing Trades, Cash Movements, Accounting Movements,
  Position snapshots and Cash Balance snapshots, wired into the same
  `veritas.ingestion` entry point.
- Shaped so **every Section C distinction is a different number**, which is the
  bar the join spike already cleared at spike scale (Gross and Net Revenue
  separated by ~39%, accrual and cash basis by ~24%): Clients holding several
  Accounts each, across the EU · UK · APAC values the region Dimension Definition
  names; a window straddling a settlement cycle so Trade Date and Settlement Date
  disagree; Rebates large enough to separate Gross from Net Revenue; Positions
  closed and Positions held, so Realised and Unrealised P&L both exist.
- Trades priced at Execution Price; Positions marked at Market Price; both
  converted through FX Rate to the Reporting Currency (R1).
- **The simulator can only be as rich as the Instruments it has to trade**, so the
  universe is checked rather than hoped for. `check_warehouse.py --sources` gained
  a richness assertion in Sub-step 2.2, and it is a **precondition of this
  Sub-step**: every `instrument_type` present, **at least two Instruments of each**,
  at least three Quotation Currencies, and at least one normalised from a minor
  unit. The two-of-each bar is the one that matters here — a type with a single
  member makes a metric sliced to that type a report on one security, which is a
  distinction the simulator cannot rescue afterwards. It failed on first run
  (one currency pair) and `TRADED_INSTRUMENTS` was widened from sixteen
  Instruments to nineteen; if this Sub-step finds the universe still too thin,
  widening it again is one line in `veritas/ingestion/universe.py` plus a
  `--refresh`.

**Verification:**

```bash
uv run python -m veritas.ingestion
uv run python .claude/scripts/check_warehouse.py --distinctions
```

The check prints **both numbers** for each Section C pair and fails if any pair
collapses. Determinism is part of it: two runs from the same seed produce
identical row counts and identical distinction figures, or the Sub-step has not
passed.

[DEBT-004](../debt-ledger.md) is **not** repaid here — its trigger is the Gold
Question Set, which this Step does not build. But the simulator's window is what
will make repayment possible or impossible later, so the Step Review must state
what the Trade Date versus Settlement Date FX delta came out as on the generated
data, and whether it cleared the 1% line the spike missed.

---

## Not in this Step

### Deferred to Step 003 — Prove the Validation Gate's parse-tree claim

**Was Sub-step 2.4 until [R6](#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
fired on 2026-08-10.** The text below is the approved 2026-08-05 wording, kept
verbatim so Step 003's plan starts from it rather than from memory. It is **not**
planned here, and Step 003 is not written until Step 002 ships.

A spike, not the Gate. The question is narrow and answerable: **can sqlglot
decide, from a parse tree alone, that a generated query computes a Certified
Metric and nothing else?**

- `uv add sqlglot`.
- `.claude/scripts/check_validation_feasibility.py` — the committed probe.
- `.claude/docs/design/validation-feasibility.md` — the findings, in the same
  shape as `data-availability.md`, ending in a go/no-go on
  [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md).

What it must answer, using the real schema from 2.1 and the real data from 2.5:

1. **Tracing.** Does a certified expression stay recognisable in a generated
   query's parse tree under aliasing, a subquery, and a common table expression?
   This is the claim the whole Gate rests on.
2. **Restricted columns.** Can a restricted column be found when it arrives via
   `SELECT *`, or aliased to a benign name? ADR-0003 rejected string matching on
   exactly this ground: *"a restricted name in a comment, a column aliased to
   something benign, a subquery, or a `SELECT *` that expands to include a
   restricted column all defeat text matching."* That rejection is currently an
   argument, not a measurement.
3. **The Shadow Metric it must catch.** A query computing revenue inline from
   `commission` instead of drawing on the certified expression — the failure
   named in the Target State's problem statement — is rejected, and the two
   queries return *different numbers* against the real warehouse. That last part
   is what makes the spike worth running against 2.5's data rather than against
   fixtures.
4. **Dialect retargeting.** A generated statement round-trips DuckDB → BigQuery
   through sqlglot without losing meaning. ADR-0002 calls transpilation *"good
   but not total"*; the spike measures where it stops on the SQL shapes we
   actually intend to generate. It does **not** test DDL, which R3 already
   settled is hand-authored per engine.

**Verification:**

```bash
uv run python .claude/scripts/check_validation_feasibility.py
```

Exits non-zero if any of the four claims fails, so ADR-0003's central bet cannot
go stale unnoticed — the pattern `check_data_availability.py` established for the
data half.

A **no-go on claim 1 or 3 is a real possible outcome**, and it would be the most
valuable thing that Step produces. It would mean ADR-0003 needs revisiting before
any Gate code exists, which is enormously cheaper than discovering it in the Step
that builds the Gate.

*End of the preserved 2026-08-05 text.*

### Also not in this Step

- **The Semantic Layer.** It is
  [ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md)'s central bet
  and its file format is the seam three Extension Register entries land against
  ([EXT-002](../extension-register.md#ext-002--semantic-layer-drift-detection),
  [EXT-003](../extension-register.md#ext-003--metric-authoring-at-scale),
  [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks)).
  A seam that load-bearing deserves a Step where it is the subject, not a fifth
  Sub-step appended after three days of ingestion work. It also needs 2.1's
  columns to quote.
- **Retrieval, Orchestrator, Validation Gate, App, Observability, Evaluation,
  containerization.** Nothing here is blocked by leaving them out, and nothing
  here half-builds them. The deferred spike above probes the Validation Gate's
  central assumption without building the Gate.
- **The Gold Question Set**, and therefore [DEBT-004](../debt-ledger.md)'s
  repayment.
- **`README.md`**, and therefore [DEBT-008](../debt-ledger.md)'s repayment. No
  access-control claim is made anywhere a reader can see it in this Step, so its
  trigger does not fire.
- **A test framework** — R5.
- **Repaying [DEBT-001](../debt-ledger.md)'s hook layer.** Its trigger fires on
  the *next* observed rule breach, not on a schedule.
