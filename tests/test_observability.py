"""What the Question Log records, and what it refuses to lose on the way.

Two claims. The **seam claim**: the only module that names Postgres is
`veritas/observability/postgres.py`, and an installation with no server says which value
it is missing rather than raising a driver's exception at whoever asked a question. The
**row claim**: a Grounded Answer becomes one row carrying its ending, its statement, its
verdict with the Rejection Reasons a chart groups by, its Lineage entry by entry and its
model calls call by call — and a cost that is absent rather than zero where the model
that served it is unpriced.

The row claim needs a real server, because a claim about a schema proven against a double
is a claim about the double. Every test under the row-claim heading takes the `log`
fixture, and that fixture is the whole of the gating: with no server reachable it skips
the test, naming the value it could not connect with. The seam-claim tests above it never
connect, and run either way.

Nothing here starts or stops a container — the server is brought up by hand, once, and
left up:

    docker compose up -d postgres && uv run pytest tests/test_observability.py

Afterwards `docker compose down` stops it and keeps the rows, because the volume is named;
`docker compose down -v` empties it, and the next connect applies `schema.sql` to an empty
database again. Either is safe to run straight after a suite: these tests record into the
Question Log this installation is configured for and delete their own rows by identifier
as each finishes, so a run leaves it as it found it. This file reads what it wrote through
its own connection rather than through the writer's, since a writer that reports its own
rows correct proves less than an independent reader does.
"""

import re
from decimal import Decimal

import psycopg
import pytest
from psycopg.rows import dict_row

from veritas.llm import ModelCall
from veritas.observability import (
    DATABASE_VARIABLE,
    HOST_VARIABLE,
    PASSWORD_VARIABLE,
    PORT_VARIABLE,
    USER_VARIABLE,
    PostgresQuestionLog,
    QuestionLogError,
    connection_string,
    settings,
)
from veritas.orchestrator import EndedBy, GroundedAnswer, Lineage
from veritas.validation import ANALYST, RejectionReason, ValidationGateOutcome

# A statement and the verdict it earns are not what this file is about, so both are
# written rather than generated: what is under test is the row, not the Gate.
STATEMENT = (
    "SELECT count(fct_trade.trade_id) AS answer FROM fct_trade "
    "JOIN dim_account ON dim_account.account_id = fct_trade.account_id "
    "JOIN dim_client ON dim_client.client_id = dim_account.client_id "
    "WHERE dim_client.client_region = 'EU'"
)

# One call to a model the price table prices, and one to a model it does not.
PRICED = ModelCall("openai", "gpt-5.4-mini", prompt_tokens=1200, completion_tokens=90)
UNPRICED = ModelCall("groq", "openai/gpt-oss-120b", prompt_tokens=900, completion_tokens=40)

ALL_FIVE = (
    HOST_VARIABLE,
    PORT_VARIABLE,
    USER_VARIABLE,
    PASSWORD_VARIABLE,
    DATABASE_VARIABLE,
)


# -- the seam claim --------------------------------------------------------------


def test_only_the_postgres_module_names_the_driver(root):
    """One boundary, checked rather than promised — the shape ADR-0002 gave the
    Warehouse, applied to the store Observability writes to."""
    importing = {
        str(path.relative_to(root))
        for path in sorted((root / "veritas").rglob("*.py"))
        if "__pycache__" not in path.parts
        and re.search(r"^import psycopg|^from psycopg", path.read_text(), re.M)
    }
    assert importing == {"veritas/observability/postgres.py"}


def test_an_installation_with_no_credentials_is_told_all_of_them(monkeypatch, tmp_path):
    """A person who has set none should be told five things once, not one thing five
    times."""
    monkeypatch.setattr("veritas.observability.postgres.ENV_FILE", tmp_path / "absent")
    for name in ALL_FIVE:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(QuestionLogError) as unreachable:
        settings()
    said = str(unreachable.value)
    assert USER_VARIABLE in said and PASSWORD_VARIABLE in said
    assert DATABASE_VARIABLE in said
    assert HOST_VARIABLE not in said and PORT_VARIABLE not in said, (
        "the host and the port default to what compose publishes"
    )


