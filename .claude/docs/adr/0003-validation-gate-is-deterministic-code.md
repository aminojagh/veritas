# ADR-0003 — The Validation Gate is deterministic code, not an LLM self-check

- **Status:** accepted
- **Date:** 2026-08-03
- **Decided in:** Step 001, Sub-step 1.3

## Context

Generated SQL must be checked before it executes. The Target State names five
checks: every metric expression traces to a Certified Metric, no restricted
column appears in the projection, the Access Profile predicate is present, the
scan is bounded, and the statement is read-only.

The path of least resistance in 2026 is to ask a model. A second Large Language
Model (LLM) call, a self-critique pass, or a judge prompt would take an
afternoon, needs no parser, and handles phrasings a rule-based checker would
miss. It is what most systems in this space do, and choosing otherwise needs a
reason.

The reason is the shape of the checks themselves. Three of the five are not
judgment calls at all. "Is a restricted column in the projection" is a
set-membership question over a parse tree — it has an answer, and answering it
with a probability distribution converts a decidable question into an unreliable
one. The same holds for read-only and for whether a predicate is present.

The second reason is what the checks are *for*. They exist to prevent a confident
wrong answer. An LLM asked to check LLM output shares the blind spots of the
thing it is checking: the same priors, the same pull toward a plausible reading.
A model that mistook Adjusted Close for Market Price is not the right instrument
for catching that mistake.

And a Gate that is right 97% of the time is not a governance control. The
remaining 3% is unbounded, undetectable, and adversarially reachable — a
question's own text arrives inside the SQL as comments and string literals, so
the input to the validator is partly attacker-controlled. "Probably no restricted
columns" does not satisfy anyone who needs the guarantee.

Two constraints from earlier decisions bear on this. ADR-0002 means the Warehouse
is DuckDB, which has **no policy-tag or row-level-security mechanism** to delegate
to — the Gate cannot hand access control to the engine. ADR-0001 means the
certified set is an enumerable corpus of machine-readable expressions, which is
what makes the certified-metrics-only check mechanically decidable at all.

## Decision

The Validation Gate is ordinary deterministic code operating on the generated
SQL's parse tree via **sqlglot**. **No LLM participates in the decision to allow
or reject a query.** LLM-as-judge exists in Veritas, but only in Evaluation,
where it measures answer quality after the fact and never gates execution.

## Alternatives considered

| Option | Why not |
|---|---|
| **LLM self-critique** — the generating model checks its own SQL | Cheapest to build and needs no parser. Rejected because it shares the blind spots of the generation it is checking, and because it is non-deterministic: the same query can pass and then fail, which makes both the rejection reason and any dashboard built on it meaningless. It also cannot produce the stable taxonomy of rejection reasons that "Validation-Gate rejections by reason" needs to be a real chart. |
| **A second, different LLM as validator** | The strongest alternative, and it does break the shared-blind-spot argument — a stronger model checking a weaker one's output is a legitimate and widely used pattern. Rejected anyway: it puts unbounded cost and latency on the critical path of every question; it is reachable by prompt content that arrives inside the SQL itself as comments and string literals; and it still yields a probability rather than a guarantee. For access control specifically, a probability is not a control. |
| **Regex / string matching on the SQL text** | The cheap deterministic option, and deterministic is most of what is wanted. Rejected because it is deterministic without being correct: a restricted name in a comment, a column aliased to something benign, a subquery, or a `SELECT *` that expands to include a restricted column all defeat text matching — and none of those are adversarial, they are ordinary SQL. A parse tree makes these questions answerable; a string does not. |
| **Warehouse-native enforcement** — grants, secure views, row/column policies | This is the *right* answer for access control, and it is where the full MVP goes with BigQuery policy tags. Rejected for the slice because DuckDB has no such mechanism (ADR-0002), and — importantly — it would not be sufficient even in the full MVP: no database permission system can express certified-metrics-only, which is a claim about *how* a number was derived rather than about who may read what. The Gate survives the migration for that check regardless. |
| **Validate after execution, on the result set** | Too late by construction. A restricted column has already been read and an unbounded scan has already been paid for. Post-execution checking measures; it does not gate. |

## Consequences

**What this buys us.**

- **Verdicts are reproducible and explainable.** A rejection names a rule and a
  parse-tree node, which is what makes rejection-reason monitoring a real
  Operational Measure rather than a word cloud.
- **Zero marginal cost, negligible latency.** The Gate can run on every query
  without anyone weighing whether it is worth it — and a check that is always
  affordable is a check that is always on.
- **It is testable in the ordinary way.** A rejection case is a unit test with an
  expected reason, not a flaky assertion about a model's mood.
- **Prompt injection cannot talk its way past it.** Whatever the question said,
  the parse tree either contains a restricted column or it does not.
- **It is the honest version of the project's own argument.** Veritas claims LLM
  output must be grounded and checked by something outside the model. Using an
  LLM as the checker would undercut that claim at precisely its load-bearing
  point.

**What this costs us.** Each cost is classified — *accepted*, *debt*, or
*extension* — so none of them sits here as a fact nobody acts on.

- **Every rule must be expressible as a parse-tree predicate.** Genuinely
  semantic rules — "this query is misleading", "this join fans out and
  double-counts" — cannot be written at all. The Gate is **silent** on the whole
  class of wrongness it cannot formalise, and silence is indistinguishable from
  approval to anyone reading the output.
  → **Accepted, and it is the price of the decision rather than a flaw in it.**
  The mitigation is honesty in the App: a passed Gate must be presented as
  "these specific checks passed", never as "this answer is correct". Note that
  the fan-out case is *not* actually beyond reach — it is decidable from a Join
  Path's declared grain, which is an argument for enriching the Semantic Layer
  rather than for putting a model in the Gate.
- **Coverage is only as good as a hand-written rule set.** A novel evasion is not
  caught until someone thinks of it. Determinism means it will then fail the same
  way every time, which is better than failing randomly, but it is still a miss.
  → **Accepted for the slice.** The five rules in the Target State cover the
  failures the project exists to prevent. Adversarial rule-set hardening is
  full-MVP work and belongs with real access control
  ([EXT-001](../extension-register.md#ext-001--warehouse-native-security-and-concurrency)).
- **False rejections are absolute.** A legitimate query that trips a conservative
  rule is refused with no appeal path. The honest version of that User Experience
  (UX) is a user seeing "rejected" for a question that was perfectly fine.
  → **Accepted, with a monitoring obligation.** Rejection-reason frequency is an
  Operational Measure precisely so a rule that over-rejects shows up as a spike
  rather than as silent user attrition.
- **sqlglot becomes load-bearing safety infrastructure.** Its parser coverage
  *is* the Gate's coverage: a construct it mis-parses is a construct the Gate
  mis-judges. ADR-0002 already depends on sqlglot for dialect retargeting, so a
  single third-party parser now sits under both the portability seam and the
  safety boundary.
  → **Accepted, and named rather than hidden.** The concentration is real; the
  alternative is writing a SQL parser, which would be worse in every dimension.
  Fail-closed on parse failure is what keeps the dependency from becoming a
  silent hole — see Commitments.
- **It cannot catch Semantic-Layer-to-Warehouse drift.** A metric expression that
  traces correctly to a Certified Metric whose SQL references a dropped column
  passes the Gate and then fails at execution.
  → **Extension: [EXT-002](../extension-register.md#ext-002--semantic-layer-drift-detection).**
  This is ADR-0001's residual risk surfacing here; the Gate is the wrong place to
  fix it, because the defect is in the Semantic Layer rather than in the query.

**What it commits us to.**

- **The rule set stays enumerable and parse-checkable.** The signal that this has
  stopped holding: a proposed rule that can only be phrased as a question about
  intent. The answer then is a new Semantic Layer constraint or a new Evaluation
  Measure — not an LLM inside the Gate.
- **sqlglot parses everything Veritas generates.** A parse failure on generated
  SQL must be treated as a **rejection, never a pass** — the Gate fails closed.
  If parse failures become common, the Gate has stopped covering the system and
  the coverage claim must be withdrawn rather than explained away.
- **LLM-as-judge stays out of the execution path.** It measures; it does not
  gate. The signal: any proposal to let a judge's score influence whether a query
  runs.

## Related

- ADR-0001 — certified-metrics-only is decidable only because the Semantic Layer
  makes the certified set an enumerable, machine-readable corpus.
- ADR-0002 — DuckDB has no policy-tag mechanism to delegate access control to,
  which is why the Gate carries it; both ADRs rest on sqlglot.
- Glossary: `Validation Gate`, `Access Profile`, `Certified Metric`,
  `Shadow Metric`, `Grounded Answer`, `Evaluation Measure`, `Operational Measure`
  — all already `agreed`; this decision introduced no new terms.
- [Target State](../design/target-state.md) — Non-goals: "Validate with an LLM.
  The Validation Gate is code. An LLM asked to check its own SQL shares its own
  blind spots."
