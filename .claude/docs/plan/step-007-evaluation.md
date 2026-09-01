# Step 007 — Evaluation: measure Veritas over a Gold Question Set

**Status:** **active** — approved by Amino on 2026-09-01, by the commit that carries
this plan. 7.1 is built and approved. Next: Sub-step 7.2.

**Goal.** Build Evaluation — the committed Gold Question Set and the Evaluation
Measures over it: hit rate and Mean Reciprocal Rank (MRR) for Retrieval,
Execution Accuracy and LLM-as-judge for generation — so every retrieval and
generation choice so far made on taste is settled on evidence.

**Moves Current State by:** seven of nine Target State components built → eight.
*"Nothing measures Veritas"* leaves [Known gaps](../design/current-state.md#known-gaps):
the four Retrieval Strategies are compared on measured numbers for the first
time, and the [Zoomcamp rows](../design/target-state.md#zoomcamp-criteria-map)
for retrieval evaluation (*"hit rate and MRR across ≥3 approaches"*), LLM
evaluation (*"Execution Accuracy across ≥2 prompts and ≥2 models"*), hybrid
search and re-ranking get their evidence.

---

## One route decision: Observability moves to Step 008

The Resume-here pointer named this Step *"Evaluation and Observability"*.
Together they are six Sub-steps — the four below, the Postgres logger, the
Grafana dashboard — and the `planning-a-step` skill's sizing table says of six:
*"This is two Steps; ship the first."* So this Step is Evaluation alone;
Observability is Step 008, and Containerization with `README.md` is Step 009.
Against the 2026-09-09 deadline that re-slices
[Step 006's schedule](step-006-retrieval-and-orchestrator.md#why-delivery-mode-exists)
as ~2 + ~1.5 + ~2 days, with eight available. Consequence, taken by this
commit:
[DEBT-032](../debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by)
and
[DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)
said *"Step 007"* where their charting and logging Sub-steps now land in
Step 008 — each Trigger line carries a one-line amendment, the firing condition
itself unchanged.

---

## Sub-steps

### 7.1 — Write the Gold Question Set

`data/gold/` — one YAML file per Gold Question: the question as a person asks
it, the gold SQL, and the gold result. The relevant Semantic Entries are
**derived** from the gold SQL through the Gate's own readers, never listed by
hand — the Target State's *"Ground truth is derived"* — by the gold loader,
which is `veritas/evaluation/`'s first module. Coverage is
[DEBT-033](../debt-ledger.md#debt-033--the-generators-live-evidence-is-five-self-written-questions-and-four-certified-metrics-never-reach-it)'s:
all nine Certified Metrics, every question carrying a period, sliced and
refusal-shaped and Clarifying-Question-shaped questions included — and the
questions people actually say, DEBT-029's four phrasing classes, in the set as
data. [DEBT-004](../debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal)
and [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level):
a question turning on either Section C pair is scoped so the two sides differ
beyond the result comparison's tolerance — proven in the test — or left out
with the limitation stated in the Step Review.

*Verify:* `uv run pytest tests/test_gold.py` — every gold SQL is allowed by the
Gate and executes to its gold result; the coverage and tolerance constraints
hold.

### 7.2 — Register the phrasings and detect them

Pays [DEBT-029](../debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently).
Which spellings a broker says are Glossary content, so the
[Section D](../glossary.md#d-ambiguous-terms) amendment rides this Sub-step for
Amino's agreement. Each row's phrasings are carried as `aliases` on its
Ambiguous Term entry — the field `veritas/semantic/loader.py` already names as
a deferral — and detection matches an alias exactly as it matches the
registered name. Both directions are proven: the four-class miss test in
`tests/test_rewrite.py` inverts, and no Gold Question that names its meaning
becomes one Veritas asks back about.

*Verify:* `uv run pytest tests/test_rewrite.py tests/test_gold.py`

### 7.3 — Measure Retrieval: hit rate and MRR

Pays [DEBT-027](../debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match)
(*"Repayment is the measurement, not the split"*) and
[DEBT-030](../debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it).
A runner over `rank` — the seam 6.2 left for exactly this — scoring each Gold
Question's derived Relevant Set: one row per Retrieval Strategy per arm. The
arms: the flat searchable text against a per-field index, and the appended
rewrite against the spliced one, both rewrite forms built from the gold entry's
own resolution so the sweep costs no model call and no key. Keep what the
numbers support; the losing arms are dated evidence in the Step Review.

*Verify:* `uv run pytest tests/test_evaluation.py` — the measures on a known
toy ranking — then `uv run python -m veritas.evaluation retrieval`, output in
the review.

### 7.4 — Measure generation: Execution Accuracy and LLM-as-judge

Execution Accuracy over the Gold Question Set, across two prompts and the
registry's two models — the first Groq call ever made, which is
[ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md)'s
first accepted cost coming due. The prompt gains a variant seam in
`generate.py`; result sets are compared under the tolerance 7.1's constraints
were built against; a question gold-labelled as a refusal or a Clarifying
Question scores by ending the same way. LLM-as-judge is the second lens, its
prompt proven against a stub like every other model-reading test. The live
sweep is opt-in and its output is dated evidence in the review.

*Verify:* `uv run pytest tests/test_evaluation.py`, then
`VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation`, output
in the review.

---

## Not in this Step

- **Observability** — Postgres logging, Grafana, feedback capture in the App:
  Step 008, where DEBT-032 and DEBT-034 fire. Nothing regresses by the wait —
  nothing logs today, and this Step writes no logger.
- **Containerization and `README.md`** — Step 009.
- **Acting on what the measures say beyond the named arms.** A losing arm is
  recorded and the winner kept; a finding needing more than that becomes a
  Ledger entry, not silent scope.
- **DEBT-023, DEBT-024, DEBT-025** — their 2026-09-09 Trigger.
- **Multi-turn memory, charting, export** — Target State non-goals, permanently.
