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

from veritas.llm import LIVE_VARIABLE, LanguageModelError
from veritas.orchestrator import (
    DEFAULT_REWRITE_FORM,
    PLACEHOLDER,
    REWRITE_FORMS,
    Rewrite,
    RewriteForm,
    ambiguous_terms_in,
    first_said,
    resolution_instruction,
    rewrite,
    rewritten_with,
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
# live test is opt-in and names what it will do — `LIVE_VARIABLE` is that name, and it
# is `veritas/llm/`'s because it is a fact about spending a key.

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
    assert "last quarter" in resolved.rewritten, "the question's own words are gone"


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


@pytest.mark.parametrize("form", list(RewriteForm))
def test_every_rewrite_form_carries_every_resolved_meaning(form, semantic):
    """Whatever the form, the certified names are in the text Retrieval searches."""
    both = ("Realised P&L", "Unrealised P&L")
    written = rewritten_with(
        "what is our P&L on tech", {"P&L": both}, semantic, form
    )
    assert all(meaning in written for meaning in both)
    assert "tech" in written, "the words that were not the term are gone"


def test_the_appended_form_leaves_the_question_it_was_given_intact(semantic):
    """The person's words, then the meanings — which is what makes it auditable."""
    written = rewritten_with(
        "what was our gross revenue last quarter",
        {"revenue": ("Gross Revenue",)},
        semantic,
        RewriteForm.APPENDED,
    )
    assert written == (
        "what was our gross revenue last quarter (revenue means Gross Revenue)"
    )


def test_the_spliced_form_writes_the_meaning_over_the_words_that_were_ambiguous(semantic):
    """The shorter sentence, and the doubled cue where the question already carried it."""
    written = rewritten_with(
        "what was our gross revenue last quarter",
        {"revenue": ("Gross Revenue",)},
        semantic,
        RewriteForm.SPLICED,
    )
    assert written == "what was our gross Gross Revenue last quarter"


@pytest.mark.parametrize(
    "question", ["how much does account 12 have", "how much is in account 12"]
)
def test_the_spliced_form_keeps_the_subject_the_spelling_captured(question, semantic):
    """`how much does X have` is a phrase about a subject, and the subject is the
    question's own words rather than the term's.

    Two spellings, one sentence, by different routes: the registered one captures
    `account 12` between its halves and the splice writes it back after the meaning,
    and the alias that ends in the placeholder never consumes it, so it is already
    where the splice leaves off.
    """
    assert rewritten_with(
        question,
        {"how much does X have": ("Cash Balance",)},
        semantic,
        RewriteForm.SPLICED,
    ) == "Cash Balance account 12"


def test_the_spliced_form_writes_every_meaning_a_term_resolved_to(semantic):
    """A term resolved to both of its meanings writes both, joined as a person joins
    them, and over the words the question used — *"PnL"*, a registered spelling of `P&L`,
    rather than the name the corpus files it under."""
    assert rewritten_with(
        "what is our PnL on tech",
        {"P&L": ("Realised P&L", "Unrealised P&L")},
        semantic,
        RewriteForm.SPLICED,
    ) == "what is our Realised P&L and Unrealised P&L on tech"


def test_the_spliced_form_writes_the_meanings_before_the_captured_subject(semantic):
    """Both halves of the splice in one question: every meaning, then the subject the
    phrase was about."""
    assert rewritten_with(
        "how much does client 42 hold",
        {"how much does X have": ("Cash Balance", "Account Value")},
        semantic,
        RewriteForm.SPLICED,
    ) == "Cash Balance and Account Value client 42"


def test_the_spliced_form_writes_every_resolved_term_from_the_right(semantic):
    """Two terms in one question, the first of them a phrase whose splice is shorter than
    the words it replaces — so a left-to-right pass would cut the second term at
    coordinates that had already moved."""
    assert rewritten_with(
        "how much does account 12 have and what was revenue",
        {"how much does X have": ("Account Value",), "revenue": ("Net Revenue",)},
        semantic,
        RewriteForm.SPLICED,
    ) == "Account Value account 12 and what was Net Revenue"


def test_the_spliced_form_writes_over_the_words_in_the_case_they_were_typed(semantic):
    """Detection ignores case, so the splice replaces what was matched rather than the
    registered spelling: a shouted word goes the way the rest of the match went."""
    assert rewritten_with(
        "what was REVENUE in March",
        {"revenue": ("Gross Revenue",)},
        semantic,
        RewriteForm.SPLICED,
    ) == "what was Gross Revenue in March"


def test_the_spliced_form_writes_over_every_mention_of_a_term(semantic):
    """A term said twice is written over twice: an ambiguous word left in the question is
    the cue resolving it was supposed to remove.

    Paid [DEBT-036](../.claude/docs/debt-ledger.md#debt-036--splicing-writes-over-the-first-mention-of-a-term-and-leaves-every-later-one),
    which pinned the first mention alone.
    """
    assert rewritten_with(
        "what was our revenue last quarter and our revenue this quarter",
        {"revenue": ("Gross Revenue",)},
        semantic,
        RewriteForm.SPLICED,
    ) == (
        "what was our Gross Revenue last quarter and our Gross Revenue this quarter"
    )


def test_the_spliced_form_writes_over_a_later_mention_in_another_spelling(semantic):
    """Every registered spelling counts as a mention, so a question that says the word
    once and an alias of it once has both written over — and neither replacement moves
    the other."""
    assert rewritten_with(
        "was our P&L better than our PnL last year",
        {"P&L": ("Realised P&L",)},
        semantic,
        RewriteForm.SPLICED,
    ) == "was our Realised P&L better than our Realised P&L last year"


def test_a_phrase_said_twice_is_written_over_twice_with_each_subject_kept(semantic):
    """Two mentions of the spelling that captures a subject, each keeping its own."""
    assert rewritten_with(
        "how much does account 12 have and how much does account 13 have",
        {"how much does X have": ("Cash Balance",)},
        semantic,
        RewriteForm.SPLICED,
    ) == "Cash Balance account 12 and Cash Balance account 13"


def test_two_terms_claiming_the_same_words_are_written_over_once(semantic):
    """`how much does X have` spans the subject it is about, and a second term can sit
    inside that subject — so both resolved, the shorter would splice into text the
    longer had already replaced.

    The longer match wins, because it spans more of the words the person used. The word
    it swallowed survives in the output as part of the subject, which is right: the
    subject is the question's own words and not the term's.
    """
    assert rewritten_with(
        "how much does the trading balance have",
        {"how much does X have": ("Account Value",), "balance": ("Cash Balance",)},
        semantic,
        RewriteForm.SPLICED,
    ) == "Account Value the trading balance"


def test_a_resolution_the_question_says_no_words_for_is_not_spliced_in(semantic):
    """The splice writes over words, so a resolution whose term the question never said —
    or whose name the Semantic Layer does not register at all — writes nothing rather
    than inventing somewhere to put it. Neither case reaches it from `rewrite`, which
    resolves only the terms a question says; the appended form, which never looks for the
    words, would write both.
    """
    for resolutions in (
        {"volume": ("Trade Count",)},
        {"not a registered term": ("Gross Revenue",)},
    ):
        assert rewritten_with(
            UNAMBIGUOUS, resolutions, semantic, RewriteForm.SPLICED
        ) == UNAMBIGUOUS


def test_a_question_that_resolved_nothing_is_itself_under_every_form(semantic):
    """No resolution, no rewrite — and the two forms cannot disagree about that."""
    assert {
        rewritten_with(UNAMBIGUOUS, {}, semantic, form) for form in RewriteForm
    } == {UNAMBIGUOUS}


def test_the_form_the_rewrite_step_writes_is_the_one_that_was_measured(semantic):
    """`DEFAULT_REWRITE_FORM` is the decision; `rewrite` is what acts on it."""
    assert set(REWRITE_FORMS) == set(RewriteForm)
    question = "what was our gross revenue last quarter"
    resolved = rewrite(question, StubModel({"revenue": "Gross Revenue"}), semantic)
    assert resolved.rewritten == rewritten_with(
        question, resolved.resolutions, semantic, DEFAULT_REWRITE_FORM
    )


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
