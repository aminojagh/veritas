"""Evaluation — the Evaluation Measures Veritas is judged by, offline.

[`Evaluation`](../../.claude/docs/glossary.md#a-the-system) *"computes Evaluation
Measures over the Gold Question Set: hit rate and MRR for Retrieval, Execution Accuracy
and LLM-as-judge for generation. **Offline, against known-correct answers** — the
opposite pole from Observability."*

`gold.py` is the Gold Question Set: the Gold Questions, what each should come back as,
and each one's Relevant Set — the Semantic Entries its statement touches, derived rather
than listed. `retrieval.py` is the first pair of measures over it, hit rate and MRR;
`generation.py` is the second pair, Execution Accuracy and LLM-as-judge agreement; and
`__main__.py` is the command that prints either.
"""

from veritas.evaluation.generation import (
    JUDGE_RULES,
    EndedBy,
    GenerationMeasures,
    Scored,
    answerable_by_veritas,
    correctly_answered,
    ended_as,
    ended_by,
    judge,
    judgement_of,
    judgement_text,
    measure_generation,
    score,
)
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
from veritas.evaluation.retrieval import (
    RetrievalMeasures,
    gold_resolutions,
    measure_retrieval,
    measures_of,
    reciprocal_rank,
    scored,
    searchable_relevant_set,
    searched_as,
)

__all__ = [
    "GOLD_DIR",
    "GOLD_SCALE",
    "JUDGE_RULES",
    "RESULT_TOLERANCE",
    "EndedBy",
    "Expectation",
    "GenerationMeasures",
    "GoldQuestion",
    "GoldQuestionError",
    "PhrasingClass",
    "RetrievalMeasures",
    "Scored",
    "answerable_by_veritas",
    "axes_touched",
    "correctly_answered",
    "ended_as",
    "ended_by",
    "filtered_columns",
    "gold_resolutions",
    "join_paths_touched",
    "judge",
    "judgement_of",
    "judgement_text",
    "load_gold_questions",
    "measure_generation",
    "measure_retrieval",
    "measures_of",
    "metrics_touched",
    "read_gold_question",
    "reading_of",
    "reciprocal_rank",
    "relevant_entries",
    "same_result",
    "score",
    "scored",
    "searchable_relevant_set",
    "searched_as",
]
