"""The seeded simulator — the synthetic half of Ingestion.

The Glossary's `Ingestion` term draws the line this module sits on: *"real FX
Rates, Market Prices and instrument reference data from key-free public sources
... synthetic Trades, Cash Movements and Positions from a seeded simulator.
**Market data real, client activity synthetic — never the reverse.**"* Everything
above this file is real and checked against its source; everything this file
emits is invented. Nothing here fetches anything, and nothing here invents a
price.

**The market data is an input, never a re-derivation.** Every Trade is priced off
a Market Price the Warehouse already holds, every Position is marked at one, and
every currency conversion goes through a real FX Rate. That is why
`read_market_data` reads the three tables Sub-steps 2.2–2.4 built rather than the
snapshots they were built from: re-deriving a price here would put a second
implementation of `fct_instrument_price.sql`'s transforms in the repository, and
two implementations of one transform is how the two quietly disagree.

Two halves, deliberately separated:

  * `read_market_data` touches the Warehouse, through the adapter, and returns
    plain Python. It is the only part of this module that knows a database
    exists, and its SQL is standard — no DuckDB-specific function name appears
    outside `veritas/warehouse/`, which is the commitment ADR-0002 makes and
    [DEBT-009] records as only half-checked.
  * `simulate` is a **pure function** of that data and a seed. Same inputs, same
    rows, every time — which is what makes the determinism check in
    `check_warehouse.py --distinctions` a check rather than a hope.

**What it writes, and what writes it.** `simulate` returns rows per `raw` table
and nothing more. dlt lands them and the hand-authored SQL in
`veritas/warehouse/builds/` builds the star tables from them — the same resource
plus build script that every real source uses, and the reason no component
outside the adapter emits star-schema SQL.

**What the shape is for.** Sub-step 2.5's bar is that *every Section C
distinction is a different number*, so the generation is not "plausible activity"
but activity chosen to separate pairs that collapse into each other when a
simulator is careless:

  Gross vs Net Revenue        rebates on a share of Accounts, and pass-through
                              fees on all of them
  Cash vs Accounting          charges are earned on Trade Date and collected on
                              Settlement Date, so any period boundary between
                              them splits the two
  Trade vs Settlement Date    T+2 on the Instrument's own trading calendar, and
                              the cash leg converts at the *settlement* date's
                              FX Rate
  Realised vs Unrealised      Positions are both closed and held open at the end
  Position Change vs Trade    a handful of transfers move a Position with no
                              Trade behind them (R14)
  Execution vs Market Price   every fill is jittered off the close, so a notional
                              at the close is a different number
  Cost Basis vs Execution     Positions are built over many Trades, so the last
                              fill is not what the holding cost
  Client vs Account           Clients hold one to three Accounts each
  Quotation vs Reporting      Accounts are billed in currencies that are not the
                              ones their Instruments are quoted in

Corporate actions are **not** simulated — R14, recorded as
[EXT-007](../../.claude/docs/extension-register.md). The assumption behind that
exclusion is checked rather than asserted: `--sources` fails the run if any loaded
price series contains a move large enough to be a split.
"""

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from random import Random

from veritas.warehouse import WarehouseAdapter

# The seed. Arbitrary — it is the date this simulator was written — and the only
# thing that has to stay fixed: changing it changes every row downstream, which is
# a regeneration of the whole client side rather than a tweak.
SEED = 20260811

# Every monetary column in the star schema is DECIMAL(18, 6), so every amount this
# module produces is quantised to six places before it leaves. Doing it here rather
# than letting the cast in the build script do it means the number this module
# reasoned about — a Cost Basis it subtracts from, a balance it accumulates — is
# the number the Warehouse stores, and not a rounding away from it.
MONEY = Decimal("0.000001")

# Settlement is two trading days after the Trade, on the Instrument's *own*
# calendar. T+2 is the convention most of these markets actually run, and the
# reason it matters here is Section C rather than realism: it is what puts a period
# boundary between the date a charge is earned and the date it is collected, and
# what makes Trade Date and Settlement Date select different FX Rates.
SETTLEMENT_TRADING_DAYS = 2

# The Clients, and the region each is sited in. Fictional, and deliberately not
# near any real firm's name. The regions are the "by region" Dimension
# Definition's own values — EU · UK · APAC — with four Clients each, because a
# region holding one Client makes a metric sliced by region a report on one
# Client.
CLIENTS = (
    ("Northwind Asset Management", "EU"),
    ("Calder Bay Partners", "UK"),
    ("Meridian Wealth Trust", "APAC"),
    ("Larkspur Holdings", "EU"),
    ("Fen and Pike Advisers", "UK"),
    ("Blue Kestrel Capital", "APAC"),
    ("Orchard Row Foundation", "EU"),
    ("Saltmarsh Investments", "UK"),
    ("Vireo Family Office", "APAC"),
    ("Tolvane Pension Fund", "EU"),
    ("Kirwan Brothers", "UK"),
    ("Hollowmere Advisers", "APAC"),
)

# The currency an Account is billed in, by its Client's region — the Denomination
# Currency, which is not the Quotation Currency of anything it trades except by
# coincidence. Every value here is one of the four the Warehouse holds FX Rates
# for; a fifth would leave its Gross Revenue unable to reach a Reporting Currency,
# and `check_warehouse.py --distinctions` fails the run if one appears.
REGION_CURRENCY = {"EU": "EUR", "UK": "GBP", "APAC": "JPY"}

# Every fourth Account is billed in USD regardless of its Client's region, and a
# share of Accounts carry a second billing currency. Both exist so that
# `fct_balance_snapshot`'s (date, account, currency) grain is exercised rather than
# degenerate, and so the region a Client sits in never *determines* the currency
# its revenue arrives in — a coupling that would make "revenue by region" and
# "revenue by currency" the same question.
GLOBAL_ACCOUNT_EVERY = 4
SECOND_CURRENCY_SHARE = Decimal("0.40")

