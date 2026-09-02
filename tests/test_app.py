"""What the App shows a person, and what it refuses to hide from them.

Two claims. The **rendering claim**: a Grounded Answer becomes strings a person reads —
values under the names the engine gave them, a verdict that says which rules ran, and
an identity that carries what its enforcement is worth. The **page claim**: every one
of the four things a question can come back as reaches the page as itself, and none of
them arrives without the statement, the Lineage and the Validation Gate outcome beside
it — [`App`](../.claude/docs/glossary.md#a-the-system)'s *"never renders a bare
number"*, as a test rather than as an intention.

The page is driven through Streamlit's own `AppTest`, which runs the script and reports
the elements it produced. Every run here answers with a prepared Grounded Answer, so
the suite needs no key and no network; the one test that asks a real provider through
the real flow runs only when `VERITAS_LIVE_MODEL` says so.
"""

import os
import re
from decimal import Decimal

import pytest
from streamlit.testing.v1 import AppTest

from veritas.app import (
    ENFORCEMENT_NOTE,
    NOTHING,
    formatted,
    identity_lines,
    labels,
    lineage_lines,
    outcome_line,
    single_value,
    table,
)
from veritas.llm import LIVE_VARIABLE, LanguageModelError
from veritas.orchestrator import GroundedAnswer, Lineage, Orchestrator
from veritas.validation import (
    ANALYST,
    RejectionReason,
    ValidationGate,
    ValidationGateOutcome,
)

# A question the corpus covers, and the shape a breakdown of it comes back in: the
# generation rules alias the axis `slice` and the metric `answer`, and the engine hands
# both names back with the rows.
QUESTION = "how many trades did we make by instrument type"
STATEMENT = (
    "SELECT dim_instrument.instrument_type AS slice, count(fct_trade.trade_id) AS answer "
    "FROM fct_trade "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "JOIN dim_instrument ON dim_instrument.instrument_id = fct_trade.instrument_id "
    "WHERE dim_client.client_region = 'EU' "
    "GROUP BY dim_instrument.instrument_type"
)


@pytest.fixture(scope="module")
def gate(warehouse, semantic):
    """One Gate over the built Warehouse and the corpus, for the rule names a verdict
    carries."""
    return ValidationGate(warehouse, semantic=semantic)


@pytest.fixture(scope="module")
def allowed(gate):
    """An allowing verdict naming the rules the Gate actually runs."""
    return ValidationGateOutcome(
        allowed=True, rules=tuple(name for name, _ in gate.rules(ANALYST))
    )


@pytest.fixture(scope="module")
def rejected(gate):
    """A refusing verdict, from the Gate's own taxonomy."""
    return ValidationGateOutcome(
        allowed=False,
        explanation="count(fct_trade.trade_id) * 2 traces to no Certified Metric",
        reasons=(RejectionReason.SHADOW_METRIC,),
        rules=tuple(name for name, _ in gate.rules(ANALYST))[:5],
    )


@pytest.fixture(scope="module")
def lineage(semantic):
    """What a breakdown of `Trade Count` by instrument type is composed from."""
    return Lineage((
        semantic.metrics["Trade Count"],
        semantic.dimensions["by instrument type"],
        semantic.join_paths["trade_to_instrument"],
    ))


@pytest.fixture
def answered(allowed, lineage):
    """A breakdown, answered: four buckets under the two names the engine returned.

    The counts are the fixture's own. What is under test is that a value is shown
    under the right label, which is a claim about the labelling and not about the data.
    """
    return GroundedAnswer(
        question=QUESTION,
        rewritten=QUESTION,
        sql=STATEMENT,
        columns=("slice", "answer"),
        rows=(("equity", 412), ("ETF", 170), ("future", 61), ("currency pair", 9)),
        lineage=lineage,
        outcome=allowed,
    )


def driven(given=None):
    """The App's page, answering with `given`.

    Streamlit's `AppTest` runs the source of this function as the script, so it imports
    what it needs itself and takes everything else as an argument: a prepared Grounded
    Answer, an exception to raise instead, or a real Orchestrator to ask.
    """
    from veritas.app.page import page
    from veritas.orchestrator import Orchestrator

    class Asked:
        """One prepared reply, behind the seam `page` asks a question through."""

        def answer(self, question, access_profile):
            if isinstance(given, Exception):
                raise given
            return given

    page(orchestrator=given if isinstance(given, Orchestrator) else Asked())


