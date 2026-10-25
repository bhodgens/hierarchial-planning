# Pitfall: Sibling orchestrator racing the SAME plan tree (orchestrator side)

Observed 2026-09-02 (meept llm-resilience-forest tree-03): this orchestrator
completed leaf 01, then dispatched group B (leaves 02+03 in parallel). While
those workers ran, a SECOND orchestrator session on the same checkout
implemented and committed the SAME leaves (1d94e2da, 4739c151) plus a
tracking-close commit (04919c01) whose note claimed it had also "dispatched
leaf 04" (it never landed). Leaf-side stand-down is covered in
pitfall-double-dispatch-leaf-race.md and
devops/multi-agent-git-coordination references/sibling-whole-leaf-standdown.md;
this file is the orchestrator's playbook.

## 1. Accept foreign leaf commits only after YOUR OWN review

A sibling's commit message citing the leaf is a claim, not a review. Before
building on it or flipping tracking rows: run the leaf doc's verify commands
+ the master's Dispatch Protocol lines + the review-checklist greps yourself
(contract symbol grep, byte-identical/parity checks, scoped suites). This
session verified ThrottleGiveUpError's contract shape, the
safeTransition→Transition→isValidTransition path, the queue requeue UPDATE's
explicit `interactive` preservation, and the full goal/queue coverage matrix
before marking rows COMPLETE.

## 2. "The sibling said it dispatched leaf N" ≠ leaf N is coming

Their dispatch can silently never materialize. Before dispatching your own
implementer (or concluding the tree is stuck), gather evidence over a
BOUNDED window (~30-45 min):
- new commits touching the leaf's file set (`git log --oneline -- <paths>`)
- working-tree activity in that set
  (`find <paths> -newermt '<last-commit-time>' -type f`)
- the shared Hermes delegation cache
  (`ls -lt ~/.hermes/cache/delegation/subagent-summary-*`) — cross-session
  per-user cache; a summary naming the leaf = their worker FINISHED; no
  summary after a long window = dispatch likely never happened.
All quiet after the window ⇒ dispatch your own, with the hardened brief in
§4. During the wait, run a background git-log watcher (30 s poll, bounded,
notify_on_complete) instead of blocking, and spend the time on verification
of the already-landed leaves.

## 3. False-live signals

- `.claude/worktrees/agent-*` entries in `git worktree list` look like live
  workers; probe with `find <worktree> -newermt '<time>' -type f` — zero
  recent mtimes = stale, ignore them as sibling evidence.
- The sibling orchestrator's earlier tracking/doc commits are not evidence a
  worker is mid-flight NOW.

## 4. Harden dispatch briefs for contended trees

The brief that landed leaf 04 cleanly (24 files, zero collisions despite the
sibling's earlier activity) carried:
- an expected-HEAD pin: "before your FIRST write: `git log --oneline -1` +
  `git status --short`; if HEAD ≠ <sha> or your target files are dirty,
  STOP and report instead of writing"
- an explicit file-ownership map: exclusive targets vs FORBIDDEN (sibling
  lanes' in-flight files, named)
- a standing abort rule: "if at ANY point you find uncommitted modifications
  in a target file that you did not make, or a new commit lands containing
  this leaf's content (WaitInfo, its labels, its invariant), ABORT that file
  and report the collision"

## 5. Tracking reconciliation when the sibling closed rows first

The sibling's 04919c01 had already flipped rows 01-03 to COMPLETE. Layer,
don't redo: fresh-read the table, keep their status/hashes as facts, add
dispatch attribution + review notes + a shared-checkout note, and correct
only factually wrong cells (e.g. iteration counts). Commit message names
both sides' shas. (Same family as shared-repo-parallel-agents §6d
close-out race; see also §10 there for conflict resolution.)
