# Executing a Plan Forest Alongside Parallel Sibling Sessions

Worked example: meept `llm-resilience-forest` (5 trees, 19 leaves), 2026-09-01.
This session was asked to execute the full forest; by the time execution
started, parallel sibling sessions had already landed most of it, and one
sibling was mid-leaf on the tree this session most needed next.

## The situation at execution start (Step 1b in action)

`git log` showed 16 plan-related commits already on HEAD: trees 01, 04,
05 fully executed (tracking tables closed), tree 02 leaves 01-02 landed
with leaf 03 UNCOMMITTED in the working tree, tree 03 untouched (correctly
gated on tree 02). Meanwhile the tree-02 master's tracking table showed
ALL leaves PENDING — the sibling updated plan docs only at tree close,
not per leaf.

Consequences for dispatch:

1. **Trees with sibling activity became VERIFY-ONLY.** Do not re-implement.
   Dispatched leaf agents were given the leaf path PLUS explicit
   "on arrival, check whether this is already implemented and committed
   (git log -- <files>); if so, VERIFY against the spec and change nothing."
   Every such agent returned "already done, zero changes" — correct.
2. **Dirty working-tree files are fences.** client.go, anthropic.go,
   errors.go, loop.go were held uncommitted by the sibling. No dispatch
   context for any other leaf may list those files as touchable, and the
   orchestrator must not patch them either (stale-read hazard plus
   ownership).
3. **Dispatch order follows the live dependency graph, not the plan's
   original numbering.** Tree 03 was gated on tree 02 COMPLETE; tree 02
   leaf 03 was mid-flight; therefore tree 03 dispatch waits, and leaves
   whose files collided with sibling WIP were deferred (tree 04 leaf 03
   touches client.go → HELD, exactly as the sibling's own tracking note
   recorded).
4. **Claim untouched leaves that the sibling is skipping.** The sibling
   was executing tree 02 in order but had not started leaf 05 (adaptive
   pacing, a separate new file with no overlap). This session claimed it
   via subagent with fences against the sibling's in-flight files.
5. **Gate behavior must be negotiated, not assumed.** Tree 04 leaf 03's
   own tracking note said "HELD: client.go conflict with tree 02;
   green-light after tree 02 leaf 03 lands" — the sibling had already
   encoded the coordination decision. Honor sibling-written gates.

## Verification-before-commit on sibling-produced leaves

A sibling's landed leaf is still subject to the same review gates. In this
session, verifying tree 02 leaf 03 before the sibling's own state settled
surfaced a REAL pre-existing bug (unbounded rotation retry in the agent
loop, 43k+ rotations in 50s under sustained 429 with a 2-model alias —
the `attempt >= maxAttempts` guard was only reachable in the
rotation-failed branch). The fix (consume backoff budget before each
rotated retry) was committed separately with the amended control test.
Lesson: "sibling committed it" ≈ implemented, not verified. Run the leaf's
own review checklist; do not assume their gates ran.

Also: sibling tracking tables may be stale in BOTH directions (shows
PENDING when done; would show COMPLETE if a later edit regressed it).
Reconcile the table from git history at gate time, and say so in the
commit message ("tracking reconciled against sibling execution").

## Pre-commit hook interaction with sibling WIP

The repo's 15-check pre-commit hook auto-staged and generated docs for
untracked sibling WIP files sitting in the working tree
(`cmd/backfill-evolver-plans/`, `internal/skills/lifecycle/writer.go`)
when this session committed a single .md file. Result: a commit carrying
foreign work-in-progress under this session's message. Mitigations:

- Before committing, check `git status --short` for untracked files in
  packages the hook's doc-generator might sweep (new cmd/ dirs, new
  workflows). If present and owned by someone else, either coordinate or
  accept-and-flag (record the sweep in your final report; do not rewrite
  history to remove it).
- Never `git add -A` yourself on top of this — the hook can do it for
  you implicitly.

## Verification commands under multi-minute tests

The llm package contains a test that legitimately sleeps ~90s
(TestClientChatRetry honors a 1-minute Retry-After). Consequences:

- Foreground `terminal` calls with the default 60s timeout WILL die
  mid-suite. Use `-run` filters for scoped suites, and run full-package
  verification with terminal(background=true, notify_on_complete=true),
  then `process wait`.
