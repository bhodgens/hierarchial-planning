# Wave Execution Patterns — Worked Example (`plans-glm/` Waves 1-3)

> Session: 2026-07-19/20, Rebellion game project.
> Task: execute the 12-tree `plans-glm/` forest in dependency-ordered waves,
> dispatching 3 Go-side implementation subagents per wave.
> This doc captures the execution-phase techniques that emerged when moving
> from planning to implementation.

Read alongside SKILL.md:
- Pitfalls 25-28 (subagent timeout, float determinism, pre-commit lint,
  undefined placeholders) — these were all discovered during execution
- Dispatch Protocol §Concurrency Rules

---

## The situation

12 Go-side plan trees, dependency-ordered into 4 waves:

```
Wave 1: gossip + ipc + embed (3 agents)
Wave 2: identity + llm + perception (3 agents)
Wave 3: dialogue + schedule + procgen (3 agents)
Wave 4: save + gamemaster (2 agents)
Wave 5: sandbox (UE5-side, after all Go-side)
```

Concurrency bumped from default 3 to 6 via:
```bash
hermes config set delegation.max_concurrent_children 6
```

## Key patterns

### 1. Dispatch context = inline everything the agent needs

Each `delegate_task` call received a massive `context` parameter containing:
- The full interface contract (Go struct definitions, function signatures)
- The relevant GDD spec excerpts (constants, tables, formulas)
- Existing package names and what they export
- Explicit "Do NOT commit" + file path constraints

**Why:** subagents have zero conversation context. Every value they need
must be in the dispatch payload. Inlining constants and tables prevents
the subagent from spending its limited 600s budget reading files (and
hitting line-number corruption if it uses `read_file`).

**Measurable impact:** dispatches with fully-inlined specs produced
~1,000-1,800 lines of compilable Go before timeout. Dispatches with
"read the spec at..." instructions produced ~300-500 lines before timeout.

### 2. Subagent timeout is the norm for large leaves, not the exception

Every large leaf (~90K+ estimated context) hit the 600s timeout.
The timeout status is NOT a failure — the subagent almost always created
all source files but ran out of time on tests, entry points, or gofmt.

**Recovery pattern (proven 7+ times):**

```
1. find <package> -type f -name "*.go"   → what landed?
2. wc -l <package>/*.go                  → how much?
3. go build ./<package>/...              → does it compile?
4a. If compiles → write missing tests + entry point + gofmt, commit
4b. If compile errors → fix undefined references (often placeholders),
    then write tests, commit
4c. If fundamentally broken → re-dispatch with narrowed scope
```

Average orchestrator completion time after timeout: 3-8 minutes.
Average re-dispatch time if starting from scratch: 10+ minutes (plus
the 600s timeout itself). Always check disk before re-dispatching.

### 3. Compile-check before logic review

When a subagent returns (timeout or otherwise), run `go build` FIRST.
The compiler lists all undefined references, type mismatches, and
syntax errors at once — faster than reading files looking for problems.

Pattern:
```bash
go build ./<package>/... 2>&1 | head -10
```

Common findings:
- `undefined: mathSqrt` (subagent used placeholder instead of `math.Sqrt`)
- `undefined: pkgRand` (subagent referenced a package-level var it never declared)
- `syntax error: unexpected : in argument list` (subagent typo)
- `cannot use X (type A) as type B` (interface mismatch between subagent's
  local types and existing package types)

Fix these mechanically before reviewing logic. Most are 1-line fixes.

### 4. Pre-commit U1000 lint loop

Repos with strict Go linters in pre-commit hooks will block commits on
ANY unused code. This is a multi-round loop:

```
Round 1: git commit → blocked (func X unused)
         → remove func X → go build (compile error: caller of X now broken)
         → remove caller too → go build OK
         → git commit → blocked (func Y unused, called only by X's caller)
         → remove Y → go build OK
         → git commit → SUCCESS
```

**Prevention:** before first commit attempt, run:
```bash
cd sidecar && go vet ./<package>/...
```
Then grep for functions defined but never called. Remove them all in one
pass. Don't rely on `//nolint:U1000` — pre-commit hooks may not honor it.

**CRITICAL: use `patch` to remove functions, NEVER regex/sed.** Using
`execute_code` Python regex or `sed` to remove multi-line Go functions
causes cascading corruption — orphaned function bodies, dangling braces,
removed signatures leaving implementations. In the procgen tree, 5 rounds
of regex removal progressively corrupted `pipeline.go` until it required
a full rewrite. Pattern that works: read the exact lines with `sed -n`,
then `patch` (mode=replace) with the verbatim old_string (full function
from comment through closing `}`) and new_string (empty). Verify `go build`
after EACH removal.

### 5. Test stub interface satisfaction

When a test defines a mock type satisfying an interface, the pre-commit
U1000 linter flags unused interface methods on the mock. Fix by adding a
test that explicitly exercises the method:

```go
func TestMockInterface(t *testing.T) {
    var _ SomeInterface = &mockType{}
    m := &mockType{}
    _ = m.InterfaceMethod() // exercises the method
}
```

### 6. Float determinism checklist for Go leaves

Before committing any Go package that computes scores, rankings, or
weighted picks:

1. Run tests with `-count=10` (not just `-count=1`)
2. Grep for `!=` in sort comparators → replace with epsilon
3. Grep for `range` over maps in accumulation loops → sort keys first

```bash
go test ./<package>/... -short -race -count=10
grep -n '!=.*score\|!=.*Score' <package>/*.go
grep -n 'range.*map' <package>/*.go
```

### 7. gofmt is always needed after subagent work

Subagents rarely produce gofmt-clean code. Always run before committing:

```bash
gofmt -w <package>/
gofmt -l <package>/  # should be empty
```

### 8. Review subagents for pre-implemented trees

When a tree was implemented by a sibling agent (not your dispatch), don't
assume completeness. Dispatch a review subagent that:
- Reads every source file against the plan's checklist
- Runs `go test -short -race`, `go vet`, `gofmt -l`
- Checks for missing functions (the gossip review caught a missing DecayMemory)
- Returns APPROVED / NEEDS_FIXES / BLOCKED with file:line evidence

Fix critical gaps directly as orchestrator (faster than re-dispatching
for small gaps like a missing function).

## Wave-by-wave results

| Wave | Trees | Subagent timeouts | Orchestrator completions | Avg files/tree |
|------|-------|-------------------|--------------------------|----------------|
| 1 | gossip (review) + ipc + embed | 0 + 1 + 0 | review fix + tests+main + tests | 8-19 |
| 2 | identity + llm + perception | 1 + 1 + 1 | fix+tests + tests + 5 impl files | 6-7 |
| 3 | dialogue + schedule + procgen | 1 + 1 + 1 | tests + tests+fixes + stages2-4+tests+lint-fixes | 4-7 |
| 4 | save + gamemaster | 0 + 1 | tests+commit + tests+fixes+commit | 5-9 |

**Final total: all 12 Go-side trees committed.** 18,123 lines of Go across 11
packages + cmd/sim. 211 tests passing with `-short -race`, zero failures.
`go build ./...` clean. The full sidecar is feature-complete; Wave 5 (sandbox,
UE5-side) is the remaining integration work.

**Session-level timing:** Waves 1-4 dispatched over ~8 hours wall-clock with
intervals for user decisions (6-needs cut, perspective pivot, ONNX format,
commitment event). Pure execution time (subagent dispatch + review + commit)
was ~3 hours for 12 trees. The subagent timeout recovery pattern (pitfall 25)
was used 7 times across the session — every large leaf hit 600s, and in all
cases the orchestrator completed the missing tests/entry-points/lint in under
10 minutes.

## Plan-Document Dispatch (Writing Trees via Subagents)

When creating large plan forests (4+ branches), dispatching subagents to
write plan documents (not code) is highly effective but has distinct failure
modes from code dispatch.

### Rate-limit failures are the dominant failure mode for doc dispatch

With 5+ concurrent subagents writing plan documents, expect 2-3 to hit
HTTP 429 before writing any files. Unlike code dispatch (where a timed-out
agent leaves partial work on disk), a rate-limited doc agent produces ZERO
files — the rate limit kills it during the initial read phase.

**Recovery pattern:**
1. Check which branches have files (some may have been written by agents
   that succeeded before the rate limit)
