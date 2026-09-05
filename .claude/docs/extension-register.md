# Extension Register

Capabilities the **full Minimum Viable Product** needs that the Veritas slice
deliberately does not have.

This is the third register, beside the [Debt Ledger](debt-ledger.md) and the
[ADRs](adr/). The distinction is not bookkeeping — it changes what the entry
means:

| | Debt Ledger | Extension Register |
|---|---|---|
| The current code is… | **wrong**, cheaply | **right**, for this scope |
| Repaying means… | fixing it | adding to it |
| Fires… | inside this project's life | when the slice becomes the full system |
| Carries a… | **Trigger** — a condition that will fire | **Readiness** — what must be true first |

Keeping them apart protects both. If extensions live in the Ledger, "open debt:
8" stops meaning "8 shortcuts to repay" and the number loses its bite; and
extensions arrive with triggers like *"when we build the full MVP"*, which the
framework itself calls a wish rather than debt.

**Every entry names the seam it lands against.** That is the load-bearing field.
It is what makes the Target State's claim — *addition, not rewrite* — a checkable
statement rather than a hope. An extension with no seam is a rewrite nobody has
admitted to yet.

**Every entry names what motivates it**, linked: the ADR cost, non-goal, or scope
boundary it answers. An extension that cannot be traced back to a decision is
speculation, and speculation belongs in the product brief, not here.

**Status:** `open` · `built` (with the Step that built it) · `dropped` (with the
reason) · `superseded`.

---

## Index

