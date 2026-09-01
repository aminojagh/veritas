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
