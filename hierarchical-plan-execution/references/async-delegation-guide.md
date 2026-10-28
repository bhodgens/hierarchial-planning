# Aasync delegation guide
When to use: dispatching subagents for parallel leaves.
Lesson: delegate_task patterns: batch shape, continuation triggers, failure handling.

# Async Delegation: Working with Subagents

## Overview

Use `delegate_task` to spawn subagents for parallel leaf implementation in plan trees. This skill covers the patterns, pitfalls, and verification workflows.

## When to Delegate

- Multiple independent leaves in a plan tree (3+ concurrent)
- Each leaf has a self-contained spec with test commands
- Leaves don't share files (or use isolation strategy from Pitfall 38)

## Dispatch Pattern

```go
delegate_task(
    tasks: [{
        goal: "Implement leaf 03: Resolver quota blocking",
        context: `Read docs/plans/quota-reset-resilience/03-resolver-quota-blocks.md
KEY CONTRACTS:
1. Add entryBlocks map[string]time.Time to AliasHealth
2. Add QuotaBlockedUntil, ActiveQuotaBlocks methods
...`,
        role: "leaf"
    }, ...]
)
```

**Critical:** Include the leaf doc path, interface contracts, test commands, and verification steps in context. The brief IS the recovery contract.

## Verifying Subagent Results

Subagents run in isolated contexts — their results must be verified on disk:

```bash
# Check files landed
find . -name "*quota*" -type f | grep -v '.git\|scratch'

# Run targeted tests
go test ./internal/llm/ -run 'TestQuota' -count=1 -timeout 30s

# Verify build
go build ./...
```

## Pitfalls

### Pitfall 54: Late-429
Subagent writes all files, runs green tests, then dies on final API call with 429. Result returns "completed" with NO summary.

**Response:** Check disk + /tmp logs before re-doing. Brief is recovery contract.

### Pitfall 55: Stale Async Delegation Reports
Subagents dispatched at session start may return hours later with "completed" status after in-session work is already done.

**Response:** Don't trust the summary. Check working tree + run tests. Skip if verified.

### Pitfall 56: Sibling Orchestrators Execute Your Plan First (meept, 2026-09-02)
On a multi-session repo, sibling Hermes sessions can execute MOST of your plan forest before you dispatch: of 5 trees, 3 were fully committed, a 4th had 2/3 leaves landed, and the 5th was mid-leaf when this session checked git. Three of four dispatched "implementation" subagents correctly returned "already implemented — verified, zero changes."

**Response:** Before dispatching ANY leaf, run the pre-dispatch check per leaf (Step 1.5) AND check `git log --since` for sibling commits touching the leaf's target files. Reframe dispatch contexts as "verify the landed implementation against the spec; fix real gaps only; report zero-change if compliant" instead of "implement." Never re-implement committed work.

### Pitfall 57: Wire-Through Claims Need Construction-Site Greps (leaf 04 gap)
A committed leaf shipped TUI/GUI surfaces + docs claiming park-event bus wiring existed — but `SetParkEventBus` was never called in components.go, so park/resume/give-up events never reached the bus in production. Tests passed because they tested the pieces, not the wiring.

**Response:** For every "wire X into Y" contract, review = grep the construction site (components.go or equivalent) for the actual call, not just the presence of the setter/API. Add a scoped test that asserts the production wiring path.

### Pitfall 58: Real-Sleep Backoff Makes Suite Timeouts New Failures
Land D8-style long backoff (30s throttle base) and every pre-existing test exercising retry paths with REAL sleeps inflates the suite past its old timeout (meept internal/llm: 300s cap → 308s runtime). Symptoms: rotating "hung" tests, each passing in isolation.

**Response:** Ship the policy with a test-mode schedule override (tiny base) OR batch-fix the real-sleep tests in the same tree. When inheriting such a suite, run with an adequate timeout first and treat timeout-failures as slow-tests, not regressions — then file the real-sleep cleanup as follow-up.

### Pitfall 59: Full-Parallel Runs Exhaust Ephemeral Ports
`go test ./internal/...` on 80+ packages with thousands of httptest servers exhausts macOS ephemeral ports (49152-65535): failures read `dial tcp 127.0.0.1:NNNNN: connect: can't assign requested address`, different tests each run, all pass serially.

**Response:** Re-run failed packages serially before diagnosing code. If recurring, reduce `go test -p` parallelism or widen the port range; treat as environment, not regression.

### Pitfall 60: Uncommitted-Sibling Files Block Your Commit
A sibling session's leaf was uncommitted in the shared working tree. Reviewing it exposed a REAL pre-existing infinite-spin bug (rate-limit rotation with no budget bound) whose new control test hung the suite — but committing the leaf as-is would land the bug, and "fix the test to match the bug" was wrong.

**Response:** When a working-tree blocker involves another session's WIP: verify the bug in isolation first (repro counts, not vibes), present evidence + proposed minimal fix, and wait for the user's pick (fix+commit vs commit-with-known-issue). Committing a sibling's WIP without that gate risks shipping their bug under your name; user chose fix-first (bounded rotation retries), which the hook-driven cleanups then accompanied.

### Pitfall: Parallel Leaves Mid-Session
Sibling leaves land while you work. A dependency can appear between your grep and write.

**Response:** Re-search before finalizing. Use RECONCILE blocks for shims.

## Best Practices

1. **Write briefs YOU could execute** — include interfaces, line numbers, test commands
2. **Scope tests to your package** — sibling runs may contend
3. **Verify before trusting** — disk + tests > subagent summary
4. **Use targeted filters** — `go test ./pkg/ -run 'TestSpecific*'` not full suite
5. **Never re-dispatch into exhausted provider** — implement directly from brief
6. **Run -run filters with generous -timeout** — long-leaf packages can carry 90s single tests; a 120s window can false-fail a passing suite
7. **Multi-session repos: pre-dispatch check is per-leaf, not per-tree** — siblings land commits between your recon and your dispatch; reframe briefs as verify-and-gap-fill when the leaf may already exist
8. **Review wire-throughs by grepping the construction site** — setter/API presence ≠ daemon wiring; assert the production call path in a scoped test
9. **Budget for real-sleep backoff in suite timeouts** — landing long-horizon policies (D8-style) inflates old retry-path tests; adequate timeout first, real-sleep cleanup as tracked follow-up
10. **Full-forest parallel test runs exhaust ephemeral ports** — serial re-run of failed packages before diagnosing code
