"""What the Orchestrator grounds a model in, and every way a question can come back.

Three claims. The **grounding claim**: the prompt is built from retrieved entries and
the identity asking, so a metric that was not retrieved publishes no expression to the
model and no Warehouse table reaches the prompt except through an entry that names it.
The **flow claim**: each of the five ways a question ends without a number comes back as
a Grounded Answer saying which, and an answered one carries its SQL, its Lineage and the
verdict it ran under. The **contract claim**: a Grounded Answer cannot be built that
says two things at once, or that carries a number without the statement and the verdict
behind it.

Every test here drives a scripted model, so the suite needs no key and no network. The
one test that calls the configured provider spends real credit and runs only when
`VERITAS_LIVE_MODEL` says so — a key being present is not consent.
"""

import json
import os
import re

import pytest

from veritas.llm import LIVE_VARIABLE
from veritas.orchestrator import (
    GROUNDED_FIELDS,
    PROMPT_FORMS,
    REWRITTEN_QUESTION,
    GroundedAnswer,
    Lineage,
    Orchestrator,
    PromptForm,
    entry_text,
    generation_instruction,
)
from veritas.semantic import MetricDefinition
from veritas.validation import ACCESS_AXIS, ANALYST, RejectionReason, ValidationGate

# A Warehouse identifier, as the corpus and a statement both spell one. Every table in
# `veritas/warehouse/schema.sql` is `fct_` or `dim_` prefixed.
TABLE = re.compile(r"\b(?:fct|dim)_[a-z_]+")

# A question saying no Ambiguous Term, so the rewrite step costs no model call and the
# only call in the flow is the generation one.
UNAMBIGUOUS = "how many trades did we make"

# The statement a model that read the rules writes for `UNAMBIGUOUS`: `Trade Count`'s
# certified expression over its own `from_table`, reached through the `by region` axis's
# route and narrowed to the region the Access Profile permits. Written out rather than
# assembled from the corpus, because what it stands for here is a **model's** output —
# a builder would test the builder.
CERTIFIED = (
    "SELECT count(fct_trade.trade_id) AS answer "
    "FROM fct_trade "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "WHERE dim_client.client_region = 'EU'"
)

# The same question with a breakdown in it: the axis aliased `slice` and the metric
# aliased `answer`, which is the shape the generation rules ask for and the names the
# engine hands back with the rows.
BREAKDOWN = (
    "SELECT dim_instrument.instrument_type AS slice, count(fct_trade.trade_id) AS answer "
    "FROM fct_trade "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "JOIN dim_instrument ON dim_instrument.instrument_id = fct_trade.instrument_id "
    "WHERE dim_client.client_region = 'EU' "
    "GROUP BY dim_instrument.instrument_type"
)

# The same question answered with arithmetic of the model's own — the failure Veritas
# exists to prevent, and the one the Gate calls a Shadow Metric.
SHADOW = (
    "SELECT count(fct_trade.trade_id) * 2 AS answer "
    "FROM fct_trade "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "WHERE dim_client.client_region = 'EU'"
)

# A small set of questions the corpus covers, one per fact table the nine metrics start
# from, plus one breakdown. The live test asks these of a real provider.
COVERED = (
    "how many trades did we make",
    "what was our gross revenue",
    "what is the total cash balance",
    "what was our realised P&L",
    "break our net revenue down by region",
)

# A question the Target State names as having no answer: *"'What columns are in
# `fct_trade`?', 'what instrument types do we hold?', 'show me ten rows' — none of these
# have an answer. Veritas is a metrics copilot, not a database browser."* The schema is
# deliberately absent from the corpus, so nothing the model is shown can produce it.
#
# It replaced *"which instrument did we trade most often"*, which is **not** uncovered:
# `Trade Count` broken down by the `by instrument type` axis answers it, and one of the
# two providers wrote exactly that statement and the Gate allowed it — correctly.
UNCOVERED = "what columns are in fct_trade"


class ScriptedModel:
    """A `LanguageModel` answering each call with the next reply it was given.

    A question can cost two calls — resolving its Ambiguous Terms, then writing SQL —
    so a stub with one fixed reply cannot drive the flow. Every call is recorded, which
    is how the tests below assert that a step was reached or skipped.
    """

    def __init__(self, *replies: object) -> None:
        self.replies = [
            reply if isinstance(reply, str) else json.dumps(reply) for reply in replies
        ]
        self.calls: list[tuple[str, str, bool]] = []

    def complete(self, system: str, user: str, json_object: bool = False) -> str:
        self.calls.append((system, user, json_object))
        if not self.replies:
            raise AssertionError(f"the model was called more times than scripted: {user!r}")
        return self.replies.pop(0)


