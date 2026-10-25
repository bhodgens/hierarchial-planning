# Tests-First Gate — full recipe

Mandatory phase for every CODE plan tree: implement the full unit + e2e test
suite for a branch BEFORE dispatching that branch's implementation leaves.
Authored 2026-10-24 at user direction. SKILL.md §"Tests-First Gate" carries the
short rules; this file carries the procedure.

## Roles

| Role | Who | Does |
|------|-----|------|
| Test implementer | Subagent (`delegate_task`) | Writes unit + e2e tests for its test leaf. Does NOT write implementation. Does NOT commit. |
| Control agent | Orchestrator, main model, IN-SESSION | Validates returned tests against the plan. Owns the delta protocol. Never a delegated subagent (same rationale as review: delegate_task children inherit delegation.model). |
| Implementation agent | Subagent | Makes the validated RED tests pass. Must not delete, weaken, skip, or rewrite gate tests. |

## Tree shape

Every code branch gains test leaves paired with its implementation leaves:

```
02-data-model/
  orchestrator.md          # carries ## Test Gate + Phase 0 dispatch
  00T-unit-tests.md        # test leaf (dispatched FIRST)
  00T-e2e-tests.md         # test leaf (dispatched FIRST, parallel with 00T-unit)
  01-schema.md             # impl leaf — gated on BOTH 00T leaves
  02-migrations.md         # impl leaf — gated on BOTH 00T leaves
```

- Naming: test leaves carry a `T` suffix in their number (`00T-`, `01T-`) so
  the gate reads off the child index at a glance.
- Default pairing: one test leaf per implementation leaf. Merge when several
  small impl leaves share one behavior surface; split when one impl leaf spans
  unit and e2e concerns (keep the one-leaf-one-language rule).
- A test leaf is sized like any leaf: ≤110K estimated context, ≤3 files rule
  relaxed only for test files (test-only leaves may create more files because
  they carry no implementation risk — but still one language per leaf).
- Root-level e2e: the root master.md owns cross-branch e2e test leaves that
  exercise the interface contracts between branches. Branch test leaves cover
  within-branch behavior.

## Coverage matrix (the validation artifact)

The control agent builds/maintains this table in the orchestrator's
`## Test Gate` section BEFORE dispatching test leaves, then fills the Test
column as leaves return:

| # | Feature (from plan) | Source (leaf/spec §) | Unit tests | E2E tests | Status |
|---|---------------------|----------------------|-----------|-----------|--------|
| F1 | Session creation returns UUID | 01-schema.md Task 1 | TestSession_CreatesWithUUID | e2e_auth_flow:1 | VALIDATED |
| F2 | Expired session rejected | 01-schema.md Task 2 | (missing) | (missing) | DELTA |

Rules:
- One row per feature the branch delivers — derive rows from the branch's
  leaf task specs and interface contracts, not from memory.
- Every row must reach VALIDATED (≥1 unit test AND e2e coverage where the
  feature is user-visible or crosses a contract boundary) before ANY
  implementation leaf in the branch dispatches.
- Pure-internal helpers may be marked `E2E: n/a` with a one-line reason.

## Delta protocol (plan vs tests disagree)

When validation finds a delta, **update the LESSER of the two artifacts to
reflect the GREATER** — coverage always converges upward, never by deletion:

