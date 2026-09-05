# Step Review — Step 001: Design the Target State

## Sub-step 1.1 — Agree the domain language and target state

**What changed**

Decided what Veritas is, and wrote the vocabulary to describe it.

- **`.claude/docs/glossary.md`** — Domain Language in four sections: **the system**
  (Semantic Layer, Validation Gate, Grounded Answer, Lineage, Execution
  Accuracy, …), **the warehouse** (Trade, Cash Movement, Position, Gross/Net
  Revenue, …), **distinctions we must not blur**, and **Ambiguous Terms**.
  All 36 terms are `proposed`.
- **`.claude/docs/design/target-state.md`** — the problem, the governing rule,
  components, flow, non-goals, the Zoomcamp criteria map, and the extension path
  to the full MVP.

The design in one line: **the model never defines a metric — it may only select
one from a certified Semantic Layer, and everything it generates is checked by
code before it runs.**

Two structural consequences worth naming, because they are why this shape was
chosen over a conventional text-to-SQL demo:

1. **Retrieval becomes the correctness mechanism**, not a nicety. Retrieving the
   wrong Metric Definition *is* the wrong answer. That is what lets retrieval
   evaluation have derived ground truth: the Semantic Entries a gold SQL touches
   are, by construction, its relevant set. No hand-labelling, no judge.
2. **Ambiguous Terms are first-class and are *not* metrics.** "Revenue",
   "volume", "balance", "P&L" each map to two or more Certified Metrics, so
   Veritas must resolve them before generating SQL. This turns the rubric's
   query-rewriting bonus point into the product's core disambiguation step
   rather than a bolt-on — and it is a direct answer to the job spec's line
   about distinguishing revenue, gross revenue, net revenue, trading volume,
   cash movement, accounting movement, balances, and position changes.

