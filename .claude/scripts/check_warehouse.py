"""Check the Warehouse against Glossary Section B and ADR-0002's commitments.

Run with:  uv run python .claude/scripts/check_warehouse.py
           uv run python .claude/scripts/check_warehouse.py --rebuild

Four checks. None of them was running before Step 002; two were promises made in
an ADR and two are promises made by comments in the schema.

  1. The star schema matches the Glossary. The expected table set is read out of
     Glossary Section B's "Lives in" column rather than typed into this file, so
     registering a term that names a new table fails this check until the Data
     Definition Language (DDL) has that table. A list typed here would only ever
     prove that two files agree with each other.

  2. No floating-point column anywhere in the star schema. ADR-0002 rejected
     SQLite because "monetary aggregation over floats in a project whose entire
     subject is quietly wrong numbers is not a trade worth making". That argument
     is about column types, not only about engines, so it is enforced as one.

  3. The schema's constraints actually fire. Fourteen deliberately invalid rows are
     offered to a throwaway Warehouse held in memory, built from the same
     schema.sql, and every one must be refused — preceded by valid rows as a
     positive control, so the probe cannot pass by rejecting everything.

  4. The seam holds, in both the halves ADR-0002 names. That ADR commits that all
     warehouse access goes through the adapter, and names the signal that it has
     stopped as "a `duckdb` import **or a DuckDB-specific function name** anywhere
     outside the adapter module". Both halves parse rather than grep: a `duckdb`
     in a docstring is prose, and this file is full of it.

       * The import half reads each module's import statements.
       * The dialect half reads each module's SQL — every string literal sqlglot
         parses as a statement — and reports any function name in it that standard
         SQL does not have. Which names those are is derived from sqlglot rather
         than typed here, so the list tracks the library instead of someone's
         memory. Added by Sub-step 2.6, paying DEBT-009.

  5. `--sources` only — what ingestion loaded is what the sources said. Added by
     Sub-step 2.2 and grown by every source since. For `dim_instrument`: no minor
     unit survives, and the loaded Instrument Symbols are exactly the universe
     declared in `veritas/ingestion/universe.py`. For `fct_instrument_price`
     (Sub-step 2.3): every row equals the snapshot's *unadjusted* close on the
     exchange's own trading date, the adjusted series is shown to be a different
     number, and no day-over-day move is large enough to be a corporate action.
     For `fct_fx_rate` (Sub-step 2.4): every rate is the one the European Central
     Bank's (ECB) published quotes imply, the table is dense over calendar dates
     rather than publishing days, every Market Price has a rate on its own date,
     and a currency converted through another and back is unchanged.
     Needs a filled Warehouse, so run `uv run python -m veritas.ingestion` first.

  6. `--distinctions` only — the client side has the shape the design needs.
     Added by Sub-step 2.5, the Sub-step that generated it. Four parts: every
     client-activity row is exactly what the simulator produces from the same
     seed; every quantity is a whole lot of its own Instrument; every Snapshot can
     be marked and at least one Position Change is one no Trade explains; and
     **every pair in Glossary Section C is two different numbers**, printed side by
     side with how far apart they are. A pair that has collapsed fails the run,
     because a distinction the data cannot tell apart is one no evaluation over
     that data can test for. Needs a filled Warehouse.

Exits non-zero if any check fails.
"""

import argparse
import ast
import datetime as dt
import json
import logging
import re
import sys
from decimal import Decimal
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.dialects.duckdb import DuckDB
from sqlglot.parser import Parser

CLAUDE_DIR = Path(__file__).resolve().parent.parent  # <repo>/.claude
REPO_ROOT = CLAUDE_DIR.parent                        # <repo>
GLOSSARY = CLAUDE_DIR / "docs" / "glossary.md"

sys.path.insert(0, str(REPO_ROOT))

from veritas.warehouse import DATABASE_PATH, WarehouseAdapter  # noqa: E402

# sqlglot logs a warning whenever it cannot parse a string and falls back to a
# generic Command node. The dialect scan below offers it every string literal in
# the repository, most of which are English, so that warning is the expected
# outcome for almost all of them rather than news.
logging.getLogger("sqlglot").setLevel(logging.CRITICAL)

# The one directory licensed to know the engine. ADR-0002: the Warehouse Adapter
# "holds the connection and the engine's dialect; nothing DuckDB-specific exists
# outside it".
ADAPTER_DIR = REPO_ROOT / "veritas" / "warehouse"

# Everywhere both halves of the seam scan look. Both roots hold code that could
# reach for the engine directly, and .claude/scripts/ is the likelier of the two
# to be tempted.
CODE_ROOTS = [REPO_ROOT / "veritas", CLAUDE_DIR / "scripts"]

# What makes a string literal SQL rather than a sentence: sqlglot reads it as one
# of these. Anything it reads as a bare column, an identifier, or its generic
# Command fallback is prose that happened to start with a SQL word — "Create the
# star schema and fill its three real tables" is a docstring in this repository.
SQL_STATEMENTS = (
    exp.Select, exp.Union, exp.Insert, exp.Create, exp.Delete, exp.Update,
    exp.Subquery,
)

# The teeth of the dialect scan, checked on every run against SQL written here
# rather than against whatever the repository happens to contain. Without them a
# clean scan proves nothing: it reads the same either way whether the code is
# portable or the name list is empty. Each probe exercises one verdict — a
# standard query is left alone, a name sqlglot files under DuckDB is named, and so
# is a name sqlglot has never heard of. `strftime` and `list_aggregate` are not
# arbitrary: they are the two examples DEBT-009 itself used.
DIALECT_PROBES = (
    ("SELECT count(*) FROM fct_trade", ()),
    ("SELECT strftime(price_date, '%Y') FROM fct_instrument_price", ("STRFTIME",)),
    ("SELECT list_aggregate(quantity, 'sum') FROM fct_trade", ("LIST_AGGREGATE",)),
)

# Where the dialect scan's one fixture exemption applies, as (file, symbol) rather
# than as a symbol on its own.
#
# The scan reads the SQL a module emits, and this file writes SQL in order to test
# the scan — so its own probes have to be excused or the check fails on its own
# test data. What must not follow from that is an exemption claimable by *name*:
# `.claude/scripts/` is a scanned root, so a later script that puts real SQL in a
# tuple called DIALECT_PROBES would take the exemption by accident and the scan
# would go quiet about it. Naming the file closes that, and is the general rule
# CLAUDE.md's Non-Negotiable #4 now states.
FIXTURE_EXEMPTIONS = {
    (".claude/scripts/check_warehouse.py", "DIALECT_PROBES"),
}

# Types that silently lose money. DECIMAL is the only numeric type this schema
# uses for a quantity anyone will ever sum.
FLOATING_POINT = ("DOUBLE", "FLOAT", "REAL")

# Half of the last digit `fct_instrument_price.market_price` stores. A DECIMAL(18,
# 6) built from the source's close is correct exactly when it is within this of
# it; anything further apart is a different number rather than a rounded one.
PRICE_TOLERANCE = Decimal("0.0000005")

# The same rule at `fct_fx_rate.fx_rate`'s two extra digits of scale.
FX_RATE_TOLERANCE = Decimal("0.000000005")

# How far a currency may drift from itself after a round trip through another one.
#
# Converting EUR to JPY and back cannot return exactly the euro it started with:
# both legs are stored to eight decimal places, so the second undoes a *rounded*
# version of the first. The residue is bounded by that rounding rather than by
# anything about markets, and the bound is what makes it a check — a round trip
# that loses real money means the two directions are not reciprocals, which is a
# rate stored the wrong way up rather than a rounding artefact. Half a basis point
# is orders of magnitude above the arithmetic and orders below an inversion.
ROUND_TRIP_TOLERANCE = Decimal("0.00005")

# The day-over-day price ratio above which a move stops being a market move and
# starts being a corporate action. Its ceiling is not a guess: the smallest split
# anyone performs is 2:1, so the threshold has to sit below 2. It sits well below
# rather than just under, so that a refresh pulling a genuine crash into the window
# gets looked at rather than waved through. The headroom between this threshold and
# the largest move actually loaded is printed on every run rather than written
# here, where it would be one snapshot's figure going stale in a comment.
# R14 excluded corporate actions from the slice *on the assumption* that no loaded
# series contains one; this is what turns that assumption into something that
# fails the run. See EXT-007.
SPLIT_RATIO = Decimal("1.5")

problems: list[str] = []


# | Term | Definition | Lives in | Status |  ->  index 3 after splitting on "|",
# because a leading pipe makes cells[0] the empty string before the first column.
LIVES_IN_COLUMN = 3

TABLE_NAME = re.compile(r"(?:dim|fct)_[a-z_]+")


def glossary_tables() -> set[str]:
    """The star schema tables Glossary Section B says exist.

    Read from the "Lives in" cell of each Section B row. Section B is the one that
    describes the warehouse; Section A's "Lives in" cells name directories, not
    tables, which is why the search is scoped to a section rather than the file.

    The cell is read by column position and scanned for *every* table it names,
    because a term can live in more than one — `Denomination Currency` names four.
    An earlier version required the whole cell to be a single table name, which
    silently contributed nothing for that row. It changed no outcome, since all
    four tables are named by other rows too, and that is exactly what made it
    worth fixing: a check that quietly checks less than it claims is worse than
    one that fails, because nothing ever tells you.
    """
    text = GLOSSARY.read_text()
    section = re.search(r"^### B\. The warehouse\n(.*?)^### ", text, re.S | re.M)
    if not section:
        problems.append("glossary.md: could not find the `### B. The warehouse` section")
        return set()

    tables: set[str] = set()
    for line in section.group(1).splitlines():
        cells = line.split("|")
        if len(cells) <= LIVES_IN_COLUMN:
            continue
        cell = cells[LIVES_IN_COLUMN]

        named = TABLE_NAME.findall(cell)
        if not named:
            # A term that lives somewhere other than the Warehouse — a metric in
            # `semantic/metrics/`, or an anti-pattern living nowhere at all.
            continue
        tables.update(named)

        # Whatever is left once the table names, backticks, commas and whitespace
        # are removed is something this parser did not understand. Reporting it
        # is the point: half-reading a cell would shrink the expected set without
        # anyone noticing, which is the failure this function just had.
        residue = TABLE_NAME.sub("", cell).strip(" `,\t")
        if residue:
            problems.append(
                f"glossary.md Section B: only partly understood the 'Lives in' cell "
                f"{cell.strip()!r} — read {sorted(named)} and did not recognise "
                f"{residue!r}"
            )
    return tables


def check_schema(warehouse: WarehouseAdapter) -> None:
    """Every Glossary table exists, nothing else does, and no column is a float."""
    expected = glossary_tables()
    actual = set(warehouse.tables())

    print(f"  Glossary Section B names {len(expected)} tables · "
          f"the Warehouse has {len(actual)}")
    print()

    for table_name in sorted(actual):
        columns = warehouse.columns(table_name)
        print(f"  {table_name}  —  {len(columns)} columns, "
              f"{warehouse.row_count(table_name)} rows")
        for column_name, data_type in columns:
            print(f"      {column_name:<24} {data_type}")
            if any(marker in data_type.upper() for marker in FLOATING_POINT):
                problems.append(
                    f"{table_name}.{column_name} is {data_type} — the star schema "
                    f"holds no floating-point column, because a number nobody can "
                    f"reproduce is the failure this project exists to prevent"
                )
        print()

    for table_name in sorted(expected - actual):
        problems.append(
            f"Glossary Section B names table {table_name!r}, which the schema does "
            f"not create — add it to veritas/warehouse/schema.sql"
        )
    for table_name in sorted(actual - expected):
        problems.append(
            f"the Warehouse holds table {table_name!r}, which no Glossary Section B "
            f"term names — register the term or drop the table"
        )


