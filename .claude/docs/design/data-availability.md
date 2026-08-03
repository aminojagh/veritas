# Data Availability

**The gate on the Target State.** Sub-step 1.2 of
[Step 001](../plan/step-001-target-state-design.md). Before the design is marked
`agreed`, prove that every source it assumes can actually be obtained, key-free,
at the scale needed to build *and test* Veritas.

**Checked:** 2026-08-03 · **Verdict: GO.** All three rulings decided the same
day — see [Rulings](#rulings).

## Reproducing this check

Every claim in this document is produced by one script, not transcribed by hand:

```bash
uv run python .claude/scripts/check_data_availability.py            # offline, deterministic
uv run python .claude/scripts/check_data_availability.py --refresh  # re-hit every source live
```

Default mode reads committed snapshots in `data/snapshots/` and re-executes the
join spike for real, so the numbers reproduce exactly on any machine whether or
not the upstream sources are alive. `--refresh` re-probes every source and
rewrites `data/snapshots/probe-results.json`. The script **exits non-zero** if a
source stops answering, if a wrong-number trap disappears, or if any Section-C
distinction collapses — so this gate cannot silently go stale, and the exclusion
of bonds and options is re-tested on every refresh rather than assumed.

---

## Verdict by source

| Source | What it must provide | Result |
|---|---|---|
| **FX Rates** — Frankfurter | ECB reference rates, key-free, daily history | ✅ GO — unconditional |
| **Instrument reference data** — NASDAQ Trader + SEC | Real Instrument identifiers and names | ✅ GO — unconditional |
| **Market prices** — Yahoo chart endpoint | Daily closes for held Instruments | ◐ GO — **but the only key-free option is unofficial** |
| **Synthetic activity** — seeded simulator | Trades/Cash Movements/Positions that exercise every distinction | ✅ GO — proven by spike |

The Target State's assumption that FX and market data are **real** while client
activity is **synthetic** holds. Nothing in the design needs to change
structurally. The three rulings below are scope questions, not redesigns.

---

## 1. FX Rates — Frankfurter ✅

`https://api.frankfurter.dev/v1/…` — key-free, no registration, no rate limit
encountered. Backs the `FX Rate` Glossary term as registered.

- **Currencies:** 30+, including every one Veritas needs — USD, GBP, JPY, CHF,
  AUD, HKD, SGD against a EUR base.
- **History:** a full-year time-series request returned in ~0.3s.
  2025 gave **256 daily rates**.
- **Gaps are real, not errors.** Weekends are absent, plus exactly 6 ECB
  holidays in 2025 (1 Jan, 18 & 21 Apr, 1 May, 25 & 26 Dec). The warehouse needs
  a **fill-forward rule**: the FX Rate for a non-publishing date is the most
  recent published rate at or before it. The spike implements this and it works.
- **Helpful quirk:** requesting a range starting `2025-01-01` returns
  `start_date: 2024-12-31` — the API back-fills to the last rate before the
  requested start, which is exactly what fill-forward needs.
- **Publication lag:** the latest rate on 2026-08-03 (Monday) was 2026-07-31
  (Friday). ECB publishes ~16:00 CET on working days. Any "today" question must
  tolerate a one-to-three-day-old FX Rate.
- **It rejects the default Python User-Agent.** Frankfurter sits behind
  Cloudflare and returns **HTTP 403** to `Python-urllib/3.x` while serving the
  byte-identical request under any named agent — confirmed both ways round
  (curl sending the urllib agent gets 403; urllib sending a curl agent gets
  200). This is a hard requirement of the FX ingestion path, not politeness, and
  it fails in a genuinely misleading way: a 403 reads as "blocked, find another
  source" when the fix is one header. The script sends a descriptive agent with
  a contact address, which also satisfies the SEC's fair-access policy.

## 2. Instrument reference data ✅

Two official, key-free sources, both live:

- **NASDAQ Trader symbol directory** —
  `nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt`, 345 KB, pipe-delimited.
  Carries `Symbol`, `Security Name`, `ETF` flag, `Test Issue`, round lot size.
  The ETF flag is directly useful: it populates the instrument-type axis of the
  **by instrument type** Dimension Definition without hand-labelling.
- **SEC `company_tickers.json`** — 798 KB, ticker → CIK → registered name.
  Official, key-free (requires a `User-Agent` with contact details).

Together these give a real `dim_instrument` for US-listed names. Non-US
Instruments (SAP.DE, VOD.L, 7203.T) come from the price source's own metadata,
which returns exchange, currency and instrument type per symbol.

## 3. Market prices ◐ — the open question, now answered

This was the question deferred from Sub-step 1.1. **It has a workable answer and
a real caveat.**

**What was tried:**

| Candidate | Key-free? | Result |
|---|---|---|
| **Stooq** CSV | yes | ❌ **Dead.** Returns HTTP 200 but the body is a JavaScript anti-bot challenge, not CSV. Unusable without a browser. |
| **Yahoo** `query1…/v8/finance/chart` | yes | ✅ Works. Clean JSON, no key. |
| Alpha Vantage, Tiingo, EODHD, Polygon, Finnhub, Twelve Data, Nasdaq Data Link | **no** | All require registration — fails the rubric's key-free reproducibility criterion. |
| **US Treasury** `fiscaldata` | yes | ✅ Works, but only average interest rates by security type — not individual bond prices. |

**Yahoo coverage** — every Instrument type in the Glossary except two, across
four currencies, all returning full OHLCV plus adjusted close:

| Type probed | Symbols | Result |
|---|---|---|
| Equity | AAPL (USD), SAP.DE (EUR), VOD.L (GBp), 7203.T (JPY) | ✅ |
| ETF | SPY, IWDA.AS, TLT, BNDX | ✅ |
| Future | ES=F, GC=F | ✅ |
| Currency pair | EURUSD=X | ✅ (but see the FX Rate note below) |
| Index | ^GSPC | ✅ |
| **Bond** (individual) | CUSIP/ISIN forms | ❌ **404.** Only yield indices (`^TNX`) exist. |
| **Option** | AAPL chain | ❌ **HTTP 401.** Requires an authenticated session; no historical option prices at all. |

**Quality:** a 5-year daily AAPL request returned **1,255 bars, zero nulls**
across open/high/low/close/volume. 20 rapid sequential requests all returned
200 — no rate limiting at the volume Veritas needs.

**Do not use Yahoo for FX Rates.** `EURUSD=X` works, but the `FX Rate` Glossary
term is registered as *the ECB reference rate from Frankfurter*. Two sources for
one concept is precisely the synonym disease Non-Negotiable #1 exists to prevent.
Frankfurter is the only FX Rate source.

### Two wrong-number traps found

Both are exactly the failure Veritas exists to prevent — a correct program
computing the wrong number — and both are now handled in the spike.

1. **`close` vs `adjclose` diverge on 95.5% of bars** (1,198 of 1,255 for AAPL).
   Adjusted close is back-adjusted for splits and dividends, so it silently
   rewrites history: AAPL's 2021-08-02 close was 145.52 but its adjusted close
   is 141.85 today, and will be different again next year. Marking a Position at
   adjusted close makes Account Value, Realised P&L and Unrealised P&L all
   subtly wrong *and irreproducible*. Positions must be marked at unadjusted
   `close`.
2. **London quotes in pence.** VOD.L returns currency `GBp`, not `GBP` — a
   factor-of-100 error in Traded Notional, Commission and every downstream
   metric, which would look entirely plausible. Any price ingestion must
   normalise minor units before anything touches the warehouse.

Both are now Glossary terms — see [Rulings](#rulings), R2.

## 4. Synthetic activity ✅ — proven, not asserted

`run_join_spike` in the check script generates seeded synthetic Trades over a
window straddling the Q1/Q2 2025 boundary with T+2 settlement, joins them to
**real** Market Prices and **real** FX Rates, and computes each Section-C
distinction. Three Clients, five Accounts — one Client holding three, so Client
and Account cannot be conflated. Run the script for the current figures; it
asserts each distinction and fails the run if any collapses.

**What this proves:** the three sources genuinely join, and synthetic activity
can be made rich enough that each distinction is a *different number* rather
than a definitional nicety. Gross and Net Revenue separate by ~39%, accrual and
cash basis by ~24%. A Gold Question Set built on this data can distinguish a
right answer from a plausible one.

**One honest caveat, now on the Ledger.** The FX-date distinction moved the
number by only **0.08%**. The Glossary says choosing Trade Date over Settlement
Date "moves the number twice" — true in direction, but over a T+2 lag in a calm
FX period the second move is small enough to hide inside rounding. The script
prints a `NOTE` whenever that delta falls below 1%. Tracked as
**[DEBT-004](../debt-ledger.md)**, triggered when the Gold Question Set is
built: a gold question turning on Trade Date versus Settlement Date must use a
window where the two FX Rates differ by more than the comparison tolerance, or
be left out and the limitation stated. Otherwise Execution Accuracy would score
a wrong answer as correct on precisely the distinction Veritas exists for.

---

## Rulings

Three, all narrow, **all decided by Amino on 2026-08-03**. None changed the
structure of the Target State, which is now `agreed`.

### R1 — Instrument type universe (bond, option) → **narrowed**

**Decided:** narrow the `Instrument` definition to exclude single bonds and
options — option (a) below. Keep Yahoo and keep key-free reproducibility. The
paid-vendor path is recorded as a future setup step in
**[DEBT-003](../debt-ledger.md)**, triggered by any requirement to hold a single
bond or an option, or by those instruments becoming obtainable key-free.

The Glossary's `Instrument` term now reads "equity, ETF, future, or currency
pair". The check script re-probes bonds and options on every `--refresh` and
fails if either becomes obtainable, so the exclusion cannot quietly go stale.

The original analysis, kept as the record of why:

The Glossary defined **Instrument** as "equity, ETF, bond, future, option, or
currency pair". Individual bonds and options have **no key-free price source**.
Options are not obtainable at any price — there is no historical option price
data outside paid vendors.

The two candidates weighed:

- **(a) Narrow the traded universe** to equity, ETF, future and currency pair,
  amending the Glossary definition. Bond exposure is still representable through
  bond ETFs (TLT, BNDX both work), which is how most brokerage clients hold
  bonds anyway. It keeps every price in the warehouse real. **Chosen.**
- **(b) Keep bond and option as types** and mark those Positions with simulated
  prices. Rejected: it costs the "market data is real" claim, which is a
  load-bearing part of the project's framing.

### R2 — Term Proposals for the two traps → **approved**

**Decided:** all three terms and both Section-C distinction rows approved, and
are now `agreed` in the Glossary. They may enter code.

**Market Price**: the unadjusted closing price at which an Instrument traded on
a date, in its Quotation Currency. The only price a Position may be marked at.
Names the column in `fct_instrument_price` and makes the rule enforceable rather
than remembered.

**Adjusted Close**: a back-adjusted price series that rewrites historical prices
for splits and dividends. Correct for computing returns, **forbidden** for
marking Positions or computing P&L. Registered as an anti-pattern, in the same
spirit as Shadow Metric — the value of the term is that it names the thing we
must not do.

**Quotation Currency**: the currency *and minor unit* an Instrument's Market
Price is quoted in, which is not always its major currency — LSE quotes in pence
(`GBp`), not pounds. Distinct from Reporting Currency. Normalising to major
units is a required ingestion step.

Both `FX Rate` and `Market Price` were also moved from `dim_` to `fct_` tables:
each is a dated observation that grows daily, which is a fact-table shape. Only
their subject, `dim_instrument`, is a dimension.

### R3 — The Yahoo dependency → **confirmed**

**Decided:** confirmed. Yahoo stays, to preserve key-free reproducibility, with
the snapshot mitigation as the defence. Recorded as
**[DEBT-002](../debt-ledger.md)**.

Market prices rest on an **unofficial** endpoint. It is key-free (so it satisfies
the rubric's reproducibility criterion literally), it is what the whole retail
Python ecosystem uses, and it worked flawlessly across 12 symbols and 20 rapid
requests — but it carries no stability or terms guarantee and could break without
notice.

The mitigation, and the reason this is a GO rather than a blocker: **snapshot
the fetched data into the repository**, and have ingestion read the snapshot by
default with a refresh flag to re-fetch. That makes the build reproducible *even
if Yahoo disappears* — a stronger reproducibility story than live-fetching from
any source, official or not.

The check script already works this way, so the pattern is proven rather than
planned; what remains is applying it to the real ingestion pipeline, which is
DEBT-002's trigger. It should also become an ADR in Sub-step 1.3.

---

## Consequences for the Target State

No structural change; `target-state.md` is now **`agreed`**. Its Ingestion and
Warehouse rows were updated to record these specifics:

- **FX Rates** come from **Frankfurter only** — never Yahoo's `EURUSD=X`, which
  would be a second source for one concept — with a fill-forward rule for
  non-publishing dates and a descriptive User-Agent.
- **Market Prices** come from Yahoo, **snapshotted into the repo**, marked at
  unadjusted close, normalised for minor units.
- **Instrument reference data** comes from NASDAQ Trader and SEC.
- The traded **Instrument** universe is equity, ETF, future and currency pair
  (R1). Bond exposure is via bond ETFs.
- `FX Rate` and `Market Price` live in `fct_fx_rate` and `fct_instrument_price`.

Sub-step 1.3 (the founding ADRs) is unblocked.
