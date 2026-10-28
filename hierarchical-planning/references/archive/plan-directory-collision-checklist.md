# Plan-directory collision: prior COMPLETE tree in the same directory


When to use: authoring into a plans dir holding a prior COMPLETE tree.
Lesson: detect and relocate first - a new master clobbers the old execution record.
## The failure

Authoring a new tree's `master.md` into `docs/plans/<name>/master.md`
when that directory already holds a COMPLETE tree from an earlier
session (its own master + leaves + completion report). Consequences:

1. The new master clobbers the old orchestrator doc (its leaf table,
   dispatch protocol, completion tracking) — the completed tree's
   execution record is erased from HEAD.
2. The write-tool's sibling-modified warning fires (if the file was
   previously read) but by then the content is already composed for
   the wrong path.
3. Git history gets two unrelated "master.md" lineages in one file,
   and `git log -- docs/plans/<name>/` shows interleaved unrelated
   work.

## Worked case (2026-09-10, classifier-outcome-loop)

The classifier-outcome-loop tree (4 leaves implementing the
outcome-metrics design from `classifier-observability/design.md`) was
initially authored into `docs/plans/classifier-observability/master.md`
— which held the EARLIER, COMPLETE classifier-observability tree
(provenance / fail-fast / digest-cwd, commits cb8031f3, 903644f0,
6f199716). Caught by the write-tool warning, reverted via `git checkout
-- <path>`, and relocated to `docs/plans/classifier-outcome-loop/`.

## Checklist before writing a new tree

1. `ls docs/plans/<name>/ 2>/dev/null` — does the directory exist with
   master.md + leaves?
2. `git log --oneline -3 -- docs/plans/<name>/` — any COMPLETE/
   completion-report commits?
3. If the new tree consumes a prior tree's design doc: keep the design
   doc where it is, put the NEW tree in its own directory, and
   cross-reference ("implements design.md committed <sha>") in the
   master's Notes section.
4. Never relocate or rename the prior tree's files — its completion
   report and commits reference those paths.

## Naming pattern that works

Prior tree: `classifier-observability/` (provenance/fail-fast/digest).
Follow-on implementing its design: `classifier-outcome-loop/`.
Related but distinct trees get distinct directories with a
cross-reference line, not shared directories.
