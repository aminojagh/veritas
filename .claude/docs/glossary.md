# Glossary — Ubiquitous Language

The single source of truth for vocabulary in this project. Every domain noun
used in a document, a plan, or a **code identifier** must appear here, spelled
exactly as registered.

**Adding a term:** see the `registering-language` skill. Never coin a term
silently — propose it, agree on it, then register it.

**Status values:** `agreed` (settled, use freely) · `proposed` (awaiting
Amino's approval, do not put in code yet) · `retired` (superseded — kept so the
old name is recognisable in history, with a pointer to its replacement).

---

## Domain Language

> **All `agreed`** — approved by Amino on 2026-07-23, including the System
> measures (`Evaluation Measure`, `Operational Measure`) added later that day.
> The Section C distinctions were ruled on explicitly, and both `Metric
> Definition` and `Certified Metric` are kept as genuinely distinct terms
> (artifact vs. status). Use freely, in prose and in code.

### A. The system

What Veritas is made of.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Semantic Layer** | The certified registry of Metric Definitions, Dimension Definitions, Join Paths and Ambiguous Terms. Veritas's knowledge base — the thing retrieval searches. | `semantic/` | agreed |
| **Semantic Entry** | One retrievable document in the Semantic Layer. The unit of retrieval and the unit of relevance in retrieval evaluation. | `semantic/` | agreed |
| **Metric Definition** | A named, versioned, certified computation over the warehouse — its SQL expression, grain, filters, units, and the aliases people use for it. | `semantic/metrics/` | agreed |
| **Certified Metric** | A metric that exists in the Semantic Layer. The only kind Veritas is permitted to compute. | `semantic/metrics/` | agreed |
| **Shadow Metric** | A metric computed inline in a query instead of drawn from the Semantic Layer. The failure mode Veritas exists to prevent. | — (an anti-pattern) | agreed |
| **Ambiguous Term** | A word users say that maps to two or more Certified Metrics and therefore has no single correct answer. Not a metric — an instruction to disambiguate before generating SQL. | `semantic/ambiguous/` | agreed |
| **Dimension Definition** | A certified axis for *slicing* a metric — the answer to "by what?". Names the column, its grain, and its allowed values, so "by region" always means the same column with the same buckets. Examples: **by date** (`trade_date`, daily), **by region** (`client_region` — EU · UK · APAC), **by instrument type** (equity · bond · future · option). "Net Revenue **by region** last quarter" applies the region Dimension Definition to the Net Revenue metric. | `semantic/dimensions/` | agreed |
| **Join Path** | A certified route between two warehouse tables, so the model never invents a join. | `semantic/joins/` | agreed |
| **Grounding** | The step where retrieved Semantic Entries constrain SQL generation. Ungrounded generation is forbidden, not merely discouraged. | `veritas/grounding/` | agreed |
| **Validation Gate** | Deterministic, non-LLM checks a query must pass before execution: certified-metrics-only, no restricted columns, access policy applied, cost bounded, read-only. | `veritas/validation/` | agreed |
| **Access Profile** | The identity Veritas runs a question as — role and permitted region. Determines which rows and columns the Validation Gate allows. | `veritas/validation/` | agreed |
| **Grounded Answer** | The response object: the answer, the SQL, the Lineage, and the Validation Gate outcome. Veritas never returns a bare number. | `veritas/` | agreed |
| **Lineage** | The record of which Semantic Entries and which Metric Definition versions produced a Grounded Answer. What makes an answer auditable. | `veritas/` | agreed |
| **Gold Question Set** | The evaluation corpus: question, gold SQL, gold result, and the Semantic Entries the gold SQL touches. | `data/gold/` | agreed |
| **Execution Accuracy** | Share of generated queries whose result set matches the gold result. The primary correctness measure — objective, unlike a judge's opinion. | `veritas/evaluation/` | agreed |
| **Reporting Currency** | The single currency a Grounded Answer is expressed in. Every monetary metric must state one. | `semantic/metrics/` | agreed |

