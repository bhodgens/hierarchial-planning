<!--
  TEMPLATE: Master / Branch Orchestrator Document
  Copy this file as master.md (root) or orchestrator.md (branch).
  Delete comments (<!-- ... ->) before saving the final document.
  Fill in ALL [BRACKETED] sections.

  DOCS-ONLY ADAPTATION (e.g. GDD, specs, audit remediation):
  - Replace "run tests" with "verify cross-references resolve"
  - Replace "run formatter" with "verify status markers consistent"
  - Line-number corruption check must include --include='*.md'
  - Do NOT skip the Dispatch Protocol / Review Checklist / Integration Test Plan
    sections on any orchestrator, even for docs-only trees — see Pitfall 20.
-->

# [FEATURE/SUBSYSTEM NAME] - Implementation Orchestrator

> **For the executing agent:** You are the orchestrator for this tree node.
> Your job: (1) dispatch implementation agents, (2) review their work,
> (3) re-dispatch if incomplete, (4) track completion.
> Do NOT implement code yourself. All implementation happens in leaf agents.

## Meta

- **Role:** [Root / Branch]
- **Parent:** [none (root) | ../../master.md | ../orchestrator.md]
- **Children:** [N leaf/branch documents under this node]
- **Scope:** [One sentence: what this subtree builds]

## Goal

[1-3 paragraphs: what this subtree delivers and why. For root: project-level
goal and user-visible outcome. For branch: subsystem-level goal.]

## Architecture

[2-5 sentences: design approach, key patterns, technology choices.
Brief — children have their own detailed sections. Focus on what ties
the subsystems together and how data/control flows between them.]

## Interface Contracts

<!--
  This is the integration surface. Be precise: actual type definitions,
  function signatures, file path conventions, API shapes.
  Ambiguity here = integration failure later.
  For each contract: name, definition, owning leaf, consuming leaf(s).
-->

### Contract 1: [Shared Type / API Name]

```
[Actual type definition, interface spec, or API shape in code.
Example for a Go struct:

type Session struct {
    ID        string    `json:"id"`
    UserID    string    `json:"user_id"`
    ExpiresAt time.Time `json:"expires_at"`
}

// Owner: 02-session-store.md
// Consumers: 01-jwt-token.md, 03-api/01-rest-handlers.md
]
```

### Contract 2: [Name]
[...]

## Child Document Index

<!--
  List every child. For each: path, type (leaf/branch), dependencies,
  estimated context budget, concurrency group.
-->

| # | Document | Type | Dependencies | Est. Context | Concurrency |
|---|----------|------|-------------|-------------|-------------|
| 01 | [path/to/01-name.md] | [leaf/branch] | [none / 02, 03] | [XXK] | [A/B/C] |
| 02 | [path/to/02-name.md] | [leaf/branch] | [none] | [XXK] | [A] |
| 03 | [path/to/03-name.md] | [leaf/branch] | [01] | [XXK] | [B] |

**Concurrency groups:** Documents in the same letter group have no
inter-dependencies and can be dispatched simultaneously (max 3 per batch).

## Dispatch Protocol

For each concurrency group, in dependency order:

### Phase 0: Test Gate (MANDATORY for code branches — before ANY implementation dispatch)

Dispatch the branch's test-gate leaves (`00T-`/`01T-` docs) FIRST, as subagents:

1. **Dispatch test leaves** via `delegate_task` (batch to the concurrency cap):
   - Goal: "Write ALL unit + e2e tests from [00T-name.md] — tests only, no implementation"
   - Context: Full test-leaf text + interface contracts INLINED + coding conventions
   - Include: "Write tests ONLY. Do NOT write or modify implementation files.
     Tests must fail RED for missing-implementation reasons — run them once to
     confirm. Do NOT commit. Do NOT run git add."

2. **Control-agent validation (IN-SESSION, main model — never delegated):**
   - Run the returned tests; confirm they compile/parse and fail for the RIGHT reason
   - Map every test to a Test Gate coverage-matrix row; update the matrix
   - Apply the DELTA PROTOCOL on any plan-vs-test mismatch: update the LESSER
     artifact to reflect the GREATER (missing tests → re-dispatch with specific
     rows; sound-but-unspecified test behavior → amend the plan; test
     contradicting the design spec → delete with written rationale)
   - Loop until every matrix row is VALIDATED