**Verification**

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       513 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          665 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr          592 words
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
```

Criteria map checked by hand against the rubric: 20 of 24 points designed for,
2 deferred (cloud deployment), 3 claimed as extra credit. Every capitalised term
in `target-state.md` traces to a Glossary entry.

**Deliberately left undone**

- **Sub-step 1.2 — the three founding ADRs** (Semantic Layer as corpus, DuckDB
  behind an adapter seam, deterministic Validation Gate). Held back because ADRs
  written against an unapproved Target State get rewritten with it. Not debt —
  planned work, sequenced.
- **Instrument/price data source** — FX is settled (Frankfurter: real ECB rates,
  no API key, good for reproducibility). Instruments and prices are left to the
  ingestion Step so the choice can be tested rather than guessed.
- **Cloud deployment** (2 bonus points) — outside a 2–3 week slice.
- No new Debt Ledger entries. This Sub-step wrote documents; there was nothing
  to shortcut.

**Look at this sceptically**

1. **36 proposed terms is a lot to agree at once.** The eight in *"distinctions
   we must not blur"* are the ones that actually matter — if the financial
   definitions there are wrong, the product is wrong. Please read those eight
   properly even if you skim the rest. I am most exposed on **Accounting
   Movement**: I have defined it as accrual-basis recognition on the date value
   is *earned*, versus Cash Movement on the date money moves. If real
   brokerage usage differs, correct me.
2. **Synthetic client activity may read as a weaker dataset** to a peer
   reviewer, even though the rubric explicitly permits generated data. The
   mitigation is that FX and market data are genuinely real, and the framing —
   "market data real, client data synthetic for privacy" — is what an actual
   broker would say. Worth knowing it is a judgement call.
3. **The scope is the top of what fits in 2–3 weeks.** Nine components. The
   honest risk is the last mile: Grafana dashboards and docker-compose are
   exactly what gets rushed, and they are 4 rubric points. If time compresses,
   my recommendation is to cut re-ranking (1 point) before cutting monitoring
   (2 points).
4. **`sqlglot` is load-bearing and unproven here.** The Validation Gate's whole
   claim — deterministic, parse-tree-level checks — rests on being able to trace
   generated SQL expressions back to Certified Metrics. I believe this works but
   have not built it. It is the single highest-risk assumption in the design, so
   Step 002 should touch it early rather than leave it to the end.
5. **"Refusing to answer is a feature" will feel bad in a demo.** It is the
   correct behaviour and it is the point of the project, but a reviewer clicking
   around may read refusals as brokenness. The UI needs to make a refusal look
   like rigour, not failure.

**Language**

36 Domain Language terms proposed, none agreed yet. No terms entered code — no
code was written, which is the intended order.

Cross-checking the Glossary against `target-state.md` caught one real collision:
I had written "Certified Metric Definitions", conflating two separately
registered terms. Fixed to "Metric Definitions" — a Metric Definition in the
Semantic Layer is certified by construction, so the adjective was doing no work.

**One collision for you to rule on:** **Certified Metric** and **Metric
Definition** are close enough to be worth questioning. My reading is that they
are genuinely different — a Metric Definition is the *artifact* (the YAML entry
you retrieve), while Certified Metric is a *status* whose value is the contrast
with Shadow Metric. But if you think one term can carry both jobs, say so and I
will retire the other before either reaches code.

Nothing in the Process Language changed. One inconsistency fixed in Step 000:
sub-steps were numbered `1.1` inside Step `000`; the scheme is now
`Step NNN → Sub-step NNN.M` throughout.

---

## Revisions from review — 2026-07-23

Amino's ruling on Sub-step 1.1, and the changes folded in. The sections above are
left as written (a point-in-time record); this section is what changed since.

**Rulings received**

- **Section-C distinctions approved**, and all other Domain Language terms
  approved → Sections A through D are now `agreed`. The batch-proposed banner is
  retired.
- **`Certified Metric` and `Metric Definition` both kept** — the collision is
  resolved as "genuinely different," so neither is retired.

**Changes made**

- **Glossary:** Sections A through D flipped `proposed` → `agreed`; `Dimension
  Definition` rewritten with a plainer explanation and worked examples (the term
  was flagged as unclear); a new **System measures** section added —
  `Evaluation Measure` and `Operational Measure` (`proposed`), keeping "metric"
  exclusively for business metrics and "measure" for how Veritas is judged.
- **Target State:** status now "terms `agreed`, document `proposed` until the
  data-availability check"; a "two senses of metric" note added by the components
  table; the Zoomcamp criteria map gained a header clarifying each row is a
  *grader's scorecard line*, and the **Problem description** row was expanded.
- **Plan (Step 001):** new **Sub-step 1.2 — verify data availability** inserted as
  an explicit gate before the design is final; the three ADRs moved to 1.3.
- **Product brief:** `.claude/docs/design/product-brief.md` written — the full system
  Veritas slices, captured in Glossary terms so `final_proposal_target.md` can be
  removed from the repo.
- **Framework (proposals to react to):** the *contour-lines / seam test* principle
  added to `CLAUDE.md` and the `recording-debt` skill; a *session-resumption*
  contract added to `CLAUDE.md` and `closing-a-substep`, with a **Resume here**
  block now opening `current-state.md`.
- **Links:** concrete doc paths in `CLAUDE.md` and the state docs are now
  clickable; globs, future code modules, and DB table names are left as plain
  monospace (linking them would be a dead link and fail `verify_framework.py`).

**Resolved since**

1. System measures approved — `Evaluation Measure` and `Operational Measure` are
   now `agreed`.
2. Framework wording (contour/seam, session-resumption) approved as written.
3. Step 000's checker-vs-description call ruled: keep the broadened checker.

---

## Sub-step 1.2 — Verify data availability

**What changed**

Proved the paints exist before committing to the composition. Every source the
Target State assumes was hit live on 2026-08-03, and the three data legs — FX
Rates, market prices, synthetic activity — were joined into one working dataset.

- **`.claude/docs/design/data-availability.md`** (new) — source-by-source verdict,
  gaps, the go/no-go, and the three rulings with their reasoning.
- **`.claude/scripts/check_data_availability.py`** (new) — the check as an
  executable, asserting gate. Plus `data/snapshots/` (288 KB), which makes it
  reproduce offline.
- **Verdict: GO.** No structural change to the Target State. Three narrow
  rulings — R1–R3 — were raised and all three were decided the same day, so
  **`target-state.md` is now `agreed`**.
- **`.claude/docs/glossary.md`** — three terms added, one narrowed, two
  Section-C distinction rows, two tables renamed `dim_` → `fct_`.
- **`.claude/docs/debt-ledger.md`** — DEBT-002, DEBT-003, DEBT-004.
- **`.claude/docs/design/current-state.md`** — the stale "awaiting the first
  commit" pointer fixed (that commit is `6281e6b`), then brought up to date.

The headline findings, in order of how much they change things:

1. **The instrument/price question deferred from 1.1 is answered, and the
   obvious answer was wrong.** Stooq — the documented, key-free CSV endpoint
   every tutorial uses — now returns a JavaScript anti-bot challenge with an
   HTTP 200. It looks like success and is not. The only key-free source that
   still works is Yahoo's chart endpoint, which is unofficial. Every supported
   vendor requires a key and therefore fails the rubric's reproducibility
   criterion.
2. **Bonds and options cannot be obtained at all** key-free — 404 on every
   CUSIP/ISIN form, HTTP 401 on the option chain. The Glossary's definition of
   `Instrument` currently promises both. That is **R1**.
3. **Two wrong-number traps in the real data**, both exactly the failure this
   project exists to prevent. `close` and `adjclose` differ on **95.5%** of
   AAPL's 1,255 daily bars, and LSE quotes in **pence** (`GBp`), a silent 100×.
   Both are now Glossary terms rather than lore. That is **R2**.
4. **The synthetic-activity premise holds, and is now demonstrated rather than
   asserted** — a seeded spike joined real FX + real prices + synthetic Trades
   and produced a materially different number for every Section-C distinction.

**Verification**

The plan's three checks were: the findings doc exists, each source is hit at
least once with output pasted into this review, and the framework checker
passes. The middle one changed on Amino's instruction — pasted output is a
transcription I could get wrong and nobody could re-run, so the probes are now a
committed script and this review points at it instead.

```bash
uv run python .claude/scripts/check_data_availability.py            # offline, deterministic
uv run python .claude/scripts/check_data_availability.py --refresh  # re-hit every source live
uv run python .claude/scripts/verify_framework.py
```

Both modes were run and **both exit 0**, producing byte-identical spike figures.
`--refresh` re-probed every source live and rewrote `data/snapshots/`; the
default offline mode replays the recorded probes and re-executes the join spike
against the committed snapshots. `verify_framework.py` passes.

The script is not a printer — it asserts, and exits non-zero if a source stops
answering, if either wrong-number trap disappears, or if any Section-C
distinction collapses. Bonds and options are re-probed on every `--refresh`, so
the R1 exclusion fails loudly rather than quietly outliving its reason.

What it checks, and what it found:

| Check | Finding |
|---|---|
| Frankfurter reachable, 2025 series | 256 daily FX Rates, 6 ECB holidays absent, weekends absent |
| NASDAQ Trader + SEC reference data | 345 KB and 798 KB, both key-free |
| Stooq | HTTP 200 carrying a JavaScript anti-bot page — detected as `blocked`, not `ok` |
| Yahoo coverage, 12 symbols | equity in USD/EUR/GBp/JPY, ETF, future, currency pair, index |
| Bonds by ISIN and CUSIP, option chain | 404, 404, 401 — not obtainable, so R1 holds |
| Adjusted Close vs Market Price | differ on 1,198 of 1,255 AAPL bars (95.5%) |
| Quotation Currency | VOD.L quotes `GBp`; normalised to GBP on load |
| Join spike, 4 distinctions | Gross/Net Δ38.95%, accrual/cash Δ23.98%, Notional/Count Δ100%, FX-date Δ0.08% |


**Deliberately left undone**

- **No ingestion pipeline.** `check_data_availability.py` fetches, but it is a
  gate, not ingestion: no dlt, no warehouse, no schema. It does establish the
  snapshot-and-replay pattern that DEBT-002 asks ingestion to adopt, so the
  pattern is proven rather than merely planned.
- **The snapshot mitigation for the real market-price pipeline** —
  [DEBT-002](../debt-ledger.md), triggered when that pipeline is written.
- **No defence in code against the two wrong-number traps.** The check script
  handles both correctly, but there is no warehouse to defend yet. They are
  Glossary terms so the defence is required rather than remembered.
- **A paid market-data vendor** for single bonds and options —
  [DEBT-003](../debt-ledger.md), a future setup step.
- **A volatile FX window for the Gold Question Set** —
  [DEBT-004](../debt-ledger.md), triggered when that set is built.

**Look at this sceptically**

1. **Offline mode replays a recording and prints `ok`.** This is the weakest
   seam in the script. `probe-results.json` is dated 2026-08-03; if Frankfurter
   dies tomorrow, the default run still reports it reachable, because it is
   reporting what happened, not what is true. The join spike is genuinely
   re-executed, so the load-bearing claim is live — but the source table is a
   memory. The date is printed on every run for exactly this reason, and
   `--refresh` is the honest check. If that trade-off is wrong, the fix is to
   make offline mode refuse to print `ok` for a record older than some age.
2. **288 KB of third-party market data is now committed to the repository.**
   That is the reproducibility mechanism, so it has to be tracked, and the size
   is trivial. Less trivial: it is Yahoo's data, and redistributing it in a
   public repo is a slightly stronger claim than merely fetching it. I think
   this is fine for a capstone — the volume is negligible and the purpose is
   plainly research — but it is a judgement call I made rather than one you
   asked for, and it is the kind of thing worth a sentence in the README.
3. **The narrowed `Instrument` definition encodes a sourcing constraint in a
   domain term.** "Single bonds and options are out of scope" is true of
   *Veritas*, not of the word *instrument* — a broker's glossary would not say
   that. The alternative is to leave `Instrument` domain-accurate and put the
   restriction in the Target State's non-goals. I put it in the Glossary because
   that is where someone about to write `dim_instrument` will actually look, and
   a constraint nobody reads is not a constraint. But it does make the Glossary
   slightly a description of our situation rather than of the domain, which is
   the drift the Glossary rule exists to resist. Reasonable people would differ.
4. **Yahoo worked flawlessly, which is the least trustworthy kind of evidence.**
   Twelve symbols, twenty rapid requests, zero failures, five years of null-free
   bars. That tells us it works today, from this IP. It says nothing about
   whether it works from a grader's machine. DEBT-002 is the answer and should
   be paid early rather than at ingestion time.
5. **DEBT-004's 1% threshold in the script is arbitrary.** I picked it so the
   FX-date `NOTE` fires on today's data. The number that actually matters is the
   Gold Question Set's result-comparison tolerance, which does not exist yet.
   When it does, that threshold should be derived from it, not left at 1%.
6. **The Frankfurter User-Agent block cost real time and is worth remembering.**
   `curl` worked, `urllib` got HTTP 403 on the identical request. Nothing about a
   403 suggests "add a User-Agent header" — it reads as "you are blocked, find
   another source", and I nearly recorded Frankfurter as unavailable. Any HTTP
   source that seems dead should be re-checked under a named agent before being
   written off.

**Language**

Three terms added and one narrowed. All four arose from real behaviour observed
in the data rather than from design speculation, and all were approved on
2026-08-03, so all are now `agreed` and may enter code.

- **`Market Price`** — the unadjusted closing price at which an Instrument
  traded on a date, in its Quotation Currency. The only price a Position may be
  marked at. Names the column in `fct_instrument_price`, and makes "do not mark
  at adjusted close" enforceable rather than conventional.
- **`Adjusted Close`** — a back-adjusted series that rewrites historical prices
  as corporate actions occur. Correct for returns, forbidden for marking
  Positions or computing P&L. Registered as an **anti-pattern**, in the same
  spirit as `Shadow Metric`. *Alternative considered:* not registering it at all
  — rejected, because an unnamed hazard is one nobody can be held to avoiding.
- **`Quotation Currency`** — the currency *and minor unit* an Instrument's
  Market Price is quoted in. Distinct from `Reporting Currency`. Needed for the
  `GBp`/`GBP` normalisation, without which every LSE figure is 100x too large
  and still entirely plausible.
- **`Instrument`** — narrowed from "equity, ETF, bond, future, option, or
  currency pair" to "equity, ETF, future, or currency pair". The first amendment
  to an already-`agreed` term; the reason is recorded in the term itself and in
  [DEBT-003](../debt-ledger.md).

Two rows added to **Section C — distinctions we must not blur**: `Adjusted
Close` vs `Market Price`, and `Quotation Currency` vs `Reporting Currency`.

**Two tables renamed on Amino's ruling:** `dim_fx_rate` -> `fct_fx_rate` and
`dim_instrument_price` -> `fct_instrument_price`. Both are dated observations
that grow daily, which is a fact-table shape; only their subject
(`dim_instrument`) is a dimension. Caught because registering `Market Price`
forced the question of where it lives, which then exposed the already-agreed
`dim_fx_rate` as misnamed. No DDL exists yet, so the rename cost nothing — which
is the argument for registering language before writing code, not after.

One collision checked and cleared: `Market Price` against `FX Rate`. They are
different quantities — an Instrument's price versus a rate between two
currencies — and the check surfaced a rule now written into the findings doc:
**Yahoo's `EURUSD=X` must never be used as an `FX Rate`**, because `FX Rate` is
registered as the ECB reference rate from Frankfurter. Two sources for one
concept is precisely the synonym disease Non-Negotiable #1 exists to prevent.

Terms did enter code this Sub-step, in `check_data_availability.py`:
`Market Price`, `Quotation Currency`, `Adjusted Close`, `FX Rate`, `Trade`,
`Trade Date`, `Settlement Date`, `Client`, `Account`, `Commission`, `Fee`,
`Rebate`, `Gross Revenue`, `Net Revenue`, `Traded Notional`, `Trade Count`,
`Reporting Currency`. All spelled as registered.

**Rulings applied — 2026-08-03**

Amino ruled on all three before this Sub-step closed, so the sections above are
written as resolved rather than pending:

- **R1 — narrowed.** Single bonds and options excluded; paid vendor recorded as
  [DEBT-003](../debt-ledger.md). Yahoo retained for key-free reproducibility.
- **R2 — approved.** All three terms and both distinction rows are `agreed`.
- **R3 — confirmed.** Yahoo stays, with the snapshot mitigation as the defence.
- **Additionally:** the spike was promoted from a throwaway to a committed,
  reproducible script; `fct_` replaces `dim_` for both dated series; and the
  FX-date evaluation trap got an explicit Trigger as
  [DEBT-004](../debt-ledger.md).

With the data gate passed and the rulings in, **`target-state.md` is now
`agreed`** and Sub-step 1.3 (the three founding ADRs) is unblocked.

---

## Sub-step 1.3 — Record the founding decisions

**What changed**

Three ADRs, one per decision that shapes every later Step and would otherwise
look arbitrary to someone reading the repo cold. No code, no dependencies.

- **[ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md) — the
  Semantic Layer is the retrieval corpus.** The central bet. Retrieval runs over
  Semantic Entries, never over warehouse schema or prose documentation. The
  argument that carries it: `fct_trade` holds `commission`, `rebate` and `fee`,
  so a complete and accurate schema still cannot say whether "revenue" means
  Gross or Net. The ambiguity is not in the schema, so retrieving the schema
  better answers a question nobody asked.
- **[ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md) —
  DuckDB is the Warehouse, reached only through an adapter.** Framed as two
  decisions rather than one, because only the second is expensive to reverse:
  *which engine* (cheap to change) and *is the choice allowed to leak* (a seam,
  and therefore not a place debt may be taken).
- **[ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md) — the
  Validation Gate is deterministic code.** No LLM in the allow/reject decision.
  LLM-as-judge stays in Evaluation, measuring after the fact, never gating.

Also updated: the ADR index; the stale line in `data-availability.md` §R3 (see
below); and Current State, including its Resume-here pointer.

**Verification**

Docs-only, so verification is that the framework still wires up and that every
link in the tree resolves — including the eleven new cross-references the ADRs
introduce.

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       552 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr          592 words
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
exit=0
```

