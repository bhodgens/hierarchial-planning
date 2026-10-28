# Subagent delegation for Godot/GUT feature work (rebellion 2026-08-14)

When to use: delegating Godot/GUT feature leaves (geometry, shaders, scene wiring, tests).
Lesson: inline the GDD spec text per leaf, expect timeout salvage, and treat lint nits as orchestrator-direct fixes.

Three parallel leaf subagents implemented GDD procgen features; the session
yielded a repeatable orchestration pattern plus concrete pitfalls. Applies
whenever delegating Godot feature leaves (SurfaceTool geometry, shaders,
scene wiring, GUT tests) to background agents.

## Dispatch pattern that worked

1. **Brief from the real spec, not memory.** Read the GDD section first;
   paste the exact contract into the task context (constants, file paths,
   public APIs to preserve, existing test files that must keep passing).
   Include repo layout (Godot project subdir, headless GUT invocation)  - 
   subagents have zero session context.
2. **Pin the exact test command** including the filter flag that works:
   `-gsuffix="<file>.gd"` (NOT `-gtest`  -  see
   godot-runtime-debugging/references/gut-cli-filtering-and-await-pitfalls.md).
   A subagent that "verifies" with `-gtest` burns its whole budget running
   the full 1090-test suite repeatedly and times out.
3. **State the GDScript freed-instance pitfall up front** in every brief
   touching node caches: never assign a possibly-freed instance from a
   Dictionary into a statically-typed local; Variant + is_instance_valid
   before cast. Subagents reintroduce this class every time it is not
   spelled out (it happened even after an in-file fix  -  a subagent rewrite
   clobbered one of four guarded sites).
4. **"Do NOT commit" + report files/test counts.** Keep the parent as the
   integration point; subagent results get reviewed, reconciled, and
   committed by the parent with pre-commit gates.

## Timeout reality

Leaf subagents implementing ~500-line .gd files + test suites hit the 600 s
cap mid-verification roughly half the time (slow API calls, full-suite
accidents). The work is usually ON DISK  -  check before re-dispatching:
`ls -la` the expected files, build/GUT-check what exists, diff against
the brief. This session: 3/3 first-wave subagents "timed out" but 2/3 had
complete implementations; only the missing deliverable was re-dispatched
(single re-dispatch completed in 471 s). Salvage first, re-dispatch second.

## Reconciliation checklist (parent, after results land)

1. **Grep for the known pitfall classes** in every new/modified .gd:
   typed-local assignment from Dictionaries holding nodes
   (`= record.get(`, `= _cache[`);
   `queue_free()` inside `_exit_tree`.
2. **Run each new suite individually** with -gsuffix; do not trust the
   subagent's reported pass counts.
3. **Classify test failures** (algorithm gap vs stale expectation vs flake)
   before patching  -  see
   godot-runtime-debugging/references/freed-instance-dispatch-and-macos-crash-triage.md §5.
4. **Commit only explicit paths** the subagent names plus any .uid sidecars
   Godot generated for new scripts (they appear AFTER the first editor/test
   run  -  easy to miss in the first commit).
5. Update changelog + Implementation Record per the repo's procedural rules
   (AGENTS.md)  -  subagents never do this.

## Concurrency hazard

Parallel subagents running GUT headless suites simultaneously compete for
CPU  -  this widened a pre-existing race into visible crashes (recursive
signal-dispatch aborts; see godot-runtime-debugging crash-triage reference).
If crash reports appear during parallel test runs, suspect load-sensitivity
of a latent bug, not the new code alone  -  and stagger heavy suite runs.
