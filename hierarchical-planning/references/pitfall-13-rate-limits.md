# Pitfall 13 - Provider Rate Limits on Concurrent Dispatch

When to use: dispatching 3+ leaf agents simultaneously, or a dispatch/subagent hits HTTP 429.
Lesson: rate limits have a dispatch phase (parent side) and an execution phase (subagent side); each has its own recovery ladder.

Dispatching 3 leaf agents simultaneously can trigger HTTP 429 rate limits on cloud providers. This is the single biggest risk with parallel leaf execution. Two distinct failure phases:

## Dispatch-phase rate limits (the parent's side)

If `delegate_task` itself returns a 429, retry only the failed leaves individually (not as a batch) - a single agent running alone rarely hits limits. Plan for 2-3 retry rounds on large trees.

## Subagent execution-phase rate limits (the subagent's side)

Even with serial dispatch, a subagent that makes many tool calls (reading files, terminal, search) can hit 429 during its own execution. Most common on aggressive providers. Three recovery strategies, try in order:

**(a) Rich-context retry.** On re-dispatch, pack as much pre-digested content into the `context` parameter as possible - spec snippets, cross-reference findings, changelog rows, known results of prior inspections. Every `terminal cat` or `search_files` the subagent avoids is one less API call that can hit a rate limit. Provide full quotes of source text, not file paths to read.

**(b) Narrow scope.** If the initial scope was broad (e.g. "audit all 12 trees"), split the retry into 2-3 narrower slices that each touch fewer files. A subagent that only needs to verify 3 trees makes ~50% fewer tool calls than one checking all 12.

**(c) Fall back to direct work.** When ALL parallel subagents fail with 429 and serial retries also struggle, the parent agent should write the deliverable directly from its own accumulated context (files read, changelog parsed, findings seen). Signs to switch: (i) subagent consistently fails before producing output, (ii) you already read enough files yourself to write a defensible deliverable, (iii) the work is read-only (audit, review, analysis) where you do not need fresh tool output. Do NOT keep dispatching the same subagent - each retry burns API calls on re-reading context rather than producing output.

Strategy (c) at batch scale (40%+ of a 10+ batch failed) is Pitfall 4's rate-limit exception. Worked examples: `references/gdscript-bulk-dispatch.md`, `references/plan-tree-dispatch-scaling.md`.
