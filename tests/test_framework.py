"""The framework's standing rules, enforced rather than remembered."""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))

# The check scripts still in `.claude/scripts/`. Behaviour is claimed in `tests/`,
# so this set only shrinks: a script deleted takes its line with it.
CHECK_SCRIPTS = {
    "check_data_availability.py",
    "check_semantic_layer.py",
    "check_validation_feasibility.py",
    "check_warehouse.py",
    "check_validation_gate/__main__.py",
    "check_validation_gate/access.py",
    "check_validation_gate/probes.py",
    "check_validation_gate/read_only.py",
    "check_validation_gate/restricted.py",
    "check_validation_gate/route.py",
    "check_validation_gate/traces.py",
}

HISTORY_LINK = re.compile(r"\]\((?:\.\./)+(?:\.claude/)?docs/(?:plan|reviews)/[^)]+\)")


def python_files(root, directory):
    """Every Python file under `directory`, as a path relative to the root."""
    for path in sorted((root / directory).rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path.relative_to(root)


def test_check_scripts_only_shrink(root):
    """`.claude/scripts/` holds exactly the scripts listed."""
    scripts = root / ".claude" / "scripts"
    found = {
        str(p.relative_to(scripts))
        for p in scripts.rglob("*.py")
        if "__pycache__" not in p.parts
    }
    assert found == CHECK_SCRIPTS, (
        f"added {sorted(found - CHECK_SCRIPTS)} — behaviour is claimed in tests/; "
        f"deleted {sorted(CHECK_SCRIPTS - found)} — remove their lines here"
    )


@pytest.mark.parametrize("directory", ["veritas", ".claude/scripts", "tests"])
def test_code_never_links_into_plans_or_reviews(root, directory):
    """Both are deleted when their Step closes, so a link from code would rot."""
    files = list(python_files(root, directory))
    # A filter that silently matches nothing is the way this check dies quietly.
    assert files, f"no Python files scanned under {directory}"
    assert not [
        str(path) for path in files if HISTORY_LINK.search((root / path).read_text())
    ], "cite the Glossary, the Ledger, an ADR or Target State instead"


def test_every_path_claude_md_names_exists(root):
    named = re.findall(r"`((?:\.claude|docs|tests)/[^`*]*)`", (root / "CLAUDE.md").read_text())
    assert named
    placeholders = ("NNN", "<")
    assert not [
        path
        for path in named
        if not any(p in path for p in placeholders) and not (root / path).exists()
    ]


@pytest.mark.parametrize("skill", SKILLS, ids=lambda path: path.parent.name)
def test_a_skill_is_named_for_its_directory_and_described_by_its_trigger(skill):
    """A description that summarises its skill gets followed instead of the skill."""
    frontmatter = re.match(r"^---\n(.*?)\n---\n", skill.read_text(), re.S)
    assert frontmatter, "frontmatter missing or unterminated"
    name = re.search(r"^name:\s*(.+)$", frontmatter.group(1), re.M)
    description = re.search(r"^description:\s*(.+)$", frontmatter.group(1), re.M)
    assert name and name.group(1).strip() == skill.parent.name
    assert description and len(description.group(1)) <= 500
    assert re.match(r"use (when|before|at|after)\b", description.group(1), re.I)


def test_the_interpreter_is_the_pinned_one_in_the_project_environment(root):
    pinned = (root / ".python-version").read_text().strip()
    assert Path(sys.executable).is_relative_to(root / ".venv")
    assert f"{sys.version_info.major}.{sys.version_info.minor}" == pinned
