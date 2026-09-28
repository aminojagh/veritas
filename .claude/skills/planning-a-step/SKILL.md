---
name: planning-a-step
description: Use when the previous Step has been committed and the next move needs deciding, when asked what to build next, or when a Step is discovered mid-flight to be too large
---

# Planning a Step

## Overview

A **Step** is one vertical slice from Current State toward Target State. It must
leave Veritas working end-to-end — thinner, but never broken.

**Core principle:** plan exactly one Step. The Target State is fixed; the route
to it is discovered by walking it. Planning Step N+2 before Step N ships is
speculation dressed as diligence.

<HARD-GATE>
Do not write implementation code until the plan file exists and Amino has
approved it. This holds however obvious the Step looks.
</HARD-GATE>

## Process

1. **Close the previous Step.** A Step closes when Amino commits its last
   Sub-step. Delete its plan and its review in this plan's diff; git keeps both.
2. **Read reality first** — `.claude/docs/design/current-state.md`, then the repository
   itself. If they disagree, fix `current-state.md` before planning on top of a
   lie.
3. **Read the destination** — `.claude/docs/design/target-state.md`. Identify the
   largest gap that can be closed while keeping the system runnable.
4. **Check the Debt Ledger** — any entry whose Trigger this Step would fire must
   be paid *inside* this Step, not deferred again. Deferring a fired Trigger
   requires saying so out loud and getting agreement.
5. **Choose the slice.** Prefer the slice that removes the most uncertainty. In
   an LLM project the riskiest assumptions are usually about data and retrieval
   quality, not about wiring — walk the skeleton end-to-end early and thin.
6. **Decompose into 1–5 Sub-steps** (see sizing below).
7. **Write** `.claude/docs/plan/step-NNN-<slug>.md` from the template below, point
   Current State's Resume-here at it, and present the Step for approval.

## Sub-step sizing

**One Sub-step = one commit.** The test: write the commit message. If it needs
the word "and" to be accurate, it is two Sub-steps.

| Symptom | Verdict |
|---|---|
| Commit message needs "and" | Split it |
| Leaves the app unrunnable at the end | Merge with its neighbour, or resequence |
| Cannot state what proves it works | Not ready to plan — the goal is still vague |
| Six or more Sub-steps | This is two Steps; ship the first |
| Only touches docs, no behaviour | Fine — documentation Sub-steps are real |

Fold setup, config, scaffolding, and docs into the Sub-step whose deliverable
needs them. Split only where Amino could reasonably approve one Sub-step and
reject the next.

## The plan

**Target: 120 lines.** A plan is a route, not a case. State the decision and move
on — a paragraph defending a choice against alternatives nobody proposed is the
single biggest source of plan length. If a choice is genuinely expensive to
reverse it is an ADR, and the plan links to it in one line. Go over for a
schedule, a Term Proposal, or a ruling Amino must make — never for restatement.

```markdown
# Step NNN — <title>

**Status:** proposed | active
**Goal:** one sentence.
**Moves Current State by:** what will be true that is not true now.

## Sub-steps

### N.1 — <the commit's subject line>

What it builds, in two or three lines. **Proved by** `tests/test_<component>.py`,
written first. **Verify:** `uv run pytest tests/test_<component>.py`.

## Not in this Step

- <what was cut> — with its DEBT-NNN if leaving it out makes the system worse.

## Rulings

- **<question>** — the recommendation. Amino's ruling replaces it once given.
```

**"Not in this Step" is mandatory and load-bearing.** It is where scope creep
goes to be recorded instead of enacted. Anything cut there that would leave the
system worse must also become a Debt Ledger entry.

**Rulings** appears only when Amino must decide something before or during the
Step.

**Do not carry a ruling into code.** The plan is deleted when its Step closes, so
a source file that links to it links to nothing. Cite the Glossary, the Ledger, an
ADR, or Target State instead.

## Common mistakes

| Mistake | Why it hurts |
|---|---|
| Planning by layer ("build all the models", then "build all the API") | No Step ships anything usable; risk stays concentrated at the end |
| Sub-steps that only make sense together | Amino cannot review or revert them independently |
| Silently widening scope mid-Step | The plan stops describing the work; write it into the plan or a later Step |
| Planning around debt instead of firing its Trigger | The Ledger becomes decorative |
| Introducing new nouns in the plan | Every domain term must clear the Glossary first — use `registering-language` |
| Arguing the Step's case at length | The Step is approved or it is not; the argument is not re-read. State the route |
| A behavioural Sub-step with no test named | The plan names the `tests/` file that proves it before it is built |
