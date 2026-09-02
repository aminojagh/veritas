"""The Evaluation Measures: what they compute, and what they compute it over.

**Retrieval — three claims.** The **measure claim**: hit rate and Mean Reciprocal Rank
(MRR) are the textbook measures on a ranking whose answer is known, checked on a toy
ranking where every position is written down. The **ground truth claim**: what a ranking
is scored against is the part of a Gold Question's Relevant Set a search could return,
and the question it is searched for is the one a correct rewrite step would have
produced — derived from the gold SQL, so nothing here calls a model. The **sweep
claim**: the two settings
[DEBT-027](../.claude/docs/debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match)
and [DEBT-030](../.claude/docs/debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it)
were opened about are both varied, over the same questions and the same relevant sets.

**Generation — three more.** The **ending claim**: which of a Grounded Answer's three
endings came back, and which step of the flow produced it, are both read off the answer
rather than guessed at. The **accuracy claim**: a question is right when it ends the way
the set says and, where that ending is a number, returns the gold result — and a
question whose own gold statement the Validation Gate refuses is nobody's generation
failure and is left out. The **judge claim**: the judge is shown the statements and
never the two result sets, so its agreement with Execution Accuracy measures something
that measure does not already say.

Every test here drives a stub, so the suite needs no key and no network — the generation
stub answers off the Gold Question Set itself, which is what lets the measures be
checked against a run whose right answer is known. The sweeps that spend a key are
`uv run python -m veritas.evaluation retrieval` and `… generation`, and the Step Review
carries what they printed.
"""

import json
from decimal import Decimal

import pytest

from veritas.evaluation import (
    EndedBy,
    Expectation,
    GenerationMeasures,
    Scored,
    answerable_by_veritas,
    correctly_answered,
    ended_as,
    ended_by,
    gold_resolutions,
    judgement_of,
    judgement_text,
    load_gold_questions,
    measure_generation,
    measure_retrieval,
    measures_of,
    reciprocal_rank,
    relevant_entries,
    scored,
    searchable_relevant_set,
    searched_as,
)
from veritas.evaluation.generation import JUDGE_RULES
from veritas.orchestrator import (
    PROMPT_FORMS,
    RESOLUTION_RULES,
    GroundedAnswer,
    PromptForm,
    RewriteForm,
    ambiguous_terms_in,
    rewritten_with,
)
from veritas.retrieval import RetrievalStrategy, SearchableForm, searchable_text
from veritas.semantic import JoinPath
from veritas.validation import ANALYST, ValidationGate

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


# -- the ending claim ------------------------------------------------------------


class GoldenModel:
    """A model that answers every call off the Gold Question Set itself.

    Three kinds of call, told apart by the instruction each carries: the resolution
    step's, either `PromptForm`'s generation instruction, and the judge's. It resolves
    each question's Ambiguous Terms the way that question's own gold SQL does, writes
    that question's gold statement, and returns whichever verdict it was built with — so
    a sweep driven by it scores what a model that got everything right would score,
    which is what makes the measures checkable without a key.

    What it resolves a question's terms to follows the ending that question calls
    correct, because that is the only reading under which every one of them is answered
    right. A number: whatever its gold SQL computes. A Clarifying Question: nothing, so
    the flow asks back. A refusal: the first certified meaning of each term, because what
    such a question claims is that the *generator* refuses it and a stub that asked back
    would never reach the step under test.
    """

    def __init__(self, questions, gate, verdict=True):
        self.verdict = verdict
        self.calls: list[tuple[str, str]] = []
        self.resolved: dict[str, str] = {}
        self.written: dict[str, str] = {}
        for gold in questions:
            resolutions = {}
            if gold.answerable:
                resolutions = gold_resolutions(gold, gate)
            elif gold.expects is Expectation.REFUSAL:
                resolutions = {
                    term.name: (term.disambiguates[0],)
                    for term in ambiguous_terms_in(gold.question, gate.semantic)
                }
            self.resolved[gold.question] = json.dumps(
                {name: list(metrics) for name, metrics in resolutions.items()}
            )
            rewritten = rewritten_with(gold.question, resolutions, gate.semantic)
            self.written[rewritten] = json.dumps(
                {"sql": gold.sql} if gold.sql
                else {"sql": None, "why": "no entry below computes this"}
            )

    def complete(self, system: str, user: str, json_object: bool = False) -> str:
        self.calls.append((system, user))
        if system.startswith(RESOLUTION_RULES):
            return self._for(self.resolved, user)
        if system.startswith(JUDGE_RULES):
            return json.dumps({} if self.verdict is None else {"correct": self.verdict})
        return self._for(self.written, user)

    @staticmethod
    def _for(replies: dict[str, str], user: str) -> str:
        if user not in replies:
            raise AssertionError(f"nothing gold to answer {user!r} with")
        return replies[user]


@pytest.fixture(scope="module")
def scorable(gold, gate):
    """The Gold Questions the sweep scores: those whose own gold statement Veritas may
    run."""
    return [one for one in gold if answerable_by_veritas(one, gate)]


