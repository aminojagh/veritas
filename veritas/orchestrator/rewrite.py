"""Resolves the Ambiguous Terms a question says, before anything searches for it.

Step 1 of the [Target State's flow](../../.claude/docs/design/target-state.md#flow)
— *"resolve Ambiguous Terms against the Semantic Layer. 'revenue' is not
answerable — ask which, or use the one the question actually names"* — and the
first place Veritas calls a model.

**Three jobs, and only the middle one is the model's.** Which Ambiguous Terms a
question says is decided here, by matching the spellings
[Glossary Section D](../../.claude/docs/glossary.md#d-ambiguous-terms) registers —
the *User says* cell and every *Also said as* cell beside it, which reach an entry
as its `name` and its `aliases` and are matched the same way.
Which certified meaning the question's own words name is decided by the model,
which is given those terms' own `description` and `resolution` text and nothing
else. Whether the model's answer counts is decided here again: a meaning outside
the `disambiguates` the term stands between is not a resolution, and an
unresolved term is asked back rather than guessed at.
"""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cache

from veritas.llm import LanguageModel, ModelCall, default_model, json_reply
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
    — the question carrying the meanings that were resolved, in whichever
    `RewriteForm` writes them, and the question itself where nothing was resolved.
    `resolutions` maps an Ambiguous Term's name to the Certified
    Metrics it resolved to, in the order the question says the terms.
    `clarifying_question` is the question Veritas asks back, and is `None` exactly when
    the question is ready to be retrieved for.
    `calls` is what asking cost — empty for a question that said no Ambiguous Term,
    because that one is resolved without a model.
    """

    question: str
    rewritten: str
    resolutions: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    clarifying_question: str | None = None
    calls: tuple[ModelCall, ...] = ()

    @property
    def resolved(self) -> bool:
        """Whether the flow may continue to Retrieval."""
        return self.clarifying_question is None


@cache
def said_as(spelling: str) -> re.Pattern[str]:
    r"""The pattern that finds one registered spelling of an Ambiguous Term.

    Whole words, any case, and a `X` in the spelling matches the subject it stands
    for. A spelling with no placeholder is one bounded literal — `revenue` becomes
    `\brevenue\b`, which finds *"our revenue last quarter"* and not `revenue` inside
    a longer word, so `revenues` is a spelling of its own rather than something this
    pattern stretches to. A spelling with the placeholder between two halves becomes
    those halves with the subject between them — `how much does X have` becomes
    `\bhow\ much\ does\s+(.+?)\s+have\b`, which finds *"how much does account 41
    have"*. A spelling that **ends** with the placeholder has nothing after the
    subject to close on, so it requires one without consuming it — `how much is in X`
    becomes `\bhow\ much\ is\ in(?=\s+\S)`, which finds *"how much is in ACC-0001"*
    where demanding whitespace after the subject would miss it, and does not find
    *"how much is in"* on its own.

    Whichever shape it is, the match spans the words the question used and no
    others, so a caller that asks a person about a term can quote them rather than
    quote the registry.
    """
    parts = [re.escape(part.strip()) for part in PLACEHOLDER.split(spelling)]
    trailing = not parts[-1]
    said = r"\b" + r"\s+(.+?)\s+".join(parts[:-1] if trailing else parts)
    return re.compile(said + (r"(?=\s+\S)" if trailing else r"\b"), re.IGNORECASE)


def spellings(term: AmbiguousTerm) -> tuple[str, ...]:
    """Every way Section D registers this term: its name, then its other spellings.

    One list rather than two, because an alias is not a lesser form of the term — a
    question that says *"turnover"* has said `volume`, and the only thing the name
    has that an alias does not is that it is what the corpus files the entry under.
    """
    return (term.name, *term.aliases)


def without_overlaps(found: Iterable[re.Match[str]]) -> list[re.Match[str]]:
    """Those of these matches that can all be written over, in question order.

    Two spellings of one term, or two terms, can match overlapping words of the same
    question, and writing over both would splice into text the first replacement had
    already removed. So a set of matches is reduced to non-overlapping ones before any
    of it is written.

    Earliest first, and the longer of two that begin together: a longer match spans more
    of the words the person used, and those words are exactly what a splice replaces and
    what a Clarifying Question quotes back.
    """
    kept: list[re.Match[str]] = []
    for match in sorted(found, key=lambda match: (match.start(), -match.end())):
        if not kept or match.start() >= kept[-1].end():
            kept.append(match)
    return kept


def said_throughout(term: AmbiguousTerm, question: str) -> list[re.Match[str]]:
    """Every mention of this term the question makes, in whichever spellings it used.

    Non-overlapping and in question order, so a caller may write over all of them.
    """
    return without_overlaps(
        match
        for spelling in spellings(term)
        for match in said_as(spelling).finditer(question)
    )


def first_said(term: AmbiguousTerm, question: str) -> re.Match[str] | None:
    """The question's first mention of this term, in whichever spelling it used.

    What the two callers that want one mention want: the resolution instruction naming
    the spelling the question used, and the Clarifying Question quoting it back.
    """
    said = said_throughout(term, question)
    return said[0] if said else None


def ambiguous_terms_in(question: str, layer: SemanticLayer) -> list[AmbiguousTerm]:
    """The Ambiguous Terms a question says, in the order it says them.

    Question order rather than corpus order, so a Clarifying Question asks about the
    words in the order the person wrote them.
    """
    said = [
        (match.start(), position, term)
        for position, term in enumerate(layer.ambiguous_terms.values())
        if (match := first_said(term, question))
    ]
    return [term for _, _, term in sorted(said, key=lambda found: found[:2])]


def resolution_instruction(terms: list[AmbiguousTerm], question: str = "") -> str:
    """The system instruction: the rules, then the terms the question said.

    Only the terms this question said, so the meanings on offer are the ones it
    could plausibly have meant and the model is never shown a metric it was not
    asked about.

    A term the question spelled some other way carries one line more, naming that
    spelling — the answer is still keyed by the registered name, and without the line
    the model would have to guess that the `volume` it is asked about is the
    *"turnover"* in front of it. A term said as it is registered carries no such
    line, so the instruction for a question that says one is the text it always was.
    """
    blocks = [
        "\n".join([
            f'Term: "{term.name}"',
            *(
                [f'  the question says it as: "{said.group(0)}"']
                if (said := first_said(term, question))
                and said.group(0).casefold() != term.name.casefold()
                else []
            ),
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


def clarifying_question_for(terms: list[AmbiguousTerm], question: str) -> str:
    """The question Veritas asks back about the terms that stayed unresolved.

    Each term is quoted as the question spelled it rather than as the corpus files
    it, so a person who typed *"turnover"* is asked about "turnover" and not about
    the `volume` entry they have never seen. The meanings on offer are the entry's,
    because those are what the two spellings share.
    """
    asked = "; ".join(
        f'"{said.group(0) if (said := first_said(term, question)) else term.name}"'
        f" could mean " + " or ".join(term.disambiguates)
        for term in terms
    )
    return f"{asked}. Which do you mean?"


class RewriteForm(StrEnum):
    """How a resolved meaning is written into the question Retrieval searches with.

    The two forms
    [DEBT-030](../../.claude/docs/debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it)
    was opened to have measured against each other. `DEFAULT_REWRITE_FORM` is which
    one `rewrite` uses.
    """

    APPENDED = "appended"
    """The person's words intact, with the certified names in a parenthesis after
    them: *"what was our gross revenue last quarter (revenue means Gross Revenue)"*."""

    SPLICED = "spliced"
    """The certified names written over the words that were ambiguous: *"what was our
    gross Gross Revenue last quarter"*. Shorter, and it doubles the cue where the
    question already carried it."""


# Which form `rewrite` writes, and therefore which one every Retrieval Strategy
# searches with. Measured rather than chosen: `veritas/evaluation/retrieval.py` scores
# both over the Gold Question Set, and the Step Review that set this line carries the
# numbers and the losing form.
DEFAULT_REWRITE_FORM = RewriteForm.SPLICED


def appended_with(
    question: str, resolutions: Mapping[str, tuple[str, ...]], layer: SemanticLayer
) -> str:
    """The question, then the meanings that were resolved, in a parenthesis.

    `layer` is unread — an appended clause names the registered term rather than the
    spelling the question used, so nothing here has to find the words again. It is in
    the signature because `REWRITE_FORMS` dispatches both forms through one shape.
    """
    if not resolutions:
        return question
    named = "; ".join(
        f"{term} means {' and '.join(metrics)}"
        for term, metrics in resolutions.items()
    )
    return f"{question.rstrip()} ({named})"


def spliced_with(
    question: str, resolutions: Mapping[str, tuple[str, ...]], layer: SemanticLayer
) -> str:
    """The question with every resolved term's own words replaced by its meanings.

    Right to left, so replacing one mention does not move the next one's position, and
    **every** mention: a question that says one term twice — *"revenue last quarter
    against revenue this quarter"* — would otherwise keep the second, and an ambiguous
    word left in the question is the cue resolving it was supposed to remove.

    The mentions of all the resolved terms are reduced together rather than term by
    term, because two terms can claim overlapping words as readily as two spellings of
    one can.

    A spelling that stands for a phrase about a subject captures that subject —
    `how much does X have` matches all of *"how much does account 12 have"* — and the
    subject is written back after the meanings, because it is the question's own words
    and not the term's. *"how much does account 12 have"* resolved to `Cash Balance`
    splices to *"Cash Balance account 12"*, which is clumsy; dropping the subject
    would lose which account was asked about, which is worse.
    """
    meant = {
        match: metrics
        for term_name, metrics in resolutions.items()
        if (term := layer.ambiguous_terms.get(term_name))
        for match in said_throughout(term, question)
    }
    spliced = question
    for match in sorted(without_overlaps(meant), key=lambda match: -match.start()):
        spliced = (
            spliced[:match.start()]
            + " ".join([" and ".join(meant[match]), *match.groups()])
            + spliced[match.end():]
        )
    return spliced


# Which function writes each form. A dispatch table rather than a match, because the
# sweep that chose between them iterates it.
REWRITE_FORMS = {
    RewriteForm.APPENDED: appended_with,
    RewriteForm.SPLICED: spliced_with,
}


def rewritten_with(
    question: str,
    resolutions: Mapping[str, tuple[str, ...]],
    layer: SemanticLayer,
    form: RewriteForm = DEFAULT_REWRITE_FORM,
) -> str:
    """The question as Retrieval will search for it, in whichever form is asked for."""
    write = REWRITE_FORMS[form]
    return write(question, resolutions, layer)


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
    reply = model.complete(
        resolution_instruction(terms, question), question, json_object=True
    )
    resolved = resolutions_in(reply.text, terms)
    unresolved = [term for term in terms if term.name not in resolved]
    if unresolved:
        return Rewrite(
            question,
            question,
            resolved,
            clarifying_question_for(unresolved, question),
            (reply.call,),
        )
    return Rewrite(
        question, rewritten_with(question, resolved, layer), resolved, calls=(reply.call,)
    )


def _flat(text: str) -> str:
    """One line of a corpus field that was written as several."""
    return " ".join(text.split())
