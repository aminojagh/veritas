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

---

## Sub-step 2.4 — Load `fct_fx_rate` from Frankfurter

**What changed**

The real half of Ingestion is complete. `fct_fx_rate` holds **11,840 FX Rates** —
every ordered pair of the four currencies the traded universe is quoted in, on
every calendar date from 2024-08-01 to 2026-08-10 — and **every Market Price in the
Warehouse now has a rate on its own date**, which is the property that turns
nineteen Instruments priced in four currencies into a book that can be totalled.

Five things.

- **`veritas/warehouse/builds/fct_fx_rate.sql`** — the third build script, and where
  all three of this Sub-step's transforms live: the base currency gets the row
  against itself that the response omits, non-publishing dates are filled forward,
  and every ordered pair is derived from the two rates against the base.
- **`veritas/ingestion/sources.py`** — `frankfurter_rates` reads one response
  covering the whole window. `PRICE_WINDOW_YEARS` is now the single number both
  sources take their window from; Yahoo takes it as a relative range and
  Frankfurter as two explicit dates, and writing it once is what stops the two
  windows drifting apart across refreshes.
- **`veritas/ingestion/__main__.py`** — one entry in `FETCHED_TABLES`, one in
  `BUILDS`, exactly as ADR-0004 said a source would cost. Plus a new failure the
  pipeline refuses to complete on: a Market Price with no FX Rate on its own date.
- **`.claude/scripts/check_warehouse.py --sources`** — a `check_fx_rates` function
  that re-derives every rate from the committed snapshot **in Python** and compares
  it to what the SQL built, on the same pattern `check_prices` established in 2.3.
- **A `--refresh` was run, twice, deliberately.** This is the gap Sub-step 2.3
  handed over, and closing it is why several of 2.3's numbers have moved. See
  *The refresh, and what it cost*.

**`check_language.py` failed first, and the fix was a root cause rather than two
words.** It reported `'ASOF' is used in the documents but is neither in the
Glossary's Abbreviations table nor in the exempt list`, and the same for `CASE`.
Neither is an abbreviation; both are SQL keywords. The script already had a group
for those, carrying a comment that it was *"derived, not remembered ... a list that
is always one document behind"* and an instruction to re-derive it from
`schema.sql` by hand after a schema change. Sub-step 2.4 is precisely the failure
that design predicts: the build scripts are hand-authored SQL too, and `ASOF JOIN`
appears in none of `schema.sql`. Adding the two words would have left the next
Sub-step to find the third. The literal group is now a function,
`warehouse_sql_keywords()`, which reads **every** `.sql` file under
`veritas/warehouse/` — with `--` comments stripped, because they are prose that
mentions ECB and UTC, and with quoted literals stripped, because those are the
domain values the CHECK constraints name and this function has no business
exempting registered vocabulary from the scan. The twenty keywords it derives were
removed from the literal; the eight that remain are the vocabulary of query
languages the ADRs *rejected*, which no file here contains.

**The design decision worth arguing about: all ordered pairs, not just the EUR
ones.** The European Central Bank (ECB) publishes rates against the euro, so
Frankfurter's response gives three numbers per date for a four-currency universe.
The table stores sixteen: every ordered pair including each currency against
itself. It costs four times the rows — 11,840, against the 2,960 that four
currencies on 740 dates would need if only the euro side were stored — and buys one
thing: a conversion in any future Metric Definition is a single lookup rather than
a division of two lookups. This project's subject is quietly wrong numbers, and a
division repeated in every metric is exactly where one appears in one of them and
nowhere else. The division is written once, here, where a check re-derives it.

The pair where both sides are the same currency falls out as exactly 1 from the
same arithmetic as every other pair rather than from a `CASE`, which is why the
base gets a row against itself first.

**A question about the Glossary, not a term proposal.** `FX Rate` is registered as
*"Real ECB reference rate between two currencies on a date."* Twelve of the sixteen
pairs are real ECB reference rates in that sense. The other four — the pairs
between two non-euro currencies, `GBP->JPY` and its like — are a **ratio of two**
published reference rates, which is what Frankfurter itself would return under
`base=GBP` and what any FX desk would call the rate, but is not literally a number
the ECB published. The definition can be read as covering it or not. If it should
not, the fix is one `WHERE` clause in the final `SELECT` and the metrics do the
division instead. **Flagged rather than decided**, because Non-Negotiable #1 makes
this Amino's call and not mine.

