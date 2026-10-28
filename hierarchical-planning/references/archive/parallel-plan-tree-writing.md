# Parallel Plan-Tree Writing — Dispatching Subagents to Write Plan Documents


When to use: dispatching subagents that write plan documents (not code).
Lesson: cap at 4-5 concurrent plan-writing subagents; per-branch dispatch pattern.
> Session: 2026-08-04, AgentAudit project.
> Task: write 4 complete phase plan trees (109 files total) using parallel
> delegate_task subagents that WRITE markdown plan documents, not code.
> This is distinct from wave-execution-patterns.md (which covers
> IMPLEMENTATION subagents that write Go/Swift/TSX code from plans).

---

## When This Pattern Applies

You need to produce a large plan tree (multiple branches, many leaves)
and the main model's context is filling up. Instead of writing each
branch sequentially, dispatch one subagent per branch to write its
orchestrator + all leaf documents.

Used in this session:
- Phase 1: 4 branches × 5-7 leaves each = 27 files (4 subagents)
- Phase 2: 4 branches × 4-9 leaves each = 27 files (4 subagents)
- Phase 3: 5 branches × 6 leaves each = 31 files (5 subagents)
- Phase 4: 4 branches × 5-6 leaves each = 24 files (4 subagents)
- Total: 109 files across 17 subagent dispatches over 4 batches

## Dispatch Pattern

### Per-branch dispatch

Each subagent gets:
1. The master.md path (to read interface contracts)
2. The research doc paths (for domain context)
3. The template paths (leaf-template.md, master-template.md)
4. The EXACT list of files to create with paths
5. What each leaf must cover (specific content requirements)

```python
delegate_task(
    goal="Write the complete plan tree for [branch name]",
    context="Read /path/to/master.md for contracts. "
            "Read /path/to/research.md for domain context. "
            "Templates at /path/to/templates/",
    # ... see actual dispatch calls from session
)
```

### Batch sizing

- Phase 1-2: 4 subagents per batch — no rate limit issues
- Phase 3-4: 9 subagents in one batch — 3 hit HTTP 429 rate limits

**Lesson: cap at 4-5 concurrent plan-writing subagents.** Rate limits
activate around 6+ concurrent subagents making 10+ API calls each. With
4-5, all complete successfully. With 9, 30-40% fail on rate limits.

## Failure Modes and Recovery

### 1. Rate Limit (HTTP 429) — subagent writes 0 files

**Symptom:** subagent returns with `status=completed` but summary says
"API call failed after 3 retries: HTTP 429". No files on disk.

**Recovery:**
```python
# Check what was actually written
search_files(pattern="*.md", target="files", path="<branch_dir>")
# If 0 files: re-dispatch the branch
# If partial: check which specific files are missing, write them directly
# or re-dispatch with narrowed scope (only missing files)
```

**Prevention:** Don't dispatch more than 5 branches at once. If you
need 9 branches, split into two waves of 4-5 with a gap between.

### 2. Timeout (600s) — subagent wrote all files but didn't return summary

**Symptom:** `status=timeout` after 600s with 20+ API calls. But when
you check disk, all expected files are present and well-formed.

**Recovery:** Check disk. If all files exist with correct size (>10KB
each, has required sections), the branch is COMPLETE. The timeout only
affected the summary return, not the file writing.

```python
# Verify completeness
for f in expected_files:
    size = os.path.getsize(f"{branch_dir}/{f}")
    has_meta = "## Meta" in open(f"{branch_dir}/{f}").read()
    # If both check out, branch is done despite timeout
```

This happened with:
- Phase 2 skill-synthesis (10 files, timed out on summary, all files present)
- Phase 3 central-server (6 files, timed out on summary, all files present)

### 3. Partial write — subagent wrote some files then died

**Symptom:** Branch directory has 3-5 of 6 expected files.

**Recovery:** Write the missing files directly as the orchestrator
(main model). You have the master.md contracts and the research docs
in context already. Writing one leaf document takes ~2 minutes
directly vs. 5+ minutes to re-dispatch a subagent.

This happened with:
- Phase 2 skill-synthesis leaf 09 (orchestrator wrote it directly)
- Phase 1 swift-agent leaves 05-06 (dispatched follow-up subagent)

### 4. All files present but orchestrator missing

Sometimes the subagent writes all leaves but not the orchestrator.
Check for orchestrator.md specifically and write it directly if missing.

## Structural Completeness Check

After all branches return (or are recovered), run a batch validation:

```python
import os, re

required_orch_sections = [
    "## Dispatch Protocol", "## Interface Contracts",
    "## Review Checklist", "## Coding Conventions",
    "## Completion Tracking Table", "## Integration Test Plan",
]
required_leaf_sections = [
    "## Meta", "## Goal", "## Tasks", "## Self-Verification Checklist",
]

for f in all_plan_files:
    content = open(f).read()
    is_orch = os.path.basename(f) in ("master.md", "orchestrator.md")
    sections = required_orch_sections if is_orch else required_leaf_sections
    for s in sections:
        if s not in content:
            issues.append(f"{f}: MISSING {s}")
    # Check for line-number corruption
    if re.findall(r'^\s+\d+\|', content, re.MULTILINE):
        issues.append(f"{f}: line-number corruption")
```

## Timing Benchmarks

| Batch | Branches | Files/branch | Subagents | Rate-limit failures | Timeouts | Direct completions |
|-------|----------|-------------|-----------|--------------------|----------|--------------------|
| Phase 1 | 4 | 5-8 | 4 | 0 | 1 (swift, recovered) | 2 leaves |
| Phase 2 | 4 | 4-10 | 4 | 0 | 1 (synthesis, recovered) | 1 leaf |
| Phase 3+4 | 9 | 5-6 | 9 | 3 (re-dispatched) | 1 (central-server, recovered) | 0 |
| **Total** | **17** | **avg 6** | **17 dispatches + 2 re-dispatches** | **3** | **3** | **3 leaves** |

## Key Differences from Implementation Subagent Dispatch

| Aspect | Plan-Tree Writing | Code Implementation |
|--------|-------------------|---------------------|
| Output | Markdown documents | Go/Swift/TSX source files |
| Context needed | Master.md contracts + research docs + templates | Leaf document + contracts + existing code |
| Rate limit risk | HIGH (many web_search/read_file calls per branch) | LOW (mostly write_file calls) |
| Timeout recovery | Check disk, files usually present | Check disk, may need tests/entry-points/gofmt |
| Verification | Structural section check + grep corruption | go build + go test + gofmt |
| Re-dispatch scope | Only empty/partial branches | N/A (implementation rarely re-dispatched) |
