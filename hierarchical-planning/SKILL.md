---
name: hierarchical-planning
description: "Use when creating implementation plans for features too large for one agent. Produces a tree of markdown documents: leaves fit one agent's 128K context. Orchestrators dispatch implementation agents and review in-session (main model), not via delegated subagents."
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [planning, hierarchical, multi-agent, delegation, implementation, tree]
    related_skills: [writing-plans, subagent-driven-development, kanban-orchestrator, parallel-report-generation, hierarchical-plan-execution, design-plan-consistency]
---

# Hierarchical Planning

## Overview

Create implementation plans as a tree of markdown documents designed for concurrent multi-agent execution. Each leaf document contains at most one agent's worth of work (128K context). Branch and root documents orchestrate their children: dispatch, review, re-dispatch, and track completion.

## Leaf sizing — the delegation budget

Pitfalls (dispatch discipline, scratch-daemon rig, MLX training):
references/dispatch-scratch-rig-mlx-pitfalls.md

Subagents are wall-clock capped (`delegation.child_timeout_seconds`, this
user: 1800 s). A leaf a single subagent cannot FINISH (write + test +
verify) inside ~25 minutes is killed mid-implementation — the model is
rarely the constraint; the stopwatch is. Measured on tree 30
(water/shores/swim): dual-language leaves (Go + GDScript, 4+ files)
reliably timed out; single-language leaves with ≤3 files fit.

**Rules:**
1. One leaf = one language where possible (Go-only or GDScript-only).
2. ≤3 files of change per leaf. More → split into sibling leaves with the
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
- **`templates/leaf-template.md`** — starter for leaf documents
- **`templates/master-template.md`** — starter for orchestrator/master documents
- **`references/multi-source-plan-authoring.md`** — technique for writing plan trees from multiple input documents (design docs, contracts, prior plans)

**Templates (copy and fill in):**
- `templates/master-template.md` — master.md (root) or orchestrator.md (branch). Contains every required section with comment instructions.
- `templates/leaf-template.md` — leaf implementation document. TDD task format with Go example code.

**Scripts (run directly):**
- `scripts/check_template_compliance.py` — structural compliance scan. Run AFTER authoring the whole tree and BEFORE dispatching agents: `python3 scripts/check_template_compliance.py <plans-root> --strict-leaves`

**References (read for deep guidance):**
- `references/go-background-processor-leaves.md` — TDD patterns for Go leaves that implement background/periodic processors (Engine struct, ticker loops, mock store, context shutdown).
- See `references/` for additional pattern guides on wave execution, gap analysis forests, bulk leaf generation, audit-driven planning, and more.

> **Do NOT guess template file names.** They are `master-template.md` and `leaf-template.md` — not `orchestrator.md` or `leaf.md`. Use the exact paths above.

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

**Hard requirement: no leaf document describes more work than one agent can implement in 128K context.** This must not compromise code quality — split along architectural seams, never mid-class or mid-module.

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

When a leaf would exceed limits, split — but ONLY along architectural seams:
- Module boundaries
- API contracts
- Layer separations
- Feature independence

**Never split a cohesive unit into two tightly-coupled leaves.** Instead, promote it to a branch with sub-leaves. Coupling between leaves kills concurrency benefits and creates integration failures.

If you find yourself needing to split a single class or function across documents, the leaf is the wrong size — make it a branch and decompose along internal responsibilities.

## Document Types

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

> **Loading this skill (size warning):** SKILL.md is ~100KB and exceeds
> `skill_view`'s output cap — the tool truncates or persists to a temp
> file instead of returning content (observed 2026-09-05, twice in one
> session). Do NOT act on the preview: read the SKILL.md from disk in
> slices with `read_file` (path from `skills_list`), paging with
> offset/limit until you have the pitfalls list (the last section).
> Support files (references/, templates/) load normally via
> `skill_view(name, file_path=...)`.

## Planning Process

### Step 1: Decompose by Architecture

Identify natural subsystem boundaries. For each subsystem, ask:

"Can one agent implement this end-to-end in one session (128K context, single tool budget) without running out of context or iterations?"

- **Yes** → leaf document
- **No** → branch directory, decompose further

Map dependencies between subsystems. Identify which can run concurrently (no dependencies) and which are sequential.

### Step 2: Define Interface Contracts

For each branch and root, define the contracts between its children:
- Data structures shared across children
- API/function signatures
- Event/message formats
- File path and naming conventions

Contracts are the integration surface. Ambiguous contracts = integration failures. Write them as actual type definitions or interface specifications, not prose.

### Step 3: Estimate Context Budget for Each Leaf

For each proposed leaf:

1. **Exploration cost:** Count files the agent must read. Tokens ≈ total lines / 3.5
2. **Generation cost:** Estimate new/modified lines from the task specs. Same ratio.
3. **Iteration cost:** ~3x single test/build run for TDD cycles
4. **Overhead:** ~15K tokens (system prompt, reasoning, tool I/O)

Total = exploration + generation + iteration + overhead.
If total > 110K → must split further. If total < 30K → consider merging with a sibling.

### Alternative: Audit-Driven Decomposition (for Documentation and Analysis Projects)

When the work targets **existing documents** (GDD, spec, API reference, audit remediation)
rather than new code, and you already have audit/analysis findings, decompose by
**problem class** rather than by architecture:

1. **Read all existing audits** — ingest every BLOCKER, GAP, INCONSISTENCY, and finding
   from existing audit/analysis documents. These are the canonical work-item list.

2. **Dispatch exploration subagents** (optional, pre-decomposition) — when the GDD
   is large (~90+ docs) and you need detailed findings before deciding the tree shape,
   batch 2-3 subagents to survey different sections in parallel. Each reads a slice
   of docs and returns a structured report (status, contradictions, gaps, needed work).
   Digest these reports in-session to inform your decomposition; do not delegate the
   tree-design decision itself.

3. **Group findings by problem class** — typical classes for docs projects:
   - **Contradictions** — doc X says A, doc Y says B. Small targeted edits (fixes).
   - **Missing specs** — named-but-undefined systems. New doc sections or new files.
   - **Draft upgrades** — docs with good shape but no final status marker. Cross-refs
     and status bumps.
   - **Todo files** — completely unwritten stubs. First-pass content creation.
   - **Audit cleanup / final verification** — update audit docs, standardize
     terminology, verify all cross-refs resolve.

   Each class becomes a branch. Order them so that contradictions (which block
   everything else) are resolved first, then specs, then upgrades, then cleanup.

4. **Estimate leaf sizing for doc work (not code):**
   - A doc-edit leaf handles **5-20 small line edits** or **1-3 new doc creations**
   - Context budget is lower than code (~30-60K per leaf) because there's no
     compilation, test runs, or TDD cycles
   - Exploration cost is higher: an agent editing a GDD section may need to read
     5-10 sibling docs for cross-reference verification
   - If a leaf would need to read more than 15 docs to verify cross-refs, split
     it — the agent's context window will fill with source material

5. **Write the tree** — same template structure as standard decomposition, but:
   - Child index uses **phase ordering** (Phase 1 = contradictions, Phase 2 = specs,
     etc.) instead of concurrency groups
   - Interface contracts are **file conventions and status markers** rather than
     type definitions
   - Review checklist swaps "tests pass" for "cross-references resolve" and
     "no contradictions introduced"

This approach is optimal when you have an existing corpus with known issues and
need a plan tree that resolves every finding in priority order. The GDD completion
session is a worked example: `plans-ds4f/` shows the 5-branch structure
(contradictions → specs → upgrades → todos → cleanup) derived from 3 audit docs
(~60 total findings).

### Alternative: Gap-Analysis-Driven Decomposition (external report → forest)

When the user provides an external engineering report, competitor analysis, or
feature comparison document and asks "which of this can we add and how much
value would it provide," the workflow is:

1. **Read the external report** in full. Extract every distinct feature/subsystem.

2. **Dispatch parallel subagents** (one per subsystem area, typically 6-10) to
   analyze the existing codebase against the report. Each subagent reads the
   relevant source files and returns: what exists, what's missing, what's
   architecturally different, and what's superior in the existing code. Give
   each subagent the relevant section of the external report as context.

3. **Synthesize a gap analysis** in-session. For each feature area, assign a
   verdict: SUPERIOR (existing is better), PARITY (equivalent), or GAP with
   severity (HIGH/MED/LOW). Rank by build-quality impact, not complexity.
   Present to user with priority tiers (DO NOW / DO NEXT / LATER / SKIP).

4. **Pre-authoring Q&A (BEFORE writing any plans).** Collect all ambiguous
   design decisions into a structured walkthrough (≤10 questions). Each
   question has: Q# (one-line title), Rec (your recommendation with rationale),
   Impact (what changes if the decision goes the other way). Do NOT write any
   plan documents until ALL questions are answered. The user may override any
   recommendation. Terse answers may hide scope changes — confirm before
   proceeding (see Step 6.8).

5. **Decompose into a forest** based on the user's answers. Group related
   small improvements into combined trees (e.g., 6 small fixes → 1 tree with
   4 leaves). Keep large features as their own trees. Assign concurrency
   waves based on dependencies.

**Key difference from Audit-Driven Decomposition:** the input is an EXTERNAL
report (not internal audit findings), and the decomposition is preceded by a
comparative analysis phase that determines which features are worth adding
vs. which the existing code already handles better. The "superior" assessment
should be based on likelihood of producing superior RESULTS (cleaner, more
consistent builds), not on complexity or feature count.

Worked example: meept session (2026-07-24) — 1,693-line Claude Code
engineering report → 9 parallel subagents (70s) → 12-area gap analysis →
7-question Q&A → 5-tree forest (14 leaves). See
`references/gap-analysis-forest-pattern.md`.

### Alternative: Ops & Asset Pipeline Trees (Shell/API/Download Trees)