# A minimal, entirely valid seed. It runs first so that every rejection below
# fails for the reason being probed rather than for a missing parent row, and it
# doubles as the positive control: if the seed itself were rejected, the probe
# would be proving nothing except that inserts do not work.
SEED = [
    "INSERT INTO dim_client VALUES (1, 'Seed Client', 'EU')",
    "INSERT INTO dim_account VALUES (1, 1, 'Seed Account')",
    "INSERT INTO dim_instrument VALUES (1, 'AAPL', 'Apple Inc.', 'equity', 'USD')",
    # One snapshot of each kind, so the duplicates below have something to collide
    # with and the daily grain is probed rather than asserted.
    "INSERT INTO fct_position_snapshot VALUES (DATE '2025-03-03', 1, 1, 100, 4500)",
    "INSERT INTO fct_balance_snapshot VALUES (DATE '2025-03-03', 1, 'USD', 5000)",
    # One movement of each kind, carrying a value from that table's own vocabulary,
    # so the three refusals below prove the lists differ rather than that both
    # columns reject everything.
    "INSERT INTO fct_cash_movement VALUES (1, 1, NULL, DATE '2025-03-03',"
    " 'deposit', 5000, 'USD')",
    "INSERT INTO fct_accounting_movement VALUES (1, 1, NULL, DATE '2025-03-03',"
    " 'realised P&L', 250, 'USD')",
]

# Each of these must be refused by the engine. Every one is a wrong number this
# project has already met: the pence trap and the adjusted-close trap are the two
# `data-availability.md` proved on real data, and the rest are the Section C
# confusions the schema is shaped to make unrepresentable.
REJECTIONS = [
    ("dim_instrument refuses a pence quotation (`GBp`) — the 100x trap",
     "INSERT INTO dim_instrument VALUES (2, 'VOD.L', 'Vodafone', 'equity', 'GBp')"),
    ("dim_instrument refuses an out-of-scope instrument type",
     "INSERT INTO dim_instrument VALUES (3, 'XX', 'A single bond', 'bond', 'USD')"),
    ("dim_client refuses a region the Dimension Definition does not name",
     "INSERT INTO dim_client VALUES (2, 'Wrong Region', 'AMER')"),
    ("fct_trade refuses a trade_side outside 'buy'/'sell', including 'BUY'",
     "INSERT INTO fct_trade VALUES (1, 1, 1, DATE '2025-03-03', DATE '2025-03-05',"
     " 'BUY', 10, 100, 1, 0.5, 0.25, 'USD')"),
    ("fct_trade refuses a negative quantity — direction lives in trade_side",
     "INSERT INTO fct_trade VALUES (2, 1, 1, DATE '2025-03-03', DATE '2025-03-05',"
     " 'sell', -10, 100, 1, 0.5, 0.25, 'USD')"),
    ("fct_trade refuses settlement before trade",
     "INSERT INTO fct_trade VALUES (3, 1, 1, DATE '2025-03-05', DATE '2025-03-03',"
     " 'buy', 10, 100, 1, 0.5, 0.25, 'USD')"),
    ("fct_trade refuses an orphan account_id",
     "INSERT INTO fct_trade VALUES (4, 999, 1, DATE '2025-03-03', DATE '2025-03-05',"
     " 'buy', 10, 100, 1, 0.5, 0.25, 'USD')"),
    ("fct_instrument_price refuses an orphan instrument_id",
     "INSERT INTO fct_instrument_price VALUES (DATE '2025-03-03', 999, 100)"),
    # The two below are what make "snapshot" mean something enforceable rather
    # than something the simulator happens to do. The grain is one row per
    # subject per date, so a second row for the same date is a contradiction —
    # two different answers to "what was held as of 2025-03-03".
    ("fct_position_snapshot refuses a second row for one date, account, instrument",
     "INSERT INTO fct_position_snapshot VALUES (DATE '2025-03-03', 1, 1, 150, 6750)"),
    ("fct_balance_snapshot refuses a second row for one date, account, currency",
     "INSERT INTO fct_balance_snapshot VALUES (DATE '2025-03-03', 1, 'USD', 6000)"),
    # A closed Position that kept its Cost Basis would report Unrealised P&L on a
    # holding of nothing — the wrong number arriving through a stale column rather
    # than through bad arithmetic.
    ("fct_position_snapshot refuses a Cost Basis on a closed Position",
     "INSERT INTO fct_position_snapshot VALUES (DATE '2025-03-04', 1, 1, 0, 4500)"),
    # The two movement vocabularies differ, and the difference *is* the Section C
    # pair. Realised P&L is earned, never received; a deposit is received, never
    # earned. Probing both directions is what stops the two tables drifting into
    # copies of each other.
    ("fct_cash_movement refuses 'realised P&L' — no cash moves when a Position closes",
     "INSERT INTO fct_cash_movement VALUES (2, 1, NULL, DATE '2025-03-03',"
     " 'realised P&L', 250, 'USD')"),
    ("fct_accounting_movement refuses 'deposit' — a deposit earns nothing",
     "INSERT INTO fct_accounting_movement VALUES (2, 1, NULL, DATE '2025-03-03',"
     " 'deposit', 5000, 'USD')"),
    # The exact failure DEBT-010 was opened for: two spellings of one concept
    # splitting a GROUP BY into two plausible-looking rows.
    ("fct_cash_movement refuses 'Deposit' — one spelling per concept",
     "INSERT INTO fct_cash_movement VALUES (3, 1, NULL, DATE '2025-03-03',"
     " 'Deposit', 5000, 'USD')"),
]


def check_constraints() -> None:
    """The schema's constraints actually fire.

    Run against a throwaway in-memory Warehouse built from the same schema.sql, so
    it never touches the real one. Without this the constraints are a claim in a
    comment; ADR-0002's whole argument is that a promise nothing runs is a promise
    that goes stale.
    """
    print("  constraint probe (in-memory Warehouse from the same schema.sql)")
    with WarehouseAdapter.in_memory() as probe:
        probe.create_schema()

        for statement in SEED:
            try:
                probe.execute(statement)
            except Exception as failure:
                problems.append(
                    f"the valid seed row was rejected, so the probe below proves "
                    f"nothing: {statement} -> {type(failure).__name__}: {failure}"
                )
                return
        print(f"    accepted  {len(SEED)} valid seed rows (positive control)")

        for description, statement in REJECTIONS:
            try:
                probe.execute(statement)
            except Exception:
                print(f"    refused   {description}")
            else:
                print(f"    ACCEPTED  {description}")
                problems.append(
                    f"the schema accepted a row it must refuse — {description}"
                )


