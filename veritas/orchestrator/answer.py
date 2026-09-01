"""The Grounded Answer and its Lineage — the data contract, before it is a return value.

Both are Glossary terms.
[`Grounded Answer`](../../.claude/docs/glossary.md#a-the-system) is *"the response
object: the answer, the SQL, the Lineage, and the Validation Gate outcome. Veritas never
returns a bare number"*, and
[`Lineage`](../../.claude/docs/glossary.md#a-the-system) is *"the record of which
Semantic Entries and which Metric Definition versions produced a Grounded Answer. What
makes an answer auditable."*

They are here rather than in `flow.py` for the reason `ValidationGateOutcome` is not in
`gate.py`: the App renders a Grounded Answer, Observability logs one, and neither
imports the sequence that produced it. A contract only its producer can import is not a
contract.

**Not answering is a result, not an absence.** A question Veritas will not answer comes
back as a Grounded Answer too — carrying the refusal, or the question Veritas asks back
— because the alternative is a caller that has to tell a return value from an
exception to know whether it was answered.
"""

from dataclasses import dataclass, field

from veritas.semantic import SemanticEntry
from veritas.validation import ValidationGateOutcome


@dataclass(frozen=True, slots=True)
class Lineage:
    """Which Semantic Entries, at which versions, produced a Grounded Answer.

    The entries themselves rather than their names, because `version` is on them and a
    record that carried the name alone would say which entry and not which reading of
    it. They are frozen, so carrying them is carrying a record and not a handle.

    Frozen for the reason a `Validation Gate outcome` is: it is evidence, and evidence
    the App or a logger could edit is evidence nothing can be held to.
    """

    entries: tuple[SemanticEntry, ...] = ()

    def versions(self) -> dict[str, int]:
        """Each entry's name and the version it was read at — the Glossary's own
        *"which Semantic Entries and which Metric Definition versions"* in one call."""
        return {entry.name: entry.version for entry in self.entries}

    def __str__(self) -> str:
        """`Gross Revenue (metric v1); trade_to_fx_rate… (join_path v1)` — one line."""
        return (
            "; ".join(
                f"{entry.name} ({entry.kind} v{entry.version})"
                for entry in self.entries
            )
            or "nothing"
        )


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    """What a question comes back as, answered or not.

    `rows` is what the Warehouse returned and `columns` is what the engine calls each
    position in them, `sql` is the statement they came back for, `lineage` is what that
    statement was built from and `outcome` is the verdict it was allowed under.
    `refusal` is the sentence a person reads when there is no number, and
    `clarifying_question` is the question Veritas asks back when the question said an
    Ambiguous Term and did not say which meaning.

    **A row is unreadable without its column names.** A breakdown comes back as
    `(('EU', Decimal('46282.79')),)`, and which position is the axis and which is the
    metric is knowledge the generation rules put in a prompt. `columns` is that
    knowledge as a field, so a caller labels an answer by reading it rather than by
    knowing what the prompt asked for.

    **`rows` being empty is an answer.** A certified statement over a period the
    Warehouse holds no rows for returns nothing and has still been answered, which is
    why `answered` reads the refusal and not the rows.

    The four checks below are the contract rather than caution. A Grounded Answer that
    both refuses and asks back says two different things about one question; one that
    answers without SQL is the bare number the Glossary says Veritas never returns; one
    that answers under a verdict that is not an allowing verdict is a number that
    reached a person past the Validation Gate; and one whose names do not label its
    values is a table whose headings belong to a different query.
    """

    question: str
    rewritten: str = ""
    sql: str = ""
    columns: tuple[str, ...] = ()
    rows: tuple[tuple[object, ...], ...] = ()
    lineage: Lineage = field(default_factory=Lineage)
    outcome: ValidationGateOutcome | None = None
    refusal: str = ""
    clarifying_question: str | None = None

    def __post_init__(self) -> None:
        if self.refusal and self.clarifying_question is not None:
            raise ValueError(
                f"this answer both refuses ({self.refusal!r}) and asks back "
                f"({self.clarifying_question!r}), and a question gets one of the two"
            )
        if self.answered and not self.sql:
            raise ValueError(
                "an answered question carries the SQL that answered it — a Grounded "
                "Answer is never a bare number"
            )
        if self.answered and not (self.outcome and self.outcome.allowed):
            raise ValueError(
                f"an answered question carries the Validation Gate outcome that let it "
                f"run, and this one carries {self.outcome!r}"
            )
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError(
                f"every value in a row is labelled by the column it came back under, "
                f"and these {len(self.columns)} names do not label "
                f"{[len(row) for row in self.rows]}"
            )

    @property
    def answered(self) -> bool:
        """Whether a number came back, as opposed to a refusal or a question."""
        return not self.refusal and self.clarifying_question is None