def asked(given=None, question=QUESTION, timeout=30):
    """Load the page, type `question`, press Ask, and return what it rendered."""
    page = AppTest.from_function(driven, kwargs={"given": given}, default_timeout=timeout)
    page.run()
    if question:
        page.text_input[0].set_value(question)
        page.button[0].click().run()
    return page


def shown(page):
    """Everything the page wrote, as one string to look for words in."""
    return "\n".join(
        element.value
        for kind in (page.markdown, page.caption, page.code, page.error,
                     page.warning, page.info, page.success, page.subheader)
        for element in kind
        if isinstance(element.value, str)
    )


# -- the rendering claim ---------------------------------------------------------


def test_the_enforcement_note_is_the_ledgers_own_sentence(root):
    """[DEBT-008](../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
    asks the App to *"say precisely what is true"*, and names the words.

    The entry's own sentence rather than a paraphrase of it, which is checked here
    because a paraphrase drifts in exactly the direction the entry exists to prevent.
    """
    entry = (root / ".claude" / "docs" / "debt-ledger.md").read_text()
    # The entry states it as a block quote, so the markers come off before the words
    # are compared; nothing else about the sentence may differ.
    quoted = " ".join(re.sub(r"^\s*>\s?", "", entry, flags=re.M).split())
    assert " ".join(ENFORCEMENT_NOTE.split()) in quoted


def test_a_value_is_shown_the_way_a_person_reads_it():
    """Separators on a figure, two places on money, a dash where there is nothing."""
    assert formatted(Decimal("46282.794")) == "46,282.79"
    assert formatted(412) == "412" and formatted(1234567) == "1,234,567"
    assert formatted(None) == NOTHING
    assert formatted("equity") == "equity"


def test_a_row_is_labelled_by_the_columns_it_came_back_under(answered):
    """[DEBT-031](../.claude/docs/debt-ledger.md#debt-031--a-grounded-answer-carries-rows-with-no-column-names)
    paid, at the end that reads it: the axis and the metric are told apart by the names
    the engine returned, and not by knowing what the prompt asked the model to alias."""
    assert table(answered) == {
        "slice": ["equity", "ETF", "future", "currency pair"],
        "answer": ["412", "170", "61", "9"],
    }


def test_two_columns_of_one_name_are_told_apart():
    """A statement may name two output columns the same thing, and neither may be
    dropped for it."""
    twice = GroundedAnswer(question="q", sql=STATEMENT, columns=("answer", "answer"),
                           rows=((1, 2),),
                           outcome=ValidationGateOutcome(allowed=True))
    assert labels(twice) == ["answer (0)", "answer (1)"]
    assert list(table(twice)) == ["answer (0)", "answer (1)"]


def test_only_a_one_number_answer_is_shown_as_one(answered, allowed):
    """A breakdown is a table, and an empty result is neither."""
    assert single_value(answered) is None
    one = GroundedAnswer(question="q", sql=STATEMENT, columns=("answer",),
                         rows=((Decimal("67935.82"),),), outcome=allowed)
    assert single_value(one) == ("answer", "67,935.82")
    empty = GroundedAnswer(question="q", sql=STATEMENT, columns=("answer",),
                           outcome=allowed)
    assert single_value(empty) is None


def test_the_verdict_says_what_ran_or_what_fired(allowed, rejected):
    """An allowed statement names the rules that ran — the Gate stops at the first
    rejection, so a verdict is only as wide as the rules it got through — and a
    refused one names the Rejection Reasons Observability charts."""
    assert outcome_line(allowed).startswith("allowed")
    assert "the access predicate" in outcome_line(allowed)
    assert outcome_line(rejected) == f"rejected — {RejectionReason.SHADOW_METRIC}"
    assert outcome_line(None) == "no statement reached the Validation Gate"


def test_the_identity_says_who_is_asking_and_what_they_may_not_see():
    """Role, region and Restricted Columns, which is the whole of an Access Profile."""
    assert identity_lines(ANALYST) == [
        "role — analyst",
        "region — EU",
        "restricted — dim_client.client_name",
    ]


def test_the_lineage_reads_as_name_kind_and_version(answered):
    """What makes an answer auditable, one entry per line."""
    assert lineage_lines(answered) == [
        "Trade Count — metric v1",
        "by instrument type — dimension_definition v1",
        "trade_to_instrument — join_path v1",
    ]


# -- the page claim --------------------------------------------------------------


