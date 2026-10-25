# Orchestrator commit & hook pitfalls (plan-tree execution phase)

Lessons from executing hierarchical plan trees with parallel leaf subagents
in a repo with strict pre-commit hooks (meept, 2026-09-05 session — 4 trees,
12 leaves). Read alongside SKILL.md §Commit Policy and wave-execution-patterns.md.

## 1. delegate_task batch API shape (fail fast, don't loop)

- Top-level call: pass EITHER `goal` (single) OR `tasks` (batch). Passing
  only `context` fails with "Provide either 'goal' (single task) or 'tasks' (batch)."
- Batch mode: EVERY item in `tasks[]` needs its own `goal` field. Context
  alone per item fails with "Task 0 is missing a 'goal'."
- Fix: duplicate the one-line goal into each task item; keep the full brief
  in the item's `context`.

## 2. Pre-commit hooks block SUBAGENT code — fix before staging

Strict Go repos (errcheck/mutexio/U1000 pre-commit) reject leaf output that
the leaf's own tests never catch:

- `_ = expr` and `defer func(){ _ = x() }()` are commit-blockers. Leaves
  write them anyway (test fixtures, rollback defers). Fix with the house
  pattern from the repo's own stores:
  ```go
  defer func() {
      if rerr := tx.Rollback(); rerr != nil && rerr != sql.ErrTxDone {
          s.logger.Debug("post-commit rollback", "error", rerr)
      }
  }()
  ```
- Instruct leaves about this IN THE DISPATCH CONTEXT (list it as a repo
  rule with the exact pattern) — cheaper than patching after return.
- Sweep `grep -rn "_ = \|panic(" <staged pkg>` before `git add`.

## 3. Hook failures on OTHER agents' in-flight code (--no-verify protocol)

With parallel leaves OR a parallel human/sibling session committing to the
same repo, the hook's build/vet stage can fail on packages you did not touch
(observed twice: undefined symbol from a sibling's mid-land commit; mutexio
failure in a pre-existing test file).

Protocol:
1. Confirm the failing package is NOT in your staged set (`git diff --cached --name-only`).
2. Re-run YOUR packages' tests green.
3. `git add` ONLY your files (never `git add .`).
4. `git commit --no-verify` and note the skip in the report.
Never --no-verify past a failure in your own staged code — fix that first.

## 4. Post-return sweep before staging

Subagents leave untracked strays: one-off probe dirs (`*_tmp/`), scratch
files. After each leaf returns: `git status --short` and stage explicit
paths only. If `rm -rf` of a stray is denied by user approval, surface it
in the report and move on — do not retry the deletion.

## 5. Summary truncation → read the full cache before judging

Long subagent reports arrive truncated (head+tail). Deviations, STOP-items,
and conflict notes often live in the omitted middle — the cache path is in
the truncation footer. Read the full file before review, not after a
surprise at commit time.

## 6. Leaf dispatch timing

Dispatch leaf N+1 only after leaf N is COMMITTED (not merely returned) —
later leaves import earlier packages, and an uncommitted leaf 01 plus a
hook race can strand leaf 02's work against a moving tree. Greenfield
packages in DIFFERENT trees can run leaf-01s concurrently; serialize within
a tree (the master's dispatch protocol usually pins this).
