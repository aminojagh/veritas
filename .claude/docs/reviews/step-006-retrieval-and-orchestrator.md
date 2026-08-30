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
