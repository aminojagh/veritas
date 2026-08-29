"""Shared fixtures: repository paths, the built Warehouse, the Semantic Layer."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def root() -> Path:
    """The repository root."""
    return ROOT


@pytest.fixture(scope="session")
def warehouse():
    """The built Warehouse, opened once for the whole session."""
    from veritas.warehouse import WarehouseAdapter

    database = ROOT / "data" / "veritas.duckdb"
    if not database.exists():
        pytest.skip(f"no Warehouse at {database}")
    with WarehouseAdapter(database) as adapter:
        yield adapter


@pytest.fixture(scope="session")
def semantic():
    """The Semantic Layer, loaded once."""
    from veritas.semantic import load_semantic_layer

    return load_semantic_layer(ROOT / "semantic")
