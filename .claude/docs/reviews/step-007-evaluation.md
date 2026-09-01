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