`verify_framework.py` already checks that every relative link in the documents
resolves — `check_links()`, at `.claude/scripts/verify_framework.py:80` — so the
exit code above covers the ADR cross-references too.

The language sweep is now a committed script rather than something I ran inline
and transcribed. It **fails**, on purpose, and its failures are the finding
described under **Language**:

```
$ uv run python .claude/scripts/check_language.py
  glossary: 71 registered terms
  Target State components (9)
    UNREGISTERED  Warehouse
    agreed        Semantic Layer
    UNREGISTERED  Ingestion
    UNREGISTERED  Retrieval
    UNREGISTERED  Copilot
    agreed        Validation Gate
    UNREGISTERED  Interface
    UNREGISTERED  Observability
    UNREGISTERED  Evaluation
  proposed terms: 0 · python files scanned: 3
  abbreviations: 23 registered in the Glossary, 15 exempt, 0 unrecognised

FAIL — 7 problem(s)
  - target-state.md names component 'Warehouse', which has no Glossary row (it will become a directory or module in Step 002)
  - target-state.md names component 'Ingestion', which has no Glossary row (it will become a directory or module in Step 002)
  - target-state.md names component 'Retrieval', which has no Glossary row (it will become a directory or module in Step 002)
  - target-state.md names component 'Copilot', which has no Glossary row (it will become a directory or module in Step 002)
  - target-state.md names component 'Interface', which has no Glossary row (it will become a directory or module in Step 002)
  - target-state.md names component 'Observability', which has no Glossary row (it will become a directory or module in Step 002)
  - target-state.md names component 'Evaluation', which has no Glossary row (it will become a directory or module in Step 002)
exit=1
```

