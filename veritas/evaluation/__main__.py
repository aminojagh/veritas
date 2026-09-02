"""Evaluation's entry point.

    uv run python -m veritas.evaluation retrieval    # hit rate and MRR, every setting

Prints the Evaluation Measures for one part of Veritas over the Gold Question Set. It
computes nothing itself: `retrieval.py` holds the measures and the sweep, and this file
is the table they are read in.

Needs the built Warehouse — a Relevant Set is derived through the Validation Gate's own
readers, and those resolve a statement against the live schema — and no key and no
network, because the sweep resolves each question's Ambiguous Terms from its own gold
SQL rather than from a model.
"""

import argparse

from veritas.evaluation.gold import GOLD_DIR, load_gold_questions
from veritas.evaluation.retrieval import (
    RetrievalMeasures,
    measure_retrieval,
    scored,
    searched_as,
)
from veritas.orchestrator import DEFAULT_REWRITE_FORM, RewriteForm
from veritas.retrieval import DEFAULT_SEARCHABLE_FORM, TOP_K, SearchableForm
from veritas.validation import ValidationGate
from veritas.warehouse import DATABASE_PATH, WarehouseAdapter

REPO_ROOT = DATABASE_PATH.parent.parent

# The setting Veritas runs under today, which is the row a reader compares the others
# against. The two defaults themselves, so the mark moves when either of them does.
TODAY = (DEFAULT_SEARCHABLE_FORM, DEFAULT_REWRITE_FORM)


def cell(row: RetrievalMeasures) -> str:
    """One strategy's two measures, hit rate then MRR."""
    return f"{row.hit_rate:.3f} {row.mrr:.3f}"


def retrieval_table(rows: list[RetrievalMeasures]) -> list[str]:
    """The sweep as one line per setting, one column per Retrieval Strategy."""
    strategies = list(dict.fromkeys(row.strategy for row in rows))
    by_setting: dict[tuple[SearchableForm, RewriteForm], dict[str, str]] = {}
    for row in rows:
        setting = (row.searchable_form, row.rewrite_form)
        by_setting.setdefault(setting, {})[row.strategy] = cell(row)

    width = max(len("hit   mrr"), *(len(str(strategy)) for strategy in strategies))
    header = "  ".join(f"{str(strategy):<{width}}" for strategy in strategies)
    lines = [
        f"  {'searchable':<10}  {'rewrite':<8}  {header}",
        f"  {'':<10}  {'':<8}  " + "  ".join(f"{'hit   mrr':<{width}}" for _ in strategies),
    ]
    for (searchable_form, rewrite_form), cells in by_setting.items():
        marked = "  <- today" if (searchable_form, rewrite_form) == TODAY else ""
        measured = "  ".join(
            f"{cells.get(strategy, '—'):<{width}}" for strategy in strategies
        )
        lines.append(
            f"  {str(searchable_form):<10}  {str(rewrite_form):<8}  {measured}{marked}"
        )
    return lines


def retrieval(warehouse: WarehouseAdapter) -> int:
    """Score every setting of Retrieval over the Gold Question Set and print the table."""
    gate = ValidationGate(warehouse)
    questions = load_gold_questions()
    wanted = scored(questions, gate)
    rewritten = sum(
        searched_as(gold, gate, RewriteForm.APPENDED)
        != searched_as(gold, gate, RewriteForm.SPLICED)
        for gold, _ in wanted
    )

    print(f"  gold          {GOLD_DIR.relative_to(REPO_ROOT)} — {len(questions)} Gold "
          f"Questions, {len(wanted)} with a Relevant Set a search can return")
    print(f"  scored        {sum(len(relevant) for _, relevant in wanted)} relevant "
          f"entries across them, at top_k = {TOP_K}")
    print(f"  rewrite       {rewritten} of the {len(wanted)} say an Ambiguous Term, so "
          f"the two rewrite forms differ on those and agree on the rest")
    print()

    if not wanted:
        print("FAIL — no Gold Question has a Relevant Set a search could return")
        return 1

    for line in retrieval_table(measure_retrieval(questions, gate)):
        print(line)
    print()
    print("PASS — hit rate and Mean Reciprocal Rank (MRR) for every Retrieval Strategy "
          "under every setting")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "measure",
        choices=["retrieval"],
        help="which part of Veritas to score over the Gold Question Set",
    )
    parser.parse_args()

    if not DATABASE_PATH.exists():
        print(
            f"FAIL — no Warehouse at {DATABASE_PATH.relative_to(REPO_ROOT)}. A Relevant "
            f"Set is derived against the live schema: run "
            f"`uv run python -m veritas.ingestion` first"
        )
        return 1
    with WarehouseAdapter() as warehouse:
        return retrieval(warehouse)


if __name__ == "__main__":
    raise SystemExit(main())
