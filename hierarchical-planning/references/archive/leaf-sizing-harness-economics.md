# Leaf Sizing from Harness Economics (2026-09-04)


When to use: sizing leaves dispatched into a harness with per-loop prompt shaping.
Lesson: size from observed token logs, not task wording; add a wiring leaf when shaping misses loops.
A leaf's context burn is set by the RUNTIME the implementer lands in, not by
the task description. Session case: a "one-line reply fix" leaf class in
meept sat inside a harness where task-scoped agent loops shipped all 75 tool
schemas every turn (schema-mode config was wired only to the primary loop) —
the coder hit 49k/50k conversational tokens on a trivial task before doing
any real work. Task wording said "small"; token logs said the opposite.

## Rule

When a plan tree dispatches implementers INTO a harness whose prompt-shaping
you don't control (schema modes, context firewalls, per-loop catalogs):

1. **Verify harness economics reach every loop type the tree touches.**
   Grep for where context-shaping config is applied (meept:
   `SetSchemaModeConfig` — was called on ONE loop while `createLoop` built
   others). A primary-loop-only wiring is the recurring gap shape.
2. **Size leaves from OBSERVED token logs, not task wording.** Grep the
   harness log for budget warnings ("Approaching conversation token
   budget", quota/token usage fields) from comparable past runs.
3. **Add a wiring leaf when the mechanism doesn't reach all loops.** This
   is a first-class plan child, not a hidden prerequisite — leave the
   "trivial fix" leaves undersized relative to a catalog-heavy loop and
   they die mid-implementation.

## Related

- `references/meept-flat-plan-trees.md` — flat layout + scanner mechanics.
- `references/execution-readiness-audits.md` — architecture-seam audit
  catches UNWIRED mechanisms; this hazard is the same class (mechanism
  exists, wired to one caller only) seen from the sizing side.
