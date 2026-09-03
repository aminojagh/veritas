"""The App — one page where a question becomes a Grounded Answer, with nothing hidden.

    uv run streamlit run veritas/app/page.py

[`App`](../../.claude/docs/glossary.md#a-the-system) is registered as *"where a person
asks a question and reads a Grounded Answer — with its SQL, its Lineage and its
Validation Gate outcome. **Never renders a bare number**"*, and `show` below is that
sentence: the statement, the entries it was composed from and the verdict it ran under
are laid out beneath every answer rather than folded away behind a control.

`page` takes the Orchestrator it asks rather than reaching for one, so the same page a
person loads is the page a test drives with a scripted model. Called with nothing it
builds the real one, once per server process.
"""

import sys
from pathlib import Path

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
    single_value,
    table,
    unit_line,
)
from veritas.llm import LanguageModelError
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


@st.cache_resource(show_spinner="Opening the Warehouse and indexing the Semantic Layer…")
def built() -> Orchestrator:
    """The Orchestrator this server answers with, built on the first question asked.

    Cached as a resource because it holds the Warehouse connection and the Retriever's
    fitted indexes, and a page that rebuilt those per question would pay the index on
    every keystroke.
    """
    return Orchestrator(WarehouseAdapter())


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
) -> None:
    """The whole page: who is asking, the question box, and the answer to the last
    question asked."""
    st.set_page_config(page_title=TITLE, page_icon="⚖️")
    st.title(TITLE)
    st.caption(CAPTION)

    with st.sidebar:
        st.subheader("Asked as")
        st.markdown("\n".join(f"- {line}" for line in identity_lines(access_profile)))
        st.caption(ENFORCEMENT_NOTE)
        st.subheader("Model")
        st.caption(model_line())

    with st.form("question"):
        question = st.text_input(PROMPT, placeholder=PLACEHOLDER)
        asked = st.form_submit_button("Ask")

    if not (asked and question.strip()):
        return

    try:
        answer = (built() if orchestrator is None else orchestrator).answer(
            question.strip(), access_profile
        )
    except LanguageModelError as unreachable:
        st.error(
            f"This question was not asked, because Veritas could not reach a model: "
            f"{unreachable}"
        )
        return
    show(answer)


if __name__ == "__main__":
    page()
