# GDScript Bulk System Dispatch Pattern

> Session: 2026-07-29, Rebellion game project.
> Task: dispatch 14 parallel subagents to create independent GDScript game
> systems (quest, law, crowd, companion, skills, combat, economy, etc.)
> for branch 12-remaining-systems.
> Total output: 15 files, 5,729 lines in ~5 minutes wall-clock.

## When This Pattern Applies

When a plan branch has 10+ independent leaves, each creating a single GDScript
file with no cross-leaf dependencies, and the target language has no compile
step or pre-commit linter that would block rapid commits.

## Key Differences from Go-Side Dispatch

1. **No mutexio / U1000 lint loop.** GDScript has no equivalent of Go's
   pre-commit analyzers. Pre-commit hooks only check the Go sidecar. The
   commit succeeds on the first attempt.

2. **Rate limits are the main failure mode.** With 10 concurrent subagents,
   3-4 will hit HTTP 429 before producing output. Recovery: check disk for
   partial work, complete missing files directly. Do NOT re-dispatch
   rate-limited agents immediately.

3. **Verification is simpler.** No `go build`. Check with:
   ```bash
   grep -rc 'print(' rebellion-godot/scripts/systems/*.gd  # should be 0
   grep -rnE 'TODO|FIXME|not_implemented' rebellion-godot/scripts/systems/*.gd
   ```
   Then optionally run GUT tests.

4. **Systems are independent — commit per wave.** Don't wait for ALL leaves
   to finish. Rate-limited agents take 10+ minutes to time out. Group
   completed files and commit immediately.

## Workflow

### Phase 1: Dispatch (max 10 concurrent)

Dispatch each leaf with:
- The GDD spec path (tell agent to `terminal cat` it)
- The output file path (`rebellion-godot/scripts/systems/<name>.gd`)
- Explicit requirements (extends Node, signal list, API methods)
- "Do NOT commit. Use DebugLogger not print()."
- "Use terminal cat to read existing files, NOT read_file"

### Phase 2: Monitor disk (not subagent returns)

After dispatching, poll disk every 60-120 seconds:
```bash
ls rebellion-godot/scripts/systems/*.gd | wc -l
for f in rebellion-godot/scripts/systems/*.gd; do wc -l "$f"; done
```

Commit each wave of completed files as they land. Don't wait for all 14.

### Phase 3: Sweep for uncommitted side-effects

After all subagents complete (or time out), run:
```bash
git status --short
git diff --stat HEAD
```

Look for:
- Test files (`tests/test_<system>.gd`) — subagents write these but don't
  always report them
- EventBus signal additions (`scripts/core/event_bus.gd` modified)
- `.uid` files (Godot auto-generates these)

Stage and commit ALL relevant files. This step is critical — see Pitfall 40.

### Phase 4: Complete missing files directly

For leaves where the subagent hit 429 with no output, write the file
directly from the orchestrator's accumulated context. The dispatch context
already contains the spec excerpts and requirements — use them.

**CRITICAL:** Do NOT use `execute_code` with Python f-strings to assemble
GDScript files. The `\\t` escape sequences produce literal backslash-t in
the output, causing parse errors. Use `write_file` directly, or if batching
multiple files, use Python but with real tab characters in regular (non-f)
strings. See Pitfall 29 variant.

## Results from Rebellion Session

| Metric | Value |
|--------|-------|
| Leaves dispatched | 14 (10 concurrent + 4 sequential) |
| Files from subagents | 9 (wave 1) |
| Files from orchestrator | 6 (wave 2, direct) |
| Rate-limit failures | 4 (completed directly) |
| Total lines | 5,729 |
| print() violations | 0 |
| TODO/stub violations | 0 |
| Lost test files caught by git sweep | 5 suites / 96 test functions (crowd 27, romance 11, skill 20, npc_combat 16, fatigue 22) |
| Pre-commit failures | 0 |

## Async Notification Sweep — Processing Late Subagent Results

When subagents complete asynchronously (notifications arriving minutes after
dispatch), each notification may carry test files and side-effects the
orchestrator didn't know about. **Process EACH notification as a mini-commit
opportunity:**

