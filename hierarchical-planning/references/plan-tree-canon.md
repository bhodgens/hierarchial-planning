# Plan-Tree Canon - Shared Model for the hierarchical-planning Skill Family

When to use: read once before working with any plan tree (authoring, executing, or dispatching). Every skill in the family links here instead of restating this model.
Lesson: one canon, eight frozen sections; skills link, never restate.

This file is the single source of truth for the shared model used by hierarchical-planning, hierarchical-plan-execution, subagent-driven-development, and writing-plans. Skills reference sections as `plan-tree-canon.md C1-<name>`. Rules here are invariants; worked examples live in each skill's references.

## C1-Nodes

- `master.md` - root orchestrator. Holds project goal, architecture overview, all top-level interface contracts, child index, completion tracking, integration review plan.
- `orchestrator.md` - branch node, identical structure scoped to one subsystem. Dispatches, reviews, and tracks its own children.
- Leaf (`NN-name.md`) - terminal implementation document. One agent's worth of work. Complete tasks, interface contracts, self-verification checklist, review checklist. Leaves never contain children.

## C1-Status

| Status | Meaning |
|---|---|
| PENDING | Not started |
| TESTS_IN_PROGRESS | Test-gate leaves dispatched, awaiting validation |
| TESTS_VALIDATED | Gate tests validated by control agent and committed; implementation may dispatch |
| IN_PROGRESS | Implementation agent dispatched, awaiting return |
| IMPLEMENTED | Implementation returned, awaiting review |
| REVIEWED | Review passed, no gaps found |
| COMPLETE | Verified, integrated, committed |
| BLOCKED | Cannot proceed (dependency missing, conflict) |

## C1-Commit

Only orchestrators commit. Implementation agents never run `git commit` or `git add` - they write code, run tests, report results. Every dispatch context states: "Do NOT commit." The orchestrator stages the leaf's specific files and commits only after review passes.

## C1-Dispatch

`delegate_task` batch shape: `tasks: [{goal: <one-line imperative>, context: <full brief>}]`. Every `tasks[]` item carries its own `goal`. Single-task mode requires a top-level `goal`. On any dispatch schema error, diagnose the shape before retrying - never blind-resend.

## C1-Review

Review in-session by the main model, never delegated. Delegated reviewers inherit `delegation.model` - the same subagent model that wrote the code would grade it. Loop: review - re-dispatch with specific feedback - re-review, max 3 iterations. The orchestrator determines completion; implementers never self-assess.

## C1-Sizing

No leaf describes more work than one agent fits in 128K context (exploration + generation + iteration + ~15K overhead; target <=110K). Wall-clock matters too: a subagent cannot finish what exceeds ~25 minutes (configurable via `delegation.child_timeout_seconds`). Split at architectural seams - modules, contracts, layers - never mid-class. Merge any leaf estimated under 30K with a sibling.

## C1-State

The orchestrator's completion tracking table is the single source of truth for subtree status. Update after every child transition. Volatile state (status columns, timestamps, reconciliation notes) stays out of protocol text; a tree running long gets a separate `STATE.md` so protocol files stay byte-stable (cache-friendly, diff-friendly).

## C1-WritePath

Skill-library write policy (applies to every skill in this family):

1. SKILL.md files are curated protocol. Never append dated session entries, campaign narratives, or worked examples to them.
2. New lesson = one line appended to the skill's `references/INDEX.md` (`- <file> - <trigger> - <one-line lesson>`, <=200 chars) plus the full lesson in a reference file opening with `# title` / `When to use:` / `Lesson:` lines.
3. Consolidation pass each quarter: merge related incident files into terse invariants; registry entries stay <=500 chars; INDEX lines stay one line.
4. Eviction: a reference not fired or cited for 2 quarters moves to `references/archive/` and loses its INDEX line.
5. Repo-specific lessons live in that repo's skill or docs; global skills hold invariants only.
6. Budgets are regression gates (verified by the plan-tree scripts under `plans/20261026-skill-token-refactor/scripts/`). A SKILL.md over budget is a refactor trigger, not a cap to raise.

## C1-Dialect

Plan documents are written in spec dialect: imperative, terse, present tense. One sentence = one rule, one claim, or one command. No rationale narration, no hedging, no persuasion, no analogy, no second person. Rationale is a one-line `WHY:` note or lives in a reference file. Goal and Context sections are bullets, not paragraphs. Hyphens, never em-dashes.

## C1-Trace

Every user-stated requirement enters the plan as a Req ID in the master's Requirement Traceability table: `| Req | Source (user words, verbatim when possible) | Plan element (leaf/task/contract) | Verified by |`. - The plan element must integrate the requirement: a task, contract, or verified anchor - never a Notes mention.
- Out of scope: mark DEFERRED with a pointer to where the work goes. Silent omission is a defect.
- Paraphrase may not weaken a requirement; numbers, names, constraints stay verbatim.