| ID | Extension | Seam it lands against | Size | Status |
|---|---|---|---|---|
| [EXT-001](#ext-001--warehouse-native-security-and-concurrency) | Warehouse-native security and concurrency | Warehouse adapter · Validation Gate Access Profile check | L | open |
| [EXT-002](#ext-002--semantic-layer-drift-detection) | Semantic Layer drift detection | Semantic Entry schema · continuous integration | M | open |
| [EXT-003](#ext-003--metric-authoring-at-scale) | Metric authoring at scale | `semantic/` file format · retrieval index build | L | open |
| [EXT-004](#ext-004--coverage-miss-capture) | Coverage-miss capture | Question Log · Grounded Answer refusal path | M | open |
| [EXT-005](#ext-005--semantic-layer-coherence-checks) | Semantic Layer coherence checks | Metric Definition fields · the same sqlglot parse as EXT-002 | M | open |
| [EXT-006](#ext-006--position-change-attribution) | Position Change attribution | `fct_position_snapshot` · the `Position Change` Metric Definition | M | open |
| [EXT-007](#ext-007--corporate-actions) | Corporate actions | `fct_instrument_price` · `fct_position_snapshot` · the P&L Metric Definitions | M | open |
| [EXT-008](#ext-008--the-data-checks-run-in-continuous-integration) | The data checks run in continuous integration | `check_warehouse.py` · `check_data_availability.py` · the one-command bring-up | M | open |
| [EXT-009](#ext-009--the-join-path-entry-type-at-warehouse-scale) | The Join Path entry type at Warehouse scale | `semantic/joins/` file format · a Metric Definition's `join_paths` | M | open |
| [EXT-010](#ext-010--a-metric-certified-over-more-than-one-date-column) | A metric certified over more than one date column | `ValidationGate.routed`'s date half · a Metric Definition's `date_column` | S | open |
| [EXT-011](#ext-011--more-large-language-model-providers-behind-the-seam) | More Large Language Model providers behind the seam | `veritas/llm/`'s `PROVIDERS` registry · the `LanguageModel` seam | S | open |
| [EXT-012](#ext-012--the-dashboards-panels-read-the-dashboards-time-range) | The dashboard's panels read the dashboard's time range | each panel's `rawSql` · `question.asked_at` | S | open |
| [EXT-013](#ext-013--grafana-reads-the-question-log-with-credentials-of-its-own) | Grafana reads the Question Log with credentials of its own | the Grafana datasource file · the `POSTGRES_*` values `.env` declares | S | open |
| [EXT-014](#ext-014--the-container-tests-run-as-pipeline-stages-before-and-after-a-deploy) | The container tests run as pipeline stages, before and after a deploy | `tests/test_container.py`'s `app` and `container` fixtures · `docker compose up -d --build --wait` | M | open |

**Open:** 14 · **Built:** 0 · **Dropped:** 0

### Target State extension path, mapped

The [Target State's extension path](design/target-state.md) table is this
register's summary view. Rows not yet detailed here are recorded but not worked
out — that is honest, not an omission, since detailing an extension before its
motivating cost exists is speculation.

| Full-MVP capability | Entry |
|---|---|
| Real row/column-level security | [EXT-001](#ext-001--warehouse-native-security-and-concurrency) |
| BigQuery instead of DuckDB | Delivered by EXT-001's migration; the engine swap itself is [ADR-0002](adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)'s stated extension path |
| dbt semantic layer as the source of Metric Definitions | [EXT-003](#ext-003--metric-authoring-at-scale) |
| Query-cost governance | Not yet detailed — lands on the Validation Gate's cost-check interface (see [ADR-0002](adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md), the cost-check cost) |
| Multi-agent reconciliation and anomaly detection | Not yet detailed — consumes Grounded Answer + Lineage |
| Entity resolution across sources | Not yet detailed — lands on the Client/Account distinction |

---

## Entries

### EXT-001 — Warehouse-native security and concurrency

- **Status:** open
- **Opened:** Sub-step 1.3 (`.claude/docs/reviews/step-001-target-state-design.md`)
- **Size:** L
- **Seam:** the Warehouse adapter ([ADR-0002](adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)),
  and the Validation Gate's Access Profile check
- **Motivated by:** [ADR-0002](adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md),
  the concurrency and access-control cost; and the *sensitive-data leakage*
  failure named first in the [product brief](design/product-brief.md)

**What the full system needs**

Two capabilities delivered by one migration, which is why they are one entry:

1. **Engine-enforced row- and column-level security.** BigQuery policy tags for
   columns, authorized views or row-access policies for rows, with the Access
   Profile mapped to a real principal. Enforcement moves out of Veritas and into
   the warehouse.
2. **Concurrent request handling.** A server-based engine, so the App serves
   more than one user at a time.

**What the slice does instead, and why that is correct here**

DuckDB is single-writer and has no policy-tag mechanism, so the Access Profile is
enforced by the Validation Gate in application code. This is right for the slice
because the data is synthetic by construction — there is nothing to leak — and
because the demonstration is of the *mechanism*: an Access Profile threading
through a deterministic check. One reviewer at a time also makes the concurrency
limit invisible.

**What this replaces, rather than adds to**

The application-layer Access Profile check is **removed** when this lands, not
kept as defence-in-depth. Two enforcement points for one rule is two places to
keep in sync and two places to get out of sync, and the weaker one supplies false
assurance about the stronger one's coverage. The warehouse becomes authoritative.

One thing is genuinely lost and should be replaced deliberately: the Gate
currently rejects an access violation *before execution*, with a specific reason
that feeds the rejection-reason Operational Measure. Warehouse-native enforcement
fails at execution with a database error instead. Keep a **non-enforcing**
pre-flight check if that signal matters — but it must be labelled as a
user-experience affordance, never described as access control.

**Readiness**

Any one of:

1. The Warehouse migrates to an engine with native row- and column-level
   security. This is the natural home.
2. Real, non-synthetic client data is in scope — see the note on what "real data"
   means in [DEBT-008](debt-ledger.md), which is the debt-shaped half of this.
3. More than one concurrent user is required.

---

### EXT-002 — Semantic Layer drift detection

- **Status:** open
- **Opened:** Sub-step 1.3 (`.claude/docs/reviews/step-001-target-state-design.md`)
- **Size:** M
- **Seam:** the Semantic Entry file format, and the continuous-integration check
- **Motivated by:** [ADR-0001](adr/0001-semantic-layer-as-the-retrieval-corpus.md),
  the first cost — the Semantic Layer is a second source of truth about the
  Warehouse

**What the full system needs**

A check that every Metric Definition still refers to columns that exist:

1. Parse each Metric Definition, Dimension Definition and Join Path expression
   with sqlglot — already a dependency, so this adds nothing new.
2. Extract the `table.column` references from each parse tree.
3. Assert every reference exists in the Warehouse's live schema.
4. Fail with the offending entry, the missing column, and the metric version that
   last worked.

**What the slice does instead, and why that is correct here**

Nothing, and nothing is needed. One author, one schema, authored once and not
migrated. Drift has no opportunity to occur inside a 2–3 week slice, and building
the checker before either the Warehouse or the Semantic Layer exists would be
guessing at both schemas.

**Why it matters in the full system**

A warehouse with real migrations breaks metrics silently. Rename
`fct_trade.commission` and every Certified Metric built on it is broken — but the
Semantic Layer still looks healthy, retrieval still returns the entry, the
Validation Gate still passes the query (the expression *does* trace to a
Certified Metric), and the failure surfaces as a database error after a user has
asked their question. It also undercuts the word *certified*: a Certified Metric
that cannot execute was never certified, only registered.

**Readiness**

The first schema change after a Semantic Layer exists — any rename, drop or
retype of a referenced column. Build this **with** [EXT-005](#ext-005--semantic-layer-coherence-checks):
both need the same parse-tree column extraction, and writing it twice would be
the duplication this register exists to prevent.

---

### EXT-003 — Metric authoring at scale

- **Status:** open
- **Opened:** Sub-step 1.3 (`.claude/docs/reviews/step-001-target-state-design.md`)
- **Size:** L
- **Seam:** the `semantic/` file format, and the retrieval index build
- **Motivated by:** [ADR-0001](adr/0001-semantic-layer-as-the-retrieval-corpus.md),
  the fourth cost — authoring cost scales with the warehouse

**What the full system needs**

Three separable pieces, in increasing cost:

1. **Generation instead of authoring.** Import Metric Definitions from an
   existing dbt semantic layer rather than retyping them. The shapes already
   match — name, expression, grain, filters — which is why ADR-0001 calls this an
   addition rather than a rewrite.
2. **Incremental indexing.** Re-embed and re-index only changed entries, so
   authoring latency stays flat as the corpus grows.
3. **Authoring assistance.** Propose a draft Metric Definition from a coverage
   miss ([EXT-004](#ext-004--coverage-miss-capture)) for a human to certify.
   **Never auto-certify** — that would make the model a metric author, which is
   the one thing the governing rule forbids.

**What the slice does instead, and why that is correct here**

Every Semantic Entry is a hand-written YAML file, and every change rebuilds the
retrieval index. At tens of metrics this is not merely acceptable, it is better:
inspectable, diffable, and reviewable in a pull request — which is what makes
"certified" mean something. Building a generation pipeline for thirty entries
would cost more than writing the thirty entries.

**Why it matters in the full system**

Hundreds of metrics and dozens of authors. The ceiling shows up first as
evaluation coverage — Gold Question Set breadth bounded by how many metrics
someone is willing to type — and later as the reason an analytics team cannot
adopt the system.

**Readiness**

Any one of: the Semantic Layer passes roughly 50 Semantic Entries, where a full
index rebuild stops being instant; a second author needs to add metrics
concurrently; or an existing dbt semantic layer becomes available to import from —
at which point hand-authoring is not just slow but a duplicate source of truth,
and collides with [EXT-002](#ext-002--semantic-layer-drift-detection).

---

### EXT-004 — Coverage-miss capture

- **Status:** open
- **Opened:** Sub-step 1.3 (`.claude/docs/reviews/step-001-target-state-design.md`)
- **Size:** M
- **Seam:** the Question Log, and the Grounded Answer refusal path
- **Motivated by:** [ADR-0001](adr/0001-semantic-layer-as-the-retrieval-corpus.md),
  the second cost — coverage is a hard ceiling, which is *intended*, but the slice
  refuses **silently and forgetfully**

**What the full system needs**

Refusal turned into a signal rather than a dead end:

1. **Record every ungroundable question** — the question, the entries retrieval
   did return, and why grounding failed (no Certified Metric, an unresolved
   Ambiguous Term, no Join Path).
2. **Cluster them**, so "eleven people asked for client acquisition cost" is
   visible as one gap rather than eleven refusals.
3. **Surface the clusters as a metric-authoring backlog**, ranked by frequency.

**What the slice does instead, and why that is correct here**

Refuses, explains why, and forgets. Correct for the slice because refusal is the
feature — a helpful guess is the exact failure Veritas exists to prevent — and
because with a hand-built Gold Question Set there is no organic question traffic
to learn from.

**Why it matters in the full system**

Without it the certified vocabulary never learns where its own edges are. The
Semantic Layer grows by whoever happens to ask an author for something, which is
the least representative sampling available. With it, coverage becomes a
measurable, improvable property instead of an anecdote.

**Note on scope:** this is the *capture* half of what was originally proposed as a
knowledge graph. It deliberately needs no graph at all. The coherence half is
[EXT-005](#ext-005--semantic-layer-coherence-checks).

**Readiness**

Real question traffic exists — meaning users other than the author, asking
questions nobody designed for. Before that, the log would record the Gold
Question Set being replayed, which teaches nothing.

---

### EXT-005 — Semantic Layer coherence checks

- **Status:** open
- **Opened:** Sub-step 1.3, after the knowledge-graph question was decided
  (`.claude/docs/reviews/step-001-target-state-design.md`)
- **Size:** M
- **Seam:** the Metric Definition's declared fields, and the same sqlglot parse
  that [EXT-002](#ext-002--semantic-layer-drift-detection) needs
- **Motivated by:** [ADR-0001](adr/0001-semantic-layer-as-the-retrieval-corpus.md)
  — a certified vocabulary that grows continuously must stay internally
  consistent, or "certified" degrades into "registered"

**What the full system needs**

The Semantic Layer must be checkable as a *set*, not only entry by entry.
Concretely, the rules a growing corpus can violate:

1. **Synonym detection** — two Metric Definitions whose expressions normalise to
   the same parse tree under different names. This is the Shadow Metric failure
   reappearing inside the certified layer, which is the worst place for it.
2. **Undeclared derivation** — `Net Revenue` is `Gross Revenue` minus Rebate and
   Fee. If that relationship is computable but not declared, nothing catches the
   two drifting apart when one is edited.
3. **Orphaned dependencies** — an entry referencing a Join Path or Dimension
   Definition that no longer exists.
4. **Ambiguous Term completeness** — every Certified Metric an Ambiguous Term
   claims to disambiguate between actually exists.

**The design decision, already taken**

A **knowledge graph** was proposed and **rejected** — agreed 2026-08-04. Not
because the relationships are unreal, but because a graph *database* answers an
infrastructure question when the open one was a modelling question. Three
reasons: the corpus is hundreds of entries, not millions, so any structure works;
a separate graph store would be a *third* representation of metrics, which is the
wrong direction when the sharpest known cost is already having two
([EXT-002](#ext-002--semantic-layer-drift-detection)); and sqlglot already
extracts the dependency edges from the SQL expression for free, removing the
hand-declaration that would otherwise drift.

**Chosen instead:** typed relationships declared in the existing YAML —
`derives_from`, `disambiguates` — plus column dependencies **derived** by parsing
the expression. A graph is constructed in memory at build time and the coherence
rules run over it as ordinary code. The files stay the single source of truth,
git supplies review on every metric change, and the checks are unit-testable.
Expression equivalence — the inference that actually matters — is a parse-tree
normalisation, not a description-logic problem.

**What would overturn this:** relationships turning out more open-ended than a
few fixed edge types, or a semantic layer orders of magnitude larger than
assumed. Either would earn a property graph, and would then deserve its own ADR.

**`derives_from` was taken for a different edge — amended 2026-08-22 (Sub-step 4.2)**

Rule 2 above needs an edge meaning *"`Net Revenue` is `Gross Revenue` minus Rebate
and Fee"* — a **declared identity**, checked so that nothing lets the two drift
apart. Sub-step 4.2 needed an edge meaning *"`Account Value` is `Cash Balance`
**added to** this metric's own expression"* — a **composition**, which the check
that executes a Metric Definition actually assembles a query from. Both are
relationships between two Certified Metrics and they are not the same
relationship: one is read to compare, the other is read to compute, and a metric
declaring the first under the field that means the second would be assembled into
arithmetic nobody wrote.

`derives_from` now carries the composition, decided in
[R8](plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)
and enforced by `check_semantic_layer.py`. **So this entry's rule 2 needs a second
edge type when it is built** — under its own name, in the same YAML, alongside
`derives_from` and `disambiguates`. Recorded here rather than left to be
rediscovered, because the cost of discovering it later is a corpus in which one
field means two things and only one of them is checked.

Two further limits the composition carries, both stated because they are what a
coherence check would otherwise assume: it adds and never subtracts, and it walks
**one** level rather than a chain. Neither is a shortcut behind a seam that this
project owes repayment on — the corpus has one composed metric, it adds, and its
part composes nothing — but a rule-2 edge type arriving into a corpus that has
grown either of those is arriving into a different problem.

**Rule 4 was built early, in Sub-step 4.4 — this entry stays open on the other three**

*"Ambiguous Term completeness"* above is now a loop in `check_semantic_layer.py`:
every Certified Metric an Ambiguous Term names must exist as a Metric Definition,
and there must be at least two distinct ones. It was taken out of the extension
rather than with it because it costs one pass over five entries and because the
Sub-step that wrote the first Ambiguous Term could not honestly publish one without
it — an entry that asks the user to choose between two meanings and can compute
only one has spent the user's turn to arrive nowhere. The
[Step 004 plan's scope boundary](plan/step-004-semantic-layer.md#not-in-this-step)
says so in those terms: *"4.4 takes one of EXT-005's four rules because it is a
single loop."*

**Nothing about the other three changed.** Synonym detection, the rule-2 edge type
this entry gained on 2026-08-22, and orphaned dependencies all still need the parse
step and the in-memory graph, and none of them is a single loop. What rule 4's early
build does establish is the shape the rest inherit: the relationship is declared in
the YAML, the check reads it against the rest of the corpus, and the failure names
the entry and the missing thing rather than reporting a count.

**Readiness**

When the Semantic Layer has enough entries for a human to stop holding the whole
set in their head — in practice the same threshold as
[EXT-003](#ext-003--metric-authoring-at-scale), around 50 entries — or as soon as
a second author can add entries. Build with EXT-002; they share the parse step.
Rule 4 above is already built and does not wait for this.

---

### EXT-006 — Position Change attribution

- **Status:** open
- **Opened:** Sub-step 2.1, on Amino's review of the snapshot design (2026-08-06)
- **Size:** M
- **Seam:** `fct_position_snapshot`, and the `Position Change` Metric Definition
- **Motivated by:** the [Section C](glossary.md#c-distinctions-we-must-not-blur)
  pair *Position Change* versus *Trade* — *"Positions also change through
  transfers and corporate actions"* — which the slice can **measure** but cannot
  **explain**

**What the full system needs**

A fact table at event grain recording every cause of a Position moving — a Trade,
a transfer in or out, a corporate action — so that the difference between a
snapshot delta and the sum of Trades has a name instead of being a residual:

```
fct_position_movement(movement_date, account_id, instrument_id,
                      quantity_delta, cost_basis_delta, movement_reason, trade_id)
```

The snapshot then becomes a materialisation of the fold rather than an
independent truth, and reconciling the two is a check rather than an act of
faith. `cost_basis_delta` is what carries a basis for quantity that arrives
without a Trade to price it, which is the case a transfer creates and the one a
fold over `fct_trade` can never recover.

**What the slice does instead, and why that is correct here**

The snapshot answers *what was held* and `fct_trade` answers *what was done*, and
`Position Change` is a delta between two snapshot dates. That satisfies the
metric exactly as registered — *"Change in a Position between two points in time,
from any cause — a Trade, a transfer, or a corporate action"*. It promises the
change; it does not promise the cause. No Certified Metric, no Dimension
Definition and no Ambiguous Term in the slice asks which cause, so building the
table now would be modelling for a question nobody has posed.

**Why it matters in the full system**

Attribution is the first thing a reconciliation agent needs — the Target State
already names *"multi-agent reconciliation and anomaly detection"* as a full-MVP
capability, and a reconciliation that can only say *"the numbers differ by 20
shares"* has done the easy half. It is also what turns the Section C pair from a
warning into a demonstrable trap: with causes recorded, a Gold Question can show
the two numbers diverging and name why.

**Readiness**

A Certified Metric, Dimension Definition or Gold Question needs to attribute a
Position Change to a cause — in practice, the first question of the form "how
much of this move was trading?".

**Not to be confused with** making the trap *real in the data*, which is a much
smaller thing and belongs to Sub-step 2.5 — numbered 2.3 when this entry was
written, renumbered by R16 on 2026-08-10: the simulator emitting a few transfers
so that a snapshot delta and a sum of Trades actually disagree somewhere. That
needs no new table, and without it the Section C distinction is asserted rather
than demonstrated.

---

### EXT-007 — Corporate actions

- **Status:** open
- **Opened:** Sub-step 2.1, when Amino approved simulating transfers but not
  corporate actions and asked where the excluded half belongs (2026-08-06)
- **Size:** M
- **Seam:** `fct_instrument_price`, `fct_position_snapshot`, and the
  `Realised P&L` / `Unrealised P&L` Metric Definitions
- **Motivated by:** the [Section C](glossary.md#c-distinctions-we-must-not-blur)
  pair *Adjusted Close vs Market Price*, which forbids the usual shortcut, and the
  `Position Change` row naming corporate actions as a cause of a Position moving

**Is this in the full Minimum Viable Product's scope? Yes — but as something the
system must not break on, rather than something it builds.**

That distinction is the whole entry. Veritas is a **reader of a warehouse, not a
book of record**. It does not create corporate actions; a real brokerage warehouse
already records them, and the full system reads that warehouse. So the extension
is not "simulate splits" — it is "be correct over a book where splits happened",
which is a Semantic Layer and pricing concern, not a generator concern.

**What the full system needs**

1. **A split-aware relationship between quantity and price.** A 4:1 split quarters
   the unadjusted close overnight. Marking a Position at `Market Price` across that
   date shows Account Value collapsing ~75% with no Trade behind it. The quantity
   must move on the same date the price does.
2. **Corporate actions as a `movement_reason`** in
   [EXT-006](#ext-006--position-change-attribution)'s `fct_position_movement` —
   the two extensions share that table, and EXT-006 should be built first or with
   it.
3. **Cost Basis carried through the action.** A split changes quantity without
   changing what the holding cost, so `cost_basis` must survive unchanged while
   quantity multiplies. A dividend does the opposite. Getting this wrong misstates
   both P&L metrics, which is the failure `data-availability.md` already measured
   for the adjusted-close route.
4. **Never by reaching for `Adjusted Close`**, which is the tempting shortcut and
   is registered as an anti-pattern precisely because it rewrites history and makes
   an Account Value irreproducible.

**What the slice does instead, and why that is correct here**

Holds no corporate actions and, more importantly, **holds no data containing
one** — the price window for held Instruments is kept split-free, and Sub-step
**2.3**'s `--sources` check is required to verify that rather than assume it. It
was Sub-step 2.2's until R16 split the price load into its own Sub-step on
2026-08-10, which is where the check now naturally belongs. Client
activity is synthetic and we choose the instruments, so this costs nothing. It is
correct for the slice because a corporate action here would force the choice
between building the machinery above and holding knowingly incoherent data, and
the third option — quietly using `Adjusted Close` — is the exact wrong number the
project exists to prevent.

**Why this is not debt**

The current code is right for its scope, and the trigger cannot fire inside this
project's life: it fires when Veritas points at a warehouse it did not populate.
It becomes debt only if the slice ever loads a price window containing a split,
which is what the `--sources` guard exists to make impossible by accident.

**Readiness**

Either: the Warehouse is pointed at real (non-synthetic) client data, which will
already contain corporate actions; or the loaded price window can no longer be
kept split-free — for example a longer history, or a held Instrument chosen for a
reason other than our convenience.

---

### EXT-008 — The data checks run in continuous integration

- **Status:** open
- **Opened:** Sub-step 2.5, on Amino's question about where the two data checks
  belong (2026-08-13)
- **Size:** M
- **Seam:** `.claude/scripts/check_warehouse.py` and
  `.claude/scripts/check_data_availability.py` as command-line programs that carry
  a non-zero exit code, and `uv run python -m veritas.ingestion` as the
  one-command, network-free bring-up they run against
- **Motivated by:** [ADR-0004](adr/0004-snapshot-and-replay-and-where-dlt-stops.md)'s
  accepted cost — nothing detects that a committed snapshot no longer matches what
  the source would return — and
  [EXT-002](#ext-002--semantic-layer-drift-detection), whose seam is *"the
  continuous-integration check"* that does not yet exist

**Two kinds of script share one directory, and only one kind is ours**

`.claude/scripts/` holds four programs, and they answer to different authorities:

| Script | What it checks | Whose rule |
|---|---|---|
| `verify_framework.py` | documents exist, links and anchors resolve, skills load | the framework in `CLAUDE.md` |
| `check_language.py` | Glossary terms, writing conventions | the framework in `CLAUDE.md` |
| `check_warehouse.py` | the schema, the constraints, the adapter seam, the loaded data, the Section C pairs | the **data** |
| `check_data_availability.py` | the sources are reachable, key-free, and still contain the traps | the **data** |

The first two check that the way we work is intact, and they stop mattering the
day the framework does. The last two check that **the numbers are right**, which is
the project's subject, and they keep mattering for as long as anything reads the
Warehouse. Nothing today runs any of them except a person remembering to.

**What the full system needs**

1. **A continuous-integration job on every change** that builds the Warehouse
   offline from the committed snapshots and runs
   `check_warehouse.py --sources` and `--distinctions`. Every one of the checks
   they carry — every price re-derived from its snapshot, every rate, every
   constraint, every Section C pair, the adapter seam, the determinism of the
   simulated half — becomes a gate rather than a habit.
2. **A scheduled job** running `check_data_availability.py --refresh`, which is the
   only thing that would notice a source dying or a wrong-number trap
   disappearing. It opens a socket, so it belongs on a schedule and not on a
   change.
3. **A home outside `.claude/`** for the two data checks, decided at the same time.
   `.claude/` is the working directory of the framework, and a check that a
   continuous-integration pipeline depends on is not a framework artefact.

**What the slice does instead, and why that is correct here**

The scripts are written, committed, and run by hand — their output is pasted into
the Step Review that made the claim, with the command that produced it, which is
what Non-Negotiable #4 requires. That is genuinely sufficient at this scale: one
author, one machine, and a review of every Sub-step by the person who commits it.
Continuous integration adds nothing a review by Amino does not already do, on a
repository where every change passes through him.

**Why this is an extension and not debt**

The scripts are right as they stand. There is no shortcut inside them to repay —
they exit non-zero, take no arguments they cannot document, and run offline. What
is missing is a **pipeline to run them in**, and this repository has none at all;
adding one now would be building infrastructure for a team of one. The trigger
test settles it: *"a continuous-integration pipeline exists"* cannot fire inside
this project's life unless we choose to make it fire, which is the definition of a
wish rather than a trigger.

**One caveat worth stating rather than assuming.** Both scripts check *toy*
sources today — a committed Yahoo snapshot and a seeded simulator. When the
Warehouse points at a real source, `check_data_availability.py` may have nothing
left to check and `check_warehouse.py --distinctions` loses its re-derivation half
entirely, because the simulator stops being the source. So this extension should be
built **after** that migration, not before: what a pipeline should run depends on
what the sources are, and deciding it now would be deciding it against sources that
are about to be replaced.

**Readiness**

Any one of:

1. A continuous-integration pipeline exists in the repository for any reason —
   at which point these two scripts are the first thing it should run.
2. A second person can change the repository, so "Amino reviews every commit"
   stops being the enforcement mechanism.
3. The Warehouse is pointed at real sources, which is when the checks' subject
   changes and their content has to be re-decided anyway.
---

### EXT-009 — The Join Path entry type at Warehouse scale

- **Status:** open
- **Seam it lands against:** the `semantic/joins/` file format · a Metric Definition's
  `join_paths` list
- **Size:** M
- **Motivated by:**
  [R9's fourth ruling](plan/step-004-semantic-layer.md#r9--aminos-four-rulings-on-the-42-review--decided-2026-08-23),
  which answers the [Sub-step 4.2 review](reviews/step-004-semantic-layer.md#sub-step-42--write-the-remaining-metric-definitions)'s
  observation that most published Join Paths have exactly one user

**What the full system needs**

A Join Path is registered as a **shared** route — a way between two tables, written once
and named so that any metric needing that way can say its name instead of re-deriving
the join. At Warehouse scale that is what the entry type buys: dozens of fact tables mean
routes multiply, the same route is wanted by many metrics, and a library of named routes
is the difference between one reviewed join condition and forty copies of it. What the
full system needs on top of what exists here is the machinery that only matters once
routes are genuinely shared:

- **a naming rule for the directory**, so a route's name says what separates it from its
  neighbours by construction rather than per file. Sub-step 4.2 renamed two routes onto
  the currency axis and left a third on the date axis, each locally correct and the set
  mixed — which is what a rule would prevent;
- **reuse as a checkable property.** A route with no second user is not wrong, but at
  scale it is the signal that a metric author wrote a private join and gave it a public
  name, which is the copy-paste the entry type exists to prevent;
- **composition beyond a flat list.** `join_paths` is an ordered list a route walks
  once. A Warehouse with real branching wants routes that share prefixes, and this format
  makes each metric restate the whole walk.

**What the slice does instead, and why that is correct here**

It publishes flat, ordered lists of named routes and checks them structurally: every
named Join Path exists, starts at a table the route has reached, arrives somewhere new,
and reaches back only to tables already joined. `check_semantic_layer.py` prints every
metric's full route on every run, so how much reuse there actually is can be counted from
its output rather than asserted here; the count as measured on 2026-08-22 is in the
Sub-step 4.2 review. The honest reading of that count is that **this Warehouse has few
tables and few ways between them** — ten tables in
[Glossary Section B](glossary.md#b-the-warehouse) — so most routes having one user is a
fact about the Warehouse, not a flaw in the entry type.

**Why this is an extension and not debt**

Nothing here is wrong, cheaply. Each Join Path file is a correct, reviewed join
condition, and a metric naming a route it alone uses still gets the thing the seam is
for: the join is written where a reviewer reads it, once, beside the expression it
serves, instead of inside a query nobody sees. The trigger test settles it — *"most
routes have more than one user"* cannot fire inside this project's life, because the
number of tables is fixed by the Warehouse and the number of metrics is fixed at nine by
Glossary Section B. Acting now would be tuning a design against a corpus too small to
show whether the tuning helps, which is
[R9](plan/step-004-semantic-layer.md#r9--aminos-four-rulings-on-the-42-review--decided-2026-08-23)'s
*"premature optimizing"* precisely.

**Readiness**

Any one of:

1. The Warehouse gains fact tables beyond Glossary Section B's ten, so routes start
   having genuine alternatives and the naming rule has something to rule on.
2. Metric authoring moves out of hand-written YAML — this is
   [EXT-003](#ext-003--metric-authoring-at-scale)'s subject, and a generator needs the
   naming rule as input rather than as review commentary.
3. A Join Path is wanted that this format cannot express: a branching route, a shared
   prefix, or a route from a table to itself — the shape
   [`Position Change`](reviews/step-004-semantic-layer.md#sub-step-42--write-the-remaining-metric-definitions)
   already needs and reaches with a correlated subquery instead.

---

### EXT-010 — A metric certified over more than one date column

- **Status:** open
- **Opened:** Sub-step 5.4 (`.claude/docs/reviews/step-005-validation-gate.md`)
- **Seam it lands against:** the date half of `ValidationGate.routed` · a Metric
  Definition's `date_column`
- **Size:** S
- **Motivated by:** the eighth sceptical item of the
  [Sub-step 5.4 review](reviews/step-005-validation-gate.md#sub-step-54--pay-debt-014-the-gate-checks-the-route-and-the-date-predicate),
  ruled on in [R15](plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28)

**What the full system needs**

A Metric Definition carries **one** `date_column`, and the Gate reads it as the only date
column any WHERE clause in a statement computing that metric may key on. That conflates
two different things which happen to be the same one today:

- **the period axis** — the column a *question's* period narrows on, which is what
  `date_column` is for and what
  [C2](design/validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate)
  put on the entry;
- **the date predicates the metric's own expression carries**, which are part of the
  certified computation and have nothing to do with the question.

A metric whose certified expression keyed on a *second* date column — a revenue metric
that counts Trades executed in the period but settling after it, a lag test between
`trade_date` and `settlement_date`, an as-of price read at a date the expression itself
fixes — would be **refused by the Gate when computed exactly as its own entry says**. The
full system needs the permitted set to come from a list, the way `permitted_route`
already takes its joins from one: the metric's `date_column`, plus the date columns its
own certified expression keys on, and nothing else.

**What the slice does instead, and why that is correct here**

One permitted date column per metric, read from `date_column`, and it is not a
simplification that happens to hold — it is checked against every metric in the corpus on
every run. `route.py`'s `check_every_certified_metric_stays_on_its_route` builds each of
the nine metrics' own statement out of its own entry and puts it in front of the rule, so
a metric that stopped satisfying this would fail the run rather than be discovered by a
question.

`Position Change` is the case that shows the reading is right rather than lucky. Its
expression holds a correlated scalar subquery carrying
`previous_snapshot.snapshot_date < fct_position_snapshot.snapshot_date` in a WHERE of its
own, so a statement computing it has a date-keyed WHERE clause whether or not the
question had a period in it — and it passes, because that column *is* its `date_column`.
The one metric in the corpus with a date predicate inside its expression is the one metric
for which one column is enough.

**Why this is an extension and not debt**

Nothing here is wrong, cheaply. Reading one column per metric is the correct reading of a
corpus in which no metric keys on two, and the narrower rule is the stronger one: it
refuses `a period keyed on Settlement Date`, which is a
[Section C](glossary.md#c-distinctions-we-must-not-blur) pair the whole rule exists to
separate. The trigger test settles it — *"a Certified Metric whose expression keys on a
second date column"* cannot fire inside this project's life, because the nine metrics are
fixed by [Glossary Section B](glossary.md#b-the-warehouse) and no Step in this project
writes a tenth. Building the list shape now would be a permission list with one source
and nothing to widen it for.

**Not the same question as `by settlement date`.** [R11's second ruling of Step
004](plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)
deferred a `by settlement date` **axis** to the Step that grounds a query, because
certifying it *"would let one question be sliced on one date while being filtered on
another."* That is about what the corpus may certify as a slice, and a slice puts the
column in a GROUP BY. This entry is about what a metric's own **expression** may key on
in a WHERE. The two meet only if a metric is later certified over both dates, which is
Readiness 2 below.

**Readiness**

Any one of:

1. A Certified Metric is written whose expression keys on a date column other than its
   own `date_column` — the direct trigger, and the one that needs a tenth metric or an
   edit to one of the nine.
2. A metric is certified over **two** period axes, so `date_column` stops being a single
   value at all. That is the corpus-side half of R11's deferred question and is decided
   where R11 sent it.
3. The date half of the route rule is widened for any other reason and gains the list
   shape `permitted_route` already has, at which point this costs one more source rather
   than a new mechanism.

### EXT-011 — More Large Language Model providers behind the seam

- **Status:** open
- **Opened:** Sub-step 6.3 (`.claude/docs/reviews/step-006-retrieval-and-orchestrator.md`)
- **Seam it lands against:** the `PROVIDERS` registry in `veritas/llm/model.py` ·
  the `LanguageModel` seam it sits behind
- **Size:** S
- **Motivated by:** [ADR-0005](adr/0005-one-openai-compatible-endpoint-for-every-provider.md)'s
  last stated cost, and Amino's ruling of 2026-08-30 that closed the list:
  *"we should restrict the supported LLM providers to these two for now and make
  it an extension to support more options."*

**What the full system needs**

Veritas talks to two providers: OpenAI, and Groq for the second model the
evaluation criterion needs. A system serving people who are not this project's
graders reaches more of them — Anthropic and Google are the two named most often,
and a deployment inside a bank reaches whichever one its procurement approved and
no other. Some of those are one more row in `PROVIDERS`; Anthropic's own
Application Programming Interface (API) is not, and needs a second class behind
`LanguageModel` speaking the Messages API — around thirty lines, and no caller
changes, because the seam is what the callers hold.

**What the slice does instead, and why that is correct here**

A closed two-row registry, and an environment variable naming anything else raises
`LanguageModelError` listing the two. That is not a narrowing of something wider —
it is the whole of what the credential rule permits. The
[Target State](design/target-state.md#what-credential-free-means) allows *"a
credential the grader already has by virtue of taking the course"*, which is the
OpenAI key and nothing else; Groq rides along because its free tier costs a
reviewer nothing and the *"≥2 models"* criterion cannot be met with one provider's
default alone.

**Why this is an extension and not debt**

The trigger test settles it. A third provider can only be wanted by someone who is
not a Zoomcamp grader — every grader has the OpenAI key by construction, and the
free Groq key is the second. Nothing inside this project's life fires it. Filing
it as debt would put *"when Veritas serves someone else"* on the Ledger, which the
framework itself calls a wish.

It also lands as pure addition. `PROVIDERS` is a table of four fields, `model_for`
reads it, and every caller holds `LanguageModel` — so a fourth provider is a row,
and a provider that does not speak Chat Completions is a class beside
`ChatCompletions` with no caller edit. That is the *addition, not rewrite* test.

**Readiness**

Any one of:

1. Veritas is run by someone who is not a Zoomcamp grader and holds a key for a
   provider that is not one of the two — the direct case, and the one the closed
   registry currently refuses by name.
2. Either provider stops being reachable on a free or already-held key, at which
   point the second row has to be replaced rather than added to.
3. A model capability Veritas needs is served by neither — the case that also
   forces the second class behind the seam rather than a third row.

### EXT-012 — The dashboard's panels read the dashboard's time range

- **Status:** open
- **Opened:** Sub-step 8.5 (`.claude/docs/reviews/step-008-observability.md`)
- **Seam it lands against:** each panel's `rawSql` in
  `grafana/dashboards/question-log.json` · `question.asked_at`, the column the two
  time-series panels already plot along
- **Size:** S
- **Motivated by:** the second sceptical item of the
  [Sub-step 8.5 review](reviews/step-008-observability.md#sub-step-85--the-grafana-dashboard),
  and Amino's ruling of 2026-09-04: *"i can zoom into panels when i open the dashboard.
  however, if this is really a limitation, open an extension for it"*

**What the full system needs**

`$__timeFilter(asked_at)` in every panel's WHERE clause and the time picker shown, so
that *"the last hour"* is a control on the page. Grafana's own idiom, and the reason a
dashboard over live traffic is a dashboard rather than a report: on a log that grows all
day, *"how many questions were refused"* has no answer until it says over what period,
and every panel here answers it over all of history.

**What the slice does instead, and why that is correct here**

Every panel reads the whole log, and the picker is hidden rather than left showing a
control that changes nothing. What a reader can still do is what Amino did on 2026-09-04:
drag across either time-series panel, which narrows the **axis** to the dragged range —
the picture zooms, the query does not, and the five counting panels are unaffected
because they carry no time axis to zoom.

That is the right trade at this size. The log holds a demo's traffic — dozens of
questions over two days, asked one at a time through the App's page — so every panel
already fits on one screen, and a picker over it would narrow a range nobody needs
narrowed.

**Why this is an extension and not debt**

The trigger test settles it: traffic big enough for a period to matter cannot arrive
inside this project's life. Rows enter the Question Log one question at a time, from a
person typing into the App, and the Evaluation sweep — the one thing here that asks
hundreds of questions — deliberately writes none of them
([Step 008 plan](plan/step-008-observability.md#three-route-decisions), route decision 1).
A Ledger entry would carry *"when Veritas serves real traffic"*, which is a wish.

**What adopting it costs**, since that is what makes it `S`: one line per panel, the
picker unhidden, and one test each way.
`test_grafana_runs_every_panel_through_the_datasource_compose_gave_it` needs no change —
it posts each query to `/api/ds/query` with a `from` and a `to`, and Grafana expands the
macro server-side exactly as it does for the browser.
`test_every_panel_query_executes_against_the_schema` cannot: it hands the string to
psycopg, which has never heard of `$__timeFilter`, so it would have to expand the macro
itself and would then be proving a string of the test's own making.
`test_no_panel_query_holds_a_macro` is what holds that line today, and is the test this
extension deletes.

**Readiness**

Any one of:

1. Veritas records traffic that no longer fits one screen — the direct case, and the one
   that makes a panel over all of history unreadable rather than merely un-zoomable.
2. A question is asked of the log that is about a period rather than about the whole
   record — *"what did this morning look like"* — which is the same need arriving before
   the volume does.
3. The direct-against-schema test is retired in favour of the one that goes through
   Grafana, at which point the macro costs nothing at all.

### EXT-013 — Grafana reads the Question Log with credentials of its own

- **Status:** open
- **Opened:** Sub-step 8.5 (`.claude/docs/reviews/step-008-observability.md`)
- **Seam it lands against:** `grafana/provisioning/datasources/question-log.yml` · the
  `POSTGRES_*` values `.env` declares and `veritas/observability/postgres.py` reads
- **Size:** S
- **Motivated by:** the fourth sceptical item of the
  [Sub-step 8.5 review](reviews/step-008-observability.md#sub-step-85--the-grafana-dashboard),
  and Amino's ruling of 2026-09-04 on it: *"it's ok for now. you can also make an
  extension for this if you see fit."*

**What the full system needs**

Two things the demo folds into one. A Postgres role that may `SELECT` on the four
Question Log tables and do nothing else, which is what the datasource file is handed; and
a viewer who signs in, rather than anonymous access with the Viewer role. A dashboard is
a read, and a read does not need the credentials that write the rows it charts —
granting `SELECT` on those four tables to a role of its own is the whole of the change on
the Postgres side.

**What the slice does instead, and why that is correct here**

Grafana connects as the same Postgres user the App writes with, and anonymous viewing is
on with the admin login declared in `.env.example` for anyone who wants to edit a panel.
Both are deliberate and both buy the same thing: `docker compose up` opens the dashboard
with nothing typed and nothing clicked, which is what the reproducibility criterion asks
of a reviewer who has cloned the repository and has five minutes.

**Why this is an extension and not debt**

These credentials are the ones the
[Target State](design/target-state.md#what-credential-free-means) already rules on —
*"**Service credentials inside `docker-compose`** — Postgres, Grafana · ✅ yes · Not
obtained, declared"* — and the same section closes the deployment question: *"Cloud
deployment is out of scope for the slice regardless."* So the condition that makes one
credential set wrong is a Veritas somebody other than the person who started it can
reach, and that cannot happen inside this project's life. The code is right for this
scope rather than cheap: nothing is being deferred except the second role that a second
reader would need.

It lands as pure addition. The datasource file names a user and a password, so a
read-only role is a different pair of values in it plus one granting statement beside the
schema; and
`GF_AUTH_ANONYMOUS_ENABLED` is one line of the compose file. No caller and no query
moves, which is the *addition, not rewrite* test.

**Readiness**

Any one of:

1. Veritas runs anywhere a second person can reach it — the direct case, and the one that
   makes anonymous viewing a decision rather than a convenience.
2. The Question Log holds anything that is not synthetic. It holds real questions today
   in the sense that a person typed them, but nothing in it is about a real client;
   [DEBT-008](debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
   is the entry that says what the access story is and is not.
3. A second dashboard or a second reader arrives, at which point one role per reader is
   cheaper than one credential set shared by all of them.

### EXT-014 — The container tests run as pipeline stages, before and after a deploy

- **Status:** open
- **Opened:** Sub-step 9.1 (`.claude/docs/reviews/step-009-containerization-and-readme.md`)
- **Seam it lands against:** `tests/test_container.py`'s two runtime fixtures — `app`,
  which skips when nothing answers on the published port, and `container`, which skips
  when `docker compose exec` reaches no App — and `docker compose up -d --build --wait`
  as a bring-up something other than a person performs
- **Size:** M
- **Motivated by:** Amino's question at the 9.1 ruling (2026-09-05): *"as far as i know,
  tests happen before app is served in a CI/CD pipeline, but we're testing the app itself
  after it's deployed and even execute something inside it. what do the best practices of
  CI/CD say about this"* — and
  [EXT-008](#ext-008--the-data-checks-run-in-continuous-integration), whose Readiness is
  the same pipeline

**What the full system needs**

Continuous integration and continuous delivery (CI/CD) does not sort tests by *whether
the application is running*. It sorts them by **which environment they are allowed to
touch**, and the ordinary shape is four stages against one artefact:

| Stage | Environment | What runs there | What it may do |
|---|---|---|---|
| Build | the runner | `docker compose build` — the image every later stage uses | — |
| Unit and static | the runner, nothing serving | this file's claims about `docker-compose.yml`, the `Dockerfile` and `.dockerignore`, and the rest of `tests/` | anything |
| Integration | a stack the pipeline brings up and destroys | the claims that need a server: the health endpoint, the published port, the page driven through `docker compose exec` | anything — write rows, open a shell, spend a budgeted key |
| Smoke, or deployment verification | the real deployment, after release | the health endpoint and one canary question | read-only or self-cleaning, idempotent, fast |

Four rules make that ordering mean something.

1. **Build once, test that artefact.** The image the pipeline releases is the image every
   later stage ran against. A stage that rebuilds has tested something else.
2. **Running the App is not deploying it.** What makes an environment pre-deploy is that
   it is disposable and nobody real reaches it — not that nothing is listening. A stage
   that runs `docker compose up -d --wait`, runs the suite against it and then
   `docker compose down -v` is the standard integration stage, and `docker compose exec`
   is the right tool inside it: reaching into the container proves the image's own
   interpreter, its installed dependencies and its wiring to the network's `postgres`,
   which nothing asked from outside the port can. So the shape Sub-step 9.1 wrote is
   pre-deploy work that happens to have no runner yet, not a test misfiled after a
   deploy.
3. **After the release, far less, under stricter rules.** Deployment verification asks
   the deployed instance for its health endpoint and one canary answer, and its result
   decides the rollout — which is why progressive delivery (canary or blue-green, with
   automatic rollback) is what gives the stage somewhere to put a failure. Its tests must
   be idempotent and either read-only or self-cleaning, because the environment is shared
   and real, and that constraint is exactly why the whole suite never runs there. The
   same check repeated on a schedule afterwards is synthetic monitoring rather than a
   test.
4. **The key comes from the pipeline, not from a file.** The one test that spends a real
   provider key reads it from `env_file` today; a pipeline reads it from a secret store,
   and the post-deploy canary spends against a budget somebody has agreed to.

The split has one consequence in the test file: the `docker compose exec` test belongs to
the integration stage and can never be the post-deploy one, because a real deployment
offers a port and no shell. Whatever runs after a release has to go through the published
interface.

**What the slice does instead, and why that is correct here**

Both stages exist as tests and the runner is a person. The file-level claims run
everywhere; the runtime claims skip — naming what was missing — rather than fail when
there is no stack, so `uv run pytest` from a fresh clone stays green, and the one that
spends a key is gated on `VERITAS_LIVE_MODEL` as well. Because the stack it runs against
is the developer's own rather than disposable, that test already keeps the discipline the
post-deploy stage would impose on it: it deletes the row it wrote, since the Question Log
it writes to is the one the Grafana dashboard charts.

**Why this is an extension and not debt**

The tests are right as they stand — the same argument
[EXT-008](#ext-008--the-data-checks-run-in-continuous-integration) makes about the two
data checks. There is no shortcut inside them to repay: they assert what they claim, they
skip only on an absent dependency, and their fixtures are already the contract a runner
would satisfy. What is missing is a pipeline to run them in, and a **deploy** for a
post-deploy stage to verify — Veritas runs where the person who started it is sitting, so
"after the deploy" has no subject. A trigger that cannot fire until the slice becomes
something else is a wish, which is the test that puts this here rather than on the Ledger.

It lands as pure addition: a workflow file running commands that already exist, plus a
marker separating the two runtime tests into their stages. No fixture, no assertion and
no name moves.

**Readiness**

Any one of:

1. A pipeline exists in the repository for any reason —
   [EXT-008](#ext-008--the-data-checks-run-in-continuous-integration)'s first condition.
   Its two data checks and this file's build-time claims are the same stage, so whichever
   entry is built first should place both.
2. Veritas is deployed anywhere that outlives the session which started it, which is what
   gives "after the deploy" something to verify.
   [EXT-013](#ext-013--grafana-reads-the-question-log-with-credentials-of-its-own)'s first
   Readiness names the same moment from the credentials' side, and the two would be built
   together: a canary question against a deployment writes a real row.
3. A second person can push, so "Amino ran the suite before committing" stops being the
   runner.
