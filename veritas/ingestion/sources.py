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

# Two years of daily bars. The range matters to Sub-step 2.3 rather than to this
# one — 2.2 reads only the `meta` block of the response — but the snapshot is
# fetched once and both Sub-steps read the same file, so the window is set here.
# Two years covers the whole of the 2025 window `frankfurter-2025.json` holds,
# which is what lets a Position be converted on the date it was held.
YAHOO_RANGE = "2y"
YAHOO_INTERVAL = "1d"

# Both NASDAQ Trader files end with a provenance line rather than a record:
#   File Creation Time: 0810202606:00|||||||
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
    named only the first: three of the sixteen traded Instruments are NYSE or
    NYSE Arca listings (JNJ, SPY) that simply do not appear in `nasdaqlisted.txt`.
    They are one directory, published together, and are treated as one source.

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
    rather than funds, so two of the traded exchange-traded funds are absent from
    it — the star build left-joins for exactly that reason.
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
    `indicators` blocks are the Market Price series, and they are Sub-step 2.3's
    to load — one file, two halves, one Sub-step each.
    """
    for symbol in TRADED_INSTRUMENTS:
        url = (
            YAHOO_CHART_URL.format(symbol=symbol)
            + f"?range={YAHOO_RANGE}&interval={YAHOO_INTERVAL}"
        )
        body = read_source(f"yahoo-chart-{symbol}.json", url, refresh=refresh)
        meta = json.loads(body)["chart"]["result"][0]["meta"]
        yield {
            "instrument_symbol": meta.get("symbol", symbol),
            "quotation_currency": meta.get("currency"),
            "source_instrument_type": meta.get("instrumentType"),
            "exchange_name": meta.get("exchangeName"),
            "long_name": meta.get("longName") or meta.get("shortName"),
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