def wrote(sql: str) -> dict[str, str]:
    """A generation reply carrying a statement."""
    return {"sql": sql}


@pytest.fixture(scope="module")
def gate(warehouse, semantic):
    """One Gate over the built Warehouse and the corpus the other fixtures read."""
    return ValidationGate(warehouse, semantic=semantic)


@pytest.fixture
def orchestrator(warehouse, gate, retriever):
    """An Orchestrator whose model each test scripts for itself."""

    def built(*replies: object) -> Orchestrator:
        return Orchestrator(
            warehouse, model=ScriptedModel(*replies), retriever=retriever, gate=gate
        )

    return built


# -- the grounding claim ---------------------------------------------------------


def test_the_identity_is_grounded_whatever_the_question_asked(orchestrator, semantic):
    """The access axis and every Join Path that reaches it are shown for every question.

    A model that was not shown the route cannot write a scoped statement, and the Gate
    refuses an unscoped one — so this is what keeps the identity from being a rule that
    refuses every question.
    """
    entries = orchestrator().grounded_entries(UNAMBIGUOUS)
    names = [entry.name for entry in entries]
    assert ACCESS_AXIS in names
    for route in semantic.dimensions[ACCESS_AXIS].routes.values():
        for join_path in route:
            assert join_path in names


def test_a_metric_that_was_not_retrieved_publishes_no_expression(
    orchestrator, semantic
):
    """*"Metrics not retrieved are not available"* — the flow's own words.

    A name can still reach the prompt through another entry's prose: `by trade date`
    describes itself as the axis `Traded Notional` is sliced on. What must not reach it
    is the **expression**, because that is the only thing a statement can be composed
    out of.
    """
    entries = orchestrator().grounded_entries("what was our gross revenue")
    retrieved = {entry.name for entry in entries}
    said = generation_instruction(entries, ANALYST)
    absent = [name for name in semantic.metrics if name not in retrieved]
    assert absent, "this question retrieved every metric, so it proves nothing"
    for name in absent:
        assert semantic.metrics[name].expression not in said


def test_the_prompt_names_no_table_the_entries_do_not(orchestrator):
    """The corpus is the Semantic Layer, so the schema reaches the model only as the
    tables the certified expressions and join conditions are written with.

    `published` is read off the whitelisted fields themselves rather than off a
    rendering of them, so a table that arrived in the prompt any other way — a rule that
    named one, a schema dump, a field `GROUNDED_FIELDS` does not list — has nothing to
    match against.
    """
    entries = orchestrator().grounded_entries(UNAMBIGUOUS)
    published = set(
        TABLE.findall(
            " ".join(
                str(getattr(entry, name))
                for entry in entries
                for name in GROUNDED_FIELDS[type(entry)]
            )
        )
    )
    assert set(TABLE.findall(generation_instruction(entries, ANALYST))) <= published


def test_the_rules_name_no_table_of_their_own(orchestrator):
    """Veritas's own instructions are about the corpus, never about the Warehouse.

    Every `PromptForm`, and what is said about the question besides them, because an
    instruction that named a table would ground the model in something the entries
    cannot check — whichever arm of the sweep was running when it did.
    """
    for said in [*PROMPT_FORMS.values(), REWRITTEN_QUESTION]:
        assert not TABLE.findall(said)


def test_the_two_prompt_forms_say_the_same_thing_at_two_lengths(orchestrator):
    """One instruction, two arms: both ask for one JSON object, both give the statement's
    shape, and one is markedly shorter than the other — which is the only difference the
    sweep in `veritas/evaluation/generation.py` is measuring."""
    rules, shape = PROMPT_FORMS[PromptForm.RULES], PROMPT_FORMS[PromptForm.SHAPE]
    for said in (rules, shape):
        assert '{"sql": null, "why"' in said
        assert "<metric expression> AS answer" in said
    assert len(shape.splitlines()) * 2 < len(rules.splitlines())


def test_the_question_the_generator_is_handed_is_described_to_it(orchestrator, semantic):
    """The rewrite step splices certified names over the words a person typed, so the
    generator is never handed the question as it was asked.

    Every form carries that, because it describes the input rather than the instruction —
    an arm that varied both would be measuring two changes at once.
    """
    entries = orchestrator().grounded_entries(UNAMBIGUOUS)
    for form in PromptForm:
        assert REWRITTEN_QUESTION in generation_instruction(entries, ANALYST, form)


def test_an_ambiguous_term_grounds_nothing(semantic):
    """The rewrite step settled which meaning; showing the others re-opens it."""
    assert GROUNDED_FIELDS[type(semantic.ambiguous_terms["revenue"])] == ()
    assert entry_text(semantic.ambiguous_terms["revenue"]) == ""


