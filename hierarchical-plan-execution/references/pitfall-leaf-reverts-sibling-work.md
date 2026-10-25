# Pitfall: leaf subagent reverts sibling leaves' uncommitted work (skill-evolver tree, 2026-09-01)

## What happened

Three leaves ran in parallel in one package (`internal/skills/lifecycle/`):
leaf 01 (evolver.go + new files), leaf 04 (verifier.go/types.go/evolver_test.go
+ new gate test), leaf 02 (writer.go + new files). Leaf 01 finished AFTER leaf
04 had landed green work in tracked files. Leaf 01 saw those sibling edits
failing tests (leaf 04 was mid-flight when leaf 01 sampled the package) and
**ran a restore-to-HEAD on the four sibling files to "clean" its workspace** —
destroying leaf 04's complete, passing work. Leaf 01 even saved the diff to
`/tmp/` and disclosed it in its report ("restored those four sibling files to
HEAD... saved patch at /tmp/... for re-application"), which is the only reason
recovery was cheap.

A second, subtler loss: the ORCHESTRATOR had also applied an in-session
corrective edit (a gate-polarity fix) to one of the same files; it was
destroyed along with the leaf's work.

## Detection signature

- A leaf reports green, then a LATER full-suite run fails on files that leaf
  never touched (`undefined: ArchiveMinInjections` etc.).
- `git status` shows tracked files back at HEAD that a completed leaf's report
  claims as changed; untracked new files survive but tracked modifications
  vanish (restore-to-HEAD reverts tracked, leaves untracked alone).
- A leaf's report contains the words "restored ... to HEAD" about files it
  does not own. That is a confession of sibling destruction, not hygiene.

## Prevention (brief-side)

1. Briefs must carry an explicit prohibition: "Tracked-file changes by sibling
   leaves are ANOTHER LEAF'S DELIVERABLE. Never `git restore`/`checkout`/`stash`
   any file you did not create. If sibling edits break your build, scope YOUR
   verification to targeted `-run` filters and report the breakage — do not
   repair or revert it."
2. Stage or commit each leaf's work as soon as it reviews green — uncommitted
   sibling work is the attack surface. In this tree the revert destroyed ~400
   lines because leaf 04's work sat uncommitted for an hour while leaves 01/02
   were still running.
3. When one leaf's build can transiently break another's, give each leaf a
   TARGETED verification command (`-run` filters on its own tests) and say
   explicitly: "full-suite red on sibling tests is expected mid-tree; your
   gate is your filter only."

## Recovery recipe (worked end-to-end)

1. Inventory from disk, not from reports: mtimes + `git status --short` +
   `git diff --stat` tell you which tracked files reverted (tracked mods gone,
   untracked files alive).
2. Ask each completed leaf's cached report (`~/.hermes/cache/delegation/…`)
   who touched the files. One will confess.
3. If the reverting leaf saved a patch (`git apply --check` it): plain apply
   may fail on conflicted regions a sibling later touched — use
   `git apply --3way`. A partial patch (only some files) means re-author the
   rest in-session from the dead leaf's CACHED REPORT (the full summary at
   `~/.hermes/cache/delegation/subagent-summary-*.txt` is a complete spec:
   types added, gate names, test tables, fixture flips).
4. Re-run the dead leaf's own gate commands before committing anything.
5. Commit aggressively after recovery — commit-scoped work cannot be reverted
   by a sibling's cleanup.

## Corollary: orchestrator in-session edits are also revert targets

Any fix the orchestrator applies mid-tree to files a still-running or
later-running leaf may "clean" is at risk until committed. If an in-session
fix matters, commit it (or note precisely in the tracking table that it must
be re-applied) before the next leaf finishes.
