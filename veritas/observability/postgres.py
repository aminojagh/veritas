"""The Question Log in Postgres — the single boundary through which it is written.

**This is the only module in the repository permitted to import `psycopg`**, which is
the shape
[ADR-0002](../../.claude/docs/adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)
gave the Warehouse and the reason is the same: a store reached from everywhere is a
store nothing can replace, and one reached through a seam is an interface plus one
trivial implementation. What is behind the seam is as crude as that ADR licenses — one
connection, held open, no pool.

The schema is one Data Definition Language (DDL) file applied on connect. It is
idempotent, so a fresh container and a container with a month of rows in it reach the
same state, and nothing has to be run by hand before the App can record.

**Credentials are one set, read from `.env`.** `docker-compose.yml` reads the same five
variables to create the server that these connect to, so a reviewer who copies
`.env.example` has a database and an App that agree without editing either.
"""

import os
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from veritas.llm import ENV_FILE
from veritas.observability.log import Feedback, QuestionLogError
from veritas.orchestrator import GroundedAnswer
from veritas.validation import AccessProfile

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

# The five variables, spelled as the `postgres` image itself spells the three it reads,
# so compose and the App take one set rather than two that have to be kept equal.
HOST_VARIABLE = "POSTGRES_HOST"
PORT_VARIABLE = "POSTGRES_PORT"
USER_VARIABLE = "POSTGRES_USER"
PASSWORD_VARIABLE = "POSTGRES_PASSWORD"
DATABASE_VARIABLE = "POSTGRES_DB"

# Where the App looks for the server compose publishes. Defaults, because a reviewer
# running `docker compose up` gets exactly this and should not have to say so.
DEFAULTS = {HOST_VARIABLE: "localhost", PORT_VARIABLE: "5432"}

INSERT_QUESTION = """
INSERT INTO question (
    question, rewritten, ended_by, role, sql, row_count,
    allowed, explanation, reasons, refusal, clarifying_question, seconds, cost
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
RETURNING question_id
"""

INSERT_LINEAGE_ENTRY = """
INSERT INTO lineage_entry (question_id, position, name, kind, version)
VALUES (%s, %s, %s, %s, %s)
"""