It goes green when the seven component names are registered or renamed. Until
then it is the open question, stated by a script rather than by me.

**Deliberately left undone**

- **The fourth ADR — snapshot-and-replay — was not written.** Deferred to the
  ingestion Step, where the decision actually binds, by agreement with Amino
  before starting. [DEBT-002](../debt-ledger.md)'s trigger already forces it to
  surface there, so nothing depends on remembering.
- **`data-availability.md` §R3 said the snapshot pattern "should also become an
  ADR in Sub-step 1.3."** Deferring made that line false, so it was rewritten
  rather than left to rot — Non-Negotiable #3. The rewrite also records Amino's
  clarification that snapshot-and-replay is the mitigation for *undocumented and
  unversioned* sources specifically (Yahoo), not for every external source;
  Frankfurter and the SEC are documented and stable, and snapshotting them is a
  reproducibility convenience rather than a hedge against disappearance.
- **No new Debt Ledger entry.** Swept the diff and found no shortcut: the ADRs
  are `proposed` because that is the process, not because they were rushed. The
  ledger stands at 4 open.

**Look at this sceptically**

- **ADR-0002 is the weakest of the three,** and it is worth pushing on. Its
  "buys us" list is real, but the adapter's value is entirely contingent on an
  engine swap that may never happen — if Veritas lives and dies on DuckDB, the
  indirection bought nothing. The ADR says so explicitly rather than hiding it.
  Disagreeing is reasonable; the counter-argument is that the extension path is
  the project's second audience, and a seam is what makes that claim true rather
  than aspirational.
- **Whether Postgres was steel-manned hard enough.** It is already in the stack
  for Observability, so "use the database you already have" is genuinely
  attractive and I rejected it on write-contention and columnar-scan grounds at
  a scale where neither may bite. If you think one engine beats two here, that
  is a live disagreement and ADR-0002 is where to have it.
- **ADR-0003 concentrates risk on sqlglot** and now says so under costs. Both
  0002 and 0003 depend on it — one for dialect retargeting, one as the safety
  boundary. A single third-party parser under both the portability seam and the
  access-control check is worth a second look. It did not seem to warrant its own
  ADR, but that judgement could go the other way.
- **All three are `proposed`, not `accepted`.** Per the Glossary's status values
  that is your call, not mine. If you accept them, the status lines and the index
  need flipping.
- **`Copilot` and `Interface` are the shakiest of the seven unregistered names**
  below, since both are closer to product vocabulary than domain vocabulary. It
  may be right to register only some of them.

**Language**

No new terms coined; the ADRs use only `agreed` Glossary terms.

But the language sweep surfaced a **gap that predates this Sub-step**: seven of
the nine Target State component names have never been registered.

