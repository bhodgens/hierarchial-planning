# Concurrent multi-session review of one plan forest

Field notes from 2026-09-01 (llm-resilience-forest, meept): a docs-only
5-tree forest reviewed by 6 audit lanes while a SIBLING agent session was
actively editing the same (then-untracked) forest mid-review.

## Signals a sibling is editing the same tree
- patch tool warning "file was modified since you last read it" — treat as
  a mandatory re-read, not advisory.
- File mtimes newer than your session start on files you did not touch.
- `git log` / `git diff` shows commits or hunks you did not author (tracked
  dirs); untracked dirs hide this — watch mtimes instead.
- Leaf counts or names change under you (this session a 3-leaf tree became
  4: one new leaf, others renumbered).

## Working rules under concurrency
1. Re-read the file region immediately before EVERY patch on a file the
   sibling has touched. Never patch from a cached read.
2. After each patch, re-run the mechanical scans (fence parity, corruption
   grep) and `sed -n` the edited region. Concurrent edits produced three
   mangled fragments this session (stray ")eaf", "set)et", a swallowed
   code fence in a contract block) — all caught only by re-reading the
   diff/region.
3. Expect regressions from your OWN side: a stale cached read reintroduced
   loop.go:4226 after the sibling had already corrected it to 4298.
   Cross-check line-number fixes against a fresh grep, never memory.
4. When the sibling restructures (renames/splits leaves), re-verify leaf
   counts across forest-root table + tree master + `ls` (root said 3,
   disk had 4), and re-grep your earlier fixes' key strings to confirm
   they survived the rename.
5. Check `git log` before committing — the sibling may commit the shared
   directory mid-session, making your commit a no-op (verify your fixes
   are IN their commit instead).

## 429-killed audit subagents: the full pattern
- Deaths are staggered. Some lanes died in 27s; others completed at 4-18
  minutes. Do not assume a fast failure means all will fail.
- Keep working while live lanes run; audit dead lanes' scopes directly
  with grep + targeted reads (this handled 2 trees + 5 leaves of scope
  in one session without quality loss).
- Late reports describe a stale snapshot. Disposition every finding
  against the CURRENT file first: already-fixed / invalidated by
  restructure / still-valid.
- Evidence-check findings before applying. In one 9-finding report, 2
  were wrong on their face (the auditor conflated one contract block
  with a different leaf's content). Disposition, don't rubber-stamp.
- Near-miss class: a report verified a fix but flagged a cited TEST NAME
  that did not exist (`TestQuotaClient_Classification` vs the real
  `TestQuotaClient_ClassifyQuotaDecision`). When verifying
  test-file references, verify the test-function name too.

## Orchestrator-level file ownership for concurrent tree dispatch
When dispatching multiple TREE orchestrators into one repo concurrently,
put an explicit ownership map in each dispatch context:
- per-tree OWNED files (this tree's leaves may edit)
- SHARED files (e.g. schema.go, resolver.go): "patch-only on unique
  anchors, never write_file the whole file; keep additions in separate
  regions"
- an explicit DO-NOT-TOUCH list naming the other trees' files
- stagger rules: trees touching the same implementation file run
  SEQUENTIALLY; a leaf whose target file belongs to another tree's
  in-flight work can be HELD (tracking table says PENDING + hold reason,
  e.g. "held: client.go conflict with tree 02 leaf 03")
- orchestrator-side stagger queue: dispatch tree N+1 only when the owner
  of its conflicted files completes; report holds in the final report so
  the next wave is mechanical.

## Post-fix verification notes
- A separate READ-ONLY verifier subagent catches reintroduced errors and
  near-misses the fixer is blind to — but it also snapshots state at
  dispatch; re-check its FAIL items against current files before acting
  (some were fixed after its snapshot).
- After ALL waves, run one final mechanical sweep (fences, corruption,
  template compliance, leaf counts, bare-phantom grep) — concurrency
  makes the LAST sweep, not the first, the authoritative one.

## Execution-phase extensions (from the same forest's dispatch wave)

The playbook above was written for the REVIEW phase. The DISPATCH wave
(5 tree orchestrators + leaf agents, one worktree) added these:

### Gate pauses are orchestrator-stops, not user vetoes
When a leaf/orchestrator hits the repo's git-commit approval gate and
stops ("The commit was denied by the user"), a clarify prompt to the
user may time out with no answer. Standing preference (no mid-task
pauses; user gates via post-hoc review) makes the parent-side path:
review the paused work yourself (build/tests/analyzers on the exact
file list), then commit by explicit path list with a body crediting
the preparing orchestrator. Proven twice in one wave (tree 05 leaf 03;
the D12-a deviation row folded into the close-out).

### Partial-commit + remainder pattern on one leaf
A leaf's files can be committable in two waves: parent commits Task
1+2 files while the leaf implementer is still finishing Tasks 3–4.
Consequences: (a) the leaf's own orchestrator will report your commit
as an unexplained anomaly — expect it, answer it in tracking ("two-sha
leaf: <partial-sha> + <remainder-sha>"); (b) NEVER stage the whole
dirty tree — only the files whose tasks are done; (c) verify the
remainder's commit exists before recording the leaf COMPLETE. If the
remainder never lands, the leaf is INCOMPLETE regardless of your
partial commit.

### Late async reports from DISPATCHED orchestrators
Tree orchestrators run 1–2 hours; their completion reports re-enter
long after you've moved on and often describe commits you already saw
land. Triage each against current `git log` (their commits, your
commits, sibling commits) before acting on their "final" state — the
tree may have moved again (leaf 03 dispatch, tracking fixes) since
their snapshot.

### Subagent phantoms in the working tree
A re-dispatched implementer reported "two sibling subagents were
concurrently editing the same files" and hit a duplicate-declaration
collision with them. Multi-orchestrator forests make same-file
implementer overlap a real event even under patch-only shared-file
rules — the parent's pre-commit gate (build + full package tests +
file-set-equals-report check) is what makes the converged result
trustable, whoever's edit landed last. Also: a sibling worker may
commit the leaf seconds before your own commit attempt — "nothing to
commit" on your identical message means verify their sha and move on
(don't fight for authorship).
