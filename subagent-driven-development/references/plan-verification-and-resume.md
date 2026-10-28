# Plan Verification and Resume: Review Subagents, Status Checks, Gap Closing

When to use: verifying a completed plan's implementation, or resuming a plan started in a prior session ("continue implementing").
Lesson: never trust tracking tables or cached assessments - ground truth comes from reading the actual code via parallel review subagents, and a resume dispatches ONLY the genuinely incomplete tasks.

## Plan verification via parallel review subagents

When asked to review a plan for completion/correctness, dispatch 2 parallel review subagents splitting the tasks between them. Each reads the actual implementation files and reports PASS/PARTIAL/FAIL per task with specific evidence (line numbers, actual code found).

Why subagent review beats parent review: full-file reads without polluting the parent's context; deep inspection of each half without time pressure; the parent sees only the structured report; catches gaps surface `search_files` misses (a method that exists but is never called, a struct field missing from a builder).

Critical rule: never trust cached assessments. "Review each file" / "do not assume correctness" means it - the previous session's percentage chart is stale. A task scored 85% might be 100% (wiring you missed) or 30% (a stub that looked real on grep).

## Resuming in-progress plans

"Continue implementing" does NOT mean re-dispatch all tasks. First determine what is done:

Step 1 - systematic status check. Batch `search_files`/`read_file` against every plan task: do the specified files exist, do the specified functions/types appear in them.

Step 2 - deeper investigation for borderline cases. Surface grep is misleading: a hit may be an import, comment, or stub.
- Read the actual WIRING code, not just definitions - a function may exist but never be called. Check call sites across the codebase.
- Assign a percentage (0/50/85/100) rather than binary done/not-done; this surfaces "implemented but not integrated".

Two calibration pitfalls:
- Overestimating incompleteness: a task looked 30% done on surface grep but was 90% done - the wiring helper was already called from both system prompt builders; only cache invalidation on switch was missing. Always read the wiring before concluding something is not done.
- Underestimating incompleteness: a task looked 100% done because the dispatcher function existed with 5 subcommand handlers - but a fresh review subagent reading the full switch statement found one subcommand missing from the switch and the help text. Surface grep returned hits and looked done.

Step 3 - present a phase-by-phase completion chart so the user can confirm the assessment before dispatching.

Step 4 - dispatch ONLY incomplete tasks. Skip 100%-complete tasks; for partial ones, include what is already done in the context so nothing is re-implemented.

## Cross-plan state assessment (forest surveys)

When asked "which plans should be implemented next" across multiple plan trees, do NOT trust tracking tables - they are routinely stale (tables show PLANNED for trees fully implemented in past sessions).

1. Survey: read every tree's `master.md` tracking table in parallel (batch reads) - statuses, PENDING leaves, dependency chains, build order.
2. Ground truth, three complementary signals batched in one turn:
   - Tests: full suite run across ALL packages; green = implemented and functional.
   - Git history: commit messages (`feat(X): implement Y (tree #Z)`, sequential feat/fix chains) tell exactly which trees were implemented and debugged.
   - Filesystem: package directories, C++ file lists, stubbed simulation phases.
3. Cross-reference into a comparison table (tree, plan status, packages exist, test result, git evidence, real status). Common finding: tables show PLANNED for 12/12 trees, code inspection shows 10/12 complete with tests passing.
4. Real gaps = packages/files that do not exist, stubbed phases, leaves never created. Exclude any tree whose code exists and tests pass - COMPLETE regardless of the table.
5. Map remaining gaps to the dependency graph into dispatch rounds (independent groups parallel, dependent groups sequenced).
6. Present: implemented-vs-claimed summary, specific real gaps, recommended rounds in dependency order, context size per dispatch - let the user confirm or reorder before dispatching.

Worked example (14 Go packages, 12 plan trees, 3 parallel dispatches): `references/plan-forest-assessment.md`.

## Gap-closing after verification

When verification finds small independent gaps (a missing UI field, a missing command), dispatch parallel fix subagents to close them all at once - after PRE-READING the target files and embedding specifics in each brief: exact struct definitions, method signatures with current implementations, available client methods, surrounding code patterns. Pre-reading makes subagents spend iterations on writing, not discovering context.