> 🆕 **TERM PROPOSAL** — `Warehouse`, `Ingestion`, `Retrieval`, `Copilot`,
> `Interface`, `Observability`, `Evaluation`.
>
> All seven have been used as capitalised component names since Sub-step 1.1 —
> in `target-state.md`, in `current-state.md`, and now in ADR-0002's title — yet
> none has a Glossary row. Only `Semantic Layer` and `Validation Gate`, of the
> nine components, are registered.
>
> **Why it matters now rather than then.** In prose this is a formatting
> inconsistency. In Step 002 it becomes a Non-Negotiable #1 problem: these names
> turn into directories and modules (`veritas/warehouse/`, `veritas/retrieval/`),
> and the rule says a domain noun must be registered *before* it names a code
> identifier. The Glossary already assigns `Lives in` paths to registered terms,
> so the two are meant to line up.
>
> **What I did not do:** register them myself. Coining seven terms unilaterally
> is exactly what Non-Negotiable #1 forbids, and `Warehouse` in particular needs
> a real definition — is it the DuckDB database, the star schema inside it, or
> the adapter boundary? ADR-0002 leans on all three readings and would read more
> precisely once that is settled.
>
> Agree, rename, narrow the list, or reject?

ADR-0002's Related section points at this proposal so the gap is discoverable
from the ADR itself rather than only from this review.

---

## Revisions from review — Sub-step 1.3, 2026-08-03

Amino's ruling on Sub-step 1.3 and the changes folded in. The section above is
left as written (a point-in-time record), except the two verification blocks,
which were the subject of a ruling and are replaced rather than annotated.

**Rulings received**

- **All three ADRs approved**, conditional on the corrections below. Statuses
  flipped `proposed` → `accepted`; the index updated.
- **ADR-0002 confirmed on both counts:** keep the adapter, because the engine
  *will* change; and DuckDB over a single Postgres for everything. The
  steel-manning question I raised is settled.
- **DEBT-002's scope clarified:** snapshot-and-replay is the mitigation for
  **undocumented and unversioned** sources, not for all external sources.

**Two root causes found, and fixed as causes rather than as symptoms**

1. **A citation that did not support its claim.** ADR-0001 said fine-tuning was
   "named as out of scope in the product brief" and linked it. The product brief
   says no such thing about fine-tuning *as a way to carry metric definitions*;
   its actual line — "Fine-tuning on historical/labelled data | Out of scope for
   the slice; noted, not built" — is about fine-tuning as a modelling technique,
   in a table of adjacent capability signals. I recalled the gist, found a line
   that resembled it, and let a link stand in for support.

   *Cause:* the Alternatives table rewards a crisp dismissal per row, and borrowed
   authority is the cheapest way to sound crisp. *Fix:* `CLAUDE.md`
   Non-Negotiable #4 and the `writing-an-adr` skill now require that **a claim
   about another document quotes the words it relies on**. A quote is
   self-verifying; a bare link is an invitation to assume. ADR-0001's row now
   quotes the line and says explicitly that it is adjacent, not authority.

2. **Two verification blocks that could not be re-run.** Both showed a truncated
   heredoc (`uv run python - <<'PY'`) as if it were a command, followed by a
   summary count. Neither is reproducible, and one of them —
   the link check — **duplicated `verify_framework.py:check_links()`**, which had
   already run and passed in the same message.

   *Cause:* `closing-a-substep`'s own rationalization table said *"docs-only
   change" → "verify the docs render and their links resolve"*, and I satisfied
   that literally by writing a fresh checker instead of looking in
   `.claude/scripts/` for one that existed. *Fix:* that table row now points at
   `verify_framework.py` by name and forbids hand-rolling a second link checker;
   two more rows cover inline scripts and summarised counts. `CLAUDE.md`
   Non-Negotiable #4 now states that evidence in a document comes from a
   committed script, and that a new check must be preceded by looking for an
   existing one.

   This rule was **already ruled on by Amino in Sub-step 1.2** and broken one
   Sub-step later, so **[DEBT-001](../debt-ledger.md)'s trigger has fired** —
   recorded there, with the partial payment below.

**What changed**

- **`.claude/scripts/check_language.py`** (new, committed) — the language sweep as
  an asserting script instead of a transcription. Checks that Target State
  component names are registered Glossary terms, that no `proposed` term has
  reached a code identifier, and that every abbreviation resolves. Partial
  payment of DEBT-001, which asked for mechanism instead of discipline.
- **Glossary** — a new **Abbreviations** section: 23 short forms expanded in one
  place, plus the deliberately-unexpanded list. This is the durable answer to
  "I could not find what DDL means", and `check_language.py` enforces it.
- **`CLAUDE.md`** — Non-Negotiable #4 gained *evidence comes from a committed
  script* and *citations quote*; a new **Writing conventions** section requires
  abbreviations expanded on first use and forbids unexplained bare numbers.
- **`writing-an-adr`** — every cost must now be classified *accepted*, *debt*, or
  *extension* in the same Sub-step, with a table saying where each goes. This is
  the forcing function discussed under **Tracking MVP extensions** below.
- **ADR-0001** — citation corrected; DDL, FAQ, MRR, LLM, MVP and FX expanded on
  first use; all four costs classified; a new **Open question 1** section holding
  the coverage-miss capture and metric-coherence design question.
- **ADR-0002** — a new **Why the adapter is not optional** section replacing the
  "seam, not fill" shorthand with the actual argument (some shortcuts get more
  expensive to fix over time; this is one, and the reason is how many places have
  to change). The cost-check cost rewritten from three lines to a full
  explanation of what a BigQuery dry run gives you, why DuckDB cannot give it,
  and the three honest differences that follow.
- **ADR-0003** — all five costs classified; UX and LLM expanded.
- **Debt Ledger** — DEBT-005 through DEBT-008 added; DEBT-001 updated with its
  fired trigger; index and counts refreshed to 8 open.

**Deliberately left undone**

- **The Extension Register is proposed, not built.** Amino asked how MVP
  extensions should be tracked and said they did not want a specific answer yet.
  The proposal is below; no register file exists. Until it does, the four new
  entries live in the Debt Ledger, which is the closest existing home and is
  where the classification rule currently points.
- **ADR-0001's Open question 1 is unresolved** — the knowledge-graph challenge is
  argued but not decided, and no ADR was written for it.
- **The seven unregistered component names** are still unregistered;
  `check_language.py` fails on exactly those and nothing else.

**Tracking MVP extensions — the answer to Amino's process question**

The question was whether Debt Ledger entries are the right home for full-MVP
extensions, and whether I would have remembered them unprompted.

**Honestly: partly not.** All four costs of ADR-0001 were already written down in
the ADR before Amino asked — so the *knowledge* was recorded and would not have
been lost. But nothing made any of them **actionable**. An ADR cost is a
statement; it has no trigger, no owner, and no moment at which anyone is obliged
to look at it again. The realistic outcome is that they would have sat in a
document nobody re-reads until one of them bit. Recording is not tracking, and I
had done the first while implying the second.

