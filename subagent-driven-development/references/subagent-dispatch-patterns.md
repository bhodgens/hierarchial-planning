# Subagent Dispatch Patterns  -  Multi-Leaf Implementation

When to use: dispatching multiple independent plan-tree leaves as parallel subagents.
Lesson: self-contained briefs (no read_file needed), disjoint file sets even within a package, per-subagent review and commit, and a U1000 dead-code scan.

Dispatch multiple independent plan-tree leaves as parallel subagents. Each subagent is self-contained  -  inline the GDD spec text, interface contracts, and code conventions so it never needs `read_file` (which risks line-number corruption).

## When to Use

- Plan tree master.md shows independent leaves (different packages, different sides of IPC boundary)
- Root master.md concurrency groups tell you what's parallelizable
- Leaves are 40-110K context each

## Dispatch Pattern

### 1. Gather Context Per Leaf

For each leaf, collect in advance:

- **GDD spec text**  -  relevant sections from the design doc (inline, don't tell agent to read_file)
- **Interface contracts**  -  exact Go struct definitions or C++ class signatures from master.md
- **Code conventions**  -  relevant sections of SHARED-CONVENTIONS.md (Go §2, UE5 §4, IPC §3, Numeric §5)
- **Existing code patterns**  -  read a sample file (one existing file in the same package) to show conventions
- **"Do NOT" instructions**  -  include: "Do NOT commit. Do NOT git add. Do NOT use read_file on existing source. Do NOT leave TODO/FIXME/PLACEHOLDER."
- **Test expectations**  -  what tests to run, success criteria

### 2. Dispatch in Parallel

Batch independent leaves into a single `delegate_task(tasks=[...])` call. Independent means:
- Different packages (no file conflicts)
- Different sides of language boundary (Go vs UE5 C++)
- Different layers of the same pipeline (early stages vs late stages)

**Same-package parallel leaves are safe IF each subagent owns a disjoint
file set.** When dispatching N subagents that each create/modify one file
in the same Go package (e.g. three fetcher files under `internal/search/ats/`),
name the forbidden siblings explicitly in each context:
"Sibling subagents are concurrently implementing usajobs.go and arbeitnow.go
 -  do NOT touch those files or ats.go/ats_test.go." This prevents a subagent
from "helpfully" updating a shared dispatcher or test file a sibling also
needs. The parent then merges the disjoint changes and does any shared-file
edits (dispatcher cases, test table rows) itself. Real instance: 3 parallel
fetcher-implementation subagents, each ~60s, zero file collisions, 25/25
tests green on first merge.

### 3. Review Each Subagent

When each returns:

1. **Read the full files**  -  `read_file` with default offset=1 (not offset=N pagination  -  full file view is needed to detect corruption)
2. **Run tests**  -  `go test ./package/... -short -race`
3. **Run pre-commit checks**  -  the project's `make test` / pre-commit hook blocks on U1000, predid, mutexio
4. **Check for stray artifacts**  -  debug prints, TODO, FIXME, PLACEHOLDER, "End of Task" markers
5. **Check shared files**  -  if a subagent modified a file the parent previously read, re-read it before any further edits

### 4. U1000 Dead Code Pattern

Subagents frequently leave unused `var` + `init()` when they change implementation mid-task (e.g. computing a total weight by init() but then using a different function for selection). The pre-commit hook blocks on this. Pattern:

```go
// ❌ Subagent left this:
var unusedVariable float64
func init() { unusedVariable = computeSomething() }

// ✅ Fix: remove the var + init() block entirely
```

### 5. Commit Per Subagent

Commit each subagent's work independently after review passes:

```
git add <exact paths from leaf>
git commit -m "feat(<scope>): implement <leaf> (plans-glm/<tree>/<leaf>)"
```

Do not batch unrelated leaves into one commit  -  independent review/commit keeps blame history clean.

## Timeout & Partial-Work Recovery (proven 2026-08, agent-orange)

Subagents hitting the 600s timeout often die AFTER finishing their file writes
but BEFORE reporting. Recovery protocol:

1. **Inspect before re-dispatching**: `git status --short` + run the test suite.
   One timed-out leaf had written all implementation files and 31 passing new
   tests; only lint nits remained. Re-dispatching from scratch would have lost it.
2. **Continuation dispatch, not fresh restart**: give the next agent the exact
   remaining scope ("tests exist and are correct  -  do not modify them; create
   these missing files") and the verification commands.
3. **Audit partial work for hacks**: an interrupted agent may leave a half-edited
   workaround (real case: an unbound `_FIRST_LOAD_DONE` variable backing a
   "lenient first load" mode invented to satisfy two contradictory tests).
   Prefer the mechanical fix  -  split the contradictory fixture into its own
   file (`source-truth-broken.yaml`) and make the code raise, per spec.
4. **Lint nits are orchestrator-direct fixes** (<10 lines: E501 wraps, import
   sort, B017 blind-except). Fix them yourself; note in the commit message.

## Formatter Containment (Python/uv repos)

**Never let a subagent run repo-wide formatters.** `ruff format .` reformats
markdown code fences inside plans/*.md spec docs (ruff treats fenced python as
formattable). Consequences: spec-doc churn mixed into feature commits.
Rules to put in every Python subagent dispatch:
- "Scope formatting to your files: `uv run ruff format src tests`" (never `.`)
- After merge, check `git diff --stat plans/ docs/`  -  if spec files show churn,
  `git checkout -- plans/ docs/` before committing.

## Docs-Only Plan-Tree Audits

For "audit and fix the whole project" passes over plan-tree/spec documentation
repos (no code), see `references/docs-only-plan-tree-audit-pipeline.md`:
parallel per-section audits → dependency-ordered fixes → SPLIT verifiers.

## Common Pitfalls

- **Stale parent read-state**: If subagent modifies file X and parent had previously read X, re-read X before any patch. The file on disk may differ from what was read.
- **Context overload**: Subagent context should be self-contained but not bloated. ~100-150 lines of inlined spec text + ~50 lines of interface contracts + ~30 lines of conventions is the sweet spot.
- **Go init() dead code**: Always scan for unused `var` + `init()` pairs after Go subagents. The pre-commit U1000 checker catches this, but fix before attempting commit.
- **UE5 C++ clangd errors**: Errors from clangd (CoreMinimal.h not found, UCLASS macro unknown) are expected  -  UE5 uses UBT, not standalone clangd. Do not treat these as compile failures.
