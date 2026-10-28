# Mmulti session repo hazards
When to use: multi-session repo hazards.
Lesson: hazard catalog: index poisoning, branch flips, table staleness.

# Multi-Session Repo Hazards

Lessons from concurrent-agent work on one repo (meept unified-theming +
loop-economics + oauth-providers, 2026-08-25; llm-resilience-forest
forest-level concurrent execution, 2026-09-01). Read before dispatching on any
repo where other agent sessions or humans may commit concurrently.
Forest-scale sibling concurrency (whole trees landing mid-session, dirty-file
fences, verification-only dispatches, commit-sweep audits) has a dedicated
walkthrough: `references/sibling-forest-concurrent-execution.md`.

## H1: Sweep-by-foreign-commit

Another session's wide `git add` commit can swallow this tree's
reviewed-but-uncommitted leaf files under an unrelated message.

Prevention:
- Commit each leaf with explicit paths IMMEDIATELY after review passes.
  "Reviewed work sits uncommitted" is the exact window where this happens.
- After any surprise commit appears in `git log`, run
  `git show <sha> --stat` and check whether your files rode along.
- If they did: record the real sha in the tracking table with a note
  ("landed in <sha>, swept by concurrent session") instead of re-committing
  duplicates. Do not rewrite the other session's commit.

## H2: External revert of in-flight subagent work

A foreign `git restore` / checkout wiped five files a sibling group was
mid-editing. Detection signals:
- Subagent reports its edits "appeared to revert" mid-task.
- File mtimes cluster at one instant across unrelated files (mass revert).

Recovery: redo mechanical swaps in-session with a deterministic script
(e.g., Python regex over an explicit hex-to-role map) rather than
re-dispatching agents that must re-read everything.

## H3: Dead-subagent detection

Dispatched leaves can die silently (provider 503s, harness restart) and never
deliver a report. Naive `sleep && git status` poll loops then burn hours
(observed: ~4h). Before settling into wait loops:

1. Process liveness: `ps aux | grep -E "[c]laude|[c]odex"` — if only idle
   language servers remain, no agent is working.
2. Disk evidence: `stat` mtimes of the leaf's target files vs wall clock.
3. Decision rule: no writes for >2x expected duration AND no live process =
   failed; take over in-session.

Honor user guidance on wait-vs-take-over, but present the liveness evidence so
the decision is informed.

## H4: Small-subset parallel dispatch for mechanical migrations

When a monolithic leaf stalls or the user asks for smaller units:

1. Partition by exact-file ownership — each agent owns 2-3 named files plus
   their `_test.go`s; siblings' files are listed as forbidden.
2. Precompute the shared foundation IN-SESSION before dispatching (bridge
   helper function, replacement map, package-cycle constraints like
   "models cannot import parent tui"). Agents then do zero design work.
3. Dispatch all partitions simultaneously; verify combined build only after
   the last returns.

Worked example: 17-file TUI color-literal migration split into 4 file-disjoint
agents after the single-leaf attempt died; zero collisions.

## H5: Reconcile found trees before executing

Plans authored by other sessions routinely have accurate CODE with stale
tables, or vice versa. Before dispatching anything on a discovered plan:

1. Grep each leaf's contract signatures (`FlowKind`, `ClaimTick`,
   `AssembleOrdered`, ...) in source.
2. Classify: IMPLEMENTED / IN-FLIGHT (uncommitted WIP = another session owns
   those files — do NOT touch them) / NOT-STARTED.
3. Dispatch only not-started leaves; note in-flight ones as skipped-owned.

Instance (2026-08-25): containment tree's tracking table said all-PENDING
while all 10 leaves were merged and tests green; loop-economics leaves
01/03/05 were mid-edit by another session while 04/06/07/08/10/11/14 were
genuinely unstarted.

## H6: Pre-commit hooks block leaf commits on foreign state (oauth session)

Three distinct blockers hit during leaf commits, each with a proven fix:

1. **staticcheck/U1000 scans the whole STAGED PACKAGE, not just staged
   files.** A sibling's uncommitted test file inside `internal/auth/` failed
   OUR clean commit. Fix trivial findings directly (delete an unused struct
   field or wrapper func — usually 1-5 lines) rather than re-dispatching.
   Never rely on //lint:ignore; some hook configs ignore them.
2. **Interactive pre-commit hooks.** meept's `pre-commit-feature-docs` runs a
   tty `read -p` offering aider doc generation when
   `docs/workflows/<pkg>.md` is missing; piping `n\n` does NOT satisfy it.
   Fix: write the REAL doc and include it in the leaf commit (also satisfies
   AGENTS.md docs requirement). Feature name = raw top-level dir under
   internal/ (e.g. `auth`).
3. **Parallel-session WIP breaks tree-wide builds**, so build-gating hooks
   block every commit. Recovery pattern: move ONLY the offending
   untracked/WIP files to `/tmp/parallel-wip/`, run `go build ./...` until
   clean, commit your exact files, then `mv` everything back byte-for-byte
   and report the restored state. Keep the moved set minimal, named, and
   listed.

## H7: Check the index before EVERY leaf commit

A prior failed commit attempt or another session's wide `git add -A` leaves
foreign files PRE-STAGED in the index; even a correct per-leaf
`git add <paths>` then inherits them. This actually happened: a graphs-only
commit shipped 799 lines of a sibling session's modelstore.go.

