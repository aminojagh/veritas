"""Check that every data source the Target State assumes is actually obtainable.

Run with:  uv run python .claude/scripts/check_data_availability.py
Refresh:   uv run python .claude/scripts/check_data_availability.py --refresh

This is the executable form of the Sub-step 1.2 gate. It does two things:

1. **Replays the source probes** recorded in `data/snapshots/probe-results.json`
   — which sources answered, which are blocked, what each covers. `--refresh`
   re-hits every source live and rewrites that file.
2. **Re-runs the join spike for real, every time** — real FX Rates + real Market
   Prices + seeded synthetic Trades, joined, with each Section-C distinction
   computed. This is the load-bearing claim of the data check, so it is executed
   rather than replayed.

Default mode is offline and deterministic: it reads committed snapshots, so the
numbers below reproduce exactly on any machine, whether or not the upstream
sources are alive. That property is the point — see DEBT-002.

Exit code is non-zero if any source is missing or any distinction collapses.
"""

import argparse
import datetime as dt
import json
import random
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOTS = REPO_ROOT / "data" / "snapshots"
RESULTS = SNAPSHOTS / "probe-results.json"

REPORTING_CURRENCY = "EUR"
SETTLEMENT_LAG_DAYS = 2  # T+2
SPIKE_SEED = 20260803

# One descriptive User-Agent for every source. This is not politeness: Frankfurter
# sits behind Cloudflare and returns HTTP 403 to the default `Python-urllib/3.x`
# agent while serving the identical request under any named agent. Sending a real
# one is a hard requirement of the FX ingestion path, not a nicety. The contact
# address also satisfies the SEC's stated fair-access policy.
USER_AGENT = "veritas/0.1 (capstone research; aminojaghi93@gmail.com)"

FX_URL = (
    "https://api.frankfurter.dev/v1/2025-01-01..2025-12-31"
    "?base=EUR&symbols=USD,GBP,JPY,CHF,AUD,HKD,SGD"
)
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

# Payloads the join spike needs. Snapshotted, so the spike is reproducible offline.
SPIKE_SNAPSHOTS = {
    "frankfurter-2025.json": FX_URL,
    "yahoo-AAPL-5y.json": YAHOO.format(symbol="AAPL") + "?range=5y&interval=1d",
    # period1/period2 pin 2024-01-01..2025-12-31 so the window never drifts.
    "yahoo-SAP.DE-2y.json":
        YAHOO.format(symbol="SAP.DE") + "?period1=1704067200&period2=1767225600&interval=1d",
    "yahoo-VOD.L-2y.json":
        YAHOO.format(symbol="VOD.L") + "?period1=1704067200&period2=1767225600&interval=1d",
}

# Sources probed for reachability and shape only — nothing downstream reads them yet.
REFERENCE_PROBES = [
    ("Frankfurter — FX Rates", "https://api.frankfurter.dev/v1/currencies", "ok"),
    ("NASDAQ Trader — symbol directory",
     "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt", "ok"),
    ("SEC — company_tickers", "https://www.sec.gov/files/company_tickers.json", "ok"),
    ("Stooq — daily CSV",
     "https://stooq.com/q/d/l/?s=aapl.us&d1=20250101&d2=20251231&i=d", "blocked"),
]

# Instrument types the Target State needs Market Prices for, probed under --refresh.
COVERAGE_SYMBOLS = [
    "AAPL", "SAP.DE", "VOD.L", "7203.T",        # equity, four Quotation Currencies
    "SPY", "IWDA.AS", "TLT", "BNDX",            # ETF (incl. bond ETFs)
    "ES=F", "GC=F",                             # future
    "EURUSD=X",                                 # currency pair
    "^GSPC",                                    # index
]
# Excluded from the Instrument definition by ruling R1 — probed to keep the
# evidence live, since the exclusion rests on them staying unobtainable.
EXCLUDED_PROBES = [
    ("option chain (AAPL)", "https://query1.finance.yahoo.com/v7/finance/options/AAPL"),
    ("single bond by ISIN", YAHOO.format(symbol="US912810TW33") + "?range=5d&interval=1d"),
    ("single bond by CUSIP", YAHOO.format(symbol="912810TW3") + "?range=5d&interval=1d"),
]

problems: list[str] = []


