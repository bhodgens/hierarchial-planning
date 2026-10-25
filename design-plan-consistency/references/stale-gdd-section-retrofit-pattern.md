# Retrofitting a Stale Engine Implementation Section in a GDD Doc

## When to Use This Pattern

A GDD specification document was written for Engine A (e.g., UE5.8) and the
project has since migrated to Engine B (e.g., Godot 4.7). The doc's
"Implementation" section is still fully Engine A, even though a prior session
may have added a "Godot Implementation Note" (inline comment, sidebar, or a
small note pointing at the actual Godot files). The note was the diagnosis;
this pattern is the repair.

**DO NOT** rewrite the entire old implementation section from scratch. That
destroys historical lineage — future engineers lose the "why this design"
context that lives in the old Blueprint/C++ structure.

## The 4-Step Retrofit

### Step 1 — Insert a new authoritative section

Insert a `## Godot X.Y Implementation` heading immediately before the old
`## UE5.X Implementation` (or `## Unreal Engine 5.8 Implementation`) heading.
In the new section, include:

- A status marker: `> Status: [IN PROGRESS — old UE5 section below is STALE]`
- The actual Godot source files: `rebellion-godot/scripts/...`, `rebellion-godot/scenes/...`
- A UE5→Godot mapping table of equivalent concepts

### Step 2 — Retitle the old section

Change the old heading to:
`## UE5.X Implementation (STALE — see Godot section above)`

Leave the body intact. Do not edit the old Blueprint/C++ code blocks — they
are historical record.

### Step 3 — Add a cross-reference

In the new Godot section, point to the authoritative Godot source files and
note that the old section's design concepts (lighting, shadows, weather)
remain valid — only the engine-specific implementation changed.

### Step 4 — Changelog entry (AGENTS.md Rule 1)

Add a changelog row documenting the doc update. Include which old section
was marked STALE and which new Godot section was added.

## Worked Example: Rebellion 2026-08-13

**File:** `docs/gdd/03-world/07-day-night-and-weather.md`

The doc already had a Godot implementation note at line ~142 (added by the
seasonal-solar-model session: "BP_SunLight/BP_MoonLight map to two
DirectionalLight3D nodes driven by day_night_cycle.gd"). But the entire
"## Unreal Engine 5.8 Implementation" section (lines ~181–285) was still UE5
Blueprints, Lumen, VSM, Niagara, etc.

**Fix applied:**
1. Inserted `## Godot 4.7 Implementation` section before the old heading.
2. Included status marker, Godot source file paths, and a 8-row UE5→Godot
   mapping table (Sky Atmosphere→ProceduralSkyMaterial, SunPositionCalculator→
   DirectionalLight3D with NOAA solar, Niagara→GPUParticles3D, Lumen→SDFGI,
   VSM→DirectionalLight3D shadow splits, etc.).
3. Retitled old heading: `## Unreal Engine 5.8 Implementation (STALE — see
   Godot section above)`.
4. Changelog entry documented the change.

## Godot Source File Inventory

For quick reference when writing the Godot section, the key files for the
day/night/weather system:

| GDD Concept | Godot File |
|---|---|
| Clock + seasonal solar model | `rebellion-godot/scripts/world/day_night_cycle.gd` |
| District ambient modifiers | `rebellion-godot/scripts/world/lighting_manager.gd` |
| Weather VFX (rain/snow/fog) | `rebellion-godot/scripts/vfx/vfx_manager.gd` |
| Lightning | `rebellion-godot/scripts/vfx/lightning_manager.gd` |
| Weather audio bridge | `rebellion-godot/scripts/world/day_night_audio_bridge.gd` |
| Fog + sky | Scene-level `WorldEnvironment` + `Environment` + `Sky` |
| Sun + moon | Scene-level `DirectionalLight3D` (×2) driven by cycle |

## Gotchas

- **Do not edit the old code blocks.** Even if they contain "wrong" UE5 code,
  they are historical record. Annotate, don't rewrite.
- **Check for multiple stale sections.** A doc may have "UE5 Implementation"
  AND "UE5 Migration Notes" sections that are both stale. Mark each.
- **Watch for inline UE5 code blocks in prose.** Markdown code spans like
  `` `BP_SkyWeatherController` `` embedded in paragraph text are easy to miss
  with grep. Read the full "Implementation" section, not just headings.