def test_the_five_values_become_one_connection_string(monkeypatch, tmp_path):
    """Assembled by the driver rather than by formatting, so a password with a space in
    it is a value and not a syntax error."""
    monkeypatch.setattr("veritas.observability.postgres.ENV_FILE", tmp_path / "absent")
    monkeypatch.setenv(USER_VARIABLE, "veritas")
    monkeypatch.setenv(PASSWORD_VARIABLE, "a pass'word")
    monkeypatch.setenv(DATABASE_VARIABLE, "veritas")
    for name in (HOST_VARIABLE, PORT_VARIABLE):
        monkeypatch.delenv(name, raising=False)
    where = psycopg.conninfo.conninfo_to_dict(connection_string())
    assert where["password"] == "a pass'word"
    assert (where["host"], where["port"]) == ("localhost", "5432")


# -- the row claim ---------------------------------------------------------------


@pytest.fixture(scope="module")
def log():
    """The Question Log this installation is configured for, opened once."""
    try:
        opened = PostgresQuestionLog()
    except QuestionLogError as unreachable:
        pytest.skip(f"no Question Log to record to: {unreachable}")
    with opened:
        yield opened


@pytest.fixture
def writing(log):
    """Record a question, and take every row this test wrote back out at the end."""
    written: list[int] = []

    def record(answer, access_profile=ANALYST) -> int:
        written.append(log.record(answer, access_profile))
        return written[-1]

    yield record
    with psycopg.connect(log.conninfo) as connection:
        connection.execute(
            "DELETE FROM question WHERE question_id = ANY(%s)", (written,)
        )


def read(log, table: str, question_id: int) -> list[dict]:
    """Every row of one table for one question, read through a connection of this
    file's own."""
    with psycopg.connect(log.conninfo, row_factory=dict_row) as connection:
        return connection.execute(
            f"SELECT * FROM {table} WHERE question_id = %s ORDER BY question_id",
            (question_id,),
        ).fetchall()


@pytest.fixture
def answered(semantic):
    """A question that was answered, with everything a row can carry on it."""
    return GroundedAnswer(
        question="how many trades did we make",
        ended_by=EndedBy.ANSWER,
        rewritten="how many trades did we make",
        sql=STATEMENT,
        columns=("answer",),
        rows=((412,),),
        lineage=Lineage((
            semantic.metrics["Trade Count"],
            semantic.join_paths["trade_to_account"],
        )),
        outcome=ValidationGateOutcome(
            allowed=True, rules=("read-only",), metrics=("Trade Count",)
        ),
        calls=(PRICED,),
        seconds=2.75,
    )


def test_the_schema_is_applied_on_connect_and_a_second_connect_keeps_the_rows(
    log, writing, answered
):
    """A fresh container and a container with a month of traffic in it reach the same
    state, so nothing has to be run by hand before the App can record — and a second
    process opening the log applies the same file without emptying it.
    """
    question_id = writing(answered)
    with PostgresQuestionLog(log.conninfo):
        pass
    assert len(read(log, "question", question_id)) == 1


def test_an_answered_question_is_one_row_saying_what_it_was_and_what_it_took(
    log, writing, answered
):
    """The whole of a Grounded Answer that carried a number: the ending a chart groups
    by, the statement, the verdict, how many rows came back, and what answering it
    cost."""
    question_id = writing(answered)
    [row] = read(log, "question", question_id)
    assert row["question"] == answered.question
    assert row["ended_by"] == str(EndedBy.ANSWER)
    assert row["role"] == ANALYST.role
    assert row["sql"] == STATEMENT
    assert row["row_count"] == 1
    assert row["allowed"] is True and row["reasons"] == []
    assert row["refusal"] is None and row["clarifying_question"] is None
    assert row["seconds"] == 2.75
    assert row["cost"] == PRICED.cost
    assert row["asked_at"] is not None


