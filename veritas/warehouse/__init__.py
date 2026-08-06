"""The Warehouse — the analytical store holding the brokerage star schema.

Reached only through the Warehouse Adapter; no component queries it directly.
"""

from veritas.warehouse.adapter import (
    DATABASE_PATH,
    IN_MEMORY,
    SCHEMA_PATH,
    WarehouseAdapter,
)

__all__ = ["DATABASE_PATH", "IN_MEMORY", "SCHEMA_PATH", "WarehouseAdapter"]
