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
   is *earned*, versus Cash Movement on the date money moves. If EXANTE-style
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
