<!--
  TEMPLATE: Master / Branch Orchestrator Document
  Copy as master.md (root) or orchestrator.md (branch). Delete comment
  blocks before saving. Fill ALL [BRACKETS].

  FROZEN DOCS: child leaf documents freeze at dispatch. Corrections ride
  dispatch context as dated addenda - never edit a dispatched leaf doc.

  DOCS-ONLY ADAPTATION (GDD, specs, audit remediation): replace "run tests"
  with "verify cross-references resolve"; Test Gate section becomes
  "N/A - docs-only tree" + the substitute verification. Never skip a
  required section (compliance scanner greps for them).
-->

# [FEATURE/SUBSYSTEM NAME] - Implementation Orchestrator

> **For the executing agent:** You are the orchestrator for this tree node.
> Your job: (1) dispatch implementation agents, (2) review their work,
> (3) re-dispatch if incomplete, (4) track completion.
> Do NOT implement code yourself. All implementation happens in leaf agents.
> Full operational detail: skill `hierarchical-plan-execution`.

## Meta

- **Role:** [Root / Branch]
- **Parent:** [none (root) | ../../master.md | ../orchestrator.md]
- **Children:** [N leaf/branch documents under this node]
- **Scope:** [One sentence: what this subtree builds]

## Goal

[1-3 paragraphs: what this subtree delivers and why. Root: project-level
outcome. Branch: subsystem-level goal.]

## Architecture

[2-5 sentences: design approach, key patterns, how data/control flows
between subsystems. Children carry their own detail.]

## Interface Contracts

<!-- Each contract: ID + ONE signature block. Owning + consuming leaves.
     Leaves list consumed contract IDs + exact signatures only - never
     restate full definitions in a leaf; the parent holds them once. -->

### C1: [Shared Type / API Name]

```
[type definition or signature in code]
// Owner: [01-name.md]
// Consumers: [02-name.md, 03-name.md]
```

### C2: [Name]
[...]

## Child Document Index

| # | Document | Type | Dependencies | Est. Context | Concurrency |
|---|----------|------|-------------|-------------|-------------|
| 01 | [path/to/01-name.md] | [leaf/branch] | [none / 02, 03] | [XXK] | [A/B/C] |
| 02 | [path/to/02-name.md] | [leaf/branch] | [none] | [XXK] | [A] |
| 03 | [path/to/03-name.md] | [leaf/branch] | [01] | [XXK] | [B] |

Same-letter children have no inter-dependencies and dispatch together
(max 3 per batch).

## Dispatch Protocol

For each concurrency group, in dependency order. Full recipe: skill
`hierarchical-plan-execution`.

### Phase 0: Test Gate (code branches, before ANY implementation dispatch)

Dispatch 00T-/01T- test leaves first: tests only, fail RED for
missing-implementation reasons. Validate in-session (never delegate
review) against the Test Gate matrix; apply the delta protocol; commit
gate tests; set children to TESTS_VALIDATED. Then implementation may
dispatch. See references/tests-first-gate.md.

### Phase 1: Dispatch Concurrency Group [A]

Dispatch same-letter children simultaneously via `delegate_task`: goal =
"Implement all tasks from [leaf]"; context = full leaf text + contracts +
conventions + relevant source INLINED; include the no-commit, no-git-add,
no-read_file, write-once-and-stop rules.

### Phase 2: Review and Commit Each Child

Review in-session (the main model - never a delegated reviewer). Check
leaf spec, contracts, Review Checklist; run tests; gate-test diff must be
empty. Pass: commit + status REVIEWED. Gaps: re-dispatch with findings,
max 3 cycles, then escalate to parent.

### Phase 3: Integration Review

After ALL children REVIEWED: verify contracts between children, run the
full suite, check no import cycles. Gaps: re-dispatch the failing child
with contract fixes (uncommitted). Pass: normalize formatting, run the
line-number corruption check, commit integration changes, set children
COMPLETE, report COMPLETE to parent (if branch).

## Review Checklist

The orchestrator (main model) verifies each child in-session:

- [ ] All tasks from the leaf document are implemented
- [ ] Interface contracts satisfied (signatures, types, paths)
- [ ] All specified files created/modified at exact paths
- [ ] Gate tests pass GREEN; `git diff` shows no gate-test modification
      (any such diff = automatic NEEDS_FIXES)
- [ ] Tests written and passing (TDD followed)
- [ ] Code follows project conventions
- [ ] No scope creep; no obvious bugs or security issues
- [ ] No debug artifacts (print debugging, TODOs, placeholders,
      commented-out code)
- [ ] No line-number corruption (`     N|` prefixes) in source files

Output: APPROVED or a list of specific gaps.

## Coding Conventions

<!-- Passed to every implementation agent in dispatch context. 5-10 bullets. -->

- **Language/Framework:** [e.g. Go 1.22, Python 3.12]
- **Naming:** [exported/unexported rules]
- **Imports:** [grouping, no unused]
- **Error handling:** [wrap pattern, return early]
- **Testing:** [table-driven, framework, file placement]
- **Formatting tool:** [gofmt / prettier / ruff - run before reporting]

## Requirement Traceability

| Req | Source (user words, verbatim when possible) | Plan element (leaf/task/contract) | Verified by |
|-----|---------------------------------------------|-----------------------------------|-------------|
| R1 | [user requirement] | [02-data-model.md T1 / Contract 1] | [test name / verify command] |
| R2 | [...] | [...] | [...] |

Rule (canon C1-Trace): every user requirement maps to a plan element that integrates it. DEFERRED rows name where the work goes. Silent omission is a defect.

## Completion Tracking Table

<!-- Single source of truth for subtree status; parent reads this. -->

| Child | Status | Iterations | Review Notes |
|-------|--------|------------|-------------|
| [00T-unit-tests] | PENDING | 0 | |
| [01-name] | PENDING | 0 | |
| [02-name] | PENDING | 0 | |

Status values: PENDING | TESTS_IN_PROGRESS | TESTS_VALIDATED | IN_PROGRESS |
IMPLEMENTED | REVIEWED | COMPLETE | BLOCKED

Gate rule: implementation children stay PENDING until the branch's
test-gate leaves reach TESTS_VALIDATED.

## Integration Test Plan

[Commands + expected output proving children work together. Include
cross-boundary tests that exercise contracts.]

## Test Gate

<!-- Mandatory for code branches. Docs-only/ops trees: "N/A - <tree type>"
     + substitute verification. Matrix validates before implementation
     dispatches; delta protocol on mismatch: update the LESSER artifact. -->

Test leaves: [00T-unit-tests.md, 00T-e2e-tests.md] - dispatched in
Phase 0, validated by the control agent (orchestrator, in-session).

| # | Feature (from plan) | Source (leaf/spec section) | Unit tests | E2E tests | Status |
|---|---------------------|----------------------------|-----------|-----------|--------|
| F1 | [feature] | [01-name.md Task 1] | [test names] | [names / n/a + reason] | PENDING |

Statuses: PENDING | DELTA (mismatch, resolution in progress) | VALIDATED

Delta log: [date, feature ID, direction, one-line reason]

## Frozen Documents

Leaf documents freeze at dispatch. Corrections ride dispatch context as
dated addenda (dated, appended to the dispatch brief). Never edit a
dispatched leaf document mid-execution.

## Notes

[Additional context: known constraints, risky integration areas.]
