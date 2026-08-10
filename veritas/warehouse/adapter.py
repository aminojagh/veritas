"""The Warehouse Adapter — the single boundary through which all Warehouse access passes.

**This is the only module in the repository permitted to import `duckdb`.**
`.claude/scripts/check_warehouse.py` fails the run if any other module does, which
is the mechanical signal ADR-0002 named and nothing ran until Step 002.

ADR-0002 sets both the shape and the licence for how crude the inside may be:

    a seam is an interface plus one trivial implementation ... Behind the seam,
    everything is fair game: the adapter's first implementation can hardcode a
    path, ignore connection pooling, and handle no errors at all — each of those
    is fixed in one place, later, for the same price as today.

So the hardcoded database path, the absent pooling and the absent error handling
below are not undeclared shortcuts; they are the costs that ADR already accepted
in writing. What may not be deferred is the boundary itself.

One rule the ADR added on 2026-08-05 does bind the code here: *prefer the
construct that assembles no text*, inside the adapter as well as outside it. Every
method below obeys it. Table and column listings go through `information_schema`
with a bound parameter, and row counts go through DuckDB's relational API, so no
method in this file builds a SQL string out of a value it was handed.
"""

from pathlib import Path
from types import TracebackType

import duckdb

WAREHOUSE_DIR = Path(__file__).resolve().parent
REPO_ROOT = WAREHOUSE_DIR.parent.parent

SCHEMA_PATH = WAREHOUSE_DIR / "schema.sql"

# Hand-authored raw-to-star build scripts, one per table, added from Sub-step 2.2.
# They live here rather than in veritas/ingestion/ because R4 puts them on this
# side of the seam: "dlt lands raw source data in a `raw` schema; the adapter
# executes the SQL that builds the star schema from it." Keeping them here is also
# what stops DEBT-009's trigger — "the first component outside the adapter emits
# SQL" — from firing on the ingestion pipeline.
BUILDS_DIR = WAREHOUSE_DIR / "builds"

# Hardcoded, and licensed as such by ADR-0002. `*.duckdb` is gitignored, so the
# built Warehouse is never committed — the snapshots in data/snapshots/ are what
# make it reproducible, not the database file.
DATABASE_PATH = REPO_ROOT / "data" / "veritas.duckdb"

# DuckDB's magic filename for a database held in memory, never written to disk,
# discarded when the connection closes. It is **not** a path, and this constant
# exists so that fact is greppable: `Path(":memory:")` round-trips back to the
# same string by coincidence rather than by design, so code that treats it as a
# path works today and would break the moment anything resolved or joined it.
IN_MEMORY = ":memory:"


class WarehouseAdapter:
    """Holds the connection and the engine's dialect. Nothing DuckDB-specific
    exists outside this class.

    Usable as a context manager:

        with WarehouseAdapter() as warehouse:
            warehouse.create_schema()
    """

    def __init__(self, database_path: Path | str = DATABASE_PATH) -> None:
        self.is_in_memory = str(database_path) == IN_MEMORY
        if self.is_in_memory:
            # Deliberately never passed through Path(). See IN_MEMORY above.
            self.database_path: Path | None = None
            self._connection = duckdb.connect(IN_MEMORY)
        else:
            self.database_path = Path(database_path)
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = duckdb.connect(str(self.database_path))

    @classmethod
    def in_memory(cls) -> "WarehouseAdapter":
        """A throwaway Warehouse held in memory, discarded when it is closed.

        The readable way to ask for one, so a call site says what it wants rather
        than passing a magic string that looks like a filename. Used by
        `check_warehouse.py` to fire deliberately invalid rows at a real copy of
        the star schema without going near the built Warehouse.
        """
        return cls(IN_MEMORY)

    def __enter__(self) -> "WarehouseAdapter":
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    # -- schema ------------------------------------------------------------

    def create_schema(self) -> None:
        """Execute the hand-authored star schema Data Definition Language (DDL).

        The whole file goes to the engine in one call. It is deliberately *not*
        split into statements here: splitting would mean this module parsing SQL,
        which is the one thing ADR-0002 reserves for sqlglot.
        """
        self._connection.execute(SCHEMA_PATH.read_text())

    def builds(self) -> list[str]:
        """The raw-to-star build scripts available, by name, alphabetically."""
        return sorted(path.stem for path in BUILDS_DIR.glob("*.sql"))

    def run_build(self, build_name: str) -> None:
        """Execute one hand-authored raw-to-star build script by name.

        The name is resolved against the scripts actually present rather than
        pasted into a path, so a caller cannot reach a file outside `builds/`, and
        an unknown name fails here with the list of real ones instead of surfacing
        as a confusing engine error. The SQL itself is human-authored text under
        the same ADR-0002 licence as `create_schema`: nothing is assembled.
        """
        available = self.builds()
        if build_name not in available:
            raise FileNotFoundError(
                f"no build script named {build_name!r} in "
                f"{BUILDS_DIR.name}/ — have {available}"
            )
        self._connection.execute((BUILDS_DIR / f"{build_name}.sql").read_text())

    # -- introspection -----------------------------------------------------

    def tables(self) -> list[str]:
        """Every table in the star schema, alphabetically.

        `information_schema` rather than DuckDB's own `duckdb_tables()`: it is the
        SQL-standard view, so this query survives the engine swap the adapter
        exists to make possible.
        """
        rows = self._connection.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' ORDER BY table_name"
        ).fetchall()
        return [name for (name,) in rows]

    def columns(self, table_name: str) -> list[tuple[str, str]]:
        """(column name, declared type) for one table, in declaration order."""
        return self._connection.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'main' AND table_name = ? "
            "ORDER BY ordinal_position",
            [table_name],
        ).fetchall()

    def row_count(self, table_name: str) -> int:
        """Exact row count for one table, star-schema or `raw.`-qualified.

        Goes through the relational API rather than `SELECT count(*) FROM <name>`
        precisely so that no SQL text is assembled from the argument — ADR-0002's
        case C, which is permitted inside the seam and still worth refusing. The
        alternative, `duckdb_tables().estimated_size`, is an estimate, and Sub-steps
        2.2 onward assert against these numbers.

        A schema-qualified name works and is how `check_warehouse.py --sources`
        counts what dlt landed in `raw`. Giving callers this rather than letting
        them build one `count(*)` string is the whole point: the alternative put
        an interpolated table name in a script outside the adapter, which is both
        the construct ADR-0002 rejects and the event DEBT-009's trigger names.
        """
        (count,) = self._connection.table(table_name).aggregate(
            "count(*) AS row_count"
        ).fetchone()
        return count

    # -- reading and writing -----------------------------------------------

    def execute(self, sql: str, parameters: list[object] | None = None) -> None:
        """Run a statement that returns no rows.

        Separate from `query` so that reads and writes are distinguishable at the
        call site — the Validation Gate's read-only rule is a claim about which of
        these two a generated statement is allowed to reach.
        """
        self._connection.execute(sql, parameters or [])

    def query(
        self, sql: str, parameters: list[object] | None = None
    ) -> list[tuple[object, ...]]:
        """Run a read query and return its rows.

        The escape hatch, and the method that will eventually receive SQL rendered
        by sqlglot rather than written by hand. It is deliberately parameterised:
        a caller with a value to interpolate has a bound parameter available, so
        there is never a reason to build the string.
        """
        return self._connection.execute(sql, parameters or []).fetchall()
