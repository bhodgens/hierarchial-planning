# Verify-Only Contract Tasks & Single-Slot → Parallel State Migration (meept phase-frontier-parallel leaf 03, 2026-09-05)

Leaf 03 of docs/plans/phase-frontier-parallel: Contract D (per-phase worktree
provisioner hook), Contract E (per-phase-start hook — "VERIFY, don't
rebuild"), and the Task-3 survey fork (BudgetHierarchy.currentPhase single
slot). Dispatched TDD, no-commit protocol. Four class-level lessons survived.

## 1. "VERIFY, don't rebuild" tasks can genuinely fail verification

Contract E was marked "no code change expected here; a regression test
only." The regression test (exactly 3 hook calls for 3 phase starts) FAILED
— exposing a real leaf-02 bug: the startPhase re-entrancy guard checked only
`step.State == StepPending`, but phase start STAMPS ConversationID without
changing step state (state changes only when the scheduler later picks the
step up). A later frontier advance re-started an already-running phase
(hook record: `->B ->C ->C ->D` instead of `->B ->C ->D`).

Rules:
- Write the verification test FIRST and watch it fail — TDD applies to
  verify-only tasks. A "verification passed" you never saw fail proves
  nothing about the mechanism it claims to pin.
- When verification contradicts the plan's premise: fix minimally IF the fix
  site is inside the leaf's file scope (here: orchestrator_phases.go), and
  promote the finding to the TOP of the completion report. Do not expand
  scope, do not silently swallow, do not weaken the test to match the bug.
- Guard pattern: when a start operation's observable is a STAMP
  (conversation ID, marker column) rather than a state transition, the
  re-entrancy guard must check the stamp too — `state == pending && stamp
  == ""` is the not-started predicate.

## 2. Single-slot → parallel-safe migration (Go) — the mechanical pattern

The survey confirmed the leaf's fork AND found a second slot in the same
mechanism (the `turnBudget` pointer, overwritten alongside `currentPhase` by
the same Select/Advance methods). Disposition rule: an additional slot in
the SAME mechanism = same fix, do together; additional single-slot state
ELSEWHERE = STOP and report per the leaf (scope discipline).

The migration shape that tested clean (serial-equivalence table proves
flag-off behavior unchanged):
- Replace slots with `selectedPhases map[string]bool` +
  `phaseTurnBudgets map[string]*BudgetAllocation`; keep ONE legacy handle
  (`turnBudget`) meaning "most recently engaged" solely for byte-compatible
  serial reads/status.
- Select becomes idempotent-per-key (re-select = no-op, preserving the
  running phase's budget continuity) — otherwise parallel re-entry mints
  duplicate child allocations and resets usage.
- Record methods gain a routing key: `RecordUsage(tokens, phaseID)`. Update
  callers mechanically (leaf checklist greps RecordUsage/SelectPhaseBudget;
  this repo had 1 prod site + 2 test sites).
- Read accessors switch to SUM semantics across selected keys, documented
  as a deliberate semantic change (the leaf authorizes updating exactly
  those assertions with a citation); add a per-key accessor
  (`TurnBudgetFor(phaseID)`).
- Carryover/advance becomes per-key with an explicit from:
  `AdvancePhaseFrom(from, to)`. The legacy `AdvancePhase(to)` DELEGATES
  with serial-only resolution (turn handle → single-selected fallback).
  NEVER let the legacy wrapper resolve the from-key by map iteration order
  when several keys are selected — that guesses, and a wrong guess
  teleports budget between two live phases (this exact failure showed up
  in the first parallel test run).

## 3. Derive table expectations from multi-actor semantics, not a serial mental model

The RED table asserted `wantCalls: 1` for one advance; the frontier advance
legitimately starts B AND C → 2 provisioner calls. When a contract says
"exactly once per X" and one operation fans out to several X, count PER-X
(`countPhase("B")`), not per-operation totals. Also: table assertions that
run before the case's `check()` see only advance-1 state — `wantCalls` must
reflect the state at assertion time; put post-step-2 assertions inside
`check()`. Watch a `-v` run and read the actual counts before "fixing" the
implementation — twice this session the implementation was right and the
expectation was serial-brained.

## 4. Whole-file test rewrites reintroduce transcription bugs — patch-append instead

Rewriting a 539-line test file with write_file (instead of patch-appending
the new tests and patching field references) silently un-escaped `%%` → `%`
inside an existing t.Errorf (vet: "%d reads arg #2, but call has 1 arg").
Hand-transcription of escape sequences is exactly where whole-file rewrites
fail. Rules: extend big test files with patch (append block + targeted
field-ref edits); if a rewrite is truly required, re-read the whole file
first (write_file warns on partial-view overwrites — heed it) and afterwards
grep format strings for unescaped `%[sdqvf]`.

## Session hygiene that worked (confirmations, not new lessons)
- Scoped build to `./internal/...` when a sibling session's stray untracked
  cmd file broke `go build ./...` (already in pre-dispatch-drift-and-baseline.md).
- The leaf's explicit caller-grep checklist item (RecordUsage/SelectPhaseBudget
  stragglers) caught every call site before the first full-suite run.
- Line-number corruption grep (`grep -rcE '^\s*[0-9]+\|'`) run on every
  touched file before reporting done — all zero.
- Survey-fork leaf discipline: re-verify every cited line number before
  editing (all cited anchors had drifted slightly; grep, don't trust).
