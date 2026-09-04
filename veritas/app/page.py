"""The App — one page where a question becomes a Grounded Answer, with nothing hidden.

    uv run streamlit run veritas/app/page.py

[`App`](../../.claude/docs/glossary.md#a-the-system) is registered as *"where a person
asks a question and reads a Grounded Answer — with its SQL, its Lineage and its
Validation Gate outcome. **Never renders a bare number**"*, and `show` below is that
sentence: the statement, the entries it was composed from and the verdict it ran under
are laid out beneath every answer rather than folded away behind a control.

`page` takes the Orchestrator it asks and the Question Log it records to rather than
reaching for either, so the same page a person loads is the page a test drives with a
scripted model and a doubled log. Called with nothing it builds both real ones, once per
server process.

**The App is the one caller that records.** The Orchestrator measures a question and
returns what it took; writing that down is this side of the seam, so the Evaluation
sweep drives the same flow a few hundred times and puts nothing on the dashboard —
Observability is live traffic, and a sweep is not traffic. It is also the one caller
that takes Feedback, for the same reason: nothing but a person reading an answer has
any to give.
"""

import sys
from pathlib import Path
from typing import NamedTuple

# `streamlit run` puts this file's own directory on the path and not the repository
# root, so the import below would fail from a fresh checkout without this. The same
# insert `tests/conftest.py` makes, for the same reason.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

from veritas.app.render import (
    ENFORCEMENT_NOTE,
    identity_lines,
    lineage_lines,
    model_line,
    outcome_line,
    recording_line,
    single_value,
    table,
    unit_line,
)
from veritas.llm import LanguageModelError
from veritas.observability import (
    Feedback,
    QuestionLog,
    QuestionLogError,
    question_log,
)
from veritas.orchestrator import GroundedAnswer, Orchestrator
from veritas.validation import ANALYST, AccessProfile
from veritas.warehouse import WarehouseAdapter

TITLE = "Veritas"
CAPTION = (
    "Ask a question about the brokerage. Every answer carries the SQL it was computed "
    "with, the certified entries it was composed from, and the Validation Gate's "
    "verdict on it — and a question Veritas cannot answer from those is refused rather "
    "than guessed at."
)
PROMPT = "Your question"
PLACEHOLDER = "what was our net revenue last quarter?"

# What the Feedback widget asks, and the three things it can say back.
FEEDBACK_PROMPT = "Was this answer useful?"
NOTE_PROMPT = "Anything to add? (optional)"
SEND = "Send"
THANKS = "Thank you — recorded against this answer."
NO_VERDICT = "Feedback is a verdict: choose 👍 or 👎."

# Where the answer on the page is kept. A page that held it in nothing but the run that
# produced it would lose it the moment a Feedback button reran the script, which is the
# one thing Feedback may not cost.
SHOWN = "shown"


class Shown(NamedTuple):
    """The Grounded Answer `show` is showing, and the Question Log row it was recorded
    as — or `None` where it was not recorded, which is where no Feedback can be left on
    it.

    Not `answered`, which a Grounded Answer already uses for the narrower thing: a
    refusal is shown and is not answered.
    """

    answer: GroundedAnswer
    question_id: int | None


@st.cache_resource(show_spinner="Opening the Warehouse and indexing the Semantic Layer…")
def built() -> Orchestrator:
    """The Orchestrator this server answers with, built on the first question asked.

    Cached as a resource because it holds the Warehouse connection and the Retriever's
    fitted indexes, and a page that rebuilt those per question would pay the index on
    every keystroke.
    """
    return Orchestrator(WarehouseAdapter())


@st.cache_resource(show_spinner="Opening the Question Log…")
def recording() -> tuple[QuestionLog | None, str]:
    """The Question Log this server records to, and where it is — or nothing, and why.

    Cached for the same reason the Orchestrator is: it holds a connection. An
    installation with no server reaches this once and says so on every page load
    afterwards, rather than retrying a connection per question in front of a person.
    """
    try:
        log = question_log()
    except QuestionLogError as unreachable:
        return None, str(unreachable)
    return log, str(log)


def show(answer: GroundedAnswer) -> None:
    """One Grounded Answer, whichever of the four it is, and the record behind it.

    A question asked back is a warning, a refusal is an error, a number is a number under
    the unit its Certified Metric is quoted in, and a breakdown is a table. What follows
    is the same in all four cases: the statement if
    one was written, the Lineage if anything grounded it, and the Validation Gate's
    verdict — including when the verdict is that nothing reached it. The statement wraps
    rather than scrolling, because a reader who has to scroll a box sideways to see the
    end of a `WHERE` clause is a reader who will not check it.
    """
    if answer.clarifying_question is not None:
        st.warning(answer.clarifying_question)
    elif answer.refusal:
        st.error(answer.refusal)
    elif not answer.rows:
        st.info("the statement ran and matched no rows")
    elif single := single_value(answer):
        st.metric(*single)
        if unit := unit_line(answer):
            st.caption(unit)
    else:
        st.dataframe(table(answer), width="stretch", hide_index=True)

    if answer.rewritten and answer.rewritten != answer.question:
        st.caption(f"read as: {answer.rewritten}")

    if answer.sql:
        st.subheader("SQL")
        st.code(answer.sql, language="sql", wrap_lines=True)

    st.subheader("Lineage")
    st.markdown(
        "\n".join(f"- {line}" for line in lineage_lines(answer))
        or "- nothing was retrieved for this question"
    )

    st.subheader("Validation Gate")
    allowed = answer.outcome is not None and answer.outcome.allowed
    (st.success if allowed else st.error)(outcome_line(answer.outcome))