### B. The warehouse

What the data describes. A brokerage: clients hold accounts, accounts trade
instruments, trades move cash and change positions.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Instrument** | A tradable asset — equity, ETF, bond, future, option, or currency pair. | `dim_instrument` | agreed |
| **Client** | The legal owner of one or more Accounts. The entity a region or segment attaches to. | `dim_client` | agreed |
| **Account** | The container trades and cash sit in. Has exactly one Client and one or more currency balances. | `dim_account` | agreed |
| **Trade** | One executed order: an Account buys or sells a quantity of an Instrument at a price, on a Trade Date, settling on a Settlement Date. | `fct_trade` | agreed |
| **Traded Notional** | Σ(quantity × price) converted to the Reporting Currency. The monetary size of trading activity. | `semantic/metrics/` | agreed |
| **Trade Count** | Number of Trades. Deliberately separate from Traded Notional — they answer different questions. | `semantic/metrics/` | agreed |
| **Commission** | What the broker charges the Client for executing a Trade. Broker income. | `fct_trade` | agreed |
| **Fee** | A third-party charge passed through to the Client — exchange, clearing, regulatory. Collected by the broker but not earned by it. | `fct_trade` | agreed |
| **Rebate** | Value returned to a Client or introducing partner out of Commission already charged. Reduces what the broker keeps. | `fct_trade` | agreed |
| **Gross Revenue** | Σ(Commission) before any Rebate or pass-through Fee is deducted. | `semantic/metrics/` | agreed |
| **Net Revenue** | Gross Revenue − Rebate − pass-through Fee. What the broker actually keeps. | `semantic/metrics/` | agreed |
| **Cash Movement** | Money actually entering or leaving an Account on a given date — deposits, withdrawals, settlement, fee charges. | `fct_cash_movement` | agreed |
| **Accounting Movement** | A ledger entry recognising economic value on the date it was *earned*, whether or not cash moved. | `fct_accounting_movement` | agreed |
| **Cash Balance** | Money held in an Account in one currency at a point in time. Cash only. | `fct_balance_snapshot` | agreed |
| **Account Value** | Cash Balance plus all Positions marked to market, in the Reporting Currency. | `semantic/metrics/` | agreed |
| **Position** | Quantity of one Instrument held by one Account at a point in time. | `fct_position_snapshot` | agreed |
| **Position Change** | Change in a Position between two points in time, from any cause — a Trade, a transfer, or a corporate action. | `semantic/metrics/` | agreed |
| **Realised P&L** | Profit or loss locked in by closing a Position. | `semantic/metrics/` | agreed |
| **Unrealised P&L** | Profit or loss on a Position still held, at current market price. Moves with the market; nothing has been banked. | `semantic/metrics/` | agreed |
| **FX Rate** | Real ECB reference rate between two currencies on a date. Sourced from the public Frankfurter API. | `dim_fx_rate` | agreed |

### C. Distinctions we must not blur

These pairs are near-synonyms in ordinary speech and different quantities in the
domain. Confusing one for another produces a **correct program computing the
wrong number** — the failure that is hardest to notice and most expensive to
trust. Every pair here is drawn from the job specification's own list.

