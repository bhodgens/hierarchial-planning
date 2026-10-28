# Ggut test authoring gotchas
When to use: GUT tests written by dispatched leaves.
Lesson: authoring gotchas proven on tree-30.

# GUT Test Authoring Gotchas for Dispatched Leaves (tree-30 lessons, 2026-08-23)

Subagents writing rebellion GUT suites hit the same five traps every
time. Put the relevant one IN the brief — the brief's 2-line warning
saves a full red→green debug loop.

## The five traps

1. **Typed-array literal assignment fails.** GDScript refuses
   `grid.ring_radii = [10.0, 30.0]` when the property is
   `Array[float]`. Always via an explicit typed local:
   `var rr: Array[float] = [10.0, 30.0]` then assign.

2. **`_make_grid()` became a coroutine** the moment it gained an
   `await get_tree().process_frame` (needed so the node's own `_ready`
   settles before internals are driven). Every CALLER then needs
   `await _make_grid(...)` — parse-time "must be called with await"
   errors if not.

3. **Node-under-test `_ready` races manual state.** A ScatterGrid's
   `_ready` awaits a frame then rebuilds from the VIEWPORT camera —
   clobbering whatever the test set up. Fix: settle one frame before
   driving internals (`await get_tree().process_frame` inside the
   maker), and/or `grid.set_process(false)`.

4. **Bare player_controller instances error in-tree** (its `_ready`
   wires cameras/anim children a fixture lacks: "Invalid assignment of
   property 'current' on null instance") — but tree-FREE instances
   break on `global_position`/`get_world_3d()` reads ("!is_inside_tree",
   "!is_inside_world"). Rule: drive state machines on FREE instances;
   every `global_position` in a test-reachable path needs a
   tree-free-safe wrapper (`pos if is_inside_tree() else position`,
   early-return guards on world probes — "no world" reads as a probe
   MISS, which is often the promotion path you want to test).

5. **Autoload bleed into assertions.** The scene's own DayNightCycle
   (or PauseController) keeps writing live state — a tide level
   snapshot taken "before" drifted by 0.7 m between two lines. Fix:
   pin the external writer first (`cycle.pin_tide(0.0)`), THEN sample
   the baseline; unpin in cleanup. before_each dismisses
   PauseController (test_chunk_content.gd pattern).

## Brief snippet (copy into any leaf that ships a GUT suite)

> GUT gotchas: typed Array[float]/[int] literals need explicit typed
> locals before assigning exports; before_each dismiss PauseController;
> add_child_autofree everything; if your maker awaits a frame, every
> caller awaits the maker; player_controller fixtures stay tree-free
> with position-based (not global_position) paths; pin any live
> autoload (tide/weather) before sampling baselines.

## Verification of a subagent's new suite

Orchestrator re-runs the suite VERBATIM before committing — never trust
the child's reported counts alone (one suite reported green while its
maker-helper was a coroutine and 4 tests silently didn't compile into
the run; the re-run caught the count mismatch).
