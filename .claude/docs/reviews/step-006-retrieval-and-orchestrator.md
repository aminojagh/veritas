# Step 006 — Ask a question, get a Grounded Answer — Step Review

Handoff notes for Amino, one section per Sub-step. See the `closing-a-substep`
skill. Under [Delivery Mode](../../../CLAUDE.md) each section is capped at 40
lines: the diff is in git and the behaviour is in `tests/`, so this file carries
only what neither of those shows.

---

## Sub-step 6.1 — Index the Semantic Layer for retrieval

**Changed.** `veritas/retrieval/` renders every Semantic Entry as the text a search may
match. `SEARCHABLE_FIELDS` is that whitelist, one row per entry type, and it is where
[ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md)'s corpus claim holds
or fails. A Join Path is the one entry type with no row at all.

**Verified.** `uv run pytest` is 9 passed; `verify_framework.py` and `check_language.py`
both PASS. Two of the six below skip without a built Warehouse; this run had one.

```
$ uv run pytest tests/test_retrieval.py -k corpus
collected 6 items

tests/test_retrieval.py ......                                           [100%]

============================== 6 passed in 0.26s ===============================
```

**Debt** — none. The one `text` field below is fill behind 6.2's `retrieve()` seam.

**Sceptically**, hardest first.

1. **A Join Path is unsearchable — a design claim, not a limit I ran into.** The
   [Target State flow](../design/target-state.md#flow) has RETRIEVE *"Returns Metric
   Definitions, Dimension Definitions, and Join Paths"* — it still can, by reference only.
2. **One `text` field, not one per source field.** Flattening loses which field a hit
   landed in, so nothing can rank a `name` match above a `description` one. Ask *"gross
   revenue"*: that phrase is the Gross Revenue entry's own `name` — and it also sits in
   Net Revenue's description, *"Gross Revenue less Rebate and pass-through Fee"*, and
   twice in the `revenue` Ambiguous Term, in its description and its `disambiguates`.
   Three entries match the same words, so the one actually named that can rank third.
   The fix is `searchable_text` returning a mapping; premature before 6.2.
3. **The schema check carries one exemption, a word list.** `commission`, `fee`,
   `rebate`, `amount` and `quantity` are Warehouse columns and also the domain's own
   words. Cost inside `tests/test_retrieval.py`: a new entry could write one meaning the
   column and nothing would notice. Every other identifier stays banned outright.

**Language** — none added, and one not coined: `RetrievalDocument` or `Corpus` would be
a second name for `Semantic Entry`, *"one retrievable document in the Semantic Layer"*.

---

## Sub-step 6.2 — Retrieve Semantic Entries for a question

**Changed.** `veritas/retrieval/search.py` puts `retrieve(question)` in front of 6.1's text, under four
Retrieval Strategies chosen per call so Step 007 can measure them; `minsearch` and `fastembed` arrive
with it. `retrieve` is `rank` plus **reference closure**, the only way a Join Path reaches an answer.

**Verified.** `uv run pytest` is 82 passed; `verify_framework.py` and `check_language.py` PASS.

```
$ uv run pytest tests/test_retrieval.py -q
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 41.12s
```

**Debt** — [DEBT-026](../debt-ledger.md#debt-026--the-retrieval-models-are-downloaded-rather-than-snapshotted): both models download on first use, so a clone builds the Warehouse
offline and cannot retrieve offline. [DEBT-027](../debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match): the flat `text` field, triggered on Step 007's
hit rate and MRR — see 4 below.

**Sceptically**, hardest first.

1. **`reranked` is the default on authority, not evidence** — Target State's *"Hybrid text + vector,
   re-ranked"*. The set proves only that the entry lands within `TOP_K`; Step 007 is what orders them.
2. **Closure is retrieval's job because 6.1 made it so.** The [flow](../design/target-state.md#flow)
   has RETRIEVE *"Returns ... Join Paths"*, unsearchable since 6.1. Two costs, both on *"break the
   answer down by where the client is based"* at `top_k=5`: `retrieve` returns more than `rank`, so hit
   rate and MRR are computed over `rank` — `test_retrieve_is_not_bounded_by_top_k_where_rank_is` holds
   the counts. And `by region` declares a route from each of the four fact tables, so closure takes all
   five of their Join Paths where a `fct_trade` question needs two; which route applies is not settled
   until SQL is generated, so retrieval cannot narrow it.
3. **The text index departs from scikit-learn twice, tuned against my own questions.** Stop words
   dropped; `&` admitted, without which `P&L` is not indexed at all. The fifteen questions are mine.
4. **6.1's flat `text` field is still flat.** Nothing measured says `name` must outrank `description`,
   and I have not guessed a boost — [DEBT-027](../debt-ledger.md#debt-027--the-searchable-text-is-one-flat-field-so-a-name-match-cannot-outrank-a-description-match) makes Step 007 measure a per-field index against
   this one and keep whichever the numbers support.

**Language** — `BAAI` and `ONNX` registered as abbreviations, and **`Retrieval Strategy`** proposed
here and **agreed 2026-08-30**: the row is in the [Glossary](../glossary.md), members stay in code
per [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell).


---

## Sub-step 6.3 — Resolve Ambiguous Terms before retrieval

**Changed.** `veritas/llm/` is the one place a provider, a model or a key is named — a `LanguageModel` seam over a
**closed two-row registry**, OpenAI at `gpt-4o-mini` and Groq at `openai/gpt-oss-120b`, anything else a
`LanguageModelError`. `veritas/orchestrator/rewrite.py` is step 1 of the flow: it matches the Ambiguous Terms a
question says, shows the model only those entries' own words, and takes an answer only if the term `disambiguates` it.

**Approved 2026-08-31, and it moved a settled document.** Your ruling of 2026-08-30 narrowed the Target State's credential
table to *"OpenAI"* required and *"Groq"* free-and-optional; [ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md) quotes it and is written around it, `VERITAS_LLM_BASE_URL` is gone, a third provider is [EXT-011](../extension-register.md#ext-011--more-large-language-model-providers-behind-the-seam), and `.env.example` is the committed template for both keys.

**Verified.** Both keys are in `.env` as of 2026-08-31, so the live path is now measured on both providers.
```
$ uv run pytest -q                      # what a reviewer runs: no key, no call made
125 passed, 1 skipped in 62.62s (0:01:02)
$ VERITAS_LIVE_MODEL=1 uv run pytest tests/test_rewrite.py tests/test_llm.py -q          # OpenAI, gpt-4o-mini
44 passed in 8.60s
$ VERITAS_LIVE_MODEL=1 VERITAS_LLM_PROVIDER=groq uv run pytest tests/test_rewrite.py -k configured -q
1 passed, 29 deselected in 4.02s
```

**Debt** — [DEBT-028](../debt-ledger.md#debt-028--no-test-reaches-a-real-provider-so-the-live-path-is-proven-only-by-a-stub-server) opened and **paid here**: the second run is two `gpt-4o-mini` calls against real OpenAI, and the model
answers `Gross Revenue` to *"our gross revenue in March"* while leaving *"our revenue last quarter"* unresolved — the pair
that tells reading from guessing. Your two points below opened [DEBT-029](../debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently) and [DEBT-030](../debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it); the Anthropic entry drafted here is **withdrawn** before it took a number, so 029 is free.

**Sceptically**, hardest first.

1. **The Groq model name was wrong, and one call was all it cost to find out.** `llama-3.3-70b-versatile` 404s on a new
   free key — *"does not exist or you do not have access to it"* — so the row reads `openai/gpt-oss-120b`, the largest Groq
   lists as production rather than preview. **Both defaults are now OpenAI-authored**; the family-diverse arm on that key is preview-only, so it is a Step 007 `VERITAS_LLM_MODEL` and not the default. Reversing me is one string.
2. **Only a docstring enforces "one place a provider is named."** `check_language.py` scans for Glossary terms, not
   for the string `openai` outside `veritas/llm/`. True today by inspection, not by a check.
3. **Detection is literal, and it is four classes of miss rather than two words** — morphology, orthography, an
   unregistered synonym, and a rewording of the one phrase row, each pinned by a test that asserts today's miss. Not fixed
   here: the phrasings are Glossary content, and an alias that fires too easily answers what Section D asks about. [DEBT-029](../debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently).
4. **The rewritten question appends rather than splices** — *"…gross revenue last quarter (revenue means Gross Revenue)"*.
   Which of the two retrieves better is unmeasured: [DEBT-030](../debt-ledger.md#debt-030--the-resolved-meaning-is-appended-to-the-question-and-nothing-has-measured-that-against-splicing-it) is one more arm on the Step 007 run DEBT-027 already forces.

**Language** — none added; `veritas/llm/` is plumbing, so no `Language Model Adapter` row. 🆕 **TERM PROPOSAL** — **`Clarifying
Question`**: what Veritas returns when an Ambiguous Term is unresolved, rendered by the App and counted by Observability
as a `Validation Gate outcome` is. Code says `clarification`; agreeing it renames one field.
