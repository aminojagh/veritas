"""Check the documents against the Glossary and the writing conventions.

Run with:  uv run python .claude/scripts/check_language.py

Where `verify_framework.py` checks that the framework is *wired up* — documents
exist, links resolve, skills load — this script checks the rules that govern what
goes *inside* those documents:

  1. Non-Negotiable #1 — every component name the Target State uses must be a
     registered Glossary term, because those names become directories, modules
     and columns. An unregistered name is a term coined by accident.
  2. Non-Negotiable #1 — a term still marked `proposed` must not appear in a code
     identifier. `proposed` means "awaiting Amino", and code is where a name
     stops being cheap to change.
  3. The writing convention — an abbreviation is expanded on first use in each
     document that uses it.

Exits non-zero when any of these fail, so the rules are enforced rather than
merely written down. This is a partial repayment of DEBT-001, which records that
the framework's rules rest on discipline with no mechanism behind them.
"""

import ast
import re
import sys
from pathlib import Path

CLAUDE_DIR = Path(__file__).resolve().parent.parent  # <repo>/.claude
REPO_ROOT = CLAUDE_DIR.parent                        # <repo>
DOCS = CLAUDE_DIR / "docs"
GLOSSARY = DOCS / "glossary.md"
TARGET_STATE = DOCS / "design" / "target-state.md"

# Directories that hold code, for the "no proposed terms in identifiers" check.
CODE_ROOTS = [REPO_ROOT / "veritas", CLAUDE_DIR / "scripts"]

# Abbreviations that must be expanded on first use in each document.
# The expansion is what the checker looks for earlier in the same file.
REQUIRE_EXPANSION = {
    "DDL": "Data Definition Language",
    "MRR": "Mean Reciprocal Rank",
    "MVP": "Minimum Viable Product",
    "LLM": "Large Language Model",
    "RAG": "Retrieval-Augmented Generation",
    "ETF": "Exchange-Traded Fund",
    "ISIN": "International Securities Identification Number",
    "CUSIP": "Committee on Uniform Securities Identification Procedures",
    "ECB": "European Central Bank",
    "LSE": "London Stock Exchange",
    "SEC": "Securities and Exchange Commission",
    "CIK": "Central Index Key",
    "OHLCV": "open, high, low, close, volume",
    "UI": "User Interface",
    "UX": "User Experience",
    "FX": "Foreign Exchange",
}

# Abbreviations left alone on purpose: each is more recognisable than its
# expansion, so spelling it out would add noise rather than clarity.
EXEMPT = {
    "SQL", "API", "HTTP", "HTTPS", "JSON", "CSV", "URL", "ID", "YAML",
    "PDF", "CLI", "RSS", "UTC", "IP", "AI",
}

# Uppercase tokens that are not abbreviations at all, so the "can the reader look
# this up?" scan should ignore them.
KNOWN_NON_ABBREVIATIONS = {
    # Currency codes — ISO 4217, and self-explanatory in context.
    "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "HKD", "SGD",
    # Ticker symbols and exchange suffixes appearing in the data-availability work.
    "AAPL", "SPY", "TLT", "BNDX", "IWDA", "SAP", "VOD", "GSPC", "TNX",
    "ES", "GC", "EURUSD", "DE", "AS", "NASDAQ",
    # SQL keywords and code-ish tokens quoted in prose.
    "SELECT", "CREATE", "TABLE", "WHERE", "DECIMAL", "NULL", "OWL", "RDF",
    "SPARQL", "DAG", "CTE", "LIMIT", "JOIN", "GROUP", "ORDER",
    # Document and tooling shorthand.
    "PY", "OK", "GO", "PASS", "FAIL", "NOTE", "TODO", "KB", "MB", "GB",
    "CET", "FAQ", "BIRD", "MD", "README", "CI", "R1", "R2", "R3",
    "DEBT", "EXT", "ADR",  # register identifier prefixes, e.g. EXT-001
    # Ordinary words that happen to be shouted: flow-diagram step labels,
    # document section markers, and the operating agreement's own filename.
    "ANSWER", "GROUND", "REWRITE", "RETRIEVE", "GENERATE", "VALIDATE",
    "EXECUTE", "DEBT", "TERM", "CLAUDE", "IMPORTANT",
    # Filename and identifier placeholders in templates.
    "NNN", "NNNN", "YYYY", "MM", "DD", "NN",
    # Geography: region values of the "by region" Dimension Definition, plus the
    # country shorthand used to describe data sources. Universally read.
    "EU", "UK", "US", "APAC",
    # Proper nouns that are not abbreviations.
    "EXANTE", "DB",
}

problems: list[str] = []


def load_glossary() -> dict[str, str]:
    """Registered term -> status, read from the bolded first cell of each row."""
    terms: dict[str, str] = {}
    for line in GLOSSARY.read_text().splitlines():
        row = re.match(r"^\|\s*\*\*([^*]+)\*\*\s*\|(.*)$", line)
        if not row:
            continue
        # A status cell may be emphasised, e.g. "**proposed**" — strip the markup.
        cells = [c.strip().strip("*_` ") for c in row.group(2).split("|")]
        status = next((c for c in cells if c in {"agreed", "proposed", "retired"}), "")
        terms[row.group(1).strip()] = status
    return terms


