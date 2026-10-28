---
name: hierarchical-planning
description: "Use when creating implementation plans for features too large for one agent. Produces a tree of markdown documents: leaves fit one agent's 128K context. Orchestrators dispatch implementation agents and review in-session (main model), not via delegated subagents."
version: 1.4.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [planning, hierarchical, multi-agent, delegation, implementation, tree]
    related_skills: [writing-plans, hierarchical-plan-execution, subagent-driven-development]
---

# Hierarchical Planning

## Overview

> Shared model and write-path policy: references/plan-tree-canon.md (C1-* sections). Read once; this skill assumes it.

Create implementation plans as a tree of markdown documents designed for concurrent multi-agent execution. Each leaf document contains at most one agent's worth of work (128K context). Branch and root documents orchestrate their children: dispatch, review, re-dispatch, and track completion.

## Leaf sizing - the delegation budget

Pitfalls (dispatch discipline, scratch-daemon rig, MLX training):
references/pitfall-13-rate-limits.md

Subagents are wall-clock capped (`delegation.child_timeout_seconds`, this
user: 1800 s). A leaf a single subagent cannot FINISH (write + test +
verify) inside ~25 minutes is killed mid-implementation - the model is
rarely the constraint; the stopwatch is. Measured on tree 30
(water/shores/swim): dual-language leaves (Go + GDScript, 4+ files)
reliably timed out; single-language leaves with 3 or fewer files fit.

**Rules:**
1. One leaf = one language where possible (Go-only or GDScript-only).
2. 3 or fewer files of change per leaf. More: split into sibling leaves with the
   interface (schema, function signatures) pinned in each brief.
3. Dual-language leaves MUST be authored as two dispatchable halves, each
   self-contained: pin the shared schema (exact JSON keys / record shape)
   in BOTH briefs so the halves meet without coordination.
4. If a leaf times out anyway: audit `git status` for surviving partial
   work, then re-dispatch ONLY the missing half or finish in-session.
   Never blindly re-dispatch the whole leaf.
5. When a tree plans leaves near the 25-minute mark, recommend the user
   raise or remove `delegation.child_timeout_seconds` (framework default
   is NO cap; stuck-child protection is heartbeat-based, not a stopwatch).

**Core principle:** A plan tree where every node is self-describing. Each document contains its own dispatch and review instructions. Any agent reading a node knows exactly what to do without external context.

## Skill Package Contents

When you load this skill, these files are available. Access them with `skill_view(name='hierarchical-planning', file_path=...)`:
- **`templates/leaf-template.md`** - starter for leaf documents
- **`templates/master-template.md`** - starter for orchestrator/master documents
- **`references/INDEX.md`** - one-line routing table for every reference file

**Scripts (run directly):**
- `scripts/check_template_compliance.py` - structural compliance scan. Run AFTER authoring the whole tree and BEFORE dispatching agents: `python3 scripts/check_template_compliance.py <plans-root> --strict-leaves`
- `scripts/check_plan_tree.py` - structural completeness check (every referenced child exists)
- `scripts/batch_leaf_generator.py` - bulk leaf generation for 10+ leaf trees: edit the `all_leaves` list, run `python3 scripts/batch_leaf_generator.py plans-dir/`, then run the compliance scanner

The tree enables N implementation agents to work concurrently while orchestrators wait, review, and assemble. Status trickles up: children report to parents, parents report to grandparents, until the root confirms full completion.

Example tree:
```
master.md  (root orchestrator: dispatches, reviews, tracks)
  |- 01-auth.md           (leaf: one agent implements all tasks)
  |- 02-data-model.md     (leaf: one agent implements all tasks)
  `- 03-ui/
       orchestrator.md    (branch: dispatches its own children)
         |- 01-components.md  (leaf)
         `- 02-pages.md       (leaf)
```
6 documents, 6 agents: 1 root (waits), 2 leaf workers at top level, 1 branch (waits), 2 leaf workers under the branch.

## When to Use

Use when:
- Feature scope exceeds what one agent can implement in 128K context
- Multiple subsystems can be built concurrently
- You want to maximize parallelism across small models/agents
- The work has natural architectural seams (modules, layers, packages)

Don't use for:
- Single-agent features (use writing-plans instead)
- Sequential-only work with no parallelism possible
- Prototypes/spikes where structure overhead exceeds value

However, when in doubt, default to this skill. A trivial tree (master.md
+ one leaf) has negligible overhead and the structure scales if scope grows.
If during planning you find the tree has only one leaf with no sub-branches,
consider collapsing to a flat writing-plans plan instead.

## The 128K Rule

**Hard requirement: no leaf document describes more work than one agent can implement in 128K context.** This must not compromise code quality - split along architectural seams, never mid-class or mid-module. Shared sizing model: plan-tree-canon.md C1-Sizing.

### Context Budget Breakdown

A 128K agent working a leaf document consumes context on:

