"""What `README.md` must be true about: every credential is listed, and the
access-control claim carries its qualification word for word.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
ENV_EXAMPLE = ROOT / ".env.example"
ADR_0002 = ROOT / ".claude" / "docs" / "adr" / "0002-duckdb-as-the-warehouse-behind-an-adapter.md"

# A variable is `NAME=` at the start of a line, live or commented out — `.env.example`
# declares its optional settings as comments so a reviewer uncomments rather than
# spells.
DECLARED = re.compile(r"^\s*#?\s*([A-Z][A-Z0-9_]*)=", re.M)

# A name the README could only mean as an environment variable: shouted, and with an
# underscore in it, so `SELECT` and `CREATE` are not read as configuration.
NAMED_IN_README = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")

# Scoped to this file and this document: the two shouted names `README.md` uses that
# `.env.example` does not declare, each with the reason it does not.
# `test_the_readme_exemptions_are_still_true` holds both reasons up to the code.
README_NOT_IN_ENV = {
    # Deliberately absent from `.env.example`, which says so: that file is read on
    # every run, and a key being present is not consent to spend it.
    "VERITAS_LIVE_MODEL",
    # A constant in the Orchestrator's prompt seam, not a setting anybody sets.
    "DEFAULT_PROMPT_FORM",
}


def normalised(text: str) -> str:
    """Markdown prose as one line, with block-quote markers off.

    Both documents state the access-control sentence as a block quote and wrap it at
    different widths, so neither the `>` nor the line breaks may count as a
    difference. Nothing else about the sentence may differ.
    """
    return " ".join(re.sub(r"^\s*>\s?", "", text, flags=re.M).split())


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text()


# -- the credential claim --------------------------------------------------------


def test_every_declared_variable_is_named_in_the_readme(readme):
    """Target State: *"`README.md` must list every credential Veritas touches"*."""
    declared = set(DECLARED.findall(ENV_EXAMPLE.read_text()))
    assert declared, "no variables read out of .env.example — the pattern has rotted"
    missing = {name for name in declared if name not in readme}
    assert not missing, (
        f".env.example declares {sorted(missing)} and README.md never names "
        f"{'it' if len(missing) == 1 else 'them'} — a reviewer meets the variable "
        f"first during bring-up, which is a reproducibility failure"
    )


def test_the_readme_names_no_variable_it_does_not_declare(readme):
    """The other direction: a README naming a setting no template ships is worse
    than one omitting it, because the reader goes looking for a field."""
    declared = set(DECLARED.findall(ENV_EXAMPLE.read_text()))
    undeclared = set(NAMED_IN_README.findall(readme)) - declared - README_NOT_IN_ENV
    assert not undeclared, (
        f"README.md names {sorted(undeclared)}, which .env.example does not declare "
        f"— add the field, or add the name to README_NOT_IN_ENV with its reason"
    )


def test_the_readme_exemptions_are_still_true():
    """Neither exemption above may become a magic name that excuses anything."""
    from veritas.llm import LIVE_VARIABLE
    from veritas.orchestrator import DEFAULT_PROMPT_FORM  # noqa: F401

    declared = set(DECLARED.findall(ENV_EXAMPLE.read_text()))
    assert LIVE_VARIABLE == "VERITAS_LIVE_MODEL" and LIVE_VARIABLE not in declared
    assert README_NOT_IN_ENV == {LIVE_VARIABLE, "DEFAULT_PROMPT_FORM"}


# -- the access-control claim ----------------------------------------------------


def test_the_readme_qualifies_access_control_in_the_adrs_own_words(readme):
    """[ADR-0002](../.claude/docs/adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md#consequences)
    names the sentence every access-control claim carries. The App renders the same one.
    """
    from veritas.app.render import ENFORCEMENT_NOTE

    sentence = normalised(ENFORCEMENT_NOTE)
    assert sentence in normalised(ADR_0002.read_text()), (
        "the sentence the App renders is no longer ADR-0002's — this test and "
        "tests/test_app.py disagree about which document is the source"
    )
    assert sentence in normalised(readme), (
        "README.md makes an access-control claim without ADR-0002's qualification, "
        "or with a paraphrase of it"
    )
