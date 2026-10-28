# Pitfall 7 - Circular Dependencies Between Leaves

When to use: the leaf dependency graph contains a cycle.
Lesson: break cycles by extracting the shared dependency into a third leaf both depend on.

Leaf A depends on B, B depends on A. Neither can dispatch first, and any wave-based execution deadlocks or silently serializes into undefined order.

## Fixes

1. **Extract the shared dependency.** The cycle usually exists because both leaves touch the same type, constant table, or helper. Move it into a new leaf C that both A and B depend on. C dispatches first, A and B dispatch in parallel.
2. **Restructure the decomposition.** If the "shared dependency" is really one cohesive unit, the seam was wrong (Pitfall 2) - merge A and B into one leaf, or split along the real module boundary instead.

## Prevention

- Draw the dependency graph before writing leaf documents (Step 6 checklist: "Dependency graph has no cycles - draw it if unsure").
- Freeze shared types in the parent's Interface Contracts section so siblings consume a contract instead of depending on each other's files.
- Same-package type dependencies can still share a wave when the plan pins full struct definitions in the consumer's leaf - see `references/same-package-type-dependency-waves.md`.
