# Pparallel review fix pipeline
When to use: review to fix pipeline.
Lesson: parallel review with fix dispatches.

# Parallel Review → Fix Pipeline (humanplusone session, 2026-08-04)

## Pattern

After implementing a full project via hierarchical plan execution, run a parallel review → fix cycle to catch integration bugs that leaf-level reviews miss.

## Review Phase

1. Dispatch 5 parallel review subagents, one per branch + one cross-cutting:
   - Branch 1 reviewer (infrastructure)
   - Branch 2 reviewer (control plane)
   - Branch 3 reviewer (provisioning)
   - Branch 4 reviewer (skills/business logic)
   - Cross-cutting reviewer (IP/port consistency, env var completeness, contract compliance, missing wiring)

2. Each reviewer gets: the files to review, the contract/spec to check against, and "report ALL issues, do NOT fix."

3. Collect results — expect 50-80 issues for a 10-leaf project across 4 branches. Common categories:
   - IP/port mismatches (different defaults in different files)
   - Missing env vars (.env.example incomplete vs code references)
   - Broken auth headers (placeholder never replaced with variable)
   - Wrong service references (nonexistent systemd units, missing Docker services)
   - NATS subject pattern violations (3-segment vs 4-segment)
   - License over-flagging (internal use vs hosting-for-customers)
   - Cross-branch contract drift (role names, IP formulas, field names)

## Fix Phase

1. Compile all issues into fix batches by file ownership (no two subagents edit the same file):
   - Batch 1: Docker compose + config files
   - Batch 2: OpenTofu declarations
   - Batch 3: Provisioning scripts + template files
   - Batch 4: Agent skills
   - Batch 5: Control plane Python code
   - Batch 6: Documentation (README, .env files)

2. Dispatch one fix subagent per batch, each with the specific issues and exact fixes needed.

3. Rate-limit fallback: if a fix subagent hits 429, the orchestrator does the fix in-session via `execute_code` (Python read → string replace → write). This handled 19 provisioning fixes and 10 Docker compose fixes in under 10 seconds when subagents were rate-limited.

4. After each fix batch returns:
   - Run tests (pytest, bash -n, json.load validation)
   - Commit with descriptive message listing the fixes applied

## What Worked Well

- Cross-cutting reviewer caught the most critical issues (wrong IPs in config defaults, port mismatches, broken auth)
- Branch reviewers caught implementation bugs (missing services, typos, wrong env vars)
- In-session execute_code fixes were faster than re-dispatching rate-limited subagents
- Committing per fix-batch gave clean git history with clear correction messages

## What to Improve

- The control plane review subagent hit rate limits and had to be re-dispatched. Consider staggering review dispatches by 10-15 seconds if rate limits are known.
- Some issues were reported by multiple reviewers (duplication). Deduplicate before dispatching fixes to avoid conflicting edits.
