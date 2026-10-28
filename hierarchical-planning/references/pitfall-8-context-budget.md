# Pitfall 8 - Underestimating Context Budget

When to use: estimating a leaf's context cost at decomposition time.
Lesson: count exploration cost, not just generation cost; use wc -l on the files the agent will need to read.

A leaf that looks like 40K of work but requires reading 30 existing files will blow past 128K. Account for exploration cost, not just generation cost.

## Estimation method (Step 3 detail)

1. **Exploration cost:** count files the agent must read. Tokens = total lines / 3.5.
2. **Generation cost:** estimate new/modified lines from the task specs. Same ratio.
3. **Iteration cost:** ~3x a single test/build run for TDD cycles.
4. **Overhead:** ~15K tokens (system prompt, reasoning, tool I/O).

Total above 110K - split further. Total under 30K - consider merging with a sibling.

## Deeper sizing hazards

- A leaf's context burn is set by the RUNTIME the implementer lands in (schema-heavy harness loops ship all tool schemas every turn) - `references/leaf-sizing-harness-economics.md`.
- Schema-migration leaves need legacy-fixture tests and a live e2e verification task, not just a green suite - `references/schema-migration-leaf-sizing.md`.
- Doc-edit leaves run 30-60K but carry high exploration cost (5-10 sibling docs for cross-reference verification) - see `references/audit-driven-gdd-planning.md`.
- The wall-clock cap (~25 minutes default) kills long leaves regardless of token fit - see SKILL.md "Leaf sizing - the delegation budget".