def check_target_state_components(terms: dict[str, str]) -> None:
    """Every component name in the Target State must be a registered term."""
    text = TARGET_STATE.read_text()
    table = re.search(r"### Components\n(.*?)\n\n", text, re.S)
    if not table:
        problems.append("target-state.md: could not find the Components table")
        return

    names = re.findall(r"^\|\s*\*\*([A-Z][^*]*)\*\*\s*\|", table.group(1), re.M)
    pending = 0
    print(f"  Target State components ({len(names)})")
    for name in names:
        status = terms.get(name)
        if status is None:
            problems.append(
                f"target-state.md names component {name!r}, which has no Glossary row "
                f"(it will become a directory or module in Step 002)"
            )
            print(f"    UNREGISTERED  {name}")
        else:
            pending += status == "proposed"
            print(f"    {status or '(no status)':<12}  {name}")
    if pending:
        # Not a failure: `proposed` is the correct state for a term under
        # discussion. It becomes a failure the moment it reaches code, which is
        # check_proposed_terms_not_in_code's job.
        print(f"    -> {pending} awaiting Amino; none may enter code until agreed")


def identifiers_in(path: Path) -> set[str]:
    """Every name a Python file *defines* — functions, classes, variables, arguments.

    Deliberately parsed rather than grepped. The rule is about identifiers, and a
    domain noun appearing in a docstring or a comment is prose, not a name: the
    Glossary governs what things are *called*, not whether a word may be written
    down. Grepping the raw text conflates the two and fires on every explanation.
    """
    names: set[str] = set()
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        match node:
            case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
                names.add(node.name)
            case ast.Name(ctx=ast.Store()):
                names.add(node.id)
            case ast.arg():
                names.add(node.arg)
            case ast.Attribute(ctx=ast.Store()):
                names.add(node.attr)
    return names


def check_proposed_terms_not_in_code(terms: dict[str, str]) -> None:
    """A `proposed` term must not have reached a code identifier yet."""
    proposed = [t for t, status in terms.items() if status == "proposed"]
    files = [p for root in CODE_ROOTS if root.exists() for p in root.rglob("*.py")]
    defined = {path: identifiers_in(path) for path in files}
    print(f"  proposed terms: {len(proposed)} · python files scanned: {len(files)} "
          f"· identifiers: {sum(len(n) for n in defined.values())}")

    for term in proposed:
        identifier = term.lower().replace(" ", "_")
        for path, names in defined.items():
            hits = {n for n in names if identifier in n.lower()}
            if hits:
                problems.append(
                    f"{path.relative_to(REPO_ROOT)}: defines {sorted(hits)}, but Glossary "
                    f"term {term!r} is still `proposed` — agree it before it enters code"
                )


def glossary_abbreviations() -> dict[str, str]:
    """Short -> expanded, from the Glossary's Abbreviations table."""
    text = GLOSSARY.read_text()
    section = re.search(r"^## Abbreviations\n(.*?)^---", text, re.S | re.M)
    if not section:
        problems.append("glossary.md: no `## Abbreviations` section")
        return {}

    found: dict[str, str] = {}
    for line in section.group(1).splitlines():
        row = re.match(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
        if not row or row.group(1).startswith(("---", "Short")):
            continue
        # A cell may carry two slash-separated forms, e.g. "**UI** / **UX**".
        shorts = re.findall(r"\*\*([A-Za-z&]+)\*\*", row.group(1))
        expansions = [e.strip() for e in row.group(2).split(" / ")]
        for i, short in enumerate(shorts):
            found[short] = expansions[i] if i < len(expansions) else expansions[0]
    return found


def check_abbreviations() -> None:
    """An abbreviation is expanded on first use, or registered in the Glossary.

    The Glossary's Abbreviations table is the project-wide answer, so a document
    that uses a registered short form does not have to expand it again. An
    abbreviation that is in neither place is a word the reader cannot look up.
    """
    registered = glossary_abbreviations()
    missing = sorted(set(REQUIRE_EXPANSION) - set(registered))
    for abbr in missing:
        problems.append(
            f"glossary.md: abbreviation {abbr!r} is used in the project but is not in "
            f"the Abbreviations table — add it, or expand it on first use everywhere"
        )

    docs = sorted(DOCS.rglob("*.md")) + [REPO_ROOT / "CLAUDE.md"]
    unknown: set[str] = set()
    for doc in docs:
        for abbr in set(re.findall(r"\b([A-Z]{2,6})\b", doc.read_text())):
            if abbr in EXEMPT or abbr in registered or abbr in KNOWN_NON_ABBREVIATIONS:
                continue
            unknown.add(abbr)
    for abbr in sorted(unknown):
        problems.append(
            f"{abbr!r} is used in the documents but is neither in the Glossary's "
            f"Abbreviations table nor in the exempt list in this script"
        )

    print(f"  abbreviations: {len(registered)} registered in the Glossary, "
          f"{len(EXEMPT)} exempt, {len(unknown)} unrecognised")


def main() -> int:
    terms = load_glossary()
    print(f"  glossary: {len(terms)} registered terms")
    check_target_state_components(terms)
    check_proposed_terms_not_in_code(terms)
    check_abbreviations()

    print()
    if problems:
        print(f"FAIL — {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("PASS — documents agree with the Glossary and the writing conventions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
