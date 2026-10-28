# Ddata manifest fragmentation
When to use: parallel subagents fragment a data manifest.
Lesson: merge discipline and ownership for manifest files.

# Data Manifest Fragmentation Across Parallel Subagents

**Session:** rebellion-the-game Tree 15 (asset retrieval), 2026-07-22
**Pitfall:** #26 in hierarchical-plan-execution skill

## The Problem

When multiple parallel subagents produce structured data files (manifests,
JSON configs, CSV exports), each may use a different data structure even
though the conceptual format is the same. An orchestrator validating only
the assumed format will silently miss data.

## Concrete Example (Tree 15)

| Leaf | Field Used | Structure | Entry Keys |
|------|-----------|-----------|------------|
| L1 (terrain/maps/textures) | `entries` | dict `{id: {field1, field2}}` | flat asset ID |
| L2 (weapons/clothing/props) | `entries` (same!) | BUT with nested `matching[]` / `models_3d[]` arrays | flat asset ID |
| L3 (audio/sfx-ambient/music) | `items` | **list** of dicts `[{{id: X, note: Y}}, ...]` | `asset_id` or `id` field |

**The trap:** Orchestrator checks `entries.keys()` for all manifests → L3's
data is completely invisible because it uses `items` not `entries`.

## Detection Pattern

```python
import json
d = json.load(path)
print("Top-level keys:", sorted(d.keys()))
if "entries" in d:
    print(f"entries ({len(d['entries'])})")
    print("sample key:", list(d["entries"].keys())[:3])
elif "items" in d:
    print(f"items ({len(d['items'])}) — DIFFERENT SCHEMA!")
    print("first item keys:", list(d["items"][0].keys()))
elif "finds" in d:
    print(f"finds ({len(d['finds'])}) — ANOTHER DIFFERENT SCHEMA!")
```

Always check the top-level keys first, before diving into any specific field.

## Prevention

1. **Specify the schema in every dispatch context.** Include a short example:
   ```
   MANIFEST FORMAT:
   {"directory": "category/", "entries": {"ID-001": {"url": "...", "source": "..."}}}
   ```
2. **Validate each leaf against its own schema.** Don't assume L1's format
   is what L2/L3 should produce. Check `d.keys()` before accessing `d.entries`.
3. **If leaves share a package/directory**, enforce a single schema in the
   dispatch context: "All manifests MUST use the `entries` dict format."

## Resolution

After discovery, repair_manifests.py can reconcile the disk state regardless
of manifest schema, because it scans actual files rather than parsing manifest fields.
But the orchestrator still needs to know what each leaf actually produced to verify
completeness correctly.