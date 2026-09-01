"""What the rewrite step does with an Ambiguous Term, and what it refuses to do.

Three claims. The corpus claim: the model is shown the Semantic Layer's own words
about the terms the question said, and nothing else — no Warehouse schema, no
metric it was not asked about. The resolution claim: a meaning the question
names is used, and a meaning it does not name is asked back rather than guessed,
including when the model answers with something the term does not stand between.
And the **detection claim**: a question says a term when it says any spelling
[Glossary Section D](../.claude/docs/glossary.md#d-ambiguous-terms) registers for
it, the corpus and Section D register the same ones, and no Certified Metric claims
one of them as an alias.

That last claim is read against the Glossary here, in the package that acts on it,
rather than in `check_semantic_layer.py` — whose check 13 reads Section D's *Could
mean* column and whose check 14 forbids a metric alias that is a Section D **name**.
The *Also said as* column arrived after `.claude/scripts/` was frozen.

Every test here drives a stub model, so the suite needs no key and no network.
The one test that calls the configured provider spends real credit, so it runs
only when `VERITAS_LIVE_MODEL` says so — a key being present is not consent.
"""

import json
import os
import re

import pytest

from veritas.llm import LanguageModelError
from veritas.orchestrator import (
    PLACEHOLDER,
    Rewrite,
    ambiguous_terms_in,
    first_said,
    resolution_instruction,
    rewrite,
    said_as,
    spellings,
)

# One question per registered Ambiguous Term, as a person would type it. Each says
# exactly one term and does not say which meaning, which is the case Section D
# registers the term for.
ASKED = {
    "revenue": "what was our revenue last quarter",
    "volume": "what was the volume on EU accounts in March",
    "balance": "what is the balance on account ACC-0001",
    "P&L": "what is the P&L on our tech positions",
    "how much does X have": "how much does client 42 have",
}

# Calling a real provider costs money on a paid one and rate limit on a free one,
# and a key sitting in `.env` for the App to use is not permission to spend it. The
# live test is opt-in and names what it will do.
LIVE_VARIABLE = "VERITAS_LIVE_MODEL"

# A question about the brokerage that says no Ambiguous Term at all. Trade Count is
# a Certified Metric named outright, so there is nothing to resolve and nothing to
# ask a model.
UNAMBIGUOUS = "how many trades did we settle in March"

# One question per class of phrasing that is not the term's own name: morphology,
# orthography, another word for the same ambiguity, and a rewording of the one
# Section D row that is a phrase. Each says an Ambiguous Term the way a person does
# rather than the way the corpus files it, and each is now registered as a spelling
# of it — DEBT-029, paid.
SAID_ANOTHER_WAY = {
    "revenue": "what were our revenues last quarter",
    "P&L": "what is our PnL on tech positions",
    "volume": "what was turnover last month",
    "how much does X have": "how much is in account 41",
}

# Glossary Section D's fourth column, and where the cells are once a table row is
# split on its pipes: an empty cell 0 before the leading pipe, then the four
# columns. The separator is the Glossary's own, the same character its *Could mean*
# cells list meanings with.
SECTION_D = re.compile(r"^### D\. Ambiguous Terms\n(.*?)^### ", re.S | re.M)
SEPARATOR = "·"
USER_SAYS_COLUMN = 1
ALSO_SAID_COLUMN = 4

# What the placeholder is filled with when a registered phrase is turned back into a
# question. Any subject would do — the pattern does not read it.
SUBJECT = "account 12"


class StubModel:
    """A `LanguageModel` that answers with a fixed reply and records what it was asked."""

    def __init__(self, reply):
        self.reply = reply if isinstance(reply, str) else json.dumps(reply)
        self.calls: list[tuple[str, str, bool]] = []

    def complete(self, system: str, user: str, json_object: bool = False) -> str:
        self.calls.append((system, user, json_object))
        return self.reply


class UncalledModel:
    """A `LanguageModel` that fails the test if anything calls it."""

    def complete(self, system: str, user: str, json_object: bool = False) -> str:
        raise AssertionError("the model was called for a question with no Ambiguous Term")


