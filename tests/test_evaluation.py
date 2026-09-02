"""The Evaluation Measures for Retrieval: what they compute, and what they compute it over.

Three claims. The **measure claim**: hit rate and Mean Reciprocal Rank (MRR) are the
textbook measures on a ranking whose answer is known, checked on a toy ranking where
every position is written down. The **ground truth claim**: what a ranking is scored
against is the part of a Gold Question's Relevant Set a search could return, and the
question it is searched for is the one a correct rewrite step would have produced —
derived from the gold SQL, so nothing here calls a model. The **sweep claim**: the two
settings [DEBT-027](../.claude/docs/debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match)
and [DEBT-030](../.claude/docs/debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it)
were opened about are both varied, over the same questions and the same relevant sets.

The sweep here is restricted to `RetrievalStrategy.TEXT`, which needs no model and no
network. The whole sweep is `uv run python -m veritas.evaluation retrieval`, and the
Step Review carries what it printed.
"""

import pytest

from veritas.evaluation import (
    Expectation,
    gold_resolutions,
    load_gold_questions,
    measure_retrieval,
    measures_of,
    reciprocal_rank,
    relevant_entries,
    scored,
    searchable_relevant_set,
    searched_as,
)
from veritas.orchestrator import RewriteForm, ambiguous_terms_in
from veritas.retrieval import RetrievalStrategy, SearchableForm, searchable_text
from veritas.semantic import JoinPath
from veritas.validation import ValidationGate

# A ranking and the entries that should have been in it, with every position known. Two
# relevant entries, at positions 2 and 4, so a measure that scores the *first* hit and
# one that scores the last are told apart.
RANKED = ["revenue", "Net Revenue", "by trade date", "Gross Revenue", "by region"]
RELEVANT = {"Net Revenue", "Gross Revenue"}


@pytest.fixture(scope="module")
def gold():
    """The Gold Question Set, loaded once."""
    return load_gold_questions()


@pytest.fixture(scope="module")
def gate(warehouse, semantic):
    """One Gate over the built Warehouse and the corpus the gold SQL is written against."""
    return ValidationGate(warehouse, semantic=semantic)


# -- the measure claim -----------------------------------------------------------


def test_the_first_relevant_entry_is_what_a_reciprocal_rank_scores():
    """Position 2 of five, and the second relevant entry at position 4 does not move it."""
    assert reciprocal_rank(RANKED, RELEVANT) == 0.5
    assert reciprocal_rank(RANKED, {"Gross Revenue"}) == 0.25
    assert reciprocal_rank(RANKED, {"revenue"}) == 1.0


def test_a_ranking_that_holds_nothing_relevant_scores_zero():
    """The two ways a search misses: it ranked the wrong entries, or it ranked none."""
    assert reciprocal_rank(RANKED, {"Trade Count"}) == 0.0
    assert reciprocal_rank([], RELEVANT) == 0.0


def test_hit_rate_is_the_share_of_questions_with_a_reciprocal_rank_above_zero():
    """Both measures off one number, which is what keeps them agreeing about a hit."""
    assert measures_of([1.0, 0.5, 0.0, 0.0]) == (0.5, 0.375)
    assert measures_of([1.0, 1.0]) == (1.0, 1.0)
    assert measures_of([0.0]) == (0.0, 0.0)


def test_no_question_is_not_a_perfect_score():
    """An empty sweep reads as zero rather than dividing by nothing."""
    assert measures_of([]) == (0.0, 0.0)


# -- the ground truth claim ------------------------------------------------------


def test_a_ranking_is_scored_against_the_entries_a_search_could_return(gold, gate):
    """Every Relevant Set loses its Join Paths and keeps everything else.

    A Join Path publishes no searchable text, so it is in neither index and `rank` can
    never return one. Scoring against it would make every question a partial miss for a
    reason no setting could change.
    """
    by_name = {entry.name: entry for entry in gate.semantic.entries()}
    dropped = 0
    for question in gold:
        derived = relevant_entries(question, gate)
        searchable = searchable_relevant_set(question, gate)
        dropped += sum(1 for entry in derived if isinstance(entry, JoinPath))
        assert set(searchable) == {
            entry.name for entry in derived if not isinstance(entry, JoinPath)
        }, question.name
        assert all(searchable_text(by_name[name]) for name in searchable)
    assert dropped, "no Join Path was dropped — this check proved nothing"


def test_only_a_question_that_should_be_answered_is_scored(gold, gate):
    """A refusal and a Clarifying Question have no entry they should have retrieved."""
    wanted = {question.name for question, _ in scored(gold, gate)}
    assert wanted == {
        question.name
        for question in gold
        if question.expects is Expectation.ANSWER
    }
    assert wanted, "nothing was scored — this check proved nothing"


def test_a_questions_resolutions_are_read_off_its_own_gold_sql(gold, gate):
    """No model call: the meaning is the Certified Metric the gold statement computes.

    Every answerable question that says an Ambiguous Term resolves it, and to a meaning
    that term stands between — which is what makes the rewritten question the one a
    correct rewrite step would have produced.
    """
    said = 0
    for question, _ in scored(gold, gate):
        terms = ambiguous_terms_in(question.question, gate.semantic)
        resolutions = gold_resolutions(question, gate)
        assert set(resolutions) <= {term.name for term in terms}
        for term in terms:
            said += 1
            assert resolutions.get(term.name), (
                f"{question.name}: says {term.name!r} and its gold SQL resolves nothing"
            )
            assert set(resolutions[term.name]) <= set(term.disambiguates)
    assert said, "no scored question says an Ambiguous Term — this check proved nothing"


def test_the_two_rewrite_forms_differ_on_exactly_the_questions_that_say_a_term(gold, gate):
    """A question that says none is itself under both forms, so the setting cannot move it."""
    differ = 0
    for question, _ in scored(gold, gate):
        forms = {form: searched_as(question, gate, form) for form in RewriteForm}
        if gold_resolutions(question, gate):
            differ += 1
            assert forms[RewriteForm.APPENDED] != forms[RewriteForm.SPLICED], question.name
        else:
            assert set(forms.values()) == {question.question}, question.name
    assert differ, "no question carried a rewrite — this check proved nothing"


# -- the sweep claim -------------------------------------------------------------


def test_the_sweep_scores_every_setting_over_the_same_questions(gold, gate):
    """One row per setting, each a rate over the same denominator.

    `TEXT` only, so this needs no model and no network. The other three strategies are
    the same code path with a different `RetrievalStrategy`, and the committed command
    runs all four.
    """
    rows = measure_retrieval(gold, gate, strategies=[RetrievalStrategy.TEXT])
    settings = [(row.searchable_form, row.rewrite_form) for row in rows]
    assert settings == [
        (searchable_form, rewrite_form)
        for searchable_form in SearchableForm
        for rewrite_form in RewriteForm
    ]
    denominator = len(scored(gold, gate))
    for row in rows:
        assert row.questions == denominator
        assert 0.0 <= row.mrr <= row.hit_rate <= 1.0, row
        print(f"\n  {row.searchable_form:10} {row.rewrite_form:10} "
              f"hit {row.hit_rate:.3f}  mrr {row.mrr:.3f}")


def test_a_sweep_over_no_strategy_and_no_setting_measures_nothing(gold, gate):
    """The loops are over what they are given, so an empty sweep is empty rather than default."""
    assert measure_retrieval(gold, gate, strategies=[]) == []
    assert measure_retrieval(gold, gate, searchable_forms=[]) == []
