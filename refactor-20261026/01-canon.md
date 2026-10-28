# 01 - Shared Canon + Write-Path Policy - Implementation Leaf

## Meta

- **Parent:** master.md
- **Scope:** One new reference file (the canon) plus a pointer line in the four SKILL.md files. Nothing else changes.
- **Dependencies:** 00T (scripts exist and run RED)
- **Estimated Context:** ~30K
- **Concurrency Group:** 1

## Goal

Create `hierarchical-planning/references/plan-tree-canon.md` containing the shared model of the whole skill family, including the write-path policy that stops future diary accretion. This file becomes the single source the other skills link to instead of re-explaining the model.

## Context

The four skills re-explain the same lifecycle with different words (not verbatim - measured 0% overlap - but conceptually). Divergence already exists in commit-ownership details. Extracting the canon first means leaves 02-04 link out instead of carrying their own versions.

Verified anchors:
- Canon lands at ~/.hermes/skills/software-development/hierarchical-planning/references/plan-tree-canon.md
- The pointer line goes after the `## Overview` heading of each of: hierarchical-planning/SKILL.md, hierarchical-plan-execution/SKILL.md, subagent-driven-development/SKILL.md, writing-plans/SKILL.md
- verify_canon.py (from 00T) is the acceptance command

## Interface Contracts (From Parent)

Section IDs are frozen (contract C1): C1-Nodes, C1-Status, C1-Commit, C1-Dispatch, C1-Review, C1-Sizing, C1-State, C1-WritePath. File <= 6,000 chars. Content rules per contract C2.

## Tasks

### Task 1: Write the canon file

**Objective:** One file, all eight sections, terse imperative rules.

Section content requirements:

- C1-Nodes: define master.md / orchestrator.md / leaf roles in <=4 lines each.
- C1-Status: the 8 status values as a table (PENDING, TESTS_IN_PROGRESS, TESTS_VALIDATED, IN_PROGRESS, IMPLEMENTED, REVIEWED, COMPLETE, BLOCKED) with one-line meanings.
- C1-Commit: only orchestrators commit; implementers never git commit or git add; dispatch contexts say "Do NOT commit".
- C1-Dispatch: delegate_task batch shape: tasks[] items each with goal + context; single-task mode requires top-level goal.
- C1-Review: review in-session by main model, never delegated; rationale one line (delegated reviewers inherit the subagent model).
- C1-Sizing: 128K context rule; ~25-minute wall-clock subagent budget; split at architectural seams; 30K floor to merge with sibling.
- C1-State: tracking table is the single source of truth; volatile state never lives in protocol files; per-tree STATE.md pattern when a tree runs long.
- C1-WritePath: the full policy - SKILL.md curated, never appended with dated entries; new lessons = one INDEX line + reference file with trigger header; quarterly consolidation; 2-quarter eviction to archive; repo-specific lessons stay in repo skills.

### Task 2: Insert pointer lines

**Objective:** One line after `## Overview` in each of the four SKILL.md files:
`> Shared model and write-path policy: references/plan-tree-canon.md (C1-* sections). Read once; this skill assumes it.`

**Files (modify):** the four SKILL.md files listed above. One line each, nothing else.

**Step 1: Apply with patch (not write_file) so no other byte changes**
**Step 2: Run gates**

Run: `python3 scripts/verify_canon.py` - Expected: EXIT 0.
Run: `python3 scripts/verify_sizes.py` - Expected: still FAILs budgets (later leaves fix that) but the pointer lines must not change any byte count beyond +~120 per file.

## Self-Verification Checklist

- [ ] verify_canon.py exits 0
- [ ] All 8 section IDs present and spelled exactly per C1
- [ ] Canon <= 6,000 chars (verify with wc -c)
- [ ] Four pointer lines inserted; diff vs /tmp backup shows only those lines
- [ ] No em-dashes in the canon

## Review Checklist (For Review Agent)

- [ ] Canon rules do not contradict any existing skill (spot-check C1-Commit vs HP "Commit Policy" section and C1-Status vs HP "Completion Tracking" table)
- [ ] C1-WritePath forbids exactly the patterns found in the source analysis (SKILL.md appends, diary sections, digest indexes)
- [ ] No session dates or campaign names appear in the canon (invariants only)

**DO NOT COMMIT.** Orchestrator archives after review.

## Notes

The canon is deliberately small. Anything that grows it belongs in a reference file it links to.
