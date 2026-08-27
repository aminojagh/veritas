"""The Validation Gate — the deterministic, non-Large-Language-Model (non-LLM) checks
a generated query must pass before it executes.

The registered home of `Validation Gate`, `Access Profile` and `Restricted Column`,
and of the two terms
[R3](../../.claude/docs/plan/step-005-validation-gate.md#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)
registered when the Gate made them code identifiers: `Validation Gate outcome` and
`Rejection Reason`.

Laid out like `veritas/warehouse/` and `veritas/semantic/`: this file re-exports, and
the modules behind it hold the work. `outcome.py` is the verdict and the reason
taxonomy — a data contract three components that import no rule still have to read;
`profile.py` is the identity a question is run as and the Restricted Columns it may not
see; and `gate.py` is the rules that produce a verdict, together with the tracer and the
lineage walk they read a parse tree with — which `check_validation_feasibility.py`
imports back from here
under [R2](../../.claude/docs/plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25),
so that one tracer answers for both corpora and one detector for both declarations of a
Restricted Column.
"""

from veritas.validation.gate import (
    ANSWER_COLUMN,
    DIALECT,
    SCAN_CEILING,
    TRUSTED_REWRITES,
    Reading,
    Schema,
    TracerRefused,
    ValidationGate,
    canonical,
    certified_form,
    certified_forms,
    certified_metrics_only,
    columns_reaching_the_answer,
    metric_expressions,
    projected_expressions,
    read,
    resolve,
    restricted_columns_in_projection,
    trusted_rewrite_names,
)
from veritas.validation.outcome import RejectionReason, ValidationGateOutcome
from veritas.validation.profile import ANALYST, AccessProfile, RestrictedColumn

__all__ = [
    "ANALYST",
    "ANSWER_COLUMN",
    "DIALECT",
    "SCAN_CEILING",
    "TRUSTED_REWRITES",
    "AccessProfile",
    "Reading",
    "RejectionReason",
    "RestrictedColumn",
    "Schema",
    "TracerRefused",
    "ValidationGate",
    "ValidationGateOutcome",
    "canonical",
    "certified_form",
    "certified_forms",
    "certified_metrics_only",
    "columns_reaching_the_answer",
    "metric_expressions",
    "projected_expressions",
    "read",
    "resolve",
    "restricted_columns_in_projection",
    "trusted_rewrite_names",
]
