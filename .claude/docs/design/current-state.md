# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**This file says what is true now. How each thing came to be true is in the dated
Step Review that produced it**, under `.claude/docs/reviews/`. That division is what
[R10 of Step 005](../plan/step-005-validation-gate.md#r10--current-state-is-trimmed-in-its-own-commit-between-the-plan-and-51--approved-by-amino-2026-08-25)
trimmed this file to on 2026-08-25, and
[R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26)
wrote the rule that keeps it short into step 5 of the `closing-a-substep` skill: a
Sub-step adds what is now true, and the story of how it got there stays in the review.

**Last updated:** 2026-09-05 — **Step 008 — Observability — is `done`, and so is every
Step before it. Nine of the nine Target State components exist, a question typed into a
browser comes back as a Grounded Answer, that question is written down, and what Veritas
does at runtime is a chart rather than a description. Step 009 is `active`: the App has
its own image, and `docker compose up -d --build` is the whole of Veritas.**
Evaluation measures both halves of the flow:
`data/gold/` holds the Gold Question Set, `veritas/evaluation/` reads it, Retrieval is
scored over it by hit rate and Mean Reciprocal Rank, and what Veritas *answers* is scored
by Execution Accuracy and an LLM-as-judge's agreement with it, across two prompts and
both registered providers. A question that says an Ambiguous Term in any spelling
[Glossary Section D](../glossary.md#d-ambiguous-terms) registers is detected as saying it,
not only in the registered name. **Observability** is the ninth component: the OpenAI
default model is `gpt-5.4-mini`, chosen by
measuring four candidates, and it answers every answerable Gold Question correctly; a
Grounded Answer's Lineage names what the statement used rather than what the model was
shown; and **every question asked through the App is recorded in Postgres** — one row
carrying the step that ended it, the statement, the verdict with its Rejection Reasons,
the identity, the seconds and the cost, one row per Lineage entry and one per model call.
Under that answer a person can leave **Feedback** — up or down and an optional sentence —
which is written against the row the answer was recorded as, where the latest verdict
stands. **`grafana/` charts those rows**: three provisioning files and one dashboard of
seven panels — questions over time by ending, Validation Gate rejections by Rejection
Reason, metric-usage frequency, latency against model time, cost by model, Feedback up
against down, and every ending that carried no number — each one statement over the
Question Log, and each one executed by a test against the schema and then through Grafana
itself. **`docker compose up -d --build` is all three services**: the App answers on
`http://localhost:8501` from an image carrying the Warehouse and both Retrieval models,
Postgres holds the log, the App says in its sidebar whether it is recording, and
`http://localhost:3000` opens the dashboard without a sign-in.
`veritas/validation/` refuses anything that
is not a single, parseable, bounded `SELECT`, refuses any statement whose expressions do
not all trace to a Certified Metric, refuses any statement whose answer would carry a
Restricted Column the Access Profile forbids, refuses any statement that computes a
Certified Metric across joins its Metric Definition does not name or over a date column
or without a certified filter it is not certified against, refuses any statement that
slices a metric by an axis no route reaches from it, and refuses any statement that is
not scoped to the permitted region of the Access Profile it is judged under. The
Semantic Layer is complete: all four entry types, thirty-two entries. The Warehouse is
full, every Certified Metric can return a number, and the sqlglot spike's verdict is
**GO** on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md). All five of
Step 005's Sub-steps are ruled, the last of them on 2026-08-29. **Retrieval is
built**: `veritas/retrieval/` renders
every Semantic Entry as the text a search may match — flat, and again field by field —
indexes those records under four
Retrieval Strategies — text, vector, their fusion, and the fusion re-ranked — and returns the entries a question
scores plus every entry those name, which is how a Join Path reaches an answer at all.
**`veritas/llm/` is the one place a
provider, a model or a key is named** — one OpenAI-compatible client over a closed
registry of two providers, OpenAI and Groq, per
[ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md).
**Sub-step 6.4 closed the flow: Veritas answers a question end to end.**
`veritas/orchestrator/` runs all seven steps — resolve the Ambiguous Terms a question
says, retrieve the Semantic Entries that can answer it, ground a model in those entries
and the identity asking, generate SQL, judge it, execute it, and return a
`Grounded Answer` carrying the statement, its `Lineage` and the
`Validation Gate outcome`. A question the corpus cannot answer comes back as a refusal
or as a question asked back, in the same object. The Gate gained the two readings its
last two open holes needed, so an outer join over a certified condition and a statement
that computes two metrics through each other's currency conversion are both refused.
**Sub-step 6.5 put the flow in a browser.** `veritas/app/` is a Streamlit page over
`Orchestrator.answer`: a question box, the identity it is asked as, and the Grounded
Answer laid out with its SQL, its Lineage and its Validation Gate outcome shown rather
than hidden — a refusal and a question asked back included. It says, beside the identity
and in
[DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s
own words, what enforcing an Access Profile in the application layer is and is not, which
is what paid that entry. A Grounded Answer now carries the names the engine gave its
columns
([DEBT-031](../debt-ledger.md#debt-031--a-grounded-answer-carries-rows-with-no-column-names)
paid), so a breakdown is labelled by the query it came from rather than by the prompt
that asked for it.
**Sub-step 7.1 wrote the Gold Question Set.** `data/gold/` holds twenty-four Gold
Questions, one file each: the question as a person asks it, which of a Grounded Answer's
three endings is correct for it, and — where that ending is a number — the gold SQL and
the gold result. The relevant Semantic Entries are **derived** from the gold SQL through
the Gate's own readers rather than listed beside it. All nine Certified Metrics, all five
Ambiguous Terms and all four of DEBT-029's phrasing classes are in the set, and
`Account Value`'s statement is the one the Gate refuses
([DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)).
**Sub-step 7.2 registered the phrasings and detects them.** Glossary Section D carries
an *Also said as* column — nine spellings across its five rows — `semantic/ambiguous/`
publishes each row's cell as the entry's `aliases`, and the rewrite step matches a
spelling exactly as it matches the registered name. *"revenues"*, *"PnL"*, *"turnover"*
and *"how much is in"* are asked back about rather than answered silently, and
*"turnover"* is a spelling of `volume` rather than an alias of `Traded Notional`,
because it cannot be both.
**Sub-step 7.3 measured Retrieval.** `uv run python -m veritas.evaluation retrieval`
scores every Retrieval Strategy over the Gold Question Set by hit rate and Mean
Reciprocal Rank, under both settings the Ledger had left to a measurement: the corpus
indexed flat or field by field, and a resolved meaning appended to the question or
spliced over it. Both defaults changed to what the numbers said — per field, and spliced.
**Sub-step 7.4 measured generation.**
`VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation` runs the whole flow
over the Gold Question Set once per prompt per registered provider and scores what came
back: Execution Accuracy against the gold result, the ending against the one the set calls
correct, and an LLM-as-judge's agreement with the first. `PromptForm` is the prompt seam —
two lengths of one contract, `rules` and `shape` — and both tell the model the question
arrives with its Ambiguous Terms already resolved into it, close the list of reasons to
refuse, and say that a period the model has never heard of is not on it. `EndedBy` says which step of
the flow ended each question, so a statement the Validation Gate refused is not read as a
generation failure. A Gold Question whose own gold statement the Gate refuses is left out
of the figures, derived rather than named. The sweep spends keys and refuses to start
without `VERITAS_LIVE_MODEL`, and its failure list prints the sentence each refusal gave,
so a refusal that is not the Gate's says why.
**Sub-step 8.1 chose the OpenAI default model by measurement.** `PROVIDERS["openai"]`
serves **`gpt-5.4-mini`**, which answers eleven of the eleven answerable Gold Questions
correctly under both prompts where `gpt-4o-mini` answered two. Four candidates were
priced off the vendor's own page and run cheapest first; two of them reject the pinned
`temperature=0.0` outright and are unusable at any price, which is
[ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md)'s own
prediction firing. The Evaluation sweep takes `--provider`, `--model` and `--no-judge`,
so ranking a candidate costs one provider and no judge; `registered_models` builds that
narrowed set, and a sweep row that never reached a model now prints what the provider
said instead of the step alone.
**Sub-step 8.2 made Lineage the record of what the statement used.** A
`Validation Gate outcome` that allows a statement names what it was composed from — the
Certified Metrics its expressions traced to, the certified axes it sliced by and the Join
Paths its route was certified by — and one that refuses names none of them, which is a
construction error rather than a convention. `Orchestrator.lineage_of` reads the verdict:
the Ambiguous Terms the rewrite step resolved, then those entries, so a `Trade Count`
answer cites `Trade Count` where the retrieval behind it showed the model three metrics,
and a refused question cites the terms alone. The App labels a single figure with that
metric's `unit` and its Reporting Currency, which the same change makes identifiable
([DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)
paid). Nothing records what was retrieved.
**Sub-step 8.3 built the Question Log.** `veritas/observability/` is the seam, four
tables and the one module that imports `psycopg`; `docker-compose.yml` creates the server
from the five `.env` variables the App connects with. A Grounded Answer names the step
that ended it — `EndedBy` moved onto it and its coarsest member split into the two the
Orchestrator decides, which is
[DEBT-032](../debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by)
paid — and carries the model calls it made and the seconds it took. The model seam
returns a `Reply` with the tokens and seconds of its `ModelCall`, and `PRICES` turns
those into a cost for a priced model and into nothing for any other. The App records
after it renders and warns rather than swallowing the answer when it cannot.
**Sub-step 8.4 added Feedback**: the seam takes a verdict and a sentence against a row,
the App offers them under every answer it recorded, and the answer stays on the page
while a person leaves them.
**`tests/` holds Delivery Mode's two guards, the six corpus checks, the search checks,
the rewrite and boundary checks, the flow checks, the two route probes, the App's
rendering, page, recording and Feedback checks, the gold checks, the evaluation checks
and the Question Log checks**;
`uv run pytest` is the command that
proves behaviour from here on, and no test in it needs a key or a network — the five that
call a real provider run only when `VERITAS_LIVE_MODEL` is set, and the eleven that need
a Postgres server skip without one.

---

## Resume here

- **Step 009 — Containerization and `README.md`, the final Step — is `active`, and
  Sub-step 9.1 is done and ruled** — the commit that carries this file is 9.1's. It added
  `Dockerfile`, `.dockerignore`, the `app` service, `python -m veritas.retrieval`,
  `Retriever.warm()` and `tests/test_container.py`, and paid
  [DEBT-026](../debt-ledger.md#debt-026--the-retrieval-models-are-downloaded-rather-than-snapshotted)
  on its own Trigger. It opened no debt and one extension,
  [EXT-014](../extension-register.md#ext-014--the-container-tests-run-as-pipeline-stages-before-and-after-a-deploy)
  — where a test that drives a running App belongs in a continuous-integration and
  continuous-delivery (CI/CD) pipeline, which is the question Amino's ruling on the first
  sceptical point came with.
  **All seven of its sceptical points are ruled**, on 2026-09-05, and the
  [9.1 review](../reviews/step-009-containerization-and-readme.md#sub-step-91--the-app-runs-in-docker-compose-beside-postgres-and-grafana)
  carries each ruling beside the point it answers: the substituted runtime test and
  `docker compose exec` from pytest are accepted, the 2.77 GB image is left as it is, and
  a container running as root is accepted rather than filed. The seventh closed itself —
  Amino opened the containerized page in a browser that day and it answered correctly.
  **The next Sub-step is 9.2, the Groq re-run.**
  [The plan](../plan/step-009-containerization-and-readme.md#92--republish-the-two-provider-generation-sweep)
  puts it on the morning of 2026-09-05 — that morning has passed with the sweep unrun, so
  it is the first thing to do, before anything else spends the Groq budget.
  The plan was approved by Amino on 2026-09-04 with both rulings taken:
  [DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)
  is stated in the README rather than paid, and 9.2 goes first.
  8.5
  wrote `grafana/` — the datasource, the dashboard provider and seven panels — and gave
  the compose file its second service. It closed
  [DEBT-041](../debt-ledger.md#debt-041--a-question-the-provider-never-answered-is-not-recorded)
  `accepted` on the route that entry's own Trigger named, and opened
  [DEBT-042](../debt-ledger.md#debt-042--no-panel-of-the-dashboard-has-been-seen-rendered)
  — **paid inside the same Sub-step**: Amino opened `http://localhost:3000` on 2026-09-04,
  all seven panels draw, and the two images the
  [8.5 review](../reviews/step-008-observability.md#sub-step-85--the-grafana-dashboard)
  carries are the page. Its
  eight sceptical points are ruled, and two of them became extensions rather than debt —
  [EXT-012](../extension-register.md#ext-012--the-dashboards-panels-read-the-dashboards-time-range),
  no panel reads the dashboard's time range, so dragging a time-series panel zooms its axis
  and not its query; and
  [EXT-013](../extension-register.md#ext-013--grafana-reads-the-question-log-with-credentials-of-its-own),
  Grafana reads the log with the App's own credentials and serves it to anyone.
  **⚠ The third point is the one to read**: twenty questions aimed at the Validation Gate
  put two bars in the rejections panel — `shadow metric` and `uncertified route` — and two
  of the thirteen it answered instead are fresh instances of
  [DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it),
  which is due before submission.
  8.4 gave the `QuestionLog` seam its second method and `schema.sql` its fourth table, and
  put one form under every answer the App recorded; all five of its points were approved
  on 2026-09-04.
  8.3 built `veritas/observability/`, the compose file and the Postgres credentials in
  `.env.example`, and paid
  [DEBT-032](../debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by):
  `EndedBy` is the Grounded Answer's own field, stated by the producer rather than
  derived, and `no sql` is split into `retrieval` and `generation`. Its eight points were
  approved on the same day, and it opened
  [DEBT-040](../debt-ledger.md#debt-040--the-price-table-is-a-vendors-page-copied-once-and-nothing-notices-when-it-moves)
  and DEBT-041.
  8.2 paid
  [DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used):
  the verdict names what the statement was composed from and the Lineage is read off it.
  8.1 reverted its own failed first attempt, measured
  four OpenAI models against Groq's mark cheapest first, and **`PROVIDERS["openai"]` now
  serves `gpt-5.4-mini`**, which answers eleven of the eleven answerable Gold Questions
  under both prompts where `gpt-4o-mini` answered two.
  [ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md) carries the
  amended row.
  **⚠ One item is outstanding inside 8.1**: the published two-provider sweep ran and
  **failed its own runner** — Groq's free tier is capped at 200,000 tokens per day, the
  budget for 2026-09-03 was already spent, and 37 of its 46 questions never reached a
  model. The OpenAI half is a measurement; the Groq half is not. **One re-run of
  `VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation` once that budget
  resets** is owed — tracked as
  [DEBT-039](../debt-ledger.md#debt-039--the-published-two-provider-sweep-failed-its-own-runner-and-is-not-republished),
  whose Trigger postpones it — and splicing the Groq arm in from a separate run is
  forbidden by the plan. Two findings came out of that Sub-step that bear on everything
  after it: a model
  rejecting `temperature=0.0` is unusable at any price, and **temperature 0 is not
  determinism** — the winner scored 21/23 and then 22/23 on `shape` across two runs.
  Both are in the
  [8.1 review](../reviews/step-008-observability.md#sub-step-81--choose-the-openai-default-model-by-measurement),
  and nothing in it is now awaiting a ruling.
  [Step 007 — Evaluation](../plan/step-007-evaluation.md) is **`done`**, and so is every
  Step before it: four Sub-steps, all four built, ruled and committed — 7.1 (`a361b79`),
  7.2 (`35099c3`), 7.3 (`47dfb8c`) and 7.4 (`7e40092`), the last approved on 2026-09-02.
  The first Groq call was made in 7.4.
- **The decision 8.1's first attempt opened was taken on 2026-09-03 and has been
  carried out.** The question was how DEBT-037 gets paid once its own remedy measured
  wrong; the ruling was that it does not get paid — **the model changes instead.**
  `gpt-4o-mini` was never
  argued for: [ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md)'s
  table justified the *provider* — *"The key the course already asks a grader for"* — and
  said nothing about the model, unlike the groq row beside it. Four OpenAI models were
  measured cheapest first; `gpt-5.4-mini` took the row and that ADR now carries why.
  **groq stayed exactly as it is**, which keeps the registry provider-keyed and the
  [Zoomcamp](../design/target-state.md#zoomcamp-criteria-map) *"≥2 models"* row intact;
  retiring it would need the seam reworked and is not bought before the deadline. The
  option weighed and dropped — publishing the Warehouse's date coverage into the prompt,
  against [ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md)'s *"corpus
  rather than a schema dump"* — is in the
  [first 8.1 review section](../reviews/step-008-observability.md#sub-step-81--tell-the-generator-an-unknown-period-is-not-a-reason-to-refuse),
  which stays as the record of the attempt that failed.
- **No Term Proposal is open**: the plan's two —
  **`Question Log`** and **`Feedback`**, from its
  [Language](../plan/step-008-observability.md#language) section — were agreed with it
  on 2026-09-03 and are [Glossary](../glossary.md#a-the-system) Section A rows; 7.1's
  **`Gold Question`** and **`Relevant Set`** were agreed on 2026-09-01, and 7.2's
  Section D column the same day. **The debt picture:
  thirteen open, twenty-four paid, three accepted, two moved — and the Extension
  Register holds fourteen open, two of them 8.5's and one 9.1's.**
  [DEBT-032](../debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by)
  is **paid** by 8.3 and
  [DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used)
  by 8.2, both on their own Triggers.
  [DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)
  is open and unpaid on the second branch its own Trigger allows — `Account Value` is
  excluded from every generation figure, derived rather than named — and Sub-step 7.4
  resized it `M` → `L`, because a Gate rule alone no longer pays it.
  [DEBT-037](../debt-ledger.md#debt-037--nothing-tells-the-generator-that-a-date-it-has-never-heard-of-is-not-a-reason-to-refuse)
  is **closed `accepted`** by 8.1: its remedy was measured not to work over
  three wordings, the honest fix crosses
  [ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md) and CLAUDE.md, and
  the generation sweep every candidate default now passes through is the guard against a
  model with the date-refusal habit. Two new entries open:
  [DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it)
  — `gpt-5.4-mini` answers *"show me ten trades"*, a refusal-expected probe, as the
  nearest Certified Metric and the Gate passes it because it traces; and
  [DEBT-039](../debt-ledger.md#debt-039--the-published-two-provider-sweep-failed-its-own-runner-and-is-not-republished)
  — the two-provider table owes one re-run, postponable until a Sub-step or the
  documentation pass needs it. 8.2 opened none and 8.3 opened
  [DEBT-040](../debt-ledger.md#debt-040--the-price-table-is-a-vendors-page-copied-once-and-nothing-notices-when-it-moves)
  and
  [DEBT-041](../debt-ledger.md#debt-041--a-question-the-provider-never-answered-is-not-recorded).
  8.5 closed DEBT-041 `accepted`, opened and paid
  [DEBT-042](../debt-ledger.md#debt-042--no-panel-of-the-dashboard-has-been-seen-rendered),
  and added two dated instances to
  [DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it)
  without opening an entry for them.
  `DEFAULT_PROMPT_FORM` stays `rules`, now on a margin
  rather than 7.4's tie — `gpt-5.4-mini` scored 22/23 under it in both runs it was
  measured in.
- **The project is under [Delivery Mode](../../../CLAUDE.md) until 2026-09-09**,
  the capstone deadline. Behaviour is proven in `tests/` (`uv run pytest`);
  `.claude/scripts/` is frozen and `tests/test_delivery_mode.py` enforces both that
  freeze and the ban on new links from code into Step history. Plans are capped at
  120 lines and Step Review sections at 40. Nothing in the Four Non-Negotiables is
  suspended.
- **Three refactors were costed and deferred**, each losing days before the
  deadline: porting the frozen checks to tests
  ([DEBT-023](../debt-ledger.md#debt-023--two-proving-systems-run-side-by-side)),
  cutting the prose and link overhang
  ([DEBT-024](../debt-ledger.md#debt-024--source-and-step-documents-carry-prose-delivery-mode-would-not-admit)),
  and de-duplicating the nine Certified Metrics
  ([DEBT-025](../debt-ledger.md#debt-025--the-nine-certified-metrics-are-implemented-twice)).
  All three come due on 2026-09-09.
- **The handoff detail for Sub-step 8.1 is in its
  [review entry](../reviews/step-008-observability.md#sub-step-81--tell-the-generator-an-unknown-period-is-not-a-reason-to-refuse)**,
  which carries the three wordings tried, their figures, and the two candidate fixes.
  Sub-step 7.4's is in its
  [review entry](../reviews/step-007-evaluation.md#sub-step-74--measure-generation-execution-accuracy-and-llm-as-judge),
  which also carries the ruling that closed Step 007. 7.3's is in
  [its own](../reviews/step-007-evaluation.md#sub-step-73--measure-retrieval-hit-rate-and-mrr),
  7.2's in
  [its own](../reviews/step-007-evaluation.md#sub-step-72--register-the-phrasings-and-detect-them)
  and 7.1's in
  [its own](../reviews/step-007-evaluation.md#sub-step-71--write-the-gold-question-set).
  Step 006's is in its
  [6.5 entry](../reviews/step-006-retrieval-and-orchestrator.md#sub-step-65--ask-a-question-in-the-browser),
  which also carries the ruling that closed that Step.

---

## Summary

A fully designed project with all nine of its components built, a question asked in a
browser comes back as a Grounded Answer, Evaluation measures both halves of that flow
over a committed Gold Question Set, and Observability writes every question down and
charts it. All three services run in `docker compose`. What the project still lacks is
the `README.md` a grader runs it from — Step 009, the final Step.
The framework is in place and the Target State is `agreed`, so there is a fixed point
to build toward: a natural-language analytics copilot over a brokerage warehouse, whose
answers are grounded in a certified Semantic Layer and checked by a deterministic
Validation Gate.

**The Warehouse is full.** The ten-table star schema of
[Glossary Section B](../glossary.md#b-the-warehouse) sits behind the Warehouse Adapter —
the only module in the repository that imports `duckdb`, and the only place a
DuckDB-specific function name appears, both checked rather than promised — and all ten
tables hold rows. Three are real: `dim_instrument`, `fct_instrument_price` and
`fct_fx_rate`, from key-free public sources snapshotted into the repository. Seven are
synthetic, from a seeded simulator that prices every Trade off a Market Price the
Warehouse already holds and converts through a real FX Rate. **One command builds all
ten offline from committed snapshots with no socket opened, and two runs are
byte-identical.**

**Every Certified Metric can return a number** — all nine — and every pair in
[Glossary Section C](../glossary.md#c-distinctions-we-must-not-blur) is two measurably
different numbers on the loaded data. Row counts, windows and Section C figures are
dated evidence in the
[Step 002 review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-25--generate-seeded-synthetic-client-activity),
because a `--refresh` moves them.

**The Semantic Layer is complete** — all four entry types
[Glossary Section A](../glossary.md#a-the-system) registers, thirty-two entries. A
Metric Definition publishes its expression as the text an Orchestrator pastes verbatim,
plus the route and the date predicate that expression does not pin down. Ambiguous Terms
carry the claim [ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md)
rejected schema retrieval for — that *"revenue"* has two certified meanings. Dimension
Definitions carry the answer to *"by what?"*, checked against the buckets the Warehouse
actually holds and — since Sub-step 5.5 — the routes that reach each axis from each fact
table a metric starts at, so an axis says where it is applicable as well as what it
means. Retrieval searches it and the Orchestrator grounds a model in what Retrieval
returns, so the corpus now slices: a question that asks for a breakdown becomes a
statement that groups by a certified axis, and one that asks for an axis no route
reaches is refused by name.

**The Validation Gate refuses anything that is not a bounded read, anything that
computes a metric the Semantic Layer does not certify, anything whose answer would
carry a Restricted Column, anything that computes a certified metric over rows its
own Metric Definition does not describe, and anything that is not scoped to the identity
asking it.** `veritas/validation/` holds the
`Validation Gate outcome` and the `Rejection Reason` taxonomy as a contract a consumer
can import without importing a rule, the `Access Profile` a statement is judged under,
and eight rules behind them. Four judge a statement's
shape: sqlglot cannot read it, it holds more or fewer than one statement, it is not a
`SELECT`, or the planner expects it to scan past a declared ceiling. The fifth reads the
corpus — every projection that aggregates is canonicalised and looked up in the nine
Certified Metrics loaded from `semantic/metrics/`, and the statement is allowed only if
at least one is found and **all** of them trace. The sixth reads an identity: every
output column's lineage is walked back to the base-table columns feeding it, and a
statement is refused if the Access Profile forbids one of them — *reaching the answer*
rather than *appearing in the statement*, so a restricted name in a comment, in a string
literal, in a filter, or aggregated away inside a subquery is not a projection of it. That
identity is an argument to `judge`, not a field on the Gate, so one Gate serves many
identities over one loaded corpus. The seventh reads the rows underneath the
projection: the joins a statement carries are compared with the Join Paths the metric it
traces to names and the axes it groups by declare, the date columns its WHERE clause keys
on with that metric's `date_column`, and its WHERE clause's conjuncts with that metric's
certified `filters` — so a certified expression converted through the wrong currency,
filtered on the wrong half of a Section C date pair, or computed with its defining
predicate dropped is refused, and so is a slice by an axis no route reaches from that
metric. **Permission comes from a list with three sources and no fourth** — the metric's
own `join_paths`, the `routes` of each axis the statement groups by, and the route the
Access Profile's predicate needs — and the Gate never searches for a chain that would
reach a table, so a join no entry names is a rejection rather than a search. The eighth
reads the identity again and asks one question of the outermost WHERE clause: is the
Access Profile's predicate there. **Present on every statement**, because a query that
never joins `dim_client` reads every region's rows and names none of them.
Each rejection carries its own named reason, thirteen in the taxonomy. The scan estimate
and the column list both come from the
engine through the Warehouse Adapter, which is the only place the plan format and the
catalogue query are known. Nothing anywhere executes a statement through it.

**The design's largest unproven assumption is now measured.** That sqlglot can decide
from a parse tree alone whether a generated query computes a Certified Metric was probed
on the real schema and the real data, on all four of the claims Step 002 deferred, and
the verdict is **GO on
[ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)**, recorded in
[validation-feasibility.md](validation-feasibility.md), the project's second design gate
beside [data-availability.md](data-availability.md). Two of the six constraints it
carries are sharp enough to restate anywhere: a certified expression is recognised **by
form**, so a paraphrase of it is refused and the Semantic Layer must publish a form the
Orchestrator pastes; and a certified expression **does not pin down the join**, so a
query converting through the wrong currency column traces and is wrong by a margin the
spike prints on every run. The second of those is now **enforced** rather than only
recorded: the Gate reads the route as well as the projection, and the query is refused
on both sides. The
fourth claim, which is ADR-0002's rather than ADR-0003's, is qualified: every parse-tree
verdict survives retargeting to BigQuery and one type does not.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Ten declared dependencies**, plus `pytest` in the dev group: `duckdb`, `dlt`, `sqlglot` and `pyyaml` from the early Steps, `minsearch` and `fastembed` since Sub-step 6.2, `openai` and `python-dotenv` since 6.3, `streamlit` since 6.5, and `psycopg[binary]` since 8.3. dlt brings the bulk of the transitive tree; `fastembed` brings `onnxruntime` and `minsearch` brings `scikit-learn`, `numpy` and `pandas`. Two check scripts are standard-library-only — `verify_framework.py` and `check_data_availability.py`; the other four and the `check_validation_gate/` package import third-party code. Everything imported anywhere is one of the ten. |
| Development framework | ✅ working | `CLAUDE.md`, the `.claude/docs/` tree, five skills in `.claude/skills/`. Non-Negotiable #4 carries the rule that **an exemption is scoped to where it is needed** — a check that excuses something names the file as well as the symbol, never a symbol alone. `closing-a-substep` step 5 carries the rule that keeps **this** file short: a Sub-step adds what is now true and the story of how it got there goes to the review, so a passage narrating a Sub-step is a defect here even when accurate. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only: documents exist, links resolve, skills load, interpreter pinned. Passes. **Links include their `#anchor`**, and a `dead anchor` is reported distinctly from a `dead link`; it prints how many links and anchors it checked. **Its scope includes code**: every `.py` file under `veritas/` and `.claude/scripts/` is read for markdown links too, because docstrings cite ADRs and Ledger entries in the same syntax — a link inside a `.py` file may point at the same things a link inside a document may, resolved the same way, anchor required. That is [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s second coverage gap, paid. `README.md` is outside the scope, and so are the skills: a skill is checked for loading and for a trigger-shaped description, but the markdown links in its body are not resolved — `writing-an-adr` has two and nothing reads them. |
| Language check | ✅ working | `.claude/scripts/check_language.py` — content rules: component names registered, no `proposed` term in code, abbreviations resolvable. Passes. Parses code with `ast` so it checks identifiers, not prose. Derives the shouted keywords of the SQL this project writes rather than remembering them, from **three** bodies: the hand-authored `.sql` files, the SQL fields a Semantic Entry publishes, and the statements written as Python string literals — the third asks sqlglot which literals are statements, exactly as `check_warehouse.py`'s dialect scan does. That is why it reads the corpus and is not standard-library-only. One keyword is listed by hand with its reason beside it, `FORMAT`, because the adapter holds `EXPLAIN (FORMAT json) ` as a fragment and a fragment parses as nothing. Partial payment of [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement). |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`. The term count is whatever `check_language.py` prints. Three rows are read back mechanically rather than by a reader: Section D's *Could mean* column, its *Also said as* column — added by Sub-step 7.2 and read back by `tests/test_rewrite.py` rather than by `check_semantic_layer.py`, which was frozen before the column existed — and Section A's `Dimension Definition` row, which registers the five certified axes with their columns, their grain and their buckets in the form `check_semantic_layer.py` parses. The last of those is [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) — a registry inside one table cell, where the other two this project reads back are tables with a row per entry. |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — real 2025 FX Rates and three real price series, plus the dated probe record, owned by `check_data_availability.py`. `data/snapshots/ingestion/` beside it is the pipeline's own, one file per source and one per traded Instrument, rewritten only by `--refresh`. Both committed on purpose: they are what make the checks reproduce without network access. |
| Founding ADRs | ✅ working | **Five ADRs** in `.claude/docs/adr/`, all **`accepted`** — the four founding ones, and [0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md), which sends every model call through one OpenAI-compatible endpoint and was accepted on 2026-09-01: 0001 Semantic Layer as the retrieval corpus, 0002 DuckDB behind an adapter, 0003 Validation Gate as deterministic code, 0004 snapshot-and-replay and where dlt stops. Every cost in each is classified *accepted* / *debt* / *extension*. ADR-0002 carries a dated clarification on what its sqlglot commitment forbids, and both 0002 and 0003 carry a dated status note pointing at [validation-feasibility.md](validation-feasibility.md); no status changed. |
| Warehouse | ✅ working | `veritas/warehouse/schema.sql` — the ten tables of [Glossary Section B](../glossary.md#b-the-warehouse), **all ten populated**. Monetary columns are `DECIMAL(18, 6)`, FX Rates `DECIMAL(18, 8)`; **no floating-point column exists** and `check_warehouse.py` fails the run if one appears. Foreign keys declared and enforced. Snapshot grain is one row per subject per date, enforced by the primary key. No `dim_date`. The two movement tables carry **opposite sign conventions** and the schema says so beside each column: cash is signed from the Account's side, accounting carries magnitudes so that Net Revenue = Σcommission − Σrebate − Σfee is literally true. |
| Warehouse Adapter | ✅ working | `veritas/warehouse/adapter.py` — the only module in the repository that imports `duckdb`, which is checked rather than promised. `create_schema`, `tables`, `columns`, `columns_by_table`, `row_count`, `execute`, `query` and `estimated_scan_rows`, plus the `in_memory()` constructor for throwaway databases. Assembles no SQL text from any argument: introspection goes through `information_schema` with a bound parameter, row counts through the relational API. `columns_by_table` returns the whole catalogue in the shape sqlglot's optimizer calls a schema, in **one** query rather than one per table, because the Validation Gate reads it on every judgement. `estimated_scan_rows` is the one method that assembles anything — it prefixes the engine's `EXPLAIN`, in the JavaScript Object Notation (JSON) form that returns a plan with a number in a field rather than a drawn box diagram, and sums the planner's estimate over the operators that read a table. **The plan format, the `EXPLAIN` spelling and the field names live only here.** It never runs the statement, and its caller must have established the statement is a single read first: the engine executes every statement after the first in such a string even under `EXPLAIN`. It raises `WarehouseError`, the adapter's own error type, which is what lets a caller that may not import `duckdb` tell an engine refusal from its own bug; `execute` and `query` raise it too, and the methods that run SQL this package wrote deliberately do not. Hardcoded database path licensed in writing by [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md). |
| Warehouse check | ✅ working | `.claude/scripts/check_warehouse.py` — four checks always, plus three flag-gated suites. Always: the table set matches Glossary Section B *read from the Glossary*, no floating-point columns, fourteen constraint rejections fire against an in-memory Warehouse with a seven-row positive control, and **the adapter seam holds in both the halves [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md) named** — no `duckdb` import outside `veritas/warehouse/`, and no DuckDB-specific **construct** in the SQL that leaves the adapter. The dialect scan reads every string literal sqlglot parses as a statement, plus every SQL field the Semantic Layer publishes (a Metric Definition's `expression` and `filters`, a Join Path's `on`), and reads all of it twice. **By name**: any function call standard SQL does not have, with the name set subtracted out of sqlglot's own dialect tables rather than typed, so the list tracks the library; this fails the run. **By type**: each statement is retargeted to BigQuery and every type construct compared against the same type retargeted *on its own*, so `DECIMAL(38, 6)` arriving as `NUMERIC` inside a statement and as `NUMERIC(38, 6)` alone is a finding while `VARCHAR` arriving as `STRING` is not; this prints a **review comment** rather than failing, because the corpus carries a widening cast the engine will not compute without — a statement sqlglot cannot write in BigQuery at all *does* fail. `retarget` and `round_trip_rewrites` live here and `check_validation_feasibility.py` imports them back, so the spike's dated measurement and this scan are one trip. Five probes run every time, each recording what **both** readings must say, and a probe reading wrong in either column fails the run. Those probes are the scan's **one fixture exemption**, scoped to the file it lives in: `FIXTURE_EXEMPTIONS` names `.claude/scripts/check_warehouse.py` as well as the symbol `DIALECT_PROBES`, so no other scanned file can claim it by choosing that name, and pointing the entry at a file that does not exist makes the run fail loudly. `--rebuild` recreates the database. `--sources` checks the loaded data, one function per star table: for `dim_instrument`, normalisation, the declared universe, every raw table non-empty and a **richness** assertion; for `fct_instrument_price` and `fct_fx_rate`, every row **re-derived from the committed snapshots in Python** and compared row-for-row against what the SQL built, with named wrong readings shown to change real rows, no day-over-day move exceeding 1.5, a rate for every Market Price in its own Quotation Currency on its own date, and a currency converted through another and back unchanged within the rounding its stored scale forces. **`--distinctions`** adds four more: every client-activity row is exactly what the simulator produces from the same seed, **every quantity is a whole lot of its own Instrument**, every Snapshot is markable and at least one Position Change is one no Trade explains, and **every Glossary Section C pair is printed as two numbers with how far apart they are** — a pair that has collapsed fails the run. `--rebuild` is mutually exclusive with both. It also holds the **nine independent figures** — one per Certified Metric — that `check_semantic_layer.py` compares every published expression against. They **read nothing from `semantic/`** ([R2](../plan/step-004-semantic-layer.md#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21)), and they are independent in **method** as well as in text: each fetches the component columns and folds them in Python, because a `DECIMAL(18, 6)` amount times a `DECIMAL(18, 8)` rate overflows `DECIMAL(18)` and an aggregate written here would need the same engine-specific width the published expressions carry. The `decimal` context precision is set explicitly for the same reason. The price of that independence is that editing a published expression means editing this SQL too, or the run fails. |
| Validation feasibility spike | ✅ working | `.claude/scripts/check_validation_feasibility.py` — the sqlglot spike, answering **all four claims** of [Step 003](../plan/step-003-validation-feasibility.md). **Not the Validation Gate and not a thin version of one**: it creates no `veritas/validation/` directory and ships no component. A tracer — parse, resolve against the real schema read through `WarehouseAdapter.columns_by_table`, rename table aliases back to their base table, canonicalise every projection that aggregates — plus 25 probe statements, each declaring the verdict this spike measured for it. **The tracer, the detector and the route reader are no longer this file's**: all three are `veritas/validation/`'s, imported back under [R2 of Step 005](../plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25), so the spike holds no copy of `resolve`, the canonical form, the two trusted rewrites, the refusal, the projection walker, the lineage walk or the route reading, and every one of its 25 declared verdicts and every one of its nine detector readings is unchanged by the two moves. What it still owns is its three pinned declarations: three certified expressions, three certified routes, and one `RestrictedColumn`. A statement is allowed when it computes at least one metric expression, **every** one traces to a certified expression, and it carries every join the metric it traced to is certified across. That last reading is narrower than the Validation Gate's own rule and deliberately so: the Gate must also refuse a join nothing certifies, and this file has no Dimension Definitions to certify a slice's extra joins with. The certified expressions and routes live as Python literals ([R2](../plan/step-003-validation-feasibility.md#r2--the-spikes-certified-expressions-stay-python-literals--approved-by-amino-2026-08-15)), pinned to the corpus rather than re-pointed at it ([R4](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)), so the dated measurement stays the one that was taken. Every executable probe is executed through the adapter and checked **against another probe's number** rather than against a figure written in the script. It exits non-zero if any verdict, any relation or any detector reading changes, in either direction — a spike's job is to hold its finding still. For claim 1, `projected_expressions` walks every scope; for claim 2, `columns_reaching_the_answer` walks each output column's lineage, so a column that never reaches the answer is not counted — both now imported rather than defined here — and nine shapes are judged three ways each — from the parse tree, by searching the query's text (ADR-0003's rejected alternative), and by claim 1's tracer. For claim 4, every one of the 25 statements is transpiled to BigQuery, re-parsed there and re-judged against a corpus and a schema retargeted the same way. |
| Validation-feasibility gate | ✅ working | `.claude/docs/design/validation-feasibility.md` — the go/no-go the spike exists to produce, in the shape of `data-availability.md` and beside it as the project's second design gate. **Verdict GO on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)**, with a verdict per claim, [what the Step did not measure](validation-feasibility.md#what-this-step-did-not-measure), [six constraints](validation-feasibility.md#consequences-for-step-004) on the Steps that follow, and four rulings. |
| Semantic Layer | ✅ working | `semantic/` — **all four entry types, every one complete**, thirty-two entries. **Nine Metric Definitions** in `metrics/`, one per Certified Metric of [Glossary Section B](../glossary.md#b-the-warehouse), and **thirteen Join Paths** in `joins/` — eight the metric expressions are computed across, and five that reach `dim_client`: one hop to `dim_account` from each of the four fact tables a metric starts at, plus the `account_to_client` they share. A Metric Definition carries its `expression` as the text an Orchestrator pastes verbatim ([C1](validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)) plus what [C2](validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate) requires — the route and the date predicate. The shape is [R8](../plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)'s: `from_table` names the table the query starts at, `join_paths` is an ordered list, `filters` holds the certified predicates, `date_column` names the column a period filter keys on, `reporting_currency` is present exactly when `unit` is `money`, and `derives_from` names the Certified Metrics whose value is **added** to this metric's own expression. One metric is composed that way — `Account Value` is *"Cash Balance plus all Positions marked to market"* — one carries a filter, two join nothing, and five carry a widening cast without which the engine refuses the expression. A Join Path carries `from_table`, `to_table` and the join condition as written, Reporting Currency literal included, because C1 forbids a template something else fills in. **Five Ambiguous Terms** in `ambiguous/`, one per row of [Glossary Section D](../glossary.md#d-ambiguous-terms) — `revenue`, `volume`, `balance`, `P&L`, `how much does X have` — each carrying a `description` of why the ambiguity is dangerous, a `resolution` from Section D's own third column, `disambiguates`, the [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) field naming the Certified Metrics the word could mean, and — since Sub-step 7.2 — `aliases`, the other spellings of the word from Section D's *Also said as* column, each of which **is** the registered term rather than a near miss of it. An Ambiguous Term publishes **no SQL**: it is a claim about language, so it can be wrong while every expression is right. **Five Dimension Definitions** in `dimensions/` — the certified axes a metric can be sliced along, each carrying `columns`, `grain`, `allowed_values` and `routes`, the first three being the [Glossary row](../glossary.md#a-the-system)'s own words for what one names and the fourth being where it can be reached from. Three are date axes rather than one: a single axis at `fct_trade.trade_date` could not be applied to the five Snapshot-and-movement metrics whose routes never reach that column, so the corpus publishes `by trade date`, `by snapshot date` and `by accounting movement date`, each named for the registered term it belongs to. `by snapshot date` is one axis over **two** columns, because `Snapshot` is one term registered as living in both Snapshot tables and one calendar writes both. A date axis enumerates no values — they are minted by the data — while `by region` and `by instrument type` enumerate theirs and are checked against what the Warehouse holds. A Dimension Definition publishes **no SQL** either. **`routes`** maps a metric's `from_table` to the Join Paths that reach the axis's columns from there, and its three shapes are three different answers: an empty list says the column is already on that table, a list says what reaching it costs, and an **absent key** says the axis cannot be reached from there at all — which is how `Cash Balance by instrument type` is refused by name, a Cash Balance having no Instrument. It is what stopped an axis being a **leaf**: `routes` names Join Paths, so an axis has an edge like every other entry type, and check 19 walks it. **`by region` is reachable from all four fact tables a metric starts at**, so the axis the Glossary's own worked example uses is applicable to all nine Certified Metrics; the check prints that count on every run. |
| Semantic Layer loader | ✅ working | `veritas/semantic/` — `loader.py` behind an `__init__.py` that re-exports it, laid out like `veritas/warehouse/`. Reads the tree into frozen dataclasses whose field lists **are** the file format, so there is no second copy of a field name to drift; refuses a file it cannot read as the kind its directory declares, a duplicate entry name, or a field the format does not name. `reporting_currency` is the one field a file may omit — the loader allows it and `check_semantic_layer.py` is what judges it, because whether omitting it is honest depends on `unit` and a loader reads one file at a time. **Executes no SQL and assembles no query** — C1 puts pasting on the consumer's side. `SQL_FIELDS` and `sql_fields()` say which fields of an entry hold SQL: `expression` and `filters` on a Metric Definition, `on` on a Join Path, nothing on an entry type not listed — so an Ambiguous Term and a Dimension Definition cost their readers nothing. They live here for the reason the dataclasses do: the format is here, and each reader deciding for itself is a second copy of it. Two readers ask so far, `check_warehouse.py`'s dialect scan and `check_language.py`'s keyword derivation; the Orchestrator that assembles a query will be the third. `ENTRY_KINDS` is not a scan of the tree, so a file in a directory it does not know fails to load rather than being skipped. The `kind` a file declares is the Glossary's term snake-cased unless a shorter one is registered, which is why a Metric Definition says `metric` and an axis says `dimension_definition` in full: no `Dimension` is registered, and shortening it would coin a noun. Reads booleans the **YAML 1.2** way rather than PyYAML's YAML 1.1, because a Join Path publishes its condition under the key `on`, which YAML 1.1 reads as the boolean `True`; the same rule keeps `no`, `on`, `y` and `n` as text in any casing, which is what an axis's allowed values need — a country code, a province code, and both halves of every yes/no flag. |
| Semantic Layer check | ✅ working | `.claude/scripts/check_semantic_layer.py` — **nineteen checks**, and it needs a filled Warehouse. The two places it executes a published expression catch `WarehouseError` rather than `Exception`, so a bug in the script surfaces as a traceback instead of as an accusation against a YAML file. Every file loads with every required field; **every Metric Definition's `name` is a Glossary Section B term whose *Lives in* cell says `semantic/metrics/`**, read from the Glossary rather than listed in the script; the expression is **pasted verbatim** into a query built from the entry's own Join Path and date column, executed through the Warehouse Adapter, and must return a number; that number must equal what `check_warehouse.py` computes from its own SQL — **twice, once over the whole Warehouse and once over one period**, because the arithmetic and the date predicate are separate mistakes and the second is invisible to a total; the declared Reporting Currency must appear as a string literal in the named Join Path's parse tree; and an expression that does not parse **fails the run**, with two probes exercising the refusal every run. Every [Section C](../glossary.md#c-distinctions-we-must-not-blur) pair whose both sides are Certified Metrics returns two different numbers **from the published expressions**. A metric's route is a route: every Join Path it names exists, starts at a table the route has reached, arrives somewhere new, and never reaches forward in its condition. The three expressions the spike measured, **and the three routes it measured them across**, are character for character what `semantic/metrics/` publishes — a pinned declaration nothing compared with the corpus would be a second corpus. A composed metric adds up metrics that exist, are not itself, do not derive further, and share its unit and currency. Every widening cast is shown to be load-bearing by running the expression without it and expecting the engine to refuse. **Three checks execute nothing** — they are claims about *language*, so they fail when a word is wrong while every number is right: every Certified Metric an Ambiguous Term names must exist and there must be at least two distinct ones ([EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks)'s fourth rule, three probes every run); Glossary Section D and `semantic/ambiguous/` must register the same words, with each row's *Could mean* cell naming the same Certified Metrics its entry does; and no metric's alias may be a registered Ambiguous Term or be claimed by two metrics. Words in a *Could mean* cell that are **not** Certified Metrics — `both`, on the P&L row — are printed rather than ignored, because a check that silently drops what it cannot resolve drops a misspelling just as silently. **Four checks read the Warehouse rather than the corpus**, because an axis's claim about buckets is a claim about the data and nothing else in the corpus would notice it being wrong: every column an axis names exists in the live schema; every column of one axis holds the **same** set of values, and an enumerated axis's buckets are exactly that set, in both directions; an axis enumerates **exactly when** its buckets are a registered vocabulary rather than dates, since a date's values are minted by the data and a list of them in the corpus would be a measurement dressed as a definition; and the Glossary's `Dimension Definition` row is read back against the corpus — a prose parse, and [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) is the cost of it. Five probes give the axis checks teeth every run. **A fifth reads both** — every route an axis declares is a route and arrives at the axis: each Join Path it names exists, the chain starts at the table the key names, each hop extends a route already arrived at its own `from_table`, no hop lands where the route already is, no condition reaches forward, and the chain ends at a table one of the axis's columns lives in. Check 8 for a Dimension Definition, with the last clause only an axis can get wrong, and an empty route is checked too, since `[]` claims the column is already on that table. Five more probes give it teeth. It also prints, without failing, how many Certified Metrics each axis declares a route from. |
| Ingestion | ✅ working | `veritas/ingestion/` — **both halves**: four real sources and the seeded simulator. `uv run python -m veritas.ingestion` builds all ten tables end-to-end from a clean clone with **no network**, and two consecutive runs produce byte-identical output. `--refresh` is the only mode that opens a socket; a refresh that fails part-way names the snapshots it had already rewritten, and one that succeeds reports how many it rewrote and how many were distinct — **failing the run if a source was fetched twice**. **Two phases, in an order that cannot be reversed:** dlt lands the real sources in `raw` and the adapter builds three star tables from them; then `simulator.py` *reads those three through the adapter*, generates the client side as a pure function of them and a seed, and a second dlt load plus seven more build scripts lands it. No two connections are ever open at once. The pipeline refuses to complete on four silent-shortness conditions, among them a Position with no Market Price on its own Snapshot date, and a monetary amount whose Denomination Currency has no FX Rate on its own date. |
| Retrieval | ✅ working | `veritas/retrieval/` — `searchable.py` and `search.py` behind an `__init__.py` that re-exports both, laid out like `veritas/semantic/`. `SEARCHABLE_FIELDS` is the whitelist of fields a search may match, one row per entry type and disjoint from the loader's `SQL_FIELDS`. A Metric Definition's `aliases` are in it and an **Ambiguous Term's are not**: the rewrite step reads those spellings before any search runs, so a question that says one arrives already asked back about or already carrying the meaning it resolved to — measured as well as argued, since indexing them moves a fixed-set question out of the vector search's top five. `searchable_entries()` renders the whole Semantic Layer as one record per entry — `name`, `kind`, the flat `text` block, and one key per field of `TEXT_FIELDS` beside it, which is the same words kept apart. Which of the two the text index is fitted on is a `SearchableForm`, an argument to `Retriever`; the **per-field form is the default**, because each field's cosine is normalised by that field's own length, so a term in the short `name` outweighs the same term inside a long `description` — measured over the Gold Question Set rather than argued, which is what paid [DEBT-027](../debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match). A **Join Path renders as empty text**, because its name, its two tables and its `on` clause are Warehouse identifiers end to end, and it is left out of both indexes rather than sitting in them at score zero. `search.py` indexes the rest under **four Retrieval Strategies**, enumerated by `RetrievalStrategy` and chosen per call: `text` is minsearch's Term Frequency-Inverse Document Frequency cosine, with stop words dropped and a token pattern that admits `&` so `P&L` survives tokenisation at all; `vector` is cosine over `BAAI/bge-small-en-v1.5` sentence embeddings; `hybrid` fuses the two by Reciprocal Rank Fusion, on positions rather than scores because the two cosines are not on one scale; and `reranked` re-scores the fusion's candidates with the `Xenova/ms-marco-MiniLM-L-6-v2` cross-encoder and is the default. Both models are Open Neural Network Exchange (ONNX) models, credential-free, and **downloaded on first use rather than snapshotted** ([DEBT-026](../debt-ledger.md#debt-026--the-retrieval-models-are-downloaded-rather-than-snapshotted)); the text index needs neither, so a `text`-only caller loads no model and opens no socket. **Two entry points, and the difference is reference closure**: `rank` returns what a search scored, which is what Evaluation will measure, and `retrieve` returns that plus every entry those hits name, transitively — a Metric Definition's `join_paths` and `derives_from`, an Ambiguous Term's `disambiguates`, a Dimension Definition's `routes`. `REFERENCE_FIELDS` is that map, one row per entry type, and closure terminates at a Join Path because a Join Path names nothing back. Nothing calls it yet — no question reaches it from anything but a test. |
| Large Language Model boundary | ✅ working | `veritas/llm/` — `model.py` behind an `__init__.py` that re-exports it. `LanguageModel` is the seam — a system instruction and a user message in, a `Reply` out, with `json_object` as a request the provider may or may not honour. A `Reply` is the text and the `ModelCall` that produced it: the provider, the model, the prompt and completion tokens the reply reported, and the seconds the socket took, measured this side of the seam because the wall time a person waits is the wall time the call took. `PRICES` costs one — five OpenAI rows read on 2026-09-03 from the vendor's pricing page, each carrying that date and the page it came from, since a price is neither a definition nor a measurement of Veritas ([DEBT-040](../debt-ledger.md#debt-040--the-price-table-is-a-vendors-page-copied-once-and-nothing-notices-when-it-moves)); a model the table does not price costs `None` and never 0, and groq is one of those. `ChatCompletions` is the one implementation, an OpenAI-compatible Chat Completions client at temperature 0. `PROVIDERS` is the whole of what it may be pointed at from the environment: **`openai`** (`OPENAI_API_KEY`, `gpt-5.4-mini`, the default, chosen by Sub-step 8.1's measurement) and **`groq`** (`GROQ_API_KEY`, `openai/gpt-oss-120b`), chosen by `VERITAS_LLM_PROVIDER` and `VERITAS_LLM_MODEL`, per [ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md); a third name raises rather than dials it. `model_for(provider, model)` builds one directly, and `registered_models(providers, model)` builds the set a sweep runs over — the whole registry by default, or one provider on one named model, which is what ranking candidates costs. **A model that rejects `temperature=0.0` is not usable at all**: two of the four candidates 8.1 priced answered every call with a 400, and the pinned temperature is not negotiable. Keys come from the environment or from `.env`, which `python-dotenv` reads without overriding what is set; `.env.example` is the committed template. Nothing outside the package names a provider, a model, a key or a message role. Every failure — refused, timed out, no text, no choice, unsupported provider, missing key — arrives as one `LanguageModelError`, and the missing-key message names the variable to set. `openai` is imported inside the client, so importing the package costs nothing until a model is called. |
| Orchestrator | ✅ working | `veritas/orchestrator/` — `rewrite.py`, `generate.py`, `answer.py` and `flow.py` behind an `__init__.py` that re-exports all four. **All seven steps of the flow run.** `flow.py` holds the `Orchestrator`: built over one Warehouse, it gives the Gate's `SemanticLayer` to the Retriever and to the rewrite step so one reading of `semantic/` serves every step, holds the Retrieval Strategy so a sweep varies the Orchestrator rather than the question, and resolves the model at the moment it is called so constructing one costs no key. `answer(question, access_profile)` runs REWRITE → RETRIEVE → GROUND → GENERATE → VALIDATE → EXECUTE → ANSWER and returns a `GroundedAnswer` however it ends. **`rewrite.py` is step 1**: `rewrite(question)` returns a frozen `Rewrite` carrying the question as asked, the text Retrieval searches, the Certified Metrics each Ambiguous Term resolved to, and the Clarifying Question asked back — `None` exactly when the question is ready to retrieve for. Which terms a question says is matched against **every spelling** [Glossary Section D](../glossary.md#d-ambiguous-terms) registers — the *User says* name and each *Also said as* alias, one pattern per spelling and the earliest match winning — in the order the question says them, with `X` in a spelling matching the subject it stands for, whether it sits between two halves or ends the phrase; which meaning it named is the model's answer, given only those terms' own `description` and `resolution` — plus the spelling the question used, on the terms where that is not the registered name, since the answer is keyed by the name; whether that answer counts is decided against `disambiguates`. A question saying no Ambiguous Term costs no model call. A Clarifying Question quotes the words the question used rather than the name the corpus files them under, so a person who typed *"turnover"* is asked about "turnover" ([DEBT-029](../debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently) paid). A resolved meaning is written into the question in whichever `RewriteForm` is asked for — appended in a parenthesis, or **spliced over the words that were ambiguous**, which is the default because it scored higher over the Gold Question Set ([DEBT-030](../debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it) paid). Splicing keeps the subject a spelling captured, so *"how much does account 12 have"* resolved to `Cash Balance` becomes *"Cash Balance account 12"*, and it writes over a term's **first** mention only, so a question saying one twice keeps the second ([DEBT-036](../debt-ledger.md#debt-036--splicing-writes-over-the-first-mention-of-a-term-and-leaves-every-later-one)); the rewritten question is what Retrieval searches **and** what the model is grounded in, and only the first of those has been measured. **`generate.py` is steps 3 and 4.** `GROUNDED_FIELDS` is the whitelist of what each entry type may put in front of a model — parallel to `SEARCHABLE_FIELDS`, `REFERENCE_FIELDS` and `SQL_FIELDS` — and an **Ambiguous Term grounds nothing**, because the rewrite step has already settled which meaning was wanted. Every field that holds a route is written out as the `JOIN … ON …` clause it stands for rather than as the Join Path's name, and each Metric Definition's join list also carries the joins the Access Profile requires from that metric's `from_table`, taken from the access axis's own `routes`. The rules the model is given are the Gate's rules written as instructions, plus the statement's clause order; the reply is one JSON object holding either a statement or a refusal, and a refusal is a first-class result. **`answer.py` is the contract**: a frozen `GroundedAnswer` carrying the question, what Retrieval searched for, the SQL, the rows, the `Lineage`, the `Validation Gate outcome`, the `EndedBy` member naming the step that ended it, the `ModelCall`s it made and the seconds it took, and either a refusal or a Clarifying Question — never both, and never a number without the statement and the allowing verdict behind it, which is *"Veritas never returns a bare number"* as three construction errors. `Lineage` holds the entries themselves, so it records the version each was read at; it leads with the Ambiguous Terms the rewrite step resolved and continues with what the **statement** used, read off the allowing verdict — the metric it computed, the axis it sliced by, the Join Paths its route was certified by — so a question that reached no allowing verdict cites the terms alone ([DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used) paid). **A question ends without a number in five ways**, each a `GroundedAnswer` and each an `EndedBy` member: `rewrite` for an Ambiguous Term left open, `retrieval` for nothing retrieved that defines a metric, `generation` for the model refusing, `gate`, and `engine` for a statement the Gate allowed and the Warehouse would not run — plus `answer`, and `provider` for a call that never came back, which no Grounded Answer may carry. The member is **stated by the branch that ends the question** rather than derived, because the middle two are the same shape from outside, and `endings()` refuses a member the fields contradict ([DEBT-032](../debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by) paid). |
| Validation Gate | ✅ working | `veritas/validation/` — an `__init__.py` that re-exports, `outcome.py`, `profile.py`, and `gate.py`. **All five of the Gate's decisions, spelled as eight rules.** `outcome.py` holds the `Validation Gate outcome` — frozen, carrying allowed-or-rejected, the explanation a person reads, the `Rejection Reason` members a chart groups by, the rules that actually ran, the trusted rewrites the verdict was reached under, and, on an allowing verdict alone, what the statement was composed from: the Certified Metrics its expressions traced to, the certified axes it sliced by and the Join Paths its route was certified by, as registered entry names. A rejecting outcome that names any of them cannot be built — and the `RejectionReason` taxonomy itself, thirteen members registered in code by [R3](../plan/step-005-validation-gate.md#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25) — a rule may register more than one, and the tracing rule registers three while the certified-route rule registers four. It is a separate module from the rules because a Grounded Answer, the App and Observability all read a verdict and import no rule. `profile.py` holds the `Access Profile` — a role, a permitted region, and the `RestrictedColumn`s that role may not see, as a table and a column rather than a bare name — and the one profile this slice declares, `ANALYST`, permitting `EU` and forbidding `dim_client.client_name`. The permitted region is a **value of the `by region` axis**, named by the `ACCESS_AXIS` constant, never a second registration of the column or its buckets; a region that axis does not certify raises `ValueError` at the first judgement made under the profile. **The profile is an argument to `judge`, not a field on the Gate** — `judge(sql, access_profile)`, with no default, so no statement is judged without an identity and a second identity is a second call rather than a second Gate ([R14](../plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27)). `rules(access_profile)` binds it into the two rules that read it, so the other six take a statement and nothing else. `gate.py` parses with `sqlglot.parse` rather than `parse_one` — `parse_one` reads `SELECT 1; SELECT 2` as one `Block` node — and runs eight rules in the order a statement meets them, **stopping at the first that rejects**: unparseable, more or fewer than one statement, not a `SELECT`, a planner estimate over the scan ceiling, a statement whose expressions do not all trace, a statement whose answer would carry a Restricted Column, a statement computed across joins or over a date column or without a certified filter the corpus does not certify for the metric it traces to or sliced by an axis no route reaches from it, and a statement not scoped to the Access Profile's permitted region. The ceiling is a policy constant and a constructor argument, not a measurement. `TRUSTED_REWRITES` names `qualify` and `merge_subqueries` as [C5](validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two) requires, and `resolve` is the one place that applies them; it turns both of the ways sqlglot refuses a statement — its own `SqlglotError`, and the bare `AssertionError` its `assert_is` raises — into one refusal a rule can act on. **The tracer, the lineage walk and the route reader live here too** — `resolve`, `projected_expressions`, `metric_expressions`, `certified_form`, `certified_forms`, `certified_metrics_only`, `columns_reaching_the_answer`, `restricted_columns_in_projection`, `route_of`, `certified_route` and `date_columns_filtered`, which the spike imports back; each has a variant taking an already-resolved tree, which is what lets one judgement resolve once. A `Route` is where a statement's rows start and the joins it reaches the rest through, read off a parse tree or assembled from the corpus — the corpus through the same reader as the query, which is `certified_form`'s argument applied to the route. **Permitted and required are two Routes**: `required_route` is the metric's own `join_paths`, which a statement must carry, and `permitted_route` adds the `routes` of each axis it groups by and the route the Access Profile's predicate needs, which it may. A join beyond the second is a rejection and a join absent from the first is a rejection; both go through `assembled_route`, which names each Join Path once and keeps them in the order they are joined. A certified expression is canonicalised through the same `resolve` a statement goes through, in a scope holding the Warehouse tables the expression names; without that symmetry `Position Change` traces to nothing. The Restricted Column rule asks whether a column **reaches the answer**, not whether its name appears: it numbers the output columns and walks each one's lineage back to base tables, so a name in a comment, in a string literal, in a filter, or projected inside a subquery and aggregated away is not a projection of it. The Semantic Layer is loaded once at construction; the catalogue, the resolved statement and the corpus's canonical forms are read **once per judgement**, on a `Reading` that every rule shares, so all four parse-tree rules judge one tree qualified against one catalogue. They are read lazily rather than in the constructor, because the rules that need nothing must return a verdict on a day the Warehouse will not open. **The order is a safety property, not a speed one**: the rules that need nothing touch nothing — proved by judging every probe through a Warehouse that raises on contact — and the single-statement rule runs before the bounded read because the engine executes the tail of a multi-statement string even under `EXPLAIN`. The route rule reads all three of the fields that pin down which rows a certified expression covers — `join_paths`, `date_column` and `filters` — the last since [DEBT-020](../debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters) was paid. `where_conjuncts` reads the **outermost** WHERE clause's ANDed parts, which is what both the filter comparison and the access predicate ask of a statement; a predicate inside a subquery the optimizer could not flatten does not count, which is the fail-closed direction. `grouped_columns` reads every scope's `GROUP BY`, because reaching an axis is permitted by grouping on it and never by mentioning its table. **A ninth reading closes the two holes Sub-step 5.5 left.** A `Join` carries the kind of join as well as the table and the condition, collapsed by `join_kind` so that a bare `JOIN` and an explicit inner join stay one join and a left join is another — so an outer join over a certified condition no longer passes as the inner one a Join Path means, and `joins_beyond` spells the kind in the rejection ([DEBT-022](../debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one) paid). And `metric_expressions_through` keeps, beside each projection's canonical form, the joins the aliases in it were read through, so `crossed_conversion` can require each metric expression to read only through the joins its **own** Metric Definition names — which the union of two metrics' routes cannot say ([DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart) paid). Both refuse as `UNCERTIFIED_ROUTE`, and `tests/test_gate.py` prints what each returns. The Orchestrator judges every statement it generates through this Gate, and executes only what it allows. |
| Validation Gate check | ✅ working | `.claude/scripts/check_validation_gate/` — a **package**, by [R8](../plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25): `__main__.py` holds the rule order, the report and the exit code, `probes.py` the shared machinery, and one module per Gate rule — `read_only.py`, `traces.py`, `restricted.py`, `route.py` and `access.py`, all five. Run as one command, `uv run python .claude/scripts/check_validation_gate/`, because Python runs a directory holding a `__main__.py`. Needs a filled Warehouse. Seventy-nine probes, each declaring the verdict and the Rejection Reason members it was measured with, so a rejection for the **wrong reason** fails as loudly as no rejection. `read_only.py` holds twelve: the six shapes read-only has to cover, a union, a string that is not SQL, a query over a lowered ceiling, one the engine will not plan, a cross product, and an ordinary question. `traces.py` holds eighteen — the shapes Sub-step 3.2 measured, re-judged through the whole Gate rather than through a tracer, plus a statement that aggregates nothing, one the optimizer will not resolve, and a certified expression sitting beside a Shadow Metric in one projection, which is the probe for the word *every* — and then builds nine more from `semantic/metrics/`, one per Certified Metric, so a tenth Metric Definition is a tenth probe with no edit — probes built out of the corpus they are checked against, which is [DEBT-018](../debt-ledger.md#debt-018--six-certified-metrics-have-no-expression-text-pinned-outside-the-corpus): they prove the Gate recognises what `semantic/metrics/` says, and six of the nine expressions have no text pinned anywhere outside it. `restricted.py` holds ten, each declaring **three** answers rather than one — the Gate's verdict, the parse tree's reading, and what a search of the query's text would say — so ADR-0003's rejected alternative is shown wrong on every run rather than in an argument; nine are the spike's claim-2 shapes and the tenth is a `SELECT *` written so that it reaches the rule. `access.py` holds twenty-one, each also declaring whether this rule reads the statement as scoped: every Certified Metric scoped and unscoped, which is eighteen and is how the rule is shown to bind on the Snapshot and movement metrics and not only on the trade-side four, plus three about the slice route — `Net Revenue by region`, `Cash Balance by instrument type` refused on the absent key, and one join to a table the statement does not group by. It **executes** the Glossary's worked example twice, unscoped and scoped, so the three buckets the axis registers and the one the Access Profile permits are printed side by side, and it runs three mutations: the access rule deleted, the absent-key branch deleted, and the certified-filter comparison deleted, each re-run to show what stops being refused. `route.py` holds nine, each also declaring whether the statement is off its metric's route and whether it filters on a date column that metric is not certified against: the spike's wrong-currency statement, a cross product computing a certified metric, a count with a join that multiplies it, a slice by `by region`, the same notional converted the certified way, a period keyed on Trade Date and the same period keyed on Settlement Date, and the two halves of [DEBT-020](../debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters). It **executes** three pairs and prints how far apart each is, because a rejection is only worth having if the thing rejected returns a different number; every date in it is read from the Snapshot calendar; and it rebuilds all nine Certified Metrics from `semantic/metrics/` to show the rule allows each one computed the way its own entry says. **The *character for character* claim is checked in both modules that make it**: `probes.py` reads the spike's statements out of its **source text** with `ast` rather than importing it, so a check that runs on every commit does not depend on a 1,700-line script staying importable, and `traces.py`'s fifteen are checked the same way — including the one it judges under a shorter local name, and the one shape the spike measures that it does not judge, which is **declared** with where the Gate refuses it instead. Checks beyond the probes: every probe decided before the bounded rule is decided again through a Warehouse that raises on any attribute access; the engine is asked to plan a two-statement string against a throwaway table in an in-memory Warehouse, and the run fails if the table **survives**; the planner's estimate is compared against a real row count, because an unread plan sums to zero and zero is under every ceiling; the corpus is canonicalised the rejected way as well as the Gate's way, failing the run if **no** Certified Metric depends on the difference; the Access Profile's own declaration is printed and an empty one fails the run; two statements no rule can read are put to the detector directly, which must refuse rather than report nothing found; and one judgement is made through an adapter that counts catalogue reads, failing the run on anything but one, with the `Reading`'s own memo read afterwards to show the resolution and the corpus were each computed once. Statements a Sub-step's own rules allow are checked by the rules that **ran** rather than by the final verdict, so a later rule refusing them is not mistaken for these rules refusing everything. It also prints the trusted rewrites, the ceiling's current headroom, and what one judgement costs. |
| App | ✅ working | `veritas/app/` — `render.py` and `page.py` behind an `__init__.py` that re-exports the first. `uv run streamlit run veritas/app/page.py` serves one page: the identity a question is asked as, a question box, and what the question came back as. `render.py` turns a Grounded Answer into strings and imports no Streamlit — values under the column names the engine returned, a single figure under the `unit` and Reporting Currency of the metric its Lineage identifies, the Lineage one line per entry, and the verdict as the rules that ran or the Rejection Reasons that fired; `page.py` places them and is the only module in the repository permitted to import `streamlit`, which `tests/test_app.py` checks the way `check_warehouse.py` checks the `duckdb` seam. **Nothing is hidden**: the statement, the Lineage and the Validation Gate outcome are laid out under every answer, including under a refusal and under a question asked back — the Glossary's *"never renders a bare number"* as a test rather than an intention. The sidebar carries the Access Profile, the model the environment configures, [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s own sentence on what enforcing that profile in the application layer is worth, and whether questions are being recorded and where. **The App is the one caller that writes to the Question Log**, and it writes after it renders: a person sees their answer before the log's verdict on it, a failed write is a warning beside that answer rather than an error in place of it, and the Evaluation sweep drives the same flow a few hundred times and puts nothing on the dashboard. **It is also the one caller that takes Feedback.** Under an answer that reached a row, one form asks for a verdict and an optional sentence and writes both against that row; an answer that reached none — no Question Log, or a write that failed — is offered no form, because there is nothing for a verdict to attach to. The answer being shown is held in session state rather than in the run that produced it, since a Feedback button reruns the script with nothing submitted in the question form, and the form is keyed by the row, so a verdict never carries onto the next answer. The page is driven in tests through Streamlit's own `AppTest`, so every rendering claim is proven without a browser and without a key. |
| Observability | ✅ working | `veritas/observability/` — `log.py` and `postgres.py` behind an `__init__.py` that re-exports both, plus `schema.sql`, laid out like `veritas/warehouse/`. `log.py` is the `QuestionLog` seam — a Protocol with two methods, `record(answer, access_profile) -> int`, returning the row's identifier because Feedback is left against an answer and never against a question string, and `leave_feedback(question_id, feedback)`, which takes that identifier back — plus `Feedback`, a frozen `up` and `note` in the Glossary's own words, and `QuestionLogError`, the one type every failure to record arrives as, so a store that is absent, unconfigured or refusing is one thing to a caller. `postgres.py` is **the only module in the repository that imports `psycopg`**, checked by `tests/test_observability.py` the way the App's Streamlit import is; it reads five variables — `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, the last three spelled as the `postgres` image itself reads them — from the environment or `.env`, defaults the host and the port to what compose publishes, names every missing value at once, and assembles the connection string through the driver rather than by formatting. It holds one connection for the process, applies `schema.sql` on connect, and writes one question in one transaction. `schema.sql` is **four tables**: `question` — one row per question asked through the App, carrying the question and the rewritten question, the `ended_by` member, the Access Profile's role, the statement, the row count, the verdict as `allowed`, `explanation` and a `reasons` array of Rejection Reason values, the refusal or the Clarifying Question, the seconds and the cost; `lineage_entry` — one row per Lineage entry, in the order the answer cites them, with its kind and the version it was read at; `model_call` — one row per call, with the provider, the model, the prompt and completion tokens, the seconds and the cost; and `feedback` — at most one row per question, carrying `up`, the optional `note` and the time it was left, keyed by the question so that a second verdict replaces the first in place and a question deleted takes its Feedback with it. Every `CREATE TABLE` is `IF NOT EXISTS`, so a fresh container and one with a month of traffic reach the same state and nothing is run by hand. A cost is `NULL` for a model `PRICES` does not price, never 0. `docker-compose.yml` is the server — `postgres:18-alpine`, the volume mounted at `/var/lib/postgresql` rather than `data/` under it, a `pg_isready` healthcheck, and the same five variables — and `.env.example` carries a generated password rather than a placeholder, so `docker compose up -d postgres` works on a fresh clone with nothing typed. **The App is the one caller that records**, and the one that takes Feedback: it writes after it renders, so a failed write is a warning beside an answer rather than an error in place of one, its sidebar says whether questions are being recorded and where, and the verdict a person leaves under an answer goes to that answer's own row. `grafana/` charts these rows: the datasource and the dashboard provider as provisioning files, and `question-log.json` — seven panels, each one statement over the log, every panel's query executed by `tests/test_observability.py` against the schema and then through Grafana, and all seven seen rendered on 2026-09-04. No row is written for a question the provider never answered ([DEBT-041](../debt-ledger.md#debt-041--a-question-the-provider-never-answered-is-not-recorded), `accepted`). |
| Evaluation | ✅ working | `data/gold/` — **twenty-four Gold Questions**, one file each, and `veritas/evaluation/` reads them. A Gold Question carries the question as a person asks it, `expects` — which of a Grounded Answer's three endings is correct, one of `answer`, `refusal`, `clarifying question` — and, where a number is correct, the gold SQL and the gold result. The dataclass field list is the file format, as it is for a Semantic Entry: an unknown key fails to load, and a question that expects no answer may not carry a statement. **The relevant Semantic Entries are derived, never listed**: the Certified Metrics a statement's projections trace to, the certified axes it groups by or filters on, and the Join Paths those two declare — three readings, all through `veritas/validation/`'s own readers, so a Relevant Set is never a second opinion about what a statement computes. `tests/test_gold.py` compares the Join Paths derived that way against the joins the statement itself carries. **Coverage is read off the statements**: all nine Certified Metrics are computed by one, every gold statement keys on its own metric's `date_column` and on no other date, `by region` and `by instrument type` are both sliced, all five Ambiguous Terms are asked about, and all three endings are present. `RESULT_TOLERANCE` is how close two result sets must be to be the same answer — relative, because the metrics span a count of dozens and a notional of tens of millions — and it is what [DEBT-004](../debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal) and [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level) are measured against: the test executes both halves of each Section C pair a Gold Question turns on. **One gold statement the Gate refuses** — `Account Value`, whose only correct form adds the two halves the corpus's `derives_from` describes, which the Gate reads as a Shadow Metric ([DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)); `REFUSED_TODAY` in the test names it, so paying that entry breaks the exemption. **Retrieval is measured.** `veritas/evaluation/retrieval.py` computes hit rate and Mean Reciprocal Rank (MRR) over the twelve Gold Questions that should come back as a number, and `uv run python -m veritas.evaluation retrieval` prints one row per Retrieval Strategy per setting. A ranking is scored against the **searchable part** of a Relevant Set — Join Paths publish no searchable text and no search can return one, so they are dropped rather than counted as misses — and both measures come off one number per question, `reciprocal_rank`, so a hit is a reciprocal rank above zero and the two cannot disagree about what a hit is. The question a ranking is scored for is the rewritten one a **correct** rewrite step would have produced, derived from the gold SQL's own metrics, so the sweep costs no model call and no key. The two settings it varies are the two the Ledger left open: `SearchableForm` and `RewriteForm`, both re-runnable rather than deleted, and their defaults are what the sweep chose ([DEBT-027](../debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match) and [DEBT-030](../debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it) paid). **What Veritas answers is measured too.** `veritas/evaluation/generation.py` runs the whole flow — rewrite, retrieve, ground, generate, validate, execute — once per `PromptForm` per registered provider, and `uv run python -m veritas.evaluation generation` prints one row per cell. Three measures come off each run: the **ending** the set calls correct, **Execution Accuracy** over the questions whose ending is a number, and an **LLM-as-judge's agreement** with the first. `EndedBy` names the step of the flow that ended each question — read off the Grounded Answer, which owns the taxonomy since Sub-step 8.3, and extended here by `provider` alone for a call that never came back — so a Gate refusal is not scored as a wrong number and a provider that never replied is not scored at all. A question is compared under the same `RESULT_TOLERANCE` the gold set's own constraints were built against; one gold-labelled a refusal or a Clarifying Question scores by ending the same way. The judge is shown the question, the correct statement and what Veritas did, and **not** the two result sets — comparing numbers is `same_result`'s job, and a judge given them would make the agreement a measure of nothing. `answerable_by_veritas` asks the Gate whether it would allow each Gold Question's **own gold statement** and drops the ones it refuses, so [DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)'s cost is derived and names no question: the day the Gate stops refusing it, the sweep scores one question more with no line edited. The sweep needs keys and is opt-in behind `VERITAS_LIVE_MODEL`; the dated table it printed is in the [Step 007 review](../reviews/step-007-evaluation.md#sub-step-74--measure-generation-execution-accuracy-and-llm-as-judge). |
| Containerization | ✅ working | `docker-compose.yml` — **all three services the [Target State row](target-state.md#components) names**: `app`, Postgres and Grafana. Postgres holds the Question Log; Grafana is provisioned read-only from `grafana/`, starts once Postgres is healthy, and serves the dashboard as its home page to a reader who signs in for nothing. The App is built from `Dockerfile`: the interpreter `.python-version` pins, the locked dependencies, the Warehouse replayed from `data/snapshots/` at image build, and both Retrieval models under `FASTEMBED_CACHE_PATH` — so a container reaches no network to answer except the model provider's, which `docker run --rm --network none veritas-app python -m veritas.retrieval` is the standing check on. `.env` never enters a layer: the service reads it through `env_file` and overrides two values inside the network, `POSTGRES_HOST` to the service name and `POSTGRES_PORT` to the port Postgres listens on rather than the one compose publishes. Published on `${APP_PORT:-8501}`, started once Postgres is healthy, health-checked on Streamlit's own `/_stcore/health`. `POSTGRES_HOST` still defaults to `localhost` in `.env.example`, because that is the developer path: `uv run streamlit run veritas/app/page.py` on the host reaches the published port. |

## Repository layout

```
veritas/
├── CLAUDE.md                  # operating agreement (root: Claude Code auto-loads it)
├── pyproject.toml, uv.lock, .python-version, .gitignore
├── .env.example               # the two provider keys and the Postgres and Grafana
│                              # credentials, as a committed template. `.env` itself is
│                              # gitignored and is what `veritas/llm/`, `veritas/observability/`
│                              # and `docker-compose.yml` read — one set
├── Dockerfile, .dockerignore  # the App's image — interpreter, dependencies, the built
│                              # Warehouse and both Retrieval models; never `.env`
├── docker-compose.yml         # all three services: the App, Postgres (the Question Log)
│                              # and Grafana (its charts)
├── grafana/
│   ├── provisioning/          # the datasource and the dashboard provider, as files
│   └── dashboards/            # question-log.json — seven panels, one statement each
├── data/
│   ├── snapshots/             # committed source data + dated probe record
│   │   └── ingestion/         # ingestion's own snapshots — one per source, one
│   │                          # per traded Instrument; only --refresh writes here
│   ├── veritas.duckdb         # the Warehouse — gitignored, rebuilt by ingestion
│   └── gold/                  # the Gold Question Set — twenty-four files, one per gold
│                              # question: the question, the ending it expects, and the
│                              # gold SQL and gold result where that ending is a number
├── semantic/                  # the Semantic Layer — the certified registry, as data
│   ├── metrics/               # nine files, one per Certified Metric of Section B
│   │   ├── gross_revenue.yaml            # ─┐ the trade side
│   │   ├── net_revenue.yaml              #  │
│   │   ├── traded_notional.yaml          #  │
│   │   ├── trade_count.yaml              # ─┘
│   │   ├── cash_balance.yaml             # ─┐ the Snapshot side
│   │   ├── account_value.yaml            #  │ composed: its own expression plus
│   │   ├── unrealised_pnl.yaml           #  │ Cash Balance
│   │   ├── position_change.yaml          # ─┘
│   │   └── realised_pnl.yaml             #   the accounting ledger
│   ├── joins/                 # thirteen routes; eight for the metric expressions and
│   │                          # five that reach dim_client for the access predicate
│   │   ├── trade_to_fx_rate_on_denomination_currency.yaml    # ─┐ the Section C
│   │   ├── instrument_to_fx_rate_on_quotation_currency.yaml  # ─┘ currency pair
│   │   ├── trade_to_instrument.yaml
│   │   ├── balance_snapshot_to_fx_rate_on_snapshot_date.yaml
│   │   ├── position_snapshot_to_instrument.yaml
│   │   ├── position_snapshot_to_price_on_snapshot_date.yaml
│   │   ├── instrument_to_fx_rate_on_snapshot_date.yaml
│   │   ├── accounting_movement_to_fx_rate_on_movement_date.yaml
│   │   ├── trade_to_account.yaml                  # ─┐ one hop to dim_account per
│   │   ├── position_snapshot_to_account.yaml      #  │ fact table a metric starts
│   │   ├── balance_snapshot_to_account.yaml       #  │ at, and the last hop all
│   │   ├── accounting_movement_to_account.yaml    #  │ four share
│   │   └── account_to_client.yaml                 # ─┘
│   ├── ambiguous/             # five words, one per row of Glossary Section D
│   │   ├── revenue.yaml       # ─┐ each names the Certified Metrics it
│   │   ├── volume.yaml        #  │ disambiguates between — and publishes no SQL,
│   │   ├── balance.yaml       #  │ because it is a claim about language
│   │   ├── pnl.yaml           #  │
│   │   └── how_much_does_x_have.yaml  # ─┘
│   └── dimensions/            # five certified axes — the answer to "by what?"
│       ├── by_trade_date.yaml            # ─┐ three date senses, not one: a
│       ├── by_snapshot_date.yaml         #  │ Snapshot metric's route never
│       ├── by_accounting_movement_date.yaml # ─┘ reaches fct_trade.trade_date
│       ├── by_region.yaml                # ─┐ the two enumerated axes; their
│       └── by_instrument_type.yaml       # ─┘ buckets are checked against the data
│                                         #   every axis also names the routes that
│                                         #   reach it, per fact table
├── veritas/
│   ├── semantic/
│   │   ├── __init__.py        # re-exports the loader, like veritas/warehouse/
│   │   └── loader.py          # reads semantic/ into frozen entries; executes nothing
│   ├── retrieval/
│   │   ├── __init__.py        # re-exports both modules
│   │   ├── searchable.py      # which fields of an entry a search may match, and the
│   │   │                      # record per entry an index is built over. A Join Path
│   │   │                      # is all schema, so it renders as no text at all
│   │   └── search.py          # the four searches, the fusion, the re-ranker, and the
│   │                          # reference closure that carries Join Paths into a result
│   ├── llm/
│   │   ├── __init__.py        # re-exports the one module
│   │   └── model.py           # the LanguageModel seam, the two-provider PROVIDERS registry,
│   │                          # and the one OpenAI-compatible client both are served by —
│   │                          # the only place a provider, a model or a key is named
│   ├── orchestrator/
│   │   ├── __init__.py        # re-exports all four modules
│   │   ├── rewrite.py         # step 1 of the flow: which Ambiguous Terms a question
│   │   │                      # says, which meaning it named, and what to ask back
│   │   ├── generate.py        # steps 3–4: GROUNDED_FIELDS, the prompt built from
│   │   │                      # retrieved entries, and the model call that returns SQL
│   │   ├── answer.py          # the Grounded Answer and its Lineage — a contract,
│   │   │                      # importable without the sequence that produces it
│   │   └── flow.py            # the Orchestrator: all seven steps, and the five ways
│   │                          # a question ends without a number
│   ├── evaluation/
│   │   ├── __init__.py        # re-exports both modules
│   │   ├── __main__.py        # `-m veritas.evaluation retrieval|generation` — each sweep, as a table
│   │   ├── gold.py            # the Gold Question Set's file format, the Relevant Set
│   │   │                      # derived from a gold SQL, and what makes two result
│   │   │                      # sets the same answer
│   │   ├── retrieval.py       # hit rate and MRR, and the sweep over every Retrieval
│   │   │                      # Strategy under every searchable and rewrite form
│   │   └── generation.py      # the whole flow over the Gold Question Set, per prompt
│   │                          # per provider: ending, Execution Accuracy, the judge
│   ├── observability/
│   │   ├── __init__.py        # re-exports both modules
│   │   ├── log.py             # the QuestionLog seam, Feedback, and the one error type
│   │   ├── postgres.py        # the Postgres implementation — the only psycopg importer
│   │   └── schema.sql         # the four tables, applied on connect
│   ├── app/
│   │   ├── __init__.py        # re-exports render.py, and not the page
│   │   ├── render.py          # a Grounded Answer as strings a person reads —
│   │   │                      # no Streamlit, so every claim is testable
│   │   └── page.py            # the Streamlit page: identity, question box, answer,
│   │                          # SQL, Lineage, verdict. The only streamlit importer
│   ├── validation/
│   │   ├── __init__.py        # re-exports all three modules
│   │   ├── outcome.py         # the Validation Gate outcome + the Rejection Reason
│   │   │                      # taxonomy — a contract, importable without the rules
│   │   ├── profile.py         # the Access Profile: a role, a permitted region, and
│   │   │                      # the Restricted Columns it forbids. One profile
│   │   └── gate.py            # the eight rules, the tracer, the lineage walk and
│   │                           # the route reader — all five of the Gate's
│   │                           # decisions
│   ├── warehouse/
│   │   ├── adapter.py         # the Warehouse Adapter — the only duckdb importer
│   │   ├── schema.sql         # the ten-table star schema, hand-authored
│   │   └── builds/            # hand-authored raw→star SQL, one file per table
│   │       ├── dim_instrument.sql        # ─┐ the real half, built first
│   │       ├── fct_instrument_price.sql  #  │
│   │       ├── fct_fx_rate.sql           # ─┘
│   │       ├── dim_client.sql            # ─┐ the synthetic half; dim_client.sql
│   │       ├── dim_account.sql           #  │ carries the reasoning for all seven
│   │       ├── fct_trade.sql             #  │
│   │       ├── fct_cash_movement.sql     #  │
│   │       ├── fct_accounting_movement.sql  │
│   │       ├── fct_position_snapshot.sql #  │
│   │       └── fct_balance_snapshot.sql  # ─┘
│   └── ingestion/
│       ├── __main__.py        # the entry point: replay by default, --refresh
│       ├── universe.py        # the 19 traded Instruments + two vocabulary maps
│       ├── snapshots.py       # snapshot-and-replay — the only socket in the package
│       ├── sources.py         # NASDAQ Trader · SEC · Yahoo metadata and bars, for dlt
│       └── simulator.py       # the seeded simulator — reads the real tables,
│                              # generates the client side as a pure function
├── tests/                     # Delivery Mode's proving system — `uv run pytest`
│   ├── conftest.py            # the repo root, the built Warehouse, the Semantic Layer
│   ├── test_delivery_mode.py  # the frozen check-script set, the history-link ratchet
│   ├── test_retrieval.py      # every entry indexed, every metric alias searchable, no
│   │                          # schema; a fixed question set found under all four strategies
│   ├── test_rewrite.py        # each of the five Ambiguous Terms resolved or asked back,
│   │                          # in every spelling Section D registers, read back against it
│   │                          # — against a stub model; one live test, skipped with no key
│   ├── test_orchestrator.py   # what the prompt grounds, and every way a question comes
│   │                          # back — two live tests, skipped with no key
│   ├── test_gate.py           # the crossed conversion and the outer join, with the
│   │                          # numbers each returns: DEBT-021 and DEBT-022's probes
│   ├── test_gold.py           # every gold SQL judged and executed, coverage read off
│   │                          # the statements, the Relevant Set compared against the
│   │                          # route, and both Section C pairs executed side by side
│   ├── test_evaluation.py     # the measures on a toy ranking, the ground truth a
│   │                          # ranking is scored against, and a `text`-only sweep
│   ├── test_app.py            # what the page shows, records and takes as Feedback, through
│   │                          # Streamlit's AppTest — two live tests, skipped with no key
│   ├── test_observability.py  # the seam, the rows, the dashboard — the row and chart
│   │                          # claims need Postgres and Grafana up, and skip without
│   └── test_llm.py            # what goes on the wire, against a stub server on localhost
└── .claude/
    ├── skills/                # 5 framework skills
    ├── scripts/
    │   ├── verify_framework.py        # structure: docs, links, skills, interpreter
    │   ├── check_language.py          # content: Glossary + writing conventions
    │   ├── check_warehouse.py         # schema vs Glossary, constraints, adapter seam
    │   ├── check_semantic_layer.py    # every published expression executes, and agrees
    │   ├── check_validation_feasibility.py  # the sqlglot spike — all four claims
    │   ├── check_validation_gate/     # a package: one module per Gate rule
    │   │   ├── __main__.py            # the runner — rule order, report, exit code
    │   │   ├── probes.py              # the adapter, the probe record, the report
    │   │   ├── read_only.py           # parseable · one statement · a read · bounded
    │   │   ├── traces.py              # every metric expression traces
    │   │   ├── restricted.py          # no Restricted Column reaches the answer
    │   │   └── route.py               # the metric's own joins and its own period
    │   └── check_data_availability.py
    └── docs/
        ├── glossary.md
        ├── debt-ledger.md
        ├── extension-register.md
        ├── design/{target-state,current-state,product-brief}.md
        ├── design/{data-availability,validation-feasibility}.md   # the two design gates
        ├── adr/
        ├── plan/
        └── reviews/
            └── images/        # screenshots a review cites, committed with it
```

## Known gaps

**What Veritas answers is measured, and since Sub-step 8.1 the default provider answers
every answerable Gold Question.** Both halves are scored over the Gold Question Set —
hit rate and Mean Reciprocal Rank for Retrieval, Execution Accuracy and an LLM-as-judge's
agreement for generation, across two prompts and both registered providers.
`gpt-5.4-mini` answers **eleven of the eleven** answerable Gold Questions correctly under
both prompts, against `gpt-4o-mini`'s two, which is why the registry row changed.
[DEBT-037](../debt-ledger.md#debt-037--nothing-tells-the-generator-that-a-date-it-has-never-heard-of-is-not-a-reason-to-refuse)
— the open-ended list of reasons to refuse — is **`accepted`**: prose was measured not
to move it, the honest fix is barred, and the generation sweep is the guard. But
`gpt-5.4-mini` **answers *"show me ten trades"*** — a refusal-expected probe — as the
nearest Certified Metric, and the Gate passes it because it traces
([DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it)):
the Gate checks that a statement computes a metric correctly, not that it answers the
question asked. **The two-provider table itself is not yet republished**: the sweep that
would carry it hit Groq's 200,000-tokens-per-day cap on 2026-09-03 and failed its own
runner, so the Groq half of that run is not a measurement and one re-run is owed
([DEBT-039](../debt-ledger.md#debt-039--the-published-two-provider-sweep-failed-its-own-runner-and-is-not-republished),
postponable) — the
[8.1 review](../reviews/step-008-observability.md#sub-step-81--choose-the-openai-default-model-by-measurement)
carries the failed run and the command. Both measures are also narrow: retrieval's
**hit rate is 1.000 in every cell**, so only MRR separates those settings, over twelve
questions in steps of 1/24; generation's Execution Accuracy is over **eleven** questions,
so one of them is worth 0.09. The dated tables and the commands that produce them are in
the [Step 007 review](../reviews/step-007-evaluation.md).

**Every question is logged and charted, and nobody has looked at the charts.** Since
Sub-step 8.3 a question asked
through the App is a Postgres row carrying its ending, its verdict with the Rejection
Reasons, its Lineage, its model calls, its seconds and its cost — so
*"Validation-Gate rejections by reason"* and *"metric-usage frequency"* are two `GROUP
BY`s away rather than chart descriptions — and since 8.5 they are the two panels the
Monitoring criterion names by name. Since 8.4 the verdict a person leaves on
an answer is a row too, so all four of what an
[`Operational Measure`](../glossary.md#a-the-system) names are recorded. **What no test
can reach is the picture**: every panel's query is executed against the schema and then
through Grafana, and what a panel *looks* like is checked by a person opening the page —
which happened on 2026-09-04 and paid
[DEBT-042](../debt-ledger.md#debt-042--no-panel-of-the-dashboard-has-been-seen-rendered),
leaving the two images in the
[8.5 review](../reviews/step-008-observability.md#sub-step-85--the-grafana-dashboard) as
the record of it. Three
narrower gaps sit inside the log itself. A question the provider never answered is **not
a row** at all — [DEBT-041](../debt-ledger.md#debt-041--a-question-the-provider-never-answered-is-not-recorded),
**`accepted`** in 8.5 because every counting panel reads the ending alone — so an outage
reads as an afternoon nobody asked anything. A cost is
[list price as of 2026-09-03](../debt-ledger.md#debt-040--the-price-table-is-a-vendors-page-copied-once-and-nothing-notices-when-it-moves)
and is `NULL` for every groq call, which no page this project has read carries a price
for. And a question's `seconds` is what a person waited — retrieval, the Gate and the
engine included — not the sum of its model calls, which are timed separately in
`model_call`.

**`Account Value` is a Certified Metric with no answer.** Its only correct statement adds
the two halves `derives_from` describes, and the Gate refuses that as a Shadow Metric —
[DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows).
Both Ambiguous Terms that can resolve to it, `balance` and `how much does X have`, can
therefore resolve to a metric Veritas will not compute.

**Two published fields have no check on what they say** — `description`, and a Metric
Definition's `aliases`. Both reach the searchable text, and `tests/test_retrieval.py`
proves every metric alias gets there, but nothing measures whether either helps a
question find its metric: the sweep in 7.3 scores an entry's fields *against each other*
and never one field against its own absence. An
**Ambiguous Term's** `aliases` are the exception on both counts: they are read back
against Glossary Section D's own column, and they are not searchable text at all. A Metric Definition's `grain` is read by nobody beyond
that same text; a Dimension Definition's is compared against the Glossary's.

**A Snapshot metric executed over the whole Warehouse is not a number anyone would ask
for.** `Cash Balance` summed across every Snapshot date is every date in the Snapshot
calendar added together — `check_semantic_layer.py` prints how many, on the
`by snapshot date` line — and the check executes it that way on purpose: it is the
strongest thing a corpus check can do without inventing a question. The "as of" date
comes from the question, and the Gold Question Set is where the questions that carry one
now live: every gold statement keys on its own metric's `date_column`, which is what
[DEBT-033](../debt-ledger.md#debt-033--the-generators-live-evidence-is-five-self-written-questions-and-four-certified-metrics-never-reach-it)
was opened about and 7.1 paid. Sub-step 7.4 is the first live run to have been asked
them, and the period every one of them carries is what
[DEBT-037](../debt-ledger.md#debt-037--nothing-tells-the-generator-that-a-date-it-has-never-heard-of-is-not-a-reason-to-refuse)
was found by.

**Every test a reviewer runs drives a stub** — a stub model for the rewrite step, a stub
server on `127.0.0.1` for the boundary — so `uv run pytest` needs no key and opens no
socket, and what it proves is the request Veritas builds, the reply it reads, and what it
does with each answer a model could give. **Four tests are not stubs, and all four are
opt-in**: `VERITAS_LIVE_MODEL=1` runs the configured provider against the real prompt —
one on the rewrite step, which is how
[DEBT-028](../debt-ledger.md#debt-028--no-test-reaches-a-real-provider-so-the-live-path-is-proven-only-by-a-stub-server)
was paid, two on the generator — one over the five questions the corpus covers, one over
a question it does not — and one that asks a question through the App's own page. The
first three have been run against both providers; a key
sitting in `.env` for the App is not consent to spend it on every run, which is why they
stay opt-in. Those five questions are self-written and reach five of the nine Certified
Metrics; the Gold Question Set replaces them, and
`VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation` is what asks it —
the same name gating the same consent, which is why it is `veritas/llm/`'s constant
rather than a literal in four files.

**The spike's go was measured on a spike, and two of its limits still stand.** Only
projections are read for claim 1, so a metric expression appearing solely in a filter
applied after grouping is invisible to the tracer 5.2 built from it, which reads
projections and nothing else.
[What this Step did not measure](validation-feasibility.md#what-this-step-did-not-measure)
is the full list and is deliberately as long as the findings.

**The bounded read has a measured blind spot.** The planner's estimate is summed over
the operators that read a table, and an operator that multiplies rows without reading
one carries no estimate — so a cross product scans each side once and produces the
square, and the rule sees only the scans. `check_validation_gate/` carries it as a probe
with a declared `allowed` verdict; the certified-route rule is what bounds it.

**Two Section C pairs are real but small at book level**, and neither is a defect in the
simulator — making either diverge would mean shaping the data to pass our own check.
Both were constraints on what a Gold Question may ask and both are now **measured
against the result tolerance rather than argued**, in `tests/test_gold.py`:
[DEBT-004](../debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal)
(the FX half of Trade Date against Settlement Date) clears it on the window the Gold
Question asks over, and
[DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level)
(Execution Price against Market Price) clears it over one day and does **not** clear it
over the whole book — which is why there is no book-level notional question in
`data/gold/`, and why that second reading is an assertion rather than a note.
`--distinctions` prints the per-Trade figures on every run.

**What the dialect scan does not cover**, so nobody reads the seam as fully mechanical:
SQL assembled at run time is not a literal and is invisible to a static scan — that is
the Validation Gate's subject — and a name sqlglot files as dialect-neutral passes even
where it is not standard SQL, `generate_series` being the example this project already
uses.

**Out of scope by decision, not oversight.** Single bonds and options: no key-free
Market Price source exists
([DEBT-003](../debt-ledger.md#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope)).
Corporate actions: [EXT-007](../extension-register.md#ext-007--corporate-actions), and
the assumption behind excluding them is checked rather than asserted — `--sources` fails
the run if any day-over-day price ratio exceeds 1.5.

**The wrong-number traps are defended in the Warehouse itself, not only in the spike.**
`check_data_availability.py` measured two of them on three probe series;
`check_warehouse.py --sources` measures **five** on everything loaded, by re-deriving
every price and every rate from the snapshots in Python and printing what each wrong
reading would have changed. How many rows each moves is a measurement, so it lives in the
Step Review with the command and the date, and the check prints the current figure on
every run. The five:

| Trap | Where it would land |
|---|---|
| `Adjusted Close` instead of the unadjusted close | `fct_instrument_price` — the Section C row for `Market Price` |
| A pence quote carried across as pounds | `fct_instrument_price` — a 100× error, `Quotation Currency` |
| A bar's timestamp read as a Coordinated Universal Time (UTC) date rather than the exchange's own | `fct_instrument_price` — every currency-pair price booked one day early |
| Rates stored only for the dates the ECB published on | `fct_fx_rate` — every weekend and ECB-holiday Position converted at nothing |
| A published rate read upside down | `fct_fx_rate` — every conversion inverted |

A sixth gotcha is recorded in [data-availability.md](data-availability.md): Frankfurter
returns HTTP 403 to the default `Python-urllib` User-Agent, which reads as "blocked" when
the fix is one header. `snapshots.fetch` sends a descriptive one.

## Open debt and extensions

The [Debt Ledger](../debt-ledger.md) and the
[Extension Register](../extension-register.md) each carry an Index with every entry's
trigger or readiness condition and its status, and the running counts. Read them there —
this file does not keep a second copy.

**Open debt: 13 · open extensions: 14.** 7.1 paid three on one Trigger — the Gold
Question Set —
[DEBT-033](../debt-ledger.md#debt-033--the-generators-live-evidence-is-five-self-written-questions-and-four-certified-metrics-never-reach-it)
(coverage, now read off the gold statements),
[DEBT-004](../debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal)
and
[DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level)
(both Section C pairs, executed against the result tolerance rather than argued) — and
opened one the gold set is the first thing to expose:
[DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows),
where the tracing rule reads a Metric Definition's `expression` and not its
`derives_from`, so the one composed metric in the corpus has no statement the Gate
allows. 6.3 opened one entry and paid it in the same
Sub-step —
[DEBT-028](../debt-ledger.md#debt-028--no-test-reaches-a-real-provider-so-the-live-path-is-proven-only-by-a-stub-server),
the live model path, run against real OpenAI once a key existed — and filed
[EXT-011](../extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam)
for the providers the closed registry does not reach. It left two open on the rewrite
step:
[DEBT-029](../debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently),
where literal detection missed every other phrasing of a registered word and missed it
silently — the question
[Sub-step 4.4 handed to the Retrieval Step](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24),
put on the Ledger because both halves of its fix were missing: the phrasings are
Glossary content and the fix was unmeasured. **7.2 paid it**, by agreeing the phrasings
into Section D first. And
[DEBT-030](../debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it),
append against splice, which rode the same Step 007 run as
[DEBT-027](../debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match),
where 6.1's flat `text` field stopped being a note in a review. **7.3 paid both**, on one
sweep: splicing and the per-field index each won, no boost was ever guessed, and the
losing form of each is in the Step Review with the table. Splicing brought one back:
[DEBT-036](../debt-ledger.md#debt-036--splicing-writes-over-the-first-mention-of-a-term-and-leaves-every-later-one),
the mention it does not reach, which came due where the generator reads what it wrote —
**7.4 paid it**, splicing every mention rather than the first. 7.4 also opened
[DEBT-037](../debt-ledger.md#debt-037--nothing-tells-the-generator-that-a-date-it-has-never-heard-of-is-not-a-reason-to-refuse)
— the generator not told that a period it has never heard of is not a reason to refuse.
**8.1 fired its Trigger, found the one sentence it prescribes moves no figure on either
provider, changed the default model instead, and closed the entry `accepted`**: prose
relabels the refusal, the honest fix is barred, and the generation sweep is the guard.
6.4 paid
[DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart)
and
[DEBT-022](../debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one)
on their shared trigger and left three open behind the flow it closed:
[DEBT-031](../debt-ledger.md#debt-031--a-grounded-answer-carries-rows-with-no-column-names),
rows with no column names, **paid in 6.5**;
[DEBT-032](../debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by),
a refusal that is not the Gate's carrying prose where the Gate's carries a taxonomy
member; and
DEBT-033, the evidence under both, **paid in 7.1**. DEBT-032 comes due in Step 008.
6.5 paid the two entries its own Trigger named —
[DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers),
the access-control claim, now made in the App with the Ledger's own qualification beside
it, and DEBT-031 — and opened one the App is the first thing to make visible:
[DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used),
where the Lineage under an answer records what the model was shown rather than what the
statement used, which the metric-usage chart in Step 008 would count wrongly — **paid in
8.2**, on that Trigger.
[DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)
is the one that is partly paid and stays open on its main subject, **the hook layer**:
nothing mechanically blocks a commit by Claude, a missing Ledger entry, or a review that
skips a section.

**Debt is not the same as an extension.** Debt means the current code is *wrong,
cheaply*; an extension means it is *right for this scope* and the full system needs more.
The test that settles it: does the trigger fire inside this project's life?

## How we got here

One line per Step. The argument, the evidence and the rulings are in each Step's plan and
its dated review.

| Step | What it did | Plan | Review |
|---|---|---|---|
| 000 | Framework scaffolding — CLAUDE.md, the docs tree, the skills, `verify_framework.py` | [plan](../plan/step-000-framework-scaffolding.md) | [review](../reviews/step-000-framework-scaffolding.md) |
| 001 | Target State design, the data-availability check, and the component-name sweep that made all nine components registered Glossary terms | [plan](../plan/step-001-target-state-design.md) | [review](../reviews/step-001-target-state-design.md) |
| 002 | The Warehouse and Ingestion — the ten-table star schema, four real sources, the seeded simulator, and the adapter seam scan | [plan](../plan/step-002-warehouse-and-ingestion.md) | [review](../reviews/step-002-warehouse-and-ingestion.md) |
| 003 | The sqlglot spike — all four parse-tree claims measured on real data, and the **GO** recorded in [validation-feasibility.md](validation-feasibility.md) with six constraints | [plan](../plan/step-003-validation-feasibility.md) | [review](../reviews/step-003-validation-feasibility.md) |
| 004 | The Semantic Layer — all four entry types, twenty-seven entries, and eighteen checks over them | [plan](../plan/step-004-semantic-layer.md) | [review](../reviews/step-004-semantic-layer.md) |
| 005 | The Validation Gate — **done**. 5.1 built: the outcome, the reason taxonomy, and the four rules that judge a statement's shape. 5.2 built: the tracer, and the rule that every metric expression traces to a Certified Metric. 5.3 built: the Access Profile, and the rule that no Restricted Column reaches the answer. 5.4 built: the route reader, and the rule that a metric is computed across its own joins and over its own date column. 5.5 built: the five Join Paths and the `routes` field that make an axis reachable, the slice route and the certified filters inside the route rule, and the rule that every statement carries the Access Profile's predicate | [plan](../plan/step-005-validation-gate.md) | [review](../reviews/step-005-validation-gate.md) |
| 006 | Retrieval, the Orchestrator and the App — **done**. 6.1 built: the searchable text each entry type exposes, one whitelist per type. 6.2 built: `retrieve` over four Retrieval Strategies, and the reference closure that is the only way a Join Path reaches an answer. 6.3 built: `veritas/llm/` as the one place a provider, a model or a key is named, and the rewrite step that resolves an Ambiguous Term against the question's own words or asks back. 6.4 built: grounding, SQL generation, the flow's seven steps and five ways out, the `Grounded Answer` with its `Lineage` and `Validation Gate outcome`, and the two Gate readings that paid DEBT-021 and DEBT-022. 6.5 built: the Streamlit page that shows the answer with its SQL, Lineage and Gate outcome rather than hiding them, the column names a breakdown needs, and the access-control wording that paid DEBT-008 | [plan](../plan/step-006-retrieval-and-orchestrator.md) | [review](../reviews/step-006-retrieval-and-orchestrator.md) |
| 007 | Evaluation — **done**. 7.1 built: `data/gold/`, the Gold Question Set's file format, the Relevant Set derived from a gold SQL through the Gate's own readers, and the result comparison both Section C constraints are measured against. 7.2 built: Glossary Section D's *Also said as* column, `aliases` on every Ambiguous Term, and detection over every registered spelling. 7.3 built: hit rate and Mean Reciprocal Rank over the Gold Question Set, the two searchable forms and the two rewrite forms compared under all four Retrieval Strategies, and the defaults set to what the numbers said. 7.4 built: the whole flow run over the Gold Question Set once per prompt per registered provider, scored by Execution Accuracy, by the ending the set calls correct and by an LLM-as-judge's agreement with the first, with `PromptForm` as the prompt seam and `EndedBy` saying which step of the flow ended each question | [plan](../plan/step-007-evaluation.md) | [review](../reviews/step-007-evaluation.md) |
| 008 | Observability — **done**. 8.1 built: the OpenAI default model chosen by measuring four candidates cheapest first against Groq's mark, `gpt-5.4-mini` taking the row, and the Evaluation sweep's `--provider`, `--model` and `--no-judge` flags that made ranking one affordable. 8.2 built: what a statement was composed from carried on the allowing verdict, the Lineage read off it, and a single figure labelled with its metric's unit and Reporting Currency. 8.3 built: the Question Log — the seam, three tables and the Postgres implementation, the compose file and its credentials, `EndedBy` moved onto the Grounded Answer and split, a `Reply` carrying what a model call read, wrote and cost, and an App that records after it renders. 8.4 built: Feedback — a fourth table keyed by the question so the latest verdict on an answer stands, a second method on the seam, and one form under every recorded answer, with the answer held in session state so that leaving a verdict does not cost it. 8.5 built: `grafana/` — the datasource, the dashboard provider and a seven-panel dashboard over the Question Log, every panel's query executed by a test against the schema and then through Grafana, the compose file's second service, and the page seen rendered | [plan](../plan/step-008-observability.md) | [review](../reviews/step-008-observability.md) |

**Commits, in order.** Step 000 and Sub-step 1.1 in `6281e6b`, Sub-step 1.2 in `4b48a46`,
Sub-step 1.3 in `9c5b060`, Step 002 planning in `57e8aee`, Sub-step 2.1 in `5a061a7`, the
R16 plan amendment in `cd5e7dd`, Sub-step 2.2 in `0fc5a34`, Sub-step 2.3 in `a58ef91`,
Sub-step 2.4 in `13b99bb`, Sub-step 2.5 in `ce2961a`, Sub-step 2.6 in `6a16d3d`, Step 003
planning in `40d72d8`, Sub-step 3.1 in `d840fa8`, Sub-step 3.2 in `89fee55`, Sub-step 3.3
in `23020e9`, Sub-step 3.4 in `c20d601`, Sub-step 3.5 in `fcf4b7d`, Step 004 planning in
`5d95393`, Sub-step 4.1 in `6c15736`, Sub-step 4.2 in `333d6fc`, Sub-step 4.3 in
`ae75f0e`, Sub-step 4.4 in `71ce677`, Sub-step 4.5 in `7ddd96c`, **Step 005 planning in
`aa42205`**, the Current State trim in `aa918fb`, Sub-step 5.1 in `d98fe7f`, Sub-step 5.2
in `7522ad8`, Sub-step 5.3 in `fce9248`, Sub-step 5.4 in `faba544`, **Sub-step 5.5 in
`1c96281`**, the Step 005 close in `3661263`, the move to Delivery Mode in `2cfd10f`,
**Step 006 planning in `fdf0dc4`**, Sub-step 6.1 in `827fca3`, Sub-step 6.2 in `e0a69bc`,
Sub-step 6.3 in `40a6f94`, Sub-step 6.4 in `d374f8d`, **Sub-step 6.5 in `814b07b`**,
**Step 007 planning in `fdf6693`**, Sub-step 7.1 in `a361b79`, Sub-step 7.2 in
`35099c3`, Sub-step 7.3 in `47dfb8c`, **Sub-step 7.4 in `7e40092`**, the Step 007 close
in `cf64d28`, **Step 008 planning in `874afe9`**, Sub-step 8.1 in `2cf4170`, Sub-step 8.2 in
`b75bdda`, Sub-step 8.3 in `f9b7bef`, Sub-step 8.4 in `05e6b46`, **Sub-step 8.5 in
`f3b76f3`**, **Step 009 planning in `227f328`**, and **Sub-step 9.1 in the commit that carries this line**. A Step's planning commit is normally what
writes the previous Step's last hash into
this list and turns that plan from `in review` to `done`; Steps 005 and 006 were both
closed ahead of that, by the commit carrying their own last Sub-step, so every hash of
each is written here at once and none is left for the next Step's planning commit to fill
in.
