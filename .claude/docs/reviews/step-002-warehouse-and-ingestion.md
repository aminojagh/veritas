# Step Review — Step 002: Build the Warehouse and fill it

> **Note added 2026-08-10 — the Sub-steps below 2.1 were renumbered after this
> review was written, and the body is left untouched because it is a dated
> record.** Amino approved
> [R16](../plan/step-002-warehouse-and-ingestion.md#r16--the-original-sub-step-22-splits-into-three--approved-by-amino-2026-08-10),
> which split the one real-market-data Sub-step into three. Read every forward
> reference below through this map:
>
> | Written here as | Now |
> |---|---|
> | 2.2 — all real market data | **2.2** `dim_instrument` · **2.3** `fct_instrument_price` · **2.4** `fct_fx_rate` |
> | 2.3 — synthetic client activity | **2.5** |
> | 2.4 — the sqlglot spike | deferred to **Step 003** by [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved) |
>
> Two specific handoffs below land more precisely under the new numbering. The
> `--sources` split-free check now belongs to **2.3**, the Sub-step that loads the
> price window it inspects. The enforced-foreign-key constraint still binds
> **2.2**, unchanged — it is why `dim_instrument` loads before
> `fct_instrument_price`, which is now the 2.2-before-2.3 ordering rather than an
> ordering inside one Sub-step.

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

---

## Sub-step 2.2 — Load `dim_instrument` from NASDAQ Trader and the Securities and Exchange Commission (SEC)

**What changed**

`Ingestion` exists. `uv run python -m veritas.ingestion` builds the Warehouse from
nothing, offline, and fills one of its ten tables with sixteen real Instruments.

- **`veritas/ingestion/`** — four modules with one job each. `universe.py` holds
  the sixteen traded Instruments and two vocabulary maps; `snapshots.py` is the
  only module in the package that opens a socket; `sources.py` parses each source
  into records; `__main__.py` wires dlt to the adapter.
- **Snapshot-and-replay, applied to every real source.** Replay is the default and
  needs no network. `--refresh` re-hits the sources and rewrites
  `data/snapshots/ingestion/` — 22 files, 2.6 MB.
- **`veritas/warehouse/builds/dim_instrument.sql`** — the raw-to-star SQL,
  hand-authored, run through the new `WarehouseAdapter.run_build`. It sits on the
  adapter's side of the seam on purpose; see the DEBT-009 note below.
- **[ADR-0004](../adr/0004-snapshot-and-replay-and-where-dlt-stops.md)**, `proposed` —
  snapshot-and-replay's scope, and where dlt stops.
- **`check_warehouse.py --sources`** — three assertions, and `--rebuild` and
  `--sources` are now mutually exclusive, since together they only ever prove an
  empty table is empty.
- `uv add dlt`.

**Verification**

```
$ uv run python -m veritas.ingestion
  mode: replay (offline)
  snapshots: data/snapshots/ingestion
  universe: 19 Instruments

    dim_account                   0 rows
    dim_client                    0 rows
  · dim_instrument               19 rows
    fct_accounting_movement       0 rows
    fct_balance_snapshot          0 rows
    fct_cash_movement             0 rows
    fct_fx_rate                   0 rows
    fct_instrument_price          0 rows
    fct_position_snapshot         0 rows
    fct_trade                     0 rows

PASS — the Warehouse is built · dim_instrument holds 19 Instruments
exit: 0
```

```
$ uv run python .claude/scripts/check_warehouse.py --sources
  Warehouse: data/veritas.duckdb (already existed)
  Glossary Section B names 10 tables · the Warehouse has 10

  [the per-table column listing is unchanged from Sub-step 2.1 and elided here
   for length — it is the same output that review already records, and the
   command above reproduces all of it]

  dim_instrument: 19 rows · 19 Instruments declared in universe.py
    minor units: none of ['GBp'] survived normalisation
    symbols: all 19 declared Instruments present, none repeated
    raw.nasdaq_symbol           13117 rows
    raw.sec_registrant          10398 rows
    raw.yahoo_instrument           19 rows
    raw.minor_unit_currency         1 rows
    raw.yahoo_instrument_type       4 rows
    instrument_type: ETF 4 · currency pair 3 · equity 9 · future 3
    quotation_currency: EUR 3 · GBP 2 · JPY 3 · USD 11
    richness: 4 types (min 3 each) · 4 currencies · minor unit normalised
  constraint probe (in-memory Warehouse from the same schema.sql)
    accepted  7 valid seed rows (positive control)
    [fourteen refusals, unchanged from 2.1]

  seam scan: 12 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
exit: 0
```

`check_language.py` and `verify_framework.py` both PASS; the former now scans 12
Python files and 371 identifiers, against 7 and 268 at the end of 2.1.

**Both checks were made to fail before being trusted.** Deleting `VOD.L` from
`dim_instrument` produced *"declared in universe.py but absent from
dim_instrument: ['VOD.L']"* and exit 1. Pointing the SEC source at a 404 produced
the source-failure path and exit 1. The second of those found a real defect, which
is why it is worth doing: dlt wraps a resource's exception in its own
`PipelineStepFailed`, so the original `except SourceUnavailable` never fired and
the operator got a dlt traceback instead of the sentence telling them what to do.
`source_failure()` now walks the exception chain.

**Deliberately left undone**

- **No new Debt Ledger entry.** The one candidate was that `--refresh` is not
  transactional — nineteen files rewritten one at a time, so a failure part-way
  leaves a mix of fresh and stale snapshots. `recording-debt` says to fix rather
  than document when the fix is smaller than the entry, so the failure path now
  names every snapshot it had already rewritten and says not to commit until a
  refresh succeeds. What remains is visible rather than silent.
- **[DEBT-002](../debt-ledger.md) is not paid**, and its trigger has not fired —
  trigger 1 names the *market-price* pipeline, which is 2.3. The snapshot half of
  the mitigation landed here, one Sub-step early, so the pipeline can never exist
  without a snapshot behind it.
- **[DEBT-009](../debt-ledger.md)'s trigger came close and did not fire**,
  deliberately. Ingestion needed SQL to build `dim_instrument`; putting it in
  `veritas/ingestion/` would have made that package the first component outside the
  adapter to emit SQL. It lives in `veritas/warehouse/builds/` instead, which is
  where R4 puts it anyway. One draft of `--sources` did interpolate a table name
  into a `count(*)` string — that is now `WarehouseAdapter.row_count`, which reaches
  `raw` through the relational API and assembles no text.
- **The split-free check is not here.** It belongs to 2.3, which loads the price
  window it inspects.

**Look at this sceptically**

1. **2.2 reads Yahoo's `meta` block, and the plan did not list Yahoo among this
   Sub-step's sources.** This is the judgement call to check first. Neither NASDAQ
   Trader file has a currency column — the header is
   `Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares`
   — and the SEC file carries only a name and a key. Yahoo's `meta.currency` is the
   only place any source states an Instrument's Quotation Currency, and it is where
   the literal `GBp` comes from. Building from the two named sources alone would
   mean guessing currency from a symbol suffix, and a guessed `GBP` would make both
   the schema's CHECK and this Sub-step's own assertion pass **without ever meeting
   the trap they exist to catch**. `data-availability.md` already said this: *"Non-US
   Instruments (SAP.DE, VOD.L, 7203.T) come from the price source's own metadata,
   which returns exchange, currency and instrument type per symbol."* I read the
   plan's "NASDAQ Trader · SEC" as shorthand that the design document had already
   qualified. **If you disagree, the alternative is a hand-authored suffix-to-currency
   map, and it is worse for the reason above.**
2. **The universe is nineteen symbols I chose.** Four types, four currencies, EU/UK/
   APAC/US. Bond exposure is TLT and BNDX because DEBT-003 rules out single bonds.
   Two GBp listings rather than one, so the 100x trap is a class of row and not a
   special case.

   **Richness is now asserted rather than printed** (added on Amino's review):
   every `instrument_type` present, **at least two Instruments of each**, at least
   three Quotation Currencies, and at least one normalised from a minor unit. The
   two-of-each bar is the one that bites — a type with a single member turns a
   metric sliced to that type into a report on one security, and no simulator
   cleverness in 2.5 repairs that afterwards.

   **It failed on the first run**, on the universe this review originally
   described: `only one Instrument of type ['currency pair']`. The sources were
   made richer rather than the bar lowered — `GBPUSD=X`, `USDJPY=X` and `CL=F`
   were added, one currency pair per non-EUR currency the book is quoted in, and a
   third future. The thinnest type is now three. That the check found a real gap
   on its first execution is the argument for it existing.
3. **`instrument_name` is visibly mixed-case** — `JOHNSON & JOHNSON` and
   `MICROSOFT CORP` next to `SAP SE`. The `coalesce` takes the SEC's registered
   name, then NASDAQ's security name, then Yahoo's long name. The shouting is the
   SEC's own, not a transform this code applied.

   **The criterion, stated properly** — the first version of this note gave the
   choice without the rule behind it, which is a fair complaint. The question is
   *what `instrument_name` is for*, and there are exactly two answers:

   | If it is a **record** | If it is a **label** |
   |---|---|
   | The name exists so a row can be traced to the entity a registry recognises | The name exists so a person reading a Grounded Answer knows which company it is |
   | Most authoritative source wins → SEC, NASDAQ, Yahoo | Most consistent source wins → Yahoo's `longName` throughout |
   | Mixed case is the sources' truth, faithfully carried | Mixed case is a defect in a user-facing string |

   **I chose *record*, and the reasoning is one step, not a preference:** this
   project's subject is numbers being traceable to where they came from, and a
   name is the only column in `dim_instrument` that a human uses to check a row is
   the company they meant. A name taken from the most authoritative source is
   checkable against a registry; a name taken from the tidiest source is not.

   **What would change my mind, and what to weigh:** nothing downstream computes
   on this column — no Certified Metric touches it — so the *record* argument buys
   traceability that only a human ever exercises, while the *label* argument buys
   readability in every answer the App will ever render. If you expect
   `instrument_name` to appear in Grounded Answers, **label is the better rule and
   I would switch**. The change is the `coalesce` order in
   `veritas/warehouse/builds/dim_instrument.sql`, and nothing else moves. I left it
   as *record* because the App does not exist yet and the reversible choice is the
   one that keeps the more authoritative data in the column meanwhile.
4. **Ingestion deletes and rebuilds the Warehouse on every run.** `schema.sql` uses
   plain `CREATE TABLE`, so there is nothing to reconcile, and a pipeline whose
   output depends on how many times it ran is not reproducible. But it does mean
   the command is destructive, and it says so in one line of output rather than
   asking.
5. **2.6 MB of committed snapshots, of which ~1.5 MB is reference data for symbols
   outside the universe.** Filtering would halve it and would break the property
   that replay and `--refresh` exercise the same parser. Recorded as an accepted
   cost in ADR-0004 rather than as debt.
6. **dlt is a large dependency for five small tables** — roughly forty transitive
   packages. R4 chose it before this Sub-step; I am flagging the size, not
   reopening the ruling. One side effect is genuinely useful: `sqlglot` is now
   installed, a Step before anything planned to use it.

**Language**

No new terms, and none proposed. Every domain identifier added resolves to a
registered term: `Instrument`, `Instrument Symbol`, `Quotation Currency`,
`Ingestion`, `Market Price`, `FX Rate`, `Snapshot`. `TRADED_INSTRUMENTS` is built
from `Instrument` rather than coining "universe" as an identifier, though the
prose uses *"the traded Instrument universe"* as `data-availability.md` already
does.

One checker change worth noting, because it is the kind that hides a rule rot:
`check_language.py` flagged `ACT` — NASDAQ Trader's `ACT Symbol` column, quoted in
ADR-0004. Rather than append two ticker symbols to a hand-maintained list, the
traded universe's tokens are now **derived** from `TRADED_INSTRUMENTS`, the same
way the schema-keyword group is derived from `schema.sql`. That file's own comment
argued for this: a remembered list *"is always one document behind"*. `ACT` itself
is listed as a source's column name, which is what it is.

---

## Sub-step 2.3 — Load `fct_instrument_price` from Yahoo by snapshot-and-replay

**What changed**

The Warehouse now holds numbers that can be aggregated. `fct_instrument_price`
carries **9,549 Market Prices** — two years of daily closes for all nineteen
traded Instruments, loaded offline from the snapshots Sub-step 2.2 had already
committed. [DEBT-002](../debt-ledger.md), open since Sub-step 1.2, is **paid**.

Four things, in the order they matter.

- **`veritas/warehouse/builds/fct_instrument_price.sql`** — the second build
  script, and the place all three of this Sub-step's transforms live. A bar's
  epoch timestamp becomes a trading date *on the exchange's own clock*; a pence
  quote is divided down to pounds; a session that had not closed when the snapshot
  was taken is dropped. Each is argued at the line that performs it, because
  `raw.yahoo_price` deliberately holds none of them — ADR-0004 says values in
  `raw` are the source's, so this file is the one place a reader looks for what
  was done to the numbers.
- **`veritas/ingestion/sources.py`** — `yahoo_prices` reads the `timestamp` and
  `indicators` blocks of the same nineteen chart responses whose `meta` block 2.2
  read. `close`, never `adjclose`. Adding the source cost one entry in
  `FETCHED_TABLES` and one in `BUILDS`, which is what ADR-0004 said it would cost.
- **`veritas/ingestion/snapshots.py`** — `read_source` now caches a source's bytes
  for the run. This is a defect fix, not a tidy-up: see *Look at this sceptically*.
- **`.claude/scripts/check_warehouse.py --sources`** — grows by a `check_prices`
  function that re-derives every price from the committed snapshots **in Python**
  and compares it to what the SQL built, then measures what three specific wrong
  readings would have changed.

**The Sub-step's most useful output is a wrong number it caught before it landed.**
`check_data_availability.py` converts a Yahoo bar's timestamp with
`datetime.fromtimestamp(stamp, dt.UTC).date()`, and copying that into the build
would have been the obvious move. It is wrong for the three currency pairs: their
daily bars are stamped 23:00 UTC, which is midnight in London, so **every one of
their bars would have been booked a day early**. The check reports the size of it
on the loaded data — `1075/9549 rows change (11%), across 6 of 19 Instruments` —
and the six are the three currency pairs plus the three futures, whose regular
session ends at 03:59 UTC the following day and whose in-progress bar therefore
stops being recognised as one. `EURUSD=X` is stored at `1.091381` on **2024-08-12**,
which is the date the London market traded it; the UTC reading files it under
2024-08-11.

The in-progress bar is the second thing the Glossary decided rather than the code.
`Market Price` is *"the unadjusted **closing** price at which an Instrument traded
on a date"*, and eleven of the nineteen snapshots were fetched at 13:28 UTC on
2026-08-10 — while London was still dealing and before New York opened — so their
final bar is a live price rather than a close. It is landed in `raw` and dropped
in the build, using `meta.regularMarketTime` against
`meta.currentTradingPeriod.regular.end`. Without this, R12's *"a Position marked at
that date's closing Market Price must be the Position held at the close"* would
have been false on its first day.

**Verification**

```
$ uv run python -m veritas.ingestion
  mode: replay (offline)
  snapshots: data/snapshots/ingestion
  universe: 19 Instruments
  removed data/veritas.duckdb — rebuilding

    dim_account                   0 rows
    dim_client                    0 rows
  · dim_instrument               19 rows
    fct_accounting_movement       0 rows
    fct_balance_snapshot          0 rows
    fct_cash_movement             0 rows
    fct_fx_rate                   0 rows
  · fct_instrument_price       9549 rows
    fct_position_snapshot         0 rows
    fct_trade                     0 rows

PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9549 Market Prices across all 19
exit: 0
```

```
$ uv run python .claude/scripts/check_warehouse.py --sources
  Warehouse: data/veritas.duckdb (already existed)
  Glossary Section B names 10 tables · the Warehouse has 10

  [the per-table column listing is unchanged in shape from Sub-step 2.1 and
   elided here for length. The one row that is new:
       fct_instrument_price  —  3 columns, 9549 rows
           price_date               DATE
           instrument_id            BIGINT
           market_price             DECIMAL(18,6)  ]

  dim_instrument: 19 rows · 19 Instruments declared in universe.py
    minor units: none of ['GBp'] survived normalisation
    symbols: all 19 declared Instruments present, none repeated
    raw.nasdaq_symbol           13117 rows
    raw.sec_registrant          10398 rows
    raw.yahoo_instrument           19 rows
    raw.yahoo_price              9586 rows
    raw.minor_unit_currency         1 rows
    raw.yahoo_instrument_type       4 rows
    instrument_type: ETF 4 · currency pair 3 · equity 9 · future 3
    quotation_currency: EUR 3 · GBP 2 · JPY 3 · USD 11
    richness: 4 types (min 3 each) · 4 currencies · minor unit normalised

  fct_instrument_price: 9549 rows · 19 Instruments · 521 distinct dates (2024-08-08 to 2026-08-10)
    values: all 9549 rows equal the snapshot's unadjusted close, on the exchange's own date, in the major unit
    if it takes indicators.adjclose instead of indicators.quote:
      5416/9549 rows change (57%), across 12 of 19 Instruments
    if it reads a bar's timestamp as a Coordinated Universal Time (UTC) date rather than shifting it onto the exchange's clock:
      1075/9549 rows change (11%), across 6 of 19 Instruments
    if it skips the division by minor_units_per_major:
      1006/9549 rows change (11%), across 2 of 19 Instruments
    corporate actions: largest day-over-day ratio is 1.196 (CL=F into 2026-04-08), against a 1.5 threshold
    calendars: 521 dates have a price for at least one Instrument · 452 have one for all 19 (Sub-step 2.5 chooses between them)
  constraint probe (in-memory Warehouse from the same schema.sql)
    accepted  7 valid seed rows (positive control)
    [fourteen refusals, unchanged from 2.1]

  seam scan: 12 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
exit: 0
```

`check_language.py` and `verify_framework.py` both PASS; the former now scans 437
identifiers across the same 12 Python files, against 371 at the end of 2.2, with 0
unrecognised abbreviations.

**The check was made to fail three times before being trusted**, by mutating the
build script and re-running the pipeline and the check unchanged. All three exit
1, and each names the specific mistake rather than reporting a generic mismatch:

| Mutation to `fct_instrument_price.sql` | What `--sources` reported |
|---|---|
| Drop `+ yahoo.utc_offset_seconds` — read the bar as a UTC date | `180 missing · 180 unexpected · 712 wrong`, and the date range widened from 521 to 580 distinct dates |
| Replace the minor-unit factor with `1` — carry pence across as pounds | `0 missing · 0 unexpected · 1006 wrong` |
| Delete the in-progress clause — store a mid-session price as a close | `0 missing · 11 unexpected · 0 wrong`, and the row count rose 9,549 → 9,560 |

The counterfactual lines move in the opposite direction under each mutation — with
the time-zone shift removed, *"if it reads a bar's timestamp as a UTC date"* falls
from 1075 rows to 3 — which is the check reporting that the build has already made
that mistake. The build script was restored byte-for-byte afterwards and both
commands re-run.

**Determinism.** Two consecutive runs of `uv run python -m veritas.ingestion`
produce identical output, including every row count. The Warehouse is deleted and
rebuilt on each run, so this is a property of the snapshots rather than of the
database file surviving.

**Deliberately left undone**

- **`--refresh` was not run, so the caching change to `read_source` is verified by
  reading rather than by execution.** Running it would open nineteen sockets and
  rewrite all 22 committed snapshots with a later window, which would silently
  invalidate every number in this review and is Amino's call rather than mine. The
  replay path — the one a reviewer runs and the one [DEBT-002](../debt-ledger.md)
  is about — is fully exercised above. What is unexercised is narrow: that a
  refresh now fetches each chart once instead of twice. The cache lookup is the
  first statement in `read_source`, so the fetch is structurally unreachable for a
  name already read; that is an argument, not a test, and it is the one claim in
  this Sub-step I have not run. **Not filed as debt** — the code is right rather
  than cheap, and a Ledger entry whose repayment is "run the command that rewrites
  the dataset" is a wish, not a trigger. Sub-step 2.4 adds Frankfurter and is the
  natural place to run a refresh once, deliberately.
- **The trading-calendar gap is surfaced, not solved.** 521 dates have a price for
  at least one Instrument; only 452 have one for all nineteen. R13 requires a
  Snapshot on *"every date the Warehouse holds a Market Price"*, and with five
  exchange calendars in one table those two readings differ by 69 dates. Choosing
  between them is Sub-step 2.5's, which is why the number is printed on every run
  rather than left to be discovered there.
- **No index beyond the primary key**, no partitioning, no incremental load. The
  pipeline drops and rebuilds; 9,549 rows do not justify anything else.

**Look at this sceptically**

1. **`read_source` now caches, and the reason is a defect I introduced and then
   removed.** Before the cache, `yahoo_instruments` and `yahoo_prices` each called
   `read_source` for the same chart files. In replay that is harmless — both reads
   return the same committed bytes. Under `--refresh` it is not: every chart is
   fetched twice, a minute or so apart, *two fetches of one chart do not return the
   same bytes*, and the second fetch is the one left on disk.

   **What "halves of one response" means, and why the line between them is real.**
   One Yahoo chart response carries two different kinds of thing:

   | half | fields | what it describes | lands in |
   |---|---|---|---|
   | `meta` | `currency`, `gmtoffset`, `regularMarketTime`, `currentTradingPeriod` | what the Instrument **is**, and when its exchange trades — one row per Instrument, changes almost never | `dim_instrument`, Sub-step **2.2** |
   | `timestamp` + `indicators` | epoch stamps and closes | what the market **did** — one row per bar, append-only | `fct_instrument_price`, Sub-step **2.3** |

   The objection this note answers is a fair one. It is **one file**, fetched once,
   so loading its two halves in two Sub-steps can look like paperwork — a way of
   getting two commits out of one download to satisfy *"one Sub-step = one
   commit"*. If that were all it was, the honest thing would be to load both at
   once and take one commit.

   **First reason it is not: the split follows a line the schema had already
   drawn.** The two halves are a dimension and a fact — identity against
   observations, one row against thousands, slowly-changing against append-only.
   That is not a categorisation invented for Yahoo's response; it is the shape
   `schema.sql` has had since Sub-step 2.1, and the foreign key from
   `fct_instrument_price` to `dim_instrument` means the engine *enforces* which
   half loads first. A single combined loader would still have to build both
   tables, in that order, from those two field groups. It would be this split with
   the line rubbed out, not a simpler design.

   **Second reason, and the one the cache proves: something has to be guaranteed
   across the line.** `read_source(name, url)` does not promise "some bytes for
   this source". It promises **the** bytes this run used for this source — the same
   ones sitting on disk when the run ends. With a single reader that promise is
   free and invisible, because there is nothing for the bytes to be inconsistent
   *with*. The moment a second table is built from the same file, that promise
   becomes the only thing making `dim_instrument` and `fct_instrument_price` two
   views of **one observation** rather than two observations that happen to share a
   filename. A boundary that needs a guarantee to hold across it is an interface —
   which is CLAUDE.md's own test for a seam, applied to a line I had drawn in 2.2
   without noticing it was one.

   **The failure, concretely.** A `--refresh` at 14:32:00, while London is open.
   `VOD.L`'s `meta` says the regular session ends at 16:30 and the last trade seen
   was 14:31:58 — so the response was taken mid-session and its final bar is a live
   price, not a close. `raw.yahoo_instrument` is built from that. Sixty seconds
   later `yahoo_prices` fetches the same chart again: the final bar now carries a
   different number, `regularMarketTime` reads 14:32:57, and *this* response
   overwrites the snapshot. The Warehouse that run produced is then a mix — the
   in-progress rule evaluated against the first response's clock, on bars taken
   from the second.

   **What that costs, split into what a check sees and what it does not.** An
   earlier draft of this note said every check would still have passed. That was
   too strong, and the accurate version is the more useful one:

   - **Caught, if `--sources` is run after the refresh.** It re-derives every price
     from the file on disk — the *second* response — so when two fetches straddle
     the closing bell they disagree about whether the final bar is a close, and the
     check reports a missing or unexpected row. That is the same signal the third
     mutation in the table above produced.
   - **Not caught, ever.** In the ordinary case the two responses agree about the
     session, no row differs, and the run looks clean while its Warehouse was built
     from bytes that are no longer on disk. ADR-0004's promise — *"`--refresh` is
     the sole mode that needs a network, and it rewrites the snapshot with the same
     bytes the run used"* — is then false for that run, silently, in the one mode
     nobody re-runs to verify.

   The cache is a dictionary lookup, and it makes that promise true by
   construction rather than by timing. **It is also the change I am least confident
   in, precisely because the failure it prevents is the one path I did not run.**

2. **`market_price` stores Yahoo's float32 artifacts, and I chose that
   deliberately.** One example carries the whole decision.

   **The example.** AAPL's close on 2024-08-08. The bytes in
   `data/snapshots/ingestion/yahoo-chart-AAPL.json` read `213.30999755859375`.
   Yahoo serialises single-precision floats and `213.31` has no exact
   single-precision representation, so that string is as close as this source can
   get to the number the exchange printed. Cast to `DECIMAL(18, 6)` it becomes
   **`213.309998`**, which is what `fct_instrument_price` holds. The alternative is
   to store **`213.31`** — the number Yahoo meant — by rounding on the way in.

   **What the difference is worth, on a Position.** A client holding 1,000 AAPL
   shares is marked at:

   | stored as | the Position is marked at |
   |---|---|
   | `213.309998` | $213,309.998 |
   | `213.31` | $213,310.000 |
   | **difference** | **$0.002** |

   Two-tenths of a cent on a Position worth over two hundred thousand dollars, and
   an answer rendered to the cent shows the same figure either way.

   **Now the same 1,000 shares against the errors this file's transforms exist to
   remove.** `VOD.L`'s last stored close is `1.205000`, because the snapshot's bar
   reads `120.5` and the London listing quotes in **pence**. Divided down, the
   holding is marked at **£1,205.00**. Carried across undivided, it is marked at
   **£120,500.00** — a hundred times too much, and nothing about the number looks
   wrong on its face. And a bar read on the wrong clock marks the Position at a
   price from a day it was not held.

   That comparison is what settled it. The artifact I am accepting moves a mark by
   two-tenths of a cent; the mistakes the three transforms remove move it by a
   **factor of a hundred**, or by a whole day. Rounding the first away is not a
   step towards catching the second.

   **So why not round anyway, since it is one `round()`?** Two specific reasons.

   - **The three transforms make a number *correct*; rounding makes it *tidy*.** A
     pence quote stored as pounds is wrong. A bar booked a day early is wrong. A
     mid-session tick stored as a close is wrong. `213.309998` is not wrong — it is
     the number the source published, carried to more digits than the source means.
     That is a presentation concern, and the presentation layer can round at any
     time without asking anyone. The Warehouse cannot un-round.
   - **Rounding would make stored precision depend on a source field.** The right
     number of digits is not simply two: Yahoo's `meta.priceHint` reads **2** for
     `AAPL` and **4** for `EURUSD=X`, and rounding a currency pair to two decimals
     destroys real information. So the build would have to join `priceHint` and
     round per Instrument — and a later `--refresh` returning a different hint for
     the same Instrument would quietly change the precision of a stored column with
     nothing failing. The snapshots exist so the Warehouse is a function of
     committed bytes; this would make it a function of committed bytes *plus*
     whatever Yahoo currently thinks it means.

   **What would change my mind:** if `market_price` is ever rendered to a user
   verbatim, `213.309998` is a defect in a Grounded Answer — and the fix belongs at
   the presentation layer rather than here. If you would rather have it on the way
   in regardless, it is one join and one `round()` in
   `veritas/warehouse/builds/fct_instrument_price.sql` plus the same rule in
   `expected_prices()`, and `PRICE_TOLERANCE` stays as it is.
3. **The 1.5 split threshold is a judgement between two measurements, not a
   standard.** The smallest split anyone performs is 2:1; the largest single-day
   move in the loaded window is 1.196. Anything in between works today. It is set
   at 1.5 rather than 1.9 because a `--refresh` pulling a window containing a real
   40% earnings collapse should not be silently accepted as normal, and rather than
   1.3 because a check that cries wolf gets deleted. **This is the assertion most
   likely to fire on a future refresh**, and when it does the fix is a symbol swap
   in `universe.py`, not a raised threshold.
4. **The in-progress rule trusts `meta.currentTradingPeriod`.** If a future
   response omitted it, `current_session_end` would be NULL, the `NOT (...)` clause
   would evaluate to NULL, and **every row for that Instrument would vanish**. That
   fails loudly rather than silently — `uv run python -m veritas.ingestion` asserts
   all nineteen Instruments are priced and exits 1 — but the diagnosis it prints
   would point at coverage rather than at the real cause. I left it rather than add
   a `coalesce`, because a default here means guessing whether a session had closed,
   and guessing that is how a mid-session price becomes a close.
5. **Nine thousand prices and no way to check one against a second source.**
   Everything above verifies that the Warehouse faithfully carries what Yahoo said.
   Nothing verifies that Yahoo is right. That is [DEBT-003](../debt-ledger.md)'s
   territory — no key-free second Market Price source exists — and it is worth
   stating plainly now that the Warehouse holds prices rather than leaving it
   implied.

**Language**

No new terms, and none proposed. Every identifier added resolves to a registered
term: `Market Price` (`fct_instrument_price.market_price`, `price_date`),
`Instrument Symbol`, `Quotation Currency`, `Adjusted Close` — which appears only
in the check that proves it was *not* loaded, which is the one use the Glossary's
anti-pattern row permits.

Three raw field names are the source's data under our names, and none of them is a
domain term: `bar_timestamp`, `unadjusted_close`, `utc_offset_seconds`. The last
is deliberately not Yahoo's spelling (`gmtoffset`): the offset is from Coordinated
Universal Time, which is what the timestamps are in and what the Glossary's
abbreviation table already covers. `unadjusted_close` is named for the trap — a
reader of `raw` can see which of the two series was landed without opening the
source.

---

### Changes made on review — 2026-08-11

Amino reviewed Sub-step 2.3 and approved it, in two passes on the same day: two
rulings and two rewrites first, then a widening of the second ruling and the
approval of one Term Proposal. Everything is applied below. **No verification
output above changed**, because nothing that executes was altered — only comment
and document text — and the commands were re-run to prove exactly that.

1. **[ADR-0004](../adr/0004-snapshot-and-replay-and-where-dlt-stops.md) is
   `accepted`** — [R17](../plan/step-002-warehouse-and-ingestion.md#r17--adr-0004-is-accepted--approved-by-amino-2026-08-11).
   Current State had flagged the stale `proposed` status rather than flipping it;
   Amino settled it. The status line, the [ADR index](../adr/README.md) and Current
   State now agree. Nothing in the ADR's Decision or Consequences changed.

2. **A measurement is dated evidence, and lives in a review** —
   [R18](../plan/step-002-warehouse-and-ingestion.md#r18--a-measurement-is-dated-evidence-and-lives-in-a-review--approved-by-amino-2026-08-11),
   raised against `fct_instrument_price.sql`'s *"300 of the 521 bars in each
   currency pair's snapshot fall on a different date under the two readings"* and
   then **widened by Amino the same day** to every figure a later run could refute
   or resize, in any file. The rule is now a
   [writing convention in CLAUDE.md](../../../CLAUDE.md#writing-conventions):
   such a figure is written as evidence — *what was measured, when, under what
   settings, and the command that reproduces it* — kept in the Step Review that
   produced it, with code, the Glossary and ADRs **referring** to it rather than
   restating the number.

   **First sweep — ten comments across five files**, the run-contingent ones:

   | File | Was | Now |
   |---|---|---|
   | `veritas/warehouse/builds/fct_instrument_price.sql` | *"300 of the 521 bars in each currency pair's snapshot"* | points at `--sources`, which prints the figure for whatever window is loaded |
   | `veritas/warehouse/builds/fct_instrument_price.sql` | *"Eleven of the nineteen snapshots currently carry such a bar"* | *"whether a given snapshot carries such a bar depends on the minute it was fetched"* |
   | `.claude/scripts/check_warehouse.py` | the `SPLIT_RATIO` rationale quoting *"1.196 — crude oil futures into 2026-04-08"* | the rationale, with the headroom printed on every run instead |
   | `veritas/ingestion/sources.py` | *"three of the sixteen traded Instruments"* — **already wrong**, the universe has been nineteen since 2.2 | no count; the reason NYSE listings need the second file |
   | `veritas/ingestion/sources.py` | *"two of the traded exchange-traded funds are absent"*; *"every one of the nine-thousand-odd price rows"*; a `File Creation Time:` line carrying one fetch's timestamp | the same points without the counts |
   | `veritas/ingestion/snapshots.py` | *"rewrites nineteen files… dies at the fourteenth… thirteen new and six old"*; *"would fetch all nineteen charts twice"* | *"one file at a time… some fresh files and some stale ones"*; *"every chart twice"* |
   | `veritas/ingestion/__main__.py` | *"nine thousand price rows covering eighteen of nineteen Instruments"* | *"a large pile of price rows covering every Instrument but one"* |

   The `sources.py` row is the argument for the rule in miniature: that comment was
   already false, had been since the universe grew from sixteen to nineteen
   Instruments in 2.2, and nothing failed — no checker reads comments.

   **Second sweep — the three places a measurement was standing in for evidence.**
   The first pass had flagged one of these and left it for a ruling; the widened
   rule settles all three, and a sweep of every remaining figure in `veritas/`,
   `.claude/scripts/` and the Glossary found no others.

   | File | Was | Now |
   |---|---|---|
   | `veritas/warehouse/schema.sql` | Adjusted Close *"differs from the close on 95.5% of AAPL's last 1,255 daily bars"* | *"differs from the close on nearly every bar of a real price series"*, then the command that measures it and the review that holds the dated evidence |
   | `.claude/docs/glossary.md` — the `Adjusted Close` / `Market Price` Section C row | *"the two differ on **95.5%** of AAPL's last 1,255 daily bars"* | the same claim as **evidence**: 1,198 of 1,255, on a five-year daily AAPL request, checked 2026-08-03, reproducible offline with the command, and linked to the Step 001 review's table |
   | `veritas/ingestion/sources.py` | *"roughly five hundred trading days per Instrument"* | the window without the count — it was an estimate of a measurement, which is the weakest form of both |

   The Adjusted Close figure is the case that shows what the rule buys, because it
   is the **best-supported number in the project** and it was still being copied
   around as a bare fact. It reproduces exactly, offline, from a committed script:

   ```
   $ uv run python .claude/scripts/check_data_availability.py
     [source probes and the join spike elided — the command prints all of it]

     == wrong-number traps ==

     Adjusted Close vs Market Price : differ on 1198/1255 bars (95.5%)
     Quotation Currency (VOD.L)     : GBp — normalised to GBP on load

     [join spike elided]

   PASS — every source is obtainable and every distinction separates
   exit: 0
   ```

   Two lines of that output are the whole point. The figure is *not* wrong today —
   it is right, and reproducible, and it was still the wrong thing to write into
   `schema.sql`, because the file gives a reader no way to tell whether it was
   measured yesterday or asserted from memory two years ago. Dated evidence with a
   command answers that question; a number in a comment cannot.

   Figures fixed by the code around them were left alone, and are definitions
   rather than measurements: the two-year range, the factor of 100 between pence
   and pounds, `2:1` as the smallest split anyone performs.

   **Nothing enforces R18, and that is not a new Ledger entry.** A checker cannot
   reliably tell a measurement from a definition inside a comment, so this rule is
   discipline — exactly the class
   [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)
   already holds open: *"Nothing mechanical stops any of it being skipped"*, with
   *"judgement-dependent rules"* named there as the part hooks cannot cover.
   Opening a second entry for the same gap would inflate the open-debt count
   without adding a trigger.

3. **Sceptical point 1 now explains the seam from the beginning** rather than
   asserting it in one clause. It says what the two halves of a chart response are
   (a table), states the objection it is answering, and gives two reasons the line
   is real: the split follows the dimension/fact line `schema.sql` already draws
   and the foreign key already enforces, and a guarantee has to hold across it —
   `read_source` promising *the* bytes this run used, not *some* bytes.
   **One claim was corrected while rewriting it**, and it mattered enough to be
   worth naming: the old text said every check would still have passed under the
   double fetch. It would not. `--sources` re-derives prices from the file on disk,
   so two fetches straddling the closing bell disagree about the final bar and the
   check catches it. What no check can see is the ordinary case — a Warehouse built
   from bytes that are no longer on disk, which is ADR-0004's promise broken
   silently.

4. **Sceptical point 2 is now built on one worked example** instead of a relative
   error. AAPL on 2024-08-08: `213.30999755859375` in the snapshot bytes,
   `213.309998` stored, `213.31` meant — worth **$0.002** on a 1,000-share
   Position, against the same holding of `VOD.L` marked at £120,500.00 instead of
   £1,205.00 when the pence division is skipped. It also replaces the old reason
   for not rounding, which was wrong: rounding would *not* have cost the check its
   exactness, since `expected_prices()` re-implements every other transform
   already. The two reasons that survive scrutiny are that the three transforms fix
   numbers that are *wrong* while rounding fixes one that is merely untidy, and
   that rounding correctly needs `meta.priceHint` — 2 for `AAPL`, 4 for
   `EURUSD=X` — which would make a stored column's precision depend on a source
   field that a later refresh can change with nothing failing.

5. **`NYSE` is registered — approved by Amino 2026-08-11.** It is a row in the
   Glossary's [Abbreviations table](../glossary.md#abbreviations), beside `LSE` and
   `SEC`, expanding to **New York Stock Exchange**. It is shorthand rather than
   Domain Language — the Abbreviations table says so of itself: *"These are **not**
   Domain Language terms — they are shorthand"* — so it carries no definition and
   no status, and no Section C row was needed. It reached a document only because
   R18 moved the reasoning about NASDAQ Trader's second file out of a code comment
   and into this review; the failing checker is quoted under *Verification* below.

**Verification after the change**

Comment and document text only, so the point of re-running is to show that nothing
moved:

```
$ uv run python -m veritas.ingestion
  mode: replay (offline)
  snapshots: data/snapshots/ingestion
  universe: 19 Instruments
  removed data/veritas.duckdb — rebuilding

    dim_account                   0 rows
    dim_client                    0 rows
  · dim_instrument               19 rows
    fct_accounting_movement       0 rows
    fct_balance_snapshot          0 rows
    fct_cash_movement             0 rows
    fct_fx_rate                   0 rows
  · fct_instrument_price       9549 rows
    fct_position_snapshot         0 rows
    fct_trade                     0 rows

PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9549 Market Prices across all 19
exit: 0
```

```
$ uv run python .claude/scripts/check_warehouse.py --sources
  [unchanged from the run recorded above — same 9549 rows, same three
   counterfactual measurements, same 1.196 largest ratio, same seam scan]

PASS — the star schema matches Glossary Section B and the adapter seam holds
exit: 0
```

```
$ uv run python .claude/scripts/check_language.py
  glossary: 88 registered terms
  proposed terms: 0 · python files scanned: 12 · identifiers: 437
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

**It failed first, and the failure is worth keeping:** *"'NYSE' is used in the
documents but is neither in the Glossary's Abbreviations table nor in the exempt
list"*. Moving the NYSE reasoning out of a code comment and into this review put
the abbreviation into a document for the first time, where the checker reads it —
code docstrings are scanned for identifiers, not prose. Registering it (item 5
above) is why the two counts here are 88 and 24 against the 87 and 23 of the run
recorded earlier in this Sub-step.

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       652 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr         1037 words
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
```
