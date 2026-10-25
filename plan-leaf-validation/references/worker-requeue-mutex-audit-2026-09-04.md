# Worker + queue requeue/park audit (auditor E, 2026-09-04, meept)

Scope: `internal/worker/worker.go` (requeue path, mutex discipline, FSM), `internal/queue/store.go` (Requeue park, Fail/Retry txns, claim gate), `queue.go` (Requeueable), `cluster_queue.go` (heartbeat/sweeper interaction). Follow-up on tree 03 leaf 03 (provider-wait requeue, D9).

## P0 found + fixed: mutex leak on the provider-wait requeue return

- `tryProcessJob`: the D9 requeue branch (`requeueOnProviderWait` true) did `return true, nil` while still holding `w.mu` (locked at the `w.CurrentJob = nil` span) and with the FSM parked in `StateProcessing`. Two stacked failures:
  1. The very next run-loop poll, plus `Stop`/`GetState`/`GetStats`/`GetCurrentJob`, deadlock on the held lock.
  2. Even after unlocking, nothing ever fires Processing→(Complete|Error|Stopping), so the worker can never claim again — permanent starvation.
- Why the existing tests missed it: each requeue test calls `tryProcessJob` exactly once and never touches worker state afterward; the run loop is never started. A branch that returns mid-lock-span with state mutated is invisible to call-once tests.
- Fix (landed in main tree): mirror the success path — `setStateWithJob(StateComplete, job.ID)` (Processing→Complete is valid per ValidTransitions; the next `tryProcessJob` resets Complete→Idle), then `w.mu.Unlock()`, before `return true, nil`. Regression test: `internal/worker/worker_requeue_mutex_regression_test.go`.

## Technique: TryLock as a deterministic lock-leak probe

Immediately after the suspect call, `w.mu.TryLock()`: false ⇒ leaked. No hangs, no timing flake — a plain second `Lock()` would deadlock the test instead of failing it. Pair with an FSM assertion (state must not be Processing/Claiming after the call) to catch the starvation half of the bug even if the lock were released.

## Audit rule: enumerate every early return inside a Lock/Unlock span

For every `Lock()` in an audited function, check EVERY return path between it and the matching `Unlock` — especially branches added by later leaves (the requeue branch was leaf-03 vintage inside leaf-original code). `defer Unlock` and the happy-path unlock do not cover mid-span returns. All other lock sites checked this session were sound (`defer`-based, or BEGIN IMMEDIATE transactions in store `Fail`/`Retry`).

## Verified sound (do not re-flag)

- `Store.Requeue`: single atomic UPDATE (`state IN ('failed','claimed','processing')`), retry_count untouched, interactive preserved via `interactive = interactive`, claimed_by/error/result cleared. `next_retry_at` IS the leaf contract's NotBefore: the claim query's `next_retry_at <= now` gate enforces the park (both the SQL fast path and the cancel-filter slow path honor it). WHERE covers the post-`MarkProcessing` `processing` state.
- `Fail`/`Retry` use BEGIN IMMEDIATE for their read-modify-write (concurrent Fail calls can't both pass the retry check).
- Wiring: daemon workers get the plain `PersistentQueue` (`components.go` ~:1978); `ClusterQueue` embeds `Queue`, so the `Requeueable` type-assertion still succeeds in cluster mode.
- Minor (documented, deliberately not fixed): requeue leaves a stale `timeout_at` + `ClusterQueue.claimed` record behind; the later stale-claim sweeper fires one spurious reclaim event that is a store-side no-op (job already pending) plus a bus event. Harmless.

## Multi-session hazard: sibling WIP breaks the build mid-audit

A parallel agent's uncommitted `internal/llm` edits (`fmt.Fprintf(sb, ...)` on a value `strings.Builder`) broke the whole repo build, blocking `internal/worker` tests. Protocol used:

1. Confirm the dirty files are the sibling's, not yours (`git status` + `git diff`); do NOT revert or patch their files.
2. `git worktree add /tmp/<repo>-audit-<id> HEAD` — build + targeted tests runnable there at a clean HEAD.
3. Apply the fix in the MAIN tree; copy the fixed file(s) into the worktree; run the full suite there (`-race`); `diff -q` main vs worktree copies for byte parity; remove the worktree.
4. Re-check the main tree once the sibling commits (`go build ./internal/...` green again) and re-run the audited packages in place as final confirmation.

(Extends the fix-session verification bar: interleaved worktree audits are valid only against their own HEAD — here the worktree's job is to make tests RUNNABLE when the main tree cannot compile through no fault of yours.)
