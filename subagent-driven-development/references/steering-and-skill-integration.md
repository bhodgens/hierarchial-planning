# Continue Steering and Skill Integration Map

When to use: the user says "continue implementing/fixing X using subagents", or you need to know which companion skill governs a sub-phase of the loop.
Lesson: "continue" is a blank check for one more wave - assess done-vs-remaining, pick the next logical item, dispatch; and route specialized sub-phases (planning, TDD, debugging, final review) to their owning skills instead of restating them.

## The "Continue" steering pattern

When the user says "continue implementing", "continue fixing", or "continue with X using subagents":

1. Assess what is done vs what remains - check git log, test status, and the plan's scope (see `references/plan-verification-and-resume.md` for the status-check protocol).
2. Identify the next logical work item - even if previously marked "out of scope". When the original plan is complete, "continue" means the deferred items: integration wiring, low-priority findings, follow-up features.
3. Dispatch subagents to do it - the user said "using subagents" because they want parallelism, not serial parent-agent work.
4. Do not ask for clarification unless there is a genuine fork (e.g. River worker vs CLI tool vs HTTP endpoint). If it is just "what should I work on next", figure it out from plan/state and proceed.

Strong opinions, loosely held: the user trusts the agent to scope correctly and will redirect if needed. Each "continue" authorizes one more wave - use it fully.

## Integration with other skills

- writing-plans: this skill EXECUTES plans that skill creates (user requirements -> plan -> working code).
- hierarchical-planning / hierarchical-plan-execution: for features too large for one agent's context, those skills own the plan-tree structure, orchestrator/reviewer split, and per-leaf dispatch. SDD covers flat, per-task dispatch.
- test-driven-development: implementer briefs embed the TDD cycle (failing test, minimal implementation, verify pass, no regressions).
- requesting-code-review: the two-stage in-loop review IS the code review; for the final integration review, use that skill's review dimensions.
- systematic-debugging: when a subagent hits bugs mid-implementation - root cause before fix, regression test, resume.

## Handling issues in the loop

- Subagent asks questions: answer clearly and completely; provide additional context; do not rush them into implementation.
- Reviewer finds issues: implementer (or a new one) fixes; reviewer reviews again; repeat until approved - never skip the re-review.
- Subagent fails a task: dispatch a new fix subagent with specific instructions about what went wrong; do not fix manually in the controller session (context pollution).
