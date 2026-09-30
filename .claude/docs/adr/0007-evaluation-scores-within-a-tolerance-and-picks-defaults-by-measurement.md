# ADR-0007 — Evaluation scores within a tolerance, and picks defaults by measurement

- **Status:** accepted

## Context

Evaluation publishes figures about Veritas itself: hit rate and Mean Reciprocal Rank
(MRR) for Retrieval, Execution Accuracy and an LLM-as-judge's agreement with it for
generation. Each figure rests on judgements a reader cannot see from the figure: what
counts as the same answer, which of several settings the shipped system runs under,
and how far one run can be trusted. The rubric's LLM-evaluation row asks that
*"Multiple approaches are evaluated, and the best one is used"*, which makes the
second of those judgements a measurement rather than a taste.

## Decision

- **Two results are the same answer within `RESULT_TOLERANCE`**, a fraction of the
  larger figure (`veritas/evaluation/gold.py`). It is relative because the Certified
  Metrics span a count of dozens and a notional of tens of millions.
- **Every setting an Evaluation Measure can separate is chosen by the sweep that
  measures it**, and the shipped default is the best arm:
  - the Semantic Entry's searchable form and the rewrite form —
    `DEFAULT_SEARCHABLE_FORM` and `DEFAULT_REWRITE_FORM` — by
    `uv run python -m veritas.evaluation retrieval`, on MRR;
  - the prompt form and the OpenAI default model — `DEFAULT_PROMPT_FORM` and
    `PROVIDERS["openai"]` — by the (model, prompt) grid,
    `VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation`, on
    Execution Accuracy.
- **A Gold Question whose own gold statement the Validation Gate refuses is excluded
  from the generation denominator**, and derived rather than named: the sweep asks the
  Gate about each question's gold SQL.

## Alternatives considered

| Option | Why not |
|---|---|
| **Exact equality of result sets** | Refuses a correct statement written differently, over the rounding its arithmetic reaches, and refuses the six decimal places a gold result is written to. |
| **An absolute tolerance** | One figure cannot mean the same thing at a count of dozens and a notional of tens of millions. |
| **Defaults chosen by judgement, and the sweep run to report them** | The rubric asks for the best approach to be the one used, and a default nobody measured against its alternatives is a claim with no evidence behind it. |
| **Score every Gold Question, including one the Gate refuses** | Charges the model for the Gate's refusal, so no model can reach the ceiling and the grid compares the Gate against itself. |

## Consequences

**What this buys us.** Every published figure is reproducible by one named command,
and every default names the sweep that chose it.

**What this costs us.**

- **The tolerance is also the width inside which a wrong answer scores as correct.**
  A Gold Question may turn only on a Glossary Section C pair that separates by more
  than it. *Accepted* — `tests/test_gold.py` executes both halves of each pair a Gold
  Question turns on and fails the run if they are closer than `RESULT_TOLERANCE`.
- **Temperature zero is not determinism.** Every published generation figure is one
  run, and the same model, prompt and questions have scored one question apart across
  runs on the same day. A one-question difference is noise, and every rate has a
  margin nobody has quantified. *Accepted* — quantifying it costs a repeat of every
  sweep, and the differences the tables are read for are several times wider.
- **A small set moves in coarse steps.** Over the Gold Question Set, MRR and Execution
  Accuracy move a question at a time, and a measure every arm maxes out decides
  nothing. *Accepted* — the published tables say which measure decided.
- **The refusal list in the generation prompts is open**, so a model may refuse a
  period it has never heard of as though the Warehouse lacked it. Closing the list in
  prose relabels the refusal rather than stopping it, and stating the Warehouse's date
  coverage in the prompt would put schema-derived content in front of the model,
  against [ADR-0001](0001-semantic-layer-as-the-retrieval-corpus.md). *Accepted* —
  the generation sweep is the guard: a default model with the habit fails it before
  it ships.

**What it commits us to.** That a changed default is re-measured before it ships.
The signal that this has stopped holding is a default whose sweep row is not the best
one in the latest published table.

## Related

- [ADR-0005](0005-one-openai-compatible-endpoint-for-every-provider.md) — the model
  registry the grid sweeps.
- [ADR-0006](0006-every-certified-metric-follows-one-stated-book-convention.md) — the
  conventions that separate each Section C pair.
- Glossary: `Evaluation Measure`, `Execution Accuracy`, `Gold Question Set`,
  `Relevant Set`, `Retrieval Strategy`.
