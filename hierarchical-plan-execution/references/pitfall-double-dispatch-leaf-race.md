# Pitfall: Double-Dispatch Leaf Race (re-dispatch while first dispatch still runs)

Observed 2026-09-01 (meept llm-resilience-forest, tree 01 leaf 04): a leaf
dispatch that appeared dead (no completion notice reached the orchestrator)
was re-dispatched while the original session was still working. Two leaf
sessions edited the same files concurrently — converging on the same gaps
produced duplicate helper/field declarations (`effectiveMaxFixLoops`,
`baseModelRef`) — and the tree also carried uncommitted output from an even
earlier dead dispatch. Leaf-side protocol lives in
`devops/multi-agent-git-coordination` pitfall #16; this file is the
orchestrator-side prevention.

## Before re-dispatching a leaf that "never completed"

1. **Inventory its target files**: `git status --short` plus grep for the
   leaf doc's contract symbols (exported function names, topic constants).
   - **Uncommitted implementation present** → a prior dispatch wrote but
     died before verifying/reporting. Either dispatch a VALIDATOR brief
     ("validate this existing work against the leaf doc + interface
     contracts, close gaps via TDD, report") or consciously clean it —
     never a fresh from-scratch brief, which clobbers possibly-correct work
     and makes the review compare two competing implementations.
   - **Nothing present** → dead-clean (see
     multi-agent-git-coordination #14 "leaf can die CLEAN"); a fresh
     re-dispatch is safe — say so in the brief so the new leaf does not
     hunt for a predecessor's work that never existed.
2. **Check for a LIVE session**: `pgrep -fl hermes` and recent mtimes in
   the leaf's target directories (a file touched within the last ~10 min =
   still working). If live, re-dispatch is a collision, not a recovery —
   wait, or let the live session finish and review its output.
3. **Check the tracking table**: a PENDING/IN_PROGRESS row plus present
   files = an earlier dispatch is mid-flight; mark it and wait — do not
   double-book the leaf.

## If the race already happened

- The second-dispatch session should validate-and-converge: keep ONE copy
  of any duplicated helper (identical behavior — either is valid), drop its
  own duplicate, rebuild. Never rename to dodge the collision — that forks
  the logic into two sources of truth.
- When the sibling is implementing the ENTIRE leaf (signatures differ, whole
  files collide) convergence is impossible — the second dispatch must
  STAND DOWN and end as a verification report of the sibling's
  orchestrator-committed work. Full worked protocol (2026-09-02 meept
  tree-03 leaf-02): `devops/multi-agent-git-coordination`
  `references/sibling-whole-leaf-standdown.md`.
- Its report must NAME the sibling sessions (subagent ids) so the
  orchestrator can verify the double-dispatch, reconcile the tracking
  table, and wait for sibling quiescence (advancing mtimes) before any
  commit touching those files.
- If the racing sibling is another ORCHESTRATOR (not a duplicate leaf
  dispatch), the orchestrator has its own playbook — verify foreign leaf
  commits yourself before accepting, treat a sibling's "dispatched leaf N"
  claim as unproven (gather bounded evidence incl. the delegation-summary
  cache), harden briefs with HEAD-pin + file-ownership map + standing abort
  rule, and LAYER tracking-table detail on the sibling's close-out rows:
  `references/orchestrator-sibling-tree-race.md` (2026-09-02 meept
  tree-03 full worked case).

## Related: orchestrator must not patch a file a still-running leaf owns

meept-bench phase-2 leaf 01 (2026-09-01): the leaf agent was iterating on a
task prompt inside its fragment while the orchestrator had already decided
the correct fix. The orchestrator held the edit (running-subagent rule) and
the agent converged on the SAME fix itself within its 3-attempt cap —
attempt 3 adopted the pinned phrase form unprompted. Holding cost zero
tokens and avoided a duplicate-writer collision. Corollary: leaf
self-iteration counts (the 3-attempt caps in dispatch briefs) exist
precisely so the orchestrator doesn't have to micro-fix prompt-level issues
— let the cap work before intervening. This mirrors main SKILL.md Pitfalls
43/44 (orchestrator fixing mid-flight / post-landing build errors in
subagent-owned files), observed from the orchestration side.
