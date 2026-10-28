# Changelog File Format Convention


When to use: project needs a changelog another agent can reconcile against plan trees.
Lesson: table with Date/Session/Scope/Changes/Verification columns and stable decision IDs.
> The canonical format for a project-level changelog that another agent can
> review and reconcile against plan trees. See SKILL.md §Plan Reconciliation
> and `references/changelog-review-digests.md` for the reconciliation workflow.

## Purpose

A changelog in this format serves as the single source of truth for *what changed
in the design corpus since the last plan tree was authored or reconciled*. It is
designed so that a read-only subagent can cross-reference it against a plan tree's
spec sources in one pass (the changelog-review digest — see
`references/changelog-review-digests.md`).

## File Location and Naming

Place at the root of the document corpus: `docs/gdd/00-CHANGELOG.md` for GDD
projects, or `<project-root>/CHANGELOG.md` for non-GDD projects. The leading
`00-` prefix ensures it sorts first in directory listings.

## File Structure

### Header

```
# GDD Change Log

> Revision history for the <project name> Game Design Document.
> Each entry: date, agent/session, scope, changes applied, verification status.
> This file is designed for another agent to review — use grep + read_file
> against cited paths to verify claims.
```

### Table Columns

| Column | Content | Rules |
|--------|---------|-------|
| **Date** | ISO date of the session | Same date for batch entries |
| **Session** | Short descriptive name (e.g. "procedural rules framework", "mechanical fixes", "perspective pivot") | Unique per row; describes the session's purpose, not just the author |
| **Scope** | Section-wide, GDD-wide, or specific doc list | Broad enough to group related changes |
| **Changes** | Bullet-list of every edit applied. Group by category (mechanical fixes, design decisions, subagent work). Include decision IDs (A1, B1, D1) and file paths. | **Must be detailed enough for a reconciliation subagent to match against plan leaves.** A changelog entry that says "multiple fixes" is useless for reconciliation. Each individual change should cite at least the affected file(s) and the nature of the change. |
| **Verification** | How the changes were verified (subagent report, unified diff, file existence check, grep results). Status for pending work. | Honest about what's verified vs what's still pending. |

### Row Order

Newest entry at the **bottom** (chronological order, oldest first). This lets
a reconciliation subagent scan from the last row they know about to the end
of the file.

## Entry Content Conventions

### Grouping

Group related changes under bold headers within the Changes column:

```
**Mechanical fixes (A1-A10):** A1: ... A3: ... A7: ...
**Design decisions (B1-B10):** B1: ... B2: ...
**Subagent work (S1-S18, R1-R13, D1-D14):** ... 
```

### Decision IDs

Assign stable IDs to decisions (A1-A10 for mechanical, B1-B10 for design,
D1-D14 for ratified decisions, S1-S18 for subagent work). These IDs become
the cross-reference points for reconciliation: a plan leaf that is
SUPERSEDED by "A3" or "B1" is immediately obvious on grep. Avoid
session-relative IDs ("fix #3 of the 2nd batch") that are meaningless outside
the session.

### File Paths

Cite full relative paths from the project root: `docs/gdd/02-gameplay/10-death-and-failure.md`.
File paths are the primary reconciliation key — a plan leaf targeting that file
can be matched against changelog entries touching the same path.

### Verification Statements

Be specific about verification method:
- "Verified by unified diff — all patches applied." (for patch() edits)
- "Verified by subagent report — 5 files, 18 patch operations." (for delegated work)
- "Verified — 961 relative links, 0 broken. 0 line-number corruption." (for grep checks)
- "Pending — subagent still running" (for in-flight work)
- "write_file — all created." (for new file creation)

## Example Row

```
| 2026-07-19 | Mechanical fixes | 8 fixes applied via patch(): doctor price
  harmonization (2 files), MASTER-OUTLINE physics claim, LLM population 300→200,
  companion pool clarification, smartphone in intro scene, player-character sleep
  claim corrected, food/stamina cross-ref, stranger penalty cross-ref. |
  Verified by unified diff — all patches applied. |
```

## Agent-Reviewable Design

This format is optimized for an agent to answer "has the design changed since I
last looked, and if so, what?" The reconciliation subagent (see
`references/changelog-review-digests.md`) reads the file from the last known
row to the end, maps each entry against the plan's spec sources via file paths
and decision IDs, and reports drift. Key design choices that enable this:

- **File paths in every entry** — the primary join key between changelog and plan
- **Stable decision IDs** — secondary join key for SUPERSEDED annotations
- **Chronological order, oldest first** — allows efficient "since last verification date" scanning
- **Verification column** — distinguishes completed work from in-flight work
- **Detailed Changes, not summaries** — a single-line "fixed bugs" is not reviewable
