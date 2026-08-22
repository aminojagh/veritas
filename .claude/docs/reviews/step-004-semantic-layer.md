# Step Review — Step 004: Build the Semantic Layer

Handoff notes for the [Step 004 plan](../plan/step-004-semantic-layer.md).
One `## Sub-step` section per Sub-step, appended as each closes.

## Sub-step 4.1 — Publish the Semantic Entry format on one Metric Definition

**What changed**

The Semantic Layer exists. `semantic/` holds its first two entries, `veritas/semantic/`
reads them, and `.claude/scripts/check_semantic_layer.py` proves the published
expression computes the metric it claims to — by executing it and putting the answer
next to one `check_warehouse.py` worked out for itself.

Six things, in the order they were written:

1. **`semantic/metrics/gross_revenue.yaml` and
   `semantic/joins/trade_to_fx_rate_on_trade_date.yaml`** — byte-for-byte the two
   blocks in the plan's [format section](../plan/step-004-semantic-layer.md#the-format-this-step-proposes),
   comments included. Approving the plan approved that shape, so the files are that
   shape rather than an interpretation of it, and a reviewer can diff them against
   the plan instead of re-reading them.
2. **`veritas/semantic/`** — the loader, `loader.py` behind an `__init__.py` that
   re-exports it, the way `veritas/warehouse/` is laid out. It reads the tree into
   frozen dataclasses and refuses anything it cannot read. **Nothing in it executes
   SQL or assembles a query**, which is [C1](../design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)
   taken literally: the Semantic Layer publishes *"a form the Orchestrator pastes"*,
   so pasting belongs to whatever pastes.
3. **`.claude/scripts/check_semantic_layer.py`** — the plan's five checks and one
   more, described under *the sixth check* below.
