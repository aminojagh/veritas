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

**`EndedBy` is here for the same reason `Lineage` is.** It was
`veritas/evaluation/`'s, where a sweep needed to tell a wrong answer from a correct
statement the Gate refused; Observability needs the same word to group a chart by, and a
taxonomy owned by the component that scores answers is a taxonomy the component that
records them has to copy. It moved here, and splitting its coarsest member is
[DEBT-032](../../.claude/docs/debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by)
paid.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from veritas.llm import ModelCall
from veritas.semantic import SemanticEntry
from veritas.validation import ValidationGateOutcome


class EndedBy(StrEnum):
    """Which step of the flow ended a question.

    `flow.py`'s five ways a question ends without a number, the one that is not an
    ending at all, and the answer itself. A closed taxonomy rather than a sentence,
    because *"refusals by reason"* is a chart and prose is not a bar:
    [ADR-0003](../../.claude/docs/adr/0003-validation-gate-is-deterministic-code.md)
    argued that for the Validation Gate's own reasons, and it applies here the moment
    anything groups by it.

    A `StrEnum` so the member survives into a table, a Postgres row and a Grafana
    filter as the word a person reads.
    """

    ANSWER = "answer"
    """A number came back, under a Validation Gate outcome that allowed it."""

    REWRITE = "rewrite"
    """The question said an Ambiguous Term and did not say which meaning, so Veritas
    asked back."""

    RETRIEVAL = "retrieval"
    """Nothing retrieved for the question defines a Certified Metric."""

    GENERATION = "generation"
    """The model was shown entries that define one and refused to write a statement."""

    GATE = "gate"
    """The model wrote a statement and the Validation Gate refused it."""

    ENGINE = "engine"
    """The Gate allowed the statement and the Warehouse would not run it."""

    PROVIDER = "provider"
    """The call did not come back at all — no key, a timeout, a reply that is not JSON.
    Not one of `flow.py`'s endings and deliberately kept apart from them: it says
    nothing about the question, and it is the one member no Grounded Answer carries,
    because there is none. A sweep scores it as a row of its own; Observability records
    no row for it at all."""


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

    **`calls` and `seconds` are what the question cost to answer**, and they are on the
    answer because the Orchestrator measures and Observability records: what `answer()`
    returns carries the measures, so nothing has to ask the Orchestrator a second
    question to find out what the first one took.

    **`ended_by` is stated, not inferred.** Four of the six endings are visible in the
    fields — a question asked back, a number, a statement the Gate refused, a statement
    the engine refused — and two are not: a refusal with no statement is either the
    corpus having nothing that defines a Certified Metric or the model declining to
    write one, and only the step that decided knows which. So the producer says, and
    the fifth check below holds what it said against what the object shows.

    The five checks are the contract rather than caution. A Grounded Answer that
    both refuses and asks back says two different things about one question; one that
    answers without SQL is the bare number the Glossary says Veritas never returns; one
    that answers under a verdict that is not an allowing verdict is a number that
    reached a person past the Validation Gate; one whose names do not label its
    values is a table whose headings belong to a different query; and one whose ending
    contradicts its own fields is a chart bar that counts the wrong questions.
    """

    question: str
    ended_by: EndedBy
    rewritten: str = ""
    sql: str = ""
    columns: tuple[str, ...] = ()
    rows: tuple[tuple[object, ...], ...] = ()
    lineage: Lineage = field(default_factory=Lineage)
    outcome: ValidationGateOutcome | None = None
    refusal: str = ""
    clarifying_question: str | None = None
    calls: tuple[ModelCall, ...] = ()
    seconds: float = 0.0

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
        if self.ended_by not in self.endings():
            raise ValueError(
                f"this answer says it ended by '{self.ended_by}' and its own fields "
                f"say {' or '.join(f"'{one}'" for one in self.endings())}"
            )

    @property
    def answered(self) -> bool:
        """Whether a number came back, as opposed to a refusal or a question."""
        return not self.refusal and self.clarifying_question is None

    def endings(self) -> tuple[EndedBy, ...]:
        """The endings these fields are consistent with — one, or the two a refusal
        with no statement cannot be told apart by.

        The whole of what a Grounded Answer can say about how it ended, which is why
        `ended_by` is a field: everything below returns one member except the case
        DEBT-032 splits, and that case is the reason the field exists.
        """
        if self.clarifying_question is not None:
            return (EndedBy.REWRITE,)
        if self.answered:
            return (EndedBy.ANSWER,)
        if not self.sql:
            return (EndedBy.RETRIEVAL, EndedBy.GENERATION)
        allowed = self.outcome is not None and self.outcome.allowed
        return (EndedBy.ENGINE,) if allowed else (EndedBy.GATE,)

    @property
    def cost(self) -> Decimal | None:
        """What answering this question cost, or `None` where any call was unpriced.

        `None` rather than a partial sum, because a total missing one of its terms is a
        smaller number and not a less certain one, and a cost chart reading it would
        under-report rather than abstain. A question that made no model call at all
        cost nothing, which is a total and not a gap.
        """
        costs = [call.cost for call in self.calls]
        return None if None in costs else sum(costs, Decimal(0))
