# Godot 4.7 Headless + GUT Testing Pitfalls

Hard-won from rebellion-the-game plan-tree execution (2026-08-07: leaves 09,
04, 03 across three branches). Every item below cost real debug cycles — check
them before dispatching or reviewing Godot test work.

## 1. Autoload pause state kills physics (the #1 silent failure)

A PauseController / main-menu autoload commonly starts `get_tree().paused =
true` (game begins in menu state). Player `_physics_process` often early-
returns on `get_tree().paused`, so EVERY movement/clock test measures 0.
Symptom: distances 0.0, clock `12.0 -> 12.0`, "sprint never engages".

Fix (in tests): before physics-dependent asserts, call
`get_node('/root/PauseController')._dismiss_main_menu()` or set
`get_tree().paused = false`, then await one frame. This is NOT a test bug —
it is how the shipped game boots.

## 2. Timing: physics_frame loops, NOT create_timer

Headless runs uncapped FPS, so `await get_tree().create_timer(1.0)` accumulates
far more than 60 physics ticks — measured distances overstate by ~5x. Use:

```gdscript
for i in range(N):
    await get_tree().physics_frame
```

For gait/speed asserts, wait ~120 physics frames for velocity CONVERGENCE —
the first frames ride the spawn-fall spike (probe: max hspeed 15.9 during
fall, settled 1.4385 ≈ SPEED_WALK 1.4 at 60Hz). Assert `player.velocity`
magnitude (zero Y) against the constant, not distance-over-frames.

## 3. `const` preloaded resources are deeply immutable

`const WEAPON := preload("res://weapon.tres")` then `WEAPON.last_fired = -1000`
is a PARSE ERROR ("Cannot assign a new value to a constant") even though the
property is a plain `var` on the resource. If a test must mutate shared
resource state (ammo, reload, cooldown), declare it `var` at script scope:
`var weapon: WeaponData = load("res://weapon.tres")`.

## 4. `_ready` that adds grandchildren fails on mid-frame instantiation

If a scene root's `_ready` adds children, and a child's `_ready` adds ITS own
children onto the root (e.g. FootstepSystem adding a RayCast3D + an
AudioStreamPlayer3D pool onto the player), then a mid-frame instantiation
(GUT `add_child_autofree`, dynamic spawns) fails with:
"Parent node is busy setting up children, add_child() failed. Consider using
add_child.call_deferred(child) instead."

Fix (production): defer the whole setup from the child's `_ready`:
`_setup_raycast.call_deferred()` etc. This also prevents same-frame-free
orphans (the old "direct add" comment was fighting a different symptom).

## 5. Threaded-loader deferred callbacks race teardown

A loader that reads a file on a Thread and returns via
`call_deferred("_on_load_success")` will fire AFTER the node is freed when a
test tears down mid-load → "Attempted to free a locked object (calling or
emitting)" at GUT autofree. Fix (production): every deferred handler starts
with `if not is_inside_tree(): return` — dropping the result when the node
is gone is correct, not an error.

## 6. Godot 4 API renames that invalid .tres/test code silently tolerates

- ArrayMesh has NO `get_triangle_count()` (removed in Godot 4). Verify
  surfaces instead: `array_mesh.get_surface_count() > 0` and
  `surface_get_arrays(0)[Mesh.ARRAY_VERTEX]` non-empty.
- Environment SDFGI: the property is `sdfgi_cascade0_distance` (NOT
  `sdfgi_cascade_0_distance`), plus `sdfgi_cascades` (count) and
  `sdfgi_max_distance`. The engine COUPLES them:
  `sdfgi_max_distance = sdfgi_cascade0_distance × 2^cascades` — setting
  cascade0=64 then max=512 silently re-derives cascade0 to 32. Set
  cascade0=64 + max=1024 for 4 cascades.
- `sdgi_enabled` is a typo — the real property is `sdfgi_enabled`. Invalid
  .tres properties are SILENTLY IGNORED (no error), so typos ship invisible.
- Probe real property names before authoring resources: a tiny SceneTree
  script that prints `env.get_property_list()` filtered by prefix beats
  guessing (this caught the SDFGI coupling in one run).

## 7. Stance/state-machine recursion drops the final leg

`_request_stance_change(STAND->PRONE)` recurses through CROUCH, and the
recursive leg sets `_is_transitioning_stance` — the SECOND `_request_stance_change`
call bails on that flag, so the player ends stuck in CROUCH. Fix (production):
queue the second leg (`_stance_queue`) and fire it from the transition
completion. Tests that chain stances must wait ≥ the transition duration in
physics frames (0.3s = 18 frames, 0.5s = 30) between requests.

## 8. GUT cross-test contamination

- Swapping `tree.current_scene` in one test (to mock a scene) leaks into
  others and breaks GUT's own runner — prefer instantiating a real level
  scene per test.
- A node that resolves siblings by name (`get_parent().get_node_or_null(
  "WorldSpecLoader")`) can pick up a STALE loader left by an earlier test via
  GUT's `current_scene` chain, flipping the code onto the wrong path. Force
  determinism in the fallback test: blank the NodePath export AND null the
  resolved ref AND clear `_use_worldspec` before asserting the fallback.

## 9. Verify the changelog entry BEFORE the commit message claims it

Committing with "changelog updated (Rule 1)" while the file is unchanged is a
Rule-1 violation — a pre-commit-changelog hook now catches this class.
Grep for the dated entry before writing the commit message that claims it.

## 10. macOS bash 3.2 has no associative arrays

Pre-commit hooks written with `declare -A` fail on macOS (bash 3.2 predates
associative arrays). Portable duplicate detection: newline-joined string +
`grep -qxF`. If a hook errors `declare: -A: invalid option`, that's the cause.
