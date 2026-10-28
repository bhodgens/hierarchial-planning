# Pitfall 30 - Survey Existing Implementation BEFORE Decomposing

When to use: creating a plan tree for a project with existing code.
Lesson: dispatch an exploration subagent first to inventory what's built; digest before writing any plan document.

When creating a plan tree for a project with existing code, dispatch an exploration subagent FIRST to inventory what's already built. In one Godot-port session, the `game/` directory contained 1,873 lines of GDScript implementing ~5% of GDD features (core FPS mechanics). Without this survey, the plan would have assumed greenfield development and wasted effort re-specifying already-built systems.

## Pattern

(a) Dispatch a read-only survey subagent listing all source files, reading key implementations, and mapping to GDD features.
(b) Digest findings in-session before writing any plan documents.
(c) Adjust decomposition scope based on what exists (rewrite vs refactor decision).

This prevents the planner from inventing work that's already done or missing critical gaps.

## Related pre-decomposition and pre-dispatch audits

- `references/audit-driven-gdd-planning.md` - exploration subagents for large doc corpora.
- `references/constructor-audit.md` - verify a proposed target component is actually wired into the runtime before planning work into it.
- `references/pre-execution-feasibility-and-citation-audits.md` and `references/post-authoring-audit-trio.md` - post-authoring equivalents (run before dispatch, catch dead seams and drifted citations).
- `references/execution-readiness-audits.md` - failure-class library for auditing prior-session trees.
