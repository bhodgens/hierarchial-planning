# Branch History Reconciliation — Quick Command Reference

Use these commands to assess whether a feature branch is merged to main and
whether its work covers a plan tree's task list.

## 1. Ancestry check (is the branch merged?)

```bash
# If this returns 0 (exit), the branch IS an ancestor of main = merged.
# If it returns 1, the branch is NOT merged (it is ahead of, or diverged from, main).
git merge-base --is-ancestor <branch> main && echo "MERGED" || echo "NOT MERGED"
```

**Interpretation:**
- `MERGED` → branch is fully in main.
- `NOT MERGED` → branch has unmerged work.

## 2. Commits on the branch but not on main

```bash
git log --oneline main..<branch>
```

- Empty output → merged (no unmerged commits).
- Non-empty → list of unmerged commits. Scan messages for completion signals
  (`PASS`, `DONE`, `complete`, `spike PASS`).

## 3. Commit list on main but not on the branch (reverse ancestry)

```bash
git log --oneline <branch>..main
```

If this is non-empty, main has commits the branch doesn't — the branch is
behind main (may need a rebase before merge).

## 4. Diff stat (Beware LFS rebase artifacts)

```bash
git diff --stat main..<branch>
```

- **Millions of deletions** = almost certainly an LFS rebase artifact
  (`.gitattributes` change). Do NOT treat as real work volume.
- **Hundreds/thousands of lines** = real code changes. Read the file list.

## 5. Per-commit file inventory

```bash
git show <commit> --stat
```

Use this to see exactly which files a specific commit touched, and confirm
it matches the scope claimed in the commit message.

## 6. Cross-reference against plan tree task table

Read the plan tree's `master.md` tracking table. For each unmerged commit,
find which plan task(s) it addresses. Mark tasks COMPLETE if the commit
message + diff covers the full scope.

## 7. Quick one-liner: merged or not?

```bash
git rev-parse --verify <branch> >/dev/null 2>&1 && \
git merge-base --is-ancestor <branch> main 2>/dev/null && \
echo "MERGED" || echo "NOT MERGED"
```
