# Decision Log Supersede & Stale Spec Cleanup — Worked Example

> Rebellion: MetaHuman/decision-log cleanup, 2026-08-12.
> 4 files changed. Follow-up to the plan directory consolidation.

## Context

After consolidating plan directories (plans-glm → plans-godot), the GDD itself
still contained stale references to the old engine's tooling. Three issues:

1. `docs/gdd/07-assets/03-metahuman-pipeline.md` — DRAFT status, never marked
   OBSOLETE despite `06-asset-pipelines.md` declaring MetaHuman "not used."
2. Decision D-13 ("MetaHuman for hero NPCs") — still DECIDED in the decision
   log. The log is append-only, so it cannot be edited in place.
3. `docs/gdd/07-assets/01-asset-standards.md` tier 1b row — still references
   "trellis2cpp on socrates → UE5 import" (stale post-port).

## Fix pattern

### 1. Mark the stale spec doc OBSOLETE

Rewrite the doc with an OBSOLETE header at the top. Retain the original content
below as historical reference — do NOT delete it. The header must:
- State the date and reason
- Point to the replacement doc
- Cross-reference any decision-log entry that supersedes it

### 2. Supersede the decision-log entry (append-only)

Decision logs are append-only. To change a DECIDED entry:

**In the summary table:** Change the status column from `DECIDED` to
`SUPERSEDED by D-NN`.

**In the detail section:** Change `Status: DECIDED` to `Status: SUPERSEDED`
and `Superseded By: —` to `Superseded By: D-NN`.

**Append a new entry (D-31):** Add a new decision with the next available
number. It must include:
- The new decision text
- A rationale that explains WHY the old decision was superseded (engine
  migration, rejected approach, etc.)
- `Status: DECIDED`, `Superseded By: —`
- Source: the authoritative replacement doc

**Update the summary table:** Add the new entry's row to the Decision Index
table at the top of the file.

### 3. Fix stale references in tier tables and prose

Grep for references to the old engine's tooling in spec docs. Common patterns:
- "trellis2cpp" → "Trellis 2" (the model changed names AND engines)
- "UE5 import" → "Godot GLB import"
- "MetaHuman" → the replacement approach (MakeHuman, Rigify, etc.)
- "AccuRig" → "Rigify" or the current rigging approach

Update both structured tables AND prose paragraphs. The tier table row AND the
explanatory paragraph below it both need fixing.

### 4. Add a changelog entry (Rule 1)

Single entry covering all three fixes: spec doc obsolescence, decision-log
supersede, tier table correction.

## Patch sequence

1. `write_file` the OBSOLETE spec doc (full rewrite, not patch — small file)
2. `patch` the decision-log summary table row (one-line status change)
3. `patch` the decision-log detail entry (status + superseded-by fields)
4. `patch` the decision-log summary table to add the new D-31 row
5. `patch` the decision-log detail section to append the D-31 entry
6. `patch` the stale tier table row in the spec doc
7. `patch` the stale prose paragraph in the spec doc
8. `patch` the changelog with a Rule 1 entry

## Verification

```bash
git diff --stat  # confirmed files changed
```

Search for remaining stale references:
```bash
grep -ri "metahuman" docs/gdd/ --include="*.md" | grep -v "OBSOLETE\|superseded\|not used"
```
Any hit that is NOT inside an OBSOLETE/superseded/historical context is a
remaining stale reference to fix.

## Key insight: the follow-up pass IS part of the consolidation

A plan directory consolidation marks plan files obsolete. But the GDD and
decision log reference the old engine too. These are NOT plan files — they
are design documents. They need separate superseding entries and status
changes. A consolidation pass that only touches plan files leaves the design
corpus inconsistent with the new authoritative plans.
