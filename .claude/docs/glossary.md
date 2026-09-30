# Glossary — Ubiquitous Language

The single source of truth for vocabulary in this project. Every Glossary term
used in a document, a plan, or a **code identifier** must appear here, spelled
exactly as registered. The `registering-language` skill says which words are
Glossary terms.

**Adding a term:** see the `registering-language` skill. Never coin a term
silently — propose it, agree on it, then register it.

**Status values:** `agreed` (settled, use freely) · `proposed` (awaiting
Amino's approval, do not put in code yet). A term that loses a collision is
deleted, and every use of it renamed.

---

## System Language

Veritas's own words, as distinct from the words of a Domain it answers questions
about.

**Metric** in Veritas means one thing only: a **business** metric — a Certified
Metric about the brokerage, like Gross Revenue or Traded Notional. The measures of
how well Veritas *itself* performs are never called metrics; they are
**measures**. Keeping the two words apart is what stops the collision this
Glossary exists to prevent — a chart labelled "metrics" mixing Gross Revenue with
hit-rate.

### A. The system

What Veritas is made of, and how it is measured.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Domain** | The subject a database records, such as a brokerage or a hospital: its things, how they relate, and how the business measures them. Veritas never holds a Domain: it holds the database's schema and a User's definitions, which together describe one. Not the database and not the definitions, which describe a Domain. Not *one database and the certified definitions that describe it*: a brokerage is not a database plus definitions. | — (not built yet) | agreed |
| **User** | The person who connects a Domain to Veritas, writes and certifies the definitions that describe it, and asks questions in its words. Runs as one Access Profile. Not the LLM, which may draft a definition but never certifies one. One role, not an *Asker* and a *Steward*: the aim is to make describing a Domain too small a job to need a role of its own. | — (not built yet) | agreed |
| **Semantic Layer** | The certified registry of Metric Definitions, Dimension Definitions, Join Paths and Ambiguous Terms. Veritas's knowledge base — the thing retrieval searches. | `semantic/` | agreed |
| **Semantic Entry** | One retrievable document in the Semantic Layer. The unit of retrieval and the unit of relevance in retrieval evaluation. | `semantic/` | agreed |
| **Metric Definition** | A named, versioned, certified computation over the warehouse — its SQL expression, grain, filters, units, and the aliases Users use for it. | `semantic/metrics/` | agreed |
| **Certified Metric** | A metric that exists in the Semantic Layer. The only kind Veritas is permitted to compute. | `semantic/metrics/` | agreed |
| **metric expression** | The SQL expression inside a query that computes a metric — the thing the Validation Gate traces. Distinct from the **Metric Definition**, which is the certified entry that publishes one, and from the **Certified Metric** it must trace to: a metric expression that traces to no Certified Metric is a **Shadow Metric**. Lower case, because that is how the [Target State's flow](design/target-state.md#flow) spells it — *"every metric expression traces to a Certified Metric"*. A statement that computes none is refused with the `Rejection Reason` `no metric expression`. | `veritas/validation/` — read out of the generated SQL | agreed |
| **Shadow Metric** | A metric computed inline in a query instead of drawn from the Semantic Layer. The failure mode Veritas exists to prevent. A **metric expression** that traces to no Certified Metric is one. `RejectionReason.SHADOW_METRIC` is the verdict the Validation Gate returns on a statement whose metric expressions do not all trace; no Semantic Entry publishes one. | `veritas/validation/` — as a Rejection Reason (no file publishes one) | agreed |
| **Ambiguous Term** | A word Users say that maps to two or more Certified Metrics and therefore has no single correct answer. Not a metric — an instruction to disambiguate before generating SQL. | `semantic/ambiguous/` | agreed |
| **Dimension Definition** | A certified axis for *slicing* a metric — the answer to "by what?". Names the column, its grain, and its allowed values, so "by region" always means the same column with the same buckets. The five certified axes, each written here as `(columns — grain — allowed values)`: **by trade date** (`fct_trade.trade_date` — daily), **by snapshot date** (`fct_position_snapshot.snapshot_date` · `fct_balance_snapshot.snapshot_date` — daily), **by accounting movement date** (`fct_accounting_movement.movement_date` — daily), **by region** (`dim_client.client_region` — one Client — EU · UK · APAC), **by instrument type** (`dim_instrument.instrument_type` — one Instrument — equity · ETF · future · currency pair). A date axis enumerates no allowed values, because its values are minted by the data rather than registered here. "Net Revenue **by region** last quarter" applies the region Dimension Definition to the Net Revenue metric. `semantic/dimensions/` publishes the five axes, and `check_semantic_layer.py` reads this cell back against them. There are three date axes because a Snapshot metric's route never reaches `fct_trade.trade_date`. An axis also declares **the routes that reach it** — the map from a metric's `from_table` to the Join Paths that reach this axis's columns from there, so that an axis is applicable rather than merely certified. The routes themselves are **not** listed here: `semantic/dimensions/` holds them and `check_semantic_layer.py`'s check 19 walks them, for the reason [DEBT-017](debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) is already open about this cell. An axis that names no route from a fact table is not reachable from it, and a slice by it is refused by name. | `semantic/dimensions/` | agreed |
| **Join Path** | A certified route between two warehouse tables, so the model never invents a join. | `semantic/joins/` | agreed |
| **Route** | Where a statement's rows come from: the tables it starts at, and the joins it reaches the rest of them through. Read off a parse tree, or built from a Metric Definition's `from_table` and `join_paths`, so that what a query took and what the corpus certifies can be compared as values. A **Join Path** is one certified hop between two tables and is published as a file; a Route is the whole chain plus where it starts, and is never published — `Traded Notional`'s Route is two Join Paths and `fct_trade`, `Trade Count`'s is no Join Paths and `fct_trade`. A Route is also built from a Dimension Definition's `routes`, and the Route the Validation Gate permits a statement is the union of the metric's, the axis's, and the route the Access Profile's predicate needs. No file is a Route; the entries publish the fields one is built from. | `veritas/validation/` — read from a statement or from a Metric Definition's fields (no file publishes one) | agreed |
| **Grounding** | The step where retrieved Semantic Entries constrain SQL generation. Ungrounded generation is forbidden, not merely discouraged. | `veritas/grounding/` | agreed |
| **Validation Gate** | Deterministic, non-LLM checks a query must pass before execution: certified-metrics-only, no restricted columns, access policy applied, cost bounded, read-only. | `veritas/validation/` | agreed |
| **Access Profile** | The identity Veritas runs a question as — role and permitted region. Determines which rows and columns the Validation Gate allows. | `veritas/validation/` | agreed |
| **Restricted Column** | A column an Access Profile forbids from appearing in a Grounded Answer's projection. *In the projection* is judged on the parse tree once `SELECT *` has been expanded against the real schema: the name in a comment, in a string literal, or in a filter is not a projection of it. | `veritas/validation/` | agreed |
| **Validation Gate outcome** | The verdict the Validation Gate returns: allowed or rejected, the Rejection Reasons that fired, the explanation a caller shows a User, and the rule set the decision was taken under. What a Grounded Answer carries, what the App renders, and what Observability charts. | `veritas/validation/` | agreed |
| **Rejection Reason** | One member of the stable taxonomy a rejected Validation Gate outcome carries — the thing *"Validation-Gate rejections by reason"* is grouped by. The **members** are registered in `veritas/validation/`, where the Gate enumerates them, and deliberately not in this cell: a vocabulary inside one table cell read by a prose parse is [DEBT-017](debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell). | `veritas/validation/` | agreed |
| **Grounded Answer** | The response object: the answer, the SQL, the Lineage, and the Validation Gate outcome. Veritas never returns a bare number. | `veritas/` | agreed |
| **Clarifying Question** | What Veritas returns instead of an answer when a question says an **Ambiguous Term** and nothing resolved which Certified Metric was meant: the question Veritas asks back, naming each unresolved term and the metrics it could mean. Not a **refusal** — a refusal says the question cannot be answered, a Clarifying Question says it is not answerable *yet* and what would settle it. They are the two ways a **Grounded Answer** carries no number, and one carrying both says two different things about one question, which is why `GroundedAnswer` refuses to be built that way. Rendered by the App, and grouped over by Observability as a `Validation Gate outcome` is grouped by its `Rejection Reason`. Spelled `clarifying_question` on both `Rewrite` and `GroundedAnswer`. | `veritas/orchestrator/` | agreed |
| **Ending** | One of the three ways a Grounded Answer ends: a number, a Clarifying Question or a refusal. A Gold Question names its correct Ending, and Evaluation scores the pair of correct and given Endings. Not the answer itself: an Ending of *a number* says only that a number was given, not which one. Not *Outcome*, *Verdict* or *Result*, which Validation Gate outcome, Feedback and the gold result already hold. Spelled `Expectation` in the code until [DEBT-045](debt-ledger.md#debt-045--the-code-calls-an-ending-an-expectation) is paid. | `veritas/evaluation/` | agreed |
| **Lineage** | The record of which Semantic Entries and which Metric Definition versions produced a Grounded Answer. What makes an answer auditable. | `veritas/` | agreed |
| **Interpretation** | An answer's statement, in the Domain's words, of exactly what it computed: which definitions, filters, period and grouping. The User checks it instead of the SQL. Not **Lineage**, which records which entries and versions an answer came from, for audit: an Interpretation says what the answer means, for the User. Not *Explanation*, which suggests narrating the result, nor *Restatement*, which suggests echoing the question. | — (not built yet) | agreed |
| **Gold Question Set** | The evaluation corpus: question, gold SQL, gold result, and the Semantic Entries the gold SQL touches. | `data/gold/` | agreed |
| **Gold Question** | One member of the **Gold Question Set**: the question as a User asks it, which of a **Grounded Answer**'s three Endings is correct for it, and — where that Ending is a number — the gold SQL and the gold result. One file under `data/gold/`, read by the `GoldQuestion` dataclass whose field list is that file format. Its **Relevant Set** is not one of its fields: a Gold Question says what the *answer* should be, and what the *corpus* should have been searched for is derived from its statement. | `data/gold/` | agreed |
| **Relevant Set** | The Semantic Entries one **Gold Question**'s gold SQL touches — what a Retrieval ranking is scored against, and the [Target State](design/target-state.md#zoomcamp-criteria-map)'s *"ground truth is derived"* in one noun. **Derived, never written down**: the Certified Metrics the statement's projections trace to, the certified axes it groups by or filters on, and the Join Paths those two declare, all read through `veritas/validation/`'s own readers. Distinct from **Lineage**, which records the entries an answer *was* built from: a Relevant Set is what a correct answer *would have needed*, so the two are the two sides hit rate and Mean Reciprocal Rank compare. A question whose correct Ending is a refusal or a **Clarifying Question** has an empty one. `relevant_entries` computes one. | `veritas/evaluation/` — derived from a gold SQL (no file publishes one) | agreed |
| **Execution Accuracy** | Share of generated queries whose result set matches the gold result. The primary correctness measure — objective, unlike a judge's opinion. | `veritas/evaluation/` | agreed |
| **Evaluation Measure** | A measure of how well Veritas answers, computed over the Gold Question Set: hit rate and MRR for Retrieval; Execution Accuracy and LLM-as-judge agreement for generation. These are the Zoomcamp evaluation measures. | `veritas/evaluation/` | agreed |
| **Reporting Currency** | The single currency a Grounded Answer is expressed in. Every monetary metric must state one. | `semantic/metrics/` | agreed |
| **Warehouse** | The analytical store holding the brokerage star schema — the `fct_` and `dim_` tables of Section B. DuckDB for the slice. Reached **only** through the Warehouse Adapter; no component queries it directly. | `veritas/warehouse/` | agreed |
| **Warehouse Adapter** | The single boundary through which all Warehouse access passes. Holds the connection and the engine's dialect; nothing DuckDB-specific exists outside it. The seam an engine swap lands on. | `veritas/warehouse/` | agreed |
| **Ingestion** | The pipeline that fills the Warehouse: real FX Rates, Market Prices and instrument reference data from key-free public sources, snapshotted into the repository and replayed by default; synthetic Trades, Cash Movements and Positions from a seeded simulator. **Market data real, client activity synthetic — never the reverse.** | `veritas/ingestion/` | agreed |
| **Retrieval** | The step that turns a question into the Semantic Entries needed to answer it. Searches the Semantic Layer **only** — never Warehouse schema, never free text. Hybrid text + vector, re-ranked. | `veritas/retrieval/` | agreed |
| **Retrieval Strategy** | Which search one call of Retrieval runs over the corpus — the thing an Evaluation Measure is grouped by when Retrieval's hit rate and MRR are compared, as a Validation Gate outcome is grouped by its Rejection Reason. Not a second word for **Retrieval**: Retrieval is the step, and a Retrieval Strategy is which of its searches that step ran, so two of them over one corpus return different entries for one question and are comparable by measure. The **members** are registered in `veritas/retrieval/`, where `RetrievalStrategy` enumerates them, and deliberately not in this cell for the reason [DEBT-017](debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) is open about. Not `Retrieval Approach`: one concept, one word. | `veritas/retrieval/` — as an enumeration (no file publishes one) | agreed |
| **Orchestrator** | The component that runs a question through the seven-step flow: rewrite, retrieve, ground, generate, validate, execute, answer. Owns the sequence and the failure paths; owns none of the steps' logic. Not `Copilot`: Veritas *is* a copilot, so the word cannot also name one component inside it, and "copilot" stays lower-case prose for the product as a whole. | `veritas/orchestrator/` | agreed |
| **App** | Where a User asks a question and reads a Grounded Answer — with its SQL, its Lineage and its Validation Gate outcome. **Never renders a bare number.** Not `Interface`, which is the rubric's criterion name; `App` matches the directory. | `veritas/app/` | agreed |
| **Observability** | Records what happened at runtime: every question, Grounded Answer, Validation Gate outcome, cost, latency and Feedback — the Question Log. Produces Operational Measures. **Records; never judges.** Live traffic, no ground truth. | `veritas/observability/` | agreed |
| **Operational Measure** | A runtime measure logged per question and shown on the Grafana dashboard: cost, latency, Validation Gate outcome, and Feedback. | `veritas/observability/` | agreed |
| **Evaluation** | Computes Evaluation Measures over the Gold Question Set: hit rate and MRR for Retrieval, Execution Accuracy and LLM-as-judge for generation. **Offline, against known-correct answers** — the opposite pole from Observability. | `veritas/evaluation/` | agreed |
| **Question Log** | The record Observability keeps: one row per question a User asked through the App, carrying its Grounded Answer, Validation Gate outcome, Lineage, Operational Measures and Feedback. The seam `veritas/observability/` exposes and the tables behind it. Not the **Gold Question Set**: a Question Log row is live traffic with no ground truth; a Gold Question is ground truth with no traffic. | `veritas/observability/` | agreed |
| **Feedback** | What a User says about a Grounded Answer they were shown: a verdict, up or down, and optionally a sentence. Attached to that answer's **Question Log** row and never to the question text alone, so Feedback on an answer is Feedback on *that* SQL, Lineage and Validation Gate outcome, and a later answer to the same words inherits none of it. The one of **Operational Measure**'s four — cost, latency, Validation Gate outcome, Feedback — that had no row of its own. Not an **Evaluation Measure**: a verdict is live traffic, and nothing scores it against a gold result. | `veritas/observability/` — offered by the App | agreed |

---

## Brokerage Language

The words of the brokerage, the first Domain Veritas answers questions about.

### B. The warehouse

What the data describes. A brokerage: clients hold accounts, accounts trade
instruments, trades move cash and change positions.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Instrument** | A tradable asset — equity, ETF, future, or currency pair. Single bonds and options are **out of scope**: neither has a key-free Market Price source, so holding them would mean fabricating prices while claiming market data is real. Bond exposure is represented through bond ETFs, which is how most brokerage clients hold bonds anyway. See [DEBT-003](debt-ledger.md#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope). | `dim_instrument` | agreed |
| **Instrument Symbol** | The ticker identifying an Instrument, and the natural key every source keys on — NASDAQ Trader's `Symbol` column, the SEC's ticker, and the symbol Yahoo's chart endpoint is queried by. Unique. Without it the price and reference feeds have nothing to join an Instrument on. | `dim_instrument` | agreed |
| **Client** | The legal owner of one or more Accounts. The entity a region or segment attaches to. | `dim_client` | agreed |
| **Account** | The container trades and cash sit in. Has exactly one Client and one or more currency balances. | `dim_account` | agreed |
| **Trade** | One executed order: an Account buys or sells a quantity of an Instrument at an Execution Price, on a Trade Date, settling on a Settlement Date. | `fct_trade` | agreed |
| **Execution Price** | The price a Trade actually filled at, in the Instrument's Quotation Currency. Distinct from Market Price, which is that day's close for the Instrument as a whole: a Trade fills at whatever the market gave it at that moment, which is not the close except by coincidence. Trades are valued at Execution Price; Positions are marked at Market Price. Never the bare word "price". | `fct_trade` | agreed |
| **Trade Side** | Whether a Trade bought or sold: `buy` or `sell`. The direction the `Trade` row described — *"an Account buys or sells"* — without ever naming it. Preferred to a signed quantity, so `quantity` is always positive and `Traded Notional` stays literally true as it is written below, with no undocumented absolute value hidden in the metric. | `fct_trade` | agreed |
| **Traded Notional** | Σ(quantity × Execution Price) converted to the Reporting Currency. The monetary size of trading activity. | `semantic/metrics/` | agreed |
| **Trade Count** | Number of Trades. Deliberately separate from Traded Notional — they answer different questions. | `semantic/metrics/` | agreed |
| **Commission** | What the broker charges the Client for executing a Trade. Broker income. | `fct_trade` | agreed |
| **Fee** | A third-party charge passed through to the Client — exchange, clearing, regulatory. Collected by the broker but not earned by it. | `fct_trade` | agreed |
| **Rebate** | Value returned to a Client or introducing partner out of Commission already charged. Reduces what the broker keeps. | `fct_trade` | agreed |
| **Gross Revenue** | Σ(Commission) before any Rebate or pass-through Fee is deducted. | `semantic/metrics/` | agreed |
| **Net Revenue** | Gross Revenue − Rebate − pass-through Fee. What the broker actually keeps. | `semantic/metrics/` | agreed |
| **Cash Movement** | Money actually entering or leaving an Account on a given date — deposits, withdrawals, settlement, fee charges. | `fct_cash_movement` | agreed |
| **Accounting Movement** | A ledger entry recognising economic value on the date it was *earned*, whether or not cash moved. | `fct_accounting_movement` | agreed |
| **Cash Balance** | Money held in an Account in one currency at a point in time. Cash only. A Certified Metric as well as a column, because two [Section D](#d-ambiguous-terms) Ambiguous Terms — "balance" and "how much does X have" — resolve to it, and an Ambiguous Term that disambiguates to something with no Metric Definition to retrieve is the incoherence [EXT-005](extension-register.md#ext-005--semantic-layer-coherence-checks) lists as its fourth rule. | `fct_balance_snapshot`, `semantic/metrics/` | agreed |
| **Account Value** | Cash Balance plus all Positions marked to market, in the Reporting Currency. | `semantic/metrics/` | agreed |
| **Snapshot** | The state of a subject **as of the close of** a date, at a grain of one row per subject per date. Authoritative for *"what was held as of D"* and nothing else: a Snapshot cannot see between its own dates, so a Position opened and closed inside one day leaves the Snapshots either side of it identical. End-of-day is part of the definition, not a loading detail — a Position marked at that date's closing Market Price must be the Position held at the close. Written on every date the Warehouse holds a Market Price for, so an "as of" question is an equality join rather than a most-recent-row-at-or-before lookup. | `fct_position_snapshot`, `fct_balance_snapshot` | agreed |
| **Position** | Quantity of one Instrument held by one Account at a point in time. | `fct_position_snapshot` | agreed |
| **Position Change** | Change in a Position between two points in time, from any cause — a Trade, a transfer, or a corporate action. | `semantic/metrics/` | agreed |
| **Cost Basis** | What a held Position cost to acquire, in the Instrument's Quotation Currency — the total for the held quantity, accumulated across the Trades that built it. The quantity both Realised and Unrealised P&L are measured against: neither is computable without it, since a Market Price alone says what a holding is worth and not what it gained. Signed, tracking the Position's own sign, so a short's proceeds are negative and one expression covers both directions. | `fct_position_snapshot` | agreed |
| **Realised P&L** | Profit or loss locked in by closing a Position. | `semantic/metrics/` | agreed |
| **Unrealised P&L** | Profit or loss on a Position still held, at current market price. Moves with the market; nothing has been banked. | `semantic/metrics/` | agreed |
| **FX Rate** | The rate between two currencies on a date, from the real ECB reference rates published against the euro and sourced from the public Frankfurter API. A pair with the euro on one side **is** a published reference rate; a pair between two non-euro currencies is the **ratio of that date's two published rates** — the cross-rate, which is what Frankfurter itself returns under a non-euro base. Both are FX Rates and both are stored; a rate of any other origin is not one. Published on working days only, so a rate for a non-publishing date is the most recent published rate at or before it. | `fct_fx_rate` | agreed |
| **Market Price** | The unadjusted closing price at which an Instrument traded on a date, in its Quotation Currency. The only price a Position may be marked at. | `fct_instrument_price` | agreed |
| **Adjusted Close** | A price series back-adjusted for splits and dividends, which rewrites historical prices as later corporate actions occur. Correct for computing returns; **forbidden** for marking Positions or computing P&L. | — (an anti-pattern) | agreed |
| **Quotation Currency** | The currency *and minor unit* an Instrument's Market Price is quoted in — LSE quotes in pence (`GBp`), not pounds. Normalising to major units is a required ingestion step. Distinct from Reporting Currency. | `dim_instrument` | agreed |
| **Denomination Currency** | The currency a monetary amount in a fact row is *held* in — a Cash Movement's amount, an Accounting Movement's amount, a Cash Balance, and a Trade's Commission, Fee and Rebate. The third currency sense, and the one with no Instrument and no answer attached to it: a broker does not necessarily charge in the currency an Instrument is quoted in, so Traded Notional and Gross Revenue take different routes through FX Rate to reach the Reporting Currency. | `fct_trade`, `fct_cash_movement`, `fct_accounting_movement`, `fct_balance_snapshot` | agreed |

### C. Distinctions we must not blur

These pairs are near-synonyms in ordinary speech and different quantities in the
brokerage. Confusing one for another produces a **correct program computing the
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
| **Execution Price** | **Market Price** | Both are a price of the same Instrument on the same date, and neither is the wrong one — they answer different questions. Traded Notional at the close values trading that never happened at that price; a Position marked at whatever a Trade happened to fill at is a mark to one order rather than to the market. Never both "price": the same word for two numbers is the disease Section C exists to catch. |
| **Adjusted Close** | **Market Price** | Measured on real data, not assumed: the two differ on **nearly every bar** — `uv run python .claude/scripts/check_data_availability.py` prints how many, offline. Adjusted Close rewrites history every time a dividend is paid, so a Position marked at it yields an Account Value that is both wrong and *irreproducible* — the same query returns a different number next quarter. |
| **Quotation Currency** | **Reporting Currency** | A Market Price is quoted in the Instrument's own currency and minor unit; a Grounded Answer is expressed in one Reporting Currency. Skipping the conversion is an FX-sized error; missing the minor unit is a **100×** error — LSE quotes pence, and £4.20 booked as £420 looks entirely plausible. |
| **Cost Basis** | **Execution Price** | An Execution Price is what *one* Trade filled at; a Cost Basis is what the *whole holding* cost, accumulated across every Trade that built it and carried on the Position rather than the Trade. Marking Unrealised P&L against the latest Execution Price prices the holding at the last thing that happened to it, which for a position built over six months is a number with no relationship to what it cost. The two are also different shapes — one is per unit, the other is a total — so substituting one for the other is off by a quantity as well as by a price. |
| **Denomination Currency** | **Quotation Currency** | Both sit on `fct_trade` and they are not the same column. `quantity × Execution Price` is in the Instrument's Quotation Currency; Commission, Fee and Rebate are in the Trade's Denomination Currency, because a broker charges in the currency it bills in rather than the one the exchange quotes in. Assuming they are equal converts Gross Revenue through the wrong FX Rate — a plausible number, off by a currency pair. |

### D. Ambiguous Terms

Words Users genuinely say that are **not** metrics. Veritas must resolve them
before generating SQL — never guess silently.

| User says | Could mean | Resolution | Also said as |
|---|---|---|---|
| "revenue" | Gross Revenue · Net Revenue | Ask, unless the question names one | revenues |
| "volume" | Traded Notional · Trade Count | Ask | volumes · turnover |
| "balance" | Cash Balance · Account Value | Ask | balances |
| "P&L" | Realised P&L · Unrealised P&L · both | Ask | PnL · P and L · P & L · P/L |
| "how much does X have" | Cash Balance · Account Value | Ask | how much is in X · how much does X hold |

*Also said as* is the other spellings of the same word — what a User types when
they do not type the registered one. A spelling here is **the registered term**: it
is detected exactly as the *User says* cell is, resolved against the same *Could
mean* pair, and `X` stands for the subject in a phrase as it does in the row above.
`semantic/ambiguous/` publishes the cell as the entry's `aliases`, and
`tests/test_rewrite.py` reads it back against them.

**"turnover" is a spelling of "volume", not an alias of `Traded Notional`.** An alias
that is also an Ambiguous Term resolves silently the very thing this section says
must be asked — `check_semantic_layer.py`'s check 14 refuses one. "Turnover" is
ambiguous for the reason "volume" is: it names notional to a trading desk and count
to an operations team, and Veritas serves both.

**`both`** in the "P&L" row is a third *answer*, not a third Certified Metric, and
the check prints it as prose rather than resolving it. Every other *Could mean* name
is a Section B term spelled as registered, which `check_semantic_layer.py` reads back
against `semantic/ambiguous/`.

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

These are shorthand, **not** terms. A word that carries meaning belongs in a
section above, with a definition and a status.

| Short | Expanded | Note |
|---|---|---|
| **ADR** | Architecture Decision Record | Also a Process Language term |
| **BAAI** | Beijing Academy of Artificial Intelligence | Publishes `bge-small-en-v1.5`, the sentence-embedding model `Retrieval` searches with |
| **BI** | Business Intelligence | The dashboard layer metric logic is being moved *out* of |
| **CI** / **CD** | Continuous Integration / Continuous Delivery | The pipeline [EXT-014](extension-register.md#ext-014--the-container-tests-run-as-pipeline-stages-before-and-after-a-deploy) would run `tests/` in, and the release it would verify afterwards |
| **CIK** | Central Index Key | Securities and Exchange Commission's issuer identifier |
| **CTE** | Common Table Expression | A named subquery in SQL's `WITH` clause |
| **CUSIP** | Committee on Uniform Securities Identification Procedures | North American security identifier |
| **DDD** | Domain-Driven Design | Where the ubiquitous-language discipline comes from |
| **DDL** | Data Definition Language | The `CREATE TABLE` subset of Structured Query Language |
| **ECB** | European Central Bank | Publishes the reference rates behind `FX Rate` |
| **EODHD** | End Of Day Historical Data | A market-data vendor, rejected for requiring a key |
| **ETF** | Exchange-Traded Fund | An `Instrument` type |
| **FAQ** | Frequently Asked Questions | The course's corpus, which the rubric forbids |
| **FX** | Foreign Exchange | As in `FX Rate` |
| **ICE** | Intercontinental Exchange | A market-data vendor, rejected as paid-only |
| **ISIN** | International Securities Identification Number | Global security identifier |
| **LLM** | Large Language Model | |
| **LLMZC** | Large Language Model Zoomcamp | The course; `aminojagh/LLMZC` holds reusable coursework |
| **LSE** | London Stock Exchange | Quotes in pence — see `Quotation Currency` |
| **ML** | Machine Learning | |
| **MRR** | Mean Reciprocal Rank | An `Evaluation Measure` for Retrieval |
| **MVP** | Minimum Viable Product | The full system in `product-brief.md` |
| **NYSE** | New York Stock Exchange | Lists traded Instruments absent from `nasdaqlisted.txt`, which is why NASDAQ Trader's second file is read |
| **OHLCV** | Open, High, Low, Close, Volume | The daily price bar fields |
| **ONNX** | Open Neural Network Exchange | The runtime format both of `Retrieval`'s models ship in — no PyTorch, no key |
| **RAG** | Retrieval-Augmented Generation | |
| **SEC** | Securities and Exchange Commission | Source of issuer reference data |
| **UI** / **UX** | User Interface / User Experience | |

Left unexpanded on purpose, being more recognisable than their expansions:
`SQL`, `API`, `HTTP`, `JSON`, `CSV`, `YAML`, `URL`, `ID`, `CLI`, `AI`. The list
lives in `tests/test_language.py`, as `EXEMPT`, and is enforced by it.
