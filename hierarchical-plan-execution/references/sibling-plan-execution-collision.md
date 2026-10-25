# Sibling-Session Plan Execution Collision

Not hypothetical: meept `docs/plans/llm-resilience-forest/` (2026-09-01/02)
was executed by THREE concurrent sessions — 5 trees, 19 leaves. Every
protocol item below fired for real, and verification of sibling work
surfaced a production infinite-loop bug (fix 1 below) that fresh
execution would have shipped.

## The situation

You begin executing a plan forest and discover sibling sessions are
executing the SAME forest concurrently: leaf-named commits already on
HEAD, other leaves' files dirty in `git status`, and each sibling keeps
its own tracking table (yours goes stale the moment they commit).

## Protocol

1. **Baseline recon (before any dispatch).** `git log --oneline -40`
   matched against every tree's leaf naming; `git status` dirty-file
   inventory. Classify each tree: COMPLETE / IN-FLIGHT (mixed) / UNTOUCHED.
2. **Fence dirty files.** Never dispatch a leaf whose surface overlaps a
   file a sibling holds modified. Re-derive dispatch order from
   (dependency graph ∩ fence), not the plan's phase numbering — trees the
   plan calls "parallel" may be forced serial by the fence.
3. **Verify-then-implement dispatch framing.** When a sibling may have
   landed a leaf mid-flight, the dispatch context says: "if already
   implemented and committed, VERIFY against the leaf spec (checklist
   items, test names, commit hash) and report zero changes; do NOT
   re-implement." 2 of 3 wave-1 subagents correctly returned "already
   implemented, zero changes."
4. **Tracking tables lie.** Siblings commit work without updating the
   plan docs. Reconcile tables from `git log` evidence (commit hash per
   leaf row) and commit the reconciliation as its own docs commit. Never
   read a PENDING row as "work not started".
5. **Claim orphaned leaves explicitly.** Name the owner in dispatch
   context ("sibling did 01-04; you own leaf 05") and instruct collision
   handling ("if the target landed, pivot to gap-fill or abort cleanly").
6. **Forest gates are yours.** Siblings close their own trees but skip
   forest-level gates. Run once at the end: full sweep (adequate timeout —
   see fix 2), analyzers, graphs-check, cross-tree contract check,
   tracking reconciliation, completion report.

## Fixes discovered while verifying sibling work

All four shipped as follow-up commits (70638e01, 9a059393, a6d299e8,
917482ca, 37a68c22):

1. **Bounded retry loops.** The rate-limit branch's `continue` fired
   whenever `RotateToNextModel` succeeded — which it ALWAYS does with a
   2-model alias — so the `attempt >= maxAttempts` guard in the
   rotation-FAILED branch was unreachable: sustained 429 ping-ponged
   healthy models forever (43k rotations / 50s). Rule: if a retry loop's
   continue path can always succeed, the success path must consume the
   retry budget. Test implication: a control test asserting the old
   unbounded behavior HANGS instead of failing — assert bounded call
   counts (min AND max), not error identity.
2. **Real backoff schedules → sweep tests at authoring time.** Landing a
   production policy with real 30s throttle steps silently tripled suite
   wall-clock (internal/llm 308s; a 300s window failed). Fix was an
   EXISTING nil-safe test-only seam (`SetFailurePolicyConfig`; unexported
   field so production constructors can't set it inline). At leaf-
   authoring time, grep the touched package for retry-path tests and wire
   them to the fast-policy seam in the same commit. Add a guard test:
   unconfigured constructors keep 30s/1h/24h.
3. **Full-sweep port exhaustion.** Unbounded `go test ./internal/...`
   (~98 binaries) empties the macOS ephemeral range (49152-65535);
   unrelated packages fail "can't assign requested address" (17 failures).
   Dose-response: `-p 4` → 1, `-p 2` → 0 (twice). Fix: `-p` bound in
   Makefile test targets + CI mirror + failure-signature doc in
   AGENTS.md. Verify the dose-response with ≥2 sweeps before committing
   the number.
4. **Hook-blocked error sites.** Pre-commit rejected blank-ignored errors
   (`_ = tx.Rollback()`). Fix meaningfully — log `sql.ErrTxDone` at debug
   (the blessed no-op-after-commit signal) — never `//nolint`.

## Addendum: inverted collision — YOU are the dispatched leaf, the files already exist (2026-09-05)

meept `phase-frontier-parallel` leaf 01: on arrival, both leaf target files
(`phase_frontier.go` / `_test.go`) were already on disk, uncommitted, written
by sibling session `sa-0-0bbe5738` — so the leaf's RED step (test must fail
to compile) was unobservable from the start, and my first test-file write
raced an in-flight sibling write (tool warned "modified by sibling subagent
but this agent never read it"). The sibling is executing the SAME leaf, not
a different one — the mirror image of the protocol above.

1. **Read the leaf's target files BEFORE writing anything**, even when you
   "own" the leaf. If present and plausible, diff them against the frozen
   contract line-by-line YOURSELF before trusting anything (implementation
   was correct per Contract A; kept as-is).
2. **Write only the file you can own end-to-end.** I authored the test file
   (overwrote cleanly, verified byte-count matches my content) and left the
   sibling's implementation intact — one writer per file, no merge-on-disk.
3. **RED becomes yellow.** When implementation pre-exists, TDD's
   compile-failure RED can't be demonstrated; state that in the leaf report
   honestly rather than faking a RED run. The test iterations still
   exercised real RED→GREEN cycles on expectation fixes.
4. **Verify sibling pre-work against the CONTRACT, not its passing tests** —
   its tests may be absent, different, or wrong; the frozen interface
   contract is the only ground truth.
5. **Flag the collision loudly in the leaf report** (sibling ids, what was
   kept vs. rewritten, what was verified) so the orchestrator can reconcile
   — parallel leaf dispatch on one tree means leaves are NOT trustworthy as
   "untouched territory".
6. **Hygiene rider — typo'd write paths in shared $HOME/git:** one
   mis-typed path (`git/meet` vs `git/meept`) silently created a whole stray
   repo tree; the recovery `rm -rf` was DENIED, so it lingers. Corollaries:
   (a) absolute paths in write_file deserve a glance before submit — a
   one-letter typo is a filesystem event, not a lint error; (b) if cleanup
   of a stray dir is denied, STOP touching it and flag it in the report for
   manual removal — never retry a denied destructive command rephrased.
