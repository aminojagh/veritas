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