# What an Account trades. Fewer than four Instruments makes an Account's P&L one
# security's story; more than eight and every Account looks like the index.
MIN_INSTRUMENTS_PER_ACCOUNT = 4
MAX_INSTRUMENTS_PER_ACCOUNT = 8

# Trades per Account over the whole window. The window is two years, so this is
# an Account trading roughly weekly — thin enough that a Position is genuinely
# held between Trades rather than churned, which is what leaves Unrealised P&L
# something to be unrealised about.
MIN_TRADES_PER_ACCOUNT = 40
MAX_TRADES_PER_ACCOUNT = 90

# The size of a Trade, in euro, before conversion into the Instrument's Quotation
# Currency. Expressed in one currency and converted through a real FX Rate so that
# a Tokyo Trade and a New York Trade are comparable in size — the alternative,
# picking a quantity directly, makes every JPY Position a hundred times the
# notional of a USD one for no reason a reader could defend.
MIN_TRADE_NOTIONAL_EUR = Decimal("20000")
MAX_TRADE_NOTIONAL_EUR = Decimal("250000")
TRADE_NOTIONAL_STEP = Decimal("1000")

# How far an Execution Price may sit from that date's Market Price. Section C:
# *"a Trade fills at whatever the market gave it at that moment, which is not the
# close except by coincidence"*. The band is deliberately narrow — this is
# intraday drift, not a different price — and deliberately never zero, so
# Traded Notional at the close is a different number on every Trade rather than on
# most of them.
MIN_EXECUTION_DRIFT = Decimal("0.0002")
MAX_EXECUTION_DRIFT = Decimal("0.0060")
EXECUTION_DRIFT_STEP = Decimal("0.0001")

# What the broker charges, as a share of notional, per Account. A basis point is
# one hundredth of a percent, so this is 4–14 basis points — the range a real
# broker's tiers span, and wide enough that Accounts differ from each other rather
# than scaling.
MIN_COMMISSION_RATE = Decimal("0.0004")
MAX_COMMISSION_RATE = Decimal("0.0014")
COMMISSION_RATE_STEP = Decimal("0.0001")

# The pass-through Fee, as a share of Commission. Charged to every Account: it is
# a third-party cost — exchange, clearing, regulatory — that the broker collects
# and does not keep, which is exactly why Net Revenue subtracts it.
MIN_FEE_SHARE = Decimal("0.08")
MAX_FEE_SHARE = Decimal("0.22")
FEE_SHARE_STEP = Decimal("0.01")

# The Rebate, as a share of Commission, for the Accounts that have one. Roughly
# half of them do — introduced by a partner who takes a cut. Section C's first row
# is the reason this is large: *"Rebates to introducing partners can be a large
# share of Commission. Reporting gross as net overstates what the business
# keeps."* A rebate of a few percent would make that row true and unmeasurable.
REBATED_ACCOUNT_SHARE = Decimal("0.55")
MIN_REBATE_SHARE = Decimal("0.25")
MAX_REBATE_SHARE = Decimal("0.45")
REBATE_SHARE_STEP = Decimal("0.01")

# Trading behaviour. An Account with no Position in an Instrument can only buy; one
# holding a Position sells with this probability, and a sale closes the whole
# Position rather than part of it with the second. Both matter for one reason: a
# Position that is never closed produces no Realised P&L, and a book where every
# Position is closed produces no Unrealised P&L. `--distinctions` fails if either
# comes out empty.
SELL_PROBABILITY = Decimal("0.45")
FULL_CLOSE_PROBABILITY = Decimal("0.35")
MIN_PARTIAL_SELL_SHARE = Decimal("0.25")
MAX_PARTIAL_SELL_SHARE = Decimal("0.75")
SELL_SHARE_STEP = Decimal("0.05")

# The lot an Instrument trades in, by type. Nobody trades 86,431 units of a
# currency pair, and a future is a whole number of contracts. Rounding to a lot is
# what keeps a generated quantity from reading as a random number with six decimal
# places attached.
LOT_SIZE = {
    "currency pair": Decimal("1000"),
    "future": Decimal("1"),
    "equity": Decimal("1"),
    "ETF": Decimal("1"),
}

# Transfers — Positions that move without a Trade behind them. R14 settles that
# the simulator emits these and not corporate actions, and the Section C row they
# exist for is `Position Change` against `Trade`: *"Positions also change through
# transfers and corporate actions. Deriving position change from trades alone
# silently loses those."* Three is a handful: enough that the check has something
# to find, few enough that a reader can follow every one of them.
TRANSFERS_IN = 2
TRANSFERS_OUT = 1
MIN_TRANSFER_SHARE = Decimal("0.30")
MAX_TRANSFER_SHARE = Decimal("0.80")
TRANSFER_SHARE_STEP = Decimal("0.05")

# Cash. The opening deposit is computed rather than picked — see `_cash_rows` —
# and these are the deposits and withdrawals that happen afterwards, so that
# `fct_cash_movement` holds movements with no Trade behind them and
# `fct_balance_snapshot` is not simply a function of trading.
MIN_CASH_EVENTS = 2
MAX_CASH_EVENTS = 5
WITHDRAWAL_PROBABILITY = Decimal("0.5")
WITHDRAWAL_SHARE = Decimal("0.10")
DEPOSIT_SHARE = Decimal("0.25")

# The buffer on the opening deposit, above the largest shortfall the Account's own
# activity would otherwise run. It is what keeps a Cash Balance from being a
# negative number for reasons nobody chose.
OPENING_DEPOSIT_BUFFER = Decimal("1.25")


def money(value: Decimal) -> Decimal:
    """Quantise to the six decimal places every monetary column stores."""
    return value.quantize(MONEY)


@dataclass(frozen=True)
class Instrument:
    """One row of `dim_instrument`, as the simulator needs it."""

    instrument_id: int
    instrument_symbol: str
    instrument_type: str
    quotation_currency: str