# --- fetching ---------------------------------------------------------------


def fetch(url: str) -> tuple[int, bytes]:
    """Return (status, body). Never raises on HTTP error — the status is the finding."""
    request = urllib.request.Request(url)
    request.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except OSError as error:
        return 0, str(error).encode()


def refresh() -> dict:
    """Hit every source live, rewrite the snapshots and the probe record."""
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    probes = []

    for name, url, expected in REFERENCE_PROBES:
        status, body = fetch(url)
        # Stooq answers 200 with a JavaScript anti-bot page — status alone lies.
        blocked = b"requires JavaScript" in body[:1000]
        verdict = "blocked" if blocked else ("ok" if status == 200 else "absent")
        probes.append(
            dict(name=name, url=url, http=status, bytes=len(body), verdict=verdict,
                 expected=expected, head=body[:120].decode("utf-8", "replace"))
        )
        print(f"  probe   {name:36} HTTP {status} {len(body):>8}B  {verdict}")

    coverage = []
    for symbol in COVERAGE_SYMBOLS:
        status, body = fetch(YAHOO.format(symbol=symbol) + "?range=1mo&interval=1d")
        entry = dict(symbol=symbol, http=status)
        if status == 200:
            result = json.loads(body)["chart"]["result"][0]
            meta = result["meta"]
            entry |= dict(
                instrument_type=meta.get("instrumentType"),
                quotation_currency=meta.get("currency"),
                exchange=meta.get("fullExchangeName"),
                bars=len(result.get("timestamp", [])),
            )
        coverage.append(entry)
        print(f"  cover   {symbol:36} HTTP {status}  {entry.get('instrument_type', '-')}")

    excluded = []
    for name, url in EXCLUDED_PROBES:
        status, _ = fetch(url)
        excluded.append(dict(name=name, url=url, http=status, obtainable=status == 200))
        print(f"  excl    {name:36} HTTP {status}")

    for filename, url in SPIKE_SNAPSHOTS.items():
        status, body = fetch(url)
        if status != 200:
            problems.append(f"snapshot {filename}: HTTP {status}")
            continue
        (SNAPSHOTS / filename).write_bytes(body)
        print(f"  snap    {filename:36} {len(body):>8}B")

    record = dict(
        checked=dt.date.today().isoformat(),
        probes=probes,
        coverage=coverage,
        excluded=excluded,
    )
    RESULTS.write_text(json.dumps(record, indent=2) + "\n")
    return record


# --- replay -----------------------------------------------------------------


def replay() -> dict:
    """Report the recorded probe outcomes without touching the network."""
    if not RESULTS.exists():
        problems.append(f"no probe record at {RESULTS.relative_to(REPO_ROOT)} — run --refresh")
        return {}
    record = json.loads(RESULTS.read_text())
    print(f"  probes recorded {record['checked']} (replayed offline; --refresh to re-hit)\n")

    for probe in record["probes"]:
        mark = "ok " if probe["verdict"] == probe["expected"] else "!! "
        print(f"  {mark} {probe['name']:36} HTTP {probe['http']} {probe['bytes']:>8}B  {probe['verdict']}")
        if probe["verdict"] != probe["expected"]:
            problems.append(f"{probe['name']}: recorded {probe['verdict']}, expected {probe['expected']}")

    print()
    for entry in record["coverage"]:
        if entry["http"] != 200:
            problems.append(f"coverage {entry['symbol']}: HTTP {entry['http']}")
            continue
        print(f"  ok  {entry['symbol']:10} {entry['instrument_type']:9} "
              f"{entry['quotation_currency']:4} {entry['exchange']:12} bars={entry['bars']}")

    print()
    for entry in record["excluded"]:
        state = "OBTAINABLE — revisit R1" if entry["obtainable"] else "not obtainable (R1 holds)"
        print(f"  --  {entry['name']:36} HTTP {entry['http']}  {state}")
        if entry["obtainable"]:
            problems.append(f"{entry['name']} is now obtainable — ruling R1 should be revisited")

    return record


# --- the join spike ---------------------------------------------------------


def load_fx_rate() -> dict[dt.date, dict[str, float]]:
    """FX Rates keyed by date. Frankfurter is EUR-based: rate[date][CCY] = CCY per 1 EUR."""
    raw = json.loads((SNAPSHOTS / "frankfurter-2025.json").read_text())["rates"]
    return {dt.date.fromisoformat(day): rates for day, rates in raw.items()}


