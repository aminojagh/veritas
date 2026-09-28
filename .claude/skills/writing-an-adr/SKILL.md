---
name: writing-an-adr
description: Use when choosing between approaches that constrain later Steps, when picking a storage engine or framework or data model, when a choice forecloses alternatives, or when a decision would puzzle someone reading the repo cold
---

# Writing an ADR

## Overview

An ADR records a decision that is **expensive to reverse**, as it stands now:
what was chosen, what it was chosen over, and what it costs.

**Core principle:** the value of an ADR is in the alternatives and the costs,
not the choice. Anyone can read the code to see what was chosen. Only the ADR
says what was given up.

**An ADR is time-invariant.** It reads as if written today: present tense, no
date, no Step, no amendment and no pointer to a record it replaced. When the
decision changes, the ADR is rewritten; git keeps the old text.

## When

| Write an ADR | Do not |
|---|---|
| Storage engine, retrieval architecture, evaluation methodology | Library version bumps |
| A choice that constrains the shape of later Steps | Anything swappable in an afternoon |
| Accepting a real cost for a real benefit | Choices with no downside — just do it |
| Rejecting an option someone would obviously suggest | Deliberate shortcuts — those are Debt Ledger entries |

The two lower-cost neighbours: a **shortcut** goes in the Debt Ledger, and a
**thing we will never do** goes in Target State's Non-goals. Use the cheapest
record that fits — ADRs are for decisions with living consequences.

## Process

1. Number it one above the highest number ever used, zero-padded to four digits.
   Deleted ADRs count: `git log --diff-filter=D --name-only -- .claude/docs/adr`
   lists them. Never reuse or renumber.
2. Copy `.claude/docs/adr/0000-template.md` to `.claude/docs/adr/NNNN-<slug>.md`.
3. Name the file for the **decision made**, not the topic:
   `0003-duckdb-as-local-warehouse.md`, not `0003-database-choice.md`.
4. Fill it in. It stays `proposed` until Amino accepts it.
5. If the decision introduces a term, run `registering-language` too.

## Writing it well

**Context** is the part that ages best. Write it as the forces that make the
decision necessary — the pressure, the constraints, what is known and what is
not — so it holds for as long as the decision does. Write it as situation, not
as justification.

**Alternatives** must be real. An option listed only to be dismissed in four
words was not considered, and a reader can tell. A former approach is an
alternative like any other: say what it was and which assumption stopped
holding. If there was genuinely one option, this is not an ADR — it is code.

**Consequences** must include what this makes harder or impossible. An ADR whose
consequences are all upside is marketing. This section is why the document
exists: it is what a future reader checks when the decision starts to hurt.

**Every cost gets classified, in the same Sub-step.** A cost written and left
dangling is a fact nobody acts on — the ADR records it, and then no one re-reads
the ADR until the cost bites. Naming a cost is the moment to decide which of
three things it is, and to say so inline:

| Classification | Meaning | Goes where |
|---|---|---|
| **Accepted** | We are living with this permanently. Say why. | Stays in the ADR, marked *accepted* |
| **Debt** | The slice does the cheap thing; it should be fixed here. | [`debt-ledger.md`](../../docs/debt-ledger.md), with a Trigger |
| **Extension** | Correct for the slice; the full system needs more. | [`extension-register.md`](../../docs/extension-register.md), with the seam it lands against |

The test that settles debt-versus-extension: **does the trigger fire inside this
project's life?** If it can only fire after Veritas becomes something else, it is
an extension, and calling it debt puts a wish on the Ledger.

**A cost may be both**, and forcing a single label loses information. Access
enforced in the application is one: enforcement inside the warehouse is an
extension, while *overstating what the application-level check guarantees* is
debt that fires the first time a document claims more. Split it and link both.

**The failure mode to watch for is ritual.** A rule that feels like paperwork
gets performed rather than thought about, and the cheapest way to perform this
one is to stamp *accepted* on everything. Two guards:

- **Accepted must carry a reason**, not just the word. "Accepted" with no
  argument is a dangling cost wearing a label.
- **An ADR where every cost is accepted deserves re-reading.** It is possible —
  some decisions really are all-upside-with-known-limits — but it is more often a
  sign the costs were written to be survivable rather than to be true.

An ADR whose Consequences list a cost that is none of the three is unfinished.
This is the forcing function that keeps future work discoverable from the
decision that created it, instead of depending on someone remembering.

**Citations quote.** Any claim about what another document says must include the
words it relies on. Do not write "named as out of scope in the product brief"
and link — quote the line. Without the quote there is nothing stopping an
adjacent, plausible-looking sentence from being pressed into service as support
for a claim it does not make, and the link makes the unsupported claim look
sourced.

**Commitments** are the assumptions that must hold. Name the signal that would
tell you they had stopped holding — that turns an ADR into something with a
falsifiable shelf life rather than a permanent justification.

## Changing a decision

Decisions get overturned; that is healthy. When one is:

- **Rewrite the ADR to state the new decision.** It keeps its number; the file is
  renamed for the decision now made. The approach it replaces moves into
  **Alternatives**, with the assumption that stopped holding as the reason it lost.
- **Delete an ADR whose decision no longer binds anything** — its component is
  gone, or nothing later depends on it. Its number is not reused.
- **No chains.** There is no `superseded` status, no `Supersedes:` line, and no
  dated amendment. `git log -- <file>` is the history.

## Common mistakes

| Mistake | Fix |
|---|---|
| Written after the fact to justify a choice | Write it while deciding, when the alternatives are still live |
| Consequences are all benefits | Name the cost, or reconsider the decision |
| Straw-man alternatives | Steel-man them, or admit there was only one option |
| ADR for a reversible choice | Debt Ledger entry, or just code |
| A dated amendment appended to an ADR | Rewrite the ADR so it states the decision as it now stands |
| A new ADR beside the one it overturns | Rewrite the old one; its former approach becomes an alternative |
| Citing a document from memory of its gist | Open it, find the line, quote it — or drop the citation |
| A cost named and left dangling | Classify it: accepted, Debt Ledger, or Extension Register |
