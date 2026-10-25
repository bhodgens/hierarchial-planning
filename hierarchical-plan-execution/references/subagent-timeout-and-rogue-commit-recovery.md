# Subagent Timeout & Rogue-Commit Recovery (Pitfalls 47–48)

Session: rebellion-the-game leaf 09 (GUT integration tests), 2026-08-07.

## Pitfall 47: Subagent timeout ≠ no work

A subagent that hits the 600s timeout with 30+ API calls has usually COMPLETED
the work and lost only the final summary. The delegation result line says
`status=timeout, api_calls=38, 600.07s (no summary)` — the summary is gone but
the filesystem may be full of valid work.

**Recovery sequence before re-dispatching:**
1. `git status --short` — what files appeared/modified.
2. `git log --oneline -3` — did the subagent commit against instructions?
3. Inventory the leaf's Files-to-Touch paths (`ls` them).
4. If work landed: keep it, review it in-session, fix failures yourself, commit.
   Zero re-dispatch needed.
5. If the filesystem is empty: re-dispatch (model-503 case below).

Real instance: subagent timed out at 600s / 38 API calls, no summary. The
filesystem showed 4 new GUT test files, a test scene, and 2 production bug
fixes already landed (worldspec_loader `as Array[Dictionary]` JSON cast that
silently emptied city data; auto_save_manager missing `await` on an async
save_game so auto-saves never wrote to disk). Orchestrator reviewed, fixed the
7 failing tests in-session, committed. Zero re-dispatch.

**Corollary — model-503 storm:** when the provider returns HTTP 503 on the
subagent's first calls, it dies in ~30s having done nothing (6 calls, 3
retries, empty filesystem). Re-dispatch is correct there. A 30s/6-call death
and a 600s/38-call timeout look identical in the result line but are OPPOSITES
in what landed — only the filesystem distinguishes them. Check before acting.

**Corollary — parallel audit agent test contention:** When N parallel agents
each try to run the same slow test suite (e.g., Godot headless GUT ~120s),
they contend on the same process/import cache/binary and ALL timeout at 600s
with zero useful output. This looks like the model-503 storm (empty
filesystem, no summary) but the root cause is resource contention, not API
failure. Fix: do not have parallel agents run tests. Run the test suite once
in-session before or after the audit. See
`references/multi-session-stale-tables.md` §Audit-and-Verify Mode and
`references/audit-complete-branches.md` for the correct in-session procedure.

Real instance (2026-08-07): 4 parallel audit agents for rebellion-the-game
all timed out at 600s because each independently ran the same Godot GUT suite.
Switched to in-session audit: same 21 leaves verified in ~10 minutes.

## Pitfall 49: timed-out agents can still be ALIVE and writing (2026-08-16)

A `status=timeout` result can arrive while the subagent's process is still
running and mid-edit. The orchestrator that concludes "it died, nothing
landed" (or worse, "it died AND stopped") then races it: both write the same
files, and the subagent's later write silently replaces the orchestrator's —
detectable only by content the orchestrator did not author appearing in a
file it just wrote (e.g. an equivalent-but-different function signature
replacing yours between write and compile).

**Detection signal:** file size/content drift on a file YOU just wrote —
re-read before patching when any timed-out dispatch targeted the same path.

