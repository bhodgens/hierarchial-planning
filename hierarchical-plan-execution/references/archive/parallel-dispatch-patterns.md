# Pparallel dispatch patterns
When to use: parallel leaf dispatch.
Lesson: patterns proven in AgentAudit implementation.

# Parallel Dispatch Patterns — Lessons from AgentAudit Implementation

## Contract Conflict from Parallel Subagents Modifying Shared Interfaces

When multiple parallel implementation subagents each need to extend a shared Go interface (e.g., `Store`), they independently change its definition. Result: "X redeclared in this block" or "wrong type for method Y" build errors.

**Prevention:** Partition subagents so shared interface files (store.go, types.go, router.go) are owned by exactly ONE subagent. Others define narrow local interfaces (`type Storer interface { StreamEvents(...) }`) that the full Store satisfies as a superset.

**Tell each subagent:** "Do NOT modify internal/store/store.go or internal/types/types.go. Define a local interface in your package."

**Recovery:** Build, find conflicts, choose the superset signature, reconcile all implementations + mocks, update master.md Contract to match.

## Wave-Based Dispatch for 8+ Leaf Branches

A branch with 8+ leaf files will time out at 600s if dispatched as one subagent. Tested twice, timed out twice.

**Pattern:** Split into Wave 1 (types + schema + deterministic logic, 3-5 files) and Wave 2 (LLM clients + API + pipeline, 3-5 files). Verify Wave 1 builds green before dispatching Wave 2.

**Sizing:**
- 4-6 new .go files: reliable (~5 min)
- 7-10 files: high timeout risk, split into 2 waves
- 10+ files: will time out, always split

## Structural Completeness Check Script

After subagents write plan trees, verify via execute_code:

```python
from hermes_tools import search_files
import os, re

required_orch = ["## Dispatch Protocol", "## Interface Contracts", "## Review Checklist",
                 "## Coding Conventions", "## Completion Tracking Table", "## Integration Test Plan"]
required_leaf = ["## Meta", "## Goal", "## Tasks", "## Self-Verification Checklist"]

for phase in ["phase1-mvp", "phase2", "phase3", "phase4"]:
    result = search_files(pattern="*.md", target="files", path=f"docs/plans/{phase}")
    files = sorted(result.get("matches", result.get("files", [])))
    for f in files:
        basename = os.path.basename(f)
        is_orch = basename in ("master.md", "orchestrator.md")
        with open(f) as fh:
            content = fh.read()
        sections = required_orch if is_orch else required_leaf
        for s in sections:
            if s not in content:
                print(f"MISSING in {basename}: {s}")
        corruption = re.findall(r'^\s+\d+\|', content, re.MULTILINE)
        if corruption:
            print(f"CORRUPTION in {basename}: {len(corruption)} matches")
```

## Rate-Limit (429) Recovery During Plan Tree Writing

9 simultaneous subagents writing plan documents triggered 429 on 3 of them. Recovery: serial re-dispatch of failed branches (not parallel), with richer context embedded to reduce internal tool calls.

## Post-Commit Batch Capture (Unintended Files in Commit)

When committing one subagent's output while other subagents are still running, untracked files from the running subagents get swept into the commit via `git add -A`. 

**Real instance:** Committing central server (branch 11) with `git add -A` also committed 30+ files from Windows agent (branch 09) and Linux agent (branch 10) that were written by concurrent subagents but not yet reviewed.

**Prevention:** Use explicit file paths instead of `git add -A` when other subagents are running:
```bash
git add internal/store/pgstore.go internal/auth/agent.go internal/team/users.go ...
# NOT git add -A
```

**Detection:** After commit, check `git show --stat HEAD` for unexpected files. If found, the commit is usually harmless (the files would be committed eventually anyway), but it muddies the commit message accuracy.

**Acceptable when:** The concurrent files compile and pass tests (they were written by a subagent following the same plan). Just note in the commit body that it includes files from concurrent branches.

## Dependency-Graph-Aware Wave Dispatch (Cross-Leaf Chaining)

The wave patterns above split ONE large branch into sequential sub-waves. A
different pattern arises when executing an entire plan tree whose leaves have a
dependency DAG declared via "Concurrency Groups" (A, B, C...) in the master.md.

**The pattern:** dispatch independent leaves (Group A) as parallel subagents, then
chain dependent leaves as their SPECIFIC dependency completes — do NOT wait for
all of Group A to finish before starting Group B/C leaves whose dependency is done.

**Concrete example (tree 18, 9 leaves, 4 concurrency groups):**
```
Wave 1 (parallel, Group A + A2 — 4 leaves):
  01-body-source, 01-garment-mesh, 01-creature-gen-gait, 02-prop-gen-placement

When 01-garment-mesh returns (before other Wave 1 leaves):
  → immediately dispatch 02-fabric-texture (depends only on garment-mesh)

When 01-body-source returns:
  → immediately dispatch 02-rigify-integration (Wave 2)

When 02-rigify-integration returns:
  → dispatch 01-bonemap-retarget + 02-rescale-gate in parallel (Wave 3)

When both return:
  → dispatch 03-foot-grounding-rewire (Wave 4, final)
```

This maximizes parallelism: fabric-texture (Group C) runs concurrently with
rigify-integration (Group B) because their dependencies are different Wave 1
leaves. Waiting for "all of Wave 1" before starting any Wave 2+ work would
serialize unnecessarily.

**Key techniques:**
1. Read ALL leaves upfront (batch read via execute_code loop) to extract the
   dependency graph before dispatching anything.
2. Track state with a todo list showing which waves are in-flight vs pending.
3. When a subagent returns, check which downstream leaves it unblocks and
   dispatch them immediately.
4. Package downstream context: embed completed leaf file paths + "follow the
   same pattern as X" instructions so the dependent leaf doesn't re-discover
   conventions.

**Context packaging for downstream leaves:** Each delegation should inline:
- The full leaf task document (don't make the subagent read_file it — you already
  have it in context)
- File paths from completed dependency leaves (e.g., "rebellion-godot/scripts/tools/trellis_garment.py — follow the same pattern")
- GDD spec references
- Existing file exploration instructions ("use search_files or terminal cat, NOT read_file")
- Test framework commands (pytest / GUT headless)
- "Do NOT commit. Do NOT run git add." guardrails

## InsertScreenshot Contract Deviation

The plan spec said `InsertScreenshot(ctx, Screenshot) error`. The implementation subagent changed it to `(int64, error)` to return the inserted row ID for the 201 Created response. This was the better design — the fix was updating the spec contract to match, not degrading the code.

**Lesson:** When a subagent improves a contract signature during implementation, evaluate whether the improvement is correct. If so, update the spec rather than reverting the code.
