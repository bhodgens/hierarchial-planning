---
name: hierarchical-plan-execution
description: "Use by default to execute any plan tree created by hierarchical-planning. Main model orchestrates and reviews; subagent model implements leaves. Iterative fix loop until review passes, then orchestrator marks complete with timestamp and completeness percentage."
version: 1.17.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [execution, hierarchical, delegation, orchestrator]
    related_skills: [hierarchical-planning, subagent-driven-development]
---

# Hierarchical Plan Execution

## Overview

Execute plan trees from `hierarchical-planning`: the main model is orchestrator and reviewer; the subagent model (configured in `delegation` settings) implements leaf documents. The orchestrator dispatches implementers, reviews in-session, fixes failures, and marks completion with timestamps and completeness percentages.

Shared model and write-path policy: references/plan-tree-canon.md (C1-* sections). Read once; this skill assumes it.

## MANDATE: Full-Tree Execution ("implement the plan" = implement EVERYTHING)

When the user says "implement the plan", "dispatch the plan", "execute the
tree", or any phrase requesting plan implementation WITHOUT explicitly
limiting scope (e.g. "just leaf 03", "only wave A"), the executing agent
is committed to the ENTIRE tree: every leaf, every branch, every gate,
through final integration and the completion report. This is a
continuation mandate, not a single-turn task.

Specifically, "implement in full" means:

1. Every leaf goes PENDING -> IN_PROGRESS -> REVIEWED -> COMPLETE. No leaf
   is left PENDING when the session ends.
2. The orchestrator does NOT stop after dispatching wave 1, after the
   first leaf commit, or at any natural pause awaiting user input.
   Background dispatches returning counts as continuation triggers, not
   interruptions: on each batch-completion message, immediately review,
   commit, dispatch the next wave, and keep going.
3. Integration gates (build, suites, lint targets defined by the master)
   run at the end, followed by the completion report. NOTHING actionable
   identified during the tree may be left in the report's "remains / next
   steps": a `--no-verify` gate bypass gets its backfill re-check at HEAD
   before close, stale generated artifacts get regenerated at the
   integration gate, and the user's standing directive is "don't defer -
   fix identified issues" (deferring them is treated as a failed close).
   Out-of-scope FEATURE work (new surfaces, product decisions) may be
   offered as a follow-up tree - but executing it starts immediately if
   the user says do it.
4. Stopping early is a FAILURE state requiring explicit user approval.
   The ONLY legitimate stop reasons: (a) a leaf invokes its STOP clause
   with an integration bug the orchestrator cannot resolve in-session,
   (b) the user interjects with changed instructions, (c) a hard
   external blocker (credentials, network, infra) that no workaround
   exists for. In each case: report what stopped, what remains (exact
   leaf list + tracking table state), and what unblocks resumption.
5. If a session must end (context limits, crash), the handoff note must
   carry the tracking table, per-leaf commit hashes, and the exact
   dispatch order - so the next session resumes without re-planning.

The mandate is self-sustaining: dispatch -> review -> commit -> dispatch
next -> repeat until the tracking table is COMPLETE and the completion
report is delivered. A response that ends with leaves still PENDING and
no stop reason above is an incomplete execution of the skill.

**Core principle:** The orchestrator owns all state. Implementation agents are stateless workers that write code and report back. Only the orchestrator commits, reviews, and updates plan documents.

## When to Use

- The user asks to execute a plan tree authored by `hierarchical-planning`.
- A multi-leaf implementation is too large for one agent context and needs dispatch and review cycles.
- A previous session left a tree partially complete and it must be resumed to COMPLETE.

## Execution Loop

