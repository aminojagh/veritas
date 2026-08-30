"""Retrieval — the step that turns a question into the Semantic Entries needed to
answer it.

Searches the Semantic Layer and nothing else: never Warehouse schema, never free
text. This package holds the search; the entries themselves are read by
`veritas.semantic`.
"""

from veritas.retrieval.searchable import (
    SEARCHABLE_FIELDS,
    searchable_entries,
    searchable_text,
)

__all__ = [
    "SEARCHABLE_FIELDS",
    "searchable_entries",
    "searchable_text",
]
