<!--
  TEMPLATE: Leaf Implementation Document
  Copy this file for each leaf. Delete comments (<!-- ... ->) before saving.
  Fill in ALL [BRACKETED] sections.
  HARD RULE: Total work must fit one agent in 128K context.
  See SKILL.md "The 128K Rule" for sizing guidance.

  TEST-GATE LEAF VARIANT (00T-/01T- docs, dispatched in Phase 0):
  - Goal = write the branch's unit + e2e tests ONLY. No implementation files.
  - Tasks list one test per coverage-matrix feature row (F1..Fn) with exact
    test names, file paths, and assertions on behavior (not implementation).
  - Expected end state: tests compile/parse and fail RED for
    missing-implementation reasons only.
  - Self-Verification swaps "tests passing" for "tests fail for the right
    reason; every assigned matrix row has a named test".
  - The control agent (orchestrator) validates the returned tests against the
    plan's Test Gate coverage matrix and runs the delta protocol — the test
    implementer never edits the plan.
  See references/tests-first-gate.md in this skill.

  DOCS-ONLY ADAPTATION (e.g. GDD, specs, audit remediation):
  - Replace TDD Step 1 (write failing test) with "Read current content"
  - Replace TDD Step 2 (run test, verify fail) with "Confirm old state"
  - Replace TDD Step 3 (write implementation) with "Write/rewrite content"
  - Replace TDD Step 4 (verify pass) with "Verify cross-references resolve"
  - Add `**Audit references:** [audit finding IDs resolved by this leaf]`
    to the Meta section for traceability.
  - The "tests passing" item in Self-Verification Checklist becomes
    "cross-references resolve" and "no contradictions introduced".
-->

# [FEATURE/MODULE NAME] - Implementation Leaf

> **For the implementing agent:** You are the implementer for this leaf.
> Implement ALL tasks below using TDD. If this branch runs a tests-first
> gate, the failing tests ALREADY EXIST and are committed — your job is to
> make them pass; do NOT delete, skip, weaken, or rewrite any gate test
> (report suspected-wrong gate tests to the orchestrator instead). Do NOT
> commit — the orchestrator handles all git operations after review. Do NOT
> use read_file on existing source files — explore with search_files or
> terminal cat. After writing a file, do NOT read it back to verify — write
> once and stop. After completing, report what you built, what files you
> touched, and any deviations from the spec.

## Meta

- **Parent:** [../orchestrator.md | ../../master.md]
- **Scope:** [One sentence: what this leaf builds]
- **Dependencies:** [none / list leaf docs this depends on and why]
- **Estimated Context:** [XXK] (exploration + generation + iteration + overhead)
- **Concurrency Group:** [A/B/C - matches parent's index]
- **Audit references:** [optional — list the audit finding IDs this leaf resolves, e.g. V1, G3, B5]

## Goal

[1-2 paragraphs: what this leaf delivers. Be specific about the module,
feature, or subsystem slice. An agent reading only this document (plus
parent's interface contracts) should understand exactly what to build.]

## Context

[Brief project context: tech stack, relevant architecture patterns,
where this leaf fits in the larger system. Assume the agent has zero
codebase knowledge. Point to key existing files they should understand.]

Key files to understand before implementing:
- [path/to/existing/module.go] - [why: contains X that this leaf extends]
- [path/to/types.go] - [why: shared types defined here]

## Interface Contracts (From Parent)

<!--
  Copy the relevant contracts from the parent orchestrator.
  The agent must implement to these exact specifications.
  This is what the review agent checks against.
-->

### What This Leaf Exposes

```
[Exact signatures, types, file paths this leaf produces.
Other leaves/branches depend on these. Example:

// File: internal/auth/session.go
package auth

type Session struct {
    ID        string
    UserID    string
    ExpiresAt time.Time
}

func NewSession(userID string, ttl time.Duration) (*Session, error)
func (s *Session) IsValid() bool
func (s *Session) Token() (string, error)  // JWT generation
]
```

### What This Leaf Consumes

```
[Signatures/types from other leaves that this leaf uses. Example:

// From 02-data-model.md
type User struct {
    ID    string
    Email string
}

func GetUserByEmail(email string) (*User, error)  // provided by sibling
]
```

## Tasks

<!--
  Use the same bite-sized TDD format as writing-plans skill.
  Each task: objective, files, failing test, implementation, verify.
  DO NOT include commit steps - only orchestrators commit.
-->

### Task 1: [Descriptive Name]

**Objective:** [One sentence]

**Files:**
- Create: `[exact/path/to/new_file.go]`
- Modify: `[exact/path/to/existing.go:45-67]`
- Test: `[exact/path/to/test_file.go]`

**Step 1: Write failing test**

<!-- If this branch runs a tests-first gate, this step becomes: "Confirm the
     committed gate test [TestName] at [path] fails (RED)." Do not write a
     new test — the gate owns it. New edge-case tests beyond the gate are
     allowed and flow through review like any code. -->

```go
func TestSession_CreatesWithUUID(t *testing.T) {
    s, err := NewSession("user-123", time.Hour)
    require.NoError(t, err)
    assert.NotEmpty(t, s.ID)
    assert.Equal(t, "user-123", s.UserID)
}
```

**Step 2: Run test to verify failure**

Run: `go test ./internal/auth/ -run TestSession_CreatesWithUUID -v`
Expected: FAIL - package auth is empty

**Step 3: Write minimal implementation**

```go
package auth

import (
    "time"
    "github.com/google/uuid"
)

type Session struct {
    ID        string
    UserID    string
    ExpiresAt time.Time
}

func NewSession(userID string, ttl time.Duration) (*Session, error) {
    return &Session{
        ID:        uuid.New().String(),
        UserID:    userID,
        ExpiresAt: time.Now().Add(ttl),
    }, nil
}
```

**Step 4: Run test to verify pass**

Run: `go test ./internal/auth/ -run TestSession_CreatesWithUUID -v`
Expected: PASS

### Task 2: [Descriptive Name]

[Same format...]

### Task N: [Descriptive Name]

[Same format...]

## Self-Verification Checklist

Before reporting completion, verify:

- [ ] All tasks implemented and tests passing
- [ ] Interface contracts (above) satisfied exactly
- [ ] All files at exact specified paths
- [ ] No deviations from spec (or deviations documented below)
- [ ] No scope creep - only what the tasks specify

**DO NOT COMMIT.** The orchestrator handles all git operations after review.

**Deviations from spec:** [none / list any with rationale]

## Review Checklist (For Review Agent)

The review agent will verify against this leaf document:

- [ ] Every Task above is implemented
- [ ] Every test in the task is present and passing
- [ ] Interface contracts match exactly (signatures, types, file paths)
- [ ] Code follows project conventions (naming, error handling, structure)
- [ ] No bugs, no security issues
- [ ] No scope creep beyond specified tasks

Output: APPROVED or list of specific gaps with file + line references.

## Notes

[Anything the implementing or review agent should know:
tricky edge cases, performance considerations, known gotchas.]

**Docs-only adaptation:** For documentation plan trees, replace TDD tasks
with: Read current content → Confirm old state → Write/rewrite text →
Verify cross-references resolve. See the SKILL.md comment block at the
top of this template for a full mapping.
