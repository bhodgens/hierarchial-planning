# Parallel Branch Authoring — Dispatching Subagents to Write Plan Trees


When to use: dispatching subagents to write plan-tree branches.
Lesson: write the master first, fan out one subagent per branch, then structurally validate.
> Session: 2026-08-04, AgentAudit project.
> Task: write a 27-file Phase 1 plan tree (master + 4 branches + 22 leaves)
> + a 27-file Phase 2 plan tree (master + 4 branches + 22 leaves).
> Total: 54 plan documents authored in one session.

This is the PLAN-WRITING counterpart to wave-execution-patterns.md.
That doc covers dispatching subagents to IMPLEMENT code from plans.
This doc covers dispatching subagents to AUTHOR the plan documents themselves.

---

## When to Use

- A plan tree has 3+ independent branches (e.g., Go backend + Swift agent +
  Dashboard + Analysis). Each branch's orchestrator + leaves can be written
  independently as long as the master's interface contracts are defined first.
- The master orchestrator is already written with complete interface contracts.
- Each branch needs 4-10 leaf documents — too much for one agent's context.

## The Pattern

### Step 1: Write the master.md yourself

The master orchestrator defines the interface contracts that all branches
implement against. This MUST be written first — it's the integration surface.
Write it fully with:
- All shared types (Contract section)
- API endpoint definitions
- Store interface signatures
- Child document index with paths, types, dependencies, concurrency groups
- Coding conventions block

This is the one document that cannot be delegated — it's the contract every
branch writes to. ~15-20 min to write.

### Step 2: Dispatch one subagent per branch IN PARALLEL

Each `delegate_task` call gets:
- **Goal:** "Write the complete hierarchical plan tree for [branch name]"
- **Context:** "Read the master at [path] for contracts. Read research doc at
  [path] for architecture. Create files under [branch path]."
- **Explicit file list:** Name every file the subagent must create
  (orchestrator.md + numbered leaves). This prevents the subagent from
  improvising structure.
- **Template paths:** Point to leaf-template.md and master-template.md
- **Code stub requirement:** "Each leaf must have actual [Go/Swift/TSX] code
  stubs in the TDD tasks, not just prose descriptions."

Batch all 4 (or however many) delegate_task calls in a single response block
so they run concurrently.

### Step 3: Handle timeouts and partial writes

Large branches (8-10 leaves, each 20-40KB) will hit the 600s timeout. This
is EXPECTED. Recovery:

1. `search_files` the branch directory — count what landed
2. Verify each file has required sections (Meta, Goal, Tasks, etc.) — a quick
   script checking for section headers catches truncated files
3. If 1-2 files are missing, write them DIRECTLY (don't re-dispatch).
   The orchestrator has full context from writing the master — writing a
   leaf for a known subsystem takes 3-5 min vs 10+ min for re-dispatch + timeout
4. If a branch is fundamentally broken (wrong architecture), re-dispatch
   with clearer context

### Step 4: Run structural completeness check

After all branches return, run a validation pass:

```python
# Check every orchestrator for required sections
required_orch = ["## Dispatch Protocol", "## Interface Contracts",
                 "## Review Checklist", "## Coding Conventions",
                 "## Completion Tracking Table", "## Integration Test Plan"]
# Check every leaf for required sections
required_leaf = ["## Meta", "## Goal", "## Tasks", "## Self-Verification Checklist"]
# Check for line-number corruption
corruption = re.findall(r'^\s+\d+\|', content, re.MULTILINE)
```

This catches: missing sections, truncated files, files that the subagent
claimed to write but didn't, and line-number corruption from read_file →
write_file cycles inside the subagent.

## Timing (observed)

| Phase | Files | Subagents | Timeouts | Direct completions | Wall time |
|-------|-------|-----------|----------|--------------------|-----------|
| Phase 1 | 27 | 4 + 1 fixup | 1 (Swift, 7 files written of 7 — all landed before timeout) | 1 file (06-https-client) | ~15 min |
| Phase 2 | 27 | 4 | 1 (skill-synthesis, 9 of 10 files written) | 1 file (09-synthesis-api-handlers) | ~15 min |

Key observation: even timed-out subagents wrote 90-100% of their files before
dying. The timeout hits on the LAST file, not the first. Always check disk
before re-dispatching.

## What Makes This Work

1. **The master.md is the contract.** Each subagent reads it and writes to
   the exact types/signatures defined there. No ambiguity about interfaces.

2. **Research docs feed the context.** Each dispatch points to specific
   research doc sections. The subagent reads the research and encodes it
   into TDD tasks with real code stubs.

3. **Explicit file lists prevent structure drift.** Telling the subagent
   "create these exact files: 01-types.md, 02-storage.md, ..." prevents
   it from inventing different names or splitting differently.

4. **The 600s timeout is not a failure mode.** A subagent writing 20-40KB
   markdown documents typically completes 80-90% before timeout. The
   orchestrator writes the last 1-2 files directly.

## What NOT to Do

- **Don't dispatch subagents without a written master.md.** Without contracts,
  each branch invents its own types and the integration phase fails.
- **Don't re-dispatch timed-out branches from scratch.** Check disk first —
  90% of the work is usually there.
- **Don't skip the structural completeness check.** A subagent can produce
  files that LOOK complete but are missing required template sections.
- **Don't dispatch more than 4-5 branches simultaneously.** Beyond that, the
  notification queue becomes hard to track and partial-write recovery gets
  complex. If you have 8 branches, do two waves of 4.