> **Answered 2026-08-11 —
> [R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11).**
> The four derived pairs stay, and the Glossary row was amended to say so in its
> own words rather than left readable both ways. The `WHERE` clause was not
> written; nothing that executes changed. See
> [Changes made on review — 2026-08-11 (Sub-step 2.4)](#changes-made-on-review--2026-08-11-sub-step-24).

**No new term was needed, and that was deliberate.** The set of currencies this
table must cover was going to be a constant called something like
`CONVERTIBLE_CURRENCIES` — a domain noun the Glossary does not register. It is
instead read from `dim_instrument.quotation_currency` in SQL, unioned with the
currency the source publishes against. That removes the term, and it means adding
an Instrument in a new currency widens this table by itself instead of requiring
someone to remember a second list.

### The refresh, and what it cost

Sub-step 2.3 recorded, under *Deliberately left undone*: *"`--refresh` was not run,
so the caching change to `read_source` is verified by reading rather than by
execution ... Sub-step 2.4 adds Frankfurter and is the natural place to run a
refresh once, deliberately."* It was, on 2026-08-11. Frankfurter had no snapshot at
all, so this Sub-step had to open a socket regardless.

**The cache claim is now checked rather than argued.** `--refresh` prints how many
snapshots it rewrote and how many were distinct, and fails the run if any name
appears twice — two resources share each Yahoo chart, so without the cache all
nineteen would be fetched twice, a minute apart, and only the second fetch would be
on disk. It reports `rewrote 23 snapshot(s), 23 distinct`.

**And it moved 2.3's numbers, which is the point of R18 arriving one Sub-step
early.** Every figure below is from the same source read a day later:

| | 2.3, on 2026-08-10 | 2.4, on 2026-08-11 |
|---|---|---|
| `fct_instrument_price` rows | 9,549 | 9,554 |
| price window | 2024-08-08 to 2026-08-10 | 2024-08-12 to 2026-08-10 |
| dates with a price for at least one Instrument | 521 | 519 |
| dates with a price for all nineteen | 452 | 453 |
| Adjusted Close would change | 5,416 (57%) | 5,466 (57%) |
| a UTC date would change | 1,075 (11%) | 1,081 (11%) |
| pence as pounds would change | 1,006 (11%) | 1,008 (11%) |

Yahoo's `2y` is relative to the moment it is asked, so the window slid forward a
day and dropped four at the front. **The 2.3 review's figures are not corrected**:
they were true on 2026-08-10, they say so, and they carry the command that produced
them. That is what a dated measurement is for. What did need correcting is every
place that quoted them as standing facts — `current-state.md` in four places.

The one figure that did **not** move is `1.196`, the largest day-over-day ratio,
still `CL=F` into 2026-04-08 against the 1.5 threshold. EXT-007's assumption
survives a refresh.

**Verification**

```
$ uv run python -m veritas.ingestion --refresh
  mode: refresh (live)
  snapshots: data/snapshots/ingestion
  universe: 19 Instruments
  removed data/veritas.duckdb — rebuilding
  rewrote 23 snapshot(s), 23 distinct

    [row listing as below]

PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9554 Market Prices across all 19 · fct_fx_rate holds 11840 FX Rates and every Market Price has one
exit: 0
```

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
  · fct_fx_rate               11840 rows
  · fct_instrument_price       9554 rows
    fct_position_snapshot         0 rows
    fct_trade                     0 rows

PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9554 Market Prices across all 19 · fct_fx_rate holds 11840 FX Rates and every Market Price has one
exit: 0
```

```
$ uv run python .claude/scripts/check_warehouse.py --sources
  [the schema listing, dim_instrument block and constraint probe are unchanged in
   shape from the runs above. The one new table:
       fct_fx_rate  —  4 columns, 11840 rows
           rate_date                DATE
           from_currency            VARCHAR
           to_currency              VARCHAR
           fx_rate                  DECIMAL(18,8)  ]

  fct_instrument_price: 9554 rows · 19 Instruments · 519 distinct dates (2024-08-12 to 2026-08-10)
    values: all 9554 rows equal the snapshot's unadjusted close, on the exchange's own date, in the major unit
    if it takes indicators.adjclose instead of indicators.quote:
      5466/9554 rows change (57%), across 12 of 19 Instruments
    if it reads a bar's timestamp as a Coordinated Universal Time (UTC) date rather than shifting it onto the exchange's clock:
      1081/9554 rows change (11%), across 6 of 19 Instruments
    if it skips the division by minor_units_per_major:
      1008/9554 rows change (11%), across 2 of 19 Instruments
    corporate actions: largest day-over-day ratio is 1.196 (CL=F into 2026-04-08), against a 1.5 threshold
    calendars: 519 dates have a price for at least one Instrument · 453 have one for all 19 (Sub-step 2.5 chooses between them)

  fct_fx_rate: 11840 rows · 4 currencies (EUR GBP JPY USD) · 740 dates (2024-08-01 to 2026-08-10)
    values: all 11840 rows equal the rate the ECB's published quotes imply · 516 of 740 dates were published on, the rest filled forward
    if it stores only the dates the ECB published on, instead of filling a rate forward across weekends and ECB holidays:
      3584/11840 rows change (30%), across 4 of 4 currencies
    if it reads a published rate as euros per unit of currency rather than currency per euro:
      8880/11840 rows change (75%), across 4 of 4 currencies
    coverage: every Market Price (2024-08-12 to 2026-08-10) has a rate in its own Quotation Currency on its own date
    round trip: worst drift over 16 ordered pairs is 0.0000010841597042 (JPY to GBP and back), against a 0.00005 tolerance

  seam scan: 12 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
exit: 0
```

**224 of the 740 dates were never published on** — weekends and ECB holidays — and
carry the most recent rate at or before them, which is the Glossary's own sentence
for `FX Rate` stored rather than left for each future metric to re-derive.

```
$ uv run python .claude/scripts/check_language.py
  glossary: 88 registered terms
  proposed terms: 0 · python files scanned: 12 · identifiers: 490
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

No term was registered in this Sub-step, which is why the Glossary count is
unchanged at 88 against 2.3's run. The exempt count is also unchanged at 15 — the
twenty SQL keywords moved out of a literal and into a derived set, which is a
different group.

```
$ uv run python .claude/scripts/verify_framework.py
  [five skills, interpreter 3.14.4]

PASS — framework is wired up correctly
```

**The check was made to fail three times before being trusted**, by mutating the
build script and re-running the pipeline and the check unchanged. Each names the
specific mistake:

| Mutation to `fct_fx_rate.sql` | What was reported |
|---|---|
| `ASOF JOIN` → an equality join — no fill-forward | Pipeline exits 1: `99 of 9554 Market Prices have no FX Rate on their own date`. `--sources`: `3584 missing`, and the table falls from 740 dates to 516 |
| `quote / base` → `base / quote` — every rate upside down | `0 missing · 0 unexpected · 8880 wrong`, first offender named: `EUR->GBP on 2024-08-01 at 1.18584575, but the published rates imply 0.84328` |
| Window ends 3 days before the last published rate — the ECB lagging Yahoo | Pipeline exits 1 at 19 unconvertible prices; `--sources` reports the missing rows *and* the coverage failure broken down by currency |

The counterfactual lines move in the opposite direction under each mutation — with
the fill-forward removed, *"if it stores only the dates the ECB published on"* falls
from 3,584 rows to 0, and the check reports that as its own problem, because a
counterfactual that changes nothing means the assertion above it cannot fail. The
build script was restored byte-for-byte (`cmp` clean) and every command re-run.

**Determinism.** Two consecutive replay runs produce byte-identical output,
including every row count.

**Deliberately left undone**

- **The round-trip check catches an asymmetric inversion, not a symmetric one.**
  Mutation 2 inverted *every* pair, so `A->B × B->A` was still 1 and the round trip
  passed while 8,880 rows were wrong. That is not a hole — assertion 1 caught it
  immediately and names the first offender — but it is worth being precise about
  what each assertion buys. The round trip is there for the case assertion 1 cannot
  see: a build that agrees with the re-derivation because both are wrong the same
  way. It is the only check here that needs no second source and no second
  implementation.
- **Nothing yet constrains 2.5's Denomination Currencies to this set.** The
  currencies come from `dim_instrument.quotation_currency`, and a Trade's
  Commission, Fee and Rebate are held in its Denomination Currency, which the
  Glossary is explicit *"a broker does not necessarily charge in the currency an
  Instrument is quoted in"*. If 2.5 bills an Account in a currency no Instrument is
  quoted in, `fct_fx_rate` will hold no rate for it and Gross Revenue cannot reach
  a Reporting Currency. **Not filed as debt** — the code is right for a Warehouse
  with no Trades in it, and the trigger cannot fire until 2.5 writes one. It is
  recorded as a 2.5 precondition in `current-state.md`, and the natural place for
  the assertion is beside the existing coverage one, once there is a row to assert
  against.
- **No index beyond the primary key.** 11,840 rows.

**Look at this sceptically**

1. **The build reads two tables built before it, which no foreign key enforces.**
   `fct_fx_rate` declares no foreign key — it is keyed on `(rate_date,
   from_currency, to_currency)` and references nothing — yet its build takes the
   currency set from `dim_instrument` and the end of its window from
   `fct_instrument_price`. Put it first in `BUILDS` and it produces a table with no
   currencies and an empty window, silently. The engine cannot refuse that the way
   it refuses an orphan `instrument_id`.

   The alternative is a constant: a list of currencies and a pair of dates,
   maintained beside the traded universe. That is worse in the specific way this
   project cares about — it is correct on the day it is written and silently wrong
   after the next `--refresh`, which is precisely the failure that just moved every
   number in the table above. Deriving both from the data means the widening
   happens by itself. The ordering risk is real and is mitigated by comment in
   `BUILDS` rather than by structure; making it structural would mean build scripts
   declaring dependencies, which is a mechanism this Warehouse does not have and
   does not yet need for three files.

2. **`ASOF JOIN` and `generate_series` are the second and third DuckDB-specific
   constructs in `builds/`**, after `make_timestamp` in 2.3.
   [DEBT-009](../debt-ledger.md) is the entry that records the seam scan cannot see
   them — it checks `duckdb` *imports*, not dialect names. Its trigger is *"the
   first component outside the adapter emits SQL"* and it still has not fired: all
   three build scripts sit inside `veritas/warehouse/builds/`. But the surface it
   would have to scan for has now tripled in one Sub-step, which is worth knowing
   before the Semantic Layer starts rendering SQL.

3. **The `1.0` for the base currency's row against itself is a literal in the SQL.**
   Every other number in this pipeline comes from a source or from a map landed in
   `raw`. This one is arithmetic: one euro is one euro. It is not a factor anyone
   could tune and it is not a measurement, so it does not belong in `universe.py`
   beside `minor_units_per_major` — but it is the one hardcoded value in the file
   and it should be seen rather than skimmed past.

**What this hands Sub-step 2.5**

- **Every Section C conversion now has real rates behind it.** A Trade on any date
  in the window converts from its Denomination Currency, a Position marks at a
  Market Price and converts from its Quotation Currency, and Trade Date against
  Settlement Date selects a *different* rate — which is the second half of what the
  Glossary says that distinction moves. [DEBT-004](../debt-ledger.md) measured that
  effect at 0.08% on the spike's data and is still open against the Gold Question
  Set; the data to re-measure it on the full window now exists.
- **The FX window starts eleven days before the price window and ends on the same
  day**, so a Trade near the end of the window whose Settlement Date is T+2 will
  reach past the last rate. 2.5 either keeps its Trades clear of the last two days
  or the window is widened. The coverage assertion only checks Market Prices, so
  this one would not be caught today.
- **The calendar question from 2.3 is unchanged and still 2.5's**: 519 dates carry
  a price for at least one Instrument, 453 for all nineteen.

### Changes made on review — 2026-08-11 (Sub-step 2.4)

Amino reviewed Sub-step 2.4, approved it, and ruled on the one open question. The
implementation was approved unchanged: **no SQL, no Python and no check was
altered**, so every verification output above still stands and the commands were
re-run to prove exactly that.

1. **An FX Rate includes the derived cross-rate** —
   [R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11).
   The question raised above was whether the four pairs between two non-euro
   currencies belong in a table whose term reads *"Real ECB reference rate between
   two currencies on a date"*. Amino's answer: **they stay, and the definition is
   widened to say so** rather than left to be read either way. The `WHERE` clause
   the question had costed at one line was not written, and `fct_fx_rate` still
   holds all sixteen ordered pairs.

   The amended Glossary row separates the two cases in its own words — a euro-side
   pair *is* a published reference rate, a non-euro pair is *"the ratio of that
   date's two published rates ... which is what Frankfurter itself returns under a
   non-euro base"* — and keeps the exclusivity that naming the ECB was always for:
   *"a rate of any other origin is not one"*. Amending an `agreed` term is a ruling
   rather than an edit, which is why R19 exists.

2. **Two documents that restated the old wording were brought with it.**
   `schema.sql`'s header over `fct_fx_rate` said only *"the ECB reference rate from
   Frankfurter, and only from Frankfurter"*, which is the sentence the question was
   about; it now states the euro-side/cross-rate split and points at the Glossary
   row for the definition. `data-availability.md` cited the term as *"the ECB
   reference rate from Frankfurter"* — a paraphrase in quotation marks, which the
   citations-quote rule forbids — and now quotes the words the claim actually rests
   on, *"sourced from the public Frankfurter API"* and *"a rate of any other origin
   is not one"*. Both edits are comment and prose only.

3. **`verify_framework.py` now checks anchors, not just files** —
   [R20](../plan/step-002-warehouse-and-ingestion.md#r20--verify_frameworkpy-checks-anchors-not-just-files--approved-by-amino-2026-08-11).
   Not part of the review; found while writing item 1. Confirming that the two new
   links above resolved meant checking them by hand, because `check_links` split
   every link on `#` and validated only the path — and same-document `#anchor`
   links it skipped entirely. A dead anchor lands the reader at the top of the
   right document, so it reads as a vague citation rather than a broken one.

   Amino approved closing the gap in this Sub-step. The check now reports a `dead
   anchor` separately from a `dead link`, and the throwaway script that found the
   gap was **not** committed — `verify_framework.py` was the existing check that
   should have done this, which is the rule in CLAUDE.md about looking there first.
   That throwaway also got the slug rule wrong twice, and both mistakes are now
   comments in `heading_anchors`: underscores are kept (`fct_fx_rate`, not
   `fctfxrate`) and a `#` line inside a fenced block is not a heading.

**Verification after the change**

Re-run because the Glossary is an input to two of these checks: `check_language.py`
reads every registered term, and `check_warehouse.py` reads the table set out of
Glossary Section B.

```
$ uv run python .claude/scripts/check_language.py
  glossary: 88 registered terms
  proposed terms: 0 · python files scanned: 12 · identifiers: 502
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

The term count is **88, unchanged**: R19 amended a row rather than adding one, and
the abbreviation counts hold because the amended text introduces no new shorthand.
The identifier count rose from the 490 recorded earlier in this Sub-step because
R20 added `heading_anchors` to `verify_framework.py`, which the scanner parses.

```
$ uv run python .claude/scripts/check_warehouse.py --sources
  [unchanged from the run recorded above — same 11,840 FX Rates over the same
   740 dates, same two counterfactual measurements, same coverage and round-trip
   assertions, same 9,554 Market Prices, same seam scan]

PASS — the star schema matches Glossary Section B and the adapter seam holds
```

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
  · fct_fx_rate               11840 rows
  · fct_instrument_price       9554 rows
    fct_position_snapshot         0 rows
    fct_trade                     0 rows

PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9554 Market Prices across all 19 · fct_fx_rate holds 11840 FX Rates and every Market Price has one
```

The rebuild was run offline and rewrote the Warehouse from the committed
snapshots — the edits above touch a comment in `schema.sql`, which is the file the
rebuild executes, so it is the one that has to be re-run rather than reasoned about.

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       652 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr         1037 words
  links      288 links, 128 anchors 22 documents
  python     3.14.4                 /home/amino/Projects/veritas/.claude/worktrees/substep-2-4-fx-rate/.venv/bin/python3

PASS — framework is wired up correctly
exit: 0
```

The `links` line is new, from R20. The interpreter path differs from every run
recorded above because this one was made in the `substep-2-4-fx-rate` worktree
rather than the main checkout — same pinned CPython 3.14.4, same `uv`-managed
environment.

**The anchor check was verified by making it fail.** A check that has only ever
passed is indistinguishable from one that returns `True`, and this one is new. A
temporary `.claude/docs/tmp-negative-control.md` carried four links — one dead
anchor into `glossary.md`, one dead anchor into itself, and one live example of
each:

```
$ uv run python .claude/scripts/verify_framework.py
  links      292 links, 132 anchors 23 documents

FAIL — 2 problem(s)
  - .claude/docs/tmp-negative-control.md: dead anchor -> glossary.md#a-heading-that-does-not-exist
  - .claude/docs/tmp-negative-control.md: dead anchor -> #no-such-heading
exit: 1
```

Both dead anchors were caught, both live ones passed silently, and the same-file
`#no-such-heading` is a link the previous `check_links` did not look at at all. The
control file was then deleted and the run above re-run to confirm the tree is clean;
it is not committed, because a fixture that must be deleted to make the suite pass
belongs in the transcript rather than in the repository.

---

## Sub-step 2.5 — Generate seeded synthetic client activity

**What changed**

The Warehouse is full. All ten tables of Glossary Section B hold rows, the seven
client-activity ones for the first time, and `uv run python -m veritas.ingestion`
builds every one of them from a clean clone with no network. This is the second
half of the `Ingestion` term — *"market data real, client activity synthetic —
never the reverse"* — and the end of Step 002.

Four things.

- **`veritas/ingestion/simulator.py`** — the seeded simulator. Two halves that do
  not touch: `read_market_data` reads the three real star tables through the
  adapter and returns plain Python, and `simulate` is a **pure function** of that
  data and a seed. Every Trade is priced off a Market Price the Warehouse already
  holds, every Position is marked at one, and every conversion goes through a real
  FX Rate. Nothing here re-derives a price from a snapshot, which would have put a
  second implementation of `fct_instrument_price.sql`'s transforms in the
  repository.
- **Seven build scripts in `veritas/warehouse/builds/`** — `dim_client`,
  `dim_account`, `fct_trade`, `fct_cash_movement`, `fct_accounting_movement`,
  `fct_position_snapshot`, `fct_balance_snapshot`. `dim_client.sql` carries the
  reasoning for all seven and the other six point at it.
- **`veritas/ingestion/__main__.py`** — a second phase, and a second dlt load. The
  simulator runs *after* the real tables are built because it reads them, so the
  pipeline is now: land the real sources in `raw`, build three star tables, check
  them, read them, simulate, land the simulated rows in `raw`, build seven more.
  Two new failures the pipeline refuses to complete on: a Position with no Market
  Price on its own Snapshot date, and a monetary amount whose Denomination
  Currency has no FX Rate on its own date — the second being the assertion
  Sub-step 2.4 handed over by name, now that there is a Trade to assert against.
- **`.claude/scripts/check_warehouse.py --distinctions`** — three checks, described
  under *Verification*.

### The decision this Sub-step had to make: which dates a Snapshot is written on

R13 fixed that a Snapshot is written *"on every date the Warehouse holds a Market
Price for"*. Sub-step 2.3 discovered that this reads two ways once the table spans
five exchange calendars, and left the choice here. The two readings, as
`--sources` reports them:

```
$ uv run python .claude/scripts/check_warehouse.py --sources
    calendars: 519 dates have a price for at least one Instrument · 453 have one for all 19 (Sub-step 2.5 chooses between them)
```

**The intersection was chosen: the 453 dates every Instrument has a Market Price
on.** The argument is markability. On a date the union includes and the
intersection does not, some Instrument did not trade, so a Position in it has no
Market Price on that date. There are then only two things a Snapshot can do with
that Position, and both are worse than not writing a Snapshot that day:

- **Mark it at a stale price.** That is a fill-forward, and it would have to be
  re-derived by every future metric that touches Account Value or Unrealised P&L.
  Storing FX Rates densely rather than making each metric fill forward was
  precisely 2.4's decision; making the opposite choice one table over would be
  incoherent.
- **Leave the row out.** Then *"what was held as of D"* answers zero for something
  that was held, which is the wrong-number-with-a-plausible-explanation this whole
  project is about.

**The cost is real and is not hidden.** Sixty-six dates on which some markets
traded carry no Snapshot, so a Position Change across one of them is attributed to
the next Snapshot date. That is the `Snapshot` term's own limitation — *"a Snapshot
cannot see between its own dates"* — rather than a new one, but it is now a
limitation with a size. The choice is load-bearing rather than cosmetic: widening
the calendar to the union stops the pipeline dead (mutation A below).

### The simulator is not a source, and still goes through `raw`

Every star table in this Warehouse is filled by hand-authored SQL in
`veritas/warehouse/builds/`, run through `run_build`. The alternative for the
seven synthetic tables was for the pipeline to insert rows itself, which would
have been less code — the simulator already emits Glossary vocabulary, so these
build scripts translate nothing the way `dim_instrument.sql` translates Yahoo's
`instrumentType`.

It was rejected for three reasons, and the third is the one that decided it:

1. **They are the contract.** The column list in each build is what the simulator
   has to produce, and a column that stopped arriving would fail there rather than
   land a null three tables downstream.
2. **They cast.** dlt infers a wide DECIMAL for every Python `Decimal`; the star
   schema's scale is `DECIMAL(18, 6)`. Mutation D below is that cast being wrong
   by four decimal places, and what catches it.
3. **One writer.** Inserting directly would make the adapter the only door for
   three tables and one of two doors for the other seven, which is the seam
   ADR-0002 exists to keep whole. It would also have fired
   [DEBT-009](../debt-ledger.md)'s trigger — *"the first component outside the
   adapter emits SQL"* — for no gain, exactly as ADR-0004 predicted when it
   rejected the same shape for the real sources.

The cost is a second dlt load in one run. The connections still never overlap:
dlt closes before the adapter opens, the adapter closes before dlt opens again.

### What the re-derivation check proves, and what it does not

`check_prices` and `check_fx_rates` re-derive every row from the committed
snapshots in Python and compare. That is a real test of the SQL, because the
snapshot is an **independent** record of what the source said.

The client side has no such record. The simulator *is* the source, so re-running
it and comparing proves two narrower things, and it is worth being exact about
them because the two checks look identical and are not:

1. **The simulation is deterministic** — the seed is the only thing that decides
   what is in those seven tables.
2. **Nothing was lost or reshaped between the simulator and the star schema** —
   dlt's inference and seven casts sit in between.

It does **not** prove the simulated numbers are right; nothing could, because
there is no outside truth to check them against. What can be checked is that the
data has the shape the design needs, and that is what the Section C figures below
are.

**Verification**

```
$ uv run python -m veritas.ingestion
  mode: replay (offline)
  snapshots: data/snapshots/ingestion
  universe: 19 Instruments
  simulator seed: 20260811
  removed data/veritas.duckdb — rebuilding

  · dim_account                  24 rows
  · dim_client                   12 rows
  · dim_instrument               19 rows
  · fct_accounting_movement    4654 rows
  · fct_balance_snapshot      15402 rows
  · fct_cash_movement          5921 rows
  · fct_fx_rate               11840 rows
  · fct_instrument_price       9554 rows
  · fct_position_snapshot     61907 rows
  · fct_trade                  1670 rows

PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9554 Market Prices across all 19 · fct_fx_rate holds 11840 FX Rates and every Market Price has one
       the client side holds 12 Clients · 24 Accounts · 1670 Trades · every Position is markable and every amount is convertible
```

First run 2026-08-11 and **re-run 2026-08-13 after the review changes below**, both
offline against the snapshots committed in `13b99bb`. Every row count is unchanged
between the two — the transfer fix moves quantities, not rows — and the figures
that did move are listed under
[Changes made on review](#changes-made-on-review--2026-08-13-sub-step-25). Every
figure above is a measurement and moves with a `--refresh`: the price window fixes
the Snapshot calendar, which fixes how many Snapshot rows exist, and Yahoo's range
is relative to the moment it is asked.

```
$ uv run python .claude/scripts/check_warehouse.py --distinctions
  client activity: regenerated from seed 20260811 against 453 Snapshot dates
    dim_client                   12 rows · identical
    dim_account                  24 rows · identical
    fct_trade                  1670 rows · identical
    fct_cash_movement          5921 rows · identical
    fct_accounting_movement    4654 rows · identical
    fct_position_snapshot     61907 rows · identical
    fct_balance_snapshot      15402 rows · identical

    fct_trade                  1670 quantities · 0 not a whole lot
    fct_position_snapshot     61907 quantities · 0 not a whole lot

  Snapshots: 453 dates · every Position has a Market Price on its own date (0 without)
    Position Change / Trade: 3 holdings differ from the sum of their own Trades
      account 3 · instrument 11: holds 61,307, Trades explain 36,063
      account 5 · instrument 4: holds 102, Trades explain 255
      account 11 · instrument 4: holds 293, Trades explain 205

  1670 of 1670 Trades priced and converted to EUR

  Section C — every pair, both numbers
    Gross Revenue / Net Revenue — "reporting gross as net overstates what the business keeps"
      Gross Revenue: 195,260.14 EUR
      Net Revenue: 131,618.93 EUR
      32.59% apart
    Execution Price / Market Price — "Traded Notional at the close values trading that never happened"
      Traded Notional at Execution Price: 262,266,110.69 EUR
      at that date's Market Price: 262,337,407.32 EUR
      0.03% apart
      per Trade: 1670 of 1670 filled away from the close, the largest by 0.60%
      at book level the two nearly cancel — see DEBT-011
    Quotation Currency / Reporting Currency — "skipping the conversion is an FX-sized error"
      converted to EUR: 262,266,110.69 (mixed)
      summed unconverted: 8,312,550,002.72 (mixed)
      96.84% apart

    Trade Date / Settlement Date — "shifts revenue across period boundaries", Gross Revenue in 2025-11
      filtered by Trade Date: 7,324.63 EUR
      filtered by Settlement Date: 5,538.64 EUR
      24.38% apart
      the same row's FX half, over every Trade: 195,260.14 at each Trade Date's rate against 195,180.21 at each Settlement Date's, 0.0409% apart
      DEBT-004: that FX half is measured against the 1% the Ledger wants for a reliable evaluation signal — does not clear it

    Cash Movement / Accounting Movement — "earned on Trade Date and collected on Settlement Date", Commission in 2025-11
      earned (Accounting): 7,324.63 EUR
      collected (Cash): 5,534.85 EUR
      24.44% apart
      25 of 25 months differ by at least 0.5%

    (as of the last Snapshot date, 2026-08-10)
    Cash Balance / Account Value — "a Client with no cash and 2m of equities has a Cash Balance of zero"
      Cash Balance: 68,302,991.96 EUR
      Account Value (cash plus Positions marked): 114,714,721.82 EUR
      40.46% apart
    Realised P&L / Unrealised P&L — "one is banked, one is a market opinion"
      Realised P&L (banked, from the ledger): 7,573,245.41 EUR
      Unrealised P&L (open Positions, marked): 4,141,577.12 EUR
      45.31% apart
    Cost Basis / Execution Price — "an Execution Price is what one Trade filled at; a Cost Basis is what the whole holding cost"
      Unrealised P&L against stored Cost Basis: 4,141,577.12 EUR
      against the last Execution Price: 2,423,347.97 EUR
      41.49% apart
      over the 151 of 151 Positions on this date that a Trade touched — the rest arrived by transfer and have no last fill

    Traded Notional / Trade Count — "one large trade and a thousand small ones are opposite answers"
      busiest Account by Traded Notional: 6 (16,946,167 EUR)
      busiest Account by Trade Count: 8 (89 Trades)
      23 of 24 Accounts rank differently under the two
    Client / Account — "counting Accounts and calling them clients inflates every per-client figure"
      Clients with activity: 12 · Accounts with activity: 24
      Gross Revenue per Client: 16,271.68 · per Account: 8,135.84 EUR

PASS — the star schema matches Glossary Section B and the adapter seam holds
```

**Eleven of Section C's twelve rows are measured here.** The twelfth, `Adjusted
Close` against `Market Price`, is market data rather than client activity and is
measured by `--sources` against the committed snapshots. Every figure is dated
evidence from this run, on this window, and moves with a `--refresh`.

Two of the eleven are close, and both are reported rather than tuned away:

- **`Execution Price` / `Market Price` is 0.03% apart at book level** and 0.60% at
  its widest on a single Trade, with all 1,670 Trades filled away from the close.
  Fills sit either side of the close, so a book-level sum cancels them. That is a
  true property of the quantity, not a thin simulation — and it is now
  [DEBT-011](../debt-ledger.md), against the Gold Question Set.
- **The FX half of `Trade Date` / `Settlement Date` is 0.0409% apart**, against the
  1% [DEBT-004](../debt-ledger.md) wants. It does not clear it, so that entry
  stays open with a figure measured on the full window rather than on the spike's
  three series. The *period* half of the same row is 24.38% in its widest month,
  which is the half a period filter actually moves.

```
$ uv run python .claude/scripts/check_warehouse.py --sources
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_language.py
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised
PASS — documents agree with the Glossary and the writing conventions

$ uv run python .claude/scripts/verify_framework.py
PASS — framework is wired up correctly
```

**The checks were made to fail seven times before being trusted.** Each mutation
was applied, the pipeline and the check re-run unchanged, and the file restored and
compared byte-for-byte with `cmp`. G was added on review, on 2026-08-13, against
the check that review produced:

| Mutation | What was reported |
|---|---|
| A. Snapshot calendar widened to the dates *some* Instrument has a price | Pipeline raises: `the Warehouse holds no Market Price for instrument_id 4 on 2026-04-03. Its exchange did not trade that day, so a Position in it cannot be marked...` |
| B. `TRANSFERS_IN` and `TRANSFERS_OUT` set to zero | `--distinctions` exits 1: `every holding equals the sum of its own Trades, so Position Change and Trade are the same number on this data` |
| C. Rebate and Fee removed from every Account | `--distinctions` exits 1: `Section C pair 'Gross Revenue / Net Revenue' has collapsed: Gross Revenue is 197,457.75 and Net Revenue is 197,457.75, 0.0000% apart against a 0.50% floor` |
| D. `fct_trade.sql` casts Execution Price to two decimal places | `--distinctions` exits 1: `1659 of 1670 rows differ from what the simulator produces from the same seed`, and separately `6 Trades filled at exactly that date's Market Price` |
| E. Accounts in one region billed in a currency the Warehouse holds no rate for | Pipeline raises: `the Warehouse holds no FX Rate from GBP to CHF on 2024-09-02. Either the date is outside the window fct_fx_rate covers, or one of the two currencies is not one the traded universe is quoted in` |
| F. one Market Price deleted from under a Position | `--distinctions` exits 1 with six problems, including `9 Positions have no Market Price on their own Snapshot date` |
| G. `build_transfers` quantises to six decimal places instead of rounding to the lot — the defect this review found | `--distinctions` exits 1: `fct_position_snapshot holds 80 quantities that are not a whole lot of their own Instrument — the first is 61307.100000 of an Instrument of type 'equity', whose lot is 1` |

Mutations A and E were what turned two bare `KeyError`s on a tuple into the
sentences above: the failures were already loud, and they did not say what to do.

**Determinism.** Two full rebuilds from a deleted database produce byte-identical
output, pipeline and check alike — including every row count and every Section C
figure:

```
$ uv run python -m veritas.ingestion > run1.txt
$ uv run python .claude/scripts/check_warehouse.py --distinctions > check1.txt
$ uv run python -m veritas.ingestion > run2.txt
$ uv run python .claude/scripts/check_warehouse.py --distinctions > check2.txt
$ diff run1.txt run2.txt && diff check1.txt check2.txt && echo IDENTICAL
IDENTICAL
```

Determinism is not left to `Random` being seeded. Every draw in the simulator goes
through three helpers — `pick`, `happens`, `take` — that bottom out in
`randrange`, because `choice` and `sample` are library implementations that have
changed shape before, and a simulation whose output moves on a Python upgrade is
not the reproducible bring-up the Target State promises. The same helpers keep the
whole module inside `Decimal`: a float in a draw reaches a monetary column through
arithmetic, and this schema refuses floats in columns for reasons that apply one
step upstream too.

**Deliberately left undone**

- **The `unbillable` assertion in the pipeline is a backstop that cannot currently
  fire.** It is the check 2.4 asked for by name, and it is genuinely unreachable
  today: the simulator converts every amount as it generates it, so an
  unconvertible Denomination Currency raises in `convert` first — which is what
  mutation E demonstrates. It stays because the reachable path is a *future* one
  (a build that produces a date and currency the simulator never converted), and
  because a check that costs one query is cheaper than rediscovering the
  requirement. Recorded here rather than filed as debt: the code is not wrong, it
  is early.
- **No index beyond the primary keys.** `fct_position_snapshot` is the largest
  table at 61,907 rows and `--distinctions` completes in seconds.
- **The simulator writes no short Positions.** `fct_position_snapshot.quantity` is
  signed and the schema comment says negative is a short, but a sale is capped at
  the holding, so nothing goes below zero. Not a gap in the schema — the column's
  shape is not a claim about what one simulator generated — but a reviewer looking
  for a short will not find one.

**Look at this sceptically**

1. **Cost Basis uses average cost, and that is a choice the Glossary does not
   make.** On a partial sale the sold quantity takes its proportional share of what
   the whole holding cost. The alternative, first-in-first-out, needs a lot ledger
   this schema does not have — `fct_position_snapshot` carries one Cost Basis per
   holding, and the registered definition is *"the total for the held quantity,
   accumulated across the Trades that built it"*, which admits exactly one reading
   given one number. It is still an accounting policy chosen here rather than
   agreed, and it changes Realised P&L. **Worth a ruling.**
2. **Realised P&L is gross of Commission.** The proceeds less what the sold share
   cost, with the Commission recognised separately as the broker's revenue in
   `fct_accounting_movement`. Netting it into Realised P&L would count the same
   charge twice across the two Certified Metrics. Also a convention chosen here.
3. **The two movement tables use opposite sign conventions, and the schema now says
   so.** `fct_cash_movement.amount` is signed from the Account's side — positive
   enters it, which the schema already stated. `fct_accounting_movement.amount`
   carries the magnitude recognised, positive, as `fct_trade` stores the same three
   charges, so that Net Revenue = Σcommission − Σrebate − Σfee is literally true
   against the table. `realised P&L` is the one signed value there. A single
   convention across both would make one of them read backwards, but two
   conventions is a thing a reader must be told, so a comment was added to
   `schema.sql` beside the column. **This is the one edit this Sub-step made to a
   file 2.1 committed.**
4. **`simulated_*` raw table names coin no Glossary term, and that was checked
   rather than assumed.** The names follow the source-prefix convention every raw
   table already uses — `yahoo_price`, `nasdaq_symbol` — with the simulator as the
   source. The word itself is already the Glossary's: the `Ingestion` row says
   *"synthetic Trades, Cash Movements and Positions from a seeded simulator"*, and
   `simulator.py` matches that spelling. No capitalised term was coined, so no
   proposal is raised — but if `Simulator` should be a registered Section A
   component alongside `Ingestion`, this is the Sub-step that should have raised
   it.
5. **The Section C floor is 0.5%, and it is a judgement.** A pair whose two sides
   differ in the sixth decimal place is technically distinct and useless: no Gold
   Question Set built on it could tell a model that confused the pair from one that
   did not. Half a percent is where "a human would notice" was put. It is
   deliberately not DEBT-004's 1%, which is a different bar — that one is about a
   pair being a *reliable evaluation signal*, this one about the pair existing at
   all.
6. **The book is cash-heavy.** Cash Balance is 68.3m of a 114.7m Account Value, so
   Accounts hold more cash than stock. That follows from the opening deposit being
   computed to cover the deepest hole an Account's own trading digs, with a
   buffer — a defensible rule that produces a conservative book. Nothing depends on
   it, and the Cash Balance / Account Value pair separates by 40% regardless.

**What this hands the rest of the project**

- **Every Certified Metric can now return a number.** All eight are computable:
  Traded Notional, Trade Count, Gross and Net Revenue, Cash Balance, Account Value,
  Realised and Unrealised P&L. That was the claim Step 002 existed to make true,
  and `--distinctions` computes seven of the eight as a side effect of measuring
  the pairs.
- **Step 002 is complete.** All five Sub-steps are built, and Step 003 — the
  sqlglot spike deferred by [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
  — now has the real data it was moved in order to run against. Its third question
  needs *"a query computing revenue inline from `commission`"* to return a
  different number from the certified expression against a real warehouse; the
  32.59% between Gross and Net Revenue is that difference.
- **Two Ledger entries wait on the Gold Question Set**, both of the same kind and
  both now measured on the full window rather than on a spike: DEBT-004 at 0.0409%
  and DEBT-011 at 0.03%. Neither is a defect in the data. Both are constraints on
  what a gold question may ask.

### Changes made on review — 2026-08-13 (Sub-step 2.5)

Amino's review approved the Sub-step's four decisions and asked six questions. Two
of the six turned out to be defects and are fixed here; the rest are answered in
place. Every figure in the verification above was re-run after these changes.

#### 1. A transfer moved a fraction of a share — **fixed, and the check that would
have caught it is now committed**

The question was whether a transfer may carry a decimal quantity when a Trade must
be a whole lot. It may not, and it was. `build_transfers` took `money(held * share)`
and never rounded, so the one path that creates a Position *without* a Trade was
also the one path that ignored the lot.

This is a seam-level disagreement rather than a cosmetic one: a transfer moves the
same stock a Trade moves, and a custodian can no more deliver half a share than a
broker can fill half a share. The fix rounds to the Instrument's own lot exactly as
the partial-sale path does, and caps at the holding so that rounding up on a
transfer out cannot move stock the Account does not have.

**Nothing reported it, which is the more important half.** Every fractional row
satisfied the schema — `quantity` is a `DECIMAL(18, 6)`, because a column type is
about scale and not about lots — every Snapshot was markable, and the holding sat
inside an Account Value that looked entirely ordinary. So `--distinctions` gained
`check_lots`, and the size of the defect is quoted from that rather than from a
script written once to measure it. Applied as a mutation, with the rounding removed
again:

```
$ uv run python .claude/scripts/check_warehouse.py --distinctions   # rounding removed
    fct_trade                  1670 quantities · 0 not a whole lot
    fct_position_snapshot     61907 quantities · 80 not a whole lot
FAIL — 1 problem(s)
  - fct_position_snapshot holds 80 quantities that are not a whole lot of their own
    Instrument — the first is 61307.100000 of an Instrument of type 'equity', whose
    lot is 1. Every path that moves stock must agree about what one unit is, and a
    Trade and a transfer are two such paths
```

and with it restored:

```
$ uv run python .claude/scripts/check_warehouse.py --distinctions
    fct_trade                  1670 quantities · 0 not a whole lot
    fct_position_snapshot     61907 quantities · 0 not a whole lot
```

Both tables are checked, not only the one that broke: a rule enforced on Trades
alone is a rule that holds until something else moves stock, which is exactly what
happened here.

**What it moved.** Row counts are identical — the same subjects on the same dates —
and only quantities changed, on the three transferred holdings:

| Figure | Before | After |
|---|---|---|
| account 11 · instrument 4 holds | 292 | 293 |
| Account Value | 114,713,966.71 EUR | 114,714,721.82 EUR |
| Unrealised P&L | 4,141,453.20 EUR | 4,141,577.12 EUR |
| Cost Basis / Execution Price | 41.48% apart | 41.49% apart |

Nothing upstream of `build_transfers` moved: the draw sequence is unchanged, so
every Trade, Cash Movement and Accounting Movement is byte-identical, which is why
Gross Revenue and the Trade-side pairs are untouched.

#### 2. `at_last_fill` had a fallback that could not be right — **fixed**

The Cost Basis / Execution Price pair valued a holding at its last Execution Price,
and fell back to `cost_basis` when it could not find one:

```python
quantity * last_fills.get(f"{account_id}-{instrument_id}", cost_basis)   # before
```

Wrong twice. **A Cost Basis is a total and an Execution Price is a per-unit
price**, so multiplying the fallback by the quantity again is out by a factor of
the holding. And it puts the left side's own number into the right side, comparing
a figure with itself on exactly the Positions where the pair is hardest to
separate.

The honest answer to *what does it mean when a pair has no last fill* is that the
Position arrived by transfer and nothing ever filled — there is no stand-in for a
price that does not exist. Both sides are now summed over the Positions a Trade
actually touched, and the count is printed, so an excluded Position is visible
rather than papered over. On the loaded data the fallback never fired — all 151
Positions have Trades behind them — so the printed figure was right by luck of the
data rather than by construction.

**A second, quieter fault in the same lines.** `last_fills` was built by a
`max(trade_date)` subquery collapsed into a `dict`, and three (Account, Instrument)
pairs carry **two** Trades on their last Trade Date, all three of them holding a
Position on the final Snapshot date. Which of the two survived was whichever row
the engine emitted last. It is now read in `trade_date, trade_id` order and folded
in Python, so the tie is broken by the numbering `fct_trade` already carries.

#### 3. A Section C figure depended on the engine's row order — found while fixing 2

Not asked about, found by re-running: `23 of 24 Accounts rank differently` came
back as `24 of 24` after the rebuild, on **identical** Trade data. The cause is the
same class as the one above. Traded Notional is a Decimal total and never ties, but
Trade Count is a small integer and Accounts routinely share one — and the ranking's
ties were broken by `by_account`'s insertion order, which came from a `SELECT` with
no `ORDER BY`. A figure that changes while its inputs do not is a figure nothing
was pinning down.

The trades query is now ordered by `trade_id` and both rankings break ties on
`account_id`. The figure returned to **23 of 24** and is now reproducible by
construction rather than stable by luck:

```
$ uv run python -m veritas.ingestion        # twice, from a deleted database
$ uv run python .claude/scripts/check_warehouse.py --distinctions
$ diff run1.txt run2.txt && diff check1.txt check2.txt && echo IDENTICAL
IDENTICAL
```

#### 4. `read_market_data` now declares its parameter type

It read `def read_market_data(warehouse)  # noqa: ANN001 — WarehouseAdapter`. There
is no reason for the suppression: `veritas/ingestion/__main__.py` already imports
`WarehouseAdapter` from `veritas.warehouse`, so the annotation creates no cycle,
and **no linter is configured in this repository at all** — so the `noqa` silenced
a rule nothing enforces while advertising one the project does not have. The
parameter is annotated and the comment is gone.

#### 5. Three answers that changed no code

- **`held` in `build_transfers` counts non-Trade events too**, and now says so.
  The question was whether an outgoing transfer could be oversized because `held`
  was folded from Trade events alone. It could not, but only because `take` yields
  each subject at most once, so no subject ever gets two transfers — the arithmetic
  was correct by an accident of the loop rather than by construction. Each transfer
  is now appended to `events_by_subject` as it is sited, so the sum is right in the
  general case, and the comment states the guarantee instead of leaving it to be
  reconstructed.
- **`if trade["trade_side"] == "sell" and trade["realised_pnl_quoted"]`** suppresses
  a **zero-amount** posting, not a missing one. Every sell does realise a value; it
  can be exactly zero when proceeds equal the share of Cost Basis removed. It is
  the same guard the three charges above it use (`if not amount: continue`), for
  the same reason: a ledger row recognising nothing is a row that says nothing. On
  the loaded data it suppresses nothing — 554 sells produce 554 `realised P&L`
  postings, and no movement row of either table carries an amount of zero.
- **The sort key in `check_client_activity` had a no-op slice.** `values[:
  len(columns)]` is the whole tuple, since the tuple is built from those exact
  columns. It is removed. The `(value is None, value)` wrapper stays and is now
  explained: `trade_id` is NULL on every Cash Movement no Trade explains, and
  Python refuses to compare `None` with an `int`.

#### 6. Four Ledger and Register entries opened

| Entry | Why |
|---|---|
| [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes) | The intersection calendar is approved, but the sparse price table underneath it is the shortcut. 66 dates carry no Snapshot, so an "as of" question about one has no answer and the absence reads as a zero. |
| [DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews) | Average-cost Cost Basis, Realised P&L gross of Commission, and the calendar choice are argued **here**, in the internal record. A user-facing decision register is owed at the final documentation pass. |
| [EXT-008](../extension-register.md#ext-008--the-data-checks-run-in-continuous-integration) | `check_warehouse.py` and `check_data_availability.py` check the *data*, not the framework, and belong in a continuous-integration pipeline. An extension rather than debt: the scripts are right, and no pipeline exists to put them in. |
| [DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect) | **Trigger ruled fired.** Paid as Sub-step 2.6, committed separately from this one — see [R21](../plan/step-002-warehouse-and-ingestion.md#r21--debt-009-has-fired-and-is-paid-as-sub-step-26--ruled-by-amino-2026-08-13). |

**Re-verified after every change above:**

```
$ uv run python -m veritas.ingestion
PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9554 Market Prices across all 19 · fct_fx_rate holds 11840 FX Rates and every Market Price has one
       the client side holds 12 Clients · 24 Accounts · 1670 Trades · every Position is markable and every amount is convertible

$ uv run python .claude/scripts/check_warehouse.py --distinctions
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_warehouse.py --sources
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_language.py
  proposed terms: 0 · python files scanned: 13 · identifiers: 784
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised
PASS — documents agree with the Glossary and the writing conventions

$ uv run python .claude/scripts/verify_framework.py
  links      309 links, 146 anchors 22 documents
PASS — framework is wired up correctly
```

Run on 2026-08-13, offline.
