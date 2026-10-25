# Pitfall: User pauses the tree mid-flight (denied commit)

Session: meept llm-resilience-forest tree 05-catalog, 2026-09-01. Leaf 01
committed (`dddb364e`); leaf 03 implemented + reviewed + verified green;
the `git add <files> && git commit` call was denied by the user with:

> BLOCKED: User denied this command. The user has NOT consented to this
> action. Do NOT retry this command, do NOT rephrase it, and do NOT attempt
> the same outcome via a different command. Stop the current workflow and
> wait for the user to respond before taking any further destructive or
> irreversible action.

## Why this is a distinct state from a crash

The Resuming section in SKILL.md covers crash/interrupt recovery. A
user-denied action is a DIFFERENT state with different rules:

- The tree is HEALTHY — files on disk are verified, not half-written.
- The pause is DELIBERATE — the user (or a policy layer) wants a checkpoint,
  not a repair.
- The runtime block binds the whole workflow, not just the one command:
  no retry, no semantically-equivalent detour (e.g. `git apply --cached`
  instead of `git add`), no dispatching the NEXT leaf "while we're at it".

## Handback protocol (what to put in the final reply)

1. **State per leaf**: e.g. leaf 01 COMPLETE + commit SHA; leaf 03
   IMPLEMENTED + REVIEWED + VERIFIED but UNCOMMITTED (list exact paths on
   disk, working-tree-dirty, index-clean); later leaves NOT DISPATCHED and
   why (dependency ordering, not neglect).
2. **Banked evidence**: which gates already passed and when (build, targeted
   tests, full package suite, gofmt, vet, analyzers) — a resume should not
   redo review, only re-verify against a possibly-changed HEAD.
3. **The drafted-but-unused commit message**: mention it exists; a resume
   can reuse it after a fresh leak-check.
4. **Remaining step count**: blocked commit → next leaf dispatch → tracking
   table + DECISIONS.md updates → final integration. Lets the user choose
   resume scope ("just commit 03" vs "finish the tree").

## What NOT to do while blocked

- Do NOT update the master.md tracking table for the blocked leaf — its
  status is IMPLEMENTED/REVIEWED, not COMPLETE. Completion happens at the
  commit, per SHARED-CONVENTIONS §6 (only orchestrators commit) and the
  per-leaf commit contract.
- Do NOT stash/reset the leaf's files to "clean up" — they are verified
  work; touching them risks losing it and changes nothing the user asked
  for.
- Do NOT dispatch leaves that would WRITE to the same files (the next leaf
  here, 02-docs, reads the shipped code from 01+03 — it is blocked by
  ordering, and dispatching it would also violate the stop-work rule).

## Resume recipe (when the user consents)

1. Re-check `git log --oneline -3` — sibling sessions commit in bursts;
   verify the leaf's files were not swept into a sibling commit
   (`git status --porcelain <paths>` empty + `git show HEAD:<path> |
   grep <leaf marker>`).
2. Re-run the cheap gates only (`go build ./...` + the leaf's targeted
   test command); skip full review.
3. `git add` the same explicit path list; `git diff --cached --stat` +
   sibling-marker leak check; retry the commit. If the ORIGINAL denial
   reason was never given, ask the user before retrying rather than
   assuming consent transfers.