- A test that hangs (not merely slow) shows as a timeout PANIC with the
  blocking goroutine stack in the log — grep the log for the top
  non-test-framework frames to find the spin site.
- During another session's WIP, scoped `-run` filters are mandatory; the
  bare package suite may not even compile while they are mid-edit.

## Coordination summary (what to encode in every dispatch context)

- "A sibling session is executing tree 0N in this repo. Files X, Y, Z are
  theirs — do not touch. If your target is already implemented, verify
  and report instead of writing."
- Orchestrator-side: re-check `git log --oneline -8` and
  `git status --short` immediately before each wave; the map changes
  between waves.
- Update the forest-root tracking table from evidence (git log) at each
  gate, and mark sibling-owned trees IN_PROGRESS with who owns them.

## Follow-up close-out wave (same forest, 2026-09-02)

The completion report's follow-up items became a second dispatch wave —
parallel subagents with fenced surfaces, each reviewed and committed by
the orchestrator:

1. **Slow-suite de-flake via the existing test-only seam.** The llm
   suite's 308s was real sleeps: tree 02's D8 policy made in-loop
   backoff steps genuine 30s waits, and pre-existing retry tests burned
   them on wall clock. Fix used the ALREADY-LANDED nil-safe
   `SetFailurePolicyConfig` seam (unexported field ⇒ production
   constructors cannot inline it) to install a ~1ms fast policy in
   tests — assertions unchanged (throttle still escalates, quota still
   no-short-retries), defaults pinned by a new defaults-untouched guard
   test. 308s → 14s. Lesson: before inventing injected-clock machinery,
   grep for a config seam the tree already shipped; test-only wiring of
   it is a production-safe fix.
2. **Dose-response discipline for resource-bound flakes.** The
   ephemeral-port exhaustion fix went unbounded (17 failures) → -p 4
   (1 failure) → -p 2 (0 failures, twice). The bound that runs clean
   ONCE is not proven; record the dose-response ladder in the fix
   comment so nobody raises the bound back. Full-sweep verification runs
   MUST go to background with notify_on_complete (foreground 60s cap
   false-fails), and expect ONE transient flake per sweep even at a good
   bound (a different package each run) — a test passing isolated right
   after is the confirmation, not a re-dispatch trigger.
3. **A completing subagent may leave an uncommitted companion test.**
   The F3 agent's final verify exposed seam semantics worth pinning
   (defaults-untouched + propagation) in a file it never staged —
   review `git status` after the report, run the new tests, commit
   under your own message if green.

## Three-audit pre-dispatch wave (see hierarchical-planning reference)

Before any implementation dispatch on a freshly-authored forest, three
parallel read-only audits (ownership/parser ambiguity, file:line
citation drift vs HEAD, architecture assumptions vs source) caught 3
design blockers — an unwired hook pipeline the whole tree built on, a
same-name/different-signature method collision, and per-alias state
that couldn't deliver cross-alias semantics. Fixing plan docs pre-
dispatch is minutes; discovering these mid-execution is leaf-rewrites.

## Honesty-challenge close-out (2026-09-02)

The user challenged: "do they pass because of shitty tests or because
failures were fixed? Be honest." Protocol + results live in
`meept-build-troubleshooting` → `references/test-honesty-audit-2026-09-02.md`.
Forest-specific outcomes:

- One orchestrator-side fix WAS cosmetic and got retracted: widening the
  shadow-capture Eventually window 3s→10s still raced the fire-and-forget
  capture goroutine. Replaced with `loop.Stop()` (joins the same WaitGroup
  the goroutine registers on) — deterministic under any load. Retractions
  are reported as retractions; the user values the admission.
- A "flaky test" during the sweep turned out to be a REAL production bug
  (HTTPHook RetryCount=0 → hooks never retry; "after 0 retries" in the
  error message was the confession). Read failing-test error text before
  attributing failures to port pressure.
- Two honesty sweeps followed: repo-wide Eventually count driven to zero
  (each async assertion now deterministic or documented external-I/O),
  and remaining real-sleep tests classified legitimate/defect with fixes
  for the defects (blind 2s WS-subscribe sleep → ack-count barrier).
