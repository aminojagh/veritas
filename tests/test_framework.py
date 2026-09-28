"""The framework's standing rules, enforced rather than remembered.

Both are exact ratchets: each table names what exists, so an entry can leave it
and nothing can join it.
"""

import re

import pytest

# The check scripts still in `.claude/scripts/`. Behaviour is claimed in `tests/`,
# so this set only shrinks: a script deleted takes its line with it.
CHECK_SCRIPTS = {
    "check_data_availability.py",
    "check_language.py",
    "check_semantic_layer.py",
    "check_validation_feasibility.py",
    "check_warehouse.py",
    "verify_framework.py",
    "check_validation_gate/__main__.py",
    "check_validation_gate/access.py",
    "check_validation_gate/probes.py",
    "check_validation_gate/read_only.py",
    "check_validation_gate/restricted.py",
    "check_validation_gate/route.py",
    "check_validation_gate/traces.py",
}

# Links from code into `plan/` or `reviews/`, per file. Code may not cite either,
# so each count only falls, a link cut lowers its count here, and the table ends
# empty.
HISTORY_LINKS = {
    "veritas/semantic/loader.py": 2,
    "veritas/validation/__init__.py": 2,
    "veritas/validation/gate.py": 15,
    "veritas/validation/outcome.py": 4,
    "veritas/validation/profile.py": 3,
    "veritas/warehouse/adapter.py": 1,
    ".claude/scripts/check_semantic_layer.py": 14,
    ".claude/scripts/check_validation_feasibility.py": 8,
    ".claude/scripts/check_validation_gate/__main__.py": 1,
    ".claude/scripts/check_validation_gate/access.py": 4,
    ".claude/scripts/check_validation_gate/probes.py": 3,
    ".claude/scripts/check_validation_gate/read_only.py": 2,
    ".claude/scripts/check_validation_gate/restricted.py": 3,
    ".claude/scripts/check_validation_gate/route.py": 5,
    ".claude/scripts/check_validation_gate/traces.py": 4,
    ".claude/scripts/check_warehouse.py": 2,
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


@pytest.mark.parametrize("directory", ["veritas", ".claude/scripts"])
def test_code_cites_plans_and_reviews_only_as_listed(root, directory):
    """Each file links into `plan/` or `reviews/` exactly as often as listed."""
    files = list(python_files(root, directory))
    # A filter that silently matches nothing is the way this check dies quietly.
    assert files, f"no Python files scanned under {directory}"
    found = {
        str(path): count
        for path in files
        if (count := len(HISTORY_LINK.findall((root / path).read_text())))
    }
    listed = {k: v for k, v in HISTORY_LINKS.items() if k.startswith(f"{directory}/")}
    assert found == listed, (
        "code may not link into plan/ or reviews/ — cite the Glossary, the Ledger, "
        "an ADR or Target State; when a link is cut, lower its count here"
    )
