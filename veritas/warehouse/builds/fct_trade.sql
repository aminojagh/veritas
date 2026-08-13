-- Build fct_trade from the seeded simulator's output.
--
-- Hand-authored, and licensed and shaped exactly as dim_client.sql explains —
-- that file carries the reasoning for all seven simulator builds.
--
-- Runs after dim_account.sql and after dim_instrument.sql, because both foreign
-- keys are declared and enforced.
--
-- **Two currency senses meet on this row and the casts below do not make them the
-- same.** `quantity * execution_price` is in the Instrument's Quotation Currency;
-- `commission`, `fee` and `rebate` are in this row's `denomination_currency`. The
-- schema comment says so and Section C's `Denomination Currency` against
-- `Quotation Currency` row says why: a broker charges in the currency it bills in
-- rather than the one the exchange quotes in, so Traded Notional and Gross Revenue
-- take different routes through fct_fx_rate to reach a Reporting Currency.
--
-- The three charge columns are **magnitudes, all positive**, as the Glossary
-- writes them: Net Revenue = Gross Revenue − Rebate − pass-through Fee. Direction
-- is not carried here at all — `trade_side` carries the Trade's direction, and
-- `fct_cash_movement.amount` carries the direction money moved.

INSERT INTO fct_trade (
    trade_id,
    account_id,
    instrument_id,
    trade_date,
    settlement_date,
    trade_side,
    quantity,
    execution_price,
    commission,
    fee,
    rebate,
    denomination_currency
)
SELECT
    trade.trade_id,
    trade.account_id,
    trade.instrument_id,
    trade.trade_date,
    -- Two trading days after the Trade, on the Instrument's own calendar. The
    -- schema's CHECK (settlement_date >= trade_date) is what refuses the inverted
    -- case; the simulator is what makes the gap a real settlement cycle rather
    -- than zero, which is what gives Section C's Trade Date against Settlement
    -- Date row something to measure.
    trade.settlement_date,
    trade.trade_side,
    -- Always positive — the schema's CHECK enforces it, so that Traded Notional
    -- stays literally Σ(quantity × Execution Price) with no hidden ABS().
    trade.quantity::DECIMAL(18, 6) AS quantity,
    trade.execution_price::DECIMAL(18, 6) AS execution_price,
    trade.commission::DECIMAL(18, 6) AS commission,
    trade.fee::DECIMAL(18, 6) AS fee,
    trade.rebate::DECIMAL(18, 6) AS rebate,
    trade.denomination_currency
FROM raw.simulated_trade AS trade;
