# Ggodot gut headless test pitfalls
When to use: GUT tests headless.
Lesson: await/frame pitfalls, scene-tree assumptions.

# Godot GUT Headless Test Pitfalls

Session: rebellion-the-game leaf 09 (integration test suite), 2026-08-07.
Applies to any GUT (`extends GutTest`) test run via
`godot --headless --path <proj> -s addons/gut/gut_cmdln.gd`.

## 1. Autoloads can PAUSE the tree at startup — physics tests see 0 movement

`PauseController` (or any UI-state autoload) may call `get_tree().paused = true`
in `_ready()` to start in the main-menu state. Player `_physics_process` gates
on `get_tree().paused` and returns immediately → movement/clock tests measure
0.0 and "fail" with identical-looking values.

**Fix:** in `before_each()` (or the scene builder), dismiss the menu:
```gdscript
func _dismiss_menu() -> void:
    var pc: Node = get_node_or_null("/root/PauseController")
    if pc != null and pc.has_method("_dismiss_main_menu"):
        pc._dismiss_main_menu()
    else:
        get_tree().paused = false
    await get_tree().process_frame
```
Probe first: a bare SceneTree script pressing an action and measuring 0 distance
while the object also doesn't fall = paused tree, not missing input.

## 2. Wall-clock timing lies in headless — wait PHYSICS frames

`await get_tree().create_timer(1.0).timeout` accumulates far more physics ticks
than 60 in headless (uncapped frame rate), so distance-over-time overstates
~5x. Two robust alternatives:
- Wait physics frames: `for i in range(N): await get_tree().physics_frame`
  (60 frames = 1 sim second at the configured 60Hz).
- Assert converged VELOCITY, not distance: settle 120 physics frames, read
  `player.velocity` with y zeroed. Probe-verified: walk converges to 1.4385
  vs SPEED_WALK 1.4 — matches the constant within tolerance.

Spawn-fall spikes inflate early samples: the player drops onto the floor in the
first frames (max hspeed ~16 during fall). Settle at least 120 frames before
reading velocity, or assert against a range that tolerates the spike.

## 3. GDScript: const preload resources are READ-ONLY members

`const WEAPON := preload("...tres")` then `WEAPON.ammo = 0` is a PARSE ERROR
("Cannot assign a new value to a constant"). GDScript treats const-bound
resources as deeply immutable. If a test mutates resource state (ammo, reload
timers), load it into a `var` instead:
```gdscript
var brown_bess: WeaponData = load("res://scripts/weapons/brown_bess.tres")
```

## 4. Shared preloads carry state across tests — reset explicitly

A weapon `.tres` preloaded once is shared by every test in the process.
`can_fire()` gates on `(now - last_fired) < fire_rate` and the manager gates
on `_fire_cooldown` — both persist. Reset before firing:
```gdscript
brown_bess.last_fired = -1000.0
wm.set("_fire_cooldown", 0.0)
```

## 5. Stance/state transitions bail while transitioning — real gameplay bug risk

`_request_stance_change` bails if `_is_transitioning_stance` is set. Two-stage
routes (STAND↔PRONE via CROUCH) recurse and can DROP the final leg, leaving
the player stuck in CROUCH. Test symptom: `current_stance` stays 1 (CROUCH)
after requesting 0 (STAND), sprint never engages (`wants_run` requires STAND).

**Fix (production code, not just test):** queue the second leg and fire it when
the first transition completes — a `_stance_queue` var checked in
`_update_stance_transition` after `t >= 1.0`.

**Test-side:** wait out the full chain between stance requests — transition
durations are 0.3s (18 physics frames) and 0.5s (30 frames); STAND↔PRONE chains
are 0.5+0.3s each way (≥96 frames total). Use 120-frame waits to be safe.

## 6. Invalid Environment property names are silently ignored (typo class)

`sdgi_enabled` (missing the f) loads without error but does nothing — Godot
silently ignores unknown `.tres`/`.gdshader` property names. The correct name
is `sdfgi_enabled`. When a test asserts an env property and the value never
changes, grep the .tres for a typo before suspecting logic.

## 7. PhysicsDirectSpaceState raycasts need physics ticks, not process frames

Scatter/grid tests that raycast ground (foliage placement, surface gating)
return zero hits if the test only awaits `process_frame` — the space state
updates on physics ticks. Await `physics_frame` in a loop (e.g. 20) before
asserting instance counts.

## 8. Detection order

When a GUT suite fails in the FULL run but passes in isolation: check for
cross-test contamination first (shared autoload state like `get_tree().paused`,
shared preload resources, `tree.current_scene` swaps). A test that leaves the
tree paused or swaps `current_scene` mid-suite breaks every subsequent test.
Run `-gselect=<file>` to bisect.