def check_sources(warehouse: WarehouseAdapter) -> None:
    """What Sub-step 2.2 loaded into `dim_instrument` is what the sources said.

    `check_prices` below is the same idea for Sub-step 2.3's table — one function
    per star table, in the order the Sub-steps built them.

    Two assertions, both of them the plan's, and both aimed at a trap that has
    already been measured rather than imagined:

      1. **No minor unit survives into `dim_instrument`.** The engine's own CHECK
         refuses a code that is not equal to its own upper case, so this cannot
         fail while that constraint stands — which is the point of asserting it
         anyway. The CHECK is a statement about *spelling*; this is a statement
         about *the loaded data*, and it also names the specific codes
         `universe.MINOR_UNIT_CURRENCIES` knows about, which is the half the
         constraint provably cannot catch (`GBX` is already upper case).

      2. **The loaded Instrument Symbols are exactly the declared universe.** A
         symbol whose metadata failed to arrive would otherwise drop out of the
         star build's driving join silently, leaving a smaller Warehouse that
         looks entirely healthy.

    The instrument_type and Quotation Currency distributions are printed but not
    asserted. They are what a reviewer needs to see to judge whether the universe
    is rich enough for Sub-step 2.5, and that judgement is Amino's rather than
    this script's.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from veritas.ingestion.universe import MINOR_UNIT_CURRENCIES, TRADED_INSTRUMENTS

    rows = warehouse.query(
        "SELECT instrument_symbol, instrument_type, quotation_currency "
        "FROM dim_instrument ORDER BY instrument_symbol"
    )
    print(f"  dim_instrument: {len(rows)} rows · "
          f"{len(TRADED_INSTRUMENTS)} Instruments declared in universe.py")

    if not rows:
        problems.append(
            "dim_instrument is empty — run `uv run python -m veritas.ingestion` "
            "before checking sources, or this check passes vacuously"
        )
        return

    # 1. minor units
    minor_units = sorted(MINOR_UNIT_CURRENCIES)
    offenders = [
        (symbol, currency)
        for symbol, _, currency in rows
        if currency != currency.upper() or currency in MINOR_UNIT_CURRENCIES
    ]
    print(f"    minor units: none of {minor_units} survived normalisation"
          if not offenders else f"    minor units: {offenders}")
    for symbol, currency in offenders:
        problems.append(
            f"dim_instrument.{symbol} is quoted in {currency!r}, a minor unit — "
            f"a Market Price in pence booked as pounds is the 100x error the "
            f"Quotation Currency term exists to prevent"
        )

    # 2. the loaded universe is the declared universe
    loaded = [symbol for symbol, _, _ in rows]
    missing = sorted(set(TRADED_INSTRUMENTS) - set(loaded))
    unexpected = sorted(set(loaded) - set(TRADED_INSTRUMENTS))
    duplicated = sorted({s for s in loaded if loaded.count(s) > 1})

    if missing:
        problems.append(
            f"declared in universe.py but absent from dim_instrument: {missing} — "
            f"the metadata fetch dropped a symbol and the star build's driving "
            f"join silently narrowed"
        )
    if unexpected:
        problems.append(f"in dim_instrument but not declared in universe.py: {unexpected}")
    if duplicated:
        problems.append(f"dim_instrument holds a repeated Instrument Symbol: {duplicated}")
    if not (missing or unexpected or duplicated):
        print(f"    symbols: all {len(loaded)} declared Instruments present, none repeated")

    # 3. every source dlt landed actually carries rows.
    #
    # Without this the check has a hole big enough to drive the whole Sub-step
    # through: `instrument_name` falls back through three sources, so an empty
    # `sec_registrant` table would silently produce a complete-looking
    # dim_instrument built from one source instead of three, and every assertion
    # above would still pass. This is the same failure `snapshots.py` refuses at
    # read time, asserted again at the far end where it would actually show up.
    for raw_table in ("nasdaq_symbol", "sec_registrant", "yahoo_instrument",
                      "yahoo_price", "minor_unit_currency",
                      "yahoo_instrument_type"):
        landed = warehouse.row_count(f"raw.{raw_table}")
        print(f"    raw.{raw_table:22} {landed:>6} rows")
        if not landed:
            problems.append(
                f"raw.{raw_table} is empty — the source landed nothing, and "
                f"dim_instrument was built without it rather than failing"
            )

    # 4. the universe is rich enough for the Sub-step that will query it.
    #
    # Sub-step 2.5 generates the client activity that makes every Section C
    # distinction a different number, and it can only be as rich as the Instruments
    # it has to trade. A universe that satisfies the Glossary on paper — one row of
    # each kind — produces a Warehouse where slicing by instrument type is really
    # slicing by one company, and no amount of simulator cleverness fixes that
    # afterwards. Asserting it here means the gap is found while widening the
    # universe is still one line in universe.py, rather than in 2.5 where it means
    # regenerating everything downstream.
    counts_by: dict[str, dict[str, int]] = {}
    for label, index in (("instrument_type", 1), ("quotation_currency", 2)):
        counted: dict[str, int] = {}
        for row in rows:
            counted[row[index]] = counted.get(row[index], 0) + 1
        counts_by[label] = counted
        spread = " · ".join(f"{value} {count}" for value, count in sorted(counted.items()))
        print(f"    {label}: {spread}")

    from veritas.ingestion.universe import YAHOO_INSTRUMENT_TYPES

    types = counts_by["instrument_type"]
    currencies = counts_by["quotation_currency"]

    absent_types = sorted(set(YAHOO_INSTRUMENT_TYPES.values()) - set(types))
    if absent_types:
        problems.append(
            f"no Instrument of type {absent_types} — the 'by instrument type' "
            f"Dimension Definition names an axis the data cannot slice on"
        )

    # Two of each kind, not one. One is indistinguishable from a special case: a
    # metric sliced to that type returns that single security's numbers, so the
    # slice proves nothing about the type.
    thin_types = sorted(value for value, count in types.items() if count < 2)
    if thin_types:
        problems.append(
            f"only one Instrument of type {thin_types} — slicing a metric by that "
            f"type would return one security's numbers, so Sub-step 2.5 cannot "
            f"make it a distinction. Add a second in universe.py"
        )

    if len(currencies) < 3:
        problems.append(
            f"only {len(currencies)} Quotation Currencies "
            f"({sorted(currencies)}) — FX conversion to the Reporting Currency "
            f"needs several to be more than a formality"
        )

    normalised = {
        mapping["major_unit_currency"] for mapping in MINOR_UNIT_CURRENCIES.values()
    }
    if not (normalised & set(currencies)):
        problems.append(
            f"no Instrument normalised from a minor unit — nothing carries the "
            f"100x trap into the fact tables, so Sub-steps 2.3 and 2.5 exercise "
            f"it nowhere"
        )

    if not any(
        problem.startswith(("no Instrument", "only ")) for problem in problems
    ):
        print(f"    richness: {len(types)} types (min {min(types.values())} each) · "
              f"{len(currencies)} currencies · minor unit normalised")


# The correct reading of a Yahoo chart snapshot, and the three wrong ones the
# build script is written to avoid. Each wrong reading is a real mistake with a
# name — one of them is the Section C row for Market Price against Adjusted Close,
# and the other two are what `fct_instrument_price.sql`'s two transforms exist for.
#
# They are here because an assertion that nothing violates proves nothing. Passing
# "every row equals the unadjusted close on the exchange's own date" is only
# evidence if the wrong answers would have been *different* answers, and this is
# what measures that on the loaded data rather than assuming it.
WRONG_READINGS = {
    "adjusted close": "takes indicators.adjclose instead of indicators.quote",
    "UTC date": "reads a bar's timestamp as a Coordinated Universal Time (UTC) "
                "date rather than shifting it onto the exchange's clock",
    "pence left as pounds": "skips the division by minor_units_per_major",
}


def expected_prices(wrong_reading: str | None = None) -> dict[tuple[str, dt.date], Decimal]:
    """Re-derive the Market Price series from the committed snapshots, in Python.

    **This is deliberately a second implementation of
    `veritas/warehouse/builds/fct_instrument_price.sql`, not a call into it.** The
    build applies three transforms — an exchange-local trading date, a minor-unit
    division, and the dropping of a session still in progress — and a check that
    reused the build's own SQL could only ever prove that the SQL agrees with
    itself. Written twice, in two languages, a disagreement is a real one.

    With no argument it returns what the Warehouse should hold. Passing one of
    `WRONG_READINGS` returns what it would hold if that mistake had been made.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from veritas.ingestion.snapshots import SNAPSHOT_DIR
    from veritas.ingestion.universe import MINOR_UNIT_CURRENCIES, TRADED_INSTRUMENTS

    if wrong_reading is not None and wrong_reading not in WRONG_READINGS:
        raise ValueError(f"unknown reading {wrong_reading!r} — have {list(WRONG_READINGS)}")

    series: dict[tuple[str, dt.date], Decimal] = {}
    for symbol in TRADED_INSTRUMENTS:
        result = json.loads(
            (SNAPSHOT_DIR / f"yahoo-chart-{symbol}.json").read_bytes()
        )["chart"]["result"][0]
        meta = result["meta"]

        offset = 0 if wrong_reading == "UTC date" else meta["gmtoffset"]
        factor = (
            1
            if wrong_reading == "pence left as pounds"
            else MINOR_UNIT_CURRENCIES.get(meta["currency"], {}).get(
                "minor_units_per_major", 1
            )
        )

        # The bar for a session that had not closed when the snapshot was taken.
        # `None` when the response was taken outside trading hours, in which case
        # every bar it holds is a genuine close.
        session_end = meta["currentTradingPeriod"]["regular"]["end"]
        open_date = (
            dt.datetime.fromtimestamp(session_end + offset, dt.UTC).date()
            if meta["regularMarketTime"] < session_end
            else None
        )

        closes = (
            result["indicators"]["adjclose"][0]["adjclose"]
            if wrong_reading == "adjusted close"
            else result["indicators"]["quote"][0]["close"]
        )
        for stamp, close in zip(result["timestamp"], closes):
            if close is None:
                continue
            price_date = dt.datetime.fromtimestamp(stamp + offset, dt.UTC).date()
            if price_date == open_date:
                continue
            series[(meta["symbol"], price_date)] = Decimal(repr(close / factor))
    return series


def rows_changed(
    stored: dict[tuple[object, ...], Decimal],
    alternative: dict[tuple[object, ...], Decimal],
    tolerance: Decimal,
) -> tuple[int, set[object]]:
    """How many rows an alternative reading would change, and for which subjects.

    A row counts as changed when the two disagree about its value *or* when only
    one of them has it at all — a date shifted by a time zone removes one row and
    adds another, and both are the Warehouse holding a price on a day the
    Instrument did not close at it. The same is true of a rate that was never
    filled forward: the row is absent rather than wrong, which is the more
    dangerous of the two because a join simply returns nothing.

    Keyed by a tuple whose **first element is the subject** — the Instrument Symbol
    for a price, the from-currency for a rate — because that is what the caller
    reports the spread across. Everything after it is what makes the key unique.
    """
    changed: set[tuple[object, ...]] = set()
    for key in set(stored) | set(alternative):
        here, there = stored.get(key), alternative.get(key)
        if here is None or there is None or abs(here - there) > tolerance:
            changed.add(key)
    return len(changed), {key[0] for key in changed}


def check_prices(warehouse: WarehouseAdapter) -> None:
    """`fct_instrument_price` holds the unadjusted close, on the right date, in
    the major unit — and the window it covers contains no corporate action.

    Three assertions, all of them Sub-step 2.3's:

      1. **Every row is the snapshot's unadjusted close**, re-derived
         independently by `expected_prices`. This is one assertion covering four
         ways to be wrong: the adjusted series, a date shifted by a time zone, a
         pence quote carried across as pounds, and a mid-session bar stored as a
         close.
      2. **Each of those wrong readings would have produced different rows**, and
         how many is printed. Without this, assertion 1 could be passing because
         the readings happen to agree on this universe, and the traps it exists to
         catch would be untested while looking tested.
      3. **No day-over-day move is large enough to be a corporate action.**
    """
    rows = warehouse.query(
        "SELECT instrument.instrument_symbol, price.price_date, price.market_price "
        "FROM fct_instrument_price AS price "
        "JOIN dim_instrument AS instrument "
        "  ON instrument.instrument_id = price.instrument_id "
        "ORDER BY instrument.instrument_symbol, price.price_date"
    )
    if not rows:
        print("  fct_instrument_price: empty")
        problems.append(
            "fct_instrument_price is empty — run `uv run python -m "
            "veritas.ingestion` before checking sources, or this check passes "
            "vacuously"
        )
        return

    symbols = {symbol for symbol, _, _ in rows}
    dates = {price_date for _, price_date, _ in rows}
    print(f"  fct_instrument_price: {len(rows)} rows · {len(symbols)} Instruments "
          f"· {len(dates)} distinct dates ({min(dates)} to {max(dates)})")

    # 1. every stored price is the snapshot's unadjusted close, on the exchange's
    #    own date, in the major unit.
    expected = expected_prices()
    stored = {(symbol, price_date): price for symbol, price_date, price in rows}

    missing = sorted(set(expected) - set(stored))
    extra = sorted(set(stored) - set(expected))
    wrong = [
        (symbol, price_date, price, expected[(symbol, price_date)])
        for (symbol, price_date), price in sorted(stored.items())
        if (symbol, price_date) in expected
        and abs(price - expected[(symbol, price_date)]) > PRICE_TOLERANCE
    ]

    for symbol, price_date in missing[:5]:
        problems.append(
            f"the snapshot holds a close for {symbol} on {price_date} that "
            f"fct_instrument_price does not — the build dropped a trading day"
        )
    for symbol, price_date in extra[:5]:
        problems.append(
            f"fct_instrument_price holds {symbol} on {price_date}, which the "
            f"snapshot has no closing price for — a date shifted by a time zone, "
            f"or a session still in progress stored as a close"
        )
    for symbol, price_date, price, want in wrong[:5]:
        problems.append(
            f"fct_instrument_price has {symbol} on {price_date} at {price}, but "
            f"the snapshot's unadjusted close is {want} — a factor of "
            f"{want / price if price else 'infinity'}"
        )
    if not (missing or extra or wrong):
        print(f"    values: all {len(rows)} rows equal the snapshot's unadjusted "
              f"close, on the exchange's own date, in the major unit")
    else:
        print(f"    values: {len(missing)} missing · {len(extra)} unexpected · "
              f"{len(wrong)} wrong (first 5 of each reported)")

    # 2. each wrong reading would have produced different rows. The first of them
    #    is the Adjusted Close trap `check_data_availability.py` measured on three
    #    probe series; this measures all three on everything actually loaded, so
    #    they are proven against the data the Warehouse holds rather than a sample.
    for reading, description in WRONG_READINGS.items():
        changed, affected = rows_changed(
            stored, expected_prices(reading), PRICE_TOLERANCE
        )
        share = 100 * changed / len(rows)
        print(f"    if it {description}:")
        print(f"      {changed}/{len(rows)} rows change ({share:.0f}%), "
              f"across {len(affected)} of {len(symbols)} Instruments")
        if not changed:
            problems.append(
                f"reading the snapshots the wrong way — it {description} — would "
                f"change no row, so the assertion above passes whether the build "
                f"is right or not and this universe cannot test it"
            )

    # 3. no corporate action inside the window.
    by_symbol: dict[str, list[tuple[dt.date, Decimal]]] = {}
    for symbol, price_date, price in rows:
        by_symbol.setdefault(symbol, []).append((price_date, price))

    largest = (Decimal(0), "", None)
    for symbol, series in by_symbol.items():
        for (_, before), (after_date, after) in zip(series, series[1:]):
            if not before:
                continue
            ratio = max(after / before, before / after)
            if ratio > largest[0]:
                largest = (ratio, symbol, after_date)
            if ratio > SPLIT_RATIO:
                problems.append(
                    f"{symbol} moved by a ratio of {ratio:.3f} into {after_date} "
                    f"({before} to {after}) — larger than {SPLIT_RATIO}, so it is "
                    f"a split or another corporate action rather than a market "
                    f"move. R14 excluded those from the slice, so this window "
                    f"cannot be loaded: swap the symbol in universe.py or shorten "
                    f"the range (see EXT-007)"
                )
    ratio, symbol, when = largest
    print(f"    corporate actions: largest day-over-day ratio is {ratio:.3f} "
          f"({symbol} into {when}), against a {SPLIT_RATIO} threshold")

    # Coverage, printed rather than asserted. Sub-step 2.5 writes a Snapshot on
    # every date the Warehouse holds a Market Price (R13), and these Instruments
    # sit on five exchange calendars, so the dates they share are fewer than the
    # dates they cover. Which of the two 2.5 uses is 2.5's decision; being
    # surprised by the gap is what this print exists to prevent.
    shared = sum(
        1 for day in dates
        if all(day in {d for d, _ in series} for series in by_symbol.values())
    )
    print(f"    calendars: {len(dates)} dates have a price for at least one "
          f"Instrument · {shared} have one for all "
          f"{len(by_symbol)} (Sub-step 2.5 chooses between them)")


