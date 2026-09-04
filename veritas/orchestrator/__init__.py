"""The Orchestrator — the sequence a question runs through, and the failure paths.

It owns none of the steps that have a component of their own: Retrieval searches, the
Validation Gate judges, the Warehouse Adapter executes. `flow.py` is the sequence;
`rewrite.py` and `generate.py` hold the two steps that have no other home — resolving
Ambiguous Terms, and grounding a model in retrieved entries to compose SQL out of
certified expressions; and `answer.py` is the Grounded Answer the whole flow returns.
"""

from veritas.orchestrator.answer import EndedBy, GroundedAnswer, Lineage
from veritas.orchestrator.flow import Orchestrator
from veritas.orchestrator.generate import (
    DEFAULT_PROMPT_FORM,
    GENERATION_RULES,
    GENERATION_SHAPE,
    GROUNDED_FIELDS,
    Generated,
    PROMPT_FORMS,
    PromptForm,
    REWRITTEN_QUESTION,
    entry_text,
    field_text,
    generate,
    generation_instruction,
    grounding,
    scope_text,
)
from veritas.orchestrator.rewrite import (
    DEFAULT_REWRITE_FORM,
    PLACEHOLDER,
    RESOLUTION_RULES,
    REWRITE_FORMS,
    Rewrite,
    RewriteForm,
    ambiguous_terms_in,
    appended_with,
    clarifying_question_for,
    first_said,
    resolution_instruction,
    resolutions_in,
    rewrite,
    rewritten_with,
    said_as,
    said_throughout,
    spellings,
    spliced_with,
    without_overlaps,
)

__all__ = [
    "DEFAULT_PROMPT_FORM",
    "DEFAULT_REWRITE_FORM",
    "GENERATION_RULES",
    "GENERATION_SHAPE",
    "GROUNDED_FIELDS",
    "EndedBy",
    "Generated",
    "GroundedAnswer",
    "Lineage",
    "Orchestrator",
    "PLACEHOLDER",
    "PROMPT_FORMS",
    "PromptForm",
    "RESOLUTION_RULES",
    "REWRITE_FORMS",
    "REWRITTEN_QUESTION",
    "Rewrite",
    "RewriteForm",
    "ambiguous_terms_in",
    "appended_with",
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
    "said_throughout",
    "scope_text",
    "spellings",
    "spliced_with",
    "without_overlaps",
]
