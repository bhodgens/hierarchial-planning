# Pitfalls 1-2 - Over-Splitting and Wrong-Seam Splitting

When to use: deciding the leaf boundaries during decomposition.
Lesson: split only when the budget forces it, and only at architectural seams - never mid-class.

## Pitfall 1 - Splitting too aggressively

A tree with 20 tiny leaves where 5 well-sized leaves suffice. More nodes = more integration surface, more dispatch overhead. Only split when the 128K limit forces it. If a leaf is under 30K estimated, merge it with a sibling. A trivial tree (master.md + one leaf) has negligible overhead; structure should scale with scope.

## Pitfall 2 - Splitting along wrong seams

Splitting a single class across two leaves because it's "too big." Instead, keep the class in one leaf and split at the module/package boundary. Tight coupling between leaves defeats concurrency and creates integration failures.

If you find yourself needing to split a single class or function across documents, the leaf is the wrong size - make it a branch and decompose along internal responsibilities.

## Valid seams

Module boundaries, API contracts, layer separations, feature independence. Never split mid-class or mid-module; promote the cohesive unit to a branch with sub-leaves instead.
