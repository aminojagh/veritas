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

1. **Read reality first** — `.claude/docs/design/current-state.md`, then the repository
   itself. If they disagree, fix `current-state.md` before planning on top of a
   lie.
2. **Read the destination** — `.claude/docs/design/target-state.md`. Identify the
   largest gap that can be closed while keeping the system runnable.
3. **Check the Debt Ledger** — any entry whose Trigger this Step would fire must
   be paid *inside* this Step, not deferred again. Deferring a fired Trigger
   requires saying so out loud and getting agreement.
4. **Choose the slice.** Prefer the slice that removes the most uncertainty. In
   an LLM project the riskiest assumptions are usually about data and retrieval
   quality, not about wiring — walk the skeleton end-to-end early and thin.
5. **Decompose into 1–5 Sub-steps** (see sizing below).
6. **Write** `.claude/docs/plan/step-NNN-<slug>.md`, add the row to
   `.claude/docs/plan/README.md`, and present the Step for approval.

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

## Plan contents

Every plan carries: **Status**, **Goal** (one sentence), **Moves Current State
by**, the numbered Sub-steps each with its **verification command**, and a
**Not in this Step** section.

**"Not in this Step" is mandatory and load-bearing.** It is where scope creep
goes to be recorded instead of enacted. Anything cut there that would leave the
system worse must also become a Debt Ledger entry.

**Delivery Mode: 120 lines, hard ceiling.** A plan is a route, not a case. State
the decision and move on — a paragraph defending a choice against alternatives
nobody proposed is the single biggest source of plan length, and it costs Amino
reading time twice: once here and again when the review cites it. If a choice is
genuinely expensive to reverse it is an ADR, and the plan links to it in one line.

**Do not carry a ruling into code.** Rulings recorded here are for Amino and for
the next planning session. A source file that links to `#rN--…` makes this plan
permanent API and pins its headings forever; cite the Glossary, the Ledger, an
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
| A Sub-step with no test named | Under Delivery Mode a behavioural Sub-step names the `tests/` file that proves it, in the plan, before it is built |
