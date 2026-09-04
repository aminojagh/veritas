"""Observability — what Veritas did at runtime, recorded rather than described.

[`Observability`](../../.claude/docs/glossary.md#a-the-system) *"records what happened at
runtime: every question, Grounded Answer, Validation Gate outcome, cost, latency and
Feedback — the Question Log. **Records; never judges.** Live traffic, no ground truth."*

`log.py` is the seam and the error every failure to record arrives as; `postgres.py` is
the one implementation that reaches a server, and `schema.sql` is the four tables it
applies on connect.
"""

from veritas.observability.log import Feedback, QuestionLog, QuestionLogError
from veritas.observability.postgres import (
    DATABASE_VARIABLE,
    DEFAULTS,
    HOST_VARIABLE,
    PASSWORD_VARIABLE,
    PORT_VARIABLE,
    SCHEMA_PATH,
    USER_VARIABLE,
    PostgresQuestionLog,
    connection_string,
    question_log,
    settings,
)

__all__ = [
    "DATABASE_VARIABLE",
    "DEFAULTS",
    "HOST_VARIABLE",
    "PASSWORD_VARIABLE",
    "PORT_VARIABLE",
    "SCHEMA_PATH",
    "USER_VARIABLE",
    "Feedback",
    "PostgresQuestionLog",
    "QuestionLog",
    "QuestionLogError",
    "connection_string",
    "question_log",
    "settings",
]
