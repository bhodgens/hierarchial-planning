# Production-Caller Grep — Catching "Isolated Island" Code

> The mandatory post-leaf verification for integration-phase plan trees.
> Catches the single most common failure mode: components built, tested,
> and marked COMPLETE — but never wired into any production code path.

## The Problem

A plan tree for a feature like "add semantic search" produces leaves that
build individual components:

- `internal/search/scorer_semantic.go` — `ScoreSemantic()` method
- `internal/search/intent.go` — `NudgeIntent()` function
- `internal/web/handlers/search_similar.go` — `SimilarJobsAPI` handler
- `internal/search/store_search.go` — `SearchJobs()` store method
- `internal/jobs/embed_job.go` — River worker `EmbedJobArgs`

Each component compiles, has its own tests, and passes review against its
leaf spec. The orchestrator marks each leaf COMPLETE.

**But none of them are ever called from production code.** DashboardPage
still uses the old keyword scorer. The ingest pipeline doesn't enqueue
embed jobs. The similar-jobs route isn't registered. The apply handler
doesn't nudge the intent vector.

`go build ./...` passes. `go test ./...` passes. Pre-commit hooks pass.
The system appears green. The feature doesn't work.

## Why This Happens

1. **Leaf boundaries split build from wire.** The plan's leaf for "dashboard
   wiring" was supposed to call `ScoreSemantic` from `DashboardPage`, but
   the subagent only added the `embSvc` field to the handler struct and
   created the `SimilarJobsAPI` endpoint — it never actually wrote the
   `ScoreSemantic(...)` call inside `DashboardPage`.

2. **`go build ./...` is a false positive.** Go compiles all packages in the
   module, not just those imported by `main`. A new package with zero
   importers compiles cleanly.

3. **`go test ./...` is a false positive.** The package's own tests exercise
   its functions. Tests prove the function works, not that it's called.

4. **Subagent self-report says "all tasks done."** The subagent sees the
   struct field exists, the handler compiles, and reports success. It
   doesn't check whether the handler actually invokes the function.

5. **The orchestrator reviews each leaf against its own spec** — but the
   spec for "add embSvc field to handler" doesn't say "and then use it
   in DashboardPage." The wiring was implied but not explicitly tasked.

## The Fix: Production-Caller Grep

After every integration-phase leaf claims to wire a component into the
application, grep for production callers of the key exported functions:

```bash
# For each new exported function, search for callers OUTSIDE its own
# package and OUTSIDE test files:
grep -rn 'ScoreSemantic' cmd/ internal/web/ | grep -v _test | grep -v scorer_semantic.go
grep -rn 'NudgeIntent' cmd/ internal/web/ | grep -v _test | grep -v intent.go
grep -rn 'SimilarJobsAPI' cmd/ internal/web/ | grep -v _test | grep -v search_similar.go
grep -rn 'SearchJobs\b' cmd/ internal/web/ | grep -v _test | grep -v store_search.go
grep -rn 'EmbedJobArgs' cmd/ internal/web/ | grep -v _test | grep -v embed_job.go
grep -rn 'ComputeResumeEmbedding' cmd/ internal/web/ | grep -v _test | grep -v resume_embedding.go
```

**Zero hits = NOT WIRED = Critical finding.** The function exists but
nobody calls it from production code.

For handlers/endpoints, also check route registration:

```bash
# Is the handler registered in the router?
grep -rn 'SimilarJobsAPI\|SimilarJobsPage\|SearchAPI' cmd/web/main.go
```

For River workers, check enqueue:

```bash
# Is the job ever enqueued?
grep -rn 'EmbedJobArgs\|embed_job' internal/web/ | grep -v _test
```

## When to Run This Check

Run it as the FINAL step before marking a tracking table COMPLETE — after
all leaves are REVIEWED and COMMITTED. Specifically:

1. After every leaf that creates an exported function expected to have
   production callers.
2. After every "integration" or "wiring" leaf (leaf 05, leaf 06, etc.).
3. As part of the root integration review (Step 5) before the final commit.

This is distinct from:
- **Step 3c item 8** (spec-section → impl-file mapping) — catches missing
  scope WITHIN a leaf (a function wasn't implemented).
- **Pitfall 21** (green tests creating false confidence) — catches missing
  algorithms when tests pass.
- **Deferred-integration-wiring reference** — catches parallel leaves where
  Leaf A has stubs for Leaf B's types.

This check catches: **the function exists, the stub doesn't exist, but
nobody wrote the call site that connects them.** That's the gap between
"component implemented" and "feature works."

## Worked Example: JobForge Semantic Search (2026-07-29)

7 components were built, tested, and marked COMPLETE:

| Component | Function | Test status | Production callers |
|-----------|----------|-------------|-------------------|
| scorer_semantic.go | `ScoreSemantic` | ✅ 9/9 tests | **ZERO** — DashboardPage still uses ScoreAgainstKeywords |
| intent.go | `NudgeIntent` | ✅ 10/10 tests | **ZERO** — apply/bad-match handlers don't call it |
| search_similar.go | `SimilarJobsAPI` | handler exists | **ZERO** — route not registered in router |
| store_search.go | `SearchJobs` | store method exists | **ZERO** — no handler calls SearchJobs |
| embed_job.go | `EmbedJobArgs` | worker registered | **ZERO** — never enqueued at ingest |
| resume_embedding.go | `ComputeResumeEmbedding` | ✅ 4/4 tests | **ZERO** — no handler calls it |
| intent.go | `GetOrCreateIntentVector` | ✅ tested | **ZERO** — no handler calls it |

All 7 were caught by the production-caller grep. The orchestrator then
wired all 7 in a single fix wave (7 files, 182 lines). The feature went
from "all green but non-functional" to "actually working" in one commit.
