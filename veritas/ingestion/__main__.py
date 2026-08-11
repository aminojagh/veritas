"""Ingestion's entry point.

    uv run python -m veritas.ingestion              # replay, no network
    uv run python -m veritas.ingestion --refresh    # re-hit every source

Builds the Warehouse from nothing, in the one order the foreign keys permit:
dimensions before facts. After Sub-step 2.4 that means `dim_instrument`,
`fct_instrument_price` and `fct_fx_rate` — the traded Instrument universe, two
years of daily Market Prices for it, and the ECB reference rates every one of
those prices has to be converted through — with the other seven tables empty.
Each Sub-step adds a source to a pipeline that already runs end-to-end rather than
half-wiring one. This is the whole real half of Ingestion; Sub-step 2.5 adds the
synthetic client activity beside it.

**The Warehouse is rebuilt from scratch on every run.** `schema.sql` uses plain
`CREATE TABLE`, so there is nothing to reconcile against an existing file, and a
pipeline whose output depends on how many times it has run is not the
reproducible bring-up the whole snapshot-and-replay design is for. The database
file is gitignored; the snapshots are what carry the data between clones.

The two connections in this file are sequential and never overlap. dlt's DuckDB
destination opens its own — the awkwardness R4 was raised to settle — so it runs
to completion and closes before the adapter opens. R4's ruling is what makes that
acceptable: dlt does extract-and-load into `raw`, and the star schema, the thing
every Metric Definition will quote, stays entirely behind the adapter.
"""

import argparse
import sys

import dlt

from veritas.ingestion import snapshots, sources
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

# The star tables built so far, in dependency order — dim_instrument must hold a
# row before fct_instrument_price may reference it, and the engine enforces that
# foreign key rather than trusting this tuple. fct_fx_rate declares no foreign key
# and is last for a different reason the engine cannot enforce: its build reads
# both tables above it, taking the currencies it must cover from dim_instrument and
# the end of the window from fct_instrument_price. Sub-step 2.5 appends to this;
# nothing else in this file changes when it does.
BUILDS = ("dim_instrument", "fct_instrument_price", "fct_fx_rate")


def raw_resources(*, refresh: bool) -> list[object]:
    """Every raw source and vocabulary map, wrapped as a dlt resource."""
    rows_by_table = [
        (table_name, generator(refresh=refresh))
        for table_name, generator in FETCHED_TABLES
    ] + [
        (table_name, generator()) for table_name, generator in DERIVED_TABLES
    ]
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


def load_raw(*, refresh: bool) -> None:
    """Extract every source and land it in the `raw` schema."""
    pipeline = dlt.pipeline(
        pipeline_name="veritas_ingestion",
        destination=dlt.destinations.duckdb(str(DATABASE_PATH)),
        dataset_name="raw",
        progress=None,
    )
    pipeline.run(raw_resources(refresh=refresh))


def build_star_schema() -> tuple[dict[str, int], int, int]:
    """Create the star schema and fill it from `raw`.

    Returns the row count of every star table and two numbers a bare row count
    cannot say, both of them about a Warehouse that is silently short while looking
    entirely healthy in a listing:

      * how many distinct Instruments `fct_instrument_price` carries a price for —
        a large pile of price rows covering every Instrument but one is a Warehouse
        where one Position can never be marked;
      * how many of those prices have no FX Rate on their own date — a price the
        Warehouse holds and cannot convert to a Reporting Currency, which is a
        Position that can be marked and still cannot be reported.
    """
    with WarehouseAdapter() as warehouse:
        warehouse.create_schema()
        for build_name in BUILDS:
            warehouse.run_build(build_name)
        counts = {name: warehouse.row_count(name) for name in warehouse.tables()}
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
        return counts, priced_instruments, unconvertible


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

    # Rebuilt from scratch, so a run never depends on a previous one. See the
    # module docstring — this is the reproducibility property, not a convenience.
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print(f"  removed {DATABASE_PATH.relative_to(REPO_ROOT)} — rebuilding")

    try:
        load_raw(refresh=arguments.refresh)
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

    counts, priced_instruments, unconvertible = build_star_schema()

    print()
    for table_name, count in sorted(counts.items()):
        marker = "·" if count else " "
        print(f"  {marker} {table_name:24} {count:>6} rows")

    # Every source must have arrived for every Instrument. Both failures below are
    # silent ones: the pipeline completes, the listing looks plausible, and the
    # Warehouse is short. Neither is a judgement about the *values* — that is
    # `check_warehouse.py --sources`, which re-derives them from the snapshots.
    expected = len(TRADED_INSTRUMENTS)
    loaded = counts.get("dim_instrument", 0)
    prices = counts.get("fct_instrument_price", 0)
    print()
    if loaded != expected:
        print(
            f"FAIL — dim_instrument holds {loaded} rows for "
            f"{expected} traded Instruments; a symbol lost its "
            f"metadata on the way in"
        )
        return 1
    if priced_instruments != expected:
        print(
            f"FAIL — fct_instrument_price covers {priced_instruments} of "
            f"{expected} Instruments; the rest can hold a Position that can "
            f"never be marked"
        )
        return 1
    if unconvertible:
        print(
            f"FAIL — {unconvertible} of {prices} Market Prices have no FX Rate on "
            f"their own date, so a Position marked at them cannot be converted to "
            f"a Reporting Currency. The FX window no longer covers the price "
            f"window: run `uv run python -m veritas.ingestion --refresh` to bring "
            f"both sources back to the same window"
        )
        return 1

    rates = counts.get("fct_fx_rate", 0)
    print(
        f"PASS — the Warehouse is built · dim_instrument holds {loaded} "
        f"Instruments · fct_instrument_price holds {prices} Market Prices "
        f"across all {priced_instruments} · fct_fx_rate holds {rates} FX Rates "
        f"and every Market Price has one"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
