"""Check that the development framework is internally consistent.

Run with:  uv run python .claude/scripts/verify_framework.py

Verifies the structural promises CLAUDE.md makes: that every document it points
at exists, that each skill is loadable and trigger-described, that no document
links to a file that isn't there or to a heading that isn't in it, and that we
are on the pinned interpreter.

This does not check whether the *content* is any good — only that the framework
is wired up. Content is Amino's review.

Layout note: CLAUDE.md stays at the repository root (so Claude Code auto-loads
it); everything else the framework owns lives under .claude/ — this script in
.claude/scripts/, the working record in .claude/docs/, the skills in
.claude/skills/.
"""

import re
import sys
from pathlib import Path

CLAUDE_DIR = Path(__file__).resolve().parent.parent  # <repo>/.claude
REPO_ROOT = CLAUDE_DIR.parent                        # <repo>
SKILLS = CLAUDE_DIR / "skills"
DOCS = CLAUDE_DIR / "docs"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

# Code cites documents too, as markdown links inside docstrings and comments, so
# that a later documentation pass can move a document and find every reference to
# it. Nothing read those links until Sub-step 4.1, which is DEBT-001's second
# coverage gap and its repayment. The same two roots `check_warehouse.py` scans for
# the adapter seam.
CODE_ROOTS = [REPO_ROOT / "veritas", CLAUDE_DIR / "scripts"]

problems: list[str] = []


def check_claude_md_references() -> None:
    """Every concrete path CLAUDE.md names must exist (resolved from the repo root)."""
    text = CLAUDE_MD.read_text()
    for ref in sorted(set(re.findall(r"`((?:\.claude|docs|scripts)/[^`]*)`", text))):
        if "NNN" in ref or "*" in ref:  # glob patterns in the document table
            continue
        if not (REPO_ROOT / ref).exists():
            problems.append(f"CLAUDE.md points at a missing path: {ref}")


def check_skills() -> None:
    """Skills need parseable frontmatter, a matching name, and a trigger description."""
    skills = sorted(SKILLS.glob("*/SKILL.md"))
    if not skills:
        problems.append(f"no skills found under {SKILLS.relative_to(REPO_ROOT)}")
        return

    for skill in skills:
        slug = skill.parent.name
        frontmatter = re.match(r"^---\n(.*?)\n---\n", skill.read_text(), re.S)
        if not frontmatter:
            problems.append(f"{slug}: frontmatter missing or unterminated")
            continue

        fields = frontmatter.group(1)
        name = re.search(r"^name:\s*(.+)$", fields, re.M)
        description = re.search(r"^description:\s*(.+)$", fields, re.M)

        if not name:
            problems.append(f"{slug}: frontmatter has no `name`")
        elif name.group(1).strip() != slug:
            problems.append(f"{slug}: `name` is {name.group(1).strip()!r}, expected {slug!r}")

        if not description:
            problems.append(f"{slug}: frontmatter has no `description`")
            continue

        text = description.group(1).strip()
        # The real rule is "triggering conditions only, never a workflow summary" —
        # a description that summarises its own skill gets followed instead of the
        # skill body. An opening trigger clause is the enforceable proxy for that.
        if not re.match(r"use (when|before|at|after)\b", text, re.I):
            problems.append(f"{slug}: description should open with a trigger clause")
        if len(text) > 500:
            problems.append(f"{slug}: description is {len(text)} chars, keep it under 500")

        print(f"  skill ok   {slug:22} {len(skill.read_text().split()):>4} words")


FENCE = re.compile(r"^\s*(?:```|~~~)")


def heading_anchors(text: str) -> set[str]:
    """The anchors a markdown renderer generates for a document's headings.

    Lowercase the heading, drop every character that is not a word character,
    space or hyphen, then turn spaces into hyphens. Two details are the ones that
    matter here and both have already caused a wrong answer:

    - `\\w` keeps underscores, so `fct_fx_rate` survives as itself. Treating an
      underscore as an emphasis marker instead silently rewrites the anchor of
      every heading that names a table.
    - A `#` line inside a fenced block is shell or SQL, not a heading. Counting
      one would invent an anchor that no renderer produces, so a dead link
      pointing at it would pass this check.

    A repeated heading gets `-1`, `-2` appended, which is what the renderers do
    and what makes the second `### Changes made on review` reachable.
    """
    anchors: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or not line.startswith("#"):
            continue
        slug = re.sub(r"[^\w\s-]", "", line.lstrip("#").strip().lower())
        slug = slug.strip().replace(" ", "-")
        base, repeat = slug, 0
        while slug in anchors:
            repeat += 1
            slug = f"{base}-{repeat}"
        anchors.add(slug)
    return anchors


def check_links() -> None:
    """Relative markdown links in our own files must resolve — file *and* anchor.

    The `#anchor` half used to be split off and thrown away, so a link could point
    at a heading that had been renamed or never existed and still pass. A dead
    anchor lands the reader at the top of the right document, which reads as the
    citation being vague rather than broken — the failure Non-Negotiable #4's
    "citations quote" rule is trying to prevent.

    **Code is read here as well as documents**, because the docstrings cite ADRs,
    Ledger entries and constraints in exactly the same markdown, and a link a
    reader cannot follow is no better for sitting inside a comment. It costs one
    line and it is precise rather than approximate: a bracketed label immediately
    followed by a parenthesised path is not otherwise Python, so every match in a
    `.py` file is a citation. The count this run read is printed below.
    """
    sources = (
        sorted(DOCS.rglob("*.md"))
        + [CLAUDE_MD]
        + sorted(path for root in CODE_ROOTS for path in root.rglob("*.py"))
    )
    anchors: dict[Path, set[str]] = {}
    links = anchored = 0

    for doc in sources:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", doc.read_text()):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            relative, _, fragment = target.partition("#")
            path = (doc.parent / relative).resolve() if relative else doc
            links += 1
            if not path.exists():
                problems.append(f"{doc.relative_to(REPO_ROOT)}: dead link -> {target}")
                continue
            if not fragment or path.suffix != ".md":
                continue
            if path not in anchors:
                anchors[path] = heading_anchors(path.read_text())
            anchored += 1
            if fragment not in anchors[path]:
                problems.append(f"{doc.relative_to(REPO_ROOT)}: dead anchor -> {target}")

    print(f"  links      {f'{links} links, {anchored} anchors':22} "
          f"{len(sources)} documents and python files")


def check_interpreter() -> None:
    """Guard the 'always uv run' rule from CLAUDE.md."""
    if REPO_ROOT.name not in sys.executable or ".venv" not in sys.executable:
        problems.append(f"not running in the project venv: {sys.executable}")
    print(f"  python     {sys.version.split()[0]:22} {sys.executable}")


def main() -> int:
    check_claude_md_references()
    check_skills()
    check_links()
    check_interpreter()

    print()
    if problems:
        print(f"FAIL — {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("PASS — framework is wired up correctly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
