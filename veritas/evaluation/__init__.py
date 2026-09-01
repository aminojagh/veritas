"""Evaluation — the Evaluation Measures Veritas is judged by, offline.

[`Evaluation`](../../.claude/docs/glossary.md#a-the-system) *"computes Evaluation
Measures over the Gold Question Set: hit rate and MRR for Retrieval, Execution Accuracy
and LLM-as-judge for generation. **Offline, against known-correct answers** — the
opposite pole from Observability."*

`gold.py` is the Gold Question Set: the Gold Questions, what each should come back as,
and each one's Relevant Set — the Semantic Entries its statement touches, derived rather
than listed.
"""

from veritas.evaluation.gold import (
    GOLD_DIR,
    GOLD_SCALE,
    RESULT_TOLERANCE,
    Expectation,
    GoldQuestion,
    GoldQuestionError,
    PhrasingClass,
    axes_touched,
    filtered_columns,
    join_paths_touched,
    load_gold_questions,
    metrics_touched,
    read_gold_question,
    reading_of,
    relevant_entries,
    same_result,
)

__all__ = [
    "GOLD_DIR",
    "GOLD_SCALE",
    "RESULT_TOLERANCE",
    "Expectation",
    "GoldQuestion",
    "GoldQuestionError",
    "PhrasingClass",
    "axes_touched",
    "filtered_columns",
    "join_paths_touched",
    "load_gold_questions",
    "metrics_touched",
    "read_gold_question",
    "reading_of",
    "relevant_entries",
    "same_result",
]
