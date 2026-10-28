# Shared-Repo Git Discipline for Subagent Workflows

When to use: any subagent workflow that stages, commits, or shares a repo with another agent or concurrent session.
Lesson: stage only your files by explicit path, detect concurrent writers before committing, and when the user authorizes committing a shared tree, verify the whole batch then disclose provenance - the user must never be surprised by what landed.

## Concurrent-writer detection

Signs another agent or session is committing to the same repo:
- `git log --oneline -5` shows commits you did not make, dated during/after your session start.
- `git status --short` lists modified files you never touched.
- A file you deleted as temp cleanup shows tracked-and-deleted (D) because the other agent committed it between your writes.
- A file you expected to be uncommitted is already tracked and clean (the other agent committed it first).

Habit: run `git log --oneline -5` and `git status --short` together at the start of any commit step. If the log has commits you did not make, you are in concurrent-writer mode.

## The rule: never `git add -A` with concurrent writers

Stage ONLY your files by explicit path:

```bash
git add path/to/file1 path/to/file2    # explicit list, nothing else
git diff --cached --stat               # staged set is exactly yours
# build + test the staged state, THEN commit
```

Triage every `git status` entry before staging:
- Modified file you do not recognize: another agent's work - leave it OUT.
- Tracked-and-deleted file you removed as cleanup but another agent committed: ambiguous ownership - leave it out; do not delete another agent's committed file in your commit.
- File you created that is already tracked+clean: the other agent committed it; nothing to stage.

Real instance: after a multi-subagent build, `git status` showed 9 of my files plus an unrelated `repeat_penalty` edit from a concurrent agent and a contested deletion. Explicit-path staging, cached-diff verification, build+tests, commit - the other agent's changes and the ambiguous deletion untouched. `git add -A` would have swept in a half-finished change.

## Exception: user explicitly authorizes committing the tree

Explicit-path staging prevents ACCIDENTALLY sweeping in another agent's work. It does not apply when the user explicitly says "commit" while the tree holds a concurrent agent's changes AND that batch is confirmed complete. Then:

1. Verify the whole batch is coherent first - project build AND analyzer/linter on every changed surface. A concurrent agent may leave the tree mid-edit; in one session the analyzer reported an undefined method the concurrent process finished writing seconds later - re-run the analyzer after a brief wait rather than committing a red tree.
2. Commit, then disclose provenance in your reply: state plainly which changes were not yours this session and that you verified they compile and pass checks; offer `git reset --soft HEAD~N` if the user did not want them yet.
3. Never commit a red build even if the user said "commit" - wait for green or stop and tell the user.

Load-bearing principle: stage-only-yours prevents surprise by exclusion; verify-then-disclose prevents surprise by transparency.

## Related rules living elsewhere

- Canon C1-Commit: only orchestrators commit; subagents are told "Do NOT commit."
- `references/parallel-dispatch-git-discipline.md`: per-sibling brief rules - explicit `git add <paths>` only, `.git/index.lock` retry (sleep 3, 3x), fixed identity via `-c` flags, one file per task where possible.
- `references/delegation-size-limits-and-splits.md`: a FAILED pre-commit gate stages the files it validated - the next commit silently sweeps them in; after any failed commit check `git diff --cached` and amend the message to credit what actually landed.
- `references/domain-pitfalls-go-npm-sim.md`: `git add -A` after a subagent's npm install commits node_modules; create `.gitignore` first.

## Post-subagent verification checklist

The full per-return checklist (stat files, read the summary file, spot-check conventions, run suites, check pre-commit lint, verify UE5 headers by inspection, fix, stage exact paths, one commit per leaf with test counts verbatim) lives in `references/post-subagent-review.md`.
