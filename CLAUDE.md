# CLAUDE.md — Operating Agreement

**Veritas** — an end-to-end LLM application. Capstone for the DataTalks.Club LLM
Zoomcamp, and a deliberately minimal slice of a larger system proposed in
`final_proposal_target.md`.

> **Design in progress.** The Glossary's Domain Language is `agreed`
> (2026-07-23). The Target State is written and its terms are settled, but stays
> `proposed` until the data-availability check confirms its sources
> ([Step 001, Sub-step 1.2](.claude/docs/plan/step-001-target-state-design.md)).
> Implementation Steps begin once it is `agreed`.

---

## Environment

- Python **3.14**, managed by **uv**. Always `uv run python …` — never bare
  `python`/`python3`, not even for a throwaway one-liner in a shell pipeline.
- Add dependencies with `uv add`. Never `pip install`.
- Scratch and intermediate files go in `scratch/` (gitignored) or
  `$CLAUDE_JOB_DIR/tmp` — never the repo root.

## Roles

- **Claude** designs, implements, verifies, and writes the Step Review.
- **Amino** reviews and **commits**. Claude never runs `git commit`, `git push`,
  or `gh pr create` unless explicitly asked in that message.

---

## The Loop

One pass through the loop moves the project from Current State toward Target
State by exactly one **Step**. A Step is a vertical slice — it must leave the
project working end-to-end, not half-wired.

```
Target State ──┐
               ├─► plan a Step (1–5 Sub-steps) ─► implement Sub-step ─► verify
Current State ─┘                                        ▲                 │
     ▲                                                  │                 ▼
     └──── update Current State ◄── Amino commits ◄── Step Review ◄───────┘
```

**One Sub-step = one commit.** If a Sub-step cannot be described in a single
commit message without the word "and", it is two Sub-steps.

**Never plan more than one Step ahead.** The Target State is fixed; the route
to it is discovered. Planning Step N+2 before Step N ships is speculation.

**Draw contour lines, not scaffolding.** Move fast by laying the *real*
structural lines of the final design thin — not by building throwaway hacks. A
**seam** (a Glossary name, an interface or adapter boundary, a data contract, the
end-to-end path) is a contour line: get it right now, because everything hangs
off it and moving it later is a repaint. The **fill** behind a seam (the
algorithm, the dataset size, the error handling, a hardcoded value) is where
speed is bought. Debt lives **behind** a seam, never **across** one. The test:
*can this shortcut be repaid without moving a name, an interface, or the flow?*
If yes, take it and log it. If no, it is not debt you may take — draw the line
properly, which is cheap in code precisely because a seam is an interface plus
one trivial implementation. See `recording-debt`.

| Phase | Skill | Produces |
|---|---|---|
| Plan a Step | `planning-a-step` | `.claude/docs/plan/step-NNN-<slug>.md` |
| Close a Sub-step | `closing-a-substep` | Step Review entry + state updates |
| Take a shortcut | `recording-debt` | `.claude/docs/debt-ledger.md` entry |
| Coin/contest a term | `registering-language` | `.claude/docs/glossary.md` entry |
| Make a costly decision | `writing-an-adr` | `.claude/docs/adr/NNNN-*.md` |

---

## The Four Non-Negotiables

### 1. Shared language is never compromised

[`.claude/docs/glossary.md`](.claude/docs/glossary.md) is the single source of truth for every
domain term. Before using a domain noun in a document, a plan, or a **code
identifier**, check it.

- Term is in the Glossary → use it, spelled exactly as registered.
- Term is not in the Glossary → **stop and flag it**. Never silently coin
  vocabulary:
  > 🆕 **TERM PROPOSAL** — `settlement date`: the date cash actually moves,
  > as distinct from `trade date`. Needed to name the column in `fct_trade`.
  > Agree, rename, or reject?
- Two words appear to mean the same thing → flag the collision and resolve it.
  Synonyms are the disease this rule exists to prevent.

Code identifiers must match Glossary terms. A `net_revenue` column and a
`netRev` variable and a "revenue (net)" chart label are three names for one
concept and therefore a bug.

### 2. Shortcuts are recorded the moment they are taken

Moving fast is allowed. Moving fast *quietly* is not. The instant you knowingly
do the cheap thing instead of the right thing, add a
[`.claude/docs/debt-ledger.md`](.claude/docs/debt-ledger.md) entry — in the same Sub-step, before
the Step Review. See `recording-debt`.

Every entry carries a **Trigger**: the condition that forces repayment. Debt
without a trigger is a wish.

**Debt is not the same as an extension.** Debt means the current code is *wrong,
cheaply*, and belongs in the Ledger. An extension means the current code is
*right for this scope* and the full MVP needs more — that belongs in
[`.claude/docs/extension-register.md`](.claude/docs/extension-register.md), with
the **seam** it lands against and a **Readiness** condition instead of a Trigger.
The test: *does the trigger fire inside this project's life?* If it can only fire
after Veritas becomes something else, it is an extension, and filing it as debt
puts a wish on the Ledger and blunts the open-debt count.

### 3. Both state documents are always true

- [`.claude/docs/design/target-state.md`](.claude/docs/design/target-state.md) — where we are
  going. Changes rarely, and only by explicit agreement.
- [`.claude/docs/design/current-state.md`](.claude/docs/design/current-state.md) — what actually
  exists **right now**. Changes every Step. It must never describe intent, only
  reality.

If reality and `current-state.md` disagree, `current-state.md` is wrong and gets
fixed immediately.

### 4. Evidence before claims

