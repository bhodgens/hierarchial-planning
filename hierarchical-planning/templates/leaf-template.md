<!--
  TEMPLATE: Leaf Implementation Document
  Copy per leaf. Delete comments before saving. Fill ALL [BRACKETS].
  HARD RULE: total work fits one agent in 128K context (SKILL.md 128K Rule).

  FROZEN DOC: This leaf is FROZEN at dispatch. Corrections ride dispatch
  context as dated addenda. Never edit the leaf document mid-execution.

  TEST-GATE VARIANT (00T-/01T- leaves): see references/tests-first-gate.md.
  Tests only; fail RED for missing-implementation reasons; the orchestrator
  validates returned tests against the Test Gate matrix (delta protocol).

  DOCS-ONLY ADAPTATION: step 1 -> read current content; 2 -> confirm old
  state; 3 -> write content; 4 -> verify cross-refs resolve. Self-check
  swaps "tests passing" for "cross-refs resolve". Audit refs in Meta.
  AUTHOR CHECKLIST: Verified Anchors grep-confirmed at authoring time.
  -->

# [FEATURE/MODULE NAME] - Implementation Leaf

> **For the implementing agent:** You are the implementer for this leaf.
> Implement ALL tasks below using TDD. If this branch runs a tests-first
> gate, the failing tests ALREADY EXIST and are committed - your job is to
> make them pass; do NOT delete, skip, weaken, or rewrite any gate test
> (report suspected-wrong gate tests to the orchestrator instead). Do NOT
> commit - the orchestrator handles all git operations after review. Do NOT
> use read_file on existing source files - explore with search_files or
> terminal cat. After writing a file, do NOT read it back - write once and
> stop. Report what you built, files touched, and any deviations.

## Meta

- **Parent:** [../orchestrator.md | ../../master.md]
- **Scope:** [One sentence: what this leaf builds]
- **Dependencies:** [none / leaf docs]
- **Estimated Context:** [XXK]
- **Concurrency Group:** [A/B/C]
- **Audit references:** [optional: finding IDs]

## Goal

[1-2 paragraphs: what this leaf delivers; readable with only the parent's
contracts.]

## Context

[Tech stack, patterns, where this leaf fits. Assume zero codebase knowledge.]
- [path/to/file] - [why it matters]

## Verified Anchors

<!-- Exact, grep-confirmed at authoring time. No approximate pointers. -->

- [exact/path/file.go:45-67] - [symbol name] - [what the implementer needs]

## Interface Contracts (From Parent)

### What This Leaf Exposes

```
[Exact signatures, types, paths this leaf produces:]
func NewSession(userID string, ttl time.Duration) (*Session, error)
```

### What This Leaf Consumes

<!-- Contract IDs + exact signatures ONLY. Full definitions live once in
     the parent orchestrator - never restate them. -->

- [C2 Session] - `NewSession(userID string, ttl time.Duration) (*Session, error)` - [owning leaf]

## Tasks

<!-- One row per task. Expand each row with the worked example below. -->

| Task ID | Objective | Files | Verify command | RED reason | PASS state | Given/When/Then |
|---------|-----------|-------|----------------|------------|------------|
| T1 | [one sentence] | Create: [path]; Modify: [path:lines]; Test: [path] | `[exact command]` | [expected failure] | [expected pass] | Given [precondition]; When [action]; Then [observable result] |
| T2 | [...] | [...] | [...] | [...] | [...] | Given [...] |


Given/When/Then: acceptance criteria in spec form - precondition, action, observable result. Ambiguity here is the top cause of re-dispatch loops.

**Worked example (canonical row expansion):**

T1: Create User model. Create `src/models/user.py`; Test `tests/models/test_user.py`.
1. Write failing test:

```python
def test_user_has_email():
    assert User(email="a@b.c").email == "a@b.c"
```

2. Verify failure: `pytest tests/models/test_user.py -v`
   Expected: FAIL - "User is not defined"
3. Minimal implementation:

```python
class User:
    def __init__(self, email: str):
        self.email = email
```

4. Verify pass: `pytest tests/models/test_user.py -v`
   Expected: PASS

Tests-first gate branch: step 1 = confirm the committed gate test fails RED; never write or edit gate tests.

## Self-Verification Checklist

- [ ] All tasks implemented and tests passing
- [ ] Interface contracts satisfied exactly
- [ ] All files at exact specified paths
- [ ] No deviations (or deviations documented in the report)
- [ ] No scope creep - only what the tasks specify

**DO NOT COMMIT.** The orchestrator handles all git operations after review.

## Completion Report Format

1. **Files touched:** [every created/modified path]
2. **Verify command + output:** [verify commands; last 20 lines of output]
3. **Deviations:** [none / list with rationale]

## Review Checklist (For Review Agent)

- [ ] Every task row implemented; tests passing, gate tests untouched
- [ ] Interface contracts match exactly (signatures, types, paths)
- [ ] Conventions followed; no bugs, no security issues
- [ ] No scope creep; no debug artifacts or line-number corruption

Output: APPROVED or specific gaps with file + line references.

## Notes

[Edge cases, gotchas, performance notes. Docs-only: per top mapping.]