# The correct reading of the Frankfurter snapshot, and the two wrong ones
# `fct_fx_rate.sql` is written to avoid. Same idea as WRONG_READINGS above: an
# assertion that nothing violates proves nothing, so each wrong answer is shown to
# be a *different* answer on the data actually loaded.
WRONG_FX_READINGS = {
    "left non-publishing dates empty": "stores only the dates the ECB published "
                                       "on, instead of filling a rate forward "
                                       "across weekends and ECB holidays",
    "stored every rate upside down": "reads a published rate as euros per unit "
                                     "of currency rather than currency per euro",
}


def expected_fx_rates(
    wrong_reading: str | None = None,
) -> dict[tuple[str, str, dt.date], Decimal]:
    """Re-derive `fct_fx_rate` from the committed snapshots, in Python.

    **A second implementation of `veritas/warehouse/builds/fct_fx_rate.sql`, not a
    call into it**, for the same reason `expected_prices` is one: the build derives
    a dense grid of ordered pairs from a sparse list of EUR quotes, and a check
    that reused its SQL could only prove the SQL agrees with itself.

    It reproduces all three of the build's transforms independently — the base
    currency's row against itself, the fill-forward, and the pair arithmetic — and
    it takes the window and the currency set from the same two places the build
    does, without going near the Warehouse: the currencies from the Yahoo metadata
    (normalised out of any minor unit) plus the base the source publishes against,
    and the window end from `expected_prices`, which re-derives the price series
    from the snapshots as well.

    With no argument it returns what the Warehouse should hold. Passing one of
    `WRONG_FX_READINGS` returns what it would hold if that mistake had been made.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from veritas.ingestion.snapshots import SNAPSHOT_DIR
    from veritas.ingestion.universe import MINOR_UNIT_CURRENCIES, TRADED_INSTRUMENTS

    if wrong_reading is not None and wrong_reading not in WRONG_FX_READINGS:
        raise ValueError(
            f"unknown reading {wrong_reading!r} — have {list(WRONG_FX_READINGS)}"
        )

    response = json.loads((SNAPSHOT_DIR / "frankfurter-rates.json").read_bytes())
    base_currency = response["base"]

    # The Quotation Currency of every traded Instrument, read from the same meta
    # block dim_instrument was built from and normalised the same way — GBp is a
    # minor unit of GBP, and no reference rate is published for pence.
    quoted = {base_currency}
    for symbol in TRADED_INSTRUMENTS:
        currency = json.loads(
            (SNAPSHOT_DIR / f"yahoo-chart-{symbol}.json").read_bytes()
        )["chart"]["result"][0]["meta"]["currency"]
        quoted.add(
            MINOR_UNIT_CURRENCIES.get(currency, {}).get("major_unit_currency", currency)
        )

    published: dict[dt.date, dict[str, float]] = {}
    for day, rates in response["rates"].items():
        on_date = {
            currency: rate for currency, rate in rates.items() if currency in quoted
        }
        on_date[base_currency] = 1.0
        published[dt.date.fromisoformat(day)] = on_date

    price_dates = {price_date for _, price_date in expected_prices()}
    start = min(published)
    end = max(max(published), max(price_dates))

    rates_by_date: dict[tuple[str, str, dt.date], Decimal] = {}
    in_force: dict[str, float] = {}
    day = start
    while day <= end:
        if day in published:
            in_force = published[day]
        elif wrong_reading == "left non-publishing dates empty":
            day += dt.timedelta(days=1)
            continue
        for from_currency, from_rate in in_force.items():
            for to_currency, to_rate in in_force.items():
                pair = (
                    from_rate / to_rate
                    if wrong_reading == "stored every rate upside down"
                    else to_rate / from_rate
                )
                rates_by_date[(from_currency, to_currency, day)] = Decimal(repr(pair))
        day += dt.timedelta(days=1)
    return rates_by_date


def check_fx_rates(warehouse: WarehouseAdapter) -> None:
    """`fct_fx_rate` is the ECB's published rates, dense over calendar dates, in
    both directions — and every Market Price the Warehouse holds can be converted.

    Four assertions, all of them Sub-step 2.4's:

      1. **Every row is derived from the snapshot's published rates**, re-derived
         independently by `expected_fx_rates`. One assertion covering the whole
         build: a missing fill-forward, an inverted quote, a currency dropped on
         the way through, or a window that stops short all surface here.
      2. **Each wrong reading would have produced different rows.**
      3. **Every Market Price has a rate on its own date**, for the currency it is
         quoted in. This is the one that matters to the Warehouse rather than to
         this table: a price with no rate is a Position that can be marked and not
         reported, and the two windows drift apart on their own, because Yahoo and
         the ECB publish on different calendars and at different times of day.
      4. **A currency converted through another and back is the currency it
         started as**, within the rounding the stored scale forces. An inverted
         pair passes assertion 1 nowhere, but this is what makes the *direction* of
         every stored rate testable without a second FX source to compare against.
    """
    rows = warehouse.query(
        "SELECT from_currency, to_currency, rate_date, fx_rate "
        "FROM fct_fx_rate ORDER BY rate_date, from_currency, to_currency"
    )
    if not rows:
        print("  fct_fx_rate: empty")
        problems.append(
            "fct_fx_rate is empty — run `uv run python -m veritas.ingestion` "
            "before checking sources, or this check passes vacuously"
        )
        return

    currencies = {from_currency for from_currency, _, _, _ in rows}
    dates = {rate_date for _, _, rate_date, _ in rows}
    print(f"  fct_fx_rate: {len(rows)} rows · {len(currencies)} currencies "
          f"({' '.join(sorted(currencies))}) · {len(dates)} dates "
          f"({min(dates)} to {max(dates)})")

    # 1. every stored rate is the one the snapshot's published rates imply.
    expected = expected_fx_rates()
    stored = {
        (from_currency, to_currency, rate_date): rate
        for from_currency, to_currency, rate_date, rate in rows
    }

    missing = sorted(set(expected) - set(stored))
    extra = sorted(set(stored) - set(expected))
    wrong = [
        (key, rate, expected[key])
        for key, rate in sorted(stored.items())
        if key in expected and abs(rate - expected[key]) > FX_RATE_TOLERANCE
    ]

    for from_currency, to_currency, rate_date in missing[:5]:
        problems.append(
            f"the snapshot implies a rate for {from_currency}->{to_currency} on "
            f"{rate_date} that fct_fx_rate does not hold — a date the fill-forward "
            f"skipped, or a currency dropped on the way through"
        )
    for from_currency, to_currency, rate_date in extra[:5]:
        problems.append(
            f"fct_fx_rate holds {from_currency}->{to_currency} on {rate_date}, "
            f"which the snapshot implies no rate for — a window wider than the "
            f"source published for, filled from nothing"
        )
    for (from_currency, to_currency, rate_date), rate, want in wrong[:5]:
        problems.append(
            f"fct_fx_rate has {from_currency}->{to_currency} on {rate_date} at "
            f"{rate}, but the published rates imply {want}"
        )
    if not (missing or extra or wrong):
        published_dates = len({
            key[2] for key in expected_fx_rates("left non-publishing dates empty")
        })
        print(f"    values: all {len(rows)} rows equal the rate the ECB's published "
              f"quotes imply · {published_dates} of {len(dates)} dates were "
              f"published on, the rest filled forward")
    else:
        print(f"    values: {len(missing)} missing · {len(extra)} unexpected · "
              f"{len(wrong)} wrong (first 5 of each reported)")

    # 2. each wrong reading would have produced different rows.
    for reading, description in WRONG_FX_READINGS.items():
        changed, affected = rows_changed(
            stored, expected_fx_rates(reading), FX_RATE_TOLERANCE
        )
        share = 100 * changed / len(rows)
        print(f"    if it {description}:")
        print(f"      {changed}/{len(rows)} rows change ({share:.0f}%), "
              f"across {len(affected)} of {len(currencies)} currencies")
        if not changed:
            problems.append(
                f"reading the snapshot the wrong way — it {description} — would "
                f"change no row, so the assertion above passes whether the build "
                f"is right or not"
            )

    # 3. every Market Price can be converted. Asked of the Warehouse rather than of
    #    the snapshots, because this is a question about two tables agreeing with
    #    each other and not about either one matching its source.
    uncovered = warehouse.query(
        "SELECT instrument.quotation_currency, min(price.price_date), "
        "       max(price.price_date), count(*) "
        "FROM fct_instrument_price AS price "
        "JOIN dim_instrument AS instrument "
        "  ON instrument.instrument_id = price.instrument_id "
        "LEFT JOIN fct_fx_rate AS rate "
        "  ON rate.rate_date = price.price_date "
        " AND rate.from_currency = instrument.quotation_currency "
        "WHERE rate.fx_rate IS NULL "
        "GROUP BY instrument.quotation_currency"
    )
    for currency, first, last, count in uncovered:
        problems.append(
            f"{count} Market Prices quoted in {currency} have no FX Rate on their "
            f"own date ({first} to {last}) — a Position marked at them cannot "
            f"reach a Reporting Currency. Either the FX window no longer covers "
            f"the price window, or {currency} is not a currency the ECB publishes"
        )
    if not uncovered:
        ((price_first, price_last),) = warehouse.query(
            "SELECT min(price_date), max(price_date) FROM fct_instrument_price"
        )
        print(f"    coverage: every Market Price ({price_first} to {price_last}) "
              f"has a rate in its own Quotation Currency on its own date")

    # 4. a round trip through another currency returns what it started as.
    round_trips = warehouse.query(
        "SELECT out.from_currency, out.to_currency, max(abs(out.fx_rate * "
        "       back.fx_rate - 1)) "
        "FROM fct_fx_rate AS out "
        "JOIN fct_fx_rate AS back "
        "  ON back.rate_date = out.rate_date "
        " AND back.from_currency = out.to_currency "
        " AND back.to_currency = out.from_currency "
        "GROUP BY out.from_currency, out.to_currency "
        "ORDER BY 3 DESC"
    )
    worst_pair, worst_back, worst = round_trips[0]
    for from_currency, to_currency, drift in round_trips:
        if drift > ROUND_TRIP_TOLERANCE:
            problems.append(
                f"converting {from_currency} to {to_currency} and back changes it "
                f"by {drift} on at least one date, more than the {ROUND_TRIP_TOLERANCE} "
                f"the stored scale can explain — the two directions are not "
                f"reciprocals, so one of them is stored upside down"
            )
    print(f"    round trip: worst drift over {len(round_trips)} ordered pairs is "
          f"{worst} ({worst_pair} to {worst_back} and back), against a "
          f"{ROUND_TRIP_TOLERANCE} tolerance")


# -- Sub-step 2.5: the client side, and the pairs it exists to keep apart ------

# The Reporting Currency every monetary figure below is expressed in. `Reporting
# Currency` is registered as *"the single currency a Grounded Answer is expressed
# in. Every monetary metric must state one"* — this check answers monetary
# questions, so it states one. The euro, because `fct_fx_rate` derives every pair
# through it, so a euro figure is one stored rate away from a published one.
REPORTING_CURRENCY = "EUR"

# How far apart the two sides of a Section C pair must be before the pair counts
# as separated, as a share of the larger side.
#
# Equality is the wrong bar. Two numbers that differ in the sixth decimal place
# are technically distinct and tell a reader nothing: a Gold Question Set built on
# them could not distinguish a model that confused the pair from one that did not,
# which is the whole reason the plan requires "every Section C distinction is a
# different number". Half a percent is the floor for "a human would notice".
#
# It is deliberately *not* the 1% line DEBT-004 names. That entry is about one
# specific pair being a reliable evaluation signal; this is the floor for the pair
# existing at all.
MIN_DISTINCTION_GAP = Decimal("0.005")

# Every client-activity table, the simulator output it is built from, and the
# columns that must match. The SQL is written out per table rather than assembled
# from the column tuple: this script sits outside veritas/warehouse/, and building
# a statement out of names here is the construct ADR-0002 tells even the adapter to
# avoid.
CLIENT_ACTIVITY_TABLES = (
    (
        "dim_client",
        "simulated_client",
        ("client_id", "client_name", "client_region"),
        "SELECT client_id, client_name, client_region "
        "FROM dim_client ORDER BY client_id",
    ),
    (
        "dim_account",
        "simulated_account",
        ("account_id", "client_id", "account_name"),
        "SELECT account_id, client_id, account_name "
        "FROM dim_account ORDER BY account_id",
    ),
    (
        "fct_trade",
        "simulated_trade",
        ("trade_id", "account_id", "instrument_id", "trade_date", "settlement_date",
         "trade_side", "quantity", "execution_price", "commission", "fee", "rebate",
         "denomination_currency"),
        "SELECT trade_id, account_id, instrument_id, trade_date, settlement_date, "
        "       trade_side, quantity, execution_price, commission, fee, rebate, "
        "       denomination_currency "
        "FROM fct_trade ORDER BY trade_id",
    ),
    (
        "fct_cash_movement",
        "simulated_cash_movement",
        ("cash_movement_id", "account_id", "trade_id", "movement_date",
         "movement_type", "amount", "denomination_currency"),
        "SELECT cash_movement_id, account_id, trade_id, movement_date, "
        "       movement_type, amount, denomination_currency "
        "FROM fct_cash_movement ORDER BY cash_movement_id",
    ),
    (
        "fct_accounting_movement",
        "simulated_accounting_movement",
        ("accounting_movement_id", "account_id", "trade_id", "movement_date",
         "movement_type", "amount", "denomination_currency"),
        "SELECT accounting_movement_id, account_id, trade_id, movement_date, "
        "       movement_type, amount, denomination_currency "
        "FROM fct_accounting_movement ORDER BY accounting_movement_id",
    ),
    (
        "fct_position_snapshot",
        "simulated_position_snapshot",
        ("snapshot_date", "account_id", "instrument_id", "quantity", "cost_basis"),
        "SELECT snapshot_date, account_id, instrument_id, quantity, cost_basis "
        "FROM fct_position_snapshot "
        "ORDER BY snapshot_date, account_id, instrument_id",
    ),
    (
        "fct_balance_snapshot",
        "simulated_balance_snapshot",
        ("snapshot_date", "account_id", "denomination_currency", "cash_balance"),
        "SELECT snapshot_date, account_id, denomination_currency, cash_balance "
        "FROM fct_balance_snapshot "
        "ORDER BY snapshot_date, account_id, denomination_currency",
    ),
)


def share(part: Decimal, whole: Decimal) -> Decimal:
    """`part` as a share of `whole`, or zero if there is no whole."""
    return part / whole if whole else Decimal("0")


def gap(left: Decimal, right: Decimal) -> Decimal:
    """How far apart two figures are, as a share of the larger."""
    return share(abs(left - right), max(abs(left), abs(right)))


def distinction(
    row: str,
    left_label: str,
    left: Decimal,
    right_label: str,
    right: Decimal,
    *,
    unit: str = REPORTING_CURRENCY,
    minimum: Decimal = MIN_DISTINCTION_GAP,
) -> None:
    """Print both sides of one Section C row, and fail if they have collapsed.

    The pair is named by the Glossary's own words, so a reader can put the figure
    next to the sentence it is evidence for.
    """
    apart = gap(left, right)
    print(f"    {row}")
    print(f"      {left_label}: {left:,.2f} {unit}".rstrip())
    print(f"      {right_label}: {right:,.2f} {unit}".rstrip())
    print(f"      {apart:.2%} apart")
    if apart < minimum:
        problems.append(
            f"Section C pair '{row}' has collapsed: {left_label} is {left:,.2f} "
            f"and {right_label} is {right:,.2f}, {apart:.4%} apart against a "
            f"{minimum:.2%} floor. A pair the data cannot tell apart is a "
            f"distinction the Gold Question Set cannot test for"
        )


def check_client_activity(warehouse: WarehouseAdapter) -> None:
    """Every client-activity row is exactly what the simulator produces.

    The same re-derive-and-compare shape as `check_prices` and `check_fx_rates`
    above, and it is worth being precise about what it does and does not prove,
    because the two cases differ.

    A Market Price has an **independent** source of truth: the committed snapshot
    is what Yahoo said, so re-deriving a price in Python and comparing it to what
    the SQL built genuinely tests the SQL. The client side has no such source —
    the simulator *is* the source. So this proves two narrower things, both of
    which are load-bearing and neither of which is "the simulated numbers are
    right":

      1. **The simulation is deterministic.** Re-running it against the same
         Warehouse produces the same rows, so the seed is the only thing that
         decides what is in these seven tables. Without this the plan's
         requirement — *"two runs from the same seed produce identical row counts
         and identical distinction figures"* — is a claim nobody has checked.
      2. **Nothing was lost or reshaped between the simulator and the star
         schema.** dlt's inference and the seven build scripts' casts sit between
         them, and a DECIMAL that arrived with the wrong scale, a date that became
         a timestamp or a null `trade_id` that became a zero would all show up
         here as a row that differs.

    Whether the *shape* of the generated activity is any good is what
    `check_distinctions` measures, and Amino's review is what judges it.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from veritas.ingestion import simulator

    market = simulator.read_market_data(warehouse)
    regenerated = simulator.simulate(market)
    print(f"  client activity: regenerated from seed {simulator.SEED} against "
          f"{len(market.snapshot_dates)} Snapshot dates")

    for table_name, raw_name, columns, sql in CLIENT_ACTIVITY_TABLES:
        loaded = warehouse.query(sql)
        rows = regenerated[raw_name]
        expected = sorted(
            (tuple(row[column] for column in columns) for row in rows),
            # Sorted into the order the query above asks for. Every `ORDER BY` in
            # CLIENT_ACTIVITY_TABLES leads with that table's primary key, and a
            # primary key is unique, so ordering the simulator's rows by the whole
            # tuple lands them in the same order — the columns after the key never
            # get to break a tie, because there are no ties.
            #
            # `(value is None, value)` rather than `value` because `trade_id` is
            # NULL on every Cash Movement no Trade explains — a deposit, a
            # withdrawal — and Python refuses to compare None with an int. It sorts
            # None last, which is also where the engine puts it.
            key=lambda values: tuple((value is None, value) for value in values),
        )
        if len(loaded) != len(expected):
            problems.append(
                f"{table_name} holds {len(loaded)} rows and the simulator "
                f"produces {len(expected)} from the same seed — either the "
                f"simulation is not deterministic or the build script dropped rows"
            )
            continue

        print(f"    {table_name:24} {len(loaded):>6} rows · identical")

        differing = [
            (built, made)
            for built, made in zip(loaded, expected)
            if list(built) != list(made)
        ]
        if differing:
            built, made = differing[0]
            problems.append(
                f"{table_name}: {len(differing)} of {len(loaded)} rows differ from "
                f"what the simulator produces from the same seed. First: the "
                f"Warehouse holds {built} and the simulator made {made}"
            )


