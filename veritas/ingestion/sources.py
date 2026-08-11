"""The real reference sources, parsed into records for dlt to land in `raw`.

Every function here is a plain generator over already-read bytes. None of them
opens a socket — `snapshots.read_source` does that, once — and none of them
touches the Warehouse. That leaves them ordinary functions over ordinary data,
which is the point: the only thing dlt is asked to do is extract-and-load.

**What "raw" means here, precisely.** Values are landed exactly as the source
gave them: `GBp` stays `GBp`, the SEC's shouting stays shouted, and no row is
dropped for being inconvenient. Field *names* are ours, because a pipe-delimited
file has to be given column names by somebody and two of these sources spell the
same concept differently (`Symbol` versus `ACT Symbol`). Renaming a field is not
transforming a value, and the values are where wrong numbers come from. ADR-0004
records this boundary.
"""

import datetime as dt
import json
from collections.abc import Iterator

from veritas.ingestion.snapshots import read_source
from veritas.ingestion.universe import (
    MINOR_UNIT_CURRENCIES,
    TRADED_INSTRUMENTS,
    YAHOO_INSTRUMENT_TYPES,
)

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
NASDAQ_OTHER_URL = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
FRANKFURTER_URL = "https://api.frankfurter.dev/v1/{start}..{end}?base=EUR"

# How far back a refresh reaches. One number, used twice: Yahoo takes it as a
# relative range and Frankfurter needs two explicit dates, so writing it once is
# what keeps the two windows from drifting apart across refreshes. They must not:
# a Market Price on a date with no FX Rate is a Position that cannot be converted
# to the Reporting Currency, which is the failure `fct_fx_rate` exists to prevent.
PRICE_WINDOW_YEARS = 2

YAHOO_RANGE = f"{PRICE_WINDOW_YEARS}y"
YAHOO_INTERVAL = "1d"

# Extra days on the *front* of the FX window only. Two reasons, both about the
# start: 365-day years drift against Yahoo's calendar-aware "2y", and the European
# Central Bank (ECB) does not publish on the day a window happens to open. A rate
# is filled forward from the most recent published one, so a window that starts
# late leaves the earliest Market Prices with nothing at or before them to fill
# from — while a window that starts early costs a few unused rows.
FX_WINDOW_LEAD_DAYS = 10

# Both NASDAQ Trader files end with a provenance line rather than a record:
#   File Creation Time: <mmddyyyyhh:mm>|||||||
# Parsing it as a symbol produces an Instrument called "File Creation Time".
NASDAQ_TRAILER = "File Creation Time:"


def _delimited_rows(body: bytes) -> Iterator[dict[str, str]]:
    """Rows of a NASDAQ Trader pipe-delimited file, keyed by its header line."""
    lines = body.decode("utf-8").splitlines()
    if not lines:
        return
    header = lines[0].split("|")
    for line in lines[1:]:
        if not line.strip() or line.startswith(NASDAQ_TRAILER):
            continue
        cells = line.split("|")
        if len(cells) != len(header):
            continue
        yield dict(zip(header, cells))


def nasdaq_symbols(*, refresh: bool) -> Iterator[dict[str, object]]:
    """The NASDAQ Trader symbol directory — both halves of it.

    `nasdaqlisted.txt` carries NASDAQ-listed securities and `otherlisted.txt`
    carries the rest of the US tape. Both are needed and the plan's shorthand
    named only the first: a traded Instrument listed on NYSE or NYSE Arca (JNJ,
    SPY) simply does not appear in `nasdaqlisted.txt`. They are one directory,
    published together, and are treated as one source.

    The two files disagree on what to call the symbol column — `Symbol` against
    `ACT Symbol` — which is exactly the synonym problem Non-Negotiable #1 is
    about, arriving from outside. It is resolved once, here, to the registered
    term: `Instrument Symbol`.
    """
    for url, symbol_column, listing in (
        (NASDAQ_LISTED_URL, "Symbol", "nasdaqlisted"),
        (NASDAQ_OTHER_URL, "ACT Symbol", "otherlisted"),
    ):
        body = read_source(f"nasdaq-{listing}.txt", url, refresh=refresh)
        for row in _delimited_rows(body):
            symbol = row.get(symbol_column, "").strip()
            if not symbol:
                continue
            yield {
                "instrument_symbol": symbol,
                "security_name": row.get("Security Name", "").strip(),
                # 'Y' for an exchange-traded fund. This is the flag
                # data-availability.md picked the source for: it populates the
                # instrument-type axis without anyone hand-labelling a row.
                "is_etf": row.get("ETF", "").strip(),
                "is_test_issue": row.get("Test Issue", "").strip(),
                "listing_file": listing,
            }


