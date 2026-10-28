# Rrate limit recovery and review fix pattern
When to use: many parallel subagents get throttled.
Lesson: 429 recovery and the parallel review-fix pattern.

# Rate Limit Recovery and Parallel Review-Fix Pattern

Two operational patterns learned from sessions that dispatch many parallel subagents.

## Rate-Limited Subagent Recovery (429)

When dispatching many parallel subagents, some may return with HTTP 429 rate limit errors instead of completed work. Detect this by:

1. The subagent summary contains "Rate limit reached" or "API call failed after 3 retries: HTTP 429"
2. The subagent reports zero files created / zero tool calls made
3. The return is suspiciously fast (under 30s for a task estimated at 60K+ context)

### Recovery Options (in priority order)

1. **Re-dispatch with a delay** — wait 30-60 seconds, then re-dispatch the same leaf. Rate limits are often transient.
2. **Handle in-session** — if the task is well-defined (targeted edits, not greenfield creation), the orchestrator can make the changes directly using patch/execute_code tools. This is faster than waiting for another subagent and avoids the rate limit window entirely.
3. **Reduce parallelism** — if multiple subagents are hitting 429, lower the batch size for subsequent waves. Dispatch 2 at a time instead of 5.

### Key Insights

- Rate limits are more likely when dispatching 5+ subagents simultaneously, especially during the review phase (which generates heavy API traffic from reading many files).
- Consider dispatching review subagents in smaller batches (3 at a time) even if the delegation concurrency limit allows more.
- In-session fixes are appropriate for: targeted edits with clear specs (fix this line, add this env var, replace this string).
- Re-dispatch is appropriate for: greenfield file creation, complex multi-file logic, tasks requiring exploration of existing code.

## Parallel Review → Batch Fix Pattern

For large multi-branch projects (4+ branches, 10+ leaves), after all leaves are implemented, run a structured review-and-fix cycle.

### Phase 1: Parallel Review (5-6 subagents, one per concern)

- One review subagent per branch (infrastructure, control-plane, provisioning, skills)
- One cross-cutting review subagent (IP/port consistency, env var completeness, contract compliance, missing wiring)
- Each reports ALL issues found with exact file paths and line numbers
- Do NOT have review subagents fix issues — separation of concerns

### Phase 2: Compile and Deduplicate

- Collect all issue lists from review subagents
- Deduplicate cross-cutting issues (same problem found by multiple reviewers)
- Group by fix category (Docker compose, Python code, shell scripts, skills, OpenTofu)

### Phase 3: Parallel Fix (5-6 subagents, one per fix category)

- Each fix subagent gets a specific list of issues to address in specific files
- Fix subagents make targeted edits only — no full rewrites
- Give each fix subagent the EXACT file paths, line numbers, and replacement values
- Include "Do NOT commit" and "Make targeted fixes only" in dispatch context

### Phase 4: Orchestrator Review and Commit

- Review each fix subagent's changes in-session
- Run tests (pytest, bash -n, docker compose config, JSON validation)
- Commit each fix batch separately with descriptive messages
- For fix subagents that hit 429 rate limits: handle in-session using patch tool

### Why This Works

Review subagents catch more issues when they focus on one branch (deeper file reading). Fix subagents are more reliable when they get a precise list of changes rather than discovering issues themselves. The separation prevents the "fix one thing, break another" pattern.

### Common Issue Categories Found in Reviews

From a 10-leaf, 4-branch AI Employee Platform project (81 files):

1. **Docker compose:** undeclared volumes, missing services referenced by env vars, hardcoded passwords instead of ${VAR}, wrong proxy targets in Caddyfile
2. **Python:** wrong default IPs in config, wrong port numbers, context manager misuse (next(get_db()) instead of with get_db() as db), role Literal values not matching contract
3. **Shell scripts:** broken auth headers (variable defined but never used in curl), wrong IPs, missing env vars in generated .env files, typo'd package names (pyautomi→pyautogui)
4. **OpenTofu:** security group referenced but never created as a resource, variables declared but never used, ZFS mountpoint paths inconsistent between shell script and TF
5. **Skills (SKILL.md):** NATS subjects with inconsistent segment counts, skills that are never triggered (no publisher sends to their subject), value-ledger hooks not called by any skill
6. **Cross-cutting:** IP/port mismatches between branches, NATS subject patterns that differ between Python code and bash scripts, control plane not calling the provisioning script
