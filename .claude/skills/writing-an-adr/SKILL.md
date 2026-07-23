---
name: writing-an-adr
description: Use when choosing between approaches that constrain later Steps, when picking a storage engine or framework or data model, when a choice forecloses alternatives, or when a decision would puzzle someone reading the repo cold
---

# Writing an ADR

## Overview

An ADR records a decision that is **expensive to reverse**, together with the
context that made it reasonable at the time.

**Core principle:** the value of an ADR is in the alternatives and the costs,
not the choice. Anyone can read the code to see what was chosen. Only the ADR
says what was given up.

## When

| Write an ADR | Do not |
|---|---|
| Storage engine, retrieval architecture, evaluation methodology | Library version bumps |
| A choice that constrains the shape of later Steps | Anything swappable in an afternoon |
| Accepting a real cost for a real benefit | Choices with no downside — just do it |
| Rejecting an option someone would obviously suggest | Deliberate shortcuts — those are Debt Ledger entries |
| Resolving a conflict between the Zoomcamp rubric and the job-proposal target | Style preferences |

The two lower-cost neighbours: a **shortcut** goes in the Debt Ledger, and a
**thing we will never do** goes in Target State's Non-goals. Use the cheapest
record that fits — ADRs are for decisions with living consequences.

## Process

1. Number it: highest existing ADR + 1, zero-padded to four digits. Never reuse
   or renumber.
2. Copy `.claude/docs/adr/0000-template.md` to `.claude/docs/adr/NNNN-<slug>.md`.
3. Name the file for the **decision made**, not the topic:
   `0003-duckdb-as-local-warehouse.md`, not `0003-database-choice.md`.
4. Fill it in. Add the row to `.claude/docs/adr/README.md`.
5. If the decision introduces a term, run `registering-language` too.

## Writing it well

**Context** is the part that ages best. Write it so it still makes sense when
the code around it has changed — what pressure existed, what was known, what was
not. Resist the urge to write it as justification; write it as situation.

**Alternatives** must be real. An option listed only to be dismissed in four
words was not considered, and a reader can tell. If there was genuinely one
option, this is not an ADR — put it in `current-state.md`.

**Consequences** must include what this makes harder or impossible. An ADR whose
consequences are all upside is marketing. This section is why the document
exists: it is what a future reader checks when the decision starts to hurt.

**Commitments** are the assumptions that must hold. Name the signal that would
tell you they had stopped holding — that turns an ADR into something with a
falsifiable shelf life rather than a permanent justification.

## Superseding

Decisions get overturned; that is healthy. When it happens:

- The new ADR gets `Supersedes: ADR-NNNN` and explains **what changed** — not
  that the old reasoning was stupid, but which assumption stopped holding.
- The old ADR gets `Status: superseded by ADR-MMMM` and **stays**. It is the
  record of what was true earlier, and deleting it makes the history unreadable.

## Common mistakes

| Mistake | Fix |
|---|---|
| Written after the fact to justify a choice | Write it while deciding, when the alternatives are still live |
| Consequences are all benefits | Name the cost, or reconsider the decision |
| Straw-man alternatives | Steel-man them, or admit there was only one option |
| ADR for a reversible choice | Debt Ledger entry, or just code |
| Deleting a superseded ADR | Mark it and keep it |
