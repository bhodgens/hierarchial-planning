---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks. Dispatches fresh delegate_task per task with two-stage review (spec compliance then code quality).
version: 2.0.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [hierarchical-planning, hierarchical-plan-execution]
---

# Subagent-Driven Development

## Overview

> Shared model and write-path policy: references/plan-tree-canon.md (C1-* sections). Read once; this skill assumes it.

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

**For features too large for one agent's context:** use `hierarchical-planning` to create a plan tree and `hierarchical-plan-execution` to execute it. Those skills own the tree structure, orchestrator/reviewer split, and per-leaf dispatch. This skill covers flat, per-task execution.

## When to Use

- You have an implementation plan (from writing-plans or user requirements)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

vs. manual execution: fresh context per task (no accumulated-state confusion), review catches issues early, consistent quality checks, and subagents can ask questions before starting.

**Delegation cap timed out at the subagent limit?** Tasks spanning two language trees (e.g. Go sidecar + Godot project) MUST be split into parallel single-half dispatches with the shared schema pinned in both briefs: `references/delegation-size-limits-and-splits.md`.

## When NOT to Delegate

- Leaf is small (3-5 files, types/config, no logic) and the spec is already loaded: write directly (~2 min vs 6+ min dispatch cycle; if the TDD cycle is under 5 tool calls, do it yourself).
- Pure writing task under ~600 lines with source material loaded: write directly (writing subagents time out on generation speed alone).
- Benchmark/measurement runs babysitting servers: run in the parent session via background terminal.
- After two failed dispatch rounds on the same task: finish in-session from the salvage. Details: `references/timeout-and-rate-limit-recovery.md`.

## The Process

### 1. Read and Parse Plan

Verify the plan file exists at the given path (wrong directory, typo, stale reference are common). Read it ONCE and extract ALL tasks with full text and context upfront; create a todo list.

Key: never make subagents read the plan file - provide the full task text in their context.

### 2. Per-Task Loop

For each task: dispatch implementer, then two-stage review, then mark complete.

**Implementer dispatch** follows canon C1-Dispatch (`delegate_task` batch shape; full brief in `context`; brief includes the task text, project context, and the TDD cycle: failing test, verify FAIL, minimal implementation, verify PASS, full suite). Include "Do NOT commit" - commits are orchestrator-owned per C1-Commit. For integration/wiring tasks, pre-read API surfaces and embed exact signatures: `references/pre-dispatch-checks.md`. Prompt shapes: `references/example-workflow-auth.md`.

**Stage 1 - spec compliance review.** Verify the output against the original spec, in-session per canon C1-Review (never delegated: reviewers inherit the subagent model that wrote the code; review by the main model). Checklist: all spec requirements implemented, file paths/signatures/behavior match, nothing extra added. Output: PASS or a list of specific gaps. Fix gaps and re-review; continue only when PASS.

**Stage 2 - code quality review.** Only after spec passes. Checklist: project conventions, error handling, naming, test coverage, bugs/edge cases, security. Output: Critical (must fix) / Important (should fix) / Minor issues plus a verdict APPROVED or REQUEST_CHANGES. Fix and re-review; continue only when APPROVED.

Never start quality review before spec compliance passes; never move to the next task with open review issues.

### 3. Final Review and Commit

After ALL tasks pass: run the full test suite yourself, review the complete diff, dispatch one final integration reviewer (components work together, no inconsistencies, tests passing). The orchestrator then commits per C1-Commit (stage exact paths; see `references/shared-repo-git-discipline.md` for concurrent-writer rules).

## Verify Every Subagent Report

A completion summary is a CLAIM, not evidence. After EVERY code subagent returns: `ls` every claimed file, `grep` every claimed symbol, run the build yourself, run new tests with `-v`. A green build is necessary, not sufficient; a "completed" status can mean zero work (503), partial work (timeout/max-iterations), or fabrication. Full protocol and sub-cases: `references/verify-subagent-self-reports.md`. Per-return checklist: `references/post-subagent-review.md`.

