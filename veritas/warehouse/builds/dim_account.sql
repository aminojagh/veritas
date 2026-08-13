-- Build dim_account from the seeded simulator's output.
--
-- Hand-authored, and licensed and shaped exactly as dim_client.sql explains —
-- that file carries the reasoning for all seven simulator builds.
--
-- Runs after dim_client.sql: the foreign key to it is declared and enforced, so
-- an Account whose Client is missing is refused by the engine rather than stored.
--
-- No currency column, deliberately. An Account has *several* currency balances,
-- one row each in fct_balance_snapshot, and collapsing them onto the dimension
-- would make "the Account's currency" a thing that exists — which is how a
-- two-currency Account quietly reports one of its balances as its whole cash
-- position.

INSERT INTO dim_account (
    account_id,
    client_id,
    account_name
)
SELECT
    account.account_id,
    account.client_id,
    account.account_name
FROM raw.simulated_account AS account;
