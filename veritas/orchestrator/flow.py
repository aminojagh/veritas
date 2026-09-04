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
five are Veritas working correctly. Each is an `EndedBy` member the branch below names,
and the two that look alike from outside — a refusal with no statement is either of the
middle two — are told apart here, where the difference is known.

**A provider that will not answer is the sixth way and is deliberately not one of
them.** A missing key, a timeout or a reply that is not JSON raises `LanguageModelError`
out of here, because *"this question cannot be answered"* and *"this installation cannot
reach a model"* are different sentences and only the first is about the question.
"""

from collections.abc import Mapping
from dataclasses import replace
from time import perf_counter

from veritas.llm import LanguageModel, ModelCall
from veritas.orchestrator.answer import EndedBy, GroundedAnswer, Lineage
from veritas.orchestrator.generate import (
    DEFAULT_PROMPT_FORM,
    PromptForm,
    generate,
)
from veritas.orchestrator.rewrite import rewrite
from veritas.retrieval import TOP_K, RetrievalStrategy, Retriever
from veritas.semantic import MetricDefinition, SemanticEntry
from veritas.validation import (
    ACCESS_AXIS,
    ANALYST,
    AccessProfile,
    ValidationGate,
    ValidationGateOutcome,
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

    `strategy` and `prompt_form` are held here rather than passed per question because a
    comparison across Retrieval Strategies or across generation prompts varies the
    Orchestrator and not the question, and every Orchestrator built over one Retriever
    shares its indexes.

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
        prompt_form: PromptForm = DEFAULT_PROMPT_FORM,
    ) -> None:
        self.warehouse = warehouse
        self.gate = ValidationGate(warehouse) if gate is None else gate
        self.retriever = (
            Retriever(self.gate.semantic) if retriever is None else retriever
        )
        self.model = model
        self.strategy = strategy
        self.top_k = top_k
        self.prompt_form = prompt_form

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
        """Run one question through the flow, and say what came of it and what it took.

        The Access Profile is an argument for the reason it is one on
        `ValidationGate.judge`: it is the identity a **question** is asked as, so one
        Orchestrator serves many identities. There is no default identity beyond the one
        Access Profile this slice declares.

        The clock is here rather than in each branch because what a person waited is one
        measurement whichever way the question ended, and a Grounded Answer that has to
        be timed by its caller is one every caller times differently.
        """
        started = perf_counter()
        answered = self._answered(question, access_profile)
        return replace(answered, seconds=perf_counter() - started)

    def _answered(
        self, question: str, access_profile: AccessProfile
    ) -> GroundedAnswer:
        """The flow itself: the six endings, and the model calls each one has made by
        the time it is reached."""
        resolved = rewrite(question, self.model, self.gate.semantic)
        calls: tuple[ModelCall, ...] = resolved.calls
        if not resolved.resolved:
            return GroundedAnswer(
                question=question,
                ended_by=EndedBy.REWRITE,
                rewritten=resolved.rewritten,
                clarifying_question=resolved.clarifying_question,
                calls=calls,
            )

        entries = self.grounded_entries(resolved.rewritten)
        terms = self.lineage_of(resolved.resolutions)
        if not any(isinstance(entry, MetricDefinition) for entry in entries):
            return GroundedAnswer(
                question=question,
                ended_by=EndedBy.RETRIEVAL,
                rewritten=resolved.rewritten,
                lineage=terms,
                refusal="nothing retrieved for this question defines a Certified "
                        "Metric, and Veritas answers only with those",
                calls=calls,
            )

        written = generate(
            resolved.rewritten, entries, access_profile, self.model, self.prompt_form
        )
        calls += written.calls
        if not written.sql:
            return GroundedAnswer(
                question=question,
                ended_by=EndedBy.GENERATION,
                rewritten=resolved.rewritten,
                lineage=terms,
                refusal=written.refusal,
                calls=calls,
            )

        outcome = self.gate.judge(written.sql, access_profile)
        if not outcome.allowed:
            return GroundedAnswer(
                question=question,
                ended_by=EndedBy.GATE,
                rewritten=resolved.rewritten,
                sql=written.sql,
                lineage=terms,
                outcome=outcome,
                refusal=outcome.explanation,
                calls=calls,
            )

        lineage = self.lineage_of(resolved.resolutions, outcome)
        try:
            columns, rows = self.warehouse.query_with_columns(written.sql)
        except WarehouseError as refused:
            return GroundedAnswer(
                question=question,
                ended_by=EndedBy.ENGINE,
                rewritten=resolved.rewritten,
                sql=written.sql,
                lineage=lineage,
                outcome=outcome,
                refusal=f"the Validation Gate allowed this statement and the engine "
                        f"would not run it: {refused}",
                calls=calls,
            )
        return GroundedAnswer(
            question=question,
            ended_by=EndedBy.ANSWER,
            rewritten=resolved.rewritten,
            sql=written.sql,
            columns=columns,
            rows=tuple(rows),
            lineage=lineage,
            outcome=outcome,
            calls=calls,
        )

    def lineage_of(
        self,
        resolutions: Mapping[str, tuple[str, ...]],
        outcome: ValidationGateOutcome | None = None,
    ) -> Lineage:
        """The entries an answer was built from: the Ambiguous Terms the rewrite step
        resolved, then what the allowed statement was composed from.

        The **verdict** decides the second half, which is
        [DEBT-034](../../.claude/docs/debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)
        paid. Until here it was `GROUNDED_FIELDS` — everything the model was shown — so
        an answer computed with `Gross Revenue` cited `Net Revenue` beside it, having
        been offered both and used one.

        A question that reached no allowing verdict is the terms alone: nothing ran, so
        nothing produced an answer. The resolved terms lead, because they are what turned
        the word the person typed into the metric that was computed, and they ground
        nothing themselves. Then what was computed, how it was sliced, and how its rows
        were reached — the order a reader checks an answer in.
        """
        semantic = self.gate.semantic
        entries: list[SemanticEntry] = [
            semantic.ambiguous_terms[name] for name in resolutions
        ]
        if outcome is not None:
            entries.extend(semantic.metrics[name] for name in outcome.metrics)
            entries.extend(semantic.dimensions[name] for name in outcome.dimensions)
            entries.extend(semantic.join_paths[name] for name in outcome.join_paths)
        return Lineage(tuple(entries))
