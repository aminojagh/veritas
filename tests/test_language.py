"""The documents and the code agree with the Glossary."""

import ast
import re

import pytest

# Left unexpanded on purpose: each is more recognisable than its expansion.
EXEMPT = {
    "SQL", "API", "HTTP", "HTTPS", "JSON", "CSV", "URL", "ID", "YAML",
    "PDF", "CLI", "RSS", "UTC", "IP", "AI",
}

# Shouted tokens that are not abbreviations at all.
NOT_ABBREVIATIONS = {
    "USD", "EUR", "GBP", "GBX", "JPY", "CHF", "AUD", "HKD", "SGD",  # currency codes
    "EU", "UK", "US", "APAC",                                        # regions
    "DEBT", "EXT", "ADR", "NNN", "NNNN", "YYYY", "MM", "DD", "NN",   # identifiers
    "README", "CLAUDE", "SKILL", "MD", "PASS", "FAIL", "TODO",       # file names, words
    "REWRITE", "RETRIEVE", "GROUND", "GENERATE", "VALIDATE", "EXECUTE", "ANSWER",
    "TERM",                                                         # a Term Proposal
    "NASDAQ", "BIRD",                                               # proper nouns
    "ACT",                                                          # NASDAQ's `ACT Symbol`
    "EXEMPT", "PRICES",                                             # constant names
}


def shouted_words() -> set[str]:
    """`NOT_ABBREVIATIONS`, every word DuckDB's SQL reserves, and the traded tickers."""
    from sqlglot.dialects.duckdb import DuckDB

    from veritas.ingestion.universe import TRADED_INSTRUMENTS

    sql = {word for keyword in DuckDB.Tokenizer.KEYWORDS for word in keyword.split()}
    tickers = {t for symbol in TRADED_INSTRUMENTS for t in re.findall(r"[A-Z]{2,6}", symbol)}
    return NOT_ABBREVIATIONS | sql | tickers


@pytest.fixture(scope="module")
def glossary(root) -> str:
    return (root / ".claude" / "docs" / "glossary.md").read_text()


@pytest.fixture(scope="module")
def terms(glossary) -> dict[str, str]:
    """Registered term -> status, read from the bolded first cell of each row."""
    found = {}
    for term, rest in re.findall(r"^\|\s*\*\*([^*]+)\*\*\s*\|(.*)$", glossary, re.M):
        cells = [c.strip().strip("*_` ") for c in rest.split("|")]
        found[term.strip()] = next((c for c in cells if c in {"agreed", "proposed"}), "")
    return found


def test_every_target_state_component_is_a_glossary_term(root, terms):
    target = (root / ".claude" / "docs" / "design" / "target-state.md").read_text()
    table = re.search(r"### Components\n(.*?)\n\n", target, re.S)
    assert table, "target-state.md has no Components table"
    names = re.findall(r"^\|\s*\*\*([A-Z][^*]*)\*\*\s*\|", table.group(1), re.M)
    assert names, "no component read out of the Components table"
    assert not [name for name in names if name not in terms]


def identifiers(path) -> set[str]:
    """Every name a Python file defines — not the words its prose uses."""
    names = set()
    for node in ast.walk(ast.parse(path.read_text())):
        match node:
            case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
                names.add(node.name)
            case ast.Name(ctx=ast.Store()) | ast.Attribute(ctx=ast.Store()):
                names.add(getattr(node, "id", None) or node.attr)
            case ast.arg():
                names.add(node.arg)
    return names


def test_no_proposed_term_names_a_code_identifier(root, terms):
    proposed = [t.lower().replace(" ", "_") for t, s in terms.items() if s == "proposed"]
    files = [
        p
        for directory in ("veritas", ".claude/scripts", "tests")
        for p in (root / directory).rglob("*.py")
        if "__pycache__" not in p.parts
    ]
    assert files
    hits = [
        f"{path.relative_to(root)}: {name}"
        for path in files
        for name in identifiers(path)
        for term in proposed
        if term in name.lower()
    ]
    assert not hits, f"a `proposed` term reached code before it was agreed: {hits}"


def test_every_abbreviation_in_the_documents_can_be_looked_up(root, glossary):
    """Registered in the Glossary's Abbreviations table, exempt, or not one at all."""
    section = re.search(r"^## Abbreviations\n(.*?)(?:^---|\Z)", glossary, re.S | re.M)
    assert section, "the Glossary has no Abbreviations section"
    registered = {
        short
        for row in re.findall(r"^\|([^|]+)\|", section.group(1), re.M)
        for short in re.findall(r"\*\*([A-Za-z&]+)\*\*", row)
    }
    known = registered | EXEMPT | shouted_words()
    documents = [*(root / ".claude" / "docs").rglob("*.md"), root / "CLAUDE.md"]
    unknown = {}
    for document in documents:
        prose = re.sub(r"^```.*?^```", "", document.read_text(), flags=re.S | re.M)
        for token in set(re.findall(r"\b([A-Z]{2,6})\b", prose)):
            if token not in known:
                unknown.setdefault(token, []).append(str(document.relative_to(root)))
    assert not unknown, (
        f"register these in the Glossary's Abbreviations table, or expand them: {unknown}"
    )