| Category | Tokens |
|----------|--------|
| System prompt + tool definitions | ~10K |
| Leaf document (the spec itself) | ~5K |
| Code exploration (reading existing files) | ~15-25K |
| Code generation (writing new/modified files) | ~20-40K |
| Build/test/review iteration (TDD cycles) | ~15-25K |
| Reasoning overhead | ~10K |
| **Total typical** | **~75-115K** |

### Practical Leaf Sizing Limits

- Touch no more than 15-20 files (read + write combined)
- Produce no more than 3,000-5,000 lines of new/modified code
- One cohesive subsystem, feature, or layer
- Completable in one agent session without context overflow

### When to Split

When a leaf would exceed limits, split - but ONLY along architectural seams:
- Module boundaries
- API contracts
- Layer separations
- Feature independence

**Never split a cohesive unit into two tightly-coupled leaves.** Instead, promote it to a branch with sub-leaves. Coupling between leaves kills concurrency benefits and creates integration failures.

If you find yourself needing to split a single class or function across documents, the leaf is the wrong size - make it a branch and decompose along internal responsibilities.

## Document Types

Node roles (what belongs in each): plan-tree-canon.md C1-Nodes.

### 1. Root (master.md)

The top-level orchestrator. Contains:
- Project goal and architecture overview
- Interface contracts between ALL children (shared types, APIs, conventions)
- Child document index with dispatch instructions
- Completion tracking table (updated as children report)
- Integration review plan

### 2. Branch (orchestrator.md)

An intermediate node. Same structure as root but scoped to one subsystem. Contains:
- Subsystem goal and design
- Interface contracts between its children
- Child document index with dispatch instructions
- Completion tracking table

### 3. Leaf (implementation)

Terminal node. Contains:
- Complete task specifications (bite-sized, TDD, exact file paths, complete code)
- Interface contract section (what this leaf exposes to siblings)
- Dependencies on other leaves/branches
- Self-verification checklist
- Review checklist for the review agent
- No further children

## Tree Structure and Naming

```
plans/feature-name/
  master.md                       # root orchestrator
  01-authentication/
    orchestrator.md               # branch (auth is too big for one leaf)
    01-jwt-token.md               # leaf
    02-session-store.md           # leaf
  02-data-model.md                # leaf (fits one agent)
  03-api/
    orchestrator.md               # branch
    01-rest-handlers.md           # leaf
    02-graphql-resolvers.md       # leaf
    03-websocket-server.md        # leaf
```

Rules:
- Each directory has exactly one orchestrator (`master.md` at root, `orchestrator.md` at branches)
- Leaves are numbered for dispatch ordering and dependency clarity
- Branch directories group related leaves under their orchestrator
- Tree depth should rarely exceed 3 levels
- Directory names are descriptive, not generic

## Planning Process

### Step 1: Decompose by Architecture

Identify natural subsystem boundaries. For each subsystem, ask:

"Can one agent implement this end-to-end in one session (128K context, single tool budget) without running out of context or iterations?"

- **Yes** -> leaf document
- **No** -> branch directory, decompose further

Map dependencies between subsystems. Identify which can run concurrently (no dependencies) and which are sequential.

### Step 2: Define Interface Contracts

For each branch and root, define the contracts between its children:
- Data structures shared across children
- API/function signatures
- Event/message formats
- File path and naming conventions

Contracts are the integration surface. Ambiguous contracts = integration failures. Write them as actual type definitions or interface specifications, not prose. Full rules: `references/pitfall-3-interface-contracts.md`.

### Step 3: Estimate Context Budget for Each Leaf

For each proposed leaf:

1. **Exploration cost:** Count files the agent must read. Tokens = total lines / 3.5
2. **Generation cost:** Estimate new/modified lines from the task specs. Same ratio.
3. **Iteration cost:** ~3x single test/build run for TDD cycles
4. **Overhead:** ~15K tokens (system prompt, reasoning, tool I/O)

Total = exploration + generation + iteration + overhead.
If total > 110K -> must split further. If total < 30K -> consider merging with a sibling.

### Technique Selection (decomposition alternatives)

