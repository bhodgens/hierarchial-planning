# Stash-Drop Recovery and Pre-Commit Hook Failure Shortcuts

Session-proven 2026-09-06 (meept, tokscale-ingest tree, Leaf 01 commit). The
anti-pattern: stash-dancing around a pre-commit hook failure in a shared
worktree, then dropping the stash that held the leaf's only copy of the work.
Recovery is ordinary git — do not re-dispatch a recoverable leaf.

## The failure sequence (5 minutes from safe to "work is gone")

1. `git commit` with the leaf's 11 files staged FAILED: the pre-commit
   typed-nil/setter gate builds ALL staged-relevant packages and choked on a
   SIBLING session's in-flight `transcript_fetch_test.go` (syntax error
   mid-edit). Failure was not in our files.
2. Instead of `--no-verify` (already permitted by standing user rule for
   exactly this case), orchestrator stash-danced:
   `git stash push -m "tokscale-leaf01-staged"` to retry on a clean tree.
3. During the stash window the sibling session edited
   `transcript_fetch_test.go` again. `git stash pop` ABORTED ("local changes
   would be overwritten by merge") — stash survived, pop did not apply.
4. Orchestrator then ran `git stash drop` while the leaf's files existed
   ONLY inside that stash commit.

## Recovery (worked, <1 minute)

`git stash drop` prints the dead ref's SHA:

    Dropped refs/stash@{0} (4ab92388d003f859b63bfebdeabb378c9a48d74f)

The stash commit stays reachable until gc. Restore selected paths directly —
the content lands in both index and worktree, exactly as stashed:

    git checkout 4ab92388... -- internal/llm/models.go internal/metrics/store.go <...>

Then: re-run the gates (tests MUST be re-verified — checkout-from-stash is
not verification), commit with explicit pathspecs + `--no-verify`.

If the drop output scrolled away: `git fsck --unreachable | grep commit`,
then `git show <sha> --stat` to identify the right one; same checkout.

## Decision rules

1. **Hook fails on sibling in-flight files → `--no-verify` immediately.**
   Never stash to dodge a hook. The shared worktree churns under you
   mid-dance; the stash window is where sibling edits collide with your pop.
2. **If you must stash in a contended worktree:** pop immediately after the
   retry commit. If pop aborts, RESOLVE FIRST (`git checkout -- <file>` on
   the conflicting sibling churn or commit it), and only drop the stash after
   confirming its content is recovered (`git stash show -p stash@{0} | head`).
3. **Commit retry uses explicit pathspecs** (`git commit <paths> -m ...`),
   never bare `git commit` after a partial add — see
   staged-index-sweep-and-model-recovery.md for the sweep variant this
   prevents.
4. **A dropped stash is normal git, not forensics.** Drop-output SHA +
   `git checkout <sha> -- <paths>` beats re-dispatching a leaf whose subagent
   report said "files touched: ..." — the file list in the report is the
   checkout list.

Related: attribution-repair-sibling-commit-sweeps.md (when the sibling
already COMMITTED your files), subagent-timeout-and-rogue-commit-recovery.md,
staged-index-sweep-and-model-recovery.md.
