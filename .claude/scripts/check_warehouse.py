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

  4. The seam holds. ADR-0002 commits that all warehouse access goes through the
     adapter and names the signal that it has stopped: "a `duckdb` import ...
     anywhere outside the adapter module". This scans for exactly that, by
     parsing the import statements rather than grepping the text — a `duckdb`
     mentioned in a docstring is prose, and this file is full of it.

  5. `--sources` only — what ingestion loaded is what the sources said. Added by
     Sub-step 2.2, and it grows with every source: no minor unit survives into
     `dim_instrument`, and the loaded Instrument Symbols are exactly the universe
     declared in `veritas/ingestion/universe.py`. Needs a filled Warehouse, so
     run `uv run python -m veritas.ingestion` first.

Exits non-zero if any check fails. This script grows across Step 002: Sub-steps
2.3 and 2.4 add assertions to `--sources`, and Sub-step 2.5 adds `--distinctions`.
"""

import argparse
import ast
import re
import sys
from pathlib import Path

CLAUDE_DIR = Path(__file__).resolve().parent.parent  # <repo>/.claude
REPO_ROOT = CLAUDE_DIR.parent                        # <repo>
GLOSSARY = CLAUDE_DIR / "docs" / "glossary.md"

sys.path.insert(0, str(REPO_ROOT))

from veritas.warehouse import DATABASE_PATH, WarehouseAdapter  # noqa: E402

# The one directory licensed to know the engine. ADR-0002: the Warehouse Adapter
# "holds the connection and the engine's dialect; nothing DuckDB-specific exists
# outside it".
ADAPTER_DIR = REPO_ROOT / "veritas" / "warehouse"

# Everywhere the import scan looks. Both roots hold code that could reach for the
# engine directly, and .claude/scripts/ is the likelier of the two to be tempted.
CODE_ROOTS = [REPO_ROOT / "veritas", CLAUDE_DIR / "scripts"]

# Types that silently lose money. DECIMAL is the only numeric type this schema
# uses for a quantity anyone will ever sum.
FLOATING_POINT = ("DOUBLE", "FLOAT", "REAL")

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
    """What Sub-step 2.2 loaded is what the sources actually said.

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
                      "minor_unit_currency", "yahoo_instrument_type"):
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


def check_seam() -> None:
    """No module outside veritas/warehouse/ imports duckdb."""
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
    arguments = parser.parse_args()

    if arguments.rebuild and arguments.sources:
        parser.error(
            "--rebuild empties the Warehouse and --sources checks what is in it, "
            "so together they only ever prove that an empty table is empty"
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