| Pattern | When to use | Reference |
|---|---|---|
| Standard decomposition (Steps 1-7) | New code with natural subsystem seams | this section |
| Audit-driven decomposition | Existing doc corpus (GDD/spec) with known findings; decompose by problem class | `references/forest-authoring-steps.md` |
| Gap-analysis forest | External report (competitor analysis, feature comparison) to triage then build | `references/gap-analysis-forest-pattern.md`, `references/gap-analysis-forest-pattern.md` |
| Capability-gap tree | "Product X can do Y that we can't" - two-sided source-anchored comparison first | `references/gap-analysis-forest-pattern.md` |
| Codebase-review forest | Remediation plans from a review session; date-prefixed dirs | `references/pitfall-35-date-prefixed-trees.md` |
| Ops & asset pipeline tree | Agents run shell/API/downloads, not code; manifest.json tracking; verify files-exist not tests-pass | `references/asset-pipeline-plan-pattern.md` |
| Frontend dashboard tree | React/Vite SPA embedded in a backend binary; foundation-first + stub-first contracts | `references/frontend-dashboard-plan-pattern.md` |
| Forest authoring (5+ trees) | Many trees at once: SHARED-CONVENTIONS.md + OPEN-QUESTIONS.md siblings, inline-leaf default, naming, Q&A walkthrough | `references/forest-authoring-steps.md`, `references/multi-tree-forest-pattern.md` |
| Research-gated tree | Project feasibility unproven (novel hypothesis, unverified APIs); spike leaf gates adapter branches | `references/research-gated-plan-trees.md` |
| Porting from reference impl | Sibling codebase is the spec; freeze reference constants verbatim | `references/porting-from-reference-implementation.md` |
| Multi-source authoring | Direction doc (not literal) + vendor research + codebase | `references/forest-authoring-steps.md` |
| Authoring from task brief | "Per the context" briefs; recover context, then author | `references/forest-authoring-steps.md` |
| Domain-specific patterns | Compliance subsystem, standalone library, live service, processor-abstraction layer, Go background processors | `references/research-gated-plan-trees.md`, `references/porting-from-reference-implementation.md`, `references/research-gated-plan-trees.md`, `references/research-gated-plan-trees.md`, `references/tests-first-gate.md` |

### Step 4: Write Orchestrator Documents

Use `templates/master-template.md` as the starting point. Key sections:
- Goal and architecture (brief - children have their own details)
- Interface contracts (precise - this is the integration surface)
- Child index with estimated context and dependencies
- Dispatch protocol (embedded instructions for the executing agent)
- Completion tracking table
- Integration review plan

### Step 5: Write Leaf Documents

Use `templates/leaf-template.md` as the starting point. Each leaf:
- Starts with a DISPATCH INSTRUCTION header (tells any agent to implement it)
- States parent, scope, dependencies, estimated context
- Contains complete tasks in the same bite-sized TDD format as writing-plans
- Ends with self-verification AND review-agent checklists
- Tasks are authored in spec dialect (canon C1-Dialect): imperative, no narration. Each user requirement carries a Req ID resolving in the master's Requirement Traceability table (canon C1-Trace).
### Step 5.5: Write Test-Gate Leaves (mandatory for code trees)

Every code branch gets test leaves (`00T-`/`01T-` naming, default one per
implementation leaf) implementing the FULL unit + e2e suite for every planned
feature BEFORE any implementation leaf dispatches. Each orchestrator carries
a `## Test Gate` coverage matrix (feature -> unit test -> e2e test ->
status). Implementation may run in parallel ACROSS branches but never prior
to its own branch's tests reaching TESTS_VALIDATED. The test implementer's
control agent (orchestrator, main model, in-session) validates tests against
the plan; on any delta the LESSER artifact is updated to reflect the GREATER
(coverage converges upward). Full recipe: `references/tests-first-gate.md`.

### Step 6: Verify the Tree

Check every item:
- [ ] Every leaf estimated at 110K context or less
- [ ] No leaf splits a cohesive class/module across documents
- [ ] Every branch/root has explicit interface contracts
- [ ] Every document has embedded dispatch/review instructions
- [ ] Dependency graph has no cycles (draw it if unsure)
- [ ] Concurrent leaves identified for parallel dispatch
- [ ] Tracking tables present in all orchestrator documents
- [ ] Every code branch has test-gate leaves + a `## Test Gate` coverage matrix (Step 5.5)

**Run the structural compliance scan** (never verify by memory). Headings must
match the scanner's EXACT strings - required list in
`references/compliance-headings.md`.

```
python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py plans/feature-name --strict-leaves
```

Re-run until `ALL TREES COMPLIANT: True`; the script reports missing required
sections per document. Scanner blind spots (flat trees, inline leaves, forest
roots): `references/plan-authoring-verification.md`,
`references/plan-authoring-verification.md`,
`references/forest-root-scanner-compliance.md`.

### Step 7: Save and Offer Execution

```
mkdir -p plans/feature-name
# Write all documents
git add plans/feature-name/
git commit -m "docs: hierarchical implementation plan for [feature]"
```

Offer: "Plan tree saved at plans/feature-name/. To execute, use the `hierarchical-plan-execution` skill - it dispatches the root orchestrator, fans out implementation agents, reviews with the main model, and marks completion hierarchically. Shall I proceed?"

## Commit Policy

**Only orchestrators commit. Implementation agents must NOT commit.** (Shared model: plan-tree-canon.md C1-Commit.)

The flow (rationale and full rule: plan-tree-canon.md C1-Commit):
1. Implementation agent writes code and tests, runs them locally to verify, reports results - but does NOT commit.
2. Review agent checks the implementation against spec + contracts.
3. Orchestrator commits ONLY after review passes: stages the specific files from that leaf, uses a descriptive message referencing the leaf document.
4. Integration commits (after all children in a branch pass) are also made by the orchestrator.

