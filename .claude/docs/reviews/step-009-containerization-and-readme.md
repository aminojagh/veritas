# Step 009 — Containerization and `README.md` — Step Review

Handoff notes for Amino, one section per Sub-step. See the `closing-a-substep`
skill. Under [Delivery Mode](../../../CLAUDE.md) each section is capped at 40
lines: the diff is in git and the behaviour is in `tests/`, so this file carries
only what neither of those shows.

---

## Sub-step 9.1 — The App runs in docker compose beside Postgres and Grafana

**Changed.** `Dockerfile`, `.dockerignore` and an `app` service. The image carries
everything a question needs except the key — the interpreter `.python-version` pins, the
locked dependencies, the Warehouse replayed offline from `data/snapshots/`, and both
Retrieval models, fetched by `python -m veritas.retrieval`, a new entry point that names
neither of them. `Retriever.warm()` is new and the App calls it as its page loads, so a
machine whose models are missing says so under a spinner rather than at a question
somebody has just typed.

**Verified.** Every command below was run on 2026-09-05 on the tree as it stands.

```
$ docker compose up -d --build --wait && docker compose ps
 Container veritas-postgres Healthy
 Container veritas-grafana Healthy
 Container veritas-app Healthy
app  Up 6 seconds (healthy)  0.0.0.0:8501->8501/tcp
grafana  Up 19 minutes  0.0.0.0:3000->3000/tcp
postgres  Up 19 minutes (healthy)  0.0.0.0:5432->5432/tcp

$ uv run pytest tests/test_container.py tests/test_observability.py
32 passed, 1 skipped in 2.84s

$ uv run pytest
308 passed, 6 skipped in 96.17s         (from 297 passed, 5 skipped at 8.5)

$ VERITAS_LIVE_MODEL=1 uv run pytest tests/test_container.py -k in_the_container
1 passed, 11 deselected in 21.64s

$ docker run --rm --network none veritas-app python -m veritas.retrieval
  FASTEMBED_CACHE_PATH: /opt/fastembed
  cache directory: /opt/fastembed
  BAAI/bge-small-en-v1.5           embeds in 384 dimensions
  Xenova/ms-marco-MiniLM-L-6-v2    scores a pair at 5.630
PASS — both Retrieval models load from /opt/fastembed · 27 files, 151.5 MiB
```

`verify_framework.py` and `check_language.py` both PASS. `time docker compose build
--no-cache app`, with the base image already pulled: **3m35s**, of which the model fetch
was 27 s and ingestion 32 s; the rest is `uv sync` and exporting layers. `docker images`
gives the image as **2.77 GB**; `docker history`'s largest layers are 1.65 GB interpreter
and locked dependencies, 206 MB models, 85 MB Debian base plus 52 MB uv, 42 MB Warehouse
— which do not sum to 2.77 GB, because the two commands account for a layer differently.
A rebuild after a source edit re-runs the model fetch too, because `COPY veritas/`
precedes it; splitting that would buy 27 s and cost a second copy step.

