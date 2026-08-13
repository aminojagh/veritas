"""Ingestion's entry point.

    uv run python -m veritas.ingestion              # replay, no network
    uv run python -m veritas.ingestion --refresh    # re-hit every source

Builds the Warehouse from nothing, in the one order the foreign keys permit:
dimensions before facts. After Sub-step 2.5 that is the whole of it — all ten
tables of Glossary Section B, in two phases that cannot be reordered:

  **1. The real half.** `dim_instrument`, `fct_instrument_price` and `fct_fx_rate`
  — the traded Instrument universe, two years of daily Market Prices for it, and
  the ECB reference rates every one of those prices has to be converted through.
  Each comes from a key-free public source, snapshotted into the repository.

  **2. The synthetic half.** The seven client-activity tables, from the seeded
  simulator in `simulator.py`. It runs *after* phase 1 because it reads it: every
  Trade is priced off a Market Price the Warehouse already holds and every
  conversion goes through a real FX Rate. That ordering is the Glossary's
  `Ingestion` rule made structural — *"market data real, client activity
  synthetic — never the reverse"*.

**The Warehouse is rebuilt from scratch on every run.** `schema.sql` uses plain
`CREATE TABLE`, so there is nothing to reconcile against an existing file, and a
pipeline whose output depends on how many times it has run is not the
reproducible bring-up the whole snapshot-and-replay design is for. The database
file is gitignored; the snapshots are what carry the data between clones.

**No two connections in this file are ever open at once.** dlt's DuckDB
destination opens its own — the awkwardness R4 was raised to settle — so each dlt
load runs to completion and closes before the adapter opens, and the adapter
closes before the next load. R4's ruling is what makes that acceptable: dlt does
extract-and-load into `raw`, and the star schema, the thing every Metric
Definition will quote, stays entirely behind the adapter. Sub-step 2.5 adds a
second dlt load rather than a second *kind* of writer: the simulator's rows land
in `raw` and are built into star tables by hand-authored SQL, exactly as every
real source's are.
"""

import argparse
import sys

import dlt

from veritas.ingestion import simulator, snapshots, sources
from veritas.ingestion.snapshots import SNAPSHOT_DIR, SourceUnavailable
from veritas.ingestion.universe import TRADED_INSTRUMENTS
from veritas.warehouse import DATABASE_PATH, WarehouseAdapter

REPO_ROOT = DATABASE_PATH.parent.parent

# One dlt resource per raw table, split by where the rows come from. `replace`
# rather than `append` because a run rebuilds the Warehouse: appending would grow
# `raw` every time and quietly fan out the star build's joins.
#
# FETCHED reads a source and therefore honours --refresh. DERIVED is the two
# vocabulary maps out of universe.py — ours, not a source's, with nothing to
# re-fetch. Keeping the split in the data rather than in an `if` is what makes it
# obvious which tables a network outage can affect.
FETCHED_TABLES = (
    ("nasdaq_symbol", sources.nasdaq_symbols),
    ("sec_registrant", sources.sec_registrants),
    ("yahoo_instrument", sources.yahoo_instruments),
    ("yahoo_price", sources.yahoo_prices),
    ("frankfurter_rate", sources.frankfurter_rates),
)

DERIVED_TABLES = (
    ("minor_unit_currency", sources.minor_unit_currencies),
    ("yahoo_instrument_type", sources.yahoo_instrument_types),
)

# The star tables built from real sources, in dependency order — dim_instrument
# must hold a row before fct_instrument_price may reference it, and the engine
# enforces that foreign key rather than trusting this tuple. fct_fx_rate declares
# no foreign key and is last for a different reason the engine cannot enforce: its
# build reads both tables above it, taking the currencies it must cover from
# dim_instrument and the end of the window from fct_instrument_price.
MARKET_BUILDS = ("dim_instrument", "fct_instrument_price", "fct_fx_rate")

# The star tables built from the simulator, in dependency order. Every ordering
# here *is* enforced by a declared foreign key: an Account needs its Client, a
# Trade needs its Account and its Instrument, and a movement needs its Trade.
CLIENT_BUILDS = (
    "dim_client",
    "dim_account",
    "fct_trade",
    "fct_cash_movement",
    "fct_accounting_movement",
    "fct_position_snapshot",
    "fct_balance_snapshot",
)


