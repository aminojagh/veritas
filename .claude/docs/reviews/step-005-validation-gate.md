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
