-- Build fct_balance_snapshot from the seeded simulator's output.
--
-- Hand-authored, and licensed and shaped exactly as dim_client.sql explains —
-- that file carries the reasoning for all seven simulator builds.
--
-- Runs after dim_account.sql; the foreign key is declared and enforced.
--
-- **One row per Account per currency per date**, which is why dim_account carries
-- no currency column. An Account billed in two currencies has two Cash Balances
-- on every date, not a total — there is no rate at which a broker's ledger adds
-- them, and the conversion to a single figure belongs to a Metric Definition with
-- a stated Reporting Currency rather than to this table.
--
-- Cash only. Section C: *"A Client with €0 cash and €2m of equities has a Cash
-- Balance of zero. Answering 'how much does this client have' with Cash Balance
-- is not wrong arithmetic — it is the wrong question answered confidently."*
-- Account Value is the other answer, and it is a Metric Definition over this
-- table plus fct_position_snapshot rather than a column here.
--
-- Dense over the same Snapshot dates as fct_position_snapshot, from each
-- Account's first movement onward, for the same reason: an "as of" question is an
-- equality join.

INSERT INTO fct_balance_snapshot (
    snapshot_date,
    account_id,
    denomination_currency,
    cash_balance
)
SELECT
    snapshot.snapshot_date,
    snapshot.account_id,
    snapshot.denomination_currency,
    snapshot.cash_balance::DECIMAL(18, 6) AS cash_balance
FROM raw.simulated_balance_snapshot AS snapshot;
