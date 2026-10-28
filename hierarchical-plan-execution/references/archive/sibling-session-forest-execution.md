# Ssibling session forest execution
When to use: sibling-session forest worked example.
Lesson: llm-resilience-forest execution record.

# Sibling-Session Forest Execution (worked example: llm-resilience-forest, 2026-09-01/02)

Scenario: a 5-tree forest (18 leaves) authored in session A; execution began
while TWO sibling sessions were concurrently executing the same trees from
the same repo. Session B (this one) was told "implement the full forest."
Baseline recon showed 3 of 5 trees already COMPLETE, tree 02 mid-leaf with
uncommitted WIP, and tree 03 untouched. Complements
`multi-session-repo-hazards.md`, `audit-complete-branches.md`, and
`stale-tracking-table-audit.md` — this is the whole-forest variant.

## What worked (do this)

1. **Baseline recon before ANY dispatch** — `git log --oneline -25` +
   `git status --short` + read each tree's tracking table. Plan-following
   commit subjects name the tree/leaf ("feat(llm): ... (tree 02 leaf 03)"),
   which makes sibling progress visible at a glance. Re-run recon at every
   wave boundary; the picture changed twice within one session.
2. **Verification-only dispatches are fine and valuable.** When a
   dispatched leaf turns out to be already implemented AND committed, the
   subagent should verify every task/contract/test against the leaf and
   report zero changes — not re-implement. Put this in the dispatch
   context explicitly: "If the target is already implemented and
   committed, verify each task against the leaf spec and report; do not
   re-implement." Three dispatches in this session came back as
   verification passes with zero diffs — exactly right.
3. **Verification subagents catch real gaps.** One verifier found a
   landed config key (`target_429_per_hour`) had zero test coverage →
   small follow-up commit. A verification pass is not a wasted dispatch.
4. **Dirty-file fencing.** The sibling held loop.go / client.go /
   anthropic.go / errors.go uncommitted for hours. Maintain an explicit
   fence list in the dispatch contexts ("Do NOT touch <files>; a sibling
   session owns them") and dispatch only into disjoint surfaces. When a
   planned leaf needs a fenced file, DEFER it: mark HELD in the tracking
   table with the reason, re-check the fence at each wave boundary. The
   dependency graph governs dispatch order, not tree numbering — pull
   conflict-free leaves forward from other trees while a fence holds.
5. **Claim untouched leaves siblings skipped.** The sibling never started
   one leaf; a scoped dispatch (new file + additive config keys + two
   small seams, with the sibling's staged files named do-not-touch) landed
   cleanly. Greed is fine; collision is not.
6. **Reconcile tracking tables at gates, not mid-flight.** Sibling
   sessions commit leaves but often leave the tree's tracking table all
   PENDING (commit subjects are the evidence). The orchestrator reconciles
   in one commit once the sibling goes quiet — never edit a table a
   sibling is actively working under.

## What bit (avoid)

- **Pre-commit hook auto-stage pollution.** A one-file tracking-table
  commit swept in a sibling's WIP because the repo's feature-doc hook
  generated and staged an extra file. ALWAYS `git status --short`
  immediately after every commit in a shared repo and verify the landed
  file list matches intent; if not, note ownership or revert.
- **"Hung test" vs "slow suite."** A full-suite run failing at a 300s
  timeout with the panic pointing at a DIFFERENT test each run is a SLOW
  SUITE, not a hang. Rerun with a much larger `-timeout` before hunting a
  phantom deadlock: the worked case passed in 308s (the cap was 300s).
  Root cause was a landed D8 feature (30s throttle-backoff base)
  exercising REAL sleeps in pre-existing retry-path tests — file a
  follow-up to inject the schedule (the tree's own test rule bans real
  sleeps), do not expand scope mid-execution. Isolate first: passes with
  `-run` but spins in the full suite = contention; spins alone with a
  rotation-style loop = the bug below.
- **A control test written against the OLD (buggy) contract HANGS instead
  of failing.** Real case: the rate-limit rotation loop could spin forever
  (rotation always succeeds with a multi-model alias, so the
  attempt>=maxAttempts guard was only reachable in the no-rotation branch —
  isolated repro: 43k+ rotations in 50s). The new control test asserted
  the old "still rotates" behavior and hung the suite. Fix pattern: bound
  the production path (consume the same backoff budget on EVERY continue
  path, not just the fallback), then assert a CALL-COUNT WINDOW (>=2, <=10)
  instead of unbounded behavior. General rules: a retry loop where any
  branch can `continue` must consume its budget on that path; a test that
  hangs is telling you the production loop hangs too; and a RunOnce-style
  API may absorb terminal errors via state recovery — the call count is
  the observable, not the returned error.
- **60s foreground terminal timeout vs long Go packages.** One 90s test
  makes a bare `go test ./pkg` exceed the foreground cap. Use `-run`
  filters with scoped names for review checks; use
  terminal(background=true, notify_on_complete=true) for full suites; set
  go test's own `-timeout` LARGER than the harness timeout so the failure
  message is go's, not the harness's. If a package's suite legitimately
  exceeds every cap, that itself is a finding (see slow-suite above).
- **Subagents clobber committed files mid-verification.** A verifier wrote
  a fresh test file over the committed one before noticing; recovered with
  `git checkout -- <file>`. The verify-first instruction (item 2) reduces
  this; also have verifiers run `git log -1 -- <file>` before writing.
- **Hook-blocked commits reveal real quality debt.** The repo's
  ignored-error hook blocked a leaf commit over 3 new `_ =` sites. Fix
  them properly (log sql.ErrTxDone at debug; make test setup meaningful)
  rather than nolint — the fixed versions also survived review better.

## Dispatch-context template additions for shared forests

- "Sibling sessions are executing trees N and M concurrently. Do NOT touch
  <fenced file list>. If your target is already implemented and committed,
  verify against the leaf spec and report instead of re-implementing."
- "Use scoped -run test filters; never run the bare package suite."
- "Report the git status of your touched files when done."