def test_the_grounded_axis_is_required_for_a_prompt_to_be_written(semantic):
    """No access axis, no way to say who is asking — so it raises rather than writing a
    prompt for a statement the Gate would refuse every time."""
    with pytest.raises(ValueError, match=ACCESS_AXIS):
        generation_instruction([semantic.metrics["Trade Count"]], ANALYST)


# -- the flow claim --------------------------------------------------------------


def test_a_question_the_corpus_covers_returns_a_number_and_its_lineage(orchestrator):
    """The whole flow, end to end: generated, judged, executed, answered."""
    answer = orchestrator(wrote(CERTIFIED)).answer(UNAMBIGUOUS)
    assert answer.answered, answer.refusal
    assert answer.sql == CERTIFIED
    assert answer.outcome is not None and answer.outcome.allowed
    [(trades,)] = answer.rows
    assert trades > 0
    assert answer.lineage.versions()["Trade Count"] == 1
    print(f"\n  {UNAMBIGUOUS!r} -> {trades}\n  lineage: {answer.lineage}")


def test_an_answered_breakdown_carries_the_names_its_values_came_back_under(
    orchestrator, semantic
):
    """[DEBT-031](../.claude/docs/debt-ledger.md#debt-031--a-grounded-answer-carries-rows-with-no-column-names)
    paid: the labels come off the engine, beside the rows they label.

    A breakdown is a tuple of an axis value and a number, and which position is which
    was knowledge in a prompt. It is now a field, read from the cursor the rows came
    from, so a reader of a Grounded Answer never has to know what the model was asked
    to alias.
    """
    answer = orchestrator(wrote(BREAKDOWN)).answer(
        "how many trades did we make by instrument type"
    )
    assert answer.answered, answer.refusal
    assert answer.columns == ("slice", "answer")
    assert all(len(row) == len(answer.columns) for row in answer.rows)
    buckets = {row[0] for row in answer.rows}
    assert buckets and buckets <= set(
        semantic.dimensions["by instrument type"].allowed_values
    )
    print(f"\n  {dict(answer.rows)}")


def test_an_unresolved_ambiguous_term_asks_back_and_generates_nothing(orchestrator):
    """The first way out. `revenue` is two Certified Metrics, and Veritas asks which."""
    orchestra = orchestrator({"revenue": None})
    answer = orchestra.answer("what was our revenue last quarter")
    assert not answer.answered
    assert answer.clarifying_question is not None
    assert "Gross Revenue" in answer.clarifying_question
    assert answer.sql == ""
    assert len(orchestra.model.calls) == 1, "the generation step ran on an open question"


def test_a_resolved_ambiguous_term_reaches_lineage(orchestrator):
    """The word the person typed is part of what produced the answer, so it is recorded.

    It grounds nothing, and it is still what turned `revenue` into the metric that was
    computed — which is what makes an answer auditable rather than merely reproducible.
    """
    answer = orchestrator(
        {"revenue": "Net Revenue"},
        wrote(CERTIFIED),
    ).answer("what was our net revenue")
    assert answer.answered, answer.refusal
    assert "Net Revenue" in answer.rewritten
    assert next(iter(answer.lineage.versions())) == "revenue"


def test_a_model_that_refuses_is_a_refusal_and_not_a_crash(orchestrator):
    """The second way out, and the Non-goal it serves: no Certified Metric, no answer."""
    answer = orchestrator({"sql": None, "why": "no metric here counts instruments"}).answer(
        UNCOVERED
    )
    assert not answer.answered
    assert answer.refusal == "no metric here counts instruments"
    assert answer.sql == ""
    assert answer.outcome is None


def test_a_model_that_refuses_without_saying_why_still_refuses(orchestrator):
    """A refusal with no reason is given the only honest one there is."""
    answer = orchestrator({"sql": None}).answer(UNCOVERED)
    assert not answer.answered
    assert "no statement" in answer.refusal


def test_a_shadow_metric_is_refused_by_the_gate_and_the_answer_says_so(orchestrator):
    """The third way out — and the whole reason the Gate is code rather than a prompt.

    The statement is scoped, routed and read-only; the arithmetic is the model's own.
    The Grounded Answer carries the statement that was refused, so a reader can see what
    Veritas would have run.
    """
    answer = orchestrator(wrote(SHADOW)).answer(UNAMBIGUOUS)
    assert not answer.answered
    assert answer.sql == SHADOW
    assert answer.outcome is not None and not answer.outcome.allowed
    assert answer.outcome.reasons == (RejectionReason.SHADOW_METRIC,)
    assert answer.refusal == answer.outcome.explanation
    assert answer.rows == ()


