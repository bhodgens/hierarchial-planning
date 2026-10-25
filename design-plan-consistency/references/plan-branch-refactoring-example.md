# Plan Branch Refactoring — Worked Example

Rebellion 06-ui-menus: 3 stale leaves → 8 leaves matching GDD §11 (473 lines).

## Context

- Project: colonial Boston immersive sim, Godot 4.7.1 + Go sidecar
- GDD written for UE5 (UMG/Common UI/C++), project uses Godot (GDScript/Control)
- Existing plans: 3 leaves (hud-ingame, menus-rebinding, quest-economy-ui)
- GDD spec: docs/gdd/02-gameplay/11-menu-and-ui-system.md (473 lines)

## Gap Analysis Results

### Missing entirely (CRITICAL)
- Main menu / New Game wizard (5-step: character, save mode, AI tier, seed, begin)
- Inventory radial wheel (body-slot layout, encumbrance tiers)
- Journal as 8-page physical book (People/Factions/Events/Knowledge/Map/Codex/Profile/Notes)
- Dialogue UI (token streaming, options 1-5, free-text, no pause)
- Death/failure screens (Standard cinematic + Ironman memorial)
- Loading screens (parchment progress bar, period text)
- Splash/legal sequence (first launch)
- UI Manager / overlay priority stack (dialogue > journal > inventory > pause > HUD)
- Aesthetic system (Caslon font, parchment palette hex values, leather frames, menu audio)

### Shallow (HIGH)
- HUD: plan had always-on bars; GDD says default Standard mode is EMPTY (contextual cues only, 3 modes)
- Settings: plan had 3 categories; GDD has 5 tabs with 40+ options
- Pause menu: missing Journal/Inventory buttons, Ironman "Save and Quit"

### Stale orchestrator (MEDIUM)
- Listed 2 leaves but 3 existed; leaf 03 untracked in completion table

## Engine Translation Table (UE5 → Godot)

| UE5 Concept | Godot Equivalent |
|---|---|
| UMG Widget Blueprint | .tscn scene with Control nodes |
| CommonActivatableWidget stack | UIManager autoload with overlay priority stack |
| Common Input routing | _input() + set_input_as_handled() for menus; _unhandled_input() for gameplay |
| UGameUserSettings | ConfigFile or JSON in user://settings.cfg |
| FSlateStyle / StyleSet | Godot Theme resource (.tres) |
| SetGlobalTimeDilation | Engine.time_scale |
| UGameplayStatics::SetGamePaused | get_tree().paused = true + process_mode |
| Enhanced Input mapping contexts | InputMap actions + runtime rebinding via InputMap.action_add_event() |

## New Leaf Structure (8 leaves)

1. 01-ui-manager-theme — UIManager autoload (overlay priority stack, pause control) + period Theme resource (frozen aesthetic constants)
2. 02-main-menu-newgame — Main menu, 5-step New Game wizard, splash/legal, loading screens
3. 03-pause-settings — Pause menu, 5-tab settings, keyboard rebinding with persistence
4. 04-hud-contextual — 3 HUD modes (Minimal/Standard/Full), diegetic cues (no always-on bars)
5. 05-journal-book — 8-page physical book, quick-look at 10% time dilation, hand-drawn map
6. 06-inventory-radial — Body-slot radial wheel, encumbrance tiers, companion trade
7. 07-dialogue-ui — Token streaming, options 1-5, free-text, real-time (no pause)
8. 08-death-loading — Standard/Ironman death screens, loading screens

## Key Patterns

1. **Aesthetic constants frozen in orchestrator**: hex palette, font names, audio cues listed once in orchestrator, referenced by all leaves. Prevents leaves from inventing their own colors.

2. **GDD values inlined in leaves**: e.g., "attention vignette when NPC attention > 7" not "per GDD perception thresholds". Every threshold, timing, key binding stated explicitly.

3. **Self-verification checklist maps 1:1 to GDD**: each checkbox corresponds to a specific GDD requirement, making review mechanical.

4. **Parallel dual-audit after refactor**: dispatched two subagents — (A) GDD completeness audit of all other branches, (B) cross-plan-tree gap review (plans-glm sidecar features vs plans-godot client consumption). Both run independently, ~50 files each.

## Time Estimate

- Read GDD spec + existing leaves: ~5 min
- Gap analysis: ~5 min
- Write orchestrator: ~5 min
- Write 8 leaves: ~15 min (batched 4+4)
- Delete old files + update master.md: ~2 min
- Dispatch parallel audits: ~2 min
- Total active work: ~35 min (audits run in background)
