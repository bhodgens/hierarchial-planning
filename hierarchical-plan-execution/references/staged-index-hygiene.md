# Staged-Index Hygiene — Parallel Sessions Sharing One Repo

Worked example: meept multiuser tree (2026-08-26). Six leaves executed by
delegated subagents while at least one OTHER Hermes session worked the same
checkout (uncommitted drain-timeout work in `internal/daemon/daemon.go`,
memory/fts5 edits, its own commits landing mid-flight).

## What actually happened (all real, all avoidable)

1. **Sibling's pre-staged files swept into my commit.** After
   `git add <my files>`, the index still carried a sibling session's
   pre-staged `internal/memory/*` and `pkg/sqlite/fts5.go`. Committing
   would have shipped their half-done work under my message.
   **Fix used:** inspect `git diff --cached --stat` BEFORE every commit;
   `git reset -q <foreign paths>` then re-add only my file list.

2. **My staged work vanished between two commands.** Between staging leaf-05
   files and committing, the sibling ran a repo-wide `git reset` that
   unstaged them. The commit then failed for "no changes".
   **Fix used:** never assume staging survives; verify + re-add immediately
   before the commit in the SAME terminal invocation:
   `git add A B C && git diff --cached --stat && git commit -m ...`

3. **Shared-file hunk splitting.** `internal/daemon/daemon.go` held BOTH my
   21-line auth-store wiring AND the sibling's uncommitted drain-timeout
   hunks. Committing the file whole either dragged foreign work in or
   tripped gates on their `_ = p.Signal(SIGTERM)` line.
   **Fix used:** generate a per-hunk patch filtered by content keywords,
   `git apply --cached /tmp/mine.patch`, keep foreign hunks unstaged:

   ```python
   # keep only hunks containing my keywords
   out=[]; i=0; lines=diff.splitlines(keepends=True)
   while i<len(lines) and not lines[i].startswith('@@'): out.append(lines[i]); i+=1
   while i<len(lines):
       if lines[i].startswith('@@'):
           hdr=lines[i]; j=i+1; body=[]
           while j<len(lines) and not lines[j].startswith('@@'):
               body.append(lines[j]); j+=1
           if any(k in ''.join(body) for k in MY_KEYWORDS):
               out.append(hdr); out.extend(body)
           i=j
   ```

4. **Stash round-trip destroyed sibling work.** To isolate my hunks I did
   `git stash push -- daemon.go`, patched, then `git stash pop`. The pop
   restored an OLD daemon.go over the sibling's newer working-tree state —
   their RegisterHealthMethods call sites disappeared from disk (the helpers
   were committed elsewhere), leaving committed dead code (U1000
   staticcheck failures). Recovery: stashes survive as dangling
   merge-commits after `stash drop`; find the SHA from the drop output or
   `git fsck`, extract a plain diff with `git diff <sha>^1 <sha> -- path`,
   filter to the wanted hunks, `git apply --3way`.
   **Lesson: on files another session is actively editing, NEVER stash-push
   as an isolation mechanism** — patch-extract + `git apply --cached`
   touches only the index and cannot clobber their working tree.

5. **Gate false-failures from unstaged context.** Pre-commit hooks run
   tools against the WORKING TREE, not the index. My commit of 3 wiring
   lines failed staticcheck U1000 because helper functions were called only
   by the sibling's UNSTAGED hunks. Two-part answer: first realize the
   gate sees worktree state; second, don't "fix" it by importing the
   sibling's hunks into your commit — restore their hunks to the worktree
   (unstaged) so tools see a compilable whole, then stage only yours.

## Rules for orchestrators fanning out into shared repos

1. Enumerate exact file paths per leaf in dispatch contexts ("You own X, Y;
   do NOT touch Z — sibling leaf owns Z").
2. Before EVERY commit: `git diff --cached --stat`; unstage anything not in
   your leaf manifest. Add+verify+commit in ONE command so no window exists
   for a sibling reset.
3. Never `git add .` / `git add -u` in a multi-session repo — enumerate.
4. Shared hot files (daemon main wiring, registry files): expect to split
   hunks. Keep MY_KEYWORDS lists per leaf ready before you need them.
5. If you must undo your own staging on a contended file, use
   `git apply --reverse --cached` on your own extracted patch — never
   stash/reset on paths others may have touched since your read.
6. Stash SHAs are recoverable post-drop (dangling until gc); save the SHA
   the moment any drop output shows, before running further git commands.

## Dispatch-context additions that prevented recurrence

- Name each leaf's owned paths AND forbidden paths explicitly ("do NOT touch
  schema.go RPCTransportConfig — leaf 06 owns it").
- Tell subagents which config fields do not exist yet ("MultiUserConfig is
  being added by another leaf; take Enabled at construction") so they stub
  instead of inventing config schema.
- Tell subagents to IGNORE unrelated mid-session build errors from other
  leaves' half-written files and report in-scope tests only; the parent
  re-runs the full suite before the integration commit.

## Sweep-commit theft by a SIBLING SESSION's own commit (2026-08-27 addendum)

New variant, worse than a swept `git add`: a sibling session committed
`internal/daemon/components.go` while MY leaf's wiring hunks were already
staged/working in that file — `git show <their-sha> --stat` then contained
10 lines of my multiuser wiring under their unrelated message
("fix(daemon): do not block daemon startup on LLM runtime load").
Detection: after ANY sibling commit lands on a file you touched, grep the
sibling's diff for your keywords — `git log -S "YourSymbolName" --oneline`
tells you which commit swallowed what. Response: verify content landed
intact (`git show <sha> -- <file>`), then correct the LEDGER in your own
follow-up commit message ("components.go wiring landed in <sibling-sha>
via shared file; this commit completes the leaf"). Content lost = worse:
re-extract from the dangling-sha recipe above.

Also from the same session: **`git clean -fd` on a shared path needs
explicit user approval** (it deletes untracked files a sibling may own) —
the terminal gate will block it; don't route around the block, name the
scope and ask.

## Benign foreign-carry: your content landed in THEIR commit (2026-08-29)

Inverse outcome of the theft case, and it happens both directions in one
session: (a) a sibling's PRE-STAGED files sat in the shared index and rode
into your `git add` window — `git diff --cached --name-only` shows foreign
paths; `git restore --staged <foreign>` evicts them without touching the
worktree. (b) Your staged files sat in the index when the SIBLING committed —
their commit now contains your complete tree under their message.

Disposition when (b) happens with COMPLETE, intentional content: do NOT
re-commit (duplicate), do NOT amend or revert their commit (shared history,
others build on it). Verify instead:

```bash
git log --oneline -3 -- <your-paths>     # find the carrying SHA
git diff HEAD -- <your-paths>            # empty = fully landed, nothing lost
```

Then record the foreign SHA in your tracking table/ledger
("plan tree landed inside <sibling-sha>") and move on. Only if
`git diff HEAD` shows MISSING content do you re-stage and commit the
remainder yourself. Provenance lives in the ledger, not in rewriting
someone else's commit. Real-world instance: meept 20260829-harness-eval —
the entire 19-file plan tree landed inside sibling commit 63be84ce
("fix(tactical): ..."); verified intact via empty `git diff HEAD`, ledger
note added, no amend.
