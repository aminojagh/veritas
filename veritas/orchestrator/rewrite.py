"""Resolves the Ambiguous Terms a question says, before anything searches for it.

Step 1 of the [Target State's flow](../../.claude/docs/design/target-state.md#flow)
— *"resolve Ambiguous Terms against the Semantic Layer. 'revenue' is not
answerable — ask which, or use the one the question actually names"* — and the
first place Veritas calls a model.

**Three jobs, and only the middle one is the model's.** Which Ambiguous Terms a
question says is decided here, by matching the names
[Glossary Section D](../../.claude/docs/glossary.md#d-ambiguous-terms) registers.
Which certified meaning the question's own words name is decided by the model,
which is given those terms' own `description` and `resolution` text and nothing
else. Whether the model's answer counts is decided here again: a meaning outside
the `disambiguates` the term stands between is not a resolution, and an
unresolved term is asked back rather than guessed at.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache

from veritas.llm import LanguageModel, default_model, json_reply
from veritas.semantic import AmbiguousTerm, SemanticLayer, load_semantic_layer

# The placeholder inside a registered term name. `how much does X have` is the one
# Section D row that is a phrase about a subject rather than a word, and `X` is
# where the subject goes. Word-bounded, so it is the standalone capital that is the
# placeholder: a term spelled with an `X` inside a word keeps its letters.
PLACEHOLDER = re.compile(r"\bX\b")

# What the model is told to do, ahead of the terms themselves. The rules are
# Veritas's; every word about a *meaning* below them comes out of the corpus.
RESOLUTION_RULES = """\
You resolve ambiguous words in questions about a brokerage, against a registry of
certified metrics. You never answer the question itself and you never compute
anything.

Answer with one JSON object and nothing else:
  - one key per term listed below, spelled exactly as the term is spelled there
  - the value is one of that term's certified meanings, spelled exactly as it is
    spelled there; or a list of them, where the question asks for more than one;
    or null
  - null means the question does not say which meaning it wants, and asking the
    person is then the correct outcome

Decide from the question's own words alone. Never pick the more common, more
likely or more useful meaning: a meaning the question does not name is null. A
name that is not listed under its term is not an available answer.\
"""


@dataclass(frozen=True, slots=True)
class Rewrite:
    """What the rewrite step made of a question.

    `question` is what was asked, verbatim. `rewritten` is what Retrieval searches
    — the question plus the meanings that were resolved, and the question itself
    where nothing was. `resolutions` maps an Ambiguous Term's name to the Certified
    Metrics it resolved to, in the order the question says the terms.
    `clarification` is the question Veritas asks back, and is `None` exactly when
    the question is ready to be retrieved for.
    """

    question: str
    rewritten: str
    resolutions: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    clarification: str | None = None

    @property
    def resolved(self) -> bool:
        """Whether the flow may continue to Retrieval."""
        return self.clarification is None


@cache
def said_as(name: str) -> re.Pattern[str]:
    r"""The pattern that finds one Ambiguous Term's name in a question.

    Whole words, any case, and a `X` in the name matches the subject it stands for.
    A name with no placeholder is one bounded literal — `revenue` becomes
    `\brevenue\b`, which finds *"our revenue last quarter"* and not `revenue` inside
    a longer word. A name with one becomes the two halves with the subject between
    them — `how much does X have` becomes `\bhow\ much\ does\s+(.+?)\s+have\b`, which
    finds *"how much does account 41 have"* and captures *"account 41"*.

    The match is literal, which is
    [DEBT-029](../../.claude/docs/debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently):
    a phrasing that is not the registered spelling is not detected, and is not
    detected silently.
    """
    parts = [re.escape(part.strip()) for part in PLACEHOLDER.split(name)]
    return re.compile(r"\b" + r"\s+(.+?)\s+".join(parts) + r"\b", re.IGNORECASE)


def ambiguous_terms_in(question: str, layer: SemanticLayer) -> list[AmbiguousTerm]:
    """The Ambiguous Terms a question says, in the order it says them.

    Question order rather than corpus order, so a clarification asks about the
    words in the order the person wrote them.
    """
    said = [
        (match.start(), position, term)
        for position, term in enumerate(layer.ambiguous_terms.values())
        if (match := said_as(term.name).search(question))
    ]
    return [term for _, _, term in sorted(said, key=lambda found: found[:2])]


def resolution_instruction(terms: list[AmbiguousTerm]) -> str:
    """The system instruction: the rules, then the terms the question said.

    Only the terms this question said, so the meanings on offer are the ones it
    could plausibly have meant and the model is never shown a metric it was not
    asked about.
    """
    blocks = [
        "\n".join([
            f'Term: "{term.name}"',
            "  certified meanings: "
            + " | ".join(f'"{name}"' for name in term.disambiguates),
            f"  what the ambiguity is: {_flat(term.description)}",
            f"  how to resolve it: {_flat(term.resolution)}",
        ])
        for term in terms
    ]
    return "\n\n".join([RESOLUTION_RULES, *blocks])


def resolutions_in(
    reply: str, terms: list[AmbiguousTerm]
) -> dict[str, tuple[str, ...]]:
    """The meanings in the model's reply that the terms actually stand between.

    A term the reply leaves out, nulls, or answers with a name outside its
    `disambiguates` is absent from the result — the three ways a term stays
    unresolved, and none of them is a reason to invent one. A reply that is not a
    JSON object at all raises through `json_reply`, because that is the provider
    failing rather than the question being ambiguous.
    """
    answer = json_reply(reply)
    resolved: dict[str, tuple[str, ...]] = {}
    for term in terms:
        chosen = answer.get(term.name)
        chosen = [chosen] if isinstance(chosen, str) else chosen
        if isinstance(chosen, list) and chosen and all(
            name in term.disambiguates for name in chosen
        ):
            resolved[term.name] = tuple(chosen)
    return resolved


def clarification_for(terms: list[AmbiguousTerm]) -> str:
    """The question Veritas asks back about the terms that stayed unresolved."""
    asked = "; ".join(
        f'"{term.name}" could mean ' + " or ".join(term.disambiguates)
        for term in terms
    )
    return f"{asked}. Which do you mean?"


def rewritten_with(question: str, resolutions: Mapping[str, tuple[str, ...]]) -> str:
    """The question with the meanings that were resolved named alongside it.

    Appended rather than spliced over the word, which is
    [DEBT-030](../../.claude/docs/debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it).
    """
    if not resolutions:
        return question
    named = "; ".join(
        f"{term} means {' and '.join(metrics)}"
        for term, metrics in resolutions.items()
    )
    return f"{question.rstrip()} ({named})"


def rewrite(
    question: str,
    model: LanguageModel | None = None,
    layer: SemanticLayer | None = None,
) -> Rewrite:
    """Resolve every Ambiguous Term the question says, or ask which was meant.

    A question that says none is returned unchanged and costs no model call at all.
    """
    layer = load_semantic_layer() if layer is None else layer
    terms = ambiguous_terms_in(question, layer)
    if not terms:
        return Rewrite(question, question)

    model = default_model() if model is None else model
    resolved = resolutions_in(
        model.complete(resolution_instruction(terms), question, json_object=True),
        terms,
    )
    unresolved = [term for term in terms if term.name not in resolved]
    if unresolved:
        return Rewrite(question, question, resolved, clarification_for(unresolved))
    return Rewrite(question, rewritten_with(question, resolved), resolved)


def _flat(text: str) -> str:
    """One line of a corpus field that was written as several."""
    return " ".join(text.split())
