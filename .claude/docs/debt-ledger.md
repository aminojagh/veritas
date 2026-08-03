# Debt Ledger

Every knowingly-taken shortcut in Veritas, recorded at the moment it was taken.

This is not a wishlist and not a bug tracker. It is the record of places where
we chose speed over correctness **on purpose**, so that choice stays visible and
reversible. See the `recording-debt` skill.

**Every entry has a Trigger** — the condition that forces repayment. Debt
without a Trigger is a wish.

**Status:** `open` · `paid` (with the Sub-step that paid it) · `accepted`
(deliberately permanent — with the reason) · `superseded` (the code it described
no longer exists).

---

## Index

| ID | Title | Size | Trigger | Status |
|---|---|---|---|---|
| [DEBT-001](#debt-001--framework-rules-rely-on-discipline-not-enforcement) | Framework rules rely on discipline, not enforcement | M | A rule is broken in practice | open |
| [DEBT-002](#debt-002--market-prices-depend-on-an-unofficial-endpoint) | Market prices depend on an unofficial endpoint | S | Before any reproducibility claim in `README.md` | open |
| [DEBT-003](#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope) | No Market Price vendor, so single bonds and options are out of scope | L | Any requirement to hold a single bond or an option | open |
| [DEBT-004](#debt-004--the-fx-date-distinction-is-too-small-to-be-a-reliable-evaluation-signal) | The FX-date distinction is too small to be a reliable evaluation signal | S | Building the Gold Question Set | open |

**Open debt:** 4 · **Paid:** 0 · **Accepted:** 0

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