Mandatory pre-commit step: `git diff --cached --name-only`; if any path is
not in the current leaf's file list,
`git reset HEAD -- <foreign paths>` before committing. If a sweep already
happened: `git reset HEAD~1` is safe when no one else has committed since
(verify `git log --oneline -1` still shows your sha), then re-stage only
your files and recommit. Never rewrite another session's commit.

## H8: Distinguish subagent hard-death from stall

A subagent returning after minutes with "API call failed after 3 retries:
HTTP 429" produced ZERO files — that's a death, not a stall. Don't
wait/poll; check disk once for partial work (`ls`, grep for the leaf's key
symbol), and if empty implement directly in-session from the dispatch
context you already hold. Contrast with timeout-stalls where files landed
on disk (see subagent-timeout-and-rogue-commit-recovery / Pitfall 25):
those get completed-in-place instead of rewritten.

## H9: Forest execution is baseline recon, not dispatch-first (2026-09-01)

"Implement the full forest" on a forest authored days earlier is a RECON
task before it is an execution task. On meept's llm-resilience-forest the
baseline found: 3 of 5 trees already COMPLETE via 16 sibling commits
(per-tree tracking tables honestly filled in; the forest ROOT still said
all-PENDING), tree 02 mid-flight with leaf 03's edits UNCOMMITTED in the
working tree, and tree 04's leaf 03 marked HELD by the sibling itself
("client.go conflict with tree 02"). Procedure that worked:

1. `git log --oneline -40` + grep per tree name; read EVERY tree's tracking
   table plus the root's. Commit messages are ground truth; tables are claims
   (and the root table is the stalest artifact in the repo).
2. `git status --short` maps the IN-FLIGHT fence: dirty files = sibling's
   active leaf. Build the dispatch order from dirty-file conflicts layered on
   the plan's dependency graph.
3. When a dispatched leaf might already exist, scope the dispatch to
   VERIFICATION ("verify against spec; if implemented and committed, report
   and change nothing") — the correct outcome is a no-op report.
4. Adopt the sibling's own holds: a leaf marked HELD with a stated conflict
   reason stays held until that reason clears.
5. Commit ONLY docs/plan reconciliations from the recon (`git add <the one
   file>`); on this repo an interactive pre-commit docs hook then auto-created
   docs for a sibling's WIP command and swept it into the commit —
   `git show --stat` after every commit, flag foreign riders, never rewrite.

Related: H5 (reconcile found trees), H6.2 (interactive docs hook),
`references/multi-session-stale-tables.md` § Sibling-Session Collision.

## H10: Control tests asserting legacy behavior can HANG, not fail (2026-09-01)

A leaf's control test ("the old branch still rotates") asserted unbounded
legacy behavior. On meept the rate-limit rotate-retry path in
`loop.go chatWithFailoverRaw` spins forever under a persistent 429 with a
2-model alias: rotation always succeeds (ResolveForAlias clears the current
model's cooldown on rotate), the only attempt-cap branch sits in the
never-reached "no rotation" path, so 43k+ rotations ran in 50s until the
harness timeout. The test didn't fail — it hung, panicking in an unrelated
goroutine (`rewakeConsumer` blocked on a channel), which misdirects
diagnosis.

Lessons:
- Write control tests as BOUNDED assertions: "≥N calls AND terminates
  within X" (wrap RunOnce in `context.WithTimeout`), never "repeats
  forever".
- A verification HANG is a candidate real defect on main, not flakiness.
- Isolation-repro technique when the suspect file is fenced (sibling owns
  it dirty): write an in-package `zz_iso<N>_test.go` scratch test — stub
  the failing dependency, inject fast backoff overrides, add a short
  ctx deadline; run `-v` to a /tmp log and grep iteration counters
  (`attempt=N`) to prove unbounded spinning; `rm` the scratch file
  IMMEDIATELY (siblings build/test against the shared working tree).
  Report the confirmed defect and get an explicit user disposition before
  committing anything that depends on the fenced file.

## H11: Bounded-retry fixes need the failure-branch reachable (2026-09-01)

Fixing H10's spin: the obvious patch is consuming the backoff budget
(`llmBackoff.NextDelay()`) before each rotated retry and returning
"max retry attempts" on exhaustion. Three non-obvious details cost several
debug cycles:

1. **State recovery absorbs the terminal error.** `RunOnce` funnels the
   max-retry error through `attemptStateRecovery`, which (state==StateError)
   resets to Idle and returns NIL. So `err != nil` is NOT a valid
   post-condition for the test — the observable bound is the dependency
   call count (chatter calls ≥ N_min and ≤ N_max).
2. **Resolver counters are not observable post-run.** Both
   `ConsecutiveFails` AND `CooldownUntil` are zeroed by
   `RotateToNextModel` itself, and the bounded run ends right after a
   successful rotate — asserting "failure was recorded" via GetAliasHealth
   fails even though RecordAliasFailure ran. Prefer call-count bounds, or
   count log lines from a captured slog handler.
3. **Read the failure branch order before assuming the guard is wrong.**
   The guard was fine but REACHABILITY was the bug (guard inside the
   no-rotation path). The fix belongs on the rotate-success path, which
   changes the test's post-condition per (1) — write the test's
   assertions AFTER the fix shape is known, not before.
