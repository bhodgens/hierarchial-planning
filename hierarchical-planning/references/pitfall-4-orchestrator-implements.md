# Pitfall 4 - Orchestrator Implementing Child Work (Exceptions)

When to use: deciding whether the orchestrator may implement a leaf directly instead of dispatching.
Lesson: always dispatch first; direct implementation is a recovery path for batch rate-limit failures and single-leaf timeouts only.

The orchestrator dispatches, reviews, and tracks - it does not implement. If you are writing code in the orchestrator session, stop and re-dispatch to a leaf agent. Two exceptions exist; both require the signs below to hold.

## Exception - Rate-limit batch failure

When a batch of 10+ subagents is dispatched and 40%+ hit HTTP 429 rate limits (Pitfall 13c), the orchestrator MAY write the missing files directly from accumulated session context rather than re-dispatching. Signs to switch:

1. 4+ subagents in the same batch returned 429 with no output.
2. The orchestrator already read the GDD specs and wrote the dispatch contexts (so it has the content).
3. The missing files are well-bounded (one file per leaf, no cross-leaf dependencies).
4. Re-dispatching will likely hit the same rate limits.

Write files using `write_file` (NOT `execute_code` f-string concatenation - see Pitfall 29 variant), verify with grep, commit as a separate wave. This is NOT a shortcut to skip dispatching - always dispatch first; only implement directly as a batch-failure recovery path. Worked example: 14-leaf GDScript bulk dispatch, `references/gdscript-bulk-dispatch.md`.

## Exception - Single-leaf timeout

When a single leaf subagent fails completely (429 or timeout with no usable output - Pitfall 25 variant), the orchestrator MAY implement the work directly provided it already has sufficient context from prior exploration. Signs to switch: the subagent consistently fails before producing output, you already read enough files to write correct code, and the work is well-bounded.

Related: `references/subagent-failure-salvage.md` (salvage decision tree when a leaf reports failed/timeout/no summary).
