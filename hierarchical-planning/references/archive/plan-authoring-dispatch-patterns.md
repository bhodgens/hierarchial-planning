# Plan Authoring Dispatch Patterns — Writing Large Plan Trees via Subagents


When to use: writing large plan trees via subagent batches.
Lesson: patterns for subagents authoring plan documents in parallel phases.
> Session: 2026-08-04, AgentAudit project.
> Task: author 4 plan phases (116 plan documents total) by dispatching
> subagents to write branch orchestrators + leaf documents.
> This doc captures the patterns that emerged when subagents write PLAN
> DOCUMENTS (not code) in parallel batches.

Read alongside SKILL.md:
- The "Writing Plan Trees" section (dispatch during the planning phase)
- references/wave-execution-patterns.md (covers dispatch during IMPLEMENTATION phase — different failure modes)

---

## The situation

4 phases, each with 4-5 branches, each branch with 5-10 leaf documents.
Each leaf is 15-40KB of structured markdown (TDD tasks with code stubs,
interface contracts, review checklists).

Total: 116 plan documents across 4 root orchestrators.

## Key patterns

### 1. Plan-tree authoring dispatch is NOT the same as code-writing dispatch

Code-writing subagents (implementation phase) hit 600s timeouts because
they compile, test, iterate. Plan-writing subagents hit timeouts because
they write many large files sequentially — each write_file call takes
3-10s for a 25KB document, and a 10-file branch takes 60-100s of pure
I/O before accounting for reading context and thinking.

**Impact on sizing:** a 10-file branch (like skill-synthesis with 9 leaves
+ 1 orchestrator) is at the edge of the 600s timeout. Expect 1-2 timeouts
per 10-file branch. A 5-6 file branch is safe.

### 2. Rate limits (429) are the dominant failure mode for 4+ parallel branches

When dispatching 4+ subagents simultaneously, 1-3 will hit HTTP 429 before
writing any files. The rate limit window appears to be ~60s — if a burst
of 4+ delegate_task calls lands within the same window, the later ones
fail.

**Recovery pattern for rate-limited plan subagents:**

```
1. Check disk: search_files for *.md in the branch directory
2. If 0 files: subagent failed before writing anything
   → Do NOT re-dispatch immediately (will 429 again)
   → Wait for other running subagents to finish, THEN re-dispatch
   → Or write the missing branch directly as orchestrator
3. If partial files: subagent wrote some before dying
   → Check which are complete (size > 10KB, has ## Tasks section)
   → Write missing files directly as orchestrator
```

### 3. Orchestrator-completes-directly works better for plan docs than code

Unlike code-writing (where the orchestrator completing timed-out work
requires understanding the codebase), plan-document writing is pure
content generation. The orchestrator has the master.md with interface
contracts and the research docs — it can write a leaf document directly
in 2-3 minutes.

**Decision rule for plan-tree authoring:**
- Subagent wrote 0 files + rate limited → wait, then re-dispatch with 2-3 branches max
- Subagent wrote partial files + timed out → orchestrator writes missing files directly
- Subagent wrote all files → review and commit

### 4. Batch size matters: 3-4 concurrent subagents is the sweet spot

Observed failure rates by batch size (plan-tree authoring):

| Concurrent subagents | Branches dispatched | Rate-limited | Timed out | Completed clean |
|---------------------|---------------------|-------------|-----------|-----------------|
| 4 (Phase 1)         | 4                   | 0           | 1 (Swift, 7 files) | 3 |
| 4 (Phase 2)         | 4                   | 0           | 1 (Synthesis, 10 files) | 3 |
| 9 (Phase 3+4)       | 9                   | 2-3         | 0         | 4-5 |

**Recommendation:** dispatch 3-4 subagents max per batch. If you have
9 branches to write, do 3 batches of 3, not one batch of 9.

### 5. Structural completeness check script

After all branches return, run a single check across the entire phase:

```python
# Checks every orchestrator has required sections, every leaf has required sections,
# and no line-number corruption exists. Returns issues list.
import os, re

required_orch = ["## Dispatch Protocol", "## Interface Contracts",
                 "## Review Checklist", "## Coding Conventions",
                 "## Completion Tracking Table", "## Integration Test Plan"]
required_leaf = ["## Meta", "## Goal", "## Tasks", "## Self-Verification Checklist"]

for f in all_md_files:
    content = open(f).read()
    basename = os.path.basename(f)
    is_orch = basename in ("master.md", "orchestrator.md")
    for section in (required_orch if is_orch else required_leaf):
        if section not in content:
            issues.append(f"MISSING in {basename}: {section}")
    # Line-number corruption check
    if re.findall(r'^\s+\d+\|', content, re.MULTILINE):
        issues.append(f"LINE-NUMBER CORRUPTION in {basename}")
```

This takes <1 second for 30+ files and catches all structural issues
before dispatching implementation agents against the plan.

### 6. File count budget per phase

Observed from AgentAudit (4 phases, 116 files):

| Phase | Branches | Leaves per branch | Total files | Total size |
|-------|----------|-------------------|-------------|------------|
| 1 (MVP) | 4 | 5-8 | 27 | ~500KB |
| 2 (Analysis) | 4 | 4-10 | 27 | ~600KB |
| 3 (Cross-platform) | 5 | 5-6 | 34 | ~700KB |
| 4 (Enterprise) | 4 | 5-6 | 28 | ~600KB |

A phase with 4-5 branches is comfortable for one planning session
(~30 minutes of subagent dispatch + 10 minutes of orchestrator
completion + 5 minutes of structural check).

### 7. Dispatching the missing-file follow-up subagent

When a branch is missing 1-2 files after timeout/rate-limit, dispatch
a focused subagent for JUST those files. Give it:
- The existing orchestrator.md and one complete sibling leaf as pattern reference
- The research doc sections relevant to the missing leaf
- The exact file path and required sections

This is faster than re-dispatching the entire branch. A single-leaf
subagent takes 2-4 minutes vs 8-10 minutes for a full branch.

## What NOT to take from this

- **Don't always limit to 3 subagents.** If the branches are small
  (3-4 files each), 4-5 concurrent is fine. Rate limits correlate with
  total API calls across all subagents, not just the count of dispatches.
- **Don't complete plan docs yourself if the subagent's architecture
  is wrong.** Direct completion is for when 80%+ of files exist and only
  1-2 are missing. If the entire branch structure is wrong, re-dispatch
  with clearer context.
- **Don't skip the structural check.** Even if all subagents reported
  success, run the completeness check. Subagents occasionally produce
  files missing required sections (especially ## Self-Verification Checklist).
