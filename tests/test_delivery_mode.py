"""Delivery Mode's two boundaries, enforced rather than remembered.

Both are ratchets: they permit exactly what exists today and nothing more, so a
Step cannot quietly restart the growth that Delivery Mode exists to stop. Both
are deleted with Delivery Mode itself on 2026-09-09, when
[DEBT-023](../.claude/docs/debt-ledger.md#debt-023--two-proving-systems-run-side-by-side)
and [DEBT-024](../.claude/docs/debt-ledger.md#debt-024--source-and-step-documents-carry-prose-delivery-mode-would-not-admit)
come due.
"""

import re

import pytest

# Every check script that exists on 2026-08-29. The set may shrink, never grow:
# new behavioural claims go in `tests/`.
FROZEN_CHECKS = {
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

# Links from code into `plan/` or `reviews/`, per file, on 2026-08-29. A file may
# hold fewer than its number and no file may appear that is not listed — which is
# what makes this a one-way ratchet rather than a budget.
FROZEN_HISTORY_LINKS = {
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


def test_no_new_check_scripts(root):
    """`.claude/scripts/` is frozen — a new behavioural check belongs in `tests/`."""
    scripts = root / ".claude" / "scripts"
    found = {
        str(p.relative_to(scripts))
        for p in scripts.rglob("*.py")
        if "__pycache__" not in p.parts
    }
    assert found <= FROZEN_CHECKS, (
        f"new check script(s) {sorted(found - FROZEN_CHECKS)} — Delivery Mode puts "
        f"behavioural claims in tests/, and `.claude/scripts/` is frozen"
    )


@pytest.mark.parametrize("directory", ["veritas", ".claude/scripts"])
def test_code_does_not_cite_step_history(root, directory):
    """No code links into `plan/` or `reviews/` beyond what already did.

    A ruling is a transcript of a conversation. Code that cites one pins that
    plan's headings forever and makes the Step's negotiation permanent API.
    """
    seen = 0
    for path in python_files(root, directory):
        seen += 1
        key = str(path)
        found = len(HISTORY_LINK.findall((root / path).read_text()))
        allowed = FROZEN_HISTORY_LINKS.get(key, 0)
        assert found <= allowed, (
            f"{key} cites Step history {found} times, {allowed} allowed — cite the "
            f"Glossary, the Debt Ledger, an ADR, or Target State instead"
        )
    # A filter that silently matches nothing is the way this check dies quietly.
    assert seen, f"no Python files scanned under {directory}"
