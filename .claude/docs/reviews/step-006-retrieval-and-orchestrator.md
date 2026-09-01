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


---

## Sub-step 6.4 — Answer a question end-to-end

**Changed.** `veritas/orchestrator/` gained the flow's other six steps — `generate.py` grounds a model in retrieved entries and asks for SQL, `answer.py` is the `GroundedAnswer` and its `Lineage`, `flow.py` is the sequence and its five ways out — with `GROUNDED_FIELDS` as the prompt's whitelist, parallel to `SEARCHABLE_FIELDS`. In the Gate, `Join` gained the join's kind and `metric_expressions_through` keeps the alias each expression reads through: the two readings [DEBT-022](../debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one) and [DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart) were missing.

**Verified.** `verify_framework.py`, `check_language.py` and `check_validation_gate` PASS. Run 1 is all a reviewer without a key proves; `-s` on runs 3 and 4 prints the five statements, and both providers write the same five and return the same figures — the generated `Gross Revenue` is 67,935.82, the number run 2 prints for the statement a person wrote.
```
$ uv run pytest -q                                        # no key, no call made, 3 live tests skipped
152 passed, 3 skipped in 36.26s
$ uv run pytest tests/test_gate.py -s -q                  # the two probes the Ledger entries owed
  certified   Gross Revenue              67,935.82   Traded Notional          89,203,984.78
  crossed     Gross Revenue              49,327.82   Traded Notional       4,001,630,547.61
  JOIN        Gross Revenue              67,935.82   over    582 rows
  LEFT JOIN   Gross Revenue              67,935.82   over    582 rows
8 passed in 0.52s
$ VERITAS_LIVE_MODEL=1 uv run pytest tests/test_orchestrator.py -k configured -q          # gpt-4o-mini
2 passed, 19 deselected in 25.00s
$ VERITAS_LIVE_MODEL=1 VERITAS_LLM_PROVIDER=groq uv run pytest … -k configured -q  # openai/gpt-oss-120b
2 passed, 19 deselected in 83.65s (0:01:23)
```