@dataclass(frozen=True)
class MarketData:
    """Everything real that the simulation is built on top of.

    Read once, through the adapter, and then never touched again — `simulate` is
    a function of this object and a seed, so a second run over the same Warehouse
    produces the same rows.
    """

    instruments: tuple[Instrument, ...]
    # (instrument_id, date) -> that date's Market Price, in the Instrument's own
    # Quotation Currency.
    prices: dict[tuple[int, dt.date], Decimal]
    # instrument_id -> every date the Warehouse holds a Market Price for it, in
    # order. Its own exchange's calendar, so a Tokyo holiday is absent here and
    # present for a New York listing.
    trading_dates: dict[int, tuple[dt.date, ...]]
    # The dates **every** Instrument has a Market Price on — see `snapshot_dates`
    # in `read_market_data` for why this and not the union.
    snapshot_dates: tuple[dt.date, ...]
    # (date, from_currency, to_currency) -> FX Rate. Dense over calendar dates,
    # because `fct_fx_rate` fills forward across weekends and ECB holidays.
    fx_rates: dict[tuple[dt.date, str, str], Decimal]
    last_rate_date: dt.date

    def price(self, instrument_id: int, date: dt.date) -> Decimal:
        """That date's Market Price, or an error that says why there is none.

        A missing price is almost always one thing — the Snapshot calendar and the
        Instrument's own trading calendar have come apart, which is what happens
        the moment `snapshot_dates` is widened from the dates *every* Instrument
        has a price to the dates *some* Instrument does. A bare `KeyError` on a
        tuple leaves the next person to work that out from the traceback.
        """
        if (instrument_id, date) not in self.prices:
            raise KeyError(
                f"the Warehouse holds no Market Price for instrument_id "
                f"{instrument_id} on {date}. Its exchange did not trade that day, "
                f"so a Position in it cannot be marked and a Trade in it cannot be "
                f"priced — see `snapshot_dates` in read_market_data for why the "
                f"Snapshot calendar is the dates every Instrument has a price"
            )
        return self.prices[(instrument_id, date)]

    def convert(
        self, amount: Decimal, from_currency: str, to_currency: str, date: dt.date
    ) -> Decimal:
        """Convert an amount between two currencies at that date's FX Rate.

        A missing rate raises rather than falling back to the previous date. The
        fill-forward already happened in `fct_fx_rate.sql`, so a gap here is a
        window that does not cover what the simulation asked for, and silently
        using a neighbouring day's rate would hide exactly the mismatch the FX
        coverage assertion exists to catch.
        """
        if from_currency == to_currency:
            return money(amount)
        if (date, from_currency, to_currency) not in self.fx_rates:
            raise KeyError(
                f"the Warehouse holds no FX Rate from {from_currency} to "
                f"{to_currency} on {date}. Either the date is outside the window "
                f"fct_fx_rate covers, or one of the two currencies is not one the "
                f"traded universe is quoted in"
            )
        return money(amount * self.fx_rates[(date, from_currency, to_currency)])


@dataclass(frozen=True)
class Account:
    """An Account and everything the simulator decided about it up front."""

    account_id: int
    client_id: int
    account_name: str
    # One or two. The first is the Account's own, and the one it opens with.
    denomination_currencies: tuple[str, ...]
    instruments: tuple[Instrument, ...]
    commission_rate: Decimal
    fee_share: Decimal
    # Zero for an Account no partner introduced.
    rebate_share: Decimal
    trade_count: int


def read_market_data(warehouse: WarehouseAdapter) -> MarketData:
    """Read the three real star tables the simulation stands on.

    Every statement here is standard SQL. That is not an accident: this module
    lives outside `veritas/warehouse/`, and ADR-0002 names *"a `duckdb` import or
    a DuckDB-specific function name anywhere outside the adapter module"* as the
    signal that the seam has stopped holding.
    """
    instruments = tuple(
        Instrument(instrument_id, symbol, instrument_type, currency)
        for instrument_id, symbol, instrument_type, currency in warehouse.query(
            "SELECT instrument_id, instrument_symbol, instrument_type, "
            "       quotation_currency "
            "FROM dim_instrument ORDER BY instrument_id"
        )
    )

    prices: dict[tuple[int, dt.date], Decimal] = {}
    dates_by_instrument: dict[int, list[dt.date]] = {
        instrument.instrument_id: [] for instrument in instruments
    }
    for instrument_id, price_date, market_price in warehouse.query(
        "SELECT instrument_id, price_date, market_price "
        "FROM fct_instrument_price ORDER BY instrument_id, price_date"
    ):
        prices[(instrument_id, price_date)] = market_price
        dates_by_instrument[instrument_id].append(price_date)

    # The dates every Instrument has a Market Price on, not the dates some
    # Instrument does.
    #
    # R13 fixed that a Snapshot is written *"on every date the Warehouse holds a
    # Market Price for"*, which reads two ways once the table spans five exchange
    # calendars, and the two differ by dozens of dates — `--sources` prints both.
    # The intersection is the one that makes a Snapshot markable: on a date the
    # union includes but the intersection does not, some Instrument did not trade,
    # so a Position in it has no Market Price on that date and an Account Value
    # containing it is silently short by a holding. Taking the union would mean
    # either marking that Position at a stale price — a fill-forward pushed into
    # every future metric, which is precisely what storing FX Rates densely avoids
    # — or leaving a row out, which makes "what was held as of D" answer zero for
    # something that was held.
    #
    # The cost is real and worth stating: dates on which some markets traded are
    # absent from the Snapshot series, so a Position Change across one of them is
    # attributed to the next Snapshot date. That is the Snapshot term's own
    # limitation — *"a Snapshot cannot see between its own dates"* — rather than a
    # new one.
    snapshot_dates = tuple(
        date
        for (date,) in warehouse.query(
            "SELECT price_date FROM fct_instrument_price "
            "GROUP BY price_date "
            "HAVING count(*) = (SELECT count(*) FROM dim_instrument) "
            "ORDER BY price_date"
        )
    )

    fx_rates = {
        (rate_date, from_currency, to_currency): fx_rate
        for rate_date, from_currency, to_currency, fx_rate in warehouse.query(
            "SELECT rate_date, from_currency, to_currency, fx_rate FROM fct_fx_rate"
        )
    }
    ((last_rate_date,),) = warehouse.query("SELECT max(rate_date) FROM fct_fx_rate")

    return MarketData(
        instruments=instruments,
        prices=prices,
        trading_dates={
            instrument_id: tuple(dates)
            for instrument_id, dates in dates_by_instrument.items()
        },
        snapshot_dates=snapshot_dates,
        fx_rates=fx_rates,
        last_rate_date=last_rate_date,
    )


