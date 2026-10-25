# Parallel Plan-Tree Authoring via Subagents

> Session: 2026-08-04, AgentAudit project.
> Task: create a 27-file Phase 1 MVP plan tree (1 master + 4 branches + 22 leaves).
> Technique: write the master orchestrator directly, then dispatch N subagents
> to author the N branch trees simultaneously.

## When to Use This Pattern

Use when the plan tree has 3+ independent branches and writing all documents
sequentially would exceed the orchestrator's turn budget. The pattern:

1. You (the main model) write `master.md` directly — it defines the interface
   contracts that all branches must implement to.
2. Dispatch one subagent per branch via `delegate_task`, giving each the
   master's contracts + relevant research docs as context.
3. Each subagent reads the research, reads the master, then writes its full
   branch tree: `orchestrator.md` + all leaf documents.
4. After all subagents return, run a structural completeness check (see
   `scripts/check_plan_tree.py`) to verify every file has required sections.

## Dispatch Context — What to Inline

Each plan-authoring subagent needs:

- **Research doc paths** — exact file paths to read for domain context
- **Master orchestrator path** — the contracts they must implement to
- **Leaf/master template paths** — the hierarchical-planning skill templates
- **Exact output file paths** — `docs/plans/<phase>/<branch>/orchestrator.md`,
  `01-name.md`, `02-name.md`, etc.
- **Tech stack** — language, framework, key dependencies
- **Architecture summary** — 2-3 sentences on how this branch fits the whole

Example dispatch (abbreviated):

```
goal: "Write the complete hierarchical plan tree for the Go backend branch"
context: |
  Read these research docs first:
  - docs/research/02-architecture-and-storage.md
  - docs/plans/phase1-mvp/master.md (interface contracts)

  Create under docs/plans/phase1-mvp/01-go-backend/:
  1. orchestrator.md (branch orchestrator)
  2. 01-types-and-schema.md (leaf)
  3. 02-storage-layer.md (leaf)
  ...

  Use templates at:
  - ~/.hermes/skills/.../templates/leaf-template.md
  - ~/.hermes/skills/.../templates/master-template.md
```

## Concurrency

Dispatch all branch subagents in a single `delegate_task` batch call (the
`tasks` array). They run in parallel. Branches with no inter-dependencies
at the code level (e.g., Go backend + Swift agent communicate via HTTPS
contract only) can be authored simultaneously.

For the AgentAudit session: 4 branches dispatched simultaneously, each
producing 5-8 files. All returned within 6-10 minutes.

## Recovery Patterns

### Subagent timeout with partial output

If a plan-authoring subagent times out (600s limit):

1. Check what files landed on disk (`search_files` for `*.md` in the branch dir)
2. If 80%+ of files exist and are well-formed, write the missing files directly
3. If <50% exist or the orchestrator itself is missing, re-dispatch with
   narrowed scope or write the branch directly

AgentAudit session: the Swift agent subagent timed out after writing 5 of 7
files. A follow-up subagent was dispatched for the 2 missing files. It wrote
1 of 2 before returning. The last file (`06-https-client.md`) was written
directly by the orchestrator in ~2 minutes. Total recovery: ~5 minutes.

### Missing sections in completed files

Run `scripts/check_plan_tree.py` after all subagents return. It scans every
`.md` file for required template sections (Dispatch Protocol, Interface
Contracts, Review Checklist on orchestrators; Meta, Goal, Tasks on leaves)
and reports any missing. Fix directly — re-dispatching for a missing section
header is overkill.

## What NOT to Take from This

- **Don't dispatch subagents for trees with <3 branches.** If the tree has
  1-2 branches, write them yourself — the dispatch overhead exceeds the savings.
- **Don't skip writing the master first.** The master defines the interface
  contracts. Without it, branch subagents will invent incompatible types and
  the integration phase will fail.
- **Don't expect plan-authoring subagents to produce implementation-ready code.**
  Their job is to produce PLAN documents with TDD task stubs, not compilable
  source. The code comes later when implementation agents execute the leaves.
