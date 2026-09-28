# Redesign Roadmap

The route from the finished capstone to a new Target State, as decisions taken one
session each, in dependency order. **It decides; it does not build.** It is deleted
when R8 writes the first new Step plan.

**Resume rule:** take the first row whose status is not `done` and whose
dependencies are all `done`. Each item ends by updating its row here, and the
Resume-here block in [Current State](../design/current-state.md) points at this file
until R8.

## Rulings this roadmap starts from — Amino, 2026-09-28

- **One mode.** Delivery Mode is removed. These parts of it become permanent:
  1. No new check scripts in `.claude/scripts/`. The existing ones are replaced by
     `tests/` as soon as possible.
  2. Short plans and reviews, written from the templates.
  3. Docstrings never say why something was built the way it is. That goes in an
     ADR, the plan, or nowhere.
  4. No links from code into `plan/` or `reviews/`.
- **Test-driven development stays.** Behaviour is claimed only in `tests/`.
- **Work continues on `main`.** The capstone review is done, and reviewers see the
  commit they were given.
- **New goal: a domain-agnostic "chat with your data" system.** It is prototyped on
  one domain: finance, or another with cleaner public data.
- **The core design is re-opened, independent of stack.** One idea to test is a
  conceptual model of the data at several levels of abstraction, with defined moves
  between levels. The model sees only those definitions, never records.
- **Skills goal, applied only after the design is decided:**
  - CI/CD, Docker and Kubernetes, preferably on Amazon Web Services
  - the relevant Amazon Web Services tools
  - agentic systems
  - API development and async
  - LLM evaluation
- **Removed regardless of design:**
  - bulky docstrings
  - verbose tests
  - documents that can be derived
  - history, except ADRs written as time-invariant decisions
  - everything tied to the old Target State, including its debt and extension
    records
- **What remains:**
  - the domain language
  - Target State and Current State
  - the Step loop that closes the gap between them
  - open and partly open Ledger and Register entries

## Items

| ID | Decision or work | Depends on | Produces | Status |
|---|---|---|---|---|
| R0 | One mode, and the new document model | — | `CLAUDE.md`, `.claude/skills/*` | done |
| R1 | Purge history and derivable documents | R0 | a `.claude/docs/` tree holding only what R0 keeps | open |
| R2 | Frame the problem | R0 | draft purpose and scope in `design/target-state-next.md` | open |
| R3 | Research prior art | R2 | research note, deleted once R4's ADRs cite what they use | open |
| R4 | Core design | R2, R3 | ADRs, draft components and flow, proposed Glossary terms | open |
| R5 | Prototype domain | R4 | ADR, domain section of the Glossary | open |
| R6 | Stack, mapped to the skills goal | R4, R5 | ADRs, the *Built with* column; `target-state-next.md` becomes the Target State, status `agreed` | open |
| R7 | What survives | R6 | pruned Ledger and Register, Current State rewritten as the gap | open |
| R8 | Plan Step 010 | R7 | `plan/step-010-*.md`; this file is deleted | open |

R1 and R2 are independent of each other. R1 goes first because every later session
starts cold, and the resume path is what R1 shrinks.

### R0 — One mode, and the new document model

Delete the Delivery Mode section and fold the four kept rules and test-driven
development into `CLAUDE.md`'s permanent sections. The plan and review templates in
`planning-a-step` and `closing-a-substep` become the only templates.
`tests/test_delivery_mode.py` becomes `tests/test_framework.py`, a permanent rules test:
- the set of check scripts may only shrink
- links from code into `plan/` and `reviews/` go to zero once R1 cuts them

**Rulings R0 took — all four approved by Amino, 2026-09-28.**

1. **Plans and reviews live only while their Step is active.** They are deleted
   when the Step closes, and git keeps them.
2. **A dated measurement lives in the commit message of the Sub-step that took it.**
   Today the rule puts it in the Step Review, which rule 1 deletes. A commit message
   is dated, carries the command, and is already where history lives. Documents
   name the command that reproduces the figure.
3. **An ADR states the decision as it stands now.** Its rejected alternatives may
   include a former approach and why it was dropped. There are no dated amendments
   and no chains of superseded records. `writing-an-adr` is rewritten to match.
4. **A paid, accepted or moved entry is deleted from the Ledger and the Register**,
   and the Glossary's *Retired terms* section goes with them. Identifiers are still
   never reused. The next free number is the only thing kept.