**Debt.** [DEBT-026](../debt-ledger.md#debt-026--the-retrieval-models-are-downloaded-rather-than-snapshotted)
**paid** on its own Trigger, both halves: the models are fetched at image build — the
`--network none` run above is the proof — and Retrieval is warmed at page load rather
than at first search. No new entry.

**Extensions.** One opened, on Amino's question at the ruling of the first point below:
[EXT-014](../extension-register.md#ext-014--the-container-tests-run-as-pipeline-stages-before-and-after-a-deploy)
— where a test that drives a running App belongs in a continuous-integration and
continuous-delivery (CI/CD) pipeline. `M`.

**Sceptically**, ranked — **all seven ruled by Amino on 2026-09-05**, and the four that
asked a question carry the ruling.

1. **The plan's runtime test cannot be written as the plan wrote it.** *"the page carries
   the title"* — it does not: `st.set_page_config` runs in a browser session, so what the
   server sends is Streamlit's shell with `<title>Streamlit</title>` and the word
   *Veritas* appears nowhere in it. I substituted two claims: the shell is Streamlit's
   (weak), and — the one that carries the intent —
   `test_the_page_in_the_container_answers_a_question_and_records_it`, which drives
   `page.py` inside the container with Streamlit's own `AppTest` against a real key and
   the real server. It is gated on `VERITAS_LIVE_MODEL` and on a running container, and
   it deletes the row it wrote. **Both accepted.** The question that came with the
   ruling — tests run before an application is served, so what is a test doing against a
   served one, and reaching inside it — is answered in
   [EXT-014](../extension-register.md#ext-014--the-container-tests-run-as-pipeline-stages-before-and-after-a-deploy):
   sorted by the environment a test may touch, this is a **pre-deploy integration stage
   that has no runner yet**, and `exec` is the tool that stage uses, since reaching into
   the container is the only way to prove the image's own interpreter and its wiring.
   What may never use `exec` is the stage *after* a release: a port and no shell.
2. **Two values in the App service's `environment`, where the plan said one.**
   `POSTGRES_PORT: 5432` sits beside `POSTGRES_HOST: postgres`, because `.env`'s
   `POSTGRES_PORT` is the *published* port: leave it out and anybody who moves 5432 to
   free it up gets a container connecting to `postgres:5433`. The plan's *"one value that
   differs"* is true only until somebody edits the file.
3. **2.77 GB, and no multi-stage build.** Both `uv`'s build cache and the interpreter's
   installer stay in the image. A trimmed image is maybe an hour's work and would need
   re-verifying end to end; a grader downloads nothing and builds once. **Left, ruled.**
4. **The container runs as root**, like every service in the file. **Accepted, and
   nothing is filed** — nothing in this Step's scope reaches a second person, and
   [EXT-013](../extension-register.md#ext-013--grafana-reads-the-question-log-with-credentials-of-its-own)
   already carries why, so this sentence is the record.
5. **The base image ships no certificate authorities at all.** Python carries its own
   bundle, so every Python request works; the Rust downloader huggingface-hub reaches for
   does not, and the first build failed at the model fetch with `Reqwest error: builder
   error`, which names neither a certificate nor a network. `ca-certificates` is now
   installed in its own layer with that written above it.
6. **The first page load takes ≈15 s**, measured in the container — the Warehouse, the
   text index, the embedded corpus and two ONNX sessions, once per server process, under
   a spinner. That is the cost of moving it off the first question.
7. **The containerized page has now been loaded in a browser.** Every claim above is
   made through the container's own Python, which was the gap; Amino closed it on
   2026-09-05 by opening the App on `:8501` and asking how many trades the client with
   the most trades has done — it came back correct. That is a person's reading and not a
   committed check: the behaviour is held by `tests/test_app.py` and by the container test
   above. The question `AppTest` asked at 09:33 UTC is still deliberately left in the
   Question Log, so the dashboard at `:3000` has traffic from the container on it.

**Language.** No Term Proposal. `Dockerfile`, `app`, image and `warm` are technical
words; `warm` names a method on `Retriever` and carries no domain meaning, as the
[Step 009 plan](../plan/step-009-containerization-and-readme.md#language) has it for the
rest. So are EXT-014's *pipeline*, *stage*, *deploy* and *smoke test*, none of which
becomes an identifier here. One row joins the Glossary's
[Abbreviations](../glossary.md#abbreviations) table — **CI** / **CD** — because the entry
uses the short form and so does the question that opened it. That table is shorthand and
not Domain Language, in its own words, so it takes no status.

---

## Sub-step 9.2 — Republish the two-provider generation sweep

**Not done, and the reason is a finding.**
[DEBT-039](../debt-ledger.md#debt-039--the-published-two-provider-sweep-failed-its-own-runner-and-is-not-republished)
booked this re-run against a day whose Groq budget was unspent. 2026-09-05 was such a
day and the run **still failed its own runner** — 2 of Groq's 46 questions rather than
8.1's 37, and not on the 200,000-per-day cap the entry names but on a **second meter it
did not know about: 8,000 tokens per minute**, which a sweep asking questions as fast as
they come back sits above for its whole run. The free tier meters twice and only one of
the two resets overnight.

**Changed.** `veritas/llm/model.py` gains `MAX_RETRIES = 8`, an argument on
`ChatCompletions` beside the temperature and the timeout it already takes. The meter
refuses a call and says how long to wait; the client already waited and asked again, and
what dropped the two questions is that it stopped after the two tries the `openai`
library defaults to. `StubEndpoint` can now throttle before it answers, which is what the
two new tests are over — one of them fails at 2 and passes at 8, so the constant is
proven rather than asserted.

**Verified.** All of it run on 2026-09-05 on the tree as it stands. The sweep first, in
full, because a run that failed is not summarised:

```
$ VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation     # 15:01–15:12
  gold          data/gold — 24 Gold Questions, 23 of them scored
  excluded      'Account Value as of 10 August 2026' — the Validation Gate refuses the statement the set itself calls correct, so no model can answer it
  prompts       rules, shape
  models        openai gpt-5.4-mini, groq openai/gpt-oss-120b
  judge         gpt-5.4-mini, on every scored question

  prompt  model                      ending  execution accuracy  judge agreement
  rules   openai gpt-5.4-mini         23/23         11/11 1.000      23/23 1.000  <- today
  rules   groq openai/gpt-oss-120b    22/23         10/11 0.909      22/22 1.000
  shape   openai gpt-5.4-mini         22/23         11/11 1.000      23/23 1.000
  shape   groq openai/gpt-oss-120b    22/23         10/11 0.909      22/22 1.000

  rules · openai gpt-5.4-mini
    nothing — every question ended the way the set says
  rules · groq openai/gpt-oss-120b
    ended by provider   wanted answer              Unrealised P&L as of 10 August 2026
      unreachable: ChatCompletions('openai/gpt-oss-120b' at 'https://api.groq.com/openai/v1') refused the call: Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` in organization `org_…` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 4734, Requested 3348. Please try again in 615ms. …', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}
  shape · openai gpt-5.4-mini
    ended by answer     wanted refusal             ten trades
  shape · groq openai/gpt-oss-120b
    ended by provider   wanted answer              Net Revenue in the second quarter of 2026
      unreachable: … the same 429, 'Used 4882, Requested 3289. Please try again in 1.2825s.'

FAIL — 2 question(s) never reached a model, so these figures are over fewer answers than they claim
```

```
$ uv run pytest
310 passed, 6 skipped in 154.56s        (from 308 passed, 6 skipped at 9.1)

$ sed -i 's/^MAX_RETRIES = 8$/MAX_RETRIES = 2/' … && uv run pytest tests/test_llm.py -k throttl
FAILED tests/test_llm.py::test_a_call_a_provider_throttles_is_asked_again_rather_than_dropped
1 failed, 1 passed, 22 deselected in 5.82s          # the edit reverted immediately after
```

`verify_framework.py` and `check_language.py` both PASS.

**What the failed table is still evidence of, and what it is not.** Groq's two rows are
**lower bounds** — an unreached question has no statement, scores wrong, and both lost
ones expect an answer, so each row's true `execution accuracy` is 10/11 or 11/11 and
nothing here says which. That is exactly why the runner fails the run, and the figure
does not go in the README. The OpenAI half needs no such reading: `rules` ended **23/23
with no failure at all**, the first clean row any sweep has printed.

**The defaults did not move**, as the plan requires. `rules` is still
`DEFAULT_PROMPT_FORM`. It now differs from 8.1 by one question — `ten trades`, answered
there under both prompts and refused here under `rules` — which is one question, and the
plan's own rule calls one question noise and two a finding.

**Debt.** No new entry. DEBT-039 stays **open**, now carrying the second date, the
second meter, and the third attempt booked for the morning of **2026-09-06**: one sweep
spends roughly 155,000 of the 200,000 daily tokens — 46 calls at the ~3,300 the two 429s
quote — so the day a sweep fails is a day it cannot be re-run, and the plan's *"a `FAIL`
books the next morning"* is the route taken.
[DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it)
is untouched and still reproduces, on the `shape` row.

**Sceptically**, ranked — **all four ruled by Amino on 2026-09-05**, and the one that
asked a question carries the ruling.

1. **I widened the Sub-step to fix the client, which the plan did not ask for.** 9.2 was
   scoped as one command run unchanged. The command is unchanged, but the code under it
   is not, and by the *"one commit without the word and"* test this is two Sub-steps —
   the fix, and the sweep it makes publishable. I took it because tomorrow's attempt
   without it is the same lottery that has now failed twice, and it spends no key. **If
   you would rather it were separately numbered, the fix is a clean commit on its own.**
   **Ruled: it is not separately numbered.** The client fix, this failed run and the
   passing grid below are one Sub-step 9.2 and one commit.
2. **`MAX_RETRIES` is global, so the App pays for a meter only the sweep meets.** A
   person waiting on a browser tab now sits through up to 8 server-directed pauses
   instead of 2 — bounded, and at the ~1 s Groq asked for it is about 8 s worse in the
   worst case, against a 30 s timeout **per attempt** that is unchanged. The narrower fix
   is the sweep passing its own number through `registered_models`; the argument is
   already on the constructor, so that is one call site whenever you want it. Not filed
   as debt: nothing is wrong here cheaply, a bound was chosen.
3. **8 is not measured.** It is above the library's 2 and below anything that would sit
   in a retry loop for a minute; what is measured is that 2 was too few, twice. The right
   number is whatever clears a per-minute bucket, and the next sweep is the only thing
   that can say whether 8 does.
4. **The 2026-09-03 run is now doubly superseded and still the only table in a review.**
   Nothing in the README quotes it yet, so nothing is wrong today — but 9.3 must not be
   written until 9.2 produces a passing table, or its Evaluation section quotes a `FAIL`.

**Language.** No Term Proposal. `MAX_RETRIES`, `max_retries` and `throttled` are
technical and carry no domain meaning; `check_language.py` scans them and passes.

---

## Sub-step 9.2 — Publish the generation grid over OpenAI, and demote Groq

**The second attempt at 9.2**, after the section above, on Amino's ruling of 2026-09-05
that the section above provoked. That ruling and the rejected alternatives are in the
[plan](../plan/step-009-containerization-and-readme.md#rulings-in-flight).

**The finding that caused it.** The Zoomcamp row this project has been building against
since Step 006 does not exist. The published rubric, read 2026-09-05 from
<https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md>, says:

> * LLM evaluation
>     * 1 point: Only one approach (**e.g., one prompt**) is evaluated
>     * 2 points: Multiple approaches are evaluated, and the best one is used

No second model, no second provider — its own example of an approach is a prompt.
*"Execution Accuracy across ≥2 prompts and ≥2 models"* was the criteria map's own
wording, and [ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md)
then cited it back as the rubric's requirement, which is how Groq came to look mandatory.
**Two sweeps failed on a free tier bought to clear a bar nobody set.**

**Changed.** `registered_models` returns one client per **(provider, model)** pair a
sweep names, keyed `"openai gpt-5.4-mini"`, and `--model` is repeatable — so one
provider's models can be swept against each other, which the registry keyed by provider
could not say. `PROVIDERS` itself did not move. Corrected in place: the criteria map row,
three passages of ADR-0005 (including one the code change falsified), EXT-011's
motivation, and the `generation.py` and `model.py` docstrings that quoted the wrong bar.

**Verified.** 2026-09-05, on the tree as it stands. The published grid, in full:

```
$ VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation \
    --provider openai --model gpt-5.4-mini --model gpt-5.4-nano --model gpt-4o-mini
  gold          data/gold — 24 Gold Questions, 23 of them scored
  excluded      'Account Value as of 10 August 2026' — the Validation Gate refuses the statement the set itself calls correct, so no model can answer it
  prompts       rules, shape
  models        openai gpt-5.4-mini, openai gpt-5.4-nano, openai gpt-4o-mini
  judge         gpt-5.4-mini, on every scored question

  prompt  model                 ending  execution accuracy  judge agreement
  rules   openai gpt-5.4-mini    22/23         11/11 1.000      23/23 1.000  <- today
  rules   openai gpt-5.4-nano    18/23          8/11 0.727      22/23 0.957
  rules   openai gpt-4o-mini     14/23          2/11 0.182      22/23 0.957
  shape   openai gpt-5.4-mini    22/23         11/11 1.000      23/23 1.000
  shape   openai gpt-5.4-nano    18/23          8/11 0.727      21/23 0.913
  shape   openai gpt-4o-mini     14/23          2/11 0.182      22/23 0.957

  rules · openai gpt-5.4-mini
    ended by answer     wanted refusal             ten trades
  [trimmed — the five other rows' failure lists, 16:17:52 to 16:23:41]

PASS — Execution Accuracy and LLM-as-judge agreement for every prompt against every registered model
```

`uv run pytest` — **311 passed, 6 skipped**, from 310 + 6 earlier today.
`verify_framework.py` and `check_language.py` PASS.

**What the grid says.** The models axis separates hard and the prompts axis barely does.
`gpt-5.4-mini` beats `gpt-5.4-nano` by three answered questions and `gpt-4o-mini` by nine,
under both prompts, and both weaker models fail the same way — refusing a date they have
never heard of, the habit
[DEBT-037](../debt-ledger.md#debt-037--nothing-tells-the-generator-that-a-date-it-has-never-heard-of-is-not-a-reason-to-refuse)
closed `accepted`, in `gpt-4o-mini`'s case citing *"the training is up to October 2023"*
outright. On the winning model the two prompts are **identical on all three measures**;
they separate only on `gpt-5.4-nano`'s judge agreement, by one question. So *"the best one
is used"* holds — the shipped pair is the joint-best row of six and nothing beats it — but
the prompt half of that claim rests on a one-question margin on a model Veritas does not
ship. Stated rather than smoothed over.

**Debt.**
[DEBT-039](../debt-ledger.md#debt-039--the-published-two-provider-sweep-failed-its-own-runner-and-is-not-republished)
**closed `accepted`**, and the entry says plainly that its cost was *dissolved rather than
paid*: no third sweep was run, and none is owed, because the criterion whose table was
missing does not exist. What is genuinely lost is written there too — no published figure
now compares Veritas across two vendors. No new entry.
[DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it)
gains its cleanest evidence yet: `ten trades` is the **only** failure of the shipped model
under either prompt.

**Sceptically**, ranked — **all five ruled by Amino on 2026-09-05**, and the three that
asked a question carry the ruling.

1. **`ten trades` fails here and passed six hours ago.** The 15:01 run had `rules ·
   gpt-5.4-mini` at 23/23 with no failure at all; this one has 22/23, `ten trades`. Same
   model, same pinned temperature, same committed questions. That is the run-to-run
   variance 8.1 measured by accident, now observed a third time, and it means **every
   single-run figure in this project is one sample** — including the 11/11 above. Nothing
   here is wrong; the honest reading is that these rates have a margin nobody has
   quantified, and quantifying it costs a repeat of every sweep. **Ruled: accepted, and
   no repeat is bought.** Nothing is filed — nothing is wrong cheaply — so 9.3 carries it
   instead: the README's Evaluation section says each figure is one run.
2. **I widened the Sub-step again**, and further than last time: this one changed a seam
   function, a rubric-derived row in Target State, three passages of an accepted ADR, an
   extension entry and two docstrings, and closed a Ledger entry. It is one coherent
   change — *the published table is the OpenAI grid* — but it is not one commit's worth by
   the *"without the word and"* test. Split it however you prefer; the code change and the
   document corrections are cleanly separable. **Ruled: not split** — one Sub-step, one
   commit, with the client fix above.
3. **The grid excludes two models on purpose.** `gpt-5.6-luna` and `gpt-5-mini` reject
   `temperature: 0`, which 8.1 measured; including them would have produced two all-error
   rows and a `FAIL`, not a comparison. So the models axis is *"every candidate that can
   run at a pinned temperature"*, which is a narrower claim than *"every candidate"* and
   is the one the README should make.
4. **Groq is still in the registry and still in `.env.example`.** Demoted means nothing
   published depends on it, not removed — the unnarrowed sweep still runs both providers,
   and ADR-0005's *"a second provider is a registry row"* stays demonstrated rather than
   asserted. If you would rather it were gone entirely, that is a smaller change than this
   one was. **Ruled: it stays registered.**
5. **No cost figure for this run.** The sweep does not total its tokens and the Question
   Log does not record sweep calls, so I have nothing reproducible to quote; 5m49s of wall
   time is all the run itself measured.

**Language.** No Term Proposal. *(model, prompt) combination* is the rubric's *approach*
spelled in the two axes the sweep already varies — `PromptForm` and the model string — and
coins nothing; `registered_models`, `--model` and the `"provider model"` key are technical.
`check_language.py` passes.

---

## Sub-step 9.3 — `README.md`, with every credential and every limitation

**Changed.** `README.md` — the grader's document, in the rubric's order, opening with an
index table from each criterion to the section that earns it. `tests/test_readme.py` is
what makes it checkable at all: neither committed checker reads it, so the credential list
is asserted in both directions, the access-control sentence is read out of the Ledger, and
every relative link in `README.md` and `docs/*.md` is resolved with its anchor —
under `verify_framework.py`'s own `heading_anchors`, **imported** rather than reimplemented,
so the two documents cannot disagree about what an anchor is. `veritas/llm/model.py`
gained a sixth price row and a new read-date.

**Also in this commit, on Amino's instruction of 2026-09-05: the name of the company whose
job specification the Product Brief was distilled from is gone from the repository.** Four
occurrences — the brief's *Provenance* line, one sentence in the Step 000 review and one in
the Step 001 review, and a row in `check_language.py`'s `KNOWN_NON_ABBREVIATIONS` that
existed only to let the other three pass. The domain survives every cut: *a multi-asset
brokerage*, *real brokerage usage*.

**Verified.** Every command run on 2026-09-05 on the tree as it stands.

```
$ uv run pytest
316 passed, 6 skipped in 166.33s (0:02:46)   (from 311 passed, 6 skipped at 9.2)

$ uv run pytest tests/test_readme.py -v
tests/test_readme.py::test_every_declared_variable_is_named_in_the_readme PASSED
tests/test_readme.py::test_the_readme_names_no_variable_it_does_not_declare PASSED
tests/test_readme.py::test_the_readme_exemptions_are_still_true PASSED
tests/test_readme.py::test_the_readme_qualifies_access_control_in_the_ledgers_own_words PASSED
tests/test_readme.py::test_every_relative_link_in_the_public_documents_resolves PASSED
5 passed in 2.66s

$ uv run python .claude/scripts/verify_framework.py | tail -4
  links      1725 links, 1406 anchors 88 documents and python files
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly

$ uv run python .claude/scripts/check_language.py | tail -3
  abbreviations: 28 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

**Every one of those is the re-run**, after the name removal above and after this review
and Current State were written to their final wording — so the figures are the tree Amino
commits and not an earlier one. The counts moved only where new links were added.

The full run **failed once first**, on the second point below —
`tests/test_observability.py::test_an_unpriced_model_leaves_a_gap_in_the_cost_column_rather_than_a_zero`,
whose `UNPRICED` constant was groq's default model. Fixed in the same Sub-step and
re-run above.

**One deliberate deviation from the plan.** The plan gives 9.3 *"one line at
`docs/decisions.md`"*. That line is **not** written, because the file does not exist until
9.4 and `test_every_relative_link_in_the_public_documents_resolves` would fail on it —
committing a link a Sub-step's own test proves dead is not a Sub-step that verified. 9.4
adds the file and the line together, which is the ordering its own verification step
(*"`uv run pytest tests/test_readme.py` (the links)"*) already assumes.

**Debt.** Five entries touched, two of them **paid**; each carries its own note, and the
two measurements behind DEBT-040 are the pages read on 2026-09-05:
<https://developers.openai.com/api/docs/pricing>, where **none of the five rows moved**,
and <https://console.groq.com/docs/model/openai/gpt-oss-120b>, which prices groq's default
model at $0.15 and $0.60 per million tokens.

| Entry | What happened |
|---|---|
| [DEBT-038](../debt-ledger.md#debt-038--a-capable-model-answers-an-ad-hoc-row-request-instead-of-refusing-it) | **paid** — second branch: the README states the limitation, and nothing enforces it |
| [DEBT-040](../debt-ledger.md#debt-040--the-price-table-is-a-vendors-page-copied-once-and-nothing-notices-when-it-moves) | **paid** — both pages re-read, `PRICES` gains a sixth row, nothing re-reads them next time |
| [DEBT-002](../debt-ledger.md#debt-002--market-prices-depend-on-an-unofficial-endpoint) | trigger 2 fired; stays `paid` on the allowed wording. Trigger 3 still live |
| [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers) | already paid at 6.5; the README makes the claim with the same sentence, held by a test |
| [DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows) | **stated, not paid**, on the plan's first ruling. Still open |

No new entry, and none opened.

**Sceptically**, ranked — **the six below were ruled by Amino on 2026-09-05**, and the two
that asked a question carry the ruling. The seventh was raised after that ruling, by the
change that ruling came with, so it is out of rank and unruled.

1. **Adding a groq price row was not in the plan, and it changes what the dashboard
   shows.** DEBT-040's Trigger says *"add groq if it is priced anywhere readable"*, and it
   is — but the entry's own reason for leaving it out was two-part, and only half of it
   dissolved: the free tier still bills nothing, so a groq call now carries a figure
   nobody was charged. I took it because the alternative reading makes the column mean two
   different things by provider; the column is now uniformly *"what this would have cost at
   list prices"*, which is what the README says it is. **If you would rather groq stayed
   unpriced, reverting is one dictionary row and one test.** **Ruled: the groq row stays**,
   and with it the column's single meaning.
2. **It forced two test rewrites, one of which I did not see coming.** Both
   `tests/test_llm.py` and `tests/test_observability.py` used groq's default model as
   their example of an unpriced one; the second was found by the full run failing, not by
   reading the diff. Both now name a model string no page carries a price for. The claim
   is unchanged and better stated — pinning *"unpriced"* to a particular registry row was
   always coupling a general rule to an accident — but two files depending on that
   accident is the measure of how far a price row reaches.
3. **Only the generation table carries the one-run caveat.** The retrieval table does not,
   because nothing has ever observed it varying — which is an absence of evidence rather
   than evidence, and it is one `uv run python -m veritas.evaluation retrieval` away from
   being either if you want it settled. **Ruled: not settled** — no repeat sweep is
   bought, and the retrieval table stands uncaveated with that as its reason.
4. **The rubric index table at the top is navigation I invented**, not in the plan. It
   duplicates no argument — links only, no "how it earns" column — but it is a second
   place that must stay true when a section is renamed, which is why the link test resolves
   in-document anchors too.
5. **The two dashboard images are linked out of `.claude/docs/reviews/images/`** rather
   than copied. One copy is the rule, and the cost is that the README's illustrations live
   under the working record: remove `.claude/` from the public tree and two images and
   several links go with it.
6. **Nobody has read the README against a clean machine yet.** Every command in it is one
   this repository has run; the document as a *set of instructions* is unrehearsed, which
   is what 9.5 is for.
7. **The company name is out of the working tree and still in the history.** `git log -S`
   finds it in the commits that first carried those three documents, and only a rewrite of
   every commit since would change that — which invalidates every hash a review cites. So
   the claim this Sub-step can make is *the repository as checked out carries no such
   name*, not *the repository never carried one*. If the second is what you want, say so
   before submission: it is cheapest while nobody has cloned this. Two of the three prose
   edits are also to **committed Step Reviews**, which are otherwise append-only — what a
   review said on its date is usually the point of it. Neither sentence carried evidence or
   a ruling; both were asides, so nothing dated changed meaning. The fourth edit deletes an
   allowlist row from a frozen check script, which is a row that had gone dead rather than
   one still excusing something — nothing was ported out and nothing was added.

**Language.** No Term Proposal. `README_NOT_IN_ENV`, `PUBLIC_DOCS`, `DECLARED`, `NAMED_IN_README`
and `GROQ_PRICING` are technical and carry no domain meaning. The README expands **LLM**,
**MRR** and **ONNX** on first use as a fresh document must, and uses the Glossary's
spelling for every domain noun it names.

---

## Sub-step 9.4 — `docs/decisions.md`: the decisions that move a number

**Changed.** `docs/decisions.md` is the user-facing decision register
[DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews)
has owed since Sub-step 2.5: thirteen rows, each naming the decision, the number it
moves, what a reader should conclude when they meet that number, and the dated review
that argued it. `README.md` sends a reader to it from the end of Ingestion;
`tests/test_readme.py` gains the test that keeps that pointer alive; CLAUDE.md's
Documents table names the file and its cadence. `read_market_data`'s fourteen lines
arguing the Snapshot calendar — the comment the entry's **Location** names — are now four
and a link to the register.

**Verified.** 2026-09-05, on the tree as it stands.

```
$ uv run pytest tests/test_readme.py -v | tail -8
tests/test_readme.py::test_every_declared_variable_is_named_in_the_readme PASSED [ 16%]
tests/test_readme.py::test_the_readme_names_no_variable_it_does_not_declare PASSED [ 33%]
tests/test_readme.py::test_the_readme_exemptions_are_still_true PASSED   [ 50%]
tests/test_readme.py::test_the_readme_qualifies_access_control_in_the_ledgers_own_words PASSED [ 66%]
tests/test_readme.py::test_the_readme_points_at_every_document_beside_it PASSED [ 83%]
tests/test_readme.py::test_every_relative_link_in_the_public_documents_resolves PASSED [100%]

============================== 6 passed in 1.97s ===============================

$ uv run pytest -q | tail -1
317 passed, 6 skipped in 124.71s (0:02:04)   (from 316 passed, 6 skipped at 9.3)

$ uv run python .claude/scripts/verify_framework.py | tail -3
  links      1736 links, 1414 anchors 88 documents and python files
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly

$ uv run python .claude/scripts/check_language.py | tail -1
PASS — documents agree with the Glossary and the writing conventions
```

The new test was made to fail before it was trusted: with the README's one line at
`docs/decisions.md` removed it fails with `assert not ['docs/decisions.md']`, and the
README was restored byte-for-byte.

**Debt.**
[DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews)
**paid** on its own Trigger, with a **How DEBT-013 was paid** section that says what
paying it does not buy. Nothing opened.

**Sceptically** — **all six ruled by Amino on 2026-09-06**, and the two that asked a
question carry the ruling.

1. **Two tables, where the plan says one** — *the numbers in an answer* against *the
   numbers Veritas publishes about itself*, because a reader arrives with one of those
   two questions and not the other. One column set, one register; merging is deleting
   two headings.
2. **Nine rows beyond the four DEBT-013 listed, and the sweep is mine.** The entry said
   the list would grow; the nine come from reading the Step 002–008 reviews, by the party
   that wrote them, so what it misses is a decision nobody recorded as a decision.
3. **I rewrote a code comment the plan did not mention.** The entry's Location names
   `read_market_data` and its remedy says such a comment points at the register instead,
   so leaving it pays the visible half only. Comment-only; reverting is one edit.
   **Ruled: the rewritten comment stays.** The other source links into `plan/` and
   `reviews/` are
   [DEBT-024](../debt-ledger.md#debt-024--source-and-step-documents-carry-prose-delivery-mode-would-not-admit)'s,
   trigger 2026-09-09, and were left alone.
4. **I renamed two headings in committed Ledger entries.** `#### How it was paid` was
   about to appear three times, and those anchors are positional: an entry inserted
   *above* the other two silently renumbers `#how-it-was-paid-1`. `verify_framework.py`
   catches it, which is how I found it. All three now carry their entry's number; no
   wording changed.
5. **Three figures in a public document are single measurements** — 1.94% between the two
   date readings, MRR 0.750 → 0.833, sixty-six dates without a Snapshot. Each carries its
   date and its review, the generation rows say in the register that a rate is one sample,
   and the warehouse figures reproduce from committed snapshots.
6. **What I judged *not* to be a reader's number**, so the boundary is visible rather than
   implied: `TOP_K` and the closure that adds what a retrieved entry names, sweeps kept
   out of the Question Log, and `ended_by`. **Ruled: none of the three joins the table**,
   so the boundary stands where this Sub-step drew it.

**Language.** No Term Proposal. *Decision register* and `decisions.md` were ruled by the
[plan's Language section](../plan/step-009-containerization-and-readme.md#language); the
document uses the Glossary's spelling for every domain noun and expands FX and MRR on
first use as a fresh public document must.

---

## Sub-step 9.5 — Fresh-clone rehearsal, and the Step closes

**Changed.** Amino ran the rehearsal on 2026-09-06 and I did not: the tree was cleaned to
what a clone holds — every Docker image, volume and cache gone, `uv cache clean` — and
`README.md` was followed verbatim on both paths. Both work. It found one defect, in the
one place this project claims to be different from an LLM writing SQL, and Amino ruled the
same day to fix it rather than state it. So this Sub-step is the rehearsal, the fix, and
the documents the fix made true — and then, after the first eight points below were
ruled, a browser confirming the fix, a second one-line fix the screenshot exposed, and
one entry filed.

**The defect.** `Account Value` was **answered rather than refused**, with 45% of itself.
It is the one composed metric: its `expression` field is the Positions operand and the
Cash Balance operand is reached through `derives_from`, which `ValidationGate.traces`
never read. So the two shapes failed in opposite directions — the correct statement adds
two scalar subqueries and was refused as a Shadow Metric, and the partial statement
matched a registered expression exactly and was **allowed**. Asked *"what is our account
value as of 10 August 2026"*, Veritas returned **15,613,821.53** against **34,972,516.94**,
labelled `Account Value — money, in EUR`, with `Account Value — metric v1` in the Lineage
and *"allowed — 8 rules ran"* from the Gate. Neither the model nor the Gate misbehaved:
the corpus published half a definition and both believed it.

**The fix.** `Reading` carries `composed_metrics` — `{name: what its value adds}`, read
off the corpus beside the certified expressions it already held — and `traces` refuses a
statement whose traced metrics include a composed one. New Rejection Reason,
`incomplete certified metric`, its own member rather than `SHADOW_METRIC` because a
Shadow Metric is arithmetic the generator invented and this expression was published by
the corpus. What a person reads is the Gate's own sentence:

```
Account Value adds Cash Balance to its own expression, and this statement computes that
expression alone — so it would answer with part of Account Value rather than Account Value
```

**Verified.** The rehearsal first, run by Amino on 2026-09-06 from the cleaned tree:

```
$ time docker compose up -d --build          # no images, no uv cache, nothing warm
 PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9554 Market Prices across all 19 …
real    3m29.003s

$ docker images veritas-app          veritas-app:latest   2.76GB disk   716MB content
$ uv sync                            9.353s, 99 packages
$ uv run python -m veritas.ingestion 22.953s, PASS
```

Then the fix, on the tree Amino commits:

```
$ uv run pytest tests/test_gold.py -k "composed or allowed_by_the_gate" -q -s
  Account Value as of 10 August 2026 — refused both ways
    composed  34972516.937747                shadow metric
    partial   15613821.52770105587254000000  incomplete certified metric
2 passed, 21 deselected in 1.87s

$ uv run pytest                              318 passed, 6 skipped in 79.01s
$ uv run python .claude/scripts/check_validation_gate      PASS
$ uv run python .claude/scripts/check_validation_feasibility.py   PASS
$ uv run python .claude/scripts/check_semantic_layer.py    PASS
$ uv run python .claude/scripts/check_warehouse.py         PASS
$ uv run python .claude/scripts/verify_framework.py        PASS
$ uv run python .claude/scripts/check_language.py          PASS

$ docker compose up -d --build && docker compose exec app python -c "…judge the partial statement…"
veritas-app  Up 9 seconds (healthy)
allowed : False
reasons : ('incomplete certified metric',)

$ uv run pytest tests/test_container.py tests/test_observability.py
32 passed, 1 skipped in 2.00s
```

The suite was also run with the services stopped and started around it, because the
README quotes both: **302 passed, 22 skipped** with nothing running, **318 passed, 6
skipped** with `docker compose up -d`. The six that never come back are the six
`VERITAS_LIVE_MODEL` guards, named by `pytest -rs`.

**The frozen Gate probes caught the change on the first run, which is what they are
for.** Three of the five modules asserted the behaviour the fix removes: `traces.py`
expected every metric's own-fields statement to be allowed, and `route.py` and
`access.py` used those statements as vehicles for their own rules. Six failures, all
`Account Value`. All three now read `derives_from` the way the rule does — the traces
probe asks the composed metric for the refusal, the other two skip it, because a
statement refused three rules earlier measures the earlier rule. No probe was deleted,
nothing was ported out, and no metric name was written into any of them. Probe count
**79 → 77**; the taxonomy is **13 → 14** members.

**The four questions and the dashboard**, from the rehearsal. Three behaved as the README
says: `gross revenue in Q2 2026` answered with its SQL, Lineage and verdict; `revenue in
Q2 2026` asked back *"could mean Gross Revenue or Net Revenue"*; `what columns are in
fct_trade` refused. The fourth was the defect. Feedback submitted on the clarification
came back *"recorded against this answer"*. Grafana opened on `:3000` with no sign-in and
five of seven panels carried the traffic; `Validation Gate rejections by Rejection Reason`
read `No data`, correctly — none of the four was refused by the Gate.

**Then the fourth question was asked again at `:8501`, after the fix** — Amino, later on
2026-09-06, in the browser, against a real model call. What a person sees is the Gate's
sentence in red above the SQL and `rejected — incomplete certified metric` under
**Validation Gate**: [screenshot](images/step-009-app-account-value-refused.png). The App
recorded both runs of the one question, on one day, either side of the fix — which is the
Question Log being a record rather than a second story:

```
$ docker compose exec -T postgres psql -U veritas -d veritas -x -c "SELECT question_id, asked_at, question, ended_by, allowed, reasons, seconds, cost FROM question WHERE question ILIKE '%account value%' ORDER BY question_id;"
-[ RECORD 1 ]------------------------------------------------
question_id | 4
asked_at    | 2026-09-06 14:21:20.39783+00
question    | what is our account value as of 10 August 2026
ended_by    | answer
allowed     | t
reasons     | {}
seconds     | 2.8099646150003537
cost        | 0.00261225
-[ RECORD 2 ]------------------------------------------------
question_id | 104
asked_at    | 2026-09-06 16:26:29.006643+00
question    | what is our account value as of  10 august 2026
ended_by    | gate
allowed     | f
reasons     | {"incomplete certified metric"}
seconds     | 4.1226978070008045
cost        | 0.0025815
```

The identifiers are 4 and 104 because the suite records into this same database between
them and deletes its rows by identifier, which the sequence does not give back. And the
panel that read `No data` no longer does — its own `rawSql` from
`grafana/dashboards/question-log.json`, run against that database:

```
$ docker compose exec -T postgres psql -U veritas -d veritas -c "SELECT reason AS \"Rejection Reason\", count(*) AS \"rejections\" FROM question, unnest(reasons) AS reason WHERE allowed IS FALSE GROUP BY 1 ORDER BY 2 DESC"
      Rejection Reason       | rejections
-----------------------------+------------
 incomplete certified metric |          1
```

**The second fix, and the image rebuilt on it.** The ninth point below, ruled the same
day it was raised:

```
$ uv run pytest tests/test_app.py
32 passed, 2 skipped in 9.83s

$ uv run pytest
318 passed, 6 skipped in 124.56s

$ docker compose up -d --build
 Container veritas-app Recreated · Started          app  Up 13 seconds (healthy)

$ docker compose exec -T app python -c "from veritas.app import NOTHING_USED; print(NOTHING_USED)"
nothing was used: no statement was allowed to run

$ uv run pytest tests/test_container.py tests/test_observability.py
32 passed, 1 skipped in 3.15s

$ uv run python .claude/scripts/verify_framework.py
PASS — 1769 links, 1442 anchors, 88 documents and python files

$ uv run python .claude/scripts/check_language.py
PASS — documents agree with the Glossary and the writing conventions
```

The suite total does not move, because the claim went into a test that already existed:
the clarification path already rendered a page with an empty Lineage, and what it asserts
now is what that page says about one. The constant was read back through the **container's
own interpreter** for the same reason the Gate rule was — it is the shipped image, not the
working tree, that a grader runs.

**Debt.**
[DEBT-043](../debt-ledger.md#debt-043--the-gate-certifies-half-of-a-composed-metric-as-the-whole-of-it)
opened and **paid in the same Sub-step**, `M`, on Amino's ruling.
[DEBT-035](../debt-ledger.md#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows)
stays **open**, and its **Cost while unpaid was rewritten**: it had claimed since 7.1
that the metric was *unanswerable*, which was the thing that turned out not to be true,
and four documents quoted it. `Account Value` is unanswerable now — refused at both
shapes rather than answered at one. Nothing else opened.

**The running counts were wrong in three places and are corrected here**, off the Index
table itself. The Ledger read *10 open · 27 paid* over a table holding 9 and 28 — it had
counted DEBT-043 as open after this Sub-step paid it. Current State carried two more
copies: *"ten open, twenty-six paid"*, stale by a Sub-step, and *"Open debt: 13"*, stale
by four — the second in the paragraph whose own first sentence is *"this file does not
keep a second copy"*. All three now read **10 open · 28 paid · 4 accepted · 2 moved**,
which is 44 entries with the one below included. The Register's fourteen open extensions
were counted the same way and are right.

[DEBT-044](../debt-ledger.md#debt-044--the-ledgers-running-counts-are-arithmetic-nothing-checks)
**opened**, `S`, on Amino's ruling of 2026-09-06: the recount was by hand and nothing
checks the next one. Trigger 2026-09-09, alongside DEBT-023, DEBT-024 and DEBT-025 —
what defers it is the deadline and nothing else.

**Sceptically**, ranked.

1. **I edited three frozen check scripts, which Delivery Mode forbids adding to.** The
   rule reads *"nothing new goes into them and nothing is ported out of them"*, and I
   read that as being about not investing in the old proving system rather than about
   leaving it red — a probe whose premise a correctness fix has falsified either gets
   corrected or fails forever, and a permanently failing check proves nothing. The edits
   are the minimum: a branch on `derives_from` in each of the three places that assumed
   every metric behaves alike. **If you would rather they had been left failing with a
   note, reverting is three hunks.**
2. **A new Rejection Reason is a taxonomy change three days before submission.** It is
   additive to a `StrEnum`, nothing enumerates the members exhaustively, and the Grafana
   panel groups by whatever is in the array — so the blast radius is the two counts in
   Current State I corrected. The alternative was reusing `SHADOW_METRIC`, which costs
   nothing and says the wrong thing: DEBT-035's original complaint was an explanation
   *"true about the parse tree and misleading about the cause"*, and reusing it would
   have reproduced exactly that while claiming to fix it.
3. **The rule refuses on the metric, not on the arithmetic.** Anything projecting a
   composed metric's own expression is now refused, including a statement that went on to
   add the cash half in some form the corpus does not describe. That is fail-closed and I
   think correct — there is no certified composed shape to recognise until DEBT-035 is
   paid — but it is broader than *"this statement is missing an operand"*, and it is why
   paying DEBT-035 has to touch this rule rather than sit beside it.
4. **`docs/decisions.md` lost the row it gained an hour earlier.** I added one for the
   wrong number while the defect stood; the number no longer exists, and a decision
   register is not a changelog, so the row is deleted rather than annotated. The
   register's contract is *what to conclude when you meet this number*, and there is no
   longer a number to meet.
5. **The rehearsal was `git clean -xdf`, not `git clone` into `scratch/` as the plan
   wrote it.** With a clean tree the two leave the same files, and `clean -xdf` is the
   stronger of the two for the failure that matters — a file the build needs that was
   never committed — because it removes ignored files a clone would simply not have. What
   only a push proves is that the remote holds what the working tree does.
6. **Closed the same day it was raised: a person has now asked it at `:8501`.** It was
   written open — the stack had been rebuilt on the fix and the verdict read back through
   the **container's own interpreter**, which is what proves the shipped image carries the
   rule rather than the working tree (`allowed: False · ('incomplete certified metric')`),
   but no browser and no real model call had touched it. Both are above, with the row the
   App wrote. What that reached and the container check could not is the pair of things no
   test asserts: that the model still writes the partial statement when a person asks in
   their own words, and that the page puts the Gate's sentence where the answer would have
   been. Nothing was changed to make it pass.
7. **The doubled cue is real and was predicted in writing before it was seen.** The App's
   *"read as"* line on the first question read *"what was our gross **Gross Revenue** in
   Q2 2026"*.
   [DEBT-030](../debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it)
   named that exact string as the known cost of the splicing arm, before Step 007
   measured that arm and chose it. No entry: the sweep that picked splicing was run with
   this in it. It is still the first thing a grader reads on the first question they ask.
8. **The README's Monitoring section is unchanged and the governance panel starts
   empty.** It already says the dashboard images are *"the demo's data, not evidence"*, so
   nothing there is wrong; a grader who asks four sensible questions still sees the
   rejections panel empty. One line naming a question that fills it would be worth the
   sentence. Not taken — the README is not wrong, and you asked for it not to grow.
9. **Found by the screenshot, after the rulings: under **Lineage** the page says
   *"nothing was retrieved for this question"*, and something was retrieved.** The
   refusal was generated from the `Account Value` Metric Definition — a question that
   retrieved no metric ends three steps earlier, at `EndedBy.RETRIEVAL`. What is empty is
   the Lineage, correctly: 8.2 made it mean *what the allowed statement used*, paying
   [DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used),
   and a rejected statement used nothing. The caption is older than that meaning — it
   arrived in 6.5 (`814b07b`), when Lineage was everything the model was shown, and
   nothing was watching it when the meaning moved underneath. Ranked last because it
   misleads about provenance and never about a number. **Fixed on your ruling the same
   day, and the class with it**: the sentence left `page.py` for `render.py` as
   `NOTHING_USED` — beside `ENFORCEMENT_NOTE` and the `outcome_line(None)` sentence it is
   the twin of, which is where this file already keeps a string a person reads — and
   `tests/test_app.py` holds it on the clarification path, where the Lineage really is
   empty, together with the absence of the word *retrieved* anywhere on that page. What
   allowed the drift was a sentence with no test and no home next to the thing it
   describes, and that is what changed; the wording alone would have been the symptom.
10. **I corrected three counts inside a diff you had already approved, and did not add
    the check that would have caught them.** They are arithmetic over a table in the same
    file, so the correction is mechanical and reversible by reading the Index — but it is
    still an edit after the ruling, and it is the second thing this Step found by looking
    rather than by running something. A dozen lines in `tests/` would count the Index's
    status column and assert the header, the way `tests/test_readme.py` already parses
    `.env.example`. **Filed rather than added, on your ruling** —
    [DEBT-044](../debt-ledger.md#debt-044--the-ledgers-running-counts-are-arithmetic-nothing-checks),
    due 2026-09-09 with
    [DEBT-023](../debt-ledger.md#debt-023--two-proving-systems-run-side-by-side), because
    a new test on submission day is a new thing to review and nothing moves a status
    between here and the commit that closes the project.

**Language.** No Term Proposal. `incomplete certified metric` is built from the
registered term **Certified Metric** and a plain adjective, the way `missing certified
filter` and `no metric expression` already are, and the Glossary's
[Rejection Reason](../glossary.md#a-the-system) row puts the members *"in
`veritas/validation/`, where the Gate enumerates them, and deliberately not in this
cell"* — so it takes no Glossary row. `composed_metrics`, `derives_from` and `traces`
are existing identifiers or built from them; *composed metric* is the phrase
[`semantic/metrics/account_value.yaml`](../../../semantic/metrics/account_value.yaml)
and DEBT-035 already use. `NOTHING_USED` carries no domain noun and is named for
`NOTHING` beside it, which it sits under. `check_language.py` passes.
