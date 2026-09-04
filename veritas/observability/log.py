"""The Question Log seam — what Observability records, before it is a table.

[`Question Log`](../../.claude/docs/glossary.md#a-the-system) is registered as *"the
record Observability keeps: one row per question a person asked through the App, carrying
its Grounded Answer, Validation Gate outcome, Lineage, Operational Measures and
Feedback"*, and this is the interface that record is written through.

It is a Protocol for the reason `LanguageModel` is one: what satisfies a seam should not
have to import it. The App holds one, a test drives a double, and `postgres.py` is the
one implementation that reaches a server.

**Recording is not answering, and a failure to record must not become one.** Every way
the log can fail arrives as `QuestionLogError`, so the App can put a warning beside an
answer a person already has rather than replacing it with one.
"""

from typing import Protocol

from veritas.orchestrator import GroundedAnswer
from veritas.validation import AccessProfile


class QuestionLogError(RuntimeError):
    """The Question Log could not be reached, or would not take a row.

    Covers the server being absent, the credentials being unset or wrong, and a write
    that failed. They are one thing to a caller: this question is not recorded, and the
    person who asked it is owed their answer anyway.
    """


class QuestionLog(Protocol):
    """What Observability needs from a store, and the whole of it.

    `record` returns the identifier of the row it wrote, because Feedback is left
    against an answer and not against a question string: a person who asks the same
    words twice gets two rows, and a verdict belongs to the one they were shown.
    """

    def record(
        self, answer: GroundedAnswer, access_profile: AccessProfile
    ) -> int: ...
