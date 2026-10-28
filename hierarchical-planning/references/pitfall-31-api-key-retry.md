# Pitfall 31 - Subagent API-Key Failures: Retry with Explicit Model

When to use: a dispatched subagent fails with HTTP 401 "Invalid API-key".
Lesson: re-dispatch immediately with an explicit model parameter or let Hermes auto-retry; for critical exploration, dispatch 2-3 in parallel so at least one succeeds.

HTTP 401 "Invalid API-key" errors occur intermittently on dispatch (seen in 2 of 3 subagents during one port session). Root cause: default model selection sometimes routes to providers requiring different auth.

## Pattern

(a) If a subagent fails with 401, immediately re-dispatch with an explicit model parameter or let Hermes auto-retry.
(b) Do NOT assume the task failed - the subagent may succeed on retry.
(c) For critical exploration tasks, dispatch 2-3 subagents in parallel so at least one succeeds.
(d) Do not proceed with incomplete data: the pattern is dispatch - if 401, re-dispatch - digest successful results.

Distinct from Pitfall 13 (429 rate limits): a 401 is an auth/routing failure, not a volume failure, and usually clears on a plain re-dispatch.
