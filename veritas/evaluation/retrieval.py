"""Scores Retrieval over the Gold Question Set: hit rate and Mean Reciprocal Rank.

Both are [`Evaluation Measures`](../../.claude/docs/glossary.md#a-the-system) — *"hit
rate and MRR for Retrieval"* — and both are computed over `Retriever.rank`, which
returns only what a search scored. `retrieve` adds every entry those hits name, so
scoring it would credit a search for a Join Path no search can reach.

**One row per Retrieval Strategy per setting, and the settings are the two open
questions.** Which form the corpus is indexed in is
[DEBT-027](../../.claude/docs/debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match);
which form a resolved meaning is written into the question in is
[DEBT-030](../../.claude/docs/debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it).
Neither can be settled by argument, so the sweep runs every combination of them and
the numbers choose.

**Nothing here calls a model.** A question's resolved meanings are derived from its
own gold SQL — the Certified Metrics the statement computes, kept where the Ambiguous
Term stands between them — so the rewritten question the sweep searches with is the
one a correct rewrite step would have produced, at no key and no call.
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from veritas.evaluation.gold import (
    GoldQuestion,
    metrics_touched,
    reading_of,
    relevant_entries,
)
from veritas.orchestrator import (
    RewriteForm,
    ambiguous_terms_in,
    rewritten_with,
)
from veritas.retrieval import (
    TOP_K,
    RetrievalStrategy,
    Retriever,
    SearchableForm,
    searchable_text,
)
from veritas.validation import ValidationGate


@dataclass(frozen=True, slots=True)
class RetrievalMeasures:
    """The Evaluation Measures for Retrieval under one setting of it.

    `questions` is how many Gold Questions were scored, because a rate over a
    different denominator is a different number and the two must travel together.
    """

    strategy: RetrievalStrategy
    searchable_form: SearchableForm
    rewrite_form: RewriteForm
    questions: int
    hit_rate: float
    mrr: float


def reciprocal_rank(ranked: Sequence[str], relevant: Collection[str]) -> float:
    """One over the position of the first relevant entry, or zero if none was ranked.

    Both measures come off this one number: MRR is its mean, and a hit is it being
    above zero. So hit rate and MRR cannot come to disagree about what a hit is.
    """
    wanted = set(relevant)
    for position, name in enumerate(ranked, start=1):
        if name in wanted:
            return 1 / position
    return 0.0


def measures_of(reciprocal_ranks: Sequence[float]) -> tuple[float, float]:
    """Hit rate and MRR over one question set's reciprocal ranks."""
    if not reciprocal_ranks:
        return 0.0, 0.0
    return (
        sum(1 for rank in reciprocal_ranks if rank) / len(reciprocal_ranks),
        sum(reciprocal_ranks) / len(reciprocal_ranks),
    )


def searchable_relevant_set(gold: GoldQuestion, gate: ValidationGate) -> tuple[str, ...]:
    """The part of a Gold Question's Relevant Set a search could return.

    A Join Path publishes no searchable text, so it is in neither index and no ranking
    can hold one — an answer reaches its routes because the entries that were found
    name them. Scoring a ranking against a Relevant Set that includes them would
    measure that shape of the corpus rather than the search.

    A question whose correct ending is a refusal or a Clarifying Question has an empty
    Relevant Set and therefore an empty one here, which is what leaves it out of the
    sweep: there is no entry it *should* have retrieved.
    """
    return tuple(
        entry.name for entry in relevant_entries(gold, gate) if searchable_text(entry)
    )


def gold_resolutions(
    gold: GoldQuestion, gate: ValidationGate
) -> dict[str, tuple[str, ...]]:
    """What a correct rewrite step resolves this question's Ambiguous Terms to.

    Read off the gold SQL, in the shape `Rewrite.resolutions` carries: the Certified
    Metrics the statement computes, kept for each term the question says that stands
    between them. A term the statement's metrics do not answer to is left out, which is
    the same thing an unresolved term is downstream.
    """
    terms = ambiguous_terms_in(gold.question, gate.semantic)
    if not terms or not gold.sql:
        return {}
    computed = [
        metric.name for metric in metrics_touched(reading_of(gold.sql, gate), gate)
    ]
    resolved = {}
    for term in terms:
        meant = tuple(name for name in computed if name in term.disambiguates)
        if meant:
            resolved[term.name] = meant
    return resolved


def searched_as(
    gold: GoldQuestion, gate: ValidationGate, form: RewriteForm
) -> str:
    """The text Retrieval searches with for this Gold Question, in one rewrite form.

    A question that says no Ambiguous Term is itself under both forms, so the rewrite
    setting moves only the questions that say one.
    """
    return rewritten_with(
        gold.question, gold_resolutions(gold, gate), gate.semantic, form
    )


def scored(
    questions: Sequence[GoldQuestion], gate: ValidationGate
) -> list[tuple[GoldQuestion, tuple[str, ...]]]:
    """Each Gold Question a ranking can be scored for, with what it should have found."""
    with_sets = ((gold, searchable_relevant_set(gold, gate)) for gold in questions)
    return [(gold, relevant) for gold, relevant in with_sets if relevant]


def measure_retrieval(
    questions: Sequence[GoldQuestion],
    gate: ValidationGate,
    strategies: Sequence[RetrievalStrategy] = tuple(RetrievalStrategy),
    searchable_forms: Sequence[SearchableForm] = tuple(SearchableForm),
    rewrite_forms: Sequence[RewriteForm] = tuple(RewriteForm),
    top_k: int = TOP_K,
) -> list[RetrievalMeasures]:
    """Every combination of the settings, scored over the same Gold Questions.

    One `Retriever` per searchable form, because that is what the form is a property
    of; the rewrite form changes only the text a question is searched with, so both
    forms are searched through the same two indexes.
    """
    wanted = scored(questions, gate)
    searched = {
        form: [searched_as(gold, gate, form) for gold, _ in wanted]
        for form in rewrite_forms
    }
    rows: list[RetrievalMeasures] = []
    for searchable_form in searchable_forms:
        retriever = Retriever(gate.semantic, searchable_form)
        for rewrite_form in rewrite_forms:
            for strategy in strategies:
                ranks = [
                    reciprocal_rank(
                        [entry.name for entry in retriever.rank(text, strategy, top_k)],
                        relevant,
                    )
                    for (_, relevant), text in zip(wanted, searched[rewrite_form])
                ]
                hit_rate, mrr = measures_of(ranks)
                rows.append(
                    RetrievalMeasures(
                        strategy, searchable_form, rewrite_form, len(ranks), hit_rate, mrr
                    )
                )
    return rows


__all__ = [
    "RetrievalMeasures",
    "gold_resolutions",
    "measure_retrieval",
    "measures_of",
    "reciprocal_rank",
    "scored",
    "searchable_relevant_set",
    "searched_as",
]