3. **Gate commit and unlock:**
   - Orchestrator commits validated test files:
     `git add <test paths> && git commit -m "test(scope): gate tests for [branch] (F1-Fn)"`
   - Update tracking table: branch children gate -> TESTS_VALIDATED
   - ONLY NOW may implementation leaves in this branch dispatch

Full recipe: skill `hierarchical-planning` → `references/tests-first-gate.md`.

### Phase 1: Dispatch Concurrency Group [A]

<!-- Implementation leaves dispatch here. Every dispatch context adds:
     "Gate tests already exist at [paths] and are committed. Make them pass.
     Do NOT delete, skip, weaken, or rewrite any gate test. If a gate test
     appears wrong, STOP and report — the orchestrator runs the delta protocol." -->

Dispatch these children simultaneously (they have no inter-dependencies):

1. **Read** [01-name.md] and dispatch via `delegate_task`:
   - Goal: "Implement all tasks from [01-name.md]"
   - Context: Full leaf document text + interface contracts from this orchestrator
     + coding conventions block + relevant existing source code INLINED
   - Include: "Do NOT commit. Do NOT run git add. Write code, run tests, report results only."
   - Include: "Do NOT use read_file on existing source files — explore with search_files
     or terminal cat instead. If you read a file, never feed its output into write_file."
   - Agent follows TDD per the leaf's instructions

2. **Read** [02-name.md] and dispatch via `delegate_task`:
   - Goal: "Implement all tasks from [02-name.md]"
   - Context: Full leaf document text + interface contracts + coding conventions
     + relevant existing source code INLINED
   - Include: "Do NOT commit. Do NOT run git add."
   - Include: "Do NOT use read_file on existing source files — explore with search_files
     or terminal cat instead. If you read a file, never feed its output into write_file."
   - Include: "After writing a file, do NOT read it back to verify. Write once and stop."

3. **Read** [03-name.md] and dispatch via `delegate_task`:
   - Goal: "Implement all tasks from [03-name.md]"
   - Context: Full leaf document text + interface contracts + coding conventions
     + relevant existing source code INLINED
   - Include: "Do NOT commit. Do NOT run git add."
   - Include: "Do NOT use read_file on existing source files — explore with search_files
     or terminal cat instead. If you read a file, never feed its output into write_file."
   - Include: "After writing a file, do NOT read it back to verify. Write once and stop."

### Phase 2: Review and Commit Each Child

After each implementation agent returns, the orchestrator reviews in-session
(the main model reviews directly, NOT a delegated subagent — delegate_task
children inherit delegation.model, so a delegated reviewer would use the
same subagent model that wrote the code):

