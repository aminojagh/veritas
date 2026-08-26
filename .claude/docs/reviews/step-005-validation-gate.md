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
