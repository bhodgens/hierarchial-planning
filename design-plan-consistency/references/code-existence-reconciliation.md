# Code-Existence Reconciliation — Worked Example

Rebellion `plans-godot/` tree, 2026-07-25. Every status cell in master.md and
all 13 branch orchestrators read PENDING, despite ~15.1K lines of GDScript
(63 `.gd`) + 12 `.tscn` scenes existing under `rebellion-godot/`. Task: make
the tables reflect reality without touching code.

## Inventory commands that built the "what exists" picture

```bash
# Per-area file + line counts (the area rollup for the summary)
for d in scripts/*/; do
  area=$(basename "$d")
  count=$(find "$d" -name '*.gd' | wc -l | tr -d ' ')
  lines=$(find "$d" -name '*.gd' -exec cat {} + 2>/dev/null | wc -l | tr -d ' ')
  echo "$area: $count files, $lines lines"
done

# Root-level scripts + scenes separately
find scripts -maxdepth 1 -name '*.gd' -exec wc -l {} +
find scenes -name '*.tscn' -exec wc -l {} +

# Skim headers in bulk to confirm real content (NOT just filename match)
for f in scripts/player/player_controller.gd scripts/player/health_system.gd ...; do
  echo "=== $f ($(wc -l < $f | tr -d ' ')L) ==="; head -12 "$f"; echo
done
```

`search_files target=files pattern='*.gd'` gave the full 63-file list first;
the `head -N` bulk skim is what separated "real impl" from "scaffold."

## Status decisions made (the conservative rubric in action)

| Evidence | Verdict |
|----------|---------|
| 691-line controller w/ GDD speeds, stamina, lean, fall damage | IN_PROGRESS (not run in-engine) |
| `npc_controller.gd` references Beehave but `addons/` dir absent | IN_PROGRESS, Note "BT not functional — addon missing" |
| `save_system.gd` basic JSON, no seed/overlay, no sidecar coord | IN_PROGRESS, Note flags the missing GDD model |
| `integration_tests.gd` custom SceneTree harness, no GUT addon | IN_PROGRESS, Note "leaf requires GUT, not installed" |
| No retargeting script anywhere | PENDING |
| `quest_economy_ui.gd` (139L) UI-only scaffold | IN_PROGRESS for 3 leaves it touches, PENDING for the rest |
| Post-MVP branches 13/14, zero files | PENDING |

Nothing got COMPLETE — no end-to-end run, no passing test suite.

## Duplicate-generation detection (flagged in Notes, not "fixed")

Two code generations coexisted; each pair was cited as "duplicate, not
reconciled" in the relevant leaf Note:
- `player/inventory.gd` (2-hand legacy) vs `player/inventory_system.gd` (carry-slot)
- `weapons/melee_system.gd` + `throw_system.gd` (legacy) vs `combat/combat_manager.gd` + `striking_system.gd`
- `npc/redcoat_ai.gd` (legacy) vs `npc/npc_controller.gd`
- root `save_system.gd` vs `save/save_system.gd`
- two `grapple_system.gd` (combat/ and world/)

## Missing-infra checks that downgraded statuses

```bash
find . -name '*.tres'        # theme resources → only weapon/env .tres, NO UI period theme
ls addons 2>/dev/null        # → no addons dir → no GUT, no Beehave
ls export_presets.cfg        # → absent → branch 14 PENDING
find . -iname '*retarget*'   # → none → leaf 10/02 PENDING
grep -in 'seed\|overlay\|sidecar' save/save_system.gd  # → no hits → seed+overlay not done
```

## Guardrail verification (markdown-only constraint)

```bash
git status --porcelain   # confirm only .md files in the change set
grep -c "$(date -I)" docs/gdd/00-CHANGELOG.md   # → 1 (Rule 1 entry present)
```

Pre-existing dirty `.gd`/`.png` files in the working tree were NOT mine —
verified by checking that every file I patched was a `.md`. Report this
distinction explicitly so the user knows the code constraint held.

## Deliverable shape

1. Files edited (all markdown).
2. Branch-status summary (IN_PROGRESS / PENDING / done=none).
3. **The gap list** — leaves with NO code — called out as a first-class
   deliverable, not buried. This is what the user actually plans from.
