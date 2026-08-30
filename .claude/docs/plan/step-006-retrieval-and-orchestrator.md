# Step 006 — Ask a question, get a Grounded Answer

**Status:** `active`

**Goal.** Make Veritas answer a question end-to-end in a browser — Retrieval,
Orchestrator and App — so the four built components become a working system.

**Moves Current State by:** four of nine Target State components built → seven.
The [Target State's flow](../design/target-state.md#flow) runs whole for the first
time: steps 1–4 and 6–7 join the VALIDATE that Step 005 built.

---

## Why Delivery Mode exists

The capstone is due **2026-09-09**, eleven days from this plan. Five components
are unbuilt and the remaining product is roughly 2,000 lines — about eight days at
the source rate Steps 002–005 sustained. The overhead around it is what does not
fit:

| Step | days | source lines | check + prose lines | overhead |
|---|---|---|---|---|
| 002 | 10 | 3,500 | 8,640 | 2.5× |
| 003 | 5 | 0 | 5,877 | — |
| 004 | 4 | 602 | 8,369 | 13.9× |
| 005 | 4 | 2,994 | 11,951 | 4.0× |

*Measured 2026-08-29 by `git log --numstat` over each Step's commit range.*

At that ratio the remaining scope lands around 2026-10-20 — six weeks late.
Costing the alternatives against eleven days: porting the check scripts to tests
(−4 days), severing the code-to-history links (−0.5), untangling the spike (−1.5),
and stripping existing docstrings (−2) all lose, because each spends days now to
save days after the deadline. Only the forward-only changes pay, and they are what
[Delivery Mode](../../../CLAUDE.md) is. The three deferred refactors are
[DEBT-023](../debt-ledger.md#debt-023--two-proving-systems-run-side-by-side),
[DEBT-024](../debt-ledger.md#debt-024--source-and-step-documents-carry-prose-delivery-mode-would-not-admit)
and [DEBT-025](../debt-ledger.md#debt-025--the-nine-certified-metrics-are-implemented-twice).

**Remaining schedule:** this Step ~4.5 days · Step 007 Evaluation and
Observability ~3.5 · Step 008 Containerization and `README.md` ~2. Eleven
available, ten needed.

---

## Sub-steps

### 6.1 — Index the Semantic Layer for retrieval

Build `veritas/retrieval/` and turn each Semantic Entry into a searchable
document. The corpus is the Semantic Layer and nothing else, per
[ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md); the schema is
deliberately absent.

*Verify:* `uv run pytest tests/test_retrieval.py -k corpus` — all 32 entries
indexed, every `aliases` entry searchable, no table or column text present.

### 6.2 — Retrieve Semantic Entries for a question

One seam: `retrieve(question) -> list[SemanticEntry]`. Behind it, text search and
vector search combined, then re-ranked. Which of the three a call uses is a
parameter, because Step 007 must measure them against each other.

*Verify:* `uv run pytest tests/test_retrieval.py` — a fixed question set retrieves
the entry a human names, under each strategy.

### 6.3 — Resolve Ambiguous Terms before retrieval

The first LLM call. "Revenue" resolves to Gross or Net by asking, never by
guessing. Provider and model are chosen in this Sub-step, not here — Target State
allows OpenAI, Anthropic or Groq with an Ollama fallback.

*Verify:* `uv run pytest tests/test_rewrite.py` — each of the five Ambiguous Terms
either resolves against the question's own words or returns a question back.

### 6.4 — Answer a question end-to-end

Ground from retrieved entries only, generate SQL, validate, execute, return a
Grounded Answer carrying its SQL, Lineage and Validation Gate outcome. Refusal is
a first-class result.

**Pays [DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart)
and [DEBT-022](../debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one).**
Both name this Sub-step as their Trigger: it is the first component that
assembles a statement out of Metric Definitions rather than a person writing one,
and a model told a join might not match writes `LEFT JOIN`.

*Verify:* `uv run pytest tests/test_orchestrator.py` — a question the corpus
covers returns a number and its Lineage; a question it does not covers returns a
refusal naming the reason; every generated statement passes the Gate.

### 6.5 — Ask a question in the browser

A Streamlit page: question in, Grounded Answer out, with SQL, Lineage and Gate
outcome shown rather than hidden.

**Pays [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)** —
its Trigger is the first access-control claim made in the App, and showing an
Access Profile's verdict is that claim. Paid in wording: the page says the data
is synthetic and enforcement is in the Gate, not the warehouse.

*Verify:* `uv run pytest tests/test_app.py` and the page loaded, with a screenshot
in the review.

---

## Not in this Step

- **Evaluation** — Gold Question Set, hit rate, Mean Reciprocal Rank, Execution
  Accuracy, LLM-as-judge. Step 007. 6.2's strategy parameter is the seam it needs.
- **Observability** — Postgres logging and Grafana. Step 007. 6.4 returns the
  Grounded Answer that a logger will consume; nothing is logged yet.
- **Containerization and `README.md`** — Step 008.
- **Multi-turn memory, charting, export** — Target State non-goals, permanently.
- **Paying DEBT-023, DEBT-024 or DEBT-025** — deferred to their 2026-09-09 Trigger
  by the costing above.
