# Step 005 — Build the Validation Gate

- **Status:** **active** — written 2026-08-25 and **approved by Amino the same day**,
  together with all seven questions the plan itself asked, in
  [Questions for Amino](#questions-for-amino).
  Each rewrote its own heading on approval, the way
  [Step 003's rulings](step-003-validation-feasibility.md#rulings) and
  [Step 004's](step-004-semantic-layer.md#questions-for-amino) did, so a link into a
  ruling carries who ruled it and when. Six were approved as written;
  **[R1](#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25) was
  approved and widened**, and it is the only ruling that changed what gets built. The
  widening: the rule that lets a query add a Join Path for a *slice*, which Step 004's
  [R11](step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)
  handed to the Grounding Step, comes back into **5.5** — so `by region` stops being a
  certified axis no query can reach, and R11's first question is answered in this Step
  rather than narrowed by it. **The one thing inside R1 left open for Amino to reject
  on its own — the `Dimension Definition` Glossary amendment — was approved the same
  day**, so nothing in the ruling is provisional.
  **Three more rulings landed after the plan was written and on the same date**:
  [R8](#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25) makes this Step's check a package with one module per rule rather than a
  fifth monolith; [R9](#r9--no-test-framework-in-this-step-and-step-002s-prediction-is-set-aside--approved-by-amino-2026-08-25) settles the test-framework question three Steps have
  deferred to this one; and [R10](#r10--current-state-is-trimmed-in-its-own-commit-between-the-plan-and-51--approved-by-amino-2026-08-25) trims Current State in its own commit before
  5.1. **Ten rulings, all of 2026-08-25**, and with them the plan is final.
  **An eleventh came with the trim commit itself**:
  [R11](#r11--aminos-rulings-on-the-trim--decided-2026-08-26), of 2026-08-26, approves
  how far the trim went and writes the rule it leaves behind into `closing-a-substep`.
  It changes nothing about what gets built.
  **Nothing is built yet**: `veritas/validation/` does not exist, this commit is the
  plan and the three documents around it, and the two commits after it are the Current
  State trim and then 5.1.
- **Goal:** Build `veritas/validation/` — the deterministic, non-Large-Language-Model
  (non-LLM) checks a generated query must pass before it executes — so that a
  statement reaching the Warehouse has been shown, on its parse tree, to compute a
  Certified Metric over that metric's own certified route, to project no Restricted
  Column, to carry its Access Profile's predicate, and to be a bounded read.
- **Moves Current State by:** turning the `Validation Gate` row from `✗ none` to
  working — the **fourth of nine** components, and the second of the two
  [Target State](../design/target-state.md#extension-path-to-the-full-proposal) calls
  *"the durable parts"*. It also pays
  [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject),
  the one open entry whose Trigger this Step fires, and
  [DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type),
  whose Trigger fires earlier than its own text predicted — see
  [Which Debt Ledger triggers this Step fires](#which-debt-ledger-triggers-this-step-fires).

---

## Why this Step

**1. It is the Step already expected, and the expectation was labelled as one.** The
Step 004 plan's scope boundary reads:

> **The Validation Gate.** C3 through C6 bind the Step that builds it, not this one.
> No `veritas/validation/` directory is created, and no Access Profile is declared —
> R3. It is the **expected** Step 005, which is an expectation and not a plan:
> *"Never plan more than one Step ahead."*

This is that plan. Nothing about it was decided in advance except that it was
expected, which is the distinction that sentence exists to keep.

**2. Its design inputs are settled rather than discovered — and they were measured.**
[ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md) decided the Gate is
deterministic code; Step 003 spent five Sub-steps measuring whether that is *possible*
and returned **GO**, with
[six constraints](../design/validation-feasibility.md#consequences-for-step-004). Two
of the six bound Step 004 and are spent. The remaining four —
[C3](../design/validation-feasibility.md#c3--the-two-parse-tree-rules-ship-together),
[C4](../design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time),
[C5](../design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
and [C6](../design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)
— bind this one, and each says *"Binds the Gate Step"* in Step 004's own constraint
table. A Step whose four open constraints all name it is the Step they were written
for.

**3. The corpus it judges against now exists.** The Gate's first rule is *"every
metric expression traces to a Certified Metric"*, which is not answerable without a
certified set. `semantic/` holds all four entry types
([Current State](../design/current-state.md)); the spike had to keep three expressions
as Python literals because none existed. This Step is the first that can read them.

**4. It is key-free, and the Step 004 plan said the key-free half ended with it.**
That plan's fourth reason reads *"It is the last Step that can be done without a
Large Language Model API key. Everything after it — Retrieval's embeddings, the
Orchestrator, Evaluation — needs one."* The list is right and the sentence around it
was loose: the Validation Gate needs no key either, and ADR-0003 is the reason —
*"No LLM participates in the decision to allow or reject a query."* So the key-free
half of the project ends **after** this Step rather than before it. Recorded here
rather than corrected there, because a committed plan is a record of what was
believed when it was written.

**5. It is the last Step that can be built against hand-written statements.**
Everything the Gate judges arrives from the Orchestrator, which does not exist. That
is not a problem to work around — it is why the Gate is testable at all. The spike
proved every claim against 25 hand-written probe statements, and this Step inherits
that method: a Gate is a judge, and a judge is tested by putting cases in front of
it, not by waiting for a defendant.

---

## What the four remaining constraints require, concretely

| Constraint | What it means here |
|---|---|
| [C3 — the two parse-tree rules ship together](../design/validation-feasibility.md#c3--the-two-parse-tree-rules-ship-together) | **Binds.** *"A Step that builds certified-metrics-only alone and defers the Restricted Column check has not built half a Gate; it has built a Gate that passes the leak."* Sub-steps 5.2 and 5.3 are both in this Step and neither may be deferred out of it — see [R4](#r4--c3-is-satisfied-at-the-step-not-the-sub-step--approved-by-amino-2026-08-25) |
| [C4 — the Gate reads the schema at run time](../design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time) | **Binds.** The Gate's interface takes the schema, not just the statement, and reads it *"through the Warehouse Adapter — which keeps it on the right side of ADR-0002's seam"*. `SELECT *` is only expandable against the real column list |
| [C5 — the trusted rewrites are named in code](../design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two) | **Binds.** `qualify` and `merge_subqueries`, as a named constant the Gate prints, *"so that widening it is a visible decision rather than a default"*. sqlglot's `optimize()` runs fourteen and the Gate runs two |
| [C6 — fail closed by a rule](../design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident) | **Binds, and is the one the spike failed.** The spike fails closed *"incidentally"*, and 3.2's review measured exactly that: one mutation passes, and *"it passes for a reason no probe here is written to measure"*. The Gate needs an explicit rejection whose reason names parse failure |

[C1](../design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)
and [C2](../design/validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate)
were spent in Step 004 and are what makes this Step cheap: the corpus already
publishes a pasteable expression and already carries `join_paths` and `date_column`,
so the Gate reads fields rather than inferring intent.

---

## What the Gate must decide

The [Target State's flow](../design/target-state.md#flow) names four things the
`VALIDATE` step checks. They are the Step's Sub-steps, in the order a statement meets
them:

```
generated SQL ─┬─► is it a statement we will run at all?        ← 5.1  (C6, read-only, bounded)
               ├─► does every metric expression trace?          ← 5.2  (C1, C5)
               ├─► does a Restricted Column reach the answer?   ← 5.3  (C3, C4)
               ├─► is it computed over the metric's own route?  ← 5.4  (C2 — pays DEBT-014)
               └─► is the Access Profile's predicate present?   ← 5.5  (+ the slice route — R1)
```

**The order is not arbitrary — it is what each rule needs to reach a verdict.** 5.1
needs the statement's parse tree and nothing else; 5.2 needs the corpus **and** the live
schema through the adapter; 5.3, 5.4 and 5.5 need that same pair, plus the Access Profile
the caller hands in. Each rule therefore runs before every rule that needs more than it
does.

**Corrected 2026-08-27** ([R13](#r13--aminos-rulings-on-the-52-review--decided-2026-08-27)).
This sentence read *"5.2 needs the corpus as well; 5.3, 5.4 and 5.5 need the live schema
through the adapter on top of that"* — the schema one Sub-step later than it actually
arrived. `qualify` cannot attach a column to the table it came from without a catalogue,
so the rule that traces an expression needs both from its first line.
[C4](../design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time) had
already said the Gate's interface *"takes the schema, not just the statement"*, and
**nothing about the rule order changes**: the tracing rule still runs after every rule
that needs less than it does, which is the property this section is about. What was
wrong was the prediction of *when* the second dependency lands, and a route sentence
that has quietly stopped being true is worse than one that was never written.

**The reason to order them that way is not speed.** The first of
[the six shapes below](#the-six-shapes-read-only-has-to-cover) — a statement that drops
a table — is refusable from the parse tree alone, so a Gate that loads twenty-seven
Semantic Entries before refusing it has made a rule that needs nothing depend on
something — and anything a rule depends on is something that can fail underneath it. Ordered as above,
the read-only rule still returns the right verdict on a day the corpus will not load or
the Warehouse will not open. Ordered the other way, it returns an error instead of a
rejection, and an error is not a rejection: a caller can act on *"this statement writes
to the Warehouse"* and cannot act on *"the Gate did not get far enough to say."*
Cheapest-first is what this independence looks like from outside; it is the consequence,
not the goal.

**Every rule ends in a rejection with a named reason**, because ADR-0003 sold the
determinism partly on that: an LLM validator *"cannot produce the stable taxonomy of
rejection reasons that 'Validation-Gate rejections by reason' needs to be a real
chart."* The taxonomy is a data contract Observability charts and the App renders, so
it is drawn as a seam in 5.1 rather than accumulated as string literals — see
[R3](#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25).

---

## How the five Sub-steps divide the work

```
veritas/validation/   ← 5.1  the seam: the outcome, the reason taxonomy, the bounded read
veritas/validation/   ← 5.2  trace every metric expression to a Certified Metric
veritas/validation/   ← 5.3  the Access Profile, and the Restricted Column it forbids
veritas/validation/   ← 5.4  pay DEBT-014 — the route and the date predicate
semantic/  + the Gate  ← 5.5  the access predicate, the slice route, and the routes both read
```

Every commit subject is conjunction-free, and every adjacent pair passes
`planning-a-step`'s real test — **Amino could reasonably approve one and reject the
next**:

| Pair | The independent failure |
|---|---|
| 5.1 / 5.2 | 5.1 fixes the *shape* of a verdict — the outcome object and the reason taxonomy — using only rules that need no corpus; 5.2 adds the first rule that reads one. Independent in **both** directions, which is what the test asks. Send 5.1's taxonomy back and 5.2's work survives it, because *"does this expression trace to a Certified Metric"* is the same question however the verdict that carries it is spelled. Send 5.2 back and 5.1 survives that, because a Gate that refuses a write and an unparseable string is already refusing things, on rules whose evidence is complete without a corpus |
| 5.2 / 5.3 | Two different questions about one statement: *how was this number derived* and *who may see this column*. C3 binds them to the same **Step**, not the same commit — [R4](#r4--c3-is-satisfied-at-the-step-not-the-sub-step--approved-by-amino-2026-08-25) |
| 5.3 / 5.4 | 5.3 judges the projection; 5.4 judges the rows underneath it. `notional through the wrong currency` has a clean projection and the wrong number, which is the whole reason [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject) exists |
| 5.4 / 5.5 | 5.5 is the only Sub-step that changes `semantic/` — five new Join Paths, and a `routes` field on five Dimension Definitions. The four rules above it read fields it does not touch, so rejecting the corpus change leaves them standing; and 5.4's route rule is written to take its permitted joins from a list, so 5.5 lengthens that list rather than rewriting the rule |

**A split point, pre-agreed.** Five Sub-steps is `planning-a-step`'s ceiling, so there
is no room for review-driven growth. If this Step grows, the Sub-step to leave is
**5.5** — see [R5](#r5--55-is-a-pre-agreed-split-point--approved-by-amino-2026-08-25). The pattern
is [Step 003's R5](step-003-validation-feasibility.md#r5--34-is-a-pre-agreed-split-point--approved-by-amino-2026-08-15)
and [Step 004's](step-004-semantic-layer.md#r5--45-is-a-pre-agreed-split-point--approved-by-amino-2026-08-21),
neither of which fired.

**5.5 is now the largest Sub-step, and R1's widening is why.** Before the widening it
was five files and one narrow rule; it is now five files, a new field on five more, a
loader change, a semantic-layer check, and a Gate rule with two callers. If the Step
grows anywhere it grows here, which is exactly the case R5 was written for.

**5.3 is the second largest and the one most likely to grow unexpectedly.** It
introduces a new concept (the Access Profile), a new rule, and the run-time schema read
C4 requires. If it splits, it splits into the Access Profile as a declared thing and the
rule that reads it — which takes the Step to six, and six is two Steps, so that split
fires 5.5's.

---

## Questions for Amino

**Eleven: ten ruled by Amino on 2026-08-25, and one on 2026-08-26.** The ten arrived
in two batches and the distinction is worth keeping, because one batch is the plan
asking and the other is the plan being corrected.

**The seven the plan asked.** Six are here; the seventh
([R7](#r7--the-bounded-read-uses-the-engines-estimate-if-the-adapter-can-reach-it--approved-by-amino-2026-08-25))
sits beside the Sub-step it is about. Six were approved as written. **[R1](#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)
was approved and widened**, and it is the only one that changed what gets built: the
slice rule Step 004 handed to Grounding comes back into 5.5.

**The three that came after it**, out of a question Amino raised once the seven were
settled — why recent sessions have been context-heavy, and whether a test framework
would help. [R8](#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25) and [R9](#r9--no-test-framework-in-this-step-and-step-002s-prediction-is-set-aside--approved-by-amino-2026-08-25) are that question's two halves: the win is
decomposition's and not pytest's, so the check is decomposed and pytest is declined.
[R10](#r10--current-state-is-trimmed-in-its-own-commit-between-the-plan-and-51--approved-by-amino-2026-08-25) is the larger half of the same answer, and it is about a document rather
than about code. None of the three changes what the Gate does; they change how it is
checked, and what a session reads before it starts.

**The eleventh is R10's own consequence.** R10 said the trim commit would put one
question up and be ruled on there;
[R11](#r11--aminos-rulings-on-the-trim--decided-2026-08-26) is that ruling, plus one
on how far the trim went, and it lands inside the trim commit rather than after it.

### R1 — The Access Profile's predicate and the slice rule ship together, in this Step → **approved and widened by Amino 2026-08-25**

**The ruling, and it is wider than what was asked.** The proposal offered to take the
half of the problem that was not Grounding's. Amino declined the narrow half:

> build it in a way that solves the current problem and answers and closes the
> step-004's R11 first question at the same time using the best practice design. it's
> ok to cover this specific part's grounding half here. i think the 5.5 substep will
> change accordingly.

So this Step takes **both** halves R11 named — the routes *and* the rule that lets a
query add a Join Path for a slice — and
[5.5](#55--the-gate-requires-the-access-profiles-predicate-and-admits-a-slice-route)
grows accordingly. What follows is the problem as it was put, then the design the
ruling asked for.

**The problem.** The Access Profile's predicate is on `dim_client.client_region` —
the only region column in the Warehouse. **No Join Path reaches `dim_client`**, which
is the first of the three questions
[R11](step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)
handed to the Grounding Step on 2026-08-25:

> Nothing under `semantic/joins/` reaches `dim_client`, so the axis the Glossary's own
> worked example uses cannot yet be applied. What closes it is two Join Path files —
> `trade_to_account` and `account_to_client` — **plus the rule that lets a query add a
> Join Path for a *slice* rather than for an expression**, and it is that second half
> that makes it Grounding's work rather than authoring work.

It collides with 5.4. Once the Gate checks that a query's joins are the metric's own
certified `join_paths`, a query carrying the access join carries a join the metric does
not name — so the route rule rejects what the access rule requires. Built naively, the
Gate rejects every query there is.

**The design: one rule about joins, with three sources of permission.** 5.4's route
rule is not *"the joins are the metric's `join_paths`"*. It is *"every join in the
statement is one some entry names for this statement"*, and exactly three things may
name one:

| Source | What it permits | Where it is declared |
|---|---|---|
| The metric's own route | The joins the **expression** needs to compute the number | `join_paths` on the Metric Definition — C2, shipped in Step 004 |
| A slice route | The joins a **`GROUP BY` on a certified axis** needs to reach that axis's columns | a new `routes` field on the Dimension Definition — 5.5 |
| The access route | The join the **Access Profile's predicate** needs to reach `dim_client.client_region` | nothing new: it is the `by region` axis's own route, read from the same field |

Anything else is a rejection. The Gate never searches the corpus for a chain of hops
that happens to arrive somewhere — see *the alternatives*, below, for why that matters
more than it looks.

**`routes` maps the metric's `from_table` to the Join Paths that reach the axis.** An
axis is not reachable from everywhere, and which route reaches it depends on where the
query starts, so one list would be wrong:

```yaml
# semantic/dimensions/by_region.yaml
routes:
  fct_trade:                [trade_to_account, account_to_client]
  fct_position_snapshot:    [position_snapshot_to_account, account_to_client]
  fct_balance_snapshot:     [balance_snapshot_to_account, account_to_client]
  fct_accounting_movement:  [accounting_movement_to_account, account_to_client]
```

Three consequences fall out of the shape, and each is a thing the Gate can now say:

- **An empty list is a real answer.** `by trade date` declares `fct_trade: []` — the
  column is already on the table the query starts from, so slicing by it needs no join
  at all. The field is not *"the joins to add"*; it is *"what reaching this axis from
  there costs"*, and sometimes that is nothing.
- **An absent key is also a real answer**, and it is the one worth having. `by
  instrument type` names `fct_trade` and `fct_position_snapshot` and nothing else,
  because a Cash Balance has no Instrument. The Gate rejects *"Cash Balance by
  instrument type"* by pointing at a missing key, rather than by joining two tables
  that share no meaning.
- **It makes R11's fourth ruling enforceable rather than argued.** That ruling defends
  three date axes where the Glossary had one, on the grounds that *"an axis named
  `fct_trade.trade_date` applied to a Snapshot metric is a certified axis whose route
  never reaches the column."* Under `routes`, that sentence stops being an argument in
  a plan and becomes an absent key the Gate reads.

**The Access Profile names the axis, not the column.** `by region` already registers
the column, the grain and the three buckets — `EU`, `UK`, `APAC`. A profile that
carried `dim_client.client_region` and its own permitted-region string would be a
second registration of both, which is the synonym Non-Negotiable 1 exists to prevent.
So an Access Profile carries a **role**, a **permitted value of the `by region` axis**,
and the **Restricted Columns** that role may not see — which is the Glossary row's own
*"role and permitted region"*, read literally. The Gate resolves the predicate's column
and its route from the axis entry, and a profile naming a region the axis does not
certify is refused where it is loaded rather than where it is used.

**Two alternatives, and why neither is the best-practice design the ruling asked for.**

1. **Let the Gate search the join graph.** Load `semantic/joins/`, find a chain from
   the metric's `from_table` to the table holding the axis column, allow it if every
   hop is certified. No corpus change, no new field. It is rejected for two reasons and
   the second is the serious one. First, *"a chain reaching the table"* is not unique:
   two certified routes already reach `fct_fx_rate` from `fct_trade`, and choosing
   between them wrongly is precisely
   [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)
   — a search that picks the shortest would be a Gate deciding a Section C question by
   hop count. Second, **a chain of certified hops is not itself certified**: a
   one-to-many hop multiplies the fact rows underneath an aggregate and moves the
   number, and nothing in a Join Path says which kind it is. C2 exists because *"the
   Gate reads fields rather than inferring intent"*; this is the same question one
   table further out, and it deserves the same answer.
2. **Put the routes on the Metric Definition.** Each metric lists the axes it admits
   and the route to each. It restates one fact once per metric–axis pair, so a sixth
   axis edits nine files instead of one, and it splits *"how do I reach `by region`"*
   across nine places that can disagree. The reachability is a property of the axis and
   the fact table, not of the metric, and it belongs where it is a property.

**Five new Join Path files, unchanged from the proposal**: `trade_to_account`,
`position_snapshot_to_account`, `balance_snapshot_to_account`,
`accounting_movement_to_account`, and `account_to_client` — one per distinct
`from_table` across the nine Metric Definitions, plus the shared last hop. Widening the
ruling does not widen this list, because `by instrument type`'s two routes
(`trade_to_instrument`, `position_snapshot_to_instrument`) already exist and the three
date axes need none.

**Five and not R11's two**, because R11 was counting the route from `fct_trade` and
four of the nine metrics start elsewhere: three at `fct_position_snapshot`, one at
`fct_balance_snapshot`, one at `fct_accounting_movement`. A Gate that can only enforce
the Access Profile on trade-side metrics enforces it on four questions out of nine,
which is the kind of partial control DEBT-008 is already about.

**What the widening costs, stated plainly.**

- **A field is added to a Semantic Entry kind Step 004 shipped and Amino approved.**
  Five Dimension Definition files gain `routes`, `veritas/semantic/loader.py` gains the
  field, and `check_semantic_layer.py` gains a check that each named Join Path exists
  and that the chain actually connects the `from_table` key to the table holding the
  axis's columns. Under
  [R6 of Step 004](step-004-semantic-layer.md#r6--no-new-adr-for-the-file-format--approved-by-amino-2026-08-21)
  the file format is plan-and-review territory rather than ADR territory, and a field
  added inside a decided format does not reopen that.
- **The `Dimension Definition` Glossary row becomes incomplete — and the amendment
  that fixes it is approved.** The row says an axis *"Names the column, its grain, and
  its allowed values"*, and after 5.5 an axis also names where it can be reached from.
  That row is `agreed`, so the amendment was put up as **the one thing inside this
  ruling still worth rejecting on its own**; Amino **approved it on 2026-08-25**,
  alongside R8, R9 and R10. It lands in 5.5 with the field, which is the same order
  R11's amendment landed in — the row and the corpus change in one commit, because a
  row that describes a field nothing has yet is the kind of intent Non-Negotiable 3
  keeps out of the state documents.
  **What the amendment may say, and what it may not.** It adds that an axis declares
  the routes that reach it, and points at `semantic/dimensions/` for them. It does
  **not** list the routes in the cell.
  [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell)
  is open for putting the five certified axes inside one table cell read by a prose
  parse, and listing four `from_table` keys per axis beside them would be that same
  shortcut, four times larger, with its Ledger entry still open — which is the reason
  [R3](#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)
  already gives for keeping the reason taxonomy in code. The Glossary gains the
  **definition**; the corpus keeps the **data**, where `check_semantic_layer.py` reads
  it.
- **5.5 becomes the largest Sub-step in the Step**, which is why
  [R5](#r5--55-is-a-pre-agreed-split-point--approved-by-amino-2026-08-25)'s split point
  now matters more than when it was written.

**What still does not close.** R11's other two questions stay with Grounding untouched:
whether `by settlement date` becomes an axis, and whether check 17's foreclosure admits
an axis whose buckets ingestion minted rather than the Glossary registering. Both ask
what the **corpus may certify**, and this ruling certifies no new axis — it gives an
already-certified one a route. And
[DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
is not paid: one role, over synthetic data, enforced in the application layer.

### R2 — The spike imports the Gate rather than keeping its own tracer → **approved by Amino 2026-08-25**

**Approved, with a rule attached that is wider than the question.** Amino: *"exactly
right. the logic that belongs to veritas must be only accessible from veritas once its
containing component is built."* So the direction is not a preference about duplication
— it is a one-way door. A `.claude/scripts/` check may hold logic that belongs to a
component **only while that component does not exist**; the moment it does, the logic
moves in and the check imports it back. That names the rule 4.3 followed without
stating it, and it decides the same question in advance for every check written after
this one.

`check_validation_feasibility.py` contains a tracer, a projection walker and a
restricted-column detector. The Gate contains the same three. Two copies of one rule
answer questions about the copy.

**The precedent is Sub-step 4.3**, which moved `retarget` and `round_trip_rewrites`
out of the spike into `check_warehouse.py` and had the spike import them back — so
that, in Current State's words, *"the dated measurement and the check that runs on
every commit are one trip."* The proposal is the same move in the same direction: the
Gate owns the logic, the spike imports it, and the spike's 25 probe statements and
their declared verdicts stay exactly where they are.

**What this does not touch is
[R4 of Step 004](step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)**,
which pins the spike's three certified expressions as Python literals so *"the dated
measurement stays the measurement that was taken"*. That ruling is about the **corpus**
the spike judges against, not about who owns the tracer. The literals stay literals,
`check_semantic_layer.py` goes on asserting they match `semantic/metrics/` character
for character, and the Gate reads the corpus while the spike goes on reading its pins.

**The cost, stated:** the spike stops being self-contained. Reading it will require
reading `veritas/validation/` too. 4.3 accepted the same cost for the same reason.

### R3 — `Validation Gate outcome` and `Rejection Reason` get Glossary rows → **approved by Amino 2026-08-25**

🆕 **TERM PROPOSAL**, two of them, both about to become code identifiers.

- **`Validation Gate outcome`** — the verdict object: allowed or rejected, with the
  reasons and the rules that produced it. The phrase is already used in three agreed
  Glossary rows — `Grounded Answer`, `App` and `Observability` all name it — and has
  no row of its own, so it is a compound nobody has had to define. It is about to be a
  class in `veritas/validation/`, which is when Non-Negotiable 1 applies.
- **`Rejection Reason`** — one member of the stable taxonomy a rejected outcome
  carries. ADR-0003 sells determinism partly on this taxonomy existing, and the
  [Target State](../design/target-state.md#zoomcamp-criteria-map)'s Monitoring row
  charts *"Validation-Gate rejections by reason"*. Without a registered name, the same
  concept becomes a reason code in the Gate, a chart label in Grafana and a string in
  the App — three names for one thing, which the Glossary's own rule calls a bug.

**The vocabulary of reasons is registered in code, not in the Glossary cell.**
[DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell)
was opened four days ago for putting the five certified axes inside one table cell read
by a prose parse. Repeating that here would be repeating a shortcut with its Ledger
entry still open. The `Rejection Reason` row names the concept and points at
`veritas/validation/`; the members live where the Gate can enumerate them.

### R4 — C3 is satisfied at the Step, not the Sub-step → **approved by Amino 2026-08-25**

C3 says the two parse-tree rules *"are one deliverable"* and that a Step shipping one
without the other *"has built a Gate that passes the leak"*. This plan reads that as a
constraint on the **Step**: 5.2 and 5.3 are both inside it, and neither may be deferred
out of it by a review.

**Why the Sub-step boundary is safe here.** The leak C3 describes is a query that
executes. Nothing executes a query through the Gate until the Orchestrator exists, two
components away — so between 5.2 and 5.3 there is no path a Restricted Column can
travel. The commit in between is a Gate nobody has wired to anything.

**Why raise it rather than assume it.** The alternative reading — one Sub-step
containing both rules — is available and is not absurd. It would make the largest
commit in this project so far, and it would remove the reviewer's ability to reject the
Restricted Column rule without also rejecting the tracer. If Amino prefers the stricter
reading, 5.2 and 5.3 merge and the Step has four Sub-steps.

### R5 — 5.5 is a pre-agreed split point → **approved by Amino 2026-08-25**

Named before the Step starts rather than at review, *"when it is already too late to
have cost nothing."* If this Step grows, **5.5 leaves**: the Gate is coherent without
it — four rules that each reject something the spike measured — and 5.5 is the only
Sub-step that changes `semantic/`, so the corpus question travels intact rather than
being split.

If it fires, two things follow rather than one. The Access Profile's predicate becomes
Step 006's first Sub-step, **and** a Ledger entry is opened in the same commit, with
its Trigger set to that Sub-step and its cost written as the half-enforcement
[R1](#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)
describes. A split point that leaves no entry behind is how a deferral becomes
invisible.

### R6 — No new ADR for the Gate → **approved by Amino 2026-08-25**

[ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md) already decides the
expensive thing — deterministic code over a parse tree, no LLM in the decision — and
Step 003 already measured it and recorded the go. The Access Profile's home is decided
too: the Glossary registers it as living in `veritas/validation/`, and
[R3 of Step 004](step-004-semantic-layer.md#r3--restricted-columns-are-declared-in-the-access-profile-not-in-a-metric-definition--approved-by-amino-2026-08-21)
already ruled that Restricted Columns are declared there rather than on a Metric
Definition.

What is left is implementation inside decisions already taken, and the pattern is
[R6 of Step 004](step-004-semantic-layer.md#r6--no-new-adr-for-the-file-format--approved-by-amino-2026-08-21):
the plan's design sections and the Step Review are the record. **One thing would
change this**: if [R7](#r7--the-bounded-read-uses-the-engines-estimate-if-the-adapter-can-reach-it--approved-by-amino-2026-08-25)
resolves toward an engine estimate, the Gate acquires a dependency on a DuckDB-specific
plan format, and whether that belongs behind ADR-0002's adapter is an ADR-sized
question. The plan's answer is that it does belong there and the adapter absorbs it,
which is what ADR-0002 is for — but it is named here so it is not discovered in code.

### R8 — The Step's check is a package with one module per rule, from 5.1 → **approved by Amino 2026-08-25**

Raised after the seven above were settled, and ruled the same day: *"modularize
`check_validation_gate` as proposed, starting from 5.1."*

**What changes, and what does not.** The verification sections below said *"a new
`.claude/scripts/check_validation_gate.py`, grown one rule per Sub-step the way
`check_semantic_layer.py` and the spike both were."* The growth method stays — one
rule per Sub-step, and the Sub-step that adds a rule is the Sub-step that adds its
probes. The **container** changes: not a file that grows five times, but a package
whose modules are added one per Sub-step.

```
.claude/scripts/check_validation_gate/
├── __main__.py     the runner: the rule list, the report, the exit code
├── probes.py       shared probe machinery — the adapter, the Snapshot-calendar dates,
│                   and the declared-verdict record every rule's probes are written in
├── read_only.py    ← 5.1
├── traces.py       ← 5.2
├── restricted.py   ← 5.3
├── route.py        ← 5.4
└── access.py       ← 5.5
```

That layout is the **shape**, not the decision; 5.1 fixes the names and the Step
Review records what they became. What the ruling fixes is that there is a runner, that
a rule is a module, and that the modules arrive one per Sub-step.

**The command stays one command**, which is the part that must not change, because
Non-Negotiable 4 is about a reader being able to re-run what a review quotes:

```bash
uv run python .claude/scripts/check_validation_gate/
```

Python runs a directory that holds a `__main__.py`, so the package is invoked the way
the flat scripts beside it are and reads the same in a review.

**Why now.** The three checks grown by the method this one inherits are each well over
a thousand lines — `wc -l .claude/scripts/*.py` prints where they have got to — and
none of them was ever *decided* to be a monolith; each became one by having a rule
added five or six times. This is a **seam** in CLAUDE.md's sense: the shape everything
later hangs off. Splitting a package that does not exist costs nothing. Splitting a
file after five Sub-steps have written into it fails the test CLAUDE.md sets for debt
— *"can this shortcut be repaid without moving a name, an interface, or the flow?"* —
because by then the rules share helpers, ordering and a single report. So the monolith
is not a shortcut that may be taken here; it is a line that gets drawn now.

**It costs nothing in the checks that read the scripts directory.** `check_language.py`,
`check_warehouse.py` and `verify_framework.py` all reach `.claude/scripts/` with
`rglob("*.py")`, so every module in the package is scanned for abbreviations, for the
`duckdb` import seam and for rotted documentation links exactly as a flat file is —
verified by reading the three scanners on 2026-08-25, and by 5.1's run.

**What it costs.** Five files where there was one, and a reader who wants the order of
the rules opens the runner instead of scrolling. That is the trade `veritas/warehouse/`
already made: the order becomes **one list in one place** rather than a reading order,
which is what lets 5.1's ordering argument — *"each rule runs before every rule that
needs more than it does"* — be a thing the code states rather than a thing the file
happens to be.

**What it does not do.** It does not convert `check_semantic_layer.py`,
`check_validation_feasibility.py` or `check_warehouse.py`. They work, they run on
every commit, and rewriting them moves no seam and no name — a scope boundary rather
than debt, and not this Step's work.
[R2](#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
does touch the spike, and it is a different operation: it removes a **second copy of
one rule**, not a monolith.

### R9 — No test framework in this Step, and Step 002's prediction is set aside → **approved by Amino 2026-08-25**

Amino: *"no pytests is approved."*

This is the fourth Step in a row to decline pytest and **the first where declining
contradicts something written down**.
[R5 of Step 002](step-002-warehouse-and-ingestion.md#r5--evidence-from-check-scripts-no-pytest-this-step--approved)
reads: *"pytest arrives with the first component that has branching logic worth
unit-testing, which is the Validation Gate rather than the warehouse."* This is that
component. Steps 003 and 004 each restated the deferral as *"a proposal rather than an
inherited ruling"* and each was right to, because R5 was scoped to Step 002 — but each
was also deferring toward a Step that R5 had named, and that Step is this one. So the
prediction is being **set aside rather than quietly outgrown**, and the argument is
here rather than in a scope-boundary bullet.

**What pytest would buy, and where that win actually comes from.** The concrete pain
today is real: adding a rule means opening a file of well over a thousand lines. But
that is decomposition's win, not a runner's — [R8](#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25) takes it, with no dependency
added and nothing installed.

**What it would cost here, specifically.**

- **The evidence model is printed output, not pass/fail.** Non-Negotiable 4 asks for a
  committed command whose output a review can quote, and the reviews do quote
  **numbers**: the spike prints the currency margin on every run, and
  [5.4](#54--pay-debt-014-the-gate-checks-the-route-and-the-date-predicate) is required
  to print two numbers side by side *"before the rejection is claimed to matter"*. A
  test runner reports which assertions held. Getting the numbers back out of one means
  running it in a mode that does not capture output — fighting the tool for what a
  script does by default.
- **Two ways to run the evidence is more surface, not less.** A rule could then live in
  either place, and the question *"where is this checked"* stops having one answer.
- **It is a sixth Sub-step.** `planning-a-step` reads six as two Steps, so it fires
  [R5](#r5--55-is-a-pre-agreed-split-point--approved-by-amino-2026-08-25)'s split point — which means introducing pytest here is paid for with
  **5.5**, the Access Profile's enforcement and `by region`'s route.

**What declining costs, stated rather than waved past.** No fixtures, no
parametrization, no assertion introspection: each check writes its own probe loop, its
own comparison and its own report, and that duplication now spans five scripts. R8
bounds it for this one and for nothing else.

**Neither debt nor extension, and the test was applied rather than skipped.** It is not
debt: the current code is *right for this scope*, and there is no Trigger that fires
inside this project's life — a check script that exits non-zero is the evidence
Non-Negotiable 4 asks for, not a cheap stand-in for it. It is not an extension either:
a test runner is not something the full proposal needs that this slice lacks. So it is
a **scope boundary**, and it is recorded here rather than on either list.

**When it should be revisited** — a prediction, which is what R5 turned out to be, and
labelled as one: the first component whose behaviour is not *"a rule judged over a
corpus of probe cases"*. The Orchestrator's retry and fallback paths and Evaluation's
scoring are the two candidates. Neither is in this Step, and neither is planned.

### R10 — Current State is trimmed in its own commit, between the plan and 5.1 → **approved by Amino 2026-08-25**

Amino: *"trim the current state before starting 5.1 but after the plan commit."*

**The problem it fixes is a contract, not a preference.**
[`current-state.md`](../design/current-state.md) is the session entry point — CLAUDE.md's
resumption contract says *"Read it first, every session"* — so every session pays its
full length before any work starts. It gains a passage every Sub-step and has lost
none since Step 000. `wc -c .claude/docs/design/current-state.md` prints where that
has got to.

**And most of what it has gained is not what the file is for.** Non-Negotiable 3:
*"It must never describe intent, only reality."* Reality now is a short document. What
has accumulated beside it is *how we got here*, told at the length it was told at the
time — and each of those passages already exists, dated and with its command, in the
review that produced it. A narrative kept in two places is the failure the Glossary
rule is about, one level up: two copies that can disagree, and the shorter one is read
more often.

**What the trim is.** It removes narrative a dated review already holds, and keeps the
component table, the Resume-here block, the open questions, the commit-hash list, and a
bounded *how we got here*. It removes **no fact recorded only there**: anything found
in Current State and nowhere else is either moved into the review it belongs to or
kept. That is the one hard rule of the commit, and it is what makes the diff safe to
be large.

**Why its own commit.** A diff that deletes several hundred lines of history and a diff
that builds a Gate are two different things to review, and folding the first into the
second is how a fact goes missing where nobody is looking. It is **not a Sub-step** —
it builds nothing and closes nothing — so it is a documentation commit, like the
planning commit before it. The order is: this plan, then the trim, then 5.1, so that
every session of this Step reads the shortened file rather than lengthening the long
one.

**One question the trim commit has to answer**, flagged here so it is not discovered
there: whether the rule it leaves behind — *a Sub-step adds to Current State what is
true now, and the story of how it got there stays in the review* — should be written
into `closing-a-substep`, which is the skill that refreshes the file. If it is not
written down, the file re-accumulates and the trim is a one-off rather than a fix.
That is a change to the framework rather than to this Step, so the trim commit puts it
up and Amino rules on it there. It was ruled in
[R11](#r11--aminos-rulings-on-the-trim--decided-2026-08-26).

### R11 — Amino's rulings on the trim → **decided 2026-08-26**

Two rulings, on the entry the trim commit wrote —
[The Current State trim](../reviews/step-005-validation-gate.md#the-current-state-trim--not-a-sub-step).
Neither changes what the Gate does or how it is built; the first settles how far the
trim went, and the second is the framework change [R10](#r10--current-state-is-trimmed-in-its-own-commit-between-the-plan-and-51--approved-by-amino-2026-08-25)
said this commit would put up. They land **in the trim commit itself** rather than
after it, because the ruling arrived before the commit did.

**1. The component table's Notes were trimmed, and that reading of R10 stands.**
Amino: *"your call about the component table is approved."* The sceptical item that
asked — the trim kept the table and everything it says about what exists **now**,
while the per-Sub-step chronology inside its cells went the way of the rest of the
narrative — is the first item in
[the review entry's sceptical list](../reviews/step-005-validation-gate.md#the-current-state-trim--not-a-sub-step).
So R10's *"keeps the component table"* means the table as a description, not the
table verbatim, and the alternative reading the entry offered — restore the Notes
cells from `git show aa42205:.claude/docs/design/current-state.md` — is declined.

**2. The rule goes into `closing-a-substep`.** Amino: *"the rule this trim leaves
behind should be written into the `closing-a-substep` skill."* It is now step 5 of
that skill, beside *"reality only"*, which was already there and was already true
every time the file grew — the reason the review entry gave for sharpening the words
rather than assuming they covered it. The addition says where the narrative goes
instead: a passage about what **this** Sub-step did is a defect in Current State even
when accurate, because step 6's review already holds it, dated and with its command.
A second row joins the skill's rationalization table for the excuse that puts it back.

**What this makes true that was not.** The trim was a repair; the rule is what stops
the repeat. Without it the file re-accumulates and the trim is a one-off — R10's own
argument for asking, and what the evidence showed: the file gained a passage every
Sub-step across four Steps and lost none, which is the absence of a rule rather than
a lapse by any one Sub-step.

---

## Sub-steps

### 5.1 — The Validation Gate refuses anything that is not a bounded read

The seam, drawn thin: the verdict, the reason taxonomy, and the two rules that need
neither the corpus nor a Certified Metric.

- `veritas/validation/` — the directory the Glossary already registers as home to
  `Validation Gate`, `Access Profile` and `Restricted Column`. Laid out like
  `veritas/warehouse/` and `veritas/semantic/`: an `__init__.py` that re-exports, and
  the module behind it.
- **The check is a package too**, under [R8](#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25):
  `.claude/scripts/check_validation_gate/`, a runner plus one module per rule, with
  this Sub-step's module the first of five. The Gate has five rules and so does the
  check; they are added in the same order, and neither becomes a file that grew.
- **The `Validation Gate outcome`** ([R3](#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)):
  a frozen object carrying allowed-or-rejected, the `Rejection Reason` members that
  fired, and the rule set the decision was taken under. It is what a Grounded Answer
  will carry and what Observability will chart, so it is a data contract before it is
  a return value.
- **C6, by a rule.** A statement sqlglot cannot parse is rejected with a reason that
  names parse failure — not refused as a side effect of finding no projections. This
  is the constraint the spike is measured to miss.
- **C5, as a printed constant.** `qualify` and `merge_subqueries`, named in one place,
  printed by the check, and reported on the outcome.
- **Read-only.** Anything that is not a single `SELECT` is rejected — see
  [the shapes below](#the-six-shapes-read-only-has-to-cover).
- **Bounded**, per [R7](#r7--the-bounded-read-uses-the-engines-estimate-if-the-adapter-can-reach-it--approved-by-amino-2026-08-25).
- **Pays [DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)**,
  whose Trigger this Sub-step fires — see
  [the trigger table](#which-debt-ledger-triggers-this-step-fires). `WarehouseError` is
  added to `veritas/warehouse/adapter.py`, raised from the engine's exception at the
  boundary that owns the engine, and `check_semantic_layer.py`'s two `except Exception`
  lines narrow to it. That is the entry's own prescription, verbatim: *"One class and
  one `raise … from` inside `veritas/warehouse/adapter.py`."*

#### The six shapes read-only has to cover

```sql
DROP TABLE fct_trade;                 -- Data Definition Language (DDL)
INSERT INTO fct_trade VALUES (1);     -- a write to a table
COPY (SELECT 1) TO 'leak.csv';        -- a write to the filesystem, not to a table
PRAGMA database_list;                 -- engine introspection, not a query
ATTACH 'elsewhere.duckdb';            -- a second database
SELECT 1; SELECT 2;                   -- two statements in one string
```

The third is the one worth naming. Read-only has to mean the Warehouse **and** the
filesystem, or a statement that reads nothing it should not is still free to write the
answer somewhere no reader of a Grounded Answer will ever see it.

**Verification:** a new `.claude/scripts/check_validation_gate/` — the package
[R8](#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25) rules on, grown one **module** per Sub-step where `check_semantic_layer.py`
and the spike were each grown one rule per Sub-step inside one file. For this Sub-step:
one probe per shape in the block above, a statement that does not parse, one whose
estimate is over the ceiling, and — because a Gate that rejects everything passes every
rejection probe — one ordinary `SELECT` that must be **allowed**.

```bash
uv run python -m veritas.ingestion
uv run python .claude/scripts/check_validation_gate/
uv run python .claude/scripts/check_semantic_layer.py
uv run python .claude/scripts/check_warehouse.py
```

plus the mutation that gives it teeth, in the pattern Sub-step 2.6 established: delete
the parse-failure rule, re-run, see the unparseable probe reported as allowed and the
run fail; restore and compare with `cmp`.

#### R7 — The bounded read uses the engine's estimate, if the adapter can reach it → **approved by Amino 2026-08-25**

**Approved as proposed**, and Amino restated the order it is to be settled in:
*"check if proposal 1 works and if not fall back to proposal 2."* So 5.1 does not
choose; it commits the check that measures, and the measurement chooses. The fallback
is pre-approved, which means finding (1) unreachable is a finding to record rather than
a question to bring back.

Two candidate rules, and the plan cannot pick between them from the armchair.

1. **The engine's estimate.** The Gate asks the Warehouse Adapter what the planner
   thinks the statement will scan and rejects above a declared ceiling. This is what
   the [Target State](../design/target-state.md#extension-path-to-the-full-proposal)
   assumes when it says the full MVP will *"swap DuckDB's estimate for BigQuery
   dry-run bytes-billed"* — a swap presupposes an estimate.
2. **The parse tree.** The Gate requires a period filter on the metric's own
   `date_column` and a row limit, and decides boundedness from the statement alone.
   This needs no engine feature and stays inside the parse-tree method ADR-0003 chose,
   but it measures intent rather than cost.

**The proposal is (1), falling back to (2).** A throwaway probe on 2026-08-25 suggested
DuckDB exposes a machine-readable per-operator estimate under `EXPLAIN` in JavaScript
Object Notation (JSON) form, where plain `EXPLAIN` returns the plan as a drawn box
diagram — and reading a number out of a drawn diagram is the text-matching ADR-0003
rejected by name. **That probe is not committed and is therefore not evidence.** 5.1's first job is to commit the check that
settles it. If the estimate turns out not to be reachable through the adapter without
DuckDB-specific parsing leaking past ADR-0002's seam, the rule becomes (2) and the
Step Review says so.

Either way the estimate is fetched **through the adapter**, never by the Gate itself:
`EXPLAIN` syntax is dialect, and `check_warehouse.py`'s seam scan fails the run on a
`duckdb` import outside `veritas/warehouse/` — correctly.

### 5.2 — The Gate traces every metric expression to a Certified Metric

The first rule that reads the corpus, and the one ADR-0001 exists to make decidable.

- The Gate loads `semantic/metrics/` through `veritas/semantic/loader.py` — **not**
  Python literals. This is the difference between the Gate and the spike, and the
  reason [R2](#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
  matters: after it, one tracer reads two corpora, and the spike's pins are what keep
  its 2026-08-20 measurement honest.
- A statement is allowed when it computes **at least one** metric expression and
  **every** one traces. Both halves are load-bearing: the first is what makes a
  statement with no recognisable metric a rejection rather than a vacuous pass, and it
  is half of what the spike achieved by accident.
- C1's pasteable form is what keeps C5's two rewrites sufficient. A paraphrase that
  returns the identical number is refused, by design, and 5.2's probes include one.
- **`Position Change` is the shape nobody has measured.** The
  [4.2 review](../reviews/step-004-semantic-layer.md#sub-step-42--write-the-remaining-metric-definitions)
  recorded it as *"the one expression shape the spike never measured — a correlated
  scalar subquery with an `ORDER BY` and a `LIMIT` inside an aggregate"*, where every
  expression the spike traced is flat arithmetic over joined columns, and said the
  Gate Step is where that lands. **It lands here.** If it does not trace under the two
  rewrites, that is a finding this Sub-step must report rather than route around: the
  options are a third rewrite (which widens what C5 trusts and is a ruling, not a
  patch), a rewritten expression (which is a Step 004 amendment), or debt with a
  trigger. The Step Review states which.

**Verification:** the package gains `traces.py`, holding the spike's claim-1 and
claim-3 probe shapes — table aliases, an output alias, a derived table, a Common Table
Expression (CTE), and the Shadow Metrics that must be rejected — re-run against the
**Gate** rather than against the spike's own tracer, plus one probe per Certified
Metric so that all nine are traced and not only the three the spike pinned.

### 5.3 — The Gate refuses a Restricted Column, under an Access Profile

C3's other half, and the first time an identity enters the system.

- **The Access Profile**, in `veritas/validation/` as the Glossary registers it and as
  [R3 of Step 004](step-004-semantic-layer.md#r3--restricted-columns-are-declared-in-the-access-profile-not-in-a-metric-definition--approved-by-amino-2026-08-21)
  ruled: the identity a question is run as — *"role and permitted region"* — carrying
  the Restricted Columns that role may not see. `dim_client.client_name` is the one the
  spike measured; the profile is what makes that a declaration rather than a constant.
- **C4's run-time schema read.** `SELECT *` is expanded against the real column list
  read through `WarehouseAdapter.columns`, because it is *"the one shape whose
  restricted name exists nowhere in its own text"*.
- **The question is whether the column reaches the answer**, not whether the name
  appears. The spike's `columns_reaching_the_answer` holds that distinction across ten
  shapes and four of them exist only to hold it: a name in a comment, a name in a
  string literal, a column in a filter, and a column projected inside a subquery and
  aggregated away are all in the statement and in none of them does a reader of a
  Grounded Answer see a Client's name.
- **The honesty note travels with the code.** The Gate's module docstring carries
  [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)'s
  own sentence — *"applied in the application layer, over synthetic data … it does not
  protect the Warehouse from being read another way"* — and the entry gains a dated
  status note naming `veritas/validation/` as where the enforcement now lives, so the
  README pass finds it rather than rediscovering it. The entry is **not** marked paid:
  its Trigger is a claim *"anywhere a reader will see it"*, and neither `README.md` nor
  the App exists.

**Verification:** the package gains `restricted.py`, holding the spike's ten
restricted-column shapes, judged by the Gate and — as the spike does — also by
searching the query's text, so ADR-0003's rejected alternative
goes on being shown wrong on every run rather than in an argument. The mutation:
remove the `SELECT *` expansion, re-run, watch the one shape whose name is nowhere in
its own text pass.

### 5.4 — Pay DEBT-014: the Gate checks the route and the date predicate

[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)'s
Trigger is *"the Sub-step that builds the Validation Gate"*, and its repayment
condition is written as a test rather than an intention:

> That Sub-step is not done until `notional through the wrong currency` is rejected by
> the Gate, and until this probe in the spike expects a rejection rather than an
> allowance.

- The Gate compares the joins in a statement against the metric's own `join_paths`,
  and the column its period filter keys on against the metric's `date_column`. Both
  fields exist because C2 required them in Step 004; this is the Sub-step that spends
  them.
- **The currency half is measured.** `Traded Notional` converted out of the Trade's
  Denomination Currency instead of the Instrument's Quotation Currency projects
  identically to the right one and is wrong by a margin the spike prints on every run.
  Its verdict flips to rejected, and `BLIND_SPOT` stops being a kind a passing run can
  contain.
- **The date half is argued and this Sub-step owes the measurement.** The entry's
  2026-08-20 status note says so outright: *"No probe converts on Settlement Date, so
  unlike the currency pair this half is argued rather than measured, and the Sub-step
  that pays this entry owes a probe for it."* The probe is a `Gross Revenue` keyed on
  `settlement_date` instead of `trade_date` — a Section C pair, two columns on
  `fct_trade`, one projection — executed so the two numbers are printed side by side
  before the rejection is claimed to matter.
- **Dates come from the Snapshot calendar.**
  [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)'s
  Trigger is *"the first 'as of' date chosen by anything but the Snapshot calendar"*,
  and a probe that picks a period boundary out of the air fires it. Every date in this
  Step's probes is read from the calendar, which keeps the arm unfired the way
  [R7 of Step 004](step-004-semantic-layer.md#r7--the-date-axis-defers-debt-012s-trigger-rather-than-avoiding-it--approved-by-amino-2026-08-21)
  did.

**Verification:** `check_validation_gate/` gains `route.py`, and it and
`check_validation_feasibility.py` both run, and the spike's own expected verdict for that probe has changed in the same
commit. **This Sub-step is not done until the spike's `BLIND_SPOT` kind has no members**
— the same bar the Ledger entry sets.

### 5.5 — The Gate requires the Access Profile's predicate, and admits a slice route

The last rule, the only Sub-step that changes `semantic/`, and the largest in the Step
after [R1](#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25) widened it.
It is the pre-agreed split point under [R5](#r5--55-is-a-pre-agreed-split-point--approved-by-amino-2026-08-25).

- **Five Join Paths**, one per distinct `from_table` across the nine Metric
  Definitions plus the hop they share: `trade_to_account`,
  `position_snapshot_to_account`, `balance_snapshot_to_account`,
  `accounting_movement_to_account`, and `account_to_client`. They are ordinary Semantic
  Entries and `check_semantic_layer.py`'s existing route checks apply to them
  unchanged.
- **A `routes` field on all five Dimension Definitions** — the map from a metric's
  `from_table` to the Join Paths that reach the axis's columns from there, in the shape
  [R1](#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)
  sets out. An empty list means the column is already there; an absent key means the
  axis is not reachable from that fact table and a slice by it is rejected by name.
  `veritas/semantic/loader.py` gains the field; `check_semantic_layer.py` gains a check
  that every named Join Path exists and that each chain actually connects its key to
  the table holding the axis's columns.
- **The rule the Gate gains has three sources of permission and no fourth**: the
  metric's own `join_paths`, the `routes` of each axis the statement groups by, and the
  `by region` route the Access Profile's predicate needs. A join no entry names is a
  rejection, and the Gate never searches for a chain that would name it.
- **The Access Profile is completed here**: 5.3 declares it with a role and its
  Restricted Columns, and 5.5 adds the permitted region — a value of the `by region`
  axis, refused at load if the axis does not certify it.
- **What this closes.** `by region` stops being certified-and-unreachable. The route
  exists and the rule that lets a query group by it exists, which are the two halves
  [R11](step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)
  named — so the first of the three questions Step 004 handed to the Grounding Step is
  **answered here rather than narrowed**, and the Step Review says so in those terms.
  The reach count `check_semantic_layer.py` prints on every run stops printing zero for
  that axis, which is the signal R11 kept alive for exactly this moment.
- **What this does not close.** R11's other two questions are untouched — no `by
  settlement date` axis, and check 17's foreclosure stands. Both ask what the corpus may
  **certify**; this Sub-step certifies no axis, it gives certified ones a route.

**Verification:** three families of probe, all in the package's `access.py`.

- **The predicate binds on every metric.** For each of the nine Certified Metrics, a
  statement carrying the Access Profile's predicate is **allowed** and the same
  statement without it is **rejected** — eighteen probes, so the rule is shown to bind
  on the Snapshot and movement metrics and not only on the trade-side four.
- **The slice route works and is bounded.** `Net Revenue by region` — the Glossary's
  own worked example, executed rather than argued — is allowed and returns three
  buckets; `Cash Balance by instrument type` is rejected on the absent key; and a
  statement joining `dim_client` while grouping by nothing is rejected, because
  reaching an axis is permitted by grouping on it, not by mentioning its table.
- **The mutations.** Delete the access-predicate rule, re-run, and watch the nine
  un-predicated probes pass; restore and `cmp`. Then delete the absent-key branch and
  watch `Cash Balance by instrument type` be allowed to join a table with no Instrument
  in it.

### R12 — Amino's rulings on the 5.1 review → **decided 2026-08-26**

One ruling, on the eight sceptical items of
[the 5.1 review entry](../reviews/step-005-validation-gate.md#sub-step-51--the-validation-gate-refuses-anything-that-is-not-a-bounded-read).
Amino: *"all approved."* Nothing is rebuilt. It lands **in the 5.1 commit itself**
rather than after it, for the reason [R11](#r11--aminos-rulings-on-the-trim--decided-2026-08-26)
did: the ruling arrived before the commit did.

**Four of the eight offered a concrete reversal, and each reversal is declined.** These
are the ones worth naming, because a later Sub-step hangs off them and approval is what
makes them load-bearing rather than provisional.

1. **`veritas/validation/` stays two modules** (item 1). The `Validation Gate outcome`
   is a data contract before it is a return value — [R3](#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)'s
   words — so a Grounded Answer, the App and Observability read a verdict without
   importing sqlglot, two optimizer rules and the Warehouse Adapter. Merging
   `outcome.py` into `gate.py`, which the entry offered as one move since `__init__.py`
   re-exports both names, is not taken.
2. **A `UNION` of two `SELECT`s goes on being refused** (item 3). *"Anything that is not
   a single `SELECT`"* holds at its literal reading, and that probe's `rejected` verdict
   is now a measurement rather than a default — a later Sub-step that wants unions flips
   it deliberately, against this ruling.
3. **`check_language.py` keeps its third keyword derivation** (item 7). The fifty-line
   fix stands over the three-line hand-list, so the comment in that file saying the
   keywords of the SQL this project writes are derived and not remembered goes on being
   true now that `DROP` is one of them.
4. **`TRUSTED_REWRITES` stays declared ahead of its first user** (item 8). [C5](../design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
   asks for the constant named in one place, printed, and reported on the outcome, and
   5.1 does all three; 5.2's tracer hangs off the contour line rather than drawing it.

**The other four are declared limits, not offers**, and approval records them as known
rather than deciding anything to build: `SCAN_CEILING` is a policy that cannot fire on
today's Warehouse and is exercised by a probe that lowers the ceiling instead (item 2);
`one_statement` reads a failed parse as zero statements, which is what makes mutation 1
legible (item 4); `reasons` is a tuple holding one member until 5.3 fills it (item 5);
and the independence proof uses a stand-in that is not a `WarehouseAdapter`, which
proves the rules touch nothing and does not prove they survive a degraded Warehouse
(item 6).

**What this makes true that was not.** The four seams above are settled, so 5.2 builds
on them instead of relitigating them: it imports the contract from `outcome.py`, it
applies `TRUSTED_REWRITES` where 5.1 declared it, and it inherits a rule set whose
`rejected` verdicts are all measurements. Nothing in the ruling changes a name, an
interface or the flow, which is why it costs no code.

### R13 — Amino's rulings on the 5.2 review → **decided 2026-08-27**

Rulings on the eight sceptical items and the one Term Proposal of
[the 5.2 review entry](../reviews/step-005-validation-gate.md#sub-step-52--the-gate-traces-every-metric-expression-to-a-certified-metric).
Amino: *"3 → edit the plan accordingly. 5 → if this won't get built in a specific future
step, create a debt for it which triggers when a semantic definition drifts. 7 → amend.
The `metric expression` term proposal is approved. All other changes are reviewed,
approved, and staged."* They land **in the 5.2 commit itself** rather than after it, for
the reason [R11](#r11--aminos-rulings-on-the-trim--decided-2026-08-26) and
[R12](#r12--aminos-rulings-on-the-51-review--decided-2026-08-26) did: the ruling arrived
before the commit did.

**Three items cost an edit and five do not.** The five approved as they stand are
declared limits rather than offers, and approval records them as known: `count(*)` is a
Shadow Metric by [C1](../design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)'s
design, so the pressure lands on Grounding rather than on a patch here (item 1); the
three new `Rejection Reason` members stay three bars rather than one, so a chart can
separate a Grounding problem from a generator problem from a statement that will not
resolve (item 2); `certified_form` goes on raising `ValueError` on a broken corpus, which
is the call [R12](#r12--aminos-rulings-on-the-51-review--decided-2026-08-26) made for a
Warehouse that will not open (item 4); the rewritten positive control stands over
changing 5.1's two probe statements (item 6); and the timing figures stay dated evidence
that no check asserts on (item 8).

**1. The plan's dependency sentence is corrected** (item 3). Amino: *"edit the plan
accordingly."* [What the Gate must decide](#what-the-gate-must-decide) predicted that the
live schema arrives with 5.3; it arrived with 5.2, because `qualify` cannot attach a
column to its table without a catalogue. The sentence now says 5.2 needs both, and it
carries the correction and its date rather than being quietly rewritten — the rule order
it exists to justify is unchanged, and only the prediction of when the second dependency
lands was wrong.

**2. [DEBT-018](../debt-ledger.md#debt-018--six-certified-metrics-have-no-expression-text-pinned-outside-the-corpus) is opened** (item 5).
Amino: *"if this won't get built in a specific future step, create a debt for it which
triggers when a semantic definition drifts."* It will not get built: no Sub-step of this
Step pins an expression's text, and 5.5's corpus edit adds Join Paths and a `routes`
field rather than touching an `expression`. So the entry is opened with exactly that
trigger — the first edit to a Certified Metric's `expression` in `semantic/metrics/`.
Writing it forced the gap to be measured rather than asserted:
`check_semantic_layer.py`'s check 4 already compares **all nine** metrics' numbers
against SQL that reads nothing from `semantic/`, so what nothing catches is narrower than
the review claimed — an edit to one of the **six** metrics
[R4 of Step 004](step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)
did not pin, that changes an expression's text **without changing its number**. The
repayment is check 9's pin widened from three metrics to nine.

**3. The `Shadow Metric` row is amended** (item 7). Amino: *"amend."* Its *Lives in* cell
read *"— (an anti-pattern)"*, which was true while nothing in the repository named one;
`veritas/validation/` now returns `RejectionReason.SHADOW_METRIC`, so the cell names that
home and keeps what the parenthetical was really saying — no Semantic Entry publishes a
Shadow Metric. The definition cell carries the amendment, its date and a pointer here,
which is the shape the `Dimension Definition` row's amendment of 2026-08-24 set.

**4. `metric expression` is registered** — the Term Proposal the review raised and did
not take. Amino: *"the `metric expression` term proposal is approved."* It goes into
[Glossary Section A](../glossary.md#a-the-system) between `Certified Metric` and
`Shadow Metric`, **entirely in lower case**, because that is how the `agreed` Target
State's flow, ADR-0001 and ADR-0003 have spelled it since Step 001 and how
`metric_expressions` has been spelled since Step 003. Registering it in Title Case would
have meant editing an `agreed` Target State to match a Glossary row, which is the wrong
way round; the row registers a word three agreed documents already relied on.

**What this makes true that was not.** The plan's route sentence is true again, the
corpus has a tripwire under it, and both `Shadow Metric` and `metric expression` are
registered where a reader naming something will look. Only the Ledger gains an entry: no
name, no interface and no flow moves, so 5.3 starts from the same seams 5.2 finished on.

### R14 — Amino's rulings on the 5.3 review → **decided 2026-08-27**

Rulings on the nine sceptical items and the one question of
[the 5.3 review entry](../reviews/step-005-validation-gate.md#sub-step-53--the-gate-refuses-a-restricted-column-under-an-access-profile).
Amino: *"1 → separate the profile from the gate as in `judge(sql, profile)`. 2 → fine for
now and approved. 3 → fine and approved. 4 → fine and approved. 5 → we shouldn't import
the spike. what is the alternative? 6 → approved. 7 → fine for now. 8 → approved. 9 →
approved and very good. All other changes are reviewed, approved and staged."* They land
**in the 5.3 commit itself** rather than after it, for the reason
[R11](#r11--aminos-rulings-on-the-trim--decided-2026-08-26),
[R12](#r12--aminos-rulings-on-the-51-review--decided-2026-08-26) and
[R13](#r13--aminos-rulings-on-the-52-review--decided-2026-08-27) did: the ruling arrived
before the commit did.

**Two items cost an edit and seven do not**, and one of the two is the only seam this
Step has moved. The seven approved as they stand are declared limits rather than offers,
and approval records them as known: `RestrictedColumn` stays a class rather than a tuple
(item 3); the tenth probe goes on grouping by ordinal, because the property it measures
— a restricted column reaching the answer with its name nowhere in the text — is real
whatever syntax produces it (item 4); the `UNRESOLVABLE` branch stays unreached inside
the assembled Gate and the check goes on saying so (item 6); `found_by_text` stays
duplicated rather than becoming a function in `veritas/validation/` that nothing may call
(item 8); and 5.1's and 5.2's printed output keeps the widened probe column and the
`replace`-based rebuild that
[came with it](../reviews/step-005-validation-gate.md#look-at-this-sceptically) (item 9).

**1. The Access Profile leaves the Gate and becomes an argument to `judge`** (item 1).
Amino: *"separate the profile from the gate as in `judge(sql, profile)`."* The review
raised this as *"the seam most likely to be wrong"*, and it was: the Glossary registers
an Access Profile as *"the identity Veritas runs a **question** as"* — per question, so
one Gate serves many identities and an application process loads the corpus once for all
of them. A field made a second identity a second Gate.

What a Gate is **built with** is now only what its rules read out of the world — the
Warehouse Adapter, the corpus, the scan ceiling — and what a statement is **judged
under** is passed in: `ValidationGate.judge(sql, access_profile)`, with no default, so a
caller who does not say who is asking gets a `TypeError` rather than a verdict reached
under an identity nobody chose.

**The rule list stays one shape.** `rules(access_profile)` binds the identity into the
one rule that reads it with `functools.partial`, so `Rule` is still *one `Reading` in, a
verdict out*. The alternative — every rule taking an Access Profile — would have given
the three rules that need nothing a parameter they ignore, and the module's whole
ordering argument rests on those three needing nothing: a signature that takes an
identity is a rule a reader has to check does not consult one.

It is cheap now for the reason the review gave — the Orchestrator does not exist, and
four construction sites is the whole of the blast radius. The cost was those four losing
an argument, eleven call sites gaining one, a parameter on the checks' shared
`judge_probes`, and two lines in `restricted.py`'s `rule_name` to unwrap the `partial`.
**No check's output moved**, which is the evidence that this was a seam moved and not a
rule changed.

**2. Nothing imports the spike; its statements are read out of its text** (item 5).
Amino: *"we shouldn't import the spike. what is the alternative?"* The alternative is to
stop treating a claim about **text** as a claim about objects. `probes.spike_statements`
parses `check_validation_feasibility.py` with `ast` and reads the `name=` and `sql=`
literals off the parse tree without executing a line of it — and adjacent string literals
are folded by the parser, so a statement the spike writes across fifteen source lines
comes back as the one string the spike compiled.

Three things are better, and one is the point:

  * **The dependency is a file, not a module.** What these checks depend on is a dated
    measurement held in this repository at a path; an import would have made the Gate's
    own check stop working the day the spike stopped importing.
  * **A 1,700-line script's module-level work no longer runs** inside a check whose
    question is *"is this string the same string"*.
  * **The direction is now unambiguous.** The spike imports the tracer and the detector
    from `veritas/validation/` under [R2](#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25);
    nothing imports the spike.

**And the claim is checked in both places that make it**, which is the review's own
*"either both should be checked or neither"*. `probes.check_the_statements_are_the_spikes`
is shared, and `traces.py`'s comment is now a run: 15 of the spike's 16 claim-1
statements are there character for character, one of them under a shorter local name, 3
added by 5.2 — and the one the spike measures that `traces.py` does not judge,
`unparseable`, is **declared** rather than silently absent, naming `read_only.py` as
where the Gate refuses that shape. A declaration that stops describing anything fails the
run too, because an allowance nobody re-reads is how coverage quietly shrinks.

**3. Two items are approved *for now*, and each has a condition that brings it back.**
Neither is Ledger debt: nothing here is the cheap thing standing in for the right thing,
and an entry with no trigger that can fire inside this project's life is a wish.

  * **`role` gets no Glossary row** (item 2). Amino: *"fine for now and approved."* The
    value is read as data an entry carries — the way `EU` is a bucket of the `by region`
    axis — and [Glossary Section A](../glossary.md#a-the-system) is a table of
    components, which a job title is not. **What brings it back is a second role**, which
    this Step's scope boundary puts outside it: one profile, one role. The row is one
    line and `ANALYST` does not move if it is written. This closes the one question the
    5.3 review left open.
  * **`resolve` goes on catching `AssertionError`** (item 7). Amino: *"fine for now."*
    It is a real widening of what gets called a rejection, and the Gate that crashes is
    the worse of the two. What would make it wrong is an `AssertionError` raised by
    **Veritas's own code** inside `optimize` being reported as a library refusal — which
    cannot happen while nothing of ours runs in there, and would be the thing to look at
    first the day a trusted rewrite of our own joins `TRUSTED_REWRITES`.
    [DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)'s
    line is unchanged for every other exception type: a `KeyError` out of a broken schema
    mapping still escapes.

**What this makes true that was not.** A second identity is a second call rather than a
second Gate, and the corpus behind it is loaded once — which is what an App process will
need and what a field would have cost. The Gate's check no longer imports a spike to
prove a text claim, and the same claim is now measured in both modules that make it. One
seam moved, in the Sub-step that introduced it and before anything was built on it;
nothing else did, so 5.4 starts from the rule list, the taxonomy and the detector 5.3
finished on.

---

## Which Debt Ledger triggers this Step fires

Checked before planning, per `planning-a-step` step 3. **Two fire and both are paid
inside the Step. One is in reach and is avoided by construction.**

| Entry | Trigger | This Step |
|---|---|---|
| [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject) | The Sub-step that builds the Validation Gate | **Fires in 5.4 and is paid there.** It cannot be deferred: the Trigger names this Step by name, and its repayment condition is a test the check either passes or does not |
| [DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type) | The first component outside `.claude/scripts/` that has to handle a failed query | **Fires in 5.1, earlier than its own text predicted, and is paid there.** The entry names *"the Orchestrator's execute step"* as the expected place; the Gate gets there first, because a bounded-read check asks the engine to plan caller-supplied SQL and that can be refused. The entry's own reasoning applies unchanged — the Gate *"cannot catch `Exception` and stay honest, because it has to tell a user which of the two happened"*: a query the engine will not plan is a rejection, and an adapter that cannot open the Warehouse is a broken installation |
| [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes) | The first "as of" date chosen by anything but the Snapshot calendar | **In reach, and avoided by construction.** Every date in this Step's probes is read from the Snapshot calendar. All three arms stay open |
| [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers) | The first access-control claim in `README.md`, the App, or a demo script | Does not fire — none of the three exists. 5.3 puts the entry's own caveat in the Gate's docstring and a dated status note on the entry, which is not payment |
| [DEBT-004](../debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal) · [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level) | Building the Gold Question Set | Not built here. A probe statement is not a gold question: it has a declared verdict, not a declared answer |
| [DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews) | The final documentation pass, before peer review | Does not fire — the Step Review is the internal record, which is what the entry is about. **[R10](#r10--current-state-is-trimmed-in-its-own-commit-between-the-plan-and-51--approved-by-amino-2026-08-25)'s trim does not enlarge it**: it moves narrative from one internal document into the internal reviews that already hold it, and the entry is about what a reader outside `.claude/docs/` can see |
| [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) | A sixth certified axis, or a rewording of that cell failing the run | Does not fire — 5.5 adds Join Paths, not an axis. [R3](#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25) is where this Step declines to repeat the shortcut it records |
| [DEBT-003](../debt-ledger.md#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope) | A requirement to hold a single bond or an option | Does not fire — the Gate judges statements over the Instruments the Warehouse already holds |
| [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement) | The next observed framework-rule breach | Nothing planned breaks a rule; if one is observed, the entry's own instruction applies |

---

## Not in this Step

- **Grounding.** No `veritas/grounding/`. The Gate judges a statement someone else
  wrote; building the prompt from retrieved entries is a different component with a
  registered home of its own. **Two of the three questions
  [R11](step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)
  handed to Grounding stay there** — whether `by settlement date` becomes an axis, and
  whether check 17's foreclosure admits an axis whose buckets ingestion minted. Both ask
  what the corpus may **certify**, and nothing here certifies anything. **The third
  closes in 5.5**, under [R1](#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)'s
  widening: it is the one piece of Grounding's work this Step takes, and it is taken
  deliberately rather than drifted into.
- **Route discovery.** The Gate never searches `semantic/joins/` for a chain that
  reaches a table. Every join a statement may carry is named by an entry pointing at it
  — a metric's `join_paths` or an axis's `routes` — and a route nothing names is a
  rejection rather than a search. [R1](#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)
  is where the two rejected alternatives are argued.
- **Retrieval, and therefore embeddings and the search index.** Nothing is indexed,
  embedded or ranked, and no Large Language Model API key is needed to run any command
  in this plan.
- **The Orchestrator, the App, Observability, Evaluation, containerization.**
  Untouched, and nothing here half-builds any of them. In particular nothing
  **executes** an allowed statement: `VALIDATE` is step 5 of the
  [Target State's flow](../design/target-state.md#flow) and `EXECUTE` is step 6, and
  the Gate that runs the query it just approved is a Gate with no boundary.
- **The Gold Question Set**, and therefore DEBT-004's and DEBT-011's repayment.
- **`README.md`**, and therefore DEBT-008's and DEBT-013's.
- **Warehouse-native enforcement**
  ([EXT-001](../extension-register.md#ext-001--warehouse-native-security-and-concurrency)).
  DuckDB has no policy-tag mechanism, which ADR-0003 already records; the
  application-layer check is the slice's only enforcement point and EXT-001 replaces it
  rather than joining it.
- **[EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks)'s
  remaining rules.** The Gate reads the corpus; it does not audit it.
- **A test framework** — [R9](#r9--no-test-framework-in-this-step-and-step-002s-prediction-is-set-aside--approved-by-amino-2026-08-25), which is a ruling rather than the proposal
  Steps 003 and 004 each carried, and which is where the argument lives: Step 002's R5
  named this Step as pytest's arrival and Amino has set that prediction aside. Evidence
  goes on coming from a committed check script that exits non-zero.
- **Converting the three existing check scripts to packages.** [R8](#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25) decides the
  shape of the check this Step writes and nothing about the ones already written. They
  work, they run on every commit, and rewriting them moves no name, no interface and no
  flow — a scope boundary, not debt.
- **A second Reporting Currency**, and a second Access Profile role. One of each
  exists in this slice; both are files or rows added rather than fields changed, so
  this is a scope boundary rather than debt.
