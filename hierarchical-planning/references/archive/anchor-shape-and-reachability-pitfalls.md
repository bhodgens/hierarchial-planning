# Anchor-Shape and Contract-Reachability Pitfalls (2026-09-04)


When to use: pinned anchors name nested-struct fields or contract points a leaf cannot reach.
Lesson: verify anchor SHAPE and reachability, not just line numbers, before authoring.
Two authoring-time failure classes observed executing the meept
`chat-dispatch-ux` tree. Both were caught by implementing agents (good TDD
discipline), but each cost a deviation round-trip the master could have
prevented.

## 1. Anchor SHAPE, not just line: nested-struct field traps

A leaf pinned "session CWD" to `internal/session/session.go:56`. Line 56 IS
a CWD field — but it belongs to the nested `DetectionContext` struct
(:54-59); the `Session` struct carries it as `DetectionContext *DetectionContext`
(:79). The implementing agent had to deviate (correctly) to
`Session.DetectionContext.CWD` with nil guards. Reading the cited line in
isolation confirms a false anchor: "line 56 is CWD" is true and useless.

**Fix at authoring time:** when a contract cites a struct field, quote the
owning TYPE PATH in the leaf:

```
`Session.DetectionContext.CWD` — DetectionContext at session.go:54-59,
field on Session at :79 (pointer; nil-guard at call sites).
```

Same for function anchors: name receiver + method
(`AgentRegistry.createLoop`), not file:line alone. The implementer verifies
the path, not just the offset. Cheap grep at authoring time:
`grep -n 'type X struct' -A 30 file.go | grep field`.

## 2. Behavioral contracts must state WHERE the guard sits

Contract: "error steps NEVER ReviewApproved." Planned edit: replace the
error-skip block at review_manager.go:150-163. Reality: a `policy.NeedsReview`
false path auto-approves at ~L105 — BEFORE the planned edit site. The
implementer's red-phase test failed with `error step was APPROVED` from the
EARLIER branch, proving the contract unsatisfiable at the planned site. The
fix (hoist the gate above all policy paths) was correct but was an
implementer decision the master should have made.

**Fix at authoring time:** before freezing a behavioral invariant, trace the
full branch order of the target function. If earlier short-circuits exist,
write the leaf's placement requirement explicitly ("this gate MUST precede
the policy.NeedsReview check at ~L105"). If the branch order is uncertain,
write the leaf's tests to assert the INVARIANT (not the edit site) so a hoist
stays in-spec — the implementer owns placement, and the red phase proves
reachability. RED-phase output naming the ACTUAL approving branch is the
diagnostic: read it before assuming the planned site was wrong.

## 3. Same-file contract sites must enumerate the real receiver

Related near-miss from the same tree: master said "wire registry schema mode
beside components.go:1422." At 1422 `c.AgentRegistry` is NIL (constructed at
~2251 inside `if cfg.MultiAgent.Enabled`). The implementer relocated to :2277
— correct, but the master could have verified construction order at authoring
time with one grep. When a wiring contract names a line, also name the
lifetime constraint ("must run AFTER X is constructed at ~Y; nil before").

## See also

- execution-readiness-audits.md (parent skill dir) — the pre-dispatch audit
  pass catches these classes at dispatch time; authoring-time discipline is
  cheaper than audit-time correction.
- references/authoring-pitfalls-from-execution.md — items 1-9, same theme.
