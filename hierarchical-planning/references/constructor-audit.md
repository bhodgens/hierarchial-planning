# Constructor Audit — Verify Production Wiring Before Planning

**When to use:** When a plan proposes placing logic in a component that looks right structurally but isn't wired into the runtime. Measured 2026-08-30 (quota-reset-resilience tree).

## The Pattern

A component exists in the codebase with the right semantics (rotation, health tracking, etc.) but zero constructor calls in the daemon startup path. Placing feature work there is dead code — the feature will never run.

## Diagnostic

Before writing a plan leaf that targets a specific component, verify it's actually used:

```bash
# Search for construction sites across the daemon path
grep -rn "NewComponentName\|ComponentName{" cmd/ internal/daemon/ pkg/ --include='*.go' | grep -v _test.go
```

If results are empty outside tests, the component is dead. Reroute the plan.

## Real Instance

Plan originally put quota blocking on `ModelBroker` because it has the right rotation semantics. `grep` found zero constructor calls in `internal/daemon/components.go`. The logic was moved to `Resolver` (the live alias-rotation component), leaving only stubs on the broker.

## Mitigation

Add a "wiring verification" step to the plan authoring checklist:

```markdown
## Pre-Dispatch Architecture Verification

1. [ ] Constructor audit: `grep -rn "NewX" cmd/ internal/daemon/ --include='*.go' | grep -v _test` returns hits
2. [ ] Path verification: trace the request flow from user input to component call
3. [ ] Dead code flag: if no hits, reroute to the component that IS wired
```