def also_said_as(root) -> dict[str, list[str]]:
    """Glossary Section D's *Also said as* column, as {the term: its other spellings}.

    Read out of the Glossary rather than listed here, for the reason
    `check_semantic_layer.py` reads the *Could mean* column out of it: a list typed
    into this file would prove that this file and the corpus agree, and the claim is
    that the **Glossary** and the corpus agree.
    """
    section = SECTION_D.search((root / ".claude" / "docs" / "glossary.md").read_text())
    assert section, "no `### D. Ambiguous Terms` section in the Glossary"
    registered: dict[str, list[str]] = {}
    for line in section.group(1).splitlines():
        cells = line.split("|")
        if len(cells) <= ALSO_SAID_COLUMN:
            continue
        said = cells[USER_SAYS_COLUMN].strip().strip('"').strip()
        # The header row and the `|---|` rule beneath it are table furniture.
        if not said or said == "User says" or set(said) <= set("-: "):
            continue
        registered[said] = sorted(
            part.strip() for part in cells[ALSO_SAID_COLUMN].split(SEPARATOR)
            if part.strip()
        )
    return registered


def test_every_registered_ambiguous_term_has_a_question_here(semantic):
    """The set below covers Section D, so a sixth term fails rather than goes untested."""
    assert set(ASKED) == set(semantic.ambiguous_terms)


@pytest.mark.parametrize("name", sorted(ASKED))
def test_a_question_that_says_a_term_says_that_term_alone(name, semantic):
    """Each question is matched by its own term and by no other."""
    assert [term.name for term in ambiguous_terms_in(ASKED[name], semantic)] == [name]


def test_a_term_is_found_whatever_case_the_question_uses(semantic):
    """A person typing `Revenue` said the same word as one typing `revenue`."""
    found = ambiguous_terms_in("What Was Our Revenue Last Quarter", semantic)
    assert [term.name for term in found] == ["revenue"]


def test_a_placeholder_stands_for_the_subject_it_is_asked_about(semantic):
    """`how much does X have` matches whoever the question is about."""
    assert said_as("how much does X have").search("how much does ACC-0001 have")
    assert not said_as("how much does X have").search("how much does have")


def test_a_question_with_no_ambiguous_term_calls_no_model(semantic):
    """No term to resolve is no model call — which is also what makes it free."""
    resolved = rewrite(UNAMBIGUOUS, model=UncalledModel(), layer=semantic)
    assert resolved == Rewrite(UNAMBIGUOUS, UNAMBIGUOUS, {}, None)
    assert resolved.resolved


@pytest.mark.parametrize("name", sorted(SAID_ANOTHER_WAY))
def test_a_phrasing_that_is_not_the_registered_name_is_detected(name, semantic):
    """[DEBT-029](../.claude/docs/debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently),
    paid: the question is asked back about rather than answered silently.

    The four classes the entry named, each said as a person says it and each
    reaching the term the corpus files under another word.
    """
    question = SAID_ANOTHER_WAY[name]
    assert [term.name for term in ambiguous_terms_in(question, semantic)] == [name]
    asked = rewrite(question, StubModel({name: None}), semantic)
    assert not asked.resolved
    assert asked.rewritten == question
    print(f"\n  {question}\n    says {name!r} -> {asked.clarifying_question}")


def test_every_registered_spelling_finds_its_own_term(semantic):
    """A spelling nothing can match is a phrasing registered and still missed.

    The guard that makes the four classes above four *examples* rather than the
    whole claim: every name and every alias in the corpus is put back into a
    question and must find the entry it was read from — which is also what catches a
    pattern built wrong for a shape the corpus adds later.
    """
    for term in semantic.ambiguous_terms.values():
        for spelling in spellings(term):
            question = f"tell me about {PLACEHOLDER.sub(SUBJECT, spelling)} this month"
            assert term in ambiguous_terms_in(question, semantic), (
                f"{term.name}: the registered spelling {spelling!r} finds nothing"
            )


def test_section_d_and_the_corpus_register_the_same_spellings(root, semantic):
    """The Glossary's *Also said as* cells are the entries' `aliases`, both ways.

    The words are Section D's, and an alias in the corpus that Section D does not
    carry is a phrasing Veritas acts on and nobody agreed.
    """
    registered = also_said_as(root)
    assert set(registered) == set(semantic.ambiguous_terms)
    assert registered == {
        name: sorted(term.aliases)
        for name, term in semantic.ambiguous_terms.items()
    }