@pytest.fixture(scope="module")
def allowing(gold, gate):
    """A gold statement and the allowing verdict it earns.

    Taken from the set rather than written, because a Grounded Answer refuses to carry a
    number under any verdict but a real allowing one.
    """
    one = next(
        item for item in gold if item.sql and gate.judge(item.sql, ANALYST).allowed
    )
    return one.sql, gate.judge(one.sql, ANALYST)


def test_which_of_the_three_endings_came_back_is_read_off_the_answer(allowing):
    """The same three words a Gold Question is written with, so the two are comparable."""
    sql, outcome = allowing
    assert ended_as(
        GroundedAnswer(question="q", clarifying_question="which?")
    ) is Expectation.CLARIFYING_QUESTION
    assert ended_as(GroundedAnswer(question="q", refusal="no")) is Expectation.REFUSAL
    assert ended_as(
        GroundedAnswer(question="q", sql=sql, columns=("answer",), outcome=outcome)
    ) is Expectation.ANSWER


def test_which_step_ended_the_question_is_read_off_the_answer(allowing, gate):
    """Five of `flow.py`'s endings, each from the Grounded Answer shape it produces.

    The Gate's and the engine's differ only in whether the verdict allowed the statement
    that produced no number, which is the distinction this pins.
    """
    sql, outcome = allowing
    refused = gate.judge(f"SELECT count(*) * 2 AS answer FROM ({sql})", ANALYST)
    assert not refused.allowed
    endings = {
        EndedBy.REWRITE: GroundedAnswer(question="q", clarifying_question="which?"),
        EndedBy.NO_SQL: GroundedAnswer(question="q", refusal="nothing defines it"),
        EndedBy.GATE: GroundedAnswer(
            question="q", sql=sql, outcome=refused, refusal=refused.explanation
        ),
        EndedBy.ENGINE: GroundedAnswer(
            question="q", sql=sql, outcome=outcome, refusal="the engine would not run it"
        ),
        EndedBy.ANSWER: GroundedAnswer(
            question="q", sql=sql, columns=("answer",), outcome=outcome
        ),
    }
    for step, answer in endings.items():
        assert ended_by(answer) is step, step


# -- the accuracy claim ----------------------------------------------------------


def test_a_question_is_right_only_when_it_ends_as_the_set_says(gold, allowing):
    """A question that should have been refused and was answered is wrong however good
    the number is, which is the whole reason a refusal is a Gold Question at all."""
    sql, outcome = allowing
    answered = GroundedAnswer(
        question="q", sql=sql, columns=("answer",), outcome=outcome
    )
    refused = 0
    for one in gold:
        if one.expects is Expectation.REFUSAL:
            refused += 1
            assert not correctly_answered(one, answered)
            assert correctly_answered(one, GroundedAnswer(question="q", refusal="no"))
    assert refused, "no Gold Question expects a refusal — this check proved nothing"


def test_an_answered_question_is_right_only_when_its_result_is_the_gold_result(
    gold, gate, warehouse
):
    """The gold statement's own rows are right; the same rows doubled are not, at any
    tolerance this measure could be given."""
    one = next(
        item for item in gold
        if item.answerable and gate.judge(item.sql, ANALYST).allowed
    )
    outcome = gate.judge(one.sql, ANALYST)
    columns, rows = warehouse.query_with_columns(one.sql)

    def came_back(returned):
        return GroundedAnswer(
            question=one.question, sql=one.sql, columns=columns,
            rows=tuple(returned), outcome=outcome,
        )

    assert correctly_answered(one, came_back(rows))
    doubled = [
        tuple(value * 2 if isinstance(value, Decimal | int | float) else value
              for value in row)
        for row in rows
    ]
    assert doubled != list(rows), one.name
    assert not correctly_answered(one, came_back(doubled))


def test_a_question_whose_own_gold_statement_the_gate_refuses_is_left_out(
    gold, scorable, gate
):
    """[DEBT-035](../.claude/docs/debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)'s
    cost, derived rather than listed.

    No model can answer a question Veritas may not run the correct statement for, so
    scoring it would report a Gate limitation as a generation failure. Nothing here names
    a question: the day the Gate stops refusing that statement the exclusion disappears
    by itself, and this prints nothing instead.
    """
    left_out = [one for one in gold if one not in scorable]
    for one in left_out:
        assert one.sql and not gate.judge(one.sql, ANALYST).allowed
        print(f"\n  excluded: {one.name}")
    for one in scorable:
        assert not one.sql or gate.judge(one.sql, ANALYST).allowed
    assert len(scorable) + len(left_out) == len(gold)


# -- the generation sweep claim --------------------------------------------------