1. **Plan has a feature the tests miss** → tests are lesser. Re-dispatch the
   test leaf with the specific missing rows ("add tests for F2, F5 — exact
   behaviors quoted from the leaf spec"). Loop until covered.
2. **Tests assert behavior the plan never specified** → plan is lesser. The
   control agent amends the plan: add the feature to the leaf spec /
   interface contracts / tracking, with the test name as the citation. If the
   invented behavior is wrong (contradicts the design spec), delete the test
   instead and record the rejection in the Test Gate section — this is the
   one sanctioned deletion, and it requires a written rationale.
3. **Ambiguity: cannot tell which is authoritative** → the upstream design
   spec (GDD/contract doc) decides; if it is silent, it becomes an
   OPEN-QUESTION for the user (Step 6.8 walkthrough). Do not guess.

Every delta resolution is recorded in the Test Gate section: date, feature
ID, direction (tests-updated / plan-updated / test-deleted), one-line reason.

## Dispatch flow (Phase 0)

Embedded in each code-branch orchestrator's `## Dispatch Protocol`:

### Phase 0: Test gate

1. Build the coverage matrix rows from the branch's leaf specs.
2. Dispatch test leaves as subagents (batch to the concurrency cap). Brief:
   - Full test-leaf document text + the branch's interface contracts INLINED
   - "Write tests ONLY. Do NOT write or modify implementation files. Tests
     will fail (RED) — that is the expected end state. Run them once to
     confirm they fail for the RIGHT reason (missing implementation, not
     syntax errors). Do NOT commit. Do NOT git add."
   - Corruption rules (no read_file→write_file, write once and stop)
3. On return, the control agent validates IN-SESSION:
   - Run the tests: they must compile/parse and fail for missing-implementation
     reasons only (in Go: build tags or `_test.go` against empty packages are
     fine; syntax errors are not).
   - Map every test back to a coverage-matrix row; update the matrix.
   - Apply the delta protocol until every row is VALIDATED.
   - Check test quality: assertions on behavior (values, state transitions),
     not on implementation details; no tautologies (`assert x == x` shapes);
     e2e tests exercise the real contract surface, not mocks of it.
4. Orchestrator commits the validated test files:
   `git commit -m "test(scope): gate tests for [branch] (F1-Fn)"`
5. Set branch status TESTS_VALIDATED in the tracking table.

### Phase 1+: Implementation (gated)

- Dispatch implementation leaves ONLY for branches at TESTS_VALIDATED.
- Implementation brief adds: "The gate tests already exist at [paths] and are
  committed. Your job: make them pass. Do NOT delete, skip, weaken, or
  rewrite any gate test. If a gate test appears wrong, STOP and report it —
  the orchestrator runs the delta protocol; you do not."
- Review (existing protocol) gains one check: `git diff` shows no
  modifications to gate test files by the implementer. Any such modification
  is an automatic NEEDS_FIXES.
- Leaf review passes only when the branch's gate suite is GREEN.

## Parallelism rules

- Test leaves across DIFFERENT branches dispatch in parallel (no gate waits
  on another branch's gate).
- Within a branch: all test leaves parallel; implementation strictly after
  TESTS_VALIDATED.
- Implementation leaves across validated branches run in parallel per normal
  concurrency rules.
- NEVER: implementation dispatch in a branch whose gate is incomplete, even
  if the implementation is "obvious" or the tests are "probably fine". The
  gate is the plan's executable form; skipping it reverts to unverified
  self-reported completion (Pitfall 24's class of failure).

## Interaction with existing skill mechanics

- **TDD inside impl leaves:** the leaf-template's TDD steps change shape —
  Step 1 (write failing test) becomes "confirm the gate test fails", Step 3
  stays (write implementation). Impl leaves may still add NEW tests for edge
  cases the gate missed; those additions flow through review like any code.
- **Commit policy:** unchanged — orchestrator-only. Gate tests get their own
  commit at TESTS_VALIDATED; impl commits reference the gate.
- **Tracking statuses:** TESTS_IN_PROGRESS and TESTS_VALIDATED insert between
  PENDING and IN_PROGRESS.
- **Timeouts/429s on test leaves:** same recovery as impl leaves (Pitfalls
  13, 25) — check disk first; test files often landed; orchestrator may
  finish small test gaps directly, then still run its own validation pass.
- **Docs-only / ops trees:** `## Test Gate` present but marked
  `N/A — docs-only tree` (or ops equivalent) with the substitute verification
  named (cross-reference resolution, manifest checks). The compliance scanner
  requires the heading to exist so the omission is always deliberate.

## Compliance

`check_template_compliance.py` requires `## Test Gate` in every
orchestrator/master. A tree failing only on Test Gate is one section away
from compliant — write the coverage matrix into it.

## Pitfall 46: Skipping or weakening the test gate

Failure modes seen in pre-gate plan execution that the gate exists to prevent:
- **Impl-first drift:** implementation dispatches "because the tests are
  obvious" — the leaf then self-reports GREEN against tests it wrote itself
  (Pitfall 24's class: 125 passing tests, missing feature). The gate's
  coverage matrix is what makes "every feature tested" checkable.
- **Implementers editing gate tests:** an impl agent that "fixes" a failing
  gate test by weakening the assertion silently converts the gate to
  self-review. Any diff to gate test files by an implementer = automatic
  NEEDS_FIXES; the delta protocol belongs to the control agent only.
- **Validating by summary:** accepting a test subagent's claim "all features
  covered" without running the tests and mapping them to matrix rows. The
  control agent must run the suite (RED for the right reasons) and fill the
  matrix itself.
- **Downward convergence:** resolving a plan/test delta by deleting the test
  or trimming the plan without written rationale. Deltas converge UP: lesser
  artifact updates to the greater. The only sanctioned deletion is a test
  that contradicts the upstream design spec, with the rationale recorded in
  the Test Gate section.

