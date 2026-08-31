"""The sequence a question runs through, and every way it can end without a number.

The whole of the
[Target State's flow](../../.claude/docs/design/target-state.md#flow) in one method:
rewrite, retrieve, ground, generate, validate, execute, answer. It owns the order and
the failure paths and none of the steps — `rewrite.py` resolves, `veritas.retrieval`
searches, `generate.py` grounds and asks, `veritas.validation` judges, and
`veritas.warehouse` executes.

**Five ways a question ends without a number, and each is a Grounded Answer.** The
question said an Ambiguous Term and did not say which meaning; nothing retrieved defines
a metric; the model refused; the Validation Gate refused; the engine refused. A caller
reads which from the Grounded Answer rather than from an exception, because four of the
five are Veritas working correctly.

**A provider that will not answer is the sixth way and is deliberately not one of
them.** A missing key, a timeout or a reply that is not JSON raises `LanguageModelError`
out of here, because *"this question cannot be answered"* and *"this installation cannot
reach a model"* are different sentences and only the first is about the question.
"""

from collections.abc import Mapping, Sequence

from veritas.llm import LanguageModel
from veritas.orchestrator.answer import GroundedAnswer, Lineage
from veritas.orchestrator.generate import GROUNDED_FIELDS, generate
from veritas.orchestrator.rewrite import rewrite
from veritas.retrieval import TOP_K, RetrievalStrategy, Retriever
from veritas.semantic import MetricDefinition, SemanticEntry
from veritas.validation import (
    ACCESS_AXIS,
    ANALYST,
    AccessProfile,
    ValidationGate,
)
from veritas.warehouse import WarehouseAdapter, WarehouseError


class Orchestrator:
    """One Warehouse, one corpus, one model — asked a question at a time.

    Built once and reused, the way a `ValidationGate` is: the Semantic Layer is read
    once and the Retriever's text index is fitted once, so the cost of asking a second
    question is the two model calls and the query.

    **One reading of the corpus serves every step.** The Gate loads the Semantic Layer,
    and the Retriever and the rewrite step are given that same `SemanticLayer` rather
    than loading their own — two readings of `semantic/` under one question is two
    chances for a Grounded Answer to cite a version the Gate did not judge against.

    `strategy` is held here rather than passed per question because a comparison across
    Retrieval Strategies varies the Orchestrator and not the question, and every
    Orchestrator built over one Retriever shares its indexes.

    The model is resolved when it is called rather than when this is built, so
    constructing one costs no key: `None` means whichever provider the environment
    names.
    """

    def __init__(
        self,
        warehouse: WarehouseAdapter,
        model: LanguageModel | None = None,
        retriever: Retriever | None = None,
        gate: ValidationGate | None = None,
        strategy: RetrievalStrategy = RetrievalStrategy.RERANKED,
        top_k: int = TOP_K,
    ) -> None:
        self.warehouse = warehouse
        self.gate = ValidationGate(warehouse) if gate is None else gate
        self.retriever = (
            Retriever(self.gate.semantic) if retriever is None else retriever
        )
        self.model = model
        self.strategy = strategy
        self.top_k = top_k

    def grounded_entries(self, question: str) -> list[SemanticEntry]:
        """What the model is shown: what the question retrieves, then what the identity
        requires.

        The access axis and the Join Paths it is reached by are appended whichever
        question was asked, because every statement Veritas runs is scoped and a model
        that was not shown the route cannot write one. They are appended rather than
        searched for: retrieval already returns them when a question is *about* region,
        and this is the case where the question is about something else and the identity
        still is not.

        Order is retrieval order, so the entry a question most nearly names stays first
        and the access route sits at the end where it is a constraint rather than a
        subject.
        """
        found = self.retriever.retrieve(question, self.strategy, self.top_k)
        axis = self.gate.semantic.dimensions[ACCESS_AXIS]
        required: list[SemanticEntry] = [axis]
        for names in axis.routes.values():
            required.extend(self.gate.semantic.join_paths[name] for name in names)

        grounded = list(found)
        seen = {entry.name for entry in grounded}
        for entry in required:
            if entry.name not in seen:
                seen.add(entry.name)
                grounded.append(entry)
        return grounded

    def answer(
        self, question: str, access_profile: AccessProfile = ANALYST
    ) -> GroundedAnswer:
        """Run one question through the flow, and say what came of it.

        The Access Profile is an argument for the reason it is one on
        `ValidationGate.judge`: it is the identity a **question** is asked as, so one
        Orchestrator serves many identities. There is no default identity beyond the one
        Access Profile this slice declares.
        """
        resolved = rewrite(question, self.model, self.gate.semantic)
        if not resolved.resolved:
            return GroundedAnswer(
                question=question,
                rewritten=resolved.rewritten,
                clarification=resolved.clarification,
            )

        entries = self.grounded_entries(resolved.rewritten)
        lineage = self.lineage_of(entries, resolved.resolutions)
        if not any(isinstance(entry, MetricDefinition) for entry in entries):
            return GroundedAnswer(
                question=question,
                rewritten=resolved.rewritten,
                lineage=lineage,
                refusal="nothing retrieved for this question defines a Certified "
                        "Metric, and Veritas answers only with those",
            )

        written = generate(resolved.rewritten, entries, access_profile, self.model)
        if not written.sql:
            return GroundedAnswer(
                question=question,
                rewritten=resolved.rewritten,
                lineage=lineage,
                refusal=written.refusal,
            )

        outcome = self.gate.judge(written.sql, access_profile)
        if not outcome.allowed:
            return GroundedAnswer(
                question=question,
                rewritten=resolved.rewritten,
                sql=written.sql,
                lineage=lineage,
                outcome=outcome,
                refusal=outcome.explanation,
            )

        try:
            rows = self.warehouse.query(written.sql)
        except WarehouseError as refused:
            return GroundedAnswer(
                question=question,
                rewritten=resolved.rewritten,
                sql=written.sql,
                lineage=lineage,
                outcome=outcome,
                refusal=f"the Validation Gate allowed this statement and the engine "
                        f"would not run it: {refused}",
            )
        return GroundedAnswer(
            question=question,
            rewritten=resolved.rewritten,
            sql=written.sql,
            rows=tuple(rows),
            lineage=lineage,
            outcome=outcome,
        )

    def lineage_of(
        self,
        entries: Sequence[SemanticEntry],
        resolutions: Mapping[str, tuple[str, ...]],
    ) -> Lineage:
        """The entries an answer was built from: the Ambiguous Terms the rewrite step
        resolved, then everything that reached the prompt.

        `GROUNDED_FIELDS` decides the second half, so what Lineage claims produced the
        answer is exactly what the model was shown — one list, read twice, rather than a
        second opinion about what mattered. An entry retrieved and grounded as nothing
        is left out.

        The resolved terms lead, because they are what turned the word the person typed
        into the metric that was computed, and they ground nothing themselves.
        """
        return Lineage(
            tuple(self.gate.semantic.ambiguous_terms[name] for name in resolutions)
            + tuple(entry for entry in entries if GROUNDED_FIELDS[type(entry)])
        )
