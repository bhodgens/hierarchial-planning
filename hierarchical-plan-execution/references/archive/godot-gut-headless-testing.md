# Ggodot gut headless testing
When to use: headless GUT for rebellion-the-game.
Lesson: engine headless flags, GUT CLI invocation, failure triage.

# Godot 4.7 Headless GUT Testing Pitfalls (from rebellion-the-game, 2026-08-07)

A full afternoon of GUT-suite triage produced these repeatable pitfalls. Every
one was a REAL failure first, then a fix. If a Godot leaf's headless tests
fail with zeroes, no movement, or "clock didn't advance", work down this list.

## 1. PauseController autoload starts the tree PAUSED (top cause of zero physics)

If any autoload enters a menu state in `_ready()` (this project's
PauseController calls `_enter_main_menu()` → `get_tree().paused = true`),
EVERY headless test runs with physics frozen: the player won't move, the
day/night clock won't advance, gravity won't apply. Symptom: distances are
exactly 0.000000, clock `12.0 -> 12.0`.

**Fix (test-side):** `before_each()` must dismiss the menu:
```gdscript
func _dismiss_menu() -> void:
    var pc := get_node_or_null("/root/PauseController")
    if pc != null and pc.has_method("_dismiss_main_menu"):
        pc._dismiss_main_menu()
    else:
        get_tree().paused = false
    await get_tree().process_frame
```
Call it in `before_each()` AND at the top of helpers that instantiate the
player scene. Do NOT change the production autoload for tests.

## 2. Headless physics timing: NEVER measure distance with `create_timer`

Headless runs at uncapped FPS; `create_timer(1.0)` is wall-clock, so physics
ticks accumulate ~5× faster than the 60 Hz nominal. A walk gait measured over
`create_timer(1.0)` reads 6.9 m instead of 1.4 m.

**Fix:** wait `physics_frame` signals, not wall-clock:
```gdscript
func _settled_speed(player: CharacterBody3D, settle_frames: int = 120) -> float:
    for i in range(settle_frames):
        await get_tree().physics_frame
    var hvel: Vector3 = player.velocity
    hvel.y = 0.0
    return hvel.length()
```
120 frames converges to the true GDD speed (walk → 1.4385 vs SPEED_WALK 1.4);
45 frames still rides the spawn-fall acceleration spike. Verify the converged
value with a standalone SceneTree probe before choosing tolerances.

## 3. GUT deadlock: `await tween.finished` + `Engine.time_scale`

GUT's frame stepping does not advance `create_tween()` tweens on their own,
and speeding time with `Engine.time_scale` + `await tween.finished` deadlocks
the whole suite (run hangs past 300s, log stalls mid-test).

**Fix:** fast-forward deterministically with `custom_step`:
```gdscript
func _await_district_tween(manager: Node) -> void:
    var tween: Tween = manager.get("_tween") as Tween
    if tween and tween.is_valid():
        tween.custom_step(LIGHTING_MANAGER_SCRIPT.TRANSITION_DURATION + 0.1)
    await get_tree().process_frame
```
For tweens the production code creates internally (e.g. death fade), store the
tween in a member var (`_death_fade_tween`) so tests can `custom_step` it.

## 4. `const X := preload(...)` then `X.prop = value` is a PARSE ERROR

GDScript treats const-referenced resources as deeply immutable. The file won't
load at all: `Parse Error: Cannot assign a new value to a constant`.

**Fix:** mutable per-test fixtures must be `var` + `load()`:
```gdscript
var brown_bess: WeaponData = load("res://scripts/weapons/brown_bess.tres")
```
`const` is fine for reading (asserting `.reload_time`) but never for mutating.

## 5. Shared preload resources carry state across tests

A preloaded weapon/mesh shared across tests keeps `last_fired`, `current_ammo`,
`is_reloading` from the previous test. `can_fire()` gates on
`(now - last_fired) < fire_rate` — with `last_fired = 0.0` default, a fire
within `fire_rate` seconds of process start returns false. Reset explicitly:
```gdscript
brown_bess.last_fired = -1000.0
wm.set("_fire_cooldown", 0.0)
```

## 6. Two-stage stance changes drop the final leg (REAL gameplay bug)

