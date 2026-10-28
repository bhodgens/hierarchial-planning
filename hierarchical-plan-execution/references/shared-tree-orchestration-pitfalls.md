# Sshared tree orchestration pitfalls
When to use: multi-agent plan execution pitfalls.
Lesson: shared-tree orchestration catalog.

# Shared-Tree Orchestration Pitfalls (multi-agent plan execution)

Lessons from executing a 15-commit plan tree in a repo shared with parallel
agent workstreams. Each item cost real time once; don't pay it twice.

## 1. Operator approval denials are session-bound, not pattern failures

A subagent hitting a terminal-approval prompt that gets denied (twice) must
NOT retry or work around it. When a leaf reports an operator-denial blocker:
- Have the leaf write a report with UNVERIFIED markers per blocked item and
  the reason — that is a valid outcome, not a failure.
- Do NOT auto-re-dispatch. Surface the decision to the user: the denial may
  be them, an automated guard, or a policy signal.
- Salvage value: static findings from already-cloned source often partially
  compensate for blocked runtime checks (see hierarchical-planning
  references/static-contract-extraction.md).

## 2. Stash/checkout dances leave HEAD detached and break everyone

An agent doing a `git stash → render baseline → pop` cycle (or any
checkout dance) in a shared repo leaves HEAD detached at a random commit.
Symptoms seen: the NEXT subagent found HEAD detached mid-edit and its
committed files "missing" from the tree (recovered read-only via
`git show <sha>:<path>` after reflog verification); branch checkout then
aborted on untracked files colliding.

Rules:
- Baselines: `git worktree add /tmp/base-<sha> <sha>` instead. Never stash.
- If you find detached HEAD: `git log --oneline -1 <branch>` to confirm the
  branch pointer is intact, then clear colliding untracked files ONLY after
  diffing them against `git show <sha>:<file>` — keep modified versions if
  they carry reviewed changes.
- Fix agents that need pristine baselines should clone to /tmp, not touch
  the shared checkout.

## 3. Sibling fixes landing mid-review: verify, don't double-fix

When two workstreams audit the same commits concurrently:
- Your reviewer may report findings against HEAD while an uncommitted fix
  for exactly that finding sits in the tree (labels like "audit D3" in
  comments are the tell).
- Do NOT re-fix. Do NOT commit their wave — that wave belongs to its own
  workstream. Verify the COMBINED tree: vet/build per module, tests with
  `-count=1` (Go caches; stale `ok (cached)` hides real state), plus the
  integration-tagged suites if the area has them.
- Record the disposition per finding in your review record, naming which
  workstream fixed what.

## 4. Dispatch-context updates beat plan-document staleness

Plan leaves written before implementation start WILL drift from reality
(main.go already wires half the thing; a dependency landed early; a pinned
decision changed). Every dispatch context should carry a dated
"IMPORTANT UPDATES since the leaf was written" block listing the deltas,
instead of leaving the agent to rediscover them or, worse, trust stale
spec text. Deltas discovered mid-execution get patched into the plan
document so the NEXT dispatch starts current.

## 5. Quiescence before editing shared files

Before hand-editing a file in a shared tree: stat its mtime. If it moved
within the last few minutes, another agent is actively writing — wait for
quiescence (poll until no .go/.ts files in your target areas are newer than
a few minutes) before patching. Editing during a sibling's write window
produces mid-edit states that fail vet and cost a re-read/re-diagnose cycle.

## 6. V4A-style multi-hunk patches on shared files

Multi-hunk patches against a file another agent may have touched fail with
 confusing "N matches" errors. Prefer single unique-context
`replace` edits; re-grep the CURRENT on-disk content between edits.

## 7. Shell cwd drift across tool calls

Terminal cwd persists across calls. A `git add` with relative paths issued
from the wrong module directory fails confusingly (`pathspec did not match`)
or, worse, writes files into a subdirectory (`go-global-runner/docs/...`
instead of `docs/...`). Re-anchor with an absolute `cd` at the start of any
command whose paths matter, and `ls` the target after writing files whose
location matters.
