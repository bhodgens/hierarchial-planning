# Pitfall: sibling leaf's git restore reverts a completed leaf's work

(meept skill-evolver tree, 2026-09-01 — three leaves in parallel, one package)

## What happened

Leaf 04 completed green (orchestrator verified its tests passing). Six
minutes later leaf 02, still running, destroyed leaf 04's work: tracked
files it had edited (`verifier.go`, `types.go`, `evolver_test.go`) reverted
to HEAD, its new untracked test file deleted. Leaf 01's concurrent work
survived — its new files were untracked and its tracked diffs were outside
leaf 02's restore scope.

## The survival asymmetry (core lesson)

- **UNTRACKED new files survive** a `git checkout`/`git restore` misfire.
- **TRACKED-file diffs are destroyed.**
A leaf that put all work in brand-new files keeps it; a leaf that edited
existing files loses everything uncommitted.

## Detection

- **mtime clustering**: several tracked files the running agent has no
  business touching share one recent timestamp (bulk revert, not
  incremental work — extends the stall-recovery mtime rule).
- **Symbol grep flip**: `grep -c 'SymbolFromReport' file` returns 0 for a
  symbol the orchestrator verified present minutes earlier.
- Pre-commit analyzers suddenly fail on packages that compiled green.

## Prevention (the actual rule)

1. **COMMIT EACH LEAF the moment its review passes — before dispatching
   the next wave.** "Sequence the commits, not the dispatches" has a
   sharper corollary: a reviewed-green leaf is a commit unit NOW. Every
   additional green-but-uncommitted leaf is hostage to a sibling's git
   operations.
2. If the orchestrator cannot commit immediately — e.g. the pre-commit
   analyzers compile the whole working tree, so a sibling's in-flight RED
   test (test written, `SetTierResolver`-style symbol not yet implemented)
   blocks YOUR commit of green work — that is the signal to wait for the
   sibling's completion notification, then commit in dependency order.
   Never carry multiple green leaves uncommitted across a wave boundary.
3. **Every leaf brief gets an explicit git prohibition**: no
   `git checkout/restore/clean/stash` beyond the leaf's own exact paths.
   A leaf needing a clean slate scopes any restore BY FILE PATH, never
   directory-wide, never `.`.

## Recovery

- The delegation cache (`~/.hermes/cache/delegation/subagent-summary-*.txt`)
  preserves the reverted leaf's full completion report: files touched,
  test names, verbatim test-command tails, deviations. It is a complete
  spec of the lost diff — re-apply from it rather than re-dispatching
  (a re-dispatch fights whatever the still-running sibling is doing).
- Salvage order: (1) protect surviving work first — commit it; (2) re-apply
  the reverted leaf from the cached report, including any deliberate
  fixture-comment style the original used; (3) re-run its gates; (4) only
  then continue the wave.