def test_an_unscoped_statement_never_reaches_the_warehouse(orchestrator, warehouse):
    """The access predicate, enforced where the flow puts it: before execution."""
    unscoped = CERTIFIED.split(" WHERE ")[0]
    answer = orchestrator(wrote(unscoped)).answer(UNAMBIGUOUS)
    assert not answer.answered
    assert answer.outcome is not None
    assert answer.outcome.reasons == (RejectionReason.MISSING_ACCESS_PREDICATE,)
    assert answer.rows == ()


def test_a_question_no_metric_is_retrieved_for_costs_no_model_call(
    warehouse, gate, retriever, semantic
):
    """The fourth way out, and the one the Orchestrator reaches on its own.

    Retrieval over this corpus almost always surfaces a metric, so this drives an
    Orchestrator whose retriever finds none — the branch is the guard, not the
    likelihood.
    """

    class NoMetrics:
        def retrieve(self, question, strategy, top_k):
            return [semantic.join_paths["trade_to_account"]]

    orchestra = Orchestrator(
        warehouse, model=ScriptedModel(), retriever=NoMetrics(), gate=gate
    )
    answer = orchestra.answer(UNAMBIGUOUS)
    assert not answer.answered
    assert "Certified Metric" in answer.refusal
    assert orchestra.model.calls == []


# -- the contract claim ----------------------------------------------------------


def test_an_answer_cannot_both_refuse_and_ask_back():
    """A question gets one of the two."""
    with pytest.raises(ValueError, match="asks back"):
        GroundedAnswer("q", refusal="no", clarifying_question="which?")


def test_an_answered_question_carries_the_statement_that_answered_it():
    """*"Veritas never returns a bare number"*, as a construction error."""
    with pytest.raises(ValueError, match="bare number"):
        GroundedAnswer("q", rows=((1,),))


def test_an_answered_question_carries_the_verdict_it_ran_under():
    """A number with no allowing verdict behind it is a number past the Gate."""
    with pytest.raises(ValueError, match="Validation Gate outcome"):
        GroundedAnswer("q", sql=CERTIFIED, rows=((1,),))


def test_lineage_reads_as_a_line_a_person_can_check(semantic):
    """What the App shows and what Observability logs: name, kind and version."""
    lineage = Lineage((semantic.metrics["Gross Revenue"],))
    assert str(lineage) == "Gross Revenue (metric v1)"
    assert Lineage().versions() == {} and str(Lineage()) == "nothing"


# -- the live path ---------------------------------------------------------------


@pytest.mark.skipif(
    not os.environ.get(LIVE_VARIABLE),
    reason=f"spends a real key: set {LIVE_VARIABLE}=1 to run it",
)
def test_the_configured_model_answers_what_the_corpus_covers(warehouse, gate, retriever):
    """Every statement a real model writes for these questions passes the Gate.

    The claim the plan's verification line makes, against whichever of the two providers
    the environment names. A model that ignores the rules writes a statement the Gate
    refuses, and this is what says so rather than a stub agreeing with itself.
    """
    orchestra = Orchestrator(warehouse, retriever=retriever, gate=gate)
    for question in COVERED:
        answer = orchestra.answer(question)
        assert answer.answered, f"{question!r}: {answer.refusal}\n{answer.sql}"
        assert answer.rows
        print(f"\n  {question!r}\n    {answer.sql}\n    -> {answer.rows}")


@pytest.mark.skipif(
    not os.environ.get(LIVE_VARIABLE),
    reason=f"spends a real key: set {LIVE_VARIABLE}=1 to run it",
)
def test_the_configured_model_refuses_what_the_corpus_does_not_cover(
    warehouse, gate, retriever
):
    """*"Refusing is a feature; a helpful guess is the exact failure being prevented."*

    Either refusal is a pass, and which one fired is printed rather than asserted: the
    model declining is Veritas working, and the model writing something the Validation
    Gate refuses is Veritas working too. Requiring a particular one would be asserting
    which of two correct behaviours a provider happens to have.
    """
    answer = Orchestrator(warehouse, retriever=retriever, gate=gate).answer(UNCOVERED)
    assert not answer.answered
    refused_by = "the Validation Gate" if answer.outcome else "the model"
    print(f"\n  {UNCOVERED!r}\n    refused by {refused_by}: {answer.refusal}")


def test_the_covered_questions_retrieve_a_metric_on_every_fact_table(
    orchestrator, semantic
):
    """The live set is not five questions about `fct_trade` wearing different words.

    Checked without a model, because it is a claim about what these questions retrieve:
    between them they ground a Certified Metric rooted at each of the four fact tables
    the nine metrics start from, so a run that passes has exercised four routes and four
    date columns rather than one.
    """
    reached = {
        entry.from_table
        for question in COVERED
        for entry in orchestrator().grounded_entries(question)
        if isinstance(entry, MetricDefinition)
    }
    assert reached == {metric.from_table for metric in semantic.metrics.values()}
