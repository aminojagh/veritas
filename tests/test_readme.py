"""What `README.md` must be true about, since nothing else checks it.

`README.md` is the public face for Zoomcamp reviewers, and it is the one document
neither committed checker reads: `verify_framework.py` scans `.claude/docs/` and the
code, and `check_language.py` scans `.claude/docs/` and `CLAUDE.md`. So the three
claims a reader is entitled to make about it are made here instead.

**Every credential is listed.** The
[Target State](../.claude/docs/design/target-state.md#what-credential-free-means)
requires it in those words — a grader who discovers a needed key halfway through
bring-up has had a reproducibility failure whatever the repository technically
supports. Checked in both directions: nothing `.env.example` declares is missing from
the README, and nothing the README names is missing from `.env.example`.

**The access-control sentence is the Ledger's.**
[DEBT-008](../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
names the words the claim must be qualified with, and a paraphrase drifts in exactly
the direction that entry exists to prevent. `tests/test_app.py` reads the same sentence
out of the same entry for the sidebar.

**Every relative link resolves**, file and anchor, under the rule a markdown renderer
uses — which is `verify_framework.py`'s own `heading_anchors`, imported rather than
rewritten so the two documents cannot disagree about what an anchor is.
"""

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
ENV_EXAMPLE = ROOT / ".env.example"
LEDGER = ROOT / ".claude" / "docs" / "debt-ledger.md"

# `docs/` is the public face beside `README.md`; `.claude/docs/` is the working record
# and is checked by `verify_framework.py`.
PUBLIC_DOCS = ROOT / "docs"

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

    Both documents state the DEBT-008 sentence as a block quote and wrap it at
    different widths, so neither the `>` nor the line breaks may count as a
    difference. Nothing else about the sentence may differ.
    """
    return " ".join(re.sub(r"^\s*>\s?", "", text, flags=re.M).split())


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text()


@pytest.fixture(scope="module")
def heading_anchors():
    """`verify_framework.py`'s anchor rule, imported from the file that owns it."""
    path = ROOT / ".claude" / "scripts" / "verify_framework.py"
    spec = importlib.util.spec_from_file_location("verify_framework", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.heading_anchors


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


def test_the_readme_qualifies_access_control_in_the_ledgers_own_words(readme):
    """[DEBT-008](../.claude/docs/debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
    fires on *"the first access-control claim made anywhere a reader will see it"*,
    and names the sentence that qualifies it. The App renders the same one.
    """
    from veritas.app.render import ENFORCEMENT_NOTE

    sentence = normalised(ENFORCEMENT_NOTE)
    assert sentence in normalised(LEDGER.read_text()), (
        "the sentence the App renders is no longer the Ledger's — this test and "
        "tests/test_app.py disagree about which document is the source"
    )
    assert sentence in normalised(readme), (
        "README.md makes an access-control claim without DEBT-008's qualification, "
        "or with a paraphrase of it"
    )


# -- the link claim --------------------------------------------------------------


def public_documents() -> list[Path]:
    """`README.md` and anything under `docs/` — the public face, in full."""
    beside = sorted(PUBLIC_DOCS.rglob("*.md")) if PUBLIC_DOCS.exists() else []
    return [README, *beside]


def test_every_relative_link_in_the_public_documents_resolves(heading_anchors):
    """File *and* anchor, because a dead anchor lands the reader at the top of the
    right document, which reads as a vague citation rather than a broken one."""
    anchors: dict[Path, set[str]] = {}
    problems: list[str] = []
    links = 0

    for doc in public_documents():
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", doc.read_text()):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            relative, _, fragment = target.partition("#")
            path = (doc.parent / relative).resolve() if relative else doc
            links += 1
            if not path.exists():
                problems.append(f"{doc.name}: dead link -> {target}")
            elif fragment and path.suffix == ".md":
                if path not in anchors:
                    anchors[path] = heading_anchors(path.read_text())
                if fragment not in anchors[path]:
                    problems.append(f"{doc.name}: dead anchor -> {target}")

    assert links, "no relative links found — the pattern has rotted"
    assert not problems, "\n".join(problems)
