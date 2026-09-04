"""Scores generation over the Gold Question Set: Execution Accuracy and LLM-as-judge.

[`Execution Accuracy`](../../.claude/docs/glossary.md#a-the-system) is *"share of
generated queries whose result set matches the gold result. The primary correctness
measure — objective, unlike a judge's opinion"*, and LLM-as-judge is the second half of
[`Evaluation Measure`](../../.claude/docs/glossary.md#a-the-system)'s *"Execution
Accuracy and LLM-as-judge agreement for generation"*. Agreement is what a judge is
scored by here: an opinion is worth reporting only against the objective measure it
either tracks or does not.

**The whole flow answers each question, not `generate` alone.** A Gold Question whose
correct ending is a refusal or a Clarifying Question has no result set to compare, and
what it claims is that Veritas ends that way — which is the Orchestrator's outcome
rather than the generator's. So the unit scored is a `GroundedAnswer`, and the `EndedBy`
it carries says which step produced it, because a question that scores zero because the
Validation Gate refused a correct statement is not a generation failure and must not be
read as one. That taxonomy is the Orchestrator's — this component reads it and no longer
owns it, so what a sweep groups by and what Observability charts are one vocabulary.

**One row per prompt per model.** The two settings this sweep varies are the
[Zoomcamp criterion](../../.claude/docs/design/target-state.md#zoomcamp-criteria-map)'s
— *"Execution Accuracy across ≥2 prompts and ≥2 models"* — the two `PromptForm`s and
the two providers `veritas/llm/`'s registry holds.

**Every call here is real.** Unlike `retrieval.py`, which derives its rewrites from the
gold SQL and costs nothing, this sweep is the measure of what a model actually writes,
so `uv run python -m veritas.evaluation generation` spends a key and the Step Review
carries what one dated run of it printed.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from veritas.evaluation.gold import Expectation, GoldQuestion, same_result
from veritas.llm import LanguageModel, LanguageModelError, json_reply
from veritas.orchestrator import (
    EndedBy,
    GroundedAnswer,
    Orchestrator,
    PromptForm,
)
from veritas.retrieval import Retriever
from veritas.validation import ANALYST, AccessProfile, ValidationGate
from veritas.warehouse import WarehouseAdapter

# What the judge is told to do, ahead of the one answer it is shown. It grades the
# **statement**, never the number: comparing result sets is what Execution Accuracy
# already does exactly, and a judge asked to do it again would be that measure in prose
# rather than a second lens on it.
JUDGE_RULES = """\
You grade one answer a question-answering system gave, against what a correct answer
would have been. You never answer the question yourself.

Answer with one JSON object and nothing else:
  {"correct": true or false, "why": "<one sentence>"}

Correct means the system did what the question needed:
  - where a statement was expected, the statement it wrote computes the quantity that
    was asked for, over the rows that were asked about;
  - where the correct outcome was to refuse, it refused;
  - where the correct outcome was to ask which meaning was wanted, it asked.

Judge what the statement computes, not how it is written: a differently written
statement that computes the same thing over the same rows is correct. A statement that
computes a different quantity, covers a different period, or drops a restriction the
correct statement has, is not.\
"""


def ended_as(answer: GroundedAnswer) -> Expectation:
    """Which of a Grounded Answer's three endings this one is.

    The same three `Expectation` names a Gold Question is written with, so what the set
    claims and what came back are compared as one vocabulary rather than two.
    """
    if answer.clarifying_question is not None:
        return Expectation.CLARIFYING_QUESTION
    if answer.refusal:
        return Expectation.REFUSAL
    return Expectation.ANSWER


def correctly_answered(gold: GoldQuestion, answer: GroundedAnswer) -> bool:
    """Whether Veritas answered this Gold Question the way the set says it should.

    The ending first, then — where that ending is a number — the result set, under the
    tolerance the Gold Question Set's own constraints were built against. A question
    that should have been refused and was answered is wrong however good the number is,
    which is the whole reason a refusal is a Gold Question at all.
    """
    if ended_as(answer) is not gold.expects:
        return False
    return same_result(gold.result, answer.rows) if gold.answerable else True


@dataclass(frozen=True, slots=True)
class Scored:
    """One Gold Question, run past one model under one prompt, and what came of it.

    `answer` is `None` exactly when `ended_by` is `PROVIDER`: there is no Grounded
    Answer, because the call raised instead of returning one.
    """

    gold: GoldQuestion
    ended_by: EndedBy
    correct: bool
    answer: GroundedAnswer | None = None
    judged: bool | None = None
    """The judge's verdict, or `None` where no judge ran or it gave no usable one."""

    provider_error: str = ""
    """What the provider said when the call did not come back, empty otherwise.

    Carried for the same reason a refusal's sentence is: a row with no Grounded Answer
    says nothing about the question and everything about the installation, and a sweep
    whose every row ended this way has to say why before a reader can act on it.
    """

    @property
    def agrees(self) -> bool | None:
        """Whether the judge and Execution Accuracy said the same thing about this one."""
        return None if self.judged is None else self.judged == self.correct


@dataclass(frozen=True, slots=True)
class GenerationMeasures:
    """The Evaluation Measures for generation under one prompt and one model.

    The scored questions are kept rather than reduced to rates, because the rates are
    over three different denominators — every question ends somewhere, not every
    question has a result set to compare, and not every question gets a usable verdict
    from the judge — and a rate whose denominator has been thrown away cannot be read.
    """

    prompt_form: PromptForm
    model: str
    scored: tuple[Scored, ...]

    @property
    def questions(self) -> int:
        """How many Gold Questions this row was measured over."""
        return len(self.scored)

    @property
    def right_ending(self) -> tuple[int, int]:
        """How many questions ended the way the set says, out of how many were asked."""
        return sum(one.correct for one in self.scored), self.questions

    @property
    def executed(self) -> tuple[Scored, ...]:
        """The questions Execution Accuracy is computed over — those with a gold result."""
        return tuple(one for one in self.scored if one.gold.answerable)

    @property
    def execution_accuracy(self) -> float:
        """The share of those whose result set matches the gold result."""
        executed = self.executed
        return sum(one.correct for one in executed) / len(executed) if executed else 0.0

    @property
    def judged(self) -> tuple[Scored, ...]:
        """The questions the judge returned a usable verdict on."""
        return tuple(one for one in self.scored if one.judged is not None)

    @property
    def judge_agreement(self) -> float:
        """The share of those where the judge and Execution Accuracy said the same thing."""
        judged = self.judged
        return sum(one.agrees for one in judged) / len(judged) if judged else 0.0

    @property
    def failed(self) -> tuple[Scored, ...]:
        """The questions this row got wrong, in the order they were asked."""
        return tuple(one for one in self.scored if not one.correct)

    @property
    def unreached(self) -> tuple[Scored, ...]:
        """The questions whose model call never came back, so this row measured less
        than it set out to."""
        return tuple(one for one in self.scored if one.ended_by is EndedBy.PROVIDER)


def judgement_text(gold: GoldQuestion, answer: GroundedAnswer) -> str:
    """What the judge is shown about one question: what was asked, what a correct answer
    is, and what Veritas did.

    The two result sets are deliberately absent. A judge shown them would be asked to
    compare numbers, which `same_result` already does exactly and without an opinion,
    and the agreement between the two measures would then be a measure of nothing.
    """
    ending = ended_as(answer)
    if ending is Expectation.ANSWER:
        did = f"wrote this statement:\n{answer.sql}"
    elif ending is Expectation.REFUSAL:
        did = f"refused, saying: {answer.refusal}"
    else:
        did = f"asked back: {answer.clarifying_question}"
    correct = (
        f"A correct answer computes this statement:\n{gold.sql}"
        if gold.answerable
        else f"A correct answer is {gold.expects}, and nothing else."
    )
    return "\n\n".join([
        f"The question asked: {gold.question}",
        correct,
        f"The system {did}",
    ])


def judgement_of(reply: str) -> bool | None:
    """The verdict in the judge's reply, or `None` if it gave none.

    A reply with no boolean `correct` in it is a judge that abstained rather than one
    that disagreed, and it is left out of the agreement rather than counted against
    either side. A reply that is not a JSON object at all raises through `json_reply`,
    because that is the provider failing.
    """
    verdict = json_reply(reply).get("correct")
    return verdict if isinstance(verdict, bool) else None


