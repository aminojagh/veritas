# ADR-0004 — Every real source is snapshot-and-replayed, and dlt stops at `raw`

- **Status:** accepted

## Context

Two questions bind before the first row of real data reaches the Warehouse.

**The first is reproducibility.** Veritas reads four external sources it does not
control, all key-free: Frankfurter's European Central Bank (ECB) reference rates, the
Securities and Exchange Commission (SEC)'s ticker file, NASDAQ Trader's symbol
directories, and Yahoo's chart endpoint for daily Market Prices. Yahoo's is the only
key-free source of daily closes across the traded universe, and it is undocumented and
unversioned: it carries no stability guarantee and no terms permitting this use. The
other three are documented and stable. So a hedge against a source disappearing is
required for one source and merely convenient for the others, and there is a real
choice: apply the mechanism where it is *needed*, or apply it uniformly.

**The second is where dlt stops.** dlt's DuckDB destination opens its own connection,
which sits awkwardly against ADR-0002's *"reached **only** through the Warehouse
Adapter"*.

## Decision

**Every real source is read through one snapshot-and-replay mechanism, replay by
default.** `veritas/ingestion/snapshots.py` is the only module in the package that
opens a socket. A source module asks for bytes by name and cannot tell whether
they came from disk or the network. `--refresh` is the sole mode that needs a
network, and it rewrites the snapshot with the same bytes the run used.

**dlt extracts and loads; it never builds the star schema.** dlt lands records in
the `raw` schema with values exactly as the source gave them. Every star-schema
table is built by hand-authored SQL living in `veritas/warehouse/builds/`,
executed through the adapter's `run_build`.

## Alternatives considered

| Option | Why not |
|---|---|
| **Snapshot only Yahoo**, fetch Frankfurter, NASDAQ Trader and the SEC live | The correct scope on paper, and wrong in practice. It makes offline replay impossible: a reviewer with no network gets three of four sources and a Warehouse that is silently short. It also puts two mechanisms in one package, so "did this run touch the internet?" stops having one answer. The stability argument is about *which source is likely to break*, not about which should be reproducible. |
| **Snapshot nothing; fetch live every run** | Fails the rubric's key-free reproducible bring-up the moment any source moves, and the likeliest source to move is the one every Position mark depends on. |
| **Let dlt build the star schema too** (its own transform layer) | Puts the tables every Metric Definition quotes behind a second connection and a second SQL generator, which is precisely what ADR-0002's adapter exists to prevent. |
| **Have ingestion emit the raw-to-star SQL** rather than the adapter | Would work, and would put SQL emitted outside the adapter into the seam scan for no gain. Keeping the text in `veritas/warehouse/builds/` puts it under the same licence as `schema.sql` and leaves the seam scan meaningful. |
| **Commit filtered snapshots** (only the traded Instruments' rows) | Would cut most of the reference data's size. It also means the committed file is no longer what the source returned, so replay and `--refresh` stop exercising the same parser — the exact "same code path a reviewer would run" property this design is for. |

## Consequences

**What this buys us.** A clone with no network runs
`uv run python -m veritas.ingestion` and gets a byte-identical Warehouse. The
reproducibility claim holds even if any source dies, not just Yahoo. Exactly one
function in the package opens a socket, so the blast radius of a source change is
one file. And the star schema — the surface every later component reads — has one
author and one connection.

**What this costs us.**

- **Megabytes of committed snapshots**, much of it NASDAQ Trader and SEC reference
  data for symbols outside the traded universe — `du -sh data/snapshots/ingestion/`
  prints the size. Accepted: the alternative breaks the shared code path.
- **The snapshots go stale silently.** Nothing tells us a committed snapshot no
  longer matches what the source would return today. `--refresh` is the only way
  to find out, and nothing runs it on a schedule. Accepted for the slice — the
  data is historical and a stale 2025 window is still a correct 2025 window — but
  it is why the refresh path is committed rather than improvised.
- **dlt is a large dependency for what it does here.** It brings dozens of
  transitive packages to move five small tables. Accepted: it is the tool the
  Zoomcamp rubric expects, and its schema inference is doing real work on files
  whose columns differ between halves.

**What it commits us to.**

- A source is added by adding a resource and a build script. If one needs to
  open its own socket, this decision has stopped holding.
- The `raw` schema is a staging area, never a query surface. No Metric Definition,
  Join Path or generated query may name a `raw.*` table; they name star tables.
- Values in `raw` are the source's, not ours. Field *names* are ours, because a
  pipe-delimited file must be given column names and NASDAQ Trader's two halves
  spell the symbol column differently (`Symbol` against `ACT Symbol`). Renaming a
  field is not transforming a value, and values are where wrong numbers come from.

## Related

- [ADR-0002](0002-duckdb-as-the-warehouse-behind-an-adapter.md) — the adapter the
  build SQL runs through, and the licence `schema.sql` holds.
- Debt Ledger: [DEBT-003](../debt-ledger.md#debt-003--no-market-price-vendor-so-single-bonds-and-options-are-out-of-scope)
  — single bonds and options, which no key-free source prices.
- Glossary: introduces no term. `Ingestion` already registers *"snapshotted into
  the repository and replayed by default"*.
