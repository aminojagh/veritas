# Step 001 — Design the Target State

- **Status:** done — all three Sub-steps committed, the last in `9c5b060` (2026-08-05)
- **Goal:** Decide what Veritas is, in language we both agree on, so that every
  later Step has a fixed point to be measured against.
- **Moves Current State by:** replacing an empty Target State and an empty Domain
  Language with agreed ones. No application code.

## Why this Step

The framework's central rule is that shared understanding is never compromised.
That rule is unenforceable while `target-state.md` is a skeleton and the Glossary
has no Domain Language — there is nothing to check names against, so the first
implementation Step would inevitably coin vocabulary by accident and the Glossary
would become a description of the code rather than its source.

Inputs: the Zoomcamp rubric, `final_proposal_target.md`, the reference project
(`alexeygrigorev/fitness-assistant`), the reusable coursework in
`aminojagh/LLMZC`, and the four design decisions taken in interview.

## Sub-steps

### 1.1 — Agree the domain language and target state ✅

- `.claude/docs/glossary.md` — Domain Language in four sections: the system, the
  warehouse, the distinctions we must not blur, and the Ambiguous Terms; plus the
  System measures added in review. All `agreed` (2026-07-23).
- `.claude/docs/design/target-state.md` — the problem, the governing rule, components,
  flow, non-goals, Zoomcamp criteria map, extension path to the full MVP.

**Verification:** `.claude/scripts/verify_framework.py` passes; every term used in
`target-state.md` appears in the Glossary; the criteria map accounts for all 24
rubric points.

### 1.2 — Verify data availability

Before the Target State is marked `agreed`, prove that every source the design
assumes can actually be obtained at the scale needed to build *and test* the
system. This is the "do we have the paints before we commit to the composition?"
check — the design is not final until it passes.

- **FX Rates** — confirm the Frankfurter API returns ECB reference rates for the
  currency pairs and date range we need, key-free.
- **Instruments & market prices** — find a key-free public source for instrument
  reference data and end-of-day prices, and confirm coverage. This is the open
  question deferred from 1.1, now answered rather than guessed.
- **Synthetic activity** — confirm we can generate Trades, Cash Movements, and
  Positions rich enough to exercise every Certified Metric and every Section-C
  distinction: periods that straddle a settlement cycle, Clients with multiple
  Accounts, Rebates large enough to separate Gross from Net Revenue.

Output: `.claude/docs/design/data-availability.md` — each source, what it provides, gaps,
and a go/no-go on the Target State. A spike, not production ingestion: the least
code needed to answer the question.

**Verification:** the findings doc exists; each source has been hit at least once
with output pasted into the Step Review; `.claude/scripts/verify_framework.py` passes.

### 1.3 — Record the founding decisions

Three ADRs for choices that shape every later Step and would otherwise look
arbitrary:

- Semantic Layer as the retrieval corpus (the central bet).
- DuckDB as the Warehouse, behind an adapter seam.
- Validation Gate as deterministic code rather than an LLM self-check.

Written once the Target State is `agreed` (after 1.2) — ADRs written against an
unapproved design would need rewriting with it.

## Not in this Step

- Any implementation. The Semantic Layer, warehouse, and simulator are Step 002
  onward. Sub-step 1.2 is a data-availability *spike* — throwaway probes, not the
  ingestion pipeline.
- `README.md` — written once there is something to run.