def load_market_price(filename: str) -> tuple[dict[dt.date, float], str]:
    """Return (Market Price by date, Quotation Currency).

    Uses unadjusted `close`, never `adjclose`: a Position is marked at the price
    that actually traded that day. Normalises pence-quoted instruments (`GBp`)
    to major units, without which every downstream figure is 100x too large.
    """
    result = json.loads((SNAPSHOTS / filename).read_text())["chart"]["result"][0]
    quotation_currency = result["meta"]["currency"]
    closes = result["indicators"]["quote"][0]["close"]
    price = {
        dt.datetime.fromtimestamp(stamp, dt.UTC).date(): close
        for stamp, close in zip(result["timestamp"], closes)
        if close is not None
    }
    if quotation_currency == "GBp":
        price = {day: close / 100 for day, close in price.items()}
        quotation_currency = "GBP"
    return price, quotation_currency


def check_traps() -> None:
    """The two ways real market data produces a plausible wrong number."""
    result = json.loads((SNAPSHOTS / "yahoo-AAPL-5y.json").read_text())["chart"]["result"][0]
    close = result["indicators"]["quote"][0]["close"]
    adjusted_close = result["indicators"]["adjclose"][0]["adjclose"]
    differing = sum(1 for c, a in zip(close, adjusted_close) if abs(c - a) > 1e-6)
    share = 100 * differing / len(close)
    print(f"  Adjusted Close vs Market Price : differ on {differing}/{len(close)} bars ({share:.1f}%)")
    if share < 50:
        problems.append("close/adjclose divergence collapsed — the Section-C row overstates the trap")

    raw_currency = json.loads(
        (SNAPSHOTS / "yahoo-VOD.L-2y.json").read_text()
    )["chart"]["result"][0]["meta"]["currency"]
    print(f"  Quotation Currency (VOD.L)     : {raw_currency} — normalised to GBP on load")
    if raw_currency != "GBp":
        problems.append(f"VOD.L now quotes {raw_currency}, not GBp — the minor-unit trap has moved")


