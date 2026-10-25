# Sibling-Executed Forest Reconciliation (worked instance: meept llm-resilience-forest, 2026-09-01)

## Situation

- Forest planned 2026-08-31 (5 trees, 19 leaves), committed as plan docs.
- Execution attempt the next day found **16 leaf commits already landed** from
  sibling sessions: trees 01/04/05 COMPLETE, tree 02 leaves 01+02 landed with
  leaf 03 **uncommitted in the working tree**, tree 03 untouched.
- The forest ROOT master.md tracking table was the stalest artifact: every tree
  still PENDING. Per-tree masters were accurate; the root was not — during
  split execution, nobody owns the root.

## Reconciliation protocol (git-first)

1. `git log --oneline -30` and grep for the tree/leaf naming convention
   ("tree 02 leaf 02"). Commit messages carry the truth; tracking tables lag.
2. Verify scoped suites for claimed-COMPLETE trees against the CURRENT working
   tree (`go test ./internal/agents/...`, etc.) — not against the sibling's
   claims. Subagent self-reports and changelog checkmarks are claims.
3. Do NOT dispatch leaves whose commits exist. Update the forest root master
   tracking table yourself and commit it.
4. `git status` before every dispatch: uncommitted leaf work = owned by a live
   session. Fence those files out of every dispatch context (name them
   explicitly in the "do not touch" list) and mark the leaf HELD in the
   tracking table so the sibling sees your intent.