**The structural fix, applied this Sub-step:** `writing-an-adr` now requires
every cost to be classified *accepted* / *debt* / *extension* **at the moment it
is written**, because that is the only moment when the full context is loaded.
An ADR with a dangling cost is now unfinished by rule. That is what makes the
answer "no, structurally" rather than "yes, if I remember".

**The open half — where extensions should live.** Debt and extensions are
genuinely different things:

| | Debt | Extension |
|---|---|---|
| The current code is… | wrong, cheaply | right, for this scope |
| Repaying means… | fixing it | adding to it |
| Trigger | a condition that will fire | often "when the MVP is built" — a wish |

Conflating them corrupts the Ledger in two ways. "Open debt: 8" stops meaning
"8 shortcuts to repay", so the number loses its bite; and extensions arrive with
triggers that never fire, which the framework itself calls a wish rather than
debt.

**Proposed: an Extension Register** — `.claude/docs/extension-register.md`, a
third register beside the Debt Ledger and the ADRs. Each entry carries:

- what the full system needs that the slice does not have;
- **the seam it lands against** — the load-bearing field, because it is what makes
  "addition, not rewrite" a checkable claim rather than a hope;
- **what motivates it** — the ADR cost, non-goal, or scope boundary it answers,
  linked, so an extension can always be traced back to the decision that created
  it;
- **readiness** instead of a Trigger: what must be true before it is worth
  building.

The Target State's *Extension path* table becomes the register's summary view; it
already lists capability → seam, and only lacks the motivation link and status.

Under that split, of the four new entries: **DEBT-005** (drift) and **DEBT-007**
(authoring scale) are extensions; **DEBT-008** (access control) is genuinely both —
its first trigger, *before any real client data is loaded*, is real debt that
fires inside this project's life; and **DEBT-006** (ad-hoc exploration) is neither,
being a decision awaiting evidence. Not moved: Amino has not ruled, and inventing
a register mid-Sub-step is the kind of unilateral structure change the framework
exists to prevent.

**Look at this sceptically**

- **The classification rule adds ceremony to every future ADR.** Three
  classifications per cost, five costs per ADR, is real friction — and friction
  in a rule is how rules get skipped. The counter-argument is that this exact
  friction is what Amino had to supply manually this round.
- **`check_language.py` fails by design right now,** and a permanently red check
  trains people to ignore it. It is only acceptable because its failure is one
  specific open question with a definite resolution. If the component names are
  not settled soon, the check becomes noise and should be changed or removed.
- **The abbreviation rule was implemented as a Glossary table rather than as
  expansion in every document** — 57 first-use expansions across 12 files became
  23 Glossary rows plus expansion in the three ADRs. My reasoning: one lookup
  place beats 57 scattered parentheticals, and it is what a Glossary is *for*.
  But it is a looser reading of "always use complete text" than a literal one,
  and if you meant the literal one, the sweep is mechanical and I will do it.
- **The knowledge-graph analysis argues against a graph database and I may be
  wrong about scale.** My case rests on the corpus being hundreds of metrics, not
  millions. If the full MVP's semantic layer is much larger, or if the
  relationships turn out to be more open-ended than `derives_from` and
  `depends_on_columns`, the calculus changes and a property graph earns its keep.
- **DEBT-006 is a debt entry with no repayment**, which stretches what the Ledger
  is for. I wrote it as "for review, not for repayment" and gave it an
  evidence-based trigger, but a purist would say a decision-pending item is not
  debt at all and belongs somewhere else.

---

## Revisions from review — Sub-step 1.3, second pass, 2026-08-04

Amino's second ruling on Sub-step 1.3. Everything from the first pass was
approved and staged; this section is what changed after it.

**Rulings received**

- **Extension Register: build it.** Created as
  [`extension-register.md`](../extension-register.md) with five entries.
- **Knowledge graph: rejected, coherence work kept.** Recorded as
  [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks);
  ADR-0001's open question is now a decided section.
- **DEBT-006: the reasoning against ad-hoc exploration is correct.** Closed
  `accepted` permanently and promoted to a Target State non-goal.
- **DEBT-008: warehouse-native security replaces application-level**, rather than
  layering on top of it.

**What "real client data" means — the question that broke DEBT-008's trigger**

Amino asked which subset of public plus simulated data would count as "real data"
for DEBT-008's trigger *"before any real client data is loaded"*.

**The honest answer is: none of it, and that trigger could never have fired.**
Veritas uses real market data — FX Rates, Market Prices, instrument reference —
and all of it is public and non-sensitive. Every Client, Account, Trade, Cash
Movement and Position is synthetic by construction, and nothing planned changes
that. The sensitive axis is *client* data, and Veritas has none.

