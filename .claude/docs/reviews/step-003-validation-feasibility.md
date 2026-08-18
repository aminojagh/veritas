# Step Review — Step 003: Prove the Validation Gate's parse-tree claim

Handoff notes for the [Step 003 plan](../plan/step-003-validation-feasibility.md).
One `## Sub-step` section per Sub-step, appended as each closes.

## Sub-step 3.1 — Scope every scan exemption to the file it lives in

**What changed**

[R3](../plan/step-003-validation-feasibility.md#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15)
lands, in the one place it currently applies, **before** this Step adds a new file
to a scanned root. Nothing about the spike is touched: no new script, no schema
change, no pipeline behaviour, and the Warehouse is byte-for-byte the one Step 002
left.

- **`check_warehouse.py`'s fixture exemption is now a `(file, symbol)` pair.** The
  dialect scan reads the SQL a module emits, and that file writes deliberately
  DuckDB-specific SQL in order to test the scan, so its own `DIALECT_PROBES` tuple
  has to be excused or the check fails on its own test data. What was wrong was the
  *shape* of the excuse: it matched the assignment name alone, in any scanned file.
  The new `FIXTURE_EXEMPTIONS` set names `.claude/scripts/check_warehouse.py` as
  well as `DIALECT_PROBES`, so no other file can claim it by choosing that name.
  `sql_statements` resolves the path it is scanning to a repository-relative one
  and looks up only the symbols exempt *there*.
- **The docstring says what the narrowing did and did not do.** It removes the
  loophole and not the cost: SQL put in a tuple by that name **inside
  `check_warehouse.py`** is still invisible to the scan, and the docstring now says
  so in those words rather than the file-agnostic ones Sub-step 2.6 wrote.
- **The rule itself is in `CLAUDE.md`**, under Non-Negotiable #4 — approved with
  the plan, because `CLAUDE.md` is the operating agreement and this is Claude
  editing it. It reads: *"A check that excuses something names the **file** and the
  **symbol** it excuses, never a symbol alone — an exemption claimable by writing a
  magic name is a hole any later file can walk through, and the directories these
  checks scan are the directories we keep adding files to."*
- **The other three check scripts were swept**, and the result is reported under
  *Look at this sceptically* below: no exemption in any of them needed narrowing,
  which is what the plan expected going in.
- **Two tokens were added to `check_language.py`'s `KNOWN_NON_ABBREVIATIONS`**, and
  they are the one unplanned edit here. Writing this review made the abbreviation
  check fail on `EXEMPT` and `HEAD` — the first because a sweep of the check
  scripts has to be able to name the list that is called that, the second because
  measuring the hole meant comparing against the committed version. Neither is an
  abbreviation: `EXEMPT` is a module-level constant name quoted in prose, which is
  a category that list already has, and `HEAD` is git's name for the current
  commit. Both will recur in later reviews, so the fix is the list rather than the
  wording.

**Verification**

The check itself, on the repository as it stands:

```
$ uv run python .claude/scripts/check_warehouse.py
  seam scan: 13 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py
  dialect scan: sqlglot files 51 function names under DuckDB that standard SQL does not have
    probe: clean
    probe: STRFTIME
    probe: LIST_AGGREGATE
      4 SQL statements in veritas/ingestion/__main__.py
      5 SQL statements in veritas/ingestion/simulator.py
     49 SQL statements in .claude/scripts/check_warehouse.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
exit=0
```

Same counts as Sub-step 2.6 recorded, which is the point: a narrowing that changed
what the scan *covers* would have moved them.

**The narrowing was made to have teeth**, by the mutation the plan specifies — a
tuple named `DIALECT_PROBES`, holding DuckDB-specific SQL, put into a module that
is not the one the exemption names:

```
$ sed -i "s/^SEED = 20260811\$/DIALECT_PROBES = (\"SELECT strftime(trade_date, '%Y') FROM fct_trade\",)\n\nSEED = 20260811/" veritas/ingestion/simulator.py
$ uv run python .claude/scripts/check_warehouse.py
  dialect scan: sqlglot files 51 function names under DuckDB that standard SQL does not have
    probe: clean
    probe: STRFTIME
    probe: LIST_AGGREGATE
      4 SQL statements in veritas/ingestion/__main__.py
      6 SQL statements in veritas/ingestion/simulator.py
     49 SQL statements in .claude/scripts/check_warehouse.py

FAIL — 1 problem(s)
  - veritas/ingestion/simulator.py:76 emits SQL calling STRFTIME(), which sqlglot knows as DuckDB's and not as standard SQL's — ADR-0002 names a DuckDB-specific function name outside the adapter as the signal that the seam has stopped holding
exit=1
```

**And the hole it closes is measured rather than asserted.** The plan's claim is
that the old exemption *"is keyed on the assignment name alone and is file-agnostic,
so any scanned file can claim it by choosing that name"*. With the same mutation
still in place, the version of the check at `HEAD` was run against it:

```
$ git show HEAD:.claude/scripts/check_warehouse.py > .claude/scripts/check_warehouse_at_head.py
$ uv run python .claude/scripts/check_warehouse_at_head.py
  seam scan: 14 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py
  dialect scan: sqlglot files 51 function names under DuckDB that standard SQL does not have
    probe: clean
    probe: STRFTIME
    probe: LIST_AGGREGATE
      4 SQL statements in veritas/ingestion/__main__.py
      5 SQL statements in veritas/ingestion/simulator.py
     49 SQL statements in .claude/scripts/check_warehouse.py
     49 SQL statements in .claude/scripts/check_warehouse_at_head.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
exit=0
$ rm .claude/scripts/check_warehouse_at_head.py
```

Read the two runs against each other. Same repository, same mutation, two versions
of one check: the old one reads **5** statements in `simulator.py` and passes, the
new one reads **6** and names `STRFTIME`. The missing sixth is the mutation, walking
through the hole. (The old run scans 14 files rather than 13 and reports its own
49 statements twice, because resurrecting `HEAD`'s script puts a second copy inside
a scanned root for the length of the run. It is deleted immediately after.)

Then restored, and the restoration checked rather than assumed:

```
$ git checkout -- veritas/ingestion/simulator.py
$ cmp <pre-mutation copy> veritas/ingestion/simulator.py && echo identical
identical
```

**The exemption was also shown to still be live**, because an exemption that has
quietly stopped applying is dead text that reads like a rule. Pointing it at a file
that does not exist, leaving the symbol alone:

```
$ sed -i 's|(".claude/scripts/check_warehouse.py", "DIALECT_PROBES"),|(".claude/scripts/nowhere.py", "DIALECT_PROBES"),|' .claude/scripts/check_warehouse.py
$ uv run python .claude/scripts/check_warehouse.py
     52 SQL statements in .claude/scripts/check_warehouse.py

FAIL — 2 problem(s)
  - .claude/scripts/check_warehouse.py:121 emits SQL calling STRFTIME(), which sqlglot knows as DuckDB's and not as standard SQL's — ADR-0002 names a DuckDB-specific function name outside the adapter as the signal that the seam has stopped holding
  - .claude/scripts/check_warehouse.py:122 emits SQL calling LIST_AGGREGATE(), which sqlglot knows in no dialect, so it cannot transpile it — ADR-0002 names a DuckDB-specific function name outside the adapter as the signal that the seam has stopped holding
exit=1
```

49 statements become 52 — the three probes stop being excused — and both
DuckDB-specific ones are named. Restored and compared the same way, then re-run
clean. This is also the failure mode of a **stale** exemption, which matters: if
`check_warehouse.py` is ever renamed or moved, the run fails loudly rather than
silently widening.

**The documents, because `CLAUDE.md` changed:**

```
$ uv run python .claude/scripts/verify_framework.py
  links      363 links, 189 anchors 23 documents
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
exit=0

$ uv run python .claude/scripts/check_language.py
  proposed terms: 0 · python files scanned: 13 · identifiers: 809
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
exit=0
```

All runs on 2026-08-15, offline, against the Warehouse Step 002 built.

**Deliberately left undone**

**No new Ledger entry, and that is a claim rather than an omission.** Nothing here
does the cheap thing instead of the right thing: the narrowing is the right thing,
and what it leaves behind is a boundary rather than a shortcut.

- **The fixture exemption still costs something inside the file it names.** SQL put
  in a tuple called `DIALECT_PROBES` in `check_warehouse.py` is invisible to the
  dialect scan. That is not debt — it is what a fixture exemption *is*, in the same
  sense the fourteen deliberately invalid rows of `check_constraints` are fixtures
  — and the docstring states it. Removing it entirely would mean the check fails on
  its own test data, which is the one finding that means nothing.
- **No dedicated "this exemption is stale" error.** A `FIXTURE_EXEMPTIONS` entry
  naming a file that does not exist is not reported as such; it surfaces as the
  check naming `check_warehouse.py`'s own probes, demonstrated above. Loud, but
  indirect. Left as is because adding a second check to explain the first one is
  more machinery than one entry justifies — flagged below rather than filed, since
  nothing is wrong, only tersely reported.
- **Nothing in this Sub-step touches the spike.** `check_validation_feasibility.py`
  does not exist yet; 3.2 creates it.

**Look at this sceptically**

- **The sweep confirmed the prediction the plan made about it, which is the least
  interesting possible outcome — so here is what was actually examined.** The plan
  said *"the expectation going in is that nothing else changes"*, and nothing else
  did. Four constructs in the other three scripts were looked at:

  | Where | Construct | Verdict |
  |---|---|---|
  | `check_language.py` | `EXEMPT`, `KNOWN_NON_ABBREVIATIONS` | **Different species.** They name *what* is excused — the token itself — from inside the checker. No scanned document can claim them by choosing a name; it would have to *be* the token |
  | `check_language.py` | `prose_only` drops fenced code blocks | **Different species, and looser.** A document could hide an unexplained abbreviation inside a fence. But the rule is about prose, a fence is code by definition, and what is excused is a position in the document rather than a name a writer picks |
  | `verify_framework.py` | `check_claude_md_references` skips a path containing `NNN` or `*` | **The closest shape found, and left.** A token in the content buys the skip, which is the species R3 is about — but the function reads exactly one file, `CLAUDE.md`, so it is already file-scoped by construction, and a literal path containing `*` cannot exist on disk. Narrowing it would restate what the function already is |
  | `check_data_availability.py` | `EXCLUDED_PROBES` | **Not an exemption at all** — the opposite. It makes the script probe *more*, keeping ruling R1's exclusion evidence live. No check is excused by it |

  The `verify_framework.py` row is the one to disagree with if any: the reasoning
  for leaving it is that the exemption is already scoped to a file, not that it is
  harmless.

- **`check_warehouse.py`'s docstring skip is untouched, and it is a genuine
  exemption.** Any file can put a string in docstring position, and the scan will
  not read it. The argument for leaving it is that the exemption is a *position the
  language defines* rather than a name anyone chooses, and a string in that position
  is documentation rather than SQL a module emits. That argument is good but not
  airtight — a module could assign `SQL = __doc__`. Contrived enough not to build
  machinery for; not so contrived that it is worth calling impossible.

- **`FIXTURE_EXEMPTIONS` is a register holding exactly one entry.** The alternative
  was an inline path comparison inside `sql_statements`, which is fewer lines. The
  register was chosen because R3's rule is general, so the next exemption should
  land somewhere that already exists rather than inventing a home under pressure —
  the *draw contour lines* argument applied to a very small line. Reasonable to
  call it premature.

- **The exemption is keyed on a repository-relative path written as a string**,
  which means the file's own location is now recorded in two places: where it sits
  on disk, and inside itself. The failure is loud rather than silent, shown above.
  A `Path(__file__)` comparison would have been self-maintaining for *this* entry
  and useless for every future one, since the point of the register is to name files
  other than the one doing the checking.

- **The Sub-step that tightens an exemption also widens one, which deserves saying
  out loud.** `EXEMPT` and `HEAD` went into `check_language.py`'s
  `KNOWN_NON_ABBREVIATIONS`. The defence is the same classification the sweep table
  uses: that list names *what* is excused — the token itself — so no document can
  claim it by choosing a name, and both additions are genuinely not abbreviations.
  The alternative was to reword this review to avoid two words that describe
  exactly what the Sub-step did, which is the tail wagging the dog. But a reader
  who thinks the honest move was to leave the check failing and record it has a
  case, and the printed counts do not show the change — the summary line reads
  `15 exempt` before and after, because the additions land in the other list.

- **The `CLAUDE.md` wording is mine.** Amino approved the rule
  ([R3](../plan/step-003-validation-feasibility.md#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15))
  and its placement under Non-Negotiable #4, on the argument that a check with a
  hole in it is the same species of problem as a claim without evidence. The
  sentence added beyond the approved text is the last one — *"narrowing an exemption
  removes the loophole and not the cost"* — which generalises what the
  `DIALECT_PROBES` case taught into the rule itself.

**Language**

No terms added, renamed, or proposed. `FIXTURE_EXEMPTIONS` and the local names
around it carry no domain meaning — they are the checker's own vocabulary, in the
same family as `DIALECT_PROBES` and `CODE_ROOTS`. `Restricted Column`, the one
Term Proposal this Step carries
([R1](../plan/step-003-validation-feasibility.md#r1--term-proposal-restricted-column--approved-by-amino-2026-08-15)),
is registered in Sub-step 3.3, the one that first gives it a code identifier.
`check_language.py` passes with the same 88 registered terms and 0 proposed terms
in code.

## Sub-step 3.2 — Probe whether a generated query traces to a Certified Metric

**What changed**

`.claude/scripts/check_validation_feasibility.py` is new and is the only **code**
file this Sub-step touches; beside it the Sub-step adds one Debt Ledger entry,
[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject),
and the Current State and review updates every Sub-step makes. Nothing else moved: no schema change, no pipeline behaviour, no
`veritas/validation/` directory — a spike that quietly becomes the component is how
its answer stops being falsifiable, and the plan says so under
[Not in this Step](../plan/step-003-validation-feasibility.md#not-in-this-step).

- **A tracer, in three steps.** Parse in the DuckDB dialect; resolve against the
  real schema read through `WarehouseAdapter.columns`; rename each table alias back
  to the table it stands for; keep the projections that aggregate, and canonicalise
  each one. A statement is **allowed** when it computes at least one metric
  expression and every one of them matches a certified expression.
- **Every sqlglot call is explained where it is made.** ADR-0003 calls sqlglot
  *"load-bearing safety infrastructure"*, so the file says in comments what
  `parse_one`, `optimize`, `build_scope`, `traverse` and `find_all` each do, what
  the two flags `canonical` hands the generator change, and why `isolate_tables` is
  turned off — enough that a reader can check the tracer's claims without reading
  the library's source.
- **Sixteen probes**, each declaring what this Sub-step measured about it, so that
  "rejected" is never left to the reader to read as good or bad news: seven
  `certified` (must be allowed), two `form` (must be rejected and are
  arithmetically the metric), five `shadow` (must be rejected), one `blind spot`
  (allowed, and being allowed is the wrong answer), one `refused` (the tracer
  cannot read it at all).
- **Three certified expressions as Python literals**, per
  [R2](../plan/step-003-validation-feasibility.md#r2--the-spikes-certified-expressions-stay-python-literals--approved-by-amino-2026-08-15)
  — `Gross Revenue`, `Net Revenue`, `Traded Notional`, each converted to one
  Reporting Currency through `fct_fx_rate`. The script says in its own words that
  they are probe inputs rather than a corpus, so the Semantic Layer's file format
  stays unfixed.
- **Every executable probe is executed** through the Warehouse Adapter and its
  number printed, and the numbers are checked **against each other** rather than
  against figures written into the script — each probe names another it must equal
  or must differ from, so a `--refresh`, a new seed or a wider window moves every
  figure and breaks nothing.

**What it found.** Six things, and two of them are constraints on the Step that
comes next rather than reassurance.

1. **Claim 1 holds on every shape it names, and on two more.** Aliasing, a derived
   table and a common table expression (CTE) all leave the certified expression
   recognisable. So does a Dimension Definition applied to a metric — `net revenue
   by region`, with two extra joins and a grouping column sitting beside the metric
   in the projection, which is the shape nearly every real question produces and
   which the plan did not ask for.
2. **Two of sqlglot's fourteen optimizer rules are enough**: `qualify` and
   `merge_subqueries`. The other twelve are left out on purpose — ADR-0003 already
   names sqlglot *"load-bearing safety infrastructure"*, and every rule is one more
   rewrite trusted to preserve meaning between the statement a reviewer reads and
   the statement a Gate judges. Which two are needed is printed on every run and
   was measured by removing one, below.
3. **Recognisable means *the same form*, and that is a constraint the Semantic
   Layer has to carry.** `commission - fee - rebate` does not trace where
   `commission - rebate - fee` does, and `fx_rate * commission` does not trace where
   `commission * fx_rate` does. Both return **exactly** the certified number — the
   run prints `== commuted subtraction and net revenue` and `== commuted
   multiplication and bare` — so the rejection is a judgement about form and not
   about arithmetic. A generator that paraphrases a certified expression is refused;
   the Semantic Layer must therefore publish a form the Orchestrator pastes rather
   than a formula it re-derives. This is the finding claim 1 was worth running for.
4. **Claim 3 holds, and the rejection is worth having.** Revenue open-coded inline
   out of `commission`, `rebate` and `fee` as three separate sums is rejected, and
   it stands **32.59% apart** from `Gross Revenue`'s certified expression on the
   currently loaded data — the same figure the
   [Sub-step 2.5 review](step-002-warehouse-and-ingestion.md#sub-step-25--generate-seeded-synthetic-client-activity)
   measured for that pair, arrived at independently here. Two more Shadow Metrics
   are rejected: the conversion left out entirely, and one of Net Revenue's three
   terms silently missing.
5. **The certified expression does not pin down the join, and that is a hole in
   certified-metrics-only.** `Traded Notional` converted out of the Trade's
   Denomination Currency instead of the Instrument's Quotation Currency has an
   identical projection, so it is **allowed** — and returns 7,264,542,867.58 against
   262,266,110.69, **96.39% apart**, a factor of roughly 28. That pair is registered
   in Glossary Section C precisely because both columns sit on `fct_trade`. **A
   Metric Definition must carry its Join Path and the Gate must check the join, not
   only the projection.** Recorded here for Sub-step 3.5 to rule on, because it
   changes what the Semantic Layer has to publish, and carried past this Step by
   [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject),
   whose Trigger is the Sub-step that builds the Gate.
6. **`Traded Notional` cannot be computed as the Glossary defines it.**
   Σ(quantity × Execution Price) × FX Rate overflows: the engine computes the
   product in DECIMAL(18) and a JPY notional does not fit. The certified expression
   therefore carries a widening cast, and `check_widening_cast` runs the uncast
   version on every run and prints the refusal, so the cast is a measurement rather
   than a preference — and so that a run where it stops being needed fails instead
   of leaving a cast whose reason has expired. Sub-step 3.4 inherits the next
   question: whether that cast survives the trip to BigQuery.

**A hole in the tracer, found and closed inside this Sub-step.** The first version
read the outermost scope's projections only. That is right for every shape above and
wrong for a union: a union node projects nothing itself, and asking sqlglot for its
projections hands back its **first branch's**. So the tracer read one branch, read it
with no table sources to resolve aliases against, and never looked at the second
branch at all. A statement whose first branch is certified and whose second is a
Shadow Metric was allowed on the strength of the first. The tracer now walks every
scope and skips the scope of a node that is not a `SELECT`, so each branch of a union
arrives on its own; the `half-certified union` probe is that case, and mutation 2
below puts the first version back and shows what it did with it.

**Verification**

Every check below was run on **2026-08-18**, offline, in the order shown, against
the Warehouse the ingestion command built on 2026-08-15 — `data/veritas.duckdb`, last
modified 2026-08-15 17:53 and not rebuilt since, so the ingestion output below is
that day's and every figure after it is today's reading of the same rows.

```
$ uv run python -m veritas.ingestion
  · fct_instrument_price       9554 rows
  · fct_position_snapshot     61907 rows
  · fct_trade                  1670 rows

PASS — the Warehouse is built · dim_instrument holds 19 Instruments · fct_instrument_price holds 9554 Market Prices across all 19 · fct_fx_rate holds 11840 FX Rates and every Market Price has one
       the client side holds 12 Clients · 24 Accounts · 1670 Trades · every Position is markable and every amount is convertible
exit=0
```

The spike itself, in full:

```
$ uv run python .claude/scripts/check_validation_feasibility.py
  Warehouse: data/veritas.duckdb · 10 tables · 1670 Trades
  Reporting Currency: EUR, stated in 13 conversion predicates and checked against every probe
  certified expressions: 3, as Python literals in this script (R2)
    Gross Revenue      SUM("fct_trade"."commission" * "fct_fx_rate"."fx_rate")
    Net Revenue        SUM(("fct_trade"."commission" - "fct_trade"."rebate" - "fct_trade"."fee") * "fct_fx_rate"."fx_rate")
    Traded Notional    SUM(CAST("fct_trade"."quantity" AS DECIMAL(38, 6)) * "fct_trade"."execution_price" * "fct_fx_rate"."fx_rate")
  tracing rules: qualify · merge_subqueries (sqlglot's own optimize() runs 14)

  claim 1 — does a certified expression survive the shapes a generator writes?
    ALLOWED   bare                                 Gross Revenue
    ALLOWED   aliased                              Gross Revenue
    ALLOWED   derived table                        Gross Revenue
    ALLOWED   common table expression              Gross Revenue
    ALLOWED   net revenue                          Net Revenue
    ALLOWED   net revenue by region                Net Revenue
    ALLOWED   traded notional                      Traded Notional
    REJECTED  commuted subtraction                 1 expression(s), none certified
    REJECTED  commuted multiplication              1 expression(s), none certified
    REJECTED  open-coded net revenue               1 expression(s), none certified
    REJECTED  unconverted commission               1 expression(s), none certified
    REJECTED  rebate silently dropped              1 expression(s), none certified
    ALLOWED   notional through the wrong currency  Traded Notional
    REJECTED  half-certified union                 Gross Revenue, plus 1 uncertified
    REJECTED  unknown table                        1 expression(s), none certified
    REFUSED   unparseable                          ParseError: Expecting ). Line 1, Col: 48.

    7 certified · 2 form · 5 shadow · 1 blind spot · 1 refused

  claim 3 — what each shape actually returns, through the adapter
    without the widening cast, Traded Notional does not compute: OutOfRangeException
      Out of Range Error: Overflow in multiplication of DECIMAL(18) (776000000000 * 1365021). You might want to add an explicit cast to a bigger decimal.
    bare                                             195,260.14 EUR
    aliased                                          195,260.14 EUR
    derived table                                    195,260.14 EUR
    common table expression                          195,260.14 EUR
    net revenue                                      131,618.93 EUR
    net revenue by region                            131,618.93 EUR over 3 rows
    traded notional                              262,266,110.69 EUR
    commuted subtraction                             131,618.93 EUR
    commuted multiplication                          195,260.14 EUR
    open-coded net revenue                           131,618.93 EUR
    unconverted commission                         8,604,323.73 (mixed)
    rebate silently dropped                          166,311.69 EUR
    notional through the wrong currency        7,264,542,867.58 EUR
    half-certified union                           not executed (shadow)
    unknown table                                  not executed (shadow)
    unparseable                                    not executed (refused)

    == aliased and bare
    == derived table and bare
    == common table expression and bare
    net revenue against bare: 131,618.93 against 195,260.14, 32.59% apart
    == net revenue by region and net revenue
    == commuted subtraction and net revenue
    == commuted multiplication and bare
    == open-coded net revenue and net revenue
    open-coded net revenue against bare: 131,618.93 against 195,260.14, 32.59% apart
    unconverted commission against bare: 8,604,323.73 against 195,260.14, 97.73% apart
    rebate silently dropped against net revenue: 166,311.69 against 131,618.93, 20.86% apart
    notional through the wrong currency against traded notional: 7,264,542,867.58 against 262,266,110.69, 96.39% apart

PASS — every probe's verdict and every probe's number is the one this spike recorded
exit=0
```

**The operand pair in that overflow message is an engine detail rather than a
measurement.** DuckDB names the first product it refused, and which product that is
is not something this check pins down: the same command against this same Warehouse
file named `11083000000 * 2616523200` when the tracer was first run on 2026-08-15 and
names `776000000000 * 1365021` today. What `check_widening_cast` asserts is the
refusal — that the uncast expression does not compute — and the run fails if the
engine ever computes it. Read the refusal, not the operands.

**The new file passes the dialect scan without claiming an exemption**, which is
what [R3](../plan/step-003-validation-feasibility.md#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15)
requires of it and the reason Sub-step 3.1 came first. Its sixteen readable
statements — fifteen probes, since the deliberately unparseable one is not SQL, plus
the uncast Traded Notional the widening-cast check runs — are read by the check
Sub-step 2.6 built:

```
$ uv run python .claude/scripts/check_warehouse.py
  seam scan: 14 Python files · 1 import duckdb
    ADAPTER  veritas/warehouse/adapter.py
  dialect scan: sqlglot files 51 function names under DuckDB that standard SQL does not have
    probe: clean
    probe: STRFTIME
    probe: LIST_AGGREGATE
      4 SQL statements in veritas/ingestion/__main__.py
      5 SQL statements in veritas/ingestion/simulator.py
     16 SQL statements in .claude/scripts/check_validation_feasibility.py
     49 SQL statements in .claude/scripts/check_warehouse.py

PASS — the star schema matches Glossary Section B and the adapter seam holds
exit=0
```

The documents and the identifiers:

```
$ uv run python .claude/scripts/verify_framework.py
  links      391 links, 216 anchors 24 documents
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
exit=0

$ uv run python .claude/scripts/check_language.py
  proposed terms: 0 · python files scanned: 14 · identifiers: 893
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
exit=0
```

**The probes were made to have teeth, by two mutations.** A tracer that says yes to
everything passes every `certified` probe, and one that says no to everything passes
every `shadow` probe; only breaking it in a named way shows which probes are load
bearing.

**Mutation 1 — take `merge_subqueries` out of the two tracing rules.** Exactly the
two shapes that rule exists for stop being allowed, and nothing else moves:

```
$ sed -i 's/^TRACING_RULES = (qualify, merge_subqueries)$/TRACING_RULES = (qualify,)/' .claude/scripts/check_validation_feasibility.py
$ uv run python .claude/scripts/check_validation_feasibility.py
  tracing rules: qualify (sqlglot's own optimize() runs 14)
    ALLOWED   bare                                 Gross Revenue
    ALLOWED   aliased                              Gross Revenue
    REJECTED  derived table                        1 expression(s), none certified
    REJECTED  common table expression              1 expression(s), none certified
    ALLOWED   net revenue                          Net Revenue
    ...
FAIL — 4 problem(s)
  - probe 'derived table' has to be allowed and was rejected — it traced to nothing and could not place ['SUM("converted"."commission" * "converted"."fx_rate")']. the conversion done in a subquery and aggregated outside it, so the certified expression is split across a boundary
  - probe 'derived table' has to trace to 'Gross Revenue' and traced to nothing. ...
  - probe 'common table expression' has to be allowed and was rejected — it traced to nothing and could not place ['SUM("converted"."commission" * "converted"."fx_rate")']. the same split, written the way a model that has read a style guide writes it
  - probe 'common table expression' has to trace to 'Gross Revenue' and traced to nothing. ...
exit=1
```

**Mutation 2 — put the tracer back to reading the outermost scope only**, which is
what the first version of this file did. That version is two edits away: the traversal
narrows to the root scope, **and** the guard that skips a scope whose node is not a
`SELECT` goes away — the first version had no such guard, because with only the root
scope to read there was nothing for it to skip. Both edits are in the one command
below, so the mutation is something a reader can paste rather than a description of
one:

```
$ sed -i -e 's/^    for scope in root.traverse():$/    for scope in [root]:/' \
         -e '/^        if not isinstance(scope.expression, exp.Select):$/,+1d' \
         .claude/scripts/check_validation_feasibility.py
$ uv run python .claude/scripts/check_validation_feasibility.py
    ALLOWED   half-certified union                 Gross Revenue
FAIL — 1 problem(s)
  - probe 'half-certified union' must be rejected and was allowed, tracing to ['Gross Revenue'] — a certified branch and a Shadow Metric branch in one statement, the certified one first. It is the probe that found the tracer's own hole: reading the outermost scope alone means reading one branch and allowing the statement on the strength of it. ...
exit=1
```

A statement whose second branch computes revenue with the conversion left out is
**allowed**, on the strength of a first branch the tracer did read. That is the hole
the traversal closes, measured rather than described.

**The first of those two edits on its own does not reproduce the hole**, and the
difference is worth reading rather than glossing. With the traversal narrowed and the
guard left in place, a union's root node is not a `SELECT`, the guard skips it, the
tracer reads no projections at all, and the probe is rejected for having computed
nothing:

```
$ sed -i 's/^    for scope in root.traverse():$/    for scope in [root]:/' .claude/scripts/check_validation_feasibility.py
$ uv run python .claude/scripts/check_validation_feasibility.py
    REJECTED  half-certified union                 nothing certified
PASS — every probe's verdict and every probe's number is the one this spike recorded
exit=0
```

The run passes, and it passes for a reason no probe here is written to measure: a
statement whose projections the tracer never read is rejected because `allowed`
requires at least one metric expression to have been found. That is fail-closed, and
it is not the traversal doing the work — which is why the mutation that shows the
traversal earning its place has to remove the guard as well.

Each of the three mutated runs was restored from a copy taken before it, and every
restoration was checked rather than assumed:

```
$ cp $CLAUDE_JOB_DIR/tmp/pristine.py .claude/scripts/check_validation_feasibility.py
$ cmp $CLAUDE_JOB_DIR/tmp/pristine.py .claude/scripts/check_validation_feasibility.py && echo restored-identical
restored-identical
```

**Deliberately left undone**

**One Ledger entry, and it was opened by a ruling rather than by the code.**
[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)
records the single place this spike is allowed to print `ALLOWED` against a query
that is wrong — the blind spot — and its Trigger is the Sub-step that builds the
Validation Gate. Nothing else here does the cheap thing instead of the right thing:
the boundaries below are the spike's *result*, and a result is not a shortcut. Where
a boundary should change a decision, it is written up above for Sub-step 3.5, which
is the Sub-step that rules.

- **The Gate is not built, and claims 2 and 4 are not answered.** Restricted Columns
  are Sub-step 3.3 and dialect retargeting is Sub-step 3.4. `Restricted Column` is
  still unregistered, correctly: [R1](../plan/step-003-validation-feasibility.md#r1--term-proposal-restricted-column--approved-by-amino-2026-08-15)
  registers it in the Sub-step that first gives it a code identifier.
- **Only projections are examined.** A metric expression that appears solely in a
  filter applied after grouping, or in an ordering clause, is not read. That is
  defensible — the Target State's rule is about what a query *computes* — but it is
  a boundary and not an oversight, and a filter that selects on an uncertified
  aggregate is a real thing a generator can write.
- **The three remaining Validation Gate checks are untouched**: the Access Profile
  predicate, bounded scan, and read-only. An `INSERT` is refused by this tracer, but
  incidentally — sqlglot builds no scope for it — rather than by a read-only rule.
- **The links in this script's own docstrings are checked by nothing, and the gap is
  logged on [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)
  rather than only here.** `verify_framework.py` resolves links and anchors in
  `.claude/docs/**/*.md` and `CLAUDE.md`; this file's links — to ADR-0003, the Step
  003 plan, the Target State and Sub-step 3.3 — sit in Python docstrings, so they
  were checked by hand this Sub-step and by nothing on any later one. They are
  written as real links because a document reference made from inside code has to be
  findable when the final documentation pass swaps internal `.claude/docs/` links for
  user-facing ones ([DEBT-013](../debt-ledger.md#debt-013--the-decisions-that-move-a-number-live-only-in-internal-reviews)),
  and a link nothing resolves rots silently until exactly that moment. DEBT-001 is
  the entry for the rules that rely on discipline: its Trigger is *"the first time any
  framework rule is observed to have been broken in practice"*, which fired in
  Sub-step 1.3, and its own instruction is that *"the next occurrence should buy the
  hooks rather than another document rule"*. So the gap is recorded there as a second
  coverage gap, with the fix named — widen `check_links` by one glob to
  `.claude/scripts/*.py` — and the deadline named: before the final documentation
  pass. It is not fixed in this Sub-step because `verify_framework.py` is not this
  Sub-step's file, and a Sub-step is one commit.
- **The five `certified` probes that trace to `Gross Revenue` or `Net Revenue` all
  convert on Trade Date.** Settlement Date is the other half of a Section C pair and
  no probe uses it, so nothing here measures whether a Metric Definition's choice of
  date column is visible to the Gate. It is the same class of problem as finding 5
  and 3.5 should treat it as one question, not two.

**Look at this sceptically**

- **The blind spot is the finding I am least comfortable presenting as a pass.**
  `notional through the wrong currency` is `ALLOWED` and the run exits zero. That is
  the honest encoding — this Sub-step measured that it traces, and the script fails
  if the measurement changes — but a reader skimming the output sees `ALLOWED`
  against a query that is 96% wrong and has to read the probe's `kind` to learn that
  this is the bad news. The alternative was to make it a failure, which would mean a
  spike that cannot pass until the Gate is built, and the plan is explicit that *"a
  shape that fails is a finding, not a failure"*. **Ruled by Amino on 2026-08-18: the
  encoding stands for the spike, on the condition that the Validation Gate rejects
  this query once the Gate is built.** That condition is now the Trigger on
  [DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject),
  opened by this Sub-step so that the condition outlives the review it was agreed in.
- **The probe set is larger than the plan's, and Amino ruled on 2026-08-18 that this
  is a shortcoming in the planning rather than work outside the plan's scope.** The
  plan names five shapes for claim 1 and one Shadow Metric for claim 3; there are
  sixteen probes. The additions are `net revenue by region` (a Dimension Definition
  applied to a metric), a third certified metric, two more Shadow Metrics, the blind
  spot, the union, the unknown table and the unparseable statement. Each is six lines
  of declaration against one tracer, and the two that matter — the blind spot and the
  union — are findings a six-probe version would have missed. The lesson is where they
  came from: each was found while writing the tracer or its docstring rather than
  while planning it, and every one was nameable in advance from the claim itself.
  **A Step that measures a boundary should enumerate the shapes it will measure at
  planning time**, so the probe set is an agreed input rather than something that
  grows during implementation — otherwise "the probe set grew because probes are
  cheap" is indistinguishable from a spike turning into a component. Sub-step 3.3 is
  already planned that way: its six Restricted Column probes and the expected verdict
  of each are written into the
  [plan](../plan/step-003-validation-feasibility.md#33--probe-whether-a-restricted-column-can-hide-from-the-parse-tree)
  before any code exists.
- **`gap()` is copied from `check_warehouse.py` rather than shared, and so is the
  `EUR` Reporting Currency.** No Ledger entry, on the argument that each check script
  in this repository stands alone and can be read start to finish — that is a
  property worth more than removing a two-line function, and a shared module would be
  the first import between check scripts. Reasonable to call that a rationalisation
  for copy-paste; if it is, the entry belongs on the Ledger and I did not write one.
- **`MIN_GAP` has the same value as `check_warehouse.py`'s `MIN_DISTINCTION_GAP` and
  is deliberately not the same rule** — that one is the floor for a Section C pair
  being separable in the data, this one is the floor for a rejection being worth
  having. They are free to move apart and neither reads the other. Two constants
  with one value and two reasons is a thing that later reads as duplication.
- **A probe's figure is the last column of every row, added up.** That is what lets
  `net revenue by region` be compared with `net revenue` — the slices have to add
  back to the total — and it is a convention rather than anything the shape of a
  result enforces. A probe projecting two numeric columns would silently have one of
  them read.
- **The five probe-kind constants are the checker's own vocabulary**, in the same
  family as `DIALECT_PROBES` and `CODE_ROOTS`. The one to look at is the kind whose
  name is the registered term `Shadow Metric` with the second word dropped: it names
  the *kind of probe* whose subject is a Shadow Metric, not a second name for one —
  but it is one word away from a registered term and worth a ruling if that is too
  close.
- **Turning `isolate_tables` off is a departure from how sqlglot's `optimize()` is
  normally called.** Left on, it wraps every base table in a subquery of its own, and
  `merge_subqueries` is then needed to undo `qualify`'s own rewrite before it can do
  the job it is here for — which made mutation 1 break six probes instead of two and
  told a muddier story. Turned off, each rule does one job. The risk is that a rule
  set assembled this way is not one the library is exercised with.
- **The tracer compares canonical strings.** Two expressions are the same when
  sqlglot generates the same text for them after resolution. That is what produces
  finding 3, and a structural comparison over parse trees would produce the same
  answer for the same reason — the operand order is in the tree, not in the string.
  Anyone reading this as "the Gate is really doing text matching after all" is half
  right and the half that matters is that the text is generated from a resolved tree.

**Language**

No terms added, renamed, or proposed. Every domain noun in the new file is a
registered term used as registered: `Certified Metric`, `Shadow Metric`,
`Reporting Currency`, `Gross Revenue`, `Net Revenue`, `Traded Notional`,
`Dimension Definition`, `Metric Definition`, `Semantic Layer`, `Validation Gate`,
`Quotation Currency`, `Denomination Currency`, `Execution Price`. `check_language.py`
passes with the same 88 registered terms and 0 proposed terms in code, over 14
Python files rather than 13. `Restricted Column` stays unregistered until Sub-step
3.3, which is the Sub-step that gives it an identifier.