def test_the_lineage_is_one_row_per_entry_at_the_version_it_was_read(
    log, writing, answered
):
    """*"Which Semantic Entries and which Metric Definition versions produced a Grounded
    Answer"* — recorded per entry, in the order the answer cites them, so
    metric-usage frequency is a count and not a parse."""
    question_id = writing(answered)
    entries = read(log, "lineage_entry", question_id)
    assert [(one["position"], one["name"], one["kind"]) for one in entries] == [
        (0, "Trade Count", "metric"),
        (1, "trade_to_account", "join_path"),
    ]
    assert all(one["version"] >= 1 for one in entries)


def test_a_model_call_is_one_row_carrying_what_it_read_wrote_and_cost(
    log, writing, answered
):
    """Per call rather than per question, because *"cost by model"* is a chart and a
    question can ask two different models one thing each."""
    question_id = writing(answered)
    [call] = read(log, "model_call", question_id)
    assert (call["provider"], call["model"]) == ("openai", "gpt-5.4-mini")
    assert (call["prompt_tokens"], call["completion_tokens"]) == (1200, 90)
    assert call["cost"] == Decimal("0.001305")


def test_a_refused_question_records_the_reasons_a_chart_groups_by(log, writing):
    """*"Validation-Gate rejections by reason"* reads this column. A refused statement
    produced no rows, which is not the same as producing none."""
    refused = ValidationGateOutcome(
        allowed=False,
        explanation="dim_client.client_name is restricted",
        reasons=(RejectionReason.RESTRICTED_COLUMN,),
        rules=("read-only", "restricted columns"),
    )
    question_id = writing(
        GroundedAnswer(
            question="what is our biggest client called",
            ended_by=EndedBy.GATE,
            rewritten="what is our biggest client called",
            sql="SELECT dim_client.client_name FROM dim_client",
            outcome=refused,
            refusal=refused.explanation,
            calls=(PRICED, PRICED),
            seconds=1.5,
        )
    )
    [row] = read(log, "question", question_id)
    assert row["allowed"] is False
    assert row["reasons"] == [str(RejectionReason.RESTRICTED_COLUMN)]
    assert row["explanation"] == refused.explanation
    assert row["row_count"] is None
    assert row["refusal"] == refused.explanation
    assert len(read(log, "model_call", question_id)) == 2


def test_a_question_asked_back_records_the_question_and_no_statement(log, writing):
    """The first way out, and a row: the person was asked which meaning, and nothing
    reached the Gate."""
    question_id = writing(
        GroundedAnswer(
            question="what was our revenue",
            ended_by=EndedBy.REWRITE,
            rewritten="what was our revenue",
            clarifying_question="Do you mean Gross Revenue or Net Revenue?",
            calls=(PRICED,),
            seconds=0.9,
        )
    )
    [row] = read(log, "question", question_id)
    assert row["ended_by"] == str(EndedBy.REWRITE)
    assert row["clarifying_question"].startswith("Do you mean")
    assert (row["sql"], row["allowed"], row["row_count"]) == (None, None, None)
    assert read(log, "lineage_entry", question_id) == []


def test_an_unpriced_model_leaves_a_gap_in_the_cost_column_rather_than_a_zero(
    log, writing, answered
):
    """A cost of nothing and a cost nobody knows are different bars, and only one of
    them is true of a model this repository has read no price for."""
    from dataclasses import replace

    question_id = writing(replace(answered, calls=(PRICED, UNPRICED)))
    [row] = read(log, "question", question_id)
    assert row["cost"] is None
    costs = [one["cost"] for one in read(log, "model_call", question_id)]
    assert costs == [PRICED.cost, None]


def test_where_the_rows_go_is_said_without_the_password(log):
    """What the sidebar prints and what an error message carries."""
    assert str(log).endswith("/veritas")
    assert settings()[PASSWORD_VARIABLE] not in f"{log!r} {log!s}"
