# ADR-0004 — Every real source is snapshot-and-replayed, and dlt stops at `raw`

- **Status:** proposed
- **Date:** 2026-08-10
- **Decided in:** Step 002, Sub-step 2.2

## Context

Two questions had to be answered before the first row of real data reached the
Warehouse, and both were deferred to this Step by name.

**The first is reproducibility.** Veritas reads four external sources it does not
control. One of them — Yahoo's chart endpoint — is the subject of
[DEBT-002](../debt-ledger.md): *"The endpoint is undocumented and unversioned. It
carries no stability guarantee and no terms permitting this use."* The mitigation
was chosen at design time and its shape was already argued in
[`data-availability.md`](../design/data-availability.md): *"snapshot the fetched
data into the repository, and have ingestion read the snapshot by default with a
refresh flag to re-fetch. That makes the build reproducible **even if Yahoo
disappears** — a stronger reproducibility story than live-fetching from any
source, official or not."*

What was left open is **scope**. The same document narrows it:

> Snapshot-and-replay applies specifically to sources that are *undocumented and
> unversioned* — Yahoo — not to every external source; Frankfurter and the SEC
> are documented and stable, and snapshotting them is a reproducibility
> convenience rather than a hedge against disappearance.

So the hedge is required for one source and merely convenient for the others.
That leaves a real choice: apply the mechanism where it is *needed*, or apply it
uniformly.

**The second is where dlt stops.** [Step 002 ruling R4](../plan/step-002-warehouse-and-ingestion.md#r4--dlt-lands-raw-the-adapter-builds-the-star-schema--approved)
settled the principle — *"dlt lands raw source data in a `raw` schema; the adapter
executes the SQL that builds the star schema from it"* — because dlt's DuckDB
destination opens its own connection, which sits awkwardly against ADR-0002's
*"reached **only** through the Warehouse Adapter; no component queries it
directly"*. R4 is a ruling in a plan; this ADR is where it becomes a decision with
its costs written down.

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
| **Snapshot nothing; fetch live every run** | Fails the rubric's key-free reproducible bring-up the moment any source moves, and DEBT-002 exists because the likeliest source to move is the one every Position mark depends on. |
| **Let dlt build the star schema too** (its own transform layer) | Puts the tables every Metric Definition quotes behind a second connection and a second SQL generator, which is precisely what ADR-0002's adapter exists to prevent. R4 rejected this. |
| **Have ingestion emit the raw-to-star SQL** rather than the adapter | Would work, and would fire [DEBT-009](../debt-ledger.md)'s trigger — *"the first component outside the adapter emits SQL"* — for no gain. Keeping the text in `veritas/warehouse/builds/` puts it under the same licence as `schema.sql` and leaves the seam scan meaningful. |
| **Commit filtered snapshots** (only the traded Instruments' rows) | Would cut roughly 1.5 MB. It also means the committed file is no longer what the source returned, so replay and `--refresh` stop exercising the same parser — the exact "same code path a reviewer would run" property this design is for. |

## Consequences

**What this buys us.** A clone with no network runs
`uv run python -m veritas.ingestion` and gets a byte-identical Warehouse. The
reproducibility claim holds even if any source dies, not just Yahoo. Exactly one
function in the package opens a socket, so the blast radius of a source change is
one file. And the star schema — the surface every later component reads — has one
author and one connection.

**What this costs us.**

- **About 2.6 MB of committed snapshots**, of which roughly 1.5 MB is NASDAQ
  Trader and SEC reference data for symbols outside the traded universe. Accepted:
  the alternative breaks the shared code path, and the figure is what
  `du -sh data/snapshots/ingestion/` reports.
- **The snapshots go stale silently.** Nothing tells us a committed snapshot no
  longer matches what the source would return today. `--refresh` is the only way
  to find out, and nothing runs it on a schedule. Accepted for the slice — the
  data is historical and a stale 2025 window is still a correct 2025 window — but
  it is why the refresh path is committed rather than improvised.
- **dlt is a large dependency for what it does here.** It landed 40-odd
  transitive packages, including `sqlglot`, to move five small tables. Accepted:
  R4 chose it and it is the tool the Zoomcamp rubric expects, and its schema
  inference is doing real work on files whose columns differ between halves.

**What it commits us to.**

- Sub-steps 2.3 and 2.4 add sources by adding a resource and a build script.
  If either needs to open its own socket, this decision has stopped holding.
- The `raw` schema is a staging area, never a query surface. No Metric Definition,
  Join Path or generated query may name a `raw.*` table; they name star tables.
- Values in `raw` are the source's, not ours. Field *names* are ours, because a
  pipe-delimited file must be given column names and NASDAQ Trader's two halves
  spell the symbol column differently (`Symbol` against `ACT Symbol`). Renaming a
  field is not transforming a value, and values are where wrong numbers come from.

## Related

- Debt Ledger: [DEBT-002](../debt-ledger.md) — the reproducibility hedge this
  implements. **Not yet paid:** its trigger is the market-price ingestion
  pipeline, which is Sub-step 2.3. The snapshot half of the mitigation lands here,
  one Sub-step early, so the pipeline never exists without it.
- Debt Ledger: [DEBT-009](../debt-ledger.md) — deliberately left unfired by
  keeping build SQL inside `veritas/warehouse/`.
- Design: [`data-availability.md`](../design/data-availability.md) §1–3, which
  proved each source obtainable and supplied the scope sentence quoted above.
- Decision: [R4](../plan/step-002-warehouse-and-ingestion.md#r4--dlt-lands-raw-the-adapter-builds-the-star-schema--approved),
  which this ADR turns from a plan ruling into a recorded decision.
- Glossary: introduces no term. `Ingestion` already registers *"snapshotted into
  the repository and replayed by default"*.
