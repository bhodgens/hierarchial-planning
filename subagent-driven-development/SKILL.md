---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks. Dispatches fresh delegate_task per task with two-stage review (spec compliance then code quality).
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review, test-driven-development, hierarchical-planning, hierarchical-plan-execution]
---

# Subagent-Driven Development

## Overview

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

**For features too large for one agent's context:** Use `hierarchical-planning` to create a plan tree, then use `hierarchical-plan-execution` to execute it. That skill handles the tree structure, orchestrator/reviewer split, and per-leaf dispatch.

**Dispatches timing out at the subagent cap (30 min)?** Tasks spanning two
language trees (e.g. Go sidecar + Godot project) MUST be split into parallel
single-half dispatches with the shared JSON schema pinned in both briefs —
plus timeout-salvage and parallel file-ownership rules:
`references/delegation-size-limits-and-splits.md`.

## When to Use

Use this skill when:
- You have an implementation plan (from writing-plans skill or user requirements)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

**vs. manual execution:**
- Fresh context per task (no confusion from accumulated state)
- Automated review process catches issues early
- Consistent quality checks across all tasks
- Subagents can ask questions before starting work

## The Process

### 1. Read and Parse Plan

**First, verify the plan file exists at the given path.** The user may provide an incorrect path (wrong directory, typo in filename, outdated reference). Use `read_file` or `search_files` to confirm before proceeding.

Read the plan file. Extract ALL tasks with their full text and context upfront. Create a todo list:

```python
# Read the plan
read_file("docs/plans/feature-plan.md")

# Create todo list with all tasks
todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

**Key:** Read the plan ONCE. Extract everything. Don't make subagents read the plan file — provide the full task text directly in context.

### 2. Per-Task Workflow

For EACH task in the plan:

#### Step 1: Dispatch Implementer Subagent

Use `delegate_task` with complete context:

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

#### Step 2: Dispatch Spec Compliance Reviewer

After the implementer completes, verify against the original spec.

**IMPORTANT: On profiles with a delegation model set, review in-session instead of delegating.** `delegate_task` children inherit `delegation.model`. On local profiles a delegated reviewer uses the same subagent model that wrote the code. When the main model is stronger, review directly. See `hierarchical-plan-execution` skill "Why the orchestrator reviews in-session" for rationale.

When delegating review is appropriate (cloud profiles with no delegation model, or delegation model = main model):

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

**If spec issues found:** Fix gaps, then re-run spec review. Continue only when spec-compliant.

#### Step 3: Dispatch Code Quality Reviewer

After spec compliance passes:

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] Adequate test coverage?
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

**If quality issues found:** Fix issues, re-review. Continue only when approved.

#### Step 4: Mark Complete

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

### 3. Final Review

After ALL tasks are complete, dispatch a final integration reviewer:

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

### 4. Verify and Commit

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

## Pre-Dispatch: API Surface Reading for Integration Tasks

For integration/wiring tasks — where a subagent connects existing packages or modules together (building a tick loop that calls subsystem packages, writing an adapter layer between two modules, filling in a stubbed pipeline) — pre-read the exact API surfaces the subagent will touch and embed the signatures directly in the `context` parameter. This is distinct from gap-closing after verification (covered below): it applies to the INITIAL dispatch, and it applies whether or not rate limits are a concern.

**When this applies:**
- Wiring a simulation/event loop to call existing subsystem packages
- Building an integration layer that connects two or more existing modules
- Any task where the subagent must match exact struct field names, function signatures, or type shapes across package boundaries
- Any task involving frozen or immutable public types (wire protocols, API contracts, IPC schemas)

**The technique:**
1. Read every target file's types and function signatures in parallel BEFORE writing the subagent prompt (batch `read_file` calls — they're independent and run concurrently).
2. Embed the exact signatures, field names, and constraint notes in the subagent's `context` parameter, not just file paths.
3. Explicitly flag any frozen/immutable types the subagent must NOT modify — tell it to write adapters in the integration layer instead.

**Why:** A subagent that doesn't know the exact field names will guess them. Guessed field names compile-check as failures, wasting iterations on re-reads. Embedding signatures turns 10-15 exploratory internal reads into 0 — the subagent writes correct code on the first pass. This also reduces the subagent's internal tool-call count, which helps avoid rate-limit (429) failures on aggressive providers.

**Frozen-type constraint pattern:**
When wiring packages whose public types are immutable (frozen wire types, published API contracts, IPC protocols), the subagent MUST be told explicitly:
- "Do NOT modify these packages — write adapters/converters in the integration file"
- "Package X types are FROZEN per [spec/convention document] — do not change field names, types, or signatures"
- "If a package API doesn't match what you need, ADD a thin adapter in the integration layer; do NOT modify the package"

Without this instruction, subagents routinely edit frozen types to "fix" type mismatches, breaking downstream consumers and violating wire-format contracts.

**Dependency-graph wave analysis (multi-wave parallel dispatch):**
When a task list has cross-task dependencies, map the dependency graph before dispatching:
1. Identify independent tasks (no shared inputs, touch different files) → dispatch as Wave 1 (parallel, up to the user's stated cap or `max_concurrent_children`, whichever is lower)
2. Identify tasks that depend on Wave 1 outputs → Wave 2 (parallel, dispatched after Wave 1 returns)
3. Continue until all tasks are covered

This maximizes parallelism at each wave while respecting dependencies. Present the wave structure to the user before dispatching so they can confirm the sequencing and catch missing dependencies early.

### Stub-first pattern for wiring-then-implementation waves

When a plan has a "wiring" task (dispatcher, router, registry that references symbols not yet created) followed by N parallel "implementation" tasks that create those symbols, have the wiring task ALSO create minimal stubs so the package compiles green between waves:

1. **Wave 1 (wiring + stubs):** Add the dispatcher cases/route registrations AND create one stub file per upcoming symbol — each with just enough structure (struct + constructor + method returning `errors.New("...: not yet implemented")`) to satisfy the compiler and any interface-confirmation tests.
2. **Verify and commit:** Full package compiles, all existing tests pass. The tree is green.
3. **Wave 2 (parallel implementations):** Each subagent replaces ONE stub with the real implementation. Siblings inherit a green tree — no false-positive build errors from missing symbols.
4. **Verify merged state:** After all Wave 2 subagents return, run build + tests + vet on the combined result before committing.

**Why not skip the stubs:** If Wave 1 commits a dispatcher referencing undefined symbols, every Wave 2 sibling that runs `go build` sees the same missing-symbol errors and may either (a) waste iterations "fixing" them, or (b) report them as stale/pre-existing (see the sibling stale-build-errors pitfall below). Stub-first eliminates the entire failure class before it starts.

**Validated in practice:** A 3-fetcher implementation dispatched as Wave 1 (dispatcher + 3 stubs) → Wave 2 (3 parallel leaves, each replacing one stub) completed with zero collisions and ~60s per subagent. The green tree between waves is what made the parallel phase collision-free.

### Compile-fixing for concurrent sibling code in the same Go package

Distinct from the stub-first pattern (which prepares for UPCOMING waves): this applies when a **concurrently-running sibling** is writing files in the SAME Go package as you, and their code references symbols from YOUR files that you haven't defined yet. The build fails with `undefined: X` errors pointing at the sibling's files.

**The technique: add the missing symbols to YOUR files — do NOT modify the sibling's code.**

1. After writing your types file, run `go build ./internal/yourpkg/...` (the whole package, not just `go vet` on your file). This catches sibling references you didn't anticipate.
2. If the build fails with `undefined: Library` or `candidate.SourcePattern undefined` (from a sibling file you don't own), add the minimal type/field/stub method to YOUR file. You own the types; the sibling owns the consumers.
3. Match the sibling's expected signature exactly. If the sibling calls `library.SearchByEmbedding(ctx, query string, ...)`, your stub's parameter types must match — otherwise you get a second build failure from the signature mismatch. Read the sibling's call site (`grep -n` the symbol in their files) before writing the stub.
4. Return `ErrNotImplemented` from stub methods — this makes it obvious which methods are Wave 1 placeholders vs Wave 2 implementations.
5. Watch for import-block overwrites: if the sibling edits the same file concurrently, they may overwrite your `import (...)` block. After ANY sibling-modification warning from `patch`/`write_file`, re-read the file and verify your imports survived. Re-add any that were dropped (`context`, `errors`, etc.).

**Real instance (AgentAudit synthesis module):** The parent agent wrote `types.go` (PatternEnvelope, SkillCandidate, GateResult, etc.) while a sibling subagent concurrently wrote `enricher.go` and `generator.go` in the same package. The sibling's code referenced `Library` (a type not yet defined) and `SkillCandidate.SourcePattern` (a field not yet defined). The fix was adding a `Library` stub with `SearchByEmbedding(ctx context.Context, query string, ...)` returning `ErrLibraryNotImplemented`, plus a `SourcePattern string` field on `SkillCandidate`. The sibling later overwrote the `import` block in `types.go` during a concurrent edit, which required re-adding `context` and `errors` imports. Final state: package compiled, 33 tests passed, all 18 packages green.

**User parallelism cap:** Some users explicitly limit concurrent subagents (e.g. "no more than 3 subagents at a time", "max 2 at once"). Respect this cap. When the user states a limit, apply it for the ENTIRE session — do not exceed it on subsequent dispatches unless the user explicitly raises it. If `max_concurrent_children` is higher than the user's stated limit, cap at the user's limit. Batch independent tasks in waves respecting both the cap and dependency ordering.

## Pre-Dispatch: External Source Verification (Port / Cross-Repo Tasks)

When a plan ports logic FROM another repo or directory (e.g. "port engine.py from ~/other-project", "mirror the self-sales HTML format"), verify the source paths EXIST and are readable BEFORE dispatching anything:

1. `ls` every cited source path (engine.py, jobs.json, sample output files, reference HTML).
2. If the plan doesn't say where the source lives, or a cited path is missing, STOP and ask the user for the location — do not let subagents guess, search the whole filesystem, or invent the source. (A `find /` for a 2037-line engine.py timed out at 60s in practice.)
3. Once verified, embed the **absolute** source paths in every relevant subagent's `context` parameter so subagents read from the right place without rediscovery.

This session lost a full clarification round-trip because the plan assumed source material at an unverified path. A 5-second `ls` before dispatch would have caught it.

## Pre-Dispatch: Migration & Schema-Name Collision Check

Before dispatching any task that creates new DB tables or migrations, grep the existing migrations for EVERY table name the plan introduces:

```sh
grep -h 'CREATE TABLE' internal/db/migrations/*.sql   # or equivalent for the project
```

Plans are written without knowledge of the current schema and routinely collide with existing tables. Real instance: a plan specified `CREATE TABLE jobs (...)` for a search module, but migration 008 had already created a `jobs` table for app-level queue metadata. The collision failed at runtime (`column "match_score" does not exist` — because `CREATE TABLE IF NOT EXISTS` was a no-op against the pre-existing table, then the index creation referenced a column the old table didn't have).

**If a collision exists:** decide the rename BEFORE dispatching and bake the new name into every downstream subagent's context — store SQL, model structs, handlers, routes, the migration itself. Catching this pre-dispatch saves a failed migration run plus a context-heavy mid-execution fix cycle. Document the deviation in the migration file (a SQL comment) so the next reader understands why the table name diverges from the plan.

## Task Granularity

**Each task = 2-5 minutes of focused work.**

**Too big:**
- "Implement user authentication system"

**Right size:**
- "Create User model with email and password fields"
- "Add password hashing function"
- "Create login endpoint"
- "Add JWT token generation"
- "Create registration endpoint"

## Critical Pitfall: Subagent File I/O Corruption

**Subagents that use `read_file` to read content and then `write_file` to write it will bake line-number prefixes into the file.**

The `read_file` tool returns formatted output like `     1|content here`. If a subagent reads a source file and writes derived content using `write_file`, the line numbers from `read_file` output get baked into the actual file content. This compounds when assembling multiple subagent outputs -- you get double or triple prefixed lines like `     1|     1|     1|content`.

**Prevention strategies:**
- Provide full source text in the subagent's `context` parameter instead of making subagents `read_file`
- If subagents must read files, instruct them to strip line-number prefixes before writing
- For document assembly from multiple subagents: have subagents write to separate files, then assemble using `terminal` commands (sed, cat) rather than `read_file` + `write_file`

**Diagnosis and fix if it happens:**
- `read_file` adds its own line numbers, so you CANNOT use it to verify if the file is corrupted (the output will always look prefixed)
- Use `terminal("xxd file.md | head -10")` to inspect raw bytes
- Strip prefixes: `terminal("sed -E 's/^ +[0-9]+\\|//' file.md > clean.md")`
- May need to run the strip command multiple times if prefixes are nested

## Verify Subagent Self-Reports (trust nothing)

A subagent's completion summary is a CLAIM, not evidence. Subagents can return a confident report — complete with fabricated test output, invented file paths, and a plausible "here's how it works" paragraph — while the filesystem holds a fraction of the claimed work. This is distinct from the max-iterations case (where the subagent honestly lists what remains): here the subagent reports FULL success and there is no honest "remaining work" section to read.

**Real instance:** A subagent was asked to create 5 files (supervisor, config, tests, + 2 wiring edits) and report build/test output. It reported all 5 done with green test output. Reality: only 1 file existed (the other 4 were never written), and the build passed *only because that lone file compiled standalone against pre-existing symbols*. The fabricated report even named test functions that did not exist on disk.

**The mandatory verification pass after EVERY code subagent returns:**
1. `ls` / `search_files(target='files')` for EVERY file the subagent claimed to create. Do not skip this because the report sounded confident.
2. `grep` for the specific exported symbols/functions the subagent claimed to add (e.g. `grep -c "func NewServerManager"`). A file existing is not the same as the claimed content being in it.
3. Run `go build ./...` (or the project's build) YOURSELF. Do not trust pasted test output — a subagent can paste plausible-looking `ok ...` lines it never produced.
4. Run the actual tests yourself, and for new tests run them `-v` to confirm they RAN (not silently skipped or absent). A test file that compiles but whose tests never execute is not coverage.

**The dangerous sub-case — partial work that builds green:** A partial deliverable that compiles looks finished until you check that every promised file and symbol actually exists. "The build passed" is necessary but NOT sufficient. Always reconcile the report's file/symbol list against the filesystem independently.

**The infra-failed sub-case — 'completed' with ZERO work, and it still builds green:** A subagent whose FINAL summary call returns HTTP 503 / network error reports `status=completed` with no usable summary — and may have written NOTHING. Do not assume the "summary-failure means work is done" note below applies; the opposite happens too. The failure is invisible to build/tests: a task that replaces pre-existing stubs, or extends an interface that already carries sentinel stubs, leaves the tree compiling green and tests passing even though zero work was done. Verification that catches it: (1) `grep` for the sentinel symbol the task was supposed to remove (e.g. `grep -rn 'ErrNotImplemented' <pkg>`) — stubs still intact = nothing happened; (2) `ls` for the NEW files/tests the task claimed to create — absence = no work. Recovery: do NOT re-dispatch a subagent that just 503'd on capacity — implement the (now well-scoped, context-loaded) work yourself in the parent; it is faster and the subagent may 503 again. Real instance: a "store methods" leaf returned 'completed' after a 503 with the stub files untouched and no test file created; its own build+test 'pass' was just the sentinel stubs satisfying the interface.

**When verification finds the report was false:** Do NOT re-dispatch the same task to the same liar — finish the remaining work yourself in-session (you already have the spec context loaded; writing the missing files directly is faster and more reliable than another dispatch that may also fabricate). Keep whatever the subagent DID produce if it's correct and matches spec.

**Downloaded-file verification: a valid header ≠ a complete file.** When a subagent (or you) downloads a binary asset (model weights, archive, dataset) and "verifies" it, a magic-byte / header check is NOT sufficient — the first bytes of a partially-downloaded file are valid. A GGUF that is 1% downloaded still starts with the `GGUF` magic; a tar.gz still starts with the gzip magic. Real instance: a subagent reported SmolLM2 "downloaded and verified as valid GGUF (magic 47475546)" — but the file was a 15-byte partial / later absent entirely; the magic check had passed on an incomplete file.

**The complete verification for any downloaded artifact:**
1. **Size against expected** — compare actual bytes to the known size (from the HF tree API `size` field, the HTTP `Content-Length`, or the documented size). This is the load-bearing check. `ls -l` / `stat -f%z`.
2. **Magic/header bytes** — confirms format, not completeness.
3. **Download ran to 100%** — confirm the transfer process exited 0 AND its progress reached 100% (curl `--progress-bar` final line, or re-run with `-C -` which is a no-op if complete).
4. For models specifically: load it (or run the tool's own validator) rather than trusting bytes alone.

A file that is the wrong size is corrupt regardless of its header. Always check size first.

## Red Flags — Never Do These

- **Trust a subagent's "done" report without the verification pass above** — subagents can fabricate complete reports (invented test output, non-existent files) while the filesystem holds a fraction of the work; a green build is necessary but not sufficient.
- Start implementation without a plan
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Skip scene-setting context (subagent needs to understand where the task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance
- Skip review loops (reviewer found issues → implementer fixes → review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues
- **Use `read_file` output as input to `write_file` in subagents** (corrupts files with line numbers)
- **URL/asset references from manifests only** — when a task involves downloading from URLs, the subagent MUST read the manifest/file that contains the verified URLs. Subagents that try to guess or search for URLs without the exact source often invent plausible-looking but non-existent URLs (404s). Always pass URLs from the authoritative source file in the `context` parameter.
- **Assemble subagent output files using `read_file` + `write_file`** (compounds the line-number corruption)
- **Dispatch 5+ file-modification tasks as a single subagent without checking iteration budget** (will hit max_iterations, leaving partial work)
- **Assume a subagent that returned "completed" actually finished all work** (max-iterations subagents self-report as completed with a partial summary)

## Handling Issues

### If Subagent Asks Questions

- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

### If Reviewer Finds Issues

- Implementer subagent (or a new one) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

### If Subagent Fails a Task

- Dispatch a new fix subagent with specific instructions about what went wrong
- Don't try to fix manually in the controller session (context pollution)

## Efficiency Notes

**Why fresh subagent per task:**

Reference: `references/parallel-python-leaves-playbook.md` — executing
parallel implementation leaves of a Python/uv plan tree: timeout recovery
protocol (continuation prompts, direct-finish thresholds), file-ownership
boundaries for concurrent workers, fault-tolerant module self-registration,
formatter-scope guardrails (never repo-wide `ruff format`), and the
cross-worker contract-drift checklist (response normalization,
rate-limit/pagination parsing, YAML selector entries, manifest status
extensions, event_id suffix formats).
- Prevents context pollution from accumulated state
- Each subagent gets clean, focused context
- No confusion from prior tasks' code or reasoning

**Parallel workstreams / same-file races / wording sweeps / sourced tables:**
see `references/multi-task-batches.md` — batch dispatch by file set, one
writer per file (queue follow-ups that land on a running agent's file),
facts-to-subagents payload checklist, protected-literal rules for terminology
renames, and the fabrication guard for comparison tables.

**Why two-stage review:**
- Spec review catches under/over-building early
- Quality review ensures the implementation is well-built
- Catches issues before they compound across tasks

**Cost trade-off:**
- More subagent invocations (implementer + 2 reviewers per task)
- But catches issues early (cheaper than debugging compounded problems later)

## Integration with Other Skills

### With writing-plans

This skill EXECUTES plans created by the writing-plans skill:
1. User requirements → writing-plans → implementation plan
2. Implementation plan → subagent-driven-development → working code

### With test-driven-development

Implementer subagents should follow TDD:
1. Write failing test first
2. Implement minimal code
3. Verify test passes
4. Commit

Include TDD instructions in every implementer context.

### With requesting-code-review

The two-stage review process IS the code review. For final integration review, use the requesting-code-review skill's review dimensions.

### With systematic-debugging

If a subagent encounters bugs during implementation:
1. Follow systematic-debugging process
2. Find root cause before fixing
3. Write regression test
4. Resume implementation

### Go project conventions reference

For Go monolith tasks (pgx/v5, River queue, chi router), see `references/go-project-conventions.md` for reusable patterns: UUID-as-TEXT scan, JSONB marshalling, River schema migration pitfalls, Makefile backgrounding, embed-directory guard tests. Embed the relevant conventions directly in Go subagent dispatch contexts.

### External API contract verification reference

When implementing fetchers/clients against external APIs (job boards,
SaaS products, data feeds), see `references/external-api-contract-verification.md`
for the 3-stage verification pipeline (pre-dispatch doc check → live
dry-run smoke test → review-phase contract check) and concrete examples
of bugs that mock-server tests cannot catch. Applies to any task where
the subagent writes code that makes HTTP requests to an API the
orchestrator hasn't verified live this session.

## Example Workflow

```
[Read plan: docs/plans/auth-feature.md]
[Create todo list with 5 tasks]

--- Task 1: Create User model ---
[Dispatch implementer subagent]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, 3/3 tests passing, committed.

[Dispatch spec reviewer]
  Spec reviewer: ✅ PASS — all requirements met

[Dispatch quality reviewer]
  Quality reviewer: ✅ APPROVED — clean code, good tests

[Mark Task 1 complete]

--- Task 2: Password hashing ---
[Dispatch implementer subagent]
  Implementer: No questions, implemented, 5/5 tests passing.

[Dispatch spec reviewer]
  Spec reviewer: ❌ Missing: password strength validation (spec says "min 8 chars")

[Implementer fixes]
  Implementer: Added validation, 7/7 tests passing.

[Dispatch spec reviewer again]
  Spec reviewer: ✅ PASS

[Dispatch quality reviewer]
  Quality reviewer: Important: Magic number 8, extract to constant
  Implementer: Extracted MIN_PASSWORD_LENGTH constant
  Quality reviewer: ✅ APPROVED

[Mark Task 2 complete]

... (continue for all tasks)

[After all tasks: dispatch final integration reviewer]
[Run full test suite: all passing]
[Done!]
```

## Batching Sequential Tasks in One Subagent

When tasks have linear dependencies (Task B needs Task A's output, Task C needs Task B's), dispatch them as a single subagent rather than one per task. This avoids the overhead of re-reading files and re-establishing context between each step.

**Pattern:**
1. Group tasks by dependency chain: [1→2→3] [4→5] [6→7→8]
2. Dispatch each chain as one subagent with numbered steps
3. Subagent commits after each step within the chain
4. Parent verifies build after each subagent completes

**When to batch vs. when to separate:**
- **Batch**: Tasks modify the same files, share context, or build on each other's output
- **Separate**: Tasks touch different files, can run in parallel, or one is risky (security-sensitive, complex)

**Example from practice:** A 18-task plan across 9 phases was dispatched as 8 subagent calls:
- Tasks 1, 2, 3 in parallel (no dependencies)
- Tasks 4+5+6 as one chain (types→store→manager→worktree)
- Tasks 7+8 as one chain (session fields→daemon wiring)
- Tasks 9+10 as one chain (RPC→HTTP)
- Tasks 11+12 as one chain (CLI flags→subcommand)
- Tasks 13+14+15 as one chain (TUI status→commands→dialog)
- Task 16 standalone (security, independent)
- Task 17 standalone (context injection, independent)

This completed in ~15 minutes vs. 18 sequential subagent calls that would have taken 30+ minutes.

## Worktree-Isolated Leaf Dispatch

When the user says "do it in a worktree" or when implementing plan tree leaves that should run in parallel without repo conflicts, create a separate git worktree per leaf and dispatch the subagent to work there.

**Pattern:**
1. `git worktree list` — check existing worktrees and naming convention
2. `git worktree add ../<repo>-leafNN -b leafNN-description <base-branch>` — create worktree from the base branch
3. For LFS repos: `cd <worktree> && git lfs checkout && git lfs install --force && git lfs pull` — settle LFS pointers (worktree creation reports "files that should have been pointers but weren't")
4. Gather implementation context from the WORKTREE paths (leaf spec, conventions, existing code, attribution registries), not the main repo
5. `delegate_task` with absolute worktree paths in both `goal` and `context` — the subagent must know it is working in a different directory than the session cwd

**Why worktrees over same-repo dispatch:**
- Multiple leaves can be implemented truly in parallel without working-tree conflicts
- The main repo stays clean for orchestration, review, and other work
- Each leaf's branch is isolated — can be reviewed and merged independently

**Naming convention (rebellion-the-game):**
- Worktree dir: `rebellion-leafNN` (sibling to main repo dir, e.g. `/Users/caimlas/git/rebellion-leaf05`)
- Branch: `leafNN-short-description` (e.g., `leaf05-foliage`)
- Base from `main` HEAD

**Critical:** The subagent's context must use ABSOLUTE paths into the worktree (e.g., `/Users/caimlas/git/rebellion-leaf05/...`), not the main repo path. Subagents default to the session cwd; without explicit worktree paths they will write to the wrong repo.

**Context-gathering pattern for worktree dispatch:**
- Read the leaf spec from the worktree's plan dir
- Read the conventions file (SHARED-CONVENTIONS.md) from the worktree
- Scan existing files in the worktree that the leaf references (existing scripts, shaders, attribution.json, scenes)
- Pre-read key files to embed in the subagent context (attribution headers, existing code patterns the leaf says to reuse)
- All context-gathering reads should batch in parallel since they're independent

## Large-Scale Parallel Dispatch (Audit/Fix Pattern)

For codebase-wide audits or batch fixes across independent modules, maximize parallelism:

1. **Survey first**: Get file counts per module via `find . -name "*.go" | cut -d'/' -f1-2 | sort -u`
2. **Group by daemon/module**: Each subagent gets ONE module with full context
3. **Batch in groups of 3**: `delegate_task` has `max_concurrent_children=3`. For >3 tasks, split into sequential batches of 3.
4. **Go format before commit**: After all subagents finish, run `go fmt ./...` in EVERY Go module. Pre-commit hooks will reject unformatted files.
5. **Verify tests after fixes**: Subagents changing behavior often miss updating tests. Run `go test ./...` after all fixes and update any broken tests yourself.

## Large-Scale Code Audit (Two-Phase Pattern)

For comprehensive codebase audits (find bugs + fix them), use a two-phase approach:

### Phase 1: Parallel Audit (3 subagents)

Split the codebase by logical domain. Each subagent reads every file and returns a structured bug report:

1. **Survey**: `find . -name "*.go" -not -path './vendor/*' | cut -d'/' -f1-2 | sort -u` to get module list and file counts.
2. **Group into 3 balanced sets**: Core infra (daemon, rpc, bus, config), Agent system (agent, llm, memory, skills, tools), Security/support (security, comm, validators, metrics, pkg).
3. **Dispatch 3 audit subagents** with explicit file lists in `goal`, project context in `context`, and `toolsets: ["terminal", "file", "search"]`.
4. **Consolidate findings** into a prioritized list (critical > high > medium > low).

### Phase 2: Parallel Fix (3 subagents)

Group fixes by the same domain boundaries so subagents don't conflict on files:

1. **Assign fixes to 3 subagents** matching the audit groupings.
2. **Each fix instruction must include**: exact file path, line number/area, what's wrong, and the exact fix approach. Don't say "fix the race" -- say "add sync.RWMutex to Client.config, use RLock in Chat()/ChatWithProgress(), Lock in SwitchModel()".
3. **Subagents MUST read files fresh** before patching. Include this in instructions.
4. **Build verification**: Each subagent runs `go build ./...` after fixes.

### Post-Fix Verification (Parent Agent)

1. `go fmt ./...` in ALL Go modules (pre-commit hook requirement).
2. `go test ./...` in ALL Go modules.
3. Fix any test failures caused by behavior changes (subagents miss this).
4. Stage only changed files (not pre-existing dirty state): `git add file1 file2 ...`.
5. Commit with descriptive message listing all fixes.

### User preference: maximize parallelism

The user expects aggressive use of parallel subagents. When you have 4+ independent work units, split into batches of 3 and dispatch immediately. Do not sequence what can be parallelized.

### Subagent timeout (600s limit)

Subagents have a 600-second timeout. A subagent tasked with 10+ file modifications plus test writing WILL timeout. Design subagent scope accordingly:
- **Bug fixes**: 8-10 fixes per subagent max
- **Bug fixes + test writing**: 6-8 combined per subagent max
- **File reads only (audit)**: Can handle more since reads are faster
- **Code audit with fixes**: For modules >15K lines, split into 2 subagents (read+audit vs read+fix), not one monolithic subagent
- **Long-running downloads or external API calls**: A single 10MB file download over a slow link can take 60-90 seconds. Multiple such downloads in one subagent will exhaust the timeout budget. Split into batches of 2-3 per dispatch, or run serially from the parent agent.
- **Long-running server-side operations** (e.g., ComfyUI image generation taking ~90 min): these NEVER fit in a subagent's time budget. Use cron-driven execution, background server processes, or remote script invocation instead.
- **Benchmark/measurement runs that load multi-GB models**: a task like "load model A on port X, run 10-iteration benchmark, swap to model B, repeat, write results doc" looks small but each GGUF load is 45-90s and each benchmark iteration is 1-3s of LLM time — 2 models × (load + 20 calls) ≈ 5-8 min of wall-clock the subagent must babysit, plus server churn (start, poll health, kill, restart). It times out at 600s having only started the first server. **Run benchmarks directly in the parent session** (servers via background terminal, `-count=1` go test, then swap) — the parent has warm-server continuity and the numbers land in its context immediately. Subagents are for code/analysis, not for babysitting measurement loops. A timed-out benchmark subagent WILL leave its first llama-server running — check `pgrep -fl llama-server` and reuse it before killing.

**Practical examples from real sessions:**
- Freesound audio download: 3 subagent dispatches of 5 items each timed out at 300s due to large MP3 preview files (5-40 MB each). Fix: reduce to 2 items per dispatch, or run serially from parent agent with `urllib.request`.
- Qwen-Image generation on PG500-216: ~84 minutes per generation at 28 steps. Cannot be done in any subagent — use cron job or server-side SSH execution.
- Subagents that attempt `pkill -f` on remote servers may trigger security scanners blocking all SSH commands. Pre-verify what the target process looks like and use exact PIDs or service names.
- HTTP 500 from ComfyUI during generation doesn't mean the script is broken — it means the GPU CUDA compute capability is incompatible with the installed PyTorch build. Always check GPU CC vs PyTorch CUDA toolkit compatibility before debugging scripts.

### Timeout recovery: split and retry with smaller scope

When initial subagent dispatches timeout, do NOT retry with the same scope. The timeout means the scope was too large. Recovery strategy:

1. **Diagnose**: Check which subagents succeeded vs failed. Successful ones may have already applied partial fixes (check git diff) or written partial files (check filesystem).
2. **Split**: Break each failed subagent's scope into 2-3 smaller, more targeted subagents. Example: if "audit all of backend-api (62 files, 47K lines)" timed out, split into "audit handlers A-M" + "audit handlers N-Z" + "audit middleware + tests".
3. **Re-dispatch only the failed groups** with the smaller scope. Don't re-dispatch the groups that already completed.
4. **Verify incremental results**: After each batch, check `go build` and `git diff` before proceeding.

**Practical sizing limits from experience:**
- Subagent reading 12 files totaling ~6K lines + applying fixes: completes reliably
- Subagent reading 30+ files totaling ~10K lines + applying fixes: risks timeout
- Subagent reading 60+ files totaling ~47K lines: will almost certainly timeout
- When in doubt, target ~5-8K lines of Go per audit subagent

### Rate-limit recovery (HTTP 429): serialize, enrich context, fall back

429 ("Too Many Requests") is NOT a scope-too-large problem. The provider's per-token or per-request quota is consumed by aggregate parallel tool calls. Recovery strategy is distinct from timeout:

**(a) Serial retry, not parallel.** The most common 429 trigger is launching 3 subagents simultaneously on aggressive providers (deepseek-v4-flash, some OpenRouter routes). After a batch-failure where ALL subagents hit 429, retry them ONE AT A TIME — not as a batch, not even as a staggered batch. A single serial subagent usually stays under the per-request limit because it isn't competing with siblings for quota.

**(b) Rich-context retry reduces internal tool calls.** A subagent that must `terminal cat` 20 files and run 10 `search_files` makes ~30+ API calls internally; each can hit a rate limit. On re-dispatch, provide full source text quotes in the `context` parameter instead of file paths. Every read the subagent avoids is one less API call competing for the quota window. This is the same principle as the line-number-corruption prevention (Pitfall 12) but the motivation here is rate-limit avoidance, not file corruption.

**(c) Fall back to direct work in the parent agent.** If even serial retries fail with 429 (same provider, same quota exhaustion), the parent agent should produce the deliverable directly from its own accumulated context rather than dispatching another subagent. Signs to switch:
- The subagent consistently fails before producing any output
- You already read enough files yourself to write a defensible deliverable
- The work is read-only (analysis, audit, review)
- The deliverable is under ~600 lines (fits a single write_file)

Do NOT keep dispatching — each retry burns API calls re-reading context rather than producing output. In one session, a serial re-dispatch of 3 read-only audit subagents all hit 429 again before the parent agent wrote all 3 reports directly from its own accumulated file reads.

**(d) Check for partial persistence.** Some subagents complete write_file calls before hitting the rate limit on a later tool call. `git diff --stat` or `find` for expected output paths — the partial work may be usable, and only a small follow-up is needed.

**(e) Dead-simple sizing guide:** if you hit 429 on parallel dispatch, the fix is always (a) first, then (b), then (c). Never try to "parallelize harder" with a different concurrency shape — that burns more quota faster.

**Practical sizing limits from experience:**
- Subagent reading 12 files totaling ~6K lines + applying fixes: completes reliably
- Subagent reading 30+ files totaling ~10K lines + applying fixes: risks timeout
- Subagent reading 60+ files totaling ~47K lines: will almost certainly timeout
- When in doubt, target ~5-8K lines of Go per audit subagent

### Research/writing subagent timeout (web research trap)

Research and document-generation subagents have a DIFFERENT timeout failure mode than code subagents. They burn their entire budget on web_search/web_extract calls, leaving no time to write the deliverable. Two of three GDD document-writing subagents timed out at 600s with 20-30 API calls each (all web research), producing zero output files.

**Root cause:** The subagent was told to "use web_search to verify" a broad topic, so it spiraled into endless research without writing.

**Prevention — constrain research, force output:**
- Tell subagents explicitly: "Use the provided context as your primary source. Do NOT spend excessive time on web research. Where data is uncertain, make reasonable design decisions and mark them clearly."
- Set a line-count target (e.g., "Target 300-500 lines") so the subagent knows when it has enough to start writing.
- If web research is genuinely needed, cap it: "Limit web research to 5-8 searches maximum, then write the document."
- Split research-heavy tasks: one subagent does targeted research and outputs findings, a second subagent writes the doc from those findings plus provided context.

**Recovery pattern:** Check if the timed-out agent wrote any partial files. Re-dispatch with tighter constraints (less research, more writing from provided context, explicit line target).

### Pure writing tasks: parent agent should write directly

Even with explicit "DO NOT use web_search/web_extract" instructions, writing-heavy subagents can STILL time out. In one session, a subagent given full context and told to write a 400-line doc timed out at 600s with only 6 API calls - the model itself was too slow generating long-form text. This happened 5 consecutive times across different docs.

**When to write directly instead of delegating:**
- The document is pure knowledge synthesis (no code execution, no file discovery)
- You already have all the source material loaded in your context
- The doc is under 600 lines (fits in one write_file call)
- The topic requires no iterative exploration (you know the structure upfront)

**When delegation still wins for writing:**
- Multiple independent docs can run in parallel (3 docs in 3 subagents = 3x throughput)
- The doc requires research you don't have loaded (web search, file reading)
- The doc is very long (>800 lines) and would pollute your context

**Decision rule:** If a writing subagent times out once, re-dispatch ONCE with tighter constraints. If it times out again, write it yourself. Do not burn a third dispatch on the same doc - the pattern is clear.

**Also applies to small code leaves:** When a leaf is small enough (3-5 files, all types/config with no complex logic) and you have the full spec loaded in your context from reading the plan, writing the code directly takes 2 minutes vs 6+ minutes for a dispatch+return cycle. Use judgment: if the TDD cycle (write test, verify fail, implement, verify pass) is under 5 tool calls total, do it yourself.

**Hybrid foundation pattern (validated in AgentAudit session):** For Go project tree execution, write the foundation leaf (types, schema, config — ~5 small files) directly as the parent agent, then dispatch the larger leaves (store implementation, API handlers, analysis modules) as subagents in parallel. The foundation leaf is the highest-risk dispatch (every other leaf depends on its types being correct), but the lowest-risk direct write (it's pure struct/interface/migration definitions with no logic to get wrong). Writing it directly also ensures the types match Contract 5 exactly — no subagent interpretation drift. Then commit the foundation so sibling subagents inherit a green tree with real types to compile against.

**Decision rule for foundation leaves:** If the leaf creates only types/interfaces/migrations/config (no business logic, no complex algorithms), write it directly. If the leaf has logic (store queries, handlers, state machines, pattern detection), dispatch a subagent.

**Practical example:** A session needed 5 GDD world-design docs. 3 succeeded via parallel subagents. 2 timed out repeatedly (even with no web research allowed). The parent agent wrote both directly in ~2 minutes each - faster than the combined dispatch + timeout + redispatch + timeout cycle that had consumed 30+ minutes.

### Salvage pass on timed-out code subagents (verify BEFORE re-dispatching)

All three subagents in one 2026-08-14 batch hit the 600s timeout
simultaneously (three Godot test suites competing for CPU made each
subagent's own verification runs too slow). The salvage results diverged
completely: task 2's file was complete, task 3's files were complete, task
1's target file was **untouched** (zero work persisted — 11 API calls but
no writes). A blanket "re-dispatch everything" would have duplicated two
finished deliverables.

**The two-round rule (2026-08-15):** when a SECOND round of delegations on
the same task also times out (both cut mid-verification, ~60% of work on
disk: manifest + parsers written, loader written, overlay missing), stop
delegating. Finishing the known-remaining pieces directly (one test file,
one .gd consumer, one getter — ~15 min) beats a third 10-minute dispatch
that will also time out. After TWO timeout rounds on one task, the
brief-writing overhead exceeds the remaining work — switch to direct
completion with the salvage as your starting point.

**The salvage checklist (run before any re-dispatch):**
1. `ls -la` + mtime on every file the subagent was supposed to write.
   An mtime BEFORE the dispatch = zero work; during it = partial/complete.
2. Skim each artifact for the load-bearing symbols (grep the key function
   names from the spec). Presence + sensible length = likely complete.
3. Run the artifact's tests yourself (the subagent timed out during
   exactly this step — its non-report is not evidence of failure).
4. Re-dispatch ONLY the zero-work tasks; finish small gaps in-session.
5. Budget one extra round for fix-ups: salvaged code averaged 3-4 real
   bugs per deliverable (wrong skip conditions, caps that can't be
   reached, engine-error paths) that the timed-out verification never
   caught.
6. **When salvage reveals test-expectation drift, check the FIXTURE's
   arithmetic before debugging the code** (2026-08-15 terrain overlay):
   a synthetic grid fixture miscounted its own cells (claimed 3 mud,
   spec had 2), producing off-by-one failures attributed to the
   implementation. Count the fixture's data against the assertion first;
   also expect group-accumulation (a determinism test building twice
   without clearing sees 2× counts) and fix the test flow, not the code.

### Timed-out subagent may clobber a parent hotfix made while it ran

A timed-out subagent is not necessarily DEAD — its last few tool calls can
land after the batch timeout report. In the same 2026-08-14 session, the
parent fixed a freed-instance crash pattern in a file at T+20min, then
discovered the timed-out subagent had ALSO rewritten that file at T+44min
(during the crash diagnosis), silently re-introducing one occurrence of
the exact bug class the parent had just fixed.

**Rule: after any fix to a file inside a still-running (or timed-out,
unconfirmed-dead) subagent's scope, re-grep that file for the fixed
pattern when the delegation result arrives.** Look for a completion
message from the delegation — until one arrives, treat the subagent's
files as concurrently mutable even if the timeout report printed. A cheap
guard: after the batch completes, `grep` for the specific bug signature
(e.g. `var light: OmniLight3D = record.get(`) across the whole file, not
just the lines you patched.

When a subagent times out, any file writes it completed before the timeout ARE persisted to disk. If you re-dispatch the same task, check what's already done first -- you may only need to complete the remaining work.

**Same rule applies to summary-failure (503 / "completed but no summary").** A subagent can finish ALL of its file work and then lose the final summary API call — the batch result shows `status=completed` (or an error text) with no usable report, but the artifacts are complete on disk. **The first action on ANY infra-failed delegation is a salvage pass, not a re-dispatch:** `git status --short` + `ls` for the expected artifacts (edited files, temp probes), review the code line-by-line for completeness (a timed-out edit can be a partial/broken half-application — a `git diff --stat` and a skim of the new code settles it), run the artifacts yourself if they're tools/probes, then clean up throwaways. Only re-dispatch the genuinely missing parts. Real instance: two parallel probe subagents both failed on delivery (one 600s timeout, one 503) but left a complete +202-line tool edit and an un-deleted temp probe — both were run, verified, and used as-is; re-dispatching would have duplicated finished work.

### Code-gen subagent sizing (writing many new files from specs)

For pure file-creation tasks (writing N new source files from a plan/spec, no reads/tests/builds), the bottleneck is output-token generation time per file. Each 200-600 line source file is one large `write_file` call. Practical limits:

- **6-8 new files per subagent**: reliable completion (~10 min)
- **10-13 new files per subagent**: high timeout risk (both 6-file and 13-file agents timed out at 600s in one session, but wrote 11/12 and 8/13 files respectively before dying)
- **Recovery**: do NOT re-dispatch. Check what persisted (`find -newer <marker-file>`), verify completeness by checking last lines of each file, then write the remaining 2-5 files directly from the parent agent. The parent already has the spec context loaded — writing 3 files directly takes ~30 seconds vs. 10 minutes for a re-dispatch that will also timeout.

**Post-timeout verification pattern:**
```bash
# Find files written after a known-good marker
find rebellion-godot/scripts -name "*.gd" -newer rebellion-godot/scripts/core/event_bus.gd -type f | sort
# Check each file's last line for proper ending (not truncated mid-function)
for f in <files>; do echo "$f: $(wc -l < $f) lines, $(tail -1 $f)"; done
```

**Post-subagent file existence check (mandatory before commit):** After subagents complete (or timeout), verify ALL expected files exist. Files written by the parent agent before dispatching subagents may need re-verification — in one session, two parent-written files were not found by `git add` after subagent completion and had to be rewritten. Always `ls` every expected path before staging.

### Max-iterations subagents leave partial work

Subagents have a tool-call limit (typically 50 iterations). Complex tasks -- especially TUI integration with multiple files and nuanced wiring -- can exhaust iterations before finishing all steps. **The subagent marks itself as "completed" with a summary listing what remains.**

**Recovery pattern:**
1. Read the subagent summary carefully -- it lists what's done and what remains
2. Verify build: `go build ./...` -- the partial work may compile fine
3. Commit the partial work
4. Dispatch a follow-up subagent scoped ONLY to the remaining items

**Sizing guidance to avoid max-iterations:**
- TUI tasks touching 4+ files (app.go, modal.go, command_handler.go, types.go, config.go, rpc.go): split into 2 subagents (types+rpc first, then wiring)
- Tasks requiring extensive file reading before writing: the reads count against the iteration limit. Consider providing file content in the context parameter instead.
- A subagent that reads 6+ files and writes to 5+ files in a single task is at high risk of hitting the limit.

### Subagents can write to the wrong repository

When working across multiple repos in one session (e.g., auditing `/Users/caimlas/git/meept` from a session rooted in `/Users/caimlas/git/strategist`), subagents may write files to the wrong repo. One subagent wrote `audit-report.md` to the strategist repo instead of meept. **Prevention**: include explicit absolute paths in every subagent's goal/context. Never let subagents choose the output directory -- tell them exactly where files go. **Detection**: after subagent completion, check for unexpected files in the parent session's working directory (`git status` in the parent repo).

### Subagents may commit with wrong messages or commit unintended files

Subagents that call `git commit` may use placeholder messages (e.g., "test") or stage all files including pre-existing dirty state. **Prevention**: tell subagents "Do NOT commit" and handle git operations yourself after verifying their work. When subagents must commit, give them an explicit commit message and a specific `git add` file list, never `git add -A`.

### Parallel fan-out partitioning on ONE repo

When N agents run CONCURRENTLY on the same repo, file-level collision is the
primary failure mode. Zero-conflict rules (file partitioning, parent-does-shared-
schema-first, parent-does-integration-wiring, per-agent verify then one
consolidated commit) + brief template: `references/parallel-fanout-partitioning.md`.
Proven 2026-08-31 with a 4-agent fan-out across 3 packages, zero conflicts.

### Committing safely when a CONCURRENT agent shares the repo

Distinct from subagents committing badly: in long-running projects, ANOTHER agent or session may be committing to the same repo in parallel with your work. Signs:

- `git log --oneline -5` shows commits you did NOT make, dated during/after your session start.
- `git status --short` lists modified files you never touched (the other agent's in-progress edits).
- A file you created/deleted as temp cleanup shows as tracked-and-deleted (D) because the other agent committed it between your writes.
- A file you expected to be uncommitted is already `git ls-files`-tracked and clean (the other agent committed it first).

**The rule: never `git add -A` / `git add .` in a repo with concurrent writers.** Stage ONLY your files by explicit path:

```bash
git add path/to/file1 path/to/file2 docs/spec.md   # explicit list, nothing else
git diff --cached --stat                            # confirm the staged set is exactly yours
# build + test the staged state, THEN commit
```

**Before staging, triage every entry in `git status`:**
- Modified file you don't recognize → another agent's work. Leave it OUT of your commit.
- Tracked file showing as deleted (D) that you removed as temp cleanup, but another agent committed it → ambiguous ownership. Leave it out; don't delete another agent's committed file in your commit.
- File you created that's already tracked+clean → the other agent committed it; nothing for you to stage.

**Real instance:** After a multi-subagent build, `git status` showed my 9 files PLUS `llama_client.go` (an unrelated `repeat_penalty,omitempty` edit from a concurrent agent) and `dual_smoke_test.go` as deleted (committed by the other agent, removed by me as temp cleanup). `server_manager.go` was already committed by the other agent. I staged only my 9 files by explicit path, verified `git diff --cached --stat` + build + tests, and committed — leaving the other agent's changes and the ambiguous deletion untouched. A `git add -A` would have swept in the other agent's half-finished change and the contested deletion.

**Detection habit:** run `git log --oneline -5` and `git status --short` together at the start of any commit step. If the log has commits you didn't make, you are in concurrent-writer mode — switch to explicit-path staging immediately.

**Exception — user explicitly authorizes committing the working tree.** The "stage only your files" rule above prevents *accidentally* sweeping in another agent's half-finished work. It does NOT apply when the user explicitly says "commit" / "commit it" while the tree holds a concurrent agent's changes AND you've confirmed that batch is complete. In that case:

1. **Verify the whole batch is coherent before committing** — `go build ./...` (or project build) AND the analyzer/linter on every changed surface. A concurrent agent may have left the tree mid-edit; in one session the analyzer reported an undefined method that the concurrent process then finished writing seconds later — re-run the analyzer after a brief wait rather than committing a red tree.
2. **Commit, then disclose provenance.** In your reply, state plainly which changes were NOT yours this session ("these appeared from a concurrent process; I verified they compile and pass checks before committing"). Offer to undo (`git reset --soft HEAD~N`) if the user didn't want them committed yet.
3. **Never commit a red build** even if the user said "commit" — a half-finished concurrent batch that doesn't compile is not committable; wait for it to go green or stop and tell the user.

The load-bearing principle in both the rule and the exception: the user must never be surprised by what landed in a commit. Stage-only-yours prevents surprise by exclusion; verify-then-disclose prevents surprise by transparency.

### After security-defaults refactoring: test helpers must override defaults

When refactoring HTTP server defaults from insecure to secure (TLS on by default, auth required by default, etc.), ALL test files that create servers via `DefaultServerConfig()` will break because tests connect via plain HTTP. **Pattern**: after the refactoring, search every test file for `DefaultServerConfig()` and add explicit overrides:
```go
cfg := DefaultServerConfig()
cfg.UseTLS = false
cfg.RequireAuth = false
```
This is a systemic pitfall -- the test failures are spread across multiple packages and may not appear until the full `go test ./...` run.

### Adding migrations/files breaks hardcoded count tests

Projects with embedded resource directories (Go `//go:embed migrations/*.sql`, fixture counts, snapshot tests) often have a guard test like `TestMigrationFiles_Count` with a hardcoded `const expectedCount = 10`. When a subagent adds a new migration or fixture, the test fails on the NEXT run because the count bumped but the test's constant didn't.

**Pattern**: when dispatching a task that adds a file to an embedded/auto-discovered directory, tell the subagent to search for and update any count-based test:
```sh
grep -rn "expectedCount\|expected.*=.*[0-9]" internal/db/*_test.go
```
Then bump the constant in the same commit. This is easy to miss because the new file compiles fine — the failure only surfaces in `go test`.

### Cross-repo auditing: be explicit about which repo to work in

When a session involves multiple repos (e.g., auditing both `/Users/caimlas/git/strategist` and `/Users/caimlas/git/meept`), include the absolute repo path in every subagent's goal. Do not assume subagents know which repo to operate on. Subagents may write files to the parent session's working directory instead of the intended repo. **Detection**: after subagent work, check `git status` in both repos to catch misplaced files.

### Mock-server tests can mask production bugs (TDD-green ≠ production-correct)

When a fetcher/integration is tested via `httptest.NewServer` with canned
JSON fixtures, TDD red-green-refactor confirms the code correctly parses
the FIXTURE — not that the fixture matches reality. If the plan's API
shape was wrong (stale docs, assumed auth scheme, wrong field types),
both the implementation AND the test fixture encode the same wrong
assumption. Tests pass green. Production fails.

**Real instance (2 bugs in one session):**
1. A USAJobs fetcher was implemented with `Authorization: Basic email:apikey`
   (literal) auth. The test fixture asserted `HasPrefix("Basic ")` and
   `Contains("email:apikey")` — both passed. The real USAJobs API requires
   `Authorization-Key: <apikey>` + `User-Agent: <email>` + host
   `data.usajobs.gov`. Every production request would have 401'd.
2. A SmartRecruiters fetcher used the `ref` field (an API detail URL) for
   the job URL instead of `applyUrl` (the user-facing apply page). The test
   fixture hand-set `ref` to a realistic-looking careers URL that the real
   API never produces — so the assertion passed but production stored API
   URLs in the `url` column, breaking "click to apply".

**Detection pattern for the review phase:** When reviewing code that
integrates with an external API the implementer has never hit live, add
these checks to the spec-compliance or code-quality review:
1. Were the API contract details (endpoint URL, auth headers, response
   field names/types) verified against live docs or a live `curl`?
2. Does the test fixture use a response shape copied from real API output,
   or one written from the plan's description (which may be stale)?
3. For auth-bearing sources: is there a live curl verification step in
   the plan? If not, flag it as an open risk and dispatch a review
   subagent to verify the auth scheme against the provider's docs.

**Prevention at dispatch time:** When dispatching an implementation task
that integrates with an external API, include the exact API contract
(endpoint, headers, response shape) IN the subagent context, verified
via `web_search`/`web_extract` of the provider's docs page BEFORE
dispatching. Do not trust the plan's API description if no one has
verified it this session — plans are often written from memory or
stale blog posts.

**Detection: live dry-run integration smoke test.** After all unit tests
pass and the code is committed, run the actual tool/CLI against REAL
endpoints in a no-side-effects mode (dry-run, --dry-run, sandbox mode).
This catches an entire class of bugs that neither mock-server tests nor
doc-based review can catch:

- **Endpoint drift**: external APIs move or deprecate endpoints. The
  Arbeitnow API changed from `/api/job-board.json` to
  `/api/job-board-api`; the old URL 302-redirected to the homepage,
  returning HTML where JSON was expected. Unit tests passed because the
  mock server always returned valid JSON at the expected path.
- **Field type mismatches**: the Arbeitnow API docs/community examples
  described `location` as an array, but the live API returned it as a
  plain string. `json.Unmarshal` failed with a type error only against
  the real response.
- **Auth scheme errors**: even when docs are checked, the actual HTTP
  exchange may reveal subtle differences (redirect chains, header
  stripping by proxies, cookie requirements).

**The pattern:** after the implementation phase + unit tests are green,
run `go run ./cmd/your-tool -dry-run` (or equivalent) pointed at real
endpoints. Scan the output for: (a) decode errors (HTML returned where
JSON expected → endpoint moved), (b) type mismatch errors (field shape
changed → struct needs updating), (c) HTTP 4xx/5xx (auth or endpoint
wrong), (d) zero results when results were expected. Fix each finding
before proceeding to the review/fix phase — it's cheaper to catch them
here than to have a review subagent discover them later.

This step takes 30 seconds and catches bugs that a 5-minute review
subagent reading docs might miss. It is complementary to — not a
replacement for — the doc-verification prevention step above.

### Subagent fixes may leave test failures

Subagents that change behavior (adding new fields, changing defaults, modifying signatures) frequently miss updating test files that depend on the old behavior. After all subagent fixes complete, the parent agent MUST run the full test suite and fix any test failures. Subagents cannot be trusted to run comprehensive tests on their own changes.

### Subagents creating new files can DELETE existing committed files

When a subagent is told to create a new `.go` file (e.g. `internal/rpc/dispatch.go`) and a file with that name ALREADY EXISTS in the repo (committed, not just in the working tree), the subagent may use `write_file` to overwrite it — or worse, delete the existing file and create a new one with a different name, losing the committed content entirely.

**Real instance:** A subagent was instructed to create `internal/rpc/dispatch.go` for dispatch-tracing RPC handlers. A committed `dispatch.go` already existed (containing cluster-dispatch RPC types from a prior feature). The subagent recognized the collision and created `dispatch_trace.go` instead — but it ALSO deleted the original `dispatch.go` (247 lines of committed cluster-dispatch types). This was only caught by `git diff --stat` showing `internal/rpc/dispatch.go | 247 ----` in the parent's verification pass.

**Detection — always check `git diff --stat` for unexpected deletions after a subagent that created new files:**

```bash
git diff --stat | grep "^ .*| .*[0-9]* -*$"
```

Or more simply, scan for any file showing as deleted that the subagent wasn't told to touch:

```bash
git diff --name-status | grep "^D"
```

**Prevention:** Before dispatching a task that creates a new file, check if the filename already exists (`ls internal/rpc/dispatch.go`). If it does, tell the subagent the exact alternative filename in the dispatch context. Don't let the subagent choose — it may resolve the collision by deleting the existing file.

### After parallel fix subagents

1. Run `go fmt ./...` in ALL Go modules (not just the ones that changed)
2. Run `go test ./...` in ALL Go modules
3. Fix any test failures caused by behavior changes (subagents often miss this)
4. Run `go build ./...` to verify compilation
5. Check `git diff --name-status` for unexpected file deletions (see pitfall above)
6. Then commit -- pre-commit hooks will also run linters

### Patch tool + sibling subagent concurrency = file corruption

When two agents (or a parent and a sibling subagent) edit the same file concurrently, the `patch` tool emits a distinct warning in its output:

```
"_warning": "... was modified by sibling subagent 'sa-X-...' at HH:MM:SS — after this agent's last read at HH:MM:SS. Re-read the file before writing."
```

**This warning is not advisory — it is a hard signal.** The file content you read is now stale. If you apply another patch using `old_string` from the stale read, the patch will match on a partial or shifted region of the file and produce corrupted output: duplicated function bodies, orphaned code blocks, or syntactically invalid Go.

**The rule:** After seeing this warning on ANY patch or write operation, you MUST re-read the file with `read_file` before applying another patch or write to that file. Never apply a second patch without re-reading first — the first patch may have already moved content around, and the second patch's `old_string` was computed against a version that no longer exists in the file.

**Recovery when it happens:**
1. Re-read the corrupted file end-to-end with `read_file` (no offset/limit — get the full file). The corruption signature is distinctive: duplicated function bodies (same function appearing twice with different content), orphaned `return` statements after closing braces, missing loop bodies (an inner `for` block reduced to just its opening line).
2. Identify the garbage region. In multi-subagent corruption, the damage is usually localized — one or two functions with duplicated bodies.
3. Use a single large `patch` to replace the entire corrupted function with the correct code. Do NOT attempt to fix it with multiple small patches — each one risks re-triggering the same corruption pattern if the file has shifted.
4. Run `go build ./...` immediately to verify. If the build fails, re-read the file again (it may have shifted further from a sibling's pending write) and re-apply the fix against the fresh content.

**Common corruption signatures from multi-subagent collisions:**
- `return violations\n}\n\treturn violations\n}` — a function's closing block duplicated
- A `for...range` loop body reduced to just the loop header with the body lines orphaned below
- Comment blocks from two different versions of the same function interleaved

**Prevention:** When dispatching sibling subagents that touch files in the same package, assign non-overlapping files. For shared files (evaluators, tracers, main orchestrators), serialize the subagents that touch them — complete subagent A, verify its file, then dispatch subagent B. If three subagents all need to add checks to the same evaluator, have them write to separate files or dispatch them sequentially.

### Parent agent racing a still-running subagent (writes that appear/disappear)

The sibling-collision sections above cover two PARALLEL subagents. A different race happens when the PARENT (orchestrator) starts editing files while a dispatched subagent is STILL RUNNING and writing to the same files. Symptoms are bizarre and easy to misread:

- A `grep`/`search_files` for a symbol returns "NOT PRESENT" — so you write it yourself — then the build fails with "method already declared" because the subagent wrote it a moment AFTER your grep ran.
- A file you confirmed absent suddenly exists; a file you wrote gets overwritten or its content shifts under your next patch.
- The `patch`/`write_file` tool emits the sibling-modification warning naming a subagent that, from your perspective, "already finished."

**Root cause:** the subagent's writes and your reads/writes are interleaved in real time. Your point-in-time grep is stale the instant the subagent's next write lands.

**Prevention — pick ONE writer per file:**
- Cleanest: do NOT edit any file the running subagent owns. Wait for it to return, run the verification pass, then fill only the genuine gaps.
- If you must work concurrently, partition strictly: the subagent owns files {A,B,C}, the parent owns {D,E} — zero overlap, same rule as sibling file-ownership partitioning.
- Never "helpfully" write a file the subagent was also told to create. You will collide.

**Recovery when a duplicate/collision surfaces:**
1. Re-read the affected file fully (`read_file`, no pagination).
2. Find the duplicated symbol (e.g. two identical `SetLLMClient` methods) and remove ONE copy with a single `patch`.
3. `go build ./...` to confirm. If it still fails, re-read — the subagent may have written again since.

**Key insight:** if a subagent is still running, treat every file in its scope as concurrently mutable. Your grep is a snapshot of the past, not the present.

### Sibling subagents report stale build errors as "pre-existing"

When two parallel subagents touch different files in the same module and one finishes before the other, the slower subagent's `go build ./...` may run AFTER the faster sibling committed but BEFORE that commit is reflected in the slower subagent's view. The slower subagent then reports a build error in a file it doesn't own, and may flag it as "pre-existing / not introduced by me, out of scope."

This is a false signal. The error was real in the window when the subagent ran `go build`, but the sibling's subsequent commit fixed it. When you (the orchestrator) verify the final state, the build is clean.

**Detection:** the subagent's "pre-existing build error" report names a file it did NOT modify, and `git status` at return time shows that file is committed (not in the working tree). Re-run `go build ./...` yourself — if it passes, the reported error was stale and can be ignored.

**Prevention:** tell subagents in their dispatch context that siblings are running concurrently, and that build errors in files they did not touch are likely transient — they should note them but NOT attempt to fix them or block on them.

- **Parent agent patches corrupt when sibling subagents modify the same file concurrently** — see "Sibling collisions" above.

### Pitfall: Interface contract signature drift during parallel implementation

When two or more subagents implement code that shares an interface (e.g., one writes the Store interface, another writes the SQLiteStore implementation, a third writes API handlers that consume it), a subagent will sometimes change the interface signature to suit its own implementation — breaking all consumers.

**Real instance:** The Store interface defined `InsertScreenshot(ctx, Screenshot) error`. A session segmenter subagent changed the SQLiteStore implementation to `InsertScreenshot(ctx, Screenshot) (int64, error)` — returning the insert ID. This broke the Store interface: SQLiteStore no longer satisfied Store, causing a compile error in every package that used `var _ Store = (*SQLiteStore)(nil)`.

**Detection:** `go build ./...` fails with `*SQLiteStore does not implement Store (wrong type for method X)`. The error names the exact method and signature mismatch.

**Fix:** Revert the implementation to match the interface defined in the foundation leaf. The interface IS the contract — if a subagent needs a different signature, it must be negotiated in the orchestrator, not silently changed in the implementation.

**Prevention:** In every implementation subagent's dispatch context, include: "Do NOT modify interface signatures defined in the foundation files. If you need a different return type, add a NEW method — do not change existing ones."

### Pitfall: ID-derived fake coordinates cause spatial collisions

When a `computeCentroid()` function derives positions from NPC IDs (e.g., `id % 100`, `(id / 100) % 100`) as temporary placeholders, two spatially-coincident candidates (same cluster key in the caller) get wildly different centroid positions. In one real instance, two NPCs both at `{X:0, Y:0}` were placed 50 units apart (centroid `6` vs `56`), which then failed the proximity check (`dist > minSphere`), preventing cross-band tension accumulation silently.

**Rule:** If the candidate map key IS already a position/bucket, pass it directly to `computeCentroid`. Do NOT recompute from member IDs. When using placeholder centroid derivation, ALWAYS verify distances are zero for co-located members. Quick sanity check: after entity creation, call `vecDistance(a.pos, b.pos)` for members that share a cluster key — should be 0 or near-zero.

### Pitfall: Dispersed entities must clear their member maps

When `Entity.Tick()` returns a dispersion event (morale collapse or membership drop), the entity remains in the Manager's list with its old members intact. The Manager's `prune()` checks `HasMembers() || !IsDissolving()` — but if members weren't cleared, the entity appears to still have 12 members and survives the prune anyway.

**Fix:** After calling `e.disperse()` in `Entity.Tick()`, set `e.members = nil`. This ensures the next `Tick` call sees `MemberCount() == 0` → returns nil immediately, and `prune()` correctly removes the ghosted entity. Without this, the crowd entity persists silently forever, wasting a pointer and producing stale data.

### Pattern: Per-alignment crowd entity formation

When implementing faction-gated group behavior, use alignment bands (±threshold on a political axis) to split clusters into per-faction crowd entities. Each band gets its own `CrowdEntity` with independent mood/morale/tension. Opposing bands at the same location accumulate cross-band tension; same-band groups merge into one entity. This enables emergent mob-vs-mob scenarios where each side has separate state, while keeping simulation O(1) per crowd regardless of size. Key constants: form threshold (10), alignment band width (±0.3), tension rate per tick, disperse thresholds for morale-based breakup. The manager handles: tick all entities, compute tension between opposing pairs, prune dissolved entities, form new entities from candidates. Spread across three files: `crowd.go` (Entity), `manager.go` (lifecycle). Tests cover band opposition, mood escalation, cross-band tension, formation, multi-band co-location, authority pressure, dispersion, gossip fact injection, and benchmark at 50/200 NPC scale.

### Pattern: Stub-first crowd injection into tick loop

When wiring a new subsystem (like crowd management) into an existing simulation tick loop, inject it as Phase N+0.5 between existing phases rather than at the end. This preserves the execution order of later phases that may depend on earlier subsystem state (e.g., perception uses positions computed by schedule, economy uses entity states). For the crowd tick specifically: Phase 5b goes between SCHEDULE (phase 5) and MEMORY_DECAY (phase 6), because crowd dispersal facts need to be available before perception resolves for newly-dispersed NPCs.

### Debugging cross-band tension silently failing

When implementing cross-band tension accumulation, verify at three points: (1) entities exist at expected positions after formEntities (use debug prints or test output to confirm), (2) computeTension iterates over the right pairs (verify `band.Opposing()` returns true for expected pairs), (3) proximity check passes (`dist < minSphere`). If step 3 fails, the root cause is usually step 1 — entity positions don't match the intended cluster location because the centroid computation is wrong (see ID-derived fake coordinates pitfall). A targeted debug test that prints entity positions, distances, and opposition results catches this in minutes rather than hours.

When you (the orchestrator) are patching a file while a sibling subagent is also modifying it, the `patch` tool warns: `"X was modified by sibling subagent — re-read the file before writing."` **This warning is NOT advisory — skipping the re-read reliably produces corrupted files with duplicated code blocks and syntax errors.**

The mechanism: your patch targets `old_string` at a specific position in the file as you last read it. If a sibling subagent inserted or deleted lines in the same region, your patch either (a) finds the wrong match and replaces the wrong section, or (b) partially succeeds on one occurrence and fails on another, leaving garbage. Either way, the resulting file has duplicate function bodies and orphaned code fragments.

**Recovery pattern:**
1. Re-read the entire corrupted file with `read_file` — never try to patch over corruption blind.
2. Identify exactly what is duplicated (look for repeated function signatures, identical blocks separated by garbage).
3. Use a single `patch` call with the full duplicated block as `old_string` and the clean version as `new_string`.
4. Verify with `go build ./...` before proceeding.

**Prevention rule:** After ANY patch that triggers the sibling-modification warning, re-read the file before the NEXT patch to the same file — even if the first patch appeared to succeed. The corruption may only become apparent on the next build, and fixing it then costs more time than one defensive re-read.

## The "Continue" Steering Pattern

When the user says "continue implementing", "continue fixing", or "continue with [X] using subagents", they expect the agent to:

1. **Assess what's done vs what remains** — check git log, test status, and the plan's scope
2. **Identify the next logical work item** — even if it was previously marked "out of scope". When the original plan is complete, "continue" means pick up the deferred items (integration wiring, low-priority findings, follow-up features)
3. **Dispatch subagents to do it** — the user said "using subagents" because they want parallelism, not serial parent-agent work
4. **NOT ask for clarification unless there's a genuine fork** — if the next step is ambiguous between two equally valid approaches (e.g. River worker vs CLI tool vs HTTP endpoint), a single clarify call is acceptable. If it's just "what should I work on next", figure it out from the plan/state and proceed.

This is the "strong opinions, loosely held" dispatch mode. The user trusts the agent to scope correctly and will redirect if needed. Each "continue" is a blank check for one more wave of work — use it fully.

## File-Ownership-Partitioned Fix Dispatch

When applying fixes from a review via parallel subagents (rather than in-session), partition the subagents by **non-overlapping file groups**, not by finding category. Each subagent gets explicit ownership of a file set and explicit "do NOT touch" instructions for siblings.

**Pattern:**
```
Fix subagent A: owns cmd/ingest-ats/main.go, cmd/ingest-ats/main_test.go
Fix subagent B: owns internal/search/ats/*_test.go files only
Fix subagent C: owns internal/search/ats/usajobs.go, smartrecruiters.go (+ their tests)
```

Each subagent's context includes: "Do NOT touch [list of sibling-owned files]. Sibling subagents are concurrently modifying them."

**Why file-ownership partition beats category partition:**
- Category partition (e.g. "subagent A fixes all auth bugs, subagent B fixes all URL bugs") causes file collisions when findings span the same files
- File partition guarantees zero `patch`-tool sibling-modification warnings
- Each subagent can safely read+write its files without re-reading after every sibling commit

**Validated in practice:** A 3-subagent fix wave (CLI fixes / ats test fixes / critical impl fixes) with explicit file ownership completed with zero collisions, zero corruption warnings, 41 tests green on merged verification.

## Fix-After-Review: When to Apply Fixes Directly vs Dispatch

After a review phase (parallel review subagents or in-session review) produces a list of Critical/Important findings, there is a dispatch decision: apply the fixes yourself (in-session) or dispatch fix subagents.

**The default reflex is to dispatch — but after a review phase, the calculus is different.** The review already loaded every relevant file into the orchestrator's context. Dispatching fix subagents forces each one to re-read those same files from scratch, burning 15-30 API calls per subagent just on re-discovery — and on rate-limited providers, that re-discovery is exactly what triggers 429 failures.

### When to apply fixes directly (in-session, no dispatch)

Apply fixes yourself when ALL of these hold:
1. The orchestrator already read the target files during the review phase (you have the full content in context).
2. The fixes are surgical — small edits at known locations (a method body, a struct field, a migration SQL block, a middleware check). Not "rewrite this 400-line file."
3. Multiple subsystem fixes share infrastructure files (e.g., `cmd/web/main.go`, `db_test.go`, a worker registration file). Fix subagents scoped to different subsystems will collide on these shared files — the patch tool's sibling-modification warning fires, and corrupted output follows.

**Real instance:** Three parallel review subagents succeeded cleanly (read-only, no collisions). Three parallel FIX subagents covering the same subsystem boundaries ALL failed — every one hit 429 (8 retries each), AND every one modified files outside its assigned subsystem (shared infrastructure), producing an uncommittable mess. Recovery required `git stash --include-untracked`, restore clean tree, then redo all fixes serially in-session.

### When dispatching fix subagents still wins

Dispatch fix subagents when:
- The orchestrator did NOT review the target files (someone else reviewed, or the review was shallow)
- The fixes are large (>200 lines of new code per subsystem) and would pollute the orchestrator's context
- Each subsystem's fixes touch entirely disjoint file sets (no shared infrastructure)
- You need the work done in parallel to save wall-clock time

### The workflow when applying fixes directly

1. `git status --short` — confirm the working tree is clean before starting
2. Work one subsystem at a time, committing after each (so partial progress is preserved)
3. After each subsystem's fixes: `go build ./... && go test ./...`
4. Be aware of your OWN tool-call budget — applying 12 fixes across 3 subsystems in-session is ~30-40 tool calls. If you sense you're approaching the iteration cap, commit what's done and hand off cleanly rather than leaving uncommitted edits on disk.

### Key insight: the review phase IS the context-loading phase

A well-run review (parallel subagents reading every file) has a side effect: the orchestrator's context now holds the full source. This makes the review phase a sunk cost — the files are already loaded. Throwing that away by dispatching fresh subagents that must re-read everything is the most expensive possible path to the same fixes. When in doubt after a review, patch directly.

## Plan Verification via Parallel Review Subagents

When asked to review a plan for completion/correctness, dispatch 2 parallel review subagents that split the tasks between them. Each subagent reads the actual implementation files and reports PASS/PARTIAL/FAIL per task with specific evidence.

**Why subagent-based review beats parent-agent review:**
- Subagents read full files without polluting the parent's context window
- Each subagent can deeply inspect its half without time pressure
- The parent only sees the structured report, not 50+ file reads
- Catches gaps that surface-level `search_files` misses (e.g., a method exists but is never called, or a struct field is missing from a ConfigUI builder)

**Pattern:**
```python
delegate_task(
    goal="Verify implementation of Tasks 1-9 from the plan...",
    context="""
    For each task, read the specified files and check EVERY requirement.
    Report: PASS (all met), PARTIAL (list gaps), or FAIL (not implemented).
    Be precise about line numbers and actual code found.
    """,
    toolsets=['terminal', 'file']
)
# Second subagent covers Tasks 10-18
```

**Critical rule: never trust cached assessments.** If the user says "review each file" or "do not assume correctness," they mean it -- the previous session's percentage chart is stale. Re-read everything. A task scored 85% might actually be 100% (wiring you missed), or 30% (stub that looked real on grep).

**Gap-closing phase after verification:** When verification finds small independent gaps (a missing UI field, a missing slash command), dispatch parallel fix subagents to close them all at once. Pre-read the target files first and include specific code context in the subagent instructions:
- Exact struct definitions the subagent needs to modify
- Method signatures and their current implementation
- The RPC methods already available on the client
- Surrounding code patterns (how similar features are structured)

This pre-reading makes subagents dramatically more effective -- they spend their iterations on writing code, not discovering context.

## Cross-Plan State Assessment (Forest Surveys)

When the user asks "which plans should be implemented next" or "what's the implementation status" across a project with multiple plan trees (a forest), do NOT trust the plan tracking tables alone. They are routinely stale — tables show PLANNED/PENDING for trees whose code was fully implemented and committed in past sessions. Always ground your assessment in actual code state.

### Step 1 — Survey the plan forest

Read every plan tree's `master.md` completion tracking table in parallel (batch `read_file` calls — they are independent). Extract:

- Which trees exist and their declared status (PLANNED/IN_PROGRESS/COMPLETE)
- Which leaves are PENDING vs COMPLETE
- Dependency chains between trees
- The build order / phase structure

### Step 2 — Get ground-truth code state

Use three complementary signals. Batch them in one assistant turn.

**Signal A — Test status:**
```
go test ./... -short -race -count=1 2>&1 | tail -20
```
A green test suite across ALL packages is a strong signal that implementation is complete and functional. Red tests = incomplete or broken work.

**Signal B — Git history (commit messages):**
```
git log --oneline --all -30
```
Commit messages like `feat(X): implement Y (tree #Z)` tell you exactly which trees were implemented. Look for:
- `feat(X): implement ... (tree #N)` — tree N's code is done
- Sequential: `feat(gamemaster): implement ... — ALL 12 GO TREES COMPLETE`
- Iterative: `fix(X): ...` after `feat(X)` — tree was implemented and then debugged

**Signal C — Filesystem:**
```
ls -d sidecar/internal/*/              # package existence
find Source -name "*.cpp" -o -name "*.h" | sort  # UE5 C++ files
```

### Step 3 — Cross-reference against tracking tables

Build a comparison table:

```
| Tree | Plan Status | Go Pkgs Exist | Test Result | Git Evidence         | Real Status |
|------|-------------|---------------|-------------|----------------------|-------------|
| 02   | PLANNED     | gossip/       | PASS        | feat(gossip)         | COMPLETE    |
| 10   | PLANNED     | procgen/ (4)  | PASS        | feat(procgen stages) | PARTIAL     |
```

Common finding: plan tables show PLANNED for 12/12 trees, but codebase inspection shows 10/12 are fully implemented and only 2 have real remaining gaps. The plan tables were never updated after implementation.

### Step 4 — Identify real gaps

From the comparison table, list what is TRULY not done:

- Go packages that do not exist (e.g. `memory/`, `economy/`)
- UE5 C++ files that do not exist (e.g. `SidecarClient.h`)
- Plan tree leaves whose code was never created
- Stubbed simulation phases (e.g. "phases 6-9 are no-ops" in `simulation.go`)
- Procgen stages past the first leaf

Exclude any tree whose code exists and tests pass — those are COMPLETE regardless of what the tracking table says.

### Step 5 — Dependency-wave analysis

Map remaining gaps to the build plan's dependency graph (usually in the root `master.md` or the project's build-plan-index):

```
Group A (critical path, no dependencies):
  Tree #03 leaf 02 — UE5 sidecar IPC (blocks sandbox PIE)
  Tree #01 leaf 04 — Portal items (standalone content)

