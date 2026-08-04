# Target State

**Where Veritas is going.** Written in Glossary terms only. This document changes
rarely and only by explicit agreement — it is the fixed point every Step is
measured against.

**Status:** **`agreed`** — 2026-08-03. The Domain Language it uses is `agreed`,
and the [data-availability check](data-availability.md) confirmed every source
this design assumes can actually be obtained key-free. Two consequences of that
check are folded in below: single bonds and options are out of scope, and market
prices are snapshotted into the repository rather than fetched live.

---

## Why this project exists

Veritas serves two audiences, and the design must satisfy both without
compromise:

1. **DataTalks.Club LLM Zoomcamp capstone** — must score full marks against the
   published rubric (see the [Zoomcamp criteria map](#zoomcamp-criteria-map)
   section).
2. **A credible minimal slice of the [full system](product-brief.md)** — a Senior
   Data Scientist role building AI-over-data-warehouse systems. It must extend
   into a full MVP for that role without reworking its core.

Where the two pull apart, the tension is recorded as an ADR, not resolved
silently.

---

## The problem

Ask an LLM a business question over a data warehouse and it will write plausible
SQL. Plausible is the problem. "What was our revenue last quarter?" has no single
correct answer at a brokerage: **Gross Revenue** and **Net Revenue** differ by
every Rebate paid to introducing partners, and a model that picks one silently
has produced a **correct program computing the wrong number**.

That failure is worse than an error, because it is confident, well-formatted, and
indistinguishable from a right answer. Repeated across a business, it is how a
**Shadow Metric** layer forms: every question invents its own definition of
revenue, and no two dashboards agree.

The failure is not a model capability problem. It is a **grounding** problem. The
definitions exist — they live in analysts' heads, in dbt models, in BI tools —
they are simply not available to the model at the moment it writes SQL.

## The system

Veritas is a natural-language analytics copilot over a brokerage warehouse whose
governing rule is:

> **The model never defines a metric. It may only select one from a certified
> Semantic Layer, and everything it generates is checked by code before it runs.**

Two consequences follow, and they are the whole design:

- **Retrieval is not a nicety, it is the correctness mechanism.** Retrieving the
  wrong Metric Definition *is* the wrong answer. This is why retrieval quality
  can be measured objectively here rather than by an LLM's opinion.
- **Governance is deterministic.** The Validation Gate is ordinary code, not a
  prompt asking the model to behave. Governance you can prove beats governance
  you request politely.

### Components

| Component | Responsibility | Built with |
|---|---|---|
| **Warehouse** | Brokerage star schema — Trades, Cash Movements, Positions and balances, plus Client/Account/Instrument/date dimensions and the dated `fct_fx_rate` and `fct_instrument_price` series. | DuckDB |
| **Semantic Layer** | Metric Definitions, Dimension Definitions, Join Paths, Ambiguous Terms. One YAML file per Semantic Entry, versioned. | YAML |
| **Ingestion** | Real FX Rates and Market Prices from key-free public APIs, snapshotted into the repository so a clone reproduces exactly; synthetic Trade/Cash/Position activity from a seeded simulator. | dlt |
| **Retrieval** | Question → the Semantic Entries needed to answer it. Hybrid text + vector, re-ranked. | minsearch + embeddings |
| **Orchestrator** | Rewrite → retrieve → ground → generate SQL → validate → execute → explain. | tool-calling LLM |
| **Validation Gate** | Deterministic pre-execution checks on the generated SQL's parse tree. | sqlglot |
| **App** | Ask questions, see the Grounded Answer with its SQL and Lineage, leave feedback. | Streamlit |
| **Observability** | Every question, Grounded Answer, Validation Gate outcome, cost, latency, and feedback. | Postgres + Grafana |
| **Evaluation** | Gold Question Set; retrieval measures; Execution Accuracy; LLM-as-judge. | notebooks + scripts |

> **Metrics vs. measures.** The Semantic Layer holds **metrics** — Certified
> Metrics like Gross Revenue, always about the brokerage. Evaluation and
> Observability produce **measures** of Veritas itself: Evaluation Measures (hit
> rate, MRR, Execution Accuracy) and Operational Measures (cost, latency,
> feedback). The two words are never used interchangeably. See the
> [System measures](../glossary.md#e-system-measures) section of the Glossary.

### Flow

```
question
   │
   ├─ 1. REWRITE ──────── resolve Ambiguous Terms against the Semantic Layer.
   │                      "revenue" is not answerable — ask which, or use the
   │                      one the question actually names.
   │
   ├─ 2. RETRIEVE ─────── hybrid search over Semantic Entries, re-ranked.
   │                      Returns Metric Definitions, Dimension Definitions,
   │                      and Join Paths — never raw table dumps.
   │
   ├─ 3. GROUND ───────── build the prompt from retrieved entries only.
   │                      Metrics not retrieved are not available.
   │
   ├─ 4. GENERATE ─────── SQL, composed from certified metric expressions.
   │
   ├─ 5. VALIDATE ─────── deterministic, on the parse tree:
   │                      · every metric expression traces to a Certified Metric
   │                      · no restricted column in the projection
   │                      · Access Profile predicate present
   │                      · scan bounded, statement read-only
   │                      fail → explain the violation, do not execute
   │
   ├─ 6. EXECUTE ──────── against the Warehouse
   │
   └─ 7. ANSWER ───────── Grounded Answer: result, SQL, Lineage (which entries,
                          which metric versions), Validation Gate outcome.
                          Logged, and open to feedback.
```

Steps 1, 2 and 5 are where the correctness lives. Step 4 is the part everyone
else builds.

---

## Non-goals

As load-bearing as the goals. Veritas deliberately does **not**:

- **Answer questions it cannot ground.** No Certified Metric, no answer. Refusing
  is a feature; a helpful guess is the exact failure being prevented.
- **Let the model define metrics.** Even correctly. A right answer by an
  uncertified route is still a Shadow Metric.
- **Validate with an LLM.** The Validation Gate is code. An LLM asked to check
  its own SQL shares its own blind spots.
- **Run on real client data.** Client activity is synthetic by construction —
  which is also what makes the access-control story demonstrable without risk.
- **Be a general text-to-SQL system.** Veritas is narrow on purpose: one
  warehouse, one certified vocabulary.
- **Browse the database.** "What columns are in `fct_trade`?", "what instrument
  types do we hold?", "show me ten rows" — none of these have an answer. Veritas
  is a metrics copilot, not a database browser: the schema is deliberately not in
  the retrieval corpus, and anyone wanting to explore it can open the Warehouse
  directly. Decided 2026-08-04; see [DEBT-006](../debt-ledger.md) for the
  alternatives that were rejected and why the most integrated one was the most
  dangerous.
- **Chase conversational polish.** Multi-turn memory, charting, and export are
  outside the slice.

---

## Zoomcamp criteria map

Each row is **one line item on the Zoomcamp grader's scorecard** — not a section
of this design. The rubric awards up to the **Max** points shown per criterion;
the right column is how Veritas earns them. Scoring is a design constraint here,
not an afterthought.

| Criterion | Max | How Veritas earns it |
|---|---|---|
| Problem description | 2 | The grader's first checkbox — *does the project explain what problem it solves and why it matters?* Veritas frames it as **silent metric ambiguity**: answering "revenue" with Gross when the business meant Net is a confident, well-formatted wrong number. The [`The problem`](#the-problem) section is that narrative, carried by the Gross-vs-Net worked example. |
| Retrieval flow | 2 | Semantic Layer knowledge base + LLM, both load-bearing in the flow. |
| Retrieval evaluation | 2 | Hit rate and MRR across ≥3 approaches — text, vector, hybrid, re-ranked. Ground truth is *derived*: the Semantic Entries a gold SQL touches are its relevant set. |
| LLM evaluation | 2 | Execution Accuracy across ≥2 prompts and ≥2 models, plus LLM-as-judge as a second lens. Objective primary signal. |
| Interface | 2 | The **App** — a Streamlit page showing answer, SQL, Lineage, and Validation Gate outcome. (The rubric's criterion is named *Interface*; our component is the `App`, renamed 2026-08-04 to stop one word carrying both.) |
| Ingestion pipeline | 2 | dlt pipelines for FX, market data, and the Semantic Layer index. |
| Monitoring | 2 | Feedback capture + Grafana dashboard, ≥5 charts — including Validation-Gate rejections by reason and metric-usage frequency. |
| Containerization | 2 | docker-compose: app, Postgres, Grafana. |
| Reproducibility | 2 | `uv.lock`, pinned Python, key-free public data sources **snapshotted into the repo** (so a clone reproduces even if a source disappears), seeded simulator, one-command bring-up. |
| Hybrid search | 1 | Text + vector, evaluated against each alone. |
| Document re-ranking | 1 | Re-ranker over hybrid candidates, evaluated. |
| Query rewriting | 1 | Ambiguous Term resolution — the core disambiguation step, not a bolt-on. |
| Cloud deployment | 2 | Out of the 2–3 week slice. Debt Ledger. |
| Extra credit | 3 | Deterministic Validation Gate, Access Profile enforcement, derived retrieval ground truth. |

**Rubric constraints:** the DataTalks.Club FAQ corpus may not be used (Veritas
does not touch it); reusing course-module code is explicitly allowed (`LLMZC`).

### What "credential-free" means

The reproducibility criterion drove three decisions — [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md),
[DEBT-002](../debt-ledger.md) and [DEBT-003](../debt-ledger.md) — so the rule it
rests on is worth stating rather than leaving implied. It is **not** "no
credentials at all", which would be impossible for a Large Language Model
project.

> **A credential the grader already has by virtue of taking the course is
> acceptable. A credential unique to this project is not.**

| Credential | Allowed? | Why |
|---|---|---|
| **Large Language Model API key** — OpenAI, Anthropic, Groq | ✅ yes | Inherent to the project category. Every Large Language Model Zoomcamp capstone needs one and the course itself assumes it, so a grader has one before they clone anything. A local model via Ollama is the zero-key fallback. |
| **Market-data vendor key** — Alpha Vantage, Tiingo, Polygon… | ❌ no | Incidental to this project. It would make a grader sign up for a service nobody else's capstone requires. This is what ruled out every supported price vendor and left Yahoo ([DEBT-002](../debt-ledger.md), [DEBT-003](../debt-ledger.md)). |
| **Cloud warehouse** — Google Cloud, Snowflake | ❌ no | Same objection, plus it bills someone. This is what ruled out BigQuery ([ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)). |
| **Service credentials inside `docker-compose`** — Postgres, Grafana | ✅ yes | Not obtained, declared. They are generated by the compose file, so bring-up needs no account anywhere. |
| **Cloud deployment credentials** | n/a | Cloud deployment is out of scope for the slice regardless. |

The distinction that matters is **obtained versus assumed**: a credential the
grader must go and get is friction Veritas imposed; one they already hold, or one
the compose file creates, is not.

**`README.md` must list every credential Veritas touches** — required by Amino on
2026-08-04, and a requirement of the reproducibility criterion rather than a
courtesy. A grader who discovers a needed key halfway through bring-up has had a
reproducibility failure, whatever the repository technically supports. The list is
short and must be complete:

| Credential | What the README must say |
|---|---|
| **Large Language Model API key** | **Required.** Which providers work, which environment variable carries it, and that no data source needs a key. State the Ollama fallback for a reviewer who has no key at all. |
| **Postgres** — user, password, database | Generated by `docker-compose`; no account anywhere. Say where the values are set so a reviewer can change them. |
| **Grafana** — admin login | Same: `docker-compose` sets it. Say what the default is, since a reviewer will need it to open the dashboard. |
| **Data sources** | **None.** Frankfurter, Yahoo, NASDAQ Trader and the Securities and Exchange Commission are all key-free, and the snapshots in `data/snapshots/` mean a clone reproduces even offline. Worth stating positively — it is a deliberate result, not an absence. |

Two Debt Ledger entries already fire on the README being written
([DEBT-002](../debt-ledger.md) on the reproducibility claim,
[DEBT-008](../debt-ledger.md) on the access-control claim), so this list belongs
in the same pass as both.

**This reading is Claude's and has not been checked against the rubric text**,
which is not in the repository. If the Large Language Model key is *not* in fact
assumed by the graders, the fallback is an Ollama-only default path — worth
knowing before the Orchestrator Step rather than after.

---

## Extension path to the full proposal

The slice is shaped so the MVP for `final_proposal_target.md` is addition, not
rewrite. Each of these lands against an existing seam:

| Full-MVP capability | Seam it plugs into |
|---|---|
| BigQuery instead of DuckDB | Warehouse is behind one adapter; SQL is generated via sqlglot, which retargets dialects. |
| dbt semantic layer as the source of Metric Definitions | Semantic Entries are already YAML with the same shape. |
| Real row/column-level security | Access Profile already threads through the Validation Gate; swap enforcement to warehouse-native policy tags. |
| Query-cost governance | Cost check already exists; swap DuckDB's estimate for BigQuery dry-run bytes-billed. |
| Multi-agent reconciliation and anomaly detection | Grounded Answer + Lineage is the interface a reconciliation agent consumes. |
| Entity resolution across sources | Client/Account distinction is already modelled as the place duplicates would surface. |

The deliberate bet: **the Semantic Layer and the Validation Gate are the durable
parts.** Warehouse engine, model, and UI are all replaceable; those two are the
thing worth having built.