# -- deterministic drawing ---------------------------------------------------
#
# Three helpers, and a rule: the simulator draws through these and nowhere else.
#
# `Random` is seeded, so it is reproducible by construction. What these add is
# reproducibility that does not depend on *which* methods of it we happened to
# call — `choice` and `sample` are library implementations that have changed
# shape before, and a simulation whose output moves on a Python upgrade is not
# the seeded, reproducible bring-up the Target State promises. Every draw below
# bottoms out in `randrange`, which is the primitive.
#
# They also keep the whole module inside Decimal. A float in a draw would reach a
# monetary column through arithmetic, and this project's schema refuses floats in
# columns for reasons that apply just as hard one step upstream.


def pick(rng: Random, low: Decimal, high: Decimal, step: Decimal) -> Decimal:
    """A Decimal drawn uniformly from `low` to `high` on a grid of `step`."""
    return low + step * rng.randrange(int((high - low) / step) + 1)


def happens(rng: Random, probability: Decimal) -> bool:
    """True with the given probability, drawn on a grid of one hundredth."""
    return pick(rng, Decimal("0"), Decimal("1"), Decimal("0.01")) < probability


def take(rng: Random, items: tuple, count: int) -> tuple:
    """`count` distinct items, in the order they were drawn."""
    remaining = list(items)
    drawn = []
    for _ in range(min(count, len(remaining))):
        drawn.append(remaining.pop(rng.randrange(len(remaining))))
    return tuple(drawn)


def one_of(rng: Random, items):
    """One item, drawn uniformly."""
    return items[rng.randrange(len(items))]


# -- the simulation ----------------------------------------------------------


def build_accounts(rng: Random, market: MarketData) -> tuple[list[dict], list[Account]]:
    """Decide the Clients and Accounts, and everything fixed about each Account.

    Every Instrument is dealt to some Account before any Account draws a second
    one, so no Instrument in the universe ends up untraded. An untraded Instrument
    is a Market Price nothing marks and a row of `dim_instrument` that no metric
    can reach, which would make the richness assertion `--sources` already runs
    true on paper and empty in practice.
    """
    clients = [
        {"client_id": index + 1, "client_name": name, "client_region": region}
        for index, (name, region) in enumerate(CLIENTS)
    ]

    # The deal: one pass over the Instruments, handed out in turn, so the first
    # Instrument each Account holds covers the universe before preference starts.
    undealt = list(take(rng, market.instruments, len(market.instruments)))

    accounts: list[Account] = []
    account_id = 0
    for client in clients:
        region = client["client_region"]
        for _ in range(1 + rng.randrange(3)):
            account_id += 1

            primary = (
                "USD"
                if account_id % GLOBAL_ACCOUNT_EVERY == 0
                else REGION_CURRENCY[region]
            )
            currencies = (primary,)
            if happens(rng, SECOND_CURRENCY_SHARE):
                currencies += ("USD" if primary != "USD" else "EUR",)

            wanted = MIN_INSTRUMENTS_PER_ACCOUNT + rng.randrange(
                MAX_INSTRUMENTS_PER_ACCOUNT - MIN_INSTRUMENTS_PER_ACCOUNT + 1
            )
            held: list[Instrument] = []
            if undealt:
                held.append(undealt.pop())
            held.extend(
                instrument
                for instrument in take(
                    rng,
                    tuple(i for i in market.instruments if i not in held),
                    wanted - len(held),
                )
            )

            accounts.append(
                Account(
                    account_id=account_id,
                    client_id=client["client_id"],
                    account_name=f"{client['client_name']} — Account {account_id:03d}",
                    denomination_currencies=currencies,
                    instruments=tuple(held),
                    commission_rate=pick(
                        rng,
                        MIN_COMMISSION_RATE,
                        MAX_COMMISSION_RATE,
                        COMMISSION_RATE_STEP,
                    ),
                    fee_share=pick(rng, MIN_FEE_SHARE, MAX_FEE_SHARE, FEE_SHARE_STEP),
                    rebate_share=(
                        pick(
                            rng,
                            MIN_REBATE_SHARE,
                            MAX_REBATE_SHARE,
                            REBATE_SHARE_STEP,
                        )
                        if happens(rng, REBATED_ACCOUNT_SHARE)
                        else Decimal("0")
                    ),
                    trade_count=MIN_TRADES_PER_ACCOUNT
                    + rng.randrange(
                        MAX_TRADES_PER_ACCOUNT - MIN_TRADES_PER_ACCOUNT + 1
                    ),
                )
            )

    # Anything left undealt means there are more Instruments than Accounts, which
    # this universe and this Client list make impossible — but it would fail
    # silently and look like a thin book, so it is asserted rather than assumed.
    if undealt:
        raise AssertionError(
            f"{len(undealt)} Instruments were never dealt to an Account: "
            f"{[instrument.instrument_symbol for instrument in undealt]}"
        )
    return clients, accounts


def tradable_dates(market: MarketData) -> dict[int, tuple[dt.date, ...]]:
    """The dates a Trade may be dated, per Instrument.

    Two trading days short of the end of each Instrument's own calendar, because a
    Trade needs a Settlement Date and settlement is T+2 — and then cut again at
    the last date `fct_fx_rate` holds a rate for, because the cash leg converts at
    the Settlement Date's rate. Sub-step 2.4 handed this over as a constraint on
    this Sub-step: the FX window ends on the same day as the price window, so a
    Trade in the last two days of the window would settle past the last rate.

    Enforcing it here rather than checking it afterwards means the constraint is
    visible in the one place that could violate it.
    """
    tradable = {}
    for instrument_id, dates in market.trading_dates.items():
        usable = dates[: len(dates) - SETTLEMENT_TRADING_DAYS]
        settles = dates[SETTLEMENT_TRADING_DAYS:]
        tradable[instrument_id] = tuple(
            trade_date
            for trade_date, settlement_date in zip(usable, settles)
            if settlement_date <= market.last_rate_date
        )
        # An Instrument with nowhere to trade would silently drop out of every
        # Account that holds it, leaving a thinner book that still looks healthy.
        if not tradable[instrument_id]:
            raise AssertionError(
                f"instrument_id {instrument_id} has no date it can be traded on: "
                f"{len(dates)} price dates, none settling by {market.last_rate_date}"
            )
    return tradable


