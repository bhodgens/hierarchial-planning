# 03 - hierarchical-planning Pitfall Registry + INDEX - Implementation Leaf

## Meta

- **Parent:** master.md
- **Scope:** HP SKILL.md 99,911 -> <=42,000 chars; HP references/INDEX.md 10,932 -> <=4,000 chars. Extract pitfall narratives and session-log sections to reference files.
- **Dependencies:** 01 (canon)
- **Estimated Context:** ~80K
- **Concurrency Group:** 2

## Goal

Keep HP the authoritative authoring skill but shrink it: pitfalls become a registry (C3), the "Session Pitfall Additions" diary moves out, the "Reference Documents" section folds into INDEX.md, and concept duplication with the canon is replaced by links.

## Context

Measured structure (read in slices; 99,911 chars - skill_view caps out, use read_file offset/limit):
- `## Common Pitfalls` 38,842 chars: 42 numbered entries, most multi-paragraph with worked-example narration (session dates, campaign names like plans-glm, plans-ds4f, meept).
- `## Session Pitfall Additions` ~6,498 chars at the end: dated diary entries + stray checklist items.
- `## Reference Documents` ~6,505 chars: prose descriptions of ~20 reference files - duplicated duty with references/INDEX.md.
- Several long alternatives sections (Audit-Driven, Gap-Analysis, Ops & Asset Pipeline, forest authoring 6.5-6.8) that are technique recipes, not core protocol.
- Cross-references to pitfalls by number ("Pitfall 12", "Pitfall 25 variant") appear throughout - the registry MUST keep the same numbering so those references stay valid.

Verified anchors:
- Target: ~/.hermes/skills/software-development/hierarchical-planning/SKILL.md
- INDEX: ~/.hermes/skills/software-development/hierarchical-planning/references/INDEX.md
- Canon already exists at references/plan-tree-canon.md (from 01) - link it from Overview.
- Existing refs cover several pitfalls already: tests-first-gate.md (46), contract-verification-digests.md (21), changelog-review-digests.md (22), cross-corpus-concept-replacement.md (23), authoring-checklist.md (tail checklist), dispatch-recovery.md, wave-execution-patterns.md.

## Interface Contracts (From Parent)

C1 (canon link), C3 (registry format <=500 chars, keep original pitfall numbers), C4 (ref headers), C5 (INDEX format). Budgets: SKILL.md <=42,000; INDEX <=4,000.

## Tasks

### Task 1: Extract pitfall narratives

**Objective:** For each of the 42 pitfalls, move the narrative (worked examples, sub-exception detail) into or alongside an existing reference file, or create references/pitfall-<n>-<slug>.md with C4 header. Keep in SKILL.md only the C3 registry line. Preserve the numbering 1-42 exactly. The 4 exception/sub-entries under Pitfall 4 and the strategy list under Pitfall 13 move with their parent's narrative.

**Rule:** registry entries keep the TRIGGER + ACTION (the decision-relevant part); DETAIL carries the file. Numbering preserved means every existing "see Pitfall N" cross-reference still resolves.

### Task 2: Extract Session Pitfall Additions

**Objective:** Move each dated bullet to a reference file (several already have homes: gdscript-bulk-dispatch.md, parallel-sibling-leaf-contracts.md, intent-gate-forensics-2026-09-05.md). Delete the section heading entirely. The stray checklist items at its end merge into references/authoring-checklist.md if not already present.

### Task 3: Compress technique sections

**Objective:** For `## Alternative: Audit-Driven Decomposition`, `## Alternative: Gap-Analysis-Driven Decomposition`, `## Alternative: Ops & Asset Pipeline Trees`, and Steps 6.5-6.8: keep in SKILL.md a decision table (when to use which pattern, <=2 lines each) + a registry line pointing to the full recipe reference. Full recipes already exist as refs (audit-driven-gdd-planning.md, gap-analysis-forest-pattern.md, asset-pipeline-plan-pattern.md, multi-tree-forest-pattern.md, open-questions-walkthrough.md). Where a recipe lacks a ref file, create one.

### Task 4: Fold Reference Documents section into INDEX

**Objective:** Delete the in-SKILL.md `## Reference Documents` prose list. INDEX.md becomes the single routing table (C5 format) covering all ~100 reference files.

### Task 5: Replace restated model content with canon links

**Objective:** Sections that restate canon material get one-line pointers: The 128K Rule (keep the budget table - it is detail; link C1-Sizing), Commit Policy (link C1-Commit, keep the 4-step flow), Completion Tracking (link C1-Status, keep the table - it is the authority), Dispatch Protocol shape (link C1-Dispatch, keep HP-specific steps 0-5). Do not delete HP-specific detail; only delete re-explanations of the shared model.

### Task 6: Run the gates

verify_sizes.py + verify_index.py + verify_styles.py. Archive to /tmp/skill-refactor-backup-20261026/gate-3.txt.

## Self-Verification Checklist

- [ ] SKILL.md <=42,000 chars; INDEX <=4,000 chars
- [ ] All 42 pitfall numbers present in the registry, in order, same numbers
- [ ] `## Session Pitfall Additions` gone; every bullet landed in a ref file
- [ ] Spot-check 5 pitfalls: DETAIL file exists and contains the narrative (grep a distinctive phrase)
- [ ] Every internal "Pitfall N" cross-reference still resolves to the right registry line
- [ ] verify_index.py exits 0; no em-dashes
- [ ] Canon linked; shared-model restatements replaced by pointers

## Review Checklist (For Review Agent)

- [ ] An agent authoring a new tree can do so from SKILL.md alone (protocol completeness check)
- [ ] Pitfall 12 and Pitfall 13 (the two longest) kept their operational checklists - either inline if <=500 chars total, or as an explicitly referenced file
- [ ] Technique decision table covers all 4 alternatives with correct routing
- [ ] INDEX covers reference files that exist (no orphans in, no silent drops)

**DO NOT COMMIT.** Orchestrator archives after review.

## Notes

The 42,000 budget is deliberately roomier than EX's: HP is the authoring authority and keeps its sizing tables, tree examples, and Step 6 verification gates inline.
