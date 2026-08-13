-- Build fct_cash_movement from the seeded simulator's output.
--
-- Hand-authored, and licensed and shaped exactly as dim_client.sql explains —
-- that file carries the reasoning for all seven simulator builds.
--
-- Runs after fct_trade.sql: `trade_id` references it and the foreign key is
-- declared and enforced. It is nullable, and the rows where it is null are the
-- point — a deposit belongs to no Trade, and neither does a withdrawal.
--
-- **This table's date is the date cash moved.** Its twin,
-- fct_accounting_movement, holds the same charges on the date they were *earned*.
-- That is the whole of Section C's `Cash Movement` against `Accounting Movement`
-- row: commission is earned on Trade Date and collected on Settlement Date, so a
-- period boundary between the two gives the two tables different totals and both
-- are right.
--
-- `amount` is signed **from the Account's side**: positive enters it, negative
-- leaves it. A buy's settlement is negative, a sell's is positive, a Commission
-- and a Fee are negative, a Rebate is positive because it is value handed back.
-- The sign convention differs from fct_accounting_movement's on purpose, and both
-- are stated where the column is defined.

INSERT INTO fct_cash_movement (
    cash_movement_id,
    account_id,
    trade_id,
    movement_date,
    movement_type,
    amount,
    denomination_currency
)
SELECT
    movement.cash_movement_id,
    movement.account_id,
    movement.trade_id,
    movement.movement_date,
    -- The column's CHECK holds this list to the six values agreed in Sub-step 2.1
    -- when DEBT-010 was paid: deposit · withdrawal · trade settlement ·
    -- commission · fee · rebate. `realised P&L` is deliberately absent — no cash
    -- moves when a Position closes, the cash moved at settlement — and a
    -- simulator that emitted one would fail here rather than in a metric.
    movement.movement_type,
    movement.amount::DECIMAL(18, 6) AS amount,
    movement.denomination_currency
FROM raw.simulated_cash_movement AS movement;
