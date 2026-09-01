"""The Orchestrator — the sequence a question runs through, and the failure paths.

It owns none of the steps that have a component of their own: Retrieval searches, the
Validation Gate judges, the Warehouse Adapter executes. `flow.py` is the sequence;
`rewrite.py` and `generate.py` hold the two steps that have no other home — resolving
Ambiguous Terms, and grounding a model in retrieved entries to compose SQL out of
certified expressions; and `answer.py` is the Grounded Answer the whole flow returns.
"""

from veritas.orchestrator.answer import GroundedAnswer, Lineage
from veritas.orchestrator.flow import Orchestrator
from veritas.orchestrator.generate import (
    GENERATION_RULES,
    GROUNDED_FIELDS,
    Generated,
    entry_text,
    field_text,
    generate,
    generation_instruction,
    grounding,
    scope_text,
)
from veritas.orchestrator.rewrite import (
    PLACEHOLDER,
    RESOLUTION_RULES,
    Rewrite,
    ambiguous_terms_in,
    clarifying_question_for,
    first_said,
    resolution_instruction,
    resolutions_in,
    rewrite,
    rewritten_with,
    said_as,
    spellings,
)

__all__ = [
    "GENERATION_RULES",
    "GROUNDED_FIELDS",
    "Generated",
    "GroundedAnswer",
    "Lineage",
    "Orchestrator",
    "PLACEHOLDER",
    "RESOLUTION_RULES",
    "Rewrite",
    "ambiguous_terms_in",
    "clarifying_question_for",
    "entry_text",
    "field_text",
    "first_said",
    "generate",
    "generation_instruction",
    "grounding",
    "resolution_instruction",
    "resolutions_in",
    "rewrite",
    "rewritten_with",
    "said_as",
    "scope_text",
    "spellings",
]
