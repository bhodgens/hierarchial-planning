# Production Caller Audit: Catching Components That Compile But Are Never Called

> Worked example for `hierarchical-plan-execution` Pitfall 42. The plan
> produced 8 components that compiled, passed all unit tests, passed vet,
> passed pre-commit hooks — and were never called from production code.
> The tracking table was prematurely marked COMPLETE.

## Session

- **Date:** 2026-07-29
- **Project:** jobforge (Go monolith — chi/pgx/River)
- **Plan tree:** `docs/plans/semantic-search/` (5 children: schema, embedding
  pipeline, hybrid scoring, FTS search, dashboard wiring)
- **Failure surface:** 8 components across 4 leaves, all individually correct

## What the standard review (Step 3c items 1-9) found

Every standard review check passed:

| Check | Result |
|-------|--------|
| File existence (36 files) | ✅ |
| Interface contracts (5 contracts, all signatures match) | ✅ |
| Tests (14 packages, all green, ~50 tests) | ✅ |
| Build (`go build ./...`) | ✅ |
| Vet (`go vet ./...`) | ✅ |
| Artifacts (no TODOs, no debug prints) | ✅ |
| Lint (pre-commit hooks: gosec, U1000, error patterns) | ✅ |
| Spec-section → impl-file mapping | ✅ every spec function exists |
| Plan checklist items | ✅ |

The orchestrator marked all 5 children COMPLETE and committed.

## What the production-caller audit caught

A post-completion review with 2 parallel subagents found that the components
were **isolated islands with zero production callers**. The plan's Phase 4
(dashboard wiring) was substantially incomplete despite being marked COMPLETE:

| Component | Exists? | Called from production? |
|-----------|---------|------------------------|
| `ScoreSemantic` method | ✅ 5 breakdown keys | ❌ DashboardPage uses ScoreWithLocation |
| `NudgeIntent` function | ✅ correct formula | ❌ Apply/bad-match handlers don't call it |
| `GetOrCreateIntentVector` | ✅ correct | ❌ Never called from any handler |
| `EmbedJobArgs` worker | ✅ registered in config.go | ❌ Never enqueued at ingest time |
| `SearchJobs` store method | ✅ FTS + semantic rerank | ❌ Dashboard still uses client-side JS |
| `SimilarJobsAPI` handler | ✅ returns JSON | ❌ Route not registered in router |
| `ComputeResumeEmbedding` | ✅ correct | ❌ Zero callers outside tests |
| `loadResumeEmbedding` | ❌ didn't exist | ❌ Was supposed to be created |

**Root cause:** the plan's leaf 05 (dashboard wiring) specified wiring tasks
but the subagent only implemented the handler struct changes + the API
endpoint code — not the actual call sites that connect the scoring layer to
the dashboard. The orchestrator reviewed each leaf in isolation, confirmed
the components compiled and tested, and marked COMPLETE without checking
whether anything actually CALLED the components.

This is distinct from Pitfall 24 (deferred integration between two PARALLEL
leaves that need to be wired together). Here, each leaf's own tasks included
wiring to production callers, but the subagent only implemented the
self-contained parts and skipped the cross-file wiring steps.

## The audit technique

After all standard checks pass, run a **production-caller audit**:

### Step 1 — List every exported function/handler/type the plan produces

```
For each leaf, extract its interface contract — every exported function,
method, type, and constant the leaf was supposed to create:
  ScoreSemantic, NudgeIntent, EmbedJobArgs, SearchJobs, SimilarJobsAPI, ...
```

### Step 2 — Grep for callers OUTSIDE the defining package and tests

```bash
# For each exported function, search for callers:
grep -rn 'ScoreSemantic' internal/web/ cmd/ | grep -v _test | grep -v scorer_semantic.go
grep -rn 'NudgeIntent\|IntentLearnApply\|IntentLearnBadMatch' internal/web/ cmd/ | grep -v _test
grep -rn 'EmbedJobArgs' internal/web/ cmd/ | grep -v _test | grep -v embed_job.go
grep -rn 'SearchJobs' internal/web/ cmd/ | grep -v _test | grep -v store_search.go
grep -rn 'SimilarJobsAPI' cmd/ | grep -v _test
```

### Step 3 — Zero hits = MISSING WIRING (Critical)

If any exported function has zero production callers, the leaf's wiring
tasks were not completed. The component exists but is dead code in the
running application. Mark the leaf NEEDS_FIXES, not COMPLETE.

### Step 4 — Check route registration for API endpoints

```bash
# Every handler method that was supposed to be an API endpoint must have a
# corresponding route registration in the router:
grep -rn 'SimilarJobsAPI\|SearchAPI' cmd/web/main.go
```

If the handler exists but the route doesn't → unreachable dead code.

## Why this is distinct from existing pitfalls

- **Pitfall 21 / leaf-review-missing-scope:** checks whether spec-required
  *implementation files* exist. Here, all files exist — the missing piece is
  *call sites in OTHER files*.
- **Pitfall 24 / deferred-integration-wiring:** covers TWO parallel leaves
  that need to import each other's types. Here, the wiring is from a leaf's
  NEW component to EXISTING production code (dashboard handler, router, etc).
- **Pitfall 33 / functional trace:** covers end-to-end user journeys AFTER
  all leaves land. The production-caller audit is a faster, earlier check
  that can be run per-leaf during review — before committing.

## Speed vs. the functional trace

The functional trace (Pitfall 33) takes 10-15 minutes and requires all leaves
to be landed. The production-caller audit takes 30 seconds per component
(one grep each) and can be run during per-leaf review. Run the audit FIRST
to catch obvious dead code, then run the functional trace after all leaves
land to catch wiring bugs between components.

## The grep script

```bash
#!/bin/bash
# production-caller-audit.sh <package> <function1> [function2 ...]
# Returns 0 if all functions have production callers, 1 if any are uncalled.
PKG="$1"; shift
STATUS=0
for fn in "$@"; do
  HITS=$(grep -rn "$fn" internal/ cmd/ --include='*.go' \
    | grep -v _test.go \
    | grep -v "$(basename $PKG)" \
    | wc -l)
  if [ "$HITS" -eq 0 ]; then
    echo "MISSING CALLERS: $fn (0 production call sites outside $PKG)"
    STATUS=1
  fi
done
exit $STATUS
```