Godot controllers that implement STAND↔PRONE via a CROUCH intermediate
commonly recurse: `_request_stance_change(PRONE)` calls
`_request_stance_change(CROUCH)` then `return` — but the second call bails on
`_is_transitioning_stance`, leaving the player stuck in CROUCH. Symptom in
tests: `stance=1` (CROUCH) after a PRONE→STAND request, sprint never engages.

**Fix (production, not test):** queue the second leg and fire it when the
first transition completes:
```gdscript
var _stance_queue: int = -1
# in _request_stance_change, two-stage routes:
if current_stance == Stance.STAND and target == Stance.PRONE:
    _request_stance_change(Stance.CROUCH)
    _stance_queue = Stance.PRONE
    return
# in _update_stance_transition, when t >= 1.0:
if _stance_queue >= 0:
    var queued := _stance_queue
    _stance_queue = -1
    _request_stance_change(queued)
```
Tests must also wait out transition durations in physics frames (0.3s = 18
frames, 0.5s = 30) before requesting the next stance — the bailing guard is
intentional, the queue is the fix.

## 7. Godot 4 API renames that break tests and shaders

- `ArrayMesh.get_triangle_count()` does NOT exist in Godot 4 — use
  `get_surface_count()` + `surface_get_arrays(0)[Mesh.ARRAY_VERTEX]`.
- `Environment.sdfgi_cascade_0_distance` / `volumetric_fog_height` /
  `volumetric_fog_height_density` are INVALID property names — Godot silently
  ignores them in .tres, so the intended setting never applies. Real API:
  `sdfgi_cascades` (count), `sdfgi_cascade0_distance` (NO underscore before
  the 0), `sdfgi_max_distance` (engine couples `max = c0 × 2^cascades` — set
  max = c0 × 16 for 4 cascades or the engine clamps c0 down), and volumetric
  fog has no height knobs (only `volumetric_fog_length`).
- `sdgi_enabled` typo (missing 'f') — check .tres environment resources.
- Verify property existence with a SceneTree probe before writing .tres:
  `print("sdfgi_cascade0_distance" in Environment.new())`.

## 8. GUT `tree.current_scene = mock` swap contaminates the whole suite

Swapping `current_scene` in a GutTest to point at a mock breaks other tests
in the same run (GUT's runner owns current_scene; later tests inherit the
swap and their physics/`get_tree().current_scene` lookups fail or hit the
stale mock). Save tests passed in isolation but failed in the full run.

**Fix:** prefer instantiating the REAL level scene (which contains the
DayNightCycle/ChunkManager nodes) instead of swapping current_scene. If a
system must not find a sibling autoload, blank the NodePath exports AND
null the resolved ref after two frames:
```gdscript
builder.set("worldspec_path", NodePath(""))
builder.set("_worldspec", null)
builder.set("_use_worldspec", false)
```

## 9. `_ready()` defer-one-frame + test timing

Scripts whose `_ready()` does `await get_tree().process_frame` before
resolving node refs need the TEST to wait TWO frames (one for _ready's await,
one for the refs to land), else child managers are null and content silently
doesn't build. Symptom: everything works in a standalone SceneTree probe (2+
frames) but fails in GUT (1 frame). Wait 2 frames in the test helper.

## 10. Changelog pre-commit hooks on macOS: no `declare -A`

macOS ships bash 3.2, which has NO associative arrays. A pre-commit hook using
`declare -A` fails with `declare: -A: invalid option` on every commit.
Portable duplicate-detection: newline-joined string + `grep -qxF`:
```bash
SEEN_KEYS=""
# ... after computing key:
if printf '%s\n' "$SEEN_KEYS" | grep -qxF "$key"; then
    echo "duplicate: $key"; FAILED=1
fi
SEEN_KEYS="$(printf '%s\n%s' "$SEEN_KEYS" "$key")"
```

## Orchestrator note: subagent timeout ≠ no work done

Leaf subagents that hit the 600s timeout with 20-40 api_calls often DID land
their files (they write code first, summarize last). Before re-dispatching or
doing the work yourself, `git status --short` — the files may be there and
only need review + fixes. This session: a "timeout" subagent had created 4
scripts + a 16-test suite; the orchestrator reviewed, fixed 3 test bugs, and
committed. The leaf-09 subagent that "failed with 503" had actually committed
its own work (cc1afc3) despite no-commit instructions — check `git log`
recent commits too.
