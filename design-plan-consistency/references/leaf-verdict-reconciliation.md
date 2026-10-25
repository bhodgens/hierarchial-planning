# Leaf Verdict Reconciliation — Worked Example

> Post-drift-digest application of SUPERSEDED/PARTIAL/STILL_NEEDED verdicts
> to a plan tree's tracking tables. Rebellion GDD, `plans-ds4f/`,
> 2026-07-19, 20 leaves across 5 branches reconciled against a 19-row changelog.

## Context

- **Project:** rebellion-the-game (colonial-Boston immersive sim, Godot 4).
- **Plan tree:** `plans-ds4f/` — 5 branches, 20 leaves, each branch has an
  `orchestrator.md` with a Completion Tracking Table.
- **Reconciliation source:** `CHANGELOG-RECONCILIATION-REPORT.md` — a read-only
  audit cross-referencing each of the 20 plan leaves against all 19 rows of
  `docs/gdd/00-AUDIT-2026-07-19-CHANGES.md`.
- **Source of verdicts:** The report assigned SUPERSEDED/PARTIAL/STILL_NEEDED
  per leaf with specific instructions for updating each tracking table entry.

## Summary

| Verdict | Count | Leaves |
|---------|-------|--------|
| SUPERSEDED | 10 | housing-tiers, smartphone-intro, first-npc, key-figures-ages, npc-population, first-hour, mythological-reaction, protagonist-voice, frontmatter-todos, appendix-todos |
| PARTIAL | 8 | sleep-fatigue, minor-inconsistencies, new-system-specs, gameplay-specs, vision-gameplay-upgrades, world-npc-upgrades, technical-pm-upgrades, pm-multiplayer-todos, update-audits |
| STILL_NEEDED | 1 | terminology-crossrefs (Task 1: comprehensive terminology sweep) |
| Mixed within leaf | 1 | terminology-crossrefs (Tasks 2-4 SUPERSEDED, Task 1 STILL_NEEDED) |

## Files Updated (6 total)

| File | Change |
|------|--------|
| `master.md` | Branch table: PENDING → RECONCILED with verdict tallies. Detailed leaf table expanded from 9 entries to all 20. Added reconciliation note + updated phase ordering. |
| `01-contradictions/orchestrator.md` | Table: 7 leaves replaced with SUPERSEDED/PARTIAL verdicts + Review Notes. Added reconciliation note flagging A10 no-op and 5→6 tier discrepancy. |
| `02-missing-specs/orchestrator.md` | Table: 5 leaves replaced with 3 SUPERSEDED + 2 PARTIAL. Added reconciliation note flagging bond-NPC location discrepancy. |
| `03-upgrade-drafts/orchestrator.md` | Table: 3 leaves replaced with all PARTIAL. Added reconciliation note about Row 18 (6-need model) and Row 19 pivot. |
| `04-todo-files/orchestrator.md` | Table: 3 leaves replaced with 2 SUPERSEDED + 1 PARTIAL. Added reconciliation note about re-categorizing leaf 02 as verification task. |
| `05-audit-cleanup/orchestrator.md` | Table: 2 leaves replaced with 1 PARTIAL + 1 STILL_NEEDED. Added reconciliation note about resolution markers referencing changelog entries vs plan paths. |

## Procedure Applied

### Step 1 — Batch reads (one assistant turn)
- `read_file` the reconciliation report (687 lines → paginated to 500+187)
- `read_file` all 6 target files (master.md + 5 orchestrator files, 228 + 151 + 140 + 134 + 118 + 110 lines)
- Total context: ~1,400 lines of existing content to understand before editing

### Step 2 — Map verdicts
For each of the 20 leaves, the report provided a verdict and exact Review Notes text.
The mapping was direct (the report was explicit). Key examples:

- **Leaf 02 (housing-tiers):** SUPERSEDED — report said "changelog went to 6 tiers,
  leaf proposed 5" → Review Notes note the discrepancy
- **Leaf 07 (minor-inconsistencies):** PARTIAL — report gave per-task breakdown
  (Tasks 3/4/7 SUPERSEDED, Tasks 1/2/5/6/9/10 STILL_NEEDED) → Review Notes reflect that
- **Leaf 20 (terminology-crossrefs):** STILL_NEEDED (for Task 1 sweep), SUPERSEDED
  (for Tasks 2-4) → Review Notes show the split

### Step 3 — Update orchestrator tracking tables (5 files, sequential patches)
Each orchestrator's Completion Tracking Table was replaced:
- Column headers changed: `Child | Status | Iterations | Review Notes` → `# | Child | Verdict | Review Notes`
- Each leaf row got its verdict + detailed Review Notes from the report
- A footer line explained the verdict values

### Step 4 — Update master.md (branch-level + detailed leaf table)
- Branch tracking table: statuses changed from PENDING to RECONCILED, with verdict tallies
- Detailed leaf table: replaced 9-row partial table with full 20-row table covering all leaves
- Phase ordering section updated to reflect changelog's effective execution of phases 01-02

### Step 5 — Add reconciliation notes (6 files)
Each file got a reconciliation note in its Notes/Changelog Reconciliation section:
- master.md: global summary + cross-cutting issues (housing tiers, bond NPC location, 6-need model)
- Per-branch notes: specific verdict counts, discrepancies, and instructions for next steps

### Step 6 — Verify (re-read key sections)
All 6 files were re-read at their tracking table and notes sections to confirm
patches applied correctly. Every leaf present, all verdicts match the report.

## Key Cross-Cutting Issues Surfaced

1. **Housing tiers (Leaf 02 vs A3):** Changelog resolved to 6 tiers; leaf proposed 5.
   Text needs full rewrite if leaf is re-executed.

2. **Sleep/Exhausted (Leaf 01 vs A10):** A10 found "Exhausted 30h fatigue tier not
   found — no-op." The core-loop doc may have a 2-tier system, not 3. Verify first.

3. **Bond NPC location (Leaf 08 vs B5/Row 13):** B5 says bond NPC "folded into identity
   doc" but Row 13 created standalone `01b-bond-npc-system.md`. Verify actual state.

4. **6-need NPC model (Row 18):** HUNGER/THIRST removed, 8→6 needs. Not referenced by
   any plan leaf. Affects NPC upgrade work (Leaf 14) and maybe bond NPC (Leaf 08).

## Pitfalls Encountered

1. **Table with missing leaves:** The master.md detailed table only covered 9/20 leaves
   (all from branches 01-02). Branches 03-05 had no entries. Had to build the remaining
   11 entries from the reconciliation report rather than editing existing entries.

2. **Status vs Verdict column collision:** The original tables used "Status" for execution
   states (PENDING). The verdicts use a different taxonomy (SUPERSEDED/PARTIAL/STILL_NEEDED).
   Renaming the column to "Verdict" kept the distinction clear.

3. **Structural bugs in leaf text:** Leaf 07 (minor-inconsistencies) mentions G18 forging
   exception in its Context section but has no corresponding Task block. This was captured
   in the Review Notes as a known structural issue.

4. **Report text must be adapted, not copied verbatim:** The reconciliation report's
   instructions say things like "Change tracking table to: 'SUPERSEDED by A3 — ...'".
   The actual table format (columns, markdown syntax) differs from what the report
   describes. The agent must adapt the instruction to the actual table shape.
