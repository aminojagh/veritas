-- Build fct_accounting_movement from the seeded simulator's output.
--
-- Hand-authored, and licensed and shaped exactly as dim_client.sql explains —
-- that file carries the reasoning for all seven simulator builds.
--
-- Runs after fct_trade.sql, for the same declared foreign key as
-- fct_cash_movement.sql. Here `trade_id` is null on nothing the simulator emits:
-- every Accounting Movement it writes recognises value from a Trade. The column
-- stays nullable because the schema's shape is not a claim about what one
-- simulator happened to generate.
--
-- **This table's date is the date value was earned.** Its twin,
-- fct_cash_movement, holds the same charges on the date cash moved.
--
-- Two things separate this table from a mirror of that one, and both are why
-- Section C names the pair:
--
--   * `realised P&L` appears here and can never appear there. Realised P&L is a
--     Certified Metric and this row is where it is computed from; no cash moves
--     when a Position closes.
--   * Deposits, withdrawals and the settlement of the Trade itself appear there
--     and never here. They move money and recognise no value.
--
-- `amount` carries the **magnitude** recognised, positive, as fct_trade stores
-- the same three charges — so the Glossary's own formula is literally true
-- against this table: Net Revenue = Σcommission − Σrebate − Σfee. `realised P&L`
-- is the one signed value here, because a loss is genuinely negative.

INSERT INTO fct_accounting_movement (
    accounting_movement_id,
    account_id,
    trade_id,
    movement_date,
    movement_type,
    amount,
    denomination_currency
)
SELECT
    movement.accounting_movement_id,
    movement.account_id,
    movement.trade_id,
    movement.movement_date,
    -- The column's CHECK holds this to four values — commission · fee · rebate ·
    -- realised P&L — and the list deliberately differs from fct_cash_movement's.
    -- That difference is the Section C pair made structural rather than
    -- remembered: `deposit` is refused here, `realised P&L` is refused there.
    movement.movement_type,
    movement.amount::DECIMAL(18, 6) AS amount,
    movement.denomination_currency
FROM raw.simulated_accounting_movement AS movement;
