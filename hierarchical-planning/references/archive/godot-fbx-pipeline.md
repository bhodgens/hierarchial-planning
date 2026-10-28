# Godot FBX → .tres Pipeline (moved from hierarchical-planning SKILL.md checklist, 2026-09-05)


When to use: converting Mixamo FBX animations to Godot .tres.
Lesson: requires Blender intermediate FBX-to-GLB and a --import pass or extraction yields zero output.
**The FBX→.tres pipeline requires a Blender intermediate (FBX→GLB→.tres), not direct FBX→.tres.**

Godot headless `-s script.gd` cannot load raw .fbx files — `ResourceLoader`
returns "No loader found for resource". The ufbx importer only runs in
editor mode.

## Steps

1. Blender batch converts FBX→GLB with `export_yup=False`.
2. `Godot --headless --import` registers the GLBs.
3. Godot headless extraction loads GLBs and saves .tres.

## Pitfall

Skipping step 2 (`--import`) makes the extraction silently produce zero
output — no error, just an empty result set.

## Timing

For 150+ files the whole pipeline takes ~5 minutes end to end.

## Related

- `references/godot-port-planning.md` — engine translation tables, MCP
  integration strategy, migration cost estimates.
- `references/gdscript-bulk-dispatch.md` — GDScript bulk dispatch, timeout
  expectations, disk checks before re-dispatch, corruption grep, async
  notification sweep.
