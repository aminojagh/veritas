"""Retrieval — the step that turns a question into the Semantic Entries needed to
answer it.

Searches the Semantic Layer and nothing else: never Warehouse schema, never free
text. This package holds the search; the entries themselves are read by
`veritas.semantic`.

`searchable.py` decides what a search may match on; `search.py` is the search
itself, and `retrieve` is the seam the Orchestrator calls.
"""

from veritas.retrieval.search import (
    CANDIDATES,
    EMBEDDING_MODEL,
    REFERENCE_FIELDS,
    RERANKER_MODEL,
    RRF_K,
    TOP_K,
    VECTORIZER_PARAMS,
    RetrievalStrategy,
    Retriever,
    default_retriever,
    embedding_model,
    fuse,
    rank,
    references,
    reranker,
    retrieve,
)
from veritas.retrieval.searchable import (
    SEARCHABLE_FIELDS,
    searchable_entries,
    searchable_text,
)

__all__ = [
    "CANDIDATES",
    "EMBEDDING_MODEL",
    "REFERENCE_FIELDS",
    "RERANKER_MODEL",
    "RRF_K",
    "SEARCHABLE_FIELDS",
    "TOP_K",
    "VECTORIZER_PARAMS",
    "RetrievalStrategy",
    "Retriever",
    "default_retriever",
    "embedding_model",
    "fuse",
    "rank",
    "references",
    "reranker",
    "retrieve",
    "searchable_entries",
    "searchable_text",
]