def raw_resources(*, refresh: bool) -> list[object]:
    """Every real source and vocabulary map, wrapped as a dlt resource."""
    rows_by_table = [
        (table_name, generator(refresh=refresh))
        for table_name, generator in FETCHED_TABLES
    ] + [
        (table_name, generator()) for table_name, generator in DERIVED_TABLES
    ]
    return as_resources(rows_by_table)


def as_resources(rows_by_table: list[tuple[str, object]]) -> list[object]:
    return [
        dlt.resource(rows, name=table_name, write_disposition="replace")
        for table_name, rows in rows_by_table
    ]


def source_failure(error: BaseException) -> SourceUnavailable | None:
    """Find a `SourceUnavailable` anywhere in an exception's chain.

    dlt wraps whatever a resource generator raises in its own
    `PipelineStepFailed`, so catching `SourceUnavailable` around `pipeline.run`
    catches nothing and the operator gets a dlt traceback instead of the one
    sentence that tells them what to do. The original is still on the chain, so
    this walks it rather than matching on dlt's exception types — which would
    couple this file to a dependency's class names for no benefit.
    """
    seen: set[int] = set()
    while error is not None and id(error) not in seen:
        if isinstance(error, SourceUnavailable):
            return error
        seen.add(id(error))
        error = error.__cause__ or error.__context__
    return None


def load_raw(resources: list[object]) -> None:
    """Land a set of resources in the `raw` schema.

    Called twice — once for the real sources and once for the simulator's rows —
    against the same pipeline name and the same dataset. Each `replace` load
    touches only the tables in the resources it was handed, so the second does not
    disturb the first.
    """
    pipeline = dlt.pipeline(
        pipeline_name="veritas_ingestion",
        destination=dlt.destinations.duckdb(str(DATABASE_PATH)),
        dataset_name="raw",
        progress=None,
    )
    pipeline.run(resources)


def build_market_tables() -> tuple[int, int]:
    """Create the star schema and fill its three real tables from `raw`.

    Returns two numbers a bare row count cannot say, both of them about a
    Warehouse that is silently short while looking entirely healthy in a listing:

      * how many distinct Instruments `fct_instrument_price` carries a price for —
        a large pile of price rows covering every Instrument but one is a Warehouse
        where one Position can never be marked;
      * how many of those prices have no FX Rate on their own date — a price the
        Warehouse holds and cannot convert to a Reporting Currency, which is a
        Position that can be marked and still cannot be reported.
    """
    with WarehouseAdapter() as warehouse:
        warehouse.create_schema()
        for build_name in MARKET_BUILDS:
            warehouse.run_build(build_name)
        ((priced_instruments,),) = warehouse.query(
            "SELECT count(DISTINCT instrument_id) FROM fct_instrument_price"
        )
        # A left join rather than a NOT EXISTS, so the failing rows are the ones
        # counted: a Market Price whose Quotation Currency has no rate on its own
        # price_date. Any surviving row is a mark that cannot leave its own
        # currency, which is what the FX window and the fill-forward exist to
        # prevent and what a mismatched refresh would reintroduce.
        ((unconvertible,),) = warehouse.query(
            "SELECT count(*) "
            "FROM fct_instrument_price AS price "
            "JOIN dim_instrument AS instrument "
            "  ON instrument.instrument_id = price.instrument_id "
            "LEFT JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = price.price_date "
            " AND rate.from_currency = instrument.quotation_currency "
            "WHERE rate.fx_rate IS NULL"
        )
        return priced_instruments, unconvertible


def simulate_client_activity() -> dict[str, list[dict]]:
    """Read the real half of the Warehouse and generate the synthetic half.

    The read and the generation are separate calls on purpose: the adapter is open
    only for the read, so the connection is closed again before dlt opens its own
    to land what came back.
    """
    with WarehouseAdapter() as warehouse:
        market = simulator.read_market_data(warehouse)
    return simulator.simulate(market)


