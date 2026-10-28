# Parallel Plan Authoring — Subagent-Written Plan Trees


When to use: writing 100+ plan documents via parallel subagents.
Lesson: batch shape, rate-limit handling, orchestrator-finishes-last-file recovery, key lessons.
> Session: 2026-08-04, AgentAudit project.
> Task: author a complete 4-phase, 109-file hierarchical plan tree using
> parallel subagent dispatch. Covers both single-phase (27 files) and
> multi-phase forest (109 files) patterns.

Read alongside SKILL.md:
- Step 6.5 "Authoring a Forest (5+ plan trees at once)"
- references/multi-tree-forest-pattern.md (forest authored by the main model)
- references/partial-plan-trees.md (detecting and recovering incomplete trees)

---

## When to Use This Pattern

Use parallel subagent plan authoring when ALL of these are true:

1. The plan tree has 3+ independent branches (subsystems with minimal cross-dependencies)
2. Each branch needs 4-8 leaf documents (too much for the main model to write sequentially in one session)
3. The interface contracts between branches are well-defined BEFORE dispatch (you've already written the master orchestrator with contracts)
4. The branches can be authored independently — branch A doesn't need to read branch B's leaves to write its own

Do NOT use this pattern when:
- The plan is a single tree (just write it yourself)
- Branches have heavy inter-dependencies (the contracts aren't stable yet)
- The master orchestrator isn't written yet (contracts aren't defined)

## The Pattern

### Step 1: Write the master orchestrator(s) FIRST

The main model writes `master.md` with:
- All interface contracts (Contract 1..N) fully specified
- Shared type definitions (Go structs, TypeScript interfaces, JSON schemas)
- Child document index listing every branch and its leaf files
- Coding conventions
- Integration test plan

This is the critical foundation. Subagents need these contracts to write
leaves that integrate. If contracts are ambiguous, the subagent-written
leaves won't match each other.

For multi-phase forests, write each phase's master.md before dispatching
that phase's branches. Phase N+1's master can reference types from Phase N's
implementation (which is already committed and running).

### Step 2: Dispatch one subagent per branch

Each `delegate_task` call gets:
- **Goal:** "Write the complete hierarchical plan tree for [branch name]"
- **Context:** Project description, tech stack, project root path, and
  EXPLICIT instructions to read the master orchestrator and relevant
  research docs before writing
- **File list:** Exact filenames and paths to create (orchestrator.md +
  N leaf files)
- **Template paths:** Point to the leaf-template.md and master-template.md

Key context to inline or point to:
- The master.md path (subagent reads it for contracts)
- Research doc paths (subagent reads for architecture decisions)
- The leaf/master template paths (subagent follows the format)
- Tech stack details (Go version, Swift version, React version)
- Project structure conventions (directory layout)

### Step 3: Monitor and handle the three failure modes

| Failure | Cause | Recovery |
|---------|-------|----------|
| **Timeout (600s)** | Branch has 6-10 leaves, subagent ran out of time | Check disk — subagent likely wrote 80-100% of files before dying. Write the last 1-2 files directly. |
| **Rate limit (429)** | Too many concurrent subagents on same provider | Branch returns empty or with only orchestrator. Wait for rate window to clear, then re-dispatch ONE AT A TIME, not in parallel. |
| **Partial write** | Subagent crashed mid-tree or transient write error | Check which files exist. Re-dispatch only the missing files, or write them directly. |

**Recovery for missing files:**
1. `search_files` the branch directory for `*.md` to see what exists
2. `read_file` the first few lines of each file to verify non-empty
3. For each missing file, either dispatch a targeted subagent OR write
   it directly (1-2 files: always write directly — it's faster)

### Step 4: Rate limit mitigation during multi-phase authoring

Unlike implementation dispatch where rate limits are caused by many
internal tool calls (reading files, running builds), plan-authoring
rate limits come from the raw number of concurrent subagents.

**Staggered dispatch pattern for large forests (9+ branches):**
- Dispatch 4 branches in parallel (not 9)
- Wait for 2-3 to complete
- Dispatch the next batch (including re-dispatches of failures)
- Never dispatch more than 4-5 simultaneously on aggressive providers

**Serial re-dispatch for rate-limited branches:**
When a branch fails with 429, re-dispatch it ALONE (not in a batch).
A single serial subagent usually stays under the per-request limit.

### Step 5: Structural completeness check after all branches return

Run a single batch check across the entire tree:

```python
required_orch = ["## Dispatch Protocol", "## Interface Contracts",
    "## Review Checklist", "## Coding Conventions",
    "## Completion Tracking Table", "## Integration Test Plan"]
required_leaf = ["## Meta", "## Goal", "## Tasks",
    "## Self-Verification Checklist"]
# Check for line-number corruption
corruption = re.findall(r'^\s+\d+\|', content, re.MULTILINE)
```

This catches: missing files, truncated files, subagents that skipped
required template sections, and line-number corruption from read_file.

## Worked Example: AgentAudit Single Phase (2026-08-04, Phase 1)

4 subagents dispatched simultaneously, one per branch:

| Branch | Files to create | Duration | Result |
|--------|-----------------|----------|--------|
| 01-go-backend | orchestrator + 5 leaves | 351s | All 6 files created |
| 02-swift-agent | orchestrator + 6 leaves | 600s (timeout) | 5 of 7 files, last 2 written directly |
| 03-dashboard | orchestrator + 7 leaves | 525s | 8 files (1 transient write error, file present on disk) |
| 04-analysis | orchestrator + 4 leaves | 363s | All 5 files created |

## Worked Example: AgentAudit Multi-Phase Forest (2026-08-04, Phases 3+4)

9 branches dispatched simultaneously across two phases:

| Branch | Phase | Files expected | Result |
|--------|-------|----------------|--------|
| 09-windows-agent | 3 | 6 | Timeout, 5/6 then 6/6 on re-check |
| 10-linux-agent | 3 | 6 | 429 rate limit (0 files) — re-dispatched serially |
| 11-central-server | 3 | 6 | Timeout at 600s, all 6 files written before timeout |
| 12-cross-user-analysis | 3 | 6 | Complete |
| 13-team-dashboard | 3 | 6 | Complete |
| 14-deployment | 4 | 6 | 429 rate limit, then completed on re-dispatch |
| 15-auth-rbac | 4 | 6 | 429 rate limit (0 files) — re-dispatched serially |
| 16-compliance | 4 | 6 | Complete |
| 17-integrations | 4 | 5 | Complete |

**Rate-limit stats:** 3 of 9 branches hit 429 (33%). All recovered via
serial re-dispatch. No data lost — rate-limited branches had 0 files,
so there was nothing to recover from disk.

**Timeout stats:** 2 of 9 branches hit 600s timeout (22%). Both had
written all or nearly all files before timing out on their summary report.
The timeout is on the API call budget, not on file writes.

**Final structural check:** 55 files across Phases 3+4, zero issues.

### Grand total across all 4 phases

| Phase | Files | Dispatches | Timeouts | Rate limits | Direct writes |
|-------|-------|------------|----------|-------------|---------------|
| Phase 1 | 27 | 4+1 | 1 | 0 | 2 files |
| Phase 2 | 27 | 4+1 | 1 | 0 | 1 file |
| Phase 3 | 31 | 5+1 | 2 | 1 | 0 files |
| Phase 4 | 24 | 4+1 | 0 | 2 | 0 files |
| **Total** | **109** | **17** | **4** | **3** | **3** |

## Key Lessons

0. **`delegate_task` batch shape: every `tasks[]` element needs its own `goal`.**
   Batch dispatch fails with "Task 0 is missing a 'goal'" when a task
   carries only `context`, and a top-level `context` without `goal` fails
   with "Provide either 'goal' (single task) or 'tasks' (batch)". Correct:
   `tasks: [{goal: "<one line>", context: "<full brief>"}, ...]`. A
   malformed batch burns a turn per retry (4 failed calls before
   diagnosis, 2026-09-05 grok-bot-gap session) — check the shape before
   dispatching multi-tree forests.

1. **The orchestrator is faster than a subagent for 1-2 files.** When a
   branch times out with 5/6 files done, writing the last file directly
   takes 30 seconds. Re-dispatching takes 10 minutes and may timeout again.

2. **Rate limits during plan authoring are per-dispatch, not per-tool-call.**
   The fix is fewer concurrent dispatches, not richer context. 4 parallel
   is safer than 9 parallel on most providers.

3. **Subagents that timeout on plan writing still persist their files.**
   Same as implementation timeout behavior (Pitfall 25 in SKILL.md).
   Always check disk before re-dispatching. The timeout often happens
   on the summary report, not on the actual file writes.

4. **The structural completeness check is the safety net.** It catches
   everything: missing files, truncated content, wrong template sections,
   line-number corruption. Run it once at the end, not per-branch.

5. **Dispatch context for plan writing needs the TEMPLATES inline.**
   Telling a subagent "use the leaf template at /path/to/template.md"
   costs one file read. Inlining the template structure (section names
   + format) in the context parameter saves that read and ensures
   compliance.

6. **Duration scales with file count.** Budget ~60-70s per leaf document.
   A 6-leaf branch will take ~400-450s. A 10-leaf branch WILL timeout.
   For 10+ leaf branches, split into two subagent dispatches.

7. **Multi-phase forests are viable but require staggered dispatch.**
   Dispatching all 9 branches of Phases 3+4 simultaneously caused 3 rate
   limit failures. Better approach: dispatch 4, wait for completion,
   dispatch the next 4, then handle failures serially.

## What NOT to Take from This

- **Don't dispatch plan authoring for small trees.** If the plan is 1-2
  branches with 3-5 leaves total, write it yourself. The dispatch overhead
  (reading research docs, crafting context) takes longer than just writing.

- **Don't skip the master orchestrator.** Without stable contracts, each
  subagent will invent its own types and API shapes. Integration fails.

- **Don't review every leaf file's content during authoring.** The main
  model's job is to verify structure (files exist, non-empty, contracts
  referenced). Content review happens when the implementation agents consume
  the leaves — that's when mismatches surface and get fixed.

- **Don't assume subagent self-reports are accurate.** One subagent reported
  a failed write, but the file was on disk. Another may report success but
  produce an empty file. Always verify with filesystem tools.