def settlement_date(market: MarketData, instrument_id: int, trade_date: dt.date) -> dt.date:
    """Two trading days after a Trade, on the Instrument's own calendar."""
    dates = market.trading_dates[instrument_id]
    return dates[dates.index(trade_date) + SETTLEMENT_TRADING_DAYS]


def build_trades(
    rng: Random, market: MarketData, accounts: list[Account]
) -> tuple[list[dict], list[dict]]:
    """Generate every Trade, and the Position events they and the transfers cause.

    Walked per Account in date order, because the decision to buy or sell depends
    on what the Account is holding at that moment — and a sale of a Position that
    was never opened is not a Trade a broker's warehouse can contain.

    Returns the Trades and a flat list of Position events. A Position event is
    `(account_id, instrument_id, date, quantity delta, cost delta)`; the Snapshot
    tables are folded from these rather than from the Trades, which is what lets a
    transfer move a Position with no Trade behind it.
    """
    trades: list[dict] = []
    position_events: list[dict] = []
    tradable = tradable_dates(market)

    for account in accounts:
        # Draw (date, Instrument) pairs first and sort them, so the walk below is
        # chronological and the holding is always the holding as of that date.
        scheduled = []
        for _ in range(account.trade_count):
            instrument = one_of(rng, account.instruments)
            scheduled.append(
                (one_of(rng, tradable[instrument.instrument_id]),
                 instrument.instrument_id)
            )
        scheduled.sort()

        by_id = {i.instrument_id: i for i in account.instruments}
        held: dict[int, list[Decimal]] = {}  # instrument_id -> [quantity, cost basis]

        for trade_date, instrument_id in scheduled:
            instrument = by_id[instrument_id]
            quantity_held, cost_basis = held.get(
                instrument_id, [Decimal("0"), Decimal("0")]
            )
            market_price = market.price(instrument_id, trade_date)

            # An Execution Price is never the close. Which side of it is drawn
            # too — a fill is not systematically better or worse than the close,
            # and a one-sided drift would put a bias into every Traded Notional.
            drift = pick(
                rng, MIN_EXECUTION_DRIFT, MAX_EXECUTION_DRIFT, EXECUTION_DRIFT_STEP
            )
            if happens(rng, Decimal("0.5")):
                drift = -drift
            execution_price = money(market_price * (Decimal("1") + drift))

            selling = quantity_held > 0 and happens(rng, SELL_PROBABILITY)
            if selling:
                if happens(rng, FULL_CLOSE_PROBABILITY):
                    quantity = quantity_held
                else:
                    lot = LOT_SIZE[instrument.instrument_type]
                    share = pick(
                        rng,
                        MIN_PARTIAL_SELL_SHARE,
                        MAX_PARTIAL_SELL_SHARE,
                        SELL_SHARE_STEP,
                    )
                    quantity = max(lot, (quantity_held * share / lot).to_integral_value() * lot)
                    quantity = min(quantity, quantity_held)
            else:
                lot = LOT_SIZE[instrument.instrument_type]
                notional_eur = pick(
                    rng,
                    MIN_TRADE_NOTIONAL_EUR,
                    MAX_TRADE_NOTIONAL_EUR,
                    TRADE_NOTIONAL_STEP,
                )
                notional = market.convert(
                    notional_eur, "EUR", instrument.quotation_currency, trade_date
                )
                quantity = max(
                    lot, (notional / market_price / lot).to_integral_value() * lot
                )

            # The Account is billed in one of its own currencies, weighted to the
            # first. Not the Instrument's — that is the whole of the Denomination
            # against Quotation Currency row, and an Account billed in the currency
            # of whatever it happened to trade would make the two columns equal on
            # every row and the distinction unmeasurable.
            denomination_currency = account.denomination_currencies[0]
            if len(account.denomination_currencies) > 1 and happens(
                rng, Decimal("0.25")
            ):
                denomination_currency = account.denomination_currencies[1]

            notional_quoted = money(quantity * execution_price)
            commission = market.convert(
                money(notional_quoted * account.commission_rate),
                instrument.quotation_currency,
                denomination_currency,
                trade_date,
            )

            if selling:
                # Average cost: the sold quantity takes its share of what the whole
                # holding cost. The alternative, first-in-first-out, needs a lot
                # ledger this schema does not have — `fct_position_snapshot` carries
                # one Cost Basis per holding, which is the Glossary's own definition
                # ("the total for the held quantity, accumulated across the Trades
                # that built it") and admits exactly one reading.
                #
                # Realised P&L is the proceeds less what that share cost, **gross of
                # Commission**: the charge is separately recognised as the broker's
                # revenue in fct_accounting_movement, and netting it here would
                # count it twice.
                cost_removed = money(cost_basis * quantity / quantity_held)
                realised = notional_quoted - cost_removed
                delta_quantity = -quantity
                delta_cost = -cost_removed
            else:
                realised = Decimal("0")
                delta_quantity = quantity
                delta_cost = notional_quoted

            trades.append(
                {
                    "trade_id": 0,  # assigned below, once every Trade exists
                    "account_id": account.account_id,
                    "instrument_id": instrument_id,
                    "trade_date": trade_date,
                    "settlement_date": settlement_date(
                        market, instrument_id, trade_date
                    ),
                    "trade_side": "sell" if selling else "buy",
                    "quantity": quantity,
                    "execution_price": execution_price,
                    "commission": commission,
                    "fee": money(commission * account.fee_share),
                    "rebate": money(commission * account.rebate_share),
                    "denomination_currency": denomination_currency,
                    # Not columns of fct_trade — carried so the movement and
                    # Snapshot folds below do not have to re-derive them.
                    "quotation_currency": instrument.quotation_currency,
                    "notional_quoted": notional_quoted,
                    "realised_pnl_quoted": realised,
                }
            )

            held[instrument_id] = [
                quantity_held + delta_quantity,
                cost_basis + delta_cost,
            ]
            position_events.append(
                {
                    "account_id": account.account_id,
                    "instrument_id": instrument_id,
                    "date": trade_date,
                    "delta_quantity": delta_quantity,
                    "delta_cost_basis": delta_cost,
                }
            )

    # trade_id, assigned once every Trade exists, in the order a reader would
    # expect to read them: by date, then by Account. Assigning as they were
    # generated would number an Account's whole life before the next Account's
    # first Trade, which is an ordering nothing in the domain has.
    trades.sort(key=lambda trade: (trade["trade_date"], trade["account_id"],
                                   trade["instrument_id"], trade["trade_side"]))
    for trade_id, trade in enumerate(trades, start=1):
        trade["trade_id"] = trade_id

    position_events.extend(build_transfers(rng, market, position_events))
    return trades, position_events


