# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**This file says what is true now. How each thing came to be true is in the dated
Step Review that produced it**, under `.claude/docs/reviews/`. That division is what
[R10 of Step 005](../plan/step-005-validation-gate.md#r10--current-state-is-trimmed-in-its-own-commit-between-the-plan-and-51--approved-by-amino-2026-08-25)
trimmed this file to on 2026-08-25, and
[R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26)
wrote the rule that keeps it short into step 5 of the `closing-a-substep` skill: a
Sub-step adds what is now true, and the story of how it got there stays in the review.

**Last updated:** 2026-08-29 — **Step 005 — Build the Validation Gate — is `active`,
and all five of its Sub-steps are built.** `veritas/validation/` refuses anything that
is not a single, parseable, bounded `SELECT`, refuses any statement whose expressions do
not all trace to a Certified Metric, refuses any statement whose answer would carry a
Restricted Column the Access Profile forbids, refuses any statement that computes a
Certified Metric across joins its Metric Definition does not name or over a date column
or without a certified filter it is not certified against, refuses any statement that
slices a metric by an axis no route reaches from it, and refuses any statement that is
not scoped to the permitted region of the Access Profile it is judged under. The
Semantic Layer is complete: all four entry types, thirty-two entries. The Warehouse is
full, every Certified Metric can return a number, and the sqlglot spike's verdict is
**GO** on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md). All five
Sub-steps are ruled, the last of them on 2026-08-29; nothing in the Step is waiting on a
decision.

---

## Resume here