1. **Orchestrator reviews in-session:**
   - Read the changed files (from the implementer's file list)
   - Check against leaf spec + interface contracts + Review Checklist below
   - Run tests and build verification

2. **If review finds gaps:**
   - Re-dispatch implementation agent with specific feedback
   - Context: original leaf + review findings + "fix these gaps"
   - Re-review after return
   - Max 3 re-dispatch cycles; if still failing, escalate to parent

3. **If review passes:**
   - **Commit the leaf's files:** `git add <exact paths> && git commit -m "feat(scope): implement [leaf name]"`
   - Update tracking table: status -> REVIEWED
   - Proceed to next child

### Phase 3: Integration Review

After ALL children reach REVIEWED:

1. **Orchestrator runs integration review in-session:**
   - Verify interface contracts between children
   - Run full test suite (not just individual leaf tests)
   - Check: contracts satisfied, no import cycles, cross-child tests pass

2. **If integration gaps found:**
   - Identify which child(ren) failed the contract
   - Re-dispatch those children with contract-fix instructions (do NOT commit)
   - Orchestrator re-reviews -> commits the fix -> re-runs integration checks

3. **If integration passes:**
   - **Normalize formatting:** run `[gofmt / prettier / ruff]` across all changed files
   - **Verify no line-number corruption:** `grep -rcE '^\s+[0-9]+\|' --include='*.go' --include='*.py' --include='*.ts' .` returns zero
   - **Commit integration changes** (if any): `git add . && git commit -m "feat(scope): integrate [branch name]"`
   - Update tracking table: all children -> COMPLETE
   - Report COMPLETE to parent (if branch)

## Review Checklist

The orchestrator (main model) verifies each child in-session:

- [ ] All tasks from the leaf document are implemented
- [ ] Interface contracts from this orchestrator are satisfied
- [ ] All specified files created/modified at exact paths
- [ ] The branch's committed gate tests pass GREEN; `git diff` shows the implementer did NOT modify, weaken, skip, or delete any gate test file (any such diff = automatic NEEDS_FIXES)
- [ ] Tests written and passing (TDD followed)
- [ ] Code follows project conventions (see Coding Conventions below)
- [ ] No scope creep (nothing beyond spec)
- [ ] No obvious bugs or security issues
- [ ] No debug artifacts: no print/stdout debugging, no TODOs, no placeholder values, no commented-out code
- [ ] No line-number corruption: no `     N|` prefixes baked into source files

Output: APPROVED or list of specific gaps.

## Coding Conventions

<!--
  Fill in project-specific style rules. These are passed to every
  implementation agent in dispatch context to ensure consistency
  across independent leaves. Keep brief — 5-10 bullet points max.
-->

- **Language/Framework:** [e.g., Go 1.22, Python 3.12, TypeScript 5.4]
- **Naming:** [e.g., exported = PascalCase, unexported = camelCase]
- **Imports:** [e.g., grouped stdlib/third-party/local, no unused]
- **Error handling:** [e.g., wrap with %w, return early, no panic in libs]
- **Testing:** [e.g., table-driven, testify require/assert, _test.go alongside]
- **Formatting tool:** [e.g., gofmt, prettier, ruff — run before reporting completion]
- **File headers:** [e.g., no boilerplate headers, or include copyright notice]

## Completion Tracking Table

<!--
  The source of truth for this subtree's status.
  Update after every child status transition.
  The PARENT reads this to determine completeness.
-->

| Child | Status | Iterations | Review Notes |
|-------|--------|------------|-------------|
| [00T-unit-tests] | PENDING | 0 | |
| [00T-e2e-tests] | PENDING | 0 | |
| [01-name] | PENDING | 0 | |
| [02-name] | PENDING | 0 | |
| [03-name] | PENDING | 0 | |

Status values: PENDING | TESTS_IN_PROGRESS | TESTS_VALIDATED | IN_PROGRESS | IMPLEMENTED | REVIEWED | COMPLETE | BLOCKED

Gate rule: implementation children stay PENDING until the branch's test-gate leaves reach TESTS_VALIDATED (see Dispatch Protocol Phase 0 and ## Test Gate).

## Integration Test Plan

[How to verify the children work together. Specific commands and expected
output. Include cross-boundary tests that exercise contracts.]

## Test Gate

<!--
  Tests-first gate (mandatory for code branches; docs-only/ops trees write
  "N/A — <tree type>" here and name the substitute verification).
  The coverage matrix is the control agent's validation artifact: one row
  per feature the branch delivers, derived from the leaf task specs and
  interface contracts. NO implementation leaf dispatches until every row
  is VALIDATED. Delta protocol: on plan-vs-test mismatch, update the
  LESSER artifact to reflect the GREATER. Full recipe: skill
  hierarchical-planning → references/tests-first-gate.md.
-->

Test leaves: [00T-unit-tests.md, 00T-e2e-tests.md] — dispatched in Phase 0, validated by the control agent (orchestrator, in-session).

| # | Feature (from plan) | Source (leaf/spec §) | Unit tests | E2E tests | Status |
|---|---------------------|----------------------|-----------|-----------|--------|
| F1 | [feature] | [01-name.md Task 1] | [test names] | [test names / n/a + reason] | PENDING |

Statuses: PENDING | DELTA (mismatch, resolution in progress) | VALIDATED

Delta log: [date, feature ID, direction (tests-updated / plan-updated / test-deleted), one-line reason]

## Structural Completeness Check (Before Dispatch)

After writing every document in this tree (this orchestrator + all its siblings +
master.md if this is a branch), run a structural scan to confirm no required
sections are missing. Required for every orchestrator:

- `## Dispatch Protocol` — dispatch instructions for the executing agent
- `## Interface Contracts` — contracts between children
- `## Review Checklist` — verification criteria for the main model
- `## Coding Conventions` — style rules for consistent output across leaves
- `## Completion Tracking Table` — status tracking
- `## Integration Test Plan` — how to verify children work together
- `## Test Gate` — coverage matrix for the tests-first gate (code trees);
  docs-only/ops trees mark it `N/A — <tree type>` with the substitute
  verification named

If any section is missing, fill it in before dispatching any review or
implementation agents. See SKILL.md Pitfall 20 for rationale.

## Notes

[Any additional context for the executing agent: project conventions,
known constraints, risky areas to watch during integration.]