def page(
    orchestrator: Orchestrator | None = None,
    access_profile: AccessProfile = ANALYST,
    log: QuestionLog | None = None,
) -> None:
    """The whole page: who is asking, the question box, the answer to the last question
    asked, the row that answer was recorded as, and the Feedback offered on it.

    `log` is taken the way `orchestrator` is, so a test drives the page against a double
    and the server the page opens for itself is the one a person gets.

    The answer is held in session state rather than in the run that produced it. A
    Feedback button reruns the script with nothing submitted in the question form, and an
    answer that lived only in that first run would leave the page as the verdict on it
    arrived.
    """
    st.set_page_config(page_title=TITLE, page_icon="⚖️")
    st.title(TITLE)
    st.caption(CAPTION)

    recorder, where = (log, str(log)) if log is not None else recording()

    with st.sidebar:
        st.subheader("Asked as")
        st.markdown("\n".join(f"- {line}" for line in identity_lines(access_profile)))
        st.caption(ENFORCEMENT_NOTE)
        st.subheader("Model")
        st.caption(model_line())
        st.subheader("Question Log")
        st.caption(recording_line(where, recorder is not None))

    with st.form("question"):
        question = st.text_input(PROMPT, placeholder=PLACEHOLDER)
        asked = st.form_submit_button("Ask")

    fresh = None
    if asked and question.strip():
        try:
            fresh = (built() if orchestrator is None else orchestrator).answer(
                question.strip(), access_profile
            )
        except LanguageModelError as unreachable:
            st.session_state.pop(SHOWN, None)
            st.error(
                f"This question was not asked, because Veritas could not reach a "
                f"model: {unreachable}"
            )
            return
        st.session_state[SHOWN] = Shown(fresh, None)

    showing = st.session_state.get(SHOWN)
    if showing is None:
        return
    show(showing.answer)
    if fresh is not None:
        showing = Shown(fresh, record(fresh, access_profile, recorder))
        st.session_state[SHOWN] = showing
    offer_feedback(showing.question_id, recorder)


def record(
    answer: GroundedAnswer,
    access_profile: AccessProfile,
    log: QuestionLog | None,
) -> int | None:
    """Put the question that was just answered in the Question Log, and return its row.

    **After the answer is on the page, and never instead of it.** A person asked a
    question; whether Veritas managed to write it down is Veritas's problem, so a failed
    write is a warning beside an answer rather than an error in place of one, and an
    installation with no log at all says so in the sidebar and is otherwise silent.

    `None` for both of those, which is what leaves an answer with no Feedback offered on
    it: Feedback is left against a row, and there is no row.
    """
    if log is None:
        return None
    try:
        return log.record(answer, access_profile)
    except QuestionLogError as unrecorded:
        st.warning(f"This answer was not recorded: {unrecorded}")
        return None


def offer_feedback(question_id: int | None, log: QuestionLog | None) -> None:
    """Take the verdict and the sentence a person leaves on the answer above.

    One form, so a verdict and the sentence that qualifies it are one write rather than
    two — and so the widgets do not rerun the script between them. It is keyed by the
    row, which is what empties it when a new question is answered and what makes a
    second verdict on the same answer a replacement rather than a second answer's.

    Offered only where the answer reached the Question Log, because Feedback attaches to
    a row: an installation with no log says so in the sidebar and shows no widget that
    would throw a person's verdict away.
    """
    if question_id is None or log is None:
        return
    st.subheader("Feedback")
    with st.form(f"feedback-{question_id}"):
        st.caption(FEEDBACK_PROMPT)
        # 1 is the thumb up and 0 the thumb down, which is the order `st.feedback`
        # returns "thumbs" in.
        thumb = st.feedback("thumbs", key=f"thumbs-{question_id}")
        note = st.text_input(NOTE_PROMPT, key=f"note-{question_id}")
        left = st.form_submit_button(SEND)

    if not left:
        return
    if thumb is None:
        st.warning(NO_VERDICT)
        return
    try:
        log.leave_feedback(question_id, Feedback(up=bool(thumb), note=note.strip()))
    except QuestionLogError as unrecorded:
        st.warning(f"This feedback was not recorded: {unrecorded}")
        return
    st.success(THANKS)


if __name__ == "__main__":
    page()