2. Re-dispatch failed branches ONE AT A TIME after the rate-limit window
   clears (wait for running agents to finish first — don't add load)
3. If re-dispatch also fails, write the orchestrator + leaf files directly
   from the master's interface contracts (you have full context loaded)

### Timeout on large branches (10+ files)

Branches with 8-10 leaf documents (e.g., skill synthesis pipeline) will
timeout at 600s. Unlike code timeout (where you check go build), doc timeout
recovery is simpler:

1. `search_files` for all *.md in the branch directory — how many landed?
2. Check each file is non-empty and has the required template sections
3. Write missing files directly — you have the interface contracts from
   the master orchestrator

**Practical sizing:** branches with ≤6 files complete reliably. Branches
with 7+ files may timeout. Split large branches or write the last 1-3 files
directly after timeout.

### Structural completeness check after parallel doc dispatch

After all branches return (some complete, some timed out, some rate-limited),
run a single validation pass:

```python
# For each .md file: check orchestrator has all 6 required sections,
# each leaf has all 4 required sections, zero line-number corruption
required_orch = ["## Dispatch Protocol", "## Interface Contracts",
                 "## Review Checklist", "## Coding Conventions",
                 "## Completion Tracking Table", "## Integration Test Plan"]
required_leaf = ["## Meta", "## Goal", "## Tasks", "## Self-Verification Checklist"]
```

This catches: files written with truncated content, orchestrators missing
sections due to timeout, and line-number corruption from read_file→write_file
cycles in the subagent.

## What NOT to take from this

- **Don't bump concurrency to 6 for small trees.** If you only have 2-3
  independent leaves, the default 3 is fine. The 6-cap helped because
  we also ran a gossip review subagent alongside 3 implementation agents.
- **Don't always complete subagent work yourself.** If the subagent's
  output is fundamentally wrong (wrong architecture, doesn't match the
  contract at all), re-dispatch with clearer context. The "complete
  directly" pattern is for when 80-90% of the work is correct and only
  tests/entry-points/gofmt/lint are missing.
- **Don't skip the post-implementation review.** Even when you wrote the
  code yourself (as orchestrator completing timed-out work), run the full
  verification suite before committing.

## GDScript Bulk System Dispatch (2026-07-29 Rebellion Session)

When dispatching 10+ parallel subagents to create independent GDScript
system files (e.g., game systems: quest, law, crowd, companion, skills,
combat, etc.), the pattern differs from Go-side leaves:

### Differences from Go dispatch

1. **No mutexio / U1000 lint loop.** GDScript has no equivalent of the
   Go pre-commit analyzers. The `go vet` + `staticcheck` lint loop that
   consumed 3-5 rounds per Go tree does not apply. The commit succeeds
   on the first attempt (pre-commit hooks only check the Go sidecar).

2. **Rate limits are the main failure mode.** With 10 concurrent subagents,
   3-4 will hit HTTP 429. Recovery: check disk for partial work (the
   subagent may have written files before the rate limit killed it),
   complete missing files directly as orchestrator. Do NOT re-dispatch
   rate-limited agents immediately — wait or complete directly.

3. **Verification is simpler.** No `go build` step. Check with:
   ```bash
   grep -rc 'print(' rebellion-godot/scripts/systems/*.gd  # should be 0
   grep -rnE 'TODO|FIXME|not_implemented' rebellion-godot/scripts/systems/*.gd
   ```
   Then optionally run GUT tests to verify the scripts load in-project.

4. **Systems are independent — commit per wave.** Group completed files
   and commit immediately. Don't wait for ALL leaves to finish before
   committing — rate-limited agents can take 10+ minutes to time out.

### Results from the Rebellion session

| Metric | Value |
|--------|-------|
| Leaves dispatched | 14 (10 concurrent + 4 sequential) |
| Files from subagents | 9 (wave 1) |
| Files from orchestrator | 6 (wave 2, direct completion) |
| Rate-limit failures | 4 (completed directly) |
| Total lines | 5,729 |
| print() violations | 0 |
| TODO/stub violations | 0 |
| Pre-commit failures | 0 |
| Test files captured from async notifications | 5 suites / 96 test functions |

### Orchestrator-completes-directly pattern

When 40%+ of subagents hit 429 rate limits, the orchestrator can write
the missing system files directly from accumulated session context.
The orchestrator has already read the GDD specs, knows the interface
contracts, and has seen the pattern from successful subagent outputs.

Key: use `write_file` for each file, NOT `execute_code` with Python
f-string concatenation. The `\\t` escape in Python f-strings produces
literal backslash-t characters, not real tabs — causing invisible GDScript
parse errors. This was hit in the session and required a separate fix
pass (`sed -i '' 's/\\t/\t/g'` to replace literal escapes with real tabs).

### Async notification sweep — capturing subagent test files

Each async delegation notification is a mini-commit opportunity. When a
notification arrives (even minutes after the main file was committed),
check for untracked test files and EventBus modifications:

```bash
git diff --stat HEAD          # modified tracked files (event_bus.gd?)
git ls-files --others         # untracked test files?
```

Session results: 5 test suites totaling 96 test functions captured this way:
- test_crowd_system.gd       27 tests (51 asserts)
- test_romance_system.gd     11 tests
- test_skill_system.gd       20 tests
- test_npc_combat_tactics.gd 16 tests (33 asserts)
- test_fatigue_system.gd     22 tests (57 asserts)

### Two-phase mutexio-compliant decode for Go IPC handlers

When adding IPC message handlers to the Go sidecar that unmarshal JSON
payloads and apply state under a mutex lock, the mutexio analyzer flags
any `json.Unmarshal` call inside `mu.Lock()` ... `mu.Unlock()`. The
fix is a two-phase pattern:

```
Phase 1: decode all sub-objects OUTSIDE the mutex (json.Unmarshal calls)
Phase 2: apply decoded data under mutex (no json.Unmarshal here)
```

This applies to any handler that receives overlay/snapshot data and writes
it into simState fields. The mutexio analyzer is correct here — JSON
unmarshal is CPU+allocation work that should not hold a lock.