5. Honor signals the sibling left in tracking notes ("leaf 03 HELD: client.go
   conflict with tree 02 — green-light after tree 02 leaf 03 lands"). They are
   coordination, not noise.

## Pre-commit hook auto-stage hazard (meept)

The 15-check pre-commit chain includes a docs check that, when a commit touches
feature code without docs, asks to generate documentation (aider). In a
non-interactive commit the hook generated `docs/workflows/backfill-evolver-plans.md`,
and the resulting commit (2476137d) landed **6 files when 1 was staged** —
sibling WIP (`cmd/backfill-evolver-plans/main.go`,
`internal/skills/lifecycle/writer.go`) was swept in.

Rule: after ANY commit that passed through a hook that asks questions or failed
mid-sequence, run `git show --stat HEAD` and verify the file list matches your
intent. Check `git status` for auto-staged files before retrying a failed
commit.

## Hung control test = review finding (Go)

Tree 02 leaf 03's control test (`TestAgentLoop_RateLimitErrorStillRotates`)
hung 500 s instead of failing. Diagnosis pattern:

1. Run leaf-written tests BEFORE committing, always with an explicit
   `-timeout` — a hang is a finding, not slowness.
2. Foreground terminal kills at 60 s: use
   `terminal(background=true, notify_on_complete=true)` writing to a /tmp log,
   then `process wait` / grep the log.
3. The panic goroutine dump names the BLOCKED bystander (rewakeConsumer), not
   the spinner. Identify the spinning branch by COUNTING a log line: 44,261
   occurrences of "Rotated to next model after rate limit" = the rotation
   branch never terminates.
4. Minimal repro confirms: the same test minus rotation (`modelRef = ""`)
   terminated in 0.08 s → the bound is missing on the rotation path.

Root cause (pre-existing, in `internal/agent/loop.go` chatWithFailoverRaw): in
the rate-limit branch, the only attempt bound (`attempt >= maxAttempts`) sits
in the "no more models to rotate to" path. A 2-model alias rotates forever —
each `continue` increments `attempt` but nothing checks it on that path.

**Review rule for orchestrators:** in multi-branch retry loops, require a
termination path per branch. A control test whose pass condition is "keeps
retrying" encodes an unbounded loop — assert BOUNDED retries and termination
instead. And never trust a green suite that includes a test which only passed
by being skipped or timed out upstream.

Status at capture: fix designed (consume the retry budget / hard attempt cap in
the rotation path), not yet applied — the file was sibling-dirty at review time
and the fix needs the owner's coordination.

Resolution update (2026-09-02, follow-up session): the fix landed as ce3a4c6e
with the owner's OK — consume `llmBackoff.NextDelay()` before each rotated
retry, return "max retry attempts" when exhausted (same contract as the
no-rotation branch). The control test was amended to assert BOUNDED chatter
calls (>=2, <=10) + termination instead of the unbounded behavior it used to
hang on. Note the test's final assertion could NOT observe RecordAliasFailure
via ConsecutiveFails/CooldownUntil: `RotateToNextModel` zeroes both as part of
rotating, and the bounded run ends right after a successful rotate — assert
the call count instead (RecordAliasFailure is implied by the rotation path's
branch order).

## Verify-before-dispatch applies to subagents too

A dispatch context for a possibly-superseded leaf should say: "this may already
be implemented — `git log -S '<signature>'` first; if the commit exists,
VERIFY against the leaf spec and report, do not re-implement." The 05-01 agent
given this framing correctly made zero changes and returned the commit id + a
spec-compliance audit. Treating a stale dispatch as an error wastes the agent;
treating it as a verification task converts it into the audit you needed
anyway.

## Double-implementation collision → verify-and-fill-gaps pivot

Leaf 04 was implemented twice in parallel: a sibling session committed
3eb6a3e3 (tree closed) while our dispatched subagent was mid-exploration —
and one of its subagents was concurrently editing parked_turn.go under ours.
Our agent detected the collision, restored its accidental overwrite
byte-identical to HEAD, deleted its duplicate test file, and pivoted to
verify-the-landed-leaf + fill-real-gaps. That pivot found a REAL production
gap: `SetParkEventBus` was never wired in the daemon, so park/resume/give-up
events never reached the bus despite docs claiming the wiring existed
(gap-fill committed 51927530).

Rules for the pivot:
1. On detecting the collision: restore any of your edits to the sibling's
   files byte-identical to HEAD FIRST, then re-verify the landed commit
   against the leaf spec.
2. Gaps in the landed leaf are still yours to fix (TDD), scoped to what the
   leaf spec requires — an unwired seam that docs claim exists is a Critical
   finding even though tests pass (tests never reference a missing publish).
3. Report the pivot honestly: what was double-implemented, what was
   reverted, what the net change is.

## Post-completion follow-up execution (F1–F4 close-out)

Fixing a completion report's follow-up items via parallel subagents worked
with three disciplines (full detail:
`../hierarchical-plan-execution/references/forest-followups-session-2026-09-02.md`
— same directory, F3 close-out file):

1. **Trace the actual wait source before de-flaking.** Log-timestamp deltas
   between attempts reveal real backoff steps. The dispatch brief guessed the
   ~90s quota test sat in a quota wait-loop; the cost was actually the
   plain-429 sibling subtest in the same table. Prefer test-only wiring of an
   EXISTING seam (`SetFailurePolicyConfig` was already there, nil-safe,
   unexported-field so production constructors can't set it inline) over new
   machinery — and pin BOTH directions: tiny-config applies AND
   untouched-constructor resolves production defaults (30s/1h/24h).
2. **Port exhaustion needs layer separation + stress-level verification.**
   Layer 1: invocation bound (`TEST_PACKAGE_PARALLELISM` in Makefile, mirrored
   in CI + AGENTS.md). Layer 2: in-test waste (fresh `http.Client` per test =
   fresh Transport pooling keep-alive conns 90s past test end; 27 tests ×
   pools × parallel packages = the multiplier) — shared singleton client with
   MaxIdleConnsPerHost=1 + t.Cleanup drain, and a DialContext retry scoped
   EXACTLY to EADDRNOTAVAIL ("assign requested address" via errors.As through
   net.OpError → os.SyscallError; every other dial error fails fast,
   test-only). Verify the fix at the STRESS setting: a bound that only works
   at the tighter `-p` is untested headroom. Dose-response was the evidence:
   unbounded → 17–23 failures, `-p 4` → 1, `-p 2` → 0.
3. **Residual single failures have two different causes — diagnose, don't
   blanket-fix.** One was a 3s `require.Eventually` window racing a tracked
   goroutine under sweep CPU load (widen the window; condition unchanged).
   The other was a client dial hitting EADDRNOTAVAIL while the server was UP
   (the readiness probe had just connected — don't debug the server when the
   signature is a client dial error).

## User honesty audit: "do they pass because of shitty tests or because the
## underlying failures were fixed?"

After the close-out, the user demanded an honest classification of each fix —
cosmetic (test-only) vs root-cause — and re-verification that the tests still
test correctly. This produced one retraction and one defense:

1. **The Eventually-widening WAS cosmetic and was retracted.** Widening 3s →
   10s lowered flake probability but left the test racing a real
   fire-and-forget goroutine (`l.wg.Add(1)` + `go func` → capture) with no
   synchronization. The deterministic replacement: `loop.Stop()` waits on
   that same WaitGroup, so after it returns the capture is GUARANTEED
   complete — exact assertions, no polling, no timeout. Lesson: before
   widening an Eventually window, look for a WaitGroup/persistence seam that
   converts the async race into a guaranteed wait. A window is a guess about
   scheduling latency; a seam is a guarantee.
2. **The EADDRNOTAVAIL dial retry was defensible and defended with evidence**:
   the failure is the KERNEL refusing a local ephemeral port (machine
   resource state) while the server was demonstrably up (readiness probe had
   connected); the retry is scoped to that exact errno via errors.As through
   net.OpError → os.SyscallError, and 3 consecutive churn runs produced zero
   exhaustion errors — it only fires under induced sweep burst, never in
   isolated runs.

Audit protocol when the user asks this question: (a) classify every test-side
fix as root-cause vs symptom-mask; (b) for symptom-masks, search for a
deterministic seam (WaitGroup join, callback, injected clock) and replace the
poll; (c) for masks that remain, prove the masked condition never occurs
without the induced stress (isolation run ×N) and scope the mask to the exact
signature. Report the retraction as a retraction — the user values the
admission over a defense.
