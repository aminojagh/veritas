"""What the App shows a person, and what it refuses to hide from them.

Three claims. The **rendering claim**: a Grounded Answer becomes strings a person reads —
values under the names the engine gave them, a single figure under the unit its
Certified Metric is quoted in, a verdict that says which rules ran, and an identity that
carries what its enforcement is worth. The **page claim**: every one
of the four things a question can come back as reaches the page as itself, and none of
them arrives without the statement, the Lineage and the Validation Gate outcome beside
it — [`App`](../.claude/docs/glossary.md#a-the-system)'s *"never renders a bare
number"*, as a test rather than as an intention. The **recording claim**: the question a
person just asked reaches the Question Log after it reaches the page, carrying the
identity it was asked as — and a log that will not take it costs a warning rather than
the answer. The **Feedback claim**: the verdict a person leaves is written against the
row that answer was recorded as, the answer stays on the page while they leave it, and
an answer that reached no row is offered no widget that would throw a verdict away.

The page is driven through Streamlit's own `AppTest`, which runs the script and reports
the elements it produced. Every run here answers with a prepared Grounded Answer, so
the suite needs no key and no network, and the log is a double for every one of them.
The two tests that ask a real provider through the real flow run only when
`VERITAS_LIVE_MODEL` says so, and the second of those also needs a Postgres server —
`docker compose up -d postgres`, which `tests/test_observability.py` describes the
lifecycle of — because recording live traffic is the one claim a double cannot make. It
skips when either the key or the server is absent. No other test in this file opens the
Question Log this installation is configured for; an autouse fixture makes sure of it.
"""

import os
import re
from dataclasses import replace
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
    recording_line,
    single_value,
    table,
    unit_line,
)
from veritas.app.page import NO_VERDICT, THANKS
from veritas.llm import LIVE_VARIABLE, LanguageModelError
from veritas.observability import Feedback, PostgresQuestionLog, QuestionLogError
from veritas.orchestrator import EndedBy, GroundedAnswer, Lineage, Orchestrator
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

# A one-number question, and the statement that answers it: `Gross Revenue`, which is
# money in a Reporting Currency where `Trade Count` is a bare count.
FIGURE_QUESTION = "what was our gross revenue"
FIGURE_STATEMENT = (
    "SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) AS answer "
    "FROM fct_trade "
    "JOIN fct_fx_rate ON fct_fx_rate.rate_date = fct_trade.trade_date "
    " AND fct_fx_rate.from_currency = fct_trade.denomination_currency "
    " AND fct_fx_rate.to_currency = 'EUR' "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "WHERE dim_client.client_region = 'EU'"
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
        ended_by=EndedBy.ANSWER,
        rewritten=QUESTION,
        sql=STATEMENT,
        columns=("slice", "answer"),
        rows=(("equity", 412), ("ETF", 170), ("future", 61), ("currency pair", 9)),
        lineage=lineage,
        outcome=allowed,
    )


@pytest.fixture
def figure(allowed, semantic):
    """One number, under a Lineage that says which metric it is.

    The engine calls the column `answer`, which is what the generation rules asked the
    model to alias it — so the Lineage is the only thing on the page that can say what
    the number is measured in.
    """
    return GroundedAnswer(
        question=FIGURE_QUESTION,
        ended_by=EndedBy.ANSWER,
        rewritten=FIGURE_QUESTION,
        sql=FIGURE_STATEMENT,
        columns=("answer",),
        rows=((Decimal("67935.82"),),),
        lineage=Lineage((
            semantic.metrics["Gross Revenue"],
            semantic.join_paths["trade_to_fx_rate_on_denomination_currency"],
            semantic.join_paths["trade_to_account"],
            semantic.join_paths["account_to_client"],
        )),
        outcome=allowed,
    )