Instruct every implementation agent in its dispatch context: "Do NOT run git commit. Do NOT run git add. Write code, run tests, report results. The orchestrator handles all git operations."

## Dispatch Protocol (Embedded in Orchestrator Documents)

Every orchestrator document contains these instructions for the executing agent. Batch shape and schema rules: plan-tree-canon.md C1-Dispatch.

### For Each Child Document:

**0. Test Gate (code branches only - runs BEFORE any implementation dispatch)**
- Dispatch test-gate leaves (Step 5.5) as subagents. Brief: "Write tests ONLY, no implementation. Tests must fail RED for missing-implementation reasons. Do NOT commit."
- The control agent (orchestrator, main model, IN-SESSION - never delegated) validates returned tests against the coverage matrix. On any delta, the LESSER of plan/tests updates to reflect the GREATER (coverage converges upward; test deletion needs written rationale).
- When every matrix row is VALIDATED: commit the gate tests, mark the branch TESTS_VALIDATED. Implementation leaves then dispatch - parallel across validated branches, never before their own gate. Recipe: `references/tests-first-gate.md`.

**1. Dispatch Implementation Agent**
- Read the child document
- Dispatch via `delegate_task` with the child document as context
- **delegate_task call shape:** per canon C1-Dispatch; both failure modes diagnose schema before retry.

  `tasks: [{goal: <one-line imperative>, context: <full leaf brief: leaf path, pinned contracts, do-not-commit, corruption rule, exact verify commands>}]`
- Include the interface contracts from the orchestrator
- Include: "Do NOT commit. Do NOT run git add. Write code, run tests, report results only."
- Agent implements all tasks in the leaf using TDD

**2. Review Implementation** (after implementation returns)
- The orchestrator (main model) reviews in-session, NOT via a delegated subagent.
- Rationale: `delegate_task` children inherit `delegation.model`. If a delegation model is set (local profiles), a delegated reviewer uses the same subagent model that wrote the code. The main model must review (plan-tree-canon.md C1-Review).
- Read the changed files, verify interface contracts, run tests, check for artifacts.
- See `hierarchical-plan-execution` skill for the full in-session review procedure.
- On local-model setups where the main model is much stronger: this is especially critical (see `local-ravenx-review-pipeline` skill for the rationale).

**3. Re-dispatch if Incomplete**
- If review identifies gaps -> re-dispatch implementation with specific feedback
- Re-review after re-dispatch
- Loop until review passes (set a max iteration count - 3 typically)

**4. Commit** (after review passes)
- Orchestrator stages the leaf's specific files: `git add <exact file paths from leaf>`
- Orchestrator commits: `git commit -m "feat(scope): implement [leaf name]"`
- Update the tracking table: status -> REVIEWED

**5. Record Status**
- Update the tracking table in the orchestrator document
- The PARENT determines completion - never the child

Duplicate/lost-dispatch recovery + leaf-errata protocol: see `references/wave-execution-patterns.md`.

### Concurrency Rules

- Hermes `delegate_task` concurrency is configurable via `delegation.max_concurrent_children`
  in config.yaml (default 3, can be raised to 6+ with `hermes config set
  delegation.max_concurrent_children 6`). Batch independent leaves up to the
  configured cap for maximum throughput.
- Sequential dependencies: wait for prerequisite to reach COMPLETE before dispatching
- Maximize parallelism - dispatch all independent leaves immediately
- When dispatching mixed work types (implementation + review + research),
  use the higher cap - a review subagent is lightweight and won't compete for
  the same resources as an implementation agent.

## Review Protocol - Orchestrator In-Session

Review happens at EVERY level, performed by the orchestrator (main model)
in-session - NOT via delegated subagents (plan-tree-canon.md C1-Review). See
`hierarchical-plan-execution` skill for the full rationale and review procedure.

### Dual-Track Review for Plan Trees

When you need to verify a plan tree before executing it, dispatch TWO types
of review subagent IN PARALLEL (not serial - they check different things):

1. **Coverage reviewer:** Reads every leaf document against every source audit
   finding. Confirms every finding has an assigned leaf. Flags orphan findings.
   Output: list of gaps (findings not addressed by any leaf).

2. **Compliance/template reviewer:** Reads every document against the
   hierarchical-planning template requirements. Checks each branch for
   Dispatch Protocol, Interface Contracts, Review Checklist, Coding Conventions,
   Completion Tracking Table, Integration Test Plan. Checks each leaf for
   "Do NOT commit", Self-Verification Checklist, and proper task structure.
   Output: list of structural issues with file:line references.

Fix issues from BOTH before dispatching implementation agents.

### Post-Authoring Verification Tiers

