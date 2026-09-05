"""Evaluation's entry point.

    uv run python -m veritas.evaluation retrieval                        # hit rate, MRR
    VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation  # accuracy

    # one provider, as many of its models as are named — the published grid is every
    # (model, prompt) combination of these; --no-judge halves the calls when a run is
    # only ranking candidates against each other
    VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation \\
        --provider openai --model <name> --model <another>

Prints the Evaluation Measures for one part of Veritas over the Gold Question Set. It
computes nothing itself: `retrieval.py` and `generation.py` hold the measures and the
sweeps, and this file is the table they are read in.

Both need the built Warehouse — a Relevant Set is derived through the Validation Gate's
own readers, and those resolve a statement against the live schema.

**`retrieval` costs nothing and `generation` spends a key.** The retrieval sweep
resolves each question's Ambiguous Terms from its own gold SQL rather than from a model;
the generation sweep is the measure of what a model actually writes, so it calls every
provider in the registry a few hundred times and refuses to start without the consent
`LIVE_VARIABLE` carries.
"""

import argparse
import os

from veritas.evaluation.generation import (
    GenerationMeasures,
    answerable_by_veritas,
    measure_generation,
)
from veritas.evaluation.gold import GOLD_DIR, GoldQuestion, load_gold_questions
from veritas.evaluation.retrieval import (
    RetrievalMeasures,
    measure_retrieval,
    scored,
    searched_as,
)
from veritas.llm import (
    DEFAULT_PROVIDER,
    ENV_FILE,
    LIVE_VARIABLE,
    PROVIDER_VARIABLE,
    PROVIDERS,
    default_model,
    registered_models,
)
from veritas.orchestrator import (
    DEFAULT_PROMPT_FORM,
    DEFAULT_REWRITE_FORM,
    PromptForm,
    RewriteForm,
)
from veritas.retrieval import DEFAULT_SEARCHABLE_FORM, TOP_K, Retriever, SearchableForm
from veritas.validation import ValidationGate
from veritas.warehouse import DATABASE_PATH, WarehouseAdapter

REPO_ROOT = DATABASE_PATH.parent.parent

# The setting Veritas runs under today, which is the row a reader compares the others
# against. The two defaults themselves, so the mark moves when either of them does.
TODAY = (DEFAULT_SEARCHABLE_FORM, DEFAULT_REWRITE_FORM)

# The mark itself, on whichever row of either table is what Veritas does today.
HERE = "  <- today"


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
        marked = HERE if (searchable_form, rewrite_form) == TODAY else ""
        measured = "  ".join(
            f"{cells.get(strategy, '—'):<{width}}" for strategy in strategies
        )
        lines.append(
            f"  {str(searchable_form):<10}  {str(rewrite_form):<8}  {measured}{marked}"
        )
    return lines


def retrieval(warehouse: WarehouseAdapter, options: argparse.Namespace) -> int:
    """Score every setting of Retrieval over the Gold Question Set and print the table.

    Takes `options` to share one signature with the sweep beside it and reads nothing
    from it: every flag there selects a model or a judge, and this sweep calls neither.
    """
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


def measured(right: int, of: int, rate: float) -> str:
    """One rate and the counts it is over, because a rate whose denominator is not
    beside it can be read as any of three different numbers here."""
    return f"{right}/{of} {rate:.3f}"


def generation_table(rows: list[GenerationMeasures], today: str) -> list[str]:
    """The sweep as one line per prompt per model, one column per Evaluation Measure.

    Agreement prints `—` where nothing was judged — a run with no judge, and a judge that
    abstained on every question, are the same absence. The rate itself would be `0.000`
    over an empty denominator, which reads as a judge that disagreed with everything.
    """
    width = max(len("model"), *(len(row.model) for row in rows))
    lines = [
        f"  {'prompt':<6}  {'model':<{width}}  {'ending':>7}  "
        f"{'execution accuracy':>18}  {'judge agreement':>15}"
    ]
    for row in rows:
        right, asked = row.right_ending
        executed, judged = row.executed, row.judged
        accuracy = measured(
            sum(one.correct for one in executed), len(executed), row.execution_accuracy
        )
        agreement = (
            measured(
                sum(bool(one.agrees) for one in judged), len(judged), row.judge_agreement
            )
            if judged
            else "—"
        )
        setting = (row.prompt_form, row.model)
        lines.append(
            f"  {str(row.prompt_form):<6}  {row.model:<{width}}  "
            f"{f'{right}/{asked}':>7}  {accuracy:>18}  {agreement:>15}"
            f"{HERE if setting == (DEFAULT_PROMPT_FORM, today) else ''}"
        )
    return lines


