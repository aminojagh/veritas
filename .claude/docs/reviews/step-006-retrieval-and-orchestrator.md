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