Never report a Sub-step as done, working, or passing without having run the
verification command *in that same message* and read its output. "Should work",
"looks right", and "the tests presumably pass" are not verification.

If verification fails and you cannot fix it within the Sub-step, say so plainly
in the Step Review and record it as debt. A failed Sub-step honestly reported is
worth more than a green one that lies.

**Evidence in a document comes from a committed script.** If a check is worth
putting in a Step Review, it is worth committing to `.claude/scripts/`. Never
paste the output of a throwaway inline script into a permanent document: the
reader cannot re-run it, the transcription can be wrong, and a summary count
(*"checked 37 links, 0 broken"*) hides what was actually covered. **Before
writing any new check, look in `.claude/scripts/` for one that already does it** —
`verify_framework.py` already validates document links **and the headings their
anchors point at**, skills, and the interpreter. A review shows the command a reader can run and the output that
command produced, nothing else.

**Citations quote.** Any claim about what another document says must include the
words it relies on. A bare link is not evidence — it is an invitation to assume
the target says what the sentence needs it to say, which is how a real line gets
stretched into support for a claim it never made. Quote it, or do not cite it.

**An exemption is scoped to where it is needed.** A check that excuses something
names the **file** and the **symbol** it excuses, never a symbol alone — an
exemption claimable by writing a magic name is a hole any later file can walk
through, and the directories these checks scan are the directories we keep adding
files to. An unavoidable exemption is stated in the Step Review that takes it,
along with what it still costs inside the file it applies to, because narrowing an
exemption removes the loophole and not the cost.

---

## Session resumption

Sessions reset between Sub-steps. The `.claude/docs/` tree is the project's memory, so a
cold session must be able to resume from the files alone. The contract:

- **`.claude/docs/design/current-state.md` is the entry point.** It opens with a
  **Resume here** block: the active Step, the next Sub-step, and any question
  awaiting Amino. Read it first, every session.
- **The active plan** (`.claude/docs/plan/step-NNN-*.md`) holds the route; the **latest
  review** (`.claude/docs/reviews/step-NNN-*.md`) holds the handoff detail.
- `closing-a-substep` is what keeps this true — it refreshes Current State and
  the Resume-here pointer before handing over. A session that ends without a
  valid Resume-here pointer has left the memory broken.

## Documents

| Path | What it is | Cadence |
|---|---|---|
| [`.claude/docs/glossary.md`](.claude/docs/glossary.md) | Ubiquitous language — domain + process terms | Whenever a term appears |
| [`.claude/docs/design/target-state.md`](.claude/docs/design/target-state.md) | The finished system, in Glossary terms | Rare, by agreement |
| [`.claude/docs/design/current-state.md`](.claude/docs/design/current-state.md) | What is built, honestly | Every Sub-step |
| [`.claude/docs/design/product-brief.md`](.claude/docs/design/product-brief.md) | The full system Veritas is a slice of | Rare |
| [`.claude/docs/debt-ledger.md`](.claude/docs/debt-ledger.md) | Known shortcuts, with repayment triggers | Every shortcut |
| [`.claude/docs/extension-register.md`](.claude/docs/extension-register.md) | What the full MVP needs that the slice deliberately lacks, each with the seam it lands against | Every ADR cost classified *extension* |
| [`.claude/docs/adr/`](.claude/docs/adr/) | Decisions that are expensive to reverse | As decided |
| `.claude/docs/plan/step-NNN-*.md` | The one active Step | Once per Step |
| `.claude/docs/reviews/step-NNN-*.md` | Handoff notes for Amino's review | Every Sub-step |

`README.md` is the public face for Zoomcamp reviewers. The `.claude/docs/` tree is the
working record. Keep them separate — do not turn the README into a changelog.

### Writing conventions

- **Expand every abbreviation on first use in each document**, then use the short
  form freely: "Data Definition Language (DDL)", "Mean Reciprocal Rank (MRR)".
  This applies to domain and technical shorthand alike. The reader of these
  documents is reading them to learn what was decided, and an unexpanded
  abbreviation silently assumes they already know. Terms registered in the
  Glossary are exempt only if the Glossary itself expands them.
- **No unexplained bare numbers.** A figure in a document says where it came
  from, or names the script that produces it.
- **A measurement is dated evidence, never a standing statement.** Any figure a
  later run could refute or resize — a row count, a percentage, a largest-observed
  value, a file size — is written as evidence: **what was measured, on what date,
  under what settings, and the command that reproduces it.** Ideally it
  reproduces; if it cannot, say so, because an unreproducible figure that reads
  like a fact is the worst of the three.
  - **Evidence lives in the Step Review that produced it**, which is dated by
    construction and carries the command. Never in the source code.
  - **Everywhere else refers to it** — a code comment, the Glossary, an ADR, a
    plan. State the **rule and why it exists**, then point at the evidence or at
    the check that prints the current figure. *"differs on nearly every bar —
    `check_data_availability.py` prints how many"* survives the next refresh;
    *"differs on 95.5% of 1,255 bars"* silently stops being true.
  - **Figures fixed by the code around them are definitions, not measurements** —
    a two-year range, the factor of 100 between pence and pounds, `2:1` as the
    smallest split. They stay.

  The reason is that nothing fails when a number in prose goes stale: no checker
  reads comments. The sweep that established this rule found a comment that had
  been false since the traded universe grew, and nothing had noticed.

Check the framework is wired up correctly at any time:

```bash
uv run python .claude/scripts/verify_framework.py
```

It checks structure, not content — that documents exist, links resolve, skills
load, and the interpreter is the pinned one. Whether the content is any good is
Amino's review.