def sec_registrants(*, refresh: bool) -> Iterator[dict[str, object]]:
    """The Securities and Exchange Commission (SEC) ticker-to-registrant file.

    Gives the name a security is *registered* under, which is the most
    authoritative name available for a US listing. It covers operating companies
    rather than funds, so a traded exchange-traded fund can be absent from it —
    the star build left-joins for exactly that reason.
    """
    body = read_source("sec-company-tickers.json", SEC_TICKERS_URL, refresh=refresh)
    for entry in json.loads(body).values():
        ticker = str(entry.get("ticker", "")).strip()
        if not ticker:
            continue
        yield {
            "instrument_symbol": ticker,
            "registered_name": str(entry.get("title", "")).strip(),
            # The SEC's Central Index Key. It reaches `raw` because it is what
            # the source is keyed on and dropping a key on the way in is how a
            # later question becomes unanswerable; it reaches no star-schema
            # column, because dim_instrument has none and R2's lesson is that
            # inventing one to hold arriving data is how a schema sprawls.
            "central_index_key": entry.get("cik_str"),
        }


def yahoo_chart(symbol: str, *, refresh: bool) -> dict[str, object]:
    """One symbol's chart response, unwrapped to the single result it contains.

    Two resources read this — `yahoo_instruments` takes the `meta` block and
    `yahoo_prices` takes the bars — and they must see the *same* response, not two
    fetched a minute apart. `snapshots.read_source` guarantees that by caching a
    source's bytes for the run; this function is what makes both of them ask for
    the file by the same name.
    """
    url = (
        YAHOO_CHART_URL.format(symbol=symbol)
        + f"?range={YAHOO_RANGE}&interval={YAHOO_INTERVAL}"
    )
    body = read_source(f"yahoo-chart-{symbol}.json", url, refresh=refresh)
    return json.loads(body)["chart"]["result"][0]


def yahoo_instruments(*, refresh: bool) -> Iterator[dict[str, object]]:
    """Per-symbol metadata for the traded Instrument universe.

    **This is the source of `quotation_currency`, and it has to be.** Neither
    NASDAQ Trader file carries a currency column at all — the directory lists US
    securities, which are quoted in dollars implicitly — and the SEC file carries
    only a name and a key. Yahoo's `meta` block is the one place any source in
    this project states the currency an Instrument is quoted in, and it is where
    the literal string `GBp` comes from. Building `dim_instrument` from the two
    reference files alone would leave the currency to be guessed from a symbol
    suffix, and a guessed `GBP` would make both the schema's CHECK and this
    Sub-step's own `--sources` assertion pass without ever meeting the trap they
    exist to catch.

    Only the `meta` block is read here. The same snapshot's `timestamp` and
    `indicators` blocks are the Market Price series, which `yahoo_prices` below
    loads — one file, two halves, one Sub-step each.

    The last four fields are the ones `fct_instrument_price` needs and no other
    table does. They live here, one row per Instrument, rather than repeated on
    every price row, because they are properties of the *response* and of the
    exchange rather than of a bar.
    """
    for symbol in TRADED_INSTRUMENTS:
        result = yahoo_chart(symbol, refresh=refresh)
        meta = result["meta"]
        yield {
            "instrument_symbol": meta.get("symbol", symbol),
            "quotation_currency": meta.get("currency"),
            "source_instrument_type": meta.get("instrumentType"),
            "exchange_name": meta.get("exchangeName"),
            "long_name": meta.get("longName") or meta.get("shortName"),
            # Seconds to add to a bar's timestamp to reach the exchange's own
            # clock. Yahoo spells it `gmtoffset`; the field name here says
            # Coordinated Universal Time (UTC), which is what the offset is from
            # and what the timestamps are in.
            "utc_offset_seconds": meta.get("gmtoffset"),
            # The two halves of "had the session closed when this was fetched?".
            # `regularMarketTime` is the last trade Yahoo had seen;
            # `currentTradingPeriod.regular.end` is when the session it belongs to
            # closes. If the first is below the second, the response was taken
            # mid-session and its final bar is a live price rather than a close.
            "last_market_time": meta.get("regularMarketTime"),
            "current_session_end": (
                meta.get("currentTradingPeriod", {}).get("regular", {}).get("end")
            ),
        }


