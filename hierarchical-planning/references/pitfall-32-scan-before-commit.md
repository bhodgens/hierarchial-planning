# Pitfall 32 - Run the Structural Compliance Scan BEFORE First Commit

When to use: finishing authoring a tree, before the first git commit.
Lesson: author everything, scan, fix, re-scan to green, THEN commit - post-commit structural fixes create noisy history.

The `check_template_compliance.py` scan must run after authoring ALL documents in a tree but BEFORE the first git commit. In one port session, two commits were made before running the scan, revealing: (a) all 8 branch orchestrators missing `## Review Checklist` sections, (b) a single-leaf branch (09-integration-tests) incorrectly structured as a directory with a leaf file instead of a flat leaf at root. Fixing these required patching 9 files and renaming/moving files post-commit - noisy git history for no benefit.

## Sequence

(a) Write all orchestrators and leaves first.
(b) Run: `python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py plans/<name> --strict-leaves`
(c) Fix all issues.
(d) Re-run until `ALL TREES COMPLIANT: True`.
(e) THEN commit.

The scan takes under 1 second - there is no excuse for skipping it. Exact-heading requirements: Pitfalls 34 and 36, `references/compliance-headings.md`. Scanner blind spots (flat trees, inline leaves, forest roots): `references/plan-authoring-verification.md`, `references/inline-leaf-compliance.md`, `references/forest-root-scanner-compliance.md`, `references/execution-pitfalls-meept-gap-trees.md`.
