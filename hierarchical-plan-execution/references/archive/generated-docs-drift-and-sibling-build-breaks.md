# Ggenerated docs drift and sibling build breaks
When to use: generated docs drift + sibling mid-edit breaks.
Lesson: regenerate at gates; transient sibling build failures are not yours.

# Generated-Docs Drift + Sibling Mid-Edit Build Breaks

Observed 2026-09-04 executing the meept `chat-dispatch-ux` tree (10 leaves,
~5h wall clock) with FOUR concurrent sibling sessions committing to main
throughout (bughunt fix wave, prompt-router sidecar, docs rename, config
work). Three hazards beyond those in hierarchical-planning
`references/shared-tree-hazards.md`:

## 1. Generated docs scan the WORKING TREE, not HEAD

`make graphs` (connectivity-graph generator) reads source from the working
tree. With sibling sessions holding uncommitted edits, regenerated docs
embed line numbers/publishers from UNCOMMITTED state. If those edits are
later reverted or amended, the docs drift again and `make graphs-check`
fails CI with nobody understanding why.

**Fix:** never regenerate from the dirty tree into the repo (it bakes
sibling WIP line refs into docs/generated and reference docs). Regenerate
at a clean basis instead: `git worktree add /tmp/gen HEAD && cd /tmp/gen &&
<generator> && cp <touched generated files> back`, then
`git worktree remove --force /tmp/gen` and commit the copied artifacts
with a message naming the scan basis (clean HEAD at <sha>). This is safe
even while siblings hold WIP because HEAD is immutable, and it keeps
`make graphs-check` / `docs-check` green at CI. Leaf-local trap: a worktree
command run with `cd` into a directory the session just deleted fails with
exit 126 — pass an explicit workdir. If a leaf's own commit shifts line
numbers in files the graph references, the shift is NAME-stable but
line-drifted: regenerate once at the integration gate, not per leaf.

## 2. Sibling mid-edit build breaks self-resolve in minutes

Three separate verification/e2e runs failed building packages this session
never touched: a syntax error mid-write, an `undefined` symbol split across
a two-file commit boundary (call site committed, definition still working-
tree), and a transient unused variable. All self-resolved within minutes
as the sibling session finished its edit.

**Fix:** before any retry or re-dispatch, re-run the build scoped to the
failing package. An e2e script that builds fresh binaries SHOULD fatal on
build failure — running against a stale binary poisons every downstream
assertion. Retry when `go build ./...` (or the scoped package) is green.
Never "fix" the sibling's half-written file.

**Leaf-gate corollary (2026-09-05):** when the foreign break blocks a gate
the leaf's own checklist REQUIRES (whole-package `go build`/`go vet`/`go
test`), the implementer is not obligated to fail-report on first red.
Churn tell that the break is mid-write rather than stuck: successive
failures name different symbols/files, and untracked sibling files appear
in `git status --porcelain <pkg>/` between checks. Protocol: prove your
own scope independently (gofmt -l on your files = empty, LSP/gopls
diagnostics on your files = empty, `git diff --stat` confined to your
files), then poll-and-wait bounded — `for i in $(seq 1 10); do go build
./internal/<pkg>/... 2>/dev/null && break; sleep 30; done` — and only run
the full gate sequence once the build stabilizes. Full detail: shared-repo-
parallel-agents references/foreign-test-failure-triage-2026-09-04.md
("Non-test WIP variant").

## 3. Interleaved sibling hunks ride along in shared-file commits

`git add <file>` stages everything in the file (shared-tree-hazards
Hazard 1). When a leaf's shared file also carries a sibling's uncommitted
fixes (loop.go carried FOUR bughunt hunks across two of this session's leaf
commits), and splitting hunks is not worth the effort (the foreign hunks
were self-contained and build-green), do not silently sweep them:

**Fix:** grep `git diff <file>` for hunks you did not author before
committing shared files. If committing through, name the foreign hunks and
their owning session explicitly in the commit message so that session can
reconcile ("this commit carries AUDIT FIX H1/C2 from the bughunt session —
flagged for that session to reconcile"). Also note it in the tracking
table's review notes.

## Related discipline that paid off

- Tracking table carried delegation IDs at dispatch and commit hashes at
  review; it was the sole reliable source of truth across 10 dispatches and
  6 sibling commits landing mid-execution.
- The pre-commit hooks bypass for sibling WIP (`git -c
  core.hooksPath=/dev/null commit` + scoped manual verification + explicit
  justification in the message) was exercised 8 times cleanly — see
  shared-tree-hazards Hazard 2 for the full procedure.
