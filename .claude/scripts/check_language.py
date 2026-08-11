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
    # Currency codes — ISO 4217, and self-explanatory in context. GBX is the
    # minor-unit spelling of GBP that dim_instrument's constraint does *not*
    # catch, so it is named in the documents on purpose.
    "USD", "EUR", "GBP", "GBX", "JPY", "CHF", "AUD", "HKD", "SGD",
    # Ticker symbols and exchange suffixes from the data-availability probes.
    # The *traded* universe is not listed here — it is derived below, for the same
    # reason the schema keywords are: a remembered list is always one document
    # behind, and Sub-steps 2.3 to 2.5 will move the universe again.
    "GSPC", "TNX", "NASDAQ",
    # A NASDAQ Trader column name, not project vocabulary: `otherlisted.txt` keys
    # its symbol column `ACT Symbol` where `nasdaqlisted.txt` says `Symbol`. It is
    # quoted in ADR-0004 because resolving that disagreement is what the ingestion
    # code does.
    "ACT",
    # Vocabulary of query languages we do *not* write, quoted in the ADRs that
    # rejected them or in prose about SQL in general. The keywords of the SQL we do
    # write are not here — `warehouse_sql_keywords()` derives those, for the reason
    # given there.
    "DECIMAL", "OWL", "RDF", "SPARQL", "DAG", "CTE", "LIMIT", "ABS",
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
    # Legal-form suffixes inside registered company names. These arrive in the
    # data — `dim_instrument.instrument_name` holds "SAP SE" and "MICROSOFT CORP"
    # — and get quoted in reviews as evidence of what actually loaded. They are
    # not abbreviations a reader looks up, they are part of a company's name. The
    # list is stocked ahead of need rather than one failure at a time, because
    # widening the traded universe is what produces the next one.
    # (`ETF` and `ADR` belong here by category but are registered in the
    # Glossary's Abbreviations table already, so listing them would be dead text.)
    "SE", "CORP", "PLC", "LTD", "INC", "NV", "AG", "SA", "REIT",
    # Module-level constant names quoted in prose, e.g. "add its name to BUILDS".
    "BUILDS", "SEED",
}


def traded_universe_tokens() -> set[str]:
    """Shouted tokens inside the traded Instrument universe's ticker symbols.

    Derived rather than remembered, exactly as the schema-keyword group above is.
    `SAP.DE` contributes SAP and DE, `EURUSD=X` contributes EURUSD; the one- and
    two-character suffixes that the abbreviation pattern would not match anyway
    fall out on their own. When Sub-step 2.3 or 2.5 changes the universe, this
    follows without anyone remembering that it has to.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from veritas.ingestion.universe import TRADED_INSTRUMENTS

    tokens: set[str] = set()
    for symbol in TRADED_INSTRUMENTS:
        tokens.update(re.findall(r"[A-Z]{2,6}", symbol))
    return tokens


def warehouse_sql_keywords() -> set[str]:
    """Shouted keywords of the hand-authored SQL in `veritas/warehouse/`.

    Derived rather than remembered, for the reason the traded-universe tokens are.
    This group used to be a literal list, re-derived by hand from `schema.sql`
    whenever a review quoted a constraint — and Sub-step 2.4 is exactly the failure
    that design predicts: the build scripts are hand-authored SQL too, its
    `ASOF JOIN` and a `CASE` in a comment about one were quoted in the review, and
    neither word appears in `schema.sql`. A list re-derived from one file is one
    file behind. This reads every one of them, so writing about any SQL this
    project actually contains is covered before it is written.

    Two things are stripped before the keywords are taken, and both matter:

      * **`--` comments**, which are prose. They mention ECB, UTC, ADR and ISO, and
        exempting those here would silence the abbreviation check on four real
        abbreviations because a build script happened to explain itself.
      * **quoted literals**, which are *domain values* rather than keywords — the
        instrument types and region codes the CHECK constraints name. Those must
        stay visible to the scan: they are registered Glossary vocabulary, and this
        function has no business exempting them from anything.

    Anything longer than six characters — VARCHAR, PRIMARY, REFERENCES, TIMESTAMP —
    never reaches this set, because the abbreviation candidate pattern in
    check_abbreviations() is `[A-Z]{2,6}`.
    """
    keywords: set[str] = set()
    for path in sorted((REPO_ROOT / "veritas" / "warehouse").rglob("*.sql")):
        statements = "\n".join(
            line.split("--")[0] for line in path.read_text().splitlines()
        )
        keywords.update(re.findall(r"\b[A-Z]{2,6}\b", re.sub(r"'[^']*'", " ", statements)))
    return keywords


KNOWN_NON_ABBREVIATIONS |= traded_universe_tokens()
KNOWN_NON_ABBREVIATIONS |= warehouse_sql_keywords()

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


def prose_only(text: str) -> str:
    """Drop fenced code blocks, so the abbreviation scan reads prose only.

    A fenced block is code, and code is full of shouted tokens that are not
    abbreviations at all: SQL keywords, type names, environment variables. They
    are not words a reader needs to look up, and enumerating them one at a time
    in KNOWN_NON_ABBREVIATIONS is a list that grows for the life of the project.
    Inline spans are deliberately *not* stripped: a short identifier inside a
    sentence is still being read as part of that sentence.
    """
    return re.sub(r"^```.*?^```", "", text, flags=re.DOTALL | re.MULTILINE)


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
        for abbr in set(re.findall(r"\b([A-Z]{2,6})\b", prose_only(doc.read_text()))):
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
