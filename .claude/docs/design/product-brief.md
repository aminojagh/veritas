# Product Brief — the full system Veritas is a slice of

**Why this document exists.** Veritas is a deliberately minimal slice of a
larger system. That larger system was first described to us as a job
specification; this brief is its durable, development-facing rewrite — the same
intent stated in our own [Glossary](../glossary.md) terms, as a system to build
rather than a role to fill. It is the context [`target-state.md`](target-state.md)
is measured against for the *full-MVP* direction, the same way the Zoomcamp
rubric is the context it is measured against for the capstone.

Once this brief, the Glossary, and the Target State hold everything material, the
original job description is redundant and can be removed from the repo.

**Provenance:** distilled from a Senior Data Scientist specification at a
multi-asset brokerage — "AI on top of the enterprise data warehouse".
Kept here as system context, not as recruitment copy.

---

## The organisation and its data

A global wealth-tech brokerage. Clients hold **multi-currency Accounts** giving
single-account access to many **Instrument** classes — equities, ETFs, bonds,
futures, options, swaps, funds, and currency pairs. The analytical estate is an
enterprise data warehouse (BigQuery in the real system); the business runs on it.

The domain nouns this generates — Client, Account, Instrument, Trade, Cash
Movement, Position, Gross vs Net Revenue, and the rest — are registered in the
[Glossary](../glossary.md). They are not incidental to Veritas; they *are* the
subject the system reasons about.

## The mission

Build an **AI-ready analytical environment on top of the warehouse**, where AI
can *understand, query, validate, reconcile, and reason on* structured business
data **reliably and under control**. The emphasis is practical implementation,
not research: AI working with analytical and financial data *inside the
warehouse ecosystem* — not AI for the whole company.

The full system's capabilities, as originally enumerated:

- Natural-language analytics over warehouse data
- AI-driven reconciliation and validation
- Analytical copilots
- Data-quality automation
- Business-metric validation
- Automated anomaly detection
- Multi-agent analytical workflows

Veritas implements the **first** of these end-to-end, and is shaped so the rest
are additions rather than rewrites.

## What the full system must do

Five build goals, reframed from the specification's responsibilities:

1. **An AI-ready warehouse.** Move business logic *into* the warehouse. Improve
   semantic consistency, define reusable metrics and dimensions, and guarantee
   analytical correctness across systems — data structures both humans and AI can
   consume without re-deriving meaning.
2. **Designed AI ↔ warehouse interaction.** Define *how* AI touches the data:
   prompts, semantic context, retrieval logic, validation, and workflows — so the
   AI produces correct, trusted answers, tested against real usage rather than in
   theory.
3. **LLMs and AI agents, hands-on.** Work with models (Claude, OpenAI, and
   similar); test, evaluate, and improve their outputs; design workflows where
   several agents collaborate on an analytical problem.
4. **Metric correctness.** Ensure the AI interprets business metrics and
   financial logic correctly — the exact distinctions between **revenue, cost,
   gross revenue, net revenue, trading volume, cash movement, accounting
   movement, balances, and position changes**. (These are the Glossary's
   [distinctions we must not blur](../glossary.md#c-distinctions-we-must-not-blur).)
5. **Governance and reliability.** Keep AI's interaction with data controlled and
   secure: validation mechanisms, prevention of sensitive-data exposure, and
   trustworthy AI-generated output.

## Scope areas

| Area | What the full system does |
|---|---|
| **Data platform** | Clean, reusable analytical layers in BigQuery; business logic moved out of BI and into the warehouse; metrics, dimensions, and semantic consistency defined once. |
| **AI interaction** | Reliable AI ↔ data interaction; schemas and instructions designed so the AI produces correct output; refined against real usage. |
| **Access & governance** | Access control at the **data layer, not the BI layer** — row/column-level security, role- and attribute-based access; consistent behaviour across BI, AI, and internal tools; metric reconciliation across sources. |
| **Automation** | Manual data workflows replaced by AI-driven processes; agents for reporting, validation, and internal analytics. |

## The three failures to prevent

The specification names three, and they map one-to-one onto Veritas's design —
which is why this slice is a credible proof of the whole:

| Must prevent | Veritas's answer |
|---|---|
| **Sensitive-data leakage** | Access Profile threaded through a deterministic Validation Gate; no restricted column reaches a projection. |
| **A shadow-metric layer** | The governing rule — the model may only compute a **Certified Metric**; a Shadow Metric is rejected before execution. |
| **Uncontrolled query cost** | A cost bound is a Validation Gate check; in the full system it becomes a BigQuery dry-run bytes-billed limit. |

## Capability and tooling signals

**Core:** strong SQL and analytical data modelling; analytical databases
(BigQuery / Snowflake / Databricks / Redshift); practical LLM use; AI-driven or
agent-based workflows; ML fundamentals.

**Adjacent (nice-to-have), and where each lands in Veritas's extension path:**

| Signal | Seam it plugs into |
|---|---|
| dbt / semantic layers | The Semantic Layer — Semantic Entries are already YAML of the same shape. |
| RAG / vector databases | Retrieval is already hybrid text + vector over Semantic Entries. |
| Entity resolution / record matching | The Client vs Account distinction is where duplicates surface. |
| BigQuery optimization | The Warehouse adapter seam; sqlglot retargets the dialect. |
| Data governance / fine-grained access | Access Profile + Validation Gate. |
| Classification, probability scoring, anomaly detection | Multi-agent extension consuming Grounded Answers + Lineage. |
| Fine-tuning on historical/labelled data | Out of scope for the slice; noted, not built. |

See the full mapping in
[`target-state.md` → Extension path](target-state.md).

## The bet

Veritas builds the two parts worth having built first — the **Semantic Layer**
and the **Validation Gate** — because warehouse engine, model, and UI are all
replaceable, and those two are not. Everything above is reached by addition
against an existing seam, never by repainting.
