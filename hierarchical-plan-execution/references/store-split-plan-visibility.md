# Store-split plan visibility (UI dead-end reborn one layer up)

## Pattern

A feature introduces a DEDICATED store (sink) for its artifacts, correctly
keeping them out of a shared store — but the user-facing surfaces (CLI,
RPC handlers, TUI panels) were built around the SHARED store only. The
artifacts become invisible/unapprovable to users. The original dead end
isn't fixed; it's reborn one layer up.

Real case (2026-09-01, meept skill-evolver tree): leaf 01 correctly gave
the evolver a dedicated plans SQLite store so machine plans stop polluting
the repo. But `meept plans list/approve` → RPC `PlanHandler` → shared store
only. Sink plans were invisible and unapprovable — exactly the "approval
dead end" the tree was built to close.

## Detection (check whenever a dedicated store/sink is introduced)

1. Trace the user surface path: CLI command → RPC method → store. Which
   store instance does the handler hold?
2. Ask: can an artifact written to the new sink be (a) listed, (b) read,
   (c) state-transitioned, through that surface? If any answer is no,
   the feature is user-invisible regardless of correct backend wiring.
3. Also check partial-listing bugs: a handler that lists the shared store
   and merges a fallback must dedupe by id and preserve shared-first
   ordering.

## Fix shape that worked

- Handler gains an OPTIONAL fallback (setter, nil-guarded): fallback
  manager for state transitions (approve/reject/confirm), fallback store
  for listing + reads. Shared side keeps priority; fallback consulted on
  miss. State ops try shared first, then sink, surfacing both errors if
  both miss (so genuine not-found still reports honestly).
- Daemon wires the fallback at construction (it owns both ends).
- Regression test covers the four user verbs: list returns the UNION
  (dedup by id), get falls through, state-transition routes to the
  owning store, and the shared-side artifact is untouched by a
  sink-side transition.

## Gotchas hit while implementing

- PlanManager may expose GetPlan/ApprovePlan but NOT ListPlans — the
  store carries listing. Fallback needs BOTH the manager (state ops) and
  the store (listing) as separate injections.
- Stores that store empty strings as NULL (`nullableString`) break
  `WHERE col = ''` filters — seeded fixtures with empty ProjectID
  silently match nothing in list. Seed fixtures with non-empty field
  values matching the query, or the test false-fails.
- Approval flows may legitimately advance state past "approved"
  (approved → executing via Synthesize). Assert "left the initial pending
  state", not an exact state, or the test fights a real behavior.

## Related

- hierarchical-plan-execution → references/adversarial-re-review-of-committed-work.md
  (this defect was caught by the integration-scope reviewer, not the
  per-leaf reviewers — store-split visibility is a cross-leaf concern).
