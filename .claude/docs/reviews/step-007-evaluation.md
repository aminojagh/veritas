# Step 007 — Evaluation — Step Review

Handoff notes for Amino, one section per Sub-step. See the `closing-a-substep`
skill. Under [Delivery Mode](../../../CLAUDE.md) each section is capped at 40
lines: the diff is in git and the behaviour is in `tests/`, so this file carries
only what neither of those shows.

---

## Sub-step 7.1 — Write the Gold Question Set

**Changed.** `data/gold/` — twenty-four Gold Questions: the question, the ending it
expects, and the gold SQL and gold result where that ending is a number.
`veritas/evaluation/gold.py` derives each one's relevant Semantic Entries from its own
statement, and computes no measure yet.

**Verified.** `uv run pytest` — 189 passed, 4 skipped (live-model). `verify_framework.py`,
`check_language.py`, `check_warehouse.py`, `check_validation_gate/` PASS. Below, the two
Section C separations paying DEBT-004 and DEBT-011, measured 2026-09-01:

```
$ uv run pytest tests/test_gold.py -q -s -k "separate or settlement"
  Gross Revenue in the second quarter of 2026  (tolerance 0.010000%)
    on Trade Date      8658.946908
    on Settlement Date 8490.762487  (1.942320%)
    rate alone         8656.321524  (0.030320%)
  Traded Notional on 18 March 2025  (tolerance 0.010000%)
    one day,    at Execution Price 828616.381946
    one day,    at the close       827268.979679  (0.162609%)
    whole book, at Execution Price 89203984.780515
    whole book, at the close       89204940.478468  (0.001071%)
2 passed, 19 deselected in 2.17s
```

**Debt** — DEBT-004, DEBT-011 and DEBT-033 paid; DEBT-035 opened.

**Sceptically.** (1) `Account Value` sits in the set with a statement the Gate refuses;
`REFUSED_TODAY` in `tests/test_gold.py` names it, so paying DEBT-035 breaks the test —
leaving it out would have met DEBT-033's coverage by hiding the defect.
(2) `RESULT_TOLERANCE` is a policy constant I chose, and it is what makes DEBT-011 bite:
loosen it and a book-level notional question is admissible again. (3) An axis is *touched*
when a statement groups by **or filters on** its column — wider than the route rule, and
why `by region` is in every set. (4) A Join Path can never be a search hit, so 7.3 scores
a set's reachable part; gold SQL is not dialect-scanned; twenty-four questions is coarse.

**Language.** **`Gold Question`** and **`Relevant Set`** proposed here and **agreed
2026-09-01**, now two Section A rows. Swept to the registered spelling: the living
documents, this code, this review. Not swept: committed reviews and closed plans, which
are point-in-time. `Expectation` and `PhrasingClass` coin nothing.

---

## Sub-step 7.2 — Register the phrasings and detect them

**Changed.** [Glossary Section D](../glossary.md#d-ambiguous-terms) gained an *Also said as*
column — nine spellings, five rows — `semantic/ambiguous/` publishes each row's cell as
`aliases`, and `rewrite.py` matches per **spelling**, naming the one used both to the model
and in the question it asks back. *"turnover"* left `Traded Notional`.

**Verified.** `uv run pytest` — 195 passed, 4 skipped (live-model), from 189 + 4 before; all
six frozen checks PASS, `check_semantic_layer.py` included. The four classes, 2026-09-01:

```
$ uv run pytest tests/test_rewrite.py -q -s -k "not_the_registered_name"
  what is our PnL on tech positions
    says 'P&L' -> "PnL" could mean Realised P&L or Unrealised P&L. Which do you mean?
  how much is in account 41
    says 'how much does X have' -> "how much is in" could mean Cash Balance or Account Value. Which do you mean?
  what were our revenues last quarter
    says 'revenue' -> "revenues" could mean Gross Revenue or Net Revenue. Which do you mean?
  what was turnover last month
    says 'volume' -> "turnover" could mean Traded Notional or Trade Count. Which do you mean?
4 passed, 31 deselected in 2.73s
```

**Debt** — DEBT-029 paid. Nothing opened.

**Sceptically.** (1) **The column is domain content I wrote and Amino has not agreed** —
nine spellings, and the "turnover" ruling inside them. Rejecting it restores the metric
alias and flips `data/gold/turnover_q2_2026.yaml` to `expects: answer`. (2) An Ambiguous
Term's `aliases` are **not** searchable text though a metric's are: nothing would match on
one, since the rewrite step reads them before any search runs — and indexing them cost
`how much does client 42 have` its vector hit, 4th to 8th, failing
`test_every_strategy_finds_the_entry_a_person_names`. Measured 2026-09-01 at `top_k=8`;
reproduce by adding `"aliases"` to `SEARCHABLE_FIELDS[AmbiguousTerm]`. It cost narrowing
`test_corpus_makes_every_alias_searchable` to Metric Definitions — the one existing claim
this Sub-step made smaller. (3) The phrase row's aliases are the first spellings ending in
`X`, which the old pattern would have missed silently, so the guard is
`test_every_registered_spelling_finds_its_own_term` rather than four examples.

**Approved 2026-09-01, on all three, and Section D's column with them** — *"all changes
and decisions including the sceptical points are approved"*. The nine spellings are agreed
Glossary content, *"turnover"* stays a spelling of `volume`, and 2's narrowing stands.

**Language.** No Term Proposal: the amendment adds spellings of five registered terms and
coins nothing. `spellings` and `first_said` are process words; `aliases` is an existing field.

---

## Sub-step 7.3 — Measure Retrieval: hit rate and MRR

**Changed.** `veritas/evaluation/retrieval.py` scores every Retrieval Strategy over the
Gold Question Set under the two settings the Ledger left to a measurement — corpus indexed
flat or per field, resolved meaning appended or spliced. Each is a named argument rather
than a rewrite, so the sweep stays re-runnable; both defaults now say what the numbers said.
`tests/test_rewrite.py` pins the winning form on the sentences that make it awkward — a
captured subject, two meanings at once, two terms, a term said twice.

**Verified.** `uv run pytest` — 219 passed, 4 skipped (live-model), from 195 + 4 before.
`verify_framework.py`, `check_language.py`, `check_semantic_layer.py`,
`check_warehouse.py` and `check_validation_gate/` PASS. The sweep, measured 2026-09-01:

```
$ uv run python -m veritas.evaluation retrieval
  gold          data/gold — 24 Gold Questions, 12 with a Relevant Set a search can return
  scored        39 relevant entries across them, at top_k = 5
  rewrite       6 of the 12 say an Ambiguous Term, so the two rewrite forms differ on those and agree on the rest

  searchable  rewrite   text       vector     hybrid     reranked
                        hit   mrr  hit   mrr  hit   mrr  hit   mrr
  flat        appended  1.000 0.681  1.000 0.708  1.000 0.681  1.000 0.750
  flat        spliced   1.000 0.681  1.000 0.778  1.000 0.722  1.000 0.833
  per field   appended  1.000 0.750  1.000 0.708  1.000 0.750  1.000 0.750
  per field   spliced   1.000 0.833  1.000 0.778  1.000 0.833  1.000 0.833  <- today
```

**Debt** — DEBT-027 and DEBT-030 paid, each with its losing form named.
[DEBT-036](../debt-ledger.md#debt-036--splicing-writes-over-the-first-mention-of-a-term-and-leaves-every-later-one)
opened: the splice writes over a term's **first** mention, so a question that says one
twice keeps the second — found by the splice tests this section's close added, after the
approval below.

**Sceptically.** (1) **Hit rate decides nothing** — 1.000 in all sixteen cells, so both
defaults flipped on MRR alone, which over twelve questions moves in steps of 1/24. (2)
**The rewritten question is also what the generator is grounded in** — `flow.py` hands
`resolved.rewritten` to `generate` — and splicing was chosen on retrieval evidence only;
7.4 is where generation gets a say, and flipping back is one line. (3) **MRR is held down
by the corpus, not the search**: for the six questions saying an Ambiguous Term, that
term's entry matches the words and is never in a Relevant Set — `gold.py`'s *"no gold SQL
touches one"* — so splicing wins partly by deleting the word it matches. (4) `vector` is
identical across the searchable forms, as it must be, which is the sweep's own check.

**Approved 2026-09-02, on all four sceptical points and the two defaults they hedge** —
*"all other changes and decision, including the sceptical points are reviewed, staged and
approved"*. DEBT-036 is the one thing here Amino has not ruled on: it was opened after that
approval and changes no code, so the measured arms and the table above stand as they are.

**Language.** No Term Proposal: `SearchableForm` and `RewriteForm` take the Ledger's own
words — DEBT-027's *"one flat field"* against a *"per-field index"*, DEBT-030's
*"Appending"* against *"splicing"* — and `RetrievalMeasures` is `Evaluation Measure`'s.

---

## Sub-step 7.4 — Measure generation: Execution Accuracy and LLM-as-judge

**Changed.** `veritas/evaluation/generation.py` runs the whole flow over the Gold Question
Set once per prompt per registered provider, scoring Execution Accuracy, the ending the set
calls correct, and a judge's agreement with the first. `PromptForm` is the prompt seam and
`EndedBy` names the step that ended each question, so a Gate refusal is not a wrong number.

**Verified.** `uv run pytest` — 236 passed, 4 skipped (live-model), from 219 + 4 before.
`verify_framework.py`, `check_language.py` and all four Warehouse checks PASS. The sweep,
2026-09-02, less two header lines the table's own columns repeat:

```
$ VERITAS_LIVE_MODEL=1 uv run python -m veritas.evaluation generation
  gold          data/gold — 24 Gold Questions, 23 of them scored
  excluded      'Account Value as of 10 August 2026' — the Validation Gate refuses the statement the set itself calls correct, so no model can answer it
  judge         gpt-4o-mini, on every scored question

  prompt  model                      ending  execution accuracy  judge agreement
  rules   openai gpt-4o-mini          14/23          2/11 0.182      17/23 0.739  <- today
  rules   groq openai/gpt-oss-120b    22/23         10/11 0.909      18/23 0.783
  shape   openai gpt-4o-mini          14/23          2/11 0.182      21/23 0.913
  shape   groq openai/gpt-oss-120b    22/23         10/11 0.909      21/23 0.913
```

**Debt** — DEBT-036 paid: every mention is spliced now, not the first. DEBT-035 **not
paid**, on the second branch its own Trigger allows; the `excluded` line above is its cost,
derived rather than named. DEBT-037 opened: eight of `gpt-4o-mini`'s nine failures are
`no sql` — asked why, it says *"The date 18 March 2025 is beyond the data available up to
October 2023"*.

**Sceptically.** (1) **The prompts tie and the models do not** — Execution Accuracy is
identical across `rules` and `shape` on both providers, so `DEFAULT_PROMPT_FORM` stays
`rules`, though `shape` says it in a quarter of the words. (2) **0.182 reads one model's
habit, not Veritas**; DEBT-037's fix is one sentence per prompt, not made here because the
prompt is the arm being measured. (3) **Eleven questions**, so one is worth 0.09 — and
`Cash Balance` failed in the sweep and answered when re-asked, so a cell moves between runs
at temperature 0. (4) **The judge grades itself among others**, disagreeing only on refusals.

**Language.** No Term Proposal: `PromptForm` takes `RewriteForm`'s shape, Execution Accuracy
and LLM-as-judge are the Glossary's [Evaluation Measure](../glossary.md#a-the-system) row,
and `EndedBy` names endings `flow.py` already had.
