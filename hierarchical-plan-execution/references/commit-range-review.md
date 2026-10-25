# Commit-Range Regression Review (post-execution gate)

Reviewing "the commits this session made" (or a branch slice) after a plan
tree executes. This is the fix-wave re-audit the orchestrator owes after
execution — distinct from per-leaf review.

## Scope and dispatch

1. Range: `git diff <baseline-sha>..HEAD`. Baseline = merge-base with the
   tracking branch, or the commit before the first session commit. Confirm
   scope with `git log --oneline <baseline>..HEAD` and exclude sibling
   workstream commits below the baseline.
2. Slice large ranges into parallel read-only reviewer dispatches by area
   (money paths / DB+infra+UI / workers+webhooks). Each dispatch carries:
   - The architecture INTENT: which invariants must hold (fail-closed
     paths, byte-compatible incumbent paths, processor-of-record vs toggle),
     phrased as "explicitly answer with a verdict line per invariant".
   - Verified baseline facts (e.g. "this test fails identically at the
     baseline commit — out of scope").
   - Read-only instruction: reviewers never modify files.
3. Reviewer output: severity-ranked findings, each with file:line + a
   concrete failure scenario.

## Proving pre-existing vs regression

Never assume; reproduce at baseline with a temp worktree:

```bash
git worktree add /tmp/baseline-<sha> <baseline-sha>
cd /tmp/baseline-<sha>/<module> && <exact same test command>
cd - && git worktree remove --force /tmp/baseline-<sha>
```

A failure that reproduces at baseline is documented and excluded — not
fixed, not counted. Never obtain a baseline via stash/checkout in a shared
repo (detached-HEAD fallout; see shared-tree-orchestration-pitfalls.md).

## Fix disposition

- Fix only what you're authorized to fix (user said "fix them" = yes;
  audit mode = report only).
- One commit per concern, explicit paths, never `-a`/`git add .`.
- If a parallel workstream's UNCOMMITTED edits already fix a finding:
  verify the combined tree (vet/build/module tests with `-count=1`) and
  record the disposition — do not double-fix, do not commit their wave.
- Cheap mechanical finds (gofmt/align drift after a field addition) fix
  immediately as their own style commit.
- Write a review record (verdicts, findings → dispositions, pre-existing
  items) into the repo; commit it separately from fixes.

## Static scans that earn their keep

- Secrets: `git diff <range> | grep '^+' | grep -iE "(api_key|secret|password|token)\s*=\s*['\"]"`.
- Debug artifacts: `fmt.Print|console.log|TODO|FIXME` on added non-test lines.
- gofmt: `git diff <range> --name-only -- '*.go' | xargs gofmt -l` —
  struct-field additions routinely break tag alignment in adjacent lines.