So a trigger that reads as the strongest in the Ledger was in fact unfireable —
which is exactly what the Ledger's own rule calls a wish rather than debt. Good
catch, and it is the clearest possible demonstration of why the Extension
Register was needed: the engineering half belongs in
[EXT-001](../extension-register.md#ext-001--warehouse-native-security-and-concurrency),
and what stays as debt is the part that *will* fire here — the honesty of the
access-control claim, triggered by the first README or Interface that makes one.

**What changed**

- **[`extension-register.md`](../extension-register.md)** (new) — EXT-001
  warehouse-native security and concurrency, EXT-002 Semantic Layer drift
  detection, EXT-003 metric authoring at scale, EXT-004 coverage-miss capture,
  EXT-005 Semantic Layer coherence checks. Each carries the **seam** it lands
  against and a **Readiness** condition instead of a Trigger, and each links back
  to the ADR cost that motivates it. The Target State's extension-path table is
  mapped onto the register, with rows that are recorded but not yet detailed
  marked as such.
- **Debt Ledger** — DEBT-005 and DEBT-007 `moved` (stubs retained so identifiers
  are never reused and links keep resolving); DEBT-006 `accepted`; DEBT-008
  narrowed to the claim-honesty debt and given a trigger that fires. A `moved`
  status and a debt-versus-extension test were added to the legend. Now 5 open,
  1 accepted, 2 moved.
- **ADR-0001** — open question resolved into *How the metric set stays coherent*;
  all four cost classifications repointed at EXT entries or at the permanent
  acceptance.
- **ADR-0002, ADR-0003** — cost pointers repointed; ADR-0002's access-control
  cost now states that EXT-001 **replaces** the application-layer check.
- **Target State** — the ad-hoc exploration non-goal, and a new
  *What "credential-free" means* section answering the credentials question below.
- **`CLAUDE.md`** and **`writing-an-adr`** — the debt-versus-extension test, and
  guards against the classification rule decaying into a rubber stamp.
- **`check_language.py`** — two real bugs fixed, see Verification.

**The credentials question**

Amino asked whether "credential-free `git clone` bring-up" excludes an
OpenAI API key. It does not, and the rule it rests on was never written down
despite driving three decisions. Now stated in the
[Target State](../design/target-state.md):

> A credential the grader already has by virtue of taking the course is
> acceptable. A credential unique to this project is not.

A Large Language Model key is inherent to the project category — every capstone
on this course needs one, and the course assumes it — so it costs a grader
nothing. A market-data vendor key is friction Veritas alone would impose. The
distinction is **obtained versus assumed**: a credential the grader must go and
get, versus one they already hold or that `docker-compose` generates.

**This is my reading and is not checked against the rubric text**, which is not
in the repository. If Large Language Model keys are not in fact assumed, the
fallback is an Ollama-only default path, and that is worth knowing before the
Copilot Step rather than after.

**Verification**

Both committed checks, run after every change above:

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       652 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr          967 words
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
exit=0
```

```
$ uv run python .claude/scripts/check_language.py
  glossary: 79 registered terms
  Target State components (9)
    proposed      Warehouse
    agreed        Semantic Layer
    proposed      Ingestion
    proposed      Retrieval
    proposed      Copilot
    agreed        Validation Gate
    proposed      Interface
    proposed      Observability
    proposed      Evaluation
    -> 7 awaiting Amino; none may enter code until agreed
  proposed terms: 8 · python files scanned: 3 · identifiers: 184
  abbreviations: 23 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
exit=0
```

`check_language.py` now passes where it failed last pass — but **not because the
question was answered.** It passes because the seven names are now *registered*,
and `proposed` is the correct state for a term under discussion. The check that
matters has moved: it fails the moment any `proposed` term reaches a code
identifier, which is Step 002's first act.

**Two real bugs found in `check_language.py` while getting there**, both worth
recording because both were the check lying rather than the documents being
wrong:

1. **Status parsing ignored emphasis.** `**proposed**` did not match the
   `{agreed, proposed, retired}` set, so every new term read as having no status
   and the proposed-in-code check silently had nothing to check. Fixed by
   stripping markup before matching.
2. **The proposed-in-code check grepped raw text.** It fired on `check_data_availability.py`
   for the words "warehouse", "ingestion" and "evaluation" — all of which appear
   in *docstrings*, explaining the domain. The rule is about identifiers; the
   Glossary governs what things are *called*, not whether a word may be written
   down. Now parsed with `ast`, collecting only names the file actually defines —
   184 of them across three files.

The second is the more instructive: a check that fires on prose would have
trained us to ignore it within a week.

**Deliberately left undone**

- **The consistency sweep for the component terms.** `target-state.md`,
  `current-state.md`, `product-brief.md` and ADR-0002 all use these words now.
  Revisiting them before the names are settled would be doing the work twice; the
  Glossary section says so explicitly.
- **Splitting Glossary Section A** into components versus artifacts. Proposed as
  an option, not taken — it restructures an `agreed` section and was not asked
  for.
- **No ADR for the coherence design.** EXT-005 records the decision and the
  reasoning; an ADR is warranted only if the property-graph question reopens.

**Look at this sceptically**

- **The Extension Register could become a graveyard.** Its entries have Readiness
  conditions rather than Triggers, which is honest but weaker — nothing forces
  anyone to look. The Debt Ledger at least has firing conditions. If this project
  ends at the capstone, all five entries are simply never read again, and the
  register will have been documentation for an audience of nobody. The
  counter-argument is that the register exists precisely so the *Ledger* stays
  sharp, and that value is realised immediately regardless.
- **Moving two entries out dropped open debt from 8 to 5,** which flatters the
  project. I believe the reclassification is right on the merits — both really
  are "correct for this scope" — but it is worth naming that the reclassifier
  benefits from the reclassification.
- **`Answer Pipeline` may be worse than `Copilot`.** My argument is that
  `Copilot` names both the product and a component inside it. But "pipeline"
  implies a linear dataflow, and the flow has branches: a failed Validation Gate
  does not continue, an unresolved Ambiguous Term goes back to the user. If that
  bothers you, `Orchestrator` is more accurate and less evocative.
- **The credentials rule is inferred, not read.** I reconstructed it from what
  the criteria map already claims and from how the course works. It is the load-
  bearing justification for three decisions, and it rests on an assumption I have
  not verified against the rubric.
- **EXT-001 says to delete the application-layer access check** when
  warehouse-native security lands. That follows Amino's instruction and the
  no-redundancy argument is sound, but it is worth flagging that defence-in-depth
  is the security-industry default, and the thing genuinely lost is a pre-execution
  rejection with a specific reason. EXT-001 names that loss and suggests keeping a
  non-enforcing pre-flight check; if that suggestion is itself unwanted, say so
  now rather than at migration time.

---

## Revisions from review — Sub-step 1.3, third pass, 2026-08-04

Amino's rulings on the component terms and the credentials question, and the
consistency sweep that followed. **This closes Sub-step 1.3 and Step 001** —
nothing is outstanding.

**Rulings received**

- **Credentials reading accepted.** The Large Language Model key stays an allowed
  dependency. **Every allowed credential must be listed in `README.md`**,
  including the ones `docker-compose` generates.
- **`veritas/copilot` → `veritas/orchestrator`.**
- **`veritas/interface` → `veritas/app`.**
- **The other six component terms are fine as proposed.** No split of Glossary
  Section A into components versus artifacts for now.

**One inference I made, flagged because it went beyond the instruction**

Both rulings named *directories*. I renamed the **Glossary terms** to match —
`Copilot` → `Orchestrator`, `Interface` → `App` — because Non-Negotiable #1
requires code identifiers to match Glossary terms, and leaving the term
`Interface` beside a directory `veritas/app/` would be the precise thing that
rule forbids: two names for one concept. Both old terms are in
[Retired terms](../glossary.md#retired-terms) with pointers.

If you meant the directories to differ from the component names, say so — but I
do not think you did, and the rename is cheap now and expensive after Step 002
creates the packages.

**`Orchestrator` over my own recommendation.** I had proposed `Answer Pipeline`
and argued against it in the same breath: "pipeline" implies a straight line, and
this flow branches — a failed Validation Gate stops, an unresolved Ambiguous Term
returns to the user. `Orchestrator` was the alternative I flagged as *more
accurate and less evocative*, and accuracy is the right trade for a module name.
The reasoning is recorded in the Glossary so the rejected candidate stays visible.

**A second reason for `App` emerged during the sweep**, which had not been in the
original argument: the Zoomcamp rubric has its own criterion named *Interface*.
The word was carrying both our component and the grader's scorecard line. The
criteria map still says "Interface" in the left column, because that column is
the grader's vocabulary rather than ours, and it now says so explicitly.

**The sweep**

Every document that used an old name was revisited in the same Sub-step:

- **`target-state.md`** — components table (two renames), the Orchestrator Step
  reference, and the criteria map row disambiguated.
- **`current-state.md`** — components table, the Resume-here block (the question
  it described is answered), and the Known-gaps paragraph that described the
  component-name gap as open.
- **ADR-0002, ADR-0003** — `Interface` → `App` in the concurrency cost, the
  access-control cost, and the Gate-honesty mitigation.
- **Debt Ledger** — DEBT-008's location, trigger, index row, and the "App Step"
  reference.
- **Extension Register** — EXT-001's concurrency clause.
- **Glossary** — both renames recorded inline on the rows, the Domain Language
  banner updated, the component-terms discussion rewritten from *proposed* to
  *agreed* with the decisions and the rejected candidate, and a Retired terms
  table created.

**Deliberately not swept: the Step Reviews.** Sub-steps 1.1 through 1.3 still say
`Copilot` and `Interface` where they said them at the time. They are
point-in-time records, and rewriting them would erase the history that makes the
renames traceable — the same convention the 2026-07-23 revision section
established. One consequence to know: a full-text search for "Copilot" will hit
this file, and that is correct rather than stale.

**Lowercase `copilot` survives on purpose.** "Veritas is a natural-language
analytics copilot" and "a metrics copilot, not a database browser" both still
read correctly and keep the thread to the product brief's "Analytical copilots".
Freeing the word for prose was the point of renaming the component.

**The README credential list**

Recorded in [Target State → What "credential-free" means](../design/target-state.md#what-credential-free-means)
as a table of what the README must state: the Large Language Model key (required,
with the Ollama fallback for a reviewer who has none), the Postgres and Grafana
credentials `docker-compose` generates, and — stated positively, because it is a
deliberate result — that **no data source needs a key at all**.

Two Ledger entries already fire on the README being written, so all three land in
one pass: [DEBT-002](../debt-ledger.md) on the reproducibility claim and
[DEBT-008](../debt-ledger.md) on the access-control claim.

**Verification**

```
$ uv run python .claude/scripts/verify_framework.py
PASS — framework is wired up correctly
exit=0

$ uv run python .claude/scripts/check_language.py
  glossary: 81 registered terms
  Target State components (9)
    agreed        Warehouse
    agreed        Semantic Layer
    agreed        Ingestion
    agreed        Retrieval
    agreed        Orchestrator
    agreed        Validation Gate
    agreed        App
    agreed        Observability
    agreed        Evaluation
  proposed terms: 0 · python files scanned: 3 · identifiers: 184
  abbreviations: 23 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
exit=0
```

All nine components `agreed`, zero `proposed`. The sweep was verified by grep as
well as by the checker: the only capitalised `Copilot` and `Interface` left
outside the Step Reviews are the Glossary's own rename records, its Retired terms
table, and the rubric criterion name — each of which is meant to be there.

**Look at this sceptically**

- **I renamed Glossary terms when you named directories.** Justified by
  Non-Negotiable #1, but it is still me extending an instruction. It is the one
  change in this pass worth checking you agree with.
- **`App` is a weak term.** It carries one real constraint — *never renders a
  bare number* — and beyond that it is a plain name for a plain thing. I argued
  earlier it was the one genuine drop candidate, and registering it is the
  slightly heavier option. It earns its place mainly by making the directory name
  legal.
- **`check_language.py` passes everywhere now, which is when a checker is least
  trustworthy.** It has never caught a regression, only the backlog it was written
  to find. Its real test is Step 002, when the first `proposed` term meets the
  first code identifier.
- **The Glossary's component-terms section is long** for what is now a settled
  question. I kept the rejected alternatives and the counter-arguments because
  someone will propose `Copilot` again in six months, but a reader who just wants
  the definitions has more to scroll past.

---

## Closing note — Sub-step 1.3

**This Sub-step failed the one-commit test, and it is worth saying so before
Step 002 is planned.**

`CLAUDE.md`: *"One Sub-step = one commit. If a Sub-step cannot be described in a
single commit message without the word 'and', it is two Sub-steps."*

Sub-step 1.3 was planned as **three ADRs**. It shipped three ADRs, a new
Extension Register, a new committed check script, three framework rule changes,
eight Glossary component terms with two renames, four Debt Ledger entries and a
reclassification of three of them. No honest commit subject covers that without a
conjunction.

**The cause is benign and worth distinguishing from scope creep.** Every addition
came from Amino's review across three passes — the register, the script, the
renames and the rule changes were all asked for, none were volunteered. A
Sub-step that grows because the reviewer found real problems is the process
working, not failing.

**But the effect is the same**, and two things follow for planning Step 002:

1. **Review-driven growth is not currently accounted for anywhere.** The plan
   sized 1.3 at three documents; it delivered fifteen files. If Step 002's
   Sub-steps are sized the same way, the same overrun should be expected — most
   of it arriving after the first hand-over, when the work looks finished.
2. **The natural split, in hindsight**, was 1.3 (the ADRs) and a separate 1.4
   (the framework and register work the ADRs exposed). That was not visible when
   1.3 was planned, because the register only became necessary once the ADR costs
   were written down and had nowhere to go. Splitting mid-flight is what
   `planning-a-step` calls for when a Step is discovered to be too large; I did
   not do it, and should have offered it at the second review pass.

Recorded here rather than on the Ledger: nothing is broken in the repository, and
the lesson is about sizing rather than about code.
