# Godot Project Setup Pattern (from rebellion-the-game, 2026-07-24)

## Context

When executing a plan tree that creates a new Godot project directory (e.g.,
`rebellion-godot/`) alongside an existing prototype (`game/`), the setup
sequence matters.

## Setup Sequence

1. **Create directory structure first:**
   ```bash
   mkdir -p rebellion-godot/scripts/{player,weapons,npc,world,ui,audio,save,sidecar,animation,vfx}
   mkdir -p rebellion-godot/scenes/{player,weapons,npc,levels,ui,tests,vfx}
   mkdir -p rebellion-godot/assets/{models,textures,audio,animations}
   mkdir -p rebellion-godot/resources/{environments,materials}
   ```

2. **Copy prototype assets (scenes, scripts, assets) from existing directory:**
   ```bash
   cp -r game/scenes rebellion-godot/
   cp -r game/scripts rebellion-godot/
   cp -r game/assets rebellion-godot/
   ```
   Do NOT recreate scenes from scratch if a working prototype exists (Pitfall 40).

3. **Write project.godot with correct version:**
   - Check actual Godot version: `/Applications/Godot.app/Contents/MacOS/Godot --version`
   - Use that version in `config/features=PackedStringArray("4.7", "Forward Plus")`
   - Plans may reference stale versions (e.g., "4.2") — always verify

4. **Create autoload stubs for every autoload in project.godot:**
   ```gdscript
   extends Node
   ## Save system autoload — full implementation in branch 07-save-load.
   ## Stub exists so project.godot autoload resolves without error.
   ```
   Without stubs, Godot ERRORs on every launch (missing autoload scripts).

5. **Verify with headless launch:**
   ```bash
   /Applications/Godot.app/Contents/MacOS/Godot --headless --quit 2>&1 | head -15
   ```
   - WARNINGs about invalid UIDs: expected and harmless (`.godot/` cache not copied)
   - ERRORs about missing autoloads or main scene: NOT OK — fix before proceeding

## Godot MCP Tools (vanilla, not Summer Engine)

The `godot` MCP server provides these key tools:
- `mcp__godot__get_godot_version` — verify engine version
- `mcp__godot__create_scene` — create new .tscn files
- `mcp__godot__add_node` — add nodes to existing scenes
- `mcp__godot__run_project` — run the project and capture output
- `mcp__godot__stop_project` — stop a running project
- `mcp__godot__save_scene` — save scene changes

## Verifying Leaf Work (scripts compile, no editor)

After implementing a Godot code leaf (new scripts, modified controllers),
verify with `--headless --editor --quit` — NOT `--check-only`:

```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --path rebellion-godot/ --editor --quit 2>&1 \
  | grep -iE "parse error|failed to load"
# Empty output = all scripts compile correctly
```

**Pitfall:** project-level `--check-only` (no `--script`) fails to resolve ALL
`class_name` globals (your own types, addon types, autoload types) and reports
mass false errors. It also times out on large projects. Always use
`--editor --quit` for full-project compile verification. See
`godot-game-development` skill → `references/godot-headless-verification.md`
for the full verification decision tree.

**Backward-compatible API changes:** when adding optional parameters to a
method signature (e.g. `take_damage(amount)` →
`take_damage(amount, attacker_pos=Vector3.ZERO, attack_type="punch")`),
all existing callers with fewer arguments remain valid. Use this to
progressively enrich combat interfaces without breaking callers in other
files you haven't audited yet. After the change, grep for all callers to
confirm none need the new parameters passed:

```bash
grep -rn '\.take_damage(' scripts/ | grep -v '\.uid'
```

- Explicit type annotations everywhere (`var x: float = 1.0`)
- Never `:=` with Variant sources
- No `print()` statements, no TODO comments
- `_input()` + `set_input_as_handled()` for pause/menu (must fire even when paused)
- `_unhandled_input()` for gameplay actions (blocked by UI)
- Reset `is_aiming = false` at start of each `_physics_process`
- AI model facing: add PI to target_yaw (models face +Z, Godot forward is -Z)

## Key GDD Values (frequently wrong in plans)

- Walk: 1.4, Run: 3.5, Sprint: 5.5, Crouch: 0.8, Prone: 0.4 m/s
- Capsule: 1.80m total (90cm half-height), radius 30cm
- Camera: third-person DEFAULT (FOV 75°), first-person toggle (FOV 90°)
- Musket reload: 10-13s (Brown Bess 13s), NOT 2-4s
- Stranger penalty: 80% initial
- Day cycle: 32 in-game sec / real sec (45 min real = 24h game)
- Sidecar IPC: NDJSON over TCP port 10909, NOT HTTP REST
- NPC IDs: uint64, NOT strings

## Subagent-Produced API Errors (Review Checklist)

Subagents writing Godot 4.7 GDScript and shaders consistently produce the same
API-name and syntax errors. After every Godot leaf subagent return, run the GUT
headless suite FIRST — it catches most of these automatically — then manually
check for:

- `class_name` declarations (cross-script resolution fails in Godot 4.7)
- `var x: Type = expr as Type` (double-type syntax error — use one or the other)
- `_get_process_delta_time()` (should be `get_process_delta_time()`, no underscore)
- `SHADOW_CAST_ONLY_SETTING_OFF` (should be `SHADOW_CASTING_SETTING_OFF`)
- `push_warning()` (counts as debug artifact — remove, use silent early-return)
- `float x: float =` in shader code (GDScript syntax leaking into GLSL — use plain `float x =`)
- `filter_linear_nearest` (invalid hint — use `filter_linear`)
- `look_at_from_position()` in SubViewport cameras (crashes headless — use `rotation_degrees`)
- `as Array[Dictionary]` on JSON-parsed arrays (silently fails — use element-by-element copy)
- Missing `await` on async function calls (coroutine abandoned — grep for `await` in callee)
- MeshInstance3D nodes with null mesh in .tscn (smoke tests fail — provide default mesh)
- Script `extends` type mismatch with scene node type

Full details: `references/godot-gdscript-shader-pitfalls.md`
