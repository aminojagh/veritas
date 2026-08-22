"""The Semantic Layer — the certified registry of Metric Definitions, Dimension
Definitions, Join Paths and Ambiguous Terms.

Veritas's knowledge base, and the thing Retrieval searches. The entries themselves
are YAML under `semantic/`; this package reads them.
"""

from veritas.semantic.loader import (
    SEMANTIC_DIR,
    JoinPath,
    MetricDefinition,
    SemanticEntry,
    SemanticEntryError,
    SemanticLayer,
    entry_files,
    load_semantic_layer,
    read_entry,
)

__all__ = [
    "SEMANTIC_DIR",
    "JoinPath",
    "MetricDefinition",
    "SemanticEntry",
    "SemanticEntryError",
    "SemanticLayer",
    "entry_files",
    "load_semantic_layer",
    "read_entry",
]
