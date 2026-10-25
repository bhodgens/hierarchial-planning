# Godot 4.7 GDScript + Shader Pitfalls (from rebellion-the-game, 2026-08-07)

Recurring errors that subagents produce when writing Godot 4.7 GDScript and
shaders. Use as a review checklist after every Godot leaf implementation.

## GDScript Pitfalls

### 1. `class_name` cross-script type resolution failure

**Symptom:** "Expected valid type hint after ':'" parse error on a line that
uses a `class_name`-typed variable from another script.

**Cause:** Godot 4.7's GDScript analyzer cannot resolve `class_name` types
across scripts in the same project reliably (especially in headless/test
mode). This is a known engine limitation.

**Fix:** Remove `class_name` declarations. Use `preload()` + `.new()` for
instantiation, and `Node3D` or the native base type for variable annotations.
Access custom properties via `.set()` / `.get()` instead of typed assignment.

```gdscript
# WRONG — class_name resolution fails cross-script
const MyScript := preload("res://my_script.gd")
var instance: MyScript  # "Expected valid type hint after ':'"

# RIGHT — use native base type
const MyScript := preload("res://my_script.gd")
var instance: Node3D
instance = MyScript.new()
```

### 2. `var x: Type = expr as Type` — double-type syntax error

**Symptom:** "Expected valid type hint after ':'" on a typed variable
declaration with an `as` cast.

**Cause:** GDScript disallows `var x: Type = expr as Type`. The `as` keyword
in a typed declaration creates an ambiguous parse.

**Fix:** Use ONE of:
```gdscript
var x: Type = expr          # typed annotation, no cast
var x = expr as Type         # cast, no annotation
var x = expr                 # untyped (use when type is ambiguous)
```

### 3. `_get_process_delta_time()` — nonexistent API

**Symptom:** "Function not found in base self" parse error.

**Cause:** The API is `get_process_delta_time()` (no leading underscore).
Subagents frequently add the underscore by analogy with `_process(delta)`.

### 4. `SHADOW_CAST_ONLY_SETTING_OFF` — wrong enum name

**Symptom:** "Cannot find member" error.

**Cause:** The correct enum is `GeometryInstance3D.SHADOW_CASTING_SETTING_OFF`
(not `CAST_ONLY`). Subagents guess the shorter name.

### 5. `push_warning()` counts as a debug artifact

The SHARED-CONVENTIONS grep catches `print()` but not `push_warning()`.
Both must be removed before commit — `push_warning` is engine-spammy and
violates the "no debug artifacts" rule. Use silent early-return instead.

## Shader Pitfalls

### 6. GDScript type annotation syntax leaking into GLSL

**Symptom:** Shader compilation fails with "Expected valid type hint after ':'"

**Cause:** Subagents write `float x: float = 0.5;` in shader code, copying
GDScript's `var x: float = 0.5` pattern. Shader language uses plain
declarations.

```glsl
// WRONG (GDScript syntax in GLSL)
float sway_phase: float = TIME * wind_speed;

// RIGHT (plain GLSL)
float sway_phase = TIME * wind_speed;
```

### 7. `filter_linear_nearest` — invalid texture hint combination

**Symptom:** Shader compilation error on a `sampler2D` uniform line.

**Cause:** `filter_linear_nearest` is not a valid Godot shading language hint.
Valid filter hints: `filter_linear`, `filter_nearest`, `filter_linear_mipmap`.

```glsl
// WRONG
uniform sampler2D tex : repeat_enable, filter_linear_nearest;

// RIGHT
uniform sampler2D tex : repeat_enable, filter_linear;
```

### 8. `look_at_from_position()` crashes in headless mode

**Symptom:** "Method/function failed. Returning: nullptr" ×5 in headless
GUT runs, traced to a Camera3D inside a SubViewport.

**Cause:** `Camera3D.look_at_from_position()` requires a rendering device to
compute the view matrix. In headless mode (--headless), no rendering device
exists, so the call returns nullptr and the engine logs errors.

**Fix:** Set `rotation_degrees` directly instead of using look_at:
```gdscript
# WRONG — crashes headless
cam.look_at_from_position(cam.position, Vector3.ZERO, Vector3.FORWARD)

# RIGHT — direct rotation, works everywhere
cam.rotation_degrees = Vector3(-90.0, 0.0, 0.0)  # point straight down
```

