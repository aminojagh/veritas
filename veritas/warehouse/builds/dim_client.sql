-- Build dim_client from the seeded simulator's output.
--
-- Hand-authored and executed by the Warehouse Adapter, under the same licence as
-- schema.sql and the three market-data builds beside it: ADR-0002's clarification
-- of 2026-08-05 settles that the sqlglot commitment governs SQL that code
-- *assembles*, not SQL a human wrote once. It lives here rather than in
-- veritas/ingestion/ because R4 puts the raw-to-star boundary on this side of the
-- seam, which is also what keeps DEBT-009's trigger — "the first component outside
-- the adapter emits SQL" — unfired.
--
-- **This is the first of seven builds whose source is the simulator rather than a
-- vendor, and they are thinner than the three before them on purpose.** A vendor
-- speaks its own vocabulary — Yahoo's `instrumentType`, NASDAQ Trader's two
-- spellings of the symbol column — so `dim_instrument.sql` and the two price
-- builds are where that vocabulary is translated into the Glossary's. The
-- simulator is ours and already emits Glossary terms, so there is nothing to
-- translate and inventing a translation would be ceremony.
--
-- What these seven files still do, and why they exist rather than the pipeline
-- writing the star tables directly:
--
--   * **They are the contract.** The column list below is what the simulator has
--     to produce; if it stops producing one, this fails loudly here rather than
--     landing a NULL three tables downstream.
--   * **They cast.** dlt infers a wide DECIMAL for every Python Decimal it lands.
--     The star schema's monetary scale is DECIMAL(18, 6) and its FX scale is
--     DECIMAL(18, 8), and the cast is what makes a `raw` value become a
--     Warehouse value at a declared precision instead of whatever the loader
--     guessed.
--   * **They keep one writer.** Every star table in this Warehouse is filled by
--     hand-authored SQL run through `run_build`. A second way in — the pipeline
--     inserting rows itself — would mean the adapter is the only door for three
--     tables and one of two doors for the other seven.
--
-- Runs first among the seven, because dim_account references it and the foreign
-- key is declared and therefore enforced.

INSERT INTO dim_client (
    client_id,
    client_name,
    client_region
)
SELECT
    client.client_id,
    client.client_name,
    -- The "by region" Dimension Definition's own values, EU · UK · APAC. The
    -- column's CHECK refuses anything else, so a simulator that invented a fourth
    -- region fails here rather than producing a slice nothing can name.
    client.client_region
FROM raw.simulated_client AS client;
