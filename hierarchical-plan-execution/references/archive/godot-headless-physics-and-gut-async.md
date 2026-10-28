# Ggodot headless physics and gut async
When to use: headless physics (Rapier) + GUT async.
Lesson: physics stepping and await patterns headless.

# Headless Physics (Rapier) & GUT Async Patterns

Findings from the 2026-08-23 plans-sandbox intro execution (rebellion-the-game).
All reproduced exhaustively in one session; treat as project-durable until
the physics engine or GUT version changes.

## 1. Rapier area-overlap and gravity are INERT in headless test contexts

rebellion-godot runs Rapier3D (project.godot `physics/3d/physics_engine`).
Under headless GUT runs, Area3D body detection NEVER resolves — and gravity
never acts on RigidBody3D. Probed exhaustively before concluding:

- Minimal Area3D + body pairs (CharacterBody3D / RigidBody3D / StaticBody3D /
  AnimatableBody3D) with matching layers/masks: `overlaps_body()` stays false
  forever.
- `Engine.get_physics_frames()` DOES tick (physics frames fire), and
  `get_tree().paused = true` is the fixture default — but unpausing and
  PROCESS_MODE_ALWAYS do not help.
- An unconstrained RigidBody3D does not fall under gravity.

Existing suites dodge this: water integration asserts only
`SwimVolume.monitoring`, never actual overlap.

**Pattern — test the LOGIC, gate the WIRING manually:**

```gdscript
# NOTE: Rapier area-pair detection does not resolve headless here; exercise
# the logic path directly. Physical wiring is covered by the playtest gate.
var fake := CharacterBody3D.new()
fake.add_to_group("player")
beat._on_shimmer_body_entered(fake)
assert_true(beat.has_fall_fired())
```

Probe recipe if ever re-verifying: bare SceneTree script placed INSIDE the
project (res:// — /tmp scripts can't load), loop `await physics_frame`,
check `overlaps_body` and RigidBody descent. Both stay inert.

## 2. Await coroutines directly; avoid wait_until state-polling

Async chains like `func on_portal_touched(): ...; await play_blink();
_enter_scene_beat(...)` are best tested as `await director.on_portal_touched()`
— the coroutine completes and state settles deterministically after the await.
Replacing these with GUT `wait_until(func(): return state == X)` polls HUNG
the whole suite (~4-minute timeouts, repeatedly) under this repo's
paused-fixture environment. `wait_for_signal(sig, max_time)` is proven safe
for pure signal-completion waits.

## 3. Capture emitted params via connected collectors, not post-hoc reads

Reading `get_signal_parameters(...)` AFTER an await that freed the emitting
node races GUT's autofree pass: "Object freed while a signal is being
emitted" + failed param reads. Connect a lambda collector BEFORE awaiting:

```gdscript
var beats := []
director.intro_beat_changed.connect(func(b: String) -> void: beats.append(b))
await director.on_portal_touched()
assert_true(beats.has("PORTAL_TRANSIT"))
```

## 4. bind() arity trap

`signal finished(duration: float)` + `.connect(handler.bind(overlay))` means
the handler must accept `(duration, overlay)` — signal args FIRST, bound args
appended. A one-arg handler errors on every emit ("Method expected 1
argument(s), but called with 2").

## 5. gdshader comments are `//`, and every new shader needs an attribution block

`#` fails the gdshader tokenizer. Convention: `//` comments plus an
ATTRIBUTION header on ALL new shaders (originals included — the pre-commit
attribution audit warns on unmarked files):

```
// ============================================================
// ATTRIBUTION (see scripts/audit_attribution.py)
// Shader:    name.gdshader
// Status:    ORIGINAL — authored for Rebellion, no external source.
// License:   Same as project.
// ============================================================
```

## 6. GUT selectors that actually work

- `-gselect=test_suite_name` — reliable suite selector.
- `-gunit_test_name=test_name` — single test inside a suite.
- `-gtest=res://path.gd` can silently miss newly-added files until a
  `--import` pass registers them; prefer `-gselect`.
- GUT 9.7.1 has no `fail("msg")` — use `assert_false(true, "msg")`.
- `has_static_method` / `get_static_method_list` do not exist on GDScript —
  verify static APIs via `script.source_code.contains("static func x")`.
- Bare SceneTree probe scripts (`-s res://probe.gd`) must live inside the
  project; `/tmp` paths fail to load.

## 7. More silent-hang / suite-death traps (plans-sandbox 04 branch, 2026-08-24)

Symptom for ALL of these: GUT prints the script name + test list but NO
pass/fail totals, exit 0, log truncated right after the listing.

- **`get_tree().quit()` reachable from a handler under test kills the
  runner.** A menu "Quit to Desktop" press in a test emits then quits —
  the run dies mid-suite with no totals. Never drive quit-paths; assert
  the signal declaration and test a sibling path instead (documented
  inline in the test so nobody "fixes" it back).
- **`watch_signals(obj)` called AFTER an emit resets history** — the
  emit count reads 0 even though the signal fired during setup. Watch
  BEFORE driving the flow (test_cabin_npc_flow rerun test).
- **First-frame lazy wiring vs immediate calls**: nodes that connect
  their response pumps on `_on_first_frame` (process_frame,
  CONNECT_ONE_SHOT) are NOT wired when `_ready` returns. A test calling
  `player_said()` immediately gets no pump. Insert one
  `await get_tree().process_frame` before driving, or assert the
  connection is valid first.
- **Frame-stepping-dependent timing tests are flaky headless** — don't
  await N process_frames and expect a `_process(delta)` accumulator to
  have ticked; call the tick function directly with a synthetic delta
  (`npc._tick_freeform_gap(TIMEOUT + 0.1)`).
- **GDScript name shadowing is a parse error that fails the whole
  script**: `var chosen_profession: String` + `func chosen_profession()`
  = every preload of it fails ("Cannot infer type... value doesn't have
  a set type" cascades into the TEST file too). Getter must be
  `get_chosen_profession()`. When a whole suite reports unresolvable
  preloads, `--check-only -s res://the_script.gd` names the real error.
- **Typed inference on `.new()` from `load()`**: `var qs := load(...).new()`
  parse-errors ("value doesn't have a set type"); declare
  `var qs: Node = ...`.
- **@onready-built Controls in tests**: instantiating a controller with
  bare `.new()` misses `$Node` children its `_ready` touches. Build the
  minimal child shape first (TitleLabel/MenuContainer/FooterLabel/
  SplashOverlay+SplashLabel for menu_controller), THEN add_child, then
  one process_frame before driving.
- **`.tscn` text-format traps**: QuadMesh `size` needs 3 components;
  `load_steps=N` must match actual resource count after edits; missing
  `[resource]` header before properties makes a .tres unparseable
  (field_mat.tres case — audit_materials.py's fixer wrote it wrong).