- **Next: plan Step 006.** All five Sub-steps of Step 005 are built and ruled, and the
  Gate decides all five of the things the
  [Target State's flow](target-state.md#flow) says `VALIDATE` decides. The
  [5.5 review entry](../reviews/step-005-validation-gate.md#sub-step-55--the-gate-requires-the-access-profiles-predicate-admits-a-slice-route-and-pays-debt-020)
  is the handoff detail; its eleven sceptical items were all approved on 2026-08-29 as
  [R16](../plan/step-005-validation-gate.md#r16--aminos-rulings-on-the-55-review--decided-2026-08-29),
  which is where the two that needed a decision are answered — the `Route` Glossary row's
  amendment is approved, and
  [DEBT-022](../debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one)
  is left for the Sub-step its Trigger names. **Sub-step 5.5 is built, ruled and staged;
  the commit is Amino's**, and the four Sub-steps before it are already committed.
- **The [Step 005 plan](../plan/step-005-validation-gate.md) is `active`**, written and
  approved 2026-08-25 with **sixteen rulings**, the last of them
  [R16](../plan/step-005-validation-gate.md#r16--aminos-rulings-on-the-55-review--decided-2026-08-29)
  of 2026-08-29. Read the plan for what each decided.
  [R5](../plan/step-005-validation-gate.md#r5--55-is-a-pre-agreed-split-point--approved-by-amino-2026-08-25)'s
  pre-agreed split point was **not taken**: Amino ruled on 2026-08-28 that 5.5 ships as
  one Sub-step. [R1](../plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25),
  [R8](../plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)
  and [R9](../plan/step-005-validation-gate.md#r9--no-test-framework-in-this-step-and-step-002s-prediction-is-set-aside--approved-by-amino-2026-08-25)
  are now all discharged, along with
  [R2](../plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
  and [R7](../plan/step-005-validation-gate.md#r7--the-bounded-read-uses-the-engines-estimate-if-the-adapter-can-reach-it--approved-by-amino-2026-08-25).
  **Nothing in the plan is left unbuilt.**
- **The Step's Ledger entries: four settled, three open.**
  [DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)
  was paid in 5.1;
  [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)
  and
  [DEBT-019](../debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again)
  in 5.4; and
  [DEBT-020](../debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters)
  in 5.5, ahead of both its Trigger arms and by ruling.
  [DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart)
  and [DEBT-022](../debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one)
  are both open, both name the Grounding Sub-step as their Trigger, both live in
  `route_of_resolved`, and **neither is demonstrated by anything that runs** — each owes
  a probe from the Sub-step that pays it.
  [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
  is unpaid and its Trigger has still not fired; the mechanism it is honest about is now
  exactly as wide as the entry describes, which makes the unqualified claim more
  tempting rather than less.
  [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)
  and [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell)
  both came into reach in this Step and neither fired.
- **Any session resuming here runs `uv run python -m veritas.ingestion` first**, because
  the Warehouse is gitignored and the Semantic Layer, Warehouse and Validation Gate
  checks execute against real data.

## Open questions

Everything awaiting a ruling, and nothing else. Each is recorded in full where it was
raised; this list exists so a cold session does not have to find them.

| Question | Where it is argued | Blocks |
|---|---|---|
| Does the `resolution` field name want a Glossary row? | [Step 004 R10](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24) left it open, and R11 did not reach it | Nothing — no file changes either way. The one question Step 004 closes without answering |

**Two questions travel on to [Retrieval](../glossary.md#a-the-system)**, both ruled
2026-08-24 as
[R10](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24)
and neither a defect in anything built:

1. **A partial alias match can resolve an Ambiguous Term silently.** `Unrealised P&L`
   claims the alias *"paper profit and loss"* and `Realised P&L` claims *"booked profit
   and loss"*, so a user who types **"profit and loss"** is a short hop from either
   metric while matching the `P&L` Ambiguous Term by no name at all — check 14 compares
   whole strings. The two candidate fixes are an `aliases` field on the Ambiguous Term
   entry or a Retrieval rule that an Ambiguous Term outranks a metric it disambiguates
   to; choosing between them without Retrieval to measure is speculation.
2. **The five Ambiguous Term `description` fields are unchecked prose, and they are what
   Retrieval will embed.** Text written to be embedded is tuned against a measurement or
   not at all.

**Two travel on to [Grounding](../glossary.md#a-the-system)**, both ruled 2026-08-25 as
[R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25).
R11 handed it three; **Sub-step 5.5 answered the first** under R1's widening — `by
region` has a route and the Gate has the rule that lets a `GROUP BY` use it — so two
remain:

1. **There is no `by settlement date` axis, and it is deferred rather than rejected.**
   The column exists and holds real dates, but every Metric Definition keys its period
   filter on `trade_date`, so certifying it would let one question be *sliced* on one
   date while being *filtered* on another — a
   [Section C](../glossary.md#c-distinctions-we-must-not-blur) pair blurred by an axis.
2. **Check 17 forecloses an axis whose values are data but not dates.** A
   `by denomination currency` axis would have to enumerate codes ingestion minted, and
   an enumeration of minted values is a measurement living in the corpus. The rule is
   not loosened; what is open is **where** such an axis gets decided.

---

## Summary

A fully designed project with three of its nine components built and a fourth begun.
The framework is in place and the Target State is `agreed`, so there is a fixed point
to build toward: a natural-language analytics copilot over a brokerage warehouse, whose
answers are grounded in a certified Semantic Layer and checked by a deterministic
Validation Gate.

**The Warehouse is full.** The ten-table star schema of
[Glossary Section B](../glossary.md#b-the-warehouse) sits behind the Warehouse Adapter —
the only module in the repository that imports `duckdb`, and the only place a
DuckDB-specific function name appears, both checked rather than promised — and all ten
tables hold rows. Three are real: `dim_instrument`, `fct_instrument_price` and
`fct_fx_rate`, from key-free public sources snapshotted into the repository. Seven are
synthetic, from a seeded simulator that prices every Trade off a Market Price the
Warehouse already holds and converts through a real FX Rate. **One command builds all
ten offline from committed snapshots with no socket opened, and two runs are
byte-identical.**

**Every Certified Metric can return a number** — all nine — and every pair in
[Glossary Section C](../glossary.md#c-distinctions-we-must-not-blur) is two measurably
different numbers on the loaded data. Row counts, windows and Section C figures are
dated evidence in the
[Step 002 review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-25--generate-seeded-synthetic-client-activity),
because a `--refresh` moves them.

**The Semantic Layer is complete** — all four entry types
[Glossary Section A](../glossary.md#a-the-system) registers, thirty-two entries. A
Metric Definition publishes its expression as the text an Orchestrator pastes verbatim,
plus the route and the date predicate that expression does not pin down. Ambiguous Terms
carry the claim [ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md)
rejected schema retrieval for — that *"revenue"* has two certified meanings. Dimension
Definitions carry the answer to *"by what?"*, checked against the buckets the Warehouse
actually holds and — since Sub-step 5.5 — the routes that reach each axis from each fact
table a metric starts at, so an axis says where it is applicable as well as what it
means. Nothing above the Semantic Layer is built: no Retrieval, no Orchestrator, no
application, and nothing turns a question into SQL. **The corpus can be sliced and does
not yet slice anything** — applying an axis to a metric is a query.

**The Validation Gate refuses anything that is not a bounded read, anything that
computes a metric the Semantic Layer does not certify, anything whose answer would
carry a Restricted Column, anything that computes a certified metric over rows its
own Metric Definition does not describe, and anything that is not scoped to the identity
asking it.** `veritas/validation/` holds the
`Validation Gate outcome` and the `Rejection Reason` taxonomy as a contract a consumer
can import without importing a rule, the `Access Profile` a statement is judged under,
and eight rules behind them. Four judge a statement's
shape: sqlglot cannot read it, it holds more or fewer than one statement, it is not a
`SELECT`, or the planner expects it to scan past a declared ceiling. The fifth reads the
corpus — every projection that aggregates is canonicalised and looked up in the nine
Certified Metrics loaded from `semantic/metrics/`, and the statement is allowed only if
at least one is found and **all** of them trace. The sixth reads an identity: every
output column's lineage is walked back to the base-table columns feeding it, and a
statement is refused if the Access Profile forbids one of them — *reaching the answer*
rather than *appearing in the statement*, so a restricted name in a comment, in a string
literal, in a filter, or aggregated away inside a subquery is not a projection of it. That
identity is an argument to `judge`, not a field on the Gate, so one Gate serves many
identities over one loaded corpus. The seventh reads the rows underneath the
projection: the joins a statement carries are compared with the Join Paths the metric it
traces to names and the axes it groups by declare, the date columns its WHERE clause keys
on with that metric's `date_column`, and its WHERE clause's conjuncts with that metric's
certified `filters` — so a certified expression converted through the wrong currency,
filtered on the wrong half of a Section C date pair, or computed with its defining
predicate dropped is refused, and so is a slice by an axis no route reaches from that
metric. **Permission comes from a list with three sources and no fourth** — the metric's
own `join_paths`, the `routes` of each axis the statement groups by, and the route the
Access Profile's predicate needs — and the Gate never searches for a chain that would
reach a table, so a join no entry names is a rejection rather than a search. The eighth
reads the identity again and asks one question of the outermost WHERE clause: is the
Access Profile's predicate there. **Present on every statement**, because a query that
never joins `dim_client` reads every region's rows and names none of them.
Each rejection carries its own named reason, thirteen in the taxonomy. The scan estimate
and the column list both come from the
engine through the Warehouse Adapter, which is the only place the plan format and the
catalogue query are known. Nothing anywhere executes a statement through it.

**The design's largest unproven assumption is now measured.** That sqlglot can decide
from a parse tree alone whether a generated query computes a Certified Metric was probed
on the real schema and the real data, on all four of the claims Step 002 deferred, and
the verdict is **GO on
[ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)**, recorded in
[validation-feasibility.md](validation-feasibility.md), the project's second design gate
beside [data-availability.md](data-availability.md). Two of the six constraints it
carries are sharp enough to restate anywhere: a certified expression is recognised **by
form**, so a paraphrase of it is refused and the Semantic Layer must publish a form the
Orchestrator pastes; and a certified expression **does not pin down the join**, so a
query converting through the wrong currency column traces and is wrong by a margin the
spike prints on every run. The second of those is now **enforced** rather than only
recorded: the Gate reads the route as well as the projection, and the query is refused
on both sides. The
fourth claim, which is ADR-0002's rather than ADR-0003's, is qualified: every parse-tree
verdict survives retargeting to BigQuery and one type does not.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Four declared dependencies**: `duckdb`, `dlt`, `sqlglot` and `pyyaml`. dlt brings the bulk of the transitive tree. Two check scripts are standard-library-only — `verify_framework.py` and `check_data_availability.py`; the other four and the `check_validation_gate/` package import third-party code. Everything imported anywhere is one of the four declared libraries. |
| Development framework | ✅ working | `CLAUDE.md`, the `.claude/docs/` tree, five skills in `.claude/skills/`. Non-Negotiable #4 carries the rule that **an exemption is scoped to where it is needed** — a check that excuses something names the file as well as the symbol, never a symbol alone. `closing-a-substep` step 5 carries the rule that keeps **this** file short: a Sub-step adds what is now true and the story of how it got there goes to the review, so a passage narrating a Sub-step is a defect here even when accurate. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only: documents exist, links resolve, skills load, interpreter pinned. Passes. **Links include their `#anchor`**, and a `dead anchor` is reported distinctly from a `dead link`; it prints how many links and anchors it checked. **Its scope includes code**: every `.py` file under `veritas/` and `.claude/scripts/` is read for markdown links too, because docstrings cite ADRs and Ledger entries in the same syntax — a link inside a `.py` file may point at the same things a link inside a document may, resolved the same way, anchor required. That is [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s second coverage gap, paid. `README.md` is outside the scope, and so are the skills: a skill is checked for loading and for a trigger-shaped description, but the markdown links in its body are not resolved — `writing-an-adr` has two and nothing reads them. |
| Language check | ✅ working | `.claude/scripts/check_language.py` — content rules: component names registered, no `proposed` term in code, abbreviations resolvable. Passes. Parses code with `ast` so it checks identifiers, not prose. Derives the shouted keywords of the SQL this project writes rather than remembering them, from **three** bodies: the hand-authored `.sql` files, the SQL fields a Semantic Entry publishes, and the statements written as Python string literals — the third asks sqlglot which literals are statements, exactly as `check_warehouse.py`'s dialect scan does. That is why it reads the corpus and is not standard-library-only. One keyword is listed by hand with its reason beside it, `FORMAT`, because the adapter holds `EXPLAIN (FORMAT json) ` as a fragment and a fragment parses as nothing. Partial payment of [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement). |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`. The term count is whatever `check_language.py` prints. Two rows are read back mechanically rather than by a reader: Section D's *Could mean* column and Section A's `Dimension Definition` row, which registers the five certified axes with their columns, their grain and their buckets in the form `check_semantic_layer.py` parses. The second of those is [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) — a registry inside one table cell, where the other two this project reads back are tables with a row per entry. |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — real 2025 FX Rates and three real price series, plus the dated probe record, owned by `check_data_availability.py`. `data/snapshots/ingestion/` beside it is the pipeline's own, one file per source and one per traded Instrument, rewritten only by `--refresh`. Both committed on purpose: they are what make the checks reproduce without network access. |
| Founding ADRs | ✅ working | Four ADRs in `.claude/docs/adr/`, all **`accepted`**: 0001 Semantic Layer as the retrieval corpus, 0002 DuckDB behind an adapter, 0003 Validation Gate as deterministic code, 0004 snapshot-and-replay and where dlt stops. Every cost in each is classified *accepted* / *debt* / *extension*. ADR-0002 carries a dated clarification on what its sqlglot commitment forbids, and both 0002 and 0003 carry a dated status note pointing at [validation-feasibility.md](validation-feasibility.md); no status changed. |
| Warehouse | ✅ working | `veritas/warehouse/schema.sql` — the ten tables of [Glossary Section B](../glossary.md#b-the-warehouse), **all ten populated**. Monetary columns are `DECIMAL(18, 6)`, FX Rates `DECIMAL(18, 8)`; **no floating-point column exists** and `check_warehouse.py` fails the run if one appears. Foreign keys declared and enforced. Snapshot grain is one row per subject per date, enforced by the primary key. No `dim_date`. The two movement tables carry **opposite sign conventions** and the schema says so beside each column: cash is signed from the Account's side, accounting carries magnitudes so that Net Revenue = Σcommission − Σrebate − Σfee is literally true. |
| Warehouse Adapter | ✅ working | `veritas/warehouse/adapter.py` — the only module in the repository that imports `duckdb`, which is checked rather than promised. `create_schema`, `tables`, `columns`, `columns_by_table`, `row_count`, `execute`, `query` and `estimated_scan_rows`, plus the `in_memory()` constructor for throwaway databases. Assembles no SQL text from any argument: introspection goes through `information_schema` with a bound parameter, row counts through the relational API. `columns_by_table` returns the whole catalogue in the shape sqlglot's optimizer calls a schema, in **one** query rather than one per table, because the Validation Gate reads it on every judgement. `estimated_scan_rows` is the one method that assembles anything — it prefixes the engine's `EXPLAIN`, in the JavaScript Object Notation (JSON) form that returns a plan with a number in a field rather than a drawn box diagram, and sums the planner's estimate over the operators that read a table. **The plan format, the `EXPLAIN` spelling and the field names live only here.** It never runs the statement, and its caller must have established the statement is a single read first: the engine executes every statement after the first in such a string even under `EXPLAIN`. It raises `WarehouseError`, the adapter's own error type, which is what lets a caller that may not import `duckdb` tell an engine refusal from its own bug; `execute` and `query` raise it too, and the methods that run SQL this package wrote deliberately do not. Hardcoded database path licensed in writing by [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md). |
| Warehouse check | ✅ working | `.claude/scripts/check_warehouse.py` — four checks always, plus three flag-gated suites. Always: the table set matches Glossary Section B *read from the Glossary*, no floating-point columns, fourteen constraint rejections fire against an in-memory Warehouse with a seven-row positive control, and **the adapter seam holds in both the halves [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md) named** — no `duckdb` import outside `veritas/warehouse/`, and no DuckDB-specific **construct** in the SQL that leaves the adapter. The dialect scan reads every string literal sqlglot parses as a statement, plus every SQL field the Semantic Layer publishes (a Metric Definition's `expression` and `filters`, a Join Path's `on`), and reads all of it twice. **By name**: any function call standard SQL does not have, with the name set subtracted out of sqlglot's own dialect tables rather than typed, so the list tracks the library; this fails the run. **By type**: each statement is retargeted to BigQuery and every type construct compared against the same type retargeted *on its own*, so `DECIMAL(38, 6)` arriving as `NUMERIC` inside a statement and as `NUMERIC(38, 6)` alone is a finding while `VARCHAR` arriving as `STRING` is not; this prints a **review comment** rather than failing, because the corpus carries a widening cast the engine will not compute without — a statement sqlglot cannot write in BigQuery at all *does* fail. `retarget` and `round_trip_rewrites` live here and `check_validation_feasibility.py` imports them back, so the spike's dated measurement and this scan are one trip. Five probes run every time, each recording what **both** readings must say, and a probe reading wrong in either column fails the run. Those probes are the scan's **one fixture exemption**, scoped to the file it lives in: `FIXTURE_EXEMPTIONS` names `.claude/scripts/check_warehouse.py` as well as the symbol `DIALECT_PROBES`, so no other scanned file can claim it by choosing that name, and pointing the entry at a file that does not exist makes the run fail loudly. `--rebuild` recreates the database. `--sources` checks the loaded data, one function per star table: for `dim_instrument`, normalisation, the declared universe, every raw table non-empty and a **richness** assertion; for `fct_instrument_price` and `fct_fx_rate`, every row **re-derived from the committed snapshots in Python** and compared row-for-row against what the SQL built, with named wrong readings shown to change real rows, no day-over-day move exceeding 1.5, a rate for every Market Price in its own Quotation Currency on its own date, and a currency converted through another and back unchanged within the rounding its stored scale forces. **`--distinctions`** adds four more: every client-activity row is exactly what the simulator produces from the same seed, **every quantity is a whole lot of its own Instrument**, every Snapshot is markable and at least one Position Change is one no Trade explains, and **every Glossary Section C pair is printed as two numbers with how far apart they are** — a pair that has collapsed fails the run. `--rebuild` is mutually exclusive with both. It also holds the **nine independent figures** — one per Certified Metric — that `check_semantic_layer.py` compares every published expression against. They **read nothing from `semantic/`** ([R2](../plan/step-004-semantic-layer.md#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21)), and they are independent in **method** as well as in text: each fetches the component columns and folds them in Python, because a `DECIMAL(18, 6)` amount times a `DECIMAL(18, 8)` rate overflows `DECIMAL(18)` and an aggregate written here would need the same engine-specific width the published expressions carry. The `decimal` context precision is set explicitly for the same reason. The price of that independence is that editing a published expression means editing this SQL too, or the run fails. |
| Validation feasibility spike | ✅ working | `.claude/scripts/check_validation_feasibility.py` — the sqlglot spike, answering **all four claims** of [Step 003](../plan/step-003-validation-feasibility.md). **Not the Validation Gate and not a thin version of one**: it creates no `veritas/validation/` directory and ships no component. A tracer — parse, resolve against the real schema read through `WarehouseAdapter.columns_by_table`, rename table aliases back to their base table, canonicalise every projection that aggregates — plus 25 probe statements, each declaring the verdict this spike measured for it. **The tracer, the detector and the route reader are no longer this file's**: all three are `veritas/validation/`'s, imported back under [R2 of Step 005](../plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25), so the spike holds no copy of `resolve`, the canonical form, the two trusted rewrites, the refusal, the projection walker, the lineage walk or the route reading, and every one of its 25 declared verdicts and every one of its nine detector readings is unchanged by the two moves. What it still owns is its three pinned declarations: three certified expressions, three certified routes, and one `RestrictedColumn`. A statement is allowed when it computes at least one metric expression, **every** one traces to a certified expression, and it carries every join the metric it traced to is certified across. That last reading is narrower than the Validation Gate's own rule and deliberately so: the Gate must also refuse a join nothing certifies, and this file has no Dimension Definitions to certify a slice's extra joins with. The certified expressions and routes live as Python literals ([R2](../plan/step-003-validation-feasibility.md#r2--the-spikes-certified-expressions-stay-python-literals--approved-by-amino-2026-08-15)), pinned to the corpus rather than re-pointed at it ([R4](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)), so the dated measurement stays the one that was taken. Every executable probe is executed through the adapter and checked **against another probe's number** rather than against a figure written in the script. It exits non-zero if any verdict, any relation or any detector reading changes, in either direction — a spike's job is to hold its finding still. For claim 1, `projected_expressions` walks every scope; for claim 2, `columns_reaching_the_answer` walks each output column's lineage, so a column that never reaches the answer is not counted — both now imported rather than defined here — and nine shapes are judged three ways each — from the parse tree, by searching the query's text (ADR-0003's rejected alternative), and by claim 1's tracer. For claim 4, every one of the 25 statements is transpiled to BigQuery, re-parsed there and re-judged against a corpus and a schema retargeted the same way. |
| Validation-feasibility gate | ✅ working | `.claude/docs/design/validation-feasibility.md` — the go/no-go the spike exists to produce, in the shape of `data-availability.md` and beside it as the project's second design gate. **Verdict GO on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)**, with a verdict per claim, [what the Step did not measure](validation-feasibility.md#what-this-step-did-not-measure), [six constraints](validation-feasibility.md#consequences-for-step-004) on the Steps that follow, and four rulings. |
| Semantic Layer | ✅ working | `semantic/` — **all four entry types, every one complete**, thirty-two entries. **Nine Metric Definitions** in `metrics/`, one per Certified Metric of [Glossary Section B](../glossary.md#b-the-warehouse), and **thirteen Join Paths** in `joins/` — eight the metric expressions are computed across, and five that reach `dim_client`: one hop to `dim_account` from each of the four fact tables a metric starts at, plus the `account_to_client` they share. A Metric Definition carries its `expression` as the text an Orchestrator pastes verbatim ([C1](validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)) plus what [C2](validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate) requires — the route and the date predicate. The shape is [R8](../plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)'s: `from_table` names the table the query starts at, `join_paths` is an ordered list, `filters` holds the certified predicates, `date_column` names the column a period filter keys on, `reporting_currency` is present exactly when `unit` is `money`, and `derives_from` names the Certified Metrics whose value is **added** to this metric's own expression. One metric is composed that way — `Account Value` is *"Cash Balance plus all Positions marked to market"* — one carries a filter, two join nothing, and five carry a widening cast without which the engine refuses the expression. A Join Path carries `from_table`, `to_table` and the join condition as written, Reporting Currency literal included, because C1 forbids a template something else fills in. **Five Ambiguous Terms** in `ambiguous/`, one per row of [Glossary Section D](../glossary.md#d-ambiguous-terms) — `revenue`, `volume`, `balance`, `P&L`, `how much does X have` — each carrying a `description` of why the ambiguity is dangerous, a `resolution` from Section D's own third column, and `disambiguates`, the [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) field naming the Certified Metrics the word could mean. An Ambiguous Term publishes **no SQL**: it is a claim about language, so it can be wrong while every expression is right. **Five Dimension Definitions** in `dimensions/` — the certified axes a metric can be sliced along, each carrying `columns`, `grain`, `allowed_values` and `routes`, the first three being the [Glossary row](../glossary.md#a-the-system)'s own words for what one names and the fourth being where it can be reached from. Three are date axes rather than one: a single axis at `fct_trade.trade_date` could not be applied to the five Snapshot-and-movement metrics whose routes never reach that column, so the corpus publishes `by trade date`, `by snapshot date` and `by accounting movement date`, each named for the registered term it belongs to. `by snapshot date` is one axis over **two** columns, because `Snapshot` is one term registered as living in both Snapshot tables and one calendar writes both. A date axis enumerates no values — they are minted by the data — while `by region` and `by instrument type` enumerate theirs and are checked against what the Warehouse holds. A Dimension Definition publishes **no SQL** either. **`routes`** maps a metric's `from_table` to the Join Paths that reach the axis's columns from there, and its three shapes are three different answers: an empty list says the column is already on that table, a list says what reaching it costs, and an **absent key** says the axis cannot be reached from there at all — which is how `Cash Balance by instrument type` is refused by name, a Cash Balance having no Instrument. It is what stopped an axis being a **leaf**: `routes` names Join Paths, so an axis has an edge like every other entry type, and check 19 walks it. **`by region` is reachable from all four fact tables a metric starts at**, so the axis the Glossary's own worked example uses is applicable to all nine Certified Metrics; the check prints that count on every run. |
| Semantic Layer loader | ✅ working | `veritas/semantic/` — `loader.py` behind an `__init__.py` that re-exports it, laid out like `veritas/warehouse/`. Reads the tree into frozen dataclasses whose field lists **are** the file format, so there is no second copy of a field name to drift; refuses a file it cannot read as the kind its directory declares, a duplicate entry name, or a field the format does not name. `reporting_currency` is the one field a file may omit — the loader allows it and `check_semantic_layer.py` is what judges it, because whether omitting it is honest depends on `unit` and a loader reads one file at a time. **Executes no SQL and assembles no query** — C1 puts pasting on the consumer's side. `SQL_FIELDS` and `sql_fields()` say which fields of an entry hold SQL: `expression` and `filters` on a Metric Definition, `on` on a Join Path, nothing on an entry type not listed — so an Ambiguous Term and a Dimension Definition cost their readers nothing. They live here for the reason the dataclasses do: the format is here, and each reader deciding for itself is a second copy of it. Two readers ask so far, `check_warehouse.py`'s dialect scan and `check_language.py`'s keyword derivation; the Orchestrator that assembles a query will be the third. `ENTRY_KINDS` is not a scan of the tree, so a file in a directory it does not know fails to load rather than being skipped. The `kind` a file declares is the Glossary's term snake-cased unless a shorter one is registered, which is why a Metric Definition says `metric` and an axis says `dimension_definition` in full: no `Dimension` is registered, and shortening it would coin a noun. Reads booleans the **YAML 1.2** way rather than PyYAML's YAML 1.1, because a Join Path publishes its condition under the key `on`, which YAML 1.1 reads as the boolean `True`; the same rule keeps `no`, `on`, `y` and `n` as text in any casing, which is what an axis's allowed values need — a country code, a province code, and both halves of every yes/no flag. |
| Semantic Layer check | ✅ working | `.claude/scripts/check_semantic_layer.py` — **nineteen checks**, and it needs a filled Warehouse. The two places it executes a published expression catch `WarehouseError` rather than `Exception`, so a bug in the script surfaces as a traceback instead of as an accusation against a YAML file. Every file loads with every required field; **every Metric Definition's `name` is a Glossary Section B term whose *Lives in* cell says `semantic/metrics/`**, read from the Glossary rather than listed in the script; the expression is **pasted verbatim** into a query built from the entry's own Join Path and date column, executed through the Warehouse Adapter, and must return a number; that number must equal what `check_warehouse.py` computes from its own SQL — **twice, once over the whole Warehouse and once over one period**, because the arithmetic and the date predicate are separate mistakes and the second is invisible to a total; the declared Reporting Currency must appear as a string literal in the named Join Path's parse tree; and an expression that does not parse **fails the run**, with two probes exercising the refusal every run. Every [Section C](../glossary.md#c-distinctions-we-must-not-blur) pair whose both sides are Certified Metrics returns two different numbers **from the published expressions**. A metric's route is a route: every Join Path it names exists, starts at a table the route has reached, arrives somewhere new, and never reaches forward in its condition. The three expressions the spike measured, **and the three routes it measured them across**, are character for character what `semantic/metrics/` publishes — a pinned declaration nothing compared with the corpus would be a second corpus. A composed metric adds up metrics that exist, are not itself, do not derive further, and share its unit and currency. Every widening cast is shown to be load-bearing by running the expression without it and expecting the engine to refuse. **Three checks execute nothing** — they are claims about *language*, so they fail when a word is wrong while every number is right: every Certified Metric an Ambiguous Term names must exist and there must be at least two distinct ones ([EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks)'s fourth rule, three probes every run); Glossary Section D and `semantic/ambiguous/` must register the same words, with each row's *Could mean* cell naming the same Certified Metrics its entry does; and no metric's alias may be a registered Ambiguous Term or be claimed by two metrics. Words in a *Could mean* cell that are **not** Certified Metrics — `both`, on the P&L row — are printed rather than ignored, because a check that silently drops what it cannot resolve drops a misspelling just as silently. **Four checks read the Warehouse rather than the corpus**, because an axis's claim about buckets is a claim about the data and nothing else in the corpus would notice it being wrong: every column an axis names exists in the live schema; every column of one axis holds the **same** set of values, and an enumerated axis's buckets are exactly that set, in both directions; an axis enumerates **exactly when** its buckets are a registered vocabulary rather than dates, since a date's values are minted by the data and a list of them in the corpus would be a measurement dressed as a definition; and the Glossary's `Dimension Definition` row is read back against the corpus — a prose parse, and [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) is the cost of it. Five probes give the axis checks teeth every run. **A fifth reads both** — every route an axis declares is a route and arrives at the axis: each Join Path it names exists, the chain starts at the table the key names, each hop extends a route already arrived at its own `from_table`, no hop lands where the route already is, no condition reaches forward, and the chain ends at a table one of the axis's columns lives in. Check 8 for a Dimension Definition, with the last clause only an axis can get wrong, and an empty route is checked too, since `[]` claims the column is already on that table. Five more probes give it teeth. It also prints, without failing, how many Certified Metrics each axis declares a route from. |
| Ingestion | ✅ working | `veritas/ingestion/` — **both halves**: four real sources and the seeded simulator. `uv run python -m veritas.ingestion` builds all ten tables end-to-end from a clean clone with **no network**, and two consecutive runs produce byte-identical output. `--refresh` is the only mode that opens a socket; a refresh that fails part-way names the snapshots it had already rewritten, and one that succeeds reports how many it rewrote and how many were distinct — **failing the run if a source was fetched twice**. **Two phases, in an order that cannot be reversed:** dlt lands the real sources in `raw` and the adapter builds three star tables from them; then `simulator.py` *reads those three through the adapter*, generates the client side as a pure function of them and a seed, and a second dlt load plus seven more build scripts lands it. No two connections are ever open at once. The pipeline refuses to complete on four silent-shortness conditions, among them a Position with no Market Price on its own Snapshot date, and a monetary amount whose Denomination Currency has no FX Rate on its own date. |
| Retrieval | ✗ none | — |
| Orchestrator | ✗ none | — |
| Validation Gate | ✅ working | `veritas/validation/` — an `__init__.py` that re-exports, `outcome.py`, `profile.py`, and `gate.py`. **All five of the Gate's decisions, spelled as eight rules.** `outcome.py` holds the `Validation Gate outcome` — frozen, carrying allowed-or-rejected, the explanation a person reads, the `Rejection Reason` members a chart groups by, the rules that actually ran, and the trusted rewrites the verdict was reached under — and the `RejectionReason` taxonomy itself, thirteen members registered in code by [R3](../plan/step-005-validation-gate.md#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25) — a rule may register more than one, and the tracing rule registers three while the certified-route rule registers four. It is a separate module from the rules because a Grounded Answer, the App and Observability all read a verdict and import no rule. `profile.py` holds the `Access Profile` — a role, a permitted region, and the `RestrictedColumn`s that role may not see, as a table and a column rather than a bare name — and the one profile this slice declares, `ANALYST`, permitting `EU` and forbidding `dim_client.client_name`. The permitted region is a **value of the `by region` axis**, named by the `ACCESS_AXIS` constant, never a second registration of the column or its buckets; a region that axis does not certify raises `ValueError` at the first judgement made under the profile. **The profile is an argument to `judge`, not a field on the Gate** — `judge(sql, access_profile)`, with no default, so no statement is judged without an identity and a second identity is a second call rather than a second Gate ([R14](../plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27)). `rules(access_profile)` binds it into the two rules that read it, so the other six take a statement and nothing else. `gate.py` parses with `sqlglot.parse` rather than `parse_one` — `parse_one` reads `SELECT 1; SELECT 2` as one `Block` node — and runs eight rules in the order a statement meets them, **stopping at the first that rejects**: unparseable, more or fewer than one statement, not a `SELECT`, a planner estimate over the scan ceiling, a statement whose expressions do not all trace, a statement whose answer would carry a Restricted Column, a statement computed across joins or over a date column or without a certified filter the corpus does not certify for the metric it traces to or sliced by an axis no route reaches from it, and a statement not scoped to the Access Profile's permitted region. The ceiling is a policy constant and a constructor argument, not a measurement. `TRUSTED_REWRITES` names `qualify` and `merge_subqueries` as [C5](validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two) requires, and `resolve` is the one place that applies them; it turns both of the ways sqlglot refuses a statement — its own `SqlglotError`, and the bare `AssertionError` its `assert_is` raises — into one refusal a rule can act on. **The tracer, the lineage walk and the route reader live here too** — `resolve`, `projected_expressions`, `metric_expressions`, `certified_form`, `certified_forms`, `certified_metrics_only`, `columns_reaching_the_answer`, `restricted_columns_in_projection`, `route_of`, `certified_route` and `date_columns_filtered`, which the spike imports back; each has a variant taking an already-resolved tree, which is what lets one judgement resolve once. A `Route` is where a statement's rows start and the joins it reaches the rest through, read off a parse tree or assembled from the corpus — the corpus through the same reader as the query, which is `certified_form`'s argument applied to the route. **Permitted and required are two Routes**: `required_route` is the metric's own `join_paths`, which a statement must carry, and `permitted_route` adds the `routes` of each axis it groups by and the route the Access Profile's predicate needs, which it may. A join beyond the second is a rejection and a join absent from the first is a rejection; both go through `assembled_route`, which names each Join Path once and keeps them in the order they are joined. A certified expression is canonicalised through the same `resolve` a statement goes through, in a scope holding the Warehouse tables the expression names; without that symmetry `Position Change` traces to nothing. The Restricted Column rule asks whether a column **reaches the answer**, not whether its name appears: it numbers the output columns and walks each one's lineage back to base tables, so a name in a comment, in a string literal, in a filter, or projected inside a subquery and aggregated away is not a projection of it. The Semantic Layer is loaded once at construction; the catalogue, the resolved statement and the corpus's canonical forms are read **once per judgement**, on a `Reading` that every rule shares, so all four parse-tree rules judge one tree qualified against one catalogue. They are read lazily rather than in the constructor, because the rules that need nothing must return a verdict on a day the Warehouse will not open. **The order is a safety property, not a speed one**: the rules that need nothing touch nothing — proved by judging every probe through a Warehouse that raises on contact — and the single-statement rule runs before the bounded read because the engine executes the tail of a multi-statement string even under `EXPLAIN`. The route rule reads all three of the fields that pin down which rows a certified expression covers — `join_paths`, `date_column` and `filters` — the last since [DEBT-020](../debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters) was paid. `where_conjuncts` reads the **outermost** WHERE clause's ANDed parts, which is what both the filter comparison and the access predicate ask of a statement; a predicate inside a subquery the optimizer could not flatten does not count, which is the fail-closed direction. `grouped_columns` reads every scope's `GROUP BY`, because reaching an axis is permitted by grouping on it and never by mentioning its table. **Two known holes in what is built:** every reading writes a column on its base table before comparing, which is what makes an alias invisible and what stops two joins to the *same* table being told apart ([DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart)); and a Route holds a join as a table and a condition and not its kind, so an outer join over a certified condition passes as the inner one the corpus means ([DEBT-022](../debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one)). Nothing anywhere executes a statement through it. |
| Validation Gate check | ✅ working | `.claude/scripts/check_validation_gate/` — a **package**, by [R8](../plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25): `__main__.py` holds the rule order, the report and the exit code, `probes.py` the shared machinery, and one module per Gate rule — `read_only.py`, `traces.py`, `restricted.py`, `route.py` and `access.py`, all five. Run as one command, `uv run python .claude/scripts/check_validation_gate/`, because Python runs a directory holding a `__main__.py`. Needs a filled Warehouse. Seventy-nine probes, each declaring the verdict and the Rejection Reason members it was measured with, so a rejection for the **wrong reason** fails as loudly as no rejection. `read_only.py` holds twelve: the six shapes read-only has to cover, a union, a string that is not SQL, a query over a lowered ceiling, one the engine will not plan, a cross product, and an ordinary question. `traces.py` holds eighteen — the shapes Sub-step 3.2 measured, re-judged through the whole Gate rather than through a tracer, plus a statement that aggregates nothing, one the optimizer will not resolve, and a certified expression sitting beside a Shadow Metric in one projection, which is the probe for the word *every* — and then builds nine more from `semantic/metrics/`, one per Certified Metric, so a tenth Metric Definition is a tenth probe with no edit — probes built out of the corpus they are checked against, which is [DEBT-018](../debt-ledger.md#debt-018--six-certified-metrics-have-no-expression-text-pinned-outside-the-corpus): they prove the Gate recognises what `semantic/metrics/` says, and six of the nine expressions have no text pinned anywhere outside it. `restricted.py` holds ten, each declaring **three** answers rather than one — the Gate's verdict, the parse tree's reading, and what a search of the query's text would say — so ADR-0003's rejected alternative is shown wrong on every run rather than in an argument; nine are the spike's claim-2 shapes and the tenth is a `SELECT *` written so that it reaches the rule. `access.py` holds twenty-one, each also declaring whether this rule reads the statement as scoped: every Certified Metric scoped and unscoped, which is eighteen and is how the rule is shown to bind on the Snapshot and movement metrics and not only on the trade-side four, plus three about the slice route — `Net Revenue by region`, `Cash Balance by instrument type` refused on the absent key, and one join to a table the statement does not group by. It **executes** the Glossary's worked example twice, unscoped and scoped, so the three buckets the axis registers and the one the Access Profile permits are printed side by side, and it runs three mutations: the access rule deleted, the absent-key branch deleted, and the certified-filter comparison deleted, each re-run to show what stops being refused. `route.py` holds nine, each also declaring whether the statement is off its metric's route and whether it filters on a date column that metric is not certified against: the spike's wrong-currency statement, a cross product computing a certified metric, a count with a join that multiplies it, a slice by `by region`, the same notional converted the certified way, a period keyed on Trade Date and the same period keyed on Settlement Date, and the two halves of [DEBT-020](../debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters). It **executes** three pairs and prints how far apart each is, because a rejection is only worth having if the thing rejected returns a different number; every date in it is read from the Snapshot calendar; and it rebuilds all nine Certified Metrics from `semantic/metrics/` to show the rule allows each one computed the way its own entry says. **The *character for character* claim is checked in both modules that make it**: `probes.py` reads the spike's statements out of its **source text** with `ast` rather than importing it, so a check that runs on every commit does not depend on a 1,700-line script staying importable, and `traces.py`'s fifteen are checked the same way — including the one it judges under a shorter local name, and the one shape the spike measures that it does not judge, which is **declared** with where the Gate refuses it instead. Checks beyond the probes: every probe decided before the bounded rule is decided again through a Warehouse that raises on any attribute access; the engine is asked to plan a two-statement string against a throwaway table in an in-memory Warehouse, and the run fails if the table **survives**; the planner's estimate is compared against a real row count, because an unread plan sums to zero and zero is under every ceiling; the corpus is canonicalised the rejected way as well as the Gate's way, failing the run if **no** Certified Metric depends on the difference; the Access Profile's own declaration is printed and an empty one fails the run; two statements no rule can read are put to the detector directly, which must refuse rather than report nothing found; and one judgement is made through an adapter that counts catalogue reads, failing the run on anything but one, with the `Reading`'s own memo read afterwards to show the resolution and the corpus were each computed once. Statements a Sub-step's own rules allow are checked by the rules that **ran** rather than by the final verdict, so a later rule refusing them is not mistaken for these rules refusing everything. It also prints the trusted rewrites, the ceiling's current headroom, and what one judgement costs. |
| App | ✗ none | — |
| Observability | ✗ none | — |
| Evaluation | ✗ none | — |
| Containerization | ✗ none | — |

## Repository layout

```
veritas/
├── CLAUDE.md                  # operating agreement (root: Claude Code auto-loads it)
├── final_proposal_target.md   # source job description — captured into .claude/docs/design/product-brief.md, removable
├── pyproject.toml, uv.lock, .python-version, .gitignore
├── data/
│   ├── snapshots/             # committed source data + dated probe record
│   │   └── ingestion/         # ingestion's own snapshots — one per source, one
│   │                          # per traded Instrument; only --refresh writes here
│   └── veritas.duckdb         # the Warehouse — gitignored, rebuilt by ingestion
├── semantic/                  # the Semantic Layer — the certified registry, as data
│   ├── metrics/               # nine files, one per Certified Metric of Section B
│   │   ├── gross_revenue.yaml            # ─┐ the trade side
│   │   ├── net_revenue.yaml              #  │
│   │   ├── traded_notional.yaml          #  │
│   │   ├── trade_count.yaml              # ─┘
│   │   ├── cash_balance.yaml             # ─┐ the Snapshot side
│   │   ├── account_value.yaml            #  │ composed: its own expression plus
│   │   ├── unrealised_pnl.yaml           #  │ Cash Balance
│   │   ├── position_change.yaml          # ─┘
│   │   └── realised_pnl.yaml             #   the accounting ledger
│   ├── joins/                 # thirteen routes; eight for the metric expressions and
│   │                          # five that reach dim_client for the access predicate
│   │   ├── trade_to_fx_rate_on_denomination_currency.yaml    # ─┐ the Section C
│   │   ├── instrument_to_fx_rate_on_quotation_currency.yaml  # ─┘ currency pair
│   │   ├── trade_to_instrument.yaml
│   │   ├── balance_snapshot_to_fx_rate_on_snapshot_date.yaml
│   │   ├── position_snapshot_to_instrument.yaml
│   │   ├── position_snapshot_to_price_on_snapshot_date.yaml
│   │   ├── instrument_to_fx_rate_on_snapshot_date.yaml
│   │   ├── accounting_movement_to_fx_rate_on_movement_date.yaml
│   │   ├── trade_to_account.yaml                  # ─┐ one hop to dim_account per
│   │   ├── position_snapshot_to_account.yaml      #  │ fact table a metric starts
│   │   ├── balance_snapshot_to_account.yaml       #  │ at, and the last hop all
│   │   ├── accounting_movement_to_account.yaml    #  │ four share
│   │   └── account_to_client.yaml                 # ─┘
│   ├── ambiguous/             # five words, one per row of Glossary Section D
│   │   ├── revenue.yaml       # ─┐ each names the Certified Metrics it
│   │   ├── volume.yaml        #  │ disambiguates between — and publishes no SQL,
│   │   ├── balance.yaml       #  │ because it is a claim about language
│   │   ├── pnl.yaml           #  │
│   │   └── how_much_does_x_have.yaml  # ─┘
│   └── dimensions/            # five certified axes — the answer to "by what?"
│       ├── by_trade_date.yaml            # ─┐ three date senses, not one: a
│       ├── by_snapshot_date.yaml         #  │ Snapshot metric's route never
│       ├── by_accounting_movement_date.yaml # ─┘ reaches fct_trade.trade_date
│       ├── by_region.yaml                # ─┐ the two enumerated axes; their
│       └── by_instrument_type.yaml       # ─┘ buckets are checked against the data
│                                         #   every axis also names the routes that
│                                         #   reach it, per fact table
├── veritas/
│   ├── semantic/
│   │   ├── __init__.py        # re-exports the loader, like veritas/warehouse/
│   │   └── loader.py          # reads semantic/ into frozen entries; executes nothing
│   ├── validation/
│   │   ├── __init__.py        # re-exports all three modules
│   │   ├── outcome.py         # the Validation Gate outcome + the Rejection Reason
│   │   │                      # taxonomy — a contract, importable without the rules
│   │   ├── profile.py         # the Access Profile: a role, a permitted region, and
│   │   │                      # the Restricted Columns it forbids. One profile
│   │   └── gate.py            # the eight rules, the tracer, the lineage walk and
│   │                           # the route reader — all five of the Gate's
│   │                           # decisions
│   ├── warehouse/
│   │   ├── adapter.py         # the Warehouse Adapter — the only duckdb importer
│   │   ├── schema.sql         # the ten-table star schema, hand-authored
│   │   └── builds/            # hand-authored raw→star SQL, one file per table
│   │       ├── dim_instrument.sql        # ─┐ the real half, built first
│   │       ├── fct_instrument_price.sql  #  │
│   │       ├── fct_fx_rate.sql           # ─┘
│   │       ├── dim_client.sql            # ─┐ the synthetic half; dim_client.sql
│   │       ├── dim_account.sql           #  │ carries the reasoning for all seven
│   │       ├── fct_trade.sql             #  │
│   │       ├── fct_cash_movement.sql     #  │
│   │       ├── fct_accounting_movement.sql  │
│   │       ├── fct_position_snapshot.sql #  │
│   │       └── fct_balance_snapshot.sql  # ─┘
│   └── ingestion/
│       ├── __main__.py        # the entry point: replay by default, --refresh
│       ├── universe.py        # the 19 traded Instruments + two vocabulary maps
│       ├── snapshots.py       # snapshot-and-replay — the only socket in the package
│       ├── sources.py         # NASDAQ Trader · SEC · Yahoo metadata and bars, for dlt
│       └── simulator.py       # the seeded simulator — reads the real tables,
│                              # generates the client side as a pure function
└── .claude/
    ├── skills/                # 5 framework skills
    ├── scripts/
    │   ├── verify_framework.py        # structure: docs, links, skills, interpreter
    │   ├── check_language.py          # content: Glossary + writing conventions
    │   ├── check_warehouse.py         # schema vs Glossary, constraints, adapter seam
    │   ├── check_semantic_layer.py    # every published expression executes, and agrees
    │   ├── check_validation_feasibility.py  # the sqlglot spike — all four claims
    │   ├── check_validation_gate/     # a package: one module per Gate rule
    │   │   ├── __main__.py            # the runner — rule order, report, exit code
    │   │   ├── probes.py              # the adapter, the probe record, the report
    │   │   ├── read_only.py           # parseable · one statement · a read · bounded
    │   │   ├── traces.py              # every metric expression traces
    │   │   ├── restricted.py          # no Restricted Column reaches the answer
    │   │   └── route.py               # the metric's own joins and its own period
    │   └── check_data_availability.py
    └── docs/
        ├── glossary.md
        ├── debt-ledger.md
        ├── extension-register.md
        ├── design/{target-state,current-state,product-brief}.md
        ├── design/{data-availability,validation-feasibility}.md   # the two design gates
        ├── adr/
        ├── plan/
        └── reviews/
```

## Known gaps

**Everything above the Semantic Layer.** The Warehouse itself has no gaps left: all ten
tables hold rows, the two components below the Semantic Layer are done, and the
Validation Gate now decides all five of the things the Target State's flow says
`VALIDATE` decides. Nothing calls it: no component anywhere hands it a statement.

**A metric returning a number is not a metric being *asked for*.** All nine Metric
Definitions are written down and certified, so every Certified Metric says in a file
which arithmetic it is and which rows it is computed over. Nothing is retrievable —
there is no Retrieval — and nothing turns a question into SQL. The machine that chooses
between them does not exist.

**The corpus can be sliced and nothing asks it to slice anything.** All four entry types
are complete, every axis names the routes that reach it, and the Gate has the rule that
lets a `GROUP BY` on a certified axis add the joins that axis declares — so a slice is
now decidable rather than merely certified, and `check_semantic_layer.py` prints how many
metrics each axis is reachable from on every run. What is still absent is anything that
would **write** such a query: no Retrieval to find the axis, no Grounding to put it in a
prompt, and no generator.

**Two published fields are unchecked** — `description` and `aliases`, which are what
Retrieval will match on when Retrieval exists. A Metric Definition's `grain` is read by
nobody; a Dimension Definition's is compared against the Glossary's.

**A Snapshot metric executed over the whole Warehouse is not a number anyone would ask
for.** `Cash Balance` summed across every Snapshot date is every date in the Snapshot
calendar added together — `check_semantic_layer.py` prints how many, on the
`by snapshot date` line — and the check executes it that way on purpose: it is the
strongest thing a corpus check can do without inventing a question. The "as of" date
comes from the question, and no component that asks questions exists yet.

**The Gate judges shape and nothing else.** Of its five rules, the two the spike
measured — certified-metrics-only and no Restricted Columns — are **not built**, and
neither is the route rule or the Access Profile predicate. What is built is read-only,
single-statement, parse-failure and bounded-scan, which together decide whether a
statement is the *kind* of thing Veritas runs and say nothing about whether it computes
a certified number. So a `SELECT` that invents a metric, projects a client's name, joins
through the wrong currency column, or reads a file through a table function passes every
rule that exists today.

**The spike's go was measured on a spike, and two of its limits still stand.** Only
projections are read for claim 1, so a metric expression appearing solely in a filter
applied after grouping is invisible to the tracer 5.2 will build from it.
[What this Step did not measure](validation-feasibility.md#what-this-step-did-not-measure)
is the full list and is deliberately as long as the findings.

**The bounded read has a measured blind spot.** The planner's estimate is summed over
the operators that read a table, and an operator that multiplies rows without reading
one carries no estimate — so a cross product scans each side once and produces the
square, and the rule sees only the scans. `check_validation_gate/` carries it as a probe
with a declared `allowed` verdict; the certified-route rule is what bounds it.

**Two Section C pairs are real but small at book level**, and both are on the Ledger
against the Gold Question Set rather than fixed in the data:
[DEBT-004](../debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal)
(the FX half of Trade Date against Settlement Date) and
[DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level)
(Execution Price against Market Price). Neither is a defect in the simulator — making
either diverge would mean shaping the data to pass our own check — and both are
constraints on what a gold question may ask. `--distinctions` prints both figures on
every run.

**What the dialect scan does not cover**, so nobody reads the seam as fully mechanical:
SQL assembled at run time is not a literal and is invisible to a static scan — that is
the Validation Gate's subject — and a name sqlglot files as dialect-neutral passes even
where it is not standard SQL, `generate_series` being the example this project already
uses.

**Out of scope by decision, not oversight.** Single bonds and options: no key-free
Market Price source exists
([DEBT-003](../debt-ledger.md#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope)).
Corporate actions: [EXT-007](../extension-register.md#ext-007--corporate-actions), and
the assumption behind excluding them is checked rather than asserted — `--sources` fails
the run if any day-over-day price ratio exceeds 1.5. Still deferred to the Retrieval
Step: which embedding and re-ranking models.

**The wrong-number traps are defended in the Warehouse itself, not only in the spike.**
`check_data_availability.py` measured two of them on three probe series;
`check_warehouse.py --sources` measures **five** on everything loaded, by re-deriving
every price and every rate from the snapshots in Python and printing what each wrong
reading would have changed. How many rows each moves is a measurement, so it lives in the
Step Review with the command and the date, and the check prints the current figure on
every run. The five:

| Trap | Where it would land |
|---|---|
| `Adjusted Close` instead of the unadjusted close | `fct_instrument_price` — the Section C row for `Market Price` |
| A pence quote carried across as pounds | `fct_instrument_price` — a 100× error, `Quotation Currency` |
| A bar's timestamp read as a Coordinated Universal Time (UTC) date rather than the exchange's own | `fct_instrument_price` — every currency-pair price booked one day early |
| Rates stored only for the dates the ECB published on | `fct_fx_rate` — every weekend and ECB-holiday Position converted at nothing |
| A published rate read upside down | `fct_fx_rate` — every conversion inverted |

A sixth gotcha is recorded in [data-availability.md](data-availability.md): Frankfurter
returns HTTP 403 to the default `Python-urllib` User-Agent, which reads as "blocked" when
the fix is one header. `snapshots.fetch` sends a descriptive one.

## Open debt and extensions

The [Debt Ledger](../debt-ledger.md) and the
[Extension Register](../extension-register.md) each carry an Index with every entry's
trigger or readiness condition and its status, and the running counts. Read them there —
this file does not keep a second copy.

**Open debt: 11.** The newest is
[DEBT-022](../debt-ledger.md#debt-022--the-gate-compares-joins-without-their-kind-so-an-outer-join-passes-as-an-inner-one),
which shares both its trigger — the Sub-step that builds Grounding, which this Step does
not fire — and its home in `route_of_resolved` with
[DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart).
Neither is demonstrated by anything that runs, and each owes a probe from the Sub-step
that pays it.
[DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)
is the one that is partly paid and stays open on its main subject, **the hook layer**:
nothing mechanically blocks a commit by Claude, a missing Ledger entry, or a review that
skips a section.

**Open extensions: 10.**

**Debt is not the same as an extension.** Debt means the current code is *wrong,
cheaply*; an extension means it is *right for this scope* and the full system needs more.
The test that settles it: does the trigger fire inside this project's life?

## How we got here

One line per Step. The argument, the evidence and the rulings are in each Step's plan and
its dated review.

| Step | What it did | Plan | Review |
|---|---|---|---|
| 000 | Framework scaffolding — CLAUDE.md, the docs tree, the skills, `verify_framework.py` | [plan](../plan/step-000-framework-scaffolding.md) | [review](../reviews/step-000-framework-scaffolding.md) |
| 001 | Target State design, the data-availability check, and the component-name sweep that made all nine components registered Glossary terms | [plan](../plan/step-001-target-state-design.md) | [review](../reviews/step-001-target-state-design.md) |
| 002 | The Warehouse and Ingestion — the ten-table star schema, four real sources, the seeded simulator, and the adapter seam scan | [plan](../plan/step-002-warehouse-and-ingestion.md) | [review](../reviews/step-002-warehouse-and-ingestion.md) |
| 003 | The sqlglot spike — all four parse-tree claims measured on real data, and the **GO** recorded in [validation-feasibility.md](validation-feasibility.md) with six constraints | [plan](../plan/step-003-validation-feasibility.md) | [review](../reviews/step-003-validation-feasibility.md) |
| 004 | The Semantic Layer — all four entry types, twenty-seven entries, and eighteen checks over them | [plan](../plan/step-004-semantic-layer.md) | [review](../reviews/step-004-semantic-layer.md) |
| 005 | The Validation Gate — **active**. 5.1 built: the outcome, the reason taxonomy, and the four rules that judge a statement's shape. 5.2 built: the tracer, and the rule that every metric expression traces to a Certified Metric. 5.3 built: the Access Profile, and the rule that no Restricted Column reaches the answer. 5.4 built: the route reader, and the rule that a metric is computed across its own joins and over its own date column. 5.5 built: the five Join Paths and the `routes` field that make an axis reachable, the slice route and the certified filters inside the route rule, and the rule that every statement carries the Access Profile's predicate | [plan](../plan/step-005-validation-gate.md) | [review](../reviews/step-005-validation-gate.md) |

**Commits, in order.** Step 000 and Sub-step 1.1 in `6281e6b`, Sub-step 1.2 in `4b48a46`,
Sub-step 1.3 in `9c5b060`, Step 002 planning in `57e8aee`, Sub-step 2.1 in `5a061a7`, the
R16 plan amendment in `cd5e7dd`, Sub-step 2.2 in `0fc5a34`, Sub-step 2.3 in `a58ef91`,
Sub-step 2.4 in `13b99bb`, Sub-step 2.5 in `ce2961a`, Sub-step 2.6 in `6a16d3d`, Step 003
planning in `40d72d8`, Sub-step 3.1 in `d840fa8`, Sub-step 3.2 in `89fee55`, Sub-step 3.3
in `23020e9`, Sub-step 3.4 in `c20d601`, Sub-step 3.5 in `fcf4b7d`, Step 004 planning in
`5d95393`, Sub-step 4.1 in `6c15736`, Sub-step 4.2 in `333d6fc`, Sub-step 4.3 in
`ae75f0e`, Sub-step 4.4 in `71ce677`, Sub-step 4.5 in `7ddd96c`, **Step 005 planning in
`aa42205`**, the Current State trim in `aa918fb`. A Step's planning commit is what writes
the previous Step's last hash into this list and turns that plan from `in review` to
`done`. Sub-step 5.1's own hash is not here for the same reason the trim's was not: this
file is part of that commit, and the next one fills it in.