## Delegation Size Limits

Fresh-subagent-per-task does not mean unlimited scope. Subagent ceilings (context, ~25-minute wall clock, tool-call caps) are canon C1-Sizing; split at seams. Observed limits: ~6K lines read+fix reliable, ~10K risky, ~47K will time out; 6-8 new files reliable, 10-13 risky; audit-only reads tolerate more.

Timed-out or 429-failed dispatches: salvage partial work from disk before re-dispatching, split scope, serialize on rate limits - `references/timeout-and-rate-limit-recovery.md`. Splitting multi-language tasks: `references/delegation-size-limits-and-splits.md`.

## Dispatch Shapes

Pick the shape from the dependency graph - full patterns in `references/dispatch-shape-catalog.md`:

- Independent tasks: parallel batch, one fresh subagent per task (canon C1-Dispatch).
- Linear chain (B needs A, C needs B): one subagent per chain, numbered steps.
- Cross-task dependencies: wave analysis - Wave 1 independent, Wave 2 consumers; stub-first wiring keeps the tree green between waves.
- User says "worktree" or true repo isolation needed: git worktree per leaf, absolute worktree paths in every brief.
- Codebase-wide audit/fix: survey, group by module, batches of 3, two-phase audit then fix, file-ownership partitioning.
- After a review phase, fixes are usually applied directly (the files are already loaded in your context) - dispatch fix subagents only for large disjoint fixes.

Concurrent-writer hazards (sibling patch corruption, parent races, stale reads, interface drift): `references/concurrency-races-and-file-ownership.md`. Shared-repo git rules: `references/shared-repo-git-discipline.md`.

## Pitfall Registry

