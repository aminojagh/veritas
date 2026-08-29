---
name: closing-a-substep
description: Use when implementation work for a Sub-step appears finished and is about to be handed to Amino, or before claiming any Sub-step is done, working, or passing
---

# Closing a Sub-step

## Overview

A Sub-step is not finished when the code is written. It is finished when it has
been verified, its shortcuts are on the Ledger, Current State is true again, and
a Step Review exists for Amino to read.

**Claude never commits.** Amino commits. Ending this skill means handing over,
not landing.

## The Iron Law

```
NO COMPLETION CLAIM WITHOUT FRESH VERIFICATION OUTPUT IN THIS MESSAGE
```

If you have not run the command and read its output in the message where you
claim success, you have not verified — you have guessed.

## Sequence

Do these in order. Later items depend on earlier ones being honest.

1. **Verify.** Run the Sub-step's verification command from the plan, in full.
   Read the whole output and the exit code. Not a subset, not a previous run.
   Evidence must come from a **committed script**: `uv run pytest` for behaviour,
   `verify_framework.py` for documents. Never transcribe the output of a throwaway
   inline script into the review; the reader cannot re-run it.

   **Under Delivery Mode, behaviour is proven in `tests/` and nowhere else.** No
   new file goes into `.claude/scripts/`; the checks already there are frozen and
   still run. A behavioural claim with no test is not verified.
2. **If verification failed** and you cannot fix it inside this Sub-step: stop.
   Say so plainly, record it, and hand over anyway. Do not quietly reduce the
   claim to something that passes.
3. **Sweep for debt.** Re-read the diff and ask, honestly: where did I do the
   cheap thing? Every answer becomes a `recording-debt` entry now — not later.
4. **Check the language.** Every identifier added in this diff must match a
   Glossary term. Any that does not is either a rename or a `registering-language`
   Term Proposal.
5. **Make Current State true, and repoint Resume-here.** Update
   `.claude/docs/design/current-state.md` to describe the repository as it now is —
   reality only — and refresh its **Resume here** block so a cold next session
   knows the active Step, the next Sub-step, and anything awaiting Amino. This is
   the project's memory; leaving it stale breaks the next session.

   **Add what is now true; the story of how it got there goes to step 6.** Current
   State describes the repository, not the Sub-steps that built it. A passage
   narrating what *this* Sub-step did — what it found, what a figure used to read,
   what changed and why — is a defect in this file even when every word of it is
   accurate, because the review already holds it, dated and with its command. The
   normal shape of this step is **editing the sentence that just became wrong**;
   appending a second one beside it is how the file grows. If nothing true
   changed, change nothing.
6. **Write the review.** Append a `## Sub-step N.M` section to
   `.claude/docs/reviews/step-NNN-<slug>.md`.
7. **Hand over.** Tell Amino what to look at sceptically and stop.

## Step Review section

**Delivery Mode: 40 lines, hard ceiling.** The diff is in git and the behaviour is
in `tests/`; the review exists for what neither of those shows. Do not narrate the
diff, do not re-argue a decision, do not quote a document back. If a Sub-step needs
more than 40 lines to hand over, the extra belongs in an ADR or in a test name.

```markdown
## Sub-step N.M — <title>

**Changed** — 2–4 lines. Intent, not a file list.

**Verified** — the command and its real output, pasted. Trim only passing
noise; never a failure, never a count in place of the lines.

**Debt** — DEBT-NNN references, or `none`.

**Sceptically** — the judgement calls, ranked. Never "nothing"; a Sub-step with
no judgement calls was too small to review.

**Language** — terms added, renamed, or proposed. Or `none`.
```

## Rationalization prevention

| Excuse | Reality |
|---|---|
| "It's a docs-only change, no need to verify" | Run `verify_framework.py` — it already checks links, skills, and paths. Do not hand-roll a second link checker |
| "I'll write a quick inline script to check this" | If it is worth showing Amino, it is worth committing to `tests/`. Check what is already there first |
| "This check doesn't fit pytest, I'll add a check script" | It fits. A check script is a test with a worse runner and no assertion. `.claude/scripts/` is frozen |
| "The reviewer needs the background to judge this" | The background is in the plan and the ADR. The review says what a reader of both still would not know |
| "40 lines isn't enough for this Sub-step" | Then the extra is a decision, and decisions live in ADRs. Or it is narration, and narration is in the diff |
| "The output is long, I'll summarise the count" | A count hides what was covered. Show the command and its real output |
| "I ran it a few messages ago" | Run it again; the code changed since |
| "The debt is obvious from the code" | It is obvious to you today and to nobody in a month |
| "I'll record the debt at the end of the Step" | The Step ends and the memory is gone. Now |
| "Nothing worth flagging sceptically" | You made choices. Name them |
| "This detail matters, so Current State should carry it too" | Current State says what is true; how it became true is the review's. Two copies can disagree, and the shorter one is read more often |
| "It mostly works" | State precisely what does and does not work |