def check_distinctions(warehouse: WarehouseAdapter) -> None:
    """Every Section C pair is two different numbers on the loaded data.

    Section C is headed *"Distinctions we must not blur"*, and says why the whole
    project turns on them: confusing one for another produces *"a correct program
    computing the wrong number — the failure that is hardest to notice and most
    expensive to trust"*. A Warehouse where the two sides of a pair happen to be
    equal cannot catch that failure, and no evaluation over it can either.

    So this is not a check that the arithmetic works. It is a check that the
    **data has the shape the design needs**: that a question about Gross Revenue
    and the same question about Net Revenue come back with different answers.

    One pair is absent because it is checked elsewhere on better evidence:
    `Adjusted Close` against `Market Price` is market data, not client activity,
    and `--sources` measures it against the committed snapshots.
    """
    if not warehouse.row_count("fct_trade"):
        problems.append(
            "fct_trade is empty — run `uv run python -m veritas.ingestion` before "
            "checking distinctions, or every pair below collapses to zero against "
            "zero and this check passes vacuously"
        )
        return

    # Every Trade, with the three rates a Trade needs to be valued: its billing
    # currency on Trade Date and again on Settlement Date, and its Instrument's
    # Quotation Currency on Trade Date. Joined rather than looked up per row, so
    # that a missing rate removes the Trade from the result and shows up as a
    # count mismatch rather than as a silently smaller total.
    trades = warehouse.query(
        "SELECT trade.trade_id, trade.account_id, account.client_id, "
        "       trade.trade_date, trade.settlement_date, trade.trade_side, "
        "       trade.quantity, trade.execution_price, trade.commission, "
        "       trade.fee, trade.rebate, price.market_price, "
        "       billed_on_trade.fx_rate, billed_on_settlement.fx_rate, "
        "       quoted_on_trade.fx_rate "
        "FROM fct_trade AS trade "
        "JOIN dim_account AS account "
        "  ON account.account_id = trade.account_id "
        "JOIN dim_instrument AS instrument "
        "  ON instrument.instrument_id = trade.instrument_id "
        "JOIN fct_instrument_price AS price "
        "  ON price.price_date = trade.trade_date "
        " AND price.instrument_id = trade.instrument_id "
        "JOIN fct_fx_rate AS billed_on_trade "
        "  ON billed_on_trade.rate_date = trade.trade_date "
        " AND billed_on_trade.from_currency = trade.denomination_currency "
        " AND billed_on_trade.to_currency = ? "
        "JOIN fct_fx_rate AS billed_on_settlement "
        "  ON billed_on_settlement.rate_date = trade.settlement_date "
        " AND billed_on_settlement.from_currency = trade.denomination_currency "
        " AND billed_on_settlement.to_currency = ? "
        "JOIN fct_fx_rate AS quoted_on_trade "
        "  ON quoted_on_trade.rate_date = trade.trade_date "
        " AND quoted_on_trade.from_currency = instrument.quotation_currency "
        " AND quoted_on_trade.to_currency = ? "
        "ORDER BY trade.trade_id",
        [REPORTING_CURRENCY] * 3,
    )
    total_trades = warehouse.row_count("fct_trade")
    print(f"  {len(trades)} of {total_trades} Trades priced and converted to "
          f"{REPORTING_CURRENCY}")
    if len(trades) != total_trades:
        problems.append(
            f"only {len(trades)} of {total_trades} Trades could be valued in "
            f"{REPORTING_CURRENCY} — a Trade with no Market Price on its Trade "
            f"Date, or no FX Rate on one of its two dates, is a Trade no monetary "
            f"metric can include and none of the figures below counts"
        )

    gross = net = Decimal("0")
    gross_at_settlement = Decimal("0")
    notional_executed = notional_at_close = Decimal("0")
    notional_unconverted = Decimal("0")
    by_account: dict[int, list[Decimal]] = {}
    by_client: dict[int, Decimal] = {}
    fills_away_from_close = 0
    largest_fill_gap = Decimal("0")
    # The same Gross Revenue, bucketed by each of a Trade's two dates. Only the
    # date column differs between them — the amount and the rate are identical —
    # so the gap between the two is exactly what a period filter moves.
    by_trade_month: dict[tuple[int, int], Decimal] = {}
    by_settlement_month: dict[tuple[int, int], Decimal] = {}

    for (_, account_id, client_id, trade_date, settlement, _, quantity,
         execution_price, commission, fee, rebate, market_price, billed,
         billed_later, quoted) in trades:
        if execution_price != market_price:
            fills_away_from_close += 1
        largest_fill_gap = max(largest_fill_gap, gap(execution_price, market_price))
        earned_here = commission * billed
        for buckets, when in (
            (by_trade_month, trade_date),
            (by_settlement_month, settlement),
        ):
            key = (when.year, when.month)
            buckets[key] = buckets.get(key, Decimal("0")) + earned_here
        gross += commission * billed
        net += (commission - rebate - fee) * billed
        gross_at_settlement += commission * billed_later
        notional_executed += quantity * execution_price * quoted
        notional_at_close += quantity * market_price * quoted
        # The mistake, not the metric: adding a JPY notional to a EUR one because
        # both columns are called `quantity * execution_price`.
        notional_unconverted += quantity * execution_price
        counted = by_account.setdefault(account_id, [Decimal("0"), Decimal("0")])
        counted[0] += quantity * execution_price * quoted
        counted[1] += 1
        by_client[client_id] = by_client.get(client_id, Decimal("0")) + (
            commission * billed
        )

    print()
    print("  Section C — every pair, both numbers")

    distinction(
        "Gross Revenue / Net Revenue — "
        "\"reporting gross as net overstates what the business keeps\"",
        "Gross Revenue", gross, "Net Revenue", net,
    )

    # Execution Price against Market Price is the one pair that separates a Trade
    # and not a book. Fills sit either side of the close — a Trade fills at
    # whatever the market gave it at that moment, which is above the close as often
    # as below — so summing 1,600 of them cancels most of the difference out. That
    # is a true property of the quantity rather than a thin simulation, so the pair
    # is checked where it actually bites: on the Trades themselves.
    distinction(
        "Execution Price / Market Price — "
        "\"Traded Notional at the close values trading that never happened\"",
        "Traded Notional at Execution Price", notional_executed,
        "at that date's Market Price", notional_at_close,
        minimum=Decimal("0"),
    )
    print(f"      per Trade: {fills_away_from_close} of {len(trades)} filled away "
          f"from the close, the largest by {largest_fill_gap:.2%}")
    print(f"      at book level the two nearly cancel — see DEBT-011")
    if fills_away_from_close < len(trades):
        problems.append(
            f"{len(trades) - fills_away_from_close} Trades filled at exactly that "
            f"date's Market Price, so Execution Price and Market Price are the "
            f"same number on them — Section C's row says a fill is the close "
            f"'except by coincidence', and this is not coincidence at that scale"
        )

    distinction(
        "Quotation Currency / Reporting Currency — "
        "\"skipping the conversion is an FX-sized error\"",
        f"converted to {REPORTING_CURRENCY}", notional_executed,
        "summed unconverted", notional_unconverted,
        unit="(mixed)",
    )

    # Trade Date against Settlement Date, which Section C says moves the number
    # *twice*. Both halves are measured, because they are wildly different sizes
    # and quoting only one would misrepresent the row:
    #
    #   the period half — a month's revenue filtered by one date or the other,
    #                     which moves whole Trades across the boundary
    #   the FX half     — the same Commission converted at each date's own rate,
    #                     which is what DEBT-004 is about
    print()
    widest_period = max(
        set(by_trade_month) | set(by_settlement_month),
        key=lambda month: gap(
            by_trade_month.get(month, Decimal("0")),
            by_settlement_month.get(month, Decimal("0")),
        ),
    )
    distinction(
        f"Trade Date / Settlement Date — \"shifts revenue across period "
        f"boundaries\", Gross Revenue in "
        f"{widest_period[0]}-{widest_period[1]:02d}",
        "filtered by Trade Date", by_trade_month.get(widest_period, Decimal("0")),
        "filtered by Settlement Date",
        by_settlement_month.get(widest_period, Decimal("0")),
    )
    fx_delta = gap(gross, gross_at_settlement)
    print(f"      the same row's FX half, over every Trade: {gross:,.2f} at each "
          f"Trade Date's rate against {gross_at_settlement:,.2f} at each "
          f"Settlement Date's, {fx_delta:.4%} apart")
    print(f"      DEBT-004: that FX half is measured against the 1% the Ledger "
          f"wants for a reliable evaluation signal — "
          f"{'clears' if fx_delta >= Decimal('0.01') else 'does not clear'} it")

    # Cash against Accounting, on one component — Commission — so the only thing
    # that differs between the two sides is *when* it was recognised. Comparing
    # whole tables would compare different things: cash holds settlements and
    # deposits, accounting holds Realised P&L, and neither has a counterpart.
    def monthly(sql: str) -> dict[tuple[int, int], Decimal]:
        buckets: dict[tuple[int, int], Decimal] = {}
        for movement_date, amount, rate in warehouse.query(
            sql, [REPORTING_CURRENCY]
        ):
            key = (movement_date.year, movement_date.month)
            buckets[key] = buckets.get(key, Decimal("0")) + abs(amount) * rate
        return buckets

    collected = monthly(
        "SELECT movement.movement_date, movement.amount, rate.fx_rate "
        "FROM fct_cash_movement AS movement "
        "JOIN fct_fx_rate AS rate "
        "  ON rate.rate_date = movement.movement_date "
        " AND rate.from_currency = movement.denomination_currency "
        " AND rate.to_currency = ? "
        "WHERE movement.movement_type = 'commission'"
    )
    earned = monthly(
        "SELECT movement.movement_date, movement.amount, rate.fx_rate "
        "FROM fct_accounting_movement AS movement "
        "JOIN fct_fx_rate AS rate "
        "  ON rate.rate_date = movement.movement_date "
        " AND rate.from_currency = movement.denomination_currency "
        " AND rate.to_currency = ? "
        "WHERE movement.movement_type = 'commission'"
    )
    months = sorted(set(collected) | set(earned))
    differing = [
        month
        for month in months
        if gap(earned.get(month, Decimal("0")), collected.get(month, Decimal("0")))
        >= MIN_DISTINCTION_GAP
    ]
    widest = max(
        months,
        key=lambda month: gap(
            earned.get(month, Decimal("0")), collected.get(month, Decimal("0"))
        ),
    )
    print()
    distinction(
        f"Cash Movement / Accounting Movement — \"earned on Trade Date and "
        f"collected on Settlement Date\", Commission in {widest[0]}-{widest[1]:02d}",
        "earned (Accounting)", earned.get(widest, Decimal("0")),
        "collected (Cash)", collected.get(widest, Decimal("0")),
    )
    print(f"      {len(differing)} of {len(months)} months differ by at least "
          f"{MIN_DISTINCTION_GAP:.1%}")
    if not differing:
        problems.append(
            "Commission earned and Commission collected agree in every month — "
            "no period boundary falls inside a settlement cycle, so the Cash "
            "against Accounting Movement pair is untestable on this data"
        )

    # The Snapshot side: Cash Balance against Account Value, and Realised against
    # Unrealised P&L, both as of the last Snapshot date.
    ((last_snapshot,),) = warehouse.query(
        "SELECT max(snapshot_date) FROM fct_position_snapshot"
    )
    # Summed in Python rather than by the engine, here and for the ledger below.
    # A DECIMAL(18, 6) amount times a DECIMAL(18, 8) rate needs 36 digits, and
    # DuckDB computes it in DECIMAL(18) and raises on overflow — a JPY balance is
    # large enough to hit it. Casting both sides wider would work and would put an
    # engine-specific width in a script outside veritas/warehouse/; Python's
    # Decimal has no width to overflow, and the rest of this file already does its
    # arithmetic there.
    cash_balance = sum(
        (
            balance * rate
            for balance, rate in warehouse.query(
                "SELECT balance.cash_balance, rate.fx_rate "
                "FROM fct_balance_snapshot AS balance "
                "JOIN fct_fx_rate AS rate "
                "  ON rate.rate_date = balance.snapshot_date "
                " AND rate.from_currency = balance.denomination_currency "
                " AND rate.to_currency = ? "
                "WHERE balance.snapshot_date = ?",
                [REPORTING_CURRENCY, last_snapshot],
            )
        ),
        Decimal("0"),
    )
    positions = warehouse.query(
        "SELECT position.account_id, position.instrument_id, position.quantity, "
        "       position.cost_basis, price.market_price, rate.fx_rate "
        "FROM fct_position_snapshot AS position "
        "JOIN dim_instrument AS instrument "
        "  ON instrument.instrument_id = position.instrument_id "
        "JOIN fct_instrument_price AS price "
        "  ON price.price_date = position.snapshot_date "
        " AND price.instrument_id = position.instrument_id "
        "JOIN fct_fx_rate AS rate "
        "  ON rate.rate_date = position.snapshot_date "
        " AND rate.from_currency = instrument.quotation_currency "
        " AND rate.to_currency = ? "
        "WHERE position.snapshot_date = ?",
        [REPORTING_CURRENCY, last_snapshot],
    )
    marked = sum(
        (quantity * market_price * rate for _, _, quantity, _, market_price, rate
         in positions),
        Decimal("0"),
    )
    unrealised = sum(
        ((quantity * market_price - cost_basis) * rate
         for _, _, quantity, cost_basis, market_price, rate in positions),
        Decimal("0"),
    )
    realised = sum(
        (
            amount * rate
            for amount, rate in warehouse.query(
                "SELECT movement.amount, rate.fx_rate "
                "FROM fct_accounting_movement AS movement "
                "JOIN fct_fx_rate AS rate "
                "  ON rate.rate_date = movement.movement_date "
                " AND rate.from_currency = movement.denomination_currency "
                " AND rate.to_currency = ? "
                "WHERE movement.movement_type = 'realised P&L'",
                [REPORTING_CURRENCY],
            )
        ),
        Decimal("0"),
    )

    print()
    print(f"    (as of the last Snapshot date, {last_snapshot})")
    distinction(
        "Cash Balance / Account Value — \"a Client with no cash and 2m of "
        "equities has a Cash Balance of zero\"",
        "Cash Balance", cash_balance,
        "Account Value (cash plus Positions marked)", cash_balance + marked,
    )
    distinction(
        "Realised P&L / Unrealised P&L — \"one is banked, one is a market "
        "opinion\"",
        "Realised P&L (banked, from the ledger)", realised,
        "Unrealised P&L (open Positions, marked)", unrealised,
    )

    # Cost Basis against Execution Price, on the same open Positions: what the
    # holding cost, against pricing it at the last thing that happened to it.
    #
    # Read as rows and folded in Python rather than asked for as one aggregate,
    # because "the last fill" is ambiguous in SQL and not in the domain: two Trades
    # can share a Trade Date, and a `max(trade_date)` subquery returns both, leaving
    # which one survives to whichever row the engine happened to emit last. Ordering
    # by `trade_date` and then `trade_id` breaks that tie the way fct_trade already
    # numbers them, and the last write into the dictionary wins.
    last_fills: dict[tuple[int, int], Decimal] = {}
    for account_id, instrument_id, execution_price in warehouse.query(
        "SELECT account_id, instrument_id, execution_price FROM fct_trade "
        "ORDER BY trade_date, trade_id"
    ):
        last_fills[(account_id, instrument_id)] = execution_price

    # Both sides are summed over the **same** Positions — the ones a Trade actually
    # touched — so the only thing that differs between them is which cost measure
    # was used, which is what the pair is about.
    #
    # A Position with no Trade behind it has no last Execution Price at all: it
    # arrived by transfer, and nothing ever filled. There is no stand-in for one.
    # Substituting the Cost Basis, as an earlier version of this check did, is wrong
    # twice over — a Cost Basis is a total where an Execution Price is a per-unit
    # price, so multiplying it by the quantity again is out by a factor of the
    # holding; and it puts the left side's own number into the right side, which
    # compares a figure with itself on exactly the Positions where the pair is
    # hardest to separate. Excluding them and saying how many is the honest version.
    touched = [row for row in positions if (row[0], row[1]) in last_fills]
    unrealised_touched = sum(
        ((quantity * market_price - cost_basis) * rate
         for _, _, quantity, cost_basis, market_price, rate in touched),
        Decimal("0"),
    )
    at_last_fill = sum(
        (
            quantity * (market_price - last_fills[(account_id, instrument_id)]) * rate
            for account_id, instrument_id, quantity, _, market_price, rate in touched
        ),
        Decimal("0"),
    )
    distinction(
        "Cost Basis / Execution Price — \"an Execution Price is what one Trade "
        "filled at; a Cost Basis is what the whole holding cost\"",
        "Unrealised P&L against stored Cost Basis", unrealised_touched,
        "against the last Execution Price", at_last_fill,
    )
    print(f"      over the {len(touched)} of {len(positions)} Positions on this "
          f"date that a Trade touched — the rest arrived by transfer and have no "
          f"last fill")

    # Traded Notional against Trade Count, and Client against Account. Both are
    # about a ranking rather than a total: "one large trade and a thousand small
    # ones are opposite answers to 'was this a busy month'", and counting Accounts
    # and calling them Clients "inflates every per-client figure".
    print()
    # Both rankings break their ties on `account_id`, and the query above is
    # ordered, so the figure below is decided by the data rather than by the order
    # the engine returned rows in. This matters here and not in the sums beside it:
    # a sum does not care what order it is taken in, and Traded Notional is a
    # Decimal total that never ties — but Trade Count is a small integer and
    # Accounts routinely share one, so without a stated tie-break the count ranking,
    # and the number of Accounts said to disagree with it, is whatever the scan
    # happened to emit first.
    by_notional = [
        account for account, _ in sorted(
            by_account.items(), key=lambda item: (-item[1][0], item[0])
        )
    ]
    by_count = [
        account for account, _ in sorted(
            by_account.items(), key=lambda item: (-item[1][1], item[0])
        )
    ]
    disagreements = sum(
        1 for left, right in zip(by_notional, by_count) if left != right
    )
    print("    Traded Notional / Trade Count — \"one large trade and a thousand "
          "small ones are opposite answers\"")
    print(f"      busiest Account by Traded Notional: {by_notional[0]} "
          f"({by_account[by_notional[0]][0]:,.0f} {REPORTING_CURRENCY})")
    print(f"      busiest Account by Trade Count: {by_count[0]} "
          f"({by_account[by_count[0]][1]:,.0f} Trades)")
    print(f"      {disagreements} of {len(by_account)} Accounts rank differently "
          f"under the two")
    if not disagreements:
        problems.append(
            "ranking Accounts by Traded Notional and by Trade Count gives the "
            "same order, so 'volume' has one answer on this data and the "
            "Ambiguous Term cannot be exercised"
        )

    accounts = len(by_account)
    clients = len(by_client)
    print("    Client / Account — \"counting Accounts and calling them clients "
          "inflates every per-client figure\"")
    print(f"      Clients with activity: {clients} · "
          f"Accounts with activity: {accounts}")
    print(f"      Gross Revenue per Client: {share(gross, Decimal(clients)):,.2f} "
          f"· per Account: {share(gross, Decimal(accounts)):,.2f} "
          f"{REPORTING_CURRENCY}")
    if clients >= accounts:
        problems.append(
            f"{clients} Clients hold {accounts} Accounts — with no Client holding "
            f"more than one, per-client and per-account figures are the same "
            f"number and the pair cannot be blurred"
        )