**Debt** — **021 and 022 paid**, each with the probe it owed. 021 moves both numbers, by 27% and by 45×; 022 moves nothing, which its own entry predicted — every Trade has a rate, so the outer join reads the same 582 rows. Opened: [DEBT-031](../debt-ledger.md#debt-031--a-grounded-answer-carries-rows-with-no-column-names) (rows carry no column names, due 6.5), [DEBT-032](../debt-ledger.md#debt-032--a-refusal-that-is-not-the-gates-carries-no-reason-a-chart-can-group-by) (a non-Gate refusal is prose, due in 007), and [DEBT-033](../debt-ledger.md#debt-033--the-generators-live-evidence-is-five-self-written-questions-and-four-certified-metrics-never-reach-it) on your ruling on 2 below.

**Sceptically**, hardest first.

1. **The Orchestrator writes the route into the prompt, so the model no longer picks it.** Each metric block carries its own joins *and* the access joins as pasteable clauses, after `gpt-4o-mini` failed four ways on the indirection — `route_text`'s docstring records them. Left to the model: which metric, whether to slice and by what, whether to filter a period, whether to refuse. That is less generation than "text-to-SQL" implies, and Step 007 measures Execution Accuracy on a generator handed the plumbing.
2. **The live set is five questions and they are mine.** They reach all four fact tables, never generate for four of the nine metrics, and **none carries a period** — so `UNCERTIFIED_DATE_COLUMN` is the one Gate rule no generated statement has met. I also mis-filed *"which instrument did we trade most often"* as uncovered: Groq answered it with `Trade Count` by `by instrument type` and the Gate allowed it, correctly.
3. **`crossed_conversion` is wider than DEBT-021 asked for** — every metric expression must read only through its own metric's joins, always, rather than only where one table is joined twice. It refuses nothing the corpus certifies, and costs one `certified_route` resolve per traced metric per judgement.

**Approved 2026-08-31, on all three.** 1 stands as built — *"totally fine for now if the model can't handle correct
join paths given only the name"* — and the extension it implies, **how much freedom the model is given and in what
abstraction and domain language its context is put to it**, is deliberately **not registered**: its scale and scope are
not known yet, and the [Extension Register](../extension-register.md)'s load-bearing field is the seam — *"An extension
with no seam is a rewrite nobody has admitted to yet."* 2 goes to the Gold Question Set, which is
[DEBT-033](../debt-ledger.md#debt-033--the-generators-live-evidence-is-five-self-written-questions-and-four-certified-metrics-never-reach-it)
— *"this must be handled when we create the gold question set"*. 3 approved as is.

**Language** — no new terms; `Grounded Answer` and `Lineage` were registered 2026-08-04 and are now code. Two renames, both collisions this Sub-step created: `rewrite.py`'s rules constant and its `instruction` became `RESOLUTION_RULES` and `resolution_instruction`, one word naming two steps being Non-Negotiable 1 inverted; and the code-fence pattern moved to `veritas/llm/` with `json_reply` beside it, a fence being a difference between providers rather than between steps. 6.3's **`Clarifying Question`** proposal stays open and now names a second field, `GroundedAnswer.clarification`.

---

## Sub-step 6.5 — Ask a question in the browser

**Changed.** `veritas/app/` is the ninth-to-seventh component: `render.py` turns a Grounded Answer into strings and imports no Streamlit, `page.py` places them and is the only module allowed to import one. `WarehouseAdapter.query_with_columns` reads the engine's column names beside the rows and `GroundedAnswer.columns` carries them, which is [DEBT-031](../debt-ledger.md#debt-031--a-grounded-answer-carries-rows-with-no-column-names); the sidebar states what Access Profile enforcement is worth in [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s own words, which is that one.

**Verified.** Run 1 is all a reviewer without a key proves. Run 2 asks OpenAI a question through the page itself and prints what the page showed — the same `Gross Revenue` figure runs 2–4 of Sub-step 6.4 print for a statement a person wrote.
```
$ uv run pytest -q                                            # no key, no call made, 4 live tests skipped
168 passed, 4 skipped in 55.25s
$ VERITAS_LIVE_MODEL=1 uv run pytest tests/test_app.py -k end_to_end -q -s     # gpt-4o-mini
  answer 67,935.82
  SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) AS answer
FROM fct_trade
JOIN fct_fx_rate ON fct_fx_rate.rate_date = fct_trade.trade_date AND fct_fx_rate.from_currency = fct_trade.denomination_currency AND fct_fx_rate.to_currency = 'EUR'
JOIN dim_account ON dim_account.account_id = fct_trade.account_id
JOIN dim_client ON dim_client.client_id = dim_account.client_id
WHERE dim_client.client_region = 'EU'
1 passed, 15 deselected in 16.51s
$ uv run python .claude/scripts/verify_framework.py           # 1433 links, 1156 anchors
PASS — framework is wired up correctly
$ uv run python .claude/scripts/check_language.py             # 41 files, 2114 identifiers, 0 proposed
PASS — documents agree with the Glossary and the writing conventions
```

**The two screenshots are illustrations, not evidence.** `uv run streamlit run veritas/app/page.py`, driven by a throwaway Playwright script in a temporary environment: Playwright is not a dependency, nothing in the repository reproduces them, and everything they show is asserted in `tests/test_app.py`, which anyone can run. [Answered](images/step-006-app-answered.png) — *"what was our gross revenue by region"*, `revenue` resolved, the breakdown under `slice` and `answer`, the statement, eleven Lineage entries, `allowed — 8 rules ran`. [Refused](images/step-006-app-refused.png) — *"what columns are in fct_trade"*, the model's refusal, no SQL, and `no statement reached the Validation Gate`.

**Debt** — **008 and 031 paid.** Opened [DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used), point 1 below.

**Sceptically**, hardest first.

1. **The Lineage is what the model was shown, and the page presents it as an audit trail.** Eleven entries under a `Gross Revenue` answer, `Net Revenue` among them; the same eleven under a refusal that produced nothing. 6.4 chose that deliberately — one list read twice — and 6.5 is where a *person* reads it and would conclude both metrics were involved. Narrowing it means the `Validation Gate outcome` carrying the metrics and Join Paths a statement traced to, which is a change to a contract three components read, so it is [DEBT-034](../debt-ledger.md#debt-034--lineage-records-what-the-model-was-shown-not-what-the-statement-used) against the Step 007 logger rather than a widening taken here. It is also why the figure has no unit or currency beside it: the metric whose `unit` would label it is not identifiable from a list naming two.
2. **The page is tested by running its source, not by importing it.** `AppTest.from_function` executes the source of the test's `driven` wrapper as the script, so that wrapper imports what it needs itself and takes the Orchestrator as an argument. It is why `page(orchestrator=…)` takes its dependency rather than reaching for one — the real page passes nothing and builds one under `st.cache_resource`. A reader who adds a module-level reference to that wrapper will get a `NameError` from a test that looks like it should work.
3. **`query` is now `query_with_columns` with the names dropped.** The alternative was changing `query`'s return type at eleven call sites, or a result record every caller unpacks; this leaves the eleven untouched and puts the cursor's description — dialect, and therefore the adapter's — in one place. The cost is two read methods where the seam had one.
4. **The App opens its own Warehouse connection and never closes it.** One per server process, held by `st.cache_resource` for its life. DuckDB takes one writer, so `uv run python -m veritas.ingestion` while the page is running will fail to open the file; nothing says so yet.

**Approved 2026-09-01, on all four, and this commit closes Step 006.** [ADR-0005](../adr/0005-one-openai-compatible-endpoint-for-every-provider.md) is `accepted` with it, the Groq row stands at `openai/gpt-oss-120b`, and the Target State's narrowed credential table is confirmed rather than re-opened — the three things the Step was holding. **6.3's `Clarifying Question` Term Proposal was approved the same day**, and is registered in [Section A](../glossary.md#a-the-system) as the second of the two ways a Grounded Answer carries no number. The rename it carried is in this commit: `clarification` is `clarifying_question` on `Rewrite` and `GroundedAnswer`, and `clarification_for` is `clarifying_question_for`. Nothing carries into Step 007.

**Language** — no new terms; `App` was registered 2026-08-04 with `veritas/app/` as its path, and the directory now exists. 6.3's **`Clarifying Question`** proposal stays open and now has a third home: the page renders `GroundedAnswer.clarification` as the question Veritas asks back.
