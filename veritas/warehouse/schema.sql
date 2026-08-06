-- Veritas star schema — the ten tables named by Glossary Section B.
--
-- Hand-authored, and deliberately so. ADR-0002's clarification of 2026-08-05
-- settles that the sqlglot commitment governs SQL that code *assembles*, not SQL
-- a human wrote once: "Static DDL inside veritas/warehouse/ — allowed. Nothing is
-- rendered; this text *is* the source." An engine swap rewrites this one file,
-- next to the one connection function that also has to be rewritten. That cost is
-- bounded and visible on day one, which is the property the whole ADR is about.
--
-- Conventions, so that no number in this schema is quietly wrong:
--
--   * Money, quantities and prices are DECIMAL(18, 6); FX Rates are
--     DECIMAL(18, 8), because a reference rate carries more significant decimals
--     than a price does. Never DOUBLE, REAL or FLOAT anywhere. ADR-0002 rejected
--     SQLite on the grounds that "monetary aggregation over floats in a project
--     whose entire subject is quietly wrong numbers is not a trade worth making",
--     and that reasoning binds our own column types just as hard as it binds the
--     engine choice. check_warehouse.py fails the run if a float column appears.
--
--   * Three currency senses exist in this project and are never spelled the same
--     way, because two of them differing by a factor of 100 is a proven trap:
--       quotation_currency     what an Instrument's Market Price is quoted in,
--                              including its minor unit before normalisation
--       denomination_currency  what a monetary amount in a fact row is held in
--       Reporting Currency     what a Grounded Answer is expressed in — a
--                              property of an answer, not of a row, so it is
--                              deliberately absent from this schema
--
--   * There is no dim_date. The date axis is the trade_date, settlement_date,
--     movement_date, price_date, rate_date and snapshot_date columns — Step 002
--     ruling R2, which corrected target-state.md rather than adding a table.
--
--   * Foreign keys are declared and therefore enforced, so dimensions must be
--     loaded before facts. That ordering constraint is deliberate: an orphan fact
--     row is a wrong number waiting to be aggregated.
--
--   * A `_snapshot` table records state as of a date, one row per subject per
--     date, enforced by the primary key. The rule that follows: ask a snapshot
--     what was *held*, ask fct_trade what was *done*, never substitute one for
--     the other — a snapshot cannot see between its own dates, and fct_trade
--     cannot see a transfer.
--
--   * The daily grain is a floor imposed by the sources, not a choice this schema
--     made. It is not a shortcut and there is nothing here to repay.
--
--     Both points are argued in full, with the cases that go wrong, in the Step
--     Review — "What `snapshot` means here" and "Was daily the problem?":
--     .claude/docs/reviews/step-002-warehouse-and-ingestion.md

-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- Dimensions
-- ---------------------------------------------------------------------------

-- Client — the legal owner of one or more Accounts, and the entity a region
-- attaches to. Kept separate from Account because Section C warns that counting
-- Accounts and calling them Clients inflates every per-client figure.
CREATE TABLE dim_client (
    client_id      BIGINT  PRIMARY KEY,
    client_name    VARCHAR NOT NULL,
    -- Named and valued by the "by region" Dimension Definition, verbatim.
    client_region  VARCHAR NOT NULL CHECK (client_region IN ('EU', 'UK', 'APAC'))
);

-- Account — the container trades and cash sit in. Exactly one Client; its
-- several currency balances live in fct_balance_snapshot, one row per currency,
-- which is why no currency column appears here.
CREATE TABLE dim_account (
    account_id    BIGINT  PRIMARY KEY,
    client_id     BIGINT  NOT NULL REFERENCES dim_client(client_id),
    account_name  VARCHAR NOT NULL
);

-- Instrument — equity, ETF, future or currency pair. Single bonds and options
-- are out of scope (DEBT-003): neither has a key-free Market Price source, so
-- holding them would mean fabricating prices while claiming market data is real.
CREATE TABLE dim_instrument (
    instrument_id      BIGINT  PRIMARY KEY,
    -- The natural key both reference sources supply and the price source keys
    -- on: NASDAQ Trader's `Symbol` column, Yahoo's `symbol` field.
    instrument_symbol  VARCHAR NOT NULL UNIQUE,
    instrument_name    VARCHAR NOT NULL,
    -- The "by instrument type" Dimension Definition axis. These four values are
    -- the Instrument term's own universe as narrowed on 2026-08-03; Step 002
    -- ruling R10 swept the Dimension Definition row to match.
    instrument_type    VARCHAR NOT NULL
        CHECK (instrument_type IN ('equity', 'ETF', 'future', 'currency pair')),
    -- Rejects a minor-unit code at load time rather than after aggregation.
    -- Yahoo returns `GBp` for London listings, which is pence, and booking £4.20
    -- as £420 looks entirely plausible all the way to the answer. Every ISO 4217
    -- code is upper case, so a code that is not equal to its own upper case is a
    -- minor-unit marker that ingestion failed to normalise.
    -- Limit worth knowing: this does not catch the `GBX` spelling, which is upper
    -- case. Ingestion's own check covers the general case.
    quotation_currency VARCHAR NOT NULL
        CHECK (quotation_currency = upper(quotation_currency))
);