def yahoo_prices(*, refresh: bool) -> Iterator[dict[str, object]]:
    """The daily Market Price series for the traded Instrument universe.

    The other half of the same snapshots `yahoo_instruments` reads, and the reason
    [DEBT-002](../../.claude/docs/debt-ledger.md) was opened: this is the
    unofficial endpoint every Position mark depends on.

    **`close`, never `adjclose`.** Both series are in the response, side by side
    and the same length, and taking the wrong one is the wrong number
    `check_data_availability.py` measured rather than imagined — they differ on
    most bars for any Instrument that has paid a dividend. The Glossary settles
    which is wanted: `Market Price` is *"the unadjusted closing price at which an
    Instrument traded on a date"*, and `Adjusted Close` is registered as the
    anti-pattern next to it. The field is named `unadjusted_close` here so that a
    reader of `raw` can see which of the two was landed without going back to the
    source.

    Bars are landed exactly as the response gives them — epoch timestamp, a close
    that may be null, no row dropped. Turning a timestamp into a `price_date` and
    a pence quote into pounds happens in `fct_instrument_price.sql`, where every
    other transform in this pipeline lives and where a reader looks for what was
    done to the numbers.
    """
    for symbol in TRADED_INSTRUMENTS:
        result = yahoo_chart(symbol, refresh=refresh)
        symbol_in_response = result["meta"].get("symbol", symbol)
        closes = result["indicators"]["quote"][0]["close"]
        for bar_timestamp, close in zip(result["timestamp"], closes):
            yield {
                "instrument_symbol": symbol_in_response,
                "bar_timestamp": bar_timestamp,
                "unadjusted_close": close,
            }


def frankfurter_rates(*, refresh: bool) -> Iterator[dict[str, object]]:
    """Every European Central Bank (ECB) reference rate Frankfurter publishes.

    **Frankfurter is the only FX Rate source**, which is a rule rather than a
    convenience. Yahoo serves `EURUSD=X` and this pipeline already reads it — as a
    traded Instrument, priced into `fct_instrument_price` like any other. Letting
    it also become an FX Rate would put two numbers for one concept in the
    Warehouse, differing by the spread and by the hour they were sampled, and
    whichever one a metric happened to join to would look equally plausible.

    Two things about the shape, both of which the build script relies on:

      * **The response is EUR-based and the base is not in it.** `rates` holds one
        entry per *other* currency — the number of that currency one euro buys —
        so a row for EUR against itself has to be derived rather than read. That
        derivation is a transform and lives in `fct_fx_rate.sql`.
      * **Only publishing days appear.** The ECB publishes on working days, so
        weekends and its own holidays are simply absent — not present-and-null.
        The Glossary settles what a Warehouse row for such a date is: *"a rate for
        a non-publishing date is the most recent published rate at or before
        it"*, which is again the build script's job.

    Every published currency is landed, not just the ones the Warehouse currently
    needs. Which currencies matter is a question about the traded universe, and it
    is answered in `fct_fx_rate.sql` against `dim_instrument`; landing the whole
    response means adding an Instrument in a new currency does not also require a
    refresh, which would need a network to load a source that is already on disk.
    """
    today = dt.date.today()
    # 365-day years rather than a calendar shift, so that a window opening on
    # 29 February is not an error case. FX_WINDOW_LEAD_DAYS absorbs the drift.
    start = today - dt.timedelta(days=365 * PRICE_WINDOW_YEARS + FX_WINDOW_LEAD_DAYS)
    url = FRANKFURTER_URL.format(start=start.isoformat(), end=today.isoformat())

    # A fixed name rather than one built from the dates. The window moves with
    # every refresh, and a dated filename would leave the previous window's file
    # behind as a second snapshot of the same source that nothing reads and
    # nothing updates.
    response = json.loads(read_source("frankfurter-rates.json", url, refresh=refresh))
    base_currency = response["base"]
    for rate_date, rates in response["rates"].items():
        for currency, rate in rates.items():
            yield {
                "rate_date": rate_date,
                "from_currency": base_currency,
                "to_currency": currency,
                "fx_rate": rate,
            }


def minor_unit_currencies() -> Iterator[dict[str, object]]:
    """The minor-unit map, landed as a table so the star build can join it.

    Not fetched from anywhere — it is our decision, not a source's. It is landed
    rather than written into the build script as a CASE expression so that the
    normalisation is visible in the database, and so Sub-step 2.3 divides prices
    by a factor that lives in the same row as the code it belongs to.
    """
    for minor_unit, mapping in MINOR_UNIT_CURRENCIES.items():
        yield {"minor_unit_currency": minor_unit, **mapping}


def yahoo_instrument_types() -> Iterator[dict[str, object]]:
    """The source-vocabulary-to-Glossary map for instrument_type.

    Landed for the same reason as the minor units: the four values on the right
    are registered domain vocabulary that `dim_instrument`'s CHECK enforces, so
    the translation into them belongs somewhere a reader can see it rather than
    buried in a CASE.
    """
    for source_type, instrument_type in YAHOO_INSTRUMENT_TYPES.items():
        yield {
            "source_instrument_type": source_type,
            "instrument_type": instrument_type,
        }