def build_client_tables() -> tuple[dict[str, int], int, int]:
    """Fill the seven client-activity tables, and count what could not be valued.

    Two more silent-shortness numbers, in the same shape as the market ones and
    for the same reason — each is a Warehouse that lists a plausible row count and
    cannot answer a question it promises:

      * Positions with no Market Price on their own Snapshot date. A Position that
        cannot be marked has no Unrealised P&L and no Account Value, and R13's
        density rule exists precisely to make this number zero.
      * monetary rows whose Denomination Currency has no FX Rate on their own
        date. Sub-step 2.4 handed this over by name: the coverage assertion it
        wrote walks Market Prices only, so a Trade billed in a currency no
        Instrument is quoted in would have no rate and its Gross Revenue could not
        reach a Reporting Currency. There is now a Trade to assert against.
    """
    with WarehouseAdapter() as warehouse:
        for build_name in CLIENT_BUILDS:
            warehouse.run_build(build_name)
        counts = {name: warehouse.row_count(name) for name in warehouse.tables()}
        ((unmarkable,),) = warehouse.query(
            "SELECT count(*) "
            "FROM fct_position_snapshot AS position "
            "LEFT JOIN fct_instrument_price AS price "
            "  ON price.price_date = position.snapshot_date "
            " AND price.instrument_id = position.instrument_id "
            "WHERE price.market_price IS NULL"
        )
        # Every date a monetary amount is dated by, against the currency it is
        # held in. A UNION ALL rather than four queries, so one number answers
        # "can every amount in this Warehouse reach a Reporting Currency?" —
        # including a Trade's settlement_date, which selects a different rate from
        # its trade_date and is the half a careless check would miss.
        ((unbillable,),) = warehouse.query(
            "WITH billed AS ( "
            "    SELECT trade_date AS on_date, denomination_currency FROM fct_trade "
            "    UNION ALL "
            "    SELECT settlement_date, denomination_currency FROM fct_trade "
            "    UNION ALL "
            "    SELECT movement_date, denomination_currency FROM fct_cash_movement "
            "    UNION ALL "
            "    SELECT movement_date, denomination_currency "
            "      FROM fct_accounting_movement "
            "    UNION ALL "
            "    SELECT snapshot_date, denomination_currency "
            "      FROM fct_balance_snapshot "
            ") "
            "SELECT count(*) FROM billed "
            "LEFT JOIN fct_fx_rate AS rate "
            "  ON rate.rate_date = billed.on_date "
            " AND rate.from_currency = billed.denomination_currency "
            "WHERE rate.fx_rate IS NULL"
        )
        return counts, unmarkable, unbillable


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="re-hit every source live and rewrite the snapshots in "
             "data/snapshots/ingestion/ — the only mode that needs a network",
    )
    arguments = parser.parse_args()

    mode = "refresh (live)" if arguments.refresh else "replay (offline)"
    print(f"  mode: {mode}")
    print(f"  snapshots: {SNAPSHOT_DIR.relative_to(REPO_ROOT)}")
    print(f"  universe: {len(TRADED_INSTRUMENTS)} Instruments")
    print(f"  simulator seed: {simulator.SEED}")

    # Rebuilt from scratch, so a run never depends on a previous one. See the
    # module docstring — this is the reproducibility property, not a convenience.
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print(f"  removed {DATABASE_PATH.relative_to(REPO_ROOT)} — rebuilding")

    try:
        load_raw(raw_resources(refresh=arguments.refresh))
    except Exception as error:
        unavailable = source_failure(error)
        if unavailable is None:
            # Not a source problem — a real defect, and hiding its traceback
            # behind a tidy message would cost more than the tidiness is worth.
            raise
        print(f"\nFAIL — {unavailable}")
        if snapshots.REWRITTEN:
            # A refresh rewrites files one at a time, so a failure part-way leaves
            # a mix of new and old snapshots that looks entirely healthy in a diff.
            # Naming what was rewritten is what makes that state visible.
            print(
                f"\n  this refresh had already rewritten "
                f"{len(snapshots.REWRITTEN)} snapshot(s) before failing, so "
                f"{SNAPSHOT_DIR.relative_to(REPO_ROOT)} now mixes fresh and stale "
                f"files. Re-run --refresh once the source is back, and do not "
                f"commit until it succeeds:"
            )
            for name in snapshots.REWRITTEN:
                print(f"    rewritten  {name}")
        return 1

    # What a successful refresh actually did. `snapshots.REWRITTEN` was added in
    # Sub-step 2.2 to make a *failed* refresh's half-written state visible, and the
    # same list answers a question 2.3 could only argue in a comment: whether the
    # cache in `read_source` really does fetch a source once however many resources
    # read it. Two resources share each Yahoo chart, so without the cache every one
    # of them would appear here twice — and the two fetches would return different
    # bytes, leaving dim_instrument and fct_instrument_price built from two
    # different observations of the same Instrument with only the second on disk.
    if arguments.refresh:
        rewritten_twice = sorted(
            {name for name in snapshots.REWRITTEN
             if snapshots.REWRITTEN.count(name) > 1}
        )
        print(f"  rewrote {len(snapshots.REWRITTEN)} snapshot(s), "
              f"{len(set(snapshots.REWRITTEN))} distinct")
        if rewritten_twice:
            print(
                f"\nFAIL — {rewritten_twice} were fetched more than once in one "
                f"run, so the resources reading them saw different bytes and only "
                f"the last fetch is on disk. The cache in snapshots.read_source is "
                f"what prevents this"
            )
            return 1

    priced_instruments, unconvertible = build_market_tables()

    # Both failures below are silent ones: the pipeline completes, the listing
    # looks plausible, and the Warehouse is short. Neither is a judgement about the
    # *values* — that is `check_warehouse.py --sources`, which re-derives them from
    # the snapshots. They are checked here, before the simulator runs, because the
    # simulator reads all three of these tables: generating a client book on top of
    # a Warehouse that is missing an Instrument's prices would bake the gap into
    # every Position it writes.
    expected = len(TRADED_INSTRUMENTS)
    if priced_instruments != expected:
        print(
            f"\nFAIL — fct_instrument_price covers {priced_instruments} of "
            f"{expected} Instruments; the rest can hold a Position that can "
            f"never be marked"
        )
        return 1
    if unconvertible:
        print(
            f"\nFAIL — {unconvertible} Market Prices have no FX Rate on their own "
            f"date, so a Position marked at them cannot be converted to a "
            f"Reporting Currency. The FX window no longer covers the price "
            f"window: run `uv run python -m veritas.ingestion --refresh` to bring "
            f"both sources back to the same window"
        )
        return 1

    simulated = simulate_client_activity()
    load_raw(as_resources(list(simulated.items())))
    counts, unmarkable, unbillable = build_client_tables()

    print()
    for table_name, count in sorted(counts.items()):
        marker = "·" if count else " "
        print(f"  {marker} {table_name:24} {count:>6} rows")

    print()
    loaded = counts.get("dim_instrument", 0)
    if loaded != expected:
        print(
            f"FAIL — dim_instrument holds {loaded} rows for "
            f"{expected} traded Instruments; a symbol lost its "
            f"metadata on the way in"
        )
        return 1
    if unmarkable:
        print(
            f"FAIL — {unmarkable} Positions have no Market Price on their own "
            f"Snapshot date, so they cannot be marked and no Account Value "
            f"containing them is complete. The Snapshot calendar and the price "
            f"calendar have come apart — see `read_market_data` in simulator.py"
        )
        return 1
    if unbillable:
        print(
            f"FAIL — {unbillable} monetary amounts are held in a Denomination "
            f"Currency with no FX Rate on their own date, so their Gross Revenue "
            f"cannot reach a Reporting Currency. Either the simulator billed an "
            f"Account in a currency no Instrument is quoted in, or a Trade "
            f"settled past the end of the FX window"
        )
        return 1

    prices = counts.get("fct_instrument_price", 0)
    rates = counts.get("fct_fx_rate", 0)
    print(
        f"PASS — the Warehouse is built · dim_instrument holds {loaded} "
        f"Instruments · fct_instrument_price holds {prices} Market Prices "
        f"across all {priced_instruments} · fct_fx_rate holds {rates} FX Rates "
        f"and every Market Price has one"
    )
    print(
        f"       the client side holds {counts.get('dim_client', 0)} Clients · "
        f"{counts.get('dim_account', 0)} Accounts · "
        f"{counts.get('fct_trade', 0)} Trades · every Position is markable and "
        f"every amount is convertible"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
