# Ccolocated method decomposition
When to use: decomposing a large method across leaves.
Lesson: implement plus parallelize tests around extracted seams.

# Co-Located Method Decomposition — Implement + Parallelize Tests

> Worked example for Step 2.6 in hierarchical-plan-execution. When multiple
> target methods all live in the same source file, file-ownership partitioning
> (Step 2.5) is impossible — parallel subagents editing one file collide on
> every patch. This variant implements the methods in-session and parallelizes
> the test files instead.

## Session

- **Date:** 2026-07-23
- **Project:** meept Go daemon
- **Plan tree:** `docs/plans/20260723-memorystore-compaction/`
- **Target:** 3 methods in `internal/session/session.go` (NavigateToBranch,
  InsertCompaction, ReparentAfterCompaction) — all returning "not implemented"
  errors, needed for parity with SQLiteStore counterparts.

## The Problem

The plan's `master.md` referenced 3 leaf documents that didn't exist. The
target methods were all in the same file (`session.go`), each replacing a
3-line stub. Standard file-ownership decomposition wouldn't work: dispatching
3 subagents to edit `session.go` in parallel would cause patch-tool collisions
on every commit.

Additionally, the methods were logically independent — none called another,
no shared types between them. This made them safe to implement together but
hard to parallelize across implementer subagents.

## The Solution: 3-Wave Decomposition

### Wave 0 — Orchestrator Implements (in-session)

The orchestrator read:
1. The 3 stub methods (lines 785-913 in session.go)
2. The SQLiteStore counterparts (store_sqlite.go lines 1466, 1774, 1834)
3. The existing MemoryStore patterns (GetMessagePath, ForkSession — for
   mutex/ID-assignment conventions)
4. The existing test patterns (branch_test.go — for helper conventions)

Then implemented all 3 methods directly via `patch`:
- NavigateToBranch: 30 lines (validate session, find target, swap leaf)
- InsertCompaction: 40 lines (marshal CompactionContent, append with seq ID)
- ReparentAfterCompaction: 20 lines (iterate slice, reparent matching children)

Total: ~90 lines. Build verified: `go build ./internal/session/` passed.

### Wave 1 — 5 Parallel Subagents (test files + review)

Each subagent owned ONE non-overlapping **test file**. The dispatch context
included the full method implementation (inlined), key types, how to create
a MemoryStore and add messages, and the exact test cases to write.

| Subagent | File | Tests | Result |
|----------|------|-------|--------|
| 1 | `memorystore_navigate_test.go` | 6 (basic, no-leaf, target-not-found, session-not-found, no-op, concurrent) | ALL PASS |
| 2 | `memorystore_insert_compaction_test.go` | 5 (basic, empty-ids, multiple, session-not-found, round-trip) | ALL PASS |
| 3 | `memorystore_reparent_test.go` | 5 (basic, multiple-children, no-match, empty, path-after) | ALL PASS |
| 4 | `memorystore_compaction_integration_test.go` | 3 (full-cycle, navigate-after, multiple-compactions) | ALL PASS |
| 5 | Code review (parity vs SQLiteStore) | — | APPROVED |

**Key dispatch context structure for test subagents:**

```
FILE TO CREATE: /absolute/path/to/test_file_test.go
Do NOT modify any other file. Only create this one test file.

THE METHOD UNDER TEST (already implemented):
<full method source inlined>

KEY TYPES:
<struct definitions inlined>

HOW TO CREATE A MemoryStore AND ADD MESSAGES:
<code snippet showing NewMemoryStore, Create, SaveMessages>

TESTS TO WRITE:
1. TestName — description of what to verify
2. TestName — ...

RULES:
- Package: `package session`
- Do NOT use read_file on existing files. All context you need is above.
- Do NOT modify any .md plan files.
- Do NOT commit or run git commands.
- After writing, run: go test -run <pattern> -v -race ./internal/session/
- Report results.
```

### Wave 2 — Orchestrator Finalizes

1. **gofmt check:** `gofmt -l` on all 4 test files — 2 needed formatting.
   Fixed with `gofmt -w`.
2. **Full test suite:** `go test -race -count=1 ./internal/session/...` —
   all pass, no regressions.
3. **Full project build:** `go build ./...` — clean.
4. **Commit:** Staged only the 5 files (session.go + 4 test files). Pre-commit
   hook caught an unused helper function (`int64Ptr` in reparent test) —
   removed it, re-committed. All 11 pre-commit gates passed.

## Why This Works Better Than Alternatives

| Approach | Problem |
|----------|---------|
| 1 subagent implements all 3 methods + writes all tests | Too large — would timeout or hit max_iterations. User asked for 5+ subagents. |
| 3 subagents each implement one method in session.go | Patch-tool collisions — all editing the same file concurrently. |
| 3 subagents implement sequentially | Serial — 3x wall-clock time. User asked for parallelism. |
| **Orchestrator implements, 5 subagents test** | **Zero collisions, full parallelism, orchestrator controls code quality.** |

## When to Use This Pattern

Prerequisites (all must hold):
- Multiple target methods in the SAME file
- Methods are logically independent (none calls another)
- The methods are small enough for the orchestrator to implement directly
  (~30-50 lines each, ~100-200 lines total)
- A reference implementation or clear spec exists (SQLiteStore counterpart,
  API documentation, or the orchestrator can derive the logic from the
  existing patterns in the file)

The user explicitly requests parallelism (e.g., "use 5+ subagents") and the
plan structure doesn't naturally decompose by file ownership.

## Metrics

- **Wall time:** ~3 minutes (Wave 0: 2 min, Wave 1: 1 min parallel, Wave 2:
  1 min)
- **Lines implemented:** 90 (3 methods)
- **Lines tested:** 983 (4 test files)
- **Tests:** 19 total, all pass with `-race`
- **Fix cycles:** 0 (pre-commit caught 1 unused function, fixed in-session)
- **Subagent collisions:** 0

## Pitfall: gofmt Before Commit

Subagent-written Go files frequently compile and pass `go vet` but are not
gofmt-clean. In this session, 2 of 4 test files needed `gofmt -w` before the
pre-commit hook would accept them. Always run `gofmt -l` on all
subagent-created `.go` files before staging (see Pitfall 30 in SKILL.md).