4. **`gross_revenue()` in `check_warehouse.py`** — the other number. It is written in
   that file, in its own SQL, and reads nothing from `semantic/`, which is
   [R2](../plan/step-004-semantic-layer.md#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21).
   `check_distinctions` gained one assertion that its own row-level Gross Revenue
   agrees with it, so the figure printed by `--distinctions` is the figure the
   comparison used rather than a second one that happens to be close.
5. **`verify_framework.py` now reads code as well as documents** — which pays
   [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s
   **second coverage gap**, not a whim of mine. That gap was opened in Sub-step 3.2
   when Amino ruled that code cites documents as resolvable markdown links, and it
   says the fix is *"one glob wider in `check_links`, plus a decision about what a
   link inside a `.py` file may point at"*. This Sub-step added sixteen more such
   links, so it is the Sub-step that should pay it. The decision, recorded on the
   entry: **the same thing a link in a document may point at, resolved the same
   way** — relative to the file carrying it, anchor required to exist. Six lines,
   and no false positives, because a bracketed label immediately followed by a
   parenthesised path is not otherwise Python.
6. **`uv add pyyaml`** — the Step's only new dependency, as planned.

**The one place the approved format did not survive contact, and it was the reader's
fault rather than the format's.** PyYAML implements YAML 1.1, in which `on`, `off`,
`yes`, `no`, `y` and `n` are booleans. A Join Path's join condition is published under
the key `on` — SQL's own word — so `yaml.safe_load` returned a mapping with the field
missing and an unnamed `True` beside it. Quoting the key in the file would have fixed
that one key and left the values, which is where it gets expensive: Sub-step 4.5
writes allowed values for a Dimension Definition, and YAML 1.1 reads `no`, `on`, `y`
and `n` as booleans **in any casing** — which is Norway's country code, Ontario's
province code, and both halves of every yes/no flag ever written. So the loader reads booleans the
way YAML 1.2 — the current specification — does, which is also how Go's `yaml.v3` and
JavaScript's `js-yaml` already read them. The files are unchanged and more portable,
not less.

**Nothing was built that the plan puts in a later Sub-step.** No second Metric
Definition, no Ambiguous Term, no Dimension Definition, no `veritas/validation/`, no
Access Profile, no Glossary amendment. `check_warehouse.py`'s dialect scan still does
not read `semantic/` — that is Sub-step 4.3's repayment of
[DEBT-015](../debt-ledger.md#debt-015--the-dialect-scan-names-functions-and-the-loss-measured-was-in-a-cast),
whose Trigger fires in 4.2 and not here.

**The sixth check, and why it is not scope creep**

The plan lists five checks. There is a sixth: **every Metric Definition's `name` must
be a Glossary Section B term whose *Lives in* cell says `semantic/metrics/`**, read
out of the Glossary rather than listed in the script.

It is Non-Negotiable #1 applied to the one place this corpus can coin a domain noun
by accident — the `name:` field is a domain noun that becomes what Retrieval matches
on and what Lineage records. It also mechanises
[R1](../plan/step-004-semantic-layer.md#r1--cash-balance-becomes-a-certified-metric--approved-by-amino-2026-08-21):
`Cash Balance`'s registered home was `fct_balance_snapshot`, so writing its Metric
Definition in 4.2 **fails this check** until the Glossary row is amended in the same
commit. R1 was found by reading the Glossary by hand while planning; this is the same
finding made mechanical, and it is about twenty lines.

Only one direction is checked. *Every Section B metric has a Metric Definition* is the
bar [4.2 sets for itself](../plan/step-004-semantic-layer.md#42--write-the-remaining-metric-definitions),
and asserting it now would fail on the eight metrics 4.2 is for.

**Verification**

Every command below was run on **2026-08-21**, offline, in the order shown. The
Warehouse was rebuilt from the committed snapshots in this session first, so every
figure is a reading of rows built minutes earlier rather than of a database left over
from Step 003.

```
$ uv run python -m veritas.ingestion
  mode: replay (offline)
  snapshots: data/snapshots/ingestion
  universe: 19 Instruments
  simulator seed: 20260811
  removed data/veritas.duckdb — rebuilding

  · dim_account                  24 rows
  · dim_client                   12 rows
  · dim_instrument               19 rows
  · fct_accounting_movement    4654 rows
  · fct_balance_snapshot      15402 rows
  · fct_cash_movement          5921 rows
  · fct_fx_rate               11840 rows
  · fct_instrument_price       9554 rows
  · fct_position_snapshot     61907 rows
  · fct_trade                  1670 rows

PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9554 Market Prices across all 19 · fct_fx_rate holds 11840 FX Rates and every Market Price has one
       the client side holds 12 Clients · 24 Accounts · 1670 Trades · every Position is markable and every amount is convertible
exit=0
```

The Sub-step's own check, in full:

```
$ uv run python .claude/scripts/check_semantic_layer.py
  Semantic Layer: semantic/ — 1 Metric Definition(s), 1 Join Path(s)
  Glossary Section B names 8 terms living in semantic/metrics/
  Warehouse: data/veritas.duckdb

  Gross Revenue  v1  ·  money in EUR  ·  one row per Trade
      expression   sum(fct_trade.commission * fct_fx_rate.fx_rate)
      join path    trade_to_fx_rate_on_trade_date — fct_trade → fct_fx_rate
      date column  fct_trade.trade_date
      query        SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) FROM fct_trade JOIN fct_fx_rate ON fct_fx_rate.rate_date = fct_trade.trade_date AND fct_fx_rate.from_currency = fct_trade.denomination_currency AND fct_fx_rate.to_currency = 'EUR'
      returns      195,260.14 EUR
      compared     check_warehouse.py computes 195,260.14 from its own SQL — identical
      period       2024-08-12 … 2026-08-06, split at 2025-08-09: 87,190.71 + 108,069.43 = 195,260.14
      compared     check_warehouse.py computes 108,069.43 from 2025-08-09 on — identical

  parse rule — an expression that does not parse fails the run
    refuses  an unclosed call: 'sum(fct_trade.commission'
    refuses  nothing at all: ''

PASS — every published expression executes against the Warehouse, and every figure with a second opinion agrees with it
exit=0
```

**The `query` line is the deliverable.** It is what an Orchestrator will paste, it was
built from the entry's own `join_path` and `date_column`, and the expression inside it
is the file's text unaltered. It is also the shape the Sub-step 3.2 spike's `bare`
probe writes out by hand — the spike had to, because no Semantic Layer existed yet to
publish one. Whether the two are still the same *text* is deliberately not asserted
here: that is [R4](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)'s
pin, which lands in 4.2 once all three of the spike's expressions are published.

`check_warehouse.py`, whose seam scan and dialect scan now read three more files:

```
$ uv run python .claude/scripts/check_warehouse.py
  Warehouse: data/veritas.duckdb (already existed)
  Glossary Section B names 10 tables · the Warehouse has 10
    … 60 lines of column listing, unchanged …
  seam scan: 17 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py
  dialect scan: sqlglot files 51 function names under DuckDB that standard SQL does not have
    probe: clean
    probe: STRFTIME
    probe: LIST_AGGREGATE
      4 SQL statements in veritas/ingestion/__main__.py
      5 SQL statements in veritas/ingestion/simulator.py
      1 SQL statements in .claude/scripts/check_semantic_layer.py
     28 SQL statements in .claude/scripts/check_validation_feasibility.py
     51 SQL statements in .claude/scripts/check_warehouse.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
exit=0
```

**Seventeen Python files, one `duckdb` import, and no exemption claimed** — the seam
holds across a new component. The one SQL statement the scan reads in
`check_semantic_layer.py` is worth naming, because it is not what a reader would
guess: it is the literal `'SELECT '`, the constant fragment of the f-string that
assembles a metric's query. The rest of that query is built at run time and is
therefore invisible to the scan, which is the boundary `sql_statements` documents —
*"SQL assembled at run time … is not a literal and is not seen"*. The published
expression itself is text in a YAML file and is read by no scan at all until 4.3.

`--distinctions`, where the independent Gross Revenue figure is printed and now
carries the agreement assertion:

```
$ uv run python .claude/scripts/check_warehouse.py --distinctions
    … unchanged through the client-activity, lot and Snapshot checks …
  Section C — every pair, both numbers
    Gross Revenue / Net Revenue — "reporting gross as net overstates what the business keeps"
      Gross Revenue: 195,260.14 EUR
      Net Revenue: 131,618.93 EUR
      32.59% apart
    … the other three pairs, unchanged …
PASS — the star schema matches Glossary Section B and the adapter seam holds
exit=0
```

The three framework and language checks:

```
$ uv run python .claude/scripts/verify_framework.py
  links      653 links, 429 anchors 44 documents and python files
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3
PASS — framework is wired up correctly
exit=0

$ uv run python .claude/scripts/check_language.py
  proposed terms: 0 · python files scanned: 17 · identifiers: 1088
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised
PASS — documents agree with the Glossary and the writing conventions
exit=0

$ uv run python .claude/scripts/check_validation_feasibility.py
    … every claim, unchanged …
PASS — every probe's verdict, every probe's number and every detector's reading is the one this spike recorded
exit=0
```

**`check_language.py` failed once, on this review's own prose, and the prose was
changed rather than the exempt list.** The paragraph about YAML 1.1 named Norway's
country code in capitals, which the abbreviation check correctly read as an
abbreviation a reader cannot look up. It is the same resolution
[Sub-step 3.2](step-003-validation-feasibility.md#sub-step-32--probe-whether-a-generated-query-traces-to-a-certified-metric)
took when two shouted constant names failed the same check: widening
`KNOWN_NON_ABBREVIATIONS` would buy one sentence at the price of the rule. The
paragraph now names the boolean words in the lower case YAML 1.1 also accepts, which
is more accurate anyway — the casing does not matter to the bug.

**44 sources** where every run before this Sub-step read documents alone: 27
documents — this review is the 27th — and 17 Python files. Sixteen of the code
citations were written by this Sub-step and none of them, new or old, had ever been
followed by anything.

**The checks were made to have teeth, by eight mutations**

A corpus that passes its own check proves nothing until the check is shown to fail on
a corpus that should not pass. Each mutation below was applied, run, and reverted, and
every file was compared with `cmp` against its pre-mutation copy afterwards — output
at the end.

**Mutation 1 — the plan's own: `commission` becomes `rebate` in the expression.**

```
      returns      34,692.76 EUR
      compared     check_warehouse.py computes 195,260.14 from its own SQL — DIFFERENT
      period       2024-08-12 … 2026-08-06, split at 2025-08-09: 15,368.50 + 19,324.26 = 34,692.76

FAIL — 1 problem(s)
  - 'Gross Revenue': the published expression returns 34,692.76 EUR and check_warehouse.py's independent SQL returns 195,260.14. One of the two is wrong, and neither file is entitled to assume it is the other one
exit=1
```

This mutation is also what found a wrong sentence in this script. The first version
reported **two** problems, the second reading *"the two totals agree, so this is the
date predicate rather than the arithmetic"* — which was false, since the totals had
just disagreed. The period comparison is the *date predicate* check and can only say
that once the arithmetic agrees, so it is now skipped when the totals already differ.
The check no longer reports one defect twice under a heading naming the wrong cause.

**Mutation 2 — `date_column` becomes `fct_trade.settlement_date`.** This is the one
that matters, because it is
[R2](../plan/step-004-semantic-layer.md#r2--the-semantic-layer-and-check_warehousepy-stay-independent--approved-by-amino-2026-08-21)'s
second example and the [Section C](../glossary.md#c-distinctions-we-must-not-blur)
pair that *"shifts revenue across period boundaries"*:

```
      returns      195,260.14 EUR
      compared     check_warehouse.py computes 195,260.14 from its own SQL — identical
      period       2024-08-14 … 2026-08-10, split at 2025-08-12: 86,649.09 + 108,611.05 = 195,260.14
      compared     check_warehouse.py computes 107,868.99 from 2025-08-12 on — DIFFERENT

FAIL — 1 problem(s)
  - 'Gross Revenue': from 2025-08-12 on, the published expression filtered on fct_trade.settlement_date returns 108,611.05 and check_warehouse.py's independent period filter returns 107,868.99. The two totals agree, so this is the date predicate rather than the arithmetic — a Glossary Section C pair, which is the whole reason C2 asks a Metric Definition to carry one
exit=1
```

**Read the first three lines: the totals are identical and the split still adds up.**
A check that compared only unfiltered totals would have passed this, and a check that
only asked whether the halves partition would have passed it too — `settlement_date`
partitions perfectly well, it just partitions the wrong rows. This is why
`check_warehouse.py`'s independent figure takes a period boundary rather than only a
total: it was written without one at first, and this mutation is what showed that
version agreeing with a Metric Definition naming the wrong date.

**Mutations 3 to 6 — one per remaining check**, each the smallest edit that should
fail it:

```
=== reporting_currency: EUR -> USD ===
FAIL — 2 problem(s)
  - Metric Definition 'Gross Revenue' declares reporting_currency 'USD', and Join Path 'trade_to_fx_rate_on_trade_date' converts to ['EUR'] — the currency is written in both places because C1 forbids a template, and the two have drifted apart
  - 'Gross Revenue' declares reporting_currency 'USD' and check_warehouse.py computes its figures in 'EUR' — two numbers in different currencies agreeing would mean nothing, and disagreeing would mean less
exit=1

=== join_path names a Join Path that does not exist ===
FAIL — 1 problem(s)
  - Metric Definition 'Gross Revenue' names Join Path 'trade_to_fx_rate_on_settlement_date', which no file under semantic/joins/ publishes — so the route the expression is computed over is one the corpus does not certify
exit=1

=== name: Gross Revenue -> Gross Commission ===
FAIL — 1 problem(s)
  - Metric Definition 'Gross Commission' is not a Glossary Section B term whose 'Lives in' cell says semantic/metrics/ — register the term, or amend its row, before certifying a computation under that name
exit=1

=== the date_column field is deleted ===
  semantic/metrics/gross_revenue.yaml: missing required field(s) ['date_column']

FAIL — the Semantic Layer does not load, so nothing below ran
exit=1
```

`Gross Commission` is not an arbitrary mutation — it is one of the three `aliases` the
entry itself publishes, which is exactly the wrong name someone would reach for.

**Mutation 7 — edit `check_warehouse.py`'s SQL instead of the YAML**, converting on
Settlement Date there. R2's authoring tax is supposed to cut both ways, and it does:

```
$ uv run python .claude/scripts/check_semantic_layer.py
FAIL — 1 problem(s)
  - 'Gross Revenue': the published expression returns 195,260.14 EUR and check_warehouse.py's independent SQL returns 195,180.21. One of the two is wrong, and neither file is entitled to assume it is the other one
exit=1

$ uv run python .claude/scripts/check_warehouse.py --distinctions
FAIL — 1 problem(s)
  - the two Gross Revenue figures in this file disagree: this check's row-level sum is 195,260.14 EUR and gross_revenue()'s aggregate is 195,180.21 — the second is what check_semantic_layer.py compares the published expression against, so the figure printed below would not be the figure that was compared
exit=1
```

**Mutation 8 — rename an anchor a docstring cites**, to show the new half of the link
check reads code and reads the anchor rather than only the file:

```
$ uv run python .claude/scripts/verify_framework.py
FAIL — 1 problem(s)
  - veritas/semantic/loader.py: dead anchor -> ../../.claude/docs/extension-register.md#ext-005--semantic-layer-coherence-rules
exit=1
```

That half also caught its own author on its first run: the docstring explaining the
new check contained a two-character example link, which the check correctly reported
as dead. It is now written without one.

**Every mutation reverted:**

```
$ cmp semantic/metrics/gross_revenue.yaml <pre-mutation copy>
cmp gross_revenue.yaml: identical
$ cmp .claude/scripts/check_warehouse.py <pre-mutation copy>
cmp check_warehouse.py: identical
$ cmp veritas/semantic/loader.py <pre-mutation copy>
cmp loader.py: identical
```

**Deliberately left undone**

**One Ledger entry opened and one half-entry paid.**

- **Opened —
  [DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type):**
  `check_semantic_layer.py` catches `Exception` around the two lines that execute a
  published expression, because it may not name DuckDB's error class and the adapter
  has no error class of its own. The run still fails when the engine refuses; what is
  wrong is the diagnosis, which would blame a YAML file for a bug in this script.
  Repayment is a `WarehouseError` on the adapter.
- **Paid — [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s
  second coverage gap**, as described above. The entry stays open: its main subject,
  the hook layer, is untouched, and its *Still unpaid* paragraph now says so alone.

**Open debt is now 10**, and drops back to 9 when 4.3 pays DEBT-015.

**Four things the format carries that nothing checks**, each named here rather than
left for a reader to discover:

- **Field *names* are not checked against the Glossary.** The plan settled this —
  *"extending `check_language.py` to scan YAML keys would be a sixth Sub-step"* — and
  said the review must state the limitation plainly, so: the only thing pinning
  `date_column`, `join_path`, `grain`, `unit` and the rest to those spellings is that
  the loader's dataclasses require them. Rename a key in the file and it fails to
  load; rename it in both places and nothing objects, however un-Glossary the new name
  is. What *is* checked is the `name:` value, which is the sixth check above.
- **`derives_from` is published and unread.** It is
  [EXT-005](../extension-register.md#ext-005--semantic-layer-coherence-checks)'s field
  and one of its four rules; 4.4 takes a different one of the four. `[]` is the only
  value in the corpus, so nothing is currently wrong — but nothing would notice if it
  named a metric that does not exist.
- **`description`, `grain`, `unit` and `aliases` are unvalidated free text.** They are
  what Retrieval will match on, and this Step builds no Retrieval. The claim made
  today is that they are *carried*, not that they are *right*.
- **The published expression is not read by the dialect scan.** It is SQL in a YAML
  file, and both halves of the seam scan read Python. 4.3 is where `check_seam` starts
  reading `semantic/`, which is DEBT-015's repayment and is scheduled rather than
  deferred.

**No Glossary change.** None was needed: every field name is either a registered term
or a plain word from the `Metric Definition` row's own definition, and the one domain
noun in the data — `Gross Revenue` — was already registered with `semantic/metrics/`
as its home.

**Look at this sceptically**

**1. The YAML 1.2 boolean resolver is a judgement call about someone else's library.**
Twelve lines of this loader replace PyYAML's boolean rules. The case for it is above;
the case against is that a reader who knows PyYAML will not expect `on:` to be a
string, and the fix lives in code rather than in the file where the problem is
visible. The alternative — writing `"on":` in every Join Path file — is one character
per file and needs no explanation, at the price of leaving the *values* wrong for 4.5.
If you would rather have the quoting, it is a two-line revert plus a quoted key, and
4.5 inherits a trap that will be worth a comment of its own.

**2. `join_path` is a single name, and `Account Value` is going to want two.** The
format was approved with a scalar and one metric is honestly served by a scalar. But
`Account Value` is *"Cash Balance plus all Positions marked to market"*, which needs
`fct_position_snapshot` → `fct_instrument_price` → `fct_fx_rate` and
`fct_balance_snapshot` → `fct_fx_rate`. Neither is one `from_table`/`to_table` pair.
Three ways out — a list of Join Paths, a Join Path that names more than two tables, or
`Account Value` deriving from two metrics through `derives_from` — and I did not pick
one, because 4.1's job is to expose the shape on one instance and this is exactly the
kind of thing it was supposed to expose. **Deciding it before 4.2 starts costs one
file to re-edit; deciding it during 4.2 costs eight.** It is the single most likely
reason 4.2 comes back for a plan amendment.

**3. The sixth check is more than the plan asked for.** It is twenty lines and it
mechanises a ruling, but it is still a check nobody approved, and it reads Glossary
Section B by cell position — which is `check_warehouse.py`'s technique, and a third
Glossary parser in this repository. Consolidating the three readers is not something I
did, and it is not obviously worth doing while each reads a different thing.

**4. The period split's boundary is the midpoint of the metric's own date range, which
means the check chooses its own test.** A metric whose data all sits in one week would
split into two thin halves and the third claim would be weak without saying so — the
"everything on one side" guard only catches the degenerate case. A fixed boundary
would be worse (it goes stale), but a reader should know the split point is derived
from the data being checked.

**5. `check_distinctions` gained an assertion it did not ask for.** It now fails if its
row-level Gross Revenue and `gross_revenue()`'s aggregate disagree. The two can only
disagree when a Trade is missing a Market Price, which the surrounding count check
already reports in better words — so this is arguably a redundant check bolted onto a
Sub-step-2.5 function. The reason it is there is narrow: without it, the figure
`--distinctions` prints and the figure `check_semantic_layer.py` compares against are
two different computations that nothing ties together, and a reader would have no way
to know which one they were looking at.

**6. `INDEPENDENT_FIGURES` has one entry, so R2's weaker branch has never run.** The
"nothing to compare against" path prints a sentence no test has exercised, because
every metric in the corpus has an independent figure. 4.2 is where that branch first
fires, and it will fire for most of the eight.

**Language**

No terms added, renamed or proposed. Every identifier this Sub-step introduces is
either a registered Glossary term in code spelling — `SemanticLayer`,
`MetricDefinition`, `JoinPath`, `SemanticEntry`, `gross_revenue`,
`reporting_currency`, `join_path`, `date_column` — or plain English from the
`Metric Definition` row's own definition, which is what the plan's format section
argued and what writing the files before the loader was meant to keep honest.

`certified_metric_terms`, `executable_query`, `reads_as_a_query`, `one_number`,
`rows_from` and `check_period_split` name what the code does rather than a domain
concept, and are the only new names that are not Glossary terms.

**Closed on 2026-08-22.** Amino reviewed and approved the Sub-step, and ruled that the
`join_path` question above — point 2 — **is settled at the start of Sub-step 4.2
rather than before it**. The Resume-here block records that, so 4.2 opens on the
decision instead of discovering it eight files in.

Two documents changed after the verification block above was written, both corrections
rather than new work: DEBT-001's paid-gap paragraph said the Sub-step added *twelve*
code citations where the diff adds sixteen, and the Resume-here block was rewritten
around the ruling. All six checks were re-run at close-out and every one still passes
with the output shown above — `check_semantic_layer.py`, `check_warehouse.py` with and
without `--distinctions`, `check_validation_feasibility.py`, `verify_framework.py` and
`check_language.py`. The Warehouse was not rebuilt between the two runs, so the figures
are readings of the same rows, which is why they are identical to the digit.