class Recorded:
    """A Question Log that keeps what it was handed, or refuses to take it.

    The double the page is driven against, so what the App writes and when is provable
    without a server — and so that no test in this file can write into the Question Log
    a person's own `.env` names. The two refusals are separate because an answer that
    was never recorded is offered no Feedback at all: a log that takes questions and
    refuses verdicts is the only way to reach the second failure.
    """

    WHERE = "localhost:5432/veritas"

    def __init__(self, refusing: str = "", refusing_feedback: str = "") -> None:
        self.rows: list[tuple[GroundedAnswer, object]] = []
        self.feedback: list[tuple[int, Feedback]] = []
        self.refusing = refusing
        self.refusing_feedback = refusing_feedback

    def record(self, answer, access_profile):
        if self.refusing:
            raise QuestionLogError(self.refusing)
        self.rows.append((answer, access_profile))
        return len(self.rows)

    def leave_feedback(self, question_id, feedback):
        if self.refusing_feedback:
            raise QuestionLogError(self.refusing_feedback)
        self.feedback.append((question_id, feedback))

    def __str__(self) -> str:
        return self.WHERE


@pytest.fixture(autouse=True)
def no_real_question_log(monkeypatch):
    """Nothing here opens the Question Log this installation is configured for.

    A page given no log builds one from `.env`, which on a machine with the compose file
    up is a real server — and a test suite that wrote its questions into a person's own
    Question Log would corrupt the only traffic the dashboard has.
    """
    from veritas.app import page as page_module

    monkeypatch.setattr(page_module, "recording", lambda: (None, "no Question Log"))


