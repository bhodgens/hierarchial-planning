# Plan Directory Consolidation — Worked Example

> Rebellion: `plans-glm/` → `plans-godot/` consolidation, 2026-08-12.
> 26 files marked across 17 trees + 4 cross-cutting files. No code changes.

## Context

The project migrated from UE5.8 to Godot 4.7.1. Two plan forests existed:
- `plans-glm/` — original 17-tree forest (Go sidecar + UE5 client)
- `plans-godot/` — post-port forest (Go sidecar unchanged, Godot client)

The Go sidecar plans in `plans-glm/` were all implemented (code in `sidecar/`,
tested). The UE5-specific plans were superseded by `plans-godot/` equivalents.
One tree (17-character-rigging) was already STALE. The asset-generation tree
(16) used a rejected approach (whole-body Trellis + AccuRig).

## Disposition categorization

Three categories, assigned per tree:

1. **IMPLEMENTED (13 trees):** Go sidecar plans (02-gossip through
   14-events-faction). Code lives in `sidecar/internal/*`, all tested.
   No successor plan — the code IS the deliverable.

2. **OBSOLETE / superseded (3 trees):** 01-sandbox, 09-save (UE5 side),
   15-assets-retrieval. Each has a direct replacement in `plans-godot/`.

3. **OBSOLETE / stale (2 trees):** 16-assets-generation (rejected approach —
   whole-body + AccuRig + UE5), 17-character-rigging (already STALE —
   UE5 Mannequin + AccuRig).

## File marking pattern

Each file got a blockquote header inserted after the first `#` heading:

```
# <original heading>

> **OBSOLETE — 2026-08-12.** <one-line reason>. <successor or code location>.
> See `plans-glm/master.md`.
```

Three header variants:
- OBSOLETE (UE5-specific, superseded) — for trees replaced by plans-godot
- IMPLEMENTED — for Go sidecar trees where code is the deliverable
- HISTORICAL — for cross-cutting files retaining reference value

## Root master.md rewrite

The legacy `plans-glm/master.md` was rewritten as a redirect page:
- OBSOLETE banner with date
- Migration map table (17 rows: tree → status → successor/code location)
- Cross-cutting files table (4 rows: file → status)
- "For new work" directive pointing to plans-godot/

## Build-plan-index update

Two changes:
1. Consolidation note blockquote at the top of "Implementation Plan Trees"
2. "Plan tree location" footer rewritten from `plans-glm/` to `plans-godot/`
   with a note that plans-glm/ is OBSOLETE

## Changelog entry

Single Rule 1 entry recording: which directory is authoritative, which is
obsolete, file count marked, and the disposition breakdown.

## Patching technique

Used `execute_code` with `read_file` to get the exact first line (heading)
of each of the 17 master.md files. Then batched `patch` calls with the exact
heading as `old_string` and heading + header block as `new_string`.

4 leaf files (01-sandbox/05-tts-playback.md, 02-gossip/01-02-03-*.md) had
different headings than expected — initial patches failed. Re-read first 2
lines with `read_file limit=2` to get exact text, then retried successfully.

## Verification

```bash
git diff --stat  # confirmed 29 files changed, 170 insertions, 310 deletions
```

All changes were markdown headers — no code modified.

## Follow-up work (completed in the same session)

These items were flagged as observations after the directory consolidation
and then immediately resolved. The pattern is documented in
`references/decision-log-supersede-and-stale-spec-cleanup.md`:

- GDD `03-metahuman-pipeline.md`: marked OBSOLETE with redirect to
  `06-asset-pipelines.md`
- Decision D-13: superseded by new D-31 (MakeHuman + Rigify + Trellis)
- `01-asset-standards.md` tier 1b + hero-NPC paragraph: updated from
  trellis2cpp/UE5/MetaHuman → Trellis 2/Rigify/Godot
- Changelog Rule 1 entry added for the cleanup

**Still open** (not resolved):
- The motion-matching plan (`plans-godot/motion-matching/MASTER.md`) does not
  appear in the build-plan-index table
