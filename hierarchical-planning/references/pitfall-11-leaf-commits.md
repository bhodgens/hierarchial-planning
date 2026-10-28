# Pitfall 11 - Leaf Agents Committing

When to use: writing dispatch contexts for implementation agents.
Lesson: implementation agents never run git commit or git add; every dispatch context says "Do NOT commit."

Implementation agents that run `git commit` independently create unreviewed history, cause conflicts when multiple leaves touch nearby files, and break the orchestrator's ownership of subtree state. On shared repos the damage compounds: a leaf commit sweeps sibling sessions' staged work and interleaves with the orchestrator's wave commits.

## Dispatch context boilerplate (include verbatim)

"Do NOT commit. Do NOT run git add. Write code, run tests, report results only. The orchestrator handles all git operations."

## Orchestrator flow (canon C1-Commit)

1. Implementation agent writes code and tests, runs them locally to verify, reports results - but does NOT commit.
2. Review agent checks the implementation against spec + contracts.
3. Orchestrator commits ONLY after review passes: stages the specific files from that leaf (`git add <exact file paths>`), uses a descriptive message referencing the leaf document.
4. Integration commits (after all children in a branch pass) are also made by the orchestrator.

On repos with strict pre-commit hooks, the orchestrator (not the leaf) handles lint-fix loops - see Pitfall 27 and `references/orchestrator-commit-hook-pitfalls.md`.
