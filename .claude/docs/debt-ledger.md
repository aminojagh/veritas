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
| [DEBT-002](#debt-002--market-prices-depend-on-an-unofficial-endpoint) | Market prices depend on an unofficial endpoint | S | Before any reproducibility claim in `README.md` | **paid** (Sub-step 2.3) |
| [DEBT-003](#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope) | No Market Price vendor, so single bonds and options are out of scope | L | Any requirement to hold a single bond or an option | open |
| [DEBT-004](#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal) | The FX-date distinction is too small to be a reliable evaluation signal | S | Building the Gold Question Set | open |
| [DEBT-005](#debt-005--moved-to-ext-002) | Nothing detects Semantic Layer drift from the Warehouse | M | — | moved → [EXT-002](extension-register.md#ext-002--semantic-layer-drift-detection) |
| [DEBT-006](#debt-006--no-ad-hoc-exploration--accepted-permanently) | No ad-hoc exploration | — | — | **accepted** (permanent) |
| [DEBT-007](#debt-007--moved-to-ext-003) | Metric authoring does not scale beyond a hand-written corpus | L | — | moved → [EXT-003](extension-register.md#ext-003--metric-authoring-at-scale) |
| [DEBT-008](#debt-008--the-access-control-story-promises-more-than-it-delivers) | The access-control story promises more than it delivers | S | Any access-control claim in `README.md` or the App | open |
| [DEBT-009](#debt-009--the-seam-scan-checks-imports-but-not-the-dialect) | The seam scan checks imports but not the dialect | S | The first component outside the adapter emits SQL — **🔴 fired** | **paid** (Sub-step 2.6) |
| [DEBT-010](#debt-010--movement_type-has-no-registered-value-vocabulary) | `movement_type` has no registered value vocabulary | S | The first Cash Movement row is generated | **paid** (Sub-step 2.1) |
| [DEBT-011](#debt-011--execution-price-against-market-price-cancels-at-book-level) | Execution Price against Market Price cancels at book level | S | Building the Gold Question Set | open |
| [DEBT-012](#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes) | The price table is sparse, so the Snapshot calendar has holes | M | The first "as of" date chosen by anything but the Snapshot calendar | open |
| [DEBT-013](#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews) | The decisions that move a number live only in internal reviews | M | The final documentation pass, before peer review | open |
| [DEBT-014](#debt-014--the-spike-allows-a-query-the-gate-must-reject) | The spike allows a query the Gate must reject | S | The Sub-step that builds the Validation Gate | open |
| [DEBT-015](#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast) | The dialect scan names functions, and the loss measured was in a cast | S | The first Metric Definition carrying a cast | open |
| [DEBT-016](#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type) | The Semantic Layer check cannot name the engine's error type | S | The first component outside `.claude/scripts/` that handles a failed query | open |

**Open debt:** 10 · **Paid:** 3 · **Accepted:** 1 · **Moved:** 2

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

**Second coverage gap, found in Sub-step 3.2 on 2026-08-18 — a document link inside
code is checked by nobody.** Amino ruled that a reference to a project document made
from *inside code* is written as a resolvable markdown link rather than as prose, so
that the final documentation pass can find every internal `.claude/docs/` link and
swap it for a user-facing one. `verify_framework.py`'s `check_links` resolves links
and their anchors in `.claude/docs/**/*.md` and `CLAUDE.md` only, so the links carried
in `.claude/scripts/*.py` — `check_warehouse.py` and `check_validation_feasibility.py`
both carry them — rest entirely on somebody remembering to look, which is this entry's
subject exactly. The fix is one glob wider in `check_links`, plus a decision about
what a link inside a `.py` file may point at. **It must be paid before the final
documentation pass** ([DEBT-013](#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews)),
because that pass works from the set of links a checker can enumerate: a docstring
link that has rotted by then is invisible at the one moment it is being read. It is
recorded here rather than as an entry of its own because it is not a new species of
problem — it is this one, in a place no mechanism reaches yet.

**That second gap was paid in Sub-step 4.1, 2026-08-21.** `check_links` now reads
every `.py` file under `veritas/` and `.claude/scripts/` alongside the documents, and
resolves the same two halves — the file and the `#anchor` — reported as the same two
problems. The decision the gap said was owed, about *what a link inside a `.py` file
may point at*: **the same thing a link inside a document may point at, resolved the
same way** — relative to the file that carries it, with its anchor required to exist.
Nothing about a citation changes because it is sitting in a docstring, and a second
rule for code would be a second thing to remember. The Sub-step that paid it was the
one that added sixteen more such links, and the check found a dead one in its own
explanatory docstring on its first run.

**Third occurrence — Sub-step 4.2, 2026-08-23, and it is the cheapest possible kind.**
While closing the Sub-step, Claude ran a bare `python3` heredoc to edit a file, and then
did it a second time, against `CLAUDE.md`'s *"Always `uv run python …` — never bare
`python`/`python3`, not even for a throwaway one-liner in a shell pipeline."* **Nothing
downstream is wrong** — both were text substitutions that produce the same bytes under
either interpreter, and the checks that ran afterwards ran under `uv run python` and
passed. That is the entry's point rather than a mitigation of it: the breach is invisible
in the diff, no mechanism noticed, and it is on this Ledger only because the party that
broke the rule chose to report it. It is also the single framework rule that a
`PreToolUse` hook on `Bash` matches with a regular expression and no judgement at all.

**Still unpaid:** the hook layer. Nothing mechanically blocks a commit by Claude, a
missing Ledger entry, or a review that skips a section. **The entry's own escalation is
now due**: after the first occurrence it said *"the next occurrence should buy the hooks
rather than another document rule"*, and the next occurrence has happened. Sub-step 4.2
did **not** buy them — the Sub-step was already closing when the breach was reported, and
adding a hook layer to a commit is a Sub-step of its own rather than a line in this one.
That is Amino's call to schedule, and it is recorded here so the decision is a decision
rather than a drift.

---

### DEBT-002 — Market prices depend on an unofficial endpoint

- **Status:** **paid** — Sub-step 2.3, 2026-08-10, under trigger 1
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

**Status note, Sub-step 2.2 (2026-08-10) — still open, and the trigger has not
fired.** Trigger 1 names the *market-price* pipeline, which is Sub-step 2.3.
What 2.2 built is the mechanism and the snapshot: `veritas/ingestion/snapshots.py`
replays by default, and `data/snapshots/ingestion/` now holds a Yahoo chart
response for all sixteen traded Instruments. 2.2 reads only the `meta` block of
those files — see [ADR-0004](adr/0004-snapshot-and-replay-and-where-dlt-stops.md)
— so the price series is loaded, and this debt paid, one Sub-step later. The
mitigation landing *before* the pipeline is the ordering the trigger wanted; the
condition it guards against, a pipeline existing with no snapshot behind it,
cannot now occur.

**Paid, Sub-step 2.3 (2026-08-10).** Trigger 1 fired — *"the market-price
ingestion pipeline is written"* — and the snapshot did land in the same Sub-step,
because 2.2 had already put it there. `veritas/ingestion/sources.py` reads the
`timestamp` and `indicators` blocks of the nineteen committed chart responses,
`veritas/warehouse/builds/fct_instrument_price.sql` turns them into 9,549 Market
Prices, and no socket is opened on the way: `uv run python -m veritas.ingestion`
builds the whole Warehouse from a clean clone with the network off. The endpoint
is now needed only to *refresh* the snapshot, never to run Veritas — which is the
mitigation this entry was opened to buy, and it is stronger than the fix it stood
in for, because it survives the endpoint disappearing rather than merely surviving
it changing.

**What paying it does not buy, stated so nobody reads more into it than is
there.** The dependency is mitigated, not removed. Three things stay true:

- **Triggers 2 and 3 are still live.** `README.md` does not exist yet, so the
  reproducibility claim trigger has not fired; when it does, what the README may
  say is *"reproducible from committed snapshots"*, not *"reproducible from
  Yahoo"*.
- **A refresh can still fail, and a stale snapshot is silent.** Nothing detects
  that a committed snapshot no longer matches what the source would return —
  recorded as an accepted cost in
  [ADR-0004](adr/0004-snapshot-and-replay-and-where-dlt-stops.md) rather than as
  new debt, because the data is historical and a stale 2025 window is still a
  correct 2025 window.
- **The window is fixed at two years by `YAHOO_RANGE`.** Widening it needs the
  endpoint alive. That is a refresh-time dependency, which is exactly where this
  entry wanted the dependency to end up.

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

- **Status:** **paid** — Sub-step 2.6, 2026-08-13, as its own commit, under the
  trigger Amino ruled had fired the same day
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

**Status note, Sub-step 2.2 (2026-08-10) — the trigger came close and did not
fire, deliberately.** Ingestion needed SQL to build `dim_instrument` from `raw`,
which would have made `veritas/ingestion/` the first component outside the adapter
to emit it. It lives in `veritas/warehouse/builds/dim_instrument.sql` instead,
hand-authored and run through `WarehouseAdapter.run_build`, which is where R4 puts
it anyway: *"the adapter executes the SQL that builds the star schema from it."*
One draft of `check_warehouse.py --sources` did interpolate a table name into a
`count(*)` string; it was replaced with `WarehouseAdapter.row_count`, which reaches
`raw` through the relational API and assembles no text. So after this Sub-step
there is still no component outside `veritas/warehouse/` emitting SQL, and the
scan would still pass vacuously.

**Status note, Sub-step 2.5 (2026-08-11) — the trigger's wording is now the
question, not the code.** The seven new build scripts sit in
`veritas/warehouse/builds/` like the three before them, and none of them uses a
DuckDB-specific name at all — they are projections and casts. So the *dialect*
half of this entry is exactly where it was.

What 2.5 makes impossible to keep saying is that no component outside the adapter
emits SQL. Two do: `veritas/ingestion/__main__.py` has held SELECT text since 2.2,
and `veritas/ingestion/simulator.py` reads the three real star tables through the
adapter in 2.5. Both are standard SQL — no dialect name, nothing assembled from a
value — which is why earlier Sub-steps read the trigger as meaning *dialect* SQL
and reported it unfired. That reading is defensible and it is not what the trigger
says. **Amino's call:** reword the trigger to name the first dialect-specific
construct outside the adapter, or accept that it has fired and the scan is owed.
Recorded rather than decided, because narrowing a trigger to keep an entry unfired
is the failure this Ledger exists to prevent.

Repayment did get cheaper, for a reason worth recording: **`sqlglot` is now an
installed dependency**, pulled in transitively by dlt (`sqlglot==30.15.0`). The
repayment plan above assumed it would arrive with the Validation Gate spike, which
[R6](plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
has since moved to Step 003. It is available now regardless.

**🔴 Trigger fired — Amino's ruling, 2026-08-13.** The question this entry put to
him was whether to reword the trigger or accept that it had fired. **He accepted
that it has fired, and the scan is owed.** The trigger is not narrowed: two modules
outside `veritas/warehouse/` hold SQL text, which is what the sentence says, and
rewriting the sentence to keep the entry unfired is the move Non-Negotiable #2
exists to prevent.

**Scheduled, not deferred.** Payment is
[Sub-step 2.6](plan/step-002-warehouse-and-ingestion.md#r21--debt-009-has-fired-and-is-paid-as-sub-step-26--ruled-by-amino-2026-08-13) —
after Sub-step 2.5 is committed and **before Step 003 is planned**, on Amino's
instruction that the two land as separate commits. The entry stays `open` until
that Sub-step is verified; a debt marked paid before the code exists is the
bookkeeping this Ledger is supposed to make impossible.

What 2.6 owes, from *What we should have done* above: a scan of the SQL text in
every module outside `veritas/warehouse/` for DuckDB-specific function names, with
the dialect list derived from `sqlglot` rather than typed by hand. It now has real
examples to run against — `veritas/ingestion/__main__.py` and
`veritas/ingestion/simulator.py` — so it can be shown to pass on standard SQL and
to fail on a dialect name, which is the mutation test that stops it passing
vacuously.

**✅ Paid — Sub-step 2.6, 2026-08-13.** `check_seam` now runs both halves of
ADR-0002's signal. The dialect half reads every string literal sqlglot parses as a
SQL statement, in every module outside `veritas/warehouse/`, and names any function
call in it that standard SQL does not have. The name list is
`DuckDB.Parser.FUNCTIONS - Parser.FUNCTIONS`, taken from sqlglot at import, so it
tracks the library rather than someone's memory of DuckDB's manual. `sqlglot` was
promoted from a transitive dependency of dlt to a declared one in the same
Sub-step, because a check that imports it is a direct dependant of it.

**It was proved rather than asserted, twice over.** Three probes run on every run —
standard SQL comes back clean, `strftime` is named as DuckDB's, `list_aggregate` is
named as one sqlglot knows nowhere — and the run fails if any probe reads wrong, so
the scan cannot quietly lose its teeth. On top of that, both real modules were
mutated with a dialect name and the run was made to fail on each, then restored and
compared byte-for-byte. Output in the
[Step Review](reviews/step-002-warehouse-and-ingestion.md#sub-step-26--scan-for-duckdb-specific-function-names-outside-the-adapter).

**What the scan does not cover**, stated here so nobody reads the entry as
promising more than it does. It sees SQL a module has *written down*; SQL assembled
at run time is not a literal and is invisible to it, which is a boundary rather
than a gap — generated SQL is the Validation Gate's subject, and
[ADR-0003](adr/0003-validation-gate-is-deterministic-code.md) inspects a parse tree
at run time precisely because no static scan can. And it is exactly as good as
sqlglot's own dialect tables: a name sqlglot files as dialect-neutral passes even
where it is not in the SQL standard, `generate_series` being the example this
project already uses. That boundary is deliberate — a hand-typed list is what this
entry rejected, because it goes stale in silence — and whether it needs
transpilation-level checking instead is a question
[Step 003's spike](plan/step-002-warehouse-and-ingestion.md#deferred-to-step-003--prove-the-validation-gates-parse-tree-claim)
answers with its fourth claim, on DuckDB → BigQuery retargeting.

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

---

### DEBT-011 — Execution Price against Market Price cancels at book level

- **Status:** open
- **Opened:** Sub-step 2.5 (`.claude/docs/reviews/step-002-warehouse-and-ingestion.md`)
- **Size:** S
- **Location:** `veritas/ingestion/simulator.py` — `MIN_EXECUTION_DRIFT` and
  `MAX_EXECUTION_DRIFT`; the `Execution Price` / `Market Price` row of Glossary
  Section C

**What we did**

Generated Execution Prices that sit either side of the day's close, drawn
symmetrically, and accepted what that does to the pair in aggregate. Every Trade
individually is priced away from the close — `check_warehouse.py --distinctions`
prints how many and by how much — but summing a whole book of them cancels the
difference almost exactly, so Traded Notional valued at Execution Price and the
same notional valued at the close come out nearly equal.

This is the same failure mode as
[DEBT-004](#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal),
on a different Section C row, and it is filed separately because the two have
different causes and different fixes. DEBT-004 is about a window with too little
FX movement in it; this is about an aggregation that cancels a symmetric quantity.

**What we should have done**

Nothing different in the simulator. A fill is above the close as often as below —
that is what Section C's own wording says, *"a Trade fills at whatever the market
gave it at that moment, which is not the close except by coincidence"* — and
introducing a systematic bias so that a book-level total diverges would be shaping
the data to pass our own check. The real half-spread on these instruments is one
to five basis points, which would not move the aggregate either.

The gap is in **what a gold question may ask**, not in the data.

**Why we deferred**

The Gold Question Set does not exist yet, and the shape of the fix belongs to it:
a question turning on this pair has to be scoped to one Account, one Instrument or
one day, where the difference is the full per-Trade size rather than the residue
of a cancellation. Deciding that now would be guessing at requirements that do not
exist.

**Cost while unpaid**

Identical in shape to DEBT-004's, and worth restating because it is the dangerous
kind: a gold question that asks for book-level Traded Notional and accepts an
answer computed at the close would score a **wrong answer as correct**, because
the wrong number is inside any plausible tolerance. Veritas would report accuracy
on a distinction it did not actually make.

**Trigger**

When the Gold Question Set is built. Any gold question turning on Execution Price
against Market Price must be scoped narrowly enough that the two differ by more
than the result comparison's tolerance — the per-Trade figures are printed by
`uv run python .claude/scripts/check_warehouse.py --distinctions` — or the
question must be left out and the limitation stated.

---

### DEBT-012 — The price table is sparse, so the Snapshot calendar has holes

- **Status:** open
- **Opened:** Sub-step 2.5 (`.claude/docs/reviews/step-002-warehouse-and-ingestion.md`),
  on Amino's approval of the intersection calendar (2026-08-13)
- **Size:** M
- **Location:** `veritas/warehouse/builds/fct_instrument_price.sql` (the table is
  sparse per Instrument) and `veritas/ingestion/simulator.py` — `snapshot_dates`
  in `read_market_data` (which narrows the Snapshot calendar in consequence)

**What we did**

Wrote a Snapshot on the dates **every** Instrument has a Market Price, rather than
the dates **some** Instrument does. That choice is right and is approved: on a date
the union includes and the intersection does not, some exchange was shut, so a
Position in an Instrument listed there has no Market Price and an Account Value
containing it would be silently short by a holding. The argument is in the
[Sub-step 2.5 review](reviews/step-002-warehouse-and-ingestion.md#the-decision-this-sub-step-had-to-make-which-dates-a-snapshot-is-written-on).

**The shortcut is one layer below that choice, and it is what this entry records.**
`fct_instrument_price` is sparse: it holds a row only on the dates an Instrument's
own exchange traded. Given a sparse price table the intersection is the only safe
calendar, so the dates on which some markets traded and some did not carry no
Snapshot at all. `--sources` prints both counts on every run:

```
$ uv run python .claude/scripts/check_warehouse.py --sources
    calendars: N dates have a price for at least one Instrument · M have one for all …
```

The figures for the currently committed window are dated evidence in the
[same review](reviews/step-002-warehouse-and-ingestion.md#the-decision-this-sub-step-had-to-make-which-dates-a-snapshot-is-written-on).

**What we should have done**

Make the price table dense, so that the intersection and the union are the same
set and the choice above stops being a choice. Concretely: fill
`fct_instrument_price` forward across every date any Instrument traded, and carry
a column saying whether a row is a close the exchange actually printed or one
carried from the previous session. Marking a holding at the last available close
on a day its own market was shut is what portfolio valuation does; what makes it
safe rather than a stale number is that the row says which it is, so a metric can
exclude carried rows and a Lineage can name them.

This is the shape `fct_fx_rate` already has. Sub-step 2.4 stored rates densely
over calendar dates precisely so that no metric downstream has to fill forward for
itself, and the review's own argument against a stale mark — *"it would have to be
re-derived by every future metric"* — is an argument for storing the fill once,
not for dropping the date. Two tables in one Warehouse answering "what was true on
D" by opposite conventions is the incoherence worth removing.

**Why we deferred**

Sub-step 2.5's job was the client side, and the intersection made every Position
markable on the day it was chosen — the pipeline refuses to complete otherwise, so
nothing silent is riding on it. Adding a provenance column to
`fct_instrument_price` changes the schema, the build, the Snapshot calendar, and
therefore every one of the seven simulated tables that hangs off it; doing that
inside the Sub-step that first filled them would have mixed a schema change into a
generation change.

**Cost while unpaid**

**An "as of" question about one of the missing dates has no answer, and the
absence looks like a zero.** Every Snapshot-grain metric — Cash Balance, Account
Value, Unrealised P&L, Position Change — is an equality join on `snapshot_date`,
which is the property `Snapshot` is registered for. On a date the calendar skips,
that join returns no rows, and *no rows* is exactly what an Account holding
nothing returns. A user asking what a Client was worth on a date the Tokyo
exchange was shut gets silence or a zero rather than "that date is not in the
Snapshot calendar", which is the wrong-number-with-a-plausible-explanation this
project exists to prevent.

Two smaller consequences follow from the same hole: a period filter whose boundary
lands on a missing date silently uses a different boundary, and a Position Change
across one is attributed to the next Snapshot date.

**Trigger**

The first "as of" date that is chosen by anything other than the Snapshot calendar
itself. In practice, whichever of these lands first:

1. A gold question naming a date — the Gold Question Set is where a date gets
   picked for a reason unrelated to which dates happen to exist.
2. The App accepting a date from a user.
3. A Dimension Definition whose period boundary is a calendar date rather than a
   Snapshot date.

Until one of those exists, every date anything asks about comes from the calendar
itself and the hole cannot be reached. After one of them exists it can be reached
by accident, which is why the trigger is the arrival of the first one rather than
the first wrong answer.

---

### DEBT-013 — The decisions that move a number live only in internal reviews

- **Status:** open
- **Opened:** Sub-step 2.5, on Amino's instruction (2026-08-13)
- **Size:** M
- **Location:** `.claude/docs/reviews/` (where the decisions are), `README.md` (not
  yet written), and the code comments that cite a review rather than a public
  document — `read_market_data` in `veritas/ingestion/simulator.py` is the example
  that prompted this

**What we did**

Recorded every judgement call that changes a number a reader will see in the Step
Review that made it. Step Reviews are the **internal working record** — `CLAUDE.md`
says so directly: *"`README.md` is the public face for Zoomcamp reviewers. The
`.claude/docs/` tree is the working record."* So there is currently no document a
domain expert can open to find out how a figure was arrived at.

The decisions this already applies to, all from Sub-step 2.5 and all approved:

| Decision | What it changes |
|---|---|
| **Cost Basis uses average cost**, not first-in-first-out | Realised P&L on every partial sale |
| **Realised P&L is gross of Commission** | Realised P&L against Gross Revenue — netting would count one charge twice |
| **The Snapshot calendar is the intersection** of the Instruments' trading calendars ([DEBT-012](#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)) | Which dates an "as of" question can be asked about |
| **The two movement tables carry opposite sign conventions** | Whether Net Revenue = Σcommission − Σrebate − Σfee reads true against the ledger |

The list is not closed — it grows with every remaining Step, which is the reason
this is a documentation pass rather than a document to start now.

**What we should have done**

Publish a **user-facing decision register**: one document, written in the reader's
terms rather than ours, naming each decision, the number it moves, what a reader
should conclude when they see that number, and a link to the internal review that
argued it. `README.md` links to it, and any code comment that today explains a
decision at length instead points at it — one explanation, one home.

The general rule this instantiates, which applies to the whole project and not
only to these four: **a decision that changes a number a user will see needs a
place the user can find it.** A review is evidence for us; it is not documentation
for them.

**Why we deferred**

Amino's instruction on 2026-08-13: *"don't do it now, just plan it for final steps
of the project when we want to finalize docs and submit for peer review and
evaluation."* Writing it now means maintaining a public document through every
remaining Step, and the register is most useful — and cheapest — written once when
the set of decisions is complete.

**Cost while unpaid**

A reviewer with domain knowledge is exactly the reader most likely to notice a
Realised P&L figure and ask which cost convention produced it, and exactly the
reader with nowhere to look. They are then left to either assume first-in-first-out
(and read every P&L figure as wrong) or read the source. Both outcomes damage the
thing the project is arguing for: that a number you cannot trace is a number you
should not trust. Making that mistake about our own numbers is the same own goal
[DEBT-008](#debt-008--the-access-control-story-promises-more-than-it-delivers)
names on access control.

**Trigger**

The final documentation pass — when `README.md` is written for peer review and
evaluation. That is the same pass [DEBT-008](#debt-008--the-access-control-story-promises-more-than-it-delivers)
fires on, and they should be paid together: both are about a public document
saying exactly what is true and no more.
### DEBT-014 — The spike allows a query the Gate must reject

- **Status:** open
- **Opened:** Sub-step 3.2 (`.claude/docs/reviews/step-003-validation-feasibility.md`),
  on Amino's ruling of 2026-08-18
- **Size:** S
- **Location:** `.claude/scripts/check_validation_feasibility.py` — the `BLIND_SPOT`
  probe kind and the probe `notional through the wrong currency`

**What we did**

Recorded, as a passing measurement, that the tracer **allows** `Traded Notional`
converted out of the Trade's Denomination Currency instead of the Instrument's
Quotation Currency. The two columns both sit on `fct_trade`, the projection is
identical either way, and the tracer reads the projection — so the query traces to
the certified expression and the run exits zero while printing `ALLOWED` beside a
figure that is 96.39% away from the right one on the currently loaded data (the run
prints both numbers and the gap; see the
[Sub-step 3.2 review](reviews/step-003-validation-feasibility.md#sub-step-32--probe-whether-a-generated-query-traces-to-a-certified-metric)).

**What we should have done**

Reject it. A Metric Definition has to carry its Join Path, and the Validation Gate
has to check the join and not only the projection. When that exists, this probe's
expected verdict flips from allowed to rejected, `BLIND_SPOT` stops being one of the
kinds a passing run can contain, and the probe becomes an ordinary Shadow Metric.

**Why we deferred**

There is no Validation Gate to reject it with — Step 003 is a spike, and its output
is the boundary rather than the enforcement. Encoding the blind spot as a *failure*
today would mean a check that cannot pass until a component two Steps away is built,
and the [Step 003 plan](plan/step-003-validation-feasibility.md) is explicit that *"a
shape that fails is a finding, not a failure"*. Amino ruled on 2026-08-18 that the
encoding stands **on the condition** that the Gate, once built, makes this case fail
correctly. This entry is that condition, moved out of a review and onto the Ledger
where it has a Trigger.

**Cost while unpaid**

The spike's own output reads as full marks when it is not: a reader skimming the
`claim 1` block sees `ALLOWED` on every certified probe and on this one, and has to
notice the probe's `kind` to learn that this line is the bad news. Anything that
quotes the run — a later plan, the go/no-go in Sub-step 3.5, a README — inherits that
reading unless it repeats the caveat. It is also the one place in this repository
where a check passes while demonstrating a wrong answer, which is precisely the shape
[DEBT-009](#debt-009--the-seam-scan-checks-imports-but-not-the-dialect) was opened
about in a different component.

**Trigger**

The Sub-step that builds the Validation Gate. That Sub-step is not done until
`notional through the wrong currency` is rejected by the Gate, and until this probe
in the spike expects a rejection rather than an allowance.

**Status note, Sub-step 3.5 (2026-08-20) — the date-column question is this entry's
question, not a second one.** Sub-step 3.2's review asked that the two be treated as
one: *"nothing here measures whether a Metric Definition's choice of date column is
visible to the Gate. It is the same class of problem as finding 5 and 3.5 should
treat it as one question, not two."* They are the same shape — two columns on
`fct_trade`, a projection that cannot tell them apart, and a Glossary Section C pair
that exists because the choice moves the number. So the repayment above is read as
covering both: a Metric Definition carries its **Join Path and its date predicate**,
and the Gate checks both. **No probe converts on Settlement Date**, so unlike the
currency pair this half is argued rather than measured, and the Sub-step that pays
this entry owes a probe for it. Raised as
[R4](design/validation-feasibility.md#r4--debt-014-is-amended-to-name-the-date-predicate--approved-by-amino-2026-08-20)
rather than applied silently, because widening an entry's scope after the fact is a
thing to do in the open, and **approved by Amino on 2026-08-20**. The Trigger below
is unchanged and now covers both halves.

---

### DEBT-015 — The dialect scan names functions, and the loss measured was in a cast

- **Status:** open
- **Opened:** Sub-step 3.5 (`.claude/docs/reviews/step-003-validation-feasibility.md`)
- **Size:** S
- **Location:** `.claude/scripts/check_warehouse.py` — `unportable_functions`, read
  by `check_seam`; and the mitigation wording in
  [ADR-0002](adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md)'s first accepted
  cost

**What we did**

Paid [DEBT-009](#debt-009--the-seam-scan-checks-imports-but-not-the-dialect) with a
scan whose unit is the **function call**, and wrote ADR-0002's mitigation in the same
unit: *"treat any DuckDB-only function in a Metric Definition as a review comment"*.

Sub-step 3.4 then measured the one construct in this project's own certified
expressions where the trip to BigQuery loses meaning, and it is not a function call.
`Traded Notional`'s widening cast to `DECIMAL(38, 6)` — which
`check_validation_feasibility.py` proves is required, by running the uncast
expression and printing the engine's refusal on every run — arrives in BigQuery as
a cast to `NUMERIC`. So does `DECIMAL(18, 6)`, the width `fct_trade.quantity` is
stored at. The two statements the cast exists to keep apart become one statement.
The scan reads that statement as **clean**, because a cast is not a function call,
and ADR-0002's mitigation produces no review comment for the same reason.

**What we should have done**

Scan for dialect-shaped **type** constructs as well as function names, and say
*construct* where ADR-0002 says *function*.

The instrument is measured and already in the repository. `round_trip_rewrites` in
`check_validation_feasibility.py` compares the parse tree before and after
retargeting, and it flags exactly the cast the name list reads as clean. It is **not**
a replacement for the name list: the same Sub-step measured that the round trip
passes 39 of the 50 measurable DuckDB-only names straight through, because sqlglot
emits a name it cannot translate as it found it and a before-and-after comparison
reads its own failure as portability. The two are blind to disjoint classes, so the
repayment is the name list **plus** a round-trip comparison over types — the table in
[validation-feasibility.md](design/validation-feasibility.md#debt-009s-open-question-answered-no)
is which one covers what.

**Why we deferred**

The same reason DEBT-009 itself gave, one level up: **there is nothing to scan yet.**
No Semantic Layer exists, so no Metric Definition exists, and the only cast outside
`veritas/warehouse/` is a Python literal in a spike whose whole subject is that the
scan cannot see it. Writing the wider scan now would mean writing it against the one
example this spike happens to hold, which is how a check comes to pass vacuously.
Sub-step 3.5 is also a document Sub-step — widening a check script in it would be a
second commit.

**Cost while unpaid**

A reader of `check_warehouse.py`, or of ADR-0002's *"how this stops being a promise"*
paragraph, can reasonably conclude the dialect commitment is mechanically checked. It
is checked in the unit where nothing was lost, and not in the unit where something
was. That is DEBT-009's cost sentence with one word changed, in the same file, which
is the part worth wincing at.

Concretely: `Traded Notional` cannot be given a Metric Definition without the
widening cast, so the first Metric Definition Step 004 writes for it carries the exact
construct nothing looks at, and the first person to read the scan's clean output will
be entitled to draw the wrong conclusion from it.

**Trigger**

The first Metric Definition that carries a cast, or any other construct whose meaning
is in a type rather than in a name. On the measurements above that is
`Traded Notional`'s, in the Step that builds the Semantic Layer, and it cannot be
avoided by writing the expression differently.

**Fired 2026-08-22, in Sub-step 4.2 — and wider than this entry says.** The trigger
reads *"the first Metric Definition that carries a cast"* and sizes the repayment
against one. Writing the corpus found that the widening cast is carried by **every**
published expression whose product overflows `DECIMAL(18)`, which is every monetary
metric on the Snapshot side plus the accounting ledger, not `Traded Notional` alone.
`check_semantic_layer.py` executes each of them with its cast taken back out and
prints the engine's refusal, so how many there are is a reading rather than a
sentence here, and the block is quoted in the
[4.2 review](reviews/step-004-semantic-layer.md#sub-step-42--write-the-remaining-metric-definitions).

The **repayment does not change** — it is the same name list plus round-trip
comparison, and a scan that reads types finds all of them at once. What changes is the
cost sentence above: the construct nothing looks at is not one expression's, it is
most of the corpus's.

**Debt rather than an extension, and the argument is on the record.** The Ledger's own
test is whether the trigger fires inside this project's life, and this one fires in
the next Step. The counter-argument — that the *consequence* can only land on
BigQuery, which is [EXT-001](extension-register.md#ext-001--warehouse-native-security-and-concurrency)'s
migration and outside this project — is real, and was
[R2](design/validation-feasibility.md#r2--debt-015-is-debt-rather-than-an-extension--approved-by-amino-2026-08-20).
**Amino settled it on 2026-08-20: it is debt and stays here.** What is wrong *now*,
and what makes it debt as written, is a check claiming coverage it does not have.

### DEBT-016 — The Semantic Layer check cannot name the engine's error type

- **Status:** open
- **Opened:** Sub-step 4.1 (`.claude/docs/reviews/step-004-semantic-layer.md`)
- **Size:** S
- **Location:** `.claude/scripts/check_semantic_layer.py` — `rows_from`, the two
  lines that execute a published expression

**What we did**

Wrapped the Warehouse Adapter's `query` in `except Exception`. Executing a published
expression against the live schema is what makes a Metric Definition a metric rather
than a claim, and the engine's refusal — a column that no longer exists, an overflow,
a type it will not compare — is the finding. Catching it is what lets one broken
entry name itself while the rest of the corpus still runs, instead of the first
failure hiding the other eight.

The catch is broad because this script may not name the class it wants.
[ADR-0002](adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md) puts the engine's
dialect inside the adapter, an engine's exception types are part of its dialect, and
`check_warehouse.py`'s seam scan fails the run on a `duckdb` import anywhere else —
correctly. So the only expressible catch is `Exception`.

**What we should have done**

Give the Warehouse Adapter an error type of its own — `WarehouseError`, raised from
the engine's exception at the boundary that already owns the engine — and catch that
here. One class and one `raise ... from` inside `veritas/warehouse/adapter.py`; every
caller outside the adapter then handles query failure without naming DuckDB.

**Why we deferred**

Sub-step 4.1's subject is the Semantic Entry format, and this is a change to the
Warehouse Adapter — a different component, and the seam ADR-0002 spent an ADR on. It
also needs a decision this Sub-step has no reason to take: whether every adapter
method wraps or only the two that execute caller-supplied SQL. ADR-0002 already
licensed the adapter's first implementation to *"handle no errors at all"*, so
nothing here is being written against that ADR — it is being left where the ADR put
it.

**Cost while unpaid**

The check reports a defect in its own code as a defect in the corpus. A `TypeError`
from a bad bound parameter, or an adapter that cannot open the Warehouse at all,
prints as *"the engine refused the query below"* beside a metric's name — which sends
a reader to a YAML file that is fine. The run still fails, so nothing passes that
should not; what is wrong is the diagnosis, and it is wrong in the direction that
costs someone else's afternoon.

It is kept to the two lines that actually execute SQL, so a bug anywhere else in this
script still surfaces as a traceback rather than as a false accusation.

**Trigger**

The first component outside `.claude/scripts/` that has to handle a failed query —
the Orchestrator's execute step, which is where a Grounded Answer has to say *"the
Validation Gate passed this and the engine still refused it"*. That component cannot
catch `Exception` and stay honest, because it has to tell a user which of the two
happened.
