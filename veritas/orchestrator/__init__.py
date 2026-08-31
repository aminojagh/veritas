"""The Orchestrator — the sequence a question runs through, and the failure paths.

It owns none of the steps that have a component of their own: Retrieval searches,
the Validation Gate judges, the Warehouse Adapter executes. `rewrite.py` holds the
one step that has no other home — resolving Ambiguous Terms, which is where a
question either becomes answerable or turns into a question back.
"""

from veritas.orchestrator.rewrite import (
    FENCED,
    PLACEHOLDER,
    RULES,
    Rewrite,
    ambiguous_terms_in,
    clarification_for,
    instruction,
    resolutions_in,
    rewrite,
    rewritten_with,
    said_as,
)

__all__ = [
    "FENCED",
    "PLACEHOLDER",
    "RULES",
    "Rewrite",
    "ambiguous_terms_in",
    "clarification_for",
    "instruction",
    "resolutions_in",
    "rewrite",
    "rewritten_with",
    "said_as",
]
