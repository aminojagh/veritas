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
> **`Execution Price` added on 2026-08-05** during Step 002 planning, approved the
> same day. The Glossary had been using the bare word "price" for the price a
> Trade filled at — in the `Trade` row and inside `Traded Notional` — while
> `Market Price` was registered for the day's close. Two different numbers under
> one unregistered word, about to become a column name. Both rows now say
> `Execution Price`, and the pair has a [Section C](#c-distinctions-we-must-not-blur)
> row of its own.
>
> **A date dimension was rejected on 2026-08-05**, in the same conversation.
> `target-state.md` had described the Warehouse as holding a *"date"* dimension
> while the `Dimension Definition` row below points the date axis at a column —
> at three of them since that row's amendment of 2026-08-24, the first being
> *"**by trade date** (`fct_trade.trade_date` — daily)"*. No metric and no Section
> C distinction needs a calendar attribute that is not derivable in SQL, so there
> is no `dim_date` and the Target State's Warehouse row was corrected instead.
>
> **Three terms added on 2026-08-05** by Sub-step 2.1, all approved the same day,
> each one found by writing the star schema's Data Definition Language (DDL) and
> discovering a column with no word to name it. `Instrument Symbol` is the natural
> key both reference sources supply. `Trade Side` names the buy-or-sell the `Trade`
> row described but never named, and keeps `Traded Notional` literally true as
> written by letting `quantity` stay positive. `Denomination Currency` is the third
> currency sense — what a monetary amount in a fact row is *held* in, as opposed to
> what an Instrument is *quoted* in or what an answer is *expressed* in — and has a
> [Section C](#c-distinctions-we-must-not-blur) row against the other two.
>
> **The instrument-type values were swept on 2026-08-05**, in the same Sub-step.
> Two `agreed` rows disagreed: `Dimension Definition` listed *"equity · bond ·
> future · option"* while `Instrument`, narrowed on 2026-08-03 by R1, reads
> *"equity, ETF, future, or currency pair"*. The parenthetical was simply missed
> when the universe narrowed — single bonds and options have no key-free Market
> Price source ([DEBT-003](debt-ledger.md)) — so the `Dimension Definition` row now
> matches the `Instrument` row, and `dim_instrument.instrument_type` carries a
> constraint that refuses anything else.
>
> **`Cost Basis` added on 2026-08-06**, approved the same day, and found by asking
> a question of the finished schema rather than of the DDL being written: *given
> that snapshots answer "what was held" and `fct_trade` answers "what was done",
> is any promised question unanswerable?* Walking all eight Certified Metrics
> against the ten tables found exactly one. `Unrealised P&L` is quantity ×
> `Market Price` − Cost Basis, and the second term existed in no column, while
> Section D commits Veritas to resolving *"P&L"* to either P&L metric on demand.
> Reconstructing it from Trades is possible only under conditions this schema
> cannot promise, and yields an expression that a Dimension Definition filter
> silently corrupts. It is now a column on `fct_position_snapshot`. `Realised P&L`
> needed no schema change: it is a ledger posting, so it lands in
> `fct_accounting_movement` as a `movement_type` — which is what makes
> [DEBT-010](debt-ledger.md) load-bearing for a registered metric rather than
> cosmetic. Attribution of a `Position Change` to its cause went to
> [EXT-006](extension-register.md) in the same ruling.
>
> **Eight component terms added on 2026-08-04** by Sub-step 1.3, all approved the
> same day: `Warehouse`, `Warehouse Adapter`, `Ingestion`, `Retrieval`,
> `Orchestrator`, `App`, `Observability`, `Evaluation`. Seven of the nine Target
> State components had been used as names since Sub-step 1.1 without ever being
> registered — a gap `.claude/scripts/check_language.py` now makes impossible to
> reintroduce. Two were renamed on registration: `Copilot` → `Orchestrator` and
> `Interface` → `App`. See [Component terms](#component-terms--agreed-2026-08-04)
> and [Retired terms](#retired-terms).
>
> **`metric expression` registered on 2026-08-27** by Sub-step 5.2, approved the
> same day, and the first Domain Language term registered **entirely in lower
> case** — `Validation Gate outcome` is the nearest precedent, and it capitalises
> the component it names. The phrase was already load-bearing in three `agreed`
> places before it had a row —
> the Target State's flow, ADR-0001 and ADR-0003, all of Step 001 — and in the
> `metric_expressions` of Step 003's spike, so the row registers a word the project
> was already using rather than coining one. Registering it in Title Case would have
> meant editing an `agreed` Target State to match a Glossary row, which is the
> wrong way round. The `Shadow Metric` row was amended in the same ruling: its
> *Lives in* cell read *"— (an anti-pattern)"* and now names `veritas/validation/`,
> where the Validation Gate returns the anti-pattern as a Rejection Reason.
>
> **`Route` registered on 2026-08-28** by Sub-step 5.4, approved the same day
> ([R15](plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28)).
> The word was already the `Join Path` row's own definition — *"a certified **route**
> between two warehouse tables"* — and the title of
> [R8 of Step 004](plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22),
> *"the route a Metric Definition carries"*. What it did not have was a row, and Sub-step
> 5.4 needed one: the certified-route rule compares the Route a statement took against
> the Route a Metric Definition declares, and the two halves of that comparison are the
> same kind of thing while a Join Path is only ever one hop of it. Registered in Title
> Case, unlike `metric expression`, because no `agreed` document had already fixed a
> lower-case spelling of it as a noun in its own right.

### A. The system

What Veritas is made of.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Semantic Layer** | The certified registry of Metric Definitions, Dimension Definitions, Join Paths and Ambiguous Terms. Veritas's knowledge base — the thing retrieval searches. | `semantic/` | agreed |
| **Semantic Entry** | One retrievable document in the Semantic Layer. The unit of retrieval and the unit of relevance in retrieval evaluation. | `semantic/` | agreed |
| **Metric Definition** | A named, versioned, certified computation over the warehouse — its SQL expression, grain, filters, units, and the aliases people use for it. | `semantic/metrics/` | agreed |
| **Certified Metric** | A metric that exists in the Semantic Layer. The only kind Veritas is permitted to compute. | `semantic/metrics/` | agreed |
| **metric expression** | The SQL expression inside a query that computes a metric — the thing the Validation Gate traces. Distinct from the **Metric Definition**, which is the certified entry that publishes one, and from the **Certified Metric** it must trace to: a metric expression that traces to no Certified Metric is a **Shadow Metric**. Registered in lower case because that is how the agreed [Target State's flow](design/target-state.md#flow) — *"every metric expression traces to a Certified Metric"* — [ADR-0001](adr/0001-semantic-layer-as-the-retrieval-corpus.md) and [ADR-0003](adr/0003-validation-gate-is-deterministic-code.md) have spelled it since Step 001, and how `metric_expressions` has been spelled since Step 003. **Registered 2026-08-27** ([Sub-step 5.2](reviews/step-005-validation-gate.md#sub-step-52--the-gate-traces-every-metric-expression-to-a-certified-metric)), which is where a phrase three agreed documents already relied on became a `Rejection Reason` value as well — `no metric expression`, the statement that computes none. | `veritas/validation/` — read out of the generated SQL | agreed |
| **Shadow Metric** | A metric computed inline in a query instead of drawn from the Semantic Layer. The failure mode Veritas exists to prevent. A **metric expression** that traces to no Certified Metric is one. **Amended 2026-08-27** ([R13](plan/step-005-validation-gate.md#r13--aminos-rulings-on-the-52-review--decided-2026-08-27)): the *Lives in* cell read *"— (an anti-pattern)"*, which was true while nothing in the repository named one. Sub-step 5.2 made it `RejectionReason.SHADOW_METRIC`, the verdict the Validation Gate returns on a statement whose metric expressions do not all trace, so the anti-pattern now has a code identifier and a reader checking this row before naming something can see where it is spelled. What it still does not have is a file: no Semantic Entry publishes a Shadow Metric, which is what the old cell was saying and what the parenthetical beside the path keeps. | `veritas/validation/` — as a Rejection Reason (no file publishes one) | agreed |
| **Ambiguous Term** | A word users say that maps to two or more Certified Metrics and therefore has no single correct answer. Not a metric — an instruction to disambiguate before generating SQL. | `semantic/ambiguous/` | agreed |
| **Dimension Definition** | A certified axis for *slicing* a metric — the answer to "by what?". Names the column, its grain, and its allowed values, so "by region" always means the same column with the same buckets. The five certified axes, each written here as `(columns — grain — allowed values)`: **by trade date** (`fct_trade.trade_date` — daily), **by snapshot date** (`fct_position_snapshot.snapshot_date` · `fct_balance_snapshot.snapshot_date` — daily), **by accounting movement date** (`fct_accounting_movement.movement_date` — daily), **by region** (`dim_client.client_region` — one Client — EU · UK · APAC), **by instrument type** (`dim_instrument.instrument_type` — one Instrument — equity · ETF · future · currency pair). A date axis enumerates no allowed values, because its values are minted by the data rather than registered here. "Net Revenue **by region** last quarter" applies the region Dimension Definition to the Net Revenue metric. **Amended 2026-08-24** ([Sub-step 4.5](plan/step-004-semantic-layer.md#45--write-the-dimension-definitions)), approved 2026-08-25 ([R11](plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)): this cell listed three *examples*, one of them *"by date (`trade_date`, daily)"* — quoted without its bold here so the check does not read the quotation as a sixth axis — where `semantic/dimensions/` now publishes five certified axes, and `check_semantic_layer.py` reads this cell back against them. One axis named `trade_date` could not be applied to a Snapshot metric, whose route never reaches that column, so the single date axis became the three the Warehouse actually keys on; the instrument-type sweep of 2026-08-05 is recorded in the amendments above rather than in the parenthetical, which now holds only what the check reads. **Amended 2026-08-28** ([Sub-step 5.5](plan/step-005-validation-gate.md#55--the-gate-requires-the-access-profiles-predicate-admits-a-slice-route-and-pays-debt-020)), pre-approved 2026-08-25 as part of [R1](plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25): an axis also declares **the routes that reach it** — the map from a metric's `from_table` to the Join Paths that reach this axis's columns from there, so that an axis is applicable rather than merely certified. The routes themselves are **not** listed here: `semantic/dimensions/` holds them and `check_semantic_layer.py`'s check 19 walks them, for the reason [DEBT-017](debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) is already open about this cell. An axis that names no route from a fact table is not reachable from it, and a slice by it is refused by name. | `semantic/dimensions/` | agreed |
| **Join Path** | A certified route between two warehouse tables, so the model never invents a join. | `semantic/joins/` | agreed |
| **Route** | Where a statement's rows come from: the tables it starts at, and the joins it reaches the rest of them through. Read off a parse tree, or built from a Metric Definition's `from_table` and `join_paths`, so that what a query took and what the corpus certifies can be compared as values. A **Join Path** is one certified hop between two tables and is published as a file; a Route is the whole chain plus where it starts, and is never published — `Traded Notional`'s Route is two Join Paths and `fct_trade`, `Trade Count`'s is no Join Paths and `fct_trade`. **Registered 2026-08-28** ([R15](plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28)), where Sub-step 5.4 made the word a class in `veritas/validation/` and the Gate gained the rule that compares the two. **Amended 2026-08-28** ([Sub-step 5.5](plan/step-005-validation-gate.md#55--the-gate-requires-the-access-profiles-predicate-admits-a-slice-route-and-pays-debt-020)), approved 2026-08-29 ([R16](plan/step-005-validation-gate.md#r16--aminos-rulings-on-the-55-review--decided-2026-08-29)): a Route is built from a Metric Definition's `from_table` and `join_paths` **or from a Dimension Definition's `routes`**, and the Route the Validation Gate permits a statement is the union of the two plus the route the Access Profile's predicate needs. Still never published: no file is a Route, and the entries publish the fields one is built from — which is the reading R16 approved, over renaming the field away from the plural of this term or leaving the row describing only the Metric Definition half. | `veritas/validation/` — read from a statement or from a Metric Definition's fields (no file publishes one) | agreed |
| **Grounding** | The step where retrieved Semantic Entries constrain SQL generation. Ungrounded generation is forbidden, not merely discouraged. | `veritas/grounding/` | agreed |
| **Validation Gate** | Deterministic, non-LLM checks a query must pass before execution: certified-metrics-only, no restricted columns, access policy applied, cost bounded, read-only. | `veritas/validation/` | agreed |
| **Access Profile** | The identity Veritas runs a question as — role and permitted region. Determines which rows and columns the Validation Gate allows. | `veritas/validation/` | agreed |
| **Restricted Column** | A column an Access Profile forbids from appearing in a Grounded Answer's projection. *In the projection* is judged on the parse tree once `SELECT *` has been expanded against the real schema: the name in a comment, in a string literal, or in a filter is not a projection of it. | `veritas/validation/` | agreed |
| **Validation Gate outcome** | The verdict the Validation Gate returns: allowed or rejected, the Rejection Reasons that fired, the explanation a caller shows a person, and the rule set the decision was taken under. What a Grounded Answer carries, what the App renders, and what Observability charts. | `veritas/validation/` | agreed |
| **Rejection Reason** | One member of the stable taxonomy a rejected Validation Gate outcome carries — the thing *"Validation-Gate rejections by reason"* is grouped by. The **members** are registered in `veritas/validation/`, where the Gate enumerates them, and deliberately not in this cell: a vocabulary inside one table cell read by a prose parse is [DEBT-017](debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell), opened four days before this row and still open. | `veritas/validation/` | agreed |
| **Grounded Answer** | The response object: the answer, the SQL, the Lineage, and the Validation Gate outcome. Veritas never returns a bare number. | `veritas/` | agreed |
| **Clarifying Question** | What Veritas returns instead of an answer when a question says an **Ambiguous Term** and nothing resolved which Certified Metric was meant: the question Veritas asks back, naming each unresolved term and the metrics it could mean. Not a **refusal** — a refusal says the question cannot be answered, a Clarifying Question says it is not answerable *yet* and what would settle it. They are the two ways a **Grounded Answer** carries no number, and one carrying both says two different things about one question, which is why `GroundedAnswer` refuses to be built that way. Rendered by the App, and grouped over by Observability as a `Validation Gate outcome` is grouped by its `Rejection Reason`. **Registered 2026-09-01**, proposed by [Sub-step 6.3](reviews/step-006-retrieval-and-orchestrator.md#sub-step-63--resolve-ambiguous-terms-before-retrieval) when the rewrite step gave the concept a field and left it unnamed. Agreeing it renamed `clarification` to `clarifying_question` on both `Rewrite` and `GroundedAnswer`, and `clarification_for` to `clarifying_question_for`. | `veritas/orchestrator/` | agreed |
| **Lineage** | The record of which Semantic Entries and which Metric Definition versions produced a Grounded Answer. What makes an answer auditable. | `veritas/` | agreed |
| **Gold Question Set** | The evaluation corpus: question, gold SQL, gold result, and the Semantic Entries the gold SQL touches. | `data/gold/` | agreed |
| **Gold Question** | One member of the **Gold Question Set**: the question as a person asks it, which of a **Grounded Answer**'s three endings is correct for it, and — where that ending is a number — the gold SQL and the gold result. One file under `data/gold/`, read by the `GoldQuestion` dataclass whose field list is that file format. Its **Relevant Set** is not one of its fields: a Gold Question says what the *answer* should be, and what the *corpus* should have been searched for is derived from its statement. **Registered 2026-09-01** ([Sub-step 7.1](reviews/step-007-evaluation.md#sub-step-71--write-the-gold-question-set)), where the set's members became files and a class; the set had a row since 2026-08-04 and the thing it is a set of did not. | `data/gold/` | agreed |
| **Relevant Set** | The Semantic Entries one **Gold Question**'s gold SQL touches — what a Retrieval ranking is scored against, and the [Target State](design/target-state.md#zoomcamp-criteria-map)'s *"ground truth is derived"* in one noun. **Derived, never written down**: the Certified Metrics the statement's projections trace to, the certified axes it groups by or filters on, and the Join Paths those two declare, all read through `veritas/validation/`'s own readers. Distinct from **Lineage**, which records the entries an answer *was* built from: a Relevant Set is what a correct answer *would have needed*, so the two are the two sides hit rate and Mean Reciprocal Rank compare. A question whose correct ending is a refusal or a **Clarifying Question** has an empty one. **Registered 2026-09-01** ([Sub-step 7.1](reviews/step-007-evaluation.md#sub-step-71--write-the-gold-question-set)), where `relevant_entries` made the Target State's own phrase a function. | `veritas/evaluation/` — derived from a gold SQL (no file publishes one) | agreed |
| **Execution Accuracy** | Share of generated queries whose result set matches the gold result. The primary correctness measure — objective, unlike a judge's opinion. | `veritas/evaluation/` | agreed |
| **Reporting Currency** | The single currency a Grounded Answer is expressed in. Every monetary metric must state one. | `semantic/metrics/` | agreed |
| **Warehouse** | The analytical store holding the brokerage star schema — the `fct_` and `dim_` tables of Section B. DuckDB for the slice. Reached **only** through the Warehouse Adapter; no component queries it directly. | `veritas/warehouse/` | agreed |
| **Warehouse Adapter** | The single boundary through which all Warehouse access passes. Holds the connection and the engine's dialect; nothing DuckDB-specific exists outside it. The seam an engine swap lands on. | `veritas/warehouse/` | agreed |
| **Ingestion** | The pipeline that fills the Warehouse: real FX Rates, Market Prices and instrument reference data from key-free public sources, snapshotted into the repository and replayed by default; synthetic Trades, Cash Movements and Positions from a seeded simulator. **Market data real, client activity synthetic — never the reverse.** | `veritas/ingestion/` | agreed |
| **Retrieval** | The step that turns a question into the Semantic Entries needed to answer it. Searches the Semantic Layer **only** — never Warehouse schema, never free text. Hybrid text + vector, re-ranked. | `veritas/retrieval/` | agreed |
| **Retrieval Strategy** | Which search one call of Retrieval runs over the corpus — the thing an Evaluation Measure is grouped by when Retrieval's hit rate and MRR are compared, as a Validation Gate outcome is grouped by its Rejection Reason. Not a second word for **Retrieval**: Retrieval is the step, and a Retrieval Strategy is which of its searches that step ran, so two of them over one corpus return different entries for one question and are comparable by measure. The **members** are registered in `veritas/retrieval/`, where `RetrievalStrategy` enumerates them, and deliberately not in this cell for the reason [DEBT-017](debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) is open about. **Registered 2026-08-30** ([Sub-step 6.2](reviews/step-006-retrieval-and-orchestrator.md#sub-step-62--retrieve-semantic-entries-for-a-question)), where Sub-step 6.2 made the word a class and gave a call a parameter Step 007 must measure the arms of — the same trigger that registered `Route` in 5.4. `Retrieval Approach` was considered and rejected: one concept, one word. | `veritas/retrieval/` — as an enumeration (no file publishes one) | agreed |
| **Orchestrator** | The component that runs a question through the seven-step flow: rewrite, retrieve, ground, generate, validate, execute, answer. Owns the sequence and the failure paths; owns none of the steps' logic. Renamed from `Copilot` on 2026-08-04 — Veritas *is* a copilot, so the word could not also name one component inside it. | `veritas/orchestrator/` | agreed |
| **App** | Where a person asks a question and reads a Grounded Answer — with its SQL, its Lineage and its Validation Gate outcome. **Never renders a bare number.** Renamed from `Interface` on 2026-08-04, so the name matches the directory and does not collide with the rubric's own "Interface" criterion. | `veritas/app/` | agreed |
| **Observability** | Records what happened at runtime: every question, Grounded Answer, Validation Gate outcome, cost, latency and Feedback — the Question Log. Produces Operational Measures. **Records; never judges.** Live traffic, no ground truth. | `veritas/observability/` | agreed |
| **Evaluation** | Computes Evaluation Measures over the Gold Question Set: hit rate and MRR for Retrieval, Execution Accuracy and LLM-as-judge for generation. **Offline, against known-correct answers** — the opposite pole from Observability. | `veritas/evaluation/` | agreed |
| **Question Log** | The record Observability keeps: one row per question a person asked through the App, carrying its Grounded Answer, Validation Gate outcome, Lineage, Operational Measures and Feedback. The seam `veritas/observability/` exposes and the tables behind it. Not the **Gold Question Set**: a Question Log row is live traffic with no ground truth; a Gold Question is ground truth with no traffic. **Registered 2026-09-03** ([Step 008 plan](plan/step-008-observability.md#language)), where the phrase [EXT-004](extension-register.md#ext-004--coverage-miss-capture)'s seam cell had carried since Step 001 — *"the Observability question log"* — became the seam Sub-step 8.3 builds; the cell now spells it as registered. | `veritas/observability/` | agreed |
| **Feedback** | What a person says about a Grounded Answer they were shown: a verdict, up or down, and optionally a sentence. Attached to that answer's **Question Log** row and never to the question text alone, so Feedback on an answer is Feedback on *that* SQL, Lineage and Validation Gate outcome, and a later answer to the same words inherits none of it. The one of **Operational Measure**'s four — cost, latency, Validation Gate outcome, Feedback — that had no row of its own. Not an **Evaluation Measure**: a verdict is live traffic, and nothing scores it against a gold result. **Registered 2026-09-03** ([Step 008 plan](plan/step-008-observability.md#language)), ahead of Sub-step 8.4, which makes it a widget in the App and a column in the Question Log. | `veritas/observability/` — offered by the App | agreed |

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
  reporting Feedback as accuracy, or expecting hit rate from production.
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

#### `Validation Gate outcome` and `Rejection Reason` — `agreed` 2026-08-25

Proposed by the Step 005 plan and ruled the same day
([R3](plan/step-005-validation-gate.md#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)),
written into the table when Sub-step 5.1 made them code identifiers.

- **`Validation Gate outcome` was already in use and had never been defined.** Three
  agreed rows name it — `Grounded Answer`, `App` and `Observability` — so it was a
  compound the Glossary relied on and did not register.
- **`Rejection Reason` is the taxonomy
  [ADR-0003](adr/0003-validation-gate-is-deterministic-code.md) sold determinism on.**
  Without a registered name the same concept becomes a reason code in the Gate, a
  chart label in Grafana and a string in the App — three names for one thing, which
  is the disease Non-Negotiable #1 exists to prevent. The **members** are enumerated
  in `veritas/validation/` rather than in the row, for the reason R3 gives.

### B. The warehouse

What the data describes. A brokerage: clients hold accounts, accounts trade
instruments, trades move cash and change positions.

| Term | Definition | Lives in | Status |
|---|---|---|---|
| **Instrument** | A tradable asset — equity, ETF, future, or currency pair. Single bonds and options are **out of scope**: neither has a key-free Market Price source, so holding them would mean fabricating prices while claiming market data is real. Bond exposure is represented through bond ETFs, which is how most brokerage clients hold bonds anyway. Narrowed 2026-08-03; see [DEBT-003](debt-ledger.md). | `dim_instrument` | agreed |
| **Instrument Symbol** | The ticker identifying an Instrument, and the natural key every source keys on — NASDAQ Trader's `Symbol` column, the SEC's ticker, and the symbol Yahoo's chart endpoint is queried by. Unique. Registered 2026-08-05: without it the price and reference feeds have nothing to join an Instrument on. | `dim_instrument` | agreed |
| **Client** | The legal owner of one or more Accounts. The entity a region or segment attaches to. | `dim_client` | agreed |
| **Account** | The container trades and cash sit in. Has exactly one Client and one or more currency balances. | `dim_account` | agreed |
| **Trade** | One executed order: an Account buys or sells a quantity of an Instrument at an Execution Price, on a Trade Date, settling on a Settlement Date. | `fct_trade` | agreed |
| **Execution Price** | The price a Trade actually filled at, in the Instrument's Quotation Currency. Distinct from Market Price, which is that day's close for the Instrument as a whole: a Trade fills at whatever the market gave it at that moment, which is not the close except by coincidence. Trades are valued at Execution Price; Positions are marked at Market Price. Registered 2026-08-05 — the Glossary had been calling this "price". | `fct_trade` | agreed |
| **Trade Side** | Whether a Trade bought or sold: `buy` or `sell`. The direction the `Trade` row described — *"an Account buys or sells"* — without ever naming it. Registered 2026-08-05 in preference to a signed quantity, so `quantity` is always positive and `Traded Notional` stays literally true as it is written below, with no undocumented absolute value hidden in the metric. | `fct_trade` | agreed |
| **Traded Notional** | Σ(quantity × Execution Price) converted to the Reporting Currency. The monetary size of trading activity. | `semantic/metrics/` | agreed |
| **Trade Count** | Number of Trades. Deliberately separate from Traded Notional — they answer different questions. | `semantic/metrics/` | agreed |
| **Commission** | What the broker charges the Client for executing a Trade. Broker income. | `fct_trade` | agreed |
| **Fee** | A third-party charge passed through to the Client — exchange, clearing, regulatory. Collected by the broker but not earned by it. | `fct_trade` | agreed |
| **Rebate** | Value returned to a Client or introducing partner out of Commission already charged. Reduces what the broker keeps. | `fct_trade` | agreed |
| **Gross Revenue** | Σ(Commission) before any Rebate or pass-through Fee is deducted. | `semantic/metrics/` | agreed |
| **Net Revenue** | Gross Revenue − Rebate − pass-through Fee. What the broker actually keeps. | `semantic/metrics/` | agreed |
| **Cash Movement** | Money actually entering or leaving an Account on a given date — deposits, withdrawals, settlement, fee charges. | `fct_cash_movement` | agreed |
| **Accounting Movement** | A ledger entry recognising economic value on the date it was *earned*, whether or not cash moved. | `fct_accounting_movement` | agreed |
| **Cash Balance** | Money held in an Account in one currency at a point in time. Cash only. **Amended 2026-08-22** ([R1 of Step 004](plan/step-004-semantic-layer.md#r1--cash-balance-becomes-a-certified-metric--approved-by-amino-2026-08-21)): it is a Certified Metric as well as a column, because two [Section D](#d-ambiguous-terms) Ambiguous Terms — "balance" and "how much does X have" — resolve to it, and an Ambiguous Term that disambiguates to something with no Metric Definition to retrieve is the incoherence [EXT-005](extension-register.md#ext-005--semantic-layer-coherence-checks) lists as its fourth rule. | `fct_balance_snapshot`, `semantic/metrics/` | agreed |
| **Account Value** | Cash Balance plus all Positions marked to market, in the Reporting Currency. | `semantic/metrics/` | agreed |
| **Snapshot** | The state of a subject **as of the close of** a date, at a grain of one row per subject per date. Authoritative for *"what was held as of D"* and nothing else: a Snapshot cannot see between its own dates, so a Position opened and closed inside one day leaves the Snapshots either side of it identical. End-of-day is part of the definition, not a loading detail — a Position marked at that date's closing Market Price must be the Position held at the close. Written on every date the Warehouse holds a Market Price for, so an "as of" question is an equality join rather than a most-recent-row-at-or-before lookup. Registered 2026-08-06. | `fct_position_snapshot`, `fct_balance_snapshot` | agreed |
| **Position** | Quantity of one Instrument held by one Account at a point in time. | `fct_position_snapshot` | agreed |
| **Position Change** | Change in a Position between two points in time, from any cause — a Trade, a transfer, or a corporate action. | `semantic/metrics/` | agreed |
| **Cost Basis** | What a held Position cost to acquire, in the Instrument's Quotation Currency — the total for the held quantity, accumulated across the Trades that built it. The quantity both Realised and Unrealised P&L are measured against: neither is computable without it, since a Market Price alone says what a holding is worth and not what it gained. Signed, tracking the Position's own sign, so a short's proceeds are negative and one expression covers both directions. Registered 2026-08-06. | `fct_position_snapshot` | agreed |
| **Realised P&L** | Profit or loss locked in by closing a Position. | `semantic/metrics/` | agreed |
| **Unrealised P&L** | Profit or loss on a Position still held, at current market price. Moves with the market; nothing has been banked. | `semantic/metrics/` | agreed |
| **FX Rate** | The rate between two currencies on a date, from the real ECB reference rates published against the euro and sourced from the public Frankfurter API. A pair with the euro on one side **is** a published reference rate; a pair between two non-euro currencies is the **ratio of that date's two published rates** — the cross-rate, which is what Frankfurter itself returns under a non-euro base. Both are FX Rates and both are stored; a rate of any other origin is not one. Published on working days only, so a rate for a non-publishing date is the most recent published rate at or before it. **Clarified 2026-08-11** (R19): the earlier wording, *"Real ECB reference rate between two currencies on a date"*, read both ways once `fct_fx_rate` held every ordered pair of its currencies rather than the euro ones alone. | `fct_fx_rate` | agreed |
| **Market Price** | The unadjusted closing price at which an Instrument traded on a date, in its Quotation Currency. The only price a Position may be marked at. | `fct_instrument_price` | agreed |
| **Adjusted Close** | A price series back-adjusted for splits and dividends, which rewrites historical prices as later corporate actions occur. Correct for computing returns; **forbidden** for marking Positions or computing P&L. | — (an anti-pattern) | agreed |
| **Quotation Currency** | The currency *and minor unit* an Instrument's Market Price is quoted in — LSE quotes in pence (`GBp`), not pounds. Normalising to major units is a required ingestion step. Distinct from Reporting Currency. | `dim_instrument` | agreed |
| **Denomination Currency** | The currency a monetary amount in a fact row is *held* in — a Cash Movement's amount, an Accounting Movement's amount, a Cash Balance, and a Trade's Commission, Fee and Rebate. The third currency sense, and the one with no Instrument and no answer attached to it: a broker does not necessarily charge in the currency an Instrument is quoted in, so Traded Notional and Gross Revenue take different routes through FX Rate to reach the Reporting Currency. Registered 2026-08-05. | `fct_trade`, `fct_cash_movement`, `fct_accounting_movement`, `fct_balance_snapshot` | agreed |

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
| **Execution Price** | **Market Price** | Both are a price of the same Instrument on the same date, and neither is the wrong one — they answer different questions. Traded Notional at the close values trading that never happened at that price; a Position marked at whatever a Trade happened to fill at is a mark to one order rather than to the market. Registered 2026-08-05, because the two were about to become `fct_trade.price` and `fct_instrument_price.market_price` — the same word for two numbers, which is the disease Section C exists to catch. |
| **Adjusted Close** | **Market Price** | Measured on real data, not assumed: the two differ on **nearly every bar** — 1,198 of 1,255, on a five-year daily AAPL request, checked 2026-08-03 ([data-availability.md](design/data-availability.md)) and reproducible offline with `uv run python .claude/scripts/check_data_availability.py`; the evidence table is in the [Step 001 review](reviews/step-001-target-state-design.md). Adjusted Close rewrites history every time a dividend is paid, so a Position marked at it yields an Account Value that is both wrong and *irreproducible* — the same query returns a different number next quarter. |
| **Quotation Currency** | **Reporting Currency** | A Market Price is quoted in the Instrument's own currency and minor unit; a Grounded Answer is expressed in one Reporting Currency. Skipping the conversion is an FX-sized error; missing the minor unit is a **100×** error — LSE quotes pence, and £4.20 booked as £420 looks entirely plausible. |
| **Cost Basis** | **Execution Price** | An Execution Price is what *one* Trade filled at; a Cost Basis is what the *whole holding* cost, accumulated across every Trade that built it and carried on the Position rather than the Trade. Marking Unrealised P&L against the latest Execution Price prices the holding at the last thing that happened to it, which for a position built over six months is a number with no relationship to what it cost. The two are also different shapes — one is per unit, the other is a total — so substituting one for the other is off by a quantity as well as by a price. Registered 2026-08-06. |
| **Denomination Currency** | **Quotation Currency** | Both sit on `fct_trade` and they are not the same column. `quantity × Execution Price` is in the Instrument's Quotation Currency; Commission, Fee and Rebate are in the Trade's Denomination Currency, because a broker charges in the currency it bills in rather than the one the exchange quotes in. Assuming they are equal converts Gross Revenue through the wrong FX Rate — a plausible number, off by a currency pair. Registered 2026-08-05, when both were about to become one word. |

### D. Ambiguous Terms

Words users genuinely say that are **not** metrics. Veritas must resolve them
before generating SQL — never guess silently.

| User says | Could mean | Resolution | Also said as |
|---|---|---|---|
| "revenue" | Gross Revenue · Net Revenue | Ask, unless the question names one | revenues |
| "volume" | Traded Notional · Trade Count | Ask | volumes · turnover |
| "balance" | Cash Balance · Account Value | Ask | balances |
| "P&L" | Realised P&L · Unrealised P&L · both | Ask | PnL · P and L · P & L · P/L |
| "how much does X have" | Cash Balance · Account Value | Ask | how much is in X · how much does X hold |

**Amended 2026-09-01 (Sub-step 7.2), agreed by Amino the same day.**
*Also said as* is the other spellings of the same word — what a person types when
they do not type the registered one. A spelling here is **the registered term**: it
is detected exactly as the *User says* cell is, resolved against the same *Could
mean* pair, and `X` stands for the subject in a phrase as it does in the row above.
`semantic/ambiguous/` publishes the cell as the entry's `aliases`, and
`tests/test_rewrite.py` reads it back against them, so this table and the corpus
cannot drift apart silently. Without the column, every one of these spellings
reached SQL generation as though the question had been unambiguous — not refused
and not asked back, but silently — which is what
[DEBT-029](debt-ledger.md#debt-029--ambiguous-term-detection-is-literal-so-every-other-phrasing-of-a-registered-word-passes-silently)
records and this amendment pays.

**"turnover" moved, and it could only go to one of the two places.** It was an
alias of `Traded Notional` in `semantic/metrics/`, which made it a word Veritas
answers with a number; it is registered here as a spelling of "volume", which makes
it a word Veritas asks about. It cannot be both — an alias that is also an
Ambiguous Term resolves silently the very thing this section says must be asked,
which is the rule `check_semantic_layer.py`'s check 14 already enforced for the
*User says* column and this amendment extends to this one. It is here rather than
there because the reason "volume" is ambiguous is the reason "turnover" is: it
names notional to a trading desk and count to an operations team, and Veritas
serves both.

**Amended 2026-08-24 (Sub-step 4.4).** The "P&L" row's *Could mean* cell read
`Realised · Unrealised`, which is neither Section B term spelled as registered.
`semantic/ambiguous/` publishes these five rows as Ambiguous Term entries and
`check_semantic_layer.py` reads this column back against them, so the shortened
names left the row's two meanings resolvable by a reader and by nothing else — the
check named it on its first run. `both` stays as written: it is a third *answer*,
not a third Certified Metric, and the check prints it as prose rather than
resolving it.

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
| **Operational Measure** | A runtime measure logged per question and shown on the Grafana dashboard: cost, latency, Validation Gate outcome, and Feedback. | `veritas/observability/` | agreed |

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
| **Delivery Mode** | The operating mode from 2026-08-29 until the 2026-09-09 deadline. Behaviour is proven in `tests/`; `.claude/scripts/` is frozen; plans, reviews and docstrings are held to stated ceilings. Suspends nothing in the Four Non-Negotiables. Expires by its own date. | `CLAUDE.md` | agreed |

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
| **BAAI** | Beijing Academy of Artificial Intelligence | Publishes `bge-small-en-v1.5`, the sentence-embedding model `Retrieval` searches with |
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
| **NYSE** | New York Stock Exchange | Lists traded Instruments absent from `nasdaqlisted.txt`, which is why NASDAQ Trader's second file is read |
| **OHLCV** | Open, High, Low, Close, Volume | The daily price bar fields |
| **ONNX** | Open Neural Network Exchange | The runtime format both of `Retrieval`'s models ship in — no PyTorch, no key |
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
