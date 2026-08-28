# Step 005 — Build the Validation Gate — Step Review

Handoff notes for Amino, one section per Sub-step. See the `closing-a-substep`
skill.

---

## The Current State trim — not a Sub-step

**This section is not a `## Sub-step N.M`** and deliberately breaks the file's
convention, because the commit it describes is not a Sub-step: it builds nothing and
closes nothing.
[R10](../plan/step-005-validation-gate.md#r10--current-state-is-trimmed-in-its-own-commit-between-the-plan-and-51--approved-by-amino-2026-08-25)
is what ordered it and where the reasoning lives — *"trim the current state before
starting 5.1 but after the plan commit"* — and it is the reason this entry exists at
all: R10 says **the trim commit puts one question up and Amino rules on it there**, so
the question needs a durable home rather than a chat message.

**Amino ruled before the commit landed, so the answer ships inside it.** Both rulings
are
[R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26),
dated 2026-08-26: the judgement call in the sceptical list below is approved, and the
rule this trim leaves behind is written into `closing-a-substep`. This entry is written
as the record of a ruled commit rather than a pending one.

**What changed.** The trim itself is one document,
[`current-state.md`](../design/current-state.md), from 1,142 lines to 402. Three more
change because of R11: `.claude/skills/closing-a-substep/SKILL.md` gains the rule at
step 5 and a row in its rationalization table, the
[Step 005 plan](../plan/step-005-validation-gate.md) gains R11 itself, and this review
records both. **No Glossary term and no Ledger entry.** One line of Python moves —
`check_language.py`'s `KNOWN_NON_ABBREVIATIONS` gains `"SKILL"`, beside `"CLAUDE"` and
`"README"`, because naming a skill file by path is the first time any document has
written `SKILL.md` and the check reads a shouted token it cannot look up as an
unexpanded abbreviation. That is the check's vocabulary list, not its rules: no
threshold, no scope and no verdict changes.

Measured 2026-08-26, against the planning commit `aa42205` that precedes this one:

```
$ git show aa42205:.claude/docs/design/current-state.md | wc -c
121855
$ wc -c < .claude/docs/design/current-state.md
47969
```

**Where the 73,886 bytes came from matters for the first judgement call below**, so it
is broken out. Both halves are the same command over the two versions — bytes per `##`
section, with the title and preamble above the first heading under the blank key.
`LC_ALL=C` makes `length()` count bytes rather than characters, so each column sums to
the `wc -c` above it:

```
$ git show aa42205:.claude/docs/design/current-state.md \
  | LC_ALL=C awk '/^## /{s=$0} {b[s]+=length($0)+1} END{for(k in b) print b[k]"\t"k}' \
  | sort -rn
53716   ## Resume here
32350   ## What is built
9967    ## Known gaps
9790    ## Open debt and extensions
5968    ## Repository layout
5491
4573    ## Summary

$ LC_ALL=C awk '/^## /{s=$0} {b[s]+=length($0)+1} END{for(k in b) print b[k]"\t"k}' \
  .claude/docs/design/current-state.md | sort -rn
22876   ## What is built
5968    ## Repository layout
5539    ## Known gaps
3397    ## Summary
2578    ## How we got here
2565    ## Open questions
2533    ## Resume here
1321
1192    ## Open debt and extensions
```

**The narrative block is where the trim happened.** *Resume here* gave up 51,183 bytes
of the 73,886 — 69% of the whole reduction — and *Open debt and extensions* gave up
8,598 by pointing at the two indexes instead of copying them. The component table under
*What is built* gave up 9,474, or **13% of the total**: that is the section the first
sceptical item below is about, and 13% is why the item was worth raising even though
the answer went the way it did. *Repository layout* is byte-identical, because it was
already a description of what exists rather than a story about it — which is the shape
the rest of the file now has.

The file's shape is now: the preamble and a short **Last updated**; **Resume here**,
which is the pointer and nothing else; a new **Open questions** section holding
everything awaiting a ruling; the **Summary**; the component table under **What is
built**; **Repository layout**; **Known gaps**; **Open debt and extensions**; and a new
bounded **How we got here** — one table row per Step, plus the commit-hash list, which
R10 named as kept.

What went: the per-Sub-step narrative that had accumulated since Step 000. Under the
old shape, **Resume here** alone was 664 lines and carried the story of Steps 002, 003
and 004 in the detail each was told in at the time.

**Verification.**

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       795 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr         1037 words
  links      887 links, 658 anchors 46 documents and python files
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly

$ uv run python .claude/scripts/check_language.py
  glossary: 89 registered terms
  Target State components (9)
    agreed        Warehouse
    agreed        Semantic Layer
    agreed        Ingestion
    agreed        Retrieval
    agreed        Orchestrator
    agreed        Validation Gate
    agreed        App
    agreed        Observability
    agreed        Evaluation
  proposed terms: 0 · python files scanned: 17 · identifiers: 1266
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

Those two are the checks that read documents. The other four read the Warehouse or the
corpus, and this commit changes neither.

**Two lines in that output are what this commit moved, and both are worth reading.**
`closing-a-substep` is now 795 words, the longest skill after `writing-an-adr`, which
is the cost side of R11's second ruling — every one of those words loads whenever the
skill does. And `check_language.py` reports **0 unrecognised** abbreviations only
because `"SKILL"` was added; without it the run fails with
`'SKILL' is used in the documents but is neither in the Glossary's Abbreviations table
nor in the exempt list in this script`, which is how the token was found. The link,
anchor and document counts are higher than the figure this entry carried before the
ruling landed, for the ordinary reason: this review file and R11's heading are among
what the run now reads.

**The counts the trimmed file restates were re-derived from source, not copied from the
prose they replaced.** Each is a definition fixed by the code around it, so each stays
in the file rather than moving to a review: `REJECTIONS` holds fourteen entries;
`DIALECT_PROBES` five; `FIXTURE_EXEMPTIONS` one; `PARSE_PROBES` two; `ambiguity_probes`
returns three and `axis_probes` five; the spike holds sixteen general probe statements
plus the nine of `RESTRICTED_COLUMN_PROBES`, which is the 25 the text claims;
`check_warehouse.py` defines nine independent metric figures, one per Certified Metric;
`semantic/` holds 27 entries as 9 + 8 + 5 + 5; the four ADRs all read
`- **Status:** accepted`; and exactly two check scripts import nothing outside the
standard library.

**The one rule this commit had to keep, and how it was checked.** R10: *"It removes
**no fact recorded only there**: anything found in Current State and nowhere else is
either moved into the review it belongs to or kept."*

The sweep for that was a **scratch script, and it cannot reproduce after this commit** —
it reads `git diff` for one file, so once the trim is committed it has nothing to read.
It is described rather than committed for that reason, and no figure from it is quoted
here as evidence. What it did: take every distinctive token in the deleted text —
backticked identifiers, `DEBT-`/`EXT-`/`ADR-` identifiers, constraint identifiers,
dates, decimal figures, commit hashes, CamelCase terms — and ask which of them appear
neither in the trimmed file nor anywhere else under `.claude/`, `veritas/`, or the
repository root.

**It surfaced exactly one candidate, and the fact behind it is recorded elsewhere in
more detail than Current State had it.** The token was `awaiting-amino`, from this
deleted passage about Step 003's four rulings:

> **Their heading anchors carried `awaiting-amino`, so approving them rewrote four
> headings and every link into them** — in this file, the Ledger, the Step Review and
> the document itself.

The [Step 003 review](step-003-validation-feasibility.md) holds the same fact in its
source form rather than its slugified one, which is why a token search missed it:

> the four ruling headings in the new document carry `→ **awaiting Amino**`, which is
> part of the anchor, and three links had been written without it

and, in that Sub-step's account of what approval changed:

> **The four ruling headings say who ruled and when.** `→ **awaiting Amino**` became
> `→ **approved by Amino 2026-08-20**` on R1–R4 […] **Every link into them moved with
> them** — in the Ledger, in this review, in Current State and inside the document
> itself.

So nothing was lost. The token differed; the fact did not.

**One thing the trim found wrong and fixed.** Current State read *"**8 open
extensions**"*. The [Extension Register](../extension-register.md) index reads
**`Open: 9`** — EXT-009 was filed during Sub-step 4.2 and the count here was never
moved. Non-Negotiable #3 makes that Current State's defect rather than the register's,
so the trimmed file says 9. This is the second standing figure in this file to be found
stale by a sweep rather than by a check, after the Glossary term count during Step 003,
and it is the same cause both times: **a number written in prose that no checker reads**.
The trimmed file therefore keeps neither count in prose — it points at the two indexes
that carry them and says so in as many words: *"this file does not keep a second copy."*

**Deliberately left undone.** No debt was taken and none is owed. The commit removes
narrative and adds one rule to a skill; it introduces no shortcut, no stub, and no
hardcoded value. Two things it could have done and did not: enforce the new rule
mechanically, which stays
[DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s,
and widen `verify_framework.py` to read links inside skills — see the sceptical list.

**Look at this sceptically.**

1. **The biggest judgement call: the component table's Notes were trimmed, not just
   kept → approved by Amino 2026-08-26, as
   [R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26).**
   R10 says the trim *"keeps the component table"*. I read that as keeping the
   table and everything it says about what exists **now**, while the per-Sub-step
   chronology inside its cells went the way of the rest of the narrative — cells said
   things like *"This row read 88 until 2026-08-20, when closing Step 003 caught that
   3.3's registration had not been counted here"*, which is a review's sentence sitting
   in a table. Two things push that way besides length: Non-Negotiable #3 says the file
   *"must never describe intent, only reality"*, and a chronology is neither; and the
   writing convention that a measurement is dated evidence rather than a standing
   statement was being broken inside those cells by figures like the term count. **The
   other reading** — the table survives verbatim and only the prose around it is cut —
   would have meant restoring the Notes cells from
   `git show aa42205:.claude/docs/design/current-state.md`, putting the file at about
   57,400 bytes rather than 47,969. It is declined: R11 reads *"keeps the component
   table"* as keeping it as a description, not verbatim. The item stays here rather
   than being deleted, because the alternative it names is what makes the ruling mean
   something.
2. **"How we got here" is one table row per Step, which may be too little.** R10 asked
   for *"a bounded how we got here"* without saying where the bound is. A row per Step
   plus the hash list is the tightest thing that still lets a cold session find the
   right review; a row per Sub-step would be about 25 rows. I chose the smaller one
   because the plan and review links in each row reach the detail in one hop.
3. **The Summary survived almost intact and is the section least like a pointer.** It
   is prose about what the project is, and much of it restates what the component table
   says. I kept it because it is the only place that says what Veritas *is* to someone
   reading cold, but it is the obvious next thing to cut if the file grows again.
4. **The check that would have caught the stale extension count still does not exist.**
   Two indexes now carry counts that Current State points at rather than copies, which
   removes the failure mode here — but nothing mechanically checks that the Ledger's own
   `**Open debt:** 10` line matches its own table. That is
   [DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s
   territory and I did not widen it into this commit.
5. **R11 is filed in the plan, though R10 said Amino would rule *"there"* — in this
   commit.** Both are true of where it ended up: the question was put up here and
   answered here, and the ruling itself is written as an `R` heading in the plan
   alongside R1–R10. I followed Step 004, where
   [R10](../plan/step-004-semantic-layer.md#r10--aminos-rulings-on-the-44-review--decided-2026-08-24)
   and [R11](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)
   are both rulings on a **review** filed in the **plan**, because an `R` number is the
   address everything else links to — Current State's Open-questions table cites `R`
   anchors and nothing else. **If you would rather rulings on a review stayed in the
   review**, this is the commit to say so, because Step 004 set the precedent and this
   one repeats it; the fix is to move the R11 section into this file and repoint the
   eight links into its anchor — three in the plan, three here, two in Current State.
6. **I put a fact about `verify_framework.py`'s scope into Current State that no
   Sub-step measured.** Writing the rule into a skill meant checking whether skill
   bodies are link-checked, and they are not: `verify_framework.py` builds its link
   sources from `.claude/docs/**.md`, `CLAUDE.md`, and the `.py` files, so the two
   markdown links inside `writing-an-adr` are unread. It is stated in the
   `Framework self-check` row beside *"`README.md` is outside the scope"*, which is
   where the file already records that check's boundaries, and the rule I added is
   written in plain paths rather than links because of it. **What I did not do is fix
   it** — widening the scan is a change to what a check *decides*, which is a different
   kind of edit from the one word this commit added to `check_language.py`'s vocabulary
   list. That is a defensible line and also a convenient one; if you want the scan
   widened, it is a small edit and it belongs in its own commit.

**Language.** No term added, renamed, or proposed, and no identifier renamed. The only
code that moves is one string added to `check_language.py`'s
`KNOWN_NON_ABBREVIATIONS` — the filename `SKILL`, which is a token the writing
convention should not ask a reader to expand, for the reason `CLAUDE` and `README` are
already there.

---

### The question R10 said this commit would put up → **ruled, and answered in this commit**

**Should the rule this trim leaves behind be written into the `closing-a-substep`
skill?** The rule: *a Sub-step adds to Current State what is true now, and the story of
how it got there stays in the review.*

**Amino: yes** — *"the rule this trim leaves behind should be written into the
`closing-a-substep` skill"*, 2026-08-26, recorded as
[R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26).

R10's argument for asking was: *"If it is not written down, the file re-accumulates and
the trim is a one-off rather than a fix."* That is what the evidence showed — the file
gained a passage every Sub-step across four Steps and lost none, which is not a lapse by
any one Sub-step but the absence of a rule.

**Where it went.** `closing-a-substep`, step 5, which before this commit read:

> **Make Current State true, and repoint Resume-here.** Update
> `.claude/docs/design/current-state.md` to describe the repository as it now is —
> reality only — and refresh its **Resume here** block so a cold next session knows the
> active Step, the next Sub-step, and anything awaiting Amino.

*"Reality only"* was already there and was already true when every one of those passages
was written, which is the case for making the rule sharper rather than assuming the
existing words cover it. The added paragraph says what happens to the narrative instead:

> **Add what is now true; the story of how it got there goes to step 6.** Current
> State describes the repository, not the Sub-steps that built it. A passage
> narrating what *this* Sub-step did — what it found, what a figure used to read,
> what changed and why — is a defect in this file even when every word of it is
> accurate, because the review already holds it, dated and with its command. The
> normal shape of this step is **editing the sentence that just became wrong**;
> appending a second one beside it is how the file grows. If nothing true
> changed, change nothing.

**And a row in the skill's rationalization table**, because that table is where the
skill answers the excuse rather than states the rule:

> | "This detail matters, so Current State should carry it too" | Current State says what is true; how it became true is the review's. Two copies can disagree, and the shorter one is read more often |

**What the rule does not say.** It does not set a length, a section list, or a budget.
The failure it names is *duplication of a narrative a dated review already holds* —
which is R10's own reasoning, one level down — so a Sub-step that genuinely makes a new
thing true still writes it here, at whatever length it takes. Nothing mechanically
enforces it; that remains
[DEBT-001](../debt-ledger.md#debt-001--framework-rules-rely-on-discipline-not-enforcement)'s
territory, and this commit does not widen it.

**Current State carries the pointer, not a second copy of the rule** — the
`Development framework` row names the skill and step, in one sentence, so a reader who
finds the file short knows what is keeping it short.

---

## Sub-step 5.1 — The Validation Gate refuses anything that is not a bounded read

**What changed.** `veritas/validation/` exists, and with it the fourth of nine
components has a first, thin version. Two modules behind an `__init__.py` that
re-exports: `outcome.py` holds the `Validation Gate outcome` and the `Rejection Reason`
taxonomy, and `gate.py` holds the rules that produce one. Four rules ship — a statement
is readable at all, is one statement, is a `SELECT`, and stays inside a declared scan
ceiling — which is everything that needs neither the Semantic Layer nor a certified
metric. The check is
[R8](../plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)'s
package rather than a fifth monolith: `.claude/scripts/check_validation_gate/`, a
runner, shared probe machinery, and `read_only.py` as the first of five rule modules.

Three things landed alongside it.

- **Two Glossary rows**, exactly the two
  [R3](../plan/step-005-validation-gate.md#r3--validation-gate-outcome-and-rejection-reason-get-glossary-rows--approved-by-amino-2026-08-25)
  approved on 2026-08-25 and no more. `Validation Gate outcome` had been used by three
  agreed rows and defined by none; `Rejection Reason` names the taxonomy
  [ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md) sold determinism on.
  The **members** are enumerated in `veritas/validation/outcome.py`, which is where R3
  put them so this Step does not repeat
  [DEBT-017](../debt-ledger.md#debt-017--the-certified-axes-are-registered-inside-one-glossary-cell)
  with that entry still open.
- **[DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)
  fired and was paid**, two components earlier than its own text predicted, exactly as
  the [plan's trigger table](../plan/step-005-validation-gate.md#which-debt-ledger-triggers-this-step-fires)
  said it would. `WarehouseError` is in `veritas/warehouse/adapter.py`, raised from the
  engine's exception in the three methods that hand the engine caller-supplied text. The
  deferred decision the entry carried — whether every adapter method wraps — was taken
  the narrow way and written into the class docstring.

  **Every `except Exception` waiting on that type now names it**, not only the two lines
  the entry gave as its Location: `check_semantic_layer.py`'s `rows_from` and its
  widening-cast probe, `check_warehouse.py`'s constraint probe, and the spike's
  widening-cast probe. The two outside the Location are the ones where narrowing changes
  a **verdict** rather than a message, because at both of them a caught exception is
  what prints a pass. `check_warehouse.py` prints `refused` for a row the schema turned
  away — under a bare `except Exception`, a probe statement mistyped into something the
  adapter rejects before the engine sees it printed `refused` too, and counted as a
  constraint doing its job. The spike prints that Traded Notional's widening cast is
  load-bearing on the strength of the engine refusing the uncast expression; a wider
  catch let a bug in that file make the same claim. Two `except Exception` clauses are
  left in `.claude/scripts/` and `veritas/`, both deliberate and both commented on the
  line: the ingestion entry point's top-level handler, and the Gate check's proof that a
  Warehouse which will not open raises something that is **not** ours — where catching
  `WarehouseError` would be the failure. The output below shows the grep.
- **`WarehouseAdapter.estimated_scan_rows`**, which is what settles
  [R7](../plan/step-005-validation-gate.md#r7--the-bounded-read-uses-the-engines-estimate-if-the-adapter-can-reach-it--approved-by-amino-2026-08-25).

One thing changed that this Sub-step did not set out to change, and it is a gap this
Sub-step exposed rather than created. `check_language.py` derives the shouted SQL
keywords it must not treat as unexpanded abbreviations, from two bodies: the
hand-authored `.sql` files under `veritas/warehouse/`, and the SQL fields a Semantic
Entry publishes. **There is a third body it never read** — SQL written as a Python string
literal, which is where the ingestion pipeline's statements, `check_warehouse.py`'s
constraint probes and the spike's twenty-five all live. Nothing had noticed, because
every keyword those use also appears in a `.sql` file. `DROP` does not, and the moment a
review quoted the Gate refusing one, the check failed on it.

The fix is a third derivation, `literal_sql_keywords()`, asking sqlglot which literals
are statements exactly as `check_warehouse.py`'s dialect scan does — hand-listing `DROP`
would have contradicted the comment in that same file saying the keywords of the SQL we
write are derived and not remembered. It picks up 37 keywords across `veritas/` and
`.claude/scripts/`, every one a real SQL keyword. **One keyword still had to be listed
by hand and is listed with its reason:** `FORMAT`, because the adapter holds
`EXPLAIN (FORMAT json) ` as a *fragment* concatenated with a caller's statement, and a
fragment parses as nothing.

### R7 is settled: the engine's estimate, not the parse-tree fallback

R7 pre-approved proposal (2) and told 5.1 to *"check if proposal 1 works and if not fall
back to proposal 2"*. **Proposal 1 works and is what shipped.** DuckDB returns its plan
as a JavaScript Object Notation (JSON) document under `EXPLAIN (FORMAT json)`, with a
per-operator `Estimated Cardinality` field — a number in a field, not a number inside a
drawn box diagram, which was the thing that would have made this the text-matching
ADR-0003 rejects. Every DuckDB-specific part of that — the `EXPLAIN` spelling, the plan
format, the field names — is in constants at the top of `adapter.py` and nowhere else,
so ADR-0002's seam holds and `check_warehouse.py`'s scan agrees.

**What the number is: the scan, not the output.** The estimates are summed over the
operators that read a table. That is the quantity the
[Target State](../design/target-state.md#flow) bounds — it says *"scan bounded"* — and
the quantity the
[extension path](../design/target-state.md#extension-path-to-the-full-proposal) swaps
for when it says *"swap DuckDB's estimate for BigQuery dry-run bytes-billed"*, since a
dry run bills bytes scanned.

**Two measured limits, both declared rather than found later.** The check prints both
on every run — `check_the_estimate_does_not_count` — so a later plan format or a
refreshed Warehouse moves the figures rather than making this paragraph quietly wrong.

1. **The estimate counts rows read off a table, and a join makes rows without reading
   them.** A cross product of `fct_trade` with itself reads each side once and returns
   the square: the run below prints **3,340 rows estimated as scanned, against 2,788,900
   returned**. The second figure is larger than `SCAN_CEILING` itself and the statement
   is allowed anyway, which is the limit in one line. It is not a defect in the rule —
   the scan is the quantity the [Target State](../design/target-state.md#flow) bounds
   and the quantity a dry run bills — it is a statement that passes this rule and is
   still too big to answer. Closing it is Sub-step 5.4's certified-route rule, and it
   ships as a probe with a declared `allowed` verdict rather than as a sentence in a
   docstring.
2. **A statement that really reads nothing estimates zero.** DuckDB answers
   `SELECT count(*) FROM fct_trade` out of the table's own metadata, so the plan holds
   no table-scan node at all and the sum over scans is 0 — printed below beside the
   1,670 rows the table actually holds. The answer is exact and the estimate is honest.
   The problem is that **a plan format that had moved would look exactly the same**:
   finding nothing also sums to zero, and zero is under every ceiling, so the rule would
   fail **open** — allowing everything, silently. The positive control below is the only
   thing standing between this rule and that, which is why it is a probe and not a
   comment: 61,907 estimated against 61,907 rows really in `fct_position_snapshot`.

`SCAN_CEILING` is a **policy**, not a measurement: a round number for what Veritas will
spend on one question, so nothing in `gate.py` goes stale when the Warehouse grows. The
headroom the loaded Warehouse leaves is printed on every run instead.

### The ordering is a safety property, and it is now measured

The plan argues the rules are ordered cheapest-first so that a rule needing nothing
*"still returns the right verdict on a day the corpus will not load or the Warehouse
will not open."* Sub-step 5.1 found a second and harder reason, which was not in the
plan:

> `EXPLAIN (FORMAT json) SELECT 1; DROP TABLE t;` **drops the table.**

Prefixing `EXPLAIN` does not neuter a string holding two statements — the engine plans
the first and executes the rest, and hands back the last one's result. So the
single-statement rule running before the bounded-read rule is not a preference about
cost; running them the other way round would be a hole. The check performs it on a
throwaway table in an in-memory Warehouse on every run rather than asserting it, and
**fails the run if the table survives**, because `estimated_scan_rows` and `gate.py`
both cite the measurement and a citation to something that has stopped being true is
worse than no citation.

The other half of the ordering claim is checked by judging every probe a second time
through a Gate whose Warehouse raises `AssertionError` on any attribute access. Eight
probes reach a verdict without touching it.

**Verification.** Needs a filled Warehouse; `uv run python -m veritas.ingestion` was run
first, as every session of this Step must.

```
$ uv run python .claude/scripts/check_validation_gate/
  Warehouse: /home/amino/Projects/veritas/data/veritas.duckdb

  read-only, single, parseable, bounded
    trusted rewrites: qualify, merge_subqueries — sqlglot's optimize() runs fourteen
    rejected  drop a table             not a read
    rejected  write to a table         not a read
    rejected  write to the filesystem  not a read
    rejected  engine introspection     not a read
    rejected  a second database        not a read
    rejected  two statements           not a single statement
    rejected  a union                  not a read
    rejected  not sql at all           unparseable
    rejected  over the ceiling         unbounded scan, ceiling 10
    rejected  engine will not plan it  unbounded scan
    allowed   a cross product          —
    allowed   an ordinary question     —
    8 probe(s) reached the same verdict through a Warehouse that raises on contact
    asking the engine to plan a two-statement string dropped the table — so the single-statement rule runs before it or not at all
    planner estimate 61907 against 61907 rows actually in fct_position_snapshot
    scan ceiling 1000000 against a largest table of 61907 rows — headroom 16x
    a cross product of fct_trade with itself estimates 3340 scanned against 2788900 rows returned — the estimate counts what is read, not what a join makes from it
    SELECT count(*) FROM fct_trade estimates 0 — a real answer off a table of 1670 rows, and the same number an unread plan would give
    the engine refusing a caller's SQL raises WarehouseError, caused by BinderException
    a Warehouse that will not open raises IOException from the constructor, which no rule catches

PASS — the Validation Gate refuses what it cannot read, what is more than one statement, what is not a read, and what the planner expects to scan past the ceiling; and it allows an ordinary question
```

The figures in that block are dated evidence of **2026-08-26**, from the Warehouse the
default `uv run python -m veritas.ingestion` builds: 61,907 rows in
`fct_position_snapshot`, which is the largest of the ten tables, and 1,670 in
`fct_trade`, against a ceiling of 1,000,000. A `--refresh` moves them and the command
above prints the new ones.

The four checks that could have been broken by this diff, run after it — the spike
joins the list because DEBT-016's payment reaches it:

```
$ uv run python .claude/scripts/check_semantic_layer.py
PASS — every published expression executes against the Warehouse, every figure with a second opinion agrees with it, every registered ambiguity resolves to metrics that exist, and every certified axis names buckets the Warehouse holds

$ uv run python .claude/scripts/check_warehouse.py
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_validation_feasibility.py
PASS — every probe's verdict, every probe's number and every detector's reading is the one this spike recorded

$ uv run python .claude/scripts/check_language.py
  proposed terms: 0 · python files scanned: 23 · identifiers: 1397
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

The two `except Exception` clauses DEBT-016's payment deliberately leaves standing, and
the two prose mentions of the construct in the files that no longer use it:

```
$ grep -rn "except Exception" .claude/scripts/ veritas/
.claude/scripts/check_validation_gate/read_only.py:162:            "`except Exception` would have called a broken adapter a bad query",
.claude/scripts/check_validation_gate/read_only.py:410:        except Exception as failure:  # noqa: BLE001 — the point is that it is not ours
.claude/scripts/check_warehouse.py:453:    *prints a pass*: under `except Exception`, a probe statement this file had
veritas/ingestion/__main__.py:281:    except Exception as error:
```

`check_warehouse.py`'s dialect scan reads the new module without an exemption, which is
[R3 of Step 003](../plan/step-003-validation-feasibility.md#r3--an-exemption-names-the-file-as-well-as-the-symbol--approved-and-widened-by-amino-2026-08-15)
holding on a file full of deliberately bad SQL:

```
     10 SQL statements in .claude/scripts/check_validation_gate/read_only.py
```

**Mutations — the pattern Sub-step 2.6 established.** Two rules were deleted from the
Gate's rule list, one at a time, and the file restored with `cmp` each time.

```
=== MUTATION 1 — delete the parse-failure rule from the rule list ===
    rejected  not sql at all           not a single statement
FAIL — 1 problem(s)
  - 'not sql at all' was rejected for ['not a single statement'] where it was measured as ['unparseable'] — a rejection for the wrong reason is a mislabelled bar on the chart ADR-0003 sold determinism on

=== MUTATION 2 — delete the read-only rule from the rule list ===
    allowed   drop a table             —
    rejected  write to a table         unbounded scan
    allowed   write to the filesystem  —
FAIL — 6 problem(s)
  - 'drop a table' was measured as rejected and came back allowed — Data Definition Language (DDL) — the shape everyone thinks of first, and the one a Gate that only looked for INSERT would pass
  - 'write to a table' was rejected for ['unbounded scan'] where it was measured as ['not a read'] — a rejection for the wrong reason is a mislabelled bar on the chart ADR-0003 sold determinism on
  - 'write to the filesystem' was measured as rejected and came back allowed — the shape worth naming — it reads nothing it should not and writes the answer somewhere no reader of a Grounded Answer will ever see it, so read-only has to mean the filesystem as well as the Warehouse

=== restored ===
cmp: identical
PASS — the Validation Gate refuses what it cannot read, what is more than one statement, what is not a read, and what the planner expects to scan past the ceiling; and it allows an ordinary question
```

**Mutation 1 came out differently from what the plan expected, and the difference is the
finding.** The plan predicted *"see the unparseable probe reported as allowed"*. It is
not reported as allowed — it is reported as **rejected for the wrong reason**, because
a string sqlglot cannot parse yields no statements and the next rule down refuses it for
holding zero of them. That is
[C6](../design/validation-feasibility.md#c6--fail-closed-on-parse-failure-by-a-rule-rather-than-by-accident)'s
scenario reproduced exactly rather than a weaker one: the Gate goes on fail-closing, and
it fail-closes *"incidentally"*, and the only thing that notices is a check comparing the
Rejection Reason against the one that was measured. A Gate whose taxonomy is unchecked
would have passed this mutation silently while charting rejections under the wrong bar.

**Deliberately left undone.**

- **The other four Gate rules.** 5.2 to 5.5, as planned. In particular
  [C3](../design/validation-feasibility.md#c3--the-two-parse-tree-rules-ship-together)
  is satisfied at the **Step** and not here —
  [R4](../plan/step-005-validation-gate.md#r4--c3-is-satisfied-at-the-step-not-the-sub-step--approved-by-amino-2026-08-25).
  Nothing executes a statement through this Gate, so there is no path a Restricted
  Column can travel between now and 5.3.
- **`SELECT * FROM read_csv_auto('x.csv')` is allowed by these four rules.** It is a
  `SELECT`, it is one statement, and it reads a file rather than the Warehouse. The
  read-only rule is about not **writing**, and closing this is 5.2's tracer — a statement
  that computes no certified metric expression is rejected for computing none — with
  5.4's route rule behind it. Named here rather than left to be found; it is not a probe
  because a probe declaring it `allowed` would have to be flipped in 5.2 anyway, and a
  probe whose verdict is scheduled to change is a probe that documents a bug.
- **No new Ledger entry.** Nothing here is the cheap version of something. The
  fail-closed refusal of `UNION`, the single Reporting Currency, the four-of-five rules —
  each is right for this scope and none has a trigger that fires inside this project's
  life.
- **The earlier reviews were not re-run, and one line in each no longer reproduces.**
  Paying DEBT-016 everywhere moves one thing in the output of every check it touches:
  the printed exception name is `WarehouseError` where it was DuckDB's own class. The
  [Step 003](step-003-validation-feasibility.md) and
  [Step 004](step-004-semantic-layer.md) reviews quote lines reading `OutOfRangeException`
  that a run today prints differently. They are left exactly as they are, because a
  review is what a command printed on its date and editing that to match today would
  make it something else. Nothing about the finding changes: the engine's own class is
  now the `__cause__`, and the Gate check fails the run if it ever is not. The spike's
  certified expressions are untouched, so
  [R4 of Step 004](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)
  still holds — it pins the inputs of a dated measurement, not the code that decides
  whether the measurement was taken.

**Look at this sceptically.**

1. **`veritas/validation/` is two modules where the plan said one.** The plan reads
   *"an `__init__.py` that re-exports, and the module behind it."* What the split buys
   is one import line. A Grounded Answer, the App and Observability all have to read a
   verdict and none of them runs a rule, and `outcome.py` imports `dataclasses` and
   `enum` where `gate.py` imports sqlglot, two optimizer rules and the Warehouse
   Adapter — so the contract can be had without any of that. R3's words for it are that
   the outcome *"is a data contract before it is a return value"*. If that reads as
   inventing a seam the plan did not ask for, merging the two files is one move: the
   `__init__.py` already re-exports both names, so no import outside the package would
   have to change.
2. **`SCAN_CEILING = 1_000_000` is a number I chose.** It is stated as policy rather than
   derived, and on today's Warehouse it leaves 16× headroom over the largest table — so
   it cannot fire on any real question here, and the probe that gives the rule teeth
   lowers the ceiling to 10 rather than building a query big enough to trip the real one.
   The alternative reading is that a ceiling which cannot fire is not a rule. My answer
   is that the comparison is what is being checked and the comparison is exercised every
   run; a ceiling tuned to fire on this Warehouse would be a measurement in code, which
   is the thing the writing conventions forbid. It is a constructor argument, so a caller
   that wants a tighter one has it.
3. **A `UNION` of two `SELECT`s is refused.** The plan says *"anything that is not a
   single `SELECT`"* and this is that reading taken literally. Nothing in `semantic/`
   needs a UNION today. If Amino reads a union as a read, the change is one `isinstance`
   and flipping one probe's verdict.
4. **`one_statement` reads a failed parse as zero statements rather than asserting.**
   That is what makes mutation 1 legible instead of a traceback — but it is also code
   written with an eye on its own mutation test, and a reviewer is entitled to call that
   backwards. The state cannot arise while `parses` runs first.
5. **The Gate stops at the first rule that rejects, so `reasons` is a tuple that holds
   one member today.** It is plural because 5.3 will name every Restricted Column it
   found rather than the first. A reviewer who wants every rule's verdict on every
   statement would get a longer chart and a Gate that asks the engine to plan a statement
   it has already refused — which, given what mutation 2 and the `EXPLAIN` measurement
   show, is not a small change.
6. **The independence proof uses a stand-in that is not a `WarehouseAdapter`.**
   `WarehouseThatWillNotOpen` implements none of the adapter and raises on any attribute
   access; the Gate is built with it behind a `# type: ignore`. It proves the rules touch
   nothing, which is the claim. It does not prove they would work against a *degraded*
   Warehouse, and nothing here claims that.
7. **`check_language.py` gained a third keyword derivation in a Sub-step about the
   Validation Gate.** It is around fifty lines in a script this Sub-step's subject does
   not touch, and the cheap alternative — two words in a hand-maintained list — is three
   lines. I took the wider one because that list's own comment says the keywords of the
   SQL we write are derived rather than remembered, and `DROP` is now one of them. A
   reviewer who reads it as scope creep would be reading it fairly; the fix is a revert
   plus two list entries.
8. **`TRUSTED_REWRITES` is imported and not yet applied.** C5 asks for the constant named
   in one place, printed, and reported on the outcome, and 5.1 does all three while no
   5.1 rule runs a rewrite — a shape survives no rewriting. Declaring it now is drawing
   the contour line 5.2's tracer hangs off; a reviewer could reasonably want it to arrive
   with its first user instead.

**Language.** Two terms added, both `agreed` 2026-08-25 under R3 and written into
[Glossary Section A](../glossary.md#a-the-system) with a dated note at the end of it:
`Validation Gate outcome` and `Rejection Reason`. Nothing renamed, nothing proposed.
The identifiers that carry them are `ValidationGateOutcome` and `RejectionReason`; the
Rejection Reason **members** — `UNPARSEABLE`, `NOT_A_SINGLE_STATEMENT`, `NOT_A_READ`,
`UNBOUNDED_SCAN` — are code vocabulary registered in `veritas/validation/outcome.py`
by R3's decision, not Glossary terms. `WarehouseError`, `estimated_scan_rows`,
`SCAN_CEILING` and `Reading` are technical names on the precedent the adapter's
`row_count`, `tables` and `columns` set: they carry no domain meaning and register none.

### The eight sceptical items → **ruled, and answered in this commit**

**Amino: *"all approved."*** 2026-08-26, recorded as
[R12](../plan/step-005-validation-gate.md#r12--aminos-rulings-on-the-51-review--decided-2026-08-26).
Nothing above is rebuilt, and the ruling lands in this commit rather than after it
because it arrived before the commit did — the shape
[R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26)
set on the trim.

**What it settles.** Four of the eight offered a concrete reversal — merge the two
modules (1), read a `UNION` as a read (3), revert `check_language.py`'s third
derivation (7), let `TRUSTED_REWRITES` arrive with its first user (8) — and each
reversal is declined, so the seams 5.2 hangs off are settled rather than provisional.
The other four are declared limits rather than offers, and approval records them as
known: the ceiling that cannot fire on this Warehouse, the failed parse read as zero
statements, the one-member `reasons` tuple, and the stand-in that is not a
`WarehouseAdapter`. R12 carries the reasoning for each.

**What it does not settle.** None of the eight was a defect, so nothing here is a fix
deferred; and approval is not a measurement — the probe verdicts, the two limits printed
by `check_the_estimate_does_not_count`, and the `EXPLAIN` finding go on being true
because the check re-establishes them on every run, not because they were approved.

**Verification.** This section changes three documents and no code, so the two checks
that read documents are the ones that can break — the other four were re-run unchanged
and are the output already pasted above.

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       795 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr         1037 words
  links      956 links, 718 anchors 52 documents and python files
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly

$ uv run python .claude/scripts/check_language.py
  glossary: 91 registered terms
  proposed terms: 0 · python files scanned: 23 · identifiers: 1397
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

Both counts are higher than the ones the trim entry above carries, for the ordinary
reason: R12, this section and the whole 5.1 entry are among what the run now reads.

---

## Sub-step 5.2 — The Gate traces every metric expression to a Certified Metric

**What changed.** The Validation Gate's fifth rule, and the first that reads the
Semantic Layer. A statement is now allowed only when it computes at least one metric
expression and **every** one of them traces to a Certified Metric loaded from
`semantic/metrics/`. `gate.py` gains the tracer that decides it — `resolve`,
`projected_expressions`, `metric_expressions`, `certified_form`, `certified_forms` and
`certified_metrics_only` — and `ValidationGate` gains a `semantic` field holding the
corpus it traces against. `outcome.py` gains three `Rejection Reason` members, because
the rule fails in three distinguishable ways.

Three things landed with it.

- **[R2](../plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
  is discharged for the tracer.** `check_validation_feasibility.py` holds no copy of
  `resolve`, `canonical`, `certified_forms`, `certified_metrics_only`,
  `metric_expressions`, `TracerRefused` or the two-rule constant; it imports each from
  `veritas/validation/`. Its own corpus stays three pinned literals under
  [R4 of Step 004](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21),
  so one tracer now answers for two corpora. **All 25 of its declared verdicts are
  unchanged by the move**, which is the evidence that it was a move and not a rewrite.
  The projection walker and the restricted-column detector are still the spike's and
  go in with 5.3.
- **`WarehouseAdapter.columns_by_table`**, which is C4's *"the Gate's interface takes
  the schema"* made concrete. It is the spike's `warehouse_schema` moved in under R2's
  wider rule, and it reads the whole catalogue in one query rather than one per table.
- **`.claude/scripts/check_validation_gate/traces.py`**, the second of
  [R8](../plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)'s
  five modules.

### The finding the plan asked for: `Position Change` traces, and only just

The [plan](../plan/step-005-validation-gate.md#52--the-gate-traces-every-metric-expression-to-a-certified-metric)
named `Position Change` as *"the shape nobody has measured"* — the
[4.2 review](../reviews/step-004-semantic-layer.md#sub-step-42--write-the-remaining-metric-definitions)
called it *"the one expression shape the spike never measured — a correlated scalar
subquery with an `ORDER BY` and a `LIMIT` inside an aggregate"* — and said that if it
did not trace, the Sub-step must report it rather than route around it, with three
options: a third trusted rewrite, a rewritten expression, or debt.

**It did not trace, and none of the three was needed.** The cause is one alias:

```
statement  SUM("fct_position_snapshot"."quantity" - COALESCE((SELECT "previous_snapshot"."quantity" AS "quantity" FROM …
corpus     SUM("fct_position_snapshot"."quantity" - COALESCE((SELECT "previous_snapshot"."quantity"                FROM …
```

`qualify` gives the projection of a nested `SELECT` an output alias. The statement goes
through `qualify`; the corpus, canonicalised by parsing the expression on its own, does
not. For flat arithmetic the two agree, which is why nine Sub-steps of measurement
never saw it — every expression the spike traced is flat.

**The fix is a fourth option the plan did not list: put the corpus through the same
reader as the statement.** `certified_form` wraps a certified expression in
`SELECT <expression> FROM <the Warehouse tables it names>` and runs it through the same
`resolve`, so both sides of the comparison are rewritten by the same two rules. That
widens nothing —
[C5](../design/validation-feasibility.md#c5--the-rewrites-the-gate-trusts-are-named-in-code-and-there-are-two)'s
two rewrites on both sides rather than a third on one — and it needs no corpus edit, so
Step 004 is not reopened. It is also the property claim 4 already relies on: *"query and
corpus go through one rewrite"*.

The scope is built from the tables the **expression** names, not from the Metric
Definition's `from_table` and `join_paths`. Both were measured and produce identical
forms for all nine metrics; the expression's own tables were chosen because a canonical
form is a property of the expression, and reading the declared route would make the
corpus move when 5.4 edits a route. It also keeps `certified_forms` callable with a
bare expression, which is what lets the spike keep its three pins.

**This is checked, not asserted.** `check_symmetric_canonicalisation_is_load_bearing`
builds the corpus the rejected way on every run and prints which metrics it loses —
today, one of nine, `Position Change`. It **fails the run if it loses none**, because at
that point the explanation in `certified_form` has stopped being true and a reason
nothing checks is how a comment quietly goes wrong. That is 5.1's rule about citations
applied to this Sub-step's own.

### Three reasons for one rule, and why they are not one bar

| Reason | What it means | The probe |
|---|---|---|
| `unresolvable` | parses, will not resolve against the live catalogue | a DuckDB list comprehension — the engine plans it, sqlglot's optimizer will not resolve the name it binds |
| `shadow metric` | an expression the corpus does not hold | five Shadow Metrics, two commuted forms, and one certified expression sitting beside a Shadow Metric |
| `no metric expression` | the statement aggregates nothing | a projection of two columns, and the cross product |

The spike is where the first distinction was found rather than invented: its
`unknown table` probe exists because *"sqlglot resolves it without objecting, so the
rejection has to come from the expression not matching rather than from resolution
failing — two mechanisms a Gate must not confuse."* `unresolvable` is that second
mechanism given a name and a bar of its own.

**A rule may register more than one member.** 5.1's four rules and four members made
them look paired; `outcome.py` now says they are not. Three bars rather than one because
a reader acts on them differently: a Shadow Metric is a Grounding problem, a statement
that aggregates nothing is a generator problem, and an unresolvable statement is neither.

### Two verdicts Sub-step 5.1 declared have flipped

Both are the Gate getting stricter, and both are worth reading carefully.

- **`an ordinary question`** — `SELECT count(*) FROM fct_trade WHERE …` — is now a
  Shadow Metric. `Trade Count` is certified as `count(fct_trade.trade_id)`, so `count(*)`
  is a paraphrase, and
  [C1](../design/validation-feasibility.md#c1--a-metric-definition-publishes-a-form-the-orchestrator-pastes)
  chose a pasteable form over a Gate that decides which paraphrases are safe. This is
  the constraint working, and it is also the sharpest thing in this Sub-step to
  disagree with — see below.
- **`a cross product`** is now rejected as `no metric expression`. It does **not** close
  the bounded read's blind spot: that statement selects columns, so it computes no
  metric, and a cross product computing a certified one would still be allowed. 5.4
  still owns it, and `check_the_estimate_does_not_count` still prints the two numbers.

**The positive control they used to be has been rewritten as the property it always
meant.** A rule module needs a statement its own rules *allow*, and "allowed by the
whole Gate" stops meaning that the moment a later rule exists — which will happen again
in 5.3, 5.4 and 5.5. `check_these_rules_allow_them` therefore asks whether **all four of
this module's rules ran without rejecting**, read off `ValidationGateOutcome.rules` —
the field 5.1 added for the reader who *"wants to know what a verdict covers rather than
assuming"*. It needs no edit when the next rule lands.

### A defect this Sub-step found in the adapter

Reading the catalogue one query per table cost **53 ms against 4 ms** for the same
mapping on the run below — an N+1 against `information_schema`, on a path the Gate now
takes on every judgement. `columns_by_table` does it in one query, and the check prints
both figures and fails the run if the two disagree, so a later tidy-up cannot quietly
restore the slow shape or a different mapping.

### Verification

Needs a filled Warehouse; `uv run python -m veritas.ingestion` was run first, as every
session of this Step must.

```
$ uv run python .claude/scripts/check_validation_gate/
  Warehouse: /home/amino/Projects/veritas/data/veritas.duckdb

  read-only, single, parseable, bounded
    trusted rewrites: qualify, merge_subqueries — sqlglot's optimize() runs fourteen
    rejected  drop a table             not a read
    rejected  write to a table         not a read
    rejected  write to the filesystem  not a read
    rejected  engine introspection     not a read
    rejected  a second database        not a read
    rejected  two statements           not a single statement
    rejected  a union                  not a read
    rejected  not sql at all           unparseable
    rejected  over the ceiling         unbounded scan, ceiling 10
    rejected  engine will not plan it  unbounded scan
    rejected  a cross product          no metric expression
    rejected  an ordinary question     shadow metric
    all 4 rules here ran on `SELECT * FROM fct_trade AS left_side, fct_tr…` and none rejected it — refused later by traces
    all 4 rules here ran on `SELECT count(*) FROM fct_trade WHERE fct_tra…` and none rejected it — refused later by traces
    8 probe(s) reached the same verdict through a Warehouse that raises on contact
    asking the engine to plan a two-statement string dropped the table — so the single-statement rule runs before it or not at all
    planner estimate 61907 against 61907 rows actually in fct_position_snapshot
    scan ceiling 1000000 against a largest table of 61907 rows — headroom 16x
    a cross product of fct_trade with itself estimates 3340 scanned against 2788900 rows returned — the estimate counts what is read, not what a join makes from it
    SELECT count(*) FROM fct_trade estimates 0 — a real answer off a table of 1670 rows, and the same number an unread plan would give
    the engine refusing a caller's SQL raises WarehouseError, caused by BinderException
    a Warehouse that will not open raises IOException from the constructor, which no rule catches

  every metric expression traces to a Certified Metric
    corpus: 9 Certified Metrics, read from semantic/metrics/ through veritas.semantic.loader — not Python literals (R2)
    corpus canonicalised through the Gate's own reader: 1 of 9 Certified Metrics would not trace if it were parsed alone — Position Change
    allowed   bare                     —
    allowed   aliased                  —
    allowed   derived table            —
    allowed   common table expression  —
    allowed   net revenue              —
    allowed   net revenue by region    —
    allowed   traded notional          —
    rejected  commuted subtraction     shadow metric
    rejected  commuted multiplication  shadow metric
    rejected  open-coded net revenue   shadow metric
    rejected  unconverted commission   shadow metric
    rejected  rebate silently dropped  shadow metric
    allowed   notional, wrong currency —
    rejected  certified beside shadow  shadow metric
    rejected  half-certified union     not a read
    rejected  unknown table            unbounded scan
    rejected  no metric expression     no metric expression
    rejected  unresolvable             unresolvable

    one probe per Certified Metric, built from semantic/metrics/:
    allowed   Account Value            —
    allowed   Cash Balance             —
    allowed   Gross Revenue            —
    allowed   Net Revenue              —
    allowed   Position Change          —
    allowed   Realised P&L             —
    allowed   Trade Count              —
    allowed   Traded Notional          —
    allowed   Unrealised P&L           —

    one judgement, fastest of 15: schema 5 ms · corpus 23 ms · statement 2 ms · whole Gate 37 ms
    the catalogue in one query against one query per table: 4 ms against 53 ms, same mapping: True

PASS — the Validation Gate refuses what it cannot read, what is more than one statement, what is not a read, what the planner expects to scan past the ceiling, and what computes a metric the Semantic Layer does not certify; and it allows every Certified Metric
```

The other five checks, run in the same session and each exiting zero:

```
$ uv run python .claude/scripts/check_validation_feasibility.py
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
…
    25 of 25 statements keep both parse-tree verdicts through the round trip
PASS — every probe's verdict, every probe's number and every detector's reading is the one this spike recorded

$ uv run python .claude/scripts/check_semantic_layer.py
PASS — every published expression executes against the Warehouse, every figure with a second opinion agrees with it, every registered ambiguity resolves to metrics that exist, and every certified axis names buckets the Warehouse holds

$ uv run python .claude/scripts/check_warehouse.py
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_language.py
PASS — documents agree with the Glossary and the writing conventions

$ uv run python .claude/scripts/verify_framework.py
PASS — framework is wired up correctly
```

### Mutation testing

The pattern Sub-step 2.6 established and 5.1 followed: break one thing, re-run, see the
check fail on the probes that name it, restore, compare with `cmp`. Four mutations, one
per claim this Sub-step makes.

```
$ # for each: apply the mutation, run the check, restore, cmp
mutation testing — delete the rule, re-run, restore, cmp
  the tracing rule is dropped from rules()             FAIL — 10 problem(s)
      'a cross product' was measured as rejected and came back allowed
      'an ordinary question' was measured as rejected and came back allowed
      'commuted subtraction' was measured as rejected and came back allowed
      'commuted multiplication' was measured as rejected and came back allowed
      'open-coded net revenue' was measured as rejected and came back allowed
      'unconverted commission' was measured as rejected and came back allowed
      'rebate silently dropped' was measured as rejected and came back allowed
      'certified beside shadow' was measured as rejected and came back allowed
      'no metric expression' was measured as rejected and came back allowed
      'unresolvable' was measured as rejected and came back allowed
  'every ... traces' becomes 'some'                    FAIL — 7 problem(s)
      'an ordinary question' was measured as rejected and came back allowed
      'commuted subtraction' was measured as rejected and came back allowed
      'commuted multiplication' was measured as rejected and came back allowed
      'open-coded net revenue' was measured as rejected and came back allowed
      'unconverted commission' was measured as rejected and came back allowed
      'rebate silently dropped' was measured as rejected and came back allowed
      'certified beside shadow' was measured as rejected and came back allowed
  the corpus is parsed alone, not resolved             FAIL — 2 problem(s)
      'Position Change' was measured as allowed and came back rejected
  a statement that will not resolve is allowed         FAIL — 1 problem(s)
      'unresolvable' was measured as rejected and came back allowed

gate.py restored byte-for-byte after every mutation
PASS — the Validation Gate refuses what it cannot read, …
```

The second mutation is the one the `certified beside shadow` probe was added for: it is
the only probe in the file that separates *every* from *some*, because the spike's
demonstration of that hole — the half-certified union — is now refused a rule earlier
for being a `UNION`. The third reports two problems; the second is
`check_symmetric_canonicalisation_is_load_bearing` finding that nothing depends on the
symmetry any more, which is the same defect said the other way round.

### Deliberately left undone

- **[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject)
  stands open and now has a second home.** The Gate traces
  `notional through the wrong currency` to `Traded Notional` and allows it, exactly as
  the spike's tracer does, so `traces.py` carries a probe of that name declaring
  `allowed`. Nothing is paid; the entry gained a dated status note saying 5.4 now has
  two declared verdicts to flip rather than one. Both fail loudly if only one is
  flipped.
- **`resolve` will be called more than once per judgement from 5.3.** The tracing rule
  resolves the statement itself; the Restricted Column and route rules will each need a
  resolved tree too, and the rule signature 5.1 fixed — `Callable[[Reading], …]` — has
  nowhere to thread one between rules. Resolving is 2 ms on the run above and
  deterministic, so this is a cost rather than a bug, and it is **not** on the Ledger:
  paying it means changing the rule signature, which is a seam R12 has just settled.
  Flagged below.
- **No new debt was taken by the code.** The one shortcut worth naming — rebuilding the
  corpus on every judgement instead of caching it — is not debt, because caching it is
  what would be wrong: both sides of the comparison have to come from one reading of the
  catalogue. **One entry was opened by the ruling**, on sceptical item 5 rather than on
  anything in the diff:
  [DEBT-018](../debt-ledger.md#debt-018--six-certified-metrics-have-no-expression-text-pinned-outside-the-corpus),
  the nine per-metric probes built from the corpus they check.

### Look at this sceptically

1. **`count(*)` is now a Shadow Metric.** This is C1's design and it is also the most
   user-visible strictness in the project so far: `Trade Count` is
   `count(fct_trade.trade_id)`, and a generator that writes the obvious thing is
   refused. Grounding is meant to paste the certified form, so the pressure lands
   there — but if it turns out that a model reliably writes `count(*)`, the answer is a
   ruling (widen the corpus, or normalise) rather than a patch. Nothing about that is
   decidable before Grounding exists, which is why nothing was done about it here.
2. **Three new Rejection Reason members in one Sub-step, against 5.1's four in one.**
   Each has a probe and each is reachable, and I have argued they are three different
   things to go and fix. The cheaper reading is that `unresolvable` and
   `no metric expression` are both "the Gate could not find a metric here" and should
   be one bar. I do not think so, but the taxonomy is a data contract Observability
   will chart, so it is worth disagreeing with now rather than after there is a chart.
3. **The plan said 5.2 needs the corpus and 5.3 needs the live schema; 5.2 needs
   both.** `qualify` cannot attach a column to its table without a catalogue, so the
   schema arrives one Sub-step earlier than
   [the plan's dependency sentence](../plan/step-005-validation-gate.md#what-the-gate-must-decide)
   predicted. Nothing about the rule order changes — the tracing rule still runs after
   every rule that needs less — and C4 already said the Gate's interface takes the
   schema. But the plan's sentence is now wrong and I have not edited the plan.
   **Ruled 2026-08-27 — edit the plan.** Done: the sentence now says 5.2 needs both, and
   carries the correction with its date rather than being quietly rewritten. See
   [R13](../plan/step-005-validation-gate.md#r13--aminos-rulings-on-the-52-review--decided-2026-08-27).
4. **`certified_form` raises `ValueError` on a corpus defect.** An expression naming no
   Warehouse table, or yielding more than one metric expression, is a broken corpus and
   gets a traceback rather than a rejection — the same call 5.1 made for a Warehouse
   that will not open. It means a bad Metric Definition takes the Gate down rather than
   failing one query. `check_semantic_layer.py` would catch most such defects first,
   but not all of them, and nothing checks that claim.
5. **The nine per-metric probes are built from the corpus, so they cannot catch a
   corpus that is wrong in the same way twice.** They prove the Gate recognises what
   `semantic/metrics/` says, not that `semantic/metrics/` says the right thing —
   `check_semantic_layer.py` is what asks the second question. The spike's three pinned
   literals are the only independent check that the corpus has not drifted, and they
   cover three of nine.
   **Ruled 2026-08-27 — open a debt triggered on a semantic definition drifting.**
   [DEBT-018](../debt-ledger.md#debt-018--six-certified-metrics-have-no-expression-text-pinned-outside-the-corpus).
   **Writing it corrected the last sentence above**, which is wrong as written: the three
   pinned literals are not the only independent check. `check_semantic_layer.py`'s check 4
   compares **all nine** metrics' numbers — twice each — against `check_warehouse.py`'s
   own SQL, which reads nothing from `semantic/`, so every edit that moves a number
   already fails a run. What the pins alone cover is the **text**, and the real gap is the
   intersection: an edit to one of the six unpinned metrics that changes an expression's
   text without changing its number. That is what the entry records and what its
   repayment — check 9 widened from three metrics to nine — closes.
6. **The two flipped 5.1 verdicts are a judgement call.** I rewrote that module's
   positive control rather than changing its probe statements to certified ones. The
   alternative — make `an ordinary question` compute `Trade Count` properly — is
   smaller today and breaks again in 5.4 when a date predicate becomes required.
7. **`Shadow Metric` is now a code identifier and its Glossary row still says its home
   is *"— (an anti-pattern)"*.** The definition is accurate and I did not amend an
   `agreed` row without a ruling, but a reader checking the Glossary before naming
   something will not learn from that cell that the Gate returns it as a
   `Rejection Reason`. Amend, or leave?
   **Ruled 2026-08-27 — amend.** The *Lives in* cell now reads
   *"`veritas/validation/` — as a Rejection Reason (no file publishes one)"*, and the
   definition cell carries the amendment, its date and a pointer to
   [R13](../plan/step-005-validation-gate.md#r13--aminos-rulings-on-the-52-review--decided-2026-08-27).
8. **The timing figures are dated evidence and will move.** They come from
   `check_what_a_judgement_reads`, which prints them on every run and asserts nothing
   about them; only the *equality* of the two catalogue readings is checked. A machine
   twice as slow changes every number in this section and breaks nothing.

### Language

**No new terms, and one used for the first time as a code identifier.**
`RejectionReason.SHADOW_METRIC` takes its name from the `Shadow Metric` row, agreed and
spelled exactly as registered — *"a metric computed inline in a query instead of drawn
from the Semantic Layer. The failure mode Veritas exists to prevent."* No Term Proposal
is raised for it, because the term was already registered; item 7 above is the open
question about its row.

🆕 **Possible TERM PROPOSAL, raised and not taken** — **`metric expression`**: the SQL
expression inside a query that computes a metric, as distinct from the
`Metric Definition` that certifies one. It is not in the Glossary and it is load-bearing
in three places that already exist: the agreed
[Target State's flow](../design/target-state.md#flow) — *"every metric expression traces
to a Certified Metric"* — the Step 005 plan, and the spike's `metric_expressions`, in
the repository since Step 003. This Sub-step makes it a `Rejection Reason` value as well
(`no metric expression`). I have not coined it and I have not registered it: every use
is the Target State's own wording. Whether a phrase three agreed documents rely on
should have a row is Amino's call.

**Approved and registered 2026-08-27.** Amino: *"the `metric expression` term proposal is
approved."* The row sits in
[Glossary Section A](../glossary.md#a-the-system) between `Certified Metric` and
`Shadow Metric`, and it is **entirely in lower case** — the first term registered that
way; `Validation Gate outcome` is the nearest precedent and it capitalises the component
it names. Lower case because the `agreed` Target State, ADR-0001 and ADR-0003 have all
spelled it that way since Step 001: Title Case would have meant editing an agreed
document to match a new Glossary row, which is the wrong direction of travel for a row
whose whole justification is that the word was already in use.

### The eight sceptical items and one Term Proposal → **ruled, and answered in this commit**

**Amino, 2026-08-27:** *"3 → edit the plan accordingly. 5 → if this won't get built in a
specific future step, create a debt for it which triggers when a semantic definition
drifts. 7 → amend. The `metric expression` term proposal is approved. All other changes
are reviewed, approved, and staged."* Recorded as
[R13](../plan/step-005-validation-gate.md#r13--aminos-rulings-on-the-52-review--decided-2026-08-27),
and landing in this commit rather than after it because it arrived before the commit did
— the shape [R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26)
set on the trim and [R12](../plan/step-005-validation-gate.md#r12--aminos-rulings-on-the-51-review--decided-2026-08-26)
kept.

**No code changed.** Every figure, verdict and mutation above was measured before the
ruling and is unchanged by it. Five documents changed — the plan, the Glossary, the Debt
Ledger, Current State and this file — and the four edits are marked inline on items 3, 5
and 7 and in the Language section above, with R13 carrying the reasoning for each.

**What it settles.** Items 1, 2, 4, 6 and 8 are approved as they stand, and two of the
five offered a concrete reversal that is therefore declined. **Item 2** offered folding
`unresolvable` and `no metric expression` into one bar; they stay three, so a chart can
separate a Grounding problem from a generator problem from a statement the optimizer will
not resolve — and that matters more with every Sub-step, because 5.3, 5.4 and 5.5 each add
members to the same taxonomy. **Item 6** offered rewriting 5.1's two flipped probe
statements into certified ones instead of rewriting that module's positive control; the
control stands, so it needs no edit when the next rule lands. The other three are declared
limits rather than offers, and approval records them as known: `count(*)` stays a Shadow
Metric and the pressure lands on Grounding (item 1), `certified_form` goes on raising on a
broken corpus (item 4), and the timings stay dated evidence nothing asserts on (item 8).

**What it does not settle.** The two open costs this entry named are still open and are
still not debt: `resolve` will be called more than once per judgement from 5.3, and
DEBT-014 still has two declared verdicts for 5.4 to flip. And approval is not a
measurement — the probe verdicts hold because the check re-establishes them on every run.

**Verification.** These edits change five documents and no code, so the two checks that
read documents are the ones that can break. Both were re-run after the edits and are
re-pasted here because their counts moved:

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       795 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          849 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr         1037 words
  links      1018 links, 776 anchors 53 documents and python files
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly

$ uv run python .claude/scripts/check_language.py
  glossary: 92 registered terms
  proposed terms: 0 · python files scanned: 24 · identifiers: 1463
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions
```

**92 terms, up from 91** — `metric expression`, the one row this ruling adds. The link
and anchor counts are higher for the ordinary reason: R13, this section, DEBT-018 and the
inline answers on items 3, 5 and 7 are among what the run now reads.

The other four checks were re-run in the same session, after
`uv run python -m veritas.ingestion`, and each exited zero with the output already pasted
above — no code changed, so nothing in them could:

```
$ uv run python .claude/scripts/check_validation_gate/
PASS — the Validation Gate refuses what it cannot read, what is more than one statement, what is not a read, what the planner expects to scan past the ceiling, and what computes a metric the Semantic Layer does not certify; and it allows every Certified Metric

$ uv run python .claude/scripts/check_validation_feasibility.py
PASS — every probe's verdict, every probe's number and every detector's reading is the one this spike recorded

$ uv run python .claude/scripts/check_semantic_layer.py
PASS — every published expression executes against the Warehouse, every figure with a second opinion agrees with it, every registered ambiguity resolves to metrics that exist, and every certified axis names buckets the Warehouse holds

$ uv run python .claude/scripts/check_warehouse.py
PASS — the star schema matches Glossary Section B and the adapter seam holds
```

**One figure in the run above moved and nothing asserts on it**, which is sceptical item
8 arriving the same day it was approved: the catalogue read in one query against one per
table printed **4 ms against 53 ms** in the block above and **2 ms against 27 ms** on this
run, on a machine under a different load. What the check asserts is that the two readings
produce the **same mapping**, and that is `True` in both runs.

---

## Sub-step 5.3 — The Gate refuses a Restricted Column, under an Access Profile

**What changed.** The Validation Gate's sixth rule, and the first that judges a statement
against an *identity*. A statement is now refused when the columns reaching its answer
include one the Access Profile forbids — *reaching the answer*, not appearing in the
text, which is the distinction the whole rule is about. `veritas/validation/profile.py`
is new and holds the `Access Profile`: a role, the `RestrictedColumn`s that role may not
see, and the one profile this slice declares. `gate.py` gains the detector that decides
it — `columns_reaching_the_answer`, `restricted_columns_in_projection` and the numbered
output aliases they need — plus the `no_restricted_column` rule and the Access Profile
argument `judge` now takes. `outcome.py` gains one `Rejection Reason` member. The check package gains
`restricted.py`, the third of [R8](../plan/step-005-validation-gate.md#r8--the-steps-check-is-a-package-with-one-module-per-rule-from-51--approved-by-amino-2026-08-25)'s
five modules.

Four things landed with it.

- **[R2](../plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
  is discharged in full.** The 5.2 review recorded that *"the projection walker and the
  restricted-column detector are still the spike's and go in with 5.3."* They have gone
  in: `check_validation_feasibility.py` holds no copy of `columns_reaching_the_answer`,
  the lineage walk, `ANSWER_COLUMN` or the detector, and its `RESTRICTED_COLUMNS` is now
  a `frozenset` of the `RestrictedColumn` the Glossary registers rather than an anonymous
  pair of strings. **Its 25 declared verdicts and its nine detector readings are
  unchanged**, which is the evidence that this was a move and not a rewrite.
- **A defect in `resolve`**, found by this Sub-step's own probe and fixed here — below.
- **`judge` gained a required argument.** `ValidationGate.judge(sql, access_profile)`
  takes the identity and has no default, so no statement is judged without one to judge
  it under; a Gate is still built with only what its rules read out of the world. It was
  a **constructor** argument in this Sub-step's first draft and moved under
  [R14](../plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27)
  — sceptical item 1 below is where it was raised, and the ruling section at the end of
  this entry is what it cost.
- **[DEBT-008](../debt-ledger.md#debt-008--the-access-control-story-promises-more-than-it-delivers)
  gains a dated status note and its own sentence gains a home.** `gate.py`'s module
  docstring now quotes the entry verbatim — *"applied in the application layer, over
  synthetic data … it does not protect the Warehouse from being read another way"* — and
  the entry says where the enforcement lives. **Nothing is paid**: the Trigger is a claim
  in `README.md`, the App or a demo script, and none of the three exists.

### The plan said ten shapes and the spike has nine

The [plan's verification for this Sub-step](../plan/step-005-validation-gate.md#53--the-gate-refuses-a-restricted-column-under-an-access-profile)
reads *"holding the spike's ten restricted-column shapes"*. `RESTRICTED_COLUMN_PROBES`
holds **nine** — five that must be caught and four that must not — and the check reads
them out of the spike on every run rather than trusting either count. There are ten here
because this Sub-step added one, for the reason in the next section. Recorded rather than
quietly reconciled, the way [R13](../plan/step-005-validation-gate.md#r13--aminos-rulings-on-the-52-review--decided-2026-08-27)
recorded the plan's route sentence.

### The finding: the spike's star probe does not reach this rule

`star over a join to dim_client` is the shape
[ADR-0003](../adr/0003-validation-gate-is-deterministic-code.md) named and the one
[C4](../design/validation-feasibility.md#c4--the-gate-reads-the-schema-at-run-time) exists
for — *"the one shape whose restricted name exists nowhere in its own text"*. Inside the
assembled Gate it never gets here: a star projection aggregates nothing, so the tracing
rule refuses it as `no metric expression` one rule earlier. The leak is real and the
verdict that reports it is somebody else's.

That is not a hole — the statement is refused either way — but it would have left C4's
run-time schema read load-bearing only inside the detector, tested by a function call
rather than by the Gate. **So this Sub-step added a tenth shape**: `client.*` beside the
certified Net Revenue expression, grouped by ordinal so that no column name appears
anywhere in the statement. It traces, so the tracing rule passes it; the star expands
against the live catalogue into three real columns, one of them a Client's name; and the
Gate refuses it as `restricted column`. The text search misses it, as the table below
shows. Turning `expand_stars` off is mutation 2, and that probe is what it breaks.

Three shapes in this module are refused before this rule runs, and all three are declared
with the reason they actually return, the way
[5.2 declared its two](#sub-step-52--the-gate-traces-every-metric-expression-to-a-certified-metric).
What the check adds is that **every** shape is also read by the detector directly, so a
leak in a statement refused for another reason is still measured rather than assumed.

### A defect this Sub-step found: sqlglot refuses in two spellings, and one of them was a crash

`resolve` caught `sqlglot.errors.SqlglotError` and turned it into `TracerRefused`, which
is what makes an unreadable statement a rejection rather than an error. sqlglot also
signals optimizer failures through `Expression.assert_is`, which raises the built-in
**`AssertionError`** — not a `SqlglotError`, and so not caught. A statement that tripped
it escaped the Gate as a traceback: an error where the caller had asked for a verdict,
which is the exact failure `TracerRefused` was introduced to prevent.

It surfaced while running mutation 2 — with `expand_stars` off, the tenth probe's
`client.*` cannot be aliased and `GROUP BY 1` asserts on it, so the mutation produced a
traceback instead of a legible failure. It then reproduced **without** the mutation:

```
SELECT unknown_table.*, count(fct_trade.trade_id) FROM fct_trade, unknown_table GROUP BY 1
```

a star no schema can expand, referred to by position. `resolve` raises
`AssertionError: unknown_table.* is not <class 'sqlglot.expressions.core.Alias'>.`

**The fix is one line in each of the two places that turn a library refusal into
`TracerRefused`**, and it is narrow on purpose: `AssertionError` is caught, a `KeyError`
out of a broken schema mapping is not, which keeps
[DEBT-016](../debt-ledger.md#debt-016--the-semantic-layer-check-cannot-name-the-engines-error-type)'s
distinction — *"a query the engine will not plan is a rejection, and an adapter that
cannot open the Warehouse is a broken installation."*

**Reachability, stated honestly.** Through the assembled Gate it is **not** reachable
today: the bounded rule asks the engine to plan the statement first, and DuckDB will not
plan a query over a table it does not have. `resolve` is nonetheless exported from
`veritas.validation`, the spike calls it, and [R7](../plan/step-005-validation-gate.md#r7--the-bounded-read-uses-the-engines-estimate-if-the-adapter-can-reach-it--approved-by-amino-2026-08-25)
pre-approved a parse-tree fallback for the bounded rule that would remove the shield. The
check puts both statements to the detector directly on every run and requires a refusal,
so the two spellings stay measured rather than argued.

### Verification

```
$ uv run python .claude/scripts/check_validation_gate/

  no Restricted Column reaches the answer
    Access Profile: role 'analyst', 1 Restricted Column(s) — dim_client.client_name
    9 of the spike's 9 claim-2 statements are here character for character; 1 added by Sub-step 5.3
    rejected  net revenue by client                  restricted column
    rejected  star over a join to dim_client         no metric expression
    rejected  aliased to a benign name               restricted column
    rejected  hidden behind a derived table          restricted column
    rejected  a union branch that names the Client   not a read
    allowed   the name in a comment                  —
    allowed   the name in a string literal           —
    allowed   the name in a filter only              —
    rejected  projected inside, aggregated away      shadow metric
    rejected  star beside a certified metric         restricted column

    tree      text      shape                                 reaching the answer
    FOUND     matched   net revenue by client                 dim_client.client_name
    FOUND     missed    star over a join to dim_client        dim_client.client_name
    FOUND     matched   aliased to a benign name              dim_client.client_name
    FOUND     matched   hidden behind a derived table         dim_client.client_name
    FOUND     matched   a union branch that names the Client  dim_client.client_name
    —         matched   the name in a comment                 —
    —         matched   the name in a string literal          —
    —         matched   the name in a filter only             —
    —         matched   projected inside, aggregated away     —
    FOUND     missed    star beside a certified metric        dim_client.client_name
    text matching and the parse tree disagree on 6 of 10 shapes: 2 the text cannot see, 4 it would reject with no Restricted Column reaching the answer at all

    this rule ran on 7 of 10 shapes and allowed 3 of them — the other 3 were refused by an earlier rule
    the optimizer will not resolve it: the Gate refuses it at 'traces', and asked directly the detector raises OptimizeError rather than reporting nothing found
    sqlglot asserts rather than raising its own error: the Gate refuses it at 'bounded', and asked directly the detector raises AssertionError rather than reporting nothing found

PASS — the Validation Gate refuses what it cannot read, what is more than one statement,
what is not a read, what the planner expects to scan past the ceiling, what computes a
metric the Semantic Layer does not certify, and what would carry a Restricted Column into
the answer; and it allows every Certified Metric
```

The three columns are the point. **Text matching and the parse tree disagree on six of
the ten shapes, in both directions** — two the text cannot see at all, and four it would
refuse with nothing restricted reaching the answer. Those four are ordinary questions: a
generator explaining in a comment why it grouped by region instead, a label saying which
column was withheld, one Client's revenue with the name in the `WHERE` clause, and a
count of distinct Clients. A Gate that refused all four is a Gate people route around.

The rest of the run, and the other five checks:

```
$ uv run python .claude/scripts/check_validation_gate/
    one judgement, fastest of 15: schema 3 ms · corpus 20 ms · statement 2 ms · whole Gate 42 ms

$ uv run python .claude/scripts/check_validation_feasibility.py
PASS — every probe's verdict, every probe's number and every detector's reading is the one this spike recorded

$ uv run python .claude/scripts/check_semantic_layer.py
PASS — every published expression executes against the Warehouse, every figure with a second opinion agrees with it, every registered ambiguity resolves to metrics that exist, and every certified axis names buckets the Warehouse holds

$ uv run python .claude/scripts/check_warehouse.py
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_language.py
PASS — documents agree with the Glossary and the writing conventions

$ uv run python .claude/scripts/verify_framework.py
PASS — framework is wired up correctly
```

**The timing line is dated evidence, measured 2026-08-27 on this machine against the
loaded Warehouse, and it is what
[DEBT-019](../debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again)
records.** A whole judgement was 32 ms when 5.2 shipped and is 42 ms now; the same line
printed 3 ms for one catalogue read, and this rule takes a second one and resolves the
statement a second time. The corpus rebuild still dominates both. Every figure here moves
with the machine and no check asserts on any of them — the line is printed by
`check_validation_gate/` on every run.

### Mutation testing

The pattern 2.6 established and 5.1 and 5.2 followed: break one thing, re-run, see the
check fail on the probes that name it, restore, compare with `cmp`. Four mutations, one
per claim this Sub-step makes. Problem lines are trimmed at the em dash, where the
probe's `why` begins.

```
$ # for each: apply the mutation, run the check, restore, cmp
  the rule is dropped from rules()
    FAIL
      - the Gate's rule list holds no entry for `no_restricted_column`, so nothing below is judging the rule this module exists to check
      - 'net revenue by client' was measured as rejected and came back allowed
      - 'aliased to a benign name' was measured as rejected and came back allowed
      - 'hidden behind a derived table' was measured as rejected and came back allowed
      - 'star beside a certified metric' was measured as rejected and came back allowed
      - this rule allowed none of the shapes it ran on, so nothing here separates it from a rule that refuses everything
  SELECT * is not expanded
    FAIL
      - 'star beside a certified metric' was rejected for ['unresolvable'] where it was measured as ['restricted column']
      - 'star over a join to dim_client' carries a Restricted Column into its answer and the parse tree did not find one
      - the columns reaching 'star beside a certified metric''s answer could not be read (AssertionError: client.* is not <class 'sqlglot.expressions.core.Alias'>.)
  the Access Profile restricts nothing
    FAIL
      - the Access Profile restricts no columns, so every probe below passes this rule for the one reason that proves nothing
      - 'net revenue by client' was measured as rejected and came back allowed
      - 'aliased to a benign name' was measured as rejected and came back allowed
      - 'hidden behind a derived table' was measured as rejected and came back allowed
      - 'star beside a certified metric' was measured as rejected and came back allowed
      - 'net revenue by client' carries a Restricted Column into its answer and the parse tree did not find one
      - 'net revenue by client' was measured as matched by text matching and is now missed
      … 12 more, one per shape whose tree or text column moved
  resolve catches only SqlglotError
        raise AssertionError(f"{self} is not {type_}.")
    AssertionError: unknown_table.* is not <class 'sqlglot.expressions.core.Alias'>.

gate.py and profile.py restored byte-for-byte after every mutation
```

Three of the four read as they should. **The fourth is a traceback and that is the
finding**, not a failure of the check: reverting the widened `except` puts the Gate back
to raising where it should reject, and a traceback is what that looks like from outside.
Mutation 2's third line is the same defect *after* the fix — contained, reported as a
problem, and legible.

Mutation 1 breaks four probes and mutation 3 breaks nineteen, which is the difference
between deleting the rule and emptying the declaration it reads: the first leaves the
detector answering correctly and nobody asking, the second makes the detector answer
*nothing restricted* about every shape, so the tree column and the text column both move.

### Deliberately left undone

- **The Access Profile's permitted region.** The Glossary registers *"role and permitted
  region"* and this profile carries the role and its Restricted Columns only. Sub-step
  5.5 adds the region, as [R1](../plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)
  specifies — *"a permitted value of the `by region` axis"*, refused at load if the axis
  does not certify it. A field with no rule behind it would be a promise this module
  cannot keep, which is the same reasoning `outcome.py` applies to a `Rejection Reason`
  with no rule.
- **One profile and one role.** The plan's scope boundary — *"both are files or rows added
  rather than fields changed, so this is a scope boundary rather than debt."*
- **The route rule and the date predicate.** 5.4, where DEBT-014 is paid.
- **[DEBT-019](../debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again)
  is opened.** Each parse-tree rule reads the catalogue and resolves the statement again.
  The consistency argument is the real cost — two rules judging one statement against two
  readings of a live catalogue can disagree about what a `SELECT *` stands for — and the
  trigger is 5.4's route rule, the third rule to read the same catalogue in one judgement.
- **DEBT-008 is not paid**, and the mechanism it is honest about is currently *narrower*
  than the entry describes: the entry says the Gate *"requires the Access Profile's
  predicate to be present"* and that half does not exist until 5.5.
- **`traces.py`'s own *character for character* claim is still unchecked.** `restricted.py`
  reads its nine statements out of the spike and fails if any differs; the module beside
  it asserts the same thing about its own probes in a comment. Extending the check is
  small and belongs to whoever touches that file next — see the sceptical items.

### Look at this sceptically

1. **The Access Profile is a constructor argument, not a `judge()` argument.** The
   Glossary says *"the identity Veritas runs a **question** as"*, which argues for
   `judge(sql, profile)` — one Gate serving many identities, which is what an App
   process does. I made it a field because `ValidationGate` is *"built once with what its
   rules read"* and because a caller wanting a second identity writes
   `replace(gate, access_profile=other)`, which shares the loaded corpus. **This is the
   seam most likely to be wrong**, and it is cheap to move now and not later: the
   Orchestrator does not exist, and there are four construction sites in the repository.
   **Ruled 2026-08-27 — separate the profile from the Gate, as `judge(sql, profile)`.**
   Done: the field is gone, `judge` and `rules` take an `access_profile`, and the one
   rule that reads it is bound to it with `functools.partial` so the other five keep a
   signature that says they need nothing but the statement. Four construction sites gave
   the argument up; seven `judge` calls and four `judge_probes` calls took it, and no
   check's output moved. See
   [R14](../plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27)
   and the ruling section below.
2. **`role="analyst"` is a value with no registered vocabulary.** I treated it the way
   `EU` is treated — data carried by an entry rather than a component of the system —
   and Section A of the Glossary is about components, so a row there would be a poor fit.
   The counter-argument is that the constant is named `ANALYST`, which *is* a code
   identifier carrying domain meaning, and Non-Negotiable 1 governs those. Raised in
   Language below rather than resolved.
   **Ruled 2026-08-27 — fine for now, and approved.** No row. **What brings it back is a
   second role**, which this Step's scope boundary puts outside it; the row is one line
   and `ANALYST` does not move if it is written. This closes the question Language below
   raises, and R14 records why it is not Ledger debt.
3. **`RestrictedColumn` is a class where a tuple did the job.** It buys `str(column)`
   spelling `dim_client.client_name` in one place, a stable sort, and a Glossary term
   with a code identifier. It costs a type in the spike's pinned declaration, which is
   a change to something [R4 of Step 004](../plan/step-004-semantic-layer.md#r4--the-spike-is-pinned-to-the-corpus-rather-than-re-pointed-at-it--approved-by-amino-2026-08-21)
   deliberately froze — the *content* is identical and every declared reading is
   unchanged, but a pin that gets respelled is a pin somebody edited.
4. **The tenth probe groups by ordinal.** `GROUP BY 1, 2, 3` is how I got a star to sit
   beside an aggregate without naming a column, and it is not what a generator with a
   style guide writes. A reviewer could fairly say the probe is built to reach the rule
   rather than drawn from life. The defence is that the property being measured — a
   restricted column reaching the answer with its name nowhere in the text — is real
   whatever syntax produces it, and no other syntax produced it.
5. **`restricted.py` imports the spike.** The provenance check reads
   `check_validation_feasibility.RESTRICTED_COLUMN_PROBES`, which couples the check that
   runs on every commit to a 1,700-line script. The import is inside the function, of one
   constant, and the dependency runs one way — but it is new, and the same claim in
   `traces.py` is still a comment. Either both should be checked or neither.
   **Ruled 2026-08-27 — do not import the spike; what is the alternative?** The
   alternative is to check a claim about **text** against text:
   `probes.spike_statements` reads the `name=` and `sql=` literals off the spike's parse
   tree with `ast` and executes none of it. The shared check it feeds now runs in
   **both** modules — `traces.py`'s comment became a run — which is this item's own
   *"either both should be checked or neither"*. See
   [R14](../plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27)
   and the ruling section below.
6. **The rule's `UNRESOLVABLE` branch is unreached inside the Gate**, and the check says
   so rather than hiding it. The two statements that exercise the detector's refusal are
   put to it directly, which is a function call and not a verdict. The `lineage` arm is
   thinner still: no statement is on file that resolves and whose lineage then cannot be
   walked, and the docstring says exactly that rather than implying a case exists.
7. **Widening `except` to `AssertionError` catches more than sqlglot.** An assertion
   failing anywhere inside `optimize` — including in code we later add — now reads as
   *"the library refused this statement"*. I judged that better than a Gate that crashes,
   and DEBT-016's line still holds for every other exception type, but it is a real
   widening of what gets called a rejection.
   **Ruled 2026-08-27 — fine for now.** It stands. What would make it wrong is an
   `AssertionError` out of **Veritas's own code** inside `optimize` being reported as a
   library refusal, which cannot happen while nothing of ours runs in there; R14 records
   that condition and why the item is not Ledger debt.
8. **`found_by_text` exists twice**, here and in the spike, because each side searches for
   its own declaration and because the rejected alternative should not live inside
   `veritas/validation/` where something could call it. Five lines duplicated to avoid a
   function nobody may use is a trade, not an obvious win.
9. **Two changes to shared check machinery that this Sub-step forced.** `judge_probes`
   now rebuilds a ceiling-carrying probe's Gate with `dataclasses.replace` instead of
   `ValidationGate(gate.warehouse, probe.ceiling)`; the old form silently re-defaulted
   every field it did not name, which meant a ceiling probe was quietly judged against a
   *second* load of `semantic/` and would now be judged under a different identity. And
   the probe-name column widened from 24 to 38 characters, because this module's names
   are the spike's and three of them overflowed. The first is a latent bug fixed in
   passing; the second changes 5.1's and 5.2's printed output, which a reviewer may
   reasonably want out of this commit.
   **Ruled 2026-08-27 — approved.** Both stand. **One clause above stopped being true
   the same day**: item 1's ruling took the Access Profile off the Gate, so a rebuilt
   Gate can no longer pick up a different identity — `judge` carries it. The corpus half
   is the whole of the latent bug now, and `judge_probes`'s docstring says so.

### Language

**No new terms.** Everything this Sub-step names was registered before it started:
[`Access Profile`](../glossary.md#a-the-system) and
[`Restricted Column`](../glossary.md#a-the-system) have been `agreed` since the Domain
Language was, both with `veritas/validation/` as their *Lives in*, and this is the
Sub-step that makes those cells true.

**Code identifiers added, and the term each answers to:** `AccessProfile` and its
`access_profile` field (`Access Profile`); `RestrictedColumn`, the `restricted_columns`
field, `restricted_columns_in_projection` and `RejectionReason.RESTRICTED_COLUMN`
(`Restricted Column`); `no_restricted_column`, the rule, named for what it decides.
`columns_reaching_the_answer` and `ANSWER_COLUMN` are the spike's own names, moved rather
than coined.

**One question, raised and answered by
[R14](../plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27)
on the day it was raised: does the Access Profile's `role` want a Glossary row?** It does
not, for now — sceptical item 2 above carries the ruling and what brings it back. The
argument that was put, unchanged:

The value is `"analyst"` and the constant naming the profile is `ANALYST`. I read
the role as a *value* — the same kind of thing as `EU`, a bucket the `by region` axis
certifies, which lives in the entry and not in a Glossary row — and Section A is a table
of components, which a job title is not. Against that: `ANALYST` is a code identifier
carrying domain meaning, and Non-Negotiable 1 says those must match Glossary terms. The
question only becomes load-bearing when a second role exists, which the plan puts outside
this Step, so it is recorded rather than settled. If it should be registered, the row is
one line and the constant does not move.

That last sentence is what the ruling took: no row now, and a second role is what asks
again.

### The nine sceptical items and one question → **ruled, and answered in this commit**

**Amino, 2026-08-27:** *"1 → separate the profile from the gate as in `judge(sql,
profile)`. 2 → fine for now and approved. 3 → fine and approved. 4 → fine and approved.
5 → we shouldn't import the spike. what is the alternative? 6 → approved. 7 → fine for
now. 8 → approved. 9 → approved and very good. All other changes are reviewed, approved
and staged."* Recorded as
[R14](../plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27),
and landing in this commit rather than after it because it arrived before the commit did
— the shape [R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26),
[R12](../plan/step-005-validation-gate.md#r12--aminos-rulings-on-the-51-review--decided-2026-08-26)
and [R13](../plan/step-005-validation-gate.md#r13--aminos-rulings-on-the-52-review--decided-2026-08-27)
set.

**Code changed this time**, which is the difference from the three rulings before it: two
of the nine items cost an edit, and one of the two moved a seam. Everything above was
re-measured after the edits and the marks are inline on items 1, 2, 5, 7 and 9.

**Item 1 — the Access Profile left the Gate.** `ValidationGate` no longer has an
`access_profile` field; `judge(sql, access_profile)` and `rules(access_profile)` take it,
with no default. The identity is bound into the single rule that reads it with
`functools.partial`, so `Rule` stays *one `Reading` in, a verdict out* and the three
module-level rules keep a signature that says they need nothing but the statement — which
is what the module's whole ordering argument rests on. Six files: `gate.py`, and the five
in `.claude/scripts/check_validation_gate/`. **Four** construction sites gave the argument
up and **eleven** call sites took it — seven `judge` calls, and four calls to the checks'
shared `judge_probes`, which gained a parameter of its own; `rule_name` gained two lines
to unwrap the `partial`.

**No verdict, reason, count or column moved.** The `no Restricted Column reaches the
answer` block above was re-run after the move and is the same 29 lines, character for
character. That is the evidence this was a seam moved and not a rule changed, and it is
the reason the move was cheap today: the Orchestrator does not exist, and what used to be
four construction sites are now four call sites.

**Item 5 — nothing imports the spike.** `probes.spike_statements` parses
`check_validation_feasibility.py` with `ast` and reads the `name=` and `sql=` literals off
its parse tree, executing none of it. What the checks depend on is now a **file at a
path** holding a dated measurement, rather than a 1,700-line module that has to keep
importing; the direction stays the one
[R2](../plan/step-005-validation-gate.md#r2--the-spike-imports-the-gate-rather-than-keeping-its-own-tracer--approved-by-amino-2026-08-25)
set, with the spike importing `veritas/validation/` and nothing importing the spike.

The shared check it feeds runs in **both** rule modules, which is the item's own *"either
both should be checked or neither"*. `restricted.py`'s line is unchanged. `traces.py`'s
comment became three lines of run output:

```
$ uv run python .claude/scripts/check_validation_gate/

  every metric expression traces to a Certified Metric
    15 of the spike's 16 claim-1 statements are here character for character (1 renamed); 3 added by Sub-step 5.2
    'notional, wrong currency' is the spike's 'notional through the wrong currency', character for character, under a shorter name
    the spike's 'unparseable' is not judged here — the Gate refuses it at `parses`, three rules earlier, and `read_only.py` measures that shape with a statement of its own
```

The third line is the part worth reading twice. A statement the spike measures and a rule
module does not judge is a **problem** unless it is declared, and `traces.py` declares
exactly one, naming where the shape is covered instead. A declaration that stops
describing anything — the spike drops the statement, or the module judges it after all —
fails the run too, because an allowance nobody re-reads is how coverage quietly shrinks.
The rename line is the same idea: the local name is shorter than the spike's and the
**statement** is identical, so the check says so rather than counting it as a new shape.

**Mutation testing, re-run.** The four above were re-applied against the moved seam and
each produced the same output it did before the ruling — 6 problems, 3, 19 and a
traceback — though mutation 1's edit is now the removal of a `partial`-bearing entry
rather than a bound method. A fifth was added for the mechanism item 5 introduced:

```
$ # apply the mutation, run the check, restore, cmp
  a probe statement drifts from the spike's
    FAIL — 1 problem(s)
      - the statement for 'bare' differs from the spike's, so this module and the spike's
        dated measurement are no longer judging the same shape
          spike: SELECT sum(fct_trade.commission * fct_fx_rate.fx_rate) FROM fct_trade …
          here:  SELECT  sum(fct_trade.commission * fct_fx_rate.fx_rate) FROM fct_trade …

gate.py, profile.py and traces.py restored byte-for-byte after every mutation
```

**The mutation is one extra space** after `SELECT` in `traces.py`'s first probe — a
change no engine would notice, which is the whole point: the two files would go on
looking like they agreed about a shape while judging different text. The check names the
file, the shape and both statements. It is the claim that was a comment in that file
until today.

**And the declared allowance was mutated in both directions**, because a coverage
allowance that nothing tests is exactly the kind of thing this Sub-step added:

```
$ # apply the mutation, run the check, restore, cmp
  the declared allowance is dropped
    FAIL — 1 problem(s)
      - the spike measures 'unparseable' and this module does not judge it — a shape the feasibility run covered and the Gate's own check does not
  an allowance that describes nothing is declared
    FAIL — 1 problem(s)
      - 'aliased' is declared as covered elsewhere (a shape this module judges) and the spike no longer has a statement this module skips under that name — the allowance has stopped describing anything and should be removed

traces.py restored byte-for-byte after both
```

The second is the one worth having. Declaring a shape as covered elsewhere is how a check
is talked out of a finding, so the declaration has to fail when it stops being about
anything — otherwise the list only ever grows.

**Items 2 and 7 are approved *for now*, and neither is Ledger debt.** R14 carries the
reasoning and the condition that brings each back: a second role for the `role` row, and
an `AssertionError` raised by Veritas's own code inside `optimize` for the widened
`except`. Neither is the cheap thing standing in for the right thing, and an entry whose
trigger cannot fire inside this project's life is a wish rather than debt.

**Item 9's second clause stopped being true the same day it was approved.** The review
said a rebuilt Gate *"would now be judged under a different identity"*; after item 1 there
is no identity on the Gate to re-default, so the latent bug `replace` fixes is the corpus
half alone. `judge_probes`'s docstring is corrected rather than left as the version this
entry quoted.

**Verification, after the edits.** Every check was re-run in the same session:

```
$ uv run python .claude/scripts/check_validation_gate/
PASS — the Validation Gate refuses what it cannot read, what is more than one statement, what is not a read, what the planner expects to scan past the ceiling, what computes a metric the Semantic Layer does not certify, and what would carry a Restricted Column into the answer; and it allows every Certified Metric

$ uv run python .claude/scripts/check_validation_feasibility.py
PASS — every probe's verdict, every probe's number and every detector's reading is the one this spike recorded

$ uv run python .claude/scripts/check_semantic_layer.py
PASS — every published expression executes against the Warehouse, every figure with a second opinion agrees with it, every registered ambiguity resolves to metrics that exist, and every certified axis names buckets the Warehouse holds

$ uv run python .claude/scripts/check_warehouse.py
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_language.py
  glossary: 92 registered terms
  proposed terms: 0 · python files scanned: 26 · identifiers: 1538
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions

$ uv run python .claude/scripts/verify_framework.py
  links      1088 links, 843 anchors 55 documents and python files
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
```

**The spike's own run is the one to look at.** It imports the tracer and the detector from
`veritas/validation/` and it exercises no `ValidationGate`, so the seam move could not
have touched it — and its 25 declared verdicts and nine detector readings are unchanged,
for the second time in this Sub-step.

**Two figures in the timing line moved and nothing asserts on either**, the same way item
8 predicted: *"one judgement, fastest of 15"* printed **schema 3 ms · corpus 20 ms ·
statement 2 ms · whole Gate 42 ms** in the block above and **schema 4 ms · corpus 22 ms ·
statement 2 ms · whole Gate 49 ms** on this run, on a machine under a different load. The
line is printed on every run and no check compares it with anything.

**What this does not settle.** DEBT-014's two declared verdicts are still there for 5.4 to
flip, DEBT-019 is still open and its trigger is still 5.4's route rule, and DEBT-008 is
still unpaid and still describes an enforcement wider than the one that exists — the
Access Profile's predicate arrives in 5.5.

---

## Sub-step 5.4 — Pay DEBT-014: the Gate checks the route and the date predicate

**What changed**

The Validation Gate gained its seventh rule and its last one before the Access Profile's
predicate: **`ValidationGate.routed`**, which asks whether a statement computed its
certified expression over the rows its Metric Definition describes. Two readings, one
rule, two `Rejection Reason` members.

- **The route.** `route_of` reads what a statement's rows come from — the tables it
  starts at, and the joins it reaches the rest through, each join written on base tables
  and canonicalised so an alias is invisible. `certified_route` builds the same value
  out of a declaration by assembling the metric's own expression over its own
  `from_table` along its own Join Paths and reading **that** statement the same way,
  which is `certified_form`'s argument applied one level out: the corpus goes through the
  same reader as the query, or the two agree only until a rewrite touches one of them.
  A `Route` is a frozen pair of frozensets with one method, `joins_beyond`, and both
  directions of the rule are that one method — called on the statement it names the
  joins nothing certifies, called on the certified route it names the joins the statement
  left out. **Permission comes from a list**, which is the shape
  [the plan fixed](../plan/step-005-validation-gate.md#how-the-five-sub-steps-divide-the-work)
  for exactly this reason: *"5.4's route rule is written to take its permitted joins from
  a list, so 5.5 lengthens that list rather than rewriting the rule."*
  `permitted_route` is that list, and today it has one source.
- **The date predicate.** `date_columns_filtered` reads every date column a WHERE clause
  in any scope keys on — a date being what the live catalogue calls `DATE`, not a list of
  column names — and the rule refuses any that is not the traced metric's `date_column`.
  It reads the WHERE and not the JOIN conditions, because every Join Path that reaches
  `fct_fx_rate` keys on a date and a rule that read those would find `trade_date` in
  every converted metric and have nothing left to say.

**[DEBT-014](../debt-ledger.md#debt-014--the-spike-allows-a-query-the-gate-must-reject) is
paid, on both of its halves and in both of its homes.** The Gate rejects `notional
through the wrong currency`; `traces.py`'s declared verdict for it moved from `allowed`
to `rejected · uncertified route`; and the spike's `BLIND_SPOT` kind is gone, its one
member now an ordinary Shadow Metric. Making the spike's verdict honest meant giving it a
third pinned declaration — `CERTIFIED_ROUTES`, three routes beside its three expressions —
and folding the route into claim 1's verdict, so the spike's tracer stops being a tracer
that reads the projection alone. `check_semantic_layer.py`'s check 9 was widened from the
expression to the route in the same commit, because a pin nothing compares with
`semantic/` is the second corpus that check exists to prevent. Claim 4 reads the route
too, so a round trip that rewrote a join condition and left the projection alone is now
something the spike would catch.

The date half was the one the Ledger called *"argued rather than measured"*.
`check_validation_gate/route.py` **executes** `Gross Revenue` over one period keyed on
`trade_date` and the same period keyed on `settlement_date`, prints both figures and the
gap, and fails the run if they stop differing. Both boundaries are read from the Snapshot
calendar, so [DEBT-012](../debt-ledger.md#debt-012--the-price-table-is-sparse-so-the-snapshot-calendar-has-holes)'s
third arm came into reach and stayed unfired.

**[DEBT-019](../debt-ledger.md#debt-019--every-parse-tree-rule-reads-the-catalogue-and-resolves-the-statement-again)
is paid, in the shape it named.** Its Trigger was this Sub-step's route rule — the third
rule to read the catalogue in one judgement — and the interface it listed first is the one
built: a per-judgement context, which is `Reading`. `judge` builds one and hands it to
every rule; the catalogue, the resolved statement and the corpus's canonical forms are
`cached_property` on it. Four parse-tree rules now read one tree qualified against one
catalogue, which was the entry's argument — *"a verdict assembled from two views of the
Warehouse is a verdict about neither"* — rather than the milliseconds. Each public helper
gained a variant taking an already-resolved tree (`projections_of`,
`metric_expressions_of`, `columns_reaching_the_answer_of`,
`restricted_columns_in_projection_of`, `route_of_resolved`), the public signatures the
spike calls are unchanged, and the one walk that edits a tree copies first — sharing a
resolution turns a local mutation into a rule judging `answer_column_0` instead of what
the generator wrote.

**Three declared verdicts moved in checks this Sub-step did not otherwise touch, and one
is a cost rather than a fix.** `traces.py`'s `net revenue by region` and `restricted.py`'s
`the name in a comment` and `the name in a filter only` all reach `dim_client` through
two joins no Semantic Entry names, so the Gate now refuses them. That is
[R1](../plan/step-005-validation-gate.md#r1--the-access-profiles-predicate-and-the-slice-rule-ship-together-in-this-step--approved-and-widened-by-amino-2026-08-25)'s
*"`by region` is a certified axis no query can reach"* said by the Gate instead of by the
plan, and **Sub-step 5.5 flips all three back** when it certifies those two hops. Each
carries its new verdict and the reason it will move again, so the flip is a measurement.

Their modules needed one real change to stay honest, and it is
`probes.rule_verdicts`: **a rule's verdict is not the Gate's**. Until this Sub-step the
two were the same answer for whichever rule ran last, and each module's positive control
read `ValidationGateOutcome.allowed`. Reading it now would report the Restricted Column
rule as having refused two shapes it passed on. `ValidationGateOutcome.rules` is what
tells them apart — a rule that appears **last** on a rejected outcome is the rule that
rejected — and it is the field Sub-step 5.1 added for exactly this. `traces.py` gained
the same reading, because two of its probes now carry a `why` claiming the tracing rule
allowed a statement the Gate rejects.

**`read_only.py`'s cross-product citation became true and was rewritten.** It said *"a
cross product that computed a certified one would still be allowed here. Bounding that is
the certified-route rule's job in Sub-step 5.4."* It is: a join with no condition is a
join nothing certifies, and `route.py` puts that statement in front of the Gate on every
run. The blind spot in the **estimate** is unchanged and is still that probe's finding.

**Verification**

```
$ uv run python .claude/scripts/check_validation_gate/
  the metric's own route, and its own period
    Snapshot calendar: the period is 2024-08-13 to 2024-11-12, both read from fct_position_snapshot (DEBT-012's third arm stays unfired)
    Traded Notional: 262266110.69 through the Quotation Currency · 7264542867.58 through the Denomination Currency — 96.39% apart
    Gross Revenue: 23263.33 keyed on trade_date, 2024-08-13 to 2024-11-12 · 22456.40 keyed on settlement_date, same period — 3.47% apart
    DEBT-020: Realised P&L is 7573245.41 with its certified filter and 7832146.76 with it dropped — 3.31% apart, and the Gate allows both

    rejected  notional through the wrong currency    uncertified route
    rejected  a cross product, certified metric      uncertified route
    rejected  a count with a multiplying join        uncertified route
    rejected  net revenue by region                  uncertified route
    allowed   traded notional                        —
    allowed   a period keyed on Trade Date           —
    rejected  a period keyed on Settlement Date      uncertified date column
    allowed   Realised P&L with its filter dropped   —
    allowed   Realised P&L as its entry says         —

    route     dates     shape                                 what this rule reads
    OFF       —         notional through the wrong currency   Traded Notional · 1 join(s) nothing certifies · 2 certified join(s) absent
    OFF       —         a cross product, certified metric     Gross Revenue · 1 join(s) nothing certifies
    OFF       —         a count with a multiplying join       Trade Count · 1 join(s) nothing certifies
    OFF       —         net revenue by region                 Net Revenue · 2 join(s) nothing certifies
    on        —         traded notional                       Traded Notional
    on        —         a period keyed on Trade Date          Gross Revenue
    on        STRAY     a period keyed on Settlement Date     Gross Revenue · filtered on fct_trade.settlement_date
    on        —         Realised P&L with its filter dropped  Realised P&L
    on        —         Realised P&L as its entry says        Realised P&L

    Account Value       3 certified join(s) · keyed on fct_position_snapshot.snapshot_date · starts at fct_position_snapshot
    Cash Balance        1 certified join(s) · keyed on fct_balance_snapshot.snapshot_date · starts at fct_balance_snapshot
    Gross Revenue       1 certified join(s) · keyed on fct_trade.trade_date · starts at fct_trade
    Net Revenue         1 certified join(s) · keyed on fct_trade.trade_date · starts at fct_trade
    Position Change     0 certified join(s) · keyed on fct_position_snapshot.snapshot_date · starts at fct_position_snapshot
    Realised P&L        1 certified join(s) · keyed on fct_accounting_movement.movement_date · starts at fct_accounting_movement
    Trade Count         0 certified join(s) · keyed on fct_trade.trade_date · starts at fct_trade
    Traded Notional     2 certified join(s) · keyed on fct_trade.trade_date · starts at fct_trade
    Unrealised P&L      3 certified join(s) · keyed on fct_position_snapshot.snapshot_date · starts at fct_position_snapshot
    this rule ran on 9 of 9 Certified Metrics and allowed 9 of them
    this rule ran on every one of the 9 shapes above and reached the verdict on 5 of them

PASS — the Validation Gate refuses what it cannot read, what is more than one statement, what is not a read, what the planner expects to scan past the ceiling, what computes a metric the Semantic Layer does not certify, what would carry a Restricted Column into the answer, and what computes a certified metric across a route or over a period the corpus does not certify for it; and it allows every Certified Metric
```

The tracing rule's own section of the same run, which is where the two moved verdicts and
DEBT-019's payment are visible:

```
    allowed   bare                                   —
    allowed   aliased                                —
    allowed   derived table                          —
    allowed   common table expression                —
    allowed   net revenue                            —
    rejected  net revenue by region                  uncertified route
    allowed   traded notional                        —
    rejected  commuted subtraction                   shadow metric
    rejected  commuted multiplication                shadow metric
    rejected  open-coded net revenue                 shadow metric
    rejected  unconverted commission                 shadow metric
    rejected  rebate silently dropped                shadow metric
    rejected  notional, wrong currency               uncertified route
    rejected  certified beside shadow                shadow metric
    rejected  half-certified union                   not a read
    rejected  unknown table                          unbounded scan
    rejected  no metric expression                   no metric expression
    rejected  unresolvable                           unresolvable
    this rule ran on 16 of 18 shapes and refused 8; 2 were refused before it and 2 after it — net revenue by region, notional, wrong currency

    one judgement, 7 rules: the catalogue was read 1 time(s), and the Reading holds one of each of corpus, resolved, schema (DEBT-019)
    one judgement, fastest of 15: schema 4 ms · corpus 22 ms · statement 2 ms · whole Gate 42 ms
```

and the Restricted Column rule's, where its verdict and the Gate's come apart:

```
    this rule ran on 7 of 10 shapes, refused 4 and passed 3 on — the other 3 were refused by an earlier rule
```

The spike's claim 1, where `BLIND_SPOT` has no members:

```
$ uv run python .claude/scripts/check_validation_feasibility.py
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
    REJECTED  notional through the wrong currency  Traded Notional · off route: 2 pinned join(s) absent
    REJECTED  half-certified union                 Gross Revenue, plus 1 uncertified
    REJECTED  unknown table                        1 expression(s), none certified
    REFUSED   unparseable                          ParseError: Expecting ). Line 1, Col: 48.

    7 certified · 2 form · 6 shadow · 1 refused · 0 blind spot (DEBT-014 paid in Sub-step 5.4)
```

and the widened check 9, which is what holds the new pin to the corpus:

```
$ uv run python .claude/scripts/check_semantic_layer.py
  spike pin — the expressions and routes the Sub-step 3.2 spike measured
    pinned   Gross Revenue     1 join path(s)
    pinned   Net Revenue       1 join path(s)
    pinned   Traded Notional   2 join path(s)
```

Every committed check, in full:

```
$ uv run python .claude/scripts/verify_framework.py
PASS — framework is wired up correctly

$ uv run python .claude/scripts/check_language.py
PASS — documents agree with the Glossary and the writing conventions

$ uv run python .claude/scripts/check_warehouse.py
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_data_availability.py
PASS — every source is obtainable and every distinction separates

$ uv run python .claude/scripts/check_semantic_layer.py
PASS — every published expression executes against the Warehouse, every figure with a second opinion agrees with it, every registered ambiguity resolves to metrics that exist, and every certified axis names buckets the Warehouse holds

$ uv run python .claude/scripts/check_validation_feasibility.py
PASS — every probe's verdict, every probe's number and every detector's reading is the one this spike recorded
```

**The three figures above are dated evidence, measured 2026-08-28 on the currently
committed snapshot window** and reproduced by the command that printed them. They move
when ingestion refreshes: the period is read from the Snapshot calendar, and the two
notional figures are the whole loaded window. The timing line moves with the machine and
nothing asserts on it.

**Deliberately left undone**

- **[DEBT-020](../debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters)
  — the rule reads two of a Metric Definition's three row-describing fields.** `filters`
  is the third, and a statement that computes `Realised P&L`'s certified expression across
  its certified route with `movement_type = 'realised P&L'` dropped is **allowed**, while
  summing four movement types instead of one. Found while building this rule, recorded
  rather than fixed, because the plan names what 5.4 builds and Amino approved that scope.
  It is declared as a passing probe with both numbers printed, which is what the entry's
  cost paragraph is about and is also the cost DEBT-014 named: this file passes while
  demonstrating a wrong answer. **This was the question for the ruling below, and
  [R15](../plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28)
  answered it: the entry is paid in Sub-step 5.5**, so the probe's `allowed` verdict is
  one Sub-step old rather than one Step old.
- **`by region` is unreachable and this Sub-step is what makes that visible.** Three
  declared verdicts moved to `rejected` and 5.5 moves them back. Nothing is broken that
  was working — the Gate had no route rule to refuse them with — but between this commit
  and 5.5 the Gate refuses a legitimate slice by a certified axis.
- **Two joins to one table under different aliases are not told apart** — now
  [DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart),
  under [R15](../plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28).

  Ask one statement for `Gross Revenue` **and** `Traded Notional` and it has to join
  `fct_fx_rate` twice, because the two metrics convert by different routes: Gross Revenue
  on the Trade's own Denomination Currency, one hop from `fct_trade`; Traded Notional on
  the Instrument's Quotation Currency, two hops, through `dim_instrument`. Call the two
  aliases `denom_rate` and `quote_rate`. Then both readings this rule depends on go
  blind at once:

  * `permitted_route` **unions** the two metrics' routes, so both joins are certified and
    `joins_beyond` is empty in both directions;
  * every reading writes columns on their base table before comparing, so
    `sum(fct_trade.commission * denom_rate.fx_rate)` and
    `sum(fct_trade.commission * quote_rate.fx_rate)` are the **same string** by the time
    the tracing rule sees either.

  So the two conversions can be swapped over — Gross Revenue taken at the Instrument's
  rate — and every rule the Gate has is satisfied. That is `notional through the wrong
  currency`, the statement DEBT-014 was opened about and this Sub-step closed, in its
  two-metric form.

  It was left as prose here on the ground that *"the trigger would be a generator that
  joins one table twice, which does not exist."* That reasoning does not hold: the
  generator is `GENERATE`, step 4 of the
  [Target State's flow](../design/target-state.md#flow), and a later Step of this project
  builds it. The trigger fires inside this project's life, so it is debt rather than an
  extension, and the entry says plainly that nothing in the repository demonstrates it and
  that the Sub-step paying it owes a probe.
- **The rule reads the metric's route and not a Dimension Definition's**, which is 5.5.

**Look at this sceptically**

1. **The route half and the date half are one rule with two reasons, and that is a
   judgement.** [C2](../design/validation-feasibility.md#c2--a-metric-definition-carries-its-join-path-and-its-date-predicate)
   and DEBT-014's 2026-08-20 status note both say the two are one question — *"the same
   shape: two columns on `fct_trade`, a projection that cannot tell them apart"* — and
   the plan's flow diagram gives 5.4 one line. The alternative is two rules in
   `rules()`, which would make the ordering list say what the taxonomy already says.
   What one rule costs is that a statement wrong in both ways reports only the route.
2. **The rule compares routes for *equality*, and the spike compares them for
   *containment*.** The Gate must refuse a join nothing certifies or it permits a cross
   product; the spike has no Dimension Definitions to certify a slice's extra joins
   against, and `net revenue by region` is the shape where the two policies differ. The
   **reading** is shared — one `route_of`, one `certified_route` — and only the
   comparison differs. It is stated in both files. A reviewer could reasonably say two
   policies is one too many and that the spike should carry the Gate's.
3. **`Route` is a new name and it has no Glossary row.** A Term Proposal is below.
   → **approved and registered in this commit**; see the Language section and
   [R15](../plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28).
4. **The route is a set, not a sequence.** A statement writing its two joins in the other
   order is allowed, which is right — the rows are the same — and the cost is that one
   table joined twice on the same condition collapses to one element. That is a
   self-cross-product no generator writes, and the set is what stops the rule refusing
   punctuation.
5. **`Reading` lost `slots=True` to gain `cached_property`.** That is a real trade: a
   slotted class has no `__dict__` and `cached_property` needs one. It is still frozen,
   and the memo is what `check_one_judgement_reads_once` reads to prove DEBT-019 paid —
   so the `__dict__` is doing two jobs, one of them as evidence.
6. **The lazy catalogue is one indirection deep and the check found why.** `judge` passed
   `self.warehouse.columns_by_table` to the `Reading` and `read_only.py` failed
   immediately: taking a bound method is already touching the adapter.
   `ValidationGate.catalogue` is the fix. It is the kind of thing that would have shipped
   silently without that check, and it is worth knowing it nearly did.
7. **`DATE_TYPE = "DATE"` is a second copy of `check_semantic_layer.py`'s constant.** Two
   files ask the catalogue what a date column is and neither reads the other. They are a
   component and a script, they ask different questions of the answer, and importing a
   script into `veritas/` is the thing this project does not do — but it is two literals.
8. **The date rule reads the WHERE clause and every scope of it.** `Position Change`'s
   correlated subquery carries `snapshot_date` in a WHERE of its own, so that metric has a
   date-keyed filter whether or not the question had a period — and it passes because the
   column is its own `date_column`. A metric whose expression filtered on a *different*
   date column would be refused when computed exactly as its entry says. None does.
   → **[EXT-010](../extension-register.md#ext-010--a-metric-certified-over-more-than-one-date-column)
   is opened for it in this commit**: the nine metrics are fixed by Glossary Section B and
   no Step in this project writes a tenth, so the trigger cannot fire here.
9. **`route.py` reads two of its statements out of the spike's source text instead of
   holding literals.** That removes a third copy and keeps the provenance claim checked
   where it already is, and it costs those two statements being invisible to
   `check_warehouse.py`'s dialect scan — which reads them in the spike. Five of this
   module's statements are literals and the scan reads them; no exemption is claimed.
10. **The DEBT-020 probe is declared `allowed`.** That re-creates, deliberately, the shape
    DEBT-014's cost paragraph complained about — a check that passes while demonstrating a
    wrong answer. The alternative is a hole nobody re-reads. It is the same trade the
    project made for DEBT-014 and it should be made knowingly or not at all.
    → **made knowingly, and for one Sub-step only**: R15 pays DEBT-020 in 5.5, where the
    probe pairs off into an allowed statement and a rejected one.

**A question for the ruling** → **answered: pay it in 5.5.** DEBT-020 is one field away
from what this rule already does, and its repayment is the comparison this rule already
performs, against the conjuncts of a WHERE clause instead of against a join list. Should
it be paid **in 5.5**, which already touches this rule to lengthen its permission list,
or left on the Ledger for the Grounding Step its Trigger names? Paying it in 5.5 makes
that Sub-step — already the largest in the Step and already the pre-agreed split point —
larger still. Leaving it means the slice ships with a Gate that certifies the arithmetic,
the route and the period and not the rows a filter selects.

**Language**

- **No new domain term reached a code identifier**, with one exception below. `route`,
  `date column` and `period filter` are all words the project already uses:
  [`Join Path`](../glossary.md#a-the-system) is registered as *"a certified **route**
  between two warehouse tables"*, [R8 of Step 004](../plan/step-004-semantic-layer.md#r8--the-route-a-metric-definition-carries--decided-in-sub-step-42-under-aminos-ruling-of-2026-08-22)
  is titled *"the route a Metric Definition carries"*, and `date_column` has been a
  Metric Definition field since Step 004.
- **Two `Rejection Reason` members added**: `UNCERTIFIED_ROUTE` (*"uncertified route"*)
  and `UNCERTIFIED_DATE_COLUMN` (*"uncertified date column"*), ten in the taxonomy. The
  members are registered in code and deliberately not in the Glossary, which is the
  `Rejection Reason` row's own decision.

> 🆕 **TERM PROPOSAL** — **`Route`**: where a statement's rows come from — the tables it
> starts at, and the joins it reaches the rest of them through. Read off a parse tree or
> built from a Metric Definition's `from_table` and `join_paths`, so that a statement's
> and a metric's can be compared as values.
>
> **Why it is not `Join Path`.** A Join Path is **one certified hop between two tables**,
> published as a file in `semantic/joins/`. A Route is the **whole chain plus where it
> starts**, and it is never published: it is read, from a statement or from an entry's
> fields. `Traded Notional`'s Route is two Join Paths and `fct_trade`; `Trade Count`'s is
> no Join Paths and `fct_trade`. Registering it separates *what the corpus certifies* from
> *what a query took*, which is the whole content of the rule this Sub-step added.
>
> The word is already in the project's prose — the `Join Path` row's own definition, R8 of
> Step 004, and this Step's plan — and Sub-step 5.4 made it a class in
> `veritas/validation/`. Agree, rename, or reject?
>
> → **Approved 2026-08-28 and registered in this commit.** The row sits in
> [Glossary Section A](../glossary.md#a-the-system) directly after `Join Path`, in Title
> Case, and Section A's amendment block carries the date and the reasoning.

### The ten sceptical items, one Term Proposal and one question → **ruled, and answered in this commit**

**Amino, 2026-08-28:** *"3 → term proposal is approved. 8 → create an extension for this
if this kind of metric won't happen in the current project's slice. 10 → pay debt-20 in
5.5. All others approved as is."* — with two clarifications on this review's own prose:
the `resolved` docstring's un-cached exception paragraph and the third *deliberately left
undone* item were to be made *"clearer, simpler and more tangible"*, and the second was
to be filed on the same test as item 8. Recorded as
[R15](../plan/step-005-validation-gate.md#r15--aminos-rulings-on-the-54-review--decided-2026-08-28),
landing in this commit rather than after it because it arrived before the commit did —
the shape [R11](../plan/step-005-validation-gate.md#r11--aminos-rulings-on-the-trim--decided-2026-08-26),
[R12](../plan/step-005-validation-gate.md#r12--aminos-rulings-on-the-51-review--decided-2026-08-26),
[R13](../plan/step-005-validation-gate.md#r13--aminos-rulings-on-the-52-review--decided-2026-08-27)
and [R14](../plan/step-005-validation-gate.md#r14--aminos-rulings-on-the-53-review--decided-2026-08-27)
set.

**No rule changed and no seam moved**, which is the difference from R14. **Every line of
code changed by this ruling is inside a docstring** — `gate.py`'s `resolved` and
`permitted_route`, and `route.py`'s module docstring and `filter_probes` — which is why
the whole Verification block above came back unchanged. Beyond that: a Glossary row was
added, each register gained an entry, and the plan's 5.5 gained a third item. The marks
are inline on items 3, 8 and 10 above.

**Item 3 — `Route` is registered.** The row goes into
[Glossary Section A](../glossary.md#a-the-system) directly after `Join Path`, in Title
Case, and Section A's amendment block carries the date and why the case differs from
`metric expression`'s: no `agreed` document had already fixed a lower-case spelling of
`Route` as a noun in its own right. `check_language.py` now reads **93** registered terms
where it read 92, and the `Route` class in `veritas/validation/gate.py` matches a
Glossary row like every other domain name in the codebase.

**Item 8 — [EXT-010](../extension-register.md#ext-010--a-metric-certified-over-more-than-one-date-column)
is opened, and the test the instruction named is what put it there.** *"If this kind of
metric won't happen in the current project's slice"* — it will not: the nine Certified
Metrics are fixed by [Glossary Section B](../glossary.md#b-the-warehouse), 5.5's corpus
change adds Join Paths and a `routes` field rather than a metric, and no later Step in
this project writes a Metric Definition. So the trigger cannot fire inside this project's
life, which is the Register's own test, and the entry carries a Readiness. It is filed
with one boundary written down, because two questions about dates are easy to run
together: [R11's second ruling of Step 004](../plan/step-004-semantic-layer.md#r11--aminos-rulings-on-the-45-review--decided-2026-08-25)
deferred a `by settlement date` **axis** — what a query may *slice* on, which lands in a
GROUP BY — while EXT-010 is what a metric's own expression may *filter* on, which lands
in a WHERE. The rule that refuses `a period keyed on Settlement Date` is unchanged and
stays right.

**Item 10 and the question — DEBT-020 is paid in 5.5.** The review put both sides up and
the ruling took the earlier one, so the slice does not ship a Gate that certifies the
arithmetic, the route and the period while saying nothing about the rows a filter
selects. The entry gains a dated status note and keeps its Trigger, because a Trigger
records when repayment stops being optional and this is a decision to pay before it
fires; the [plan's 5.5](../plan/step-005-validation-gate.md#55--the-gate-requires-the-access-profiles-predicate-admits-a-slice-route-and-pays-debt-020)
gains the work, the flipped probe and the mutation that proves the flip is a rule.
**What that costs is named rather than absorbed**: 5.5's title now needs two `and`s,
which is `planning-a-step`'s own test for a Sub-step that is really two, and R15 says
where the split falls if [R5](../plan/step-005-validation-gate.md#r5--55-is-a-pre-agreed-split-point--approved-by-amino-2026-08-25)
fires — the corpus change and the access predicate in one Sub-step, the filters in the
next.

**The third *left undone* item became [DEBT-021](../debt-ledger.md#debt-021--two-joins-to-one-table-under-different-aliases-are-not-told-apart),
not an extension**, because the instruction's own test comes out the other way here. The
item is rewritten above with the statement that reaches it; what the rewrite exposed is
that the reason for leaving it as prose — *"the trigger would be a generator that joins
one table twice, which does not exist"* — was reading "does not exist **yet**" as "will
not exist". `GENERATE` is step 4 of the
[Target State's flow](../design/target-state.md#flow) and a later Step of this project
builds it, so the trigger fires inside this project's life and the Ledger is where it
belongs. The entry says plainly that nothing in the repository demonstrates the hole and
that the Sub-step paying it owes a probe — the state DEBT-014's date half was in between
2026-08-20 and this Sub-step. `permitted_route`'s docstring already reasoned about the
two-metric case — *"a statement computing two metrics genuinely carries both routes"* —
so the entry is linked from there, where the next person reading that paragraph will meet
it. **No probe was added**, and that is the same call
[DEBT-020's own *Why we deferred*](../debt-ledger.md#debt-020--the-gate-checks-a-metrics-route-and-not-its-certified-filters)
made: adding a shape to a check that has been reviewed and staged is the quiet widening
*"the requested scope is the deliverable"* is about. The ruling's own edits to `route.py`
are docstrings recording what it decided; a probe is new behaviour, and it belongs to the
Sub-step that pays the entry.

**The `resolved` docstring's second half was rewritten.** It said the exception is *"not
cached: a rule that asks twice pays twice, which is the failure path and is the cheapest
thing here to get wrong in the other direction"* — three claims compressed into one
sentence, none of them showing its working. It now says the mechanism (`cached_property`
stores what a property *returns*, and a raise returns nothing), names a statement that
triggers it (`SELECT a FROM no_such_table`), says who pays (nobody: the first rule to
reach the refusal turns it into `unresolvable` and `judge` stops at the first rule that
rejects), and says what the alternative would be (a second, hand-written cache on the
path that ends in a refusal anyway).

**Verification, after the edits.** Every check was re-run in the same session:

```
$ uv run python .claude/scripts/verify_framework.py
  links      1188 links, 943 anchors 56 documents and python files
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly

$ uv run python .claude/scripts/check_language.py
  glossary: 93 registered terms
  proposed terms: 0 · python files scanned: 27 · identifiers: 1701
  abbreviations: 24 registered in the Glossary, 15 exempt, 0 unrecognised

PASS — documents agree with the Glossary and the writing conventions

$ uv run python .claude/scripts/check_warehouse.py
PASS — the star schema matches Glossary Section B and the adapter seam holds

$ uv run python .claude/scripts/check_data_availability.py
PASS — every source is obtainable and every distinction separates

$ uv run python .claude/scripts/check_semantic_layer.py
PASS — every published expression executes against the Warehouse, every figure with a second opinion agrees with it, every registered ambiguity resolves to metrics that exist, and every certified axis names buckets the Warehouse holds

$ uv run python .claude/scripts/check_validation_feasibility.py
PASS — every probe's verdict, every probe's number and every detector's reading is the one this spike recorded

$ uv run python .claude/scripts/check_validation_gate/
PASS — the Validation Gate refuses what it cannot read, what is more than one statement, what is not a read, what the planner expects to scan past the ceiling, what computes a metric the Semantic Layer does not certify, what would carry a Restricted Column into the answer, and what computes a certified metric across a route or over a period the corpus does not certify for it; and it allows every Certified Metric
```

**Every verdict, count and figure in the Verification block above is unchanged**, which is
the evidence that nothing here touched a rule. The route rule's whole block — the three
executed figures, the nine declared verdicts, the two reading tables, the nine per-metric
route lines and both coverage lines — was diffed against the block above and came back
character for character, and so did the tracing rule's eighteen verdicts, its coverage
line, the DEBT-019 line and the Restricted Column rule's coverage line. `check_language.py`'s counts are
printed above where the Verification block showed only its PASS line: **93** registered
terms and **27** Python files, against the 92 and 26 the
[5.3 ruling](#the-nine-sceptical-items-and-one-question--ruled-and-answered-in-this-commit)
recorded — one term added by this ruling, one file added by 5.4's own `route.py`. The
only other thing that moved is the timing line, which prints a different pair of figures
on every run of every session and which nothing compares with anything.

**What this does not settle.** DEBT-020 is still open and is paid in 5.5, not here.
DEBT-021 and EXT-010 are both open, both untouched by 5.5, and neither is demonstrated by
anything that runs. DEBT-008 is still unpaid and still describes an enforcement wider than
the one that exists — the Access Profile's predicate arrives in 5.5, which is the last
Sub-step of this Step.

---
