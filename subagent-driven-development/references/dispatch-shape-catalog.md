# Dispatch Shape Catalog: Batching, Granularity, Waves, Worktrees

When to use: deciding how many subagents, how big, how parallel, and in what order for a task list.
Lesson: match dispatch shape to the dependency graph - one fresh subagent per independent task, one subagent per sequential chain, waves for parallel groups, worktrees for true repo isolation - and keep every dispatch inside the size/time limits.

## Task granularity

Each task = 2-5 minutes of focused work. "Implement user authentication system" is too big; "Create User model with email and password fields", "Add password hashing function", "Create login endpoint" are right-sized. This is canon C1-Sizing applied to task lists.

## Batching sequential tasks in one subagent

When tasks have linear dependencies (B needs A, C needs B), dispatch the CHAIN as one subagent rather than one per task - avoids re-reading files and re-establishing context per step.

Pattern: group tasks by dependency chain ([1-2-3] [4-5] [6-7-8]); dispatch each chain as one subagent with numbered steps; the orchestrator verifies build after each subagent returns (and commits, per C1-Commit).

Batch vs separate: batch when tasks modify the same files, share context, or build on each other's output; separate when tasks touch different files, can run in parallel, or one is risky (security-sensitive, complex).

Real instance: an 18-task plan across 9 phases dispatched as 8 subagent calls (three singles in parallel, four chains of 2-3 tasks, two standalone risky tasks) completed in ~15 minutes vs 30+ minutes sequential.

## Dependency-wave parallel dispatch

Map cross-task dependencies into waves before dispatching: Wave 1 = independent tasks (parallel, capped by the user's stated limit or `max_concurrent_children`, whichever is lower); Wave 2 = tasks consuming Wave 1 outputs; continue until covered. Present the wave structure before dispatching so the user can confirm sequencing and catch missing dependencies.

Stub-first variant: when a plan has a wiring task (dispatcher/router referencing symbols not yet created) followed by N parallel implementation tasks, the wiring task ALSO creates minimal stubs (struct + constructor + method returning a not-implemented error) so the package compiles green between waves. Each Wave 2 subagent replaces ONE stub; siblings inherit a green tree - no false-positive missing-symbol errors. Real instance: a dispatcher + 3 stubs in Wave 1, 3 parallel replacements in Wave 2, zero collisions, ~60s per subagent.

Validated batch shape: Wave 1 wiring + stubs, verify and commit green; Wave 2 parallel implementations; verify the merged state (build + tests) before the orchestrator commits.

## Worktree-isolated leaf dispatch

When the user says "do it in a worktree", or leaves should run in parallel without repo conflicts:

1. `git worktree list` - check existing worktrees and naming.
2. `git worktree add ../<repo>-leafNN -b leafNN-description <base-branch>`.
3. LFS repos: `git lfs checkout && git lfs install --force && git lfs pull` in the worktree (creation reports "files that should have been pointers but weren't").
4. Gather implementation context from the WORKTREE paths (leaf spec, conventions, attribution registries), not the main repo.
5. `delegate_task` with ABSOLUTE worktree paths in both `goal` and `context` - subagents default to the session cwd and will otherwise write to the wrong repo.

Why worktrees: leaves run truly in parallel without working-tree conflicts; the main repo stays clean for orchestration and review; each leaf's branch merges independently. Naming example: dir `rebellion-leaf05`, branch `leaf05-foliage`, based from main HEAD.

Context-gathering: read the leaf spec, conventions file, and files the leaf references from the worktree; pre-read key files to embed; batch all reads in parallel.

## Large-scale parallel dispatch (audit/fix)

1. Survey first: file counts per module (`find . -name "*.go" | cut -d'/' -f1-2 | sort -u`).
2. Group by module - each subagent gets ONE module with full context.
3. Batch in groups of 3 (`max_concurrent_children=3`); >3 tasks run in sequential batches.
4. After all subagents finish: run the formatter in EVERY module (pre-commit hooks reject unformatted files), run the full test suite, fix test failures the subagents missed.
5. Respect a user's stated parallelism cap for the ENTIRE session ("max 3 at a time" holds until the user raises it).

## Two-phase large-scale audit

Phase 1, parallel audit (3 subagents): split the codebase by logical domain (core infra / agent system / security-support), explicit file lists in `goal`, project context in `context`, consolidate findings into a prioritized list (critical > high > medium > low).

Phase 2, parallel fix (3 subagents): same domain boundaries so subagents do not conflict; each fix instruction names exact file, location, what is wrong, and the exact fix approach ("add sync.RWMutex to Client.config, use RLock in Chat()") - never "fix the race"; subagents read files fresh before patching; each runs the build after fixes.

Post-fix (parent): format all modules, full tests, fix behavior-change test breakages the subagents missed, stage only changed files explicitly, one descriptive commit.

## File-ownership-partitioned fix dispatch

When applying review findings via parallel fix subagents, partition by non-overlapping FILE groups, not finding category. Category partition ("A fixes all auth bugs") collides when findings span the same files; file partition guarantees zero sibling-modification warnings. Each context names its owned files and the explicit "do NOT touch" sibling list. Validated: a 3-subagent fix wave with explicit ownership, zero collisions, 41 tests green on merged verification.

## Fix-after-review: dispatch vs direct

After a review phase, the orchestrator's context already holds the reviewed files - dispatching fix subagents forces 15-30 re-read calls each, and on rate-limited providers that re-discovery triggers 429s. Apply fixes directly when ALL hold: you reviewed the files yourself, fixes are surgical (known locations), and multiple fixes share infrastructure files. Dispatch fix subagents when: you did not review the files, fixes are large (>200 lines per subsystem), file sets are fully disjoint, or parallelism is needed. Real failure: three parallel review subagents succeeded; three parallel fix subagents on the same boundaries all hit 429 AND edited outside their subsystems - recovery required stashing and redoing serially. The review phase IS the context-loading phase; when in doubt, patch directly.
