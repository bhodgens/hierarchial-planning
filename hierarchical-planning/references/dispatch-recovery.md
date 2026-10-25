# Dispatch recovery + leaf errata (hierarchical-planning)

Session-proven patterns from the 2026-09-05 meept four-tree execution
(12 leaves, 4 trees, ~30 subagent dispatches in one day).

## 1. Silent non-landing

A dispatched leaf produced no files and no completion notification.

Diagnosis sequence:
1. `ls <target paths>` — did anything land?
2. `process(action='list')` — is anything still running?
3. If nothing landed and nothing runs: re-dispatch with context that
   states "a previous dispatch did not land; restart from zero. Verify
   first that <exact target files> do NOT exist." The explicit
   restart-from-zero framing prevented the second run from assuming
   partial state that wasn't there.

The re-dispatch ran clean. Do not treat one silent non-landing as a
reason to stop dispatching; treat it as a retryable transient.

## 2. Late duplicate run

A re-dispatched leaf's ORIGINAL run completed ~1h later and rewrote the
same files. Worse variant: the original run typo'd the repo path
(`~/git/meet/` instead of `meept`) and wrote its file there.

Handling when the duplicate arrives:
1. `git status` the leaf's files — expect modified (not just untracked).
2. Re-run the leaf's exact test commands yourself; do not trust the
   arrival summary.
3. Read the diff. If the second version is a SUPERSET (adds tests,
   reconciles the same errata, touches no product code), commit it as a
   test-only follow-up commit with an explicit message ("second
   implementation of the leaf's test file... product code unchanged").
   Do not revert — the superset was strictly better (deeper purity
   test).
4. If the duplicate touches product code differently, diff against the
   committed version and reconcile by hand before committing anything.

Prevention note: duplicate runs are a direct cost of re-dispatching a
leaf you believed lost. Accept it; budget for it; verify on arrival.

## 3. Leaf-table errata vs frozen rules

Recurrence: an authoring agent writes a leaf whose test-table CASE
LITERALS contradict the master's frozen rules (three cases in one
leaf-table of 16). The implementer must not silently pick a side.

Protocol that worked:
1. Frozen rules win — always. The rules are the contract; the table is
   an illustration that can be wrong.
2. The implementer reconciles each affected case to the rules and
   states the reconciliation in its report ("Case 4: leaf expected {A,B}
   but rule 1 makes optional consumes create edges; rule-correct {A}").
3. The ORCHESTRATOR records the errata in the tree's OPEN-QUESTIONS.md
   under `## Implementation errata (leaf NN, date)` — one bullet per
   case, rule citation included — in the same commit as the leaf.
4. Authoring-side prevention: a leaf-table case that required hand
   reasoning beyond restating a rule is a signal the authoring agent
   invented the expectation rather than derived it. Contract-verification
   digests (see Review Protocol) catch this class pre-dispatch; errata
   handling is the post-dispatch backstop.

## 4. Shared-repo commit interplay (pre-commit hooks)

When many trees execute in one shared repo with a strict pre-commit
hook suite:
- The hook builds/vets STAGED packages plus, in practice, transitive
  packages. A parallel session's in-flight edit can fail YOUR commit
  (`undefined: pdfReadResult` from an uncommitted sibling file). Verify
  the failure is not in your files: `git stash list` no, `git status`,
  `go build <your packages>`, `go test <your packages>`. If clean and
  the failure is in their file, commit YOUR staged files with
  `--no-verify` after re-verification, and say so in the report.
- The hook also has commit-BLOCKING lint classes (ignored errors
  `_ =`, new `panic(err)`). Leaf agents will produce `_ =
  tx.Rollback()` despite instructions. Orchestrator-side fix pattern:
  deferred rollback after commit -> check `rerr != sql.ErrTxDone`, log
  otherwise (house pattern: internal/agent/park_store_sqlite.go);
  close-on-error-path -> capture and fold into the returned error.
- Reserve a section in every dispatch context: "if the pre-commit hook
  fails on a package you did not touch, re-run your tests, stage ONLY
  your files, commit with --no-verify, and report it."
