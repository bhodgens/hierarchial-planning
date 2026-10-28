# Pitfall 36 - Compliance Scanner Requires Exact Heading "Completion Tracking Table"

When to use: writing or reviewing orchestrator documents.
Lesson: the heading must be exactly `## Completion Tracking Table` - "Completion Tracking" without "Table" fails.

The scanner checks for the literal string `## completion tracking table` (case-insensitive). Using `## Completion Tracking` (without "Table") fails compliance. This was the most common heading mismatch in one parity session - 4 of 5 orchestrators initially used the wrong heading. Always use the exact template heading.

Sister rule: Pitfall 34 (`## Integration Test Plan`). Full exact-heading list and historical miss examples: `references/compliance-headings.md`. Flat-tree scanner blind spots: `references/meept-flat-plan-trees.md`, `references/plan-authoring-verification.md`.