| Tier | Technique | Catches | Reference |
|---|---|---|---|
| 1 | Structural compliance scan | Missing/misspelled required sections | `references/compliance-headings.md` |
| 2 | Contract-verification digests (read-only subagents per spec slice) | Paraphrase-drift: frozen contract values contradicting the source spec (Pitfall 21) | `references/contract-verification-digests.md` |
| 3 | Changelog-review digest (one subagent over changelog + recent commits) | Design drift from sibling sessions AFTER authoring (Pitfall 22) | `references/changelog-review-digests.md` |
| 4 | Post-authoring audit trio (citation drift + architecture feasibility + domain ambiguity) | Dead seams, unwired mechanisms, drifted file:line anchors | `references/post-authoring-audit-trio.md`, `references/pre-execution-feasibility-and-citation-audits.md`, `references/pre-execution-feasibility-and-citation-audits.md` |

Tier 2 is highest-value when the plan defines frozen wire types/shared structs consumed by multiple trees, translates prose into concrete types, or invents threshold bands "derived from the spec narrative". Skip for single-tree plans with trivial or verbatim-copied contracts. Prose-quality checks beyond headings: `references/plan-authoring-verification.md`.

## Plan Reconciliation

Plan trees are NOT static. External work (a changelog-driven session, a parallel agent team, a human developer) can execute some or all leaf tasks independently before the plan tree runs. When you return to a plan tree after external work, reconcile before dispatching.

### Pre-Work: Changelog Drift Check

Before reconciling or dispatching any plan tree, apply the changelog-drift check from the `design-plan-consistency` skill (Rule 2):

1. Read the project's changelog.
2. Read the Implementation Record for the plan tree.
3. Cross-reference changelog entries since the tree's last verification date against the tree's design-spec sources.
4. If any entry touches a spec source -> the plan needs updating first.

This catches the case where the *design* moved while you were away, even if no *code* was written.

### Reconciliation Process

**Step 1: Verify leaf state against reality.** For each leaf, check whether its intended outputs exist on disk. Use `find`, `search_files`, or `stat` - do not guess.

**Step 2: Classify each leaf:**

| Classification | Meaning | Action |
|---|---|---|
| SUPERSEDED | All intended work was done externally | Mark COMPLETE in tracking table, add note |
| PARTIALLY SUPERSEDED | Some work was done externally, some remains | Update leaf tasks to cover only remaining work |
| STILL_NEEDED | No external work touched this leaf | Dispatch as normal |
| BLOCKED | External work created a dependency or conflict | Report to user, add note |

**Step 3: Update the tracking table** with new statuses and a reconciliation note.

**Step 4: Add a reconciliation note** to each updated orchestrator doc, referencing the source of the external work.

**Step 5: Adjust phase ordering** if external work completed early phases; update the master.md's dispatch protocol.

**Step 6: Commit.** The orchestrator commits the reconciliation changes. Changelog file format convention: `references/changelog-review-digests.md`.

### Subagent-Driven Reconciliation (efficient shape)

1. Dispatch a reconciliation audit subagent (read-only): reads changelog + every plan leaf + current spec state; produces per-leaf verdicts, stale leaf-text, and tracking-table updates. It does NOT edit files - pure audit, no stale-read risk (Pitfall 19).
2. Digest the report in-session; do NOT delegate the update decision.
3. Dispatch a reconciliation update subagent (write-only) with explicit instructions - it must NOT re-read the spec or leaves.
4. Update the changelog if any spec edits resulted.

Proven at ~5 minutes wall-clock for 20 leaves against 19 changelog rows.

### Common Reconciliation Patterns

- **Changelog from a parallel session:** verify each leaf against changelog items; mark SUPERSEDED where matched; add follow-up items as new leaf tasks.
- **Partial execution before cancellation:** check file existence AND test results. Don't assume "file exists = work done."
- **Human landed a PR:** run `git diff` from the branch point; if the PR covers a leaf's entire scope, mark SUPERSEDED.

When a leaf is PARTIALLY SUPERSEDED, narrow it to remaining work and add a reconciliation header; never delete the leaf - it documents original scope and the reconciliation decision.

### When to Reconcile

- A changelog, commit log, or status report shows work done that overlaps with plan leaves
- Another session or agent modified files the plan was targeting
- Some time has passed and project state may have diverged
- You're about to dispatch execution and want to skip already-completed work

## Completion Tracking

Status values (canonical table: plan-tree-canon.md C1-Status). The orchestrator's tracking table is the single source of truth for subtree status (C1-State); update after every child transition.

| Status | Meaning |
|--------|---------|
| PENDING | Not started |
| TESTS_IN_PROGRESS | Test-gate leaves dispatched, awaiting validation |
| TESTS_VALIDATED | Gate tests validated by control agent and committed; implementation may dispatch |
| IN_PROGRESS | Implementation agent dispatched, awaiting return |
| IMPLEMENTED | Implementation returned, awaiting review |
| REVIEWED | Review agent passed, no gaps found |
| COMPLETE | Verified, integrated, committed |
| BLOCKED | Cannot proceed (dependency missing, conflict) |

