# Aattribution repair sibling commit sweeps
When to use: sibling swept your files into its commit.
Lesson: detect by content diff never messages; filter-branch msg repair on unpushed commits only.

# Sibling-Session Commit Sweeps: Attribution Verification & Repair

Multiple orchestrator sessions sharing one worktree is normal on this
machine. Consequence: a sibling session's broad `git add`/commit can sweep
YOUR reviewed-but-uncommitted leaf files into ITS commit, under ITS message.
Observed twice in one day (meept, 2026-09-06): five leaf files
(daemonpath/launchd/manager) swept into `feat(daemon): production per-phase
worktree provisioner` (256e620a), and the ServerConfig.InstallHint field into
the same commit — attribution lost, `Closes #32` closure lost.

## Prevention (primary)

- **Commit each leaf immediately after review.** The commit policy
  ("orchestrator commits after review") implicitly assumes one orchestrator;
  with concurrent sessions, a delayed commit is sweep exposure. Treat the
  post-review commit as part of the review step, not a later phase.
- A leaf that finishes while you are blocked on user consent is a parked
  liability — say so explicitly in the status update and re-attempt the
  commit at every user touchpoint.

## Detection (diff, never messages)

- After any sibling commit lands mid-wave, verify your files by CONTENT:
  `git log --all -- <your files>` then `git show <commit> -- <file>`.
- `git diff HEAD --stat` shows residue (files still on disk vs committed).
- A sibling commit message describing only sibling work tells you nothing
  about what else rode along — the worktree-provisioner message mentioned
  none of the five swept files.

## Repair: message-only rewrite (unpushed commits ONLY)

1. **Verify unpushed**: `git merge-base --is-ancestor <sha> <remote>/<branch>
   && echo PUSHED || echo SAFE`. Never rewrite pushed history.
2. **Stash ALL unstaged churn** — filter-branch refuses on any unstaged
   change, and one stash pass is often not enough: tracked-file edits first,
   then binary submodules (`M animation` survives a plain stash; needs its
   own `git stash push -- animation`). Gate: `git status --short |
   grep -v '^??'` must be empty.
3. **Rewrite the message**:
   ```
   git filter-branch -f --msg-filter 'if [ "$GIT_COMMIT" = "<full-sha>" ]; then
   cat <<MSG
   <corrected message, including Closes #N if the sweep swallowed a closure>
   MSG
   else
   cat
   fi' -- <sha>~1..HEAD
   ```
4. **Restore + clean**: `git stash pop`; `git update-ref -d
   refs/original/refs/heads/<branch>`.
5. **Re-verify content** on the new sha (`git show <new> -- <files>`) — the
   rewrite preserves the tree, but verify anyway.

## When NOT to repair

- Pushed commits: never. Content-correct + message-incomplete → leave it.
- Either way, record the REAL hash in the plan tree's tracking table — plan
  documents outlive commit messages, and the table is the audit trail.

## Cross-reference

- `pitfall-sibling-commit-sweep-and-scratch-module.md` covers the sweep
  happening mid-wave (staging/review hygiene). This file covers what to do
  after the sweep swallowed your work: attribution repair.
