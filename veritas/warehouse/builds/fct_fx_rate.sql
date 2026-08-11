-- Build fct_fx_rate from the European Central Bank (ECB) reference rates dlt
-- landed via Frankfurter.
--
-- Hand-authored and executed by the Warehouse Adapter, under the same licence as
-- schema.sql and the two build scripts beside it: ADR-0002's clarification of
-- 2026-08-05 settles that the sqlglot commitment governs SQL that code
-- *assembles*, not SQL a human wrote once. It lives here rather than in
-- veritas/ingestion/ because R4 puts the raw-to-star boundary on this side of the
-- seam, which is also what keeps DEBT-009's trigger — "the first component outside
-- the adapter emits SQL" — unfired.
--
-- Runs after fct_instrument_price, and reads both tables built before it. That is
-- deliberate rather than incidental: the window this table has to cover and the
-- currencies it has to cover are properties of what the Warehouse already holds,
-- not constants someone maintains alongside them. A constant would be correct on
-- the day it was written and silently wrong after the next --refresh.
--
-- **Three transforms happen here and nowhere else.** raw.frankfurter_rate holds
-- the response's own values — one row per published date per currency, the number
-- of that currency one euro buys — so this file is where a reader looks for what
-- was done to the numbers.
--
--   1. The base currency gets a row against itself, which the response omits.
--   2. Non-publishing dates are filled forward from the most recent published rate.
--   3. Every ordered pair of currencies is derived from the two EUR rates.
--
-- Each is argued at the line that does it.

INSERT INTO fct_fx_rate (
    rate_date,
    from_currency,
    to_currency,
    fx_rate
)

-- The currencies the Warehouse has to be able to convert between: every currency
-- an Instrument is quoted in, plus the one the source publishes against.
--
-- Read from dim_instrument rather than declared here, so that adding an
-- Instrument in a new currency widens this table by itself. The base is unioned in
-- because it is the pivot every rate below is derived through — it stays reachable
-- even in a universe where nothing happens to be quoted in it, which is what keeps
-- a Reporting Currency of EUR expressible independently of the traded universe.
--
-- Quotation Currency, not the raw one: dim_instrument records GBP for the London
-- listings, and Frankfurter publishes GBP. `GBp` is a minor unit rather than a
-- currency and no rate exists for it — the normalisation that already happened in
-- dim_instrument.sql is what makes this join find one.
WITH currency AS (
    SELECT DISTINCT quotation_currency AS currency FROM dim_instrument
    UNION
    SELECT DISTINCT from_currency FROM raw.frankfurter_rate
),

-- 1. What the source published, against EUR, for the currencies that matter —
--    plus EUR against itself.
--
-- The response carries one entry per *other* currency, so the base is absent from
-- its own rates block. Deriving the missing row here rather than special-casing it
-- three joins later is what lets every pair below be one division with no
-- exceptions: EUR to EUR comes out as 1 by the same arithmetic as every other
-- pair, rather than by a CASE that a reader has to trust.
-- The dates arrive as the strings the response keyed its rates block by, and are
-- cast once here. Unlike the timestamp arithmetic in fct_instrument_price.sql this
-- is a type change and not a reinterpretation: an ECB reference rate is published
-- for a date, in ISO 8601, with no clock and no zone to get wrong.
published AS (
    SELECT
        rate.rate_date::DATE AS rate_date,
        rate.to_currency AS currency,
        rate.fx_rate
    FROM raw.frankfurter_rate AS rate
    JOIN currency ON currency.currency = rate.to_currency

    UNION ALL

    SELECT DISTINCT
        rate.rate_date::DATE AS rate_date,
        rate.from_currency AS currency,
        1.0 AS fx_rate
    FROM raw.frankfurter_rate AS rate
),

-- 2a. Every calendar date the Warehouse needs a rate on.
--
-- The ECB publishes on working days, so weekends and its own holidays are absent
-- from the response entirely. The Glossary settles what this table holds for them:
-- FX Rate is "published on working days only, so a rate for a non-publishing date
-- is the most recent published rate at or before it". Dense over calendar dates is
-- how that definition is stored rather than re-derived by every future metric —
-- and a metric that forgets to re-derive it silently converts a Saturday Position
-- at nothing.
--
-- The end is the later of what the source published and what the Warehouse holds
-- prices for. The two disagree routinely and in both directions: the ECB publishes
-- at 16:00 Central European Time, so a refresh run in the morning has Market
-- Prices for a date the rates have not reached yet.
--
-- The start is the *first published* date, never the first price date. Filling
-- forward needs something at or before a date to fill from, and before the first
-- published rate there is nothing — so a window starting earlier could only
-- fabricate one. FX_WINDOW_LEAD_DAYS in sources.py is what buys the headroom that
-- makes this start early enough; check_warehouse.py --sources reports any Market
-- Price left outside the window rather than this file inventing a rate for it.
--
-- generate_series over dates is DuckDB's; so is the ASOF JOIN below. Both are
-- inside the adapter's directory and therefore licensed by ADR-0002, and both are
-- the kind of name DEBT-009 records that the seam scan cannot yet see.
calendar AS (
    SELECT unnest(generate_series(
        (SELECT min(rate_date) FROM published),
        greatest(
            (SELECT max(rate_date) FROM published),
            (SELECT max(price_date) FROM fct_instrument_price)
        ),
        INTERVAL 1 DAY
    ))::DATE AS rate_date
),

-- 2b. The rate in force for each currency on each of those dates.
--
-- ASOF JOIN is exactly the Glossary's sentence as an operator: for each date on
-- the left it takes the single most recent row on the right at or before it. The
-- alternative — a correlated max() subquery — computes the same thing while
-- reading like an optimisation problem, and this table's whole content is that one
-- definition.
effective AS (
    SELECT
        grid.rate_date,
        grid.currency,
        published.fx_rate
    FROM (SELECT calendar.rate_date, currency.currency
          FROM calendar CROSS JOIN currency) AS grid
    ASOF JOIN published
        ON published.currency = grid.currency
       AND grid.rate_date >= published.rate_date
)

-- 3. Every ordered pair, derived from the two rates against the base.
--
-- Both sides are "currency per 1 EUR" on the same date, so their ratio is the rate
-- between them, and the pair where both sides are the same currency comes out as
-- exactly 1. Storing all pairs rather than the EUR ones alone is a deliberate
-- trade: it is more rows, and it makes a conversion in any future Metric
-- Definition a single lookup instead of a division of two lookups. A division
-- written once here is checkable; the same division repeated in every metric is
-- the kind of arithmetic that produces a plausible wrong number in one of them.
--
-- Frankfurter itself would serve these directly under `base=USD`, computing the
-- same ratio from the same ECB rates. Doing it here keeps the pipeline at one
-- request per source and puts the arithmetic somewhere a reader can see it.
SELECT
    base.rate_date,
    base.currency AS from_currency,
    quote.currency AS to_currency,
    (quote.fx_rate / base.fx_rate)::DECIMAL(18, 8) AS fx_rate

FROM effective AS base
JOIN effective AS quote
    ON quote.rate_date = base.rate_date;
