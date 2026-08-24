"""The Semantic Layer — the certified registry of Metric Definitions, Dimension
Definitions, Join Paths and Ambiguous Terms.

Veritas's knowledge base, and the thing Retrieval searches. The entries themselves
are YAML under `semantic/`; this package reads them.
"""

from veritas.semantic.loader import (
    ENTRY_KINDS,
    SEMANTIC_DIR,
    SQL_FIELDS,
    AmbiguousTerm,
    JoinPath,
    MetricDefinition,
    SemanticEntry,
    SemanticEntryError,
    SemanticLayer,
    entry_files,
    load_semantic_layer,
    read_entry,
    sql_fields,
)

__all__ = [
    "ENTRY_KINDS",
    "SEMANTIC_DIR",
    "SQL_FIELDS",
    "AmbiguousTerm",
    "JoinPath",
    "MetricDefinition",
    "SemanticEntry",
    "SemanticEntryError",
    "SemanticLayer",
    "entry_files",
    "load_semantic_layer",
    "read_entry",
    "sql_fields",
]