def judge(
    gold: GoldQuestion, answer: GroundedAnswer, model: LanguageModel
) -> bool | None:
    """One judge's opinion of one answer, or `None` where it gave no usable one."""
    return judgement_of(
        model.complete(JUDGE_RULES, judgement_text(gold, answer), json_object=True).text
    )


def score(
    gold: GoldQuestion,
    orchestrator: Orchestrator,
    judge_model: LanguageModel | None = None,
    access_profile: AccessProfile = ANALYST,
) -> Scored:
    """Ask one Gold Question and say what came of it, judged as well where a judge is given.

    A provider that will not answer is caught here and nowhere deeper. `flow.py` raises
    `LanguageModelError` on purpose — *"this question cannot be answered"* and *"this
    installation cannot reach a model"* are different sentences — and a sweep of two
    hundred calls that lost every earlier row to one timeout would be a measurement
    nobody could take. So it becomes a row of its own, scored wrong and named as
    unreached, and the runner says how many there were and fails the run.

    A judge that will not answer is the smaller case and joins the judge that abstained:
    the question keeps the objective verdict it already has and drops out of the
    agreement, whose denominator is printed beside it.
    """
    try:
        answer = orchestrator.answer(gold.question, access_profile)
    except LanguageModelError as error:
        return Scored(gold, EndedBy.PROVIDER, correct=False, provider_error=str(error))

    correct = correctly_answered(gold, answer)
    verdict = None
    if judge_model is not None:
        try:
            verdict = judge(gold, answer, judge_model)
        except LanguageModelError:
            verdict = None
    return Scored(gold, answer.ended_by, correct, answer, verdict)


def answerable_by_veritas(
    gold: GoldQuestion, gate: ValidationGate, access_profile: AccessProfile = ANALYST
) -> bool:
    """Whether the statement this Gold Question calls correct is one Veritas may run.

    A Gold Question whose **own gold SQL** the Validation Gate refuses cannot be
    answered by any model however well it writes, so scoring it would report a Gate
    limitation as a generation failure. It is left out of the sweep and named by the
    runner instead — which is
    [DEBT-035](../../.claude/docs/debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)'s
    cost, paid in the one place it would otherwise be invisible.

    Derived rather than listed: nothing here names a question, so the day the Gate stops
    refusing that statement the exclusion disappears by itself.
    """
    return not gold.sql or gate.judge(gold.sql, access_profile).allowed


def measure_generation(
    questions: Sequence[GoldQuestion],
    warehouse: WarehouseAdapter,
    gate: ValidationGate,
    retriever: Retriever,
    models: Mapping[str, LanguageModel],
    prompt_forms: Sequence[PromptForm] = tuple(PromptForm),
    judge_model: LanguageModel | None = None,
    access_profile: AccessProfile = ANALYST,
) -> list[GenerationMeasures]:
    """Every prompt against every model, over the same Gold Questions.

    One `Orchestrator` per cell, all of them over the one Retriever and the one Gate the
    caller built: an Orchestrator holds the prompt and the model, and rebuilding the
    indexes for each would cost more than every model call in the sweep.

    `models` is keyed by the label a table prints, so nothing here names a provider —
    that is `veritas/llm/`'s, and the registry it publishes is what the runner iterates.
    """
    return [
        GenerationMeasures(
            prompt_form,
            label,
            tuple(
                score(
                    gold,
                    Orchestrator(
                        warehouse,
                        model=model,
                        retriever=retriever,
                        gate=gate,
                        prompt_form=prompt_form,
                    ),
                    judge_model,
                    access_profile,
                )
                for gold in questions
            ),
        )
        for prompt_form in prompt_forms
        for label, model in models.items()
    ]


__all__ = [
    "JUDGE_RULES",
    "GenerationMeasures",
    "Scored",
    "answerable_by_veritas",
    "correctly_answered",
    "ended_as",
    "judge",
    "judgement_of",
    "judgement_text",
    "measure_generation",
    "score",
]