def test_no_certified_metric_claims_a_registered_spelling(semantic):
    """An alias that is also a Section D spelling answers what Section D says to ask.

    `check_semantic_layer.py`'s check 14 forbids a metric alias that is a Section D
    *name*; this is the same rule over the *Also said as* column, and it is what
    moved "turnover" off `Traded Notional` when it became a spelling of "volume".
    """
    said = {
        spelling.casefold(): term.name
        for term in semantic.ambiguous_terms.values()
        for spelling in spellings(term)
    }
    claimed = {
        alias.casefold(): metric.name
        for metric in semantic.metrics.values()
        for alias in metric.aliases
    }
    collisions = sorted(set(said) & set(claimed))
    assert not collisions, "\n".join(
        f"{claimed[alias]} claims the alias {alias!r}, which Section D registers as "
        f"a spelling of {said[alias]!r} — a word the corpus must ask about"
        for alias in collisions
    )


def test_the_instruction_names_the_spelling_the_question_used(semantic):
    """The answer is keyed by the registered name, so the model is told which word it is.

    Only where the two differ: a question that says the registered name produces the
    instruction it always did, which is what `test_the_model_is_asked_for_json_and_
    given_the_question_verbatim` holds it to.
    """
    question = SAID_ANOTHER_WAY["volume"]
    said = resolution_instruction(ambiguous_terms_in(question, semantic), question)
    assert 'Term: "volume"' in said
    assert 'the question says it as: "turnover"' in said


def test_the_clarifying_question_quotes_the_words_the_question_used(semantic):
    """A person who typed "turnover" is asked about "turnover", not about `volume`.

    The entry's name is what the corpus files it under and is not a word the person
    has seen; the meanings are the entry's, because that is what the two spellings
    share.
    """
    asked = rewrite("what was turnover last month", StubModel({"volume": None}), semantic)
    assert not asked.resolved
    assert '"turnover"' in asked.clarifying_question
    assert "volume" not in asked.clarifying_question
    for meaning in semantic.ambiguous_terms["volume"].disambiguates:
        assert meaning in asked.clarifying_question


def test_a_question_that_names_a_meaning_resolves_to_it(semantic):
    """`gross revenue` says which of the two, so the question is answerable as asked."""
    model = StubModel({"revenue": "Gross Revenue"})
    resolved = rewrite("what was our gross revenue last quarter", model, semantic)
    assert resolved.resolutions == {"revenue": ("Gross Revenue",)}
    assert resolved.clarifying_question is None
    assert resolved.resolved
    assert "Gross Revenue" in resolved.rewritten
    assert resolved.rewritten.startswith(resolved.question)


@pytest.mark.parametrize("name", sorted(ASKED))
def test_a_term_the_question_leaves_open_is_asked_back(name, semantic):
    """Every one of the five, unresolved, comes back as a question naming both meanings.

    The word quoted back is the one the question used, which for the phrase row is
    the phrase with its subject in it rather than with the registered `X`.
    """
    model = StubModel({name: None})
    asked = rewrite(ASKED[name], model, semantic)
    assert not asked.resolved
    assert asked.resolutions == {}
    assert asked.rewritten == asked.question
    said = first_said(semantic.ambiguous_terms[name], asked.question)
    assert f'"{said.group(0)}"' in asked.clarifying_question
    for meaning in semantic.ambiguous_terms[name].disambiguates:
        assert meaning in asked.clarifying_question


def test_a_meaning_the_term_does_not_stand_between_is_not_a_resolution(semantic):
    """A certified metric is not an available answer unless the term names it."""
    asked = rewrite(ASKED["revenue"], StubModel({"revenue": "Traded Notional"}), semantic)
    assert asked.resolutions == {}
    assert not asked.resolved
    assert "Traded Notional" not in asked.clarifying_question


def test_an_invented_meaning_is_not_a_resolution(semantic):
    """The guard is the corpus, not the plausibility of the string."""
    asked = rewrite(ASKED["revenue"], StubModel({"revenue": "Total Revenue"}), semantic)
    assert asked.resolutions == {}
    assert not asked.resolved


