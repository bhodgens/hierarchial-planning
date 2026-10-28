# Example Workflow: Auth Feature, Two Tasks End to End

When to use: first run of the subagent-driven loop, or when calibrating prompt shapes for implementer/spec/quality briefs.
Lesson: the loop is dispatch implementer, spec review (PASS required), quality review (APPROVED required), mark complete - and review findings loop back to the implementer, never forward.

```
[Read plan: docs/plans/auth-feature.md]
[Create todo list with 5 tasks]

--- Task 1: Create User model ---
[Dispatch implementer subagent]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, 3/3 tests passing, committed.

[Dispatch spec reviewer]
  Spec reviewer: PASS - all requirements met

[Dispatch quality reviewer]
  Quality reviewer: APPROVED - clean code, good tests

[Mark Task 1 complete]

--- Task 2: Password hashing ---
[Dispatch implementer subagent]
  Implementer: No questions, implemented, 5/5 tests passing.

[Dispatch spec reviewer]
  Spec reviewer: FAIL - Missing: password strength validation (spec says "min 8 chars")

[Implementer fixes]
  Implementer: Added validation, 7/7 tests passing.

[Dispatch spec reviewer again]
  Spec reviewer: PASS

[Dispatch quality reviewer]
  Quality reviewer: Important: Magic number 8, extract to constant
  Implementer: Extracted MIN_PASSWORD_LENGTH constant
  Quality reviewer: APPROVED

[Mark Task 2 complete]

... (continue for all tasks)

[After all tasks: dispatch final integration reviewer]
[Run full test suite: all passing]
[Done]
```

## Implementer brief shape

```
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

Note: no commit step in the brief. Only orchestrators commit (canon C1-Commit); the orchestrator stages and commits after both reviews pass.

## Spec review brief shape

```
CHECK:
- [ ] All requirements from spec implemented?
- [ ] File paths match spec?
- [ ] Function signatures match spec?
- [ ] Behavior matches expected?
- [ ] Nothing extra added (no scope creep)?
OUTPUT: PASS or list of specific spec gaps to fix.
```

## Quality review brief shape

```
CHECK:
- [ ] Follows project conventions and style?
- [ ] Proper error handling?
- [ ] Clear variable/function names?
- [ ] Adequate test coverage?
- [ ] No obvious bugs or missed edge cases?
- [ ] No security issues?
OUTPUT FORMAT:
- Critical Issues: [must fix before proceeding]
- Important Issues: [should fix]
- Minor Issues: [optional]
- Verdict: APPROVED or REQUEST_CHANGES
```

## Final integration review

After ALL tasks pass their two-stage reviews, run the full test suite yourself and dispatch one final reviewer for cross-task consistency: do components work together, any inconsistencies between tasks, ready for handoff. The orchestrator commits the whole feature after that review (canon C1-Commit).