def test_the_page_loads_before_a_question_is_asked():
    """A question box, the identity it will be asked as, and what that enforcement is
    worth — with no model, no Warehouse and no question."""
    page = asked(question="")
    assert page.title[0].value == "Veritas"
    assert page.text_input[0].label and page.button[0].label == "Ask"
    assert "role — analyst" in shown(page) and ENFORCEMENT_NOTE in shown(page)
    assert not page.error and not page.exception


def test_an_answer_is_never_a_bare_number(answered):
    """The registered constraint on the App, as the four things that arrive together.

    The number, the statement it was computed with, the entries it was composed from
    and the verdict it ran under are all on the page — none of them behind a control a
    reader has to know to open.
    """
    page = asked(answered)
    assert not page.exception
    assert page.dataframe[0].value["answer"].tolist() == ["412", "170", "61", "9"]
    assert page.code[0].value == STATEMENT
    assert "Trade Count — metric v1" in shown(page)
    assert page.success[0].value.startswith("allowed")


def test_a_breakdown_is_shown_under_the_names_it_came_back_under(answered):
    """The axis and the metric are two labelled columns, not two positions in a tuple."""
    page = asked(answered)
    assert list(page.dataframe[0].value.columns) == ["slice", "answer"]
    assert page.dataframe[0].value["slice"].tolist()[0] == "equity"


def test_a_refusal_is_an_answer_and_says_which_rule_refused(rejected, lineage):
    """A rejected statement is shown, with the reason and the verdict — the App reports
    the Validation Gate rather than reporting that nothing happened."""
    page = asked(GroundedAnswer(
        question=QUESTION,
        sql=STATEMENT,
        lineage=lineage,
        outcome=rejected,
        refusal=rejected.explanation,
    ))
    assert not page.exception and not page.metric and not page.dataframe
    assert rejected.explanation in [error.value for error in page.error]
    assert f"rejected — {RejectionReason.SHADOW_METRIC}" in shown(page)
    assert page.code[0].value == STATEMENT


def test_a_question_asked_back_is_shown_as_a_question(semantic):
    """An Ambiguous Term the question did not settle comes back as a question, and
    nothing about it looks like an answer."""
    page = asked(GroundedAnswer(
        question="what was our revenue",
        clarifying_question="Do you mean Gross Revenue or Net Revenue?",
    ), question="what was our revenue")
    assert page.warning[0].value == "Do you mean Gross Revenue or Net Revenue?"
    assert not page.metric and not page.dataframe and not page.code
    assert "no statement reached the Validation Gate" in shown(page)


def test_a_provider_that_cannot_be_reached_is_not_a_traceback():
    """*"This question cannot be answered"* and *"this installation cannot reach a
    model"* are different sentences, and the second one is the App's to say."""
    page = asked(LanguageModelError("no key for openai: put OPENAI_API_KEY in .env"))
    assert not page.exception
    assert "could not reach a model" in page.error[0].value
    assert "OPENAI_API_KEY" in page.error[0].value


def test_only_the_page_imports_streamlit(root):
    """The widget layer is one file, so everything the App decides is testable without
    one."""
    importing = {
        str(path.relative_to(root))
        for path in sorted((root / "veritas").rglob("*.py"))
        if "__pycache__" not in path.parts
        and re.search(r"^import streamlit|^from streamlit", path.read_text(), re.M)
    }
    assert importing == {"veritas/app/page.py"}


# -- the live path ---------------------------------------------------------------


@pytest.mark.skipif(
    not os.environ.get(LIVE_VARIABLE),
    reason=f"spends a real key: set {LIVE_VARIABLE}=1 to run it",
)
def test_the_page_answers_a_real_question_end_to_end(warehouse, gate, retriever):
    """The whole of Veritas behind the box a person types into.

    Nothing is scripted: the configured provider resolves the question, writes the
    statement, the Gate judges it and the Warehouse runs it — and what the page shows
    is a number under its own column name, the statement, the Lineage and the verdict.
    """
    page = asked(
        Orchestrator(warehouse, retriever=retriever, gate=gate),
        question="what was our gross revenue",
        timeout=120,
    )
    assert not page.exception and not page.error, shown(page)
    assert page.metric or page.dataframe
    assert page.code[0].value and page.success[0].value.startswith("allowed")
    print(f"\n  {page.metric[0].label if page.metric else ''} "
          f"{page.metric[0].value if page.metric else ''}\n  {page.code[0].value}")
