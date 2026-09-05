# Step Review — Step 000: Development framework scaffolding

## Sub-step 0.1 — Scaffold the framework

**What changed**

Turned the working agreement you described into documents that can actually hold
it, before any application code exists to contaminate the vocabulary.

- **Python environment** — `uv` project on CPython 3.14.4, matching the pin in
  `aminojagh/LLMZC` so the coursework stack (pandas 3, sentence-transformers,
  streamlit) is known to work. `pyproject.toml`, `uv.lock`, `.python-version`,
  `.gitignore`. No dependencies added yet.
- **`CLAUDE.md`** — roles (you commit, I don't), the Loop, the four
  non-negotiables, the document index.
- **`.claude/docs/glossary.md`** — Process Language populated and settled; Domain
  Language deliberately empty until the design interview.
- **`.claude/docs/design/{target-state,current-state}.md`** — target is a skeleton with
  the Zoomcamp criteria map pre-wired so scoring is a design constraint rather
  than an afterthought; current is populated and honest.
- **`.claude/docs/debt-ledger.md`**, **`.claude/docs/adr/`** (README + template),
  **`.claude/docs/plan/`**, **`.claude/docs/reviews/`**.
- **`.claude/skills/`** — `planning-a-step`, `closing-a-substep`,
  `recording-debt`, `registering-language`, `writing-an-adr`.
- **`.claude/scripts/verify_framework.py`** — makes the framework's structural promises
  checkable instead of aspirational.

**Verification**

```
$ uv run python .claude/scripts/verify_framework.py
  skill ok   closing-a-substep       513 words
  skill ok   planning-a-step         564 words
  skill ok   recording-debt          665 words
  skill ok   registering-language    564 words
  skill ok   writing-an-adr          592 words
  python     3.14.4                 /home/amino/Projects/veritas/.venv/bin/python3

PASS — framework is wired up correctly
```

First run failed with 2 problems: my checker demanded every skill description
open with the literal string `Use when`, and two of them open with `Use at the
moment of…` and `Use before naming…`. I changed the **checker**, not the
descriptions — normally a smell, so it is called out here for you to overrule.
The reasoning: the rule that matters is *"a description states triggering
conditions and never summarises its own workflow"*; the `Use when` prefix was
only a proxy for it, and for those two skills the timing and ordering words are
the sharper trigger. Both are the skills where *when* you invoke them is the
entire point.

**Deliberately left undone**

- **DEBT-001** — nothing mechanically enforces any of this. Hooks could block
  `git commit`, or run the verifier on Stop. Deferred because the rules are
  untested and hooks would harden guesses; several of these rules will likely
  turn out to be wrong once they meet real work. Trigger is the first observed
  breach.
- `README.md` — cannot be written before the problem is chosen.
- Domain Language and Target State — gated on the interview, by design.

**Look at this sceptically**

1. **Five skills may be four too many.** Skills compete for attention, and a
   skill that never fires is dead weight. My guess is `recording-debt` and
   `registering-language` will earn their place because they fire mid-task, and
   `writing-an-adr` may not fire often enough to be worth its slot. Worth
   revisiting after Step 002.
2. **"One Sub-step = one commit" will chafe.** The "no *and* in the commit
   message" test is crisp but strict; genuine vertical slices sometimes need
   two things at once. I would rather start strict and loosen with evidence.
3. **Framework docs originally lived at `docs/`, not under `.claude/`.** I read
   the state and design documents as genuine project artefacts worth surfacing —
   a reviewer reading this repo sees an ADR log and a glossary, itself
   evidence for the role. *Resolved 2026-07-23:* Amino chose to keep the whole
   working record under `.claude/`, so it now lives in `.claude/docs/` with only
   `CLAUDE.md` at the root (where Claude Code auto-loads it). See the closure
   note below.
4. **The Glossary claims authority over code identifiers.** That is real DDD and
   it has teeth: it means renaming a concept means renaming columns. For this
   project I think that is a feature rather than a cost, since the product is
   likely to *be* a semantic layer — but it is a commitment worth making
   deliberately.
5. **`current-state.md` is maintained by hand and will drift.** It is the
   document most likely to quietly become false, and DEBT-001's hook idea is the
   real fix.

**Language**

Registered nine Process Language terms, all `agreed`, all describing the
framework rather than the problem: Target State, Current State, Step, Sub-step,
Debt Ledger, Trigger, Step Review, ADR, Term Proposal.

No Domain Language yet — that is the interview, and registering domain terms
before agreeing what the project *is* would be exactly the failure the Glossary
rule exists to prevent.

---

## Closure — 2026-07-23

Step 000 is closed and ready for the first commit. The two open review items are
resolved:

- **Skill-description checker:** kept broadened — a description may open with
  "Use when / before / at / after", so `recording-debt` and `registering-language`
  keep their sharper timing triggers. The rule that matters is "trigger-only,
  never a workflow summary"; the exact opening word was only a proxy for it.
- **Framework layout:** `.claude/docs/` and `.claude/scripts/` now hold the
  working record and its tooling; `CLAUDE.md` stays at the repository root so
  Claude Code auto-loads it. Every reference and link was repointed, and
  `.claude/scripts/verify_framework.py` passes from the repo root.

Non-blocking observations above (five skills may be too many; one-Sub-step-one-
commit strictness; Glossary authority over code; current-state drift) are left
standing — revisit with evidence, not pre-emptively. DEBT-001 remains open by
design.
