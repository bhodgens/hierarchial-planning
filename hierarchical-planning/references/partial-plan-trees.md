# Partial Plan Trees — Avoiding Incomplete Trees

**Context**: When authoring multiple plan trees in one session, it's easy to create a master.md that references leaf documents that don't exist yet.

## Problem

In the 2026-07-23 codebase review session, 4 plan trees were created but only 3 were complete:
- `20260723-panic-replacement/` — ✅ Complete (master + 5 leaves)
- `20260723-dispatcher-stop-wiring/` — ✅ Complete (master + 1 leaf)
- `20260723-config-extraction/` — ✅ Complete (master + 1 leaf)
- `20260723-memorystore-compaction/` — ⚠️ PARTIAL (master only, missing 3 leaves)

The partial tree has a master.md with a Child Index referencing leaves 01, 02, 03 that don't exist on disk. The compliance scanner won't catch this because it only checks existing files.

## Signs of Partial Trees

- Child index lists documents that don't exist on disk
- Master references leaves via pattern like `| 01 | 01-navigate-to-branch.md |` but file is missing
- Compliance scan passes because it only validates structure of existing files

## Prevention

### Before Committing Any Tree

Verify all referenced child documents exist:

```bash
cd plans/feature-name/
for f in $(grep -oP '(?<= \| )[0-9]+-[^ ]+\.md' master.md); do
  test -f "$f" || echo "MISSING: $f"
done
```

If any are missing:
1. **Write them before committing** (preferred), OR
2. **Mark the tree as PARTIAL** in the master header and document which leaves are pending

### When Creating Many Trees at Once

Prefer simplified single-leaf trees for small items rather than full multi-leaf structures. This reduces:
- Risk of partial trees
- Authoring time per tree
- Context needed per tree

Decision rule:
- **Multi-leaf tree**: Only when the feature truly needs decomposition (>128K context)
- **Single-leaf tree**: For everything else (even if estimated at 60-90K)

Example from 2026-07-23 session:
- Panic replacement (5 separate issues) → 5 leaves ✅ justified
- Dispatcher stop wiring (1 simple change) → 1 leaf ✅ correct
- Config extraction (multiple hardcoded values) → 1 leaf ✅ correct (could have been split but wasn't necessary)
- MemoryStore compaction (3 methods) → Should have been 3 leaves but ran out of time ⚠️ partial

## Recovery

If you discover a partial tree after committing:

1. **Complete the missing leaves** ASAP
2. **Add a note** to the master.md: "Note: This tree was committed incomplete on YYYY-MM-DD. Leaves 02 and 03 added on YYYY-MM-DD."
3. **Update the changelog** if the project uses one

## Template Addition

Add this check to Step 6 (Verify the Tree):

```markdown
- [ ] All child documents referenced in Child Index exist on disk
      (run: for f in $(grep -oP '(?<= \| )[0-9]+-[^ ]+\.md' master.md); do test -f "$f" || echo "MISSING: $f"; done)
```
