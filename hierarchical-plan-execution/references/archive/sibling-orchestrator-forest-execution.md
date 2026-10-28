# Ssibling orchestrator forest execution
When to use: sibling orchestrators on one forest.
Lesson: shared-repo hazard catalog.

# Sibling-Orchestrator Forest Execution (Shared-Repo Hazard)

Scenario: a hierarchical plan forest (multiple tree directories under one
root) is authored in one session, but EXECUTION is split — a parallel
orchestrator session begins dispatching leaf subagents for the same forest
while your session is planning, reviewing, or idle. Observed on meept
(llm-resilience-forest, 2026-09-01/02): by the time execution began, sibling
sessions had landed 16 leaf commits across three of five trees.

## Detection at baseline

Before dispatching ANY leaf, check whether a sibling is already executing:

```bash
git log --oneline -20 | grep -E "tree 0[0-9]"
git status --short   # sibling-dirty files = in-flight leaf
```

The commit-message convention ("feat(scope): ... (tree 0N leaf 0M)") is the
fingerprint. A dirty file from the sibling's current leaf is the in-flight
signal — e.g. client.go/anthropic.go/errors.go all modified plus new test
files matching the leaf's scope.

## Protocol

1. **Supersede, don't duplicate.** Before dispatching a leaf, run the leaf's
   own verification greps against HEAD. If the target work exists, mark the
   leaf SUPERSEDED/COMPLETE in the tracking table with the sibling's commit
   hash and dispatch nothing. A dispatched leaf that arrives to find its work
   committed should verify against spec and report "already implemented" —
   that is correct behavior, not failure (it costs one verification pass, not
   a re-implementation).
2. **Fence dispatch contexts by file.** For each leaf, list the exact files a
   sibling currently holds dirty and forbid them in the leaf's RULES block
   ("Do NOT touch X, Y, Z — a sibling session owns them"). Two leaves editing
   one file concurrently produce conflicts neither session attributes cleanly.
   If two planned leaves must touch the same file, serialize their dispatch
   explicitly in the Child Index notes.
3. **Assign shared-file ownership up front** in dispatch contexts: "components.go
   wiring is leaf A's; leaf B exposes its constructor and the orchestrator
   registers it after A merges." Registration-after-merge was an 8-line
   orchestrator patch vs. a collision-prone concurrent edit.
4. **Verify scoped, not module-wide, during leaf review.** A leaf's
   full-suite gate (`go test ./internal/llm/...`) can fail on an UNTRACKED
   file half-written by the sibling's leaf — an error naming a third party's
   file. Scope verification to the leaf's own files plus its leaf-prescribed
   test command; run the module-wide suite only at commit time, and re-check
   `git log --oneline -3` immediately before staging.
5. **Re-run build + targeted tests immediately before `git commit`,** not
   just before `git add`. Siblings land commits in BURSTS — four tree commits
   landed between one leaf's verification pass and its staging in the
   observed session. The tree you verified is not the tree you stage from.
   Re-check whose hunks are dirty at each commit (a dirty schema.go may hold
   BOTH trees' work before a burst and only yours after).
6. **The stalest tracking doc is the FOREST ROOT.** Per-tree masters get
   updated by whoever executes; nobody owns the root during split execution
   (observed: root listed all five trees PENDING while 16 leaf commits had
   landed). Reconcile the root table from `git log` once scoped suites verify
   green, and commit it even mid-forest.
7. **Reviewer-challenge landed work.** Do not trust either the sibling's
   tracking notes or your subagent's self-report. Run the leaf's own
   verification commands yourself. Real catches from one pass: a schema key
   with zero test coverage, and production wiring (a park-event bus) that the
   landed leaf's docs claimed existed but didn't — the gap-fill was small,
   but the docs had been asserting a false behavior.
8. **In-flight subagents may collide with sibling commits.** A dispatched
   leaf can arrive to find its work committed and either duplicate it (watch
   for clobbered files: one subagent restored a clobbered test file via
   `git checkout --` and reported the incident) or pivot to verify+gap-fill.
   The pivot is the right behavior; say so explicitly in the dispatch context
   ("if the work already exists at HEAD, verify it against the spec instead
   of re-implementing").

## Bookkeeping quirks observed

- Pre-commit hooks that auto-generate docs (aider-style prompts) can sweep
  sibling WIP into YOUR commit. After any commit that passed through a
  question-asking or failed hook, `git show --stat HEAD` and verify the file
  list matches intent.
- Sibling commits can make your intended commit land with extra files; if the
  file list is wrong, `git reset HEAD~1` (no push yet) and re-stage exactly.
- Tracking-table drift direction is one-way: tables lag reality (say PENDING
  while work is COMPLETE). Trust `git log` + verification runs over tables,
  then fix the tables.