1. Read the tree (master + next wave's leaf docs); run the drift audit and record a build/test baseline before each wave.
2. Dispatch each wave per plan-tree-canon.md C1-Dispatch (batch `tasks[]`, per-item goal + context; "Do NOT commit").
3. Review every return in-session per C1-Review (never delegated; max 3 fix iterations; verify do not trust reports).
4. Commit per C1-Commit: orchestrator stages the leaf's exact file list, commits immediately after review (delayed commits are sweep exposure).
5. Update the tracking table per C1-State after every child transition; repeat until the table is COMPLETE; run integration gates; deliver the completion report.

## Pitfall Registry

**Dispatch failures.**
1. **Late-429 silent completion.** TRIGGER: subagent lands work then dies before reporting. ACTION: verify files on disk before re-dispatch. DETAIL: references/pitfall-54-late-429.md
2. **Ghost "completed".** TRIGGER: status=completed but files never landed. ACTION: stat the list; re-dispatch the missing subset. DETAIL: references/pitfall-55-ghost-completed.md
3. **Dispatch-storm 429s.** TRIGGER: many parallel leaves die at once with HTTP 429. ACTION: serial re-dispatch with the ORIGINAL contexts. DETAIL: references/fix-wave-and-429-lessons-2026-09-10.md
4. **Timeout with work done.** TRIGGER: timeout/failed status but all files written. ACTION: verify then salvage; do not redo. DETAIL: references/silent-subagent-failures.md
5. **Stale async reports.** TRIGGER: hours-old delegation returns after in-session completion. ACTION: diff against the tracking table before acting. DETAIL: references/pitfall-55-stale-delegation.md

**Shared-repo races.**
6. **Sibling commit sweep.** TRIGGER: a parallel session sweeps your uncommitted leaf into its commit. ACTION: verify unpushed, stash churn, filter-branch msg rewrite. DETAIL: references/attribution-repair-sibling-commit-sweeps.md
7. **Staged-index sweep.** TRIGGER: a sibling's already-staged file rides your commit. ACTION: audit the staged list; commit with explicit pathspecs. DETAIL: references/staged-index-sweep-and-model-recovery.md
8. **Same-file dual ownership.** TRIGGER: two leaves or trees edit one file in a wave. ACTION: hunk ownership per dispatch context; serialize same-function edits. DETAIL: references/meept-plan-tree-execution-2026-09.md
9. **Branch switched mid-tree.** TRIGGER: commit output shows an unexpected branch. ACTION: never switch back; keep committing, reconcile via cherry-pick at the gate. DETAIL: references/branch-switch-under-running-tree.md
10. **Hook blocks on sibling files.** TRIGGER: pre-commit gate names files you never touched. ACTION: index poisoning - unstage foreign paths; never blind --no-verify. DETAIL: references/pitfall-sibling-commit-sweep-and-scratch-module.md

**Sibling collisions.**
11. **Double dispatch race.** TRIGGER: re-dispatch while the first dispatch still runs. ACTION: check in-flight state; one writer per leaf. DETAIL: references/pitfall-double-dispatch-leaf-race.md
12. **Leaf reverts sibling work.** TRIGGER: leaf writes over a sibling's uncommitted files. ACTION: read-before-write; attribute dirty paths in reports. DETAIL: references/pitfall-leaf-reverts-sibling-work.md
13. **Sibling already wrote the leaf.** TRIGGER: dispatched leaf finds its files already exist. ACTION: verify sibling pre-work against the frozen contract; flag loudly. DETAIL: references/sibling-plan-execution-collision.md
14. **Missing sibling package.** TRIGGER: leaf consumes a sibling's not-yet-landed symbols; build red by construction. ACTION: author to contract signatures; close RED-BUILD-BLOCKED with the unblock condition. DETAIL: references/classi-fly-integration-leaf-2026-09-11.md
15. **Sibling RED test file.** TRIGGER: a sibling's failing test breaks the package build. ACTION: gofmt + LSP filtered to sibling symbols; go build stays authoritative. DETAIL: references/leaf-spec-conflicts-and-sibling-red-build.md

**Verification discipline.**
16. **Wrong failure attribution.** TRIGGER: 3+ consecutive failures blamed on the same external cause. ACTION: dispatch read-only forensics on the newest kept workdir. DETAIL: references/forensic-run-attribution.md
17. **Provider degradation.** TRIGGER: verification leaf fails on 429/503/empty-content rotations. ACTION: diagnose from the kept workdir; escalate cooldowns; keep assertions. DETAIL: references/provider-degraded-verification.md
18. **Port-collision masquerade.** TRIGGER: scratch-daemon symptoms mimic provider faults. ACTION: lsof the fixed ports and remap before blaming providers. DETAIL: references/mlx-local-runtime-2026-09-06.md
19. **Config archaeology.** TRIGGER: quality problem dead-ends at "the model can't follow rules". ACTION: git log -S the config; current config is not a decision record. DETAIL: references/config-archaeology.md
20. **Leaf-doc drift.** TRIGGER: leaf docs name symbols planned earlier. ACTION: grep claims + go doc fields into dispatch contexts before wave 1. DETAIL: references/pre-dispatch-drift-and-baseline.md
21. **Leaf-spec conflicts.** TRIGGER: leaf contract contradicts source or its own tests. ACTION: hand-trace the normative text; adjudicate before implementing. DETAIL: references/spec-test-expectation-mismatches.md
22. **Consent denials propagate.** TRIGGER: a leaf report says a command class was denied. ACTION: accept leaf evidence; never re-attempt the denied class in-session. DETAIL: references/worktree-sweep-and-denial-classes.md

**Provider degradation.**
23. **Fallback-model masquerade.** TRIGGER: green HTTP but wrong verdicts during outages. ACTION: reconstruct which model served each call; shared clients rotate silently. DETAIL: references/fallback-model-masquerade.md
24. **Duplicate background runs.** TRIGGER: stacked cooldown retries fire late on stale binaries. ACTION: kill stale runs; keep script-log-to-workdir numbering explicit. DETAIL: references/duplicate-background-verification-runs.md

**Campaign closeout.**
25. **Parked-commit liability.** TRIGGER: a consent-blocked commit leaves files uncommitted in a shared worktree. ACTION: re-attempt once per user touchpoint; twice-denied, hand over the manual command. DETAIL: references/parked-commit-reattempt-protocol.md
26. **End-of-campaign sweep.** TRIGGER: the user says "commit" after a long campaign. ACTION: sweep the worktree for YOUR unparked work; verify old shas survived repairs. DETAIL: references/worktree-sweep-and-denial-classes.md
27. **Per-leaf cleanliness.** TRIGGER: `git status -s` shows leaf files after its commit. ACTION: commit the remainder immediately tagged with the SAME leaf. DETAIL: references/campaign-2026-09-09-openbot-parity.md
28. **Stale tracking tables.** TRIGGER: table state diverges from disk or branch state. ACTION: audit table vs commits before resuming. DETAIL: references/stale-tracking-table-audit.md
29. **Long-campaign reporting.** TRIGGER: the user loses the thread across runs and trees. ACTION: answer with a state table (live processes, per-fix verdicts, parked decisions). DETAIL: references/campaign-progress-state-tables.md

## Escalation

- Start with references/INDEX.md: one line per reference file (trigger plus lesson). Scan it when a symptom matches a trigger.
- Grep references/ directly when you already know the campaign name or the INDEX line is too coarse.
- Nothing matches? Record a new lesson per plan-tree-canon.md C1-WritePath.

## Maintenance

> Maintenance: references/skill-maintenance.md.

Per plan-tree-canon.md C1-WritePath: never append dated entries to this file; new lessons go one line in references/INDEX.md plus a reference file with the `# title` / `When to use:` / `Lesson:` header. Quarterly consolidation merges related incident files; unfired references are evicted. Shared model and write-path policy: references/plan-tree-canon.md (C1-* sections).