def test_a_question_that_asks_for_both_resolves_to_both(semantic):
    """`P&L` has three answers, and the third is two Certified Metrics rather than one."""
    both = ["Realised P&L", "Unrealised P&L"]
    resolved = rewrite("what is my P&L, split banked and open", StubModel({"P&L": both}), semantic)
    assert resolved.resolutions == {"P&L": tuple(both)}
    assert resolved.resolved
    assert all(meaning in resolved.rewritten for meaning in both)


def test_two_terms_in_one_question_are_asked_about_in_the_order_asked(semantic):
    """A partly-resolved question asks back about what is left, and keeps what was resolved."""
    question = "what was our revenue and volume last quarter"
    assert [term.name for term in ambiguous_terms_in(question, semantic)] == [
        "revenue", "volume",
    ]
    model = StubModel({"revenue": "Net Revenue", "volume": None})
    asked = rewrite(question, model, semantic)
    assert asked.resolutions == {"revenue": ("Net Revenue",)}
    assert not asked.resolved
    assert "volume" in asked.clarifying_question
    assert '"revenue" could mean' not in asked.clarifying_question


def test_a_reply_that_is_not_a_json_object_is_the_provider_failing(semantic):
    """Not an ambiguity — a caller must be able to tell the two apart."""
    for reply in ("I think you mean gross.", "[1, 2]", '"Gross Revenue"'):
        with pytest.raises(LanguageModelError):
            rewrite(ASKED["revenue"], StubModel(reply), semantic)


def test_a_reply_in_a_code_fence_is_still_read(semantic):
    """An open model behind the same endpoint fences what a hosted one returns bare."""
    fenced = '```json\n{"revenue": "Net Revenue"}\n```'
    resolved = rewrite(ASKED["revenue"], StubModel(fenced), semantic)
    assert resolved.resolutions == {"revenue": ("Net Revenue",)}


def test_the_model_is_asked_for_json_and_given_the_question_verbatim(semantic):
    """The question reaches the model as it was typed, never as something rephrased."""
    model = StubModel({"revenue": None})
    rewrite(ASKED["revenue"], model, semantic)
    [(system, user, json_object)] = model.calls
    assert user == ASKED["revenue"]
    assert json_object is True
    said = ambiguous_terms_in(ASKED["revenue"], semantic)
    assert system == resolution_instruction(said, ASKED["revenue"])
    # The question says the term as it is registered, so the instruction is the one a
    # question with no alias in it has always produced.
    assert system == resolution_instruction(said)


def test_the_instruction_carries_the_terms_own_words(semantic):
    """The rule the model applies is the corpus's, not one written into this package."""
    term = semantic.ambiguous_terms["revenue"]
    said = resolution_instruction([term])
    assert "Ask, unless the question names one" in said
    assert "Gross Revenue is Commission before Rebate and Fee" in said
    for meaning in term.disambiguates:
        assert meaning in said


def test_the_instruction_offers_no_metric_the_question_did_not_ask_about(semantic):
    """The options are closed: only the terms said, and only their own meanings."""
    said = resolution_instruction(ambiguous_terms_in(ASKED["revenue"], semantic))
    named = {
        metric
        for metric in semantic.metrics
        if metric not in semantic.ambiguous_terms["revenue"].disambiguates
    }
    assert not [metric for metric in named if metric in said]


def test_the_instruction_carries_no_warehouse_schema(semantic):
    """[ADR-0001](../.claude/docs/adr/0001-semantic-layer-as-the-retrieval-corpus.md)'s
    corpus claim reaches the prompt: the model is grounded in Semantic Entries.
    """
    said = resolution_instruction(list(semantic.ambiguous_terms.values()))
    assert "fct_" not in said
    assert "dim_" not in said


@pytest.mark.skipif(
    not os.environ.get(LIVE_VARIABLE),
    reason=f"spends a real key: set {LIVE_VARIABLE}=1 to run it",
)
def test_the_configured_model_reads_the_corpus_rule(semantic):
    """The live path, against whichever of the two providers the environment names.

    Two calls, and the pair is the point: a model that reads the rule resolves the
    question that names a meaning and asks back about the one that does not. A model
    that guesses passes the first and fails the second.
    """
    resolved = rewrite("what was our gross revenue in March", layer=semantic)
    assert resolved.resolutions == {"revenue": ("Gross Revenue",)}
    asked = rewrite(ASKED["revenue"], layer=semantic)
    assert not asked.resolved
