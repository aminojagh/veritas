# Architecture Decision Records

One file per decision that is **expensive to reverse**. Numbered sequentially,
never renumbered, never deleted — a superseded ADR stays in place with a pointer
to the one that replaced it, because the reasoning that was wrong is as useful
as the reasoning that was right.

**Write an ADR when** a choice constrains later Steps, closes off alternatives,
or would prompt "why on earth is it done this way?" from someone reading the
repo cold. See the `writing-an-adr` skill.

**Do not write an ADR** for reversible choices, library-version bumps, or
anything whose alternative could be swapped in an afternoon. Those are either
Debt Ledger entries or just code.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-semantic-layer-as-the-retrieval-corpus.md) | The Semantic Layer is the retrieval corpus | accepted |
| [0002](0002-duckdb-as-the-warehouse-behind-an-adapter.md) | DuckDB is the Warehouse, reached only through an adapter | accepted |
| [0003](0003-validation-gate-is-deterministic-code.md) | The Validation Gate is deterministic code, not an Large Language Model (LLM) self-check | accepted |
| [0004](0004-snapshot-and-replay-and-where-dlt-stops.md) | Every real source is snapshot-and-replayed, and dlt stops at `raw` | accepted |
| [0005](0005-one-openai-compatible-endpoint-for-every-provider.md) | Every model call goes through one OpenAI-compatible endpoint | proposed |

ADR-0004 was written in Sub-step 2.2 and **accepted by Amino on 2026-08-11**, with
Sub-step 2.3's review — the Sub-step that first built on both of its decisions.
It was deferred to this Step by name in Sub-step 1.3: *"this was considered as a
fourth founding ADR and deferred to the ingestion Step, where the decision
actually binds."*

The first three were accepted by Amino on 2026-08-03, conditional on the corrections applied
the same day (see the Step 001 review, Sub-step 1.3). ADR-0002 carries one dated
**clarification** added 2026-08-05 — what its sqlglot commitment forbids, with
worked examples. A clarification makes an accepted decision precise; it is not a
supersede, and the status stays `accepted`. Each ADR's **Consequences**
classify every cost as *accepted*, *debt*, or *extension* — the ones that became
debt are [DEBT-005](../debt-ledger.md) through [DEBT-008](../debt-ledger.md).

Statuses: `proposed` · `accepted` · `superseded by ADR-NNNN` · `rejected`
(rejected ADRs are kept — they record an option we considered and declined).