**Recovery when a collision is detected:**
1. STOP editing the contended file immediately.
2. Read the surviving content; if the subagent's version is contract-correct,
   keep it and reconcile YOUR tests/callers to its API instead of rewriting.
   (Real instance: leaf-04's variadic `EffectiveRange(light, wm, tier...)`
   replaced the orchestrator's 3-arg version; the fix was adapting the
   orchestrator's test file to the variadic form, not re-editing vision.go.)
3. Guard your shared-state work: when the orchestrator must keep editing the
   same package, run `go build`/tests immediately after EVERY write so a
   collision surfaces as a compile error within minutes, not at final review.

**Escalation rule:** two same-session waves of 600s timeouts (interrupted
first wave + timed-out second wave) on a ≤6-leaf tree → abandon delegation
entirely and implement the remaining leaves directly. Real instance
(2026-08-16, rebellion tree 24): 5 dispatches, 5 timeouts; direct
implementation of all 6 leaves (~2.5h with tests) finished faster than a
third re-dispatch round would have. Delegation is a throughput tool, not a
mandatory step — the skill's own "Small foundation leaves in-session" rule
generalizes: when the channel is unreliable, the orchestrator IS the worker.

## Pitfall 48: Subagents may commit despite explicit no-commit instructions

Subagents run with terminal access and sometimes commit anyway. Do NOT revert
working content out of process-purity — that throws away valid tests and real
bug fixes. Instead:
1. `git show --stat <commit>` to review what landed.
2. Keep it if valid; commit orchestrator-side fixes on top as a separate commit.
3. Note the violation in the completion table / changelog so the pattern is on
   record for future dispatches.

Real instance: leaf-09 subagent committed `cc1afc3` ("test: add GUT coverage
for foundation, world-streaming, save-load branches") with 3 valid test suites
+ 2 real bug fixes. Retained; the orchestrator's fix pass (integration suite +
stance-queue fix) committed on top as `dd90d9b`.

## Pitfall 50: Timeout salvage checklist — the stragglers are PREDICTABLE (2026-08-22)

A late-stage timeout (e.g. 1800s, 79 API calls) leaves work that is nearly
done but fails in a small, predictable set of ways. After the Pitfall 47
inventory, run this fixed sequence instead of ad-hoc poking:

1. `go build ./...` first — if clean, the production code is likely coherent.
2. Run the leaf's own packages' tests. Expect exactly two failure classes:
   - **Call-site drift:** the subagent changed a function signature but died
     before fixing its callers (fix: update the call site, usually adding
     trailing nil args).
   - **Test-expectation-vs-behavior mismatch:** the subagent wrote an
     assertion that contradicts how the code actually behaves. Decide which
     is right; often the TEST is wrong (real instance: round-trip test
     expected empty slices to be omitted from JSON — they aren't; omitempty
     only drops the whole map when empty. Fixed the test, added a comment).
3. `go vet ./...` / repo linters BEFORE committing — dead helper functions
   the subagent wrote then abandoned trip U1000-class pre-commit hooks.
   Delete them rather than nolint-suppressing.
4. The subagent also dies before DOCS: GDD spec section, changelog row,
   leaf-status flip. Write those yourself (Rule 1 obligations), then commit.

Full worked example (rebellion tree 28 leaf 02): timeout at 1800s/79 calls
left a complete `internal/venue` package, passing acceptance tests, one
broken call-site in simulation_test.go, one wrong round-trip expectation,
one unused helper, and zero docs. Orchestrator salvage: ~6 tool calls to
green, then docs + commit (`e6f894cd`). Total cost far below re-dispatch.

## Pitfall 51: Dual-stack leaves (Go + Godot in one dispatch) are the #1 timeout cause (2026-08-22)

A leaf that spans BOTH the Go sidecar AND the Godot client reliably blows
the 1800s subagent budget while still in its reading phase — 1800s/37
api-calls with ZERO files written (twice in one session: rebellion tree 30
leaves 01 and 02, identical signature). The subagent reads Go structs, then
GDScript conventions, then test patterns for both stacks, and never reaches
the write phase.

**Rule: never dispatch a cross-stack leaf whole.** Split along the stack
boundary into two dispatches:
1. **Go half** — the WorldSpec data + structs + testify tests, sidecar/ only.
2. **Godot half** — the builder/consumer script + GUT suite, rebellion-godot/ only.

**Pin the interface contract in BOTH dispatch briefs.** The halves meet at
a JSON shape, so the orchestrator must fix it before either runs — write
the exact record schema into each brief (field names, json tags, units,
axis-mapping gotchas like "polygon y is the 3D Z axis"). With the schema
pinned, neither half needs to read the other's code, and they can run in
PARALLEL — the split is a speedup, not just a timeout fix (tree 30 leaf 01:
both halves green concurrently in ~10-25 min vs. a 30-min dead dispatch).

**Dispatch-brief discipline for each half:**
- Name the exact files to read (with line hints) and the exact files to own.
- List the sibling half's forbidden files explicitly ("a parallel agent owns
  day_night_cycle.gd — do not touch").
- Include verify commands verbatim (build + vet + test for Go; import +
  specific -gselect suites for Godot).
- State the JSON contract verbatim in both briefs.

**Verify the seam yourself when both land.** Each half's tests pass in
isolation, but the schema only truly meets when the orchestrator runs the
consumer's suite after both halves are on disk (real instance: leaf 01 —
test_water_bodies.gd re-run after the Go half landed; green meant the
pinned contract held).

**Related pattern — sibling-leaf parallelism within one stack:** leaves
that share NO files dispatch concurrently with file-ownership carve-outs
in each brief (tree 30: shelf leaf + shader leaf + tide leaf in parallel;
each brief listed the other two's files as forbidden). Regressions that
cross owned files are deferred to the orchestrator — the shader leaf's
chunk_content regression waited for the shelf leaf to land. Never let a
parallel agent "quickly regression-test" a file another live agent owns.