-- ---------------------------------------------------------------------------
-- Facts — market data (real)
-- ---------------------------------------------------------------------------

-- FX Rate — the ECB reference rate from Frankfurter, and only from Frankfurter.
-- Yahoo's EURUSD=X works but is forbidden here: two sources for one concept is
-- the synonym disease Non-Negotiable #1 exists to prevent.
--
-- Named from_currency/to_currency rather than the conventional base/quote pair
-- on purpose. "Quote currency" is standard FX vocabulary and would sit one letter
-- away from quotation_currency above while meaning something entirely different,
-- which is the collision Section C exists to catch.
--
-- The ECB publishes on working days only. Ingestion fills forward, so a rate for
-- a non-publishing date is the most recent published rate at or before it, and
-- every calendar date in the loaded window resolves to a row.
CREATE TABLE fct_fx_rate (
    rate_date      DATE           NOT NULL,
    from_currency  VARCHAR        NOT NULL,
    to_currency    VARCHAR        NOT NULL,
    fx_rate        DECIMAL(18, 8) NOT NULL,
    PRIMARY KEY (rate_date, from_currency, to_currency)
);

-- Market Price — the unadjusted close, the only price a Position may be marked
-- at. There is deliberately no adjusted-close column: Adjusted Close is
-- registered as an anti-pattern, it differs from the close on 95.5% of AAPL's
-- last 1,255 daily bars, and it is back-adjusted every time a dividend is paid,
-- so an Account Value marked at it is both wrong and irreproducible. Giving it
-- nowhere to land is cheaper than remembering not to use it.
CREATE TABLE fct_instrument_price (
    price_date     DATE           NOT NULL,
    instrument_id  BIGINT         NOT NULL REFERENCES dim_instrument(instrument_id),
    market_price   DECIMAL(18, 6) NOT NULL,
    PRIMARY KEY (price_date, instrument_id)
);

-- ---------------------------------------------------------------------------
-- Facts — client activity (synthetic)
-- ---------------------------------------------------------------------------

-- Trade — one executed order. Two currency senses meet on this row and the
-- difference is not decorative:
--   quantity * execution_price  is in the Instrument's quotation_currency
--   commission, fee, rebate     are in this row's denomination_currency
-- A broker does not necessarily charge in the currency the Instrument is quoted
-- in, so Traded Notional and Gross Revenue take different routes through
-- fct_fx_rate to reach the Reporting Currency.
CREATE TABLE fct_trade (
    trade_id               BIGINT  PRIMARY KEY,
    account_id             BIGINT  NOT NULL REFERENCES dim_account(account_id),
    instrument_id          BIGINT  NOT NULL REFERENCES dim_instrument(instrument_id),
    -- Section C: which of these a period filter uses shifts revenue across period
    -- boundaries, and also selects the FX Rate, so it moves the number twice.
    trade_date             DATE    NOT NULL,
    settlement_date        DATE    NOT NULL,
    trade_side             VARCHAR NOT NULL CHECK (trade_side IN ('buy', 'sell')),
    -- Always positive; direction lives in trade_side. This is what keeps the
    -- Traded Notional definition literally true as the Glossary writes it,
    -- Σ(quantity × Execution Price), with no undocumented ABS().
    quantity               DECIMAL(18, 6) NOT NULL CHECK (quantity > 0),
    execution_price        DECIMAL(18, 6) NOT NULL,
    commission             DECIMAL(18, 6) NOT NULL,
    fee                    DECIMAL(18, 6) NOT NULL,
    rebate                 DECIMAL(18, 6) NOT NULL,
    denomination_currency  VARCHAR NOT NULL,
    CHECK (settlement_date >= trade_date)
);

