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
`profile.py` is the identity a question is run as — its role, the region it may see, and
the Restricted Columns it may not; and `gate.py` is the rules that produce a verdict, together with the tracer, the
lineage walk and the route reader they read a parse tree with — which
`check_validation_feasibility.py` imports back from here
under [R2](../../.claude/docs/plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25),
so that one tracer answers for both corpora, one detector for both declarations of a
Restricted Column, and one route reader for both declarations of a route.
"""

from veritas.validation.gate import (
    ANSWER_COLUMN,
    DATE_TYPE,
    DIALECT,
    SCAN_CEILING,
    TRUSTED_REWRITES,
    Hop,
    Join,
    Reading,
    Route,
    Schema,
    TracerRefused,
    ValidationGate,
    access_predicate,
    base_tables,
    canonical,
    certified_form,
    certified_forms,
    certified_metrics_only,
    certified_route,
    columns_reaching_the_answer,
    columns_reaching_the_answer_of,
    date_columns_filtered,
    grouped_columns,
    join_kind,
    joins_in,
    metric_expressions,
    metric_expressions_of,
    metric_expressions_through,
    on_base_tables,
    projected_expressions,
    projections_of,
    read,
    resolve,
    restricted_columns_in_projection,
    restricted_columns_in_projection_of,
    route_of,
    route_of_resolved,
    spelled,
    trusted_rewrite_names,
    where_conjuncts,
    written_projections,
)
from veritas.validation.outcome import RejectionReason, ValidationGateOutcome
from veritas.validation.profile import (
    ACCESS_AXIS,
    ANALYST,
    AccessProfile,
    RestrictedColumn,
)

__all__ = [
    "ACCESS_AXIS",
    "ANALYST",
    "ANSWER_COLUMN",
    "DATE_TYPE",
    "DIALECT",
    "SCAN_CEILING",
    "TRUSTED_REWRITES",
    "AccessProfile",
    "Hop",
    "Join",
    "Reading",
    "RejectionReason",
    "RestrictedColumn",
    "Route",
    "Schema",
    "TracerRefused",
    "ValidationGate",
    "ValidationGateOutcome",
    "access_predicate",
    "base_tables",
    "canonical",
    "certified_form",
    "certified_forms",
    "certified_metrics_only",
    "certified_route",
    "columns_reaching_the_answer",
    "columns_reaching_the_answer_of",
    "date_columns_filtered",
    "grouped_columns",
    "join_kind",
    "joins_in",
    "metric_expressions",
    "metric_expressions_of",
    "metric_expressions_through",
    "on_base_tables",
    "projected_expressions",
    "projections_of",
    "read",
    "resolve",
    "restricted_columns_in_projection",
    "restricted_columns_in_projection_of",
    "route_of",
    "route_of_resolved",
    "spelled",
    "trusted_rewrite_names",
    "where_conjuncts",
    "written_projections",
]
