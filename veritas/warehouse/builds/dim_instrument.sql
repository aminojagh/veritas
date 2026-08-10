-- Build dim_instrument from the raw reference sources dlt landed.
--
-- Hand-authored and executed by the Warehouse Adapter, under the same licence as
-- schema.sql: ADR-0002's clarification of 2026-08-05 settles that the sqlglot
-- commitment governs SQL that code *assembles*, not SQL a human wrote once, and
-- "static DDL inside veritas/warehouse/ — allowed. Nothing is rendered; this text
-- *is* the source."
--
-- It lives here rather than in veritas/ingestion/ deliberately. Step 002 ruling R4
-- settles the boundary — "dlt lands raw source data in a `raw` schema; the adapter
-- executes the SQL that builds the star schema from it" — and keeping the text on
-- the adapter's side of the seam means no component outside veritas/warehouse/
-- emits SQL. That is also what keeps DEBT-009's trigger unfired: it fires on "the
-- first component outside the adapter emits SQL", and after this Sub-step there
-- still is not one.
--
-- Re-runnable: the caller recreates the star schema before this runs, so this
-- script inserts into an empty table and never has to reason about what a second
-- run would do to a primary key.

INSERT INTO dim_instrument (
    instrument_id,
    instrument_symbol,
    instrument_name,
    instrument_type,
    quotation_currency
)
SELECT
    -- A surrogate key the sources do not supply. Ordered by Instrument Symbol so
    -- that two runs over the same snapshots produce the same ids — a rebuilt
    -- Warehouse that renumbers its dimension would silently invalidate every
    -- foreign key in a fact table loaded against the previous run.
    row_number() OVER (ORDER BY yahoo.instrument_symbol) AS instrument_id,

    yahoo.instrument_symbol,

    -- Name precedence: the registered name where the security has one, then the
    -- exchange's security name, then the price source's long name. Most
    -- authoritative first. The visible consequence is a mixed-case column — the
    -- SEC shouts ("JOHNSON & JOHNSON") where Yahoo does not ("SAP SE") — which is
    -- the sources' own inconsistency rather than a transform, and is a one-line
    -- change here if a reader would rather have the tidier column.
    coalesce(sec.registered_name, nasdaq.security_name, yahoo.long_name)
        AS instrument_name,

    -- The exchange's own exchange-traded fund flag wins where there is one: it is
    -- the reference source's classification, and data-availability.md chose the
    -- source partly for it. Yahoo's vocabulary covers everything else, translated
    -- through raw.yahoo_instrument_type rather than a CASE, so the four permitted
    -- values live in exactly one place.
    CASE
        WHEN nasdaq.is_etf = 'Y' THEN 'ETF'
        ELSE instrument_type_map.instrument_type
    END AS instrument_type,

    -- Normalise the minor unit before the row is offered to the engine. `GBp` is
    -- pence; dim_instrument's CHECK refuses any code that is not equal to its own
    -- upper case, so an unnormalised London listing fails the insert loudly
    -- instead of booking £4.20 as £420 four joins later.
    coalesce(minor_unit.major_unit_currency, yahoo.quotation_currency)
        AS quotation_currency

-- The traded Instrument universe is exactly what raw.yahoo_instrument holds, so
-- this join drives the row set and every other source is an enrichment. That is
-- why the universe is declared once, in veritas/ingestion/universe.py, and why a
-- symbol missing its metadata drops out here rather than arriving half-populated
-- — the row count assertion in check_warehouse.py --sources is what catches it.
FROM raw.yahoo_instrument AS yahoo

-- Both NASDAQ Trader files are landed in one table and a symbol can appear in
-- either, so the join is against one row per symbol rather than the raw rows.
-- max(is_etf) resolves 'Y' over 'N' because 'Y' sorts after 'N': if either half
-- of the directory calls it a fund, it is one.
LEFT JOIN (
    SELECT
        instrument_symbol,
        max(security_name) AS security_name,
        max(is_etf)        AS is_etf
    FROM raw.nasdaq_symbol
    GROUP BY instrument_symbol
) AS nasdaq
    ON nasdaq.instrument_symbol = yahoo.instrument_symbol

LEFT JOIN (
    SELECT
        instrument_symbol,
        max(registered_name) AS registered_name
    FROM raw.sec_registrant
    GROUP BY instrument_symbol
) AS sec
    ON sec.instrument_symbol = yahoo.instrument_symbol

LEFT JOIN raw.minor_unit_currency AS minor_unit
    ON minor_unit.minor_unit_currency = yahoo.quotation_currency

-- Three similar names meet on the next two lines, and they are three different
-- things. Reading `instrument_type_map.instrument_type` without this note is
-- harder than it should be:
--
--   raw.yahoo_instrument_type   the TABLE. Named for what it holds — Yahoo's
--                               instrument-type vocabulary — because every raw
--                               table is named for its source.
--   instrument_type_map         the ALIAS this query gives that table. Named for
--                               the ROLE it plays here: it is the translation
--                               table, not a source of Instruments. Aliasing it
--                               `yahoo` would collide with the driving join, and
--                               reusing the table name would read as though the
--                               row set came from it.
--   .instrument_type            the COLUMN holding *our* registered value —
--                               'equity', 'ETF', 'future', 'currency pair'. Its
--                               sibling `.source_instrument_type` holds Yahoo's
--                               word ('EQUITY', 'CURRENCY'). The join matches on
--                               theirs and selects ours, which is the whole
--                               purpose of the table: one place where a source's
--                               vocabulary becomes the Glossary's.
LEFT JOIN raw.yahoo_instrument_type AS instrument_type_map
    ON instrument_type_map.source_instrument_type = yahoo.source_instrument_type;
