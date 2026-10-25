# Gate-Tripping Patterns Under Strict Pre-Commit Hooks (shared-tree flavor)

Observed across the meept multiuser tree (2026-08-26): 8 orchestrator
commits through an 11-gate pre-commit hook; 5 commits initially blocked.
These are the trips that REPEAT and their fixes that actually passed.

## 1. Newly-added `_ = expr()` discard sites

Error-handling gates flag newly-added ignored-error sites. Subagent code
produces these constantly. Comment-annotated discards (`_ = encErr //
reason`) STILL BLOCK.

Fixes that passed:
- Best-effort JSON error bodies in HTTP middleware → extract a helper:
  `writeAuthError(w, status, kind, msg)` that checks the encoder error and
  `slog.Debug`s on failure. Same shape as §2's warn-and-continue but
  reusable at N call sites.
- Deliberately non-fatal side-calls ("exchange users, never fail the
  pull") → `if err := call(); err != nil { slog.Warn(...) }` inline.

## 2. Foreign hunks swept into your filtered staged set

A hunk-filtered `git apply --cached` patch of a shared file can carry
sibling lines inside a kept hunk's context — a sibling's `_ =
p.Signal(syscall.SIGTERM)` then reads as "newly added" by YOU and blocks
the commit twice before you notice.

Rule: after building any filtered staged set, read the FULL
`git diff --cached -- <file>` and confirm EVERY `+` line is yours before
committing. Extract foreign hunks OUT — you cannot add nolint comments to
code you don't own. `git restore --staged <path>` is the safe default when
a foreign staged hunk blocks (evicts from index, never touches worktree).

## 3. staticcheck U1000 scans the WORKING TREE, not your staged subset

Two failure directions, both observed:
- Your staged hunk references symbols whose call sites live in an
  UNstaged sibling hunk → compile passes, staticcheck fails elsewhere or
  claims unused code.
- A committed file's callers live ONLY in sibling unstaged/uncommitted
  work → ANY commit touching that package fails U1000 until the sibling
  lands or the callers are restored to the worktree.

No staging trick fixes direction 3 — either restore the missing callers to
the working tree (if you have them from a stash/dangling commit) or wait
for the sibling session to land. Never delete the "unused" symbol: it has
an owner.

## 4. Re-run the gate fresh after ANY staging manipulation

Evicting a file from the index changes what every gate sees. An earlier
red/green result is void after `git restore --staged`, `git apply
--cached`, stash surgery, or a partial re-add. The final green must be
the last thing that happens before `git commit`.

## 5. Dangling merge-stash recovery with plain two-dot diff

If stash surgery goes sideways mid-sequence, a dropped stash survives as a
dangling MERGE commit. Recovery details that matter:
- `git show <stash-sha> -- <path>` emits combined `diff --cc` format which
  `git apply` REJECTS ("corrupt patch").
- Use `git diff <stash>^1 <stash-sha> -- <path>` instead — plain two-dot
  diff of what the stash captured vs its first parent, directly
  re-appliable (with `--3way` for drift tolerance).
- Hunk-filter THAT patch for the lines you need, verify end-state with
  grep-counts of BOTH sessions' marker symbols + full-tree build, then
  re-run the gate fresh (§4).
