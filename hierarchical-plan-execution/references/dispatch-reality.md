# Ddispatch reality
When to use: most repo-leaf subagents die at the timeout.
Lesson: plan for partial returns: checkpoint reports, subset re-dispatch.

# Dispatch reality for leaf subagents (2026-08-17, rebellion tree 25)

Finding: during tree-25 execution, 5 of 5 repo-leaf subagents died —
4 at the 600 s hard timeout, 1 at context compaction. Zero or partial
writes; 3 delivered no report at all; 1 delivered a late report after
the orchestrator had already finished the leaf manually.

Root causes:
1. Leaf specs sized "Estimated Context: 45–60K" assume the subagent can
   hold the leaf + code + test runs. The 600 s ceiling plus compaction
   kills mid-run agents on large leaves.
2. Dead agents leave PARTIAL files silently — one wrote the config and
   the implementation but not the test; one wrote only generators.

Rules adopted:
- After the SECOND dead dispatch on one tree, STOP dispatching repo
  leaves. The orchestrator implements directly — it was faster and the
  tests were green every time.
- On any delegation report (late or on-time), verify disk state first:
  file mtimes, grep for the leaf's key symbols, git diff. Never trust
  "status=completed" or "timeout" alone as a statement of disk truth.
- Non-repo art tasks (image generation on a remote box, small scope,
  no repo writes) remain safe to delegate.
- Subagents must never commit; the orchestrator owns all commits.

When a late report arrives after manual completion: diff its claims
against the verified implementation; only act if it reports something
the disk check missed (e.g. a path typo in its own verifier warning).

## Additions (2026-08-22, agent-orange tree)

- **Continuation dispatch beats restart** when a leaf died mid-TDD: the RED
  phase artifacts (tests, fixtures) survive on disk and are usually good.
  Inspect them, then dispatch one continuation agent scoped to "GREEN phase
  only — do NOT modify existing tests". This recovered a leaf where the first
  agent died after writing tests and the second completed the implementation.
  Inspect the dead agent's partial code first: it may contain a broken
  workaround for a genuinely self-contradictory test spec (fix by splitting
  fixtures — valid entries in one yaml, invalid entry in `<name>-broken.yaml`
  — not by adding leniency to production code).
- **Formatter blast radius**: leaf agents that run repo-wide `ruff format .`
  reformat markdown CODE FENCES inside plans/*.md / docs/*.md (re-indents
  contract blocks, breaks pipe alignment). Instruct every dispatch: scope
  formatters to code dirs (`ruff format src tests`). Orchestrator runs
  `git diff --stat plans/ docs/` before each commit and reverts doc churn.
- **Interrupted-agent debris check**: before trusting anything a timed-out
  agent left, run `pytest -q && ruff check .`. Found an unbound-variable
  half-edit (F821) plus a wrong-exception-type workaround in otherwise-green
  files.
