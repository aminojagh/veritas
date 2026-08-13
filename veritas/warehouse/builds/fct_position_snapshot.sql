-- Build fct_position_snapshot from the seeded simulator's output.
--
-- Hand-authored, and licensed and shaped exactly as dim_client.sql explains —
-- that file carries the reasoning for all seven simulator builds.
--
-- Runs after dim_account.sql and dim_instrument.sql; both foreign keys are
-- declared and enforced.
--
-- **The grain is one row per Account, Instrument and date, and the primary key is
-- what enforces it.** The simulator writes a row on *every* Snapshot date from a
-- holding's first appearance onward, including the zero rows a closed Position
-- leaves behind, so an "as of D" question is an equality join rather than a
-- most-recent-row-at-or-before lookup. That density is part of what `Snapshot`
-- means, not a loading detail.
--
-- Which dates those are was Sub-step 2.5's to settle. R13 fixed *"every date the
-- Warehouse holds a Market Price for"*, which reads two ways across five exchange
-- calendars — the dates *some* Instrument has a price, or the dates *every* one
-- does. The simulator takes the second; `read_market_data` in
-- veritas/ingestion/simulator.py argues why, and `check_warehouse.py
-- --distinctions` fails the run if any Snapshot lands on a date its own
-- Instrument has no Market Price for.
--
-- `cost_basis` is stored rather than folded out of fct_trade. That is a
-- correctness decision with three worked examples behind it in the Step Review,
-- and this build is where it becomes a column with rows in it.

INSERT INTO fct_position_snapshot (
    snapshot_date,
    account_id,
    instrument_id,
    quantity,
    cost_basis
)
SELECT
    snapshot.snapshot_date,
    snapshot.account_id,
    snapshot.instrument_id,
    -- Signed, unlike fct_trade.quantity: negative is a short and zero records a
    -- closed Position. The simulator writes no shorts, and the column stays
    -- signed because the schema's shape is not a claim about what one simulator
    -- generated.
    snapshot.quantity::DECIMAL(18, 6) AS quantity,
    -- In the Instrument's Quotation Currency, signed with quantity — so
    -- Unrealised P&L is quantity × Market Price − cost_basis for a long and a
    -- short alike. The schema's CHECK (quantity != 0 OR cost_basis = 0) refuses a
    -- closed Position that kept a stale basis.
    snapshot.cost_basis::DECIMAL(18, 6) AS cost_basis
FROM raw.simulated_position_snapshot AS snapshot;
