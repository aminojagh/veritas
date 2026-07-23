# Step Review — Step 001: Design the Target State

## Sub-step 1.1 — Agree the domain language and target state

**What changed**

Decided what Veritas is, and wrote the vocabulary to describe it.

- **`.claude/docs/glossary.md`** — Domain Language in four sections: **the system**
  (Semantic Layer, Validation Gate, Grounded Answer, Lineage, Execution
  Accuracy, …), **the warehouse** (Trade, Cash Movement, Position, Gross/Net
  Revenue, …), **distinctions we must not blur**, and **Ambiguous Terms**.
  All 36 terms are `proposed`.
- **`.claude/docs/design/target-state.md`** — the problem, the governing rule,
  components, flow, non-goals, the Zoomcamp criteria map, and the extension path
  to the full MVP.

The design in one line: **the model never defines a metric — it may only select
one from a certified Semantic Layer, and everything it generates is checked by
code before it runs.**

Two structural consequences worth naming, because they are why this shape was
chosen over a conventional text-to-SQL demo:

1. **Retrieval becomes the correctness mechanism**, not a nicety. Retrieving the
   wrong Metric Definition *is* the wrong answer. That is what lets retrieval
   evaluation have derived ground truth: the Semantic Entries a gold SQL touches
   are, by construction, its relevant set. No hand-labelling, no judge.
2. **Ambiguous Terms are first-class and are *not* metrics.** "Revenue",
   "volume", "balance", "P&L" each map to two or more Certified Metrics, so
   Veritas must resolve them before generating SQL. This turns the rubric's
   query-rewriting bonus point into the product's core disambiguation step
   rather than a bolt-on — and it is a direct answer to the job spec's line
   about distinguishing revenue, gross revenue, net revenue, trading volume,
   cash movement, accounting movement, balances, and position changes.

**Verification**

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       513 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          665 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr          592 words
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
```

Criteria map checked by hand against the rubric: 20 of 24 points designed for,
2 deferred (cloud deployment), 3 claimed as extra credit. Every capitalised term
in `target-state.md` traces to a Glossary entry.

**Deliberately left undone**

- **Sub-step 1.2 — the three founding ADRs** (Semantic Layer as corpus, DuckDB
  behind an adapter seam, deterministic Validation Gate). Held back because ADRs
  written against an unapproved Target State get rewritten with it. Not debt —
  planned work, sequenced.
- **Instrument/price data source** — FX is settled (Frankfurter: real ECB rates,
  no API key, good for reproducibility). Instruments and prices are left to the
  ingestion Step so the choice can be tested rather than guessed.
- **Cloud deployment** (2 bonus points) — outside a 2–3 week slice.
- No new Debt Ledger entries. This Sub-step wrote documents; there was nothing
  to shortcut.

**Look at this sceptically**

1. **36 proposed terms is a lot to agree at once.** The eight in *"distinctions
   we must not blur"* are the ones that actually matter — if the financial
   definitions there are wrong, the product is wrong. Please read those eight
   properly even if you skim the rest. I am most exposed on **Accounting
   Movement**: I have defined it as accrual-basis recognition on the date value
   is *earned*, versus Cash Movement on the date money moves. If EXANTE-style
   brokerage usage differs, correct me.
2. **Synthetic client activity may read as a weaker dataset** to a peer
   reviewer, even though the rubric explicitly permits generated data. The
   mitigation is that FX and market data are genuinely real, and the framing —
   "market data real, client data synthetic for privacy" — is what an actual
   broker would say. Worth knowing it is a judgement call.
3. **The scope is the top of what fits in 2–3 weeks.** Nine components. The
   honest risk is the last mile: Grafana dashboards and docker-compose are
   exactly what gets rushed, and they are 4 rubric points. If time compresses,
   my recommendation is to cut re-ranking (1 point) before cutting monitoring
   (2 points).
4. **`sqlglot` is load-bearing and unproven here.** The Validation Gate's whole
   claim — deterministic, parse-tree-level checks — rests on being able to trace
   generated SQL expressions back to Certified Metrics. I believe this works but
   have not built it. It is the single highest-risk assumption in the design, so
   Step 002 should touch it early rather than leave it to the end.
5. **"Refusing to answer is a feature" will feel bad in a demo.** It is the
   correct behaviour and it is the point of the project, but a reviewer clicking
   around may read refusals as brokenness. The UI needs to make a refusal look
   like rigour, not failure.

**Language**

36 Domain Language terms proposed, none agreed yet. No terms entered code — no
code was written, which is the intended order.

Cross-checking the Glossary against `target-state.md` caught one real collision:
I had written "Certified Metric Definitions", conflating two separately
registered terms. Fixed to "Metric Definitions" — a Metric Definition in the
Semantic Layer is certified by construction, so the adjective was doing no work.

**One collision for you to rule on:** **Certified Metric** and **Metric
Definition** are close enough to be worth questioning. My reading is that they
are genuinely different — a Metric Definition is the *artifact* (the YAML entry
you retrieve), while Certified Metric is a *status* whose value is the contrast
with Shadow Metric. But if you think one term can carry both jobs, say so and I
will retire the other before either reaches code.

Nothing in the Process Language changed. One inconsistency fixed in Step 000:
sub-steps were numbered `1.1` inside Step `000`; the scheme is now
`Step NNN → Sub-step NNN.M` throughout.

---

## Revisions from review — 2026-07-23

Amino's ruling on Sub-step 1.1, and the changes folded in. The sections above are
left as written (a point-in-time record); this section is what changed since.

**Rulings received**

- **Section-C distinctions approved**, and all other Domain Language terms
  approved → Sections A through D are now `agreed`. The batch-proposed banner is
  retired.
- **`Certified Metric` and `Metric Definition` both kept** — the collision is
  resolved as "genuinely different," so neither is retired.

**Changes made**

- **Glossary:** Sections A through D flipped `proposed` → `agreed`; `Dimension
  Definition` rewritten with a plainer explanation and worked examples (the term
  was flagged as unclear); a new **System measures** section added —
  `Evaluation Measure` and `Operational Measure` (`proposed`), keeping "metric"
  exclusively for business metrics and "measure" for how Veritas is judged.
- **Target State:** status now "terms `agreed`, document `proposed` until the
  data-availability check"; a "two senses of metric" note added by the components
  table; the Zoomcamp criteria map gained a header clarifying each row is a
  *grader's scorecard line*, and the **Problem description** row was expanded.
- **Plan (Step 001):** new **Sub-step 1.2 — verify data availability** inserted as
  an explicit gate before the design is final; the three ADRs moved to 1.3.
- **Product brief:** `.claude/docs/design/product-brief.md` written — the full system
  Veritas slices, captured in Glossary terms so `final_proposal_target.md` can be
  removed from the repo.
- **Framework (proposals to react to):** the *contour-lines / seam test* principle
  added to `CLAUDE.md` and the `recording-debt` skill; a *session-resumption*
  contract added to `CLAUDE.md` and `closing-a-substep`, with a **Resume here**
  block now opening `current-state.md`.
- **Links:** concrete doc paths in `CLAUDE.md` and the state docs are now
  clickable; globs, future code modules, and DB table names are left as plain
  monospace (linking them would be a dead link and fail `verify_framework.py`).

**Resolved since**

1. System measures approved — `Evaluation Measure` and `Operational Measure` are
   now `agreed`.
2. Framework wording (contour/seam, session-resumption) approved as written.
3. Step 000's checker-vs-description call ruled: keep the broadened checker.