def check_snapshots(warehouse: WarehouseAdapter) -> None:
    """The two rules R12 and R13 fixed for Snapshots, checked on the loaded rows.

    Both are about a Snapshot being *markable*. A Position the Warehouse holds and
    cannot price is an Account Value that is silently short by a holding, and it
    looks exactly like an Account that does not hold it.
    """
    for table_name, sql in (
        (
            "fct_position_snapshot",
            "SELECT count(DISTINCT snapshot_date) FROM fct_position_snapshot "
            "WHERE snapshot_date NOT IN (SELECT price_date FROM fct_instrument_price)",
        ),
        (
            "fct_balance_snapshot",
            "SELECT count(DISTINCT snapshot_date) FROM fct_balance_snapshot "
            "WHERE snapshot_date NOT IN (SELECT price_date FROM fct_instrument_price)",
        ),
    ):
        ((orphan_dates,),) = warehouse.query(sql)
        if orphan_dates:
            problems.append(
                f"{table_name} holds {orphan_dates} Snapshot dates the Warehouse "
                f"has no Market Price for at all — R13 fixes that a Snapshot is "
                f"written on the dates prices exist for, so these cannot be marked"
            )

    # The stronger reading, and the one Sub-step 2.5 chose: not just that the date
    # has *some* price, but that this Instrument has one on it.
    ((unmarkable,),) = warehouse.query(
        "SELECT count(*) "
        "FROM fct_position_snapshot AS position "
        "LEFT JOIN fct_instrument_price AS price "
        "  ON price.price_date = position.snapshot_date "
        " AND price.instrument_id = position.instrument_id "
        "WHERE price.market_price IS NULL"
    )
    ((dates,),) = warehouse.query(
        "SELECT count(DISTINCT snapshot_date) FROM fct_position_snapshot"
    )
    print(f"  Snapshots: {dates} dates · every Position has a Market Price on its "
          f"own date ({unmarkable} without)")
    if unmarkable:
        problems.append(
            f"{unmarkable} Positions have no Market Price on their own Snapshot "
            f"date, so they cannot be marked. The Snapshot calendar was chosen as "
            f"the dates *every* Instrument has a price precisely so this is zero"
        )

    # Position Change against Trade. Every Position starts at zero, so the holding
    # on the last Snapshot date is the sum of everything that ever moved it — and
    # the sum of its Trades is only part of that. The gap is the transfers, which
    # is the whole content of the Section C row: "deriving position change from
    # trades alone silently loses those".
    unexplained = warehouse.query(
        "SELECT position.account_id, position.instrument_id, position.quantity, "
        "       coalesce(traded.net_quantity, 0) AS net_quantity "
        "FROM fct_position_snapshot AS position "
        "LEFT JOIN ( "
        "    SELECT account_id, instrument_id, "
        "           sum(CASE WHEN trade_side = 'buy' THEN quantity "
        "                    ELSE -quantity END) AS net_quantity "
        "    FROM fct_trade GROUP BY account_id, instrument_id "
        ") AS traded "
        "  ON traded.account_id = position.account_id "
        " AND traded.instrument_id = position.instrument_id "
        "WHERE position.snapshot_date = "
        "      (SELECT max(snapshot_date) FROM fct_position_snapshot) "
        "  AND position.quantity <> coalesce(traded.net_quantity, 0)"
    )
    print(f"    Position Change / Trade: {len(unexplained)} holdings differ from "
          f"the sum of their own Trades")
    for account_id, instrument_id, quantity, net_quantity in unexplained:
        print(f"      account {account_id} · instrument {instrument_id}: "
              f"holds {quantity:,.0f}, Trades explain {net_quantity:,.0f}")
    if not unexplained:
        problems.append(
            "every holding equals the sum of its own Trades, so Position Change "
            "and Trade are the same number on this data — R14 requires the "
            "simulator to emit transfers, and none reached the Warehouse"
        )