### R1 — Purge history and derivable documents

- **Delete:**
  - `reviews/` and the closed plans `step-000`–`step-009`
  - the Ledger entries rule 4 removes
  - `docs/decisions.md`: its reasons that are still true move into ADRs first
  - the dated amendments inside the Glossary, ADRs and Target State, and each
    ADR's date, Step and supersede lines
  - the Glossary's *Retired terms* section, and the Register entries rule 4 removes
  - the index READMEs of `plan/`, `reviews/` and `adr/`: each is derivable
- **Rewrite** the Ledger's and Register's headers and entry templates to R0's
  rules: open entries only, a next free number in place of counts, no link to a
  review.
- **Rewrite** Current State as reality only: short, pointing at code rather than
  describing it.
- **Cut every link from code to a deleted anchor.** This is a mechanical pass that
  only edits docstrings. They carry links to more than twenty closed Ledger entries,
  and to `plan/` and `reviews/` from the files `tests/test_framework.py` lists;
  that table ends empty.
- **Trim `README.md`** to what is true. It is rewritten after the new design is
  built.
- **Move the framework checks into `tests/`.** These are `verify_framework.py` and
  `check_language.py`, and nothing in the redesign changes them.

**Not in R1:** slimming the product code's docstrings and tests, and porting the
product checks. Both would spend effort on code the redesign may delete. R7 scopes
them to what survives.

### R2 — Frame the problem

These questions come before any research, so the research knows what it is for:

- Who asks the questions, and who connects Veritas to a new database?
- What does connecting a new domain cost? That cost is what domain-agnostic
  measurably means.
- **What does an answer promise?** The current thesis is to refuse rather than
  guess, and [DEBT-006](../debt-ledger.md#debt-006--no-ad-hoc-exploration--accepted-permanently)
  says *"Veritas is a metrics copilot, not a database browser."* "General and
  flexible" pulls the other way. R2 decides where Veritas sits between the two.
- What is out of scope, and what number says the prototype works?
- Does the [Product Brief](../design/product-brief.md) survive, get rewritten, or
  get deleted?

### R3 — Research prior art

Concepts only; no products chosen here. These are leads to check, not findings:

- the three-schema architecture: conceptual, logical, physical
- ontology-based data access: questions posed over an ontology and rewritten to SQL
  through mappings
- semantic layers and metric stores used as the interface for an LLM
- published evidence on whether a knowledge graph or semantic layer raises
  text-to-SQL accuracy
- text-to-SQL methods, such as schema linking, decomposition and self-correction,
  and their benchmarks
- building the conceptual model automatically from schema and profiling

**One problem the "definitions only, never records" idea must answer:** a filter
needs real values (`'UK'` or `'United Kingdom'`?). The options are a value index or a
lookup tool that the model calls without seeing rows.

### R4 — Core design

- What are the levels of abstraction, how is each represented, and what defines a
  move between levels?
- **Does the model write SQL guided by concepts, or a query in the concept language
  that deterministic code compiles to SQL?** The second makes validation largely
  true by construction. This fork shapes everything after it.
- Which parts of the Semantic Layer, Validation Gate and Ambiguous Term handling
  generalise, and which were finance-specific?
- Who authors the conceptual model for a new domain: a person, an LLM with a person
  checking, or a machine alone?

The finance domain serves as the worked example, because it is known ground. The
skills goal is deliberately not an input.

### R5 — Prototype domain

- **Criteria:**
  - public, clean and licensed
  - enough levels of abstraction to exercise R4
  - joins
  - real ambiguity
- **Open question:** proving domain-agnosticism may need two domains, not one.
  Keeping finance as one of them costs nothing that already exists.

### R6 — Stack, mapped to the skills goal

Each skill lands on a component where it is the right tool, and is never forced
onto one. There is one ADR per choice that is expensive to reverse.

**Ruling R6 needs:** a monthly ceiling on Amazon Web Services cost.

### R7 — What survives

Classify every existing module, test, check script, Ledger entry and Register entry
as keep, adapt or delete, against the new Target State.

- **Old-design records** are deleted.
- **[DEBT-023](../debt-ledger.md#debt-023--two-proving-systems-run-side-by-side)'s
  port** covers only the checks whose component survives. The rest are deleted with
  their component.
- **[DEBT-024](../debt-ledger.md#debt-024--source-and-step-documents-carry-prose-delivery-mode-would-not-admit)'s
  slimming** applies to surviving code only.