def build_transfers(
    rng: Random, market: MarketData, position_events: list[dict]
) -> list[dict]:
    """A handful of Position movements with no Trade behind them.

    This is the `Position Change` against `Trade` row of Section C made real:
    *"Positions also change through transfers and corporate actions. Deriving
    position change from trades alone silently loses those."* A securities
    transfer moves stock between custodians; no cash moves, so it appears in
    neither movement table, and an Account whose Position Change is folded out of
    `fct_trade` is wrong about it by exactly this quantity.

    A transfer in brings its own Cost Basis, valued at that date's Market Price —
    the holding cost the transferring custodian passed on. A transfer out removes
    Cost Basis proportionally and books **no** Realised P&L: nothing was sold.
    """
    # Every (Account, Instrument) that ever holds anything, with its events in
    # date order. Sorted before drawing, so the choice does not depend on
    # dictionary ordering.
    events_by_subject: dict[tuple[int, int], list[dict]] = {}
    for event in position_events:
        events_by_subject.setdefault(
            (event["account_id"], event["instrument_id"]), []
        ).append(event)
    for events in events_by_subject.values():
        events.sort(key=lambda event: event["date"])
    candidates = tuple(sorted(events_by_subject))
    by_id = {instrument.instrument_id: instrument for instrument in market.instruments}

    # Where in the window a transfer may be sited. Both ends are cut, for opposite
    # reasons, and both are about the transfer being *visible* in the Snapshot
    # series rather than about realism:
    #
    #   the first half is dropped   so the Account has already traded its way into
    #                               a holding worth moving a share of, and so the
    #                               Snapshot immediately before the transfer is a
    #                               real one rather than the start of the series
    #   the last five are dropped   so Snapshots follow the transfer. A transfer on
    #                               the final Snapshot date would move a Position
    #                               with nothing after it to show the new holding,
    #                               and the Section C row it exists for is about a
    #                               holding that stops matching its own Trades.
    dates = market.snapshot_dates[len(market.snapshot_dates) // 2 : -5]

    transfers: list[dict] = []
    for key in take(rng, candidates, len(candidates)):
        if len(transfers) == TRANSFERS_IN + TRANSFERS_OUT:
            break
        account_id, instrument_id = key
        date = one_of(rng, dates)

        # The holding **as of the transfer's own date**, not at the end of the
        # window. Sizing a transfer out against the final Position is how a
        # transfer quietly turns a long into a short: the Account may hold far
        # less on the day the stock actually moves.
        #
        # Summed over *every* event this subject has, including transfers already
        # sited by an earlier pass of this loop, which is why each one is appended
        # to `events_by_subject` below. Today `take` yields each subject at most
        # once so no subject gets two, but a `held` that silently ignored non-Trade
        # movements would be wrong the moment that stopped being true — and it
        # would be wrong in the direction that oversizes a transfer out.
        held = sum(
            (
                event["delta_quantity"]
                for event in events_by_subject[key]
                if event["date"] <= date
            ),
            Decimal("0"),
        )
        if held <= 0:
            continue

        # Rounded to the Instrument's lot, exactly as a Trade is. A transfer moves
        # the same stock a Trade moves — 292.5 shares of an equity is not a holding
        # a custodian can deliver any more than it is a Trade a broker can fill —
        # so the two paths cannot disagree about what a whole unit is. Capped at
        # the holding, because rounding up on a transfer out would move stock the
        # Account does not have.
        lot = LOT_SIZE[by_id[instrument_id].instrument_type]
        share = pick(rng, MIN_TRANSFER_SHARE, MAX_TRANSFER_SHARE, TRANSFER_SHARE_STEP)
        quantity = min(held, max(lot, (held * share / lot).to_integral_value() * lot))
        cost = money(quantity * market.price(instrument_id, date))
        incoming = len(transfers) < TRANSFERS_IN
        transfer = {
            "account_id": account_id,
            "instrument_id": instrument_id,
            "date": date,
            "delta_quantity": quantity if incoming else -quantity,
            "delta_cost_basis": cost if incoming else -cost,
        }
        transfers.append(transfer)
        events_by_subject[key].append(transfer)
        events_by_subject[key].sort(key=lambda event: event["date"])

    if len(transfers) < TRANSFERS_IN + TRANSFERS_OUT:
        raise AssertionError(
            f"only {len(transfers)} transfers could be sited — Section C's "
            f"Position Change against Trade row needs at least one"
        )
    return transfers


def build_movements(
    market: MarketData, trades: list[dict]
) -> tuple[list[dict], list[dict]]:
    """The two movement tables, from the same Trades, on two different dates.

    This function is the Section C `Cash Movement` against `Accounting Movement`
    row, written once:

      * a charge is **earned** on Trade Date          -> fct_accounting_movement
      * a charge is **collected** on Settlement Date  -> fct_cash_movement

    Same amounts, different dates, so any period whose boundary falls between a
    Trade and its settlement gives the two tables different totals — and both are
    right.

    Two things are in one table and not the other, and that asymmetry is the point
    rather than an omission:

      * `realised P&L` is an Accounting Movement only. No cash moves when a
        Position closes; the cash moved at settlement, as the sale proceeds.
      * the settlement of the Trade itself, and every deposit and withdrawal, are
        Cash Movements only. They move money without recognising any value.

    Sign conventions, which differ between the two tables on purpose:

      * `fct_cash_movement.amount` is signed from the **Account's** side —
        positive enters it. The schema comment says so.
      * `fct_accounting_movement.amount` carries the **magnitude** recognised, as
        `fct_trade` stores it, with `movement_type` saying what it is. That is
        what makes the Glossary's own formula literally true against this table:
        Net Revenue = Σcommission − Σrebate − Σfee. `realised P&L` is the one
        signed value, because a loss is genuinely negative.
    """
    cash: list[dict] = []
    accounting: list[dict] = []

    def cash_row(account_id, trade_id, date, movement_type, amount, currency):
        cash.append(
            {
                "cash_movement_id": 0,
                "account_id": account_id,
                "trade_id": trade_id,
                "movement_date": date,
                "movement_type": movement_type,
                "amount": amount,
                "denomination_currency": currency,
            }
        )

    def accounting_row(account_id, trade_id, date, movement_type, amount, currency):
        accounting.append(
            {
                "accounting_movement_id": 0,
                "account_id": account_id,
                "trade_id": trade_id,
                "movement_date": date,
                "movement_type": movement_type,
                "amount": amount,
                "denomination_currency": currency,
            }
        )

    for trade in trades:
        currency = trade["denomination_currency"]
        settles = trade["settlement_date"]

        # The Trade's own cash leg, converted at the **Settlement Date's** rate.
        # Section C: which date a period filter uses "also selects the FX Rate, so
        # it moves the number twice". Cash settles when it settles, at the rate of
        # the day it moved — so this is the second half of that sentence, and the
        # reason the two dates are not interchangeable even for one Trade.
        settled = market.convert(
            trade["notional_quoted"], trade["quotation_currency"], currency, settles
        )
        cash_row(
            trade["account_id"],
            trade["trade_id"],
            settles,
            "trade settlement",
            settled if trade["trade_side"] == "sell" else -settled,
            currency,
        )

        for movement_type, amount, entering in (
            ("commission", trade["commission"], False),
            ("fee", trade["fee"], False),
            ("rebate", trade["rebate"], True),
        ):
            if not amount:
                continue
            cash_row(
                trade["account_id"],
                trade["trade_id"],
                settles,
                movement_type,
                amount if entering else -amount,
                currency,
            )
            accounting_row(
                trade["account_id"],
                trade["trade_id"],
                trade["trade_date"],
                movement_type,
                amount,
                currency,
            )

        if trade["trade_side"] == "sell" and trade["realised_pnl_quoted"]:
            accounting_row(
                trade["account_id"],
                trade["trade_id"],
                trade["trade_date"],
                "realised P&L",
                market.convert(
                    trade["realised_pnl_quoted"],
                    trade["quotation_currency"],
                    currency,
                    trade["trade_date"],
                ),
                currency,
            )

    return cash, accounting


def build_cash_events(
    rng: Random, market: MarketData, accounts: list[Account], cash: list[dict]
) -> list[dict]:
    """Deposits and withdrawals — the Cash Movements no Trade explains.

    The opening deposit is **computed, not drawn**: it is the largest shortfall the
    Account's own trading would otherwise run, with a buffer. Picking a number
    instead would leave some Accounts financing two years of trading out of an
    overdraft and others sitting on an idle balance, and Cash Balance is a
    Certified Metric — a negative one for a reason nobody chose is a wrong number
    with a plausible explanation, which is the exact failure this project is about.

    The later deposits and withdrawals are drawn, and a withdrawal is sized
    against the *smallest* balance between its own date and the end of the window,
    so taking money out cannot push a later date negative.
    """
    events: list[dict] = []

    for account in accounts:
        for currency in account.denomination_currencies:
            movements = sorted(
                (
                    (row["movement_date"], row["amount"])
                    for row in cash
                    if row["account_id"] == account.account_id
                    and row["denomination_currency"] == currency
                ),
            )
            if not movements:
                continue

            # The opening deposit, on the first Snapshot date on or before the
            # first movement — an Account has to be funded before it can trade.
            opening_date = min(
                market.snapshot_dates[0], movements[0][0] - dt.timedelta(days=1)
            )
            # Enough to cover the deepest hole the Account's own trading digs, and
            # never less than its largest single movement. The second half is what
            # keeps this currency-blind: an Account whose flows never go negative
            # still needs a balance of a plausible size, and "one settlement" is a
            # size expressed in the Account's own currency rather than a constant
            # that would mean something different in JPY than in GBP.
            shortfall = Decimal("0")
            balance = Decimal("0")
            largest = Decimal("0")
            for _, amount in movements:
                balance += amount
                shortfall = min(shortfall, balance)
                largest = max(largest, abs(amount))
            opening = money(max(-shortfall, largest) * OPENING_DEPOSIT_BUFFER)
            events.append(
                {
                    "cash_movement_id": 0,
                    "account_id": account.account_id,
                    "trade_id": None,
                    "movement_date": opening_date,
                    "movement_type": "deposit",
                    "amount": opening,
                    "denomination_currency": currency,
                }
            )

            # The running balance after the opening deposit, so a withdrawal can
            # be sized against what is genuinely spare from that date onwards.
            dated = [(opening_date, opening)] + movements
            for _ in range(
                MIN_CASH_EVENTS + rng.randrange(MAX_CASH_EVENTS - MIN_CASH_EVENTS + 1)
            ):
                date = one_of(rng, market.snapshot_dates[1:-1])
                running = Decimal("0")
                lowest_after = None
                for movement_date, amount in sorted(dated):
                    running += amount
                    if movement_date >= date:
                        lowest_after = (
                            running if lowest_after is None else min(lowest_after, running)
                        )
                spare = lowest_after if lowest_after is not None else running

                if happens(rng, WITHDRAWAL_PROBABILITY) and spare > 0:
                    amount = -money(spare * WITHDRAWAL_SHARE)
                    movement_type = "withdrawal"
                else:
                    amount = money(abs(opening) * DEPOSIT_SHARE)
                    movement_type = "deposit"
                if not amount:
                    continue
                events.append(
                    {
                        "cash_movement_id": 0,
                        "account_id": account.account_id,
                        "trade_id": None,
                        "movement_date": date,
                        "movement_type": movement_type,
                        "amount": amount,
                        "denomination_currency": currency,
                    }
                )
                dated.append((date, amount))

    return events


def fold_position_snapshots(
    market: MarketData, position_events: list[dict]
) -> list[dict]:
    """Fold the Position events into one row per Account, Instrument and date.

    Dense from the first event onward: a Snapshot exists on **every** date after
    a holding first appears, including the zero rows a closed Position leaves
    behind. `Snapshot` is registered as *"written on every date the Warehouse
    holds a Market Price for, so an 'as of' question is an equality join rather
    than a most-recent-row-at-or-before lookup"*, and a sparse table would make
    every future metric re-derive the fill-forward that this loop does once.

    Before the first event there is no row, and that is deliberate: a zero row on
    a date before an Account ever touched an Instrument asserts a holding that did
    not exist rather than recording one that was empty.
    """
    by_subject: dict[tuple[int, int], list[dict]] = {}
    for event in position_events:
        by_subject.setdefault(
            (event["account_id"], event["instrument_id"]), []
        ).append(event)

    rows: list[dict] = []
    for (account_id, instrument_id), events in sorted(by_subject.items()):
        events.sort(key=lambda event: event["date"])
        quantity = Decimal("0")
        cost_basis = Decimal("0")
        pending = list(events)
        started = False
        for snapshot_date in market.snapshot_dates:
            while pending and pending[0]["date"] <= snapshot_date:
                event = pending.pop(0)
                quantity += event["delta_quantity"]
                cost_basis += event["delta_cost_basis"]
                started = True
            if not started:
                continue
            # A closed Position holds nothing, so it cost nothing to hold — the
            # schema's own CHECK. Average-cost arithmetic lands exactly on zero
            # when the last unit goes, so this is the transfer-out case and the
            # residue of a partial sale, not a rounding sweep.
            if quantity == 0:
                cost_basis = Decimal("0")
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "account_id": account_id,
                    "instrument_id": instrument_id,
                    "quantity": money(quantity),
                    "cost_basis": money(cost_basis),
                }
            )
    return rows


