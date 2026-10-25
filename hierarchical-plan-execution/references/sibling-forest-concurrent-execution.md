# Sibling-Session Concurrent Forest Execution

Executing a plan forest when OTHER sessions/worktrees are running the same
or adjacent trees. The orchestrator's Step 1.5 (already-implemented check)
covers stale plans; this covers LIVE concurrent execution.

## Baseline recon (before every wave, not just the first)

1. `git log --oneline -15` + `git status --short` before dispatching.
   Sibling commits are recognizable by message convention:
   `feat(scope): ... (tree NN leaf MM)`.
2. Match commits against the tree's tracking table. Tables go stale — a
   tree whose leaves all have matching commits is COMPLETE even if the
   table says PENDING. Reconcile the root table (don't trust it either
   direction).
3. Working-tree dirty files are a sibling's IN-FLIGHT leaf. Fence them:
   every dispatch context that could plausibly touch those files gets an
   explicit "Do NOT touch <file list>" rule, and test commands are SCOPED
   (`go test ./pkg/ -run 'TestPrefix' -count=1`) instead of package-wide
   suites that would compile or run against sibling WIP.

## Dispatch-order implications

- The dependency graph still governs, but "landed by sibling" counts as
  COMPLETE for gating downstream trees.
- A leaf that must touch a sibling-dirty file gets HELD in the tracking
  table with the conflict reason (e.g. "held: client.go conflict with
  tree 02; green-light after tree 02 leaf 03 lands"). Do not dispatch
  into a file another agent holds dirty.
- If a leaf you dispatched returns "already implemented, zero changes",
  that is a SUCCESS of the pre-dispatch check, not a wasted dispatch —
  verify the sibling commit exists, mark COMPLETE with that hash, commit
  nothing.

## Pre-commit hook sweep hazard

Shared-repo pre-commit hooks may auto-generate files mid-commit (doc
stubs for undocumented features, formatter rewrites) and can sweep
staged/working sibling WIP into your commit. After EVERY orchestrator
commit run `git show --stat HEAD` and verify the file list matches the
intended leaf scope. If a hook pulled in sibling WIP or generated docs
for the sibling's feature, note it in the tracking table rather than
rewriting history.

## Control tests that assert legacy behavior can HANG, not fail

If a leaf adds a control test asserting the PRE-change behavior, and that
behavior was an unbounded loop, the control test spins past the test
timeout instead of failing cleanly. Worked example (meept, 2026-09-01):
`TestAgentLoop_RateLimitErrorStillRotates` asserted rate-limit
rotate-and-retry; with a 2-model alias, rotation always succeeds, the
attempt-cap branch is unreachable, and the test hit 43k+ rotations in 50s
before the harness timeout. Prefer bounded assertions ("≥2 calls AND
terminates within X") and treat a verification hang as a possible REAL
pre-existing defect on main, not just flakiness.

## Isolation-repro technique for hangs in dispatch-owned files

When a test hangs and the suspect file is fenced (sibling-owned), prove
the defect with an in-package scratch repro instead of editing the fenced
file:

1. Write `zz_iso<N>_test.go` in the same package: stub the failing
   dependency, inject fast backoff/clock overrides, add a short
   `context.WithTimeout` as a safety net.
2. Run with `-v` into a `/tmp` log; grep for iteration counters
   (`attempt=N`) to prove unbounded spinning vs bounded retries.
3. `rm` the scratch file immediately. Never leave scratch test files in
   a shared repo's working tree — siblings will build/test against them.

Report the confirmed defect to the user and get an explicit disposition
before committing anything that depends on the fenced file.
