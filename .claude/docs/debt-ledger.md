# Debt Ledger

Every knowingly-taken shortcut in Veritas, recorded at the moment it was taken.

This is not a wishlist and not a bug tracker. It is the record of places where
we chose speed over correctness **on purpose**, so that choice stays visible and
reversible. See the `recording-debt` skill.

**Every entry has a Trigger** — the condition that forces repayment. Debt
without a Trigger is a wish.

**Status:** `open` · `paid` (with the Sub-step that paid it) · `accepted`
(deliberately permanent — with the reason) · `superseded` (the code it described
no longer exists) · `moved` (it was never debt — it belongs in the
[Extension Register](extension-register.md); the stub stays so the identifier is
never reused).

**Debt or extension?** If the current code is *wrong, cheaply*, it is debt and
belongs here with a Trigger. If the current code is *right for this scope* and
the full system simply needs more, it is an extension and belongs in the
[Extension Register](extension-register.md) with a Readiness condition. The test
that settles most cases: **does the trigger fire inside this project's life?**
A trigger that can only fire after Veritas becomes something else is a wish.

---

## Index

| ID | Title | Size | Trigger | Status |
|---|---|---|---|---|
| [DEBT-001](#debt-001--framework-rules-rely-on-discipline-not-enforcement) | Framework rules rely on discipline, not enforcement | M | A rule is broken in practice | open |
| [DEBT-002](#debt-002--market-prices-depend-on-an-unofficial-endpoint) | Market prices depend on an unofficial endpoint | S | Before any reproducibility claim in `README.md` | open |
| [DEBT-003](#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope) | No Market Price vendor, so single bonds and options are out of scope | L | Any requirement to hold a single bond or an option | open |
| [DEBT-004](#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal) | The FX-date distinction is too small to be a reliable evaluation signal | S | Building the Gold Question Set | open |
| [DEBT-005](#debt-005--moved-to-ext-002) | Nothing detects Semantic Layer drift from the Warehouse | M | — | moved → [EXT-002](extension-register.md#ext-002--semantic-layer-drift-detection) |
| [DEBT-006](#debt-006--no-ad-hoc-exploration--accepted-permanently) | No ad-hoc exploration | — | — | **accepted** (permanent) |
| [DEBT-007](#debt-007--moved-to-ext-003) | Metric authoring does not scale beyond a hand-written corpus | L | — | moved → [EXT-003](extension-register.md#ext-003--metric-authoring-at-scale) |
| [DEBT-008](#debt-008--the-access-control-story-promises-more-than-it-delivers) | The access-control story promises more than it delivers | S | Any access-control claim in `README.md` or the App | open |
| [DEBT-009](#debt-009--the-seam-scan-checks-imports-but-not-the-dialect) | The seam scan checks imports but not the dialect | S | The first component outside the adapter emits SQL | open |
| [DEBT-010](#debt-010--movement_type-has-no-registered-value-vocabulary) | `movement_type` has no registered value vocabulary | S | The first Cash Movement row is generated | **paid** (Sub-step 2.1) |

**Open debt:** 6 · **Paid:** 1 · **Accepted:** 1 · **Moved:** 2

DEBT-005 through DEBT-008 were opened by Sub-step 1.3 and resolved by Amino's
review on 2026-08-04, which is why three of the four are no longer open debt:

- **005 and 007 moved to the [Extension Register](extension-register.md).** Both
  describe a slice that is *right for its scope* and a full system that needs
  more — that is an extension, not a shortcut. The entries stay here as stubs so
  the identifiers are never reused and existing links keep resolving.
- **006 accepted permanently.** Ad-hoc exploration is not a gap; Veritas is a
  metrics copilot, not a database browser.
- **008 narrowed** to the part that can actually fire inside this project. Its
  original first trigger — *before any real client data is loaded* — cannot fire
  here, because Veritas has no real client data by construction. The engineering
  work moved to [EXT-001](extension-register.md#ext-001--warehouse-native-security-and-concurrency);
  what remains is a claim-honesty debt, which is small, real, and firing soon.

---

## Entries

<!--
Copy this template for each new entry. Keep entries in ID order.

### DEBT-001 — <short title>

- **Status:** open
- **Opened:** Sub-step N.M (`.claude/docs/reviews/step-NNN-<slug>.md`)
- **Size:** S | M | L  (S ≈ under an hour, M ≈ half a day, L ≈ a Step of its own)
- **Location:** `path/to/file.py:42` — or the component name if it is diffuse

**What we did**
The shortcut, concretely. Someone reading this in two months must be able to
find the code without archaeology.

**What we should have done**
The correct approach, specifically enough to act on. Not "do it properly".

**Why we deferred**
Usually "not needed for this slice" — but say *why* it was not needed, because
that reasoning is what expires.

**Cost while unpaid**
What is worse because of this. What is blocked. What breaks, and for whom.
If nothing is worse, this is not debt — delete the entry.

**Trigger**
The condition that forces repayment. Prefer observable conditions over dates:
"before any real customer data is loaded", "when the corpus exceeds 5k
documents", "if retrieval latency exceeds 2s". This is the most important
field in the entry.
-->

### DEBT-001 — Framework rules rely on discipline, not enforcement

- **Status:** open
- **Opened:** Sub-step 0.1 (`.claude/docs/reviews/step-000-framework-scaffolding.md`)
- **Size:** M
- **Location:** `CLAUDE.md` (the four non-negotiables), `.claude/skills/*`

**What we did**

Wrote the framework as instructions Claude is asked to follow. Nothing mechanical
stops any of it being skipped: Claude could commit despite "Amino commits", ship
a Sub-step with no Step Review, take a shortcut without a Ledger entry, or put an
unregistered term in a column name. `.claude/scripts/verify_framework.py` checks that the
framework's *documents* are wired together — it cannot check that the framework
was *followed*.

**What we should have done**

Enforce the mechanical subset with hooks in `.claude/settings.json`:

- `PreToolUse` on `Bash(git commit*)` — block, since Amino commits.
- `PostToolUse` on Write/Edit — warn when a source file changes but
  `current-state.md` has not, within the same Sub-step.
- A `Stop` hook running `verify_framework.py`.

Judgement-dependent rules (is this a shortcut? is this term a domain noun?)
cannot be hooked and will always rest on discipline.

**Why we deferred**

The framework is untested. Enforcing rules before knowing which ones survive
contact with real work would harden guesses — several of these rules will
probably turn out to be wrong or annoying, and hooks make them expensive to
change. Discipline first, mechanism once the rules have proven themselves.

**Cost while unpaid**

Compliance decays as sessions get long and context gets summarised — exactly when
care matters most and is least available. The failure is silent: a missing Ledger
entry looks identical to no debt having been taken. This directly threatens the
premise of the whole framework, which is that the record can be trusted later.

**Trigger**

The first time any framework rule is observed to have been broken in practice —
a shortcut found during a Step Review that was not on the Ledger, a missing
review section, a commit made by Claude, or an unregistered term found in code.
One occurrence is enough; do not wait for a pattern.

**🔴 Trigger fired — Sub-step 1.3, 2026-08-03.** Amino ruled in Sub-step 1.2 that
verification evidence must come from a committed script, because "pasted output
is a transcription I could get wrong and nobody could re-run". Sub-step 1.3's
review then pasted the output of two throwaway inline scripts, one of which
duplicated a check `verify_framework.py` already performs. The rule was written
down, agreed, and broken one Sub-step later — which is exactly the decay this
entry predicted, and it was caught by Amino reading the review rather than by any
mechanism.

**Partial payment, same Sub-step:**

- `.claude/scripts/check_language.py` — mechanises Non-Negotiable #1: Target
  State component names must be registered Glossary terms, `proposed` terms must
  not appear in code identifiers, and every abbreviation must be expandable from
  the Glossary. **Its coverage is narrower than the rule.** It reads component
  names from the Target State's Components table only, so a domain noun that
  becomes a directory, a column, or a class without appearing in that table is
  not checked. And judgement-dependent parts — *is this word a domain noun?* —
  cannot be mechanised at all. The checker closes the gap that produced this
  Sub-step's finding; it does not close the rule.
- `CLAUDE.md` Non-Negotiable #4 gained two clauses — *evidence comes from a
  committed script* and *citations quote* — and `closing-a-substep` gained the
  rationalizations that produced this failure.

**Still unpaid:** the hook layer. Nothing mechanically blocks a commit by Claude,
a missing Ledger entry, or a review that skips a section. The trigger having
fired once, the next occurrence should buy the hooks rather than another
document rule.

---

### DEBT-002 — Market prices depend on an unofficial endpoint

- **Status:** open
- **Opened:** Sub-step 1.2 (`.claude/docs/reviews/step-001-target-state-design.md`)
- **Size:** S
- **Location:** design-level — `.claude/docs/design/data-availability.md` §3; will
  become the market-price ingestion pipeline

**What we did**

Chose Yahoo's `query1.finance.yahoo.com/v8/finance/chart` endpoint as the source
of Market Prices, because it is the *only* key-free option that still works.
Stooq — the obvious documented-CSV alternative — now serves a JavaScript anti-bot
challenge instead of data, and every properly-supported vendor (Alpha Vantage,
Tiingo, EODHD, Polygon, Finnhub, Twelve Data, Nasdaq Data Link) requires
registration, which fails the rubric's key-free reproducibility criterion.

The endpoint is undocumented and unversioned. It carries no stability guarantee
and no terms permitting this use.

**What we should have done**

Either license a supported market-data vendor, or accept an API-key dependency
and document the signup as a prerequisite. Both were rejected: the first costs
money for a capstone, the second breaks the one-command reproducible bring-up
that is worth 2 rubric points.

**Why we deferred**

The mitigation is cheaper than the fix and strictly better for reproducibility:
**snapshot the fetched prices into the repository** and have ingestion read the
snapshot by default, with an explicit refresh flag to re-fetch. A reviewer
cloning the repo then gets identical data whether or not Yahoo is alive — which
is a *stronger* reproducibility story than live-fetching from any source. The
live endpoint is then only needed to refresh the snapshot, not to run Veritas.

Not doing that work now because no ingestion code exists yet; this Sub-step was
a design gate, not a build.

**Cost while unpaid**

Until the snapshot exists, the project is one silent upstream change away from
having no market data at all — and the failure would land during the ingestion
Step or, worse, during a reviewer's clone. Every Position mark, Account Value,
and P&L figure depends on this one source.

**Trigger**

Whichever comes first:

1. The market-price ingestion pipeline is written — the snapshot lands in the
   same Sub-step, not after it.
2. Any reproducibility claim is made in `README.md`.
3. The endpoint returns a non-200 for a symbol in the traded universe.

---

### DEBT-003 — No Market Price vendor, so single bonds and options are out of scope

- **Status:** open
- **Opened:** Sub-step 1.2 (`.claude/docs/reviews/step-001-target-state-design.md`)
- **Size:** L
- **Location:** the `Instrument` definition in `.claude/docs/glossary.md`

**What we did**

Narrowed the `Instrument` Glossary term — an already-`agreed` term — from
"equity, ETF, bond, future, option, or currency pair" to "equity, ETF, future, or
currency pair", because no key-free source provides Market Prices for single
bonds or options. Probed and recorded in
`data/snapshots/probe-results.json`: HTTP 404 for bonds by ISIN and by CUSIP,
HTTP 401 for the option chain. Bond exposure is now represented through bond
ETFs (TLT, BNDX), which do have Market Prices.

**What we should have done**

Subscribe to a market-data vendor that covers fixed income and listed
derivatives — the realistic options are paid (Refinitiv, Bloomberg, ICE, or at
the cheaper end Polygon or EODHD with a fixed-income add-on) — and model single
bonds and options as first-class Instruments, with their own price series,
accrued-interest handling, and option greeks.

**Why we deferred**

A paid vendor cannot be a dependency of a capstone that must be reproducible
from a `git clone` with no credentials; it would forfeit the reproducibility
criterion outright. The narrowing costs Veritas little, because none of the
Certified Metrics or Section-C distinctions require a bond or an option to be
demonstrated — they are exercised fully by equities, ETFs, futures and FX.

**Cost while unpaid**

Veritas cannot answer any question about a client's single-bond or option
holdings, and cannot model the two behaviours those instruments uniquely
introduce: accrued interest between coupon dates, and non-linear exposure.
A real brokerage has both, so this is the largest single gap between Veritas and
the system it is a slice of. It is also the gap most likely to be noticed by a
domain reviewer.

**Trigger**

Whichever comes first:

1. Any requirement to hold a single bond or an option appears — in the full-MVP
   scope, in the Gold Question Set, or in a stakeholder question.
2. `check_data_availability.py` reports that bonds or options have become
   obtainable key-free. The script probes them on every `--refresh` precisely so
   this ruling cannot go stale unnoticed.

---

### DEBT-004 — The FX-date distinction is too small to be a reliable evaluation signal

- **Status:** open
- **Opened:** Sub-step 1.2 (`.claude/docs/reviews/step-001-target-state-design.md`)
- **Size:** S
- **Location:** `.claude/scripts/check_data_availability.py` (the `NOTE` emitted by
  `run_join_spike`); the Trade Date / Settlement Date row of Glossary Section C

**What we did**

Accepted a Section-C distinction that the data does not currently make
measurable. The Glossary says choosing Trade Date over Settlement Date "moves the
number twice" — once by shifting the period, once by selecting a different FX
Rate. The second move measured **0.08%** in the spike: real, but small enough to
disappear into rounding.

**What we should have done**

Chosen the spike window deliberately rather than for convenience — a period of
genuine FX volatility, or instruments in a more volatile Quotation Currency —
so the distinction produces a difference no plausible wrong answer could
reproduce by accident.

**Why we deferred**

The spike's job was to prove the sources *join*, and it did. Choosing an
evaluation window is properly the evaluation Step's decision, and making it now
would be guessing at requirements that do not exist yet.

**Cost while unpaid**

This is the dangerous kind of debt, because the failure is invisible: an
Execution Accuracy check on an FX-date question would score a **wrong answer as
correct**, since the wrong number sits inside tolerance. Veritas would then
report high accuracy on precisely the distinction it claims to exist for. The
measure would be lying, and nothing would look broken.

**Trigger**

When the Gold Question Set is built. Any gold question that turns on Trade Date
versus Settlement Date must be constructed over a window where the two FX Rates
differ by more than the result comparison's tolerance — or that question must be
left out and the limitation stated. Do not add the question and hope.

---

### DEBT-005 — moved to EXT-002

- **Status:** `moved` → [EXT-002 — Semantic Layer drift detection](extension-register.md#ext-002--semantic-layer-drift-detection)
- **Opened:** Sub-step 1.3 · **Moved:** 2026-08-04, on Amino's review

Recorded here first as debt, then reclassified. Nothing detects that a Metric
Definition's SQL expression still refers to columns that exist in the Warehouse.

**Why it was not debt.** The slice has one author and one schema, authored once
and never migrated, so drift has no opportunity to occur. The current state is
not a shortcut — it is correct for this scope. The full system, with real
migrations, needs the check. That is an extension.

The identifier is retained so it is never reused and existing links resolve.
---

### DEBT-006 — No ad-hoc exploration — accepted permanently

- **Status:** `accepted` — deliberately permanent
- **Opened:** Sub-step 1.3 · **Decided:** 2026-08-04 by Amino
- **Location:** design-level — the third cost in
  [ADR-0001](adr/0001-semantic-layer-as-the-retrieval-corpus.md)

**The decision**

Veritas does not answer schema questions. "What columns are in `fct_trade`?",
"what instrument types do we hold?" and "show me ten rows" have no path to an
answer, and that is final rather than pending.

**The reason**

*Veritas is a metrics copilot, not a database browser.* Retrieval runs over
Semantic Entries; the schema is deliberately not in the corpus. Anyone wanting to
explore the schema can open the Warehouse directly, which is the honest tool for
that job.

Two options were weighed and both rejected: a separate, clearly-labelled
exploration mode, and schema as its own Semantic Entry type. The second is the
more dangerous precisely because it is the more integrated — once schema sits in
the same corpus as Metric Definitions, the model can compose them, and "revenue"
gets computed from `commission` directly. That is the Shadow Metric failure
arriving through the front door.

**What this closes**

Nothing further is expected. This entry is kept because a permanent decision
recorded as a decision is more useful than an absence, and because the
alternatives are worth having on record for anyone who proposes them again. The
matching non-goal is stated in the
[Target State](design/target-state.md#non-goals).
---

### DEBT-007 — moved to EXT-003

- **Status:** `moved` → [EXT-003 — Metric authoring at scale](extension-register.md#ext-003--metric-authoring-at-scale)
- **Opened:** Sub-step 1.3 · **Moved:** 2026-08-04, on Amino's review

Recorded here first as debt, then reclassified. Every Semantic Entry is a
hand-written YAML file and every change rebuilds the retrieval index.

**Why it was not debt.** At tens of metrics, hand-authoring is not a shortcut —
it is the better choice, being inspectable, diffable and reviewable in a pull
request, which is what makes "certified" mean anything. It stops scaling at the
hundreds of metrics a real brokerage warehouse holds. Right for this scope, and
the full system needs more: an extension.

The identifier is retained so it is never reused and existing links resolve.
---

### DEBT-008 — The access-control story promises more than it delivers

- **Status:** open
- **Opened:** Sub-step 1.3 · **Narrowed:** 2026-08-04, on Amino's review
- **Size:** S
- **Location:** `README.md` (not yet written) and the App's rendering of the
  Validation Gate outcome
- **Engineering half:** moved to
  [EXT-001](extension-register.md#ext-001--warehouse-native-security-and-concurrency)

**What we did**

Built — will build — an access-control demonstration that is genuinely weaker than
its name suggests, and have not yet committed to saying so.

The Access Profile is enforced by the Validation Gate in application code: the
Gate inspects the parse tree, refuses restricted columns in the projection, and
requires the Access Profile's predicate to be present. DuckDB has no policy-tag
mechanism to delegate to ([ADR-0002](adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)),
so this is the only enforcement point.

Application-layer enforcement protects **exactly one path**. Anything reaching
the Warehouse another way — a notebook, a debugging session, a future component
that forgets to route through the Gate — bypasses it completely, and the engine
hands over every row to anyone who connects.

**Why this is the debt and the engineering is not**

The original entry made *before any real client data is loaded* its first trigger.
That trigger **cannot fire inside this project**: Veritas has no real client data
by construction, and none is planned. A trigger that can only fire after the
project becomes something else is a wish, which is what the Ledger's own rule
forbids. The engineering work therefore belongs in the Extension Register, and
what stays here is the part that fires soon and for real — **the honesty of the
claim.**

**What we should have done**

Say precisely what is true, in `README.md` and wherever the App reports the
Validation Gate outcome:

> Access Profile enforcement is applied in the application layer, over synthetic
> data. It demonstrates the mechanism; it is not a production access control, and
> it does not protect the Warehouse from being read another way.

**When EXT-001 lands, the application-layer check is removed, not retained.**
Warehouse-native row- and column-level security *replaces* it rather than adding
to it. Two enforcement points for one rule is two places to keep in sync, two
places to drift, and the weaker one supplies false assurance about the stronger
one's coverage — so the redundancy is a liability, not defence-in-depth. The
warehouse becomes the single authority.

One consequence to plan for rather than discover: the Gate currently rejects an
access violation *before execution*, with a specific reason that feeds the
rejection-reason Operational Measure. Engine enforcement fails at execution with
a database error instead. If that signal is worth keeping, keep a **non-enforcing**
pre-flight check — but label it a user-experience affordance, never access
control.

**Cost while unpaid**

Nothing is technically worse; the data is synthetic and there is nothing to leak.
The cost is entirely in what a reader is allowed to conclude. "Access Profile
enforcement" in a README, unqualified, invites a grader or a future reader to
believe a guarantee exists that does not — and the project's whole argument is
that a confident, well-formatted overstatement is the failure worth preventing.
Making that mistake in our own documentation, about our own governance, would be
the sharpest possible own goal.

**Trigger**

The first access-control claim made anywhere a reader will see it: `README.md`,
the App, or a demo script. Whichever comes first — and it will come during the
App Step, not at the end.

---

### DEBT-009 — The seam scan checks imports but not the dialect

- **Status:** open
- **Opened:** Sub-step 2.1 (`.claude/docs/reviews/step-002-warehouse-and-ingestion.md`)
- **Size:** S
- **Location:** `.claude/scripts/check_warehouse.py` — `duckdb_importers` and
  `check_seam`

**What we did**

Implemented half of the signal ADR-0002 named. That ADR commits that all warehouse
access goes through the adapter, and says the signal that it has stopped holding
is *"a `duckdb` import **or a DuckDB-specific function name** anywhere outside the
adapter module"*. `check_seam` scans imports only. A module that never imports
`duckdb` but writes `list_aggregate(...)` or `strftime(...)` into a query string
passes the check while breaking exactly the commitment the check exists to
protect.

The clarification added to ADR-0002 on 2026-08-05 says of this script that it
"performs that scan, so the commitment is checked on every run rather than
asserted in a review" — which is currently true of the import half and not of the
function-name half.

**What we should have done**

Scan string literals in every module outside `veritas/warehouse/` for
DuckDB-specific function names, with the list derived from something that can go
stale honestly — sqlglot already knows which functions belong to which dialect,
and the sqlglot spike adds sqlglot as a dependency for unrelated reasons. That
spike was Sub-step 2.4 when this entry was written; R16 moved it to a future
Step 003 on 2026-08-10, which delays the cheap version of this scan but does not
change what it should do.

**Why we deferred**

There is nothing to scan. No module outside the adapter emits SQL yet, because no
Semantic Layer and no Orchestrator exist. Writing the scan now would mean writing
a dialect list against zero examples and having it pass vacuously — the same
failure mode `check_seam` already guards against for imports, where it fails the
run if *nothing* imports duckdb.

**Cost while unpaid**

A reader of `check_warehouse.py`, or of ADR-0002's clarification, can reasonably
conclude the adapter commitment is mechanically enforced. It is enforced against
the coarse half of the signal. The finer half — the one that actually leaks a
dialect assumption into generated SQL — is still discipline, which is precisely
what [DEBT-001](#debt-001--framework-rules-rely-on-discipline-not-enforcement)
records goes quiet under pressure.

**Trigger**

The first component outside `veritas/warehouse/` that emits SQL — the Semantic
Layer's first Metric Definition expression, or the Orchestrator's first generated
query, whichever lands first. The scan is written in the same Sub-step as the
thing it has to scan, so it is written against real examples.

---

### DEBT-010 — `movement_type` has no registered value vocabulary

- **Status:** **paid** — Sub-step 2.1, 2026-08-06, in the same Sub-step that opened
  it and before a single row was written
- **Opened:** Sub-step 2.1 (`.claude/docs/reviews/step-002-warehouse-and-ingestion.md`)
- **Size:** S
- **Location:** `veritas/warehouse/schema.sql` — `fct_cash_movement.movement_type`
  and `fct_accounting_movement.movement_type`

**What we did**

Gave both movement tables a `movement_type` column with no `CHECK` constraint and
no registered value set, while the schema's three other enumerated columns —
`client_region`, `instrument_type`, `trade_side` — each carry a constraint listing
values the Glossary agreed. The asymmetry is deliberate and it is a shortcut.

The Glossary's `Cash Movement` row does enumerate them in prose — *"deposits,
withdrawals, settlement, fee charges"* — so the words exist; what does not exist
is agreement on their exact spelling as data, which is the thing a constraint
would freeze.

**What we should have done**

Raised a Term Proposal for the movement-type value set alongside the three raised
in this Sub-step, agreed the spellings, and constrained both columns the same way
the other three are constrained.

**Why we deferred**

Nothing consumed the values at the time. No Certified Metric named then — Gross
Revenue, Net Revenue, Traded Notional, Cash Balance, Account Value — sliced by
movement type; the Section C pair these tables exist for is *Cash Movement versus
Accounting Movement*, which is a table-level distinction, not a type-level one.
Agreeing a value vocabulary against zero consumers means guessing at requirements
that do not exist, which is the reasoning that kept the fourth Term Proposal off
the list rather than an oversight.

**That reasoning no longer holds. Amended 2026-08-06**, on Amino's review of the
snapshot design. Walking every Certified Metric against the ten tables asked where
`Realised P&L` — *"profit or loss locked in by closing a Position"* — is computed
from, and the answer is this column. It is a value recognised on a date, which is
what `Accounting Movement` is registered to hold: *"a ledger entry recognising
economic value on the date it was earned, whether or not cash moved."* So a
`movement_type` value **is** the home of a registered metric, and this entry is
load-bearing rather than cosmetic. It stays open and stays `S` — the fix is still
one Term Proposal and two `CHECK` constraints — but the vocabulary must now cover
realised P&L explicitly, and a metric depends on getting the spelling right rather
than only a tidy `GROUP BY`.

**Cost while unpaid**

The column is the one place in the star schema where a simulator can write
`'Deposit'` on one row and `'deposit'` on the next and nothing objects. That is a
small version of exactly the disease this project is about: two spellings of one
concept, silently splitting a `GROUP BY` into two rows that each look plausible.
Since the amendment above, the cost is larger than tidiness: a realised-P&L
posting spelled two ways is a P&L metric that under-reports, with no error
anywhere.

**Trigger**

Sub-step 2.5 — numbered 2.3 when this entry was written, renumbered by R16 on
2026-08-10 — when the simulator generates the first Cash Movement or Accounting
Movement row. The values become real at that moment, so the proposal is raised
before the generator is written, not after — otherwise the vocabulary is decided
by whichever string got typed first.

**How it was paid**

Amino's instruction on 2026-08-06 was *"if that 'if' is a bad one, make sure it
won't happen — don't leave these cases hanging hoping that they will get fixed."*
The "if" was that Sub-step 2.5 might pay this debt without noticing that
`Realised P&L` now depends on it. Recording the dependency in a third place would
have been one more thing to hope someone reads, so the debt was paid instead:

Both columns now carry a `CHECK`, and the two lists **differ**, which is the point:

| Table | Permitted `movement_type` |
|---|---|
| `fct_cash_movement` | `deposit` · `withdrawal` · `trade settlement` · `commission` · `fee` · `rebate` |
| `fct_accounting_movement` | `commission` · `fee` · `rebate` · `realised P&L` |

`realised P&L` is accounting-only — no cash moves when a Position closes, the cash
moved at settlement — and `deposit` is cash-only, because a deposit earns nothing.
That asymmetry is the Section C pair *Cash Movement vs Accounting Movement* made
structural instead of remembered, and three probes in `check_warehouse.py` hold it
there: the two cross-table refusals, and `'Deposit'` refused for its capital D,
which is the exact spelling failure this entry was opened for.

The trigger above can no longer fire: 2.5's simulator cannot write a movement row
at all without using an agreed spelling, and cannot give `Realised P&L` no home
without the engine refusing the insert.

**Term Proposal — the spellings, for Amino to amend if he disagrees.** These are
data values rather than Glossary terms, and the words themselves were already
agreed — the `Cash Movement` row enumerates *"deposits, withdrawals, settlement,
fee charges"*. What is new is their spelling as data: lowercase with spaces,
following `instrument_type`'s *"currency pair"* and `trade_side`'s *"buy"*, with
`realised P&L` keeping its registered capitalisation the way `ETF` does. Changing
any of them is a one-line edit in `schema.sql` while the tables are empty; it stops
being free once 2.5 has loaded rows.