1. When `[ASYNC DELEGATION BATCH COMPLETE]` notification arrives, run:
   ```
   git diff --stat HEAD          # modified tracked files
   git ls-files --others --exclude-standard  # untracked files
   ```
2. If the subagent's main file was already committed (by a prior wave), check
   for test files, EventBus signal additions, or other side-effects.
3. Stage and commit ALL relevant files with a descriptive message.
4. Move to the next notification.

In the 2026-07-29 session, this pattern saved 5 test suites totaling 96 test
functions. Each arrived as a late async notification AFTER the main system
file was already committed. Without the sweep, they would have been lost.

## GDScript Subagent Timeout Recovery (600s variant)

Subagents implementing GDScript leaves can time out at the 600s limit in two
distinct modes. The recovery differs for each:

**Mode A: Timeout AFTER writing files (verification timeout).** The subagent
wrote all source files but timed out on `godot --check-only` or a similar
verification step. GDScript's `--check-only` triggers a full project import
which can take 60+ seconds on large projects — the subagent runs out of time
waiting for it.

Signs: `wc -l` on target files shows expected sizes; `git status` shows new
untracked files. The subagent's `delegate_task` status is `timeout` with
high API call count (30+).

Recovery: verify files directly (grep for TODO/stubs, grep for line-number
corruption), commit them. Do NOT re-dispatch — the work is done.

**Mode B: Timeout WITHOUT writing files (stuck subagent).** The subagent
got stuck early (network stall, provider slowness) and produced zero output.

Signs: target files unchanged or non-existent; API call count is low (under 15).
The `delegate_task` status is `timeout` with <15 API calls.

Recovery: implement the leaf directly from the orchestrator's accumulated
context. The dispatch context already contains the spec excerpts — use them
with `write_file`. Do NOT re-dispatch (will likely hit the same stall).

**Distinguishing the two:** check disk FIRST. `ls -la` on target files +
`git status --short` tells you immediately which mode occurred. If files
exist with expected sizes → Mode A. If files are missing or unchanged → Mode B.

**Sibling-scope bleed:** A subagent implementing leaf N may incidentally
implement parts of leaf N+1 if the work is tightly coupled. When leaf N+1
times out, check whether leaf N's subagent already wrote the needed code.
Example: leaf 01's subagent (animation library) also added sneak walk,
climb sub-states, swim blend, and drunk walk — all traversal states that
were nominally leaf 07's scope. When leaf 07 timed out with a partial write,
the orchestrator checked the state machine and found all traversal states
already present from leaf 01. Only a small prone-crawl improvement needed
committing.

Concrete example (2026-07-30 combat-animation session):
- Leaf 01: Mode A timeout (38 API calls, 600s). All 5 files written (920 lines).
  Orchestrator verified + committed directly.
- Leaf 02: Mode B timeout (10 API calls, 600s). Zero output.
  Orchestrator wrote striking_system.gd (358 lines) directly from context.
- Leaf 07: Mode B timeout. Partial write (1 file, small diff).
  Sibling-scope bleed from leaf 01 had already done the bulk of the work.
  Orchestrator committed the small diff.

When adding IPC handlers to the Go sidecar that unmarshal JSON and apply
state under a mutex lock, the mutexio analyzer flags any `json.Unmarshal`
inside `mu.Lock()`. Fix with a two-phase pattern:

```
Phase 1: decode all sub-objects OUTSIDE the mutex
Phase 2: apply decoded data under mutex (no json.Unmarshal here)
```

Collect all decoded data into a struct (e.g., `overlayRestoreData`), then
apply under lock. This keeps the analyzer happy and is genuinely better
design (CPU work outside lock).

**Concrete worked example:** `sidecar/internal/overlay_handler.go` — the
initial implementation had all `json.Unmarshal` calls inside
`s.state.mu.Lock()`. The mutexio pre-commit hook blocked the commit with 10
violations. The fix introduced an `overlayRestoreData` struct holding all
decoded fields. Phase 1 (outside lock) populates it; Phase 2 (under lock)
applies each field to simState. Clean commit on the first retry.
