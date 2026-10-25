# Post-Implementation Review and Fix Pattern

After ALL leaves in a plan tree reach COMPLETE and are committed, run a structured review-and-fix cycle. This is a distinct phase from per-leaf review (which happens during execution). The per-leaf review catches implementation-vs-spec gaps; this phase catches integration bugs, cross-branch inconsistencies, and wiring failures that only surface when all branches exist together.

## Phase 1: Parallel Review (N+1 subagents)

Dispatch one review subagent per branch PLUS one cross-cutting review subagent. All run in parallel (up to max_concurrent_children).

### Per-Branch Reviewers

Each reads every file in one branch. Checks:
- Spec compliance: every task from the leaf/orchestrator doc implemented
- Interface contracts: exported types, function signatures, file paths match contracts
- IP/port consistency within the branch
- Missing imports, undefined variables, incorrect function signatures
- YAML/JSON validity
- Correct env var references (compose `${VAR}` → `.env.example`)
- Healthchecks, restart policies, named volumes on all Docker services
- Scripts: `set -euo pipefail`, proper shebangs, error handling

### Cross-Cutting Reviewer

Reads files ACROSS branches. Checks:
- IP/port consistency between branches (config.py defaults vs docker-compose ports vs Caddyfile routes vs provisioning script references)
- Env var completeness: every `${VAR}` in docker-compose.yml appears in `.env.example`
- Contract compliance: SQLite schema matches root contract, NATS subjects match across skills/scripts/config
- Missing wiring: does the control plane actually call the provisioning script? Do skills reference tools that exist?
- Proxmox API token name consistent across infra scripts, Python client, and bash provisioning
- Role/tier names match between Python Literal types, JSON config, and architecture docs

### Typical Issue Yield

From a real 4-branch, 10-leaf project (AI Employee Platform):

| Review Stream | Issues Found | Critical | High | Medium | Low |
|--------------|-------------|----------|------|--------|-----|
| Infrastructure | 26 | 7 | 5 | 7 | 7 |
| Control plane | 25 | 5 | — | 10 | 10 |
| Provisioning | 15 | 7 | — | 8 | — |
| Skills | 15 | 3 | — | 12 | — |
| Cross-cutting | 20 | 6 | 5 | 5 | 4 |
| **Total** | **101** | **28** | **10** | **42** | **21** |

### Most Common Cross-Branch Issues (ranked by frequency)

1. **IP/port mismatches** — config.py has placeholder IPs (10.10.10.50/60/61) that don't match architecture (10.10.10.2). Found in 3+ files.
2. **Undeclared Docker volumes** — service mounts `langfuse_data:/data` but `langfuse_data` is not in top-level `volumes:` block. Compose won't start.
3. **Missing service references** — service environment references `langfuse-clickhouse:8123` but no ClickHouse service is defined.
4. **Broken auth headers in bash** — `PROXMOX_TOKEN` variable defined at top of script but never actually used in the curl Authorization header (placeholder string left in).
5. **Context manager misuse in Python** — `next(get_db())` in scheduler/background tasks. Crashes at runtime but passes all HTTP-handler tests (handlers use `Depends(get_db)` which works differently).
6. **NATS subjects inconsistent** — 3-segment pattern (`client.{slug}.{role}`) in some files, 4-segment (`client.{slug}.{role}.task`) in others.
7. **Skills that are never triggered** — skill subscribes to `client.{slug}.office-manager.task` expecting `type: "new_lead"` messages, but no publisher skill ever sends that message type.
8. **Role/tier name mismatches** — Python `Literal["va", "sales"]` vs JSON `["receptionist", "office-manager"]`. API returns 422 for valid roles.
9. **Port 8000 vs 8001** — Settings class says port 8001, Dockerfile CMD hardcodes `--port 8000`.
10. **Horus/project name remnants** — template files reference old project names ("Horus") instead of current name.

## Phase 1.5: The Self-Review Checklist (single-session trees, 2026-08-16)

When the orchestrator implemented the leaves DIRECTLY (no subagents to
review), the post-implementation review is a SELF-review — and the
orchestrator's blind spots are systematic, not random. Four defects found
in one adversarial self-review of rebellion tree 24 (6 leaves), every one
invisible to 1167 green headless tests:

1. **Shader-rename fallout** — a GLSL variable rename that missed one
   later line. Headless suites never compile GLSL; the effect silently
   dies at runtime. After any .glsl edit: `grep -n <old_identifier>` on
   the shader must return ZERO hits.
2. **Child-name lookups vs multi-child nodes** — activation code written
   for a single-child node ("Particles") silently no-ops when a refactor
   introduced N children. Grep for name-based child lookups touching any
   node whose children you added.
3. **Orphan public APIs** — a `set_x()` with zero production callers is a
   stub even if tests exercise it. For every new public method: grep
   callers OUTSIDE tests. If none, either wire it through the owning
   system's single writer or mark it debug-only in its docstring.
4. **Wire-contract documentation** — a new IPC field that crossed the
   engine↔sidecar boundary but was never added to the shared wire-table
   doc (SHARED-CONVENTIONS §4). The code worked; the contract of record
   lied.

Run this checklist as a distinct pass AFTER the full suites go green —
these are wiring/compile classes that green tests actively mask. Also
expect the review to surface the one thing headless CI cannot: schedule
the user's visual smoke run as an explicit gate, and say so in the
completion record ("pending user gates: visual X, perf Y").

## Phase 2: Parallel Fix (N subagents)

Group issues by file/area. Dispatch one fix subagent per group. Rules:
- TARGETED edits only — no full file rewrites
- Each fix subagent gets the exact list of issues with file paths and line numbers
- Verify with tests (`pytest`, `docker compose config`, `bash -n`, `yaml.safe_load`) after each group returns
- Commit each fix group separately with descriptive messages

### Rate Limit Handling (HTTP 429)

When dispatching 5-6 parallel fix subagents, some will hit API rate limits. Two responses:

1. **Re-dispatch** after a brief delay — works if transient
2. **Fix in-session** — orchestrator applies fixes directly using `execute_code` (Python string replace) and `patch` tool

In-session fix approach:
```python
# Use execute_code for bulk find-replace across multiple files
with open(path) as f:
    content = f.read()
content = content.replace("wrong_value", "correct_value")
with open(path, "w") as f:
    f.write(content)
```

For surgical single-file edits, use the `patch` tool with exact old/new strings.

Always validate after in-session fixes: run `pytest`, `bash -n` on scripts, `yaml.safe_load` on YAML files.
