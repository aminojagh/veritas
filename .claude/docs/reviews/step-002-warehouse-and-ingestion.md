# Step Review — Step 002: Build the Warehouse and fill it

## Sub-step 2.1 — Create the Warehouse behind its adapter

**What changed**

The Warehouse exists, empty, behind the seam
[ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md) was written to
protect. Four things, in the order they matter.

- **`veritas/warehouse/schema.sql`** — the ten tables of
  [Glossary Section B](../glossary.md#b-the-warehouse), hand-authored, which the
  ADR's dated clarification licenses: *"Static DDL inside `veritas/warehouse/` —
  allowed. Nothing is rendered; this text **is** the source."* Every monetary
  column is `DECIMAL`; the schema holds no floating-point column at all. Foreign
  keys are declared and therefore enforced.
- **`veritas/warehouse/adapter.py`** — the Warehouse Adapter, and the only module
  in the repository that imports `duckdb`. It assembles **no SQL text from any
  argument it is handed**: `tables` and `columns` go through `information_schema`
  with a bound parameter, and `row_count` goes through DuckDB's relational API
  rather than `SELECT count(*) FROM <name>`. That is the ADR's case C — permitted
  inside the seam and *"still worth refusing"* — declined rather than taken.
- **`.claude/scripts/check_warehouse.py`** — the committed evidence script, which
  runs four checks. The first is worth calling out: **the expected table set is
  read out of Glossary Section B rather than typed into the script.** A list typed
  there would only ever prove that two files I wrote agree with each other;
  reading the Glossary means registering a term that names a new table fails the
  check until the schema has that table.
- **`uv add duckdb`** — `duckdb==1.5.5`, the project's first dependency.

Four questions had to be settled before a single column could be named, and all
four are recorded as
[R7–R10](../plan/step-002-warehouse-and-ingestion.md#r7r10--four-rulings-from-writing-the-data-definition-language-ddl-2026-08-05).
Three were Term Proposals; the fourth was two `agreed` Glossary rows contradicting
each other about the instrument-type values. **This is the Sub-step's most useful
output.** The plan predicted that "everything downstream quotes column names that
do not exist yet"; what it did not predict is that three of those names did not
exist in the Glossary either, and every one of them was found by the act of
writing the DDL rather than by reading the design.

**Verification**

Both commands the plan specified for this Sub-step, plus the framework check.

```
$ uv run python .claude/scripts/check_warehouse.py --rebuild
  removed data/veritas.duckdb
  Warehouse: data/veritas.duckdb (created from schema.sql)
  Glossary Section B names 10 tables · the Warehouse has 10

  dim_account  —  3 columns, 0 rows
      account_id               BIGINT
      client_id                BIGINT
      account_name             VARCHAR

  dim_client  —  3 columns, 0 rows
      client_id                BIGINT
      client_name              VARCHAR
      client_region            VARCHAR

  dim_instrument  —  5 columns, 0 rows
      instrument_id            BIGINT
      instrument_symbol        VARCHAR
      instrument_name          VARCHAR
      instrument_type          VARCHAR
      quotation_currency       VARCHAR

  fct_accounting_movement  —  7 columns, 0 rows
      accounting_movement_id   BIGINT
      account_id               BIGINT
      trade_id                 BIGINT
      movement_date            DATE
      movement_type            VARCHAR
      amount                   DECIMAL(18,6)
      denomination_currency    VARCHAR

  fct_balance_snapshot  —  4 columns, 0 rows
      snapshot_date            DATE
      account_id               BIGINT
      denomination_currency    VARCHAR
      cash_balance             DECIMAL(18,6)

  fct_cash_movement  —  7 columns, 0 rows
      cash_movement_id         BIGINT
      account_id               BIGINT
      trade_id                 BIGINT
      movement_date            DATE
      movement_type            VARCHAR
      amount                   DECIMAL(18,6)
      denomination_currency    VARCHAR

  fct_fx_rate  —  4 columns, 0 rows
      rate_date                DATE
      from_currency            VARCHAR
      to_currency              VARCHAR
      fx_rate                  DECIMAL(18,8)

  fct_instrument_price  —  3 columns, 0 rows
      price_date               DATE
      instrument_id            BIGINT
      market_price             DECIMAL(18,6)

  fct_position_snapshot  —  4 columns, 0 rows
      snapshot_date            DATE
      account_id               BIGINT
      instrument_id            BIGINT
      quantity                 DECIMAL(18,6)

  fct_trade  —  12 columns, 0 rows
      trade_id                 BIGINT
      account_id               BIGINT
      instrument_id            BIGINT
      trade_date               DATE
      settlement_date          DATE
      trade_side               VARCHAR
      quantity                 DECIMAL(18,6)
      execution_price          DECIMAL(18,6)
      commission               DECIMAL(18,6)
      fee                      DECIMAL(18,6)
      rebate                   DECIMAL(18,6)
      denomination_currency    VARCHAR

  constraint probe (in-memory Warehouse from the same schema.sql)
    accepted  5 valid seed rows (positive control)
    refused   dim_instrument refuses a pence quotation (`GBp`) — the 100x trap
    refused   dim_instrument refuses an out-of-scope instrument type
    refused   dim_client refuses a region the Dimension Definition does not name
    refused   fct_trade refuses a trade_side outside 'buy'/'sell', including 'BUY'
    refused   fct_trade refuses a negative quantity — direction lives in trade_side
    refused   fct_trade refuses settlement before trade
    refused   fct_trade refuses an orphan account_id
    refused   fct_instrument_price refuses an orphan instrument_id
    refused   fct_position_snapshot refuses a second row for one date, account, instrument
    refused   fct_balance_snapshot refuses a second row for one date, account, currency

  seam scan: 7 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
```

The plan said this command should "list ten tables at zero rows and report the
import scan clean", and it does. Two of the four checks are additions and are
argued for under *Look at this sceptically* below.

```
$ uv run python .claude/scripts/check_language.py
  glossary: 85 registered terms
  Target State components (9)
    agreed        Warehouse
    agreed        Semantic Layer
    agreed        Ingestion
    agreed        Retrieval
    agreed        Orchestrator
    agreed        Validation Gate
    agreed        App
    agreed        Observability
    agreed        Evaluation
  proposed terms: 0 · python files scanned: 7 · identifiers: 268
  abbreviations: 23 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

The plan called this "the one that matters most here: it is the first time it
scans real domain identifiers rather than three framework scripts". It scanned
**268 identifiers across 7 files**. The three framework scripts are what
`git ls-tree -r --name-only 57e8aee | grep '\.py$'` lists, so the four added here
are the first Python files in the project that carry domain meaning at all.

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       652 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr         1037 words
  python     3.14.4                 /home/amino/Projects/veritas/.claude/worktrees/step-002-substep-2-1/.venv/bin/python3

PASS — framework is wired up correctly
```

The interpreter path is the worktree this Sub-step was built in, not a second
environment: this session was isolated to
`.claude/worktrees/step-002-substep-2-1`, so `uv` created a `.venv` there. Run
from the main checkout it reads `/home/amino/Projects/veritas/.venv/bin/python3`.
It is pasted unaltered because a review that tidies its own evidence is not
evidence.

This run also caught something worth keeping in the record: on its first
invocation it **failed**, with `current-state.md: dead link ->
../reviews/step-002-warehouse-and-ingestion.md` — the Resume-here block pointed at
this file before this file existed. That is the framework check doing exactly the
job it was built for.

**Deliberately left undone**

- **[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect)**
  — the seam scan implements half the signal ADR-0002 named. That ADR says the
  signal is *"a `duckdb` import **or a DuckDB-specific function name** anywhere
  outside the adapter module"*; `check_seam` scans imports only. Deferred because
  no module outside the adapter emits SQL yet, so the function-name half would
  pass vacuously — the exact failure the import scan already guards against by
  failing the run if *nothing* imports duckdb.
- **[DEBT-010](../debt-ledger.md#debt-010--movement_type-has-no-registered-value-vocabulary)**
  — `movement_type` has no agreed value set and no constraint, while the schema's
  three other enumerated columns all have both. Its trigger fires in Sub-step 2.3,
  before the simulator writes the first row.
- **No cost basis on `fct_position_snapshot`.** Realised and Unrealised P&L can be
  expressed as a weighted average of Execution Prices over `fct_trade`, so the
  column is unnecessary *unless* a Position changes by a route other than a
  Trade — which Section C warns is possible through transfers and corporate
  actions. Not debt: it is 2.3's decision, and adding a column is additive rather
  than a rename.
- **No pytest** — R5, and the adapter therefore has no unit tests. Its only
  exercise is `check_warehouse.py`.
- **Not debt, and worth saying so explicitly:** the hardcoded database path, the
  absent connection pooling and the absent error handling in the adapter. ADR-0002
  pre-classified all three in writing — *"the adapter's first implementation can
  hardcode a path, ignore connection pooling, and handle no errors at all"* — so
  putting them on the Ledger would inflate the open-debt count with decisions
  already accepted.

**Look at this sceptically**

1. **I put two checks in `schema.sql` that the plan assigned to Sub-step 2.2, and
   you may want them struck.** The plan gives 2.2's `--sources` the job of
   asserting "no `GBp` survives into `dim_instrument`". I also added a constraint
   —`quotation_currency` must equal its own upper case — which refuses the pence
   trap at insert time. My reasoning is that a constraint prevents the defect
   while a check detects it afterwards, and this is the 100× error the project's
   own Section C calls out. But it *is* scope the plan put elsewhere, it makes
   2.2's ingestion fail loudly rather than warn, and it does not catch the `GBX`
   spelling, which is upper case. If you would rather 2.1 stayed at exactly the
   plan's line, this is the first thing to remove.

2. **`fct_trade.denomination_currency` is a column I added on judgement, and it
   may be dead weight.** The alternative is to derive it: Commission is charged in
   the Instrument's Quotation Currency, reachable by joining `dim_instrument`. I
   chose the explicit column because a broker does not necessarily bill in the
   currency an exchange quotes in, and because leaving it implicit hides the
   assumption inside a comment rather than the data. The cost is real: if 2.3's
   simulator always sets it equal to `quotation_currency`, the column carries no
   information and the Section C row I wrote for it describes a distinction the
   data never makes.

3. **I treated `movement_type` as a structural compound rather than a domain
   noun, and did not raise it as a fifth Term Proposal.** The reasoning: `_type`
   and `_date` are suffixes on registered terms in the same way `trade_date` and
   `instrument_type` are, so the column *name* follows an existing pattern. What is
   genuinely unregistered is the value vocabulary, which is why that half went to
   [DEBT-010](../debt-ledger.md) instead. You may think the name itself needed
   proposing; if so the fix is cheap now and expensive after 2.3 fills it.

4. **The constraint probe and the float check are additions to what the plan asked
   `check_warehouse.py` to do.** The plan specified table/column/row-count listing
   and the import scan. I added the other two because the schema comments make
   claims — "refuses a pence quotation", "no floating-point column" — and
   Non-Negotiable #4 says a claim without a run command is a guess. The probe
   builds a throwaway in-memory Warehouse from the same `schema.sql` and includes a
   positive control, so it cannot pass by rejecting everything.

5. **Reading the expected table set from the Glossary had a soft spot — found in
   review, and fixed.** The original parser required a whole cell to be exactly
   one table name, so the `Denomination Currency` row, which lists four
   comma-separated, contributed **none**. It changed no outcome, because all four
   are named by other rows, and that is precisely what made it dangerous: the
   check silently verified less than the Glossary said and nothing failed. See
   [Changes made on review](#changes-made-on-review--2026-08-05) below.

6. **Enforced foreign keys constrain Sub-step 2.2 in a way worth knowing now.**
   Dimensions must load before facts, so dlt's landing order matters. I think this
   is right — an orphan fact row is a wrong number waiting to be aggregated — but
   it is a constraint 2.2 inherits without having chosen it.

7. **`WarehouseAdapter.query` takes arbitrary SQL from any caller.** Nothing
   restricts it until the Validation Gate exists. That is dependency order rather
   than a shortcut, but it means the seam currently proves *where* SQL enters, not
   *what* may enter.

8. **`fx_rate` is `DECIMAL(18, 8)` while every other number is `DECIMAL(18, 6)`.**
   Deliberate — a reference rate carries more significant decimals than a price —
   but it is the one place the schema is inconsistent, and inconsistency is what
   the next person will assume is a mistake.

### Changes made on review — 2026-08-05

Amino reviewed the above, approved it, and asked for four fixes. All four are in
the verification output pasted above, which was re-run after them.

1. **The Glossary parser now reads the "Lives in" column by position and takes
   every table it names**, instead of requiring the whole cell to be one name. It
   also **reports what it could not read**: once the table names, backticks,
   commas and whitespace are removed, anything left is raised as a problem rather
   than skipped. A cell reading ``` `fct_trade` and the general ledger ``` now
   reads `fct_trade` *and* fails the run with the residue `'and the general
   ledger'`. The fix changes no outcome today — still ten tables, no problems —
   which is the whole argument for making it: a check that quietly checks less
   than it claims never tells you.

2. **`:memory:` is explicit rather than incidental.** It was working by accident:
   the adapter ran it through `Path()`, and `str(Path(":memory:"))` happens to
   return the same string, so nothing broke — but nothing said it was special
   either, and anything that resolved or joined that path later would have. There
   is now an `IN_MEMORY` constant, a branch that never passes it to `Path()`, an
   `is_in_memory` attribute, and a `WarehouseAdapter.in_memory()` constructor. The
   probe's call site reads `with WarehouseAdapter.in_memory() as probe:`.

3. **The `check_warehouse.py` docstring said "Three checks" when there were
   four**, having not been updated when the constraint probe was added — the exact
   documentation drift this project is about, in my own script. It now describes
   all four. It also renders properly: the default argparse formatter collapses
   all whitespace and re-wrapped the numbered list into one unbroken paragraph, so
   `formatter_class=argparse.RawDescriptionHelpFormatter` was added.

4. **Two probes were added for the snapshot grain** (below), taking the
   constraint probe from eight rejections to ten and the positive control from
   three seed rows to five.

### What "snapshot" means here

Amino asked whether "snapshot" implies state captured at intervals, with changes
between intervals missed. **It does, exactly**, and the schema now says so where
it binds rather than leaving it to be inferred from a table name.

A `_snapshot` table records **state as of** a date, at a grain of one row per
subject per date. That grain is now enforced by the primary key and probed:
`fct_position_snapshot` refuses a second row for one date, account and instrument,
and `fct_balance_snapshot` refuses a second row for one date, account and
currency. Two contradictory answers to *"what was held as of 2025-03-03"* cannot
both exist.

The consequence is real and worth stating plainly: **a snapshot cannot see between
its own dates.** A Position opened and closed inside a single day leaves the
snapshots either side of it identical, while `fct_trade` holds two Trades that
earned Commission and may have realised a profit. So:

| | sees | misses |
|---|---|---|
| snapshot delta | transfers, corporate actions | anything opened and closed between dates |
| sum of Trades | every execution | transfers, corporate actions |

Section C already warns of the second — *"Positions also change through transfers
and corporate actions"* — and this is the first. Neither is a repair for the
other, which is why both tables exist and why deriving one from the other was
rejected. The rule: **ask a snapshot what was held, ask `fct_trade` what was
done.**

**Two things this leaves for Sub-step 2.3 to decide rather than discover:**

- **Is a snapshot end-of-day?** Nothing says so yet. It matters because a Position
  marked at that date's Market Price — which is the *close* — is only coherent if
  the snapshot is taken at the close too.
- **Dense or sparse?** A row for every account × instrument × date, or only on
  dates something changed. Sparse means every "as of" question needs a
  most-recent-row-at-or-before lookup, which is the same shape as the fill-forward
  rule FX Rates already need. Dense means simple joins and a table that grows as
  the product of three axes.

**Language**

Four rulings, all approved by Amino on 2026-08-05 before any of them reached a
column name, and all recorded as
[R7–R10](../plan/step-002-warehouse-and-ingestion.md#r7r10--four-rulings-from-writing-the-data-definition-language-ddl-2026-08-05).

| Term | Ruling | Column |
|---|---|---|
| **`Instrument Symbol`** | added, `agreed` | `dim_instrument.instrument_symbol` |
| **`Trade Side`** | added, `agreed` | `fct_trade.trade_side` |
| **`Denomination Currency`** | added, `agreed`, with a Section C row against `Quotation Currency` | four tables |

The fourth ruling was not a new term but a contradiction: `Dimension Definition`
listed the instrument-type values as *"equity · bond · future · option"* while
`Instrument` — narrowed on 2026-08-03 by R1 — reads *"equity, ETF, future, or
currency pair"*. The parenthetical was missed when the universe narrowed, so the
`Dimension Definition` row was swept to match and `dim_instrument.instrument_type`
now refuses anything else. Like R2, this removed a contradiction rather than
making a choice.

Two naming decisions inside the schema that did not need a ruling but did need
thought:

- **`from_currency` / `to_currency` on `fct_fx_rate`**, not the conventional
  `base`/`quote` pair. "Quote currency" is standard Foreign Exchange vocabulary and
  would have sat one letter from `quotation_currency` while meaning something
  entirely different — a collision Section C exists to catch, arriving through the
  front door of an industry convention.
- **Three tokens were added to `check_language.py`'s known-non-abbreviation
  lists**, all found by the checker failing rather than by inspection. `GBX` joins
  the currency codes, because the documents now name it on purpose as the spelling
  the `dim_instrument` constraint does *not* catch. `BY` and `CHECK` join the SQL
  keywords already there — `SELECT`, `GROUP`, `INSERT` and the rest — because this
  is the first review with enough schema prose to quote them. None of the three is
  an abbreviation a reader could fail to look up, which is the test that list
  applies.

Glossary total: **85 registered terms**, as counted by `check_language.py` in the
run pasted above. Three terms were added this Sub-step; I have not put a
before-figure here, because the only honest source for one is the same script run
against the previous commit, and I did not run it that way.

#### 🆕 TERM PROPOSAL — `Snapshot` — **approved 2026-08-06 (R12)**

Registered in Section B, with end-of-day and the dense trading-day calendar folded
into the definition rather than left as loading conventions. The proposal as
written is kept below, since it is what was agreed to.

**Means:** the state of a subject as of a date, at a grain of one row per subject
per date. Authoritative for *"what was held as of D"*.

**Not:** a record of what happened *between* two dates — that is a Trade, a Cash
Movement or an Accounting Movement. A Snapshot cannot see between its own dates,
so a Position opened and closed inside one day leaves the Snapshots either side of
it identical.

**Needed for:** the word already names two tables and a column —
`fct_position_snapshot`, `fct_balance_snapshot`, `snapshot_date` — and is the
"Lives in" for two `agreed` terms, `Position` and `Cash Balance`, **without ever
having been defined**. Amino's review asking what it means is the symptom that
matters: a word doing this much load-bearing work in the schema, which a reader
has to ask about, is an unregistered domain noun.

**Alternatives considered:** `As-Of State` — more precise about the semantics and
nobody says it. Leaving it undefined — the status quo, and the reason the question
had to be asked at all.

Not registered, and not in any new identifier. The two table names that already
contain the word were agreed on 2026-07-23 and are unaffected either way; what a
ruling changes is whether the meaning above becomes Glossary law or stays a
comment in `schema.sql`.

---

### Changes made on review — 2026-08-06

Amino held the commit open on one question: *assuming the current design — asking
snapshot tables "what was held" and trade tables "what was done" — is there any
question that cannot be answered?* Plus a specific case: *are we satisfied that
balance and positions can only be answered on a daily basis?*

#### The walk

Every Certified Metric named in Glossary Section B, against the ten tables:

| Certified Metric | Computed from | Answerable as built? |
|---|---|---|
| Traded Notional | `fct_trade.quantity × execution_price` | ✅ |
| Trade Count | `fct_trade` | ✅ |
| Gross Revenue | `fct_trade.commission` | ✅ |
| Net Revenue | `− rebate − fee` | ✅ |
| Cash Balance | `fct_balance_snapshot` | ✅ |
| Account Value | balance + position × Market Price × FX Rate | ✅ (daily) |
| Position Change | delta between two snapshot dates | ✅ (daily) |
| **Realised P&L** | closing price − cost of the lot sold | ⚠️ no home named |
| **Unrealised P&L** | quantity × Market Price − **Cost Basis** | ❌ **nothing to compute it from** |

Neither P&L metric is optional. Both are `agreed`, and Section D registers *"P&L"*
as an Ambiguous Term resolving to *"Realised · Unrealised · both"* — so Veritas
must be able to produce either on demand. `data-availability.md` already treats
them as live, warning that adjusted close *"makes Account Value, Realised P&L and
Unrealised P&L all subtly wrong and irreproducible"*. The schema forbade adjusted
close and then gave two of those three nowhere to stand.

#### Was daily the problem? No — and it is not a choice we made

The daily grain is a **floor imposed by the sources**, not a consequence of
snapshotting, and `schema.sql` now says so in its conventions block so it is not
"repaid" later as if it were debt:

- Market Price arrives as daily bars — `data-availability.md` records *"1,255
  bars"* over five years for AAPL.
- FX Rate is one ECB reference rate per working day — *"2025 gave **256** daily
  rates"* — with a registered fill-forward rule.
- `Dimension Definition` has registered the date axis as **"by date
  (`trade_date`, daily)"** since 2026-07-23. Daily *is* the certified slicing
  grain, so a sub-daily question has no Dimension Definition to ground against and
  Veritas refuses it. Refusing is a Target State non-goal working as designed.

The decisive point: **`fct_trade.trade_date` is a `DATE`, not a `TIMESTAMP`.**
Intraday is out of reach for the *event* tables too, so event-sourcing positions
would buy attribution, not resolution — and an Account Value at 14:32 would still
be marked at a close that has not happened yet. Precision in one factor and
staleness in another is the quietly-wrong number this project exists to prevent.
Nor is the intraday round trip actually lost: a Position opened and closed inside
one day is invisible to snapshots but is two rows in `fct_trade`.

#### Why Cost Basis is stored, in three examples

Unrealised P&L is `quantity × Market Price − Cost Basis`. The first two exist as
columns; the third did not. The alternative to storing it is **folding** it — a
query that walks the client's whole trade history and adds up what they paid. The
three examples below are what convinced me that fold returns a plausible wrong
number. Each uses the same client.

> **Setup.** A client buys 100 AAPL at \$150 in January (\$15,000), then 100 more
> at \$170 in June (\$17,000). They hold **200 shares that cost \$32,000**. AAPL
> is \$180 today, so the true Unrealised P&L is
> `200 × 180 − 32,000 = ` **\$4,000 profit**.

**Example 1 — the fold breaks the moment you filter by date.**
Someone asks *"what was their Unrealised P&L in Q3?"* (July–September). The
Dimension Definition applies a date filter, which narrows `fct_trade` to Q3 — and
this client made **no trades in Q3**. So the fold finds no purchases, computes a
cost of \$0, and answers `200 × 180 − 0 = ` **\$36,000**. Off by the entire cost of
the holding, and it looks like a spectacular quarter. Nothing in the Validation
Gate can catch this: the SQL is valid, the metric is certified, the filter is the
one that was asked for. With a stored column the Q3 snapshot row already says
`quantity 200, cost_basis 32,000` and the answer is \$4,000 under any filter.

**Example 2 — the fold cannot see shares that arrived without a trade.**
The client transfers in 50 AAPL shares from another broker. There is no row in
`fct_trade`, because no trade happened — this is the Section C case *Position
Change vs Trade*, and it is the reason this table is snapshotted at all. The
snapshot correctly says 250 shares. The fold still only knows about \$32,000 of
purchases, so it answers `250 × 180 − 32,000 = ` **\$13,000** — crediting the
client with pure profit on 50 shares that in fact cost them something. With a
column, whatever those shares cost is recorded when they arrive.

**Example 3 — the fold flips the sign after a round trip.**
The client buys 100 at \$150, sells all 100 at \$160, and later buys 100 at \$200.
They now hold 100 shares that cost **\$20,000**. At \$180 that is a **\$2,000
loss**. But the natural fold — average what they paid across all purchases —
computes `(15,000 + 20,000) / 200 = $175` per share and reports a **\$500 profit**.
The client is told they are up when they are down. Getting this right needs the
fold to notice the position went to zero and reset, which is a stateful rule that
has to be written correctly once and then survive every future edit.

**The common thread:** the fold is not one expression, it is an expression *plus a
set of conditions* — the position opened inside the loaded window, never went flat
and rebuilt, and was never touched by a transfer. Those conditions are invisible
in the SQL and are not checkable by the Validation Gate, and the third one is the
exact thing this table exists because it cannot promise. Stored, Cost Basis is an
ordinary column on a row: it survives any filter and needs no conditions at all.

**The counter-argument, recorded because it is a real one:** this designs against
a Metric Definition that does not exist yet, which is precisely the reasoning
[DEBT-010](../debt-ledger.md) used to defer — *"guessing at requirements that do
not exist"* — and the simulator is seeded, so a later re-run is cheap. What tipped
it is that the choice was not *decide now* versus *decide later*, but *decide
later having already learned the fold is hazardous*. Amino ruled: add it now.

#### What changed

1. **`Cost Basis` registered** (Section B, `fct_position_snapshot`) with a Section
   C row against `Execution Price` — one fill versus the accumulated cost of a
   whole holding, and different shapes besides, one per-unit and one a total.
2. **`cost_basis DECIMAL(18, 6) NOT NULL`** added to `fct_position_snapshot`,
   signed so that one expression covers long and short, plus
   `CHECK (quantity != 0 OR cost_basis = 0)` — a closed Position holds nothing, so
   it cost nothing to hold, and a stale basis on a zero row would report P&L on a
   holding that does not exist. That check is the eleventh constraint probe.
3. **`Realised P&L` needed no schema change.** It is a value recognised on a date,
   which is what `Accounting Movement` is registered to hold — *"a ledger entry
   recognising economic value on the date it was earned, whether or not cash
   moved"* — so it is an `fct_accounting_movement` posting keyed by the closing
   Trade. [DEBT-010](../debt-ledger.md) was **amended**, not merely annotated: its
   "Why we deferred" paragraph claimed no Certified Metric consumes a
   `movement_type`, and that claim is now false.
4. **[EXT-006](../extension-register.md#ext-006--position-change-attribution)
   opened** for Position Change attribution, against the `fct_position_snapshot`
   seam. `Position Change` as registered promises *"change… from any cause"* — the
   change, not the cause — so the slice is right as built.
5. **`schema.sql` conventions block** gained the daily-grain paragraph.
6. **Current State's known-gaps section was rewritten, not appended to.** It had
   said a cost basis column was unnecessary because both P&L metrics *"can be
   expressed as a weighted average of Execution Prices over `fct_trade`"*. That
   sentence was wrong and is now quoted as wrong rather than quietly deleted.
7. **A third convention was added to Sub-step 2.3's list**, and one of the existing
   two was corrected: snapshot density and Market Price density are **one decision,
   not two**. `FX Rate` carries a registered fill-forward rule and `Market Price`
   carries none, so dense snapshots against trading-day-only prices means Account
   Value on a Sunday joins to nothing.
8. **`check_language.py`'s SQL-keyword exemption is now derived rather than
   remembered.** It failed on `DATE`, `NOT` and `OR` — the third time the same
   defect has fired, after `BY` and `CHECK` the day before. The root cause was a
   list maintained one failure at a time, so it is always one document behind
   whatever prose quotes the schema next. It now holds the whole keyword
   vocabulary of our own Data Definition Language (DDL), with the one-line command
   that re-derives it after a schema change recorded beside it. Adding the three
   failing words would have left the fourth failure waiting.

#### Verification after the change

```
$ uv run python .claude/scripts/check_warehouse.py --rebuild
  fct_position_snapshot  —  5 columns, 0 rows
      snapshot_date            DATE
      account_id               BIGINT
      instrument_id            BIGINT
      quantity                 DECIMAL(18,6)
      cost_basis               DECIMAL(18,6)
...
  constraint probe (in-memory Warehouse from the same schema.sql)
    accepted  7 valid seed rows (positive control)
    refused   dim_instrument refuses a pence quotation (`GBp`) — the 100x trap
    refused   dim_instrument refuses an out-of-scope instrument type
    refused   dim_client refuses a region the Dimension Definition does not name
    refused   fct_trade refuses a trade_side outside 'buy'/'sell', including 'BUY'
    refused   fct_trade refuses a negative quantity — direction lives in trade_side
    refused   fct_trade refuses settlement before trade
    refused   fct_trade refuses an orphan account_id
    refused   fct_instrument_price refuses an orphan instrument_id
    refused   fct_position_snapshot refuses a second row for one date, account, instrument
    refused   fct_balance_snapshot refuses a second row for one date, account, currency
    refused   fct_position_snapshot refuses a Cost Basis on a closed Position
    refused   fct_cash_movement refuses 'realised P&L' — no cash moves when a Position closes
    refused   fct_accounting_movement refuses 'deposit' — a deposit earns nothing
    refused   fct_cash_movement refuses 'Deposit' — one spelling per concept

  seam scan: 7 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
```

The table listing is elided at `...` — the other nine tables printed unchanged, and
the full output is what the command above reproduces. Four of the fourteen refusals
are new since the block earlier in this review: the Cost Basis one from R11, and
the three movement-vocabulary ones from R15.

```
$ uv run python .claude/scripts/check_language.py
  glossary: 87 registered terms
  proposed terms: 0 · python files scanned: 7 · identifiers: 268
  abbreviations: 23 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

87 terms, up from the 85 counted in the run pasted earlier in this review —
`Cost Basis` and `Snapshot` are the difference, and all figures come from the same
script.

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       652 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr         1037 words
  python     3.14.4                 /home/amino/Projects/veritas/.claude/worktrees/step-002-substep-2-1/.venv/bin/python3

PASS — framework is wired up correctly
```

#### Sceptical about this change

- **The `CHECK (quantity != 0 OR cost_basis = 0)` constraint asserts a convention
  nothing yet produces.** No loader writes a snapshot row until 2.3, so the rule
  binds a simulator that does not exist. That is the intended direction — the
  constraint is what tells 2.3 the convention rather than 2.3 discovering it — but
  it is worth naming that it currently constrains nothing.
- **Cost Basis is registered as *total*, not per unit, and the two are easy to
  confuse in a Metric Definition.** The Section C row is the defence; there is no
  code check, and there cannot be until a Metric Definition exists to check.
- **The signed-basis convention is verified by argument, not by data.** The long
  and short worked examples in `schema.sql` are arithmetic I checked by hand, not
  a probe. A probe would need rows, which arrive in 2.3.
- ~~**`Realised P&L` living in `fct_accounting_movement` is a decision recorded in
  two registers but implemented in neither.**~~ **Closed 2026-08-06 (R15).** Amino's
  ruling on this item was *"if that 'if' is a bad one, make sure it won't happen —
  don't leave these cases hanging hoping that they will get fixed."* It was a bad
  "if": the only thing standing between 2.3 and a homeless metric was someone
  reading a ledger entry. So [DEBT-010](../debt-ledger.md) was **paid** instead of
  annotated — its justification had already been falsified — and both
  `movement_type` columns now carry a `CHECK` whose two lists deliberately differ.
  The engine now refuses the failure. See the ledger entry for the vocabulary and
  the three probes that hold it.

---

### The three snapshot conventions — **all three approved 2026-08-06**

Recorded as [R12–R14](../plan/step-002-warehouse-and-ingestion.md#r11r15--five-rulings-from-aminos-review-of-the-snapshot-design-2026-08-06).
These are Sub-step 2.3's to implement, but they were decisions rather than
discoveries, so they were settled before the simulator is written. This section is
the only place they are argued; `current-state.md` and the plan link here.

Two of the three left something behind that is now enforced rather than intended:
`Snapshot`'s Glossary definition carries end-of-day and the dense trading-day
calendar, and `--sources` is required to prove the price window is split-free.

#### 1. End-of-day — recommend yes

`Market Price` is registered as *"the unadjusted closing price at which an
Instrument traded on a date"*. A Position marked at that date's **closing** price
must be the position held at the **close**, or Account Value mixes a holding from
one moment with a price from another — a wrong number with no error anywhere.

End-of-day also makes the delta arithmetic line up with the event tables:
`snapshot(D) − snapshot(D−1)` is everything that happened during day D, which is
exactly the set of Trades with `trade_date = D`. Under any other convention the
two are offset by part of a day and a reconciliation that should be exact is not.

No real cost, and the alternative has no argument for it that I can find.

#### 2. Dense or sparse — recommend dense, over trading days only

One row per account × instrument per **trading day**, where the trading-day
calendar is *the set of dates present in `fct_instrument_price`* — not the calendar
week.

Two decisions in one, and they must agree:

- **Dense rather than sparse**, because sparse makes every "as of" question a
  most-recent-row-at-or-before lookup — a correlated subquery or a window function
  that has to be right in every Join Path, forever. Dense makes it an equality
  join. Veritas generates SQL for a living; the version with fewer ways to be
  subtly wrong is worth the rows. And the rows are cheap: a synthetic book of ~50
  accounts × ~20 instruments × ~250 trading days is on the order of 250,000 rows,
  which is nothing to DuckDB.
- **Trading days rather than calendar days**, because Account Value needs a Market
  Price on the same date. Dense-over-calendar-days manufactures Saturday snapshot
  rows that join to no price row, and *"what was this account worth on Sunday?"*
  returns an empty result or a silent `NULL` mark. This is the half I previously
  had as a separate decision about `Market Price` fill-forward; it is not separate.

The payoff is that the rule becomes checkable rather than conventional: **every
`snapshot_date` must exist in `fct_instrument_price.price_date`.** That is one
more probe for `check_warehouse.py` in 2.3, and it is what stops the two densities
drifting apart later.

**The simplification worth naming:** instruments do not share one calendar. LSE,
NASDAQ and a currency pair have different holidays, so "the set of dates in
`fct_instrument_price`" is really a union across instruments, and a snapshot on a
date when one venue was shut still has no price for that instrument. For a slice
whose held instruments are chosen by us, the cheap answer is to choose them from
one calendar and say so. If 2.3 wants a genuinely multi-venue book, this becomes a
per-instrument fill-forward rule and deserves its own decision.

#### 3. Non-trade movements — recommend transfers yes, corporate actions no

**Transfers: yes, a small number, deliberately.** *Position Change vs Trade* is one
of the twelve Section C distinctions, and it is the one the snapshot tables exist
for. If every Position moves only by Trade, then in our data a snapshot delta and a
sum of Trades are equal **everywhere**, and no Gold Question can discriminate the
two. Evaluation would score a model that conflates them as fully correct, and the
distinction would be a claim in the Glossary that the warehouse quietly refutes.
A handful — transfers on two or three accounts — is enough for one Gold Question
to catch it, and it needs no new table.

It also puts the Cost Basis column under load in the one case that proves it earns
its place: transferred shares arrive with a cost that `fct_trade` can never supply,
which is Example 2 above.

**Corporate actions: no, and this needs an explicit guard.** A split is not
symmetrical with a transfer, because `Market Price` is **real data** while the
Position is synthetic. If a held Instrument splits 4:1 inside the loaded window,
the real unadjusted close drops ~75% overnight. A simulator that ignores it shows
Account Value collapsing with no trade behind it. Handling it properly means
adjusting quantity at the split — which is the corporate-action machinery we do not
want — and the one thing we must *not* do is reach for `Adjusted Close`, which is
registered as an anti-pattern precisely here.

The cheap way out is to keep the price window free of splits for held Instruments
and **verify it rather than assume it**: a day-over-day ratio in any loaded price
series above a threshold is either a split or a market event worth knowing about,
and it should fail `check_warehouse.py --sources` in Sub-step 2.2. Recording it as
a check rather than an intention is the difference between this holding and this
having held on the day someone widened the window.
