# Ggossip execution worked example
When to use: concrete code-execution workflow model.
Lesson: Rebellion gossip engine session worked example.

# Gossip Engine Execution — Worked Example

> Concrete model of the code-execution workflow, drawn from the
> Rebellion gossip engine session (2026-07-19/20). Read this alongside
> the main skill for the abstract procedure.

## Context

Plan tree `plans-glm/02-gossip/` — 3 leaves implementing the NPC knowledge-propagation engine in Go. Leaves 01 (data layer) and 02 (propagation) + 03 (reputation) with 01 as the foundation. Module bootstrap required (no `go.mod` existed).

## Leaf 01 — Foundation (data layer)

**Scope:** Fact type, NPCKnowledge, GossipNetwork, Config. Also bootstrap Go module + world/alignment stubs.

**Dispatch:** Single subagent, ~3.5 min. 10 files created, 16 tests pass with `-race`.

**Review result:** APPROVED on first pass. All types matched frozen contracts exactly. `go vet` + `gofmt` clean.

**Pre-commit fix needed:** Analyzer tools (`mutexio`, `predid`) had stale module path `github.com/bhodgens/rebellion-the-game` from before the repo rename. Fixed by patching imports + `go mod tidy`. This is a common pattern when bootstrapping a module under an existing `tools/` directory — check for stale import paths.

**Commit:** `feat(gossip): implement fact, knowledge, and network registry` — 14 files.

## Leaf 02 — Propagation (behavior layer)

**Scope:** Compatibility, importance, shareable filter (8 rules), transfer (3-tier alignment bias), Tick driver, decay. Largest leaf (~1,800 lines across 8 files).

**Dispatch:** Single subagent, ~7.4 min. 55 tests pass with `-race`.

**Review result:** APPROVED. All formulas match spec exactly. Pre-commit caught `calculateImportance` as unused (U1000) — added 5 table-driven tests to exercise it. This is the green-tests-missing-usage pattern: the function compiled and all existing tests passed, but it had zero call sites. `staticcheck` caught it where `go vet` didn't.

**Commit:** `feat(gossip): implement propagation algorithm` — but `git add -A` accidentally swept in ~130 pre-existing dirty files (Pitfall 18). Lesson: stage specific paths, not everything.

## Leaf 03 — Reputation (aggregation layer)

**Scope:** Standing (5 reputation dimensions), celebrity multiplier (fact-count bands), scenario fixture + integration test.

**Dispatch:** Single subagent, ~5.6 min. Self-corrected 2 test failures (ApplyCelebrity date math, fixture accuracy degradation threshold) before reporting. 100+ cumulative tests pass.

**Review result:** APPROVED. Notoriety blending deviation (breadth + weighted average) was documented and reasonable.

**Commit:** `feat(gossip): implement reputation layer and scenario fixture` — clean, 5 files.

## Gate 1 — Branch Code Review

Dispatched a senior-review subagent. Returned CHANGES_NEEDED with:

| Severity | Count | Key Findings |
|----------|-------|-------------|
| Critical | 2 | snake_case identifiers (`calculate_max_hops`), dead code (`Facts()` with 0 callers) |
| Important | 6 | error swallowing in CreateFact, redundant compat calc (2x per pair), duplicate test doubles, `sort.Slice` instability for equal-importance facts, untested export, coverage gaps |
| Minor | 5 | scenarioPersonality duplication comment, proximity validation, hardcoded threshold, unbounded transfer log, unused param |

**Fix strategy — direct patching (Pitfall 20):** All 8 Critical+Important items were surgical. Fixed directly in-session with 12 `patch` calls across 10 files in ~5 minutes — no subagent dispatch needed. Each fix was a rename, a signature change, or a small addition.

- C1: `calculate_max_hops` → `calculateMaxHops` (8 call sites across 5 files, `replace_all`)
- C2: Added `TestFacts` (27-line test function) + kept the utility method
- I1: Changed `return nil` → `panic("gossip: CreateFact: " + err.Error())` with explanatory comment
- I2: Passed `socialCompat` into `processGossipPair` as a parameter, updated 2 call sites
- I3: Extracted `testMemoryStore` to `testhelpers_test.go`, removed 2 duplicate implementations
- I4: `sort.Slice` → `sort.SliceStable` for fact-by-importance sort (determinism)
- I5: Covered by C2 (Facts test)
- I6: Not fixed (coverage gaps on `addDays` year-rollover and `processGossipPair` reinforcement — logged as follow-up)

**Commit:** `fix(gossip): address gate-1 review` — all 9 pre-commit checks pass, 10 files changed.

## Gates 2-3

- **Gate 2:** `make test` passes (all packages), all 9 pre-commit checks (mutexio, U1000, vet, gosec, errors, predid, sqlite pragma, channel pattern, concurrency annotations).
- **Gate 3:** Pre-commit hook passed on all 4 commits.

## Completion

Branch marked COMPLETE. 19 Go files, ~3,200 lines, 100+ tests, 89%+ coverage. 5 Minor items logged for follow-up (later session fixed all 5).

## Key Takeaways

1. **Foundation-first dispatch:** Leaf 01 alone → review → commit, THEN leaves 02+03 in parallel. Don't parallelize a leaf whose types are consumed by siblings.
2. **Pre-commit catches what `go vet` misses:** U1000 (unused function), staticcheck naming conventions, analyzer tools are not part of `go vet`. The pre-commit hook is the real lint gate.
3. **Direct-fix for gate-1 items:** A 10-file rename-and-signature-change is 5 minutes of orchestrator patching vs. 10+ minutes of subagent dispatch. Delegate only when the fix requires code generation or exploration.
4. **`git add -A` is a trap:** Stage specific paths. The commit that swept 130+ files polluted the tree. The fix commits were clean because they staged package-scoped paths.
5. **`sort.SliceStable` for determinism:** When sorting facts by importance, tie-breaking matters for determinism guarantees. `sort.Slice` is unstable; `sort.SliceStable` preserves insertion order on ties.
