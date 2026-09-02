"""Searches the Semantic Layer and returns the Semantic Entries a question needs.

`retrieve(question)` is the seam. Behind it are four searches over one corpus —
text, vector, their fusion, and the fusion re-ranked — named by
`RetrievalStrategy` and chosen per call.

**Two entry points, and the difference between them is reference closure.**
`rank` returns only what a search scored, which is what hit rate and Mean
Reciprocal Rank (MRR) are computed over. `retrieve` returns that ranking plus
every entry those hits name, transitively: the Join Paths a Metric Definition is
computed across, the Certified Metrics it derives from, the ones an Ambiguous
Term stands between, and the routes a Dimension Definition is reached by. Closure
is how a Join Path reaches an answer at all — `searchable.py` gives it no
searchable text, so no search can score one.

**The corpus is the searchable records of `searchable_entries`.** An entry whose
searchable text is empty is left out of both indexes rather than sitting in them
at score zero.

The two models are loaded on first use and cached for the life of the process.
Both are ONNX models fetched from the Hugging Face hub on first run and cached on
disk, and neither takes a credential — but neither is snapshotted into the
repository the way the data sources are, which is
[DEBT-026](../../.claude/docs/debt-ledger.md#debt-026--the-retrieval-models-are-downloaded-rather-than-snapshotted).
"""

from collections import defaultdict
from collections.abc import Mapping
from enum import StrEnum
from functools import cache, cached_property
from typing import TYPE_CHECKING

import numpy as np
from minsearch import Index, VectorSearch

from veritas.retrieval.searchable import TEXT_FIELDS, searchable_entries
from veritas.semantic import (
    AmbiguousTerm,
    DimensionDefinition,
    JoinPath,
    MetricDefinition,
    SemanticEntry,
    SemanticLayer,
    load_semantic_layer,
)

if TYPE_CHECKING:
    from fastembed import TextEmbedding
    from fastembed.rerank.cross_encoder import TextCrossEncoder


class RetrievalStrategy(StrEnum):
    """Which search one call runs. A `StrEnum`, so the member survives into an
    Evaluation table and a Grafana filter as the word a person reads.
    """

    TEXT = "text"
    """Term Frequency–Inverse Document Frequency (TF-IDF) cosine over the
    searchable text. Matches the words a question and an entry share, so an alias
    written into a Metric Definition is a direct hit and a synonym nobody wrote
    down is a miss. Returns nothing at all when no term overlaps."""

    VECTOR = "vector"
    """Cosine over `EMBEDDING_MODEL`'s sentence embeddings. Matches meaning rather
    than words, so it survives a question that shares no vocabulary with the entry
    — and, unlike `TEXT`, it always returns something, however far away."""

    HYBRID = "hybrid"
    """`TEXT` and `VECTOR` fused by `fuse`, over a candidate pool of
    `CANDIDATES` from each."""

    RERANKED = "reranked"
    """`HYBRID`'s candidates re-scored by `RERANKER_MODEL`, a cross-encoder that
    reads the question and one entry together instead of comparing two vectors
    embedded apart. The default, and the pipeline the Target State describes."""


class SearchableForm(StrEnum):
    """How the text index carries one entry — as one document, or as its fields.

    Orthogonal to `RetrievalStrategy`: a strategy is which search runs, and this is
    what the text half of that search is fitted on. `VECTOR` embeds the flat text
    whichever form is chosen, so it is the one strategy this cannot move.
    """

    FLAT = "flat"
    """One document per entry, every searchable field concatenated. A term matching
    the entry's own name counts for exactly what the same term inside its description
    counts for."""

    PER_FIELD = "per field"
    """One document per field per entry, scored apart and summed. Each field's cosine
    is normalised by that field's own length, so a term matching the short `name`
    outweighs the same term inside a long `description` without any weighting being
    written down."""


# Which form the text index is fitted in, and therefore what every Retrieval Strategy
# but `VECTOR` searches. Measured rather than chosen: `veritas/evaluation/retrieval.py`
# scores both over the Gold Question Set, and the Step Review that set this line carries
# the numbers and the losing form.
DEFAULT_SEARCHABLE_FORM = SearchableForm.PER_FIELD


# Both models are the small English ones of their family: the corpus is tens of
# entries and the App answers one question at a time, so nothing here is bounded by
# model size.
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
RERANKER_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"

# Term Frequency-Inverse Document Frequency (TF-IDF) settings for the text search.
# Two departures from scikit-learn's defaults, and each is a term the corpus would
# otherwise lose. The token pattern admits `&` inside a word, because the default
# one needs two word characters and splits on everything else, which drops `P&L`
# from the index entirely — a registered Ambiguous Term, and half the name of two
# Certified Metrics. Stop words go because without them the "what is our" of a
# question outweighs its one content word.
VECTORIZER_PARAMS = {"stop_words": "english", "token_pattern": r"(?u)\b\w[\w&]+\b"}