## Execution Backends

The plan tree is backend-agnostic. Two execution modes:

### Direct Dispatch (default)
Use `delegate_task` to fan out leaf agents. Orchestrator waits for returns,
dispatches review agents, commits, and tracks. Multi-session repos: see
`references/concurrent-wave-execution.md`.

### Kanban Board (for durable execution)
Use `kanban_create` to create cards for each leaf, assigned to worker
profiles. Dependency links via `parents=[...]` enforce ordering. Best for:
work spanning multiple sessions, crash recovery, human-in-the-loop gates,
audit trail. See `kanban-orchestrator` skill for the decomposition playbook
and dispatch patterns.

The plan documents are the same either way - only the dispatch mechanism
changes. Orchestrator documents can specify which backend to use in their
Meta section.

## Integration with Existing Skills

| Skill | Relationship |
|-------|-------------|
| design-plan-consistency | Governs WHEN a plan tree should be authored, updated, or marked stale relative to design-doc changes. This skill's Plan Reconciliation Pre-Work is the integration point: run the changelog drift check before dispatching. |
| hierarchical-plan-execution | The default execution engine for plan trees created by this skill. Main model orchestrates and reviews; subagent model implements leaves. |
| writing-plans | Leaf documents use the same bite-sized TDD task format. This skill is the hierarchical wrapper. |
| subagent-driven-development | The dispatch + review loop is the same pattern. This skill adds tree structure and trickle-up. |
| plan | Plan mode produces a single flat plan. This skill produces a tree when one plan is too big. |
| requesting-code-review | Review agents use the same review dimensions. This skill automates the review loop. |
| kanban-orchestrator | Alternative execution backend. Kanban gives durable state, crash recovery, and human-in-the-loop gates. Same decomposition + anti-temptation philosophy. |
| local-ravenx-review-pipeline | On local-model setups, the review agent must be a stronger model than the implementer. This skill provides the review script and enforcement pattern. |
| parallel-report-generation | Same parallel-subagent assembly pattern. Its line-number corruption prevention applies to leaf agents writing code files. |
| godot-game-development | Godot 4 / Summer Engine development patterns. Load alongside when planning a Godot port. |

## Pitfall Registry

Full narratives live in the referenced files. Numbers are stable: any "see Pitfall N" cross-reference resolves here.