### 8b. GLSL NEVER compiles in headless GUT — rename fallout is invisible (2026-08-16)

**Symptom:** Every GDScript suite green, but in-game the CompositorEffect
silently fails (`pipeline_create` warning) and the effect does not render.

**Cause:** Compute/fragment shaders are only compiled when a real rendering
device exists. A GLSL edit that references an undefined identifier — e.g. a
variable rename in `main()` that missed one later line (`float dy = cam_y -
world_pos.y;` after `world_pos` was renamed to `world_pos_raw`) — parses
fine to the eye, passes every headless test, and breaks only at runtime.

**Fix (review discipline):** after ANY GLSL edit, grep the shader for every
identifier you renamed and confirm zero stale references:
`grep -n "old_name" shader.glsl` must return nothing. Treat a GLSL rename
like a code rename: the compiler is NOT in the loop during headless CI.

**Same class — rename fallout in GDScript is caught, in GLSL it is not:**
GUT exercises GDScript paths (parse errors surface), but nothing headless
exercises the shader. The visual smoke run is the only real gate for GLSL.

## GDScript Runtime Pitfalls

### 11. `as Array[Dictionary]` silently fails on JSON-parsed arrays

**Symptom:** Typed array fields (buildings, roads, npc_spawns, etc.) are empty
after loading from JSON, with zero errors or warnings.

**Cause:** `JSON.parse_string()` returns untyped `Array` and `Dictionary`.
The `as Array[Dictionary]` cast sees a plain Array, fails the type check, and
returns `null` — which becomes an empty array on assignment. No error is
logged.

**Fix:** Element-by-element copy into the typed array:

```gdscript
# WRONG — silently fails, _buildings ends up empty
_buildings = data.get("buildings", []) as Array[Dictionary]

# RIGHT — safe copy
func _to_dict_array(raw: Variant) -> Array[Dictionary]:
    var result: Array[Dictionary] = []
    if raw is Array:
        for item in raw:
            if item is Dictionary:
                result.append(item)
    return result

_buildings = _to_dict_array(data.get("buildings", []))
```

This affects EVERY typed-array field populated from JSON. Audit all
`as Array[...]` patterns in code that touches `JSON.parse_string()`.

### 12. Async function called without `await` — coroutine abandoned

**Symptom:** Save file never written, signal fires before completion, no error.

**Cause:** When a function is `async` (contains `await`), calling it without
`await` starts the coroutine but immediately abandons it. The caller proceeds
as if it completed, but the function body after the `await` never runs.

**Fix:** Always `await` async function calls:

```gdscript
# WRONG — save never completes to disk
_save_system.save_game(slot_id)

# RIGHT — awaits the sidecar overlay collection
await _save_system.save_game(slot_id)
```

Audit: grep for any function call where the callee contains `await` and the
caller doesn't `await` it. Common in auto-save, auto-save UI hooks, and
sidecar coordination code.

## Scene (.tscn) Pitfalls

### 9. Smoke tests require non-null meshes on MeshInstance3D

**Symptom:** Scene smoke test fails: "FollowPlane: mesh is null"

**Cause:** Scripts that assign `mesh` at runtime (in `_ready()`) leave the
scene's MeshInstance3D with a null mesh. Smoke tests that check for valid
meshes before `_ready()` completes will fail.

**Fix:** Always provide a default placeholder mesh in the .tscn file:
```
[sub_resource type="PlaneMesh" id="default_mesh"]
size = Vector2(5, 5)

[node name="FollowPlane" type="MeshInstance3D" parent="."]
mesh = SubResource("default_mesh")
```

### 10. Script `extends` type must match scene node type

**Symptom:** "Script inherits from native type 'RigidBody3D', so it can't be
assigned to an object of type 'Node'."

**Cause:** A .tscn node has `type="Node"` but the attached script has
`extends RigidBody3D`. The script must match or be a subtype of the node's
native type.

**Fix:** Put the script directly on the correctly-typed node, or change the
script to extend the node's base type and use `get_parent()` to access the
body.
