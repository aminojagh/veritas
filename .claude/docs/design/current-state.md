# Current State

**What actually exists in this repository right now.** Reality only — never
intent, never plans. If this file and the repository disagree, this file is
wrong and gets fixed immediately.

**Last updated:** 2026-08-25 — **the Semantic Layer is complete and approved.** Sub-step 4.5 of Step 004 is written and verified: `semantic/dimensions/` publishes the five certified axes a metric can be sliced along — `by trade date`, `by snapshot date`, `by accounting movement date`, `by region`, `by instrument type` — and with them the corpus holds **all four entry types [Glossary Section A](../glossary.md#a-the-system) registers**: nine Metric Definitions, eight Join Paths, five Ambiguous Terms and five Dimension Definitions, **twenty-seven entries**. `check_semantic_layer.py` went from fourteen checks to **eighteen**, and the four new ones read the **Warehouse** rather than the rest of the corpus, because a Dimension Definition is the only entry type that is a **leaf** — nothing names an axis, so nothing above one would notice if it were wrong. **The single date axis became three**: an axis at `fct_trade.trade_date` cannot be applied to the five Snapshot-and-movement metrics whose routes never reach that column, so the corpus publishes the three date senses the Warehouse actually keys on, each named for its registered term. That is one **Glossary amendment**, ruled and **agreed on 2026-08-25** ([R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)): the `Dimension Definition` row listed three axes as *examples* and now names all five with their columns, grain and buckets, in a form check 18 reads back — and the check caught a quotation of the old wording inside the row's own amendment note on its first run. **One new shortcut**: [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) — that registry is one table cell read by a prose parse, where the other two are tables — so the open-debt count is **10**. **[DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes) carries the dated deferral note [R7](../plan/step-004-semantic-layer.md#r7--the-date-axis-defers-debt-012s-trigger-rather-than-avoiding-it--approved-by-amino-2026-08-21) asked for** and stays open on all three arms. **Step 004 is `in review`** — all five Sub-steps written, the first four committed, and **4.5 reviewed and approved by Amino on 2026-08-25**: *"all approved"*, recorded in full as [R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25). [R5](../plan/step-004-semantic-layer.md#r5--45-is-a-pre-agreed-split-point--approved-by-amino-2026-08-21)'s pre-agreed split point was never needed. **Three questions travel on to [Grounding](../glossary.md#a-the-system)**, ruled there in the same words four times — *"the Step that grounds a query"* — and none of them a defect in what was built: `by region` sits inside no metric route because no Join Path reaches `dim_client`; there is no `by settlement date` axis; and check 17 forecloses an axis whose values are data but not dates.
**Eleven rulings now carry this Step**, and one question outlives it. Amino approved the plan and all seven of its rulings on 2026-08-21, and amended it four times since: [R8](../plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22) on 2026-08-22, [R9](../plan/step-004-semantic-layer.md#r9--aminos-four-rulings-on-the-42-review--decided-2026-08-23) on 2026-08-23, [R10](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24) on 2026-08-24 — the five things the [4.4 review](../reviews/step-004-semantic-layer.md#sub-step-44--write-the-ambiguous-terms) put up sceptically plus the prefix question R9 had left open — and [R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25) on 2026-08-25. **The question neither R10 nor R11 reached is whether the `resolution` field name wants a Glossary row**; it blocks nothing, and no file changes either way. 4.4 took no shortcut, and its review says why its two candidates are neither debt nor extension. **Sub-step 4.5 — the Dimension Definitions — is this commit, the last of this Step.** **The Warehouse is full: all ten tables of Glossary Section B hold rows, every Certified Metric can return a number, and the adapter seam is checked in all three of the readings ADR-0002's two signals now come to.**

**Steps completed:** Step 000 (framework), Step 001 and **Step 002, all six Sub-steps, fully committed**. Step 000 and Sub-step 1.1 in `6281e6b`, Sub-step 1.2 in `4b48a46`, Sub-step 1.3 in `9c5b060`, Step 002 planning in `57e8aee`, Sub-step 2.1 in `5a061a7`, the R16 plan amendment in `cd5e7dd`, Sub-step 2.2 in `0fc5a34`, Sub-step 2.3 in `a58ef91`, Sub-step 2.4 in `13b99bb`, Sub-step 2.5 in `ce2961a`, Sub-step 2.6 in `6a16d3d`, Step 003 planning in `40d72d8`, **Sub-step 3.1 in `d840fa8`, Sub-step 3.2 in `89fee55`, Sub-step 3.3 in `23020e9`, Sub-step 3.4 in `c20d601`, Sub-step 3.5 in `fcf4b7d`**. **Step 004 planning is committed in `5d95393`** and **Sub-step 4.1 in `6c15736`**, which is what wrote 3.5's hash above and turned the [Step 003 plan](../plan/step-003-validation-feasibility.md) from `in review` to `done` — how every hash above arrived, and how `40d72d8` closed Step 002. **Sub-step 4.2 is committed in `333d6fc`, Sub-step 4.3 in `ae75f0e` and Sub-step 4.4 in `71ce677`. This commit is Sub-step 4.5, the last of Step 004**; its own hash is not here for the reason every Sub-step's is not, which is that this file is part of it, and the first commit of Step 005 fills it in — as `40d72d8` closed Step 002 and `6c15736` closed Step 003.

---

## Resume here

- **Next: plan Step 005.** Step 004 has no Sub-step left — 4.5 is the last, it is
  written, verified and **approved on 2026-08-25** ([R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)), and
  [the plan](../plan/step-004-semantic-layer.md) stays `in review` until Step 005's
  first commit can carry 4.5's hash, which is how every Step's plan reaches `done`.
  The next move is `planning-a-step`
  against a Semantic Layer that exists, with the
  [six constraints](validation-feasibility.md#consequences-for-step-004) already spent
  and [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)'s go recorded.
  The plan's own scope boundary calls the Validation Gate *"the **expected** Step 005,
  which is an expectation and not a plan"* — so it is expected and not decided, and
  **nothing here plans it**.
  **Three things the next Step should read first.** The three questions
  [R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25) handed to Grounding, below — the first of them, `by region`, is the
  corpus's one certified-and-inapplicable axis. The two questions
  [R10](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24)
  handed to Retrieval, also below. And
  [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject),
  whose trigger is *"the Sub-step that builds the Validation Gate"* and which the Step
  004 plan says this Step wrote the fields for.
- **Sub-step 4.5 was approved on 2026-08-25, and one question stays open.** The seven
  things the [4.5 review](../reviews/step-004-semantic-layer.md#sub-step-45--write-the-dimension-definitions) put up sceptically and the five it deliberately
  left undone were ruled on together — *"all approved"* — and argued in full as
  [R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25), in the plan rather than only in the review, because a review is read
  once. Nothing was reverted and nothing was renamed. **Four of the items carry a stated
  reason and it is the same one four times**: they belong to the Step that grounds a
  query, which is [Grounding](../glossary.md#a-the-system) — the three questions below.
  The **Glossary amendment stands**, so the `Dimension Definition` row is agreed rather
  than provisional and check 18 keeps both halves; the four remaining sceptical points —
  `grain` compared as text, the plural `columns`, the `dimension_definition` kind, and
  4.4's two renames — are approved **as written, with no separate reason given**, which
  is how R11 records them.
  **Still open — whether `resolution` needs a Glossary row.** Flagged in the 4.4 review,
  left open by [R10](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24),
  and untouched here: 4.5 adds no field by that name, so *"all approved"* approves
  nothing about it. It blocks nothing — no file changes either way — and it is the one
  question Step 004 closes without answering.
- **What Sub-step 4.5 built**, and the one thing it deliberately left standing.
  `semantic/dimensions/` publishes five Dimension Definitions, each naming its
  `columns`, its `grain` and its `allowed_values` — the
  [Glossary row](../glossary.md#a-the-system)'s own three words for what an axis names.
  `veritas/semantic/loader.py` gained `DimensionDefinition` and the `dimensions` row in
  `ENTRY_KINDS`, which had to come first for the reason 4.4's row did, and no row in
  `SQL_FIELDS` — an axis names identifiers, and what checks them is the live schema.
  `check_semantic_layer.py` gained checks 15 to 18: every named column exists in the
  live schema; every column of one axis holds the **same** values and an enumerated
  axis's buckets are exactly that set, in both directions; an axis enumerates **exactly
  when** its buckets are a registered vocabulary rather than dates, since a date's
  values are minted by the data; and the Glossary's `Dimension Definition` row and the
  corpus register the same five axes with the same columns, grain and buckets. Five
  probes give the first three teeth on every run.
  **`by region` sits inside no metric route, and that is the first of the three
  questions Grounding inherits.** Nothing under `semantic/joins/` reaches `dim_client`, so the axis the
  Glossary's own worked example uses — *"Net Revenue by region last quarter"* — is
  certified, true and not yet applicable. It is not a defect in anything written here:
  4.2 wrote the routes the **expressions** need, and no expression needs `dim_client`;
  what a grouping needs is a Join Path added for a *slice* plus the rule that lets a
  query add one, and both belong to the Step that grounds a query. The Sub-step 3.2
  spike's `net revenue by region` probe writes `fct_trade → dim_account → dim_client`
  **by hand** and calls it *"two more joins … and the shape nearly every real question
  produces"*. The check prints the count on every run so it cannot go quiet, and the
  [4.5 review](../reviews/step-004-semantic-layer.md#sub-step-45--write-the-dimension-definitions) put the case for calling it debt instead — **ruled against on
  2026-08-25**: *"correctly belongs to the Step that grounds a query."*
  **Both things that went up for Amino are settled.** The Glossary amendment — three
  examples became five certified axes — **stands**, so the row is agreed rather than
  provisional and check 18 keeps both halves; and
  [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell),
  the price of registering them inside one table cell, **stays open on its own trigger**,
  because approving what the cell says is not approving that it is a cell.
  **Nothing from a later Step was built**: no `veritas/validation/`, no Retrieval, no
  Access Profile, no `README.md`. `semantic/metrics/`, `semantic/joins/` and
  `semantic/ambiguous/` were not touched — `git status` on all three is empty.
- **Three questions the Grounding Step inherits**, all ruled on 2026-08-25 and none of
  them a defect in anything built here. They are [R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)'s first three rulings, and
  they take the shape R10 gave the two questions above: a named place to look first, not
  an open defect.
  1. **`by region` is certified and unreachable.** Nothing under `semantic/joins/`
     reaches `dim_client`, so the axis the Glossary's own worked example uses cannot yet
     be applied. What closes it is two Join Path files — `trade_to_account` and
     `account_to_client` — **plus the rule that lets a query add a Join Path for a
     *slice* rather than for an expression**, and it is that second half that makes it
     Grounding's work rather than authoring work. It is **not** debt: *"correctly belongs
     to the Step that grounds a query."*
  2. **There is no `by settlement date` axis, and it is deferred rather than rejected.**
     The column exists and holds real dates, but every Metric Definition keys its period
     filter on `trade_date`, so certifying it would let one question be *sliced* on one
     date while being *filtered* on another — a
     [Section C](../glossary.md#c-distinctions-we-must-not-blur) pair blurred by an axis.
     The Step that decides which date a query filters on is the one that decides whether
     it can also be sliced on.
  3. **Check 17 forecloses an axis whose values are data but not dates.** A
     `by denomination currency` axis would have to enumerate codes ingestion minted, and
     an enumeration of minted values is a measurement living in the corpus. The rule is
     not loosened; what the ruling settles is **where** such an axis gets decided, which
     is where a query needs to slice by one.
- **Six rulings arrived on 2026-08-24, and one question is left open.** The five things
  the [4.4 review](../reviews/step-004-semantic-layer.md#sub-step-44--write-the-ambiguous-terms)
  put up sceptically, and the prefix question
  [R9](../plan/step-004-semantic-layer.md#r9--aminos-four-rulings-on-the-42-review--decided-2026-08-23)'s
  third ruling left open, are all decided and argued in full as
  [R10](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24) — in the plan
  rather than only in the review, because a review is read once. In one line each: the
  Glossary amendment **stands**, so check 13 keeps its Glossary half; the alias
  partial-match risk and the unchecked `description` fields become **the two questions
  the Retrieval Step inherits**, below; check 13's unresolvable half **stays a printed
  comment**, cost accepted; `certified_metric_terms()` **stays read once** and passed to
  two checks; and the Join Path prefix question is **closed** —
  `instrument_to_fx_rate_on_quotation_currency` is the decided name, nothing is renamed,
  and no `from_table` field changes.
  **Still open — whether `resolution` needs a Glossary row.** It is a new field name on
  the Ambiguous Term entry, taken from Section D's own third column header, flagged
  rather than assumed settled in the 4.4 review's Language section. **It does not block
  4.5**: no file changes either way, and 4.5 adds no field by this name.
- **What Sub-step 4.4 built**, and what it deliberately did not.
  `semantic/ambiguous/` holds the five rows of
  [Glossary Section D](../glossary.md#d-ambiguous-terms) as entries, each naming the
  Certified Metrics it disambiguates between through `disambiguates`, the field
  [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) chose.
  `veritas/semantic/loader.py` gained `AmbiguousTerm` and the `ambiguous` row in
  `ENTRY_KINDS` — which had to come first, because that mapping is not a scan of the
  tree and five files in an unregistered directory would have failed to load rather
  than being skipped. `check_semantic_layer.py` gained checks 12, 13 and 14, which
  execute nothing: **every metric an Ambiguous Term names must exist** and there must
  be at least two distinct ones (EXT-005's fourth rule, with three probes on every
  run); **Section D and the corpus must register the same five words**, each row's
  *Could mean* cell naming the same Certified Metrics its entry does; and **no
  metric's alias may be a registered Ambiguous Term or be claimed by two metrics**,
  which is the decision 4.2 took and the 4.2 review recorded as *"invisible in the
  files, and nothing checks it"*.
  **The Glossary was wrong and the check said so on its first run** — Section D's
  "P&L" row, above. **Two Summary claims in this file had also stopped being true
  before 4.4 and were fixed with it**: *"all eight of them"* where nine Certified
  Metrics now return a number, and a paragraph still describing the Semantic Layer as
  *"one entry type of four and one Metric Definition of nine"*, which 4.2 had left
  behind.
  **Nothing from a later Sub-step was built**: no Dimension Definition, no
  `veritas/validation/`, no Retrieval, no Access Profile. `semantic/metrics/` and
  `semantic/joins/` were not touched — `git status` on both is empty — and the other
  four committed checks pass unchanged, because an Ambiguous Term publishes no SQL and
  the two scripts that read the corpus for SQL got an empty list from it.
- **Two questions the Retrieval Step inherits**, both ruled on 2026-08-24 and neither a
  defect in anything built here. They are
  [R10](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24)'s
  second and fifth rulings, and they take the shape R9.2 gave the `Position Change`
  expression: a named place to look first, not an open defect.
  1. **A partial alias match can resolve an Ambiguous Term silently.** `Unrealised P&L`
     claims the alias *"paper profit and loss"* and `Realised P&L` claims *"booked profit
     and loss"*, so a user who types **"profit and loss"** is a short hop from either
     metric while matching the `P&L` Ambiguous Term by no name at all — Section D's own
     failure, arriving through the door check 14 does not cover, because check 14
     compares whole strings. The two candidate fixes are an `aliases` field on the
     Ambiguous Term entry or a Retrieval rule that an Ambiguous Term outranks a metric it
     disambiguates to; choosing between them without Retrieval to measure is speculation.
  2. **The five Ambiguous Term `description` fields are unchecked prose, and they are
     what Retrieval will embed.** Improving them belongs where retrieval performance can
     be measured — text written to be embedded is tuned against a measurement or not at
     all — so until then they stay as authored.
- **What Sub-step 4.3 built**, and what it deliberately did not.
  [DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)
  is **paid**. `check_seam` reads every SQL field of every Semantic Layer entry — a
  Metric Definition's `expression` and its certified `filters`, a Join Path's `on` —
  as well as the SQL a module emits, and reads all of it twice: the name list
  unchanged, plus `unportable_types`, which retargets each statement to BigQuery and
  compares every type construct against the **same type retargeted on its own**.
  `DECIMAL(38, 6)` arrives inside a statement as `NUMERIC` and on its own as
  `NUMERIC(38, 6)`, so the statement's trip lost what the type's did not; `VARCHAR`
  arriving as `STRING` is the same type in the other engine's words and is not a
  finding. `retarget` and `round_trip_rewrites` **moved** out of
  `check_validation_feasibility.py` into `check_warehouse.py`, and the spike imports
  them back, so the dated measurement and the check that runs on every commit are one
  trip. `DIALECT_PROBES` went from three probes to five and gained a second column, so
  both readings are asserted on every run.
  **The two readings end differently on purpose.** A DuckDB-only function name
  outside the adapter fails the run; a lossy type prints as a **review comment**,
  which is the word ADR-0002's mitigation has always used, because this corpus
  carries a lossy type the engine will not compute without. A statement sqlglot
  cannot write in BigQuery at all does fail — that is the ending with no legitimate
  case. The argument, the four mutations and what the run names are in the
  [4.3 review](../reviews/step-004-semantic-layer.md#sub-step-43--pay-debt-015-the-dialect-scan-reads-type-constructs);
  **its third sceptical point is the one to read first**, because it is where Amino
  would overrule this.
  **Three things changed outside the Sub-step's own file.** `veritas/semantic/`
  gained `SQL_FIELDS` and `sql_fields()`, which say which fields of an entry hold
  SQL, so the scan does not decide that for itself. `check_language.py` derives the
  shouted keywords of the SQL the corpus publishes instead of remembering them —
  writing this Sub-step's own review is what made it fail on `CAST` — and reading
  the corpus costs it the stdlib-only property, which the dependency row records.
  And `check_semantic_layer.py` said in two places that *four* published
  expressions carry the widening cast where the run refuses **five**; the 4.2
  review had already recorded five, so the docstring had been false since the
  corpus was written and nothing failed. **Nothing from a later Sub-step was
  built**: no Ambiguous Term, no Dimension Definition, no `veritas/validation/`, no
  Access Profile.

- **What Sub-step 4.2 built**, and what it deliberately did not. `semantic/metrics/`
  publishes all nine Certified Metrics of
  [Glossary Section B](../glossary.md#b-the-warehouse) and `semantic/joins/` the eight
  Join Paths they are computed across. `check_semantic_layer.py` grew from six checks
  to eleven, `check_warehouse.py` gained the eight remaining independent figures — so
  **every** metric now has a second opinion and R2's weaker branch is unreachable —
  the `Cash Balance` Glossary row was amended per R1, and
  [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) records
  that its rule-2 edge now needs a name of its own. **Then Amino reviewed it**, and the
  same commit carries what his rulings changed: two Join Paths renamed onto the currency
  axis, and
  [EXT-009](../extension-register.md#ext-009--the-join-path-entry-type-at-warehouse-scale)
  filed for the Join-Path-reuse question — both recorded as [R9](../plan/step-004-semantic-layer.md#r9--aminos-four-rulings-on-the-42-review--decided-2026-08-23). **Nothing from a later Sub-step
  was built**: no Ambiguous Term, no Dimension Definition, no `veritas/validation/`,
  no Access Profile, and `check_warehouse.py`'s dialect scan did not yet read
  `semantic/` — **4.3 is what changed that**, one bullet up.
- **[R8](../plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)
  amended the approved format, and is the first thing to read after this block — with
  [R9](../plan/step-004-semantic-layer.md#r9--aminos-four-rulings-on-the-42-review--decided-2026-08-23) straight after it, which is Amino's four rulings on the 4.2 review.**
  The open question was `join_path` being a single name; reading all nine metrics
  against the approved shape before writing any of them turned it into four separate
  holes, and the three ways out the 4.1 review named turned out not to be
  alternatives. Five changes to the Metric Definition, **none to the Join Path**:
  `join_path` became `join_paths`, a list; `from_table` and `filters` were added;
  `reporting_currency` became optional and is present exactly when `unit` is `money`;
  and `derives_from` became load-bearing, naming the Certified Metrics whose value is
  **added** to this metric's own expression. No new domain noun was coined. The
  re-edit cost the one file the ruling was protecting.
- **Three findings from 4.2 that the next Sub-steps inherit.**
  1. **`Position Change` carries the one expression shape the spike never measured** —
     a correlated scalar subquery with an `ORDER BY` and a `LIMIT` inside an
     aggregate, where every expression the spike traced is flat arithmetic over joined
     columns. Whether
     [C5](validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)'s
     two rewrite rules can trace a generated query back to it is **not known**, and
     the Gate Step is where that lands.
  2. **No metric's `aliases` contain an Ambiguous Term.** "revenue", "volume",
     "balance" and "P&L" resolve to two metrics each, and a metric claiming one as an
     alias would let Retrieval resolve silently what
     [Section D](../glossary.md#d-ambiguous-terms) says must be asked about. It is a
     decision, it is invisible in the files, and nothing checks it — the check that
     would belongs with **4.4**, which is where Ambiguous Terms are written.
  3. **PyYAML reads `on:` as the boolean `True`**, from 4.1 and still live. The loader
     reads booleans the YAML 1.2 way instead. This matters again in **4.5**: a
     Dimension Definition's allowed values are domain text, and YAML 1.1 reads `no`,
     `on`, `y` and `n` as booleans in any casing — Norway's country code, Ontario's
     province code, and both halves of every yes/no flag.
- **All seven questions put with the plan were approved on 2026-08-21**, in
  [Questions for Amino](../plan/step-004-semantic-layer.md#questions-for-amino). Four
  as written; **R2, R4 and R7 were sent back once and approved on the second pass**,
  which is why each of those three now argues from a worked example rather than in the
  abstract.
  - **[R1](../plan/step-004-semantic-layer.md#r1--cash-balance-becomes-a-certified-metric--approved-by-amino-2026-08-21)
    — `Cash Balance` becomes a Certified Metric**, so **the Step authors nine Metric
    Definitions rather than eight** and 4.2 carries the Glossary amendment with it. It
    was found while planning: two of the five
    [Ambiguous Terms](../glossary.md#d-ambiguous-terms) resolve to `Cash Balance`,
    whose registered home was `fct_balance_snapshot` rather than `semantic/metrics/`,
    so an Ambiguous Term would have disambiguated to something with no Metric
    Definition to retrieve.
  - **[R2](../plan/step-004-semantic-layer.md#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21)
    — the Semantic Layer and `check_warehouse.py` stay independent**, and their
    agreement is the check. The example that settles it: a `Gross Revenue` expression
    written without its FX conversion. Independent, the two figures disagree and the
    run fails; coupled, both sides compute the same wrong sum and the run passes,
    having confirmed only that the expression agrees with itself.
  - **[R3](../plan/step-004-semantic-layer.md#r3--restricted-columns-are-declared-in-the-access-profile-not-in-a-metric-definition--approved-by-amino-2026-08-21)
    — Restricted Columns are declared in the Access Profile**, so Step 004 adds
    nothing for them and the Gate Step inherits a decision rather than an omission.
  - **[R4](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)
    — the spike is pinned to the corpus, not re-pointed at it.** Its three
    expressions stay Python literals so the dated measurement stays the measurement
    that was taken, and 4.2 adds the assertion that they still match what
    `semantic/metrics/` publishes. A re-pointed spike would silently re-bless an
    expression that grew a filter after the go/no-go was decided.
  - **[R5](../plan/step-004-semantic-layer.md#r5--45-is-a-pre-agreed-split-point--approved-by-amino-2026-08-21)
    — 4.5 is the pre-agreed split point.** If the Step grows, Dimension Definitions
    become Step 005's first Sub-step and this Step ships three of the four entry types,
    with the Current State row naming the missing one.
  - **[R6](../plan/step-004-semantic-layer.md#r6--no-new-adr-for-the-file-format--approved-by-amino-2026-08-21)
    — no fifth ADR for the file format.** Every expensive part is already decided in
    ADR-0001, C1, C2 and EXT-005; the plan's format section and the Step Review are
    the record.
  - **[R7](../plan/step-004-semantic-layer.md#r7--the-date-axis-defers-debt-012s-trigger-rather-than-avoiding-it--approved-by-amino-2026-08-21)
    — the narrow date axis *defers* DEBT-012's trigger rather than avoiding it.** It
    keeps unfired the one arm Step 004 could fire and leaves the other two live — a
    gold question naming a date, and the App accepting one. Deferring is right because
    [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)'s
    repayment is a **Warehouse** change of size M touching the schema, the build, the
    Snapshot calendar and all seven simulated tables; the cost is that the Semantic
    Layer cannot express *"Account Value at the end of Q2"*, and **4.5 writes the
    deferral onto the entry** so the Step that pays it does not rediscover the
    reasoning.
- **One Ledger trigger fired inside Step 004 and was paid inside it.**
  [DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)
  fired the moment `Traded Notional`'s Metric Definition was written in 4.2, because it
  cannot be written without the widening cast, and **4.3 paid it on 2026-08-23** —
  wider than the entry predicted, because the corpus turned out to carry the same cast
  on every expression whose product overflows `DECIMAL(18)` rather than on that one.
- **The open-debt count is 9**, having been 10 between 4.1 and 4.3. 4.1 opened
  [DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)
  — `check_semantic_layer.py` catches `Exception` around the two lines that execute a
  published expression, because ADR-0002 puts the engine's error classes inside the
  adapter and the adapter has none of its own. It also **paid
  [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s
  second coverage gap**: `verify_framework.py` now resolves markdown links and their
  anchors inside `.py` files as well as documents. DEBT-001 itself stays open — its
  subject is the hook layer — and the count returned to 9 when 4.3 paid DEBT-015.
- **Any session resuming here runs `uv run python -m veritas.ingestion` first**,
  because the Warehouse is gitignored and every check in the Step 004 plan executes
  against real data.
- **Sub-step 3.5 was committed unchanged in `fcf4b7d`**, the last Sub-step of Step
  003, having been written, verified and approved by Amino on 2026-08-20 with no
  change asked for. Eight files: the new
  [`validation-feasibility.md`](validation-feasibility.md), a dated status note on
  each of [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md) and
  [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md), one new Ledger
  entry plus a status note on an existing one, the
  [Step Review](../reviews/step-003-validation-feasibility.md), and this file — plus
  the two the approval itself moved, the [plan](../plan/step-003-validation-feasibility.md)
  to `in review` with the four committed hashes and [its README](../plan/README.md)
  to match. **No code changed** —
  no script, no schema, no pipeline behaviour, still no `veritas/validation/`
  directory, and no Glossary term added. The verification commands were run on
  2026-08-20 against a Warehouse rebuilt the same day, and their output is in the
  [review](../reviews/step-003-validation-feasibility.md#sub-step-35--record-the-gono-go-on-adr-0003s-parse-tree-claim).
- **The verdict is GO on ADR-0003**, and the document says what the go costs.
  1. **Claims 1, 2 and 3 hold.** A certified expression survives every rewrite a
     generator performs for its own reasons; a Shadow Metric is rejected and returns
     a number far from the right one; a Restricted Column is found in all five shapes
     that put it in the answer and reported in none of the four that do not.
  2. **Claim 4 is qualified, and it is ADR-0002's claim rather than ADR-0003's.**
     Every verdict survives retargeting; one type does not.
  3. **Six constraints are the price of the go**, written up as C1–C6 for the Step
     that builds the Semantic Layer: publish a pasteable form, carry the Join Path
     and the date predicate, ship both parse-tree rules together, read the schema at
     run time, name the two rewrites the Gate trusts, and fail closed by a rule
     rather than by accident.
  4. **What would have made it a no-go is on the record**, so the bar is not written
     after the result.
- **One new Ledger entry and one amendment**, both put up for ruling rather than
  applied silently, and **both ruled on 2026-08-20**. **The open-debt count is now 9.**
  - **[DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)** —
    the dialect scan names functions and the loss 3.4 measured was in a cast, so a
    check claims coverage it does not have. Trigger: the first Metric Definition
    carrying a cast, which is `Traded Notional`'s and cannot be avoided. **Ruled
    debt rather than an extension**, both arguments written out, in
    [R2](validation-feasibility.md#r2--debt-015-is-debt-rather-than-an-extension--approved-by-amino-2026-08-20).
  - **[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)
    gains a dated status note** reading the Trade Date / Settlement Date gap as the
    same question as the join blind spot, per 3.2's request. **Approved** as
    [R4](validation-feasibility.md#r4--debt-014-is-amended-to-name-the-date-predicate--approved-by-amino-2026-08-20):
    one entry covers both halves, and the Sub-step that pays it owes a probe that
    converts on Settlement Date, because that half is argued rather than measured.
- **All four rulings were approved on 2026-08-20**, in
  [Rulings](validation-feasibility.md#rulings): the go itself and its six
  constraints (R1), DEBT-015's classification (R2), that the constraints bind
  Step 004's plan and that C1's fork is settled as written (R3), and
  DEBT-014's amendment (R4). **Their heading anchors carried `awaiting-amino`, so
  approving them rewrote four headings and every link into them** — in this file,
  the Ledger, the Step Review and the document itself. `verify_framework.py` is what
  proves none was missed, and it is the same edit the plan's R1–R6 took.
- **One standing figure in this file was wrong and is fixed.** The Glossary row read
  **88 registered terms** and said the most recent change was an amendment; both
  stopped being true at Sub-step 3.3, which registered `Restricted Column`. No check
  reads a number written in prose, which is why nothing caught it for two Sub-steps.
  The row now reads 89, names the registration and says when it was wrong — and the
  figure that settles it is whatever `check_language.py` prints.
- **Two things in the document were judgement rather than measurement, and both
  stand.** The review says so at length: ADR-0002 was given a status note although
  the plan named only ADR-0003, and C1's fork — publish a pasteable form versus let
  the Gate normalise commuted operands — was decided in the document rather than put
  to Amino as an open question. Approving the document approved both: the note stays,
  and the fork is now settled by R3 rather than by the document alone.
- **Sub-step 3.4 was committed unchanged in `c20d601`**, so its seven points under
  *Look at this sceptically* stand as built with no ruling recorded against them —
  including the reading that the Step's split point had not fired, which the commit
  settles: 3.4 is the fourth Sub-step of Step 003 and not Step 004.
- **Sub-step 3.3 was committed in `23020e9` after Amino's 2026-08-19 review**, which
  changed three things and approved the rest.
  1. **A union probe was added to claim 2** — Net Revenue by region in one branch
     and by Client name in the other. It is the claim 2 counterpart of
     `half-certified union`, and it fails Sub-step 3.2's traversal mutation
     alongside it.
  2. **A probe that completes the set is kept, wherever it is found** — ruled and
     recorded as [R6](../plan/step-003-validation-feasibility.md#r6--a-probe-that-completes-the-set-is-kept-wherever-it-is-found--ruled-by-amino-2026-08-19)
     in the plan rather than in a Step Review, because it governs every Sub-step
     that measures a boundary. Enumerate at planning time; keep what implementation
     turns up; account for why the enumeration missed it. **3.4 owes that account
     and gives it** — its retargeting probes were enumerated by the plan exactly,
     its five detector probes were not.
  3. **The fail-closed over-strictness was fixed rather than recorded as debt.**
     Claim 2 no longer reads every scope's projections; it walks each output
     column's lineage back to the base-table columns that produced it. `sqlglot.lineage`
     runs `qualify` and no other rule, so the number of rewrites this file trusts is
     still two.
- **Sub-step 3.2 was committed in `89fee55` after Amino's 2026-08-18 review**, which
  changed three things and approved the rest.
  1. **The blind spot may pass now, on condition the Gate makes it fail later** —
     opened as [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject),
     whose Trigger is the Sub-step that builds the Validation Gate.
  2. **The larger-than-planned probe set is a planning shortcoming, not scope
     creep** — a Step that measures a boundary should enumerate the shapes it will
     measure at planning time, the way Sub-step 3.3's plan already does. **The
     ruling was completed as [R6](../plan/step-003-validation-feasibility.md#r6--a-probe-that-completes-the-set-is-kept-wherever-it-is-found--ruled-by-amino-2026-08-19)
     at 3.3's review**, and both halves bind every later Sub-step.
  3. **Mutation 2 in the review did not reproduce**, and now does. Reverting the
     tracer to the first version takes two edits rather than one: narrowing the
     traversal to the root scope *and* removing the guard that skips a scope whose
     node is not a `SELECT`. Both `sed` commands still reproduce after 3.4, which
     re-ran all five recorded mutations — **and two of 3.3's own no longer apply**,
     because 3.4 gave `columns_reaching_the_answer` a `dialect` argument and the
     recorded `sed` now matches nothing. A `sed` that matches nothing exits 0 and
     the run passes, which reads exactly like a mutation that broke nothing;
     [3.4's review](../reviews/step-003-validation-feasibility.md#sub-step-34--probe-duckdb--bigquery-retargeting-on-the-sql-veritas-will-generate)
     carries the corrected commands and their output.
  4. **The tracer's docstrings now explain sqlglot step by step** — what
     `parse_one`, `optimize`, `build_scope`, `find_all` and the two generator flags
     each do, and why `isolate_tables` is turned off.
- **Sub-step 3.1 was committed unchanged in `d840fa8`**, so its three points under
  *Look at this sceptically* stand as built with no ruling recorded against them:
  the Sub-step that narrowed one exemption widened another (`EXEMPT` and `HEAD`
  into `check_language.py`'s `KNOWN_NON_ABBREVIATIONS`); `verify_framework.py`'s
  `NNN`/`*` skip is the closest shape found elsewhere and was left, on the ground
  that the function reads exactly one file and so is already file-scoped; and
  `FIXTURE_EXEMPTIONS` is a register holding one entry. **3.2 did not widen any
  exemption**: the abbreviation check failed on two shouted constant names in the
  review's prose and the review was reworded, rather than the list extended.
- **Active Step:** 003 — Prove the Validation Gate's parse-tree claim
  ([plan](../plan/step-003-validation-feasibility.md)), **written and approved
  2026-08-15, committed in `40d72d8`**, and **complete: every Sub-step is built and
  approved, and the plan is `in review` until 3.5's commit makes it `done`**. All
  five Sub-steps are written, four are committed, and the Step
  ran as the five it was planned as — its
  [split point](../plan/step-003-validation-feasibility.md#r5--34-is-a-pre-agreed-split-point--approved-by-amino-2026-08-15)
  never fired. It is the sqlglot spike
  [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
  moved out of Step 002, whose approved 2026-08-05 wording is preserved verbatim
  under [Deferred to Step 003](../plan/step-002-warehouse-and-ingestion.md#deferred-to-step-003--prove-the-validation-gates-parse-tree-claim)
  and whose four questions the plan changes in no way.
- **What the spike found is now in one place**, and this block no longer repeats it:
  [validation-feasibility.md](validation-feasibility.md) carries a verdict per claim,
  the findings behind each, what the Step did **not** measure, and the six
  constraints on the next Step. The dated run output and the mutations that give each
  probe teeth stay in the
  [Step Review](../reviews/step-003-validation-feasibility.md), one Sub-step at a
  time. Read the document first; read the review when you need the command that
  produced a figure.
- **What 3.1 did.**
  [R3](../plan/step-003-validation-feasibility.md#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15)
  landed in its one existing instance, before this Step added a file to a scanned
  root. `check_warehouse.py`'s dialect-scan fixture exemption is now the
  `(file, symbol)` pair `FIXTURE_EXEMPTIONS` rather than the bare name
  `DIALECT_PROBES`, so no other scanned file can claim it by choosing that name;
  the rule in its general form is in `CLAUDE.md` under Non-Negotiable #4; and the
  other three check scripts were swept, with the four constructs examined and the
  verdict on each in the [review](../reviews/step-003-validation-feasibility.md#sub-step-31--scope-every-scan-exemption-to-the-file-it-lives-in).
  **No other exemption needed narrowing, which is what the plan expected.** The
  hole is measured rather than asserted: the same mutation passes `HEAD`'s check
  and fails the narrowed one. **3.2 is the file that R3 was raised about, and it
  passes the dialect scan claiming no exemption at all.**
- **Step 004 is now planned**, which was the first act of the session after 3.5
  landed. Step 003 ended there — all five Sub-steps written, approved and committed.
  **Step 004 is the Semantic Layer**, which was
  [R4](../plan/step-003-validation-feasibility.md#r4--step-003-is-the-spike-alone-the-semantic-layer-is-step-004--approved-by-amino-2026-08-15)'s
  stated expectation, and the plan confirms it rather than inherits it. **The six
  constraints in
  [validation-feasibility.md](validation-feasibility.md#consequences-for-step-004)
  are the input it starts from**, as
  [R3](validation-feasibility.md#r3--the-six-constraints-bind-step-004s-plan--approved-by-amino-2026-08-20)
  requires — two of them, C1 and C2, bind what gets authored, and the other four bind
  the Step after it and are recorded as **not foreclosed** rather than as silence.
  **This planning commit also closes Step 003 formally** — it writes 3.5's hash into
  the list above and turns the
  [plan](../plan/step-003-validation-feasibility.md) from `in review` to `done`,
  which is exactly how `40d72d8` closed Step 002.
  **No component row moved off `✗ none` in Step 003 and none was going to** — a
  spike moves what is known, not what is built. **`Semantic Layer` is the row Step
  004 turns**, and it has not turned yet.
- **The plan's four questions were all approved on 2026-08-15**, recorded as
  [R1–R4](../plan/step-003-validation-feasibility.md#rulings): `Restricted Column`
  is a registered term as of Sub-step 3.3; the spike's certified expressions stay
  Python literals, so the Semantic Layer's file format is not fixed inside a spike;
  **an exemption names the file as well as the symbol** — widened by Amino from the
  new script to every exemption, which is what Sub-step 3.1 is and why the Step has
  five Sub-steps rather than four; and Step 003 is the spike alone, with the
  Semantic Layer as the expected Step 004. **R6 was ruled later, on 2026-08-19**, at
  Sub-step 3.3's review: a probe that completes the set is kept wherever it is
  found, and the Sub-step that finds one owes the account of why the enumeration
  missed it.
- **Step 004 was planned in its own commit rather than appended to the Step it
  follows** — the route to the Target State is discovered one Step at a time, so
  planning it was the next session's first act. **Step 005 is not planned**, and the
  Validation Gate is its *expectation* rather than its plan.
- **Sub-step 2.6 was committed unchanged**, so the three points its review put up
  under *Look at this sceptically* stand as built, with no ruling recorded against
  them: `generate_series` is not standard SQL and the scan does not flag it,
  because sqlglot files it as dialect-neutral; `DIALECT_PROBES` is exempt from the
  scan it feeds, because the probes are real DuckDB SQL living in a scanned file;
  and `sqlglot` was promoted from a transitive dependency to a declared one, which
  the plan text did not ask for. The first and third are inputs to Step 003 —
  claim 4 measures whether a name-based scan is the right instrument at all.
- **The four decisions 2.5 put to Amino were all approved on 2026-08-13**, and two
  of them left something behind:
  1. **A Snapshot is written on the dates *every* Instrument has a Market Price**
     — the intersection, argued under
     [which dates a Snapshot is written on](../reviews/step-002-warehouse-and-ingestion.md#the-decision-this-sub-step-had-to-make-which-dates-a-snapshot-is-written-on).
     Approved. **The dates it drops are now
     [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes):**
     the choice is right given a sparse price table, and the sparse price table is
     the shortcut. An "as of" question about a dropped date has no answer, and the
     absence reads as a zero.
  2. **Cost Basis uses average cost**, not first-in-first-out. Approved as a
     documented behaviour rather than a silent one — see 4 below.
  3. **`fct_accounting_movement.amount` carries magnitudes, positive**, where
     `fct_cash_movement.amount` is signed from the Account's side. Approved. **This
     is the one edit 2.5 made to a file 2.1 committed** — a comment beside the
     column in `schema.sql`.
  4. **Realised P&L is gross of Commission**, which is recognised separately as the
     broker's revenue. Approved. Together with 2 and 1, it is owed a **user-facing**
     home: [DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews)
     records that decisions moving a number a reader will see currently live only
     in Step Reviews, which are the internal record. Paid at the final
     documentation pass, with [DEBT-008](../debt-ledger.md).
- **Two defects were found on review and fixed, both in the same class.** A
  transfer moved a fraction of a share where every Trade is a whole lot, and
  nothing checked it — `--distinctions` now runs `check_lots` over `fct_trade` and
  `fct_position_snapshot`, and it was made to fail before being trusted. And the
  `Cost Basis` / `Execution Price` figure fell back to a Cost Basis when no last
  fill existed, which is a total standing in for a per-unit price. Both are written
  up in the review's changes section; row counts did not move, three Position-side
  figures did.
- **No new Glossary term was coined, and that was checked rather than assumed.**
  The `simulated_*` raw tables follow the source-prefix convention every raw table
  already uses, with the simulator as the source, and the word is already the
  Glossary's own: the `Ingestion` row says *"synthetic Trades, Cash Movements and
  Positions from a seeded simulator"*. If `Simulator` should be a registered
  Section A component, 2.5 is the Sub-step that should have raised it.
- **One new debt: [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level).**
  `Execution Price` against `Market Price` separates every individual Trade and
  nearly cancels across a whole book, because fills sit either side of the close.
  Not a defect in the simulator — introducing a bias to make the total diverge
  would be shaping data to pass our own check — but a constraint on what a gold
  question may ask. Same shape as [DEBT-004](../debt-ledger.md), different cause,
  same trigger: the Gold Question Set.
- **Both Ledger entries that wait on the Gold Question Set now have figures
  measured on the full window** rather than on the spike's three series. DEBT-004's
  FX-date effect is 0.0409% and DEBT-011's is 0.03%; `--distinctions` prints both
  on every run and says whether they clear DEBT-004's 1% line.
- **What is settled and needs no revisiting.** Everything raised on 2026-08-05,
  2026-08-06 and 2026-08-11 has been ruled on and applied — recorded as
  [R7–R10](../plan/step-002-warehouse-and-ingestion.md#r7r10--four-rulings-from-writing-the-data-definition-language-ddl-2026-08-05),
  [R11–R15](../plan/step-002-warehouse-and-ingestion.md#r11r15--five-rulings-from-aminos-review-of-the-snapshot-design-2026-08-06)
  and R16–R20. In short: `Cost Basis`, `Snapshot`, `Instrument Symbol`,
  `Denomination Currency` and `Trade Side` registered and built; Snapshots are
  **end-of-day** and **dense**; the simulator emits **transfers but not corporate
  actions**; `FX Rate` covers the derived cross-rate
  ([R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11));
  [ADR-0004](../adr/0004-snapshot-and-replay-and-where-dlt-stops.md) is `accepted`
  ([R17](../plan/step-002-warehouse-and-ingestion.md#r17--adr-0004-is-accepted--approved-by-amino-2026-08-11));
  a measurement is dated evidence and lives in a review
  ([R18](../plan/step-002-warehouse-and-ingestion.md#r18--a-measurement-is-dated-evidence-and-lives-in-a-review--approved-by-amino-2026-08-11),
  now a [writing convention in CLAUDE.md](../../../CLAUDE.md#writing-conventions));
  and `verify_framework.py` checks anchors as well as files
  ([R20](../plan/step-002-warehouse-and-ingestion.md#r20--verify_frameworkpy-checks-anchors-not-just-files--approved-by-amino-2026-08-11)).
  The two halves excluded from the slice went to
  [EXT-006](../extension-register.md#ext-006--position-change-attribution) and
  [EXT-007](../extension-register.md#ext-007--corporate-actions).
- **The `movement_type` spellings are now frozen in practice.**
  [DEBT-010](../debt-ledger.md) noted they were free to change while the tables
  were empty. 2.5 filled them, so changing one now means regenerating the client
  side — which is one command, but it is no longer free.
- **What Step 003 inherits**, and what its
  [plan](../plan/step-003-validation-feasibility.md) is built on. The sqlglot spike
  deferred by
  [R6](../plan/step-002-warehouse-and-ingestion.md#r6--the-sqlglot-spike-then-numbered-24-is-a-pre-agreed-split-point--approved)
  now has the real data it was moved in order to run against. Its third question
  needs a query computing revenue inline from `commission` to return a *different
  number* from the certified expression against a real warehouse: the 32.59%
  between Gross and Net Revenue is that difference. **Its first bullet — `uv add
  sqlglot` — is already done**, in 2.6, which needed the library for the dialect
  scan. And its fourth question, on DuckDB → BigQuery retargeting, is what tells us
  whether that scan should stay name-based at all.
- **[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect),
  opened in 2.1, is paid — that is what 2.6 is.** The seam scan checked `duckdb`
  imports and not the DuckDB-specific function names ADR-0002 named alongside them;
  it now checks both. The name list is subtracted out of `sqlglot`'s own dialect
  tables rather than typed, probes prove the scan's teeth on every run — three then,
  five since 4.3 gave the scan a second reading — and both ingestion modules were
  mutated with a dialect name and made to fail.
- **Obligations recorded for later Steps**, so they are not rediscovered:
  `README.md` must list every credential Veritas touches
  ([Target State](target-state.md#what-credential-free-means)), and
  [DEBT-008](../debt-ledger.md) fires on the same pass, on the access-control
  claim. [DEBT-002](../debt-ledger.md) was **paid in 2.3** and no longer waits for
  the README — but it constrains what the README may say: *reproducible from
  committed snapshots*, never *reproducible from Yahoo*.

---

## Summary

A fully designed project with three of its nine components built. The framework is
in place and the Target State is `agreed`, so there is a fixed point to build
toward: a natural-language analytics copilot over a brokerage warehouse, whose
answers are grounded in a certified Semantic Layer and checked by a deterministic
Validation Gate.

Every data source that design assumes has been verified obtainable, key-free, and
is snapshotted into the repository. **The Warehouse is full.** The ten-table star
schema of Glossary Section B sits behind the Warehouse Adapter — the only module in
the repository that imports `duckdb`, and the only place a DuckDB-specific function
name appears, both of which are now checked rather than promised — and all ten
tables hold rows. Three are
real: `dim_instrument`, nineteen Instruments across four types and four Quotation
Currencies; `fct_instrument_price`, two years of daily Market Prices covering all
nineteen; and `fct_fx_rate`, every ordered pair of those four currencies on every
calendar date of a window that covers the prices. Seven are synthetic, from a
seeded simulator that prices every Trade off a Market Price the Warehouse already
holds and converts through a real FX Rate: Clients, Accounts, Trades, both movement
ledgers, and dense Position and Cash Balance Snapshots. **One command builds all
ten offline from committed snapshots with no socket opened, and two runs are
byte-identical.**

**Every Certified Metric can now return a number** — all nine of them — and every
pair in Glossary Section C is two measurably different numbers on the loaded data.
The row counts, windows and Section C figures are dated evidence in the
[Step Review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-25--generate-seeded-synthetic-client-activity),
because a `--refresh` moves them.

**The Semantic Layer is built.** Sub-step 4.1 published one Metric Definition and the
Join Path it carries, in the format the Step 004 plan proposed and Amino approved, and
proved the arrangement end-to-end: the expression the file publishes is pasted
verbatim into a query built from the entry's own Join Path and date column, executed
through the Warehouse Adapter, and returns the same figure `check_warehouse.py`
computes from SQL that never reads `semantic/`. 4.2 filled that shape out to all nine
Certified Metrics and the eight Join Paths they are computed across; **4.4 added the
Ambiguous Terms** — the five words of
[Glossary Section D](../glossary.md#d-ambiguous-terms) that resolve to two Certified
Metrics each, which is
[ADR-0001](../adr/0001-semantic-layer-as-the-retrieval-corpus.md)'s reason for
rejecting schema retrieval made into files: *"it cannot represent the one fact that
matters: that 'revenue' has two certified meanings"*; and **4.5 added the certified
axes**, the answer to *"by what?"*, checked against the buckets the Warehouse actually
holds. **All four entry types, every one complete** — twenty-seven entries.
Nothing above the Semantic Layer is built: no Retrieval, no Orchestrator, no
application, and nothing yet turns a question into SQL. **The corpus can be sliced and
not yet slice anything**: applying an axis to a metric is a query, and the one axis
whose column no metric route reaches — `by region` — is the shape of what the next
Step inherits.

**What has moved since is knowledge rather than machinery.** The design's largest
unproven assumption — that sqlglot can decide from a parse tree alone whether a
generated query computes a Certified Metric — is now measured on the real schema
and the real data, on all four of the claims Step 002 deferred, and the verdict is
recorded: **GO on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)**,
in [validation-feasibility.md](validation-feasibility.md), which is the second design
gate beside [data-availability.md](data-availability.md). The go carries six
constraints on the Step that builds the Semantic Layer, two of them sharp enough to
restate anywhere: a certified expression is recognised **by form**, so a paraphrase of
it is refused and the Semantic Layer must publish a form the Orchestrator pastes; and
a certified expression **does not pin down the join**, so a query converting through
the wrong currency column is allowed and is 96% wrong, which is why a Metric
Definition has to carry its Join Path and its date predicate. The fourth claim, which
is ADR-0002's rather than ADR-0003's, is qualified: every parse-tree verdict survives
retargeting to BigQuery and one type does not.

## What is built

| Component | State | Notes |
|---|---|---|
| Python environment | ✅ working | `uv`-managed, CPython 3.14.4, `.venv/`. `pyproject.toml` + `uv.lock` + `.python-version` all pinned. **Four declared dependencies**: `duckdb` (2.1), `dlt` (2.2), `sqlglot` (2.6) and `pyyaml` (4.1). dlt brings roughly forty transitive packages, sqlglot among them — 2.6 promoted it to a declared dependency because `check_warehouse.py` now imports it, and a transitive dependency is one someone else's release notes can remove. `uv add sqlglot` installed nothing: the locked version did not move. **Sub-step 3.2 added a fifth check script and no dependency, and Sub-step 3.3 added neither. Sub-step 4.1 added a sixth check script and `pyyaml`, which the Step 004 plan named as its only new dependency** — the Semantic Layer is YAML, and nothing in the standard library reads it. **Sub-step 4.3 added no dependency and moved one script across the line**: `check_language.py` derives the shouted keywords of the SQL the Semantic Layer publishes rather than remembering them, which means reading the corpus through `veritas.semantic`, which reads YAML. So the stdlib-only check scripts are now **two** — `verify_framework.py` and `check_data_availability.py` — and `check_language.py` joins `check_warehouse.py` and `check_validation_feasibility.py` in importing third-party code. Everything imported anywhere is one of the four libraries the project already declares. |
| Development framework | ✅ working | `CLAUDE.md`, `.claude/docs/` tree, five skills in `.claude/skills/`. Non-Negotiable #4 gained a rule in 3.1: **an exemption is scoped to where it is needed** — a check that excuses something names the file as well as the symbol, never a symbol alone. |
| Framework self-check | ✅ working | `.claude/scripts/verify_framework.py` — structure only (documents exist, links resolve, skills load, interpreter pinned), passes. **Links now include their `#anchor`** ([R20](../plan/step-002-warehouse-and-ingestion.md#r20--verify_frameworkpy-checks-anchors-not-just-files--approved-by-amino-2026-08-11), 2026-08-11): the fragment used to be split off and discarded, so a link to a renamed heading passed, and same-document `#anchor` links were not checked at all. It reports a `dead anchor` distinct from a `dead link` and prints how many links and anchors it checked. Verified by making it fail against a temporary document with two dead anchors, in the [Sub-step 2.4 changes-on-review section](../reviews/step-002-warehouse-and-ingestion.md#changes-made-on-review--2026-08-11-sub-step-24). **Scope widened in 4.1 to include code**: every `.py` file under `veritas/` and `.claude/scripts/` is read for markdown links too, because docstrings cite ADRs and Ledger entries in exactly the same syntax and nothing had ever followed one. That pays [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s second coverage gap, and settles the decision that gap left open: a link inside a `.py` file may point at the same things a link inside a document may, resolved the same way, anchor required. `README.md` is still outside the scope. |
| Language check | ✅ working | `.claude/scripts/check_language.py` — content rules: component names registered, no `proposed` term in code, abbreviations resolvable. Passes. Parses code with `ast` so it checks identifiers, not prose. Partial payment of [DEBT-001](../debt-ledger.md). |
| Glossary | ✅ working | Process Language + Domain Language Sections A–E, all `agreed`, **89 registered terms** as counted by `check_language.py`. **The most recent change is an amendment, and the check that reads it back is what forced it:** the `Dimension Definition` row in Section A listed three axes as *examples* — one of them a single `by date` axis at `trade_date` — where `semantic/dimensions/` publishes five certified axes. The row now names all five with their columns, their grain and their buckets, in the form `check_semantic_layer.py` reads back, and its own amendment note had to be rewritten mid-Sub-step because the check read a quotation of the old wording as a sixth axis. **The amendment before it was found the same way:** Section D's "P&L" row read `Realised · Unrealised · both`, which spells neither of the two Section B terms as registered — a near-collision inside the Glossary itself, resolvable by a reader and by nothing else since Section D was written. Sub-step 4.4 pointed `check_semantic_layer.py` at that column and it failed on the first run; the row now reads `Realised P&L · Unrealised P&L · both`, with a dated note beneath the table, and `both` stays because it is a third *answer* rather than a third Certified Metric. **And before that:** `Cash Balance`'s *Lives in* cell now reads `fct_balance_snapshot`, `semantic/metrics/` — it is a Certified Metric as well as a column, which is [R1 of Step 004](../plan/step-004-semantic-layer.md#r1--cash-balance-becomes-a-certified-metric--approved-by-amino-2026-08-21), carried by Sub-step 4.2 because the check that reads that column fails until it is. **The most recent registration is `Restricted Column`**, added to Section A by Sub-step 3.3 under [R1](../plan/step-003-validation-feasibility.md#r1--term-proposal-restricted-column--approved-by-amino-2026-08-15) — the Sub-step that first gave it a code identifier — and its row says how *in the projection* is judged: on the parse tree once `SELECT *` has been expanded against the real schema, so the name in a comment, a string literal or a filter is not a projection of it. **This row read 88 until 2026-08-20**, when closing Step 003 caught that 3.3's registration had not been counted here; the figure is whatever `check_language.py` prints, which is why it names the script. The change before it was an amendment rather than a registration: `FX Rate`, clarified 2026-08-11 under [R19](../plan/step-002-warehouse-and-ingestion.md#r19--an-fx-rate-includes-the-derived-cross-rate--approved-by-amino-2026-08-11), now says in its own words that a euro-side pair *is* a published ECB reference rate while a pair between two non-euro currencies is the ratio of that date's two published rates — both are FX Rates, and a rate of any other origin is not one. The most recent *addition* is not a Domain Language term but an abbreviation: **NYSE** — New York Stock Exchange — **approved 2026-08-11**, added when R18 moved the reasoning about NASDAQ Trader's second file out of a code comment and into the Step Review, where the abbreviation checker reads it. The same ruling rewrote the `Adjusted Close` / `Market Price` Section C row so its 95.5% divergence figure is dated evidence with the command that reproduces it rather than a standing claim. Sub-step 1.2 added `Market Price`, `Adjusted Close`, `Quotation Currency`; narrowed `Instrument`; renamed `dim_fx_rate` → `fct_fx_rate` and registered `fct_instrument_price`. Step 002 planning added `Execution Price` and its Section C row against `Market Price`. Sub-step 2.1 added `Instrument Symbol`, `Trade Side` and `Denomination Currency` (R7–R9), a Section C row for the last against `Quotation Currency`, and swept the `Dimension Definition` instrument-type values to match the narrowed `Instrument` row (R10); Amino's 2026-08-06 review added `Cost Basis` and its Section C row against `Execution Price`, and registered `Snapshot` (R11–R12). |
| Target State | ✅ working | **`agreed`** 2026-08-03. Terms agreed, data sources verified, rulings R1–R3 applied. One correction 2026-08-05: no date dimension in the Warehouse row. |
| Product brief | ✅ working | `.claude/docs/design/product-brief.md` — the full system Veritas slices, captured so the job description can be removed. |
| Data-availability check | ✅ working | `.claude/docs/design/data-availability.md` + `.claude/scripts/check_data_availability.py`. Verdict GO. Runs offline from `data/snapshots/` or live with `--refresh`; exits non-zero if a source dies, a wrong-number trap vanishes, or a distinction collapses. |
| Data snapshots | ✅ working | `data/snapshots/` — real 2025 FX Rates and three real price series, plus the dated probe record, owned by `check_data_availability.py`. `data/snapshots/ingestion/` beside it is the pipeline's own, one file per source and one per traded Instrument, rewritten only by `--refresh`. Both committed on purpose: they are what make the checks reproduce without network access. |
| Founding ADRs | ✅ working | Four ADRs in `.claude/docs/adr/`, all **`accepted`**. The first three on 2026-08-03: 0001 Semantic Layer as the retrieval corpus, 0002 DuckDB behind an adapter, 0003 Validation Gate as deterministic code. The fourth — snapshot-and-replay, and where dlt stops — was deferred to the ingestion Step ([DEBT-002](../debt-ledger.md)), written in Sub-step 2.2 and **accepted 2026-08-11** (R17). Every cost in each is classified *accepted* / *debt* / *extension*. ADR-0002 carries a dated clarification (2026-08-05) on what its sqlglot commitment forbids; its status stays `accepted`. |
| Warehouse | ✅ working | `veritas/warehouse/schema.sql` — the ten tables of Glossary Section B, **all ten populated**. Monetary columns are `DECIMAL(18, 6)`, FX Rates `DECIMAL(18, 8)`; **no floating-point column exists** and `check_warehouse.py` fails the run if one appears. Foreign keys declared and enforced. Snapshot grain is one row per subject per date, enforced by the primary key. No `dim_date` (R2). The two movement tables carry **opposite sign conventions** and the schema says so beside each column: cash is signed from the Account's side, accounting carries magnitudes so that Net Revenue = Σcommission − Σrebate − Σfee is literally true. |
| Warehouse Adapter | ✅ working | `veritas/warehouse/adapter.py` — the only module in the repository that imports `duckdb`, which is now checked rather than promised. `create_schema`, `tables`, `columns`, `row_count`, `execute`, `query`, plus the `in_memory()` constructor for throwaway databases. Assembles no SQL text from any argument: introspection goes through `information_schema` with a bound parameter, row counts through the relational API. Hardcoded database path and no error handling, both licensed in writing by [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md). |
| Warehouse check | ✅ working | `.claude/scripts/check_warehouse.py` — four checks always, plus `--sources`: the table set matches Glossary Section B *read from the Glossary*, no floating-point columns, fourteen constraint rejections fire against an in-memory Warehouse with a seven-row positive control, and **the adapter seam holds in both the halves [ADR-0002](../adr/0002-duckdb-as-the-warehouse-behind-an-adapter.md) named** — no `duckdb` import outside `veritas/warehouse/`, and no DuckDB-specific **construct** in the SQL that leaves the adapter. The dialect half (2.6) reads every string literal sqlglot parses as a statement — and since **4.3** every SQL field the Semantic Layer publishes, a Metric Definition's `expression` and `filters` and a Join Path's `on` — and reads all of it twice. **By name**: any function call standard SQL does not have, with the name set subtracted out of sqlglot's own dialect tables rather than typed, so the list tracks the library; this fails the run. **By type** (4.3, paying [DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast)): each statement is retargeted to BigQuery and every type construct is compared against the same type retargeted *on its own*, so `DECIMAL(38, 6)` arriving as `NUMERIC` inside a statement and as `NUMERIC(38, 6)` alone is a finding while `VARCHAR` arriving as `STRING` is not; this prints a **review comment** rather than failing, because the corpus carries a widening cast the engine will not compute without — a statement sqlglot cannot write in BigQuery at all *does* fail. `retarget` and `round_trip_rewrites` live here since 4.3 and `check_validation_feasibility.py` imports them back, so the spike's dated measurement and this scan are one trip. Five probes run every time, each recording what **both** readings must say — standard SQL clean, `strftime` named, `list_aggregate` named, a widening cast flagged by type alone, a `VARCHAR` cast clean — and a probe reading wrong in either column fails the run. Those probes are the scan's **one fixture exemption**, and since 3.1 it is scoped to the file it lives in: `FIXTURE_EXEMPTIONS` names `.claude/scripts/check_warehouse.py` as well as the symbol `DIALECT_PROBES`, so no other scanned file can claim it by choosing that name. Pointing the entry at a file that does not exist makes the run fail loudly, so a stale exemption cannot widen quietly. `--rebuild` recreates the database; `--sources` checks the loaded data, one function per star table. For `dim_instrument` (2.2): normalisation, the declared universe, every raw table non-empty, and a **richness** assertion that the universe is thick enough for 2.5. For `fct_instrument_price` (2.3): every price is **re-derived from the committed snapshots in Python** and compared row-for-row against what the SQL built, three named wrong readings are shown to change real rows, and no day-over-day move exceeds 1.5. For `fct_fx_rate` (2.4): every rate is re-derived the same way, two named wrong readings are shown to change real rows, **every Market Price has a rate in its own Quotation Currency on its own date**, and a currency converted through another and back is unchanged within the rounding its stored scale forces. **`--distinctions` (2.5)** adds four more: every client-activity row is exactly what the simulator produces from the same seed, **every quantity is a whole lot of its own Instrument** (added on review, 2026-08-13, after a transfer moved a fraction of a share and nothing objected), every Snapshot is markable and at least one Position Change is one no Trade explains, and **every Glossary Section C pair is printed as two numbers with how far apart they are** — a pair that has collapsed fails the run. `--rebuild` is mutually exclusive with both — together they only prove an empty table is empty. **4.1 added `gross_revenue()`**, the independent figure `check_semantic_layer.py` compares the published expression against, over the whole Warehouse or from a date on. It is written in this file, in its own SQL, and **reads nothing from `semantic/`** — [R2](../plan/step-004-semantic-layer.md#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21) is why, and the price is that editing a published expression means editing this SQL too or the run fails. `--distinctions` now also fails if its own row-level Gross Revenue and that figure disagree. **4.2 added the other eight independent figures** — `net_revenue`, `traded_notional`, `trade_count`, `cash_balance`, `account_value`, `unrealised_pnl`, `realised_pnl`, `position_change` — so every Certified Metric has a second opinion. They are independent in **method** as well as in text: each fetches the component columns and folds them in Python, because a DECIMAL(18, 6) amount times a DECIMAL(18, 8) rate overflows DECIMAL(18) and an aggregate written here would need the same engine-specific width the published expressions carry, in a script that sits outside `veritas/warehouse/`. The `decimal` context precision is set explicitly for the same reason: the default 28 significant digits leaves three digits of margin over the widest fold, and a rounded fold against an exact engine sum would read as a wrong expression. `glossary_tables()` also learned the one *Lives in* home that is not a table, `METRIC_HOME`, which `check_semantic_layer.py` imports rather than spelling again. |
| Validation feasibility spike | ✅ working | `.claude/scripts/check_validation_feasibility.py` (3.2, 3.3, 3.4) — the sqlglot spike, answering **all four claims** of [Step 003](../plan/step-003-validation-feasibility.md). **Not the Validation Gate and not a thin version of one**: it creates no `veritas/validation/` directory and ships no component. A tracer — parse, resolve against the real schema read through `WarehouseAdapter.columns`, rename table aliases back to their base table, canonicalise every projection that aggregates — plus 25 probe statements, each declaring the verdict this spike measured for it. A statement is allowed when it computes at least one metric expression and **every** one traces to a certified expression. Three certified expressions live as Python literals ([R2](../plan/step-003-validation-feasibility.md#r2--the-spikes-certified-expressions-stay-python-literals--approved-by-amino-2026-08-15)), so the Semantic Layer's file format stays unfixed. Every executable probe is executed through the adapter and checked **against another probe's number** rather than against a figure written in the script. It exits non-zero if any verdict, any relation or any detector reading changes, in either direction — a spike's job is to hold its finding still. **3.3 added claim 2**: `resolve` holds the rewriting settings both claims are judged under, `projected_expressions` walks every scope for claim 1, and `columns_reaching_the_answer` walks each output column's lineage for claim 2, so a column that never reaches the answer is not counted; nine shapes are judged three ways each — from the parse tree, by searching the query's text (ADR-0003's rejected alternative), and by claim 1's tracer. **3.4 added claim 4**: every one of the 25 statements is transpiled to BigQuery, re-parsed there and re-judged against a corpus and a schema retargeted the same way, plus two checks the round trip does not answer by surviving — what happened to the one certified expression carrying a cast, and whether transpile-and-compare would be a better dialect scan than `check_seam`'s name list. **4.3 moved `retarget` and `round_trip_rewrites` into `check_warehouse.py`** and this file imports them back, for the reason it already imports `unportable_functions`: a second copy would answer the question about the copy. Its numbers are unchanged by the move, which is what [R4](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)'s pin exists to make checkable. Figures and mutations are dated evidence in the [3.2](../reviews/step-003-validation-feasibility.md#sub-step-32--probe-whether-a-generated-query-traces-to-a-certified-metric), [3.3](../reviews/step-003-validation-feasibility.md#sub-step-33--probe-whether-a-restricted-column-can-hide-from-the-parse-tree) and [3.4](../reviews/step-003-validation-feasibility.md#sub-step-34--probe-duckdb--bigquery-retargeting-on-the-sql-veritas-will-generate) reviews. |
| Validation-feasibility gate | ✅ working | `.claude/docs/design/validation-feasibility.md` (3.5) — the go/no-go the spike exists to produce, in the shape of `data-availability.md` and beside it as the project's second design gate. **Verdict GO on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md)**, with a verdict per claim, what the Step did **not** measure, six constraints on the Step that builds the Semantic Layer, and **four rulings, all approved by Amino on 2026-08-20**. Both ADRs carry a dated status note pointing at it; neither status changed. |
| Semantic Layer | ✅ working | `semantic/` — **all four entry types, every one complete**, twenty-seven entries: nine Metric Definitions in `metrics/`, one per Certified Metric of [Glossary Section B](../glossary.md#b-the-warehouse), and the eight Join Paths in `joins/` they are computed across. A Metric Definition carries its `expression` as the text an Orchestrator pastes verbatim ([C1](validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)) plus what [C2](validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate) requires — the route and the date predicate. **The shape is [R8](../plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)'s**, which amended 4.1's on 2026-08-22: `from_table` names the table the query starts at, `join_paths` is an ordered list, `filters` holds the certified predicates, `date_column` names the column a period filter keys on, `reporting_currency` is present exactly when `unit` is `money`, and `derives_from` names the Certified Metrics whose value is **added** to this metric's own expression. One metric is composed that way — `Account Value` is *"Cash Balance plus all Positions marked to market"* — one carries a filter, two join nothing, and five carry a widening cast without which the engine refuses the expression. A Join Path is unchanged from 4.1 and unchanged by R8: `from_table`, `to_table` and the join condition as written, Reporting Currency literal included, because C1 forbids a template something else fills in. **4.4 added the third entry type**: five Ambiguous Terms in `ambiguous/`, one per row of [Glossary Section D](../glossary.md#d-ambiguous-terms) — `revenue`, `volume`, `balance`, `P&L`, `how much does X have` — each carrying a `description` of why the ambiguity is dangerous, a `resolution` from Section D's own third column, and `disambiguates`, the [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks) field naming the Certified Metrics the word could mean. An Ambiguous Term publishes **no SQL**: it is a claim about language, so it can be wrong while every expression is right, and `SQL_FIELDS` has no row for it. **4.5 added the fourth**: five Dimension Definitions in `dimensions/` — the certified axes a metric can be sliced along, each carrying `columns`, `grain` and `allowed_values`, which are the [Glossary row](../glossary.md#a-the-system)'s own three words for what one names. Three are date axes rather than one: a single axis at `fct_trade.trade_date` could not be applied to the five Snapshot-and-movement metrics whose routes never reach that column, so the corpus publishes `by trade date`, `by snapshot date` and `by accounting movement date`, each named for the registered term it belongs to. `by snapshot date` is one axis over **two** columns, because `Snapshot` is one term registered as living in both Snapshot tables and one calendar writes both. A date axis enumerates no values — they are minted by the data — while `by region` and `by instrument type` enumerate theirs and are checked against what the Warehouse holds. A Dimension Definition publishes **no SQL** either, and it is the only entry type that is a **leaf**: nothing in the corpus names an axis, which is why its checks read the Warehouse rather than the rest of the corpus. **`by region` sits inside no metric route** — no Join Path reaches `dim_client` — so the axis the Glossary's own worked example uses is certified and not yet applicable; the check prints that count rather than failing, and the [4.5 review](../reviews/step-004-semantic-layer.md#sub-step-45--write-the-dimension-definitions) argues why. |
| Semantic Layer loader | ✅ working | `veritas/semantic/` — `loader.py` behind an `__init__.py` that re-exports it, laid out like `veritas/warehouse/`. Reads the tree into frozen dataclasses whose field lists **are** the file format, so there is no second copy of a field name to drift; refuses a file it cannot read as the kind its directory declares, a duplicate entry name, or a field the format does not name. **4.2 widened it to R8's shape** — `join_paths`, `filters`, `from_table`, and `reporting_currency` as the one field a file may omit, which the loader allows and `check_semantic_layer.py` is what judges, because whether omitting it is honest depends on `unit` and a loader reads one file at a time. **Executes no SQL and assembles no query** — C1 puts pasting on the consumer's side. **4.3 added `SQL_FIELDS` and `sql_fields()`**, which say which fields of an entry hold SQL: `expression` and `filters` on a Metric Definition, `on` on a Join Path, nothing on an entry type not listed. They live here for the reason the dataclasses do — the format is here, and each reader deciding for itself is a second copy of it. Two readers ask so far, `check_warehouse.py`'s dialect scan and `check_language.py`'s keyword derivation, and the Orchestrator that assembles a query will be the third. **4.3's prediction that an entry type absent from `SQL_FIELDS` costs those readers nothing held in 4.4**: `AmbiguousTerm` was added with no row, both readers got an empty list, and neither script needed a line changed. **4.4 added that third entry type** — `AmbiguousTerm`, and the `ambiguous` row in `ENTRY_KINDS` that had to arrive with it, because the mapping is not a scan of the tree and a file in a directory it does not know fails to load rather than being skipped. **4.5 added the fourth on the same terms** — `DimensionDefinition`, the `dimensions` row, and `columns` and `allowed_values` in the list of fields that hold lists of strings — and it too needed no row in `SQL_FIELDS`, so both readers were again unchanged. The `kind` a file declares is the Glossary's term snake-cased unless a shorter one is registered, which is why a Metric Definition says `metric` and an axis says `dimension_definition` in full: no `Dimension` is registered, and shortening it would coin a noun. Reads booleans the **YAML 1.2** way rather than PyYAML's YAML 1.1, because a Join Path publishes its condition under the key `on`, which YAML 1.1 reads as the boolean `True`; the same rule keeps `no`, `on`, `y` and `n` as text in any casing, which is what an axis's allowed values need — a country code, a province code, and both halves of a yes/no flag are all domain values that YAML 1.1 would silently turn into booleans. |
| Semantic Layer check | ✅ working | `.claude/scripts/check_semantic_layer.py` (4.1, 4.2, 4.4, 4.5) — **eighteen checks**: the plan's five, a sixth from 4.1, five more from 4.2, three from 4.4 and four from 4.5. Every file loads with every required field; **every Metric Definition's `name` is a Glossary Section B term whose *Lives in* cell says `semantic/metrics/`**, read from the Glossary rather than listed in the script; the expression is **pasted verbatim** into a query built from the entry's own Join Path and date column, executed through the Warehouse Adapter, and must return a number; that number must equal what `check_warehouse.py` computes from its own SQL — **twice, once over the whole Warehouse and once over one period**, because the arithmetic and the date predicate are separate mistakes and the second is invisible to a total; the declared Reporting Currency must appear as a string literal in the named Join Path's parse tree; and an expression that does not parse **fails the run**, with two probes exercising the refusal on every run. A metric with no independent counterpart figure would get the weaker claim — *it executes and returns a number* — and the run would say which it got; **after 4.2 no metric takes that branch**, because all nine have an independent figure. **4.2 added five checks**: every [Section C](../glossary.md#c-distinctions-we-must-not-blur) pair whose both sides are Certified Metrics returns two different numbers **from the published expressions**; a metric's route is a route, so every Join Path it names exists, starts at a table the route has reached, arrives somewhere new, and never reaches forward in its condition; the three expressions the spike measured are **character for character** what `semantic/metrics/` publishes ([R4](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)); a composed metric adds up metrics that exist, are not itself, do not derive further, and share its unit and currency; and every widening cast is shown to be load-bearing by running the expression without it and expecting the engine to refuse. Check 2 now runs in **both** directions, so a Section B metric with no Metric Definition fails the run. **4.4 added three more, and they are the only ones in the file that execute nothing** — they are claims about *language*, so they fail when a word is wrong while every number is right. Every Certified Metric an Ambiguous Term names must exist and there must be at least two distinct ones, which is [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks)'s fourth rule and carries three probes on every run; Glossary Section D and `semantic/ambiguous/` must register the same words, with each row's *Could mean* cell naming the same Certified Metrics its entry does — check 2 pointed at Section D, and it reads the directory name out of Section A's *Lives in* cell too; and no metric's alias may be a registered Ambiguous Term or be claimed by two metrics, which is the decision 4.2 took and nothing enforced. Words in a *Could mean* cell that are **not** Certified Metrics — `both`, on the P&L row — are printed rather than ignored, because a check that silently drops what it cannot resolve drops a misspelling just as silently. **4.5 added four, and they read the Warehouse rather than the corpus**, because a Dimension Definition is the only entry type that is a leaf and nothing above one would notice if it were wrong. Every column an axis names must exist in the live schema; every column of one axis must hold the **same** set of values, and an enumerated axis's buckets must be exactly that set — both directions, so a promised bucket the Warehouse never held and a held value the axis does not name each fail; and an axis must enumerate **exactly when** its buckets are a registered vocabulary rather than dates, since a date's values are minted by the data and a list of them in the corpus would be a measurement dressed as a definition. Five probes give those three teeth on every run. The fourth is check 2 pointed at the Glossary's `Dimension Definition` row, which registers the five axes with their columns, grain and buckets and is read back against the corpus — a prose parse, and [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell) is the cost of it. It also prints, without failing, how many metric routes each axis already sits inside. Needs a filled Warehouse. Twenty-seven mutations, and the figures they produced, are dated evidence in the [4.1](../reviews/step-004-semantic-layer.md#sub-step-41--publish-the-semantic-entry-format-on-one-metric-definition), [4.2](../reviews/step-004-semantic-layer.md#sub-step-42--write-the-remaining-metric-definitions), [4.4](../reviews/step-004-semantic-layer.md#sub-step-44--write-the-ambiguous-terms) and [4.5](../reviews/step-004-semantic-layer.md#sub-step-45--write-the-dimension-definitions) reviews. |
| Ingestion | ✅ working | `veritas/ingestion/` — **both halves**: four real sources and the seeded simulator. `uv run python -m veritas.ingestion` builds all ten tables end-to-end from a clean clone with **no network**, and two consecutive runs produce byte-identical output. `--refresh` is the only mode that opens a socket; a refresh that fails part-way names the snapshots it had already rewritten, and one that succeeds reports how many it rewrote and how many were distinct — **failing the run if a source was fetched twice**. **Two phases, in an order that cannot be reversed:** dlt lands the real sources in `raw` and the adapter builds three star tables from them; then `simulator.py` *reads those three through the adapter*, generates the client side as a pure function of them and a seed, and a second dlt load plus seven more build scripts lands it. No two connections are ever open at once. The pipeline refuses to complete on four silent-shortness conditions, two of them added in 2.5: a Position with no Market Price on its own Snapshot date, and a monetary amount whose Denomination Currency has no FX Rate on its own date. |
| Retrieval | ✗ none | — |
| Orchestrator | ✗ none | — |
| Validation Gate | ✗ none | — |
| App | ✗ none | — |
| Observability | ✗ none | — |
| Evaluation | ✗ none | — |
| Containerization | ✗ none | — |

## Repository layout

```
veritas/
├── CLAUDE.md                  # operating agreement (root: Claude Code auto-loads it)
├── final_proposal_target.md   # source job description — captured into .claude/docs/design/product-brief.md, removable
├── pyproject.toml, uv.lock, .python-version, .gitignore
├── data/
│   ├── snapshots/             # committed source data + dated probe record
│   │   └── ingestion/         # ingestion's own snapshots — one per source, one
│   │                          # per traded Instrument; only --refresh writes here
│   └── veritas.duckdb         # the Warehouse — gitignored, rebuilt by ingestion
├── semantic/                  # the Semantic Layer — the certified registry, as data
│   ├── metrics/               # nine files, one per Certified Metric of Section B
│   │   ├── gross_revenue.yaml            # ─┐ the trade side
│   │   ├── net_revenue.yaml              #  │
│   │   ├── traded_notional.yaml          #  │
│   │   ├── trade_count.yaml              # ─┘
│   │   ├── cash_balance.yaml             # ─┐ the Snapshot side
│   │   ├── account_value.yaml            #  │ composed: its own expression plus
│   │   ├── unrealised_pnl.yaml           #  │ Cash Balance
│   │   ├── position_change.yaml          # ─┘
│   │   └── realised_pnl.yaml             #   the accounting ledger
│   ├── joins/                 # eight routes; two are shared, the rest serve one metric
│   │   ├── trade_to_fx_rate_on_denomination_currency.yaml    # ─┐ the Section C
│   │   ├── instrument_to_fx_rate_on_quotation_currency.yaml  # ─┘ currency pair
│   │   ├── trade_to_instrument.yaml
│   │   ├── balance_snapshot_to_fx_rate_on_snapshot_date.yaml
│   │   ├── position_snapshot_to_instrument.yaml
│   │   ├── position_snapshot_to_price_on_snapshot_date.yaml
│   │   ├── instrument_to_fx_rate_on_snapshot_date.yaml
│   │   └── accounting_movement_to_fx_rate_on_movement_date.yaml
│   ├── ambiguous/             # five words, one per row of Glossary Section D
│   │   ├── revenue.yaml       # ─┐ each names the Certified Metrics it
│   │   ├── volume.yaml        #  │ disambiguates between — and publishes no SQL,
│   │   ├── balance.yaml       #  │ because it is a claim about language
│   │   ├── pnl.yaml           #  │
│   │   └── how_much_does_x_have.yaml  # ─┘
│   └── dimensions/            # five certified axes — the answer to "by what?"
│       ├── by_trade_date.yaml            # ─┐ three date senses, not one: a
│       ├── by_snapshot_date.yaml         #  │ Snapshot metric's route never
│       ├── by_accounting_movement_date.yaml # ─┘ reaches fct_trade.trade_date
│       ├── by_region.yaml                # ─┐ the two enumerated axes; their
│       └── by_instrument_type.yaml       # ─┘ buckets are checked against the data
├── veritas/
│   ├── semantic/
│   │   ├── __init__.py        # re-exports the loader, like veritas/warehouse/
│   │   └── loader.py          # reads semantic/ into frozen entries; executes nothing
│   ├── warehouse/
│   │   ├── adapter.py         # the Warehouse Adapter — the only duckdb importer
│   │   ├── schema.sql         # the ten-table star schema, hand-authored
│   │   └── builds/            # hand-authored raw→star SQL, one file per table
│   │       ├── dim_instrument.sql        # ─┐ the real half, built first
│   │       ├── fct_instrument_price.sql  #  │
│   │       ├── fct_fx_rate.sql           # ─┘
│   │       ├── dim_client.sql            # ─┐ the synthetic half; dim_client.sql
│   │       ├── dim_account.sql           #  │ carries the reasoning for all seven
│   │       ├── fct_trade.sql             #  │
│   │       ├── fct_cash_movement.sql     #  │
│   │       ├── fct_accounting_movement.sql  │
│   │       ├── fct_position_snapshot.sql #  │
│   │       └── fct_balance_snapshot.sql  # ─┘
│   └── ingestion/
│       ├── __main__.py        # the entry point: replay by default, --refresh
│       ├── universe.py        # the 19 traded Instruments + two vocabulary maps
│       ├── snapshots.py       # snapshot-and-replay — the only socket in the package
│       ├── sources.py         # NASDAQ Trader · SEC · Yahoo metadata and bars, for dlt
│       └── simulator.py       # the seeded simulator — reads the real tables,
│                              # generates the client side as a pure function
└── .claude/
    ├── skills/                # 5 framework skills
    ├── scripts/
    │   ├── verify_framework.py        # structure: docs, links, skills, interpreter
    │   ├── check_language.py          # content: Glossary + writing conventions
    │   ├── check_warehouse.py         # schema vs Glossary, constraints, adapter seam
    │   ├── check_semantic_layer.py    # every published expression executes, and agrees
    │   ├── check_validation_feasibility.py  # the sqlglot spike — all four claims
    │   └── check_data_availability.py
    └── docs/
        ├── glossary.md
        ├── debt-ledger.md
        ├── extension-register.md
        ├── design/{target-state,current-state,product-brief}.md
        ├── design/{data-availability,validation-feasibility}.md   # the two design gates
        ├── adr/
        ├── plan/
        └── reviews/
```

## Known gaps

**Everything above Ingestion.** The Warehouse itself has no gaps left: all ten
tables hold rows, and the two components below the Semantic Layer are done.

**Every Certified Metric can now return a number**, which was the claim Step 002
existed to make true and had narrowed three times on the way. After 2.2 nothing
aggregatable existed. After 2.3 there were real Market Prices in four Quotation
Currencies with no way to total them. After 2.4 every price converted, but every
metric the Glossary registers is about *client activity* and not one Trade
existed. 2.5 closed the last gap: all eight are computable, and
`check_warehouse.py --distinctions` computes seven of them as a side effect of
measuring the Section C pairs. **Sub-step 4.2 made it nine and made every one of them
a named function**: `check_warehouse.py` now computes each Certified Metric
independently of `semantic/`, which is what `check_semantic_layer.py` compares every
published expression against.

**What that does not mean.** A metric returning a number is not a metric being
*asked for*. Sub-step 4.2 finished the half this paragraph is about and left the other
half untouched: **all nine** Metric Definitions are now written down and certified, so
every Certified Metric says in a file which arithmetic it is and which rows it is
computed over. Nothing is retrievable — there is no Retrieval — and nothing turns a
question into SQL. The machine that chooses between them does not exist.

**The Semantic Layer is all four entry types, and the gap moved.** `semantic/metrics/`,
`semantic/joins/`, `semantic/ambiguous/` and `semantic/dimensions/` are each complete,
so the corpus carries the claim ADR-0001 rejected schema retrieval for — that
*"revenue"* has two certified meanings — and a metric can be sliced along a certified
axis. What is missing is **the machinery that applies one axis to one metric**: a
Dimension Definition is a leaf, nothing in the corpus points at one, and `by region`
sits inside no metric route at all, because no Join Path reaches `dim_client`.
`check_semantic_layer.py` prints that count on every run. Two things the format
carries are still published and unchecked — `description` and `aliases`, which are
what Retrieval will match on when Retrieval exists. `derives_from` left that list in
4.2 and `grain` left it in 4.5: a Dimension Definition's grain is compared against the
Glossary's, though a Metric Definition's is still read by nobody.

**A Snapshot metric executed over the whole Warehouse is not a number anyone would
ask for.** `Cash Balance` summed across every Snapshot date is every date in the
Snapshot calendar added together — `check_semantic_layer.py` prints how many, on the
`by snapshot date` line — and the check executes it that way on purpose — it is the strongest thing a
corpus check can do without inventing a question. The "as of" date comes from the
question, and no component that asks questions exists yet.

**All four of the spike's claims are answered and the verdict is recorded**, in
[validation-feasibility.md](validation-feasibility.md): tracing and the Shadow Metric
in Sub-step 3.2, Restricted Columns in 3.3, DuckDB → BigQuery retargeting in 3.4, and
the go on [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md) in 3.5.
**What that does not mean is that the Gate is feasible in full.** Of the Validation
Gate's five checks the spike looked at **two** — certified-metrics-only and no
restricted columns. The Access Profile predicate, the bounded scan and read-only are
unexamined; a statement that writes is refused by the tracer, but incidentally rather
than by a rule, and ADR-0003's fail-closed commitment is met by nothing. Only
projections are read for claim 1, so a metric expression that appears solely in a
filter applied after grouping is invisible. The document's own
[what this Step did not measure](validation-feasibility.md#what-this-step-did-not-measure)
is the full list and is deliberately as long as the findings.

**Two Section C pairs are real but small at book level**, and both are on the
Ledger against the Gold Question Set rather than fixed in the data:
[DEBT-004](../debt-ledger.md) (the FX half of Trade Date against Settlement Date)
and [DEBT-011](../debt-ledger.md#debt-011--execution-price-against-market-price-cancels-at-book-level)
(Execution Price against Market Price). Neither is a defect in the simulator —
making either diverge would mean shaping the data to pass our own check — and both
are constraints on what a gold question may ask. `--distinctions` prints both
figures on every run.

The one thing 2.1 chose not to settle is now settled.
[DEBT-009](../debt-ledger.md#debt-009--the-seam-scan-checks-imports-but-not-the-dialect)
— the adapter seam scan checked `duckdb` imports but not the DuckDB-specific
function names ADR-0002 also named — **fired and was paid in 2.6**. Amino ruled the
trigger fired on 2026-08-13
([R21](../plan/step-002-warehouse-and-ingestion.md#r21--debt-009-has-fired-and-is-paid-as-sub-step-26--ruled-by-amino-2026-08-13)):
it reads *"the first component outside the adapter emits SQL"*, and two modules
outside `veritas/warehouse/` hold SQL text — `__main__.py` since 2.2 and
`simulator.py` since 2.5. Both are standard SQL with no dialect-specific name in
them, which is what the entry was *about*, but it is not what the sentence said, and
rewording a trigger to keep an entry unfired is the move Non-Negotiable #2 exists to
prevent.

**Both modules still scan clean, and that is now a result rather than an
assertion.** All ten star-schema build scripts live in `veritas/warehouse/builds/`,
so every dialect-specific name the pipeline uses is inside the licensed directory:
`make_timestamp` from 2.3, `generate_series` over dates and `ASOF JOIN` from 2.4,
and nothing new from 2.5, whose seven builds are projections and casts.

**What the scan does not cover**, so nobody reads the seam as fully mechanical: SQL
assembled at run time is not a literal and is invisible to it — that is the
Validation Gate's subject, not a static scan's — and a name sqlglot files as
dialect-neutral passes even where it is not standard SQL, `generate_series` being
the example this project already uses. Both are argued in the
[2.6 review](../reviews/step-002-warehouse-and-ingestion.md#sub-step-26--scan-for-duckdb-specific-function-names-outside-the-adapter).

[DEBT-010](../debt-ledger.md) was **paid in 2.1** and both `movement_type` columns
now carry a `CHECK`; [DEBT-002](../debt-ledger.md) was **paid in 2.3**, under its
first trigger.

**The cost-basis gap is closed** (2026-08-06). This section previously read that
Realised and Unrealised P&L *"can both be expressed as a weighted average of
Execution Prices over `fct_trade`, so no column is needed"*. Amino's review asked
whether the snapshot design leaves any promised question unanswerable, and walking
all eight Certified Metrics against the ten tables showed that sentence was wrong:
the fold is valid only if a Position opened inside the loaded window, never went
flat and rebuilt, and was never touched by a transfer — the last being the very
thing `fct_position_snapshot` exists because it cannot promise. It is also unsafe
under a Dimension Definition filter, which would narrow `fct_trade` to the asked
period and build the basis from that period's buys alone. `Cost Basis` is now a
registered term and a column. `Realised P&L` needed no schema change — it is a
ledger posting, so it lands in `fct_accounting_movement` as a `movement_type`,
which is why [DEBT-010](../debt-ledger.md) was amended the same day.

The component-name gap found in Sub-step 1.3 is **closed**: all nine Target State
components are now registered Glossary terms, two of them renamed in the process
(`Copilot` → `Orchestrator`, `Interface` → `App`). Every directory Step 002
creates has a name that was agreed before the directory existed, which is the
order Non-Negotiable #1 exists to produce. `check_language.py` enforces it from
here on.

Answered since Sub-step 1.1: the market-price source is **Yahoo's chart
endpoint**, key-free, covering equity/ETF/future/currency pair. Stooq, the
obvious alternative, serves an anti-bot page. Single bonds and options are
**out of scope** — no key-free source exists ([DEBT-003](../debt-ledger.md)).
Still deferred to the retrieval Step: which embedding and re-ranking models.

**The wrong-number traps are defended in the Warehouse itself, not only in the
spike.** `check_data_availability.py` measured two of them on three probe series;
`check_warehouse.py --sources` measures **five** on everything loaded, by
re-deriving every price and every rate from the snapshots in Python and printing
what each wrong reading would have changed. How many rows each moves is a
measurement, so it lives in the Step Review with the command and the date, and the
check prints the current figure on every run. The five:

| Trap | Where it would land |
|---|---|
| `Adjusted Close` instead of the unadjusted close | `fct_instrument_price` — the Section C row for `Market Price` |
| A pence quote carried across as pounds | `fct_instrument_price` — a 100× error, `Quotation Currency` |
| A bar's timestamp read as a Coordinated Universal Time (UTC) date rather than the exchange's own | `fct_instrument_price` — every currency-pair price booked one day early. Found by writing 2.3, not inherited from the spike |
| Rates stored only for the dates the ECB published on | `fct_fx_rate` — every weekend and ECB-holiday Position converted at nothing |
| A published rate read upside down | `fct_fx_rate` — every conversion inverted |

A sixth gotcha is recorded in [data-availability.md](data-availability.md):
Frankfurter returns HTTP 403 to the default `Python-urllib` User-Agent, which reads
as "blocked" when the fix is one header. `snapshots.fetch` sends a descriptive one,
which is why 2.4 hit it nowhere.

## Open debt and extensions

**10 open debt** — see [debt-ledger.md](../debt-ledger.md) — plus **4 paid**, 1
accepted permanently and 2 moved out. **8 open extensions** — see
[extension-register.md](../extension-register.md).

The split is new as of 2026-08-04. Debt means the current code is *wrong,
cheaply*; an extension means it is *right for this scope* and the full system
needs more. The test that settles it: does the trigger fire inside this project's
life? Three Sub-step 1.3 entries failed that test and moved.

- **DEBT-001** — framework rules rely on discipline, not enforcement. **Its second
  coverage gap was paid in Sub-step 4.1**: `verify_framework.py` now resolves
  markdown links and their anchors inside every `.py` file under `veritas/` and
  `.claude/scripts/`, so a document link written in a docstring is checked the same
  way one written in a document is. The entry stays open on its main subject, the
  hook layer — nothing mechanically blocks a commit by Claude, a missing Ledger
  entry, or a review that skips a section.
- **DEBT-002** — **paid 2026-08-10** in Sub-step 2.3, under its first trigger. The
  market-price pipeline was written and the snapshot was already behind it, so a
  clean clone builds the whole Warehouse with the network off. The dependency is
  mitigated rather than removed: the endpoint is still needed to *refresh*, and a
  stale snapshot is still silent.
- **DEBT-003** — no Market Price vendor, so single bonds and options are out of
  scope; a paid vendor is a future setup step.
- **DEBT-004** — the FX-date distinction moves the number by only 0.08%, too
  little to be a reliable evaluation signal; must be addressed when the Gold
  Question Set is built.
- **DEBT-005** — moved to EXT-002. Was never debt: the slice has one schema,
  authored once, so drift cannot occur here.
- **DEBT-006** — **accepted permanently.** No ad-hoc exploration; Veritas is a
  metrics copilot, not a database browser. Now a Target State non-goal.
- **DEBT-007** — moved to EXT-003. Hand-authored YAML is the *better* choice at
  slice scale, not a shortcut.
- **DEBT-008** — narrowed to what can fire here: the README and App must
  not overstate what application-layer access enforcement guarantees. The
  engineering moved to EXT-001.
- **DEBT-009** — **paid 2026-08-13** in Sub-step 2.6, under the trigger Amino ruled
  had fired the same day. The seam scan now checks the DuckDB-specific function
  names ADR-0002 named alongside the imports, with the name list derived from
  sqlglot rather than typed. Two boundaries are stated rather than closed:
  run-time-assembled SQL is invisible to a static scan, and the list is exactly as
  good as sqlglot's dialect tables.
- **DEBT-010** — **paid 2026-08-06**, in the Sub-step that opened it. Both
  `movement_type` columns now carry a `CHECK`, and the two lists differ:
  `realised P&L` is accounting-only, `deposit` is cash-only. It was paid rather
  than deferred because its justification — *"nothing consumes the values yet"* —
  had been falsified by `Realised P&L` landing there. 2.5 has now written rows
  using every one of the spellings, so amending one is a regeneration rather than
  a one-line edit.
- **DEBT-011** — opened 2026-08-11 in Sub-step 2.5. `Execution Price` against
  `Market Price` separates every Trade and cancels across a book. Fires on the
  Gold Question Set, like DEBT-004 and for the same reason: a gold question that
  turns on the pair must be scoped narrowly enough that the two differ by more
  than the comparison's tolerance, or be left out with the limitation stated.
- **DEBT-012** — opened 2026-08-13 on Amino's approval of the Snapshot calendar.
  `fct_instrument_price` is sparse per Instrument, so the calendar has to be the
  intersection and the dates it drops carry no Snapshot at all. An "as of"
  question about one of them returns nothing, which is indistinguishable from an
  Account holding nothing. Fires on the first "as of" date chosen by anything
  other than the calendar itself.
- **DEBT-013** — opened 2026-08-13, also on Amino's instruction. The decisions that
  move a number a reader will see — average-cost Cost Basis, Realised P&L gross of
  Commission, the Snapshot calendar, the two sign conventions — are argued in Step
  Reviews, which `CLAUDE.md` designates the internal working record. A user-facing
  decision register is owed at the final documentation pass, with DEBT-008.
- **DEBT-014** — opened 2026-08-18, on Amino's ruling in the Sub-step 3.2 review.
  The spike prints `ALLOWED` against `Traded Notional` converted through the wrong
  currency column, because the tracer reads the projection and the two joins project
  identically. It is allowed to stay a passing measurement while no Validation Gate
  exists; the Sub-step that builds the Gate is not done until the Gate rejects that
  query and the probe expects a rejection. **Amended 2026-08-20** with a dated status
  note reading the Trade Date / Settlement Date gap as the same question — the
  repayment covers the Join Path **and** the date predicate, and no probe measures the
  date half, so the Sub-step that pays it owes one.
- **DEBT-017** — opened 2026-08-24 in Sub-step 4.5, by the check that made it
  necessary. The five certified axes are registered inside **one Glossary table
  cell** — names, columns, grain and buckets, in prose — and check 18 reads them back
  out of it with a regular expression, where the other two registries this project
  reads back are tables with a row per entry. It works, and it caught a real
  divergence on its first run; what it costs is that the check is bound to a
  sentence's punctuation, which was paid once inside the Sub-step itself when the
  amendment note quoting the old wording failed the run. Repayment is a Glossary
  section of its own, one row per axis — a change to the shape of the shared
  vocabulary, which is Amino's to agree to. Fires on a sixth axis, or the first time
  the cell is reworded and the run fails for it.
- **DEBT-016** — opened 2026-08-21 in Sub-step 4.1. `check_semantic_layer.py` catches
  `Exception` around the two lines that execute a published expression, because
  ADR-0002 puts the engine's dialect — and therefore its exception classes — inside
  the Warehouse Adapter, and the adapter raises nothing of its own. The run still
  fails when the engine refuses; what is wrong is the diagnosis, which reports a bug
  in the script as a defect in the corpus. Repayment is a `WarehouseError` on the
  adapter, and the trigger is the first component outside `.claude/scripts/` that has
  to handle a failed query — the Orchestrator's execute step, which cannot catch
  `Exception` and still tell a user whether the Gate or the engine refused.
- **DEBT-015** — opened 2026-08-20 in Sub-step 3.5, **paid 2026-08-23 in Sub-step
  4.3**, so it is no longer open debt. `check_seam`'s dialect scan named DuckDB-only
  **function** names and so did ADR-0002's stated mitigation, while the one construct
  where Sub-step 3.4 measured meaning being lost on the way to BigQuery is a **cast**,
  which neither reached. It fired in 4.2 on `Traded Notional`'s Metric Definition, and
  wider — every published expression whose product overflows `DECIMAL(18)` carries the
  same cast. The repayment is the name list **plus** a round-trip comparison over
  types, both halves now reading `semantic/` as well as the SQL a module emits, with
  the mitigation reworded to *construct*. It was **ruled debt rather than an extension
  on 2026-08-20**, both arguments on the record, in
  [R2](validation-feasibility.md#r2--debt-015-is-debt-rather-than-an-extension--approved-by-amino-2026-08-20).
- **EXT-006** — attributing a `Position Change` to its cause (Trade, transfer,
  corporate action). Opened 2026-08-06 against the `fct_position_snapshot` seam.
  The metric as registered promises the change, not the cause, so the slice is
  right as built; a reconciliation agent is what needs more.
- **EXT-007** — corporate actions. Opened 2026-08-06. In the full MVP's scope, but
  as something it must not *break* on rather than something it builds: Veritas
  reads a warehouse it did not populate, and a real one already records splits.
  **Its assumption is now checked rather than asserted**: R14 excluded corporate
  actions on the ground that no loaded price series contains one, and
  `--sources` fails the run if any day-over-day ratio exceeds 1.5. The largest in
  the currently loaded window is 1.196.
- **EXT-008** — the two data checks run in continuous integration. Opened
  2026-08-13 on Amino's question about where they belong. `check_warehouse.py` and
  `check_data_availability.py` check the **data**, where `verify_framework.py` and
  `check_language.py` check the way we work — and nothing runs any of them except a
  person remembering to. An extension rather than debt: the scripts are right as
  they stand and this repository has no pipeline to put them in, so the trigger
  could only fire if we chose to make it fire.

[DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s
trigger **fired** in Sub-step 1.3 — a framework rule agreed in 1.2 was broken in 1.3.
Partially paid by `check_language.py` and by new rules in `CLAUDE.md`, and again in
Sub-step 4.1 by the widening of `check_links` to read `.py` files — the gap recorded
on 2026-08-18, paid before the final documentation pass as it required, because that
pass swaps internal document links for user-facing ones and works from the set a
checker can enumerate. **Unpaid: the hook layer.** Nothing mechanically blocks a
commit by Claude, a missing Ledger entry, or a review that skips a section.