def check_lots(warehouse: WarehouseAdapter) -> None:
    """Every quantity the Warehouse holds is a whole lot of its own Instrument.

    `LOT_SIZE` in the simulator is the statement of what one unit of each
    instrument type is: nobody trades 86,431.5 units of a currency pair, a future
    is a whole number of contracts, and no custodian delivers half a share. The
    schema cannot express that rule — `quantity` is a `DECIMAL(18, 6)`, because a
    column type is about scale and not about lots — so it is checked here or
    nowhere.

    **Added by Sub-step 2.5's review, after nowhere turned out to be the answer.**
    `build_transfers` quantised to six decimal places instead of rounding to the
    lot, so the one path that moves a Position *without* a Trade was also the one
    path that disagreed with every Trade about what a whole unit is. Nothing
    reported it: every row satisfied the schema, every Snapshot was markable, and
    the fractional holding sat inside an Account Value that looked entirely
    ordinary. That is the shape of failure this project is about, arriving in our
    own generator.

    Both tables are checked, not just the one that broke. A Trade and a Position
    are two records of the same stock, and a rule enforced on one of them is a rule
    that holds until the other one moves.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from veritas.ingestion.simulator import LOT_SIZE

    for table_name, sql in (
        (
            "fct_trade",
            "SELECT instrument.instrument_type, trade.quantity "
            "FROM fct_trade AS trade "
            "JOIN dim_instrument AS instrument "
            "  ON instrument.instrument_id = trade.instrument_id",
        ),
        (
            "fct_position_snapshot",
            "SELECT instrument.instrument_type, position.quantity "
            "FROM fct_position_snapshot AS position "
            "JOIN dim_instrument AS instrument "
            "  ON instrument.instrument_id = position.instrument_id",
        ),
    ):
        rows = warehouse.query(sql)
        broken = [
            (instrument_type, quantity)
            for instrument_type, quantity in rows
            if quantity % LOT_SIZE[instrument_type]
        ]
        print(f"    {table_name:24} {len(rows):>6} quantities · "
              f"{len(broken)} not a whole lot")
        if broken:
            instrument_type, quantity = broken[0]
            problems.append(
                f"{table_name} holds {len(broken)} quantities that are not a whole "
                f"lot of their own Instrument — the first is {quantity} of an "
                f"Instrument of type {instrument_type!r}, whose lot is "
                f"{LOT_SIZE[instrument_type]}. "
                f"Every path that moves stock must agree about what one unit is, "
                f"and a Trade and a transfer are two such paths"
            )


def duckdb_importers() -> list[Path]:
    """Every Python file that imports `duckdb`, adapter or not.

    Parsed rather than grepped, for the same reason check_language.py parses: the
    rule is about imports, and the word `duckdb` in a comment or a docstring is
    prose. Grepping conflates the two and fires on every explanation of the rule,
    including this one.
    """
    found: list[Path] = []
    for root in CODE_ROOTS:
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                match node:
                    case ast.Import(names=names):
                        modules = [alias.name for alias in names]
                    case ast.ImportFrom(module=module):
                        modules = [module or ""]
                    case _:
                        continue
                if any(m.split(".")[0] == "duckdb" for m in modules):
                    found.append(path)
                    break
    return found


def duckdb_function_names() -> set[str]:
    """Function names sqlglot files under DuckDB and not under standard SQL.

    Derived, not typed. sqlglot builds every dialect's function table on top of
    one dialect-neutral table, so what DuckDB adds to that table *is* the list of
    names this project may not use outside the adapter — and it comes from the
    library that would have to transpile them, which is the only opinion that
    matters. A list typed into this file would be one person's memory of DuckDB's
    manual, and it would go stale silently: nothing would fail when DuckDB grew a
    function, because nothing reads a comment.

    What this cannot see is a name sqlglot considers dialect-neutral when it is
    not — `generate_series` is in the neutral table and is not in the SQL standard.
    The scan is exactly as good as sqlglot's own dialect knowledge, which is the
    trade [ADR-0002](../docs/adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)
    already made when it put sqlglot in charge of retargeting.
    """
    return {name for name in DuckDB.Parser.FUNCTIONS if name not in Parser.FUNCTIONS}


DUCKDB_FUNCTIONS = duckdb_function_names()


def sql_statements(path: Path) -> list[tuple[int, str]]:
    """Every string literal in `path` that sqlglot reads as a SQL statement.

    Parsed rather than matched, for the reason `duckdb_importers` parses: this
    repository writes about SQL constantly, and the word FROM appears in more
    English sentences here than in queries.

    Two kinds of string are skipped, and each is scoped to exactly what it
    excuses rather than to what a string looks like.

      * **Docstrings**, which are prose by construction. What is excused here is a
        *position* in the syntax tree — one the language defines, not a name any
        file can choose — so the exemption cannot widen. The docstrings in this
        file quote the very function names the scan looks for, including two lines
        above this one.
      * **A fixture listed in `FIXTURE_EXEMPTIONS`**, which is one entry:
        `DIALECT_PROBES` **in this file**. That tuple is the SQL this file writes
        in order to test the scan. It is deliberately DuckDB-specific and is never
        sent anywhere, so it is a fixture in the sense the fourteen invalid rows of
        `check_constraints` are — and this scan reads the SQL a module *emits*.
        Without the exemption the check fails on its own test data, which is the
        one finding that means nothing. Naming the file removes the loophole and
        not the cost, and the cost is stated rather than hidden: SQL put in a tuple
        by that name **inside this file** is still invisible here.

    What this reads is SQL a module has **written down**. SQL assembled at run
    time — an f-string, a join, anything a generator returns — is not a literal
    and is not seen. That is a boundary rather than an oversight: the SQL an
    Orchestrator generates is the Validation Gate's subject
    ([ADR-0003](../docs/adr/0003-validation-gate-is-deterministic-code.md)), which
    inspects a parse tree at run time precisely because no static scan can.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    documentation = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        )
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    here = path.relative_to(REPO_ROOT).as_posix()
    exempt = {symbol for file, symbol in FIXTURE_EXEMPTIONS if file == here}
    fixtures = {
        id(constant)
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id in exempt
            for target in node.targets
        )
        for constant in ast.walk(node.value)
        if isinstance(constant, ast.Constant)
    }

    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in documentation or id(node) in fixtures:
            continue
        try:
            parsed = sqlglot.parse_one(node.value, dialect="duckdb")
        except sqlglot.errors.SqlglotError:
            continue
        if isinstance(parsed, SQL_STATEMENTS):
            found.append((node.lineno, node.value))
    return found