INSERT_MODEL_CALL = """
INSERT INTO model_call (
    question_id, position, provider, model,
    prompt_tokens, completion_tokens, seconds, cost
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

# The latest verdict on an answer stands, so a second one replaces the first in place
# rather than becoming a second row about the same answer.
LEAVE_FEEDBACK = """
INSERT INTO feedback (question_id, up, note) VALUES (%s, %s, %s)
ON CONFLICT (question_id) DO UPDATE
SET up = EXCLUDED.up, note = EXCLUDED.note, left_at = now()
"""


def settings() -> dict[str, str]:
    """The five connection values, from the environment or from `.env`.

    Read without overriding, exactly as a key is: a variable already set wins over the
    file, which is what makes a one-off run against another server possible without
    editing it.

    Raises `QuestionLogError` naming every variable that has no value, because a person
    who has set none should be told all five rather than one per attempt.
    """
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)
    values = {
        name: os.environ.get(name) or DEFAULTS.get(name, "")
        for name in (
            HOST_VARIABLE,
            PORT_VARIABLE,
            USER_VARIABLE,
            PASSWORD_VARIABLE,
            DATABASE_VARIABLE,
        )
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise QuestionLogError(
            f"the Question Log has no {', '.join(missing)}: copy .env.example to "
            f"{ENV_FILE.name}, or run without recording"
        )
    return values


def connection_string(values: dict[str, str] | None = None) -> str:
    """One connection string from those five values.

    Assembled by the driver rather than by formatting, for the reason the Warehouse
    Adapter prefers a construct that assembles no text: a password with a space or a
    quote in it is a value, not a syntax error.
    """
    values = settings() if values is None else values
    return make_conninfo(
        host=values[HOST_VARIABLE],
        port=values[PORT_VARIABLE],
        user=values[USER_VARIABLE],
        password=values[PASSWORD_VARIABLE],
        dbname=values[DATABASE_VARIABLE],
    )


class PostgresQuestionLog:
    """One Postgres connection, held open for the process, with the schema applied.

    Usable as a context manager:

        with PostgresQuestionLog() as log:
            log.record(answer, ANALYST)
    """

    def __init__(self, conninfo: str = "") -> None:
        self.conninfo = conninfo or connection_string()
        try:
            self._connection = psycopg.connect(self.conninfo)
            with self._connection.cursor() as cursor:
                cursor.execute(SCHEMA_PATH.read_text())
            self._connection.commit()
        except psycopg.Error as unreachable:
            raise QuestionLogError(
                f"the Question Log at {self} would not open: {unreachable}"
            ) from unreachable

    def __str__(self) -> str:
        """`localhost:5432/veritas` — where the rows go, never the password."""
        where = conninfo_to_dict(self.conninfo)
        return f"{where.get('host')}:{where.get('port')}/{where.get('dbname')}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self!s})"

    def __enter__(self) -> "PostgresQuestionLog":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Give the connection back."""
        self._connection.close()

    def record(self, answer: GroundedAnswer, access_profile: AccessProfile) -> int:
        """Write one question, its Lineage and its model calls, and return its row.

        One transaction, because a question with half its Lineage recorded is a row that
        under-reports what an answer was composed from and reads exactly like a row that
        was composed of less.
        """
        outcome = answer.outcome
        try:
            with self._connection.transaction(), self._connection.cursor() as cursor:
                cursor.execute(
                    INSERT_QUESTION,
                    (
                        answer.question,
                        answer.rewritten,
                        str(answer.ended_by),
                        access_profile.role,
                        answer.sql or None,
                        len(answer.rows) if answer.answered else None,
                        outcome.allowed if outcome else None,
                        outcome.explanation if outcome else None,
                        [str(reason) for reason in outcome.reasons] if outcome else [],
                        answer.refusal or None,
                        answer.clarifying_question,
                        answer.seconds,
                        answer.cost,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    raise QuestionLogError("the Question Log took a row and named none")
                question_id = int(row[0])
                cursor.executemany(
                    INSERT_LINEAGE_ENTRY,
                    [
                        (question_id, position, entry.name, entry.kind, entry.version)
                        for position, entry in enumerate(answer.lineage.entries)
                    ],
                )
                cursor.executemany(
                    INSERT_MODEL_CALL,
                    [
                        (
                            question_id,
                            position,
                            call.provider,
                            call.model,
                            call.prompt_tokens,
                            call.completion_tokens,
                            call.seconds,
                            call.cost,
                        )
                        for position, call in enumerate(answer.calls)
                    ],
                )
        except psycopg.Error as refused:
            raise QuestionLogError(
                f"the Question Log at {self} would not take this question: {refused}"
            ) from refused
        return question_id


    def leave_feedback(self, question_id: int, feedback: Feedback) -> None:
        """Attach Feedback to the row a question was recorded as.

        Whatever stood there before is replaced, and a `question_id` no row carries is
        refused by the foreign key rather than stored as Feedback about nothing.
        """
        try:
            with self._connection.transaction(), self._connection.cursor() as cursor:
                cursor.execute(
                    LEAVE_FEEDBACK,
                    (question_id, feedback.up, feedback.note or None),
                )
        except psycopg.Error as refused:
            raise QuestionLogError(
                f"the Question Log at {self} would not take this feedback: {refused}"
            ) from refused


def question_log() -> PostgresQuestionLog:
    """The Question Log this installation records to.

    Raises `QuestionLogError` when there is none to reach, which is a thing the App says
    beside the identity rather than a thing it stops for.
    """
    return PostgresQuestionLog()
