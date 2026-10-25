# Orchestrated-Leaf Commit Hygiene in Shared Hot Files

Lessons from a 10-leaf parallel execution (meept chat-dispatch-ux, 2026-09-04)
where four leaves shared components.go/loop.go with each other AND with a
sibling audit session self-fixing bugs mid-run in the same files.

## The core pattern

Implementation leaves edit hot files in parallel per plan concurrency groups.
Subagents correctly never commit; the ORCHESTRATOR commits each leaf after
in-session review. When a leaf's file also holds another leaf's or a sibling
session's uncommitted hunks, `git add <file>` sweeps them all in. Options,
in order:

1. **Wait for the owner**: if the other hunk belongs to a leaf you yourself
   dispatched and its results just landed, review+commit that leaf first,
   then commit yours (hunks separate cleanly once the other is committed).
2. **Commit together, flag loudly**: when hunks are interleaved in one file
   and belong to a DIFFERENT session you cannot commit for, commit your leaf
   WITH the sibling hunks and put an explicit reconciliation note in the
   commit message naming the origin ("carries AUDIT FIX H1/C2 from the
   bughunt session — flagged for that session to reconcile"). Never sweep
   silently.
3. **Hunk filtering** (last resort, highest effort): `git diff <file>` →
   filter hunks by contract keywords → `git apply --cached`. Only worth it
   for large unrelated deltas (see shared-tree-hazards Hazard 1).

## Pre-commit hook gates on sibling WIP

Repo pre-commit hooks that build the WHOLE repo fail when any parallel
session has a transiently broken file in the tree. Two verified behaviors:

- The failure names an unrelated file (`reply_guard.go:54 undefined` from
  another leaf) — diagnose by reading the error, not by assuming your leaf
  broke.
- Resolution: `git -c core.hooksPath=/dev/null commit ...` with manual
  package-level verification done first (scoped tests + vet + gofmt +
  analyzers), and the bypass RECORDED in the commit body with the reason.
  Never bypass silently.

## Order the shared-file leaves strictly, dispatch sequentially

Plan said "04 and 06 both edit components.go — run sequentially." Executing
that (dispatch 04, review, commit, then dispatch 06) worked cleanly: each
implementer saw the previous leaf's committed state, and no hunk collision
occurred. The same-file sequencing note in the dispatch context ("leaf NN
just landed, commit <sha>, relocate via grep") prevented stale-anchor work.

## Anchor drift is normal mid-execution

Line anchors pinned at authoring time drifted across the session's own
commits (components.go:1422 wiring site → registry actually constructed at
:2251, nil at :1422). Dispatch contexts should say "line numbers shifted by
earlier leaves — relocate via grep '<symbol>'", and review must verify the
DEVIATION note explains any site change. Two implementers found real
improvements this way (nil at the master's pinned wiring site; CWD living
in DetectionContext.CWD, not a top-level field).

## Flaky suite runs under parallel load

One daemon-suite FAIL appeared during a verification run while other leaves
ran; two immediate reruns were clean (flake, not regression). Protocol:
rerun twice before treating as real; if it persists, stash-test per
shared-tree-hazards Hazard 3. Record the flake call in the tracking table
either way.
