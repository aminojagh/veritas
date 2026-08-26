"""The Validation Gate — the deterministic, non-Large-Language-Model (non-LLM) checks
a generated query must pass before it executes.

The registered home of `Validation Gate`, `Access Profile` and `Restricted Column`,
and of the two terms
[R3](../../.claude/docs/plan/step-005-validation-gate.md#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)
registered when the Gate made them code identifiers: `Validation Gate outcome` and
`Rejection Reason`.

Laid out like `veritas/warehouse/` and `veritas/semantic/`: this file re-exports, and
the modules behind it hold the work. `outcome.py` is the verdict and the reason
taxonomy — a data contract three components that import no rule still have to read —
and `gate.py` is the rules that produce one.
"""

from veritas.validation.gate import (
    DIALECT,
    SCAN_CEILING,
    TRUSTED_REWRITES,
    Reading,
    ValidationGate,
    read,
    trusted_rewrite_names,
)
from veritas.validation.outcome import RejectionReason, ValidationGateOutcome

__all__ = [
    "DIALECT",
    "SCAN_CEILING",
    "TRUSTED_REWRITES",
    "Reading",
    "RejectionReason",
    "ValidationGate",
    "ValidationGateOutcome",
    "read",
    "trusted_rewrite_names",
]
