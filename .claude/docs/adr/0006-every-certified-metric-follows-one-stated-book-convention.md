# ADR-0006 — Every Certified Metric follows one stated book convention

- **Status:** accepted

## Context

Every figure a Certified Metric returns rests on a judgement: which cost convention a
profit is computed under, which of two dates a period filter keys on, which rate a
foreign amount converts at. Each judgement has two defensible readings, both give a
plausible number, and a reader cannot tell from the number which was taken. That is
the Shadow Metric failure at the level of the book itself, and Veritas exists to
prevent it: a number nobody can trace is a number nobody should trust.

The conventions are also schema. `fct_position_snapshot` carries one Cost Basis per
holding, the two movement tables carry amounts, and the simulator writes both.
Changing a convention means changing the tables, the simulator and every Metric
Definition that reads them — which is why it is recorded here and not only in code.

## Decision

The book follows one convention per judgement, and each Certified Metric states the
one it rests on:

| Judgement | Convention | The number it moves |
|---|---|---|
| **Cost Basis** | **Average cost**: a sale takes its proportional share of what the whole holding cost. | Realised P&L on every partial sale. |
| **Realised P&L and Commission** | **Gross of Commission**: proceeds less the sold share's cost. Commission is recognised separately, as the broker's revenue. | Realised P&L, and its relation to Gross Revenue. |
| **Reporting Currency** | **EUR, converted row by row** at the FX Rate on that row's own date. Trade Count and Position Change, a count and a quantity, state no currency. | Every monetary metric. |
| **A metric's period** | **The fact's own date**: Trade Date for a Trade metric, the Snapshot date for a Snapshot metric, the Accounting Movement date for Realised P&L. There is **no *by settlement date* axis**. | Every "in this period" figure. |
| **The Snapshot calendar** | **The intersection** of the traded Instruments' trading calendars: a date carries Snapshots for every Instrument or for none. | Which dates an "as of" question can ask about, and where a Position Change lands. |
| **Movement signs** | `fct_cash_movement.amount` is **signed from the Account's side** — positive enters it. `fct_accounting_movement.amount` is the **magnitude recognised**, always positive, with Realised P&L the one signed value. `schema.sql` states each beside its column. | Whether Net Revenue reads true against the ledger. |
| **Market Price** | **The unadjusted close**, booked on the exchange's own trading date and normalised to the major unit. | Every mark: Account Value, Unrealised P&L, Position Change. |
| **The book** | The traded universe in `veritas/ingestion/universe.py`, over `PRICE_WINDOW_YEARS` of real Market Prices, and **one seeded simulation** of client activity. | Every absolute total. |

## Alternatives considered

| Option | Why not |
|---|---|
| **First-in-first-out Cost Basis** | The other standard convention, and often the tax one. It needs a lot ledger — one Cost Basis per acquisition rather than per holding — which this schema deliberately does not carry, and the Glossary's `Cost Basis` is *"the total for the held quantity, accumulated across the Trades that built it"*, which admits one reading. |
| **Realised P&L net of Commission** | Closer to what a client feels. It counts one charge twice across two Certified Metrics: once as the broker's Gross Revenue and once inside the client's Realised P&L. |
| **Convert a period total once, at the closing rate** | Simpler, and it is what a single-currency report would show. It prices a trade from January at a December rate, so the same Trades total differently depending on when the question is asked. |
| **A *by settlement date* axis beside *by trade date*** | Both readings are correct answers to different questions, and the Glossary's Section C pair exists because the choice moves the number. Certifying both doubles the surface an Ambiguous Term has to disambiguate for a question almost nobody asks; certifying one, and saying which, keeps the answer traceable. |
| **The union of the trading calendars, filling each Instrument forward** | Every date gets a Snapshot, but a holding on a closed market is marked at a stale price, and every later metric inherits the fill. |
| **One sign convention across both movement tables** | Tidier, and wrong for one of them: cash is naturally signed by direction, while a recognised amount is naturally a magnitude with its kind in `movement_type`. |
| **Adjusted Close for Market Price** | The series most data vendors lead with. It rewrites history as later corporate actions occur, so a Position marked at it is wrong and irreproducible — the Glossary's Section C pair. |

## Consequences

**What this buys us.** Every figure is traceable to a stated convention, so two
people reading the same number agree on what it means. The Gold Question Set can
separate near-identical metrics, because each Section C pair is two different numbers
on this data — `check_warehouse.py --distinctions` fails the run if one converges.

**What this costs us.**

- **A reader expecting the other convention reads a different number.** A
  first-in-first-out Realised P&L, a settlement-date revenue or a closing-rate total
  can differ materially from what Veritas certifies. *Accepted* — the certified one
  is stated, and the other is a different question.
- **Dates on which some market traded carry no Snapshot**, so a Position Change
  across one lands on the next Snapshot date; `check_warehouse.py --sources` prints
  how many. *Debt* — [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes).
- **The book is small and synthetic on the client side**, so its totals are
  internally consistent and never realistic: each Account's opening deposit is
  computed to cover the deepest hole its own trading digs, so Accounts hold more cash
  than stock. *Accepted* — Veritas has no real client data by construction.
- **Single bonds and options are out of the book**, because no key-free source
  prices them. *Debt* — [DEBT-003](../debt-ledger.md#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope).

**What it commits us to.** That each convention is stated where its metric is
certified and where its column is declared. The signal that this has stopped holding
is a Metric Definition whose figure depends on a judgement this table does not name.

## Related

- Glossary: `Cost Basis`, `Realised P&L`, `Reporting Currency`, `Snapshot`,
  `Market Price`, `Adjusted Close`, and [Section C](../glossary.md#c-distinctions-we-must-not-blur).
- [ADR-0004](0004-snapshot-and-replay-and-where-dlt-stops.md) — where the real half
  of the book comes from.
