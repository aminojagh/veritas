# Validation Feasibility

**The gate on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md).**
Sub-step 3.5 of [Step 003](../plan/step-003-validation-feasibility.md). Before any
Validation Gate or Semantic Layer code exists, prove that sqlglot can decide **from
a parse tree alone** that a generated query computes a Certified Metric and nothing
else, and that a Restricted Column cannot hide from the same tree.

**Checked:** 2026-08-20 · **Verdict: GO on ADR-0003** — its central bet is measured
rather than assumed. The go carries **six constraints on the Semantic Layer and the
Gate**, one of which is already on the Ledger, and a **qualified** result on the one
claim that belongs to [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)
instead. See [The verdict](#the-verdict); the four questions this document put to
Amino were **all approved on 2026-08-20** and are in [Rulings](#rulings).

This is the second design gate, beside [data-availability.md](data-availability.md),
and it is the same kind of document: a question the design could not answer about
itself, answered by a committed script instead of by argument. That one gated the
Target State on whether its sources exist. This one gates the decision the Target
State's [flow](target-state.md#flow) rests on — *"5. VALIDATE — deterministic, on the
parse tree"* — on whether a parse tree can carry the weight.

**No component was built.** The nine component rows in
[current-state.md](current-state.md) are the same after this Step as before it. What
moved is what is known, which is the honest description of a spike and the reason
[the plan argued for it](../plan/step-003-validation-feasibility.md#why-a-spike-is-allowed-to-be-a-step)
before starting.

## Reproducing this check

Every claim in this document is produced by one script, not transcribed by hand:

```bash
uv run python -m veritas.ingestion                            # the Warehouse is gitignored
uv run python .claude/scripts/check_validation_feasibility.py
```

The first builds all ten Warehouse tables offline from the snapshots committed in
`data/snapshots/`; the second is the spike. It **exits non-zero** if any probe's
verdict changes in either direction, if any probe's number stops standing in the
relation the spike recorded for it, or if either dialect detector's reading of a
statement moves — so a finding here cannot quietly stop being true when sqlglot is
upgraded.

**What the script holds still, and what it only prints.** The difference decides
which figures below can go stale, so it is worth stating plainly.

- **Verdicts are asserted.** Every one of the 25 probe statements carries the
  verdict this spike measured for it, and a run where one moves fails. That covers
  the shapes that must trace, the ones that must not, the nine Restricted Column
  shapes judged three ways each, the 25 retargeted statements, and the five
  statements the two dialect detectors are compared over.
- **Percentages and population counts are printed, not asserted.** The script
  checks that two probes which must differ still differ by more than its floor, not
  that they differ by the same amount as last time — a `--refresh` of the source
  data or a new simulator seed moves every figure and breaks nothing. Likewise the
  count of DuckDB-only names the round trip passes through: the run fails only if
  that count reaches zero, which would mean the answer given to
  [DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect)
  had been measured against a weaker transpiler and needed re-deciding.

So **every figure in this document is dated evidence**: measured **2026-08-20**,
against a Warehouse rebuilt the same day by the first command above, and printed by
the second.

**The mutations are not in this document.** A probe only means something if breaking
the thing it measures makes it fail, and each of those is one `sed` command with its
output in the Step Review that recorded it —
[3.2](../reviews/step-003-validation-feasibility.md#sub-step-32--probe-whether-a-generated-query-traces-to-a-certified-metric)
(two),
[3.3](../reviews/step-003-validation-feasibility.md#sub-step-33--probe-whether-a-restricted-column-can-hide-from-the-parse-tree)
(three) and
[3.4](../reviews/step-003-validation-feasibility.md#sub-step-34--probe-duckdb--bigquery-retargeting-on-the-sql-veritas-will-generate)
(three, plus a re-run of all five earlier ones).

---

## Verdict by claim

The four claims are the ones
[Step 002 deferred](../plan/step-002-warehouse-and-ingestion.md#deferred-to-step-003--prove-the-validation-gates-parse-tree-claim)
verbatim, with what counts as an answer fixed in the
[plan](../plan/step-003-validation-feasibility.md#what-the-four-claims-mean-concretely)
before any of them ran.

| # | Claim | Result |
|---|---|---|
| **1** | **Tracing** — a certified expression stays recognisable under aliasing, a subquery and a common table expression | ✅ GO — **and recognisable means *the same form*** |
| **2** | **Restricted Columns** — one can be found behind `SELECT *` or an alias, and is not tripped by a comment | ✅ GO — unconditional, and the schema is what makes it hold |
| **3** | **The Shadow Metric** — revenue open-coded inline is rejected, and returns a different number | ✅ GO — rejected, and the two numbers are far apart |
| **4** | **Dialect retargeting** — a statement round-trips DuckDB → BigQuery without losing meaning | ◐ GO — **every verdict survives; one type does not** |

Claims 1, 2 and 3 are ADR-0003's. Claim 4 is
[ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)'s, which is why
it was the Step's pre-agreed split point and why its qualification does not qualify
the go above.

**The instrument, in one paragraph.** Parse the statement in the Warehouse's
dialect; resolve it against the real schema read through `WarehouseAdapter.columns`,
expanding `SELECT *` and renaming every table alias back to the table it stands for;
then read the resolved tree two ways. Claim 1 walks **every scope** and canonicalises
each projection that aggregates, because a metric computed anywhere in the statement
is one the Gate must place. Claim 2 walks **each output column's lineage** back to
the base-table columns that produced it, because the Target State's rule is about
what reaches the answer. **Two of sqlglot's fourteen optimizer rules are enough** —
`qualify` and `merge_subqueries` — and which two is printed on every run.

---

## 1. Tracing ✅ — but recognisable means *the same form*

Seven shapes trace to a certified expression and are allowed: bare, aliased, a
derived table, a common table expression, a second metric, a **Dimension Definition
applied to a metric** (`net revenue by region`, two extra joins and a grouping column
beside the metric — the shape nearly every real question produces), and a third
metric carrying a cast. The three certified expressions are `Gross Revenue`,
`Net Revenue` and `Traded Notional`, each converted to one Reporting Currency
through `fct_fx_rate`, because a tracer proved against `sum(commission)` proves
nothing about a metric with a join and a conversion in it.

**The finding claim 1 was worth running for is where tracing stops.**
`commission - fee - rebate` does **not** trace where `commission - rebate - fee`
does, and `fx_rate * commission` does not trace where `commission * fx_rate` does.
Both return **exactly** the certified number — the run prints `== commuted
subtraction and net revenue` and `== commuted multiplication and bare` — so the
rejection is a judgement about form, not about arithmetic.

That is a constraint on the Semantic Layer rather than a defect in the tracer, and
it is [C1](#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)
below.

**One shape is allowed and should not be.** `Traded Notional` converted out of the
Trade's Denomination Currency instead of the Instrument's Quotation Currency has an
identical projection, so it traces — and returns 7,264,542,867.58 against
262,266,110.69, **96.39% apart**, a factor of roughly 28. Both columns sit on
`fct_trade`, and the pair is in Glossary Section C precisely because they do. This is
the spike's one deliberate blind spot; it is
[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)
and [C2](#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate)
below.

**A hole in the tracer was found and closed inside Sub-step 3.2**, and it is worth
recording because it is the shape of mistake a Gate will make again. Reading the
outermost scope's projections alone is right for every shape above and wrong for a
union: a union node projects nothing itself, so asking for its projections hands
back its **first branch's**. A statement whose first branch was certified and whose
second was a Shadow Metric was allowed on the strength of the first. The tracer now
walks every scope; the `half-certified union` probe is that case, and 3.2's second
mutation puts the first version back and shows what it did with it.

## 2. Restricted Columns ✅ — and the schema is what makes it hold

Nine shapes, each judged three ways: from the parse tree (the verdict a Gate would
act on), by searching the query's text for the restricted name (ADR-0003's rejected
alternative), and by claim 1's tracer. `dim_client.client_name` is the Restricted
Column, held as a `(table, column)` pair rather than a bare name, because a parse
tree resolves a column to the table it came from and a Gate that forbade the *name*
would forbid it on every table that had one.

Five shapes put a Client's name in the answer and all five are caught. Four do not
and none of them is reported — **four of the nine probes exist only to measure the
second direction**, because a Restricted Column reported where the answer carries
none is the false positive that makes a Gate something people route around.

**`SELECT *` over a join reaching `dim_client` is the shape that decides the
design.** It projects a Client's name while the text `client_name` appears nowhere in
the query. Only expanding the star against the real schema finds it — turning that
expansion off is 3.3's first mutation, and the query becomes allowed. **The Gate is
therefore not a pure function of the SQL text**: it needs the Warehouse's column list
at run time, which is [C4](#c4--the-gate-reads-the-schema-at-run-time) below.

**ADR-0003's rejection of text matching is now a measurement, and it was
understated.** The two disagree on **5 of 9 shapes**. One is the miss the ADR
predicted. The other four are the direction it did not dwell on: text matching
**refuses four perfectly legitimate queries** — a generator explaining in a comment
why it grouped by region instead, a label carrying the withheld column's name as
data, a query that filters on a Client and reports only a total, and a count of
distinct Clients. Making the detector *be* text matching is 3.3's third mutation and
the run fails on all five at once. The ADR's own sentence — *"deterministic without
being correct"* — is the right verdict, and the false-refusal half is the larger one.

**The two parse-tree rules are independent checks, and this one is the only one
standing in four cases.** `net revenue by client`, `aliased to a benign name`,
`hidden behind a derived table` and `a union branch that names the Client` all
compute Net Revenue's certified expression exactly, so claim 1 allows all four, and
all four put a Client's name in the answer. **A Gate implementing
certified-metrics-only alone would ship the leak** — which is worth stating plainly,
because certified-metrics-only is the check ADR-0003 is mostly argued on. It is
[C3](#c3--the-two-parse-tree-rules-ship-together) below.

**Reaching the answer is a different question from appearing in the statement.** A
Client name projected inside a subquery that cannot be folded away and then
aggregated into `count(*)` is in the statement and in nobody's answer — *how many
distinct Clients traded* is an ordinary question whose answer is one number. Reading
every scope's projections, which is the reading claim 1 needs, rejects it;
`sqlglot.lineage` does not, and it costs no new trust because it runs `qualify` and
no other rule.

**One shape is allowed by design and is not a hole.** A query filtered to one Client
and returning only a total leaks by inference, and the Target State's
[flow](target-state.md#flow) already assigns that to a different check on the same
list — *"Access Profile predicate present"*. Claim 2 is the projection rule; the
predicate rule is its neighbour, and this Step measured one of them.

## 3. The Shadow Metric ✅ — rejected, and the rejection is worth having

A tracer that says yes to everything passes claim 1 and catches nothing, so the
statements that must be **rejected** ship beside the ones that must be allowed:
five Shadow Metrics, two paraphrases that are arithmetically the metric, an unknown
table, and a statement sqlglot cannot parse at all.

Revenue open-coded inline out of `commission`, `rebate` and `fee` as three separate
sums is rejected, and it stands **32.59% apart** from `Gross Revenue`'s certified
expression on the data loaded on 2026-08-20 — independently arriving at the same
figure the
[Sub-step 2.5 review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-25--generate-seeded-synthetic-client-activity)
measured for that pair. Two more are rejected and are further away still: the
conversion left out entirely (97.73% apart, and the number is a meaningless sum of
mixed currencies), and one of Net Revenue's three terms silently missing (20.86%
apart from Net Revenue). **The rule the script enforces is that each of these differs
from the certified number by more than its floor**, not that it differs by the
figures quoted here; a run where any pair collapses fails.

That is the whole argument for the Gate in one line. Each of these queries is
correct SQL that executes without error and returns a plausible, well-formatted
number, and each returns the wrong one.

**`Traded Notional` cannot be computed as the Glossary defines it.** Σ(quantity ×
Execution Price) × FX Rate overflows: the engine computes the product in
`DECIMAL(18)` and a JPY notional does not fit. Its certified expression therefore
carries a widening cast to `DECIMAL(38, 6)`, and the script runs the uncast version
on every run and prints the engine's refusal, so the cast is a measurement rather
than a preference — and so a run where it stops being needed fails instead of leaving
a cast whose reason has expired. That cast is what claim 4 then loses.

## 4. Dialect retargeting ◐ — every verdict survives, one type does not

Every statement claims 1 to 3 built — all 25 — is transpiled to BigQuery, re-parsed
there, and put through **both** parse-tree readings against a corpus and a schema
retargeted the same way. **All 25 keep both verdicts.** A Gate reading a retargeted
statement reaches the same decision as one reading the original, on the shapes that
must trace, the Shadow Metrics that must not, the five that project a Restricted
Column and the four that must not be caught.

**A surviving verdict is not surviving meaning.** `Traded Notional`'s widening cast
to `DECIMAL(38, 6)` retargets to the single word `NUMERIC`. So does `DECIMAL(18, 6)`,
the width `fct_trade.quantity` is stored at. **The widened and the unwidened
expressions arrive in BigQuery as the same statement**, and the distinction the
metric needs in order to compute at all is gone from it.

**No certified-metrics-only check can notice that**, and the reason is structural
rather than fixable: the corpus is retargeted by the same rewrite as the query, so
both collapse identically and still match. Claim 1 says *traces*, and it is right
about the question it was asked. A round trip is worth checking for what it preserves
**and** for what it quietly agrees to, and only the first of those is a differential
test.

**What is not measured is what BigQuery would then do.** Nothing here executes
against BigQuery — there is no instance, by ADR-0002's own decision — so this is a
statement about the SQL that would be sent, not about the number that would come
back. BigQuery's `NUMERIC` is fixed at precision 38 scale 9, which is 29 integer
digits where `DECIMAL(38, 6)` has 32: narrower than asked for, and wider than the
`DECIMAL(18, 6)` that provably fails here. **It is entirely possible the retargeted
statement computes correctly.** The defensible claim is the narrow one — the round
trip erases a distinction the Warehouse needs, and nothing in this repository would
notice.

### DEBT-009's open question, answered: no

[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect)
paid half of ADR-0002's dialect signal with a name list read off sqlglot's own
dialect tables, and left one question open in writing: *"whether it needs
transpilation-level checking instead is a question Step 003's spike answers with its
fourth claim"*.

**Transpile-and-compare is not strictly better. The two are blind to disjoint
classes**, which means neither replaces the other:

| | The name list catches | The round trip catches |
|---|---|---|
| `strftime(...)` — a DuckDB name sqlglot can translate | ✅ | ✅ |
| `list_aggregate(...)` — a name sqlglot knows nowhere | ✅ | ❌ |
| `generate_series(...)` — a name sqlglot files as dialect-neutral | ❌ | ✅ |
| a cast to `DECIMAL(38, 6)` — a type, not a call | ❌ | ✅ |

The round trip's blindness has a cause worth naming: **sqlglot emits a name it
cannot translate exactly as it found it, and a comparison of before against after
reads its own failure as portability.** Asked of the whole population rather than of
four hand-picked statements, it passes **39 of the 50 measurable DuckDB-only names
sqlglot knows** straight through unchanged; the name list catches all 51 by
construction, because it *is* that table. The name list's own two misses are in the
table above, and the second of them is not an oversight — a cast is not a function
call, so no list of function names can ever reach it.

**That is the same fact as the cast collapse, seen from the other side.** The one
construct where meaning was measurably lost is the one construct the existing scan
cannot see, and ADR-0002's stated mitigation is *"treat any DuckDB-only function in a
Metric Definition as a review comment"* — **a function is the wrong unit**. Opened as
[DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast),
whose repayment is the name list **plus** a round-trip comparison over types, because
the table above says each one covers what the other misses.

---

## What this Step did not measure

Stated at the same volume as the findings, because a feasibility gate that lists only
what it proved is the confident overstatement this project exists to prevent.

- **Three of the Validation Gate's five checks are untouched.** The Glossary's
  `Validation Gate` row lists
  *"certified-metrics-only, no restricted columns, access policy applied, cost
  bounded, read-only"*. This Step looked at the first two. The Access Profile
  predicate, the bounded scan and read-only are unexamined; a statement that writes
  is refused by the tracer, but incidentally — sqlglot builds no scope for it —
  rather than by a rule.
- **Only projections are read for claim 1.** A metric expression appearing solely in
  a filter applied after grouping, or in an ordering clause, is not examined. That is
  defensible, since the Target State's rule is about what a query *computes*, but it
  is a boundary rather than an oversight: a filter selecting on an uncertified
  aggregate is a real thing a generator can write.
- **The probe inputs are small and hand-written.** Three certified expressions, one
  Restricted Column, one Reporting Currency, 25 statements. They are Python literals
  in the script by
  [R2](../plan/step-003-validation-feasibility.md#r2--the-spikes-certified-expressions-stay-python-literals--approved-by-amino-2026-08-15),
  so that a spike does not fix the Semantic Layer's file format, and they are probe
  inputs rather than a corpus.
- **Every certified probe converts on Trade Date.** Settlement Date is the other half
  of a Glossary Section C pair and no probe uses it, so nothing here measures whether
  a Metric Definition's choice of date column is visible to the Gate. It is the same
  question as the blind spot in claim 1 and is treated as one question below, not two.
- **The text-matching baseline is our construction of ADR-0003's rejected
  alternative, not the ADR's.** It lower-cases both sides and searches for the column
  name — no tokenising, no comment stripping. A more careful text matcher would strip
  comments and string literals and would score better than 5 disagreements out of 9.
  What it could never do is expand the star, so the *direction* of that finding holds
  for any text matcher and the *count* is specific to this one.
- **Claim 4 compares a thing with a version of itself.** Query, corpus and schema all
  go through one rewrite. That is the right model of a Gate standing in front of the
  other engine — the Semantic Layer's expression is retargeted alongside the query —
  but it makes *25 of 25 unchanged* a weaker statement than it looks, and it is
  exactly the property that produces the blindness to the cast collapse. The stronger
  measurement would be a Gate holding a **hand-written** BigQuery certified
  expression rather than a transpiled one, and that is a Semantic Layer question.
- **Nothing was executed against BigQuery**, as set out under claim 4.
- **The population count in the DEBT-009 answer is construction-dependent.** The
  DuckDB-only names are probed at zero to three arguments, and one name parses at
  none of them, so the population is 50 of 51 and the run says so. A different set of
  arities gives a different denominator. The finding is that the round trip misses
  most of the class; the number is not a property of sqlglot alone.

## The access-control limitation, stated before anything claims otherwise

Claim 2 works. It is worth being exact about what working means here, because this is
the first document in the repository where the Restricted Column check has evidence
behind it, and evidence is what makes an overstatement easy.

> Access Profile enforcement is applied in the application layer, over synthetic
> data. It demonstrates the mechanism; it is not a production access control, and it
> does not protect the Warehouse from being read another way.

Those are
[DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s
own words, quoted rather than rewritten so that the eventual `README.md` has
something to copy instead of compose. That entry's Trigger is *"the first
access-control claim made anywhere a reader will see it"*, and this document is the
internal working record rather than the public face, so it does not fire — but the
measurement makes the sentence more necessary, not less. Application-layer
enforcement protects **exactly one path**: anything reaching the Warehouse another
way bypasses the Gate entirely and the engine hands over every row.

---

## Consequences for Step 004

Six constraints. Each is something the next Step has to obey rather than an
observation about this one, which is why they are here and not only in a review.

### C1 — A Metric Definition publishes a form the Orchestrator pastes

**Because** a certified expression is recognised by its form, and a paraphrase that
returns the identical number is refused.

The Semantic Layer must publish the expression as the text the Orchestrator inserts
verbatim, and Grounding must not leave the model free to re-derive an equivalent one.
That is a constraint on the Metric Definition's file format and on the prompt, before
either exists.

**The alternative was weighed and not taken.** The Gate could instead normalise
commuted operands before comparing, which would make both orderings trace. It is
rejected for the slice: a normalising comparison has to decide which rewrites
preserve meaning, and every rewrite it accepts is one more thing trusted between the
statement a reviewer reads and the statement the Gate judges — in a component
ADR-0003 itself calls *"load-bearing safety infrastructure"*. Publishing a pasteable
form costs nothing and moves the problem to where it is decidable. This is
[R3](#r3--the-six-constraints-bind-step-004s-plan--approved-by-amino-2026-08-20).

### C2 — A Metric Definition carries its Join Path, and its date predicate

**Because** a certified expression pins down the arithmetic and not the rows it is
computed over.

`Traded Notional` converted through the wrong currency column projects identically to
the right one, traces, and is 96.39% wrong. `Join Path` is already a registered
Glossary term with a home in `semantic/joins/`; what this Step adds is that a Metric
Definition must **carry** one and the Gate must **check** it, not only the projection.

**The Trade Date / Settlement Date question is this question, not a second one.** No
probe converts on Settlement Date, so nothing here measures it — but the shape is
identical: two columns on `fct_trade`, a projection that cannot tell them apart, and a
Glossary Section C pair that exists because the choice moves the number. A Metric
Definition that carries its Join Path and not its date predicate has closed one half
of one hole.

On the Ledger as
[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject),
whose Trigger is the Sub-step that builds the Gate: that Sub-step is not done until
the Gate rejects this query and the spike's probe expects a rejection.

### C3 — The two parse-tree rules ship together

**Because** four of the nine Restricted Column shapes compute a certified expression
exactly, so certified-metrics-only allows all four and only the projection rule stops
them.

A Step that builds certified-metrics-only alone and defers the Restricted Column
check has not built half a Gate; it has built a Gate that passes the leak. The two
are one deliverable.

### C4 — The Gate reads the schema at run time

**Because** `SELECT *` is only expandable against the real column list, and that is
the one shape whose restricted name exists nowhere in its own text.

The Gate's interface therefore takes the schema, not just the statement, and reads it
through the Warehouse Adapter — which keeps it on the right side of ADR-0002's seam.
A Gate written as a pure function of SQL text cannot implement claim 2.

### C5 — The rewrites the Gate trusts are named in code, and there are two

**Because** every optimizer rule is one more rewrite trusted to preserve meaning
between the statement a reviewer reads and the statement the Gate judges. sqlglot's
`optimize()` runs fourteen; `qualify` and `merge_subqueries` are enough for every
shape measured here, and `sqlglot.lineage` adds none — it runs `qualify` internally
and nothing else.

The Gate should name its rule set as a constant and print it, as the spike does, so
that widening it is a visible decision rather than a default.

### C6 — Fail closed on parse failure, by a rule rather than by accident

**Because** ADR-0003 already commits to it — *"a parse failure on generated SQL must
be treated as a rejection, never a pass"* — and the spike only achieves it
incidentally: a statement it cannot parse is refused, and a statement whose
projections it never reads is rejected because *allowed* requires at least one metric
expression to have been found. Both are the right outcome for the wrong reason, and
[3.2's review](../reviews/step-003-validation-feasibility.md#sub-step-32--probe-whether-a-generated-query-traces-to-a-certified-metric)
measures exactly that: one of its mutations passes, and *"it passes for a reason no
probe here is written to measure"*.

---

## Rulings

Four questions, all raised by this document and **all four approved by Amino on
2026-08-20**, with Sub-step 3.5. Amino could have accepted every measurement above
and still rejected the conclusion drawn from it, which is why the go/no-go is a Sub-step
of its own rather than a paragraph appended to the Sub-step that produced the last
number.

### R1 — the go on ADR-0003, with its six constraints → **approved by Amino 2026-08-20**

The verdict below, and the six constraints in
[Consequences for Step 004](#consequences-for-step-004) as the price of it. Accepting
the go means ADR-0003 stays `accepted` with a dated status note recording that its
central bet was measured; rejecting it opens an amendment or a supersession, which is
`writing-an-adr` work and would make the Semantic Layer Step wait on it.

**Amino approved the go, and the six constraints with it.** ADR-0003 stays `accepted`
and carries the
[status note this Sub-step wrote](../adr/0003-validation-gate-is-deterministic-code.md#status-note-2026-08-20--the-parse-tree-claim-was-measured-go);
no amendment and no supersession is owed, so the Step that builds the Semantic Layer
waits on nothing here.

### R2 — DEBT-015 is debt rather than an extension → **approved by Amino 2026-08-20**

The classification is a real question and the Ledger's own test is the one that
settles it: *does the trigger fire inside this project's life?*

**The argument for debt, which is what was written.** What is wrong *now* is that a
check claims coverage it does not have — the same shape DEBT-009 was opened about,
in the same file. The trigger fires in Step 004, when `Traded Notional`'s Metric
Definition is written, and it cannot be dodged by writing the expression differently
because the widening cast is proved necessary on every run.

**The argument against.** The *consequence* — a number computed at the wrong width —
can only land on BigQuery, which is [EXT-001](../extension-register.md#ext-001--warehouse-native-security-and-concurrency)'s
migration and outside this project. Read that way it is an extension, and filing it as
debt puts a wish on the Ledger.

**Amino ruled it debt, as written.**
[DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)
stays on the Ledger with the trigger it carries, and the open-debt count it moves is
the real one: what is wrong now is a check claiming coverage it does not have, and
that is inside this project rather than after it.

### R3 — the six constraints bind Step 004's plan → **approved by Amino 2026-08-20**

Specifically that [C1](#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)'s
fork is settled the way it is written — the Semantic Layer publishes a pasteable form
and the Gate does not normalise — since that decision shapes the Metric Definition
file format, and the file format is a seam three Extension Register entries land
against.

**Amino approved both halves.** The six constraints are an input Step 004's plan
starts from rather than a suggestion it may weigh, and C1's fork is settled as
written: the Semantic Layer publishes a pasteable form, and the Gate normalises
nothing beyond the two rewrites [C5](#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
names.

### R4 — DEBT-014 is amended to name the date predicate → **approved by Amino 2026-08-20**

Sub-step 3.2 asked that the Trade Date / Settlement Date gap and the join blind spot
be treated as one question rather than two. Acting on that means the existing entry
grows a dated status note naming the date predicate, rather than a second entry being
opened beside it. Recorded as a ruling because widening an entry's scope after the
fact is a thing to do in the open.

**Amino approved the amendment.**
[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)
covers both halves under one Trigger, and the Sub-step that pays it owes the probe
this Step never wrote: one that converts on Settlement Date, so the date half is
measured rather than argued.

---

## The verdict

**GO on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md).** The
decision was that the Validation Gate is deterministic code operating on the
generated SQL's parse tree via sqlglot, with no Large Language Model participating in
the decision to allow or reject. On the real schema and the real data, that works:

- A certified expression survives every rewrite a generator performs for its own
  reasons — aliasing, a derived table, a common table expression, and a Dimension
  Definition applied to the metric.
- A query that computes revenue inline instead of drawing on the certified
  expression is rejected, and returns a number 32.59% away from the right one.
- A Restricted Column is found in all five shapes that put it in the answer,
  including the one where its name appears nowhere in the query, and is not reported
  in any of the four shapes that do not.
- The alternative the ADR rejected is measurably worse in both directions, not just
  in the one the ADR argued.
- Both verdicts survive retargeting to the engine the full system runs on.

**The go is conditional on the six constraints**, and two of them are sharp enough to
restate here: a Metric Definition must publish a form the Orchestrator pastes rather
than a formula it re-derives, and it must carry its Join Path and its date predicate,
because a certified expression pins down the arithmetic and not the rows. Neither is a
defect in ADR-0003 — both are decisions it left to the Semantic Layer, which is
exactly what a feasibility gate is for finding before the corpus is authored.

**Qualified on [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)'s
retargeting claim, and its decision is unchanged.** That ADR conceded transpilation is
*"good but not total"* and this Step measured where it stops on the SQL Veritas will
actually generate: the verdicts are total, the types are not, and the mitigation it
names — a review comment on any DuckDB-only **function** — is written in the wrong
unit for the one loss found. That is DEBT-015 and a dated status note, not a
re-decision.

**What would make this a no-go, so the bar is on the record.** If a certified
expression had failed to trace through an ordinary subquery or common table
expression, or if a Restricted Column had reached the answer unseen through
`SELECT *`, the parse tree would not have been able to carry the Gate and ADR-0003
would have needed reopening. Neither happened. The one query that is allowed and
should not be is allowed for a reason that names its own fix, and the fix is a
Metric Definition field rather than a different kind of Gate.
