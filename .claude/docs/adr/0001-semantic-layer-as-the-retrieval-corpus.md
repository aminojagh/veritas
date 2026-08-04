# ADR-0001 — The Semantic Layer is the retrieval corpus

- **Status:** accepted
- **Date:** 2026-08-03
- **Decided in:** Step 001, Sub-step 1.3

## Context

Veritas is a retrieval-augmented system over a warehouse, so something must be
retrieved. What that something *is* has several defensible answers, and the
choice determines what the rest of the system can guarantee.

The default answer in the text-to-SQL literature is **schema**: table and column
names, Data Definition Language (DDL), sometimes sample rows. The default answer
in the Zoomcamp reference project is **documents**: Frequently Asked Questions
(FAQ) prose. Veritas retrieves neither.

The pressure that forces the choice is the problem statement itself. The failure
being prevented is not that the model cannot write SQL — it writes SQL fine. It
is that "what was our revenue last quarter?" has two correct answers, Gross
Revenue and Net Revenue, and picking one silently produces a **correct program
computing the wrong number**. Schema retrieval cannot address that, and the
reason is worth stating precisely: `fct_trade` carries `commission`, `rebate` and
`fee`, so *both* metrics are derivable from a schema that is complete, accurate,
and entirely silent on which one the business means. The ambiguity does not live
in the schema. Handing the model a better description of the tables is answering
a question nobody asked.

What was known at the time: the Domain Language was `agreed`, including
`Semantic Layer`, `Semantic Entry`, `Metric Definition`, `Certified Metric` and
`Shadow Metric`, and the data-availability check had confirmed the warehouse
could be built from real Foreign Exchange (FX) Rates and Market Prices. What was
not known: how many Semantic Entries the Gold Question Set would need, or which
retrieval approach would win — both deliberately left to later Steps.

## Decision

Retrieval operates over **Semantic Entries** in the Semantic Layer — Metric
Definitions, Dimension Definitions, Join Paths and Ambiguous Terms — and never
over raw warehouse schema or free-text documentation. Grounding builds the prompt
from retrieved entries only: a Certified Metric that was not retrieved is not
available to the model.

## Alternatives considered

| Option | Why not |
|---|---|
| **Schema retrieval** — Data Definition Language (DDL), column names, sample rows, as in Spider/BIRD-style text-to-SQL | The best-studied approach, needs no hand-authored corpus, and never drifts from the warehouse because it *is* the warehouse. Rejected because it cannot represent the one fact that matters: that "revenue" has two certified meanings. Schema describes what *can* be computed and is silent on what *should* be. It would also leave retrieval evaluation without meaningful ground truth — "did it fetch the right tables" is nearly always yes, and tells us nothing about whether the answer was right. |
| **Free-text documentation** — a metrics wiki, retrieved as prose | Cheapest to author, and it matches how metric definitions actually exist in most companies. Rejected because prose cannot be executed or checked. The Validation Gate must trace a generated metric expression back to a machine-readable certified expression; a paragraph reading "net revenue is gross minus rebates" gives the model a hint and gives the Gate nothing. It also reintroduces exactly the drift being prevented, since the prose and the real SQL can disagree with no way to detect it. |
| **No retrieval — put the whole Semantic Layer in the prompt** | Genuinely viable at the slice's scale: tens of metrics fit in context comfortably, and it removes an entire failure mode. Rejected on two grounds. It forfeits the rubric's retrieval-flow, retrieval-evaluation, hybrid-search and re-ranking criteria (6 points), and it does not extend — the full Minimum Viable Product (MVP)'s dbt semantic layer has hundreds of metrics. It also destroys the ability to *measure* whether the right definition was found, which is the project's central claim. Worth keeping as a **baseline** to evaluate retrieval against, which is where it will reappear. |
| **Fine-tune a model on the metric definitions** | Bakes the definitions in and removes retrieval latency entirely. Rejected on three grounds, all internal to this decision: definitions change and a fine-tune is a redeploy; it cannot produce Lineage, so no answer is auditable; and the certified set stops being inspectable, which is the property the Validation Gate depends on. The [product brief](../design/product-brief.md) is *adjacent but not authority* here — it lists "Fine-tuning on historical/labelled data" as "Out of scope for the slice; noted, not built", which is about fine-tuning as a modelling technique on business data, not about using it to carry metric definitions. The reasons above stand on their own. |

## Consequences

**What this buys us.**

- **Retrieval becomes a correctness mechanism, not a relevance mechanism.**
  Retrieving the wrong Metric Definition *is* the wrong answer. This is why hit
  rate and Mean Reciprocal Rank (MRR) are meaningful measures here rather than
  proxies for user satisfaction.
- **Retrieval ground truth is derived, not labelled.** The Semantic Entries a
  gold SQL touches are its relevant set. No hand-labelling and no Large Language
  Model (LLM) judge is needed for the primary retrieval signal.
- **The Validation Gate has something to check against.** Certified-metrics-only
  is enforceable only because the certified set is an enumerable corpus of
  machine-readable expressions. ADR-0003 rests on this one.
- **Lineage is nearly free** — the retrieved entries and their versions *are* the
  audit record.
- **The extension path is addition.** dbt semantic-layer models have the same
  shape (name, expression, grain, filters), so changing where Semantic Entries
  come from does not move the seam.

**What this costs us.** Each cost is classified — *accepted*, *debt*, or
*extension* — so none of them sits here as a fact nobody acts on.