-- Cash Movement — money actually entering or leaving an Account on a date.
-- Half of the Section C pair below; the other half is fct_accounting_movement.
-- trade_id is nullable because a deposit belongs to no Trade.
--
-- The movement_type values are the Glossary's own list for this table —
-- "deposits, withdrawals, settlement, fee charges" — spelled as data, plus the
-- three charge kinds fct_trade already names as columns. `amount` is signed:
-- positive enters the Account, negative leaves it.
--
-- Note what is *not* here: `realised P&L`. No cash moves when a Position closes;
-- the cash moved at settlement. It is an accounting movement only, and the two
-- lists differ on purpose — that difference is the Section C pair made structural
-- rather than remembered.
CREATE TABLE fct_cash_movement (
    cash_movement_id       BIGINT  PRIMARY KEY,
    account_id             BIGINT  NOT NULL REFERENCES dim_account(account_id),
    trade_id               BIGINT  REFERENCES fct_trade(trade_id),
    movement_date          DATE    NOT NULL,
    movement_type          VARCHAR NOT NULL
        CHECK (movement_type IN ('deposit', 'withdrawal', 'trade settlement',
                                 'commission', 'fee', 'rebate')),
    amount                 DECIMAL(18, 6) NOT NULL,
    denomination_currency  VARCHAR NOT NULL
);

-- Accounting Movement — a ledger entry recognising economic value on the date it
-- was *earned*, whether or not cash moved. Commission is earned on Trade Date and
-- collected on Settlement Date, so in any period straddling a settlement cycle
-- this table and fct_cash_movement disagree, and both are correct answers to
-- different questions.
-- `realised P&L` is the value that makes this table load-bearing rather than a
-- mirror of fct_cash_movement: Realised P&L is a registered Certified Metric and
-- this row is where it is computed from. Section C's Realised/Unrealised pair is
-- the reason it cannot live on a Position — one is banked, one is a market
-- opinion, and only the banked one is a ledger entry.
CREATE TABLE fct_accounting_movement (
    accounting_movement_id BIGINT  PRIMARY KEY,
    account_id             BIGINT  NOT NULL REFERENCES dim_account(account_id),
    trade_id               BIGINT  REFERENCES fct_trade(trade_id),
    movement_date          DATE    NOT NULL,
    movement_type          VARCHAR NOT NULL
        CHECK (movement_type IN ('commission', 'fee', 'rebate', 'realised P&L')),
    amount                 DECIMAL(18, 6) NOT NULL,
    denomination_currency  VARCHAR NOT NULL
);

-- Cash Balance — money held in an Account in one currency at a point in time.
-- Cash only. Section C: a Client with €0 cash and €2m of equities has a Cash
-- Balance of zero, and answering "how much does this client have" with it is not
-- wrong arithmetic but the wrong question answered confidently. Account Value is
-- the other answer, and it is a Metric Definition over this table plus
-- fct_position_snapshot, not a column.
CREATE TABLE fct_balance_snapshot (
    snapshot_date          DATE    NOT NULL,
    account_id             BIGINT  NOT NULL REFERENCES dim_account(account_id),
    denomination_currency  VARCHAR NOT NULL,
    cash_balance           DECIMAL(18, 6) NOT NULL,
    PRIMARY KEY (snapshot_date, account_id, denomination_currency)
);

-- Position — quantity of one Instrument held by one Account at a point in time.
-- Unlike fct_trade.quantity this is signed and may be zero: negative is a short,
-- and a zero row is how a closed Position records that it closed, which is what
-- Realised P&L is computed against.
--
-- Position — quantity held, plus what it cost.
--
--   quantity    signed; negative is a short, zero records a closed Position.
--   cost_basis  Cost Basis: the total the held quantity cost to acquire, in the
--               Instrument's Quotation Currency. Signed with quantity, so
--               Unrealised P&L is quantity × Market Price − cost_basis for a long
--               and a short alike.
--
-- Snapshotted rather than derived from fct_trade, and cost_basis stored rather
-- than folded out of it. Both are correctness decisions, not conveniences, and
-- the three worked examples that show why a fold returns a plausible wrong number
-- are in the Step Review — "Why Cost Basis is stored, in three examples":
-- .claude/docs/reviews/step-002-warehouse-and-ingestion.md
--
-- The CHECK below says a closed Position cost nothing to hold: without it a
-- zero-quantity row could keep a stale basis and report P&L on nothing.
CREATE TABLE fct_position_snapshot (
    snapshot_date  DATE           NOT NULL,
    account_id     BIGINT         NOT NULL REFERENCES dim_account(account_id),
    instrument_id  BIGINT         NOT NULL REFERENCES dim_instrument(instrument_id),
    quantity       DECIMAL(18, 6) NOT NULL,
    cost_basis     DECIMAL(18, 6) NOT NULL,
    PRIMARY KEY (snapshot_date, account_id, instrument_id),
    CHECK (quantity != 0 OR cost_basis = 0)
);