def test_the_sweep_scores_every_prompt_against_every_model_over_the_same_questions(
    scorable, warehouse, gate, retriever
):
    """One row per prompt per model, and a model that answers gold scores gold.

    The whole flow runs for every cell — resolve, retrieve, ground, generate, judge,
    execute — so what this pins is the measures **and** the wiring the prompt form
    reaches the generator through.
    """
    models = {
        "first": GoldenModel(scorable, gate),
        "second": GoldenModel(scorable, gate),
    }
    rows = measure_generation(
        scorable, warehouse, gate, retriever, models,
        judge_model=GoldenModel(scorable, gate),
    )
    assert [(row.prompt_form, row.model) for row in rows] == [
        (form, label) for form in PromptForm for label in models
    ]
    for row in rows:
        assert row.right_ending == (len(scorable), len(scorable)), [
            one.gold.name for one in row.failed
        ]
        assert row.execution_accuracy == 1.0
        assert row.judge_agreement == 1.0
        assert not row.unreached
        print(f"\n  {row.prompt_form:6} {row.model:6} ending "
              f"{row.right_ending[0]}/{row.questions}  "
              f"accuracy {row.execution_accuracy:.3f}  "
              f"agreement {row.judge_agreement:.3f}")


def test_each_prompt_form_reaches_the_generator_as_its_own_instruction(
    scorable, warehouse, gate, retriever
):
    """The seam the sweep varies: two arms, two instructions, each carrying its own
    form's text and nothing of the other's.

    Over one question, and an answerable one, because a question that ends at the
    rewrite step never reaches the instruction under test.
    """
    one = [next(item for item in scorable if item.answerable)]
    asked = {}
    for form in PromptForm:
        model = GoldenModel(scorable, gate)
        measure_generation(
            one, warehouse, gate, retriever, {"one": model}, prompt_forms=[form],
        )
        asked[form] = [
            system for system, _ in model.calls
            if not system.startswith(RESOLUTION_RULES)
        ]
    for form, instructions in asked.items():
        assert instructions, form
        assert all(said.startswith(PROMPT_FORMS[form]) for said in instructions)
    assert asked[PromptForm.RULES] != asked[PromptForm.SHAPE]


def test_a_sweep_over_no_prompt_and_no_model_measures_nothing(
    scorable, warehouse, gate, retriever
):
    """The loops are over what they are given, so an empty sweep is empty rather than
    default — and neither loop is the one that matters."""
    assert measure_generation(
        scorable, warehouse, gate, retriever, {}
    ) == []
    assert measure_generation(
        scorable, warehouse, gate, retriever, {"one": object()}, prompt_forms=[]
    ) == []


# -- the judge claim -------------------------------------------------------------


def test_the_judge_is_shown_the_statements_and_never_the_two_result_sets(
    gold, gate, warehouse
):
    """Comparing result sets is what Execution Accuracy already does, exactly and without
    an opinion, so a judge shown them would make agreement a measure of nothing."""
    one = next(
        item for item in gold
        if item.answerable and gate.judge(item.sql, ANALYST).allowed
    )
    columns, rows = warehouse.query_with_columns(one.sql)
    said = judgement_text(
        one,
        GroundedAnswer(
            question=one.question, sql=one.sql, columns=columns, rows=tuple(rows),
            outcome=gate.judge(one.sql, ANALYST),
        ),
    )
    assert one.question in said
    assert one.sql.strip() in said
    for row in one.result:
        for value in row:
            assert str(value) not in said, value


def test_what_the_judge_is_shown_of_a_question_that_was_not_answered(gold):
    """A refusal and a Clarifying Question are what the system did, so they are what the
    judge is shown — beside the ending the set calls correct, and no statement, because
    there is none to show."""
    refused = next(one for one in gold if one.expects is Expectation.REFUSAL)
    said = judgement_text(refused, GroundedAnswer(question="q", refusal="no entry does"))
    assert "no entry does" in said and str(Expectation.REFUSAL) in said

    asking = next(
        one for one in gold if one.expects is Expectation.CLARIFYING_QUESTION
    )
    said = judgement_text(
        asking, GroundedAnswer(question="q", clarifying_question="which?")
    )
    assert "which?" in said and str(Expectation.CLARIFYING_QUESTION) in said


def test_a_judge_that_gives_no_usable_verdict_is_left_out_of_the_agreement(gold):
    """Abstaining is neither agreement nor disagreement, and counting it as either would
    move a measure of the judge with the shape of its own failures."""
    assert judgement_of('{"correct": true}') is True
    assert judgement_of('{"correct": false}') is False
    for nothing in ("{}", '{"correct": "yes"}', '{"why": "it is fine"}'):
        assert judgement_of(nothing) is None

    row = GenerationMeasures(
        PromptForm.RULES,
        "stub",
        (
            Scored(gold[0], EndedBy.ANSWER, correct=True, judged=True),
            Scored(gold[0], EndedBy.GATE, correct=False, judged=True),
            Scored(gold[0], EndedBy.ANSWER, correct=True, judged=None),
        ),
    )
    assert len(row.judged) == 2
    assert row.judge_agreement == 0.5


def test_agreement_is_with_execution_accuracy_rather_than_with_the_judge_alone(gold):
    """A judge that calls everything correct agrees only where the objective measure
    does, which is what makes the figure worth printing at all."""
    row = GenerationMeasures(
        PromptForm.SHAPE,
        "stub",
        tuple(
            Scored(gold[0], EndedBy.ANSWER, correct=correct, judged=True)
            for correct in (True, True, False, False)
        ),
    )
    assert row.judge_agreement == 0.5