1. **Splitting too aggressively.** TRIGGER: a tree of many tiny leaves where fewer suffice. ACTION: split only when the 128K limit forces it; merge any leaf estimated under 30K. DETAIL: references/pitfall-1-2-splitting.md
2. **Splitting along wrong seams.** TRIGGER: one class split across two leaves. ACTION: keep the class whole; split at module/package boundaries only. DETAIL: references/pitfall-1-2-splitting.md
3. **Missing or vague interface contracts.** TRIGGER: branches whose children share types/APIs by prose only. ACTION: write contracts as actual type definitions; update them when they evolve. DETAIL: references/pitfall-3-interface-contracts.md
4. **Orchestrator implementing child work.** TRIGGER: writing code in the orchestrator session. ACTION: stop and dispatch; the only exceptions are 40%+ batch 429 failure (13c) and single-leaf timeout with sufficient context. DETAIL: references/pitfall-4-orchestrator-implements.md
5. **Skipping the review agent.** TRIGGER: marking REVIEWED/COMPLETE without review. ACTION: orchestrator (main model) reviews in-session at every level before any status bump. DETAIL: references/pitfall-5-review-agent.md
6. **Status not trickling up.** TRIGGER: child completion not recorded. ACTION: update the tracking table after every transition; parent determines completion. DETAIL: references/pitfall-6-status-trickle.md
7. **Circular dependencies between leaves.** TRIGGER: leaf A depends on B and B on A. ACTION: extract the shared dependency into a third leaf, or restructure the seam. DETAIL: references/pitfall-7-circular-dependencies.md
8. **Underestimating context budget.** TRIGGER: sizing from generation cost only. ACTION: count exploration (lines/3.5), iteration, and 15K overhead; split above 110K, merge below 30K. DETAIL: references/pitfall-8-context-budget.md
9. **Dispatching leaves one at a time.** TRIGGER: independent leaves dispatched sequentially. ACTION: batch them (default 3, raise `delegation.max_concurrent_children`); serialize only shared-file leaves. DETAIL: references/pitfall-9-batch-dispatch.md
10. **Forgetting to reset status on re-dispatch.** TRIGGER: a leaf re-dispatched after review failure. ACTION: set status back to IN_PROGRESS with a note - never leave IMPLEMENTED. DETAIL: references/pitfall-10-status-reset.md
11. **Leaf agents committing.** TRIGGER: implementation agents running git commit/add. ACTION: every dispatch context says "Do NOT commit"; orchestrator commits after review. DETAIL: references/pitfall-11-leaf-commits.md
12. **Line-number corruption from read_file.** TRIGGER: leaf agents feeding read_file output into write_file. ACTION: inline source snippets in the context; if agents explore, use search_files/cat; write once, never read back; grep `^\s+[0-9]+\|` to verify zero. DETAIL: references/pitfall-12-line-number-corruption.md
13. **Provider rate limits on concurrent dispatch.** TRIGGER: 3+ concurrent leaf agents or any HTTP 429. ACTION: retry failed dispatches individually; for subagent-side 429 use rich-context retry (13a), narrow scope (13b), then direct fallback (13c). DETAIL: references/pitfall-13-rate-limits.md
14. **Inconsistent code conventions across leaves.** TRIGGER: independent leaf agents, no style guidance. ACTION: coding-conventions block in every orchestrator + dispatch context; gofmt/prettier/ruff after integration. DETAIL: references/pitfall-14-15-conventions-artifacts.md
15. **Stray artifacts from leaf agents.** TRIGGER: leaf output review. ACTION: review checklist includes "no debug artifacts, no TODOs, no placeholder values"; grep print/TODO/FIXME. DETAIL: references/pitfall-14-15-conventions-artifacts.md
16. **Heredocs in execute_code fail silently.** TRIGGER: `cat > file << 'EOF'` inside execute_code. ACTION: use write_file for creation, terminal append for concatenation - never heredocs in execute_code. DETAIL: references/pitfall-16-heredocs.md
17. **`grep -c`/`grep -q` zero-match silently aborts && chains.** TRIGGER: git add/commit chained after a verification grep. ACTION: run the check separately, then commit unconditionally (or use `;` / inverted if). DETAIL: references/pitfall-17-grep-exit-code.md
18. **Docs trees: extend the corruption check, drop code-only steps.** TRIGGER: plan tree authors/reconciles .md documents. ACTION: corruption-check glob adds `*.md`; replace tests/build/format with cross-reference resolution. DETAIL: references/pitfall-18-docs-trees.md
19. **Orchestrator patching a subagent-edited file = stale read-state.** TRIGGER: patch/write_file against a pre-dispatch read. ACTION: re-read the whole file in-session first; serialize multi-leaf edits to one doc. DETAIL: references/pitfall-19-stale-read-state.md
20. **Docs trees ship with incomplete orchestrator sections.** TRIGGER: content-focused authoring of doc trees. ACTION: run check_template_compliance.py after the whole tree; fix gaps until ALL TREES COMPLIANT. DETAIL: references/pitfall-20-docs-orchestrator-sections.md
21. **Inventing spec values that contradict the source (paraphrase-drift).** TRIGGER: translating prose specs into frozen structs/thresholds. ACTION: quote the spec verbatim at every frozen contract; dispatch contract-verification digests. DETAIL: references/pitfall-21-paraphrase-drift.md
22. **Design drift between sibling sessions (post-authoring spec movement).** TRIGGER: active changelog or parallel sessions may ratify changes after authoring. ACTION: run a changelog-review digest before execution; mandatory on projects with an active changelog. DETAIL: references/pitfall-22-design-drift.md
23. **Cross-corpus concept replacement (perspective pivot).** TRIGGER: sweeping rename/perspective/cut across the whole corpus. ACTION: 2 parallel read-only digest subagents categorize hits; apply in one verified batch. DETAIL: references/pitfall-23-concept-replacement.md
24. **Pre-implemented trees need audit, not just dispatch.** TRIGGER: a tree was implemented by a parallel agent or prior session. ACTION: dispatch a post-implementation review subagent with the full plan checklist before COMPLETE. DETAIL: references/pitfall-24-preimplemented-audit.md
25. **Subagent timeout leaves partial work on disk.** TRIGGER: delegate_task returns timeout. ACTION: check what landed, build, complete missing pieces in-session; re-dispatch only if broken. DETAIL: references/pitfall-25-timeout-partial-work.md
26. **Go floating-point determinism: two silent failure modes.** TRIGGER: Go leaves ranking/sorting by float scores. ACTION: epsilon comparisons (no exact !=); sort map keys before float accumulation; run -count=10. DETAIL: references/pitfall-26-go-float-determinism.md
27. **Pre-commit lint hooks (U1000) block orchestrator commits.** TRIGGER: strict Go repos with unused code in staged files. ACTION: remove unused code before staging; never rely on //nolint; run staticcheck first. DETAIL: references/pitfall-27-u1000-hooks.md
28. **Subagent code referencing undefined placeholder functions.** TRIGGER: reviewing subagent output. ACTION: compile-check IMMEDIATELY before logic review; fix undefined references first. DETAIL: references/pitfall-28-undefined-placeholders.md
29. **String-based code assembly causes cascading corruption.** TRIGGER: regex/sed function removal or f-string code assembly. ACTION: patch with full verbatim old_string; verify after each edit; write_file if too corrupted; real tabs never in f-strings. DETAIL: references/pitfall-29-string-assembly.md
30. **Survey existing implementation BEFORE decomposing.** TRIGGER: planning against a repo with existing code. ACTION: dispatch a read-only survey subagent first; digest before writing any plan document. DETAIL: references/pitfall-30-survey-first.md
31. **Subagent API key failures require retry with explicit model.** TRIGGER: HTTP 401 on dispatch. ACTION: re-dispatch with explicit model (or auto-retry); parallel-dispatch critical exploration. DETAIL: references/pitfall-31-api-key-retry.md
32. **Run structural compliance scan BEFORE first commit.** TRIGGER: tree authoring complete. ACTION: author everything, scan, fix, re-scan to green, then commit - post-commit fixes make noisy history. DETAIL: references/pitfall-32-scan-before-commit.md
33. **Single-leaf trees skip Interface Contracts and Architecture Overview.** TRIGGER: trivial-scope authoring. ACTION: include every required section; document what the leaf exposes. DETAIL: references/pitfall-33-single-leaf-sections.md
34. **Compliance scanner requires exact heading "Integration Test Plan".** TRIGGER: writing orchestrator sections. ACTION: use the exact heading; no "Integration Review Plan" variants. DETAIL: references/pitfall-34-integration-test-plan-heading.md
35. **Codebase review sessions produce date-prefixed plan trees.** TRIGGER: review-driven remediation planning. ACTION: YYYYMMDD-prefixed dirs under docs/plans/, one tree per theme, plus an index doc. DETAIL: references/pitfall-35-date-prefixed-trees.md
36. **Compliance scanner requires exact heading "Completion Tracking Table".** TRIGGER: writing orchestrator sections. ACTION: include "Table" - bare "Completion Tracking" fails. DETAIL: references/pitfall-36-completion-table-heading.md
37. **Pre-authoring design Q&A prevents plan rewrites.** TRIGGER: source material implies trade-off decisions. ACTION: structured Q&A (10 or fewer, Q#/Rec/Impact) BEFORE authoring; wait for all answers. DETAIL: references/pitfall-37-pre-authoring-qa.md
38. **Plan forests must be self-contained (no cross-forest references).** TRIGGER: multiple forests for different implementation targets. ACTION: grep for sibling-forest references; replace with shared-spec citations. DETAIL: references/pitfall-38-self-contained-forests.md
39. **Dual-audit pattern for plan completeness.** TRIGGER: auditing a forest against its spec. ACTION: run completeness auditor + cross-implementation gap auditor in parallel; neither alone suffices. DETAIL: references/pitfall-39-dual-audit.md
40. **Subagent test files/side-effects lost without a sweep after EACH completion.** TRIGGER: any async or batch subagent completion. ACTION: git status --short + git diff --stat HEAD + git ls-files --others; commit all relevant files before the next notification. DETAIL: references/pitfall-40-async-sweep.md
42. **Visual/coordinate fixes require visual verification.** TRIGGER: fixing model position, capsule offsets, animation placement. ACTION: read runtime transforms via Godot MCP + verify with screenshots; never guess iteratively. DETAIL: references/pitfall-42-visual-verification.md

(Pitfall 41 consolidated into Pitfall 25 - check disk before re-dispatch.)

## Session Pitfall Extensions (post-v1.3 registry additions)

The registry above holds numbered invariants. Later session-derived pitfalls
live in reference files and keep their own numbering:

- Pitfalls 43-45 (duplicate dispatches, shared-repo hook interference, leaf-table errata): `references/concurrent-wave-execution.md`
- Pitfalls 43-44 variant (same-package concurrency, leaf-reported API drift): `references/concurrent-wave-execution.md`, extended by `references/concurrent-wave-execution.md` (incl. its Pitfall 45 license gate and Pitfall 46 registration-site serialization, numbered in that file)
- 2026-09-05 session lessons (background notifications are telemetry; shared-file serialization; API-drift verification; license gating): `references/session-pitfall-additions-2026-09-05.md`
- Meept gap-tree execution findings: `references/plan-authoring-verification.md`
- Authoring pitfalls observed at execution time: `references/session-pitfall-additions-2026-09-05.md`

## Skill Maintenance

> Maintenance: references/skill-maintenance.md (write-path loop, quarterly consolidation, eviction, regression scripts).

Write-path policy: never append dated session entries to this file. New lesson = one line appended to `references/INDEX.md` + a reference file with a `When to use:` / `Lesson:` header. Full policy: references/plan-tree-canon.md (C1-WritePath); consolidation and eviction rules live there too.

Files that must stay synchronized: `templates/master-template.md`, `templates/leaf-template.md` (section headings match SKILL.md and the compliance scanner), `scripts/check_template_compliance.py` (Step 6 / Pitfall 20), `references/compliance-headings.md` (exact heading list), `references/tests-first-gate.md` (Step 5.5 recipe; keep template Test Gate and scanner requirement in sync).