def driven(given=None, log=None):
    """The App's page, answering with `given` and recording to `log`.

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

    page(
        orchestrator=given if isinstance(given, Orchestrator) else Asked(),
        log=log,
    )


def asked(given=None, question=QUESTION, timeout=30, log=None):
    """Load the page, type `question`, press Ask, and return what it rendered."""
    page = AppTest.from_function(
        driven, kwargs={"given": given, "log": log}, default_timeout=timeout
    )
    page.run()
    if question:
        page.text_input[0].set_value(question)
        page.button[0].click().run()
    return page


def left(page, up=True, note=""):
    """Choose a verdict on the answer showing, type the optional sentence, press Send.

    `up=None` presses Send with no verdict chosen, which is the one thing the form can
    be submitted with and not be Feedback.
    """
    if up is not None:
        page.feedback[0].set_value(1 if up else 0)
    if note:
        page.text_input[1].set_value(note)
    page.button[1].click().run()
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
    twice = GroundedAnswer(question="q", ended_by=EndedBy.ANSWER, sql=STATEMENT,
                           columns=("answer", "answer"), rows=((1, 2),),
                           outcome=ValidationGateOutcome(allowed=True))
    assert labels(twice) == ["answer (0)", "answer (1)"]
    assert list(table(twice)) == ["answer (0)", "answer (1)"]


def test_only_a_one_number_answer_is_shown_as_one(answered, allowed):
    """A breakdown is a table, and an empty result is neither."""
    assert single_value(answered) is None
    one = GroundedAnswer(question="q", ended_by=EndedBy.ANSWER, sql=STATEMENT,
                         columns=("answer",), rows=((Decimal("67935.82"),),),
                         outcome=allowed)
    assert single_value(one) == ("answer", "67,935.82")
    empty = GroundedAnswer(question="q", ended_by=EndedBy.ANSWER, sql=STATEMENT,
                           columns=("answer",), outcome=allowed)
    assert single_value(empty) is None


def test_a_single_figure_carries_the_unit_its_metric_is_quoted_in(
    figure, answered, semantic
):
    """The smaller thing
    [DEBT-034](../.claude/docs/debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)
    was blocking: the metric whose `unit` and `reporting_currency` label the figure is
    identifiable now that Lineage names what the statement used.

    A count has no Reporting Currency and says so by not naming one. A breakdown is a
    table under the names the engine returned, and gets no unit line.
    """
    assert unit_line(figure) == "Gross Revenue — money, in EUR"
    counted = replace(figure, lineage=Lineage((semantic.metrics["Trade Count"],)))
    assert unit_line(counted) == "Trade Count — count"
    assert unit_line(answered) == ""


def test_a_figure_no_lineage_identifies_carries_no_unit(figure, semantic):
    """A unit no entry pins down is a unit invented for the page.

    Two metrics in one Lineage is the state this replaced — every retrieved metric
    cited — and it is still what a two-metric statement produces.
    """
    two = replace(figure, lineage=Lineage((
        semantic.metrics["Gross Revenue"], semantic.metrics["Net Revenue"],
    )))
    assert unit_line(two) == ""
    assert unit_line(replace(figure, lineage=Lineage())) == ""


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


def test_a_one_number_answer_reaches_the_page_with_its_unit(figure):
    """The number, and what it is measured in, beside each other — where the engine's
    own label for it is `answer`."""
    page = asked(figure, question=FIGURE_QUESTION)
    assert not page.exception and not page.dataframe
    assert page.metric[0].value == "67,935.82"
    assert "Gross Revenue — money, in EUR" in shown(page)


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
        ended_by=EndedBy.GATE,
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
        ended_by=EndedBy.REWRITE,
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


# -- the recording claim ---------------------------------------------------------


def test_a_question_is_recorded_once_it_has_been_answered(answered):
    """The App is the one caller that writes to the Question Log, and it writes the
    answer a person was just shown — with the identity it was asked as, which the
    Grounded Answer does not carry."""
    log = Recorded()
    page = asked(answered, log=log)
    assert not page.exception
    assert [(one.question, profile.role) for one, profile in log.rows] == [
        (QUESTION, "analyst")
    ]
    assert log.rows[0][0] is answered


def test_a_refusal_is_recorded_as_readily_as_an_answer(rejected, lineage):
    """*"Every question a person asks"* — a refused one is traffic, and the ending is
    what makes it a bar on a chart rather than a gap in one."""
    log = Recorded()
    page = asked(
        GroundedAnswer(
            question=QUESTION,
            ended_by=EndedBy.GATE,
            sql=STATEMENT,
            lineage=lineage,
            outcome=rejected,
            refusal=rejected.explanation,
        ),
        log=log,
    )
    assert not page.exception and page.error
    [(one, _)] = log.rows
    assert one.ended_by is EndedBy.GATE


def test_a_question_that_was_never_asked_is_never_recorded():
    """A provider Veritas could not reach produced no Grounded Answer, so there is
    nothing to record and the page says so instead."""
    log = Recorded()
    page = asked(LanguageModelError("no key for openai"), log=log)
    assert "could not reach a model" in page.error[0].value
    assert log.rows == []


def test_a_log_that_will_not_take_the_row_does_not_take_the_answer_away(answered):
    """A person asked a question; whether Veritas managed to write it down is Veritas's
    problem. So a failed write is a warning beside the answer and never instead of it."""
    page = asked(answered, log=Recorded(refusing="the server went away"))
    assert not page.exception
    assert page.dataframe[0].value["answer"].tolist() == ["412", "170", "61", "9"]
    assert "was not recorded" in page.warning[0].value
    assert "the server went away" in page.warning[0].value


def test_the_page_says_whether_questions_are_being_recorded(answered):
    """Said on the page rather than left to be discovered: an installation with no
    Question Log answers exactly as well as one with it, and the only place the
    difference shows is a dashboard nobody is looking at yet."""
    assert recording_line(Recorded.WHERE, True) == f"recording to {Recorded.WHERE}"
    assert recording_line("no POSTGRES_PASSWORD", False) == (
        "not recording — no POSTGRES_PASSWORD"
    )
    assert f"recording to {Recorded.WHERE}" in shown(asked(answered, log=Recorded()))


def test_a_page_with_no_question_log_says_so_and_records_nothing(answered):
    """The installation the autouse fixture arranges: no server, and an App that
    answers anyway."""
    page = asked(answered)
    assert not page.exception and not page.warning
    assert "not recording — no Question Log" in shown(page)
    assert page.dataframe


# -- the Feedback claim ----------------------------------------------------------


def test_feedback_is_offered_on_every_answer_that_reached_the_log(answered, rejected,
                                                                 lineage):
    """*"Under every Grounded Answer"* — a refusal is an answer a person may have
    something to say about as readily as a number is."""
    for one in (
        answered,
        GroundedAnswer(question=QUESTION, ended_by=EndedBy.GATE, sql=STATEMENT,
                       lineage=lineage, outcome=rejected, refusal=rejected.explanation),
    ):
        page = asked(one, log=Recorded())
        assert page.feedback, shown(page)
        assert "Feedback" in shown(page)


def test_a_verdict_is_written_against_the_row_the_answer_was_recorded_as(answered):
    """The whole of Feedback in one write: which row, up or down, and the sentence."""
    log = Recorded()
    page = left(asked(answered, log=log), up=True, note="matches the finance pack")
    assert not page.exception
    assert log.feedback == [(1, Feedback(up=True, note="matches the finance pack"))]
    assert THANKS in shown(page)


def test_the_answer_is_still_on_the_page_after_a_verdict_is_left(answered):
    """A verdict reruns the script with nothing submitted in the question form, and an
    answer that lived only in the run that produced it would leave as the verdict
    arrived."""
    page = left(asked(answered, log=Recorded()), up=False)
    assert not page.exception
    assert page.dataframe[0].value["answer"].tolist() == ["412", "170", "61", "9"]
    assert page.code[0].value == STATEMENT


def test_a_second_verdict_on_one_answer_is_left_on_that_same_row(answered):
    """Which is what makes *"the latest verdict stands"* the log's decision to take,
    rather than two rows about one answer for it to choose between."""
    log = Recorded()
    page = left(asked(answered, log=log), up=False)
    left(page, up=True, note="I misread it")
    assert [question_id for question_id, _ in log.feedback] == [1, 1]
    assert log.feedback[-1][1] == Feedback(up=True, note="I misread it")


def test_a_new_answer_is_offered_a_verdict_of_its_own(answered, figure):
    """The form is keyed by the row, so a verdict left on one answer never carries onto
    the next — a stale thumb would be a verdict on an answer nobody gave it to."""
    log = Recorded()
    page = left(asked(answered, log=log), up=True, note="matches the finance pack")
    page.text_input[0].set_value(FIGURE_QUESTION)
    page.button[0].click().run()
    assert len(log.rows) == 2
    assert page.feedback[0].value is None and page.text_input[1].value == ""
    left(page, up=False)
    assert [question_id for question_id, _ in log.feedback] == [1, 2]


def test_a_sentence_with_no_verdict_is_not_feedback(answered):
    """Registered as *"a verdict, up or down, and optionally a sentence"*: the optional
    half cannot arrive on its own, and Send doing nothing silently would be worse."""
    log = Recorded()
    page = left(asked(answered, log=log), up=None, note="not sure about this")
    assert log.feedback == []
    assert NO_VERDICT in [warning.value for warning in page.warning]


def test_an_answer_that_reached_no_row_is_offered_no_verdict(answered):
    """Feedback attaches to a row. Where there is none — no Question Log, or a write
    that failed — there is nothing to attach it to, so nothing is offered rather than a
    widget that throws what a person says away."""
    assert not asked(answered).feedback
    page = asked(answered, log=Recorded(refusing="the server went away"))
    assert "was not recorded" in page.warning[0].value
    assert not page.feedback


def test_a_log_that_will_not_take_the_verdict_does_not_take_the_answer_away(answered):
    """The same bargain the answer's own row is written under, applied to the verdict on
    it: a failed write is a warning beside what is on the page."""
    page = left(asked(answered, log=Recorded(refusing_feedback="the server went away")))
    assert not page.exception
    assert page.dataframe[0].value["answer"].tolist() == ["412", "170", "61", "9"]
    assert "feedback was not recorded" in page.warning[0].value
    assert "the server went away" in page.warning[0].value


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


@pytest.mark.skipif(
    not os.environ.get(LIVE_VARIABLE),
    reason=f"spends a real key: set {LIVE_VARIABLE}=1 to run it",
)
def test_a_real_question_asked_on_the_page_becomes_a_row(warehouse, gate, retriever):
    """The one claim no double can make: live traffic reaches the Question Log.

    Both halves are real — the configured provider answers and Postgres takes the row —
    so this needs a key **and** a server and skips without either. Two questions, so two
    endings are recorded from one run: one answered, and one that says an Ambiguous Term
    and is asked back. A verdict is then left on the second of them through the widget a
    person clicks, so the Feedback claim is made once against the real schema rather
    than only against the double. It deletes the rows it wrote, because a test that
    leaves traffic behind is a test that changes what the dashboard says.
    """
    import psycopg

    try:
        opened = PostgresQuestionLog()
    except QuestionLogError as unreachable:
        pytest.skip(f"no Question Log to record to: {unreachable}")

    class Watched:
        """The real log, keeping the row identifiers it hands back."""

        def __init__(self, log):
            self.log = log
            self.rows: list[int] = []

        def record(self, answer, access_profile):
            self.rows.append(self.log.record(answer, access_profile))
            return self.rows[-1]

        def leave_feedback(self, question_id, feedback):
            self.log.leave_feedback(question_id, feedback)

        def __str__(self):
            return str(self.log)

    log = Watched(opened)
    with opened:
        for question in ("what was our gross revenue", "what was our revenue"):
            page = asked(
                Orchestrator(warehouse, retriever=retriever, gate=gate),
                question=question,
                timeout=120,
                log=log,
            )
            assert not page.exception, shown(page)
        assert f"recording to {opened}" in shown(page)
        assert len(log.rows) == 2, "one row per question asked, whatever it came back as"

        left(page, up=False, note="I meant gross revenue")

        with psycopg.connect(opened.conninfo) as reading:
            written = reading.execute(
                "SELECT question_id, ended_by, row_count, "
                "       round(seconds::numeric, 2), cost, "
                "       (SELECT count(*) FROM lineage_entry e "
                "         WHERE e.question_id = q.question_id), "
                "       (SELECT count(*) FROM model_call c "
                "         WHERE c.question_id = q.question_id), "
                "       (SELECT round(sum(c.seconds)::numeric, 2) FROM model_call c "
                "         WHERE c.question_id = q.question_id) "
                "FROM question q WHERE question_id = ANY(%s) ORDER BY question_id",
                (log.rows,),
            ).fetchall()
            print("\n  id  ended_by    rows  seconds  cost         lineage  calls  in calls")
            for row in written:
                print("  " + "  ".join(f"{value!s:<10}" for value in row))
            verdicts = reading.execute(
                "SELECT question_id, up, note FROM feedback "
                "WHERE question_id = ANY(%s)",
                (log.rows,),
            ).fetchall()
            print(f"\n  feedback: {verdicts}")
            reading.execute(
                "DELETE FROM question WHERE question_id = ANY(%s)", (log.rows,)
            )
            assert reading.execute(
                "SELECT count(*) FROM feedback WHERE question_id = ANY(%s)", (log.rows,)
            ).fetchone() == (0,), "a question taken back takes its Feedback with it"
    endings = [row[1] for row in written]
    assert endings == ["answer", "rewrite"], endings
    assert all(row[6] >= 1 for row in written), "every question here calls a model"
    assert verdicts == [(log.rows[1], False, "I meant gross revenue")], verdicts
