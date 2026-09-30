# Debt Ledger

Every open shortcut in Veritas: a place where the code is knowingly wrong, cheaply,
recorded when the shortcut was taken. See the `recording-debt` skill.

**Every entry has a Trigger** — the condition that forces repayment. Debt without a
Trigger is a wish.

**Debt or extension?** If the current code is *wrong, cheaply*, it is debt and
belongs here. If it is *right for this scope* and the full system needs more, it is
an extension and belongs in the [Extension Register](extension-register.md). The
test: **does the trigger fire inside this project's life?**

**Only open entries live here.** An entry that is paid, accepted as permanent, or
moved to the Register is deleted, with every link to it; git keeps it. Numbers are
never reused.

**Next free number:** DEBT-046

---

## Index

| ID | Title | Size | Trigger |
|---|---|---|---|
| [DEBT-001](#debt-001--framework-rules-rely-on-discipline-not-enforcement) | Framework rules rely on discipline, not enforcement | M | Fired — awaiting scheduling |
| [DEBT-003](#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope) | No Market Price vendor, so single bonds and options are out of scope | L | A requirement to hold a single bond or an option |
| [DEBT-012](#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes) | The price table is sparse, so the Snapshot calendar has holes | M | The first "as of" date chosen by anything but the Snapshot calendar |
| [DEBT-017](#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) | The certified axes are registered inside one Glossary cell | S | A sixth certified axis, or a rewording of that cell failing the run |
| [DEBT-018](#debt-018--six-certified-metrics-have-no-expression-text-pinned-outside-the-corpus) | Six Certified Metrics have no expression text pinned outside the corpus | S | The first edit to a Certified Metric's `expression` |
| [DEBT-023](#debt-023--two-proving-systems-run-side-by-side) | Two proving systems run side by side | L | Fired — repaid per surviving component |
| [DEBT-024](#debt-024--docstrings-argue-why-they-were-built-as-they-are) | Docstrings argue why they were built as they are | L | Fired — repaid per surviving component |
| [DEBT-025](#debt-025--the-nine-certified-metrics-are-implemented-twice) | The nine Certified Metrics are implemented twice | M | A change to a Certified Metric's `expression`, or DEBT-023's port |
| [DEBT-035](#debt-035--a-composed-certified-metric-has-no-statement-the-gate-allows) | A composed Certified Metric has no statement the Gate allows | L | Fired — stated, not paid |
| [DEBT-045](#debt-045--the-code-calls-an-ending-an-expectation) | The code calls an Ending an Expectation | S | The first change to `veritas/evaluation/` |

---

## Entries

<!--
Copy this template for each new entry, take the next free number, and advance it.
Keep entries in ID order.

### DEBT-NNN — <short title>

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

- **Size:** M
- **Location:** `CLAUDE.md` (the four non-negotiables), `.claude/skills/*`

**What we did**

Wrote the framework as instructions Claude is asked to follow. `tests/` checks that
the framework's documents are wired together — links and anchors resolve, skills
load, the Glossary's rules hold over the documents and the identifiers — but nothing
checks that the framework was *followed*: Claude could stage or commit despite
"Amino commits", close a Sub-step with no Step Review, take a shortcut without a
Ledger entry, or run a bare `python`.

**What we should have done**

Enforce the mechanical subset with hooks in `.claude/settings.json`:

- `PreToolUse` on `Bash(git add*)`, `Bash(git rm*)` and `Bash(git commit*)` — block,
  since Amino stages and commits.
- `PreToolUse` on `Bash` matching a bare `python` or `python3` — block, since the
  interpreter is always `uv run python`.
- A `Stop` hook running `uv run pytest tests/test_framework.py tests/test_links.py
  tests/test_language.py`.

Judgement-dependent rules — is this a shortcut? is this word a Glossary term? — cannot
be hooked and will always rest on discipline.

**Why we deferred**

Enforcing rules before knowing which survive contact with real work would harden
guesses, and hooks make a rule expensive to change.

**Cost while unpaid**

Compliance decays as sessions get long and context is summarised — exactly when care
matters most. The failure is silent: a missing Ledger entry looks identical to no
debt having been taken, and a breach is on the record only if the party that broke
the rule reports it.

**Trigger**

The first time a framework rule is observed broken in practice. **Fired**, more than
once: verification pasted from throwaway scripts, a bare `python3`, and a staged
deletion. The hook layer is Amino's to schedule.

---

### DEBT-003 — No Market Price vendor, so single bonds and options are out of scope

- **Size:** L
- **Location:** the `Instrument` definition in `.claude/docs/glossary.md`

**What we did**

Narrowed `Instrument` to "equity, ETF, future, or currency pair", because no key-free
source provides Market Prices for single bonds or options.
`data/snapshots/probe-results.json` records the probes: HTTP 404 for bonds by
International Securities Identification Number (ISIN) and by CUSIP, HTTP 401 for the
option chain. Bond exposure is represented through bond ETFs, which do have Market
Prices.

**What we should have done**

Subscribe to a market-data vendor that covers fixed income and listed derivatives —
the realistic options are paid (Refinitiv, Bloomberg, ICE, or at the cheaper end
Polygon or EODHD with a fixed-income add-on) — and model single bonds and options as
first-class Instruments, with their own price series, accrued-interest handling, and
option greeks.

**Why we deferred**

A paid vendor cannot be a dependency of a project that must be reproducible from a
`git clone` with no credentials. None of the Certified Metrics or Section C
distinctions needs a bond or an option to be demonstrated.

**Cost while unpaid**

Veritas cannot answer any question about single-bond or option holdings, and cannot
model the two behaviours those instruments uniquely introduce: accrued interest
between coupon dates, and non-linear exposure. A real brokerage has both, so this is
the largest single gap between Veritas and the system it is a slice of.

**Trigger**

Whichever comes first:

1. A requirement to hold a single bond or an option — in the full-system scope, in
   the Gold Question Set, or in a stakeholder question.
2. `check_data_availability.py --refresh` reporting that bonds or options have
   become obtainable key-free. It probes them on every refresh so this cannot go
   stale unnoticed.

---

### DEBT-012 — The price table is sparse, so the Snapshot calendar has holes

- **Size:** M
- **Location:** `veritas/warehouse/builds/fct_instrument_price.sql` (sparse per
  Instrument) and `veritas/ingestion/simulator.py` — `snapshot_dates` in
  `read_market_data`

**What we did**

`fct_instrument_price` holds a row only on the dates an Instrument's own exchange
traded. Given a sparse price table, the intersection of the trading calendars is the
only safe Snapshot calendar ([ADR-0006](adr/0006-every-certified-metric-follows-one-stated-book-convention.md)),
so the dates on which some markets traded and some did not carry no Snapshot at all.
`uv run python .claude/scripts/check_warehouse.py --sources` prints both counts.

**What we should have done**

Make the price table dense, so that the intersection and the union are the same set:
fill `fct_instrument_price` forward across every date any Instrument traded, with a
column saying whether a row is a close the exchange printed or one carried from the
previous session, so a metric can exclude carried rows and a Lineage can name them.
This is the shape `fct_fx_rate` already has; two tables answering "what was true on
D" by opposite conventions is the incoherence worth removing.

**Why we deferred**

A provenance column changes the schema, the build, the Snapshot calendar and every
simulated table that hangs off it. The pipeline refuses to complete if a Snapshot is
unmarkable, so nothing silent rides on the intersection.

**Cost while unpaid**

**An "as of" question about a missing date has no answer, and the absence looks like
a zero.** Every Snapshot-grain metric is an equality join on `snapshot_date`, and on a
date the calendar skips that join returns no rows — which is exactly what an Account
holding nothing returns. A period filter whose boundary lands on a missing date
silently uses a different boundary, and a Position Change across one is attributed to
the next Snapshot date. Each certified date axis names a Warehouse date column rather
than a calendar period, so no axis carries a boundary the calendar lacks, and
`semantic/dimensions/by_snapshot_date.yaml` says so in the entry a reader retrieves —
but *"Account Value at the end of Q2"* cannot be expressed.

**Trigger**

The first "as of" date chosen by anything other than the Snapshot calendar: a Gold
Question naming a date, the App accepting a date from a User, or a Dimension
Definition whose period boundary is a calendar date.

---

### DEBT-017 — The certified axes are registered inside one Glossary cell

- **Size:** S
- **Location:** [`glossary.md`](glossary.md#a-the-system) — the `Dimension Definition`
  row's *Definition* cell — and `.claude/scripts/check_semantic_layer.py`,
  `dimension_axes_in_glossary`

**What we did**

Registered the five certified axes — names, columns, grain and allowed values —
inside the prose of one Section A cell, and read them back with a regular expression
over that prose. Check 18 is what keeps the Glossary and `semantic/dimensions/` saying
the same thing. The other two registries this project reads back are tables: Section
B gives every Certified Metric a row, and Section D gives every Ambiguous Term one.

**What we should have done**

Give the axes a Glossary section of their own, one row per axis, with the columns,
the grain and the allowed values in columns of their own — the shape Section D has.
The `Dimension Definition` row would then define the term and point at that section.

**Why we deferred**

A new Glossary section changes the shape of the shared vocabulary, which is Amino's
to agree, and at five axes the sentence is still legible. The parse is strict, so a
reworded parenthetical fails the run rather than silently reading a different list.

**Cost while unpaid**

**The check is bound to a sentence's punctuation.** `dimension_axes_in_glossary`
requires a bold axis name followed immediately by a parenthetical of two or three
em-dash-separated parts, so editing that cell for readability can fail the run for a
reason that has nothing to do with the corpus. And the cell gets less legible with
every axis added.

**Trigger**

A sixth certified axis, or the first time that cell is reworded and the run fails
for it.

---

### DEBT-018 — Six Certified Metrics have no expression text pinned outside the corpus

- **Size:** S
- **Location:** `.claude/scripts/check_validation_gate/traces.py` — `certified_probes`;
  and `.claude/scripts/check_semantic_layer.py`'s check 9, which pins three of the nine

**What we did**

Built the Gate check's nine per-metric probes out of the corpus they are checked
against: `certified_probes` writes each Metric Definition's simplest statement from
its own `expression`, `from_table`, `join_paths` and `filters`, and declares it
`allowed`. So an edit to an expression moves the probe and the Gate's certified form
together, and the run goes on printing `allowed`.

Two checks cover most of such an edit. `check_semantic_layer.py`'s check 4 executes
every published expression and compares the number against `check_warehouse.py`'s own
SQL, which reads nothing from `semantic/` — any edit that moves a number fails. Its
check 9 pins the exact text of `Gross Revenue`, `Net Revenue` and `Traded Notional`.
The hole is an edit to one of the six unpinned metrics — `Account Value`,
`Cash Balance`, `Position Change`, `Realised P&L`, `Trade Count`, `Unrealised P&L` —
that changes the text without changing the number: commuting a subtraction, splitting
an aggregate, spelling `count(fct_trade.trade_id)` as `count(*)`.

**What we should have done**

Widen check 9's pin from three metrics to nine: one recorded expression text per
Certified Metric, held outside `semantic/`, with the run failing and both texts
printed when a published expression no longer matches its record. The second copy is
the mechanism: keeping it in step turns a silent drift into an edit a reviewer reads.

**Why we deferred**

The fix belongs to `check_semantic_layer.py`, which owns the pin, and not to the
Gate's check, where the probes that exposed the gap live.

**Cost while unpaid**

The Semantic Layer can drift into a paraphrase of itself and stay green. `traces.py`
refuses a generator that writes a paraphrase of a certified expression, but a
paraphrase written into `semantic/metrics/` is certified by definition: the Gate then
rejects the statement it allowed the day before, and no check says so. Six of the
nine per-metric probes have no second opinion on their text.

**Trigger**

The first edit to a Certified Metric's `expression` in `semantic/metrics/`. The
repayment is then cheap: the nine texts are on disk.

---

### DEBT-023 — Two proving systems run side by side

- **Size:** L
- **Location:** `.claude/scripts/` against `tests/` — `tests/test_framework.py` lists
  the scripts that remain

**What we did**

Froze the product check scripts and put every new behavioural claim in `tests/`,
rather than porting the checks over. `tests/test_framework.py` enforces the freeze.
The spike's three-way coupling is frozen with them: it imports `veritas.validation`,
`check_semantic_layer.py` imports *it*, and `check_validation_gate/probes.py` parses
its **source text** to assert its SQL literals match character for character.

**What we should have done**

One proving system. The check scripts' probe tables are already test data — the probe
tuple in `restricted.py` is a parametrized case list with a bespoke runner — so the
port is mechanical: fixtures to `conftest.py`, probe tuples to
`pytest.mark.parametrize`, report lines to assertions. Then the spike's SQL corpus is
owned by tests, and the spike itself becomes deletable.

**Why we deferred**

Porting was days of work against a deadline, for a return inside it of a fraction of
that.

**Cost while unpaid**

Two places to look for "what does this component guarantee", in different idioms. The
frozen scripts cannot be refactored, because `probes.py` asserts on another script's
source text — so a rename in the spike breaks a check that never imports it, and the
coupling is invisible to every tool.

**Trigger**

**Fired** — the deadline that justified the freeze has passed. Repaid component by
component, and only for components the redesign keeps: a check whose component is
deleted goes with it.

---

### DEBT-024 — Docstrings argue why they were built as they are

- **Size:** L
- **Location:** `veritas/validation/gate.py` most acutely; `veritas/` and
  `.claude/scripts/` generally

**What we did**

Applied the docstring convention — what a thing is and how it works, never why —
forward only. Existing docstrings still argue why they were built as they are, cite
rulings by name, and quote the Step history that produced them.

**What we should have done**

Move the reasoning to the ADR that owns each decision, or delete it where no decision
is being recorded. `gate.py` would fall to a fraction of its size without losing a
claim, because the claims live in `tests/` where they execute.

**Why we deferred**

Days of work across the tree against a deadline, for a return inside it of a fraction
of that.

**Cost while unpaid**

A session cannot hold the project and reasons from fragments instead, and Amino reads
it all: the reading rate, not the build rate, sets this project's pace.

**Trigger**

**Fired** — the deadline that justified forward-only has passed. Repaid component by
component, and only for code the redesign keeps.

---

### DEBT-025 — The nine Certified Metrics are implemented twice

- **Size:** M
- **Location:** `.claude/scripts/check_warehouse.py` — the nine metric functions —
  against `semantic/metrics/*.yaml`; and `tests/test_gate.py`, which writes
  `Gross Revenue`'s and `Traded Notional`'s expressions out with the rate they convert
  through left open. That copy fails loudly rather than quietly: the certified half of
  the pair asserts the Gate **allows** it, so an expression that moved in `semantic/`
  breaks the test.

**What we did**

`check_warehouse.py` defines `gross_revenue`, `net_revenue`, `traded_notional`,
`trade_count`, `cash_balance`, `account_value`, `unrealised_pnl`, `realised_pnl` and
`position_change` as Python functions computing expected values, while
`semantic/metrics/` defines the same nine as certified SQL expressions. Neither is
derived from the other.

**What we should have done**

Compute the expected value *from* the Metric Definition's `expression`, so the corpus
is the single definition and the check tests that the Warehouse agrees with it. A
second implementation of a metric is the Shadow Metric this project exists to prevent,
inside its own tooling.

**Why we deferred**

It is frozen under [DEBT-023](#debt-023--two-proving-systems-run-side-by-side).

**Cost while unpaid**

Changing a Certified Metric's expression leaves `check_warehouse.py` computing the old
one, and it still passes — it compares the Warehouse against itself, not against the
corpus.

**Trigger**

A change to a Certified Metric's `expression`, or repayment of
[DEBT-023](#debt-023--two-proving-systems-run-side-by-side), whichever is first.

---

### DEBT-035 — A composed Certified Metric has no statement the Gate allows

- **Size:** L
- **Location:** `veritas/validation/gate.py` — `ValidationGate.traces`, which reads a
  Metric Definition's `expression` and not its `derives_from`; the exemption it forces
  is `REFUSED_TODAY` in `tests/test_gold.py`

**What we did**

Left the tracing rule reading one field. `Account Value` is the one Metric Definition
with `derives_from`: *"Cash Balance plus all Positions marked to market"*, rooted at
two Snapshot tables that join on nothing without multiplying rows. So the only correct
statement for it adds two scalar subqueries, and the Gate reads that outer addition as
an expression it cannot trace — a `SHADOW_METRIC`. The partial statement, the
positions expression alone, is refused as an `incomplete certified metric`.
`check_semantic_layer.py`'s `query_parts` and `executable_query` assemble and execute
the correct statement, so the corpus and the Semantic Layer check agree on a shape the
Gate refuses.

**What we should have done**

Read `derives_from` in the tracing rule: an addition whose operands each trace to a
Certified Metric is certified when the corpus says one metric derives from the others.
And admit the composed shape in the generation prompts, which pin a single `SELECT`
with no second top-level statement, measured across both prompt forms again — a Gate
that allowed the shape would otherwise be asked for it by no prompt Veritas writes.

**Why we deferred**

The tracing rule is the rule every other rule runs behind, its verdicts are pinned by
the probes in `.claude/scripts/check_validation_gate/`, and widening it for one metric
is a change with more ways to go wrong than right. The Gold Question carries the
correct statement and result, so the specification is on record and the Gate is
measurably behind it.

**Cost while unpaid**

`Account Value` is unanswerable, and both Ambiguous Terms that resolve to it —
`balance` and `how much does X have` — resolve to a metric with no statement behind
it. `README.md` says so. `REFUSED_TODAY` in `tests/test_gold.py` names the one Gold
Question the Gate refuses, so the test breaks when this is paid; and the generation
sweep excludes that question by asking the Gate, so it scores one question more the
day this is paid without a line edited.

**Trigger**

**Fired** when Execution Accuracy was first measured, and ruled stated rather than
paid. Repaid when `Account Value` must be answerable.

---

### DEBT-045 — The code calls an Ending an Expectation

- **Size:** S
- **Location:** `veritas/evaluation/gold.py` (`Expectation`, `GoldQuestion.expects`),
  `veritas/evaluation/generation.py` (`ended_as`), the `expects:` key of every file in
  `data/gold/`, and the tests that read them

**What we did**

Registered **Ending** in the Glossary and left the code's older name for the same
concept: the `Expectation` enumeration of the three Endings, and the `expects` field
that holds a Gold Question's correct Ending.

**What we should have done**

Renamed `Expectation` to `Ending` and `expects` to `correct_ending`, in the code, the
Gold Question files and the tests, in the change that registered the term.

**Why we deferred**

Registering the term was a documents-only change, and the redesign may reshape or
delete `veritas/evaluation/`, which would make the rename wasted work.

**Cost while unpaid**

Two names for one concept: a reader of `gold.py` meets `Expectation` where the
Glossary says Ending.

**Trigger**

The first change to `veritas/evaluation/`. If the redesign deletes the module, this
entry goes with it.
