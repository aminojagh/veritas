# Step 008 — Observability: record every question and chart it

**Status:** **active** — approved by Amino on 2026-09-03, by the commit that carries
this plan and its two Term Proposals. Next: Sub-step 8.5 — 8.1 (`2cf4170`), 8.2
(`b75bdda`) and 8.3 (`f9b7bef`) are committed, and 8.4 is approved and staged. The
status turns `done` by the commit that closes 8.5.

**Goal.** Build Observability — every question a person asks, recorded in Postgres
with its Grounded Answer, Validation Gate outcome, Lineage, cost, latency and Feedback,
and a Grafana dashboard over those rows — so what Veritas does at runtime is a chart
rather than a description.

**Moves Current State by:** eight of nine Target State components built → **nine**.
*"Nothing logs a question, a verdict, a cost or a latency"* leaves
[Known gaps](../design/current-state.md#known-gaps), and with it the Lineage gap
([DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)).
The [Zoomcamp row](../design/target-state.md#zoomcamp-criteria-map) for Monitoring —
*"Feedback capture + Grafana dashboard, ≥5 charts — including Validation-Gate
rejections by reason and metric-usage frequency"* — gets its evidence, and two of the
three services the Containerization row names arrive; the App's own container is
Step 009's.

---

## Three route decisions

1. **The Orchestrator measures; the App records.** `Orchestrator.answer()` keeps its
   signature and gains the Operational Measures of the question it just ran, and the
   App is the one caller that writes them to the log. So the Evaluation sweep drives
   the same flow and puts nothing on the dashboard — Observability is *"live traffic,
   no ground truth"* ([Glossary](../glossary.md#a-the-system)) — and a person sees
   their answer before the log's verdict on it, because the write comes after the
   render and a failed write is a warning beside an answer rather than instead of one.
2. **Postgres is reached through one seam, the way the Warehouse is.** `QuestionLog`
   is the interface, `veritas/observability/` holds the only module that imports
   `psycopg`, the schema is one Data Definition Language (DDL) file applied
   idempotently on connect, and every other test drives a test double the way the
   model tests drive a stub. The tests that need a real server skip without one and
   the Step Review runs them with it up. No ADR: Postgres and Grafana are the Target
   State's own row, agreed 2026-08-03.
3. **The model seam's reply carries its usage and its wall time.** `complete()`
   returns the text with the prompt tokens, completion tokens and seconds the call
   took; the three callers and four test stubs follow. Cost is tokens × a price per
   registered model, `NULL` for a model the table does not price — never zero. A
   price is neither a definition nor a measurement of Veritas and goes stale silently,
   so each row carries the date it was read and the page it was read from, and the
   Ledger entry 8.3 opens says when it is re-read.

---

## Sub-steps

### 8.1 — Choose the OpenAI default model by measurement

**Rewritten 2026-09-03, after its first attempt failed.** That attempt did exactly what
[DEBT-037](../debt-ledger.md#debt-037--nothing-tells-the-generator-that-a-date-it-has-never-heard-of-is-not-a-reason-to-refuse)'s
Trigger prescribes — the list of reasons to refuse closed in both prompt forms, a
sentence in each saying an unfamiliar period is not on it — and across three wordings and
three sweeps **no figure moved**. Its
[review section](../reviews/step-008-observability.md#sub-step-81--tell-the-generator-an-unknown-period-is-not-a-reason-to-refuse)
carries the table and stays as the record. The Ledger entry is not paid — what changes
is which model OpenAI's registry row names, and the entry's cost falls out rather than
being repaid — and it is **closed `accepted`** in the second review section: prose was
measured not to work, the honest fix is barred by ADR-0001 and CLAUDE.md, and the
generation sweep is the standing guard. Still first in the Step, for the reason it
always was — the dashboard's first traffic should show what Veritas decides, not one
model's habit.

**Revert first.** `GENERATION_RULES` and `GENERATION_SHAPE` go back to their 7.4 text,
closed list and date sentence alike, and `UNFAMILIAR_PERIOD` leaves
`tests/test_orchestrator.py`. Candidates are then measured against the prompt Veritas
actually shipped, so a result is the model's and not a model and a prompt moving
together. The printed refusal reasons in `failures()` stay — they only print, they are
what made the first attempt legible, and nothing a model sees changes.

**Confirm the candidates exist before spending anything.** One `/v1/models` call covers
`gpt-5-mini`, `gpt-5.4-nano`, `gpt-5.4-mini` and `gpt-5.6-luna`; if any of the four is
missing the Sub-step **stops and reports** rather than substituting a neighbour, because
[ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md)'s own row
named a model until the first call returned a 404. Price per 1M input tokens is not on
that endpoint and comes off the pricing page, recorded with the date read and the page
read from — which is the form
[route decision 3](#three-route-decisions) needs for 8.3's cost column, bought early.

**The bar, and the order.** Candidates run cheapest first, in the order the fetched
prices give rather than an assumed one. groq's `openai/gpt-oss-120b` is the mark, last
measured 2026-09-03: ending **22/23**, Execution Accuracy **10/11**. The first candidate
to reach both is the winner — **no confirming re-run**, ruled by Amino on 2026-09-03 as
the Sub-step started: the first run is enough. (The ruling stands on its own; do not
justify it by the pinned temperature, which the Sub-step went on to measure as *not*
giving two identical runs — see its review.) If none reaches the mark, the best of the
four wins instead — but
it replaces `gpt-4o-mini` only if it also beats `gpt-4o-mini`'s 14/23 and 2/11, so a
measurement cannot install a default worse than the incumbent. Those two figures need no
re-run either: the revert restores the prompt they were measured under, twice.

**Ranking sweeps are OpenAI-only and judge-free.** `veritas/evaluation/__main__.py`
gains a flag selecting which registered clients a sweep runs, so a candidate costs one
provider rather than two; `measure_generation` already takes `judge_model=None`, which
halves the calls again. The table prints `—` for agreement where nothing was judged —
today it would print `0/0 0.000`, which reads as a judge that disagreed with everything.

**Then one published sweep.** The winner becomes OpenAI's `default_model` and, by being
the default, the judge; ADR-0005's table row is amended with the measurement that moved
it, as that ADR already does for the groq row it replaced. That sweep is the full one —
both prompts, both registered providers, one judge — so the
[Zoomcamp](../design/target-state.md#zoomcamp-criteria-map) row's *"≥2 prompts and ≥2
models"* is one dated table rather than rows spliced from two runs judged by two models.
It is the only groq call in the Sub-step.

**Not here.** Retiring groq and carrying a second **OpenAI** model in its place: the
registry is keyed by provider and holds one model each, so that cannot be expressed
without reworking the seam, and a seam is not something to hack behind
([CLAUDE.md](../../../CLAUDE.md)). Nor a runtime failover from one model to another.

*Verify:* `uv run pytest tests/test_orchestrator.py tests/test_evaluation.py`, then the
published sweep. The review gains a **second** section — titled for this attempt, not
the first, so both anchors resolve — carrying the price table, the per-candidate figures
and the final table.

### 8.2 — Lineage records what the statement used

Pays [DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used).
The Validation Gate outcome gains the Certified Metrics the statement's expressions
traced to, the axes it sliced by and the Join Paths its route was certified by —
three lists the rules already compute and discard — with empty defaults, so the
frozen probes in `.claude/scripts/check_validation_gate/` read a verdict unchanged
and the three outcomes `tests/test_app.py` builds by hand still build.
`lineage_of` reads them: the resolved Ambiguous Terms lead as today, then what the
statement used, so a refused question's Lineage is the terms alone. The App labels a
single figure with its metric's `unit` and Reporting Currency, which this makes
identifiable. Nothing reads what was retrieved — `veritas/evaluation/` scores
`rank` directly — so that list leaves the Grounded Answer rather than moving.

*Verify:* `uv run pytest tests/test_gate.py tests/test_orchestrator.py tests/test_app.py`
— a `Gross Revenue` answer cites `Gross Revenue` and not `Net Revenue`; a refusal
cites nothing it did not use; the figure carries its unit.

### 8.3 — Record every question a person asks

`veritas/observability/`: the `QuestionLog` seam, `schema.sql`, and the Postgres
implementation. **One row per question** — asked, rewritten, the step that ended it,
the SQL, the row count, the Validation Gate outcome with its Rejection Reasons, the
Access Profile's role, seconds and cost — **one per Lineage entry** with its kind and
version, **one per model call** with its provider, model, tokens and seconds.
`docker-compose.yml` arrives with Postgres; its credentials are generated values in
`.env.example`, read by compose and by the App alike, so there is one set. The App
records after it renders, and its sidebar says whether questions are being recorded.

**Pays [DEBT-032](../debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by)
ahead of its Trigger**, because the row's *ending* column is the thing 8.5 groups by
and a column is a taxonomy or it is prose: `EndedBy` moves from `veritas/evaluation/`
to the Grounded Answer it is read off, and its `no sql` member — which today carries
*"the model refused"* and *"nothing retrieved defines a Certified Metric"* as one — is
split into the two the Orchestrator decides. Evaluation then reads one taxonomy rather
than owning a coarser copy.

*Verify:* `uv run pytest tests/test_observability.py tests/test_app.py` — a test
double proves what the App writes and when; then
`docker compose up -d postgres && uv run pytest tests/test_observability.py` proves
the DDL and the Postgres implementation against a real server, output in the review.

### 8.4 — Leave Feedback on a Grounded Answer

Term Proposal below. Under every Grounded Answer the App offers a verdict — up or
down — and an optional sentence, written to the log against the row 8.3 recorded, so
Feedback on an answer is Feedback on *that* SQL, Lineage and verdict and never on a
question string that a later answer might match. The latest verdict on an answer
stands.

*Verify:* `uv run pytest tests/test_app.py tests/test_observability.py` — Feedback
lands on the row of the answer it was left on and on no other; a second verdict
replaces the first.

### 8.5 — The Grafana dashboard

`grafana/` holds the Postgres datasource and one dashboard as provisioning files, so
`docker compose up` opens the dashboard with nothing clicked; `docker-compose.yml`
gains Grafana. Seven charts, each one query over 8.3's rows: questions over time by
ending · Validation Gate rejections by Rejection Reason · metric-usage frequency, from
the Lineage of answered questions · latency, per question and per model call · cost
by model · Feedback, up against down · refusals by reason across every `EndedBy`
member. `tests/test_observability.py` reads the dashboard file: at least five panels,
the two the rubric names present by title, and every panel's SQL executes against the
schema when Postgres is reachable — a chart whose query breaks on the next schema
change should fail a test, not a demo.

*Verify:* `docker compose up -d && uv run pytest tests/test_observability.py`, then
the dashboard loaded on questions asked in the browser, screenshot in the review.

---

## Not in this Step

- **The App's container and `README.md`** — Step 009. The compose file arrives here
  with two services and gains its third there.
- **[DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)**,
  `Account Value` — now `L`: a Gate rule *and* a generation rule, measured across
  both prompts again. Nothing here fires it. Whether it is paid before submission is
  Amino's call with the schedule below in hand; if not, Step 009's README states it.
- **A question the provider did not answer is not recorded.** It is not a Grounded
  Answer — `flow.py` raises rather than ending — and the App already says so on the
  page. The Target State says *"every question"*, so 8.3 opens a Ledger entry for it
  rather than widening the log to a row with no answer in it.
- **Clustering refusals into an authoring backlog** —
  [EXT-004](../extension-register.md#ext-004--coverage-miss-capture). This Step builds
  the seam it lands on and not the clustering.
- **DEBT-023, DEBT-024, DEBT-025** — their 2026-09-09 Trigger.
- **[DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it)**
  (`gpt-5.4-mini` answers *"show me ten trades"*) and
  **[DEBT-039](../debt-ledger.md#debt-039--the-published-two-provider-sweep-failed-its-own-runner-and-is-not-republished)**
  (the failed two-provider sweep owes one re-run) — both opened by 8.1, both with
  Triggers that postpone them to a later Sub-step, the documentation pass, or submission.
- **Cloud deployment; multi-turn memory, charting of answers, export** — outside the
  slice by the Target State's own word.

---

## Language

Two unregistered nouns become a class, a table and a widget in this Step. Both were
proposed with the plan and **agreed with it on 2026-09-03**; they are
[Glossary](../glossary.md#a-the-system) Section A rows, and the Sub-step that makes
each one code spells it as registered.

> 🆕 **TERM PROPOSAL** — `Question Log`: the record Observability keeps — one row per
> question a person asked through the App, carrying its Grounded Answer, Validation
> Gate outcome, Lineage, Operational Measures and Feedback. The seam
> `veritas/observability/` exposes and the tables behind it.
> [EXT-004](../extension-register.md#ext-004--coverage-miss-capture) had said *"the
> Observability question log"* since Step 001 without registering it, and now spells
> the seam as registered.

> 🆕 **TERM PROPOSAL** — `Feedback`: what a person says about a Grounded Answer they
> were shown — a verdict, up or down, and optionally a sentence — attached to that
> answer's Question Log row and never to the question text alone. The one of
> `Operational Measure`'s four (*"cost, latency, Validation Gate outcome, and user
> feedback"*, now spelled `Feedback` there) with no row of its own.

`EndedBy`, `Reply` and `ModelCall` coin nothing: the first exists, the other two are
process words for a model's reply and one call to it.

---

## Schedule

Measured 2026-09-02 by `git log --numstat --format= <range> -- <dir>` over each
Step's commit range, with the dates from `git log --format='%h %ad'`:

| Step | days | `veritas/` | `tests/` | `.claude/docs/` | docs ÷ (code + tests) |
|---|---|---|---|---|---|
| 006 `fdf0dc4..814b07b` | 2.8 | 2,255 | 1,719 | 1,334 | 0.34× |
| 007 `814b07b..cf64d28` | 1.2 | 1,909 | 1,427 | 1,076 | 0.32× |

Against the 2.5×–14× the [Step 006 plan](step-006-retrieval-and-orchestrator.md#why-delivery-mode-exists)
measured before Delivery Mode, the overhead is a third of the code rather than a
multiple of it. This Step is about Step 007's size — roughly 1,000 product lines plus
a hand-written dashboard file, and 700 of tests — but carries three Ledger payments
the [Step 007 plan](step-007-evaluation.md#one-route-decision-observability-moves-to-step-008)'s
*"~1.5"* did not count, and a dashboard is checked by eye. **Estimate: 2 days.**
Step 009 — the App's Dockerfile, the compose file's third service, the README with
its credential list, and a fresh-clone rehearsal — is ~1.5. **Projected finish:
2026-09-06, submission 2026-09-07, two days inside the 2026-09-09 deadline.** The
Delivery Mode schedule of 2026-08-29 needed ten of eleven days and finished on
2026-09-08; Step 006 came in at 2.8 against 4.5 and Step 007 at 1.2 against 2, so
the project is one to two days ahead of it, and the slack is exactly one `L` entry
wide.
