# Godot Port Planning Pattern

## When to Use

When porting a game from UE5/Unity to Godot 4 / Summer Engine. This pattern extends the standard `hierarchical-planning` skill with engine-specific translation tables, MCP integration strategy, and GDScript pitfalls.

## Key Differences from Standard Plan Trees

### 1. Engine Translation Tables Required

Every branch orchestrator must include a **Translation Table** mapping UE5 concepts to Godot equivalents:

| UE5 Concept | Godot Equivalent | Notes |
|-------------|------------------|-------|
| CharacterMovementComponent | CharacterBody3D + custom script | Re-port movement logic |
| World Partition | Custom chunk system + ResourceLoader | No built-in streaming |
| Chaos Physics | Jolt Physics plugin or GodotPhysics | Evaluate performance |
| UMG Widgets | Control nodes | Layout portable, widgets rebuild |
| MetaSounds | AudioServer + AudioStreamPlayer3D | Design portable, graph rebuild |

### 2. Go Sidecar IPC is Engine-Agnostic

55-60% of game logic lives in the Go sidecar (`sidecar/internal/sim/`) and requires **zero changes**:
- Gossip network, NPC memory, dialogue orchestration, LLM bridge
- Economy, quest system, faction AI, NPC scheduler
- Alignment system (math portable, sensor inputs need rewrite)

The plan tree should explicitly mark these as "no work needed" to avoid redundant effort.

### 3. Summer Engine MCP Integration Strategy

Summer Engine exposes 52 MCP tools (free tier). The plan should leverage:
- `summer_get_script_errors` — compilation verification
- `summer_screenshot target:game` — runtime visual verification
- `summer_import_asset_by_id` — asset library import
- `summer_play` / `summer_stop` — playtest automation

Include MCP tool usage in every leaf's verification checklist.

### 4. Existing Prototype Survey Mandatory

Before decomposing, dispatch a read-only survey subagent to inventory existing code:
- List all source files (.gd, .tscn, .tres)
- Read key implementations (player controller, weapons, NPC AI, save system)
- Map to GDD features (what's implemented vs missing)
- Check for Summer Engine MCP integration (likely vanilla Godot only)

In the Rebellion session, this revealed 1,873 lines of GDScript implementing ~5% of GDD features — critical for the "rewrite vs refactor" decision.

### 5. Migration Cost Estimate

Per GDD §06-technical/01-engine-comparison.md:
- **9-13 weeks** for single developer focused on engine integration
- Sidecar client component: Small (~300-500 LOC)
- Rendering setup (GI, materials, LOD): Large (full rebuild)
- World-gen scene assembly: Medium-Large
- Combat physics + damage: Medium

Use this estimate when sizing leaves — don't underestimate rendering/world-gen complexity.

## Branch Structure for Godot Ports

Recommended branch decomposition:

```
plans-godot/
  master.md
  SHARED-CONVENTIONS.md     # Frozen wire types, numeric scales, save schema
  OPEN-QUESTIONS.md          # Engine choice, prototype reuse, sidecar changes
  01-foundation/             # Project setup, MCP config, base scene
  02-player-systems/         # Movement, combat, stealth, advanced traversal
  03-npc-systems/            # Sidecar client, perception, behavior tree, dialogue
  04-world-streaming/        # Procedural gen, chunk loading, day/night
  05-audio-tts/              # Footsteps, ambient, Piper/Qwen TTS pipeline
  06-ui-menus/               # HUD, pause, save/load, settings, rebinding
  07-save-load/              # JSON serialization, auto-save
  08-asset-pipeline/         # Model import, textures, Summer library
  09-integration-tests.md    # Full smoke test suite (single leaf)
```

## Common Pitfalls Specific to Godot Ports

1. **Assuming built-in open-world streaming.** Godot has no equivalent to UE5's World Partition. Must implement custom chunk system with ResourceLoader for async loading.

2. **Using UE5 StateTree directly.** Godot has no native StateTree — use BehaviorTree addon (godot-behavior-tree) and translate StateTree concepts to BT nodes.

3. **Forgetting AI model facing offset.** AI-generated 3D models face +Z, but Godot forward is -Z. Add PI to target_yaw when computing NPC facing direction.

4. **Underestimating rendering rebuild.** Lumen → SDFGI, Nanite → manual LOD chains, Virtual Shadow Maps → baked/VCT shadows. This is a full rebuild, not a port.

5. **Not preserving sidecar IPC contract.** JSON schemas are the engine↔sidecar contract. Any change breaks cross-referencing. Freeze wire types in SHARED-CONVENTIONS.md.

## Reference

- GDD §06-technical/01-engine-comparison.md — UE5 vs Godot scoring (~200/220 vs ~120/220)
- GDD §06-technical/10-physics-system.md — Mentions Godot Jolt (evaluated but UE5 chosen)
- `godot-game-development` skill — GDScript patterns, MCP setup, pitfalls
- `godot-summer-engine` skill — Detailed workflow, 52-tool catalog, verification ladder