# How many entries a search returns, before closure adds what they name.
TOP_K = 5

# How many each of `TEXT` and `VECTOR` contributes to a fusion, and how many the
# re-ranker re-scores. Wider than `TOP_K` so an entry one searcher ranks low can
# still be rescued by the other; short enough that the cross-encoder scores a
# handful of pairs rather than the corpus.
CANDIDATES = 10

# The rank-fusion constant of Cormack, Clarke and Buettcher (2009), where
# Reciprocal Rank Fusion was introduced. It flattens the contribution of the top
# ranks, so one searcher's first place cannot outvote two searchers agreeing
# further down: at 60, a lone first place scores 1/61 and a pair of third places
# scores 2/63, and the pair wins. At 0 the lone first place would score 1 against
# their 2/3 and win instead.
RRF_K = 60

# Which fields of each entry type name other Semantic Entries. Parallel to
# `SEARCHABLE_FIELDS` and to the loader's `SQL_FIELDS`, and this is the one that
# reaches a Join Path: nothing searches for one, so an answer gets its routes
# because the entries that were found name them.
#
# A Join Path names nothing back — its `from_table`, `to_table` and `on` are
# Warehouse identifiers — so closure terminates there.
REFERENCE_FIELDS: dict[type[SemanticEntry], tuple[str, ...]] = {
    MetricDefinition: ("derives_from", "join_paths"),
    AmbiguousTerm: ("disambiguates",),
    DimensionDefinition: ("routes",),
    JoinPath: (),
}


def references(entry: SemanticEntry) -> list[str]:
    """The names of every Semantic Entry one entry names, in the order it names them.

    A route map contributes the Join Paths of all its routes rather than of one:
    which route applies depends on the table the query starts from, and that is not
    settled until SQL is generated.
    """
    named: list[str] = []
    for field in REFERENCE_FIELDS[type(entry)]:
        value = getattr(entry, field)
        if isinstance(value, Mapping):
            named.extend(name for route in value.values() for name in route)
        else:
            named.extend(value)
    return named


def fuse(rankings: list[list[str]]) -> list[str]:
    """Several rankings of names as one, by Reciprocal Rank Fusion.

    Each ranking contributes `1 / (RRF_K + position)` to every name it holds, and
    names sort by the total. Positions rather than scores, because a TF-IDF cosine
    and an embedding cosine are not on one scale and nothing normalises them onto
    one. Ties break on the name, so the order does not depend on which searcher ran
    first.

    The sort key negates the score rather than passing `reverse=True` because its
    two halves run in opposite directions: score descending, name ascending. Given
    `Gross Revenue` and `Net Revenue` tied, negating puts the higher score first and
    `Gross Revenue` ahead of `Net Revenue`; `reverse=True` would flip both halves
    and put `Net Revenue` first.
    """
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for position, name in enumerate(ranking, start=1):
            scores[name] += 1 / (RRF_K + position)
    return sorted(scores, key=lambda name: (-scores[name], name))


@cache
def embedding_model() -> "TextEmbedding":
    """`EMBEDDING_MODEL`, loaded once per process."""
    from fastembed import TextEmbedding

    return TextEmbedding(EMBEDDING_MODEL)


@cache
def reranker() -> "TextCrossEncoder":
    """`RERANKER_MODEL`, loaded once per process."""
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(RERANKER_MODEL)


class Retriever:
    """One Semantic Layer, indexed for search.

    The text index is fitted on construction, which needs no model and no network.
    The vector index and the two models behind the searches that use them are built
    on first use, so a caller that only ever runs `RetrievalStrategy.TEXT` never
    loads either.
    """

    def __init__(
        self, layer: SemanticLayer, form: SearchableForm = DEFAULT_SEARCHABLE_FORM
    ) -> None:
        self.layer = layer
        self.form = form
        self.entries = {entry.name: entry for entry in layer.entries()}
        self.records = [
            record for record in searchable_entries(layer) if record["text"]
        ]
        self.text_by_name = {
            record["name"]: record["text"] for record in self.records
        }
        self._text_index = self._fitted_index(form)

    def _fitted_index(self, form: SearchableForm) -> Index:
        """The text index of one `SearchableForm`, over the same records.

        `name` is a keyword field in the flat form and a text field in the per-field
        one — a field cannot usefully be both, and identity does not need it either
        way, because a hit carries the whole record and is resolved by the `name` key
        on it.
        """
        index = Index(
            text_fields=["text"] if form is SearchableForm.FLAT else list(TEXT_FIELDS),
            keyword_fields=["name", "kind"] if form is SearchableForm.FLAT else ["kind"],
            vectorizer_params=VECTORIZER_PARAMS,
        )
        index.fit(self.records)
        return index

    @cached_property
    def _vector_index(self) -> VectorSearch:
        """The same records, as sentence embeddings."""
        index = VectorSearch(keyword_fields=["name", "kind"])
        index.fit(
            np.array(
                list(embedding_model().embed(
                    [record["text"] for record in self.records]
                ))
            ),
            self.records,
        )
        return index

    def rank(
        self,
        question: str,
        strategy: RetrievalStrategy = RetrievalStrategy.RERANKED,
        top_k: int = TOP_K,
    ) -> list[SemanticEntry]:
        """The `top_k` Semantic Entries one search scores highest, best first.

        What Evaluation measures. May be shorter than `top_k`, and `TEXT` may
        return nothing at all when the question shares no term with the corpus.
        """
        match strategy:
            case RetrievalStrategy.TEXT:
                names = self._text_hits(question, top_k)
            case RetrievalStrategy.VECTOR:
                names = self._vector_hits(question, top_k)
            case RetrievalStrategy.HYBRID:
                names = self._fused_hits(question, top_k)
            case RetrievalStrategy.RERANKED:
                names = self._reranked_hits(question, top_k)
            case _:
                raise ValueError(
                    f"{strategy!r} is not a RetrievalStrategy — "
                    f"{sorted(RetrievalStrategy)} are"
                )
        return [self.entries[name] for name in names]

    def retrieve(
        self,
        question: str,
        strategy: RetrievalStrategy = RetrievalStrategy.RERANKED,
        top_k: int = TOP_K,
    ) -> list[SemanticEntry]:
        """Everything an answer to this question may be built from.

        The ranking first, best first, then the entries it names — so a caller
        reading the list in order reads it in relevance order and then in the order
        the routes and derivations were reached.
        """
        found = self.rank(question, strategy, top_k)
        return found + self._closure(found)

    def _closure(self, found: list[SemanticEntry]) -> list[SemanticEntry]:
        """Every entry the ranked hits name, transitively, that they do not hold.

        Transitive because a derivation chains: `Account Value` names `Cash
        Balance`, and `Cash Balance` names the Join Paths it is computed across.
        """
        seen = {entry.name for entry in found}
        pending = list(found)
        added: list[SemanticEntry] = []
        while pending:
            for name in references(pending.pop(0)):
                if name in seen:
                    continue
                seen.add(name)
                added.append(self.entries[name])
                pending.append(added[-1])
        return added

    def _text_hits(self, question: str, limit: int) -> list[str]:
        return [
            hit["name"] for hit in self._text_index.search(question, num_results=limit)
        ]

    def _vector_hits(self, question: str, limit: int) -> list[str]:
        query = next(iter(embedding_model().query_embed([question])))
        return [
            hit["name"]
            for hit in self._vector_index.search(query, num_results=limit)
        ]

    def _fused_hits(self, question: str, limit: int) -> list[str]:
        return fuse([
            self._text_hits(question, CANDIDATES),
            self._vector_hits(question, CANDIDATES),
        ])[:limit]

    def _reranked_hits(self, question: str, limit: int) -> list[str]:
        candidates = self._fused_hits(question, CANDIDATES)
        if not candidates:
            return []
        scores = list(
            reranker().rerank(question, [self.text_by_name[n] for n in candidates])
        )
        # Negated for the same reason as in `fuse`, but keyed on the score alone:
        # the sort is stable, so two candidates the cross-encoder scores equally
        # keep the order the fusion gave them rather than falling back on the name.
        ranked = sorted(zip(scores, candidates), key=lambda pair: -pair[0])
        return [name for _, name in ranked][:limit]


@cache
def default_retriever() -> Retriever:
    """The Retriever over `semantic/`, built once per process."""
    return Retriever(load_semantic_layer())


def rank(
    question: str,
    strategy: RetrievalStrategy = RetrievalStrategy.RERANKED,
    top_k: int = TOP_K,
) -> list[SemanticEntry]:
    """`Retriever.rank` over the Semantic Layer at `semantic/`."""
    return default_retriever().rank(question, strategy, top_k)


def retrieve(
    question: str,
    strategy: RetrievalStrategy = RetrievalStrategy.RERANKED,
    top_k: int = TOP_K,
) -> list[SemanticEntry]:
    """`Retriever.retrieve` over the Semantic Layer at `semantic/`."""
    return default_retriever().retrieve(question, strategy, top_k)
