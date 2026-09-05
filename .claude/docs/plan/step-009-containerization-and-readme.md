# Step 009 — Containerization and `README.md`: finish Veritas for submission

**Status:** **active** — written 2026-09-04 and approved by Amino the same day, by the
commit that carries this plan, with both [rulings](#rulings-at-approval) taken:
DEBT-035 is stated in the README, not paid, and 9.2 runs on the morning of
2026-09-05. **9.1, 9.2 and 9.3 are done**, all twenty-two of their sceptical points ruled on
2026-09-05, 9.2 in two attempts and under [ruling 3](#rulings-in-flight); 9.4 is next.

**Goal.** Put the App in the compose file beside Postgres and Grafana, write the
`README.md` a grader runs Veritas from, pay every Ledger entry whose Trigger names the
README or the submission, and rehearse the bring-up from a fresh clone — so the capstone
can be submitted.

**Moves Current State by:** nine of nine components built → **the slice complete and
submittable**. *"two of three services"* leaves
[What is built](../design/current-state.md#what-is-built). The
[Zoomcamp](../design/target-state.md#zoomcamp-criteria-map) rows for Containerization
and Reproducibility get their evidence, and the row the whole table hangs off — Problem
description — gets its document. The rubric that map was written against was fetched from
<https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md> on 2026-09-04, and
the map holds; the two rows this Step earns read, at 2 points, *"Everything is in
docker-compose"* and *"Instructions are clear, the dataset is accessible, it's easy to run
the code, and it works. The versions for all dependencies are specified."* Five Ledger
entries are paid on their own Triggers —
[DEBT-026](../debt-ledger.md#debt-026--the-retrieval-models-are-downloaded-rather-than-snapshotted),
[DEBT-039](../debt-ledger.md#debt-039--the-published-two-provider-sweep-failed-its-own-runner-and-is-not-republished),
[DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews),
[DEBT-040](../debt-ledger.md#debt-040--the-price-table-is-a-vendors-page-copied-once-and-nothing-notices-when-it-moves)
and
[DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it)
on its README branch — and
[DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)
is stated, not paid, by the first ruling. *(DEBT-039 closed `accepted` rather than paid,
under [ruling 3](#rulings-in-flight): the criterion its missing table served does not
exist, so four are paid and one is dissolved.)*

---

## Four route decisions

1. **The image carries everything a question needs except the key.** The Warehouse is
   built at image build from the committed snapshots — replay opens no socket and two
   runs are byte-identical — and both Retrieval models are fetched at image build into
   the directory fastembed's own `FASTEMBED_CACHE_PATH` names. That pays DEBT-026 on its
   Trigger, *"the Step that containerizes Veritas"*. The App builds Retrieval when the
   server starts rather than at the first question, so an image without the models fails
   at `up` and not in front of a person. Not a one-shot compose service writing a volume:
   the build is deterministic, and a volume is state nobody set.
2. **One `.env`, three readers, one value that differs.** Compose already reads `.env`
   for Postgres and Grafana; the App's service reads the same file through `env_file`,
   and the one value that differs inside the network — the host, `postgres` rather than
   `localhost` — is set in the service's `environment`, which wins over the file because
   `settings()` reads the environment first. `.env` never enters the image. The host
   path, `uv run streamlit run veritas/app/page.py`, stays as the developer's, unchanged.
3. **`README.md` is the grader's document.** Its sections follow the rubric's criteria in
   the rubric's order, so a grader ticks rows; every figure in it is quoted from a dated
   Step Review with the command that produced it; and it links into `.claude/docs/` for
   the working record rather than copying from it — CLAUDE.md: *"do not turn the README
   into a changelog"*. The decisions that move a number a reader will see are one table
   in `docs/decisions.md`, linked from the README — DEBT-013's *"one document, written in
   the reader's terms rather than ours"*. `docs/` is the public face beside `README.md`;
   `.claude/docs/` stays the working record.
4. **No ADR.** Compose with three services is the Target State's own row, agreed
   2026-08-03; where the Warehouse and the models live inside the image is fill behind
   that seam, reversible in an afternoon.

---

## Sub-steps

### 9.1 — The App runs in docker compose beside Postgres and Grafana

`Dockerfile` at the root: the interpreter `.python-version` pins, `uv sync --frozen
--no-dev`, `python -m veritas.ingestion` for the Warehouse, and `python -m
veritas.retrieval` — a new entry point that fetches both models into
`FASTEMBED_CACHE_PATH` and prints what it holds, so the Dockerfile names no model and the
two constants in `search.py` stay the one place that does. `.dockerignore` keeps `.env`,
`.venv/`, `scratch/`, the built Warehouse and the working record out of the image.
`docker-compose.yml` gains `app`: built from the Dockerfile, `env_file: .env`,
`POSTGRES_HOST: postgres`, started once Postgres is healthy, published on
`${APP_PORT:-8501}`, with a healthcheck on Streamlit's own `/_stcore/health`.
`.env.example` gains `APP_PORT`. The page calls `built()` on load rather than on the
first question.

`tests/test_container.py`: the compose file names three services, the App's depends on
Postgres being healthy and sets the host to the service name, the Dockerfile runs both
build-time commands; and, when the App answers on its published port, its health
endpoint does and the page carries the title — skipped otherwise, the Grafana test's
pattern.

*Verify:* `docker compose up -d --build --wait && uv run pytest tests/test_container.py
tests/test_observability.py`; then `docker run --rm --network none <the image compose
built> python -m veritas.retrieval` — both models present with the network off; then one
question asked at `http://localhost:8501` and seen on the dashboard at `:3000`. Image
size and build time are measured in the review, not guessed here.

### 9.2 — Republish the two-provider generation sweep

> **⚠ Superseded 2026-09-05 by [ruling 3](#rulings-in-flight).** The two-provider sweep
> failed its runner twice, and the criterion it was run for turned out not to exist. What
> 9.2 delivers instead is the **(model, prompt) grid over OpenAI**, and Groq is demoted
> from a measured alternative to a second registered provider. The Sub-step below is kept
> as written because it is what was approved and what the first attempt executed; the
> route now is the ruling.

Pays DEBT-039 on its Trigger. One command, unchanged, first thing on a day Groq's
200,000-token budget is unspent — nothing else calls Groq that day before it:

    VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation

Both prompts, both providers, one judge, one dated table in the review — the table the
README's LLM-evaluation row quotes. If Groq caps again the runner prints `FAIL`, the entry
stays open with a second date, and the README quotes the OpenAI rows as OpenAI-only.
**The defaults do not move on this run**: `DEFAULT_PROMPT_FORM` is `rules` on two runs
of the default model, and 8.1 measured one question as run-to-run variation, so a table
that contradicts it by one question is noise and by two is a finding for Amino to rule
on, not a change made here. DEBT-038's `ten trades` row is read off the same table.
Independent of 9.1; runs first thing on the morning of 2026-09-05, the second ruling's
day and the first try — `tests/` reach Groq only through a stub, and the App only
when `VERITAS_PROVIDER` says so, so nothing else spends the budget. A `FAIL` books
the next morning.

*Verify:* the command above and its whole table, `PASS` on its last line.

### 9.3 — `README.md`, with every credential and every limitation

The grader's document, in the rubric's order. **The problem** — silent metric ambiguity,
carried by the Gross-against-Net example, written for the grader rather than copied from
Target State. **The flow**, with the Semantic Layer as the knowledge base, and the
rewrite step, hybrid search and the re-ranker each named where the rubric's row is
earned. **Bring-up** — Docker and a key, `cp .env.example .env`,
`docker compose up --build`, the two ports — and the developer path beside it: `uv sync`,
ingestion, the App, `uv run pytest`. **The credential table**
[Target State](../design/target-state.md#what-credential-free-means) requires, all four
rows in its words. **Ingestion** — dlt, snapshot-and-replay, the seeded simulator,
*market data real, client activity synthetic*. **Evaluation** — the retrieval table from
the [7.3 review](../reviews/step-007-evaluation.md#sub-step-73--measure-retrieval-hit-rate-and-mrr)
and the generation table from 9.2, each dated with its command and the default it set.
**Monitoring** — the seven panels, the two images the
[8.5 review](../reviews/step-008-observability.md#sub-step-85--the-grafana-dashboard)
holds, Feedback. **What Veritas will not do and what it gets wrong**: no database
browsing ([DEBT-006](../debt-ledger.md#debt-006--no-ad-hoc-exploration--accepted-permanently));
the access-control sentence in
[DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s
own words; an eager model answering an ad-hoc row request with the nearest metric —
which pays DEBT-038 on its README branch, with the `ten trades` row as the count;
`Account Value` unanswerable, DEBT-035 stated in its own words as the first ruling
has it; cost figures as list
prices on the date the page was last read — which fires DEBT-040: the page re-read, the
five rows and the date updated, a groq row if one is priced anywhere readable; and a
reproducibility claim that says *"reproducible from committed snapshots"*, the wording
[DEBT-002](../debt-ledger.md#debt-002--market-prices-depend-on-an-unofficial-endpoint)'s
live trigger allows. One line points at `.claude/docs/` as the working record and one at
`docs/decisions.md`.

`tests/test_readme.py`: every variable `.env.example` declares is named in the README
and every variable the README names is declared there — Target State's *"must list every
credential"* as a test; the enforcement sentence is the Ledger's, character for
character, as `tests/test_app.py` already reads it; every relative link in `README.md`
and `docs/*.md` resolves, because `verify_framework.py` scans neither.

*Verify:* `uv run pytest tests/test_readme.py`, then `verify_framework.py` and
`check_language.py`.

### 9.4 — `docs/decisions.md`: the decisions that move a number

Pays DEBT-013 on its Trigger, *"the final documentation pass"*. One table, in the
reader's terms: the decision, the number it moves, what a reader should conclude on
seeing that number, and the dated review that argued it. The four rows the entry lists —
average cost basis, Realised P&L gross of Commission, the Snapshot calendar as an
intersection, the two sign conventions — and the ones the Steps since added: the result
tolerance two answers are compared under (7.1), the per-field index and the spliced
rewrite (7.3), `rules` as the prompt and `gpt-5.4-mini` as the model (7.4, 8.1),
temperature pinned at zero and measured not to be determinism (8.1), and a cost as a
list price read on a date (8.3). The Sub-step sweeps the Step 002–008 reviews for any
other. CLAUDE.md's Documents table gains the row.

*Verify:* `uv run pytest tests/test_readme.py` (the links), then `verify_framework.py`.

### 9.5 — Fresh-clone rehearsal, and the Step closes

Clone the repository into `scratch/` and follow `README.md` verbatim with nothing
remembered: copy `.env.example`, set the key, `docker compose up --build`, ask a
question, leave Feedback, open the dashboard; then the developer path — ingestion and
`uv run pytest` in the clone. Whatever the README got wrong is fixed here; whatever the
code got wrong goes back to the Sub-step that owns it. Then the Step closes: Current
State's Resume-here says the project is submittable and what Amino submits — the
repository URL and the commit; the plan index; Target State's *"has not been checked
against the rubric text"* replaced by the dated check above; CLAUDE.md's and Current
State's references to `final_proposal_target.md`, which `git ls-files` no longer holds,
pointed at the product brief.

*Verify:* the README's own commands, run in the clone, output pasted; `uv run pytest` in
the clone; `verify_framework.py` and `check_language.py`.

---

## Not in this Step

- **DEBT-035 paid** — `L`: a Gate rule reading `derives_from`, a generation rule
  admitting the composed shape, and a re-measure across both prompts and both providers.
  **Stated, not paid — the first [ruling](#rulings-at-approval)**: the schedule's slack
  is one `L` wide, and this would spend all of it on one of nine metrics. 9.3 states it.
- **[DEBT-023](../debt-ledger.md#debt-023--two-proving-systems-run-side-by-side),
  [DEBT-024](../debt-ledger.md#debt-024--source-and-step-documents-carry-prose-delivery-mode-would-not-admit),
  [DEBT-025](../debt-ledger.md#debt-025--the-nine-certified-metrics-are-implemented-twice)**
  — Triggers on 2026-09-09, after submission; the Delivery Mode section deletes itself
  the same day.
- **DEBT-038's boundary fix** (`M`) — the README branch is taken; every sweep re-measures.
- **DEBT-001's hook layer, DEBT-003, DEBT-012, DEBT-017, DEBT-018** — no Trigger fires.
- **Cloud deployment** — the rubric's 2 bonus points, outside the slice by the Target
  State's own word;
  [EXT-013](../extension-register.md#ext-013--grafana-reads-the-question-log-with-credentials-of-its-own)
  says why the credentials as declared could not go anywhere a second person reaches.
- **[EXT-012](../extension-register.md#ext-012--the-dashboards-panels-read-the-dashboards-time-range),
  EXT-013, a continuous-integration run
  ([EXT-008](../extension-register.md#ext-008--the-data-checks-run-in-continuous-integration))**
  — extensions.
- **Evaluation notebooks.** The Target State's component row says *"notebooks +
  scripts"*; the rubric asks for neither by name, and both sweeps are scripts with their
  commands in the README. Not debt — nothing is wrong, cheaply.
- **Publishing the image, a multi-architecture build, running the tests inside the
  image** — a grader builds locally and runs the tests with `uv`.
- **Removing `.claude/` from the public tree** — it is the working record the extra-credit
  row is claimed on, and the README points at it.

---

## Rulings in flight

3. **The Target State's LLM-evaluation row is corrected, the published generation table
   becomes OpenAI-only as (model, prompt) combinations, and Groq is demoted from being a
   measured alternative** — Amino, 2026-09-05, after the second failed sweep. The rubric
   fetched that day from
   <https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md> reads *"2 points:
   Multiple approaches are evaluated, and the best one is used"* and gives *"one prompt"*
   as its own example of an approach — it names no second model and no second provider,
   so the *"≥2 prompts and ≥2 models"* the criteria map carried was the project's own
   invention and the Groq dependency was never required. Alternatives priced the same
   day and rejected: a paid OpenAI-compatible provider in Groq's place — DeepInfra at
   $0.037/$0.17 per million tokens, or OpenRouter, which also takes AliPay and a
   stablecoin —
   both about a cent a sweep, but both trade a free optional key for a paid one against
   the credential rule.

## Rulings at approval

Both taken by Amino on 2026-09-04, with the approval.

1. **DEBT-035 is stated, not paid** — the recommendation, for the reason
   [Not in this Step](#not-in-this-step) gives. The alternative was a sixth Sub-step,
   which makes this two Steps by the sizing table and moves submission to the deadline
   day.
2. **9.2 runs on the morning of 2026-09-05, the first try** — as soon as possible: the
   earliest budget reset after approval.

## Language

No Term Proposal. `Dockerfile`, image, container, `docs/` and `decisions.md` are
technical words and file names, not domain nouns, and none becomes a code identifier;
*decision register* names a document the way *Extension Register* does, and neither has a
Glossary row. *Fresh-clone rehearsal* is the process phrase the Step 007 and 008 plans
already used. `veritas.retrieval`'s entry point is named for the component it belongs to.

## Schedule

Measured 2026-09-04 by `git log --numstat --format= 874afe9..f3b76f3 -- <dir>`, with the
dates from `git log --format='%h %ad'`, added to the
[Step 008 plan](step-008-observability.md#schedule)'s table:

| Step | days | `veritas/` | `tests/` | `grafana/` | `.claude/docs/` | docs ÷ (code + tests) |
|---|---|---|---|---|---|---|
| 006 `fdf0dc4..814b07b` | 2.8 | 2,255 | 1,719 | — | 1,334 | 0.34× |
| 007 `814b07b..cf64d28` | 1.2 | 1,909 | 1,427 | — | 1,076 | 0.32× |
| 008 `874afe9..f3b76f3` | 1.3 | 1,224 | 1,493 | 331 | 1,814 | 0.60× |

Step 008 came in at 1.3 days against 2 estimated, with the overhead back up to 0.60× —
five Ledger payments and two Extension entries were written, and a dashboard was checked
by eye. This Step is smaller in code than any since 005 — a Dockerfile, one compose
service, one entry point, two test files — and larger in prose than any since 001,
because its product is two public documents. **Estimate: 1.75 days** — 9.1 half a day
including the build, 9.2 a quarter on the 2026-09-05 morning, 9.3 half, 9.4 and 9.5 a
quarter each. **Projected finish 2026-09-06, submission 2026-09-07**, unchanged from the
Step 008 plan's projection and two days inside 2026-09-09. The slack is exactly what
paying DEBT-035 would have spent, and the first ruling keeps it.
