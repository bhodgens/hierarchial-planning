# Procgen Pipeline Completeness Checklist

Session-specific detail for reviewing `plans-glm/10-procgen` (procedural generation pipeline).

## What the Pipeline Produces

Deterministic, seed-driven colonial Boston world generation:
- Stage 0: Geography (peninsula, hills, Neck, harbor)
- Stage 2: District zoning (9 historical districts, faction lean)
- Stage 3: Road network (historical arteries + procedural fill)
- Stage 4: Parcel subdivision (lots with wealth/faction metadata)
- Stage 5: Building generation (colonial types, modular assembly)
- Stage 6: Interior generation (rooms, layout presets, condition)
- Stage 7: Furniture placement (constraint-based, tagged)
- Stage 8: Vegetation (trees, shrubs by district zone)
- Stage 8b: Wildlife (deer, rabbit on woodland tiles)
- Stage 9: Environment props (lampposts, wells, cover)
- Stage 10: NPC spawn specs (roles, counts, room assignments)
- Stage 11: Lighting plan (sun direction, ambient, shadow quality)
- Stage 12: Audio metadata (ambient layers, reverb, wind)
- Stage 13: Timeline state (era, days elapsed, events)

**Output:** Pure data `WorldSpec` struct → JSON → `worldspec_<seed>.json`

## Known Open Items (as of 2026-08-14)

| Item | Status | Details |
|------|--------|---------|
| Stage 1 terrain heightmap | DEFERRED | No `stage1_terrain.go`; `WorldSpec.Terrain` zero-valued |
| Stage -1 reference collection | UNDECIDED | Q-proc-2; no historic map/elevation data loaded |
| WorldSpec→NPC identity tie | OPEN | Offset 1,000,000 used; sim generates 500 NPCs independently |

## Godot Bridge Files (2026-08-14 integration pass)

- `rebellion-godot/scripts/world/building_instantiator.gd` (511L) — GLB path + SurfaceTool facades
- `rebellion-godot/scripts/world/street_lighting.gd` (723L) — fire baskets 1764-1773, oil lanterns 1774+
- `rebellion-godot/scripts/world/wavy_glass_material.gd` (60L) — screen-space refraction shader factory
- `rebellion-godot/scripts/world/wallpaper_palette.gd` (3604 bytes) — merchant_house variant mapping
- `rebellion-godot/scripts/world/chunk_content_builder.gd` — integration point, wired into `showcase_map.tscn`

## Test Counts

- Go procgen suite: 25 tests, all passing, determinism verified
- Godot GUT: facades 8/8, street lighting 23/23, glass 5/5, wallpaper 16/16, chunk-content 17/17 regression