def unportable_functions(sql: str) -> list[tuple[str, bool]]:
    """The function names in `sql` that standard SQL does not have.

    Read off the *dialect-neutral* parse, where a function sqlglot's neutral table
    does not know is left as an anonymous call carrying the name as written. That
    is what makes this precise where matching text is not: `count(` and `max(` are
    known functions and never appear, and `CREATE TABLE dim_account (` is a table
    rather than a call to something named `dim_account`.

    Each name comes back with whether sqlglot knows it as DuckDB's. Both answers
    are findings and neither is worse: a name DuckDB owns is a dialect assumption
    that has escaped the adapter, and a name sqlglot knows in no dialect at all is
    one it cannot transpile either — the risk ADR-0002 calls transpilation being
    "good but not total".
    """
    tree = sqlglot.parse_one(sql, error_level=sqlglot.ErrorLevel.RAISE)
    names = sorted({call.name.upper() for call in tree.find_all(exp.Anonymous)})
    return [(name, name in DUCKDB_FUNCTIONS) for name in names]


def check_seam() -> None:
    """No module outside veritas/warehouse/ reaches for the engine.

    Two halves, because ADR-0002 names two signals and Sub-step 2.1 shipped one of
    them ([DEBT-009](../docs/debt-ledger.md)): a `duckdb` import, and a
    DuckDB-specific function name in the SQL a module emits.
    """
    importers = duckdb_importers()
    scanned = sum(len(list(root.rglob("*.py"))) for root in CODE_ROOTS if root.exists())
    print(f"  seam scan: {scanned} Python files · "
          f"{len(importers)} import duckdb")

    for path in importers:
        inside = ADAPTER_DIR in path.parents
        print(f"    {'ADAPTER ' if inside else 'OUTSIDE '} {path.relative_to(REPO_ROOT)}")
        if not inside:
            problems.append(
                f"{path.relative_to(REPO_ROOT)} imports duckdb, but only "
                f"veritas/warehouse/ may — this is the exact signal ADR-0002 named "
                f"for the adapter seam having stopped holding"
            )
    if not importers:
        problems.append(
            "no module imports duckdb at all — the adapter cannot be reaching the "
            "engine, so this check is passing vacuously"
        )

    print(f"  dialect scan: sqlglot files {len(DUCKDB_FUNCTIONS)} function names "
          f"under DuckDB that standard SQL does not have")

    for probe, expected in DIALECT_PROBES:
        found = tuple(name for name, _ in unportable_functions(probe))
        verdict = ", ".join(found) if found else "clean"
        print(f"    probe: {verdict}")
        if found != expected:
            problems.append(
                f"the dialect scan reads {probe!r} as {found or 'clean'} and it has "
                f"to read it as {expected or 'clean'} — the scan cannot be trusted "
                f"about the repository when it is wrong about SQL written to test it"
            )

    # Python modules only. A `.sql` file is read nowhere: inside the adapter it is
    # licensed to be DuckDB-specific, and outside it none exists — one appearing
    # there later needs a second glob rather than turning up on its own.
    statements = 0
    for root in CODE_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if path == ADAPTER_DIR or ADAPTER_DIR in path.parents:
                continue
            emitted = sql_statements(path)
            if not emitted:
                continue
            statements += len(emitted)
            print(f"    {len(emitted):3} SQL statements in {path.relative_to(REPO_ROOT)}")
            for line, sql in emitted:
                for name, duckdb_owns_it in unportable_functions(sql):
                    whose = (
                        "sqlglot knows as DuckDB's and not as standard SQL's"
                        if duckdb_owns_it
                        else "sqlglot knows in no dialect, so it cannot transpile it"
                    )
                    problems.append(
                        f"{path.relative_to(REPO_ROOT)}:{line} emits SQL calling "
                        f"{name}(), which {whose} — ADR-0002 names a DuckDB-specific "
                        f"function name outside the adapter as the signal that the "
                        f"seam has stopped holding"
                    )

    if not statements:
        problems.append(
            "no module outside veritas/warehouse/ emits SQL at all — there is "
            "nothing for the dialect scan to read, so it is passing vacuously"
        )


def main() -> int:
    # RawDescriptionHelpFormatter, because the default one collapses all
    # whitespace and re-wraps: it turns the numbered list above into a single
    # unbroken paragraph, which is worse than no help text.
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="delete the Warehouse and recreate it from schema.sql "
             "(the file is gitignored; the snapshots are what make it reproducible)",
    )
    parser.add_argument(
        "--sources",
        action="store_true",
        help="also check what ingestion loaded against what the sources said — "
             "run `uv run python -m veritas.ingestion` first",
    )
    parser.add_argument(
        "--distinctions",
        action="store_true",
        help="also check the client side: that the simulator reproduces it "
             "exactly, that every Snapshot is markable, and that every Glossary "
             "Section C pair is two different numbers",
    )
    arguments = parser.parse_args()

    if arguments.rebuild and (arguments.sources or arguments.distinctions):
        parser.error(
            "--rebuild empties the Warehouse and --sources and --distinctions "
            "check what is in it, so together they only ever prove that an empty "
            "table is empty"
        )

    if arguments.rebuild and DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print(f"  removed {DATABASE_PATH.relative_to(REPO_ROOT)}")

    fresh = not DATABASE_PATH.exists()
    with WarehouseAdapter() as warehouse:
        if fresh:
            warehouse.create_schema()
        print(f"  Warehouse: {DATABASE_PATH.relative_to(REPO_ROOT)} "
              f"({'created from schema.sql' if fresh else 'already existed'})")
        check_schema(warehouse)

        if arguments.sources:
            print()
            check_sources(warehouse)
            print()
            check_prices(warehouse)
            print()
            check_fx_rates(warehouse)

        if arguments.distinctions:
            print()
            check_client_activity(warehouse)
            print()
            check_lots(warehouse)
            print()
            check_snapshots(warehouse)
            print()
            check_distinctions(warehouse)

    check_constraints()
    print()
    check_seam()

    print()
    if problems:
        print(f"FAIL — {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("PASS — the star schema matches Glossary Section B and the adapter seam holds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
