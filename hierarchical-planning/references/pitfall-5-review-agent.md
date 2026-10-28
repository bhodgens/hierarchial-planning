# Pitfall 5 - Skipping the Review Agent

When to use: tempted to mark a leaf REVIEWED or COMPLETE without review.
Lesson: always review before marking; unreviewed gaps propagate upward and integration fails catastrophically.

Without review, incomplete work propagates upward and integration fails catastrophically. Always review before marking REVIEWED or COMPLETE.

## Protocol

- Review happens at EVERY level, performed by the orchestrator (main model) in-session - NOT via delegated subagents (canon C1-Review). Delegated reviewers inherit `delegation.model`: the same subagent model that wrote the code would grade it.
- Read the changed files, verify interface contracts, run tests, check for artifacts.
- On gaps: re-dispatch with specific feedback, re-review, loop (max ~3 iterations).
- The parent determines completion - never the child. Implementation status is tracked ONLY by the orchestrator.

Full in-session review procedure: the `hierarchical-plan-execution` skill. Local-model rationale: `local-ravenx-review-pipeline` skill. Post-authoring review variants: Dual-Track Review (SKILL.md Review Protocol) and Pitfall 24 (pre-implemented trees).