def run_join_spike() -> None:
    """Join real FX Rates + real Market Prices + synthetic Trades, and prove that
    every Section-C distinction produces a materially different number."""
    fx_rate = load_fx_rate()
    fx_dates = sorted(fx_rate)

    def to_reporting_currency(amount: float, currency: str, on: dt.date) -> float:
        """ECB publishes on working days only, so fall back to the most recent
        published FX Rate at or before `on` — the warehouse's fill-forward rule."""
        if currency == REPORTING_CURRENCY:
            return amount
        day = max((d for d in fx_dates if d <= on), default=fx_dates[0])
        return amount / fx_rate[day][currency]

    instrument = {
        "AAPL": load_market_price("yahoo-AAPL-5y.json"),
        "SAP.DE": load_market_price("yahoo-SAP.DE-2y.json"),
        "VOD.L": load_market_price("yahoo-VOD.L-2y.json"),
    }

    # One Client holding three Accounts, so Client and Account cannot be conflated.
    account = {
        "ACC-01": dict(client="CLI-A", introduced=True),
        "ACC-02": dict(client="CLI-A", introduced=False),
        "ACC-03": dict(client="CLI-A", introduced=False),
        "ACC-04": dict(client="CLI-B", introduced=True),
        "ACC-05": dict(client="CLI-C", introduced=False),
    }

    def next_settlement_date(trade_date: dt.date) -> dt.date:
        settlement_date = trade_date
        for _ in range(SETTLEMENT_LAG_DAYS):
            settlement_date += dt.timedelta(days=1)
            while settlement_date.weekday() >= 5:
                settlement_date += dt.timedelta(days=1)
        return settlement_date

    # A window straddling the Q1/Q2 boundary, so T+2 pushes late-March Trades
    # into April cash and the accrual/cash split becomes visible.
    rng = random.Random(SPIKE_SEED)
    window = [d for d in fx_dates if dt.date(2025, 3, 20) <= d <= dt.date(2025, 4, 10)]

    trade = []
    for trade_date in window:
        for _ in range(rng.randint(3, 6)):
            symbol = rng.choice(list(instrument))
            market_price, quotation_currency = instrument[symbol]
            if trade_date not in market_price:
                continue
            account_id = rng.choice(list(account))
            quantity = rng.choice([-1, 1]) * rng.randint(50, 500)
            price = market_price[trade_date]
            traded_notional = abs(quantity) * price
            commission = traded_notional * 0.0012   # 12 bps — broker income
            fee = traded_notional * 0.0003          # pass-through, not earned
            rebate = commission * 0.40 if account[account_id]["introduced"] else 0.0
            trade.append(dict(
                trade_date=trade_date,
                settlement_date=next_settlement_date(trade_date),
                account_id=account_id,
                symbol=symbol,
                quotation_currency=quotation_currency,
                quantity=quantity,
                market_price=price,
                traded_notional=traded_notional,
                commission=commission,
                fee=fee,
                rebate=rebate,
            ))

    quarter_end = dt.date(2025, 3, 31)
    in_quarter = [t for t in trade if t["trade_date"] <= quarter_end]

    def total(field_fn, date_key: str) -> float:
        return sum(
            to_reporting_currency(field_fn(t), t["quotation_currency"], t[date_key])
            for t in in_quarter
        )

    gross_revenue = total(lambda t: t["commission"], "trade_date")
    net_revenue = total(lambda t: t["commission"] - t["rebate"] - t["fee"], "trade_date")
    # Accounting Movement recognises Commission on Trade Date (earned);
    # Cash Movement collects it on Settlement Date (money moves).
    accrual_basis = gross_revenue
    cash_basis = sum(
        to_reporting_currency(t["commission"], t["quotation_currency"], t["settlement_date"])
        for t in trade if t["settlement_date"] <= quarter_end
    )
    gross_revenue_fx_on_settlement = total(lambda t: t["commission"], "settlement_date")
    traded_notional = total(lambda t: t["traded_notional"], "trade_date")
    trade_count = float(len(in_quarter))

    print(f"  Trades generated: {len(trade)}  (Q1 2025: {len(in_quarter)})")
    print(f"  Clients: {len({a['client'] for a in account.values()})}  Accounts: {len(account)}")
    print(f"  Reporting Currency: {REPORTING_CURRENCY}\n")

    distinctions = [
        ("Gross Revenue", gross_revenue, "Net Revenue", net_revenue, 1.0),
        ("Accounting Movement (accrual)", accrual_basis, "Cash Movement (cash)", cash_basis, 1.0),
        ("FX on Trade Date", gross_revenue, "FX on Settlement Date",
         gross_revenue_fx_on_settlement, 0.0),
        ("Traded Notional", traded_notional, "Trade Count", trade_count, 1.0),
    ]
    for left_name, left, right_name, right, min_delta_pct in distinctions:
        delta = abs(left - right) / left * 100 if left else 0.0
        print(f"    {left_name:32} {left:14,.2f}")
        print(f"    {right_name:32} {right:14,.2f}   Δ {delta:6.2f}%\n")
        if delta <= min_delta_pct:
            problems.append(
                f"{left_name} vs {right_name}: Δ {delta:.2f}% — distinction has collapsed"
            )

    # DEBT-004: the FX-date distinction is real but small in a calm window.
    fx_delta = abs(gross_revenue_fx_on_settlement - gross_revenue) / gross_revenue * 100
    if fx_delta < 1.0:
        print(f"  NOTE  FX-date distinction is only {fx_delta:.2f}% — too small to be a "
              f"reliable evaluation signal. See DEBT-004.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true",
                        help="re-hit every source live and rewrite the snapshots")
    args = parser.parse_args()

    print("== sources ==\n")
    if args.refresh:
        refresh()
    else:
        replay()

    missing = [name for name in SPIKE_SNAPSHOTS if not (SNAPSHOTS / name).exists()]
    if missing:
        problems.extend(f"missing snapshot: {name} — run --refresh" for name in missing)
    else:
        print("\n== wrong-number traps ==\n")
        check_traps()

        print("\n== join spike: real FX + real Market Prices + synthetic Trades ==\n")
        run_join_spike()

    print()
    if problems:
        print(f"FAIL — {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("PASS — every source is obtainable and every distinction separates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
