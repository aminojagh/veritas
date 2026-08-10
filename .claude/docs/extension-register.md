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
| [EXT-004](#ext-004--coverage-miss-capture) | Coverage-miss capture | Observability question log · Grounded Answer refusal path | M | open |
| [EXT-005](#ext-005--semantic-layer-coherence-checks) | Semantic Layer coherence checks | Metric Definition fields · the same sqlglot parse as EXT-002 | M | open |
| [EXT-006](#ext-006--position-change-attribution) | Position Change attribution | `fct_position_snapshot` · the `Position Change` Metric Definition | M | open |
| [EXT-007](#ext-007--corporate-actions) | Corporate actions | `fct_instrument_price` · `fct_position_snapshot` · the P&L Metric Definitions | M | open |

**Open:** 7 · **Built:** 0 · **Dropped:** 0

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
- **Seam:** the Observability question log, and the Grounded Answer refusal path
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

**Readiness**

When the Semantic Layer has enough entries for a human to stop holding the whole
set in their head — in practice the same threshold as
[EXT-003](#ext-003--metric-authoring-at-scale), around 50 entries — or as soon as
a second author can add entries. Build with EXT-002; they share the parse step.

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
