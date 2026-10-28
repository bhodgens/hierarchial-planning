# 06 - Final Audit + Before/After Report + Maintenance Adoption - Implementation Leaf

## Meta

- **Parent:** master.md
- **Scope:** Full gate run, before/after byte report, routing spot-checks, and a maintenance doc that makes the reduction permanent. No further edits to skill content except fixes this audit proves necessary.
- **Dependencies:** 00T-05 all REVIEWED
- **Estimated Context:** ~40K
- **Concurrency Group:** 4

## Goal

Prove the refactor with the RED-then-GREEN gates, quantify the savings, verify routing integrity, and leave behind the maintenance loop that prevents re-accretion.

## Context

Everything needed is on disk: gates in the plan dir scripts/, baseline manifest at /tmp/skill-refactor-backup-20261026/baseline-bytes.txt, per-wave gate outputs gate-0T-red.txt through gate-5.txt, pre-refactor file snapshots in the same backup dir.

## Interface Contracts (From Parent)

Report lands at /Users/caimlas/plans/20261026-skill-token-refactor/REPORT.md. Maintenance doc lands at ~/.hermes/skills/software-development/hierarchical-planning/references/skill-maintenance.md and is linked from each SKILL.md's Maintenance section (one line each - four one-line edits).

## Tasks

### Task 1: Full gate run (GREEN proof)

Run all four scripts against the real root. Expected: all exit 0. Archive combined output to /tmp/skill-refactor-backup-20261026/gate-final-green.txt. Any failure: record it, dispatch a fix to the owning leaf's scope, re-run. Do not waive failures.

### Task 2: Before/after report

**Objective:** REPORT.md with:
1. Table: file | before chars | after chars | before ~tokens | after ~tokens | delta % - for all 8 budgeted files.
2. Corpus totals before/after (SKILL.md layer + INDEX layer separately).
3. Token-load estimate: a session that triggers HP + EX pays ~38K tokens pre-refactor vs ~12-14K post (compute exact from the table).
4. RED evidence: paste the gate-0T-red.txt summary lines proving the checks bound before the work.
5. Routing spot-check: 5 random INDEX lines from each rewritten INDEX - confirm target exists + C4 header present; record pass/fail per line.
6. Functional spot-check: `skill_view(name='hierarchical-plan-execution')` now returns full content inline (pre-refactor it persisted 106K chars to a spill file); record the result.
7. Canon link check: grep all four SKILL.md files for plan-tree-canon.md; confirm the link resolves.
8. Per-leaf savings estimate: old vs new leaf-template char count and the multiplier math (leaves x dispatches x reviews).

### Task 3: Maintenance doc

**Objective:** ~/.hermes/skills/software-development/hierarchical-planning/references/skill-maintenance.md (C4 header) with the operational loop:
1. Appends: INDEX one-liner + ref file only. Never SKILL.md.
2. Quarterly consolidation: merge incident refs into invariants; registry lines stay <=500 chars.
3. Eviction: 2 quarters unfired -> move to references/archive/ (INDEX line removed).
4. Budget check: run the four gate scripts as the skill's regression suite; a SKILL.md over budget is a refactor trigger, not a cap to bump.
5. The 100K skill_view cap as the hard failure signal (observed 2026-10-26 on HP).

Then add one line to each of the four SKILL.md Maintenance sections pointing at it.

### Task 4: Tracking table closeout

Master.md Completion Tracking Table: all leaves COMPLETE with timestamps and completeness %. No actionable item left in any "remains" list.

## Self-Verification Checklist

- [ ] All gates GREEN (archived output)
- [ ] REPORT.md complete with all 8 required elements
- [ ] skill-maintenance.md exists with C4 header and is linked from 4 SKILL.md files
- [ ] Tracking table fully closed
- [ ] No unexplained byte delta in files outside leaf scope (diff backup vs current tree; every delta maps to a leaf)

## Review Checklist (For Review Agent)

- [ ] Re-run 2 gate scripts independently - same GREEN result
- [ ] Pick 3 INDEX lines not used in Task 2's spot-check and verify them
- [ ] The maintenance loop, if followed, would have prevented the original accretion (reason through one counterfactual in the report)

**DO NOT COMMIT.** Orchestrator archives the final state to /tmp/skill-refactor-backup-20261026/final/.

## Notes

This leaf's report is the deliverable the user reads. Numbers over adjectives.
