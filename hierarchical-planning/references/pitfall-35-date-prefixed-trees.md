# Pitfall 35 - Date-Prefixed Plan Trees for Codebase Review Sessions

When to use: reviewing a codebase and creating remediation plan trees.
Lesson: one tree per remediation theme, date-prefixed directories under docs/plans/, plus an index document.

When reviewing a codebase and creating remediation plans, use date-prefixed directory names under `docs/plans/` (e.g. `20260723-panic-replacement/`, `20260723-config-extraction/`). This keeps review artifacts organized and sortable by date.

## Pattern

(a) Create one tree per remediation theme.
(b) Prefix with YYYYMMDD for chronological sorting.
(c) Include an index document summarizing all trees.
(d) Create GitHub issues for architectural concerns that need team discussion.

Worked example and patterns: `references/codebase-review-plan-patterns.md` (2026-07-23 session). Related hygiene: check tree numbering against any build-plan index before naming the directory - `references/repo-tree-authoring.md`; and check for a prior COMPLETE tree in the same directory before authoring - `references/plan-directory-collision-checklist.md`.
