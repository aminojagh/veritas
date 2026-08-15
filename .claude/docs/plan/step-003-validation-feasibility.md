# Step 003 — Prove the Validation Gate's parse-tree claim

- **Status:** **active** — written 2026-08-15 and **approved by Amino the same
  day**, together with every ruling in [Rulings](#rulings). Sub-step 3.1 may begin
  once this plan is committed. **The Step has five Sub-steps rather than the four
  it was approved with**: [R3](#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15)
  was widened from the new script to *every* exemption, which is one commit of its
  own and lands first. [R5](#r5--34-is-a-pre-agreed-split-point--approved-by-amino-2026-08-15)
  pre-agrees where the Step splits if it grows.
- **Goal:** Answer, with a committed script run against the real schema and the
  real data, whether sqlglot can decide **from a parse tree alone** that a
  generated query computes a Certified Metric and nothing else — and record the
  go/no-go on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)
  before any Validation Gate or Semantic Layer code exists.
- **Moves Current State by:** replacing the project's largest unproven assumption
  with a measured, re-runnable finding, and adding
  `.claude/docs/design/validation-feasibility.md` beside
  [`data-availability.md`](../design/data-availability.md) as the second design
  gate. **No component row turns from `✗ none` to working**, which is the honest
  description of a spike: the movement is in what is known, not in what is built.

## Why this Step

**1. It is the Step already agreed, and its text is already written.**
[R6](step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
fired on 2026-08-10 and moved the spike out of Step 002 with its wording
preserved: *"Its text is preserved under Not in this Step so Step 003's plan
starts from it rather than from memory."* This plan starts from
[that text](step-002-warehouse-and-ingestion.md#deferred-to-step-003--prove-the-validation-gates-parse-tree-claim)
and changes none of its four questions. What it adds is decomposition,
verification, and the three things the intervening Sub-steps changed.

**2. It is the largest remaining uncertainty, and it is unmoved.** The Step 001
review's handoff, quoted in Step 002's plan, says:

> **`sqlglot` is load-bearing and unproven here.** The Validation Gate's whole
> claim — deterministic, parse-tree-level checks — rests on being able to trace
> generated SQL expressions back to Certified Metrics. I believe this works but
> have not built it. It is the single highest-risk assumption in the design, so
> Step 002 should touch it early rather than leave it to the end.

Step 002 did not touch it. It is still the single highest-risk assumption, and
two ADRs now rest on the same library: ADR-0003 puts sqlglot under the safety
boundary, ADR-0002 puts it under the portability seam.

**3. Everything the spike was waiting for now exists.** The preserved text says
it must be answered *"using the real schema from 2.1 and the real data from
2.5"*. Both are committed: ten tables, every Certified Metric computable, and
`uv run python .claude/scripts/check_warehouse.py --distinctions` printing every
Section C pair as two different numbers. Its first bullet — `uv add sqlglot` — is
already done, in Sub-step 2.6, which needed the library for the dialect scan.

**4. It gates a design, not just an implementation, so it must come before the
Semantic Layer.** The Gate's tracing rule decides what a Metric Definition has to
carry. If a certified expression is only recognisable when the generated query
reproduces it verbatim, then the Semantic Layer must publish a form the
Orchestrator can paste and the Gate can match — which is a constraint on the file
format, on grounding, and on what "certified" means in code. Discovering that
after the corpus is authored is a repaint of a seam; discovering it now costs one
script. **A no-go on claim 1 or 3 is a real possible outcome and would be the most
valuable thing this Step produces**, which is the preserved text's own position.

## Why a spike is allowed to be a Step

`CLAUDE.md` requires that a Step be *"a vertical slice — it must leave the project
working end-to-end, not half-wired."* This Step ships no component, and that is
worth stating rather than glossing.

It satisfies the rule in the sense the rule is about: **nothing is left half-wired.**
The pipeline, the Warehouse and all four check scripts run exactly as they do
today, before and after every Sub-step; the new script is additive and exits
non-zero on its own terms. What it does not do is make Veritas answer a question
it could not answer before — no Step can, until the Semantic Layer and the
Orchestrator exist, and the argument above is that those are cheaper to build
after this answer than before it.

There is precedent in this repository, and it was the same shape of decision:
Sub-step 1.2 built no component either, and the reason it was worth a Sub-step is
the reason this is worth a Step — *"the least code that answers the question, plus
a committed script so the answer can be re-run."*

## What the four claims mean, concretely

Restated from the preserved text with what counts as an answer, because a spike
whose success condition is written after the run is not a gate.

| # | Claim | Answered when |
|---|---|---|
| **1** | **Tracing.** A certified expression stays recognisable in a generated query's parse tree under aliasing, a subquery, and a common table expression | One function decides *traces / does not trace* for every shape, and the verdict on each shape is printed. A shape that fails is a finding, not a failure — the Step's output is the boundary, wherever it falls |
| **2** | **Restricted columns.** A Restricted Column can be found when it arrives via `SELECT *`, or aliased to a benign name | The same, plus the two cases ADR-0003's rejection of string matching turns on: a restricted name in a comment or string literal must **not** trip the check, and the column must be caught when only its alias is visible in the projection |
| **3** | **The Shadow Metric it must catch.** A query computing revenue inline from `commission` instead of drawing on the certified expression is rejected, and the two queries return **different numbers** against the real Warehouse | The check rejects it, and both queries are executed through the Warehouse Adapter and their results printed side by side. The difference is what makes the rejection worth having |
| **4** | **Dialect retargeting.** A generated statement round-trips DuckDB → BigQuery through sqlglot without losing meaning | Every statement shape the spike traces is transpiled to BigQuery, re-parsed, and put through claim 1's tracer again. Where meaning is lost, the construct is named. **Data Definition Language (DDL) is out of scope** — [R3 of Step 002](step-002-warehouse-and-ingestion.md#r3--hand-authored-ddl-inside-the-adapter--allowed-with-the-reasoning-written-down) already settled that it is hand-authored per engine |

**The certified expressions the spike traces are real ones, not toy ones.** A
tracer proved against `sum(commission)` proves nothing about the metric Veritas
will actually certify: `Gross Revenue` is registered as *"Σ(Commission) before any
Rebate or pass-through Fee is deducted"*, and every monetary metric must state a
`Reporting Currency`, so the honest expression joins `fct_fx_rate` and converts
out of each Trade's `Denomination Currency`. The spike uses that shape — one
Reporting Currency, conversion on `trade_date`, both choices stated in the script
and in the findings — because a parse tree with a join and a conversion in it is
the tree the Gate will actually see.

## How the five Sub-steps divide the work

One rule landed first, then one new script grown one claim at a time, then the
document that rules on it.

```
.claude/scripts/     ← 3.1   scan exemptions scoped to the file they live in — R3 widened
                     ← 3.2   certified-metrics-only: does a certified expression survive?   (claims 1 and 3)
                     ← 3.3   Restricted Columns: can one hide behind SELECT * or an alias?   (claim 2)
                     ← 3.4   dialect retargeting: where does DuckDB → BigQuery stop?         (claim 4)
.claude/docs/design/ ← 3.5   validation-feasibility.md — the findings and the go/no-go
```

Every one passes the sizing test with a conjunction-free commit subject, and every
adjacent pair passes `planning-a-step`'s test for splitting — **Amino could
reasonably approve one and reject the next**:

| Pair | The independent failure |
|---|---|
| 3.1 / 3.2 | 3.1 changes a check that exists and touches no new ground; 3.2 creates the spike. Rejecting the tightened exemption does not stop the tracer being written, and rejecting the tracer does not put the loophole back |
| 3.2 / 3.3 | Tracing is a claim about *expressions*; Restricted Columns is a claim about *identifiers reaching a projection*. One can work while the other does not, and they have different fixes — a verbatim-form constraint versus schema-aware expansion |
| 3.3 / 3.4 | Retargeting is ADR-0002's claim, not ADR-0003's. A Gate that works perfectly on DuckDB and a transpiler that drops a window function are unrelated results |
| 3.4 / 3.5 | The findings document states a verdict. Amino can accept every measurement and reject the conclusion drawn from it — which is the whole reason the go/no-go is not folded into the Sub-step that produces the last number |

**The claims are ordered by what a no-go would cost.** Claim 1 is the one ADR-0003
rests on, so it is first among them: if it fails, 3.3 and 3.4 are still worth
having but the Step's conclusion is already written, and Amino can stop the Step
at 3.2 rather than paying for two more Sub-steps to reach a verdict he already
has.

**A split point, pre-agreed** —
[R5](#r5--34-is-a-pre-agreed-split-point--approved-by-amino-2026-08-15). Five
Sub-steps is `planning-a-step`'s ceiling, so there is no room for review-driven
growth — and Step 002 grew twice. If it grows here, the Sub-step to leave is
**3.4**: it answers ADR-0002's claim rather than ADR-0003's, and 3.5 can return a
go/no-go on the parse-tree claim without it, saying so.

## Rulings

Four questions were put to Amino with this plan and **all four were approved on
2026-08-15**. R3 was approved *and widened*, which is why the Step has five
Sub-steps. R5 records the split point offered alongside them, approved the same
day.

### R1 — Term Proposal: `Restricted Column` → **approved by Amino 2026-08-15**

> 🆕 **TERM PROPOSAL** — `Restricted Column`: a column an Access Profile forbids
> from appearing in a Grounded Answer's projection.

Raised because Sub-step 3.3 gives it a code identifier, and Non-Negotiable #1
requires the name to clear the Glossary before that happens. The words are already
used in three `agreed` documents — the Glossary's own `Validation Gate` row says
*"no restricted columns"*, the Target State's flow says *"no restricted column in
the projection"*, and ADR-0003 uses the phrase in its
[context](../adr/0003-validation-gate-is-deterministic-code.md#context), in two of
its [rejected alternatives](../adr/0003-validation-gate-is-deterministic-code.md#alternatives-considered)
and in its [consequences](../adr/0003-validation-gate-is-deterministic-code.md#consequences)
— so this registers existing usage rather than coining vocabulary.

**Registered in Glossary Section A in Sub-step 3.3**, the Sub-step that first uses
it, with `check_language.py` passing over it from then on.

### R2 — the spike's certified expressions stay Python literals → **approved by Amino 2026-08-15**

The tracer needs certified expressions to trace. Writing them as
`semantic/metrics/*.yaml` would fix the Semantic Layer's file format — a seam
three Extension Register entries land against — inside a spike, which is the
opposite of *draw contour lines, not scaffolding*. Step 002's plan is explicit
that the format deserves better:

> A seam that load-bearing deserves a Step where it is the subject, not a fifth
> Sub-step appended after three days of ingestion work.

So the expressions live as literals in `check_validation_feasibility.py`, the
script says in its own words that they are probe inputs rather than a corpus, and
the Semantic Layer's format stays unfixed until the Step whose subject it is. **No
debt entry**, because nothing is left wrong — a spike input is not a shortcut
version of a seam.

### R3 — an exemption names the file as well as the symbol → **approved and widened by Amino 2026-08-15**

The question asked was narrow: `check_seam` scans `.claude/scripts/` as well as
`veritas/`, so the new script's SQL literals are read by the dialect scan Sub-step
2.6 built, and claim 4 may need deliberately DuckDB-specific SQL. The proposal was
to keep every literal in the new script portable, transpile *from* the statements
3.2 and 3.3 already build, and — if a dialect-specific literal proves unavoidable
— say so in the Step Review and make the exemption name the file as well as the
tuple, rather than taking the existing exemption silently by naming a tuple
`DIALECT_PROBES`.

**Amino approved it and widened it to every exemption, not only this one.** The
rule, in its general form:

> An exemption is scoped to where it is needed. A check that excuses something
> names the **file** and the **symbol** it excuses, never a symbol alone — an
> exemption claimable by writing a magic name is a hole any later file can walk
> through. An unavoidable exemption is stated in the Step Review that takes it.

The rule has one existing instance to bring into line, which is what Sub-step 3.1
is. `check_warehouse.py`'s `DIALECT_PROBES` exemption is keyed on the assignment
name alone and is file-agnostic, so any scanned file can claim it by choosing that
name — including the one this Step adds. Its own docstring already states the cost
honestly (*"SQL put in a tuple by that name, in a scanned file, is invisible
here"*), which is what made the hole findable; the rule now says the cost should
not be paid at all where it is avoidable.

### R4 — Step 003 is the spike alone; the Semantic Layer is Step 004 → **approved by Amino 2026-08-15**

The alternative was folding the Semantic Layer into this Step behind an R6-style
pre-agreed split point. Rejected for two reasons: Step 002's plan already ruled
that the Semantic Layer deserves a Step where it is the subject, and the spike's
own findings are an input to that Step's design — a Sub-step that authored Metric
Definitions would be written before 3.5 decided what a Metric Definition must
carry.

The cost is stated plainly: **Step 003 is small**, and it ends with the same nine
component rows Step 002 ended with.

### R5 — 3.4 is a pre-agreed split point → **approved by Amino 2026-08-15**

Offered with the four questions rather than asked as one, and approved with them.
Five Sub-steps is `planning-a-step`'s ceiling, so if review-driven growth arrives
in 3.1–3.3, **3.4 becomes Step 004** rather than being squeezed into an over-full
Step, and 3.5 returns its go/no-go on the parse-tree claim with the retargeting
claim named as unanswered. It leaves rather than 3.5 because it answers ADR-0002's
claim and not ADR-0003's.

Agreed in advance for
[R6](step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)'s
reason: the option should be on the table before the Step starts rather than
offered at review, when it is already too late to have cost nothing.

## Sub-steps

### 3.1 — Scope every scan exemption to the file it lives in

Lands [R3](#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15)
in the one place it currently applies, **before** this Step adds a new file to a
scanned root. Nothing about the spike is touched.

- `check_warehouse.py`'s fixture exemption becomes a `(file, symbol)` pair rather
  than a bare symbol: `DIALECT_PROBES` is exempt **in `check_warehouse.py`** and
  nowhere else. The docstring says so, and says what the exemption still costs
  inside that file, because the narrowing removes the loophole and not the cost.
- The rule itself goes into `CLAUDE.md`, under Non-Negotiable #4, where a check
  with a hole in it is the same species of problem as a claim without evidence.
  Flagged when this plan was presented, because `CLAUDE.md` is the operating
  agreement and this is Claude editing it; **approved by Amino 2026-08-15** with
  the rest of the plan.
- A sweep of the other three check scripts for exemptions of the same shape, with
  the result reported in the Step Review. `check_language.py`'s two lists — the
  abbreviations it leaves alone, and the uppercase tokens it knows are not
  abbreviations at all — are a different species: they name *what* is excused from
  inside the checker, and no scanned file can claim them by choosing a name. So the
  expectation going in is that nothing else changes. The sweep is
  reported either way, since "we looked and found nothing" is the finding.

**Verification:**

```bash
uv run python .claude/scripts/check_warehouse.py
```

plus the mutation that proves the narrowing has teeth: put a tuple named
`DIALECT_PROBES` holding DuckDB-specific SQL into `veritas/ingestion/simulator.py`,
re-run, see it **named** where before it would have been exempt, restore and
compare with `cmp`. The pattern Sub-step 2.6 established.

### 3.2 — Probe whether a generated query traces to a Certified Metric

Creates `.claude/scripts/check_validation_feasibility.py` with the tracer and
claims 1 and 3. They are one Sub-step because they are one rule seen from both
sides: the certified query must trace, the Shadow Metric must not. A tracer that
only ever says *yes* is the vacuous pass
[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect)
was opened about, so the negative case ships with the positive one.

- A small set of certified expressions held as **Python literals in the script**,
  per [R2](#r2--the-spikes-certified-expressions-stay-python-literals--approved-by-amino-2026-08-15):
  `Gross Revenue`, `Net Revenue` and `Traded Notional`, each converted to one
  Reporting Currency through `fct_fx_rate`.
- The tracer: parse, qualify against the real schema read through
  `WarehouseAdapter.columns`, and decide whether each projected expression matches
  a certified one.
- Claim 1's shapes, each printed with its verdict: bare, aliased, inside a
  subquery, inside a common table expression, and with commuted operands
  (`commission - rebate - fee` against `commission - fee - rebate`) — the last
  because it is where "recognisable" stops being obvious and starts being a design
  constraint.
- Claim 3: `Gross Revenue`'s certified expression against revenue computed inline
  from `fct_trade.commission`. Both are executed through the adapter and the two
  numbers printed. The Sub-step 2.5 review measured Gross against Net at 32.59%
  apart on the currently loaded data; the script prints what the difference is on
  the data in front of it rather than repeating that figure.
- Exits non-zero if a shape that must trace does not, or if the Shadow Metric
  traces.

**Verification:**

```bash
uv run python -m veritas.ingestion            # the Warehouse is gitignored
uv run python .claude/scripts/check_validation_feasibility.py
uv run python .claude/scripts/check_warehouse.py
```

The third is not decoration: `.claude/scripts/` is inside `check_seam`'s
`CODE_ROOTS`, so the new script's SQL literals are scanned by the check Sub-step
2.6 built and tightened by 3.1. It must still pass, and under R3 it must pass
**without claiming an exemption**.

### 3.3 — Probe whether a Restricted Column can hide from the parse tree

Adds claim 2, and registers `Restricted Column` in the Glossary per
[R1](#r1--term-proposal-restricted-column--approved-by-amino-2026-08-15) — in this
Sub-step because this is the one that gives it a code identifier.
`dim_client.client_name` is the Restricted Column the probe uses.

ADR-0003 rejected string matching on exactly this ground, and the rejection is
currently an argument rather than a measurement:

> a restricted name in a comment, a column aliased to something benign, a
> subquery, or a `SELECT *` that expands to include a restricted column all
> defeat text matching — and none of those are adversarial, they are ordinary SQL

Each of those becomes a probe with a printed verdict: direct projection (caught),
`SELECT *` over a join that reaches `dim_client` (caught, which needs the schema
rather than the text), aliased to `name` (caught), the name inside a comment and
inside a string literal (**not** caught — a false positive here is the failure),
and the column used only in a `WHERE` clause (**not** caught: the Target State's
rule is *"no restricted column in the projection"*, and a filter on a column
nobody reads is a different question that this Step does not widen into).

Exits non-zero if any verdict is wrong in either direction.

**Verification:** as 3.2, plus `check_language.py` for the new Glossary row, plus
the mutation that proves the teeth — remove the schema-aware expansion, watch the
`SELECT *` probe stop being caught, restore, and compare byte-for-byte.

### 3.4 — Probe DuckDB → BigQuery retargeting on the SQL Veritas will generate

Adds claim 4, which belongs to [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)
rather than ADR-0003. That ADR concedes transpilation is *"good but not total"*;
this measures where it stops on the shapes we actually intend to generate.

- Every statement 3.2 and 3.3 built is transpiled DuckDB → BigQuery, re-parsed in
  the BigQuery dialect, and run through the tracer again. A statement whose
  certified expression stops tracing after the round trip is named.
- It also answers a question DEBT-009 left open in writing: *"whether it needs
  transpilation-level checking instead is a question Step 003's spike answers with
  its fourth claim"*. If a transpile-and-compare test is strictly better than the
  name list `check_seam` uses, that is a finding with a home — a Ledger entry
  against the existing scan, opened in 3.5.
- No DDL, per R3 of Step 002.

**Verification:** as 3.2.

### 3.5 — Record the go/no-go on ADR-0003's parse-tree claim

Writes `.claude/docs/design/validation-feasibility.md` in the shape of
[`data-availability.md`](../design/data-availability.md): how to reproduce it,
a verdict per claim, the findings, and rulings — ending in an explicit **go** or
**no-go** on ADR-0003.

- A dated status note on ADR-0003 either way. A go records that its central bet
  was measured rather than assumed; a no-go opens the amendment or supersession,
  which is `writing-an-adr` work and would make the Semantic Layer Step wait on it.
- Any constraint the findings place on the Semantic Layer or the Orchestrator is
  written here, because the next Step is where it has to be obeyed.
- Every figure is dated evidence with the command that reproduces it, per the
  [writing conventions](../../../CLAUDE.md#writing-conventions).
- Any shortcut the probes took gets its Ledger entry now rather than later.

**Verification:**

```bash
uv run python .claude/scripts/verify_framework.py
uv run python .claude/scripts/check_language.py
```

## Which Debt Ledger triggers this Step fires

Checked before planning, per `planning-a-step` step 3. **None fire, and one is
avoided by construction rather than by luck.**

| Entry | Trigger | This Step |
|---|---|---|
| [DEBT-004](../debt-ledger.md#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal) · [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level) | Building the Gold Question Set | Not built here. The spike's queries are probes, not gold questions: nothing scores an answer against them |
| [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes) | The first "as of" date chosen by anything but the Snapshot calendar | **Avoided deliberately.** No probe query names a date literal. Where one needs a date it reads it from `fct_position_snapshot`, so every date still comes from the calendar itself and the hole stays unreachable |
| [DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers) | The first access-control claim a reader will see — `README.md`, the App, a demo script | Does not fire: `validation-feasibility.md` is the internal working record, not the public face. It states the limitation anyway, in the words the entry already drafted, so the eventual README has something to copy rather than compose |
| [DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect) | Paid in 2.6 | Not re-opened, and 3.1 is not a re-payment: the scan does what the entry required, and what R3 narrows is the exemption beside it. Claim 4 may produce a **new** entry about the scan's name-based boundary |
| [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement) | The next observed framework-rule breach | Nothing planned breaks a rule. If one is observed during the Step, the entry's own instruction is that the next occurrence buys the hooks |

## Not in this Step

- **The Validation Gate itself.** This is the feasibility gate for it, not a thin
  version of it. No `veritas/validation/` directory is created; a spike that
  quietly becomes the component is how the answer stops being falsifiable.
- **The Semantic Layer** — [R4](#r4--step-003-is-the-spike-alone-the-semantic-layer-is-step-004--approved-by-amino-2026-08-15).
  It is the expected Step 004, and this plan does not write it, because *"Never
  plan more than one Step ahead."*
- **The Orchestrator, Retrieval, the App, Observability, Evaluation,
  containerization.** Untouched, and nothing here half-builds any of them.
- **The Gold Question Set**, and therefore DEBT-004's and DEBT-011's repayment.
- **`README.md`**, and therefore DEBT-008's repayment.
- **A test framework.** The pattern
  [R5 of Step 002](step-002-warehouse-and-ingestion.md#r5--evidence-from-check-scripts-no-pytest-this-step--approved)
  established continues — evidence comes from a committed check script that exits
  non-zero. R5 was scoped to Step 002, so this is a proposal rather than an
  inherited ruling: if pytest should arrive, this is a reasonable Step to introduce
  it in, and it would be a sixth Sub-step — which `planning-a-step` reads as two
  Steps, so it would take the split point above with it.
- **Access-control enforcement.** Claim 2 measures whether a Restricted Column can
  be *found* in a parse tree. What Veritas then does about it is the Gate's
  behaviour, and belongs with the Gate.
