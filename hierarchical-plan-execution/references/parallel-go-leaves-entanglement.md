# Parallel Go Leaves in One Repo — Entanglement Protocol

## Context

Multiple leaves of one plan tree dispatched in parallel into the same Go
module (e.g. rebellion sidecar: 7 daily-life leaves touching the same
schedule/resolver/simulation files). Each leaf's "full suite" run sees the
others' half-written code. This reference is the protocol that worked
end-to-end on tree 32 (7/7 leaves, all committed, zero cross-contamination).

## The recurring failure shapes

1. **Cross-agent test races**: leaf 01's suite fails on leaf 03's
   half-written `biphasic.go`; hours later both are green. These are NOT
   your bugs.
2. **Shared-file hunk entanglement**: two agents editing `resolver.go` /
   `simulation.go` — `git add -p` drags sibling hunks into your commit; a
   mid-patch struct collision from a sibling requires repair preserving both
   leaves' fields exactly.
3. **Gate analyzers don't distinguish test from prod**: mutexio blocks any
   call under RLock even in tests (`Registry.Get()` allocates). Pattern:
   snapshot what you need under the lock (copy map values to locals),
   RUnlock, then assert.
4. **Deterministic time-math + quantized wire formats**: when a scheduler
   returns GameTime built by whole-minute rounding, an epsilon smaller than
   the rounding step lets chained calls re-return the SAME instant or lose
   phase (tide model: chained NextLowTide gaps of 12.4167 h vs true 12.42;
   one 0.0167 h collapse to zero). Epsilon must exceed the quantization step.

## Protocol

### Dispatch
- Parallelize only leaves with disjoint file ownership; sequence leaves that
  share a hot file (state machine / resolver) OR instruct the second
  dispatcher's brief with explicit "another agent may be editing X
  concurrently — confine edits to new files + minimal integration points;
  re-read shared files before patching".
- Give each leaf the same rules block: no commit, deterministic, report
  pre-existing failures separately.

### Per-leaf verification (parent review)
- Run ONLY the leaf's named tests first (`go test ./internal/<pkg>/ -run
  "<Leaf>" -short -race`). Sibling reds are noise.
- Then full `go build ./... && go test ./... -short -race`. Fix failures only
  in packages the leaf owns; report others as out-of-scope.
- Read the subagent's summary tail: timeout/no-summary does NOT mean no work
  — check `git status` for its untracked files and run its suite yourself
  before re-dispatching (salvaged two full leaves this way on tree 32).

### Committing under entanglement
- Stage per-leaf file sets EXPLICITLY: `git add <new files owned by this
  leaf>`. Never `git add -p` a shared file when sibling hunks are present —
  let shared-file changes ride with the LAST leaf to land, verified via
  `git diff --cached --stat` immediately before commit.
- Expect transient `.git/index.lock` from sibling sessions committing
  concurrently: wait ~20–30 s, confirm gone, retry. Never delete the lock.
- Pre-commit gate failures caused by sibling WIP (e.g. mutexio trip in their
  test): fix minimally if trivial (snapshot-under-lock pattern) and note it,
  or wait for their completion if structural.
- When a sibling's landed change invalidates your test (e.g. their park venue
  makes your placeholder-skip assertion stale), update YOUR test in a small
  follow-up commit — never revert their feature.

### Latent-shadowing follow-ups
- A leaf that inserts hard-priority blocks inside another system's generic
  window (dawn HUNTING inside WORK hours) may be shadowed at runtime while
  its integration test passes — test time helpers must not truncate
  fractional hours. Log these as follow-up issues rather than patching
  mid-tree; fix after the tree closes.

### Adjudicating sibling style divergence: trace the convergence point (2026-09-05, skill-authoring tree)

One wave produced two skill tools with different error idioms: leaf 02
returned `nil, err` (Go error), leaf 03 returned `tools.NewErrorResult(msg), nil`
(failed ToolResult). During parent review do NOT normalize by taste:

1. Count call sites per idiom in the target package — if both are
   established (381 vs 58 in meept builtin/), both are legitimate local
   conventions, not one leaf's mistake.
2. Trace where the framework CONVERGES them: `Registry.Execute` wraps any
   Go error into `NewErrorResultErr`, so both paths produce identical
   `*ToolResult{Success:false}` for the executor. Identical downstream
   behavior = acceptable divergence; record it in the review note instead
   of burning a re-dispatch cycle on cosmetics.
3. Re-dispatch is warranted only when the divergence CHANGES downstream
   behavior (one style triggers retry/escalation logic the other skips) or
   violates an explicit project convention (AGENTS.md rule, analyzer gate).
