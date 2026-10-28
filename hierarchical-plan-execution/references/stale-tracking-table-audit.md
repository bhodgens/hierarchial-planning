# Sstale tracking table audit
When to use: tracking table diverges from reality.
Lesson: audit table vs disk and branch state before resuming a tree.

# Stale Tracking Table Audit

> The highest-leverage time saver in plan execution. A 5-minute audit can
> save hours of re-implementing work that's already done.

## The Problem

Plan tracking tables (master.md completion tables, orchestrator leaf tables)
are updated manually by prior sessions. They fall behind the actual codebase
because:

- Sessions implement code but forget to update tracking tables
- Multiple parallel sessions work on different branches; each updates its own
  table but not the master
- Remediation work (bug fixes, deduplication) happens in side trees that don't
  update the main tracking table
- Addons get installed, themes get created, legacy files get deleted — none
  of which is reflected in tracking notes written months earlier

## The Audit (5 minutes)

Before dispatching ANY implementation subagents, run these checks:

### 1. File inventory

```bash
find <project>/scripts -name '*.gd' -not -path '*/addons/*'   # GDScript
find <project> -name '*.go' -not -path '*/vendor/*'            # Go
```

Count files and lines (`wc -l`). Compare against what the tracking table
claims. If the codebase has 174 files / 49.7K lines but the table says "63
files / 15.1K lines," the table is stale.

### 2. API verification

For each leaf's spec, grep for the key functions/constants it requires:

```bash
grep -rn 'WALK_SPEED\|SPRINT_SPEED\|CROUCH_SPEED' scripts/player/
grep -rn 'func save_game\|func load_game\|seed.*overlay' scripts/save/
grep -rn 'StreamPeerTCP\|init_ack\|send_player_action' scripts/sidecar/
```

If the functions exist with correct values, the leaf is done.

### 3. Dependency/addon check

Verify claimed-missing things are actually missing:

```bash
ls <project>/addons/beehave/     # "NOT installed" in table?
ls <project>/resources/themes/   # "NO theme found" in table?
```

### 4. Duplicate detection

Check for files that remediation work was supposed to delete:

```bash
find . -name 'redcoat_ai.gd'     # Should be deleted
find . -name 'inventory.gd'      # Legacy duplicate
```

### 5. Test suite baseline

Run the test suite ONCE to establish ground truth:

```bash
# Godot
/Applications/Godot.app/Contents/MacOS/Godot --headless --path <project> \
  -s addons/gut/gut_cmdln.gd -gconfig=.gutconfig.json -gexit

# Go
go test ./... -short
```

Record the pass/fail count. Any failures from uncommitted work in other
branches are pre-existing — don't try to fix them.

## When Tables Are Stale

Do NOT dispatch implementation subagents. Instead:

1. **Mark leaves COMPLETE** in the tracking table with audit notes citing
   specific file:line evidence
2. **Only implement leaves that genuinely have gaps** — these are the ones
   where grep returns zero hits for the required functions
3. **Run the test suite** after any changes to confirm no regressions
4. **Commit the tracking table updates** separately from code changes

## Real-World Instance

**rebellion-the-game Godot port (2026-08-07):** The master.md tracking table
listed 8 of 14 branches as IN_PROGRESS with notes like:
- "Beehave behavior tree NOT installed (npc_controller references it)"
- "NO period .tres theme found"
- "save_system.gd (155L) — basic JSON only"
- "animation_controller.gd (566L); retargeting leaf has NO code"

Actual codebase state:
- Beehave WAS installed (`addons/beehave/` + 6 BT action nodes)
- Period theme existed (`resources/themes/period_theme.tres`)
- `save_system.gd` was 928L with full seed+overlay model
- Retargeting code existed (`retargeting_helper.gd`, `bone_name_map.gd`,
  `retarget_all.gd` from remediation tree 15)
- 174 GDScripts, 49.7K lines, 977/987 GUT tests passing

The entire "implementation" session was actually a 30-minute audit +
tracking-table update, not a multi-hour implementation effort. All 8 branches
were marked COMPLETE based on code evidence.
