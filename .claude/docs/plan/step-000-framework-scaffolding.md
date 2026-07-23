# Step 000 — Development framework scaffolding

- **Status:** done — closed 2026-07-23, awaiting the first commit
- **Goal:** Establish the working agreement and its documents before any
  application code exists, so that every later Step has somewhere to record
  language, state, debt, and decisions.
- **Moves Current State by:** creating the framework itself. No application
  behaviour changes, because there is no application yet.

## Why this Step first

The framework's own rules — flag unregistered terms, record debt at the moment
of the shortcut, keep Current State true — only work if the documents exist
before the first line of application code. Retrofitting a glossary onto code
that already named things is exactly the failure mode this framework is meant
to prevent.

This Step deliberately does **not** design the project. Design requires the
interview, and the interview should happen with the framework already in place
so its output lands in the right documents.

## Sub-steps

### 0.1 — Scaffold the framework ✅

- Python environment: `uv` project on CPython 3.14.4, matching the pin in
  `aminojagh/LLMZC`.
- `CLAUDE.md` — roles, the Loop, the four non-negotiables, document index.
- `.claude/docs/glossary.md` — Process Language populated, Domain Language pending.
- `.claude/docs/design/current-state.md`, `.claude/docs/design/target-state.md`.
- `.claude/docs/debt-ledger.md`, `.claude/docs/adr/`, `.claude/docs/plan/`, `.claude/docs/reviews/`.
- `.claude/skills/` — `planning-a-step`, `closing-a-substep`, `recording-debt`,
  `registering-language`, `writing-an-adr`.

**Verification:** every document referenced by `CLAUDE.md` exists; every skill
has valid frontmatter; `uv run python` resolves to `.venv`.

## Not in this Step

- Any decision about what Veritas does. That is the design interview, which
  gates Step 001.
- `README.md`. It is the public face for Zoomcamp reviewers and cannot be
  written before the problem is chosen.
