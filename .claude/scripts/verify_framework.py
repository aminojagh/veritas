"""Check that the development framework is internally consistent.

Run with:  uv run python .claude/scripts/verify_framework.py

Verifies the structural promises CLAUDE.md makes: that every document it points
at exists, that each skill is loadable and trigger-described, that no document
links to a file that isn't there, and that we are on the pinned interpreter.

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


def check_links() -> None:
    """Relative markdown links in our own documents must resolve."""
    docs = sorted(DOCS.rglob("*.md")) + [CLAUDE_MD]
    for doc in docs:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", doc.read_text()):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = (doc.parent / target.split("#")[0]).resolve()
            if not path.exists():
                problems.append(f"{doc.relative_to(REPO_ROOT)}: dead link -> {target}")


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
