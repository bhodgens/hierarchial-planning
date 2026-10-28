# Skill-Family Token Refactor - Final Report

Date: 2026-10-26. Plan tree: /Users/caimlas/plans/20261026-skill-token-refactor/ (master + 7 leaves, all COMPLETE).
Skill root: ~/.hermes/skills/software-development/. Pre-refactor snapshot: /tmp/skill-refactor-backup-20261026/pre-refactor/.

## 1. Before/after - the 8 budgeted files + 2 new files

Char counts measured by UTF-8 decode of the snapshot and current files (both units shown; the earlier 53,972 figure was bytes - 53,657 is the char count).

| File | Pre chars | Post chars | Pre ~tok | Post ~tok | Delta |
|---|---|---|---|---|---|
| hierarchical-planning/SKILL.md | 99,391 | 41,956 | 24,848 | 10,489 | -58% |
| hierarchical-plan-execution/SKILL.md | 53,657 | 11,986 | 13,414 | 2,997 | -78% |
| subagent-driven-development/SKILL.md | 99,998 | 13,173 | 25,000 | 3,293 | -87% |
| writing-plans/SKILL.md | 14,951 | 14,973 | 3,738 | 3,743 | +0.1% (em-dash fix + pointer) |
| EX references/INDEX.md | 59,768 | 7,978 | 14,942 | 1,995 | -87% |
| HP references/INDEX.md | 10,842 | 3,991 | 2,711 | 998 | -63% |
| HP templates/leaf-template.md | 7,439 | 4,984 | 1,860 | 1,246 | -33% |
| HP templates/master-template.md | 13,494 | 6,714 | 3,374 | 1,679 | -50% |
| SDD references/INDEX.md (new) | - | 4,934 | - | 1,234 | new |
| HP references/plan-tree-canon.md (new) | - | 4,317 | - | 1,079 | new |

## 2. Session token-load (skill-trigger cost)

A session triggering all three big skills paid ~63,262 tokens pre (HP 24,848 + EX 13,414 + SDD 25,000); post it pays ~16,779 (10,489 + 2,997 + 3,293). **Cut: 73%.** Adding the two INDEXes that load during reference lookup: pre ~80,915, post ~20,008 (**cut: 75%**). writing-plans unchanged by design (healthy source shape).

## 3. RED evidence (checks bound before work started)

gate-0T-red.txt, against the pre-refactor corpus: verify_sizes.py 12 failures; verify_index.py 67 failures; verify_canon.py 1 failure (canon missing); verify_styles.py 14 failures (199 em-dashes in HP alone). Same scripts now: **all four EXIT 0** (gate-final-green.txt, re-archived after the final pointer edits).

## 4. Archive/eviction audit (leaves 02/03 spec-conflict resolution)

- Method: full-corpus walk of the pre-refactor snapshot; every file located in live tree, references/archive/, or scripts/ (batch_leaf_generator.py moved to HP scripts/).
- Result: **zero data loss.** EX archived 116 files (MANIFEST.md present, C4 header added by orchestrator); HP archived 76 files (MANIFEST.md written by orchestrator during wave-2 review - the subagent had omitted it).
- Both leaves hit the same genuine spec conflict: C5-format one-line INDEX entries for every reference file cannot fit the 8,000/4,000 budgets. Resolution per canon C1-WritePath: evict superseded/repo-specific/diary files to archive/ with manifests; live INDEXes fully cover the surviving 92 (EX) and 63 (HP) files. Nothing deleted; archives are INDEX-discoverable (both INDEXes mention archive/).
- SDD needed no eviction: 27/27 reference files INDEX-listed, zero over 200 chars.

## 5. Routing spot-check (15 lines, 5 per INDEX, seed 20261026)

15/15 PASS - every sampled INDEX line names a file that exists and opens with `When to use:` / `Lesson:` headers.

## 6. Functional spot-check (the skill_view 100K cap)

Pre-refactor, hierarchical-planning SKILL.md persisted to a 106K spill file instead of loading (observed directly this session). Post: HP 41,956 chars, EX 11,986 - both load inline with margin. All four SKILL.md files link the canon (grep-verified).

## 7. Per-leaf savings (the compounding multiplier)

Leaf template: 7,439 -> 4,984 chars (-2,455 chars = ~614 tokens per leaf instance). Assumptions: 10-leaf tree, 2 dispatch rounds per leaf (1 re-dispatch), 1 review pass re-reading the leaf: 10 x 3 = 30 loads = **~18,400 tokens saved per tree** before counting the orchestrator's own reads. Task-table format additionally removes the per-task 4-step prose boilerplate (est. 300-600 tokens per leaf per the template redesign, not included above).

## 8. Pitfall-41 verification

Claim from leaf 03 confirmed against the snapshot: the pre-refactor HP Common Pitfalls section contained numbers 1-40 and 42 - **41 was absent in the source** (renumbering gap in the original). The registry preserves source numbering; no content was dropped.

## 9. Structural changes shipped

1. Canon file (4,317 chars, 8 frozen C1-* sections) - single source of the shared model; all 4 skills link it instead of restating.
2. Write-path policy (C1-WritePath) in the canon + skill-maintenance.md operational loop + one-line pointers in all 4 SKILL.md Maintenance sections - the mechanism that prevents re-accretion.
3. Pitfall registries: EX 29 entries, HP 41, SDD 28 - all <=500 chars, all DETAIL targets verified on disk.
4. Templates: task-table format, Verified Anchors section, Completion Report Format (bounded output), Frozen-Documents rule, contracts-by-reference. Compliance scanner unchanged and passing (fixture re-run: ALL TREES COMPLIANT).
5. related_skills trimmed on all 4 skills; writing-plans em-dash-free.

## 10. Gate evidence index

/tmp/skill-refactor-backup-20261026/: gate-0T-red.txt (RED), gate-1.txt, gate-2-review.txt, gate-3.txt, gate-4.txt, gate-5.txt, gate-final-green.txt (GREEN, post-pointer), baseline-bytes.txt, pre-refactor/ (full snapshot), post-05-pre/ (template snapshot).

## 11. Follow-up: spec dialect + traceability (2026-10-26, user-approved)

- Canon: added `C1-Dialect` (imperative spec-dialect rule for all plan docs) and `C1-Trace` (every user requirement maps to a Req ID in the master's Requirement Traceability table; must integrate into a task/contract/anchor; DEFERRED allowed, silent omission is a defect; paraphrase may not weaken).
- Master template: new `## Requirement Traceability` section (Req | Source verbatim | Plan element | Verified by).
- Leaf template: task table gains a `Given/When/Then` acceptance-criteria column (prevents interpretive re-dispatch loops).
- HP SKILL.md: Step 5 authoring rule added; compensated by compressing the delegate_task shape line (canon C1-Dispatch already carries it). Budget holds: 41,817/42,000.
- Gates after changes: all four EXIT 0 (gate-dialect-trace.txt); scanner fixture ALL TREES COMPLIANT.
- Char deltas: canon 4,317->5,215; leaf-template 4,984->4,993; master-template 6,714->7,238 (cap 8,000).
