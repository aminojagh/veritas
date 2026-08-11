"""Ingestion's entry point.

    uv run python -m veritas.ingestion              # replay, no network
    uv run python -m veritas.ingestion --refresh    # re-hit every source

Builds the Warehouse from nothing, in the one order the foreign keys permit:
dimensions before facts. After Sub-step 2.3 that means `dim_instrument` and
`fct_instrument_price` — the traded Instrument universe and two years of daily
Market Prices for it — with the other eight tables empty. Each Sub-step adds a
source to a pipeline that already runs end-to-end rather than half-wiring one.

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
)

DERIVED_TABLES = (
    ("minor_unit_currency", sources.minor_unit_currencies),
    ("yahoo_instrument_type", sources.yahoo_instrument_types),
)

# The star tables built so far, in foreign-key order — dim_instrument must hold a
# row before fct_instrument_price may reference it, and the engine enforces that
# rather than trusting this tuple. Sub-steps 2.4 and 2.5 append to it; nothing
# else in this file changes when they do.
BUILDS = ("dim_instrument", "fct_instrument_price")


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


def build_star_schema() -> tuple[dict[str, int], int]:
    """Create the star schema and fill it from `raw`.

    Returns the row count of every star table, and how many distinct Instruments
    `fct_instrument_price` carries a price for. The second number is what a bare
    row count cannot say: a large pile of price rows covering every Instrument but
    one is a Warehouse where one Position can never be marked, and it looks
    entirely healthy in a listing.
    """
    with WarehouseAdapter() as warehouse:
        warehouse.create_schema()
        for build_name in BUILDS:
            warehouse.run_build(build_name)
        counts = {name: warehouse.row_count(name) for name in warehouse.tables()}
        ((priced_instruments,),) = warehouse.query(
            "SELECT count(DISTINCT instrument_id) FROM fct_instrument_price"
        )
        return counts, priced_instruments


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

    counts, priced_instruments = build_star_schema()

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

    print(
        f"PASS — the Warehouse is built · dim_instrument holds {loaded} "
        f"Instruments · fct_instrument_price holds {prices} Market Prices "
        f"across all {priced_instruments}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
