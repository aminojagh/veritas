# ADR-0002 — DuckDB is the Warehouse, reached only through an adapter

- **Status:** accepted
- **Date:** 2026-08-03
- **Decided in:** Step 001, Sub-step 1.3

## Context

The system Veritas is a slice of — the full Minimum Viable Product (MVP)
described in the [product brief](../design/product-brief.md) — runs on
**BigQuery**. Warehouse-native governance (policy tags, row- and column-level
security, bytes-billed cost limits) is a large part of what makes that full MVP
credible.

Veritas cannot use it. Two constraints rule it out, and both are load-bearing
rather than convenient:

1. **Reproducibility (2 rubric points, and the project's own claim).** Veritas
   must come up from a `git clone` with no credentials. Sub-step 1.2 already
   spent real effort keeping every data source key-free and snapshotting the
   results into the repository; requiring a Google Cloud account at the warehouse
   layer would throw that away at the last step.
2. **Containerization (2 rubric points).** `docker-compose up` must produce a
   working system. A cloud warehouse is not a container.

So the engine used for the slice will not be the engine used for the real system.
That is the actual situation, and it means the decision is not really "which
engine" — it is **"which engine, and is the choice allowed to leak?"** Those two
questions have very different costs and only the second is expensive to reverse.

One more piece of context matters: a **Postgres already exists in the stack** for
Observability, which makes "use the database you already have" a live and
reasonable option rather than a straw man.

## Decision

**DuckDB** is the Warehouse for the slice, reached only through a single Warehouse
adapter. All SQL is parsed and rendered through **sqlglot**, whose target dialect
is a parameter rather than an assumption. No DuckDB-specific type, function, or
connection object appears anywhere outside the adapter.

## Alternatives considered

| Option | Why not |
|---|---|
| **BigQuery** — the real target engine | The obviously "correct" choice for the full system, and the one that would make the extension path a no-op. Rejected because it requires a Google Cloud account and project id even on the free sandbox tier, which forfeits key-free reproducibility outright, and because a reviewer cloning the repo would be running queries against someone's billing account. Deferred to the extension path, where the adapter is precisely the seam it lands against. |
| **Postgres** — already in the stack for Observability | Genuinely tempting: one fewer engine to install, already containerized, already in the compose file, and mature. Rejected because it collapses the analytical store and the operational store into one box — Observability writes a row on every question, and analytical scans over the fact tables would contend with exactly the writes that record them. It also gives up columnar scan performance and the single-file, zero-server property that makes the simulator and the evaluation notebooks cheap to run outside the container. The operational/analytical split is worth keeping honest even at slice scale. |
| **SQLite** | Zero-dependency and universally available. Rejected on data-correctness grounds rather than performance: no real `DECIMAL`, dynamic typing that will accept a string into a numeric column, and no analytical column store. Monetary aggregation over floats in a project whose entire subject is quietly wrong numbers is not a trade worth making. |
| **Snowflake / Databricks** | Same credential and cost objection as BigQuery, without BigQuery's compensating property of being the actual target. |
| **DuckDB with no adapter** — generate and execute DuckDB SQL directly | The cheap version, and it would ship faster. Rejected because the cost of adding the boundary later is not proportional to the cost of adding it now — see [Why the adapter is not optional](#why-the-adapter-is-not-optional) below. |

## Why the adapter is not optional

The operating agreement phrases this as "a Warehouse boundary is a **seam**, not
fill". That is shorthand, and shorthand is not an argument. Plainly:

**Some shortcuts get cheaper to fix over time, and some get more expensive. The
difference is how many places have to change.**

A slow query is the cheap kind. It lives in one function; you rewrite that
function and you are done, whether you do it today or in six months. The cost of
fixing it does not grow.

Talking to the database directly is the expensive kind. There is no single place
where "we use DuckDB" lives — the assumption spreads into every module that
builds a query, executes one, or reads a result. Each of those is a small,
individually reasonable line of code. Six months later, changing engines means
finding and editing all of them, and the ones you miss fail at runtime rather
than at import.

So the two options are not "adapter now" versus "adapter later at the same
price". They are:

| | Cost |
|---|---|
| **Adapter now** | One module with one implementation. Perhaps an afternoon. The `Warehouse` name and the method signatures are the only things that must be right; what is behind them can be as crude as we like. |
| **Adapter later** | Find every place that assumed DuckDB, change them together, and re-test everything downstream — including the Validation Gate, which reads the same parse trees. |

The second cost is unbounded because it depends on how much code got written in
between, which is exactly the thing we cannot know in advance.

This is why the operating agreement allows debt *behind* a seam but not *across*
one. Behind the seam, everything is fair game: the adapter's first implementation
can hardcode a path, ignore connection pooling, and handle no errors at all —
each of those is fixed in one place, later, for the same price as today. What may
not be deferred is the boundary itself, because deferring it is the one shortcut
whose repayment cost grows with time.

The practical test, and the reason this is cheap rather than ceremonial: **a seam
is an interface plus one trivial implementation.** We are not building an
abstraction layer for engines we do not have. We are naming a boundary once,
today, while there is nothing on either side of it.

## Consequences

**What this buys us.**

- Zero-credential, zero-cost bring-up. The reproducibility criterion is satisfied
  literally rather than argued for.
- Fast local analytical queries, which matters more than it first appears: the
  evaluation loop runs the whole Gold Question Set repeatedly, and its speed
  determines how often we are willing to run it.
- DuckDB reads Parquet and CSV directly, so the snapshotted source data from
  Sub-step 1.2 is ingestible with very little machinery.
- The engine swap on the extension path becomes an adapter implementation plus a
  sqlglot dialect parameter, instead of a rewrite of everything that emits SQL.

**What this costs us.** Each cost is classified — *accepted*, *debt*, or
*extension* — so none of them sits here as a fact nobody acts on.

- **DuckDB's dialect is not BigQuery's, and sqlglot's transpilation is good but
  not total.** Anything the generated SQL comes to rely on that has no BigQuery
  equivalent is a migration cost that stays invisible until the migration. The
  adapter contains the *connection*, not the dialect risk.
  → **Accepted.** Unavoidable given the engine choice, and the mitigation is
  discipline: prefer portable constructs in generated SQL, and treat any
  DuckDB-only **construct** in a Metric Definition as a review comment — a
  function name, a type, or anything else whose meaning does not survive the trip
  to the target engine. *Construct* rather than *function* since 2026-08-23; the
  note below says what was measured and what changed the word.

- **The Validation Gate's cost check is much weaker than the real system's, and
  the gap is worth being precise about.** In BigQuery, the check that matters is
  a **dry run**: you submit the query with a flag that says "do not execute
  this", and BigQuery returns the exact number of bytes it *would* scan, before
  a cent is spent. Because BigQuery bills by bytes scanned, that number converts
  directly into money — so a rule like *"reject any query that would cost more
  than $5"* is enforceable, exact, and known in advance.

  DuckDB has no equivalent. It is a local process reading local files; there is
  no billing model, so there is no number to ask for and nothing to convert. The
  slice's cost check therefore cannot be about money at all. What it can do is
  inspect the parse tree and reject queries with the *shapes* that get expensive:
  no `WHERE` clause on a fact table, no date bound on a dated series, a
  cross join, a missing `LIMIT` on an exploratory query.

  Three honest differences follow. **It is a proxy, not a measurement** — query
  shape correlates with cost but does not determine it, so a bounded-looking
  query over a huge partition passes and an unbounded one over a tiny table is
  refused. **It cannot be tuned to a budget**, because "expensive" has no units
  here; the thresholds will be structural rules someone chose, not a limit
  derived from what the business will pay. **It is untested against the thing it
  is a proxy for**, since there is no real cost signal in the slice to correlate
  it against.

  What it *does* buy is the seam: the Validation Gate gains a cost-check
  interface, exercised by real rules, that the full MVP swaps for a dry-run call
  without moving anything around it. The claim to make about it is "the cost
  check exists and is structural", never "Veritas enforces a query budget".
  → **Accepted for the slice, extension for the full MVP** — the swap lands
  against the Validation Gate's existing cost-check interface.

- **No concurrency story, and no engine-native row- or column-level security.**
  DuckDB is single-writer, so the App supports one user at a time. And
  because DuckDB has no policy-tag mechanism, the Access Profile must be enforced
  in application code by the Validation Gate rather than by the engine — a
  strictly weaker guarantee than the real system's warehouse-native policies, and
  the direct reason ADR-0003 carries as much responsibility as it does.
  → **Extension: [EXT-001](../extension-register.md#ext-001--warehouse-native-security-and-concurrency)**
  for the engineering — one migration delivers both, and the application-layer
  check is **removed** when it lands rather than kept as defence-in-depth, since
  two enforcement points for one rule is two places to drift and the weaker one
  supplies false assurance about the stronger one's coverage.
  → **Debt: [DEBT-008](../debt-ledger.md)** for what fires inside this project —
  the README and App must say the enforcement is application-layer over
  synthetic data, because an unqualified claim invites a reader to believe a
  guarantee that does not exist.

- **The adapter is overhead unless the engine is ever swapped.** If Veritas lives
  and dies on DuckDB, the indirection bought nothing.
  → **Accepted knowingly.** The extension path is the project's second audience,
  and the seam is what makes the claim to it true rather than aspirational. The
  cost is bounded at roughly an afternoon, which is what makes it acceptable to
  be wrong about.

**What it commits us to.**

- **All warehouse access goes through the adapter.** The signal that this has
  stopped holding is mechanically greppable: a `duckdb` import or a
  DuckDB-specific function name anywhere outside the adapter module. Check it
  before making any claim about the extension path.
- **sqlglot is the only place SQL is parsed or rendered.** If any component
  starts building SQL by string manipulation, the dialect seam and the Validation
  Gate are compromised in the same stroke — ADR-0003 depends on the same
  parse tree.
- **The slice never needs concurrent writers or more data than one machine
  holds.** The signal it has stopped holding: the simulator's output no longer
  fitting comfortably in memory, or bring-up requiring a second writing process.

### Clarification, 2026-08-05 — what the sqlglot commitment forbids

Not a change of decision. Step 002 asked whether hand-authored Data Definition
Language (DDL) inside the adapter is allowed under *"sqlglot is the only place SQL
is parsed or rendered"*, the answer was not obvious from the sentence, and every
later Step inherits the reading. Recorded here rather than in the plan, because
the plan will be closed and this will still be binding.

**The commitment is about SQL that code assembles, not about SQL a human wrote
once.** The sentence's own justification says so — *"if any component starts
**building** SQL by string manipulation"* — and the danger it names is the
dialect assumption spreading into places nobody can enumerate. A static
`schema.sql` spreads nowhere: it is one literal, in the one module the Glossary
already licenses to know the engine (*the Warehouse Adapter "holds the connection
and the engine's dialect"*).

Four cases, in the order they stop being acceptable.

**A. Static DDL inside `veritas/warehouse/` — allowed.**

```sql
CREATE TABLE fct_trade (
    trade_id         BIGINT PRIMARY KEY,
    account_id       BIGINT NOT NULL REFERENCES dim_account(account_id),
    trade_date       DATE   NOT NULL,
    settlement_date  DATE   NOT NULL,
    quantity         DECIMAL(18, 6) NOT NULL,
    execution_price  DECIMAL(18, 6) NOT NULL,
    commission       DECIMAL(18, 6) NOT NULL
);
```

Nothing is rendered; this text *is* the source. An engine swap rewrites this one
file, next to the one connection function that also has to be rewritten. That
cost is bounded and visible on day one, which is the property the whole ADR is
about.

**B. SQL assembled outside the adapter — forbidden, and the case the rule
exists for.**

```python
# anywhere outside veritas/warehouse/
sql = f"SELECT {metric.expression} FROM fct_trade WHERE trade_date >= '{start}'"
```

Two failures in one line. The dialect assumption has escaped the seam into a
module that will be copied, and the Validation Gate can never trust the parse
tree of a string it did not receive intact — ADR-0003 checks *"every metric
expression traces to a Certified Metric"* against a tree, and a tree built from
interpolated fragments has already lost the boundary between certified and
invented.

**C. SQL assembled *inside* the adapter — permitted by the letter, and still
worth refusing.**

```python
# veritas/warehouse/adapter.py
cols = ", ".join(rows[0])
conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})")
```

Inside the seam, so it breaks no commitment. But it is the shape of B, and it is
avoidable at no cost: DuckDB registers an in-memory relation and
`INSERT INTO … SELECT * FROM …` reads it, so no SQL is built from data at all.
The rule to carry forward is **prefer the construct that assembles no text**,
inside the adapter as well as outside it.

**D. DDL generated by concatenation — forbidden even inside the adapter.**

```python
# veritas/warehouse/adapter.py — no
ddl = f"CREATE TABLE {name} (" + ", ".join(f"{c} {t}" for c, t in columns.items()) + ")"
```

This is the case that shows the recommendation is not laziness. The alternative
to hand-authored DDL is not sqlglot-rendered DDL by default — it is *this*, and
it is strictly worse against the concern being protected: the star schema stops
being readable in one place, and a reviewer cannot see what columns `fct_trade`
has without running Python.

**The steel-man for rendering the schema through sqlglot**, since it is the
option the question implies: define the schema as sqlglot expressions once and
render per dialect, so the extension path retargets for free. Rejected, and the
reason is specific rather than stylistic. **The free retarget is not free.**
BigQuery has no enforced primary or foreign keys and no `REFERENCES` clause, so
every constraint in case A is dropped or rewritten by hand on migration anyway —
this ADR already concedes transpilation is *"good but not total"*, and DDL is
where it is least total. What would be bought is a schema nobody can read, in
exchange for a migration that still needs a human.

**The cost this accepts, stated plainly:** the schema does **not** retarget
automatically. The extension path to BigQuery writes a second DDL file by hand.
That is one file, known in advance, against a schema that is legible to every
reviewer for the whole life of the project.
→ **Accepted.**

**How this stops being a promise.** ADR-0002 already named the signal —
*"a `duckdb` import or a DuckDB-specific function name anywhere outside the
adapter module"* — but nothing ran it. Step 002's `check_warehouse.py` performs
that scan, so the commitment is checked on every run rather than asserted in a
review.

### Status note, 2026-08-20 — the retargeting claim was measured, and the mitigation names the wrong unit

Not a change of decision, and the status stays `accepted`. The fourth claim of
[Step 003](../plan/step-003-validation-feasibility.md)'s spike belongs to this ADR
rather than to ADR-0003, because it is this one that put sqlglot in charge of
retargeting and conceded in the same breath that transpilation is *"good but not
total"*. The full findings and the command that reproduces them are in
[validation-feasibility.md](../design/validation-feasibility.md#4-dialect-retargeting---every-verdict-survives-one-type-does-not).

**The verdicts survive completely.** All 25 statements the spike builds keep both
parse-tree verdicts through a DuckDB → BigQuery round trip: a Gate reading a
retargeted statement reaches the same decision as one reading the original.

**One type does not.** `Traded Notional`'s widening cast to `DECIMAL(38, 6)` — proved
necessary on every run, since the engine refuses the uncast expression — retargets to
the single word `NUMERIC`, and so does `DECIMAL(18, 6)`, the width
`fct_trade.quantity` is stored at. The two arrive in BigQuery as the same statement.
Nothing here executes against BigQuery, so this is a statement about the SQL that
would be sent and not about the number that would come back.

**The mitigation above is written in the wrong unit.** The first accepted cost says
to *"treat any DuckDB-only function in a Metric Definition as a review comment"*. The
one construct where meaning was measurably lost is a **cast**, and a cast is not a
function call — so neither that sentence nor `check_seam`'s name-based dialect scan
reaches it. Opened as
[DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast),
whose repayment is the name list **plus** a round-trip comparison over types: the same
Sub-step measured that a round trip passes 39 of the 50 measurable DuckDB-only names
straight through, so the two detectors are blind to disjoint classes and neither
replaces the other. The wording above is left as written for now, with this note
beside it, which is how the 2026-08-05 clarification above was handled — **and was
changed on 2026-08-23, when the debt was paid; see the note below.**

**A related question it also settles.**
[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect)
left open in writing whether transpilation-level checking would be the better scan.
**It would not** — not strictly better, for the reason in the paragraph above.

### Status note, 2026-08-23 — the mitigation now says *construct*, and a run performs it

Not a change of decision, and the status stays `accepted`. The note above recorded
that the first accepted cost's mitigation named the wrong unit and left the sentence
as written, because there was nothing to scan: the Semantic Layer did not exist, so
no Metric Definition existed, and the only cast outside `veritas/warehouse/` was a
Python literal in the spike that measured it. Sub-step 4.2 wrote the corpus, and
Sub-step 4.3 paid
[DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast).

**Two things changed, and the second is what makes the first more than a word.**

The mitigation says **construct** where it said *function*, so the sentence covers a
cast — the one construct the spike measured meaning being lost in.

And `check_seam` performs it rather than asking a reviewer to. It reads the SQL every
Semantic Layer entry publishes as well as the SQL a module emits, and reads all of it
twice: **by name**, as before, and **by type**, retargeting each statement to
BigQuery and reporting every type construct that arrives there saying less than it
says at home. The two readings are blind to disjoint classes and neither replaces the
other, which is the note above's finding and is why the repayment was *the name list
plus a round trip* rather than a swap.

**The two readings end differently, deliberately.** A DuckDB-only function name
outside the adapter fails the run; a lossy type is printed as a **review comment**,
which is the word this mitigation has used since the ADR was written. The reason is
that this corpus carries a lossy type it cannot do without: the published expressions
whose product overflows `DECIMAL(18)` widen the cast to `DECIMAL(38, 6)`, and
`check_semantic_layer.py` runs each of them uncast on every run and prints the
engine's refusal. A check that failed on a construct the engine requires could only be
satisfied by publishing an expression that does not execute.

What the review comment names on the current corpus, and the mutations that show both
readings have teeth, are in the
[Sub-step 4.3 review](../reviews/step-004-semantic-layer.md#sub-step-43--pay-debt-015-the-dialect-scan-reads-type-constructs).

## Related

- ADR-0003 — shares the sqlglot dependency, and inherits the missing
  bytes-billed cost bound; warehouse-native enforcement of the Access Profile is
  the extension-path repayment for both.
- [Target State](../design/target-state.md) — Extension path: "BigQuery instead
  of DuckDB — Warehouse is behind one adapter; SQL is generated via sqlglot,
  which retargets dialects."
- Glossary: `Warehouse` is used as a component name in `target-state.md` but has
  no Glossary row — raised as a Term Proposal in the Step 001 review, together
  with the other unregistered component names.
