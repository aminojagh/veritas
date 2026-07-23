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
| _(none yet)_ | | |

Statuses: `proposed` · `accepted` · `superseded by ADR-NNNN` · `rejected`
(rejected ADRs are kept — they record an option we considered and declined).