| Not this | …but this | Why it matters |
|---|---|---|
| **Gross Revenue** | **Net Revenue** | Rebates to introducing partners can be a large share of Commission. Reporting gross as net overstates what the business keeps. |
| **Cash Movement** | **Accounting Movement** | Commission is *earned* on Trade Date and *collected* on Settlement Date. In any period that straddles a settlement cycle the two disagree, and both are correct answers to different questions. |
| **Cash Balance** | **Account Value** | A Client with €0 cash and €2m of equities has a Cash Balance of zero. Answering "how much does this client have" with Cash Balance is not wrong arithmetic — it is the wrong question answered confidently. |
| **Trade Date** | **Settlement Date** | Which one a period filter uses shifts revenue across period boundaries. Also selects the FX Rate, so it moves the number twice. |
| **Position Change** | **Trade** | Positions also change through transfers and corporate actions. Deriving position change from trades alone silently loses those. |
| **Realised P&L** | **Unrealised P&L** | One is banked, one is a market opinion. Summing them without saying so mixes fact with mark-to-market. |
| **Traded Notional** | **Trade Count** | "Volume" means either. One large trade and a thousand small ones are opposite answers to "was this a busy month". |
| **Client** | **Account** | One Client may hold many Accounts. Counting Accounts and calling it clients inflates every per-client figure. |

### D. Ambiguous Terms

Words users genuinely say that are **not** metrics. Veritas must resolve them
before generating SQL — never guess silently.

| User says | Could mean | Resolution |
|---|---|---|
| "revenue" | Gross Revenue · Net Revenue | Ask, unless the question names one |
| "volume" | Traded Notional · Trade Count | Ask |
| "balance" | Cash Balance · Account Value | Ask |
| "P&L" | Realised · Unrealised · both | Ask |
| "how much does X have" | Cash Balance · Account Value | Ask |

### E. System measures

> **`agreed`** — approved 2026-07-23, together with the rest of the Domain
> Language.

**Metric** in Veritas means one thing only: a **business** metric — a Certified
Metric about the brokerage, like Gross Revenue or Traded Notional. The measures of
how well Veritas *itself* performs are never called metrics; they are
**measures**. Keeping the two words apart is what stops the collision this
Glossary exists to prevent — a chart labelled "metrics" mixing Gross Revenue with
hit-rate.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Evaluation Measure** | A measure of how well Veritas answers, computed over the Gold Question Set: hit rate and MRR for Retrieval; Execution Accuracy and LLM-as-judge agreement for generation. These are the Zoomcamp evaluation measures. | `veritas/evaluation/` | agreed |
| **Operational Measure** | A runtime measure logged per question and shown on the Grafana dashboard: cost, latency, Validation Gate outcome, and user feedback. | `veritas/observability/` | agreed |

Execution Accuracy is registered separately in
[Section A. The system](#a-the-system) because it is the primary correctness
signal; it is itself an Evaluation Measure.

---

## Process Language

Vocabulary of how we work. Settled — this is the framework described in
`CLAUDE.md`.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Target State** | The finished system we are building toward, described in Glossary terms. Fixed unless explicitly renegotiated. | `.claude/docs/design/target-state.md` | agreed |
| **Current State** | What actually exists right now. Describes reality only, never intent. | `.claude/docs/design/current-state.md` | agreed |
| **Step** | One vertical slice moving Current State toward Target State. Leaves the project working end-to-end. Composed of 1–5 Sub-steps. | `.claude/docs/plan/step-NNN-*.md` | agreed |
| **Sub-step** | The smallest unit of work that is independently reviewable and committable. Exactly one commit. | `.claude/docs/plan/step-NNN-*.md` | agreed |
| **Debt Ledger** | The register of knowingly-taken shortcuts, each with a repayment Trigger. | `.claude/docs/debt-ledger.md` | agreed |
| **Trigger** | The condition that forces a Debt entry to be repaid. Debt without a Trigger is a wish, not debt. | `.claude/docs/debt-ledger.md` | agreed |
| **Step Review** | The handoff note Claude writes at the close of each Sub-step, for Amino to review before committing. | `.claude/docs/reviews/step-NNN-*.md` | agreed |
| **ADR** | Architecture Decision Record — a decision that is expensive to reverse, with its context, alternatives, and consequences. | `.claude/docs/adr/` | agreed |
| **Term Proposal** | A flagged request to admit a new word into the Glossary, raised the moment an unregistered term is needed. | this file | agreed |

---

## Retired terms

_(none yet)_
