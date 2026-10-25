# Parallel Subagent Hazards

Lessons from dispatching 4+ parallel subagents on Godot/GDScript plan-tree leaves.

## Hazard 1: Godot/GUT Headless Test Contention (CRITICAL)

**Symptom:** Multiple parallel subagents each spawn `godot --headless --path game/
-s addons/gut/gut_cmdln.gd`. All processes spin at 100% CPU. Subagents hit the
600s timeout one after another. Even after timeouts fire, orphaned Godot
processes keep running.

**Root cause:** Godot's project import system acquires an exclusive lock on
`.godot/imported/`. When two or more `--headless` processes start against the
same project directory simultaneously, they deadlock on the import lock. Each
process thinks it needs to (re)import assets; neither can proceed.

**Reproduced:** 2026-08-07 rebellion-the-game tree 18 character-asset-pipeline
dispatch. 4 Wave-1 subagents + 2 Wave-3 subagents = 6 concurrent Godot headless
GUT processes. All timed out at 600s. `ps aux` showed 6 Godot processes at
~100% CPU each, none making progress.

**Fix — orchestrator owns ALL engine verification runs:**

1. In the dispatch context for each subagent, add explicitly:
   "Write code and pytest tests ONLY. Do NOT run `godot --headless`, GUT, or any
   engine verification — the orchestrator runs the full suite after all
   subagents return."
2. After ALL subagents complete (success or timeout), run a single GUT suite
   from the orchestrator session:
   ```
   godot --headless --path rebellion-godot -s addons/gut/gut_cmdln.gd
   ```
3. Orphaned Godot processes from timed-out subagents will eventually exit when
   their parent `timeout` wrapper fires. Do NOT `pkill` them without user
   consent — the user denied `pkill -f Godot` in one session. Ask first.

**Generalizes to:** Any engine with a project-import lock (Godot, Unity, Unreal).
The pattern: **one process owns compilation/import/verification; parallel workers
write code and lightweight tests (pytest, go test) only.**

## Hazard 2: Subagent Timeout ≠ Incomplete Work

**Symptom:** Subagent returns `status=timeout` after 600s with 25–59 API calls
completed. Looks like a failure.

**Reality:** In 3 of 4 observed timeouts, all code files were fully written.
The timeout fired during the GUT verification step (Hazard 1 contention), not
during implementation. The subagent wrote everything, then hung trying to run
`godot --headless` alongside 5 other processes.

**Recovery procedure (do NOT blindly re-dispatch):**

1. `ls -la` every expected output file from the leaf's interface contract.
2. If all files exist with reasonable sizes (>500 bytes for scripts, >100 for
   JSON manifests), verify them yourself:
   - `grep -c 'pass$\|TODO\|FIXME\|not_implemented'` on .gd files → expect 0
   - `python3 -m pytest <test_file> -v` on Python tests → expect all pass
   - Spot-check key functions for real implementation (not stubs)
3. If a test file is missing (common — the subagent ran out of time before
   writing the test), write it yourself. Faster than re-dispatching and waiting
   another 600s.
4. If an implementation file is missing or clearly incomplete (stub body, <100
   bytes), re-dispatch ONLY that file with a narrow, specific goal.
5. Update the todo list to reflect actual verified status.

**Decision matrix:**

| Files on disk? | Stubs found? | Tests present? | Action |
|----------------|-------------|-----------------|--------|
| All present | No | Yes, pass | Mark DONE |
| All present | No | Missing | Write test yourself |
| All present | Yes | — | Re-dispatch the stub file |
| Missing | — | — | Re-dispatch the leaf |

## Hazard 3: API Matchup in Tests vs Implementation

When a subagent writes both implementation and tests but you write the missing
test yourself (or fix a failed test), watch for API mismatches:

- Subagent's `trellis_prop.py` used lowercase `"queued"` status; the leaf spec
  said `"QUEUED"`. Tests must match implementation, not spec assumptions.
- Subagent raised `KeyError` not `ValueError` for unknown IDs. Tests must accept
  the actual exception type.

**Fix:** When writing tests for someone else's code, `cat` the implementation
first and match its exact return values, exception types, and key names.

## Hazard 4: Salvage-timeout leaves must be re-verified against the FULL suite, not just their package (2026-08-22)

After salvaging a timed-out leaf (fixing call sites + test expectations),
the subagent's earlier edits to SHARED files may have broken OTHER packages
that it never got to test. Real instance: leaf-02 subagent changed
`buildNPCStates`'s signature in `internal/simulation.go`; `go build ./...`
passed but `go test ./...` failed to COMPILE `internal/simulation_test.go`
(a file outside the leaf's packages). Always run the full
`go test ./... -short -race` after salvage, before committing — a green
package-local run is not sufficient.

## Hazard 5: Concurrent dispatch — exclude in-flight siblings' paths by NAME, not by promise (2026-08-22)

When two subagents run concurrently on adjacent packages (e.g. leaf 03 on
`internal/events` while leaf 05 writes scenarios that might reference
events), "coordinate, don't duplicate" prose is not enough. In each
dispatch context, list the sibling's exact paths as read-only-forbidden:
"DO NOT touch sidecar/internal/events*, sidecar/internal/smarte*, or any
file under those packages." And when a desired scenario depends on the
sibling's not-yet-landed API, instruct the agent to OMIT that case and
note it for the leaf that owns it — never allow placeholder/skipped tests,
which violate the repo's no-stubs policy anyway.