def failures(rows: list[GenerationMeasures]) -> list[str]:
    """Every question each row got wrong, which step of the flow ended it, and — where it
    ended in a refusal or never reached a model — the sentence that says which.

    A wrong answer and a correct statement the Validation Gate refused score zero
    identically, so a table of rates alone cannot say whether a low figure is the
    generator's. This is what says. The sentence is printed because the step says which
    of them refused and not what it said, and a run comparing one prompt against another
    cannot be read from a count of refusals alone. A row that
    never reached a model prints what the provider said for the same reason: the step
    alone leaves a reader with a failed sweep and nothing to fix.
    """
    lines: list[str] = []
    for row in rows:
        lines.append(f"  {row.prompt_form} · {row.model}")
        for one in row.failed:
            lines.append(
                f"    ended by {str(one.ended_by):<10} wanted "
                f"{str(one.gold.expects):<19} {one.gold.name}"
            )
            if one.provider_error:
                lines.append(f"      unreachable: {one.provider_error}")
            elif one.answer is not None and one.answer.refusal:
                lines.append(f"      said: {one.answer.refusal}")
        if not row.failed:
            lines.append("    nothing — every question ended the way the set says")
    return lines


def excluded(
    questions: list[GoldQuestion], gate: ValidationGate
) -> list[GoldQuestion]:
    """The Gold Questions no model could get right, because Veritas may not run the
    statement the set itself calls correct."""
    return [gold for gold in questions if not answerable_by_veritas(gold, gate)]


def generation(warehouse: WarehouseAdapter, options: argparse.Namespace) -> int:
    """Score every prompt against every registered model over the Gold Question Set.

    Asks for consent before spending anything, the way the tests that call a real
    provider do: this is a few hundred calls to every provider in the registry, and a
    key sitting in `.env` so the App can answer a question is not consent to spend it on
    a sweep nobody has asked for.

    `options` narrows what is spent: which providers run, which model the one named
    serves, and whether a judge runs at all. The published figures come from the run
    that narrows nothing.
    """
    if not os.environ.get(LIVE_VARIABLE):
        print(
            f"FAIL — this sweep calls every registered provider once per Gold Question "
            f"per prompt, and again to judge each answer. Set {LIVE_VARIABLE}=1 to "
            f"spend the keys in {ENV_FILE.name}"
        )
        return 1

    gate = ValidationGate(warehouse)
    retriever = Retriever(gate.semantic)
    questions = load_gold_questions()
    beyond = excluded(questions, gate)
    scorable = [gold for gold in questions if gold not in beyond]

    models = registered_models(options.provider, options.model)
    judge_model = None if options.no_judge else default_model()
    # What Veritas does today is the configured provider on its **registered** model. A
    # run that names candidates marks the row that is that pair and no other, so a grid
    # comparing the shipped setting against the rest says which one ships.
    configured = os.environ.get(PROVIDER_VARIABLE) or DEFAULT_PROVIDER
    today = f"{configured} {PROVIDERS[configured].default_model}"

    print(f"  gold          {GOLD_DIR.relative_to(REPO_ROOT)} — {len(questions)} Gold "
          f"Questions, {len(scorable)} of them scored")
    for gold in beyond:
        print(f"  excluded      {gold.name!r} — the Validation Gate refuses the "
              f"statement the set itself calls correct, so no model can answer it")
    print(f"  prompts       {', '.join(str(form) for form in PromptForm)}")
    print(f"  models        {', '.join(models)}")
    print(f"  judge         {judge_model.model}, on every scored question"
          if judge_model is not None
          else "  judge         none — this run ranks by Execution Accuracy alone")
    print()

    if not scorable:
        print("FAIL — no Gold Question has a gold statement the Validation Gate allows")
        return 1

    rows = measure_generation(
        scorable, warehouse, gate, retriever, models, judge_model=judge_model
    )
    for line in generation_table(rows, today):
        print(line)
    print()
    for line in failures(rows):
        print(line)
    print()

    unreached = sum(len(row.unreached) for row in rows)
    if unreached:
        print(f"FAIL — {unreached} question(s) never reached a model, so these figures "
              f"are over fewer answers than they claim")
        return 1
    print("PASS — Execution Accuracy and LLM-as-judge agreement for every prompt "
          "against every registered model")
    return 0


# Which sweep each word on the command line runs. A dispatch table rather than a match,
# so the choices argparse offers and the functions it reaches are one list.
MEASURES = {"retrieval": retrieval, "generation": generation}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "measure",
        choices=sorted(MEASURES),
        help="which part of Veritas to score over the Gold Question Set",
    )
    parser.add_argument(
        "--provider",
        action="append",
        choices=sorted(PROVIDERS),
        help="a registered provider to sweep, repeatable; every one of them by default",
    )
    parser.add_argument(
        "--model",
        action="append",
        help="a model to run on the named provider instead of the one its registry row "
             "serves, repeatable; needs exactly one --provider",
    )
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="run no LLM-as-judge, halving the calls: a run ranking models against each "
             "other is read off Execution Accuracy alone",
    )
    options = parser.parse_args()
    chosen = options.measure

    if not DATABASE_PATH.exists():
        print(
            f"FAIL — no Warehouse at {DATABASE_PATH.relative_to(REPO_ROOT)}. A Relevant "
            f"Set is derived against the live schema: run "
            f"`uv run python -m veritas.ingestion` first"
        )
        return 1
    sweep = MEASURES[chosen]
    with WarehouseAdapter() as warehouse:
        return sweep(warehouse, options)


if __name__ == "__main__":
    raise SystemExit(main())
