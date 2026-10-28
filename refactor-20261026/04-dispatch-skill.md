# 04 - Rewrite subagent-driven-development SKILL.md - Implementation Leaf

## Meta

- **Parent:** master.md
- **Scope:** SDD SKILL.md 99,998 -> <=25,000 chars; build a references/INDEX.md for its 17 existing reference files. Extraction of narratives to refs.
- **Dependencies:** 01 (canon)
- **Estimated Context:** ~60K
- **Concurrency Group:** 2

## Goal

SDD has the same disease as HP/EX: a ~100K SKILL.md that grew by appends. Apply the same treatment: terse protocol + registry + INDEX routing.

## Context

Verified anchors:
- Target: ~/.hermes/skills/software-development/subagent-driven-development/SKILL.md (99,998 chars - read in slices)
- 17 reference files already exist under references/ (adversarial-test-infrastructure.md, delegation-size-limits-and-splits.md, orchestrator-fix-and-dispatch-contracts.md, parallel-dispatch-git-discipline.md, subagent-dispatch-patterns.md, plan-forest-assessment.md, go-project-conventions.md, etc.)
- No INDEX.md exists yet - create one (C5 format).
- SDD's dispatch + review loop duplicates canon C1-Dispatch/C1-Review/C1-Commit: link, do not restate.

## Interface Contracts (From Parent)

C1 (canon link), C3 (registry), C4 (ref headers for new files), C5 (new INDEX). Budget: SKILL.md <=25,000.

## Tasks

### Task 1: Inventory and map

**Objective:** Read the full SKILL.md in slices. Produce a section map: which sections are (a) core protocol, (b) narrative/worked examples, (c) duplicates of canon content, (d) already mirrored in a reference file. The map drives Tasks 2-4 and goes in your report.

### Task 2: Rewrite core

**Objective:** New SKILL.md <=25,000 chars: frontmatter (related_skills trimmed to hierarchical-planning, hierarchical-plan-execution), Overview + canon pointer, When to Use, the two-stage review loop (spec compliance then code quality) in <=15 lines, fresh-subagent-per-task dispatch protocol linked to C1-Dispatch, Pitfall Registry (C3 format), Maintenance (C1-WritePath pointer).

### Task 3: Extract narratives

**Objective:** Worked examples, long sub-patterns, and per-domain playbooks move to reference files (new ones with C4 headers, or merge into the 17 existing where topical). Registry lines route to them.

### Task 4: Create INDEX.md

**Objective:** references/INDEX.md covering all files (existing 17 + new ones from Task 3), C5 format.

### Task 5: Run the gates

verify_sizes.py + verify_index.py + verify_styles.py. Archive to /tmp/skill-refactor-backup-20261026/gate-4.txt.

## Self-Verification Checklist

- [ ] SKILL.md <=25,000 chars (wc -c in report)
- [ ] Section map delivered; every removed narrative landed in a ref file
- [ ] INDEX.md exists and verify_index.py exits 0
- [ ] Two-stage review loop preserved (spec compliance + code quality)
- [ ] Canon linked; dispatch/commit rules not restated
- [ ] No em-dashes

## Review Checklist (For Review Agent)

- [ ] An agent can run a subagent-driven task session from SKILL.md alone
- [ ] 4 random registry DETAIL targets exist and contain the lesson
- [ ] No verbatim duplication with HP or EX sections (this refactor must not copy text between skills - link the canon instead)

**DO NOT COMMIT.** Orchestrator archives after review.

## Notes

Keep SDD's distinct value (two-stage review, per-task fresh subagents, delegation size limits) - the refactor removes accretion, not its identity.