- **The Semantic Layer is a second source of truth, and it can drift.** A Metric
  Definition whose SQL expression references a renamed column is a broken system
  with no compile-time error anywhere. Nothing in the slice detects this; the
  Validation Gate will pass such a query and execution will fail. This is the
  sharpest cost of the decision.
  → **Extension: [EXT-002](../extension-register.md#ext-002--semantic-layer-drift-detection).**
  A drift check that parses every Metric Definition's expression with sqlglot and
  asserts each referenced column exists in the Warehouse. Not debt: the slice has
  one author and one schema authored once, so drift has no opportunity to occur.
  The full Minimum Viable Product (MVP), with real migrations, needs it.
- **Coverage is a hard ceiling.** A question needing an uncertified metric is
  unanswerable by construction, so the honest failure mode of Veritas is "I
  cannot answer that", far more often than a general text-to-SQL system would say
  it.
  → **Accepted — this is the intent, not a defect.** Refusing is the feature; a
  helpful guess is the exact failure being prevented. What is *missing* is that
  the slice refuses **silently and forgetfully**: a refusal teaches no one
  anything, so the certified vocabulary never learns where its own edges are.
  → **Extension: [EXT-004](../extension-register.md#ext-004--coverage-miss-capture)**
  captures and clusters the misses into an authoring backlog;
  **[EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks)**
  keeps the growing metric set internally consistent as that backlog is worked.
  See [How the metric set stays coherent](#how-the-metric-set-stays-coherent).
- **Ad-hoc exploration is out.** "What columns are in `fct_trade`?" has no answer,
  because the schema is not in the corpus.
  → **Accepted permanently — decided 2026-08-04, [DEBT-006](../debt-ledger.md).**
  Veritas is a metrics copilot, not a database browser. Both alternatives were
  rejected; the more integrated one — schema as its own Semantic Entry type — is
  the more dangerous, because once schema sits in the same corpus as Metric
  Definitions the model can compose them and "revenue" gets computed from
  `commission` directly. That is the Shadow Metric failure arriving through the
  front door. Recorded as a [non-goal](../design/target-state.md#non-goals).
- **Authoring cost scales with the warehouse.** Every new metric is a hand-written
  YAML file plus a corpus change, not a schema migration. At tens of metrics this
  is fine; at the hundreds a real brokerage warehouse needs, hand-authoring is the
  bottleneck.
  → **Extension: [EXT-003](../extension-register.md#ext-003--metric-authoring-at-scale).**
  Generation from an existing dbt semantic layer, incremental re-indexing, and
  draft definitions proposed from coverage misses — never auto-certified. Not
  debt: at tens of metrics, hand-authored YAML is the *better* choice, being
  inspectable, diffable and reviewable in a pull request.

## How the metric set stays coherent

Raised by Amino on 2026-08-03 and **decided 2026-08-04.** The requirement: detect
when a question cannot be grounded, record it, and use those records to grow the
certified vocabulary *continuously but coherently* — so the metric set never
becomes a pile of one-off definitions that contradict each other.

The proposal was a **knowledge graph** of Metric Definitions. It splits into two
problems, and separating them is most of the answer, because only one is a
data-structure question:

1. **Capture** — logging ungroundable questions and clustering them into an
   authoring backlog. Observability work; needs no graph at all.
   → [EXT-004](../extension-register.md#ext-004--coverage-miss-capture).
2. **Coherence** — the constraints that must hold across a growing set: no two
   metrics with the same expression under different names, no undeclared
   derivation, no orphaned dependency, no Ambiguous Term pointing at a metric
   that does not exist.
   → [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks).

**A graph database was rejected**, and the coherence work was kept. Three
reasons. The corpus is hundreds of entries rather than millions, so any structure
works and the scale argument for a graph store does not apply. A separate store
would be a **third** representation of metrics, which is the wrong direction when
the sharpest cost this ADR already carries is having two
([EXT-002](../extension-register.md#ext-002--semantic-layer-drift-detection)).
And sqlglot already extracts each metric's column dependencies from its SQL
expression for free, which removes the hand-declaration that would otherwise be
the thing that drifts.

What was kept is the part that carried the value: **typed relationships plus
automated checks.** `derives_from` and `disambiguates` are declared in the
existing YAML; column dependencies are derived by parsing. A graph is built in
memory at build time and the coherence rules run over it as ordinary code. The
files stay the single source of truth, git supplies review on every metric
change, and the checks are unit-testable. Expression equivalence — the inference
that actually matters — is a parse-tree normalisation, not a description-logic
problem.

What would overturn this: relationships turning out more open-ended than a few
fixed edge types, or a semantic layer orders of magnitude larger than assumed.
Either would earn a property graph and would deserve its own ADR.

## Related

- ADR-0003 — the Validation Gate can enforce certified-metrics-only *only*
  because this decision makes the certified set an enumerable, machine-readable
  corpus.
- Glossary: `Semantic Layer`, `Semantic Entry`, `Metric Definition`,
  `Certified Metric`, `Shadow Metric`, `Ambiguous Term`, `Dimension Definition`,
  `Join Path`, `Grounding`, `Lineage` — all already `agreed`; this decision
  introduced no new terms.
- [Target State](../design/target-state.md) — "the deliberate bet: the Semantic
  Layer and the Validation Gate are the durable parts".
