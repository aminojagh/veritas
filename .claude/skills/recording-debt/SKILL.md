---
name: recording-debt
description: Use at the moment of hardcoding a value, stubbing a function, skipping validation or error handling, copy-pasting instead of extracting, narrowing scope to make something pass, or choosing a library because it is quick rather than because it is right
---

# Recording Debt

## Overview

Veritas moves fast on purpose. The price of that is that every shortcut is
written down **as it is taken** — not swept up later, not left for the code to
imply.

**Core principle:** the debt entry is part of the shortcut. Taking the shortcut
without writing the entry is the only thing this framework forbids outright.

## The moment to write it

Not at the end of the Sub-step. Not "once it works". The moment you decide to do
the cheap thing — that is when you still know *why*, and why is the part that
decays fastest.

## What counts as debt

**Debt:** a deliberate choice that works now and will hurt later.

| Is debt | Is not debt |
|---|---|
| Hardcoded config that belongs in a settings file | A bug — fix it or file it |
| Stub returning a fixed value | Something you have not built yet but planned |
| No error handling on a path that can fail | A deliberate, permanent simplification (that is a Non-goal) |
| Single retrieval strategy where the design calls for several | A style preference |
| Copy-pasted logic in two places | Code you dislike but that is correct and clear |
| Evaluation on 20 rows because generating 200 was slow | Work explicitly scheduled in the next Step |

The test: **would a competent reviewer, told this was intentional, still wince?**
If yes, it is debt. If nothing is actually worse, it is not debt — do not
inflate the Ledger with entries that have no cost.

## The seam test — is this debt you may take?

Not every shortcut is allowed. Debt is fill left thin *behind* a seam; it is
never a seam drawn wrong. A **seam** is a contour line of the design — a Glossary
name, an interface or adapter boundary, a data contract between components, or the
end-to-end path.

Ask: **can this be repaid later without moving a name, an interface, or the
flow?**

| Answer | Verdict |
|---|---|
| Yes — repayment is a localized fill behind an existing seam | *Detail debt.* Take it, log it, move on. (Naive single-strategy retrieval, 20 gold questions not 200, a stubbed cost estimator, a hardcoded currency.) |
| No — repayment means erasing a contour line and repainting what hung off it | *Structural shortcut.* Not debt you may take. Draw the seam properly now — it is cheap in code, because a seam is an interface plus one trivial implementation. |

The wince test tells you *whether* it is a shortcut. The seam test tells you
*whether you are allowed to take it now*.

## The Trigger

The most important field. It is the condition that forces repayment, and it is
what turns a wishlist into a set of tripwires.

**Prefer observable conditions to dates.**

| Weak | Strong |
|---|---|
| "Later" | "Before the first Step that ingests real data" |
| "When we have time" | "When the corpus exceeds 5,000 documents" |
| "Before launch" | "Before anything other than Amino can reach the app" |
| "Eventually" | "If p95 retrieval latency exceeds 2s" |

A Trigger you cannot imagine ever firing means the shortcut is permanent —
mark the entry `accepted` and say why, rather than pretending it is open.

## Writing the entry

Copy the template from the comment block in `.claude/docs/debt-ledger.md`. Fill every
field; append to the Entries section; add a row to the Index table and update
the counts at the bottom of it.

Keep **Location** precise enough (`path/file.py:42`, or a component name if the
shortcut is genuinely diffuse) that it can be found without archaeology.

Write **What we should have done** specifically enough to act on. "Do it
properly" is not a repayment plan.

## Paying debt

When a Trigger fires, repayment belongs *inside* the Step that fired it. Set
`Status: paid`, name the Sub-step that paid it, and leave the entry in place —
the Ledger is a record, not a queue, and deleting paid entries destroys the
history of how the project was actually built.

## Common mistakes

| Mistake | Fix |
|---|---|
| Ledger entry with no Cost | Then it is not debt; delete it |
| Ledger entry with no Trigger | Invent the tripwire or mark it `accepted` |
| One entry covering several unrelated shortcuts | Split — they will be repaid at different times |
| Using the Ledger as a TODO list | Planned work goes in the plan; the Ledger is only for shortcuts already in the code |
| Recording debt to avoid a five-minute fix | If it is faster to fix than to document, fix it |
