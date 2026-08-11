-- Build fct_instrument_price from the Yahoo chart bars dlt landed.
--
-- Hand-authored and executed by the Warehouse Adapter, under the same licence as
-- schema.sql and dim_instrument.sql: ADR-0002's clarification of 2026-08-05
-- settles that the sqlglot commitment governs SQL that code *assembles*, not SQL
-- a human wrote once. It lives here rather than in veritas/ingestion/ because R4
-- puts the raw-to-star boundary on this side of the seam, which is also what
-- keeps DEBT-009's trigger — "the first component outside the adapter emits SQL" —
-- unfired.
--
-- Runs after dim_instrument.sql, because the foreign key below is declared and
-- enforced: a price for an Instrument the dimension does not hold is refused by
-- the engine rather than stored.
--
-- **Three transforms happen here and nowhere else.** raw.yahoo_price holds the
-- response's own values — an epoch timestamp and a close that may be null — so
-- this file is where a reader looks for what was done to the numbers.
--
--   1. A bar's timestamp becomes the trading date **on the exchange's own clock**.
--   2. A price quoted in a minor unit is divided down to the major unit.
--   3. A bar from a session that had not closed yet is dropped.
--
-- Each is argued at the line that does it.

INSERT INTO fct_instrument_price (
    price_date,
    instrument_id,
    market_price
)
WITH bar AS (
    SELECT
        price.instrument_symbol,

        -- 1. The trading date on the exchange's own clock.
        --
        -- Yahoo timestamps a daily bar at the moment the session opened, in
        -- Coordinated Universal Time (UTC), and `meta.gmtoffset` is how far the
        -- exchange is from it. Reading the timestamp as a UTC date instead is
        -- correct for New York, Tokyo and Frankfurt by coincidence and **wrong
        -- for a currency pair**: its bars sit at 23:00 UTC, which is midnight in
        -- London, so a UTC date books every one of them a day early.
        --
        -- Measured, not feared: `check_warehouse.py --sources` re-derives every
        -- date independently and prints how many rows the UTC reading would move
        -- on whatever window is loaded.
        --
        -- make_timestamp() rather than to_timestamp(): to_timestamp() returns a
        -- value with a time zone attached, so casting it to DATE would give an
        -- answer that depends on the session's TimeZone setting. This produces
        -- the same date on every machine.
        make_timestamp(
            (price.bar_timestamp + yahoo.utc_offset_seconds) * 1000000
        )::DATE AS price_date,

        price.unadjusted_close,

        -- 2. The minor-unit factor, or 1 for a currency that is not one.
        --
        -- The London listings quote in pence and dim_instrument records them as
        -- GBP, so a price carried across unchanged would be a hundred times the
        -- Position's real value — the trap the Quotation Currency term exists to
        -- name. The factor is joined from raw rather than written here as a
        -- literal, so the currency and the number that divides it stay in one
        -- place: veritas/ingestion/universe.py.
        coalesce(minor_unit.minor_units_per_major, 1) AS minor_units_per_major,

        -- 3. The two halves of "was this response taken mid-session?".
        --
        -- Yahoo includes the day in progress as a bar whose close is the current
        -- price. That is not a Market Price: the Glossary defines one as "the
        -- unadjusted **closing** price at which an Instrument traded on a date",
        -- and R12 makes end-of-day part of what a Snapshot means, so a Position
        -- marked against a mid-session number would be marked against a price
        -- that never closed anything. Whether a given snapshot carries such a bar
        -- depends on the minute it was fetched, which is why the rule lives here
        -- rather than in a note about the files currently committed.
        yahoo.last_market_time < yahoo.current_session_end AS taken_mid_session,
        make_timestamp(
            (yahoo.current_session_end + yahoo.utc_offset_seconds) * 1000000
        )::DATE AS current_session_date

    FROM raw.yahoo_price AS price

    -- The `meta` block of the same response the bars came from: one row per
    -- Instrument, carrying the exchange's offset, its session times and the
    -- currency the bars are quoted in.
    JOIN raw.yahoo_instrument AS yahoo
        ON yahoo.instrument_symbol = price.instrument_symbol

    LEFT JOIN raw.minor_unit_currency AS minor_unit
        ON minor_unit.minor_unit_currency = yahoo.quotation_currency
)
SELECT
    bar.price_date,
    instrument.instrument_id,
    (bar.unadjusted_close / bar.minor_units_per_major)::DECIMAL(18, 6) AS market_price

FROM bar

-- An inner join, deliberately. dim_instrument is the traded Instrument universe,
-- so a bar for anything outside it has no Position to mark and no Trade to price;
-- the foreign key would refuse it anyway, and refusing it here says why.
JOIN dim_instrument AS instrument
    ON instrument.instrument_symbol = bar.instrument_symbol

-- A holiday inside the requested range arrives as a timestamp with a null close.
-- It is landed in raw because that is what the response held, and dropped here
-- because market_price is NOT NULL and a day the Instrument did not trade has no
-- closing price to record.
WHERE bar.unadjusted_close IS NOT NULL
  AND NOT (bar.taken_mid_session AND bar.price_date = bar.current_session_date);