When the plan dispatches agents that primarily run shell commands, API calls,
web searches, and file downloads — asset retrieval, AI generation, data
collection — rather than writing code or editing docs. Same tree shape
(inline leaves, dispatch + review), but verification swaps "tests pass" for
"files exist, correct size, expected format"; leaves use `manifest.json` for
progress tracking; the orchestrator reviews output files (stat, file, jq,
vision_analyze) rather than code diffs. Watch for incomplete orchestrator
process sections (Dispatch Protocol, Review Checklist, Integration Test
Plan) in docs-only trees — do a completeness pass after authoring ALL docs.
Full pattern and worked example: `references/ops-asset-pipeline-2026-09.md`.
See `references/frontend-dashboard-plan-pattern.md` for React/Vite SPA
dashboard trees (foundation-first decomposition, stub-first contracts,
TSX-in-task-specs quality standard).

### Step 4: Write Orchestrator Documents

Use `templates/master-template.md` as the starting point. Key sections:
- Goal and architecture (brief — children have their own details)
- Interface contracts (precise — this is the integration surface)
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
match the scanner's EXACT strings — required list in
`references/compliance-headings.md`.

```
python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py plans/feature-name --strict-leaves
```

Re-run until `ALL TREES COMPLIANT: True`; the script reports missing required
sections per document. (The `plans-glm/` scan caught 5 of 12 trees missing
Dispatch Protocol/Coding Conventions before any were dispatched.)

### Step 6.5: Authoring a Forest (5+ plan trees at once)

When a session authors MANY plan trees under one root (e.g. a 12-system
build-plan-index, or a full-project decomposition), re-stating identical
conventions, wire types, pitfalls, and commit policy in every `master.md`
causes massive duplication and drift. The forest pattern fixes this:

