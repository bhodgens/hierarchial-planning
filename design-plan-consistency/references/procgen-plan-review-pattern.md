# Procgen Plan Tree Review Pattern

> Rebellion session 2026-08-14. Lightweight completion review for a procgen
> plan tree — less than a full drift digest, more than a status check.
> Use when the user says "review plan tree X for completion" or "what's next
> for the procgen pipeline."

## Context

Procgen plan trees have a distinctive structure: Go-side pipeline stages +
Godot-side bridge scripts. A completion review must verify BOTH layers and
the connection between them.

## Verification Steps

### 1. Inventory Go stage files

```bash
ls sidecar/internal/procgen/stage*.go
```

Expected: one file per stage (0 through 13, plus any bonus stages like 8b).
Missing files = unimplemented stages. Note: Stage 1 (terrain) is commonly
deferred — check the plan tree's own notes before flagging.

### 2. Run the test suite

```bash
cd sidecar && go test ./internal/procgen/... -v -count=1
```

Check for:
- All tests passing
- Determinism tests present (`TestPipelineDeterminism`, `TestDeterminismWithStages*`)
- Test counts matching plan tree claims (e.g. "25 tests")

### 3. Check for stubs / TODOs

```bash
grep -rnE 'TODO|FIXME|not_implemented|pass\s*#' sidecar/internal/procgen/
```

Zero matches expected. Any hit = incomplete implementation.

### 4. Verify determinism contract

```bash
grep -n "time\.Now\|rand\.NewSource" sidecar/internal/procgen/*.go
```

Expected: `rand.NewSource` appears once (in `pipeline.go`), `time.Now` never.
Any other RNG source or time call = determinism violation.

### 5. Check Godot bridge scripts exist

```bash
ls rebellion-godot/scripts/world/building_instantiator.gd \
   rebellion-godot/scripts/world/street_lighting.gd \
   rebellion-godot/scripts/world/wavy_glass_material.gd \
   rebellion-godot/scripts/world/wallpaper_palette.gd
```

Note line counts — a 20-line stub is different from a 500-line implementation.
Use `wc -l` on each file to get exact counts for the report.

### 6. Check for staged tests

```bash
ls rebellion-godot/tests/test_building_facades.gd \
   rebellion-godot/tests/test_street_lighting.gd \
   rebellion-godot/tests/test_wavy_glass.gd \
   rebellion-godot/tests/test_wallpaper_palette.gd
```

Tests should exist for each major bridge script. Headless run:
```bash
godot --headless --path rebellion-godot/ -s addons/gut/gut_cmdln.gd \
  --path_to_test_files tests/ --run_selected_only
```

### 7. Verify changelog vs Implementation Record consistency

```bash
grep "10-procgen\|10 | Procedural" docs/gdd/09-pm/02-build-plan-index.md
```

Check:
- Changelog Check date matches the last review date
- Open items in the index match the plan tree's own open items list
- OBSOLETE note present if plan tree is in legacy directory

### 8. Check for partial implementations

Look for:
- Manifest entries without runtime consumers (e.g. `fire_basket_01` in
  `props_manifest.json` but no GLB and no placement code)
- Helper functions without callers (e.g. `GenerateWithRole` in identity
  generator but not wired into `worldspec_delivery.go`)
- Offset constants without explanation (e.g. `godotNPCIDOffset = 1_000_000`)

## Common Open Items in Procgen Trees

| Item | Status | Notes |
|------|--------|-------|
| Stage 1 terrain heightmap | OPEN | Deferred; `WorldSpec.Terrain` zero-valued |
| Stage -1 reference collection | OPEN | Q-proc-2 undecided; no historic map loaded |
| WorldSpec→NPC identity tie | OPEN | Offset by 1e6; sim generates NPCs independently |
| GLB asset presence | Varies | Manifest entries ≠ implementation; check for `.glb` on disk |

## Reporting Format

When delivering a review, use this structure:

```
## Procgen Plan Review — [tree name]

**Status:** IN_PROGRESS (N/M stages complete)

### Implemented
- Go stages: 0, 2-13 (X files, Y tests passing)
- Godot bridge: [script names with line counts]
- Tests: [test names with pass counts]

### Still Open
- Stage N: [reason]
- Bridge item: [what's missing]

### Observations
- [partial implementations, wiring gaps, etc.]
```

## Pitfalls

1. **Don't trust the plan tree's own status claims.** Code may have advanced
   without the tracking table being updated. Always verify by reading files
   and running tests, not by trusting the table.

2. **Manifest entries are not implementation.** A prop in `props_manifest.json`
   with `status: "ready"` but no `.glb` file on disk is NOT implemented.
   Verify actual files exist.

3. **Offset constants hide wiring gaps.** `godotNPCIDOffset = 1_000_000` in
   `worldspec_delivery.go` means "we haven't wired the identity roster yet,
   so we use a magic number to avoid collisions." Flag this as an open item,
   not as a design decision.

4. **Legacy directory plans still need tracking updates.** Even though
   `plans-glm/` is OBSOLETE, the build-plan-index rows and Implementation
   Record entries for those trees must stay current. Agents may still read
   them.

5. **Commit tracking updates separately from code.** When a review discovers
   stale tracking, update the plan files in their own commit — don't bundle
   with unrelated code changes. This makes the audit trail clearer.
