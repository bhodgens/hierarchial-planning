# 05 - Template Redesign + Cross-Skill Wiring - Implementation Leaf

## Meta

- **Parent:** master.md
- **Scope:** leaf-template.md 7,459 -> <=5,000 chars; master-template.md 13,551 -> <=8,000 chars; task-table format; related_skills trims; writing-plans canon link + related_skills trim.
- **Dependencies:** 02, 03 REVIEWED (template heading strings must match the landed SKILL.md text; the compliance scanner requirements stay authoritative)
- **Estimated Context:** ~50K
- **Concurrency Group:** 3

## Goal

Make every future plan tree cheaper: task tables instead of repeated per-task TDD prose, contracts by reference, verified-anchor and bounded-report sections. This is the per-leaf token multiplier - savings here apply to every leaf of every future tree, per dispatch and per review.

## Context

Verified anchors:
- Templates: ~/.hermes/skills/software-development/hierarchical-planning/templates/{leaf-template.md, master-template.md}
- The compliance scanner (scripts/check_template_compliance.py in the HP skill) checks for exact literal headings. Read it FIRST and keep every heading it greps for byte-identical. Required orchestrator headings (per current source): `## Dispatch Protocol`, `## Interface Contracts`, `## Child Index`, `## Review Checklist`, `## Coding Conventions`, `## Completion Tracking Table`, `## Integration Test Plan`; leaves need "Do NOT commit" and (strict mode) a Self-Verification checklist. The scanner is the gate - if a redesign breaks it, the redesign is wrong, not the scanner.
- Leaf template's "For the implementing agent" blockquote (no-commit, no read_file, write-once rules) is load-bearing protocol - preserve its rules verbatim even if reflowed.

## Interface Contracts (From Parent)

C1 canon (templates reference C1-Status/C1-Commit), C6 (frozen leaf docs during execution - the new template must state this rule in its header comments), C3/C5 formats where templates show registry/INDEX examples.

## Tasks

### Task 1: Redesign leaf-template.md

**Objective:** <=5,000 chars. Changes:
1. Tasks section becomes a table: `Task ID | Objective | Files | Verify command | RED reason | PASS state` - one row per task, keeping ONE worked 4-step TDD example after the table as the canonical expansion.
2. New `## Verified Anchors` section: exact paths, symbol names, line ranges, each grep-confirmed during authoring (a checklist item in the template's author comment).
3. `## Interface Contracts` keeps exposed/consumed subsections but consumed side lists contract IDs + exact signatures only (contracts-by-reference; full definitions live in the parent orchestrator once).
4. New `## Completion Report Format` section: files touched, verify command + last 20 lines of output, deviations. Bounded output per contract with the plan's bounded-report goal.
5. Header comment adds: "This leaf is FROZEN at dispatch. Corrections ride dispatch context as dated addenda. Never edit mid-execution."
6. Keep: Meta block, Self-Verification Checklist, Review Checklist, "DO NOT COMMIT" line, docs-only adaptation mapping, test-gate variant note (may compress to a pointer at references/tests-first-gate.md).

### Task 2: Redesign master-template.md

**Objective:** <=8,000 chars. Changes:
1. Dispatch Protocol phases stay (Phase 0 test gate, Phase 1 dispatch, Phase 2 review+commit, Phase 3 integration) but inline instructions shrink to <=2 lines each + pointer to the execution skill.
2. Interface Contracts: each contract gets an ID and one signature block; add the rule "leaves list consumed contract IDs + signatures only - never restate full definitions".
3. Completion Tracking Table keeps exact heading (scanner).
4. Add `## Frozen Documents` note: leaf docs freeze at dispatch; addenda via dispatch context.
5. Remove the long inline examples duplicated from SKILL.md; keep skeleton + one-liner guidance per section.

### Task 3: Wire writing-plans + frontmatter trims

**Objective:**
1. writing-plans/SKILL.md: add the canon pointer line after `## Overview` (01 did this - verify it landed; if not, add it); trim related_skills to [subagent-driven-development, hierarchical-planning].
2. HP SKILL.md frontmatter: trim related_skills to [writing-plans, hierarchical-plan-execution, subagent-driven-development] (drop kanban-orchestrator, parallel-report-generation, design-plan-consistency from frontmatter; they remain reachable via the Integration table).
3. Verify the Integration with Existing Skills tables in HP and EX still point at real skills.

### Task 4: Update the compliance scanner if needed

**Objective:** Run `python3 <HP>/scripts/check_template_compliance.py` against the two redesigned templates placed in a fixture tree under /tmp. If the scanner's literal checks fail against a compliant new template, patch the scanner minimally (it is versioned with the skill) and record the diff. Do not weaken checks - only adjust literal strings if section content moved.

**Files:** possibly modify ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py

### Task 5: Gates

verify_sizes.py (template budgets), verify_styles.py. Plus the Task 4 scanner fixture run. Archive to /tmp/skill-refactor-backup-20261026/gate-5.txt.

## Self-Verification Checklist

- [ ] leaf-template <=5,000 chars; master-template <=8,000 chars
- [ ] Scanner passes against fixture trees built from BOTH new templates (output archived)
- [ ] All scanner-required headings byte-identical
- [ ] Task-table + one worked example present; verified-anchor + completion-report sections present
- [ ] Frozen-docs rule stated in both templates
- [ ] related_skills trims applied to HP, SDD (04 did), writing-plans
- [ ] No em-dashes

## Review Checklist (For Review Agent)

- [ ] A leaf authored from the new template contains everything an implementing agent needs (no lost protocol: no-commit, write-once, no read_file rules all present)
- [ ] The worked example in the template is sufficient to expand any table row unambiguously
- [ ] Scanner diff (if any) is minimal and check-preserving

**DO NOT COMMIT.** Orchestrator archives after review.

## Notes

This leaf carries the compounding payoff: a 40% smaller leaf template multiplies across every dispatch, re-dispatch, and review of every future tree.