**Create a `SHARED-CONVENTIONS.md` sibling to the root `master.md`.** Move
there: project layout, language coding conventions, the frozen IPC / wire
types, the numeric/scale contract, the test strategy, the pitfalls list, and
the commit policy. Every `master.md` and leaf then REFERENCES it ("see
SHARED-CONVENTIONS.md §3") rather than re-declaring its contents.

Why this matters:
- One source of truth for cross-tree contracts (wire types, numeric scales).
- When a contract evolves during implementation, you edit ONE file, not 12.
- Leaf dispatch contexts inline the relevant §section of SHARED-CONVENTIONS.md
  rather than re-deriving conventions per leaf.
- The forest's root `master.md` shrinks to: goal, architecture overview, child
  tree index, dependency graph, concurrency groups, cross-tree contracts
  (one-line pointers into SHARED-CONVENTIONS.md), root review checklist, root
  integration test plan, completion tracking table, and cross-tree open questions.

A forest also benefits from a single `OPEN-QUESTIONS.md` sibling that collects
every tree's open questions in one place, sorted by tree, with a "summary: N
questions, M needing decisions" footer. This is what the user reviews to amend
plans before execution — they should not have to open 12 files to find the
questions.

### Step 6.6: Inline vs separate leaf files (forest scale decision)

When a forest has 5+ trees, authoring fully-expanded separate leaf files for
every leaf (like the worked `02-gossip/01,02,03-*.md` set) produces 30-50
files and is rarely justified at planning time. Decision rule:

- **Separate leaf files** when: the tree is the critical-path / de-risk
  milestone AND has 3+ leaves with complex inter-leaf dependencies. Full TDD
  task expansion is warranted because execution is imminent and the leaves
  will be dispatched verbatim.
- **Inline leaf definitions inside `master.md`** when: the tree has 2-3
  moderate leaves (~60-90K each) AND the leaves' task detail will be obvious
  once the orchestrator reads the spec at dispatch time. Inline = each leaf
  gets a `## Leaf NN-name` section in master.md with: scope, dependencies,
  estimated context, files-touched, interface contract, self-verification
  checklist pointer, "Do NOT commit", and a one-line dispatch instruction.
  The executing orchestrator expands the inline leaf into a full TDD task list
  AT DISPATCH TIME (reads the GDD spec, writes the tasks, then dispatches).

In the `plans-glm/` session: 1 of 12 trees (the gossip de-risk milestone) got
separate leaf files; the other 11 used inline leaf definitions. Both shapes
passed the compliance scan. Inline is the default for forests; expand to
separate files when execution of that specific tree is next.

### Step 6.7: Differential / convergence plan naming

A `plans-<label>/` directory signals a forest authored for a specific session
or purpose — differential/convergence implementation (same leaf, multiple
agents/models, outputs compared: freeze wire types, signatures, paths; state
the purpose in the root `master.md`) vs session-specific doc completion
(archived once done). If the user names a directory `plans-<something>/`,
ask which purpose it serves before authoring — differential forests need
tighter contracts. Full pattern: see `references/execution-protocol-2026-09.md`.

### Step 6.8: Resolving Open Questions with the User (Walkthrough Pattern)

After authoring a plan tree or forest, OPEN-QUESTIONS.md typically has 8-15
items needing user decisions (plus many more that are accept-as-default). Do
NOT dump all of them on the user unstructured, and do NOT silently
batch-accept items that need a real decision. Use this pattern:

**Mechanical vs. user-facing split.** Bifurcate the questions into:
- **Mechanical corrections** (spec values the plan got wrong, confirmations
  where the spec is authoritative) — apply these yourself in a batch, do NOT
  ask the user. Just report "applied N corrections."
- **User decisions** (genuine forks: scope cuts, format choices, separate-tree
  vs. in-tree) — these need the user. Collect them into a walkthrough.

**Walkthrough format (≤10 questions per batch):** For each user-facing question:
- **Q#** — one-line title
- **Rec** — your recommendation (the user wants you to extrapolate, not just ask)
- **Impact** — what breaks or changes if the decision goes the other way
- **Options** — lettered (a/b/c) when you have alternatives beyond rec-vs-not

**Re-establish technical context before asking.** If a question asks the user
to decide between two technical artifacts (e.g. "GGUF vs ONNX format"), the
user may not recall what that artifact IS or its role. Before the rec, give a
1-3 sentence orientation: what the thing is, what it does in the system, why
the format matters. The user said "I don't recall the role" when asked cold —
that's a signal to re-establish context first, not push the decision.

**Terse answers may hide bigger changes — confirm scope before executing.**
When the user gives a short answer to a framed blocker, check whether they're
answering the framed question or proposing a deeper change. Example: a blocker
framed as "save schema vs schedule doc — which 8-needs list wins?" got the
answer "No hunger, thirst!" — which is NOT picking a source, it's cutting 2
of the 8 needs entirely (6-needs model, aligning with a prior no-starvation
decision). Read the answer back to the user ("I read this as cutting X and Y,
giving result Z — confirm?") before editing multiple GDD docs and plan trees.
The cost of one confirmation round is trivial compared to cutting the wrong
thing across 5 trees.

**Apply AGENTS.md Rule 1 (changelog) for any GDD edits.** If the user's
decision requires editing GDD docs (not just plan docs), record a changelog
entry in the same batch — see the `design-plan-consistency` skill.

### Step 7: Save and Offer Execution

```
mkdir -p plans/feature-name
# Write all documents
git add plans/feature-name/
git commit -m "docs: hierarchical implementation plan for [feature]"
```

Offer: "Plan tree saved at plans/feature-name/. To execute, use the `hierarchical-plan-execution` skill — it dispatches the root orchestrator, fans out implementation agents, reviews with the main model, and marks completion hierarchically. Shall I proceed?"

## Commit Policy

**Only orchestrators commit. Implementation agents must NOT commit.**

Rationale: the orchestrator owns the subtree's state and is the only agent with full visibility into which children passed review and integration. If leaf agents commit independently, partial/unreviewed work lands in git history, commits conflict when multiple leaves touch nearby files, and the orchestrator loses control over what gets committed and when.

The flow:
1. Implementation agent writes code and tests, runs them locally to verify, reports results — but does NOT commit.
2. Review agent checks the implementation against spec + contracts.
3. Orchestrator commits ONLY after review passes: stages the specific files from that leaf, uses a descriptive message referencing the leaf document.
4. Integration commits (after all children in a branch pass) are also made by the orchestrator.

Instruct every implementation agent in its dispatch context: "Do NOT run git commit. Do NOT run git add. Write code, run tests, report results. The orchestrator handles all git operations."

## Dispatch Protocol (Embedded in Orchestrator Documents)

Every orchestrator document contains these instructions for the executing agent:

### For Each Child Document:

**0. Test Gate (code branches only — runs BEFORE any implementation dispatch)**
- Dispatch test-gate leaves (Step 5.5) as subagents. Brief: "Write tests ONLY, no implementation. Tests must fail RED for missing-implementation reasons. Do NOT commit."
- The control agent (orchestrator, main model, IN-SESSION — never delegated) validates returned tests against the coverage matrix. On any delta, the LESSER of plan/tests updates to reflect the GREATER (coverage converges upward; test deletion needs written rationale).
- When every matrix row is VALIDATED: commit the gate tests, mark the branch TESTS_VALIDATED. Implementation leaves then dispatch — parallel across validated branches, never before their own gate. Recipe: `references/tests-first-gate.md`.

**1. Dispatch Implementation Agent**
- Read the child document
- Dispatch via `delegate_task` with the child document as context
- **delegate_task call shape (two distinct failures, 2026-09-05 meept session):** single-task mode REQUIRES `goal` — a `context`-only dispatch errors with "Provide either 'goal' (single task) or 'tasks' (batch)". Batch mode REQUIRES a `goal` INSIDE each `tasks[]` item — a top-level goal with items lacking per-item goals errors with "Task 0 is missing a 'goal'". Working shape: `tasks: [{goal: <one-line imperative>, context: <full leaf brief: leaf path, pinned contracts, do-not-commit, corruption rule, exact verify commands>}]`. On any dispatch error, diagnose the schema shape before retrying — do not just resend.
- Include the interface contracts from the orchestrator
- Include: "Do NOT commit. Do NOT run git add. Write code, run tests, report results only."
- Agent implements all tasks in the leaf using TDD

**2. Review Implementation** (after implementation returns)
- The orchestrator (main model) reviews in-session, NOT via a delegated subagent.
- Rationale: `delegate_task` children inherit `delegation.model`. If a delegation model is set (local profiles), a delegated reviewer uses the same subagent model that wrote the code. The main model must review.
- Read the changed files, verify interface contracts, run tests, check for artifacts.
- See `hierarchical-plan-execution` skill for the full in-session review procedure.
- On local-model setups where the main model is much stronger: this is especially critical (see `local-ravenx-review-pipeline` skill for the rationale).

**3. Re-dispatch if Incomplete**
- If review identifies gaps → re-dispatch implementation with specific feedback
- Re-review after re-dispatch
- Loop until review passes (set a max iteration count — 3 typically)

**4. Commit** (after review passes)
- Orchestrator stages the leaf's specific files: `git add <exact file paths from leaf>`
- Orchestrator commits: `git commit -m "feat(scope): implement [leaf name]"`
- Update the tracking table: status -> REVIEWED

5. **Record Status**
- Update the tracking table in the orchestrator document
- The PARENT determines completion — never the child

Duplicate/lost-dispatch recovery + leaf-errata protocol: see `references/dispatch-recovery.md`.

### Concurrency Rules

- Hermes `delegate_task` concurrency is configurable via `delegation.max_concurrent_children`
  in config.yaml (default 3, can be raised to 6+ with `hermes config set
  delegation.max_concurrent_children 6`). Batch independent leaves up to the
  configured cap for maximum throughput.
- Sequential dependencies: wait for prerequisite to reach COMPLETE before dispatching
- Maximize parallelism — dispatch all independent leaves immediately
- When dispatching mixed work types (implementation + review + research),
  use the higher cap — a review subagent is lightweight and won't compete for
  the same resources as an implementation agent.

## Review Protocol — Orchestrator In-Session

Review happens at EVERY level, performed by the orchestrator (main model)
in-session — NOT via delegated subagents. `delegate_task` children inherit
`delegation.model`; on local profiles a delegated reviewer would use the
same subagent model that wrote the code. See `hierarchical-plan-execution`
skill for the full rationale and review procedure.

### Dual-Track Review for Plan Trees

When you need to verify a plan tree before executing it, dispatch TWO types
of review subagent IN PARALLEL (not serial — they check different things):

1. **Coverage reviewer:** Reads every leaf document against every source audit
   finding. Confirms every finding has an assigned leaf. Flags orphan findings.
   Output: list of gaps (findings not addressed by any leaf).

2. **Compliance/template reviewer:** Reads every document against the
   hierarchical-planning template requirements. Checks each branch for
   Dispatch Protocol, Interface Contracts, Review Checklist, Coding Conventions,
   Completion Tracking Table, Integration Test Plan. Checks each leaf for
   "Do NOT commit", Self-Verification Checklist, and proper task structure.
   Output: list of structural issues with file:line references.

They run in parallel (same concurrency group) because neither depends on the
other. Fix issues from BOTH before dispatching implementation agents. In the
worked example (`plans-ds4f/`), the compliance reviewer found 18 issues
(3 critical, 6 structural, 6 missing-section, 3 cosmetic). Fixing these
before execution saved the orchestrator from having to compensate for gaps
mid-flight.

### Contract Verification Digests (post-authoring, pre-execution)

The dual-track review above checks **structural** coverage (every finding
assigned to a leaf) and **template** compliance (every required section
present). Neither checks whether the **frozen contract values** in your plan
match the source spec. A plan can pass both reviews and still be wrong in a
way that causes integration failure across every consumer of a shared struct.

**Dispatch contract-verification digest subagents after authoring a plan tree
or forest, especially when the plan invents frozen Go structs / constant
tables / threshold enums from prose spec language.** This is the technique
that caught Pitfall 21 (paraphrase-drift) in the `plans-glm/` session.

Pattern (see `references/contract-verification-digests.md` for the full recipe):

1. Slice the plan tree's contracts by source spec (one subagent per spec slice
   — e.g. one for the gossip spec, one for the perception spec, one for the
   save schema).
2. Each subagent reads ONLY the source GDD spec (via `terminal cat` or
   `search_files`, never `read_file` — line-number corruption) and returns a
   structured report: for each contract (struct field, constant, threshold
   table, enum), quote the spec's exact words and flag any mismatch with what
   the plan authored.
3. The orchestrator (main model) digests the reports in-session and amends
   the plan contracts. Do NOT delegate the amendment decision.

This is distinct from the exploration subagents in the "Audit-Driven
Decomposition" alternative (Step 3), which run BEFORE decomposition to inform
the tree shape. Contract-verification digests run AFTER authoring to catch
spec-drift in the authored contracts. Both are read-only; neither writes files.

When to run contract-verification digests:
- The plan defines frozen wire types, shared structs, or constant tables that
  multiple trees consume (highest value — one wrong field breaks integration
  everywhere).
- The plan translates prose spec ("reputation is the durable aggregate")
  into a concrete type — this is where paraphrase-drift lives.
- The plan invents threshold bands, enum members, or formula coefficients
  "derived from the spec narrative" without an exact spec quote.
- You authored a forest (5+ trees) — the integration surface is larger and
  contract drift compounds across trees.

When NOT to run them: for a single-tree plan with trivial contracts, or when
every contract value is a verbatim copy of a spec table (no paraphrase risk).

### Tier-3 Verification: Changelog-Review Digests (post-authoring, catches design drift)

Contract-verification digests (tier 2) diff your plan's frozen contracts
against the source spec *as it exists today*. But on a long-running project
with an active changelog (per the `design-plan-consistency` skill), the spec
itself may have drifted *after* you read it — a parallel session may have
ratified new constants, cut a system, or elevated a doc's status. Your plan
inherits stale values even if your translation was faithful at the time.

**Run a changelog-review digest after the contract-verification digests,
before execution, on any project with an active changelog.** Pattern (see
`references/changelog-review-digests.md` for the full recipe):

1. Dispatch one subagent to read the project's changelog + recent commit log
   (`git log --oneline -30 -- docs/gdd/` or equivalent) and cross-reference
   every entry dated *after* the plan tree's last verification date against
   the plan's spec sources.
2. For each changelog entry that touches a plan spec source, the subagent
   reports: (a) hard contradictions (plan holds values the spec has since
   changed), (b) resolved open questions (the changelog closed something the
   plan still lists as open), (c) new info the plan should incorporate,
   (d) status changes (a doc the plan treats as [DRAFT] is now [DECIDED]).
3. Orchestrator digests in-session, amends the plan, and — per AGENTS.md
   Rule 1 — writes a changelog entry for any GDD edits *caused by* the
   reconciliation.

This is the technique that caught two hard errors in the `plans-glm/` session
that survived tier 1 (structural scan) AND tier 2 (contract digests): the
Boston hill heights (Pemberton 24m→34m, ratified by a primary-source research
commit the plan author never saw) and the procgen condition-label rename
(`derelict`→`ruined`). Both were *post-authoring* design drift, invisible to
any verification that only reads the current spec file.

Whether reviewing a plan tree or reviewing implementations, the protocol
is the same:

```
Leaf implementation returns
  -> Orchestrator (main model) reviews changed files in-session
  -> Gaps found? Re-dispatch implementation with feedback -> re-review
  -> Review passes? Orchestrator commits, marks leaf REVIEWED

All children of a branch reach REVIEWED
  -> Orchestrator runs integration checks in-session
  -> Checks: cross-child contracts, integration tests, no regressions
  -> Gaps? Re-dispatch specific children -> re-review
  -> Passes? Branch marked COMPLETE

All children of root reach COMPLETE
  -> Orchestrator runs final integration review
  -> Full test suite, end-to-end verification
  -> Passes? Project COMPLETE
```

**Key rule:** Implementation status is tracked ONLY by the orchestrator. The implementer does not self-assess completion. The orchestrator determines when and to what degree a leaf's plan was completed, based on its own review of the changed files.

## Plan Reconciliation

Plan trees are NOT static. External work (a changelog-driven session, a parallel agent team, a human developer) can execute some or all leaf tasks independently before the plan tree runs. When you return to a plan tree after external work, reconcile before dispatching.

### Pre-Work: Changelog Drift Check

Before reconciling or dispatching any plan tree, apply the **changelog-drift
check** from the `design-plan-consistency` skill (Rule 2):

1. Read the project's changelog.
2. Read the Implementation Record for the plan tree.
3. Cross-reference changelog entries since the tree's last verification date
   against the tree's design-spec sources.
4. If any entry touches a spec source → the plan needs updating first.

This check catches the case where the *design* moved while you were away, even
if no *code* was written. The code-level reconciliation below assumes no
design-spec drift has occurred. If drift is found, update the plan before
proceeding (the plan's tasks must reflect the current design).

### Subagent-Driven Reconciliation

The reconciliation process above describes WHAT to do. The most efficient
execution pattern (proven in the `plans-ds4f/` session — 20 leaves reconciled
against 19 changelog rows in ~5 minutes wall-clock) is:

**1. Dispatch a reconciliation audit subagent (read-only).** One subagent
reads the changelog + every plan leaf + the current GDD state. It produces:
- Per-leaf verdict (SUPERSEDED / PARTIAL / STILL_NEEDED / BLOCKED)
- Specific leaf-text that is now wrong (stale file references, wrong numbers,
  superseded proposals)
- Tracking table updates for each branch orchestrator

The subagent does NOT edit files. This keeps the audit pure — no risk of
stale read-state corruption (Pitfall 19).

**2. Digest the report in-session.** The orchestrator (main model) reads the
reconciliation report and decides which updates to apply. Do NOT delegate this
judgment to a subagent — the orchestrator owns the plan tree.

**3. Dispatch a reconciliation update subagent (write-only).** One subagent
applies the tracking table updates, adds reconciliation notes, and adjusts
phase ordering. Give it explicit instructions — do NOT make it re-read the
GDD or the plan leaves (it already knows the changes from your instructions).

**4. Update the changelog.** Record the reconciliation as a new changelog
entry (per AGENTS.md Rule 1 if any GDD edits were made as part of the
reconciliation — this is rare; usually only plan docs change).

**5. Commit.** The orchestrator commits the reconciliation changes.

The changelog file format convention (table with Date/Session/Scope/Changes/
Verification columns designed for agent review) is documented in
`references/changelog-file-format.md`.

### When to Reconcile

Reconcile when:
- A changelog, commit log, or status report shows work was done that overlaps with plan leaves
- Another session or agent modified files the plan was targeting
- Some time has passed and the project state may have diverged from the plan
- You're about to dispatch execution and want to skip already-completed work

### Reconciliation Process

**Step 1: Verify leaf state against reality.** For each leaf, check whether its intended outputs exist on disk. Use `find`, `search_files`, or `stat` — do not guess.

**Step 2: Classify each leaf:**

| Classification | Meaning | Action |
|---|---|---|
| SUPERSEDED | All intended work was done externally | Mark COMPLETE in tracking table, add note |
| PARTIALLY SUPERSEDED | Some work was done externally, some remains | Update leaf tasks to cover only remaining work |
| STILL_NEEDED | No external work touched this leaf | Dispatch as normal |
| BLOCKED | External work created a dependency or conflict | Report to user, add note |

**Step 3: Update the tracking table.** In the plan tree's orchestrator documents, update the Completion Tracking Table with the new statuses and a reconciliation note.

**Step 4: Add a reconciliation note** to the Notes section of each updated orchestrator doc, referencing the source of the external work.

**Step 5: Adjust phase ordering.** If external work completed Phase 1 (contradictions) and Phase 2 (specs), the remaining phases may need re-ordering. Update the master.md's dispatch protocol accordingly.

### Common Reconciliation Patterns

**Pattern A: Changelog from a parallel session.** Another session generated a changelog documenting many changes. The plan tree's leaves correspond to some of them. Reconciliation: verify each leaf against the changelog items, mark as SUPERSEDED where matched, add the changelog's follow-up items as new leaf tasks.

**Pattern B: Partial execution before cancellation.** A prior session dispatched some leaves but was interrupted. Check file existence AND test results. Don't assume "file exists = work done."

**Pattern C: Human landed a PR.** A developer committed changes that overlap with plan scope. Run `git diff` from the branch point to see what changed. If the PR covers a leaf's entire scope, mark SUPERSEDED.

### Updating Leaves After Reconciliation

When a leaf is PARTIALLY SUPERSEDED, update the leaf document to narrow its scope to what remains:
1. Read the leaf and identify which tasks are still needed
2. Update the leaf's Goal and Tasks sections to reflect only remaining work
3. Add a reconciliation header showing which tasks were completed externally
4. Update the leaf's Estimated Context if it shrank significantly

Do NOT delete the leaf document — it documents the original scope and the reconciliation decision. The orchestrator tracking table is the source of truth for current status; the leaf is the source of truth for original intent.

## Completion Tracking

Status values (recorded in orchestrator's tracking table):

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

The orchestrator's tracking table is the source of truth for subtree status. Update after every child transition.

## Execution Backends

The plan tree is backend-agnostic. Two execution modes:

### Direct Dispatch (default)
Use `delegate_task` to fan out leaf agents. Orchestrator waits for returns,
dispatches review agents, commits, and tracks. Multi-session repos: see
`references/live-multi-session-repos.md`.

### Kanban Board (for durable execution)
Use `kanban_create` to create cards for each leaf, assigned to worker
profiles. Dependency links via `parents=[...]` enforce ordering. Best for:
work spanning multiple sessions, crash recovery, human-in-the-loop gates,
audit trail. See `kanban-orchestrator` skill for the decomposition playbook
and dispatch patterns.

The plan documents are the same either way — only the dispatch mechanism
changes. Orchestrator documents can specify which backend to use in their
Meta section.

## Reference Documents

- `references/tests-first-gate.md` — tests-first gate recipe (Step 5.5,
  Dispatch Protocol step 0, Pitfall 46): test-leaf tree shape, coverage
  matrix, control-agent delta protocol, Phase 0 flow, parallelism rules.
- `references/cross-repo-informational-contracts.md` — Pin a sibling repo's
  future read surface (exact columns, projection SQL, zero-value semantics)
  as a frozen informational contract in the producer's master.md; repo A
  tests pin it from the A side. Worked example: meept↔tokscale 2026-09-06.
- `references/audit-driven-gdd-planning.md` — Rebellion GDD completion
  worked example: exploration subagents → problem-class decomposition →
  5-branch tree.
- `references/multi-tree-forest-pattern.md` — plans-glm 12-system forest:
  SHARED-CONVENTIONS.md + OPEN-QUESTIONS.md siblings, inline-vs-separate
  leaf decision, plan-naming convention.
- `references/contract-verification-digests.md` — Recipe for the post-authoring
  contract-verification digest pattern (Review Protocol §"Contract Verification
  Digests"). Includes the dispatch prompt template, the report shape subagents
  return, and the `plans-glm/` session's two caught errors as worked examples.
  Read alongside Pitfall 21 (paraphrase-drift).
- `references/standalone-reusable-library-trees.md` — forest pattern for a standalone library a host consumes (freeze contracts first, one example leaf, synthetic-first de-risk, independent verify).
- `references/client-onboarding-checklist.md` — the 8 touch points for
  adding a new client to the tokscale registry (registry entry, parser,
  scanner, two parse lanes, CLI filter, TUI, tests) with gate commands.
- `references/changelog-review-digests.md` — Recipe for the tier-3 changelog-review
  digest (Review Protocol §"Tier-3 Verification"). Dispatched after the contract-
  verification digests to catch design drift caused by sibling sessions. Includes
  the dispatch prompt template and the `plans-glm/` session's two caught errors
  (hill heights, condition labels) as worked examples. Read alongside Pitfall 22.
- `references/cross-corpus-concept-replacement.md` — Recipe for the sweeping
  concept-replacement pattern (Pitfall 23): parallel digest subagents → categorize
  hits → batch apply via execute_code → verify. Covers the first-person→third-person
  pivot as the worked example, including the false-positive categories (genre
  labels, narrative-grammatical person, competitor perspectives) and the technical
  consequences (FOV, camera rig, viewmodel scope).
- `references/open-questions-walkthrough.md` — Recipe for presenting a plan
  tree's OPEN-QUESTIONS to the user for resolution (Step 6.8). Covers the
  mechanical-vs-user-decision bifurcation, the ≤10-question walkthrough format,
  re-establishing technical context before asking, and confirming terse answers
  that may hide deeper scope changes.
- `references/changelog-file-format.md` — The canonical file format for a
  project-level changelog designed for agent review. Table with Date/Session/
  Scope/Changes/Verification columns, stable decision IDs, chronological
  order. Read alongside the changelog-review-digests recipe and the
  Subagent-Driven Reconciliation section.
- `references/orchestrator-execution-mechanics.md` — orchestrator-side execution mechanics (meept 2026-09-05 forest): leaf-return fixes, commit procedure under parallel-session hook interference, generated-docs churn, known-limitation ledger. Also `references/execution-pitfalls-meept-gap-trees.md` — flat-layout trees bypass --strict-leaves (hand-verify leaves), leaf-table-vs-frozen-contract errata, parallel-session commit storms, delegate_task batch dispatch shapes (meept 2026-09-06 gap trees).
- `references/parallel-branch-authoring.md` — Dispatching subagents to WRITE
  plan trees in parallel (master first, then fan out branches). Covers plan-
  writing timeout recovery and structural validation.
  Read alongside Pitfalls 25-28 when executing a plan forest.
- `references/asset-pipeline-plan-pattern.md` — Ops/asset pipeline tree pattern:
  non-code trees that execute shell commands, API calls, and file downloads
  instead of writing code. Covers manifest.json tracking, verification swap
  (file exists vs tests pass), tooling conventions, and pitfalls specific to
  ComfyUI/SSH/web-search leaves. Worked example from the `plans-glm/` session
  (trees #15 and #16). Read alongside the "Ops & Asset Pipeline Trees" section.
- `references/frontend-dashboard-plan-pattern.md` — Frontend SPA dashboard tree
  pattern: React/Vite dashboards embedded in a backend binary (Go `//go:embed`).
  Foundation-first concurrency (shell leaf must complete before view leaves),
  stub-first contracts (typed prop interfaces as binding contracts), actual TSX
  code in task specs (not prose), chart library sizing, and CSS/Tailwind
  consistency. Worked example from the AgentAudit Phase 1 dashboard branch.
- `references/batch_leaf_generator.py` — Python script for bulk leaf document
  generation. Use when a plan tree has 10+ leaves and writing them individually
  is tedious. The script takes a structured list of leaf definitions and generates
  all .md files with consistent structure (DISPATCH INSTRUCTION, tasks, checklists).
  Edit the `all_leaves` list in the script, then run:
  `python3 references/batch_leaf_generator.py plans-dir/`. After generation, run
  the compliance scanner to verify. Worked example: `plans-godot/` session
  (25 leaves generated across 9 branches in ~5 minutes).
- `references/godot-port-planning.md` — Godot 4 / Summer Engine port specialization
  (translation tables, sidecar IPC, MCP strategy; Rebellion session 2026-07-23).
- `references/execution-pitfalls-shared-repo-trees.md` — Pitfalls 43-45:
  late duplicate dispatches overwriting leaf files, pre-commit failures
  caused by parallel sibling sessions, leaf-table errata vs frozen rules.
  Session-proven 2026-09-05.
- `references/cross-repo-contract-pinning.md` — Freezing a future CONSUMER's
  read surface (external parser/aggregator over this repo's data) as an
  informational no-owner contract in the producer's root master.md: what to
  pin (paths, column names, zero-value semantics, error-row filtering, dedup
  rule, registry entry) and the rule that contract changes are master edits,
  never silent leaf drift. Worked example: meept→tokscale metrics.db ingest
  (2026-09-06). Also records that flat trees pass the compliance scanner with
  a benign "no subdirectories" warning.

## Integration with Existing Skills

| Skill | Relationship |
|-------|-------------|
| design-plan-consistency | Governs WHEN a plan tree should be authored, updated, or marked stale relative to design-doc changes. This skill's Plan Reconciliation §Pre-Work is the integration point: run the changelog drift check before dispatching. |
| hierarchical-plan-execution | The default execution engine for plan trees created by this skill. Main model orchestrates and reviews; subagent model implements leaves. |
| writing-plans | Leaf documents use the same bite-sized TDD task format. This skill is the hierarchical wrapper. |
| subagent-driven-development | The dispatch + review loop is the same pattern. This skill adds tree structure and trickle-up. |
| plan | Plan mode produces a single flat plan. This skill produces a tree when one plan is too big. |
| requesting-code-review | Review agents use the same review dimensions. This skill automates the review loop. |
| kanban-orchestrator | Alternative execution backend. Kanban gives durable state, crash recovery, and human-in-the-loop gates. Same decomposition + anti-temptation philosophy. |
| local-ravenx-review-pipeline | On local-model setups, the review agent must be a stronger model than the implementer. This skill provides the review script and enforcement pattern. |
| parallel-report-generation | Same parallel-subagent assembly pattern. Its line-number corruption prevention (inline source data, never read_file in subagents, verify with xxd) applies to leaf agents writing code files. |
| godot-game-development | Godot 4 / Summer Engine development patterns, GDScript gotchas, MCP setup. Load alongside this skill when planning a Godot port — provides engine-specific implementation details that inform plan decomposition. |

## Common Pitfalls

1. **Splitting too aggressively.** A tree with 20 tiny leaves where 5 well-sized leaves suffice. More nodes = more integration surface, more dispatch overhead. Only split when the 128K limit forces it. If a leaf is under 30K estimated, merge it with a sibling.

2. **Splitting along wrong seams.** Splitting a single class across two leaves because it's "too big." Instead, keep the class in one leaf and split at the module/package boundary. Tight coupling between leaves defeats concurrency.

3. **Missing or vague interface contracts.** Branches without explicit contracts between children lead to integration failures. Define shared types, API signatures, and file conventions as actual code, not prose. Update contracts if they evolve during implementation.

4. **Orchestrator implementing child work.** The orchestrator dispatches, reviews, and tracks — it does not implement. If you're writing code in the orchestrator session, stop and re-dispatch to a leaf agent.
    **Exception — Rate-limit batch failure:** When a batch of 10+ subagents is dispatched and 40%+ hit HTTP 429 rate limits (Pitfall 13c), the orchestrator MAY write the missing files directly from accumulated session context rather than re-dispatching. Signs to switch: (i) 4+ subagents in the same batch returned 429 with no output, (ii) the orchestrator already read the GDD specs and wrote the dispatch contexts (so it has the content), (iii) the missing files are well-bounded (one GDScript file per leaf, no cross-leaf dependencies), (iv) re-dispatching will likely hit the same rate limits. Write files using `write_file` (NOT `execute_code` f-string concatenation — see Pitfall 29 variant), verify with grep, commit as a separate wave. This is NOT a shortcut to skip dispatching — always dispatch first; only implement directly as a batch-failure recovery path.
    **Exception — Single-leaf timeout:** When a single leaf subagent fails completely (429 or timeout with no usable output — Pitfall 25 variant), the orchestrator MAY implement the work directly provided it already has sufficient context from prior exploration. Signs to switch: subagent consistently fails before producing output, you already read enough files to write correct code, and the work is well-bounded.

5. **Skipping the review agent.** Without review, incomplete work propagates upward and integration fails catastrophically. Always review before marking REVIEWED or COMPLETE.

6. **Status not trickling up.** If a parent doesn't record child completion, the grandparent has no visibility. Update the tracking table after every transition.

7. **Circular dependencies between leaves.** Leaf A depends on B, B depends on A. Break cycles by extracting the shared dependency into a third leaf that both depend on, or restructure the decomposition.

8. **Underestimating context budget.** A leaf that looks like 40K of work but requires reading 30 existing files will blow past 128K. Account for exploration cost, not just generation cost. Use `wc -l` on the files the agent will need to read.

9. **Dispatching leaves one at a time.** Independent leaves should be batched in groups of 3 for concurrent dispatch. Sequential dispatch of independent work wastes time.

10. **Forgetting to reset status on re-dispatch.** When a leaf is re-dispatched after review failure, reset its status to IN_PROGRESS — don't leave it at IMPLEMENTED.

11. **Leaf agents committing.** Implementation agents that run `git commit` independently create unreviewed history, cause conflicts when multiple leaves touch nearby files, and break the orchestrator's ownership of subtree state. Every dispatch context must say "Do NOT commit." The orchestrator commits after review passes.

12. **Line-number corruption from read_file.** Leaf agents that use `read_file` to inspect existing code and then feed that output into `write_file` will bake `     N|` line-number prefixes into source files. This is catastrophic in code (not just reports) and compounds when the orchestrator assembles outputs from multiple leaves. Three-part prevention: (a) inline the relevant source snippets in the dispatch context instead of telling agents to read files; (b) if agents must explore, instruct them to use `search_files` (which returns clean content) or `terminal("cat file")` rather than `read_file`; (c) tell agents "After writing a file, do NOT read it back to verify — write once and stop." If source material is too large to inline, have the orchestrator read it once and extract the relevant portion, then pass that extracted content as context to the leaf agent. After all leaves complete, verify no corruption: `grep -rcE '^\s+[0-9]+\|' --include='*.go' --include='*.py' --include='*.ts' --include='*.md' .` should return zero hits.

13. **Provider rate limits on concurrent dispatch.** Dispatching 3 leaf agents simultaneously can trigger HTTP 429 rate limits on cloud providers. This is the single biggest risk with parallel leaf execution. Two distinct failure phases:

    **Dispatch-phase rate limits (the parent's side):** If `delegate_task` itself returns a 429, retry only the failed leaves individually (not as a batch) — a single agent running alone rarely hits limits. Plan for 2-3 retry rounds on large trees.

    **Subagent execution-phase rate limits (the subagent's side):** Even with serial dispatch, a subagent that makes many tool calls (reading files, terminal, search) can hit 429 during its own execution. This is most common on aggressive providers (deepseek-v4-flash, some OpenRouter routes). Three recovery strategies, try in order:

    (a) **Rich-context retry.** On re-dispatch, pack as much pre-digested content into the `context` parameter as possible — spec snippets, cross-reference findings, changelog rows, known results of prior inspections. Every `terminal cat` or `search_files` the subagent avoids is one less API call that can hit a rate limit. Provide full quotes of source text, not file paths to read.

    (b) **Narrow scope.** If the initial scope was broad (e.g. "audit all 12 trees"), split the retry into 2-3 narrower slices that each touch fewer files. A subagent that only needs to verify 3 trees makes ~50% fewer tool calls than one checking all 12.

    (c) **Fall back to direct work.** When ALL parallel subagents fail with 429 and serial retries also struggle, the parent agent should write the deliverable directly from its own accumulated context (files read, changelog parsed, findings seen). Signs to switch: (i) subagent consistently fails before producing output, (ii) you already read enough files yourself to write a defensible deliverable, (iii) the work is read-only (audit, review, analysis) where you don't need fresh tool output. Do NOT keep dispatching the same subagent — each retry burns API calls on re-reading context rather than producing output.

14. **Inconsistent code conventions across leaves.** Independent leaf agents will produce code with different naming styles, import organizations, error-handling patterns, and file headers. Interface contracts cover the API surface but not internal style. Prevention: include a brief coding-conventions block (naming, imports, error handling) in every orchestrator document and pass it in every dispatch context. After integration, run `gofmt`/`prettier`/`ruff` globally to normalize.

15. **Stray artifacts from leaf agents.** Implementation agents leave debug print statements, TODO comments, placeholder values, commented-out code, and "End of Task" markers in their output. The review agent must check for these — add "no debug artifacts, no TODOs, no placeholder values" to the review checklist.

16. **Heredocs in execute_code fail silently.** If orchestrators or leaf agents use `execute_code` for batch file operations, heredoc syntax (`cat > file << 'EOF'`) causes "unterminated string literal" errors in Python. Use `write_file` for content creation and `terminal("cat temp.md >> target.md")` for appending. Never embed heredocs inside `execute_code` terminal calls.

17. **`grep -c` / `grep -q` zero-match silently aborts `&&` chains.** A verification step like `grep -rcE '...' --include='*.go' . && git add . && git commit ...` BREAKS when the check correctly finds zero matches: `grep -c` exits 1 on no matches, so the `&&` chain stops and `git add`/`git commit` never run — the change is written but never committed, with no error surfaced. This session actually lost a commit this way. Fix: never gate `git add`/`git commit` behind a `grep` that may legitimately return 0. Either (a) run the check separately and inspect its output, then commit unconditionally; (b) use `grep -c ... ; git add . && git commit ...` (semicolon, not `&&`, so the chain continues regardless of grep's exit code); or (c) invert with `if ! grep -q ...; then :; fi`. Prefer (a) — verify, then commit as a separate deliberate step.

18. **Markdown / docs trees: extend the corruption check and drop code-only steps.** When the plan tree authors or reconciles DOCUMENTS (e.g. a GDD of .md files) rather than code, the same structure works but two adjustments apply: (a) the line-number corruption check glob (Pitfall 12) must include `*.md` — `grep -rcE '^\s+[0-9]+\|' --include='*.md' <tree> .` — because `write_file`/`patch` on markdown can still bake `  N|` prefixes if a leaf agent feeds `read_file` output into a doc; (b) TDD, build/test runs, and `gofmt`/`prettier`/`ruff` normalization do NOT apply — replace "run tests" with "verify cross-references resolve to existing files (loop the cited paths, confirm each exists)" and "confirm no broken relative links." Leaves still must NOT commit; the orchestrator reviews in-session and commits.

19. **Orchestrator patching a file a subagent already edited = stale read-state mismatch.** After concurrent leaf agents return, the orchestrator often does a small follow-up edit (e.g. fixing a stray comment, tightening one line) on a file a leaf just wrote. The patch tool warns: "subagent modified files the parent previously read — re-read before editing" and the resolved_path. PATCHING AGAINST YOUR OLD read (read_file pagination or a pre-dispatch read) CAN MISMATCH and silently fail or corrupt. Fix: before any orchestrator-side `patch`/`write_file` on a file a subagent touched, RE-READ THE WHOLE FILE IN-SESSION (full read_file, not offset pagination) so your old/new strings match the current on-disk content. This is separate from Pitfall 12 — it is about stale parent read-state vs subagent writes, not line-number prefixes. When multiple leaves touch the same doc (rare but possible for adjacent sections), serialize: review each leaf's output, then apply orchestrator edits only after re-reading the merged result.

20. **Docs-only plan trees commonly ship with incomplete orchestrator sections.** When writing a plan tree for documents (GDD, specs, audits) rather than code, you naturally focus on content — which doc needs what edit, what the new spec should say, what status marker to bump. This makes it very easy to skip the PROCESS sections in orchestrator documents: Dispatch Protocol, Interface Contracts, Review Checklist, Coding Conventions, and Integration Test Plan are the most commonly forgotten. In the worked example (`plans-ds4f/`), a template compliance reviewer found 4 of 5 branch orchestrators missing the Dispatch Protocol, and all 5 were missing at least one required section. In the `plans-glm/` forest (12 trees), an `execute_code` grep scan caught 5 of 12 masters missing Dispatch Protocol and/or Coding Conventions before dispatch. **Prevention:** after writing the entire tree, run the structural compliance scan — do NOT verify by memory:

    python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py plans/feature-name --strict-leaves

    The script walks every `master.md`/`orchestrator.md` (checking for `## Dispatch Protocol`, `## Interface Contracts`, `## Child Index`, `## Review Checklist`, `## Coding Conventions`, `## Completion Tracking Table`, `## Integration Test Plan`) and every leaf (checking for "Do NOT commit" and, with `--strict-leaves`, a Self-Verification checklist). Patch any gaps, re-run until `ALL TREES COMPLIANT: True`. A plan tree with content-only orchestrators forces the executing orchestrator agent to guess its own workflow, which wastes context and produces inconsistent results.

21. **Inventing spec values that contradict the source (paraphrase-drift).** Translating prose specs into frozen structs/threshold tables invites paraphrase: the `plans-glm/` session invented a single `Regard int` where the GDD specified 5 float dimensions, and fabricated tier thresholds where the GDD keyed on fact counts. Both survived the structural scan (sections present, values wrong). **Prevention:** (a) quote the spec verbatim in a `// SPEC (file:line, [STATUS]): <text>` comment at every frozen contract; (b) never invent threshold tables/enum members "derived from the narrative" — record the derivation as an OPEN-QUESTION with a documented default; (c) after authoring, dispatch contract-verification digest subagents (Review Protocol §"Contract Verification Digests") that re-read the source spec and diff it against the frozen contracts.

22. **Design drift between sibling sessions (post-authoring spec movement).** On an active project, the design doc is a moving target. A parallel session (another agent, a human, a `plans-ds4f/` doc-completion tree) may ratify new constants, cut a system, or rename a field *after* you read the spec but *before* you execute the plan. Your plan's contracts were faithful at authoring time but are now stale — and neither the structural scan (tier 1) nor the contract-verification digest (tier 2, which reads the *current* spec file) will catch it if you don't think to re-read. **This happened in `plans-glm/`:** the Boston hill heights were ratified to different values (Pemberton 24m→34m) by a primary-source-research commit that landed while the plan was being authored; the procgen condition label changed `derelict`→`ruined`; the active-tier cap was unified across 4 docs. None of these were visible by re-reading the current spec file alone — the *changelog* was the only source of the drift. **Prevention:** after the contract-verification digests, run a changelog-review digest (Review Protocol §"Tier-3 Verification") that reads the project changelog + recent commits and flags any entry touching a plan spec source. This is mandatory on any project with an active changelog (per the `design-plan-consistency` skill / AGENTS.md Rule 2). The cost is one subagent dispatch; the alternative is executing a forest against ratifiable-but-now-wrong values.

23. **Cross-corpus concept replacement (the perspective-pivot class).** When the user makes a sweeping design change that touches a concept appearing across the entire corpus — "this is third-person now, not first-person", "rename all instances of X to Y", "cut feature Z everywhere" — a naive find-and-replace produces three failure modes: (a) it changes the literal phrase but misses semantic equivalents ("FPS" as genre-shorthand, "through the eyes" as idiom, "viewmodel" as technical assumption); (b) it over-corrects, changing references that should stay (a competitor's perspective in a comparison table, narrative-grammatical "first person" voice); (c) it misses the technical consequences (FOV values, camera rig component tree, LOD chain scope, interaction-trace origin). **Pattern that works** (proven in the `plans-glm/` first-person→third-person pivot): dispatch 2 parallel read-only digest subagents — one scanning the GDD, one scanning the plans — each returning a structured report grouping hits by category (hard statements / gameplay assumptions / competitive comparisons / technical specs / out-of-scope false positives). Digest in-session, then apply all amendments in one `execute_code` batch (N find-and-replace edits with per-edit match verification — see `references/cross-corpus-concept-replacement.md`). Verify post-application with a grep that distinguishes intentionally-kept references (e.g. genre labels) from stale ones. This is the same parallel-digest-then-batch-apply shape as the contract-verification digests, but the "contract" is a semantic concept rather than a struct field.

24. **Pre-implemented trees need audit, not just dispatch (post-implementation review).** When a tree was implemented by a parallel agent or a prior session — not dispatched by you — do NOT assume it's complete just because the files exist and tests pass. Dispatch a **post-implementation review subagent** that: (a) reads every source file against the plan's checklist (1-N, each item PASS/FAIL with file:line evidence); (b) runs `go test ./... -short -race`, `go vet`, `gofmt -l`, and both analyzers (mutexio, predid); (c) checks for stray artifacts (fmt.Println, TODO, FIXME, placeholder values); (d) checks for line-number corruption; (e) returns a structured verdict (APPROVED / NEEDS_FIXES / BLOCKED) with specific issues. **This caught a critical gap in the `plans-glm/` session:** the gossip engine (tree #02, implemented by a sibling agent) had 125 passing tests and passed 16/17 checklist items — but the entire `DecayMemory` function (GDD §Fact Decay) was missing, meaning facts never lost confidence or got pruned. The missing function was in the plan spec's review checklist but the sibling agent's leaf scope didn't cover it. The review subagent's structured checklist comparison is what surfaced it. **Prevention:** for any pre-implemented tree, dispatch a review subagent with the full plan checklist before marking it COMPLETE. Fix critical gaps directly (the orchestrator can implement missing functions — it's faster than re-dispatching for small gaps). Minor contract drifts (extra Config fields, changed function signatures with sensible rationale) can be noted without blocking.

25. **Subagent timeout → partial work on disk → orchestrator completes directly.** Subagents implementing large leaves (~90K+ context) can hit the 600s timeout, especially on providers with slower inference or higher latency. The subagent's `delegate_task` returns `status=timeout` — but critically, **the subagent often created most or all files before timing out**; it simply didn't finish the last steps (tests, gofmt, verification). **Do NOT re-dispatch from scratch.** Instead: (a) `find <package> -type f -name "*.go"` to see what landed; (b) `go build ./<package>/...` to check if the core compiles; (c) if it compiles, write the missing pieces (tests, entry points, gofmt fixes) directly as the orchestrator — this is faster than re-dispatching and burning another 600s. This pattern occurred 3× in the `plans-glm/` Wave 1+2 execution (IPC leaf, embed model leaf, identity leaf) — in all 3 cases the subagent had written all source files; the orchestrator completed tests/entry-points in <5 minutes each. If the files DON'T compile or are clearly broken, THEN re-dispatch with narrowed scope (just the broken pieces).

26. **Go floating-point determinism: two silent failure modes.** Subagent Go code with float arithmetic can pass once but fail under `-race`/`-count=N`. Known patterns: (a) `sort.SliceStable` with exact `!=` on float scores — two scores from different float addition orders can differ by 1 ULP; use epsilon comparison (`diff > 1e-12 || diff < -1e-12`); (b) map-iteration-order float accumulation in scoring loops — Go randomizes map iteration order and float addition is non-associative, so `for trait, w := range weights { score += w * value }` yields run-to-run drift; extract and sort map keys first. Both hit `plans-glm/` (intermittent `TestSelectBond_TieBreak`, `TestScoreBondCandidate_Determinism`). Both bugs are invisible when running tests once but surface under `-count=5+` or in CI. Review checklist for Go leaves that rank/sort by float scores: run determinism-sensitive tests with `-count=10`; grep for `!=` in sort comparators and `range` over maps in accumulation loops.

27. **Pre-commit lint hooks (U1000 unused code) block orchestrator commits.** Repos with strict Go linters (golangci-lint, staticcheck U1000) in pre-commit hooks will reject `git commit` if the staged files contain ANY unused function, variable, or import — even transitive ones (e.g. `mathAcosDeg` called only by `horizontalAngleBetween`, which itself is never called from production code). This happened 5+ times across the `plans-glm/` implementation waves (identity, llm, perception, schedule trees). **Prevention:** before staging, run `go vet ./<package>/...` AND manually check for unused code. Remove unused helper functions entirely — do NOT rely on `//nolint:U1000` directives, as some pre-commit hook configurations do not honor them (the hook runs a fresh `staticcheck` pass that ignores inline nolint comments). The pattern for handling this: (a) `go build ./<package>/...` succeeds, (b) `go vet ./<package>/...` passes, (c) `git commit` fails with `U1000: func X is unused`, (d) orchestrator removes the function, (e) commit succeeds. Steps (c-e) can repeat 2-3 times for the same tree if multiple unused functions exist. Save time by running `staticcheck ./<package>/...` (if available) before the first commit attempt.

28. **Subagent-produced code referencing undefined placeholder functions.** Subagents sometimes write code that calls helper functions they never define — using placeholder names like `mathSqrt()` instead of `math.Sqrt()`, `pkgRand` instead of a package-level `var pkgRand = rand.New(...)`, or invented helpers like `weightedChoice()`, `weightedPickIdx()` that are referenced but never implemented. This compounds with pitfall 25 (timeout → partial work) but is a DISTINCT failure mode even when the subagent does not time out: the subagent may produce syntactically plausible code that simply references symbols it forgot to define. **Prevention:** when reviewing subagent output, compile-check IMMEDIATELY (`go build ./<package>/...`) before reading the code for logic review — the compiler is faster and more reliable than human/agent inspection at finding undefined references. The pattern: (a) `find <package> -type f -name "*.go"` to see what landed, (b) `go build ./<package>/...` to get a list of ALL compile errors at once, (c) fix undefined references (often just renaming to stdlib calls or removing dead code), (d) THEN read for logic/style review. Do NOT read every file looking for problems the compiler will list for free.

29. **String-based code assembly via execute_code causes cascading corruption (regex, sed, f-string escape sequences).** When removing unused functions from subagent-produced Go code to satisfy U1000 linter pre-commit hooks (see Pitfall 27), using `execute_code` with Python regex or `sed` to remove function bodies is extremely fragile. Go functions span multiple lines with nested braces, and regex removal leaves orphaned bodies (function removed but body remains), dangling closing braces, or removed signatures while leaving the implementation. In the `plans-glm/` procgen tree, 5 rounds of regex-based removal progressively corrupted `pipeline.go` — each attempt fixed one undefined symbol but introduced a syntax error elsewhere.

    **Same failure mode — escape sequences in f-strings.** Using `execute_code` to ASSEMBLE source code via Python string concatenation introduces a second corruption vector: literal escape sequences like `\\t` in Python f-strings render as the literal characters backslash-t, not as tab characters. When the output is then written to a `.gd` (or `.py`, `.go`, etc.) file, the result contains invisible syntax errors (the Go/GDScript/Python parser sees `\t` as an invalid escape). This happened in the 2026-07-29 Godot session — a full `.gd` file was assembled via f-strings with `\\t` for indentation, producing 100+ parse errors that took a separate fix pass to resolve.

    **Prevention:** (a) use `patch` (mode=replace) with the FULL old_string (including the complete function from comment through closing brace) and new_string (empty or replacement), NOT regex or string concatenation; (b) if the function is multi-line and the exact text is uncertain, re-read the file with `terminal("sed -n 'N,Mp' file")` to get exact line ranges, then use `patch` with the verbatim text; (c) verify with `go build` or the language's equivalent after EACH removal, not after all removals; (d) if the file is too corrupted for incremental patches, use `write_file` to rewrite the entire file with the correct content. The cost of `write_file` on one file is trivial compared to 5 rounds of cascading regex failures. (e) When assembling code via execute_code, use REAL tab characters in the Python source code (`\t` only inside regular strings, NEVER inside f-strings), or better, write the file directly with `write_file` instead of building it via string concatenation.

40. **Subagent test files and side-effects get lost without a `git status` sweep after EACH async notification.**s often create files the orchestrator doesn't know about — test files, support files, EventBus signal additions, `.uid` files. When the orchestrator commits only the files the subagent highlighted in its summary, these extras are left uncommitted on disk. If a later subagent or orchestrator edit touches the same area, the uncommitted files are silently overwritten or orphaned. **This happened FIVE TIMES in the 2026-07-29 session:** (a) crowd_system subagent wrote 27 GUT tests (376 lines) — caught from async notification; (b) romance_system subagent wrote 11 tests AND modified `event_bus.gd` adding 2 signals — caught from `git diff --stat`; (c) skill_system subagent wrote 20 tests + added 9 signals to `event_bus.gd` — caught from `git ls-files --others`; (d) npc_combat_tactics subagent wrote 16 tests (172 lines) — caught from async notification; (e) fatigue_system subagent wrote 22 tests (296 lines) — caught from async notification. **Total: 96 test functions (178+ assertions) would have been lost without post-notification sweeps.** **Prevention:** after EACH subagent async delegation notification arrives, run `git status --short` AND `git diff --stat HEAD` to find all untracked and modified files. Subagents do NOT report all files they touch — their summaries focus on the implementation file, not test files, not signal additions to shared autoloads. Stage and commit all relevant files from each subagent's output before processing the next notification or moving to the next task. This is a recurring, high-value pattern for GDScript projects where subagents commonly add signals to `event_bus.gd` or create test files alongside the implementation.



42. **Visual/coordinate fixes require visual verification — don't guess iteratively.** When fixing visual issues (model positioning, capsule offsets, animation placement), iterative code-guess-test cycles are extremely inefficient. Each round-trip (guess a number → user tests → reports "still wrong") costs 5+ minutes. Instead: (a) use Godot MCP servers to read actual runtime transforms (BodyMesh position, capsule offset, model AABB); (b) use computer_use screenshots to verify the visual result; (c) calculate the exact offset from real data. If MCP servers aren't installed, install the Godot AI plugin (`hi-godot/godot-ai` on GitHub → copy `addons/godot_ai` into project → enable in Project Settings → Plugins). This gives programmatic access to node properties, transforms, and screenshots. The user explicitly flagged this: "would this be something that's done easier visually in godot than having reiterative attempts to 'guess' visual equivalence on your part?" — the answer is yes, always prefer visual verification for spatial/visual fixes.

30. **Survey existing implementation BEFORE decomposing.** When creating a plan tree for a project with existing code, dispatch an exploration subagent FIRST to inventory what's already built. In the Rebellion Godot port session, the `game/` directory contained 1,873 lines of GDScript implementing ~5% of GDD features (core FPS mechanics). Without this survey, the plan would have assumed greenfield development and wasted effort re-specifying already-built systems. Pattern: (a) dispatch read-only survey subagent listing all source files, reading key implementations, and mapping to GDD features; (b) digest findings in-session before writing any plan documents; (c) adjust decomposition scope based on what exists (rewrite vs refactor decision). This prevents the planner from inventing work that's already done or missing critical gaps.

31. **Subagent API key failures require retry with explicit model.** When dispatching exploration subagents, HTTP 401 "Invalid API-key" errors occur intermittently (seen in 2/3 subagents during Rebellion Godot port session). Root cause: default model selection sometimes routes to providers requiring different auth. Prevention: (a) if a subagent fails with 401, immediately re-dispatch with explicit model parameter or let Hermes auto-retry; (b) do NOT assume the task failed — the subagent may succeed on retry; (c) for critical exploration tasks, dispatch 2-3 subagents in parallel so at least one succeeds. The pattern is: dispatch → if 401, re-dispatch → digest successful results. Do not proceed with incomplete data.

32. **Run structural compliance scan BEFORE first commit.** The `check_template_compliance.py` script must run after authoring ALL documents in a tree but BEFORE the first git commit. In the Rebellion Godot port session, two commits were made before running the scan, revealing: (a) all 8 branch orchestrators missing `## Review Checklist` sections, (b) single-leaf branch (09-integration-tests) incorrectly structured as directory with leaf file instead of flat leaf at root. Fixing these required patching 9 files and renaming/moving files post-commit, creating noisy git history. Prevention: (a) write all orchestrators and leaves first; (b) run `python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py plans/<name> --strict-leaves`; (c) fix all issues; (d) re-run until `ALL TREES COMPLIANT: True`; (e) THEN commit. The scan takes <1 second — there's no excuse for skipping it.

33. **Single-leaf plan trees commonly skip Interface Contracts and Architecture Overview.** When authoring simple single-leaf plan trees (master.md + 1 leaf), it's tempting to omit "optional" sections like `## Interface Contract` and `## Architecture Overview` because the scope seems trivial. In the 2026-07-23 codebase review session, 3 of 4 single-leaf masters were missing Interface Contracts (89% completeness) and 1 was missing Architecture Overview (78% for Config Extraction). While these omissions don't block implementation, they violate the template contract and reduce clarity for future readers. **Prevention:** even for trivial single-leaf trees, include all required sections. For Interface Contracts on single-leaf plans, document what the leaf exposes (errors defined, constants added, behavior changes). For Architecture Overview, write 2-3 sentences explaining the system context. The compliance scanner (`check_template_compliance.py`) catches these — run it before committing. Fix effort: ~5 minutes per missing section.

34. **Compliance scanner is strict about "Integration Test Plan" heading.** The `check_template_compliance.py` script requires the exact heading `## Integration Test Plan` — it does NOT accept variants like `## Integration Review Plan`, `## Integration Testing`, or `## Integration Tests`. In the 2026-07-23 session, 3 of 4 plan trees initially failed compliance because they used "Integration Review Plan" instead. **Prevention:** always use the exact template heading `## Integration Test Plan`. If you prefer "review" terminology in your content, keep the heading as-is but you can title subsections differently. The scanner checks for the literal string `## integration test plan` (case-insensitive) in the markdown. See `references/codebase-review-plan-patterns.md` for worked example.

35. **Codebase review sessions produce multiple date-prefixed plan trees.** When reviewing a codebase and creating remediation plans, use date-prefixed directory names under `docs/plans/` (e.g., `20260723-panic-replacement/`, `20260723-config-extraction/`). This keeps review artifacts organized and sortable by date. Pattern: (a) create one tree per remediation theme; (b) prefix with YYYYMMDD for chronological sorting; (c) include index document summarizing all trees; (d) create GitHub issues for architectural concerns that need team discussion. Worked example and patterns documented in `references/codebase-review-plan-patterns.md` from 2026-07-23 session.

36. **Compliance scanner requires exact heading `## Completion Tracking Table`.** The scanner checks for the literal string `## completion tracking table` (case-insensitive). Using `## Completion Tracking` (without "Table") fails compliance. This was the most common heading mismatch in the meept claude-code-parity session (2026-07-24) — 4 of 5 orchestrators initially used the wrong heading. Always use the exact template heading.

37. **Pre-authoring design Q&A prevents plan rewrites.** When the source material (external report, competitor analysis) implies design decisions with meaningful trade-offs, present them as a structured Q&A BEFORE authoring any plan documents. The user's answers change leaf sizing, tree structure, and scope — authoring first means rewriting. Pattern: ≤10 questions per batch, each with Q#/Rec/Impact. Wait for all answers before writing any .md files. This is distinct from Step 6.8 (post-authoring open questions) — this runs BEFORE authoring, not after. Worked example: meept × Claude Code session (2026-07-24) — 7 questions resolved before 14 documents authored, zero rewrites needed.

38. **Plan forests targeting different implementations must be self-contained (no cross-references).** When a project has multiple plan forests for different implementation targets (e.g., `plans-glm/` for a Go sidecar, `plans-godot/` for a Godot client), NEVER reference one forest from another. Each forest should reference only the shared source of truth (the GDD/spec), not sibling plan trees. Three failure modes: (a) **Progress contamination** — referencing `plans-glm/02-gossip/` from `plans-godot/` can imply the gossip engine's implementation status carries over, when the Godot plans are all PENDING; (b) **Coupling** — if `plans-glm/` is archived or restructured, every cross-reference in `plans-godot/` breaks; (c) **Scope confusion** — an implementer reading `plans-godot/` shouldn't need to open `plans-glm/` to understand their task. **Prevention:** after authoring or auditing a plan forest, grep for sibling forest references: `grep -rn "plans-glm\|plans-godot\|plans-<other>" plans-<this>/`. Replace each with a GDD spec citation (e.g., "Per GDD §04-npc/04-gossip-and-reputation.md" instead of "Per plans-glm/02-gossip/"). The GDD is the shared contract; plan trees are implementation-specific. Worked example: Rebellion session (2026-07-24) — 10 cross-references removed from plans-godot, all replaced with GDD citations.

39. **Dual-audit pattern for plan completeness (completeness + cross-implementation gaps).** When auditing a plan forest against its spec, dispatch TWO parallel subagents: (a) **Completeness auditor** — reads every plan leaf against the GDD spec, reports missing features, wrong architecture, stale references; (b) **Cross-implementation gap auditor** — reads the sibling implementation's plan trees (e.g., Go sidecar plans) and identifies data/capabilities the target implementation must consume but has no plan for. The cross-implementation auditor catches a distinct class of gap: the sidecar produces data (GossipEvents, QuestUpdates, OcclusionData, NPC identity) that the client must handle, but no client plan leaf mentions it. Neither audit alone is sufficient — the completeness auditor checks "does the plan cover the GDD?" while the gap auditor checks "does the plan cover what the OTHER half of the architecture produces?" Worked example: Rebellion session — completeness audit found 3 CRITICAL + 9 HIGH gaps; gap audit found 4 CRITICAL + 7 HIGH gaps (only 2 overlapped). Together they caught 21 unique issues.

## Skill Maintenance

This skill has files that must stay synchronized:
- `SKILL.md` — canonical guidance
- `templates/master-template.md`, `templates/leaf-template.md` — document templates
- `scripts/check_template_compliance.py` — structural compliance scan (Step 6 / Pitfall 20)
- `references/tests-first-gate.md` — tests-first gate recipe (Step 5.5, Dispatch Protocol Phase 0, Pitfall 46); keep master-template Phase 0 / Test Gate and the scanner's `## Test Gate` requirement in sync
- `references/partial-plan-trees.md` — incomplete-tree avoidance
- `references/parallel-plan-authoring.md` — subagent-dispatched plan authoring
- `references/contract-verification-digests.md` — tier-2 contract digest recipe (Pitfall 21)
- `references/changelog-file-format.md` — changelog table convention
- `references/changelog-review-digests.md` — tier-3 drift digest recipe (Pitfall 22)
- `references/cross-corpus-concept-replacement.md` — sweeping rename recipe (Pitfall 23)
- `references/wave-execution-patterns.md` — dependency-ordered execution; plus `references/wave-execution-2026-09-11.md`.
- `references/asset-pipeline-plan-pattern.md` — non-code ops trees
- `references/execution-protocol-2026-09.md` — post-execution protocol lessons (meept 2026-09-05 four-tree run). Also `references/quickplan-cascade-campaign-2026-09.md` — classifier-campaign → plan-tree arc: 50× head-lr underdose diagnosis, deterministic chain-credit, adjudicated-label promotion, plateau-as-contract. Read with the pitfall additions below.
- `references/godot-port-planning.md` — UE5/Unity → Godot porting
- `references/gap-analysis-forest-pattern.md` — external report → forest
- `references/codebase-review-plan-patterns.md` — date-prefixed review forests; omitted-section snippets
- `references/gdscript-bulk-dispatch.md` — 10+ parallel GDScript dispatch; orchestrator-completes-directly (429 recovery); async notification sweep (`git diff --stat HEAD` + `git ls-files --others` after EVERY completion notification — subagents under-report test files and EventBus signal edits)
- `references/intent-gate-forensics-2026-09-05.md` — under agent-benchmark-harness: 13-run e2e campaign where the run-narrative ("quota") was overturned by artifact forensics (real cause: empty-content fallback rotations on a shared classifier client); includes the digest/context-conditioned-rules fix pattern for canned-clarification failures and e2e assertion-heuristic pitfalls (`?`-contains false positives).

## Session Pitfall Additions (2026-09-05, meept research-audit-tools tree)

- **Background-process notifications from in-flight subagents are progress telemetry, NOT failures.** Long leaves run their own shell verifications; the orchestrator sees `proc_*` exit notifications (possibly exit 127 from a malformed trailing echo in the subagent's own command). Do NOT re-dispatch on this signal alone. `tail` the log file named in the command (usually `/tmp/*.log`): it holds mid-flight test results (a test failing at iteration N, passing at N+1). The verdict remains the subagent's return PLUS the orchestrator's own re-run.
- **Concurrent same-package TDD leaves transiently break compile.** A tests-first leaf leaves RED test files referencing its not-yet-written implementation; while it runs, whole-package `go build`/`go test` fail for every sibling. Re-verify by reading diffs; run targeted `go test -run 'OtherLeafPattern'` once the package settles. Never re-dispatch a healthy leaf because a sibling's RED file broke the build. A sibling SESSION can also commit to main mid-tree with its own half-written files — classify as out-of-scope, verify your scope in isolation, wait out their churn.
- **Serialize leaves that edit the same shared file** (e.g. two `components.go` registration blocks): separate waves, second dispatches only after the first is committed. Concurrent edits to one file are how integration bugs happen (Pitfall 19 covers stale read-state; this prevents the collision).
- **Verify agent API-drift claims via primary sources before accepting.** A leaf reporting "the brief's library API is wrong" may be right — confirm each claim with `go doc <pkg>` before amending contracts. Worked example: leaf correctly overrode a brief's `pdf.NewReader(io.Reader)` with the real `io.ReaderAt` signature; orchestrator confirmed via go doc, recorded drift in the tracking table.
- **License-gate new deps in the dispatch brief; re-verify at review.** Put in the leaf brief: "read LICENSE under `go env GOMODCACHE`; if GPL/AGPL STOP and report". Orchestrator re-reads the LICENSE file itself at review (trust but verify, same as API drift).
- [ ] The tail checklist (Pitfalls 21-29, 38-39, 42) lives in `references/authoring-checklist.md` — run it from there; this file stays under the 100K cap.
- **Byte-layout contracts + RED-BUILD-BLOCKED + verifier-briefing (2026-09-11 classi-fly run):** see `references/parallel-sibling-leaf-contracts.md` — exact shapes in every consuming brief, foreign-reader round-trip inside the writing leaf, RED-BUILD-BLOCKED dispatch for sibling-on-sibling leaves, verification leaf briefed with orchestrator-known issues + pin-flip closure, in-repo probe tests instead of /tmp scripts in deny-gated runs, and 1-6-line cross-leaf gaps fixed by the orchestrator directly.
- [ ] Every branch has interface contracts between its children (even single-leaf trees — see Pitfall 33)
- [ ] Architecture Overview present in all orchestrators (even single-leaf trees — see Pitfall 33)
- [ ] Every leaf estimated at 110K context or less (with headroom)
- [ ] No leaf splits a cohesive unit across documents
- [ ] Every document has embedded dispatch/review instructions
- [ ] Dependency graph has no cycles
- [ ] Concurrent leaves identified and batched in groups of 3
- [ ] Tracking tables present in all orchestrator documents
- [ ] Integration review planned at each branch level and at root
- [ ] All leaf tasks follow bite-sized TDD format with exact paths and complete code
- [ ] No leaf task includes commit steps (orchestrators only)
- [ ] Every dispatch instruction tells implementation agents "Do NOT commit"
- [ ] Dispatch contexts inline relevant source code (no "read the file" instructions that lead to line-number corruption)
- [ ] Orchestrator documents include a coding-conventions block for style consistency across leaves
- [ ] Review checklist includes "no debug artifacts, no TODOs, no placeholder values"
- [ ] Post-integration plan includes format normalization (gofmt/prettier/ruff) and line-number corruption check
- [ ] All child documents referenced in Child Index exist on disk (see `references/partial-plan-trees.md`)
- [ ] For GDScript subagent dispatches: expect ~40% timeout rate on 300+ line leaves (GDScript files are large and subagents spend many calls reading existing files); check disk with `git status --short` + `ls -la` before re-dispatching; complete missing pieces directly if files landed. GDScript doesn't need compilation to verify — use `grep -cE 'TODO|FIXME|pass\\s*#'` and `grep -rcE '^\\s+[0-9]+\\|'` (corruption check). Legitimate `pass # comment` in match/case is NOT a stub. `godot --check-only` can verify parse errors but may time out on projects with heavy imports (60s+).
- [ ] **Godot FBX→.tres pipeline requires Blender intermediate (FBX→GLB→.tres), not direct FBX→.tres.** Godot headless `-s script.gd` cannot load raw .fbx files — `ResourceLoader` returns "No loader found for resource". The ufbx importer only runs in editor mode. When a leaf or pipeline needs to convert Mixamo FBX animations to Godot .tres: (a) Blender batch converts FBX→GLB with `export_yup=False`, (b) `Godot --headless --import` registers the GLBs, (c) then Godot headless extraction loads GLBs and saves .tres. Skip the `--import` step and the extraction silently produces zero output. For 150+ files the whole pipeline takes ~5 minutes.
- [ ] After each subagent batch completes (not just at final commit): run `git status --short` to catch uncommitted test files, support files, or side-effect edits the subagent created but didn't highlight (Pitfall 40). **For GDScript projects specifically:** also check `git diff --stat HEAD` for modifications to `event_bus.gd` (subagents commonly add signals) and `git ls-files --others --exclude-standard` for untracked test files (subagents commonly create `test_<system>.gd` alongside the implementation). Commit ALL files from each subagent's output before processing the next async notification.
- [ ] When the orchestrator implements a leaf directly (rate-limit recovery): do NOT use `execute_code` to assemble code via Python string concatenation — use `write_file` directly or assemble with real tab characters. f-string `\\t` produces literal backslash-t in output files (Pitfall 29 variant)
- [ ] For visual/coordinate fixes (model positioning, capsule offsets, animation placement): use Godot MCP or computer_use screenshots to verify — do NOT guess iteratively (Pitfall 42)
