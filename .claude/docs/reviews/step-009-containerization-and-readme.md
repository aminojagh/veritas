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
