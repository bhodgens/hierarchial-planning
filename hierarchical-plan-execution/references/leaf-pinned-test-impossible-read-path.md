# Pinned Test with an Impossible Read-Path — Swap the Loader, Keep the Assertions

Leaf docs sometimes pin a TEST whose assertions are correct but whose read
mechanism is impossible against real repo behavior the planner never executed.
The failure is BEHAVIORAL COMPOSITION, not API drift: the leaf's own pinned
production flow (step A) makes the leaf's pinned test read path (step B)
return not-found — both halves are individually real code, but the planner
never composed them. The pinned test then fails in a way that looks like YOUR
implementation is broken when it isn't.

## Anatomy (2026-09-05, meept claim-temporal-validity leaf 01)

- Pinned flow: `MarkSuperseded` calls pre-existing `markVersionNonCurrent`
  → `UPDATE ... SET is_current = 0`.
- Pinned test: loads the stamped row via pre-existing `GetByID`, whose SQL
  filters `WHERE id = ? AND (is_current = 1 OR is_current = '')`.
- Result: `GetByID(oldID)` returns ErrNotFound for ANY superseded claim,
  regardless of the new stamping code. Deterministic, pre-existing, nothing
  to fix in product code (fixing it would be a behavior change outside the
  leaf's file scope).

Verification-before-coding does NOT catch this class: every symbol the test
uses exists with the documented signature. Only running the pinned test RED
exposes it. So: write the pinned test verbatim first, run it red, and read
the failure mode before touching product code.

## Triage protocol when the pinned test fails red

1. Localize the failure. If it fails at a LOAD/READ step before any
   assertion on your new code, suspect a read-path conflict, not a bug in
   your implementation. Prove it empirically (sqlite3 probe of the exact
   WHERE clause, or a minimal repro) — don't argue from the SQL text alone.
2. Classify: (a) your code wrong → fix your code; (b) leaf test wrong about
   repo behavior → triage below; (c) genuine contract conflict → STOP and
   report per the leaf's escalation clause.
3. For (b): the CONTRACT is the assertions, not the plumbing. Keep every
   pinned assertion byte-identical (same IDs loaded, same values checked)
   and swap ONLY the load mechanism for one that reads the same row/ID
   without the blocking filter (here: `GetVersionHistory(id)`, which has no
   is_current filter). Add an assertion that pins the property the swap
   implicitly verifies (e.g. `len(history) == 1` proves same-row/in-place).
4. Annotate the swap in the test with a dated review note naming the two
   conflicting pre-existing behaviors, and list it as a DEVIATION in the
   final report — the orchestrator needs it for OPEN-QUESTIONS and for
   downstream leaves that inherit the assumption.

## Downstream impact note (cheap, high value)

When a leaf assumption turns out impossible, check whether LATER leaves in
the same tree inherit it and say so in the report ("GetByID cannot fetch
superseded claims — relevant to leaf 02's ListExpiredClaims filtering, since
expired-but-not-superseded claims remain current and are unaffected"). Two
sentences at report time save a re-dispatch later.

## What NOT to do

- Don't "fix" the product read path to make the pinned test pass — that's a
  scope-violating behavior change (fourth file / cross-leaf semantics).
- Don't weaken or delete pinned assertions to go green; the orchestrator's
  review compares assertions against the contract.
- Don't silently edit the leaf doc itself; the deviation report is the
  channel.
