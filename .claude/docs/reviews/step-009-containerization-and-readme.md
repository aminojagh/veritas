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
