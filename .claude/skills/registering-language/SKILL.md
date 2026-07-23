---
name: registering-language
description: Use before naming any table, column, function, class, or variable that carries domain meaning; when a needed domain noun is absent from the Glossary; or when two words in the project appear to mean the same thing
---

# Registering Language

## Overview

`.claude/docs/glossary.md` is the single source of truth for the project's vocabulary.
The Glossary is not documentation of the code — the code is an expression of the
Glossary.

**Core principle:** never coin a term silently. A word that entered the codebase
without agreement is a word two people understand differently.

## The check

Before writing a domain noun into a document, a plan, or an identifier:

```
In the Glossary, status `agreed`?  → use it, spelled exactly as registered
In the Glossary, status `proposed`? → do not put it in code yet; it is unsettled
Not in the Glossary?                → STOP. Raise a Term Proposal
```

"Domain noun" means any word carrying meaning about the problem. Framework and
plumbing words (`client`, `parser`, `retry`) do not need registering. If unsure:
would getting this word wrong produce a *correct program computing the wrong
thing*? If yes, register it.

## Raising a Term Proposal

Interrupt the work. Do not defer it to the end of the Sub-step — by then the
name is in twelve places.

```markdown
🆕 **TERM PROPOSAL** — `settlement date`

**Means:** the date cash actually moves between accounts.
**Not:** `trade date`, the date the order executed. These differ by up to
three business days and confusing them misstates every daily cash balance.
**Needed for:** naming the date column in `fct_trade`.
**Alternatives considered:** `value date` (banking term, less common in
brokerage), `cash date` (unambiguous but nobody says it).

Agree, rename, or reject?
```

Then wait. Registering the term is Amino's call, not yours.

Once agreed, add the row to the Glossary with its definition, where it lives,
and status `agreed` — then use it.

## Collisions

Two words for one concept is the disease this rule exists to prevent, and it
arrives quietly: `net_revenue` in the warehouse, `netRev` in a helper, "revenue
(net)" on a chart. Three names, one concept, and a reader who cannot tell
whether they are the same number.

When you notice a collision, flag it and resolve it in that Sub-step. Retire the
loser — move it to the Retired section with a pointer to its replacement, so old
commits and old conversations stay readable.

## Distinctions we must not blur

Some pairs are dangerous precisely because they are near-synonyms in ordinary
speech but different quantities in the domain. These go in their own Glossary
section, defined *against each other* rather than separately.

State what each one is **not**. A definition that does not exclude its neighbour
has not done its job.

## Common mistakes

| Mistake | Fix |
|---|---|
| Coining a term in code and back-filling the Glossary | Propose first; the Glossary leads |
| Defining a term in isolation when it has a dangerous neighbour | Define it against the neighbour |
| Registering every word, including plumbing | Only terms whose misuse would silently produce wrong answers |
| Using a `proposed` term in an identifier | Wait for `agreed` — renaming code is the cost of jumping early |
| Quietly renaming an agreed term | Retire the old one explicitly; silent renames orphan the history |
