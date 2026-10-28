# Ppitfall 55 stale delegation
When to use: stale async delegation reports.
Lesson: hours-late completed returns after in-session completion.

# Pitfall 55: stale async delegation reports after in-session completion

Subagents dispatched at session start may return hours later with "completed"
status (often via API 429), but the parent session has already implemented the
same work directly. Do NOT trust the subagent's summary as ground truth.

## Pattern observed (2026-08-30, meept quota-reset-resilience)

Multiple delegation batches returned "completed" after 15–22 minutes:
- deleg_eb5996ef, deleg_4cfc58cd: reported success, no files on disk
- deleg_923f3356: claimed `quota_deferral_test.go` written — file absent
  (subagent ran in isolated sandbox, did not land in working tree)
- deleg_82a7a58a (leaf 10 docs), deleg_ead8a407 (leaf 04): same pattern

All returned with API 429 errors on final call — work was done by parent.

## Protocol on any late async delegation return

1. Check working tree immediately:
   ```bash
   find . -name "*<leaf-key>*" -type f | grep -v '.git\|scratch'
   git status --short | grep <pkg>
   ```
2. Run targeted tests (scope to your package only):
   ```bash
   go test ./internal/llm/ -run 'TestQuota' -count=1 -timeout 30s
   ```
3. Decision tree:
   - Files exist + tests pass → skip subagent report, move on
   - Files missing or tests fail → implement from dispatch brief directly
4. Never re-dispatch into an exhausted provider before rate limit reset

## Key insight

The dispatch brief IS the recovery contract. If orchestrator already
implemented from it, subagent output is noise. If not, brief contains all
info needed to complete — no waiting required.

## Related

- Pitfall 54 (late-429): subagent writes files then dies before reporting
- Pitfall parallel-leaves-mid-session: sibling leaves land while you work
