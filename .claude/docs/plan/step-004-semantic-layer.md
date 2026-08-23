# Step 004 — Build the Semantic Layer

- **Status:** **active** — written 2026-08-21 and **approved by Amino the same day**,
  together with all seven rulings in [Questions for Amino](#questions-for-amino).
  **Sub-step 4.1 may begin once this plan is committed.** Four rulings were approved
  as written; **R2, R4 and R7 were sent back once and approved on the second
  pass** — R2 and R4 with their reasoning rewritten around the worked example that
  decides each, and R7 restated as the **deferral** it is rather than the avoidance it
  first claimed to be. The Step has five Sub-steps, and
  [R5](#r5--45-is-a-pre-agreed-split-point--approved-by-amino-2026-08-21) pre-agrees
  where it splits if it grows.
- **Goal:** Author the certified registry Veritas retrieves over — every Certified
  Metric, Ambiguous Term, Join Path and Dimension Definition as a versioned YAML
  Semantic Entry under `semantic/` — in the shape the
  [six constraints](../design/validation-feasibility.md#consequences-for-step-004)
  require, with every Metric Definition's published expression **executed against the
  real Warehouse** and checked against the figure `check_warehouse.py` computes
  independently.
- **Moves Current State by:** turning the `Semantic Layer` row from `✗ none` to
  working — the **third of nine** components, and the first built since the
  Warehouse. It is also the first Step whose output is *authored content* rather
  than code, which changes what verification has to mean: a corpus cannot be proved
  by running it, only by running what it claims.

---

## Why this Step

**1. It is the Step already agreed.**
[R4 of Step 003](step-003-validation-feasibility.md#r4--step-003-is-the-spike-alone-the-semantic-layer-is-step-004--approved-by-amino-2026-08-15)
settled this on 2026-08-15:

> The alternative was folding the Semantic Layer into this Step behind an R6-style
> pre-agreed split point. Rejected for two reasons: Step 002's plan already ruled
> that the Semantic Layer deserves a Step where it is the subject, and the spike's
> own findings are an input to that Step's design — a Sub-step that authored Metric
> Definitions would be written before 3.5 decided what a Metric Definition must
> carry.

3.5 has now decided what a Metric Definition must carry. This is that Step.

**2. Its design inputs are settled rather than discovered.** Step 003 ended with
**GO on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)** and six
constraints, and
[R3](../design/validation-feasibility.md#r3--the-six-constraints-bind-step-004s-plan--approved-by-amino-2026-08-20)
ruled how they land here:

> The six constraints are an input Step 004's plan starts from rather than a
> suggestion it may weigh, and C1's fork is settled as written: the Semantic Layer
> publishes a pasteable form, and the Gate normalises nothing beyond the two
> rewrites C5 names.

So the two questions that would otherwise dominate this plan — what a Metric
Definition carries, and whether the Gate or the Semantic Layer absorbs the
difference between two spellings of one expression — are already answered. What is
left is authoring, and proving the authoring.

**3. Everything above it is blocked on it.** Retrieval searches Semantic Entries
([ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md)); Grounding builds
the prompt from retrieved entries only; the Validation Gate traces a generated
expression back to a certified one; retrieval evaluation derives its ground truth
from which entries a gold SQL touches. Four components take this corpus as input and
none of them can start without it.

**4. It is the last Step that can be done without an LLM API key.** Everything after
it — Retrieval's embeddings, the Orchestrator, Evaluation — needs one. That is not a
reason to do it now so much as a reason to notice that the project's key-free half
ends here, and to have the corpus be good before anything starts consuming it.

---

## What the six constraints require of this Step, concretely

Two constraints shape what is built here. Four shape the Step after it, and this
Step's only obligation to them is to not foreclose them — recorded so that a Gate
Step does not have to rediscover it.

| Constraint | What it means for Step 004 |
|---|---|
| [C1 — publishes a pasteable form](../design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes) | **Binds.** A Metric Definition's `expression` is the exact text an Orchestrator pastes, and the check pastes it **verbatim** rather than re-deriving it — a check that rebuilds the expression proves the rebuild, not the file |
| [C2 — carries its Join Path, and its date predicate](../design/validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate) | **Binds.** Two required fields, `join_path` and `date_column`, because *"a certified expression pins down the arithmetic and not the rows it is computed over"*. `Traded Notional` converted through the wrong currency column *"projects identically to the right one, traces, and is 96.39% wrong"* |
| [C3 — the two parse-tree rules ship together](../design/validation-feasibility.md#c3--the-two-parse-tree-rules-ship-together) | Binds the Gate Step. Here it means only that `semantic/` must record **which columns are restricted**, so the Gate has something to read — see [R3](#r3--restricted-columns-are-declared-in-the-access-profile-not-in-a-metric-definition--approved-by-amino-2026-08-21) |
| [C4 — the Gate reads the schema at run time](../design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time) | Binds the Gate Step. Not foreclosed: nothing here caches a column list into a file |
| [C5 — the trusted rewrites are named in code](../design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two) | Binds the Gate Step. Not foreclosed, and C1 is what keeps it cheap — a pasteable form is why two rewrites are enough |
| [C6 — fail closed on parse failure](../design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident) | Binds the Gate Step. Here it has one echo: an entry whose expression does not parse must fail this Step's check loudly, not be skipped |

---

## The format this Step proposes

Presented in the plan rather than discovered in the implementation, because
[R3](../design/validation-feasibility.md#r3--the-six-constraints-bind-step-004s-plan--approved-by-amino-2026-08-20)
calls the file format *"a seam three Extension Register entries land against"* and a
seam is a contour line — the thing `CLAUDE.md` says to get right now because moving
it later is a repaint. Approving this plan approves this shape.

> **Amended by [R8](#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)**,
> which was delegated to Sub-step 4.2 by Amino's ruling of 2026-08-22. The
> Metric Definition block below is the shape 4.1 published and 4.2 amends in five
> named ways; the Join Path block below is still the format, and the only thing in it
> that moved is the **name** —
> [R9](#r9--aminos-four-rulings-on-the-42-review--decided-2026-08-23) renamed it to
> `trade_to_fx_rate_on_denomination_currency` in Sub-step 4.2, and no field changed.
> Read R8 for what a Metric Definition carries now, R9 for the rename, and the four
> bullets under this section for why each field is here at all — those arguments
> survive both amendments.

`semantic/metrics/gross_revenue.yaml`:

```yaml
name: Gross Revenue          # the Glossary term, spelled exactly as registered
version: 1                   # what Lineage records; bumped when the expression moves
kind: metric
description: >
  Sum of Commission before any Rebate or pass-through Fee is deducted.
expression: "sum(fct_trade.commission * fct_fx_rate.fx_rate)"
grain: one row per Trade
unit: money
reporting_currency: EUR
join_path: trade_to_fx_rate_on_trade_date
date_column: fct_trade.trade_date
aliases: ["gross commission", "revenue before rebates", "commission income"]
derives_from: []
```

`semantic/joins/trade_to_fx_rate_on_trade_date.yaml`:

```yaml
name: trade_to_fx_rate_on_trade_date
version: 1
kind: join_path
from_table: fct_trade
to_table: fct_fx_rate
on: >
  fct_fx_rate.rate_date = fct_trade.trade_date
  AND fct_fx_rate.from_currency = fct_trade.denomination_currency
  AND fct_fx_rate.to_currency = 'EUR'
```

Four things about this shape are decisions rather than typing, and each is stated
here so that rejecting one costs a conversation instead of a Sub-step.

- **Every field name is either a registered Glossary term or a plain English word
  from the `Metric Definition` row's own definition** — *"a named, versioned,
  certified computation over the warehouse — its SQL expression, grain, filters,
  units, and the aliases people use for it"*. `join_path` is
  [`Join Path`](../glossary.md#a-the-system); `reporting_currency` is
  [`Reporting Currency`](../glossary.md#a-the-system); `derives_from` is the name
  [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks)
  already chose. **No new domain noun is coined**, which is checked by writing the
  eight files before the loader is written, not asserted here.
- **`date_column` names a column, not a concept.** C2 says *"date predicate"*, and
  the honest implementation of a predicate for this slice is the column the period
  filter and the FX join both key on: `fct_trade.trade_date` or
  `fct_trade.settlement_date` — the
  [Section C pair](../glossary.md#c-distinctions-we-must-not-blur) that *"shifts
  revenue across period boundaries"* and *"moves the number twice"*. Both are
  registered terms, so the field carries no vocabulary of its own.
- **The Reporting Currency appears twice, and a check makes that safe.** `'EUR'` is
  inside the Join Path text because C1 forbids a template the loader fills in — a
  placeholder is exactly the re-derivation between *what a reviewer reads* and *what
  the Gate judges* that C1 exists to remove. The duplication is made safe rather than
  eliminated: `check_semantic_layer.py` fails if a Metric Definition's declared
  `reporting_currency` does not appear in the Join Path it names.
- **One Reporting Currency exists in this slice, and the format does not foreclose a
  second.** A second currency is a second Join Path file and a second Metric
  Definition naming it — files added, no field changed, no name moved. That is why
  it is a scope boundary in [Not in this Step](#not-in-this-step) rather than a
  Ledger entry: nothing here is *wrong*, there is simply less of it.

---

## How the five Sub-steps divide the work

The seam first, proved end-to-end on one entry; then the corpus; then the debt that
the corpus fires; then the two entry types that consume it.

```
semantic/metrics/     ← 4.1  the format, the loader, the check — on Gross Revenue alone
semantic/joins/       ← 4.1  the one Join Path that metric carries
semantic/metrics/     ← 4.2  the remaining seven Metric Definitions and their Join Paths
.claude/scripts/      ← 4.3  pay DEBT-015 — the dialect scan reads type constructs
semantic/ambiguous/   ← 4.4  the five Ambiguous Terms of Glossary Section D
semantic/dimensions/  ← 4.5  the Dimension Definitions
```

Every commit subject is conjunction-free, and every adjacent pair passes
`planning-a-step`'s real test — **Amino could reasonably approve one and reject the
next**:

| Pair | The independent failure |
|---|---|
| 4.1 / 4.2 | 4.1 decides a shape on one instance; 4.2 fills it eight times. Rejecting the shape wastes one file, not eight — which is the entire reason 4.1 is one metric rather than all of them |
| 4.2 / 4.3 | 4.2 authors content; 4.3 changes a check script and an ADR's wording. Rejecting the wider dialect scan does not unwrite a Metric Definition, and rejecting a Metric Definition does not put a hole back in the scan |
| 4.3 / 4.4 | An Ambiguous Term is a claim about **language** — that "revenue" has two certified meanings. It can be wrong while every expression is right, and its fix is in the Glossary rather than in SQL |
| 4.4 / 4.5 | A Dimension Definition is the "by what?" axis and nothing in the corpus points at one. It is the only entry type that is a leaf, which is why it is last and why it is the split point |

**A split point, pre-agreed.** Five Sub-steps is `planning-a-step`'s ceiling, so
there is no room for review-driven growth — and Step 002 grew twice, which is why
Step 003 pre-agreed one and said so before the Step started rather than at review,
*"when it is already too late to have cost nothing."* If it grows here, the Sub-step
to leave is **4.5**: nothing in the corpus references a Dimension Definition, so the
Semantic Layer is coherent without one, and 4.5 is also where
[DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)'s
third trigger lives — so the debt question travels with the Sub-step intact instead
of being split from it. See
[R5](#r5--45-is-a-pre-agreed-split-point--approved-by-amino-2026-08-21).

**4.2 is the largest Sub-step and the one most likely to grow.** Seven Metric
Definitions is more authoring than any single commit in this project so far, and
five of them touch Snapshots rather than Trades. If it has to split, it splits into
trade-side and Snapshot-side, which takes the Step to six — and six is two Steps, so
that split fires 4.5's.

---

## Questions for Amino

Seven, all raised here rather than decided during implementation — six below and
[R7](#r7--the-date-axis-defers-debt-012s-trigger-rather-than-avoiding-it--approved-by-amino-2026-08-21)
beside the Sub-step it is about. Each rewrites its own heading on approval, the way
[Step 003's rulings](step-003-validation-feasibility.md#rulings) did, so a link into a
ruling carries who ruled it and when.

**All seven were approved on 2026-08-21.** R1, R3, R5 and R6 as written. R2, R4 and
R7 on a second pass: the first two argued their point abstractly and were rewritten
around the example that decides each, and R7 described as *avoidance* what is in fact
a deliberate **deferral** — the version approved says so.

### R1 — `Cash Balance` becomes a Certified Metric → **approved by Amino 2026-08-21**

**The problem is a hole in the corpus, found while planning it.** Two of the five
Ambiguous Terms in [Glossary Section D](../glossary.md#d-ambiguous-terms) resolve to
`Cash Balance`:

> | "balance" | Cash Balance · Account Value | Ask |
> | "how much does X have" | Cash Balance · Account Value | Ask |

But `Cash Balance`'s registered home is `fct_balance_snapshot` — a Warehouse column
concept — while `Account Value`'s is `semantic/metrics/`. So as the Glossary stands,
**an Ambiguous Term would disambiguate to something that has no Metric Definition to
retrieve**, which is precisely the incoherence
[EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) lists as
its fourth rule: *"every Certified Metric an Ambiguous Term claims to disambiguate
between actually exists."*

**Approved 2026-08-21:** amend the `Cash Balance` row's *Lives in* to
`fct_balance_snapshot` · `semantic/metrics/` and write the ninth Metric Definition.
The alternative — dropping two Ambiguous Terms — deletes the
[Section C](../glossary.md#c-distinctions-we-must-not-blur) pair the Glossary calls
*"the wrong question answered confidently"*, which is the failure this project
exists to prevent. This is a Glossary amendment under `registering-language`, not a
new term.

**Approved 2026-08-21: the Step authors nine Metric Definitions, not eight**, and
4.2 carries the Glossary amendment with it.

### R2 — the Semantic Layer and `check_warehouse.py` stay independent → **approved by Amino 2026-08-21**

`check_warehouse.py` already computes every one of these metrics in its own SQL, to
prove the *data* separates the [Section C](../glossary.md#c-distinctions-we-must-not-blur)
pairs. The Semantic Layer will now compute them again, from a published expression.
Two places, one piece of arithmetic — so the question is whether one should read the
other.

**The example that decides it.** Suppose 4.1 writes `Gross Revenue` with the
Commission but without the conversion:

```yaml
expression: "sum(fct_trade.commission)"        # wrong — no FX Rate
```

- **Independent:** the Metric Definition returns four currencies added together, and
  `check_warehouse.py` returns the EUR figure from its own SQL. They disagree, **the
  run fails**, and it names the metric.
- **Coupled** — `check_warehouse.py` reading `semantic/`: both sides compute the same
  wrong sum, the two figures agree exactly, and **the run passes**. The check has
  confirmed that the expression agrees with itself.

The same split shows up on the mistakes this corpus is most likely to make. Set
`date_column` to `fct_trade.settlement_date` by mistake and the independent pair
disagrees across every period boundary; the coupled pair moves together and stays
quiet. A check that passes while demonstrating a wrong answer is
[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect)'s
shape reappearing in a new component.

**Approved 2026-08-21: keep both, and make their agreement the check.** The cost is
real and is the point: editing a published expression now means editing `check_warehouse.py`'s
SQL too, or the run fails. That is an authoring tax on every later change, and it is
what buys the failure above.

**Where there is nothing to compare against, the Step Review says so.** Not every
metric has an independent counterpart figure in `check_warehouse.py`. For those the
check can only assert *it executes and returns a number*, which is the weaker claim,
and 4.2 names which metrics got which rather than letting one word cover both.

### R3 — Restricted Columns are declared in the Access Profile, not in a Metric Definition → **approved by Amino 2026-08-21**

The spike holds `RESTRICTED_COLUMNS = frozenset({("dim_client", "client_name")})` as
a Python literal, and [C3](../design/validation-feasibility.md#c3--the-two-parse-tree-rules-ship-together)
means the Gate Step needs a real home for it. Two homes are available: a flag on the
Metric Definitions that touch the column, or a separate declaration.

**Approved 2026-08-21: a separate declaration, and *not* in this Step.**
[`Restricted Column`](../glossary.md#a-the-system) is registered as *"a column an
**Access Profile** forbids"* and `Access Profile`'s home is `veritas/validation/` —
so restriction is a property of the identity asking, not of a metric. Putting it on
Metric Definitions would make the same column restricted or not depending on which
entry retrieved it, which is the wrong shape and would then be a seam to move. This
Step therefore adds **nothing** for it, and the Gate Step builds
`veritas/validation/` with the Access Profile in it. Recorded here so the Gate Step
inherits a decision rather than an omission.

### R4 — the spike is pinned to the corpus rather than re-pointed at it → **approved by Amino 2026-08-21**

[R2 of Step 003](step-003-validation-feasibility.md#r2--the-spikes-certified-expressions-stay-python-literals--approved-by-amino-2026-08-15)
kept the spike's three certified expressions as Python literals *"so that a spike does
not fix the Semantic Layer's file format"*. That reason expires the moment the format
exists, so: should `check_validation_feasibility.py` now read `semantic/`?

**The example that decides it.** Suppose 4.2 publishes `Gross Revenue` with a filter
the spike never traced:

```yaml
expression: "sum(CASE WHEN fct_trade.trade_date >= '2025-01-01'
                      THEN fct_trade.commission * fct_fx_rate.fx_rate END)"
```

- **Re-pointed:** the spike re-runs against the new expression, prints its verdicts
  and **passes**. `validation-feasibility.md` still reads GO — but the run behind that
  word is now a run over an expression that did not exist when the go was decided, and
  nothing anywhere says so. The document has quietly become a claim about a moving
  target.
- **Pinned:** the literals stay, so the dated measurement stays the measurement that
  was actually taken. That is what a feasibility gate *is* — `validation-feasibility.md`
  carries output from one dated run, and evidence whose inputs move is not evidence.

Pinning **alone** has the mirror-image failure: the go/no-go could be about
expressions the project no longer uses, and nothing would notice.

**Approved 2026-08-21: pin, and add one assertion.** 4.2 makes `check_semantic_layer.py`
assert that the three expressions the spike measured are still **exactly** what
`semantic/metrics/` publishes, failing with both texts printed if they differ. A
divergence then forces a decision — re-run the spike and update the verdict, or put
the Metric Definition back — instead of passing unnoticed in either direction.

### R5 — 4.5 is a pre-agreed split point → **approved by Amino 2026-08-21**

Offered with the plan rather than at review, for the reason
[Step 003's R5](step-003-validation-feasibility.md#r5--34-is-a-pre-agreed-split-point--approved-by-amino-2026-08-15)
gave: *"the option should be on the table before the Step starts rather than offered
at review, when it is already too late to have cost nothing."* If review-driven
growth arrives in 4.1–4.4, **Dimension Definitions become Step 005's first
Sub-step** and this Step ships a Semantic Layer with three of its four entry types.
The Current State row would then read partially built, naming the missing type —
`current-state.md` describes reality, and a corpus missing an entry type is not
"working".

### R6 — no new ADR for the file format → **approved by Amino 2026-08-21**

**Approved 2026-08-21, with the argument against it stated.** The case *for* an ADR
is real:
this is a data model, three Extension Register entries land against it, and
`writing-an-adr` fires on *"a decision that would puzzle someone reading the repo
cold."* The case against is that every expensive part is **already** decided and
already has a written home — the corpus choice is
[ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md), the pasteable-form
fork is [C1](../design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)
and R3, the two required fields are C2, and the relationship fields are EXT-005. A
fifth ADR would mostly cite the other four. The format section above, plus the Step
Review, is proposed as the record instead. **Approved 2026-08-21: no fifth ADR.** Had
an ADR been preferred it would have been a sixth Sub-step and would therefore have
fired [R5](#r5--45-is-a-pre-agreed-split-point--approved-by-amino-2026-08-21)'s split
point.

---

## Sub-steps

### 4.1 — Publish the Semantic Entry format on one Metric Definition

The seam, drawn thin: the format, the loader, and the check, proved end-to-end on
`Gross Revenue` before the shape is repeated eight times.

- `semantic/metrics/gross_revenue.yaml` and
  `semantic/joins/trade_to_fx_rate_on_trade_date.yaml`, exactly as shown above. Both
  files are still there and both have since been amended by a later Sub-step: the
  Metric Definition by [R8](#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22),
  the Join Path by [R9](#r9--aminos-four-rulings-on-the-42-review--decided-2026-08-23),
  which renamed it `trade_to_fx_rate_on_denomination_currency`.
- `veritas/semantic/` — the loader. Named for the component the way
  `veritas/warehouse/`, `veritas/validation/` and `veritas/evaluation/` are; it reads
  the `semantic/` tree, which is the data. The echo between the two names is
  deliberate and is the pattern every other component already follows.
- `uv add pyyaml`, the Step's only new dependency.
- `.claude/scripts/check_semantic_layer.py` — every later Sub-step grows it, the way
  the spike grew one claim at a time:
  1. every file under `semantic/` parses, and every required field is present;
  2. the expression is **pasted verbatim** into a query built from the entry's own
     `join_path` and `date_column`, executed through the Warehouse Adapter, and
     returns a number;
  3. that number equals the `Gross Revenue` figure `check_warehouse.py` computes from
     its own independent SQL ([R2](#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21));
  4. the declared `reporting_currency` appears in the named Join Path;
  5. an unparseable expression **fails the run**, not skipped — C6's echo.
- **The vocabulary check happens by writing the files first.** The eight field names
  are settled against the Glossary before the loader exists, so the loader is written
  against agreed names rather than the names inventing themselves in code. Extending
  `check_language.py` to scan YAML keys would be a sixth Sub-step; instead the
  required-field list in `check_semantic_layer.py` *is* where a key name is enforced,
  and the Step Review states that limitation plainly.

**Verification:**

```bash
uv run python .claude/scripts/check_semantic_layer.py
uv run python .claude/scripts/check_warehouse.py
```

plus the mutation that gives it teeth, in the pattern Sub-step 2.6 established:
change the expression's `commission` to `rebate`, re-run, see the figure disagree
with `check_warehouse.py`'s and the run fail; restore and compare with `cmp`.

### 4.2 — Write the remaining Metric Definitions

The corpus. Eight more, [R1](#r1--cash-balance-becomes-a-certified-metric--approved-by-amino-2026-08-21)
having been approved — `Net Revenue`, `Traded Notional`, `Trade Count`,
`Account Value`, `Position Change`, `Realised P&L`, `Unrealised P&L`, and
`Cash Balance` — with the Join Paths they carry, and the `Cash Balance` Glossary row
amended in the same commit.

- Every [Section C](../glossary.md#c-distinctions-we-must-not-blur) pair in the metric
  set is asserted to return **two different numbers from the published expressions**.
  `check_warehouse.py --distinctions` already proves the *data* separates them; this
  proves the *Semantic Layer* does, which is a different claim and the one that
  matters for a corpus whose whole purpose is keeping them apart.
- `Traded Notional` carries the widening cast to `DECIMAL(38, 6)` that
  [DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)
  is about, and it *"cannot be avoided by writing the expression differently"* —
  `check_validation_feasibility.py` runs the uncast expression on every run and
  prints the engine's refusal.
- [R4](#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)'s
  pin lands here, once all three expressions the spike measured are published.
- **Coverage is stated, not implied.** The Step Review names which of the nine
  metrics execute over which tables, so a reader can see that the corpus reaches the
  Snapshot tables and the movement ledgers rather than only `fct_trade`.

**Verification:** the same two commands, plus
`uv run python .claude/scripts/check_warehouse.py --distinctions`. **This Sub-step is
not done until every Certified Metric in
[Glossary Section B](../glossary.md#b-the-warehouse) has a Metric Definition that
returns a number** — the same bar Step 002 set for the Warehouse.

### 4.3 — Pay DEBT-015: the dialect scan reads type constructs

[DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)'s
Trigger fired in 4.2. Its own words on why it could not be paid earlier:

> **there is nothing to scan yet.** No Semantic Layer exists, so no Metric Definition
> exists, and the only cast outside `veritas/warehouse/` is a Python literal in a
> spike whose whole subject is that the scan cannot see it.

Now there is. The repayment the entry specifies is *"the name list **plus** a
round-trip comparison over types"*, because the two are blind to disjoint classes:

- `check_warehouse.py`'s `check_seam` reads Metric Definition expressions from
  `semantic/` as well as the SQL `veritas/` emits, and flags dialect-shaped **type**
  constructs by comparing the parse tree before and after retargeting — the
  `round_trip_rewrites` instrument Sub-step 3.4 already measured and committed.
- [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)'s mitigation is
  reworded from *function* to *construct*, with a dated note; its status does not
  change.
- The Ledger entry is marked **paid**, with the Sub-step and date.

**Verification:**

```bash
uv run python .claude/scripts/check_warehouse.py
```

plus the mutation the entry itself names: `Traded Notional`'s cast is the construct
the name list reads as clean, so the run must **name it** where `HEAD` says nothing.
A scan that flags nothing after this change has not been paid, it has been
re-promised.

### 4.4 — Write the Ambiguous Terms

The five rows of [Glossary Section D](../glossary.md#d-ambiguous-terms) as
`semantic/ambiguous/` entries — "revenue", "volume", "balance", "P&L", "how much does
X have" — each naming the Certified Metrics it disambiguates between, using the
`disambiguates` field
[EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) already
chose.

This is the Sub-step that carries the project's central claim. ADR-0001 rejected
schema retrieval because *"it cannot represent the one fact that matters: that
'revenue' has two certified meanings"* — these five files are that fact, made
retrievable.

- `check_semantic_layer.py` gains EXT-005's fourth rule, which is one loop here and
  not the extension itself: **every metric an Ambiguous Term names must exist as a
  Metric Definition.** This is the check that would have failed had
  [R1](#r1--cash-balance-becomes-a-certified-metric--approved-by-amino-2026-08-21) gone
  the other way, which is why R1 had to be ruled before 4.2 rather than discovered
  here.

**Verification:** `uv run python .claude/scripts/check_semantic_layer.py`, plus the
mutation: point one Ambiguous Term at a metric that does not exist, see the run fail,
restore, `cmp`.

### 4.5 — Write the Dimension Definitions

The certified axes — by date, by region, by instrument type — as
`semantic/dimensions/` entries, with the columns and allowed values the
[`Dimension Definition`](../glossary.md#a-the-system) row already names.

- `check_semantic_layer.py` asserts each named column exists in the live schema and
  that its **allowed values match what the Warehouse actually holds** — a
  Dimension Definition promising four instrument types over a Warehouse holding three
  is a certified axis that lies.
- **The date axis is deliberately not a calendar boundary for Snapshot metrics**, per
  [R7](#r7--the-date-axis-defers-debt-012s-trigger-rather-than-avoiding-it--approved-by-amino-2026-08-21)
  below — and that Sub-step adds the dated status note to
  [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)
  recording the deferral, since a deferral nobody wrote down is indistinguishable from
  not having noticed.

**Verification:** `uv run python .claude/scripts/check_semantic_layer.py`, plus the
mutation: add a fourth region to the allowed values, see the run fail against the
Warehouse's three, restore, `cmp`.

### R7 — the date axis defers DEBT-012's trigger rather than avoiding it → **approved by Amino 2026-08-21**

Raised beside 4.5 rather than with the others because it is a question about one
Sub-step's content.
[DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)'s
third trigger is *"a Dimension Definition whose period boundary is a calendar date
rather than a Snapshot date"* — and 4.5 writes Dimension Definitions.

**This is a deferral, and the plan says so in those words rather than calling it
avoidance.** Writing the narrow date axis keeps the third arm unfired; it does
nothing to the other two, and they fire on their own schedule:

| Arm of the Trigger | Fires in |
|---|---|
| 1. A gold question naming a date | The Gold Question Set Step — and it cannot be dodged there, because a gold question names a date precisely when the question needs one |
| 2. The App accepting a date from a user | The App Step |
| 3. A Dimension Definition with a calendar period boundary | **Step 004**, unless 4.5 is written the narrow way |

**What deferring buys.** DEBT-012's repayment is a **Warehouse** change, not a
Semantic Layer one. Its own entry sizes it **M** and lists what moves:

> Adding a provenance column to `fct_instrument_price` changes the schema, the
> build, the Snapshot calendar, and therefore every one of the seven simulated
> tables that hangs off it.

Paying that inside the Step that authors a corpus mixes a schema migration into an
authoring Step — the same objection that deferred it out of Sub-step 2.5, where the
entry says doing it *"would have mixed a schema change into a generation change."*

**What deferring costs, and it is not nothing.** The Semantic Layer ships with a date
axis that cannot express *"Account Value at the end of Q2"* — only "as of a date the
Snapshot calendar holds". Every component above it inherits that until DEBT-012 is
paid, so the Gold Question Set Step meets the hole as a **design constraint** and not
merely as a trigger it happens to trip.

**Approved 2026-08-21: defer deliberately, and record the deferral where the next
Step will find it.** 4.5 adds a dated status note to DEBT-012 naming the narrowing, what it
costs, and the fact that arms 1 and 2 stay live — so the Step that does pay it starts
from the reasoning instead of rediscovering it. The alternative is to write the
calendar-boundary axis in 4.5 and pay DEBT-012 here, which is a Warehouse Step wearing
a Semantic Layer Step's name and would deserve to be its own Step if chosen.

---

### R8 — the route a Metric Definition carries → **decided in Sub-step 4.2, under Amino's ruling of 2026-08-22**

The [4.1 review](../reviews/step-004-semantic-layer.md#sub-step-41--publish-the-semantic-entry-format-on-one-metric-definition)
left one question open — *"`join_path` is a single name, and `Account Value` is going
to want two"* — and named three ways out without picking one, because *"deciding it
before 4.2 starts costs one file to re-edit; deciding it during 4.2 costs eight."*
Amino ruled on 2026-08-22 that it is settled **at the start of 4.2** rather than
before it. This is that settlement, written before any of the eight files.

**The question is larger than `Account Value`.** Reading all nine metrics against the
approved format before writing any of them turns one exception into a table, and the
table is what decides the shape:

| Certified Metric | The route its expression is computed over | What the approved format cannot say |
|---|---|---|
| Gross Revenue | `fct_trade` → `fct_fx_rate` | — |
| Net Revenue | `fct_trade` → `fct_fx_rate` | — |
| Traded Notional | `fct_trade` → `dim_instrument` → `fct_fx_rate` | **two** joins under one `join_path` |
| Trade Count | `fct_trade` | **no** join at all — and then nothing names the table the query starts at |
| Cash Balance | `fct_balance_snapshot` → `fct_fx_rate` | — |
| Account Value | `fct_position_snapshot` → `dim_instrument` → `fct_instrument_price` → `fct_fx_rate`, **and** `fct_balance_snapshot` → `fct_fx_rate` | three joins, and **two routes that never meet** |
| Unrealised P&L | `fct_position_snapshot` → `dim_instrument` → `fct_instrument_price` → `fct_fx_rate` | three joins |
| Realised P&L | `fct_accounting_movement` → `fct_fx_rate` | the row filter that selects `realised P&L` movements |
| Position Change | `fct_position_snapshot` | no join, and the previous Snapshot is reached from **inside** the expression |

Two more things the table does not show. `Trade Count` and `Position Change` have no
Reporting Currency at all — one is a count and one is a quantity, and
[`Reporting Currency`](../glossary.md#a-the-system) is registered as something *"every
**monetary** metric must state"*, so a non-monetary metric stating one would be
inventing a fact. And the widening cast
[DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)
is about turns out to be carried by every expression whose product overflows
`DECIMAL(18)` rather than by the one metric the Ledger predicted —
`check_semantic_layer.py` executes each of them without its cast on every run and
prints the engine's refusal, so how many there are is a reading rather than a
sentence here.

**So the three ways out are not alternatives.** `Traded Notional` forces a multi-hop
route whatever happens to `Account Value`, and `Account Value` forces a composition
whatever happens to `Traded Notional`. Picking one of the three would have left the
other hole open — which is the finding that repays reading nine metrics before
writing one.

**Decided — five changes to the Metric Definition, none to the Join Path.**

1. **`join_path` becomes `join_paths`, a list**, applied in the order written.
   `Join Path` stays exactly what
   [the Glossary](../glossary.md#a-the-system) registers — *"a certified route between
   **two** warehouse tables"* — and a metric composes several. This is the way out
   that costs no Glossary amendment; the alternative the review named, *a Join Path
   that names more than two tables*, buys nothing extra and contests a registered
   definition to get it. The name goes plural because a field holding a list and
   named in the singular is a small lie in the one file format this project retrieves
   over.
2. **`from_table` is added to the Metric Definition** — the table the query starts at,
   spelled the way the Join Path already spells it. `Trade Count` is what forces it:
   with no join, nothing else in the entry names a table. It is checked against
   `join_paths[0]` rather than trusted.
3. **`filters` is added** — the certified predicates, ANDed into the `WHERE`. This is
   not a new field so much as an unimplemented one: the
   [`Metric Definition`](../glossary.md#a-the-system) row has always said a Metric
   Definition carries *"its SQL expression, grain, **filters**, units, and the aliases
   people use for it"*, and `Gross Revenue` simply had none. `Realised P&L` has one,
   and it is the whole difference between that metric and the three other movement
   types in the same table.
   **Why not a `CASE` inside the expression.** It would work and it would need no
   field. It is rejected because the shape a generator writes for *"Realised P&L in
   2025"* is a `WHERE`, and
   [C1](../design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)
   says the certified form is *the* form — so publishing the filter as a predicate is
   publishing what the Gate will actually have to find.
4. **`reporting_currency` becomes optional**, present exactly when `unit` is `money`.
   The biconditional is checked, so the field cannot go missing from a monetary metric
   and cannot appear on a count.
5. **`derives_from` becomes load-bearing**: the Certified Metrics whose value is
   **added** to this metric's own expression. `Account Value` is *"Cash Balance plus
   all Positions marked to market"*, so its own expression marks the Positions and it
   derives the cash from `Cash Balance` — which means the certified `Cash Balance`
   expression is **reused rather than restated**, and the two can never drift apart.

**Why `Account Value` cannot be one query, demonstrated rather than asserted.** Its
two routes are rooted at two Snapshot tables that join on nothing without multiplying
rows — one is per Account per currency, the other per Account per Instrument. The near
miss is worth recording because it looks right: put the second route in a scalar
subquery inside the expression, and the whole metric is one pasteable string over one
route. It fails the period split. The subquery is not reached by a `WHERE` the
assembler puts on the outer query, so the two halves of any date range each carry the
**whole** of the marked Positions and add up to more than the unfiltered total. A
period filter has to reach both halves of a composite metric, which is exactly what
composing at the query level does and what composing inside the expression cannot.

**What this does not change.** The Join Path file format is untouched, so
`semantic/joins/` is still what the plan approved. `expression` is still pasted
verbatim and is still the whole of C1's pasteable form — a composed metric assembles
*around* two published expressions and re-derives neither. No new domain noun is
coined: `from_table` is the Join Path's own field name, `filters` is the
`Metric Definition` row's own word, and `join_paths` is the plural of a registered
term. And the re-edit lands where the ruling meant it to — **one file**,
`semantic/metrics/gross_revenue.yaml`, three lines.

**What it costs.** `derives_from` now means *added to*, which is narrower than the
word suggests and is not the relationship
[EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) had in
mind for its second rule — *"`Net Revenue` is `Gross Revenue` minus Rebate and Fee"*
is a declared identity, not a composition, and the two cannot share one field. That
entry is amended in this Sub-step to say so, so the Step that builds the coherence
checks inherits the distinction instead of discovering it. A metric that had to
**subtract** another would need a field this format does not have; none of the nine
does.

---

### R9 — Amino's four rulings on the 4.2 review → **decided 2026-08-23**

The [4.2 review](../reviews/step-004-semantic-layer.md#sub-step-42--write-the-remaining-metric-definitions)
put six things up sceptically. Amino ruled on four of them on 2026-08-23 and accepted
the other two — the `aliases` decision and the Snapshot-date period split — as written.
The rulings are recorded here rather than only in the review because a review is read
once, by the person who commits it, and a plan is read by every Sub-step that follows.

**1. `derives_from` keeps the narrow meaning R8 gave it — *added to*.** The second field
beside it is not bought now: *"the `derives_from` usage is fine for now. we'll make a
decision about it if in the future we need it to mean a more general meaning."* Nothing
is lost by waiting, because
[EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) already
holds the distinction the full MVP inherits — a declared identity is not a composition,
and the two cannot share one field. The decision arrives when a metric needs the word to
mean something this format cannot say, and none of the nine does.

**2. `Position Change`'s expression is examined when the Validation Gate is built, not
here.** The review's point stands unchanged. Every expression
[the spike traced](../reviews/step-003-validation-feasibility.md#sub-step-32--probe-whether-a-generated-query-traces-to-a-certified-metric)
is *"a flat arithmetic expression over joined columns"*; `Position Change` carries a
correlated scalar subquery with an `ORDER BY` and a `LIMIT` inside an aggregate, which is
a shape the spike never measured, and whether the Gate can trace a generated query back
to it is **not known**. Amino ruled it a question for the
Sub-step that builds the Gate: *"it'll be examined for needing more rules when we'll
build the gate."* That Sub-step inherits it as a **named place to look first**, not as an
open defect: nothing in this Step is wrong because of it, and measuring it needs the Gate
that does not exist yet. If it turns out to need a third rewrite rule, that is a
[C5](../design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)
amendment — C5 allows the Gate two rules and no more — and therefore a decision, not a
quiet addition.

**3. The two Trade-date FX routes are renamed onto the currency axis, in Sub-step 4.2.**
The review's point was that `trade_to_fx_rate_on_trade_date` and
`instrument_to_fx_rate_on_trade_date` are *"named on different axes"*: both suffixes name
the date, both dates are the same date, and what actually separates them is the
[Section C](../glossary.md#c-distinctions-we-must-not-blur) currency pair the whole
`Traded Notional` trap turns on. Amino ruled the rename in, and 4.2 does it:

| Was | Is |
|---|---|
| `trade_to_fx_rate_on_trade_date` | `trade_to_fx_rate_on_denomination_currency` |
| `instrument_to_fx_rate_on_trade_date` | `instrument_to_fx_rate_on_quotation_currency` |

**The prefix was not part of the rename, and that is a decision rather than an
oversight.** The review wrote the second name as `..._on_quotation_currency` with the
prefix elided, which reads two ways: `trade_to_…`, pairing both names under one
from-table, or `instrument_to_…`, keeping each name its own. It is `instrument_to_…`,
because **every name in `semantic/joins/` begins with its own `from_table`**, and
`route_problem` in `check_semantic_layer.py` prints the name and the `from_table` in one
sentence. Under the other reading its route error would read *"joins
'trade_to_fx_rate_on_quotation_currency', which starts at 'dim_instrument'"* — a message
that contradicts itself in the one line a reader has to trust. The review's own sentence
points the same way: the from-cue is *"true and is a weaker cue than the one that
matters"*, so what needed replacing was the weak cue, which is the suffix. If Amino meant
the other reading, it is one more file rename and one `from_table` field.

**What the rename does not fix, stated because renaming did not remove it.**
`instrument_to_fx_rate_on_snapshot_date` converts the Quotation Currency too, so
`semantic/joins/` now names three FX routes on two axes: the Trade-date pair by currency,
the Snapshot route by date. Every name is still unique on what separates it from its
nearest neighbour — currency inside the Trade-date pair, date between the two
`instrument_to_fx_rate_*` routes — but a reader who assumes one axis across the directory
will read the Snapshot route as a *different* currency, so both files now say so in a
comment. A naming rule for the directory as a whole is EXT-009's business.

**4. Nine metrics over eight Join Paths is a full-MVP question, not a slice one.** The
review observed that six of the eight Join Paths serve exactly one metric each and asked
whether the Join Path entry type is carrying less than its name suggests. Amino ruled the
concern **real** and acting on it now **premature**: *"spending time on it would be
premature optimizing and revising of the current design … this revision or optimization
belongs to the full MVP rather than the current project's slice."* That is `CLAUDE.md`'s
extension test applied exactly — the current design is *right for this scope*, and what
is missing cannot even be measured until a Warehouse has more tables than this one's ten.
Filed as
[EXT-009](../extension-register.md#ext-009--the-join-path-entry-type-at-warehouse-scale),
against the `semantic/joins/` file format as its seam.

---

## Which Debt Ledger triggers this Step fires

Checked before planning, per `planning-a-step` step 3. **One fires and is paid
inside the Step. One is in reach and is avoided by construction.**

| Entry | Trigger | This Step |
|---|---|---|
| [DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast) | The first Metric Definition carrying a cast — *"`Traded Notional`'s, in the Step that builds the Semantic Layer"* | **Fires in 4.2, paid in 4.3.** It cannot be deferred and it cannot be dodged by rewriting the expression, both of which the entry says outright |
| [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes) | A Dimension Definition whose period boundary is a calendar date | **In reach, and deliberately deferred** — [R7](#r7--the-date-axis-defers-debt-012s-trigger-rather-than-avoiding-it--approved-by-amino-2026-08-21). The narrow date axis keeps this arm unfired and leaves the other two live; 4.5 writes the deferral onto the entry |
| [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject) | The Sub-step that builds the Validation Gate | Does not fire — no Gate is built here. But this Step **writes the fields its repayment needs**: a Metric Definition that carries `join_path` and `date_column` is what lets the Gate reject `notional through the wrong currency`, and the Settlement Date probe the entry still owes |
| [DEBT-004](../debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal) · [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level) | Building the Gold Question Set | Not built here. Authoring a metric is not asking a question of it |
| [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers) · [DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews) | `README.md`, the App, or a demo script | Does not fire — `semantic/` and the Step Review are the internal record. [R3](#r3--restricted-columns-are-declared-in-the-access-profile-not-in-a-metric-definition--approved-by-amino-2026-08-21) keeps the access-control story out of this Step entirely |
| [DEBT-003](../debt-ledger.md#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope) | A requirement to hold a single bond or an option | Does not fire — the nine metrics are computed over the Instruments the Warehouse already holds |
| [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement) | The next observed framework-rule breach | Nothing planned breaks a rule; if one is observed, the entry's own instruction applies |

---

## Not in this Step

- **The Validation Gate.** [C3](../design/validation-feasibility.md#c3--the-two-parse-tree-rules-ship-together)
  through [C6](../design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)
  bind the Step that builds it, not this one. No `veritas/validation/` directory is
  created, and no Access Profile is declared —
  [R3](#r3--restricted-columns-are-declared-in-the-access-profile-not-in-a-metric-definition--approved-by-amino-2026-08-21).
  It is the **expected** Step 005, which is an expectation and not a plan: *"Never
  plan more than one Step ahead."*
- **Retrieval, and therefore embeddings and the search index.** A corpus is not a
  retriever. Nothing here is indexed, embedded or ranked, and no LLM API key is
  needed to run any command in this plan.
- **The Orchestrator, the App, Observability, Evaluation, containerization.**
  Untouched, and nothing here half-builds any of them.
- **The Gold Question Set**, and therefore DEBT-004's and DEBT-011's repayment.
- **`README.md`**, and therefore DEBT-008's and DEBT-013's.
- **[EXT-002](../extension-register.md#ext-002--semantic-layer-drift-detection) and
  [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) as
  such.** Executing every published expression against the live schema gives EXT-002's
  purpose for free — a renamed column throws — without building the drift checker,
  and 4.4 takes one of EXT-005's four rules because it is a single loop. The other
  three, and the coherence graph, stay extensions: their Readiness is *"around 50
  entries"* and this corpus is roughly twenty.
- **[EXT-003](../extension-register.md#ext-003--metric-authoring-at-scale).** Every
  entry is hand-written, which the register calls *"not merely acceptable"* but
  *"better: inspectable, diffable, and reviewable in a pull request"* at this scale.
- **A second Reporting Currency.** One exists in this slice. The format does not
  foreclose a second — it is files added, not fields changed — so this is a scope
  boundary rather than debt.
- **A test framework.** The pattern
  [R5 of Step 002](step-002-warehouse-and-ingestion.md#r5--evidence-from-check-scripts-no-pytest-this-step--approved)
  established continues: evidence comes from a committed check script that exits
  non-zero. As in Step 003 this is a proposal rather than an inherited ruling, and
  introducing pytest here would be a sixth Sub-step, which fires
  [R5](#r5--45-is-a-pre-agreed-split-point--approved-by-amino-2026-08-21)'s split point.
