"""What the rewrite step does with an Ambiguous Term, and what it refuses to do.

Two claims. The corpus claim: the model is shown the Semantic Layer's own words
about the terms the question said, and nothing else — no Warehouse schema, no
metric it was not asked about. And the resolution claim: a meaning the question
names is used, and a meaning it does not name is asked back rather than guessed,
including when the model answers with something the term does not stand between.

Every test here drives a stub model, so the suite needs no key and no network.
The one test that calls the configured provider spends real credit, so it runs
only when `VERITAS_LIVE_MODEL` says so — a key being present is not consent.
"""

import json
import os

import pytest

from veritas.llm import LanguageModelError
from veritas.orchestrator import (
    Rewrite,
    ambiguous_terms_in,
    resolution_instruction,
    rewrite,
    said_as,
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

# One question per class of phrasing a registered term's own spelling does not
# match: morphology, orthography, an unregistered synonym, and a rewording of the
# one Section D row that is a phrase. Every one of them says an Ambiguous Term as a
# person would and is detected as saying none — DEBT-029, below.
UNSAID = {
    "revenue": "what were our revenues last quarter",
    "P&L": "what is our PnL on tech positions",
    "volume": "what was turnover last month",
    "how much does X have": "how much is in account 41",
}


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


@pytest.mark.parametrize("name", sorted(UNSAID))
def test_a_phrasing_that_is_not_the_registered_spelling_is_missed(name, semantic):
    """[DEBT-029](../.claude/docs/debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently):
    the question goes to Retrieval as though it had been unambiguous.

    Asserts what Veritas does today rather than what it should do — no term found,
    no model called, no clarification asked — so paying the debt breaks this test
    instead of passing quietly beside it.
    """
    question = UNSAID[name]
    assert name in semantic.ambiguous_terms
    assert ambiguous_terms_in(question, semantic) == []
    assert rewrite(question, UncalledModel(), semantic) == Rewrite(question, question)


def test_a_question_that_names_a_meaning_resolves_to_it(semantic):
    """`gross revenue` says which of the two, so the question is answerable as asked."""
    model = StubModel({"revenue": "Gross Revenue"})
    resolved = rewrite("what was our gross revenue last quarter", model, semantic)
    assert resolved.resolutions == {"revenue": ("Gross Revenue",)}
    assert resolved.clarification is None
    assert resolved.resolved
    assert "Gross Revenue" in resolved.rewritten
    assert resolved.rewritten.startswith(resolved.question)


@pytest.mark.parametrize("name", sorted(ASKED))
def test_a_term_the_question_leaves_open_is_asked_back(name, semantic):
    """Every one of the five, unresolved, comes back as a question naming both meanings."""
    model = StubModel({name: None})
    asked = rewrite(ASKED[name], model, semantic)
    assert not asked.resolved
    assert asked.resolutions == {}
    assert asked.rewritten == asked.question
    assert name in asked.clarification
    for meaning in semantic.ambiguous_terms[name].disambiguates:
        assert meaning in asked.clarification


def test_a_meaning_the_term_does_not_stand_between_is_not_a_resolution(semantic):
    """A certified metric is not an available answer unless the term names it."""
    asked = rewrite(ASKED["revenue"], StubModel({"revenue": "Traded Notional"}), semantic)
    assert asked.resolutions == {}
    assert not asked.resolved
    assert "Traded Notional" not in asked.clarification


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
    assert "volume" in asked.clarification
    assert '"revenue" could mean' not in asked.clarification


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
    assert system == resolution_instruction(ambiguous_terms_in(ASKED["revenue"], semantic))


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