1. **Line-number corruption.** TRIGGER: subagent pipes read_file output into write_file. ACTION: forbid the pattern in briefs; assemble via separate files and terminal; strip with sed if it lands. DETAIL: references/verify-subagent-self-reports.md
2. **URL guessing.** TRIGGER: task involves downloading and no manifest was supplied. ACTION: pass URLs from the authoritative manifest in context only. DETAIL: references/pre-dispatch-checks.md
3. **Schema-name collision.** TRIGGER: plan creates DB tables. ACTION: grep existing migrations for every planned table name and rename pre-dispatch. DETAIL: references/pre-dispatch-checks.md
4. **Unverified source path.** TRIGGER: plan ports code from another repo. ACTION: ls every cited path and ask the user if missing before dispatching. DETAIL: references/pre-dispatch-checks.md
5. **Sibling patch corruption.** TRIGGER: patch warns a file was modified by a sibling. ACTION: re-read the file before any further patch; fix corruption with one large patch. DETAIL: references/concurrency-races-and-file-ownership.md
6. **Stale "pre-existing" build errors.** TRIGGER: parallel siblings build in one module. ACTION: treat errors in untouched files as transient; rebuild yourself before believing them. DETAIL: references/concurrency-races-and-file-ownership.md
7. **Parent-subagent write race.** TRIGGER: urge to edit a file a running subagent owns. ACTION: wait; partition strictly; your grep is a snapshot of the past. DETAIL: references/concurrency-races-and-file-ownership.md
8. **Interface signature drift.** TRIGGER: parallel siblings implement a shared interface. ACTION: brief "do not modify foundation signatures"; revert silent changes. DETAIL: references/concurrency-races-and-file-ownership.md
9. **Fabricated completion.** TRIGGER: any code subagent returns. ACTION: ls files, grep symbols, build and test yourself before staging. DETAIL: references/verify-subagent-self-reports.md
10. **Zero-work 503.** TRIGGER: completed status with empty/failed summary. ACTION: grep for the sentinel stubs; salvage or implement in-session, never blind re-dispatch. DETAIL: references/verify-subagent-self-reports.md
11. **Header-only download check.** TRIGGER: subagent reports a downloaded artifact verified by magic bytes. ACTION: compare actual size to expected size first; then load the artifact. DETAIL: references/verify-subagent-self-reports.md
12. **Wrong-repo writes.** TRIGGER: session spans multiple repos. ACTION: absolute output paths in every brief; git status both repos after. DETAIL: references/verify-subagent-self-reports.md
13. **Timeout misread as failure.** TRIGGER: status=timeout. ACTION: salvage pass first (mtimes, symbols, run tests) - partial work is often complete. DETAIL: references/timeout-and-rate-limit-recovery.md
14. **Two-round timeout.** TRIGGER: second delegation round on one task also times out. ACTION: stop delegating; finish the known-remaining pieces in-session. DETAIL: references/timeout-and-rate-limit-recovery.md
15. **429 parallel retry.** TRIGGER: all subagents in a batch hit rate limits. ACTION: retry serially with enriched context; fall back to direct work; never parallelize harder. DETAIL: references/timeout-and-rate-limit-recovery.md
16. **Research-spiral timeout.** TRIGGER: writing subagent told to web-verify a broad topic. ACTION: cap searches, set a line target, or split research from writing. DETAIL: references/timeout-and-rate-limit-recovery.md
17. **Committed-file deletion.** TRIGGER: subagent creates a file whose name already exists. ACTION: pre-check and name the alternative; git diff --name-status | grep ^D after. DETAIL: references/domain-pitfalls-go-npm-sim.md
18. **Go JSON tags.** TRIGGER: struct fields consumed by generated JSON. ACTION: require explicit json: tags in every Go dispatch brief. DETAIL: references/domain-pitfalls-go-npm-sim.md
19. **node_modules commit.** TRIGGER: subagent runs npm install in an ungitted project. ACTION: create .gitignore before dispatching; never git add -A. DETAIL: references/domain-pitfalls-go-npm-sim.md
20. **Embedded-count test break.** TRIGGER: task adds files to an embedded/auto-discovered directory. ACTION: brief the subagent to bump hardcoded count-guard tests in the same change. DETAIL: references/domain-pitfalls-go-npm-sim.md
21. **Concurrent-writer commit.** TRIGGER: git log shows commits you did not make. ACTION: stage only your files by explicit path; verify staged diff before committing. DETAIL: references/shared-repo-git-discipline.md
22. **git add -A on shared repos.** TRIGGER: any commit after parallel subagent work. ACTION: explicit-path staging plus git diff --cached --stat; red trees never commit. DETAIL: references/shared-repo-git-discipline.md
23. **Mock-server masking.** TRIGGER: external-API client tested only via fixtures. ACTION: verify the API contract against live docs pre-dispatch; live dry-run after. DETAIL: references/external-api-contract-verification.md
24. **Contract guessing in same-wave siblings.** TRIGGER: two tasks reference each other's outputs by name. ACTION: pin the contract on disk or verbatim in both briefs before the wave. DETAIL: references/delegation-size-limits-and-splits.md
25. **Brief degradation.** TRIGGER: very long delegate_task context fails schema validation. ACTION: re-dispatch compact, never fix the corrupted text; one verify command per check. DETAIL: references/parallel-dispatch-git-discipline.md
26. **Trusting tracking tables.** TRIGGER: resume or forest-survey asks what is done. ACTION: ground truth via parallel review subagents reading actual code. DETAIL: references/plan-verification-and-resume.md
27. **Surface-grep completion.** TRIGGER: search_files hits look done. ACTION: read wiring and call sites; assign a percentage; a fresh reviewer catches hidden gaps. DETAIL: references/plan-verification-and-resume.md
28. **File-collision fix waves.** TRIGGER: applying review findings via parallel fix subagents. ACTION: partition by file groups, not finding category; or fix in-session post-review. DETAIL: references/dispatch-shape-catalog.md

## Maintenance

> Maintenance: references/skill-maintenance.md (write-path loop, quarterly consolidation, eviction, regression scripts).

New lessons never append to this file. One line goes to `references/INDEX.md`; the full lesson goes in a reference file with a `# title` / `When to use:` / `Lesson:` header. Quarterly consolidation and eviction rules: plan-tree-canon.md C1-WritePath.