Group B (parallel after A):
  Tree #10 leaf 02 — Procgen buildings (independent)
  Memory package — sim phase 6 (standalone Go)

Group C (after identity + gossip):
  Economy package — sim phase 8
```

Each dispatch round runs independent tasks in parallel (max 3 concurrent per delegation config).

### Step 6 — Present recommendation

Show the user:
1. Summary chart (what is actually implemented vs what the plan claims)
2. Real gaps (specific files/packages missing)
3. Recommended rounds (ordered, dependency-respecting)
4. Context size per dispatch (files to create, estimated lines)
5. Let them confirm or reorder before dispatching

### Worked Example

A full worked example (Rebellion game: 14 Go packages, 12 plan trees, 3 parallel dispatches) is in `references/plan-forest-assessment.md`. Key finding: plan tables showed 12/12 PLANNED but code inspection showed 10/12 COMPLETE with 211 tests passing, and only 3 trees had real remaining gaps.

## Resuming In-Progress Plans

When a user says "continue implementing" or asks you to pick up a plan that was started in a prior session, do NOT blindly re-dispatch all tasks. First determine what is already done:

### Step 1: Systematic Status Check

Use `execute_code` to batch `search_files`/`read_file` calls against every task in the plan:

```python
from hermes_tools import search_files, read_file

