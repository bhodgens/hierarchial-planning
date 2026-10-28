# Ppost merge review and subagent recovery
When to use: post-merge review + subagent recovery.
Lesson: recovery when a merged tree still has failures.

# Post-merge review pass + subagent failure recovery

Two workflow patterns from the rebellion-the-game rendering-vfx session
(2026-08-07). SKILL.md is at its size cap, so these live here.

## Pitfall 47: Post-merge review pass — "review the full leaf and close the gap"

When a branch/leaf was implemented in a worktree by a different session and
merged with status already marked COMPLETE (or PENDING-but-code-exists), do
NOT trust the merge. The user's explicit pattern (rebellion-the-game,
2026-08-07): "review the full leaf using subagents and close the gap."

1. Read the leaf spec + all implementation files yourself first (find
   suspected gaps with file:line evidence).
2. Dispatch a READ-ONLY review subagent with your suspicions as explicit
   verify/refute targets. Require: file:line evidence per finding, run the
   test suite to get the real baseline, confirm/refute each suspicion,
   find NEW gaps, and recommend exact fixes. Subagent must NOT modify files.
3. Fix the confirmed gaps yourself (small) or dispatch implementers (large).
4. Re-run the full suite, update tracking tables + changelog, commit.

Real instance (leaf 05-environmental-foliage): the merged implementation had
3 real bugs the review caught — a signal-arg mismatch (2-arg handler on a
1-arg signal = runtime error on every emit), a declared-but-never-read
surface gate, and a node leak on reposition (hide+erase without
queue_free). Plus: orphan .tscn assets (unreferenced AND broken), a budget
50x over spec, and an inert alpha-scissor (shader never wrote ALPHA).
Review → fix pass took the leaf from "merged, looks done" to actually done,
tests 15 → 23.

## Pitfall 48: Subagent 503/timeout — check for partial landing before re-dispatching

When a delegation batch fails with upstream HTTP 503s or a 600s timeout, do
NOT assume nothing happened. Check the filesystem FIRST:

```
git status --short
ls <leaf's target directories>
```

Real instance (rebellion-the-game leaves 01/02, 2026-08-07): delegation 1
reported "API call failed after 3 retries: HTTP 503" for both tasks — but
leaf 01's files had ALL landed before the subagent's final summary call
failed (files created, then the summary LLM call 503'd). The work was 80%
done; only verification + fixes were needed. Re-dispatching blind would have
collided with the landed files.

Recovery ladder:
1. Check for partial work (git status + target dirs). If files exist, review
   them as if a subagent returned normally — verify, fix gaps, continue.
2. Only re-dispatch for work that genuinely did NOT land.
3. If the provider keeps 503ing and the remaining work is small (one wiring
   edit + one test file), do it in-session instead of burning a third
   dispatch — "using subagents" was the means, completion is the goal.
## Pitfall 49: GUT test contention — subagents launching Godot headless simultaneously

When multiple code-review subagents each try to run the GUT test suite
(`/Applications/Godot.app/Contents/MacOS/Godot --headless ...`), they
contend for the single Godot process lock. Each GUT run takes ~120-180s.
With 4 agents all trying to run GUT, each hits the 600s timeout.

Real instance (rebellion-the-game, 2026-08-07): 4 review subagents
dispatched to audit branches 01/02/03/05. ALL 4 timed out at exactly
600.06s with only 13-19 API calls each — they were blocked waiting for
Godot, not doing review work.

**Fix:** Tell subagents explicitly: "Do NOT run GUT tests, Godot headless,
or any build commands. Read code, find bugs, fix them, report." The
parent agent runs GUT once after all fixes are applied. This eliminates
the contention and each subagent finishes in ~5 minutes.

## Pitfall 50: Rate-limit cascade — all agents fail simultaneously

When dispatching 4-8 parallel subagents on a large codebase, the provider
may hit HTTP 429 rate limits that kill ALL agents simultaneously (typical:
2 complete with real findings, 6 return "Rate limit reached" after 1 API
call each).

Real instance (rebellion-the-game, 2026-08-07): 8 review subagents
dispatched. 2 completed (branches 01 and 06) with 10 bugs found. 6
returned "Rate limit reached for requests" after 1-3 API calls. Retrying
the dispatch produced the same result — the rate limit persisted.

## Pitfall 51: Timed-out subagents — triage by what's on disk, then finish the missing piece in-session (2026-08-14)

The 600s delegate_task cap fires mid-verification more often than mid-coding. A timed-out
batch almost always left artifacts. Inventory before re-dispatching:

```
ls -la <every promised file>   # mtimes vs dispatch time = written during the run?
```

Three real timeout shapes from one procgen session, each with a different correct follow-up:
1. **Nothing written** (facade task, 11 API calls): the subagent never got past
   reading. → Re-dispatch with a tighter, better-briefed scope.
2. **Code + tests written, tests failing** (street lighting, 20 API calls): the subagent
   ran out of clock mid-fix-loop. → Review failures yourself; some are real algorithm
   gaps (endpoint-only intersection detection missing mid-segment crossings; sparse-fill
   capped at road count) and some are over-strict test expectations (see Pitfall 52).
   Fix in-session — re-dispatching risks a second timeout on the same slow loop.
3. **Implementation written, tests never started** (Stage 1 terrain, 18 API calls — 700
   lines of Go, zero test file): → Write the tests yourself against the delivered API;
   you'll need to read the code closely anyway to review it.

Also sweep for orphan side-artifacts near the target paths: a 3214-line
`gdextension_interface.h` appeared at the Godot project root mid-test-run with zero repo
references (likely a stray download during a subagent test). Flag for deletion — don't
silently keep, don't let it get committed.

**Brief hard-won pitfalls EXPLICITLY in the dispatch context.** Subagents preserve the
public API (it's in the brief) but know nothing about parent-session hotfixes that
postdate their file read. In the same session, a crash-class typed-assignment bug fixed
in street_lighting.gd reappeared in the subagent's later rewrite because the dispatch
context predated the fix. State patterns like "NEVER assign a possibly-freed instance
from a Dictionary into a statically-typed var (use Variant + is_instance_valid guard)"
verbatim in the brief. After every delegation batch, re-grep for the fixed pattern in the
files the subagents owned.

## Pitfall 52: Discrete-grid test expectations vs continuous-math thresholds (2026-08-14)

When writing tests against a grid-quantized algorithm (erosion kernels, distance-decay
sampling, influence maps), clean-math expectations fail against CORRECT code:

- **Mass-transfer kernels** (thermal erosion): moving material to a receiving cell can
  steepen THAT cell slightly (observed +0.0004 rad) even while the aggregate smooths.
  Assert non-increase only within a tolerance (~0.02), or assert on aggregate/mean slope.
- **Distance-decay sampling** (path wear near roads): grid cell centers rarely coincide
  with source points, so peak strength tops out at ~(1 − cellSize/radius)·traffic —
  observed 0.816, not 1.0. Assert >= a realistic bound (e.g. 0.7), never == 1.0.
- **Rebuild-vs-stale checks**: a `queue_free()`'d node remains a child until end of
  frame — a test doing `get_node("Name")` after a rebuild gets the OLD node. Fix in code
  (rename the old node before queue_free), not in the test.

Correct the TEST to the discrete contract; don't patch the algorithm to satisfy
continuous-math expectations — but read the algorithm first to confirm which side is
wrong (the intersection-detection failures in the same session were genuine algorithm
gaps, not test strictness).

