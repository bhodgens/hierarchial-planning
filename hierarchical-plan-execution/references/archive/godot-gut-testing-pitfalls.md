# Ggodot gut testing pitfalls
When to use: headless testing + Environment resources.
Lesson: resource-path pitfalls in CI runs.

# Godot headless testing + Environment resource pitfalls

Source: rebellion-the-game session 2026-08-07 — implementing/verifying
rendering-vfx plan leaves 01/02/05 under Godot 4.7.1 with GUT headless.

## 1. GUT + Tween deadlock: never `await tween.finished` in a test

`Engine.time_scale = 20` + `await tween.finished` HANGS the headless run
(>300s when the suite normally finishes in ~20s). GUT's frame stepping does
not advance `create_tween()` tweens the way the game loop does — the
`finished` signal never fires.

- Fix (production side, justifiable as testability): store the tween in a
  member var (`var _death_fade_tween: Tween`) so tests can drive it. No
  behavior change.
- Fix (test side): `tween.custom_step(duration + 0.1)` fast-forwards
  deterministically. For looping pulse tweens, `custom_step` twice
  (half-cycle → assert scale grew, full → assert returned toward min).
- Symptom signature: GUT run hangs mid-file at the first tween-awaiting test
  with no error output. Check `ps aux | grep Godot` — a killed foreground
  run can also leave a stray process holding the project (see §4).

## 2. Godot SILENTLY IGNORES invalid Environment (.tres) property names

`sdfgi_cascade_0_distance`, `sdfgi_cascade_1_distance`, `volumetric_fog_height`,
`volumetric_fog_height_density` do NOT exist on `Environment`. The .tres loads
fine, the values are dropped, ZERO errors — the "4 cascades / 64m" intent
never takes effect. A pre-existing harbor_env.tres carried these for days
without anyone noticing.

Real property names (verify with a probe, don't trust memory):
- SDFGI: `sdfgi_cascades` (int), `sdfgi_cascade0_distance` (NOTE: no
  underscore before the digit), `sdfgi_max_distance`, `sdfgi_min_cell_size`,
  `sdfgi_energy`, `sdfgi_bounce_feedback`. Only cascade0 exists as a distance
  knob; cascades 1-3 derive as 2x/4x/8x.
- Volumetric fog: `volumetric_fog_enabled/density/albedo/emission/length/
  detail_spread/gi_inject/anisotropy/temporal_reprojection_*` — there is NO
  height or height_density knob (that's a regular-fog concept).

Engine coupling: `sdfgi_max_distance = sdfgi_cascade0_distance × 2^cascades`.
Setting cascade0=64 with max=512 silently clamps cascade0 back to 32
(512/16). To express "cascade0 = 64m", write BOTH
`sdfgi_cascade0_distance = 64.0` AND `sdfgi_max_distance = 1024.0`.

## 3. Probe-before-assert for resource APIs

Before writing tests against a Godot resource's numeric contract, dump the
real API with a throwaway `extends SceneTree` script (`_init()`):
load the resource, iterate `get_property_list()` filtered by prefix, print
defaults, SET candidate values and print readbacks.

Run: `godot --headless --path rebellion-godot/ -s scripts/tools/probe.gd`

This caught both the invalid property names and the max=c0×2^cascades
coupling before any test was written. Delete the probe script afterwards.
GDScript gotcha in probes: `for p in ...` collides with a prior `var p`
("There is already a variable named p declared in this scope") — use
distinct names.

## 4. Stray headless Godot processes block subsequent runs

A foreground GUT invocation that times out (the tool timeout kills the
wrapper) leaves the Godot child process running and holding the project;
the next headless run then hangs. Before re-running:

```
ps aux | grep "Godot.*headless" | grep -v grep | awk '{print $2}' | xargs kill
```

Then the suite completes in ~20-30s. Also: running TWO headless Godot
instances concurrently (e.g. a leftover + a fresh one) causes contention —
kill strays first.

## 5. Headless runs don't emit .uid sidecar files

New .gd files get their `.uid` companions only from an editor import scan.
After creating new scripts/tests, run once:

```
godot --headless --path rebellion-godot/ --import
```

(exit 0, ~30-60s) so the repo convention — commit `.uid` files alongside
every `.gd` — holds for new scripts.

## 6. Color equality on lerped values

`assert_eq(sun.light_color, expected_color)` FAILS even when both print
identically in the failure message — phase-boundary blending leaves float
error in the low bits. Compare per-channel with tolerance instead:
`assert_almost_eq(color[i], expected[i], 0.02)`.

## 8. JSON.parse_string() logs engine errors on invalid JSON

When testing a manifest parser with deliberately invalid JSON input,
`JSON.parse_string("{{{")` logs an internal engine error
(`Condition "error != Error::OK" is true. Returning: Variant()`)
that GUT's error tracker catches as an unexpected error, failing the test.

**Fix:** Use `JSON.new().parse(text)` which returns an `Error` enum without
logging:
```gdscript
var json := JSON.new()
var err := json.parse(text)
if err != OK or typeof(json.data) != TYPE_ARRAY:
    return []
# iterate json.data
```

Real instance: `prop_registry.gd` `load_props()` test
`test_load_props_invalid_json_returns_empty` failed because the parser logged
the engine error. Switching from `JSON.parse_string()` to `JSON.new().parse()`
silenced the error while preserving the same return-value contract.

## 9. get_bone_global_pose() fails on off-tree Skeleton3D

Calling `get_bone_global_pose()` on a Skeleton3D that is NOT in the scene tree
(detached, synthetic, headless test) logs:
`Condition "!is_inside_tree()" is true. Returning: Transform3D()`

GUT catches this as an unexpected error. Use `get_bone_rest()` instead — it
works on detached skeletons and is sufficient for geometric calculations
(foot-grounding offset, stride length) that only need REST geometry.

Real instance: `test_rigify_foot_grounding.gd` synthetic skeleton test failed
on `skel.get_bone_global_pose(idx)` because the skeleton was never added to
the scene tree. Switching to `get_bone_rest(idx)` fixed it.

## 10. Markdown table row mangling (GDD changelog / tracking tables)

Patching a huge markdown table row by matching only its leading cells
(e.g. `| 2026-08-07 | Camera anti-clip...`) replaces the ENTIRE line — the
unmatched tail of the original row stays appended inside your new row's last
cell. The table silently loses a row and gains a column of garbage.

Prevention: match the FULL row, or append by matching the row's final cell
text. Repair: a small Python script that finds the orphaned tail
(`| cell1, `cell2 | ...`) after your row's real end and splits it back into
its own `| 2026-... |` line. Verify afterwards with a per-row pipe count
(`l.count('|') == 6` for a 5-column table) — but note legacy rows may
legitimately use double pipes (`|| 2026-07-25 | ...`), so whitelist known
legacy rows before flagging.