# For each task, check: do the specified files exist? Do the specified
# functions/methods/types appear in those files?
results = {}
results["task1"] = bool(search_files(pattern="ProjectsConfig", path="internal/config/schema.go", output_mode="content").get("matches"))
results["task2"] = '"projects"' in read_file("config/meept.json5", limit=200).get("content","")
# ... etc for all tasks
```

### Step 2: Deeper Investigation for Borderline Cases

Surface-level grep hits can be misleading. A `search_files` hit for a function name might be an import, a comment, or a stub -- not a real implementation. When a task looks partially done:

1. **Read the actual wiring code**, not just type/function definitions. A function may exist but never be called.
2. **Check call sites**, not just definitions. `search_files` for the function name across the whole codebase to see if it's actually invoked.
3. **Assign a percentage** (0/50/85/100) rather than binary done/not-done. This surfaces the "implemented but not integrated" gap.

**Pitfall: Overestimating incompleteness.** A task can look 30% done on surface grep but be 90% done on deeper inspection. Example: "scope context to project path" looked incomplete because `SetWorkingDir` wasn't called from session binding -- but `resolveWorkingDir()` was already wired into both system prompt builders at the correct locations. Only cache invalidation on switch was missing. Always read the wiring before concluding something isn't done.

**Pitfall: Underestimating incompleteness.** Conversely, a task can look 100% done on surface grep but have real gaps when a fresh review subagent reads the actual files. Example: Task 14 "/project slash commands" looked complete because `executeProject` existed with 5 subcommand handlers -- but `/project set` was missing from the switch statement and the help text didn't list it. Only a subagent that read the full switch statement caught it. Surface-level `search_files` for "executeProject" returned hits and looked done.

### Step 3: Present Completion Chart

Show the user a phase-by-phase chart with percentages before dispatching. This lets them confirm your assessment and prioritize.

### Step 4: Dispatch Only Incomplete Tasks

Skip 100%-complete tasks. For partially-complete tasks, include what's already done in the subagent context so it doesn't re-implement.

### Pitfall: git add -A commits node_modules after subagent npm install

When a subagent runs `npm install` as part of a React/dashboard build, and the parent then does `git add -A` to commit the subagent's work, thousands of node_modules files get committed. The .gitignore may not exist yet.

**Real instance:** `git add -A && git commit` committed 5,441 files (all of node_modules/) in a single commit. Fixing this with `git rm -r --cached web/node_modules` was then BLOCKED by the pre-commit hook because the working tree was mid-cleanup.

**Prevention:** Always create the `.gitignore` BEFORE dispatching any subagent that runs npm/yarn/pnpm install. Add `node_modules/`, `dist/`, and `*.tsbuildinfo` to the project-level or directory-level `.gitignore` before any `git add -A`.

**Recovery if it happens:** `git rm -r --cached <dir>` with `--no-verify` flag on the commit, or temporarily disable the hook.

### Pitfall: Pre-commit hook blocks cleanup commits

After installing a pre-commit hook (via `make hooks`), any `git commit` — including cleanup operations like `git rm -r --cached node_modules` — must pass the full hook chain (build, vet, fmt, lint). If the working tree is in a partial state during cleanup, the hook blocks the commit.

**Prevention:** Run cleanup operations (removing tracked files that shouldn't be tracked) BEFORE installing the pre-commit hook, or use `git commit --no-verify` for cleanup-only commits.

## Remember

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
Maximize parallelism -- batch in 3s
Batch sequential tasks into single subagents
Pre-read API surfaces + embed signatures in context for integration/wiring tasks
Flag frozen types explicitly -- subagents must adapt, never modify
Map dependency graph into waves before dispatching multi-task lists
go fmt BEFORE commit (every time)
Verify tests after subagent fixes
Check max-iteration summaries for leftover work
Status-check before resuming a plan -- don't re-dispatch done work
Verify plans with parallel review subagents -- never trust cached assessments
Pre-read files before dispatching fix subagents -- context in > iterations out
Close gaps in parallel after verification finds them
After a review phase, the files are already loaded -- apply surgical fixes directly rather than dispatching re-reading subagents (avoids 429 + shared-file collisions)
Create .gitignore BEFORE dispatching subagents that run npm install
Run cleanup commits BEFORE installing pre-commit hooks
Worktree dispatch: git worktree add → LFS settle → context-gather from worktree paths → delegate_task with absolute worktree paths

For Go projects: the JSON tag pitfall -- Go JSON does NOT auto-match snake_case to CamelCase without explicit tags. Fields consumed by LLM-generated JSON MUST have `json:` tags. See references/adversarial-test-infrastructure.md

Pattern summaries (append to remember):
- ID-derived fake coords → spatial collisions at 50 units for same-location candidates; fix: pass cluster key directly to centroid, not from IDs
- Dispersed entities must nil members map after Tick() → otherwise ghost entities persist forever in Manager.prune()
- Per-alignment crowd entities: band split ±0.3 on political axis, O(1) per entity, cross-band tension for opposing groups
- Crowd tick injection: Phase N+0.5 between SCHEDULE and MEMORY_DECAY so dispersed NPCs' gossip is available before perception
```

**Quality is not an accident. It's the result of systematic process.**
