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
>
> **Three terms added and one narrowed on 2026-08-03** by Sub-step 1.2, all
> approved the same day. `Market Price`, `Adjusted Close` and `Quotation
> Currency` each name a way the real market data was found to produce a
> *plausible wrong number*. `Instrument` was narrowed to exclude single bonds
> and options, neither being obtainable from a key-free source
> ([DEBT-003](debt-ledger.md)). Evidence:
> [data-availability.md](design/data-availability.md).
>
> **`FX Rate` and `Market Price` live in `fct_` tables, not `dim_`.** Both are
> dated observations that grow daily, which is a fact-table shape; only their
> subjects (`dim_instrument`) are dimensions.
>
> **Eight component terms added on 2026-08-04** by Sub-step 1.3, all approved the
> same day: `Warehouse`, `Warehouse Adapter`, `Ingestion`, `Retrieval`,
> `Orchestrator`, `App`, `Observability`, `Evaluation`. Seven of the nine Target
> State components had been used as names since Sub-step 1.1 without ever being
> registered — a gap `.claude/scripts/check_language.py` now makes impossible to
> reintroduce. Two were renamed on registration: `Copilot` → `Orchestrator` and
> `Interface` → `App`. See [Component terms](#component-terms--agreed-2026-08-04)
> and [Retired terms](#retired-terms).

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
| **Warehouse** | The analytical store holding the brokerage star schema — the `fct_` and `dim_` tables of Section B. DuckDB for the slice. Reached **only** through the Warehouse Adapter; no component queries it directly. | `veritas/warehouse/` | agreed |
| **Warehouse Adapter** | The single boundary through which all Warehouse access passes. Holds the connection and the engine's dialect; nothing DuckDB-specific exists outside it. The seam an engine swap lands on. | `veritas/warehouse/` | agreed |
| **Ingestion** | The pipeline that fills the Warehouse: real FX Rates, Market Prices and instrument reference data from key-free public sources, snapshotted into the repository and replayed by default; synthetic Trades, Cash Movements and Positions from a seeded simulator. **Market data real, client activity synthetic — never the reverse.** | `veritas/ingestion/` | agreed |
| **Retrieval** | The step that turns a question into the Semantic Entries needed to answer it. Searches the Semantic Layer **only** — never Warehouse schema, never free text. Hybrid text + vector, re-ranked. | `veritas/retrieval/` | agreed |
| **Orchestrator** | The component that runs a question through the seven-step flow: rewrite, retrieve, ground, generate, validate, execute, answer. Owns the sequence and the failure paths; owns none of the steps' logic. Renamed from `Copilot` on 2026-08-04 — Veritas *is* a copilot, so the word could not also name one component inside it. | `veritas/orchestrator/` | agreed |
| **App** | Where a person asks a question and reads a Grounded Answer — with its SQL, its Lineage and its Validation Gate outcome. **Never renders a bare number.** Renamed from `Interface` on 2026-08-04, so the name matches the directory and does not collide with the rubric's own "Interface" criterion. | `veritas/app/` | agreed |
| **Observability** | Records what happened at runtime: every question, Grounded Answer, Validation Gate outcome, cost, latency and feedback. Produces Operational Measures. **Records; never judges.** Live traffic, no ground truth. | `veritas/observability/` | agreed |
| **Evaluation** | Computes Evaluation Measures over the Gold Question Set: hit rate and MRR for Retrieval, Execution Accuracy and LLM-as-judge for generation. **Offline, against known-correct answers** — the opposite pole from Observability. | `veritas/evaluation/` | agreed |

#### Component terms — `agreed` 2026-08-04

The eight component rows above were proposed and decided the same day. Seven had
been used as capitalised names since Sub-step 1.1 — in `target-state.md`, in
`current-state.md`, in the ADRs — without ever being registered.
`.claude/scripts/check_language.py` fails on any Target State component name with
no Glossary row, which is what surfaced them.

**Why it mattered.** In prose an unregistered component name is a formatting
inconsistency. In Step 002 these become **directories and modules**, and
Non-Negotiable #1 requires a domain noun to be registered *before* it names a
code identifier. Registering them first was the cheap order; renaming a directory
after it exists is not.

**Why Section A.** Section A is headed *"What Veritas is made of"* and already
held `Semantic Layer` and `Validation Gate` — two of the nine components. Putting
the rest anywhere else would have raised "why is Validation Gate in A but App in
F?". Splitting Section A into components versus artifacts-and-concepts was
considered and **declined for now** (2026-08-04): the combined table is readable
enough, and restructuring an `agreed` section costs more than it returns today.

##### Two renames

- **`Copilot` → `Orchestrator`.** `Copilot` named two different things at two
  different scopes: Veritas *is* a natural-language analytics copilot, and Veritas
  *contained* a Copilot. One word for a whole and one of its parts is the synonym
  disease inverted. `Orchestrator` names the job — it owns the sequence and the
  failure paths, and none of the steps' logic. `Answer Pipeline` was the other
  candidate and was **rejected**: "pipeline" implies a straight line, and this
  flow branches — a failed Validation Gate stops, an unresolved Ambiguous Term
  returns to the user.
  **"copilot" survives in lowercase prose**, which is the point of the rename:
  *"Veritas is a natural-language analytics copilot"* and *"a metrics copilot,
  not a database browser"* both still read correctly, and both keep the thread
  back to the [product brief](design/product-brief.md), which lists "Analytical
  copilots" among the full system's capabilities.
- **`Interface` → `App`**, matching `veritas/app/`. A second reason emerged
  beyond the directory name: the Zoomcamp rubric has its own criterion called
  *Interface*, so the word was carrying both our component and the grader's
  scorecard line. The criteria map still says "Interface" because that is the
  grader's vocabulary, not ours.

##### What each term buys, strongest first

- **`Warehouse` and `Warehouse Adapter`** — the pair matters most. ADR-0002 had
  been leaning on three different readings of "Warehouse" (the DuckDB database,
  the star schema, the adapter boundary), exactly the ambiguity a Glossary exists
  to kill. Split, the constraint becomes sayable: the Warehouse is *the store*,
  the Adapter is *the only way in*. Unsplit, "no component touches the Warehouse
  directly" is a sentence that contradicts itself.
- **`Retrieval`** — carries a hard constraint rather than a generic meaning. Here
  it means retrieval *over Semantic Entries, never over schema* (ADR-0001), which
  is the central bet of the project. The word must not drift back to its ordinary
  sense.
- **`Ingestion`** — likewise specific: snapshot-and-replay for real market data,
  a seeded simulator for client activity. *"Market real, client synthetic — never
  the reverse"* is a rule someone could otherwise break without noticing.
- **`Observability` and `Evaluation`** — weak individually, strong as a pair. One
  is live traffic with no ground truth; the other is offline against known
  answers. Blurring them produces the disease Section E exists to prevent —
  reporting user feedback as accuracy, or expecting hit rate from production.
  Section E registers the *measures*; these register the components that produce
  them.
- **`Orchestrator`** — thin by design. It owns sequence and failure paths only,
  so its definition is mostly a list of what it does *not* own.
- **`App`** — one real constraint, *"never renders a bare number"*, echoing
  `Grounded Answer`. Beyond that it is a plain name for a plain thing.

##### Documents swept on agreement

`target-state.md`, `current-state.md`, the ADRs, the Debt Ledger and the
Extension Register were all revisited in the same Sub-step so no document uses an
old name. The Step Reviews were **not** rewritten: they are point-in-time records
of what was true when written, and editing them would destroy the history that
makes the renames traceable.

### B. The warehouse

What the data describes. A brokerage: clients hold accounts, accounts trade
instruments, trades move cash and change positions.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Instrument** | A tradable asset — equity, ETF, future, or currency pair. Single bonds and options are **out of scope**: neither has a key-free Market Price source, so holding them would mean fabricating prices while claiming market data is real. Bond exposure is represented through bond ETFs, which is how most brokerage clients hold bonds anyway. Narrowed 2026-08-03; see [DEBT-003](debt-ledger.md). | `dim_instrument` | agreed |
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
| **FX Rate** | Real ECB reference rate between two currencies on a date. Sourced from the public Frankfurter API. Published on working days only, so a rate for a non-publishing date is the most recent published rate at or before it. | `fct_fx_rate` | agreed |
| **Market Price** | The unadjusted closing price at which an Instrument traded on a date, in its Quotation Currency. The only price a Position may be marked at. | `fct_instrument_price` | agreed |
| **Adjusted Close** | A price series back-adjusted for splits and dividends, which rewrites historical prices as later corporate actions occur. Correct for computing returns; **forbidden** for marking Positions or computing P&L. | — (an anti-pattern) | agreed |
| **Quotation Currency** | The currency *and minor unit* an Instrument's Market Price is quoted in — LSE quotes in pence (`GBp`), not pounds. Normalising to major units is a required ingestion step. Distinct from Reporting Currency. | `dim_instrument` | agreed |

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
| **Adjusted Close** | **Market Price** | Measured on real data: the two differ on **95.5%** of AAPL's last 1,255 daily bars. Adjusted Close rewrites history every time a dividend is paid, so a Position marked at it yields an Account Value that is both wrong and *irreproducible* — the same query returns a different number next quarter. |
| **Quotation Currency** | **Reporting Currency** | A Market Price is quoted in the Instrument's own currency and minor unit; a Grounded Answer is expressed in one Reporting Currency. Skipping the conversion is an FX-sized error; missing the minor unit is a **100×** error — LSE quotes pence, and £4.20 booked as £420 looks entirely plausible. |

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

## Abbreviations

Every abbreviation used anywhere in the project, expanded once. `CLAUDE.md`
requires abbreviations to be expanded on first use in each document; an entry
here satisfies that requirement project-wide, so this table is the one place to
look when a document uses a short form you do not recognise.

These are **not** Domain Language terms — they are shorthand. A word that carries
domain meaning belongs in a section above, with a definition and a status.

| Short | Expanded | Note |
|---|---|---|
| **ADR** | Architecture Decision Record | Also a Process Language term |
| **BI** | Business Intelligence | The dashboard layer metric logic is being moved *out* of |
| **CIK** | Central Index Key | Securities and Exchange Commission's issuer identifier |
| **CUSIP** | Committee on Uniform Securities Identification Procedures | North American security identifier |
| **DDD** | Domain-Driven Design | Where the ubiquitous-language discipline comes from |
| **DDL** | Data Definition Language | The `CREATE TABLE` subset of Structured Query Language |
| **ECB** | European Central Bank | Publishes the reference rates behind `FX Rate` |
| **EODHD** | End Of Day Historical Data | A market-data vendor, rejected for requiring a key |
| **ETF** | Exchange-Traded Fund | An `Instrument` type |
| **FX** | Foreign Exchange | As in `FX Rate` |
| **ICE** | Intercontinental Exchange | A market-data vendor, rejected as paid-only |
| **ISIN** | International Securities Identification Number | Global security identifier |
| **LLM** | Large Language Model | |
| **LLMZC** | Large Language Model Zoomcamp | The course; `aminojagh/LLMZC` holds reusable coursework |
| **LSE** | London Stock Exchange | Quotes in pence — see `Quotation Currency` |
| **ML** | Machine Learning | |
| **MRR** | Mean Reciprocal Rank | An `Evaluation Measure` for Retrieval |
| **MVP** | Minimum Viable Product | The full system in `product-brief.md` |
| **OHLCV** | Open, High, Low, Close, Volume | The daily price bar fields |
| **RAG** | Retrieval-Augmented Generation | |
| **SEC** | Securities and Exchange Commission | Source of issuer reference data |
| **UI** / **UX** | User Interface / User Experience | |

Left unexpanded on purpose, being more recognisable than their expansions:
`SQL`, `API`, `HTTP`, `JSON`, `CSV`, `YAML`, `URL`, `ID`, `CLI`, `AI`. The list
lives in `.claude/scripts/check_language.py` and is enforced by it.

---

## Retired terms

Kept so the old name stays recognisable in history, with a pointer to its
replacement.

| Retired | Replaced by | When | Why |
|---|---|---|---|
| **Copilot** | [`Orchestrator`](#a-the-system) | 2026-08-04 | Named both the product and one component inside it. "copilot" remains valid in lowercase prose for the product as a whole. |
| **Interface** | [`App`](#a-the-system) | 2026-08-04 | Renamed to match `veritas/app/`, and to stop colliding with the Zoomcamp rubric's own *Interface* criterion. |

Neither term ever reached code — both were renamed while still `proposed`, which
is the order the Glossary rule exists to produce.