def fold_balance_snapshots(market: MarketData, cash: list[dict]) -> list[dict]:
    """Fold the Cash Movements into a Cash Balance per Account, currency and date.

    The same fold as the Positions above, over money instead of stock, and dense
    for the same reason. One row per currency is what `fct_balance_snapshot`'s
    grain means and why `dim_account` carries no currency column: an Account with
    two billing currencies has two balances, not a total.
    """
    by_subject: dict[tuple[int, str], list[tuple[dt.date, Decimal]]] = {}
    for row in cash:
        by_subject.setdefault(
            (row["account_id"], row["denomination_currency"]), []
        ).append((row["movement_date"], row["amount"]))

    rows: list[dict] = []
    for (account_id, currency), movements in sorted(by_subject.items()):
        movements.sort()
        balance = Decimal("0")
        pending = list(movements)
        started = False
        for snapshot_date in market.snapshot_dates:
            while pending and pending[0][0] <= snapshot_date:
                balance += pending.pop(0)[1]
                started = True
            if not started:
                continue
            rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "account_id": account_id,
                    "denomination_currency": currency,
                    "cash_balance": money(balance),
                }
            )
    return rows


def simulate(market: MarketData, seed: int = SEED) -> dict[str, list[dict]]:
    """Generate the whole client side, as rows per `raw` table.

    A pure function of `market` and `seed`. Every draw goes through one `Random`
    seeded once here, and every helper above takes it as an argument rather than
    reaching for a module-level one, so the order of draws is the order of the
    code and a second call returns the same rows.
    """
    rng = Random(seed)

    clients, accounts = build_accounts(rng, market)
    trades, position_events = build_trades(rng, market, accounts)
    cash, accounting = build_movements(market, trades)
    cash += build_cash_events(rng, market, accounts, cash)

    # Movement identifiers, assigned last for the same reason Trade ones are:
    # sorted into the order a reader would page through them rather than the order
    # the generator happened to produce.
    cash.sort(key=lambda row: (row["movement_date"], row["account_id"],
                               row["movement_type"], row["trade_id"] or 0))
    for movement_id, row in enumerate(cash, start=1):
        row["cash_movement_id"] = movement_id
    accounting.sort(key=lambda row: (row["movement_date"], row["account_id"],
                                     row["movement_type"], row["trade_id"] or 0))
    for movement_id, row in enumerate(accounting, start=1):
        row["accounting_movement_id"] = movement_id

    return {
        "simulated_client": clients,
        "simulated_account": [
            {
                "account_id": account.account_id,
                "client_id": account.client_id,
                "account_name": account.account_name,
            }
            for account in accounts
        ],
        # The three carried fields the star table has no column for are dropped
        # here rather than in SQL: `raw` is what the source produced, and this
        # module is the source.
        "simulated_trade": [
            {
                key: value
                for key, value in trade.items()
                if key not in ("quotation_currency", "notional_quoted",
                               "realised_pnl_quoted")
            }
            for trade in trades
        ],
        "simulated_cash_movement": cash,
        "simulated_accounting_movement": accounting,
        "simulated_position_snapshot": fold_position_snapshots(
            market, position_events
        ),
        "simulated_balance_snapshot": fold_balance_snapshots(market, cash),
    }
