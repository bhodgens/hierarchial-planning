# Rrate limit orchestrator completes
When to use: 429s block the orchestrator mid-tree.
Lesson: orchestrator-completes pattern for stalled leaves.

# Rate-limit completions and orchestrator-completes patterns (2026-08-29, wikiskill tree)

Worked additions to the SKILL.md pitfalls. SKILL.md is at its size cap, so new
variants live here.

## 429 AFTER files landed, no report (variant of Pitfall 13c)

A subagent can die on the provider's 429 AFTER writing its files but BEFORE
reporting (real case: meept wikiskill leaf 05 — both background `-race`
verification runs were green, then the entire delegation return value was
"API call failed after 3 retries: HTTP 429: Usage limit reached"). The
subagent's own summary is absent, so the normal review entry point is gone.

Protocol:

1. `git status --porcelain <leaf target paths>` — are the leaf's files on disk?
2. Read the subagent's redirected test logs if it piped output to files
   (watch for its background-process completion notifications; they arrive
   even when the delegation itself died).
3. Files present + tests green ⇒ review in-session (diff, contracts, U1000
   via `staticcheck -checks=U1000 -tags=test ./<pkg>/`) and commit as
   orchestrator. Record in the tracking table that the subagent died on 429
   and the orchestrator completed the review/commit.
4. Do NOT re-dispatch into the exhausted provider — the limit resets on a
   clock; a re-dispatch wastes the whole wait and re-reads context you
   already hold.

Related variants already in SKILL.md: Pitfall 13c (all-429 batch, zero
output) and the memory-note variant (first API call 429'd, zero files).
The distinguishing question is always: did the files land? Zero files →
briefs are the deliverable, implement in-session. Files + green tests →
review and commit directly. Files + failing tests → fix in-session scoped
to the failures.

## Subagent finish order vs orchestrator commit (late formal report)

A subagent whose files were already reviewed + committed can still deliver
its formal report LATER (async notification). Reconcile, don't redo:

- `git diff HEAD -- <its files>` must be EMPTY — if not, the subagent wrote
  after your commit and the diff is a re-review.
- Grep its files for any orchestrator post-fixes (e.g. the WithRawGrammar
  swap) to confirm the committed state survived.
- Its self-reported blockers may already be resolved (leaf 04 flagged a
  sibling-test hang that leaf 01 fixed before its own commit) — verify
  rather than reopen.

## Late reports can also surface NEW content: reconcile, then decide per-file

meept llm-resilience-forest leaf-05 (2026-09-01): the late report said the
subagent "restored pacing_test.go via git checkout" after accidentally
clobbering the committed one, and that it had added a config-test the
committed leaf lacked. Reconciliation protocol:

1. Diff its late-reported file set against HEAD. Restored-via-checkout
   files diff EMPTY — trust but verify with the diff, not the narrative.
2. NEW additions it flagged as gap-fills are real work needing review:
   run the scoped tests (green), check the diff is additive-only, then
   commit as an explicit follow-up commit citing the late report
   (1c790e7b: pacing.target_429_per_hour had zero coverage; late agent's
   default/round-trip/tag-pin tests landed as the follow-up).
3. Honest-incident reports ("I clobbered X and restored it") deserve a
   `git status`/diff check of X specifically — clobber-and-restore is
   exactly the pattern that leaves silent truncation behind.
