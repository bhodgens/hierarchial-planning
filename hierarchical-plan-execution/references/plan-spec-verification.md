# Pplan spec verification
When to use: leaf documents contain wrong assumptions.
Lesson: verify spec claims against the codebase before implementing (Pitfall 27 worked example).

# Plan Spec Verification — When Leaf Documents Get Signatures Wrong

> Worked example for Pitfall 27 in hierarchical-plan-execution. A plan tree's
> leaf documents contained factually wrong assumptions about existing function
> signatures across all 5 leaves. The orchestrator caught every one by
> pre-reading source before dispatch, resulting in zero fix cycles.

## Session

- **Date:** 2026-07-23
- **Project:** meept Go daemon
- **Plan tree:** `docs/plans/20260723-panic-replacement/`
- **Leaves:** 5 independent panic-replacement tasks

## The Five Wrong Assumptions

| Leaf | Plan claimed | Actual | Caller count | Corrected dispatch approach |
|------|-------------|--------|--------------|---------------------------|
| 01-bus | `Publish()` returns `(int, error)`, add `ErrNoSubscribers` sentinel | Returns just `int` | 20+ | Replace panic with `logger.Error` + return 0, no signature change |
| 02-agent | `NewAgentLoop()` can return `(*AgentLoop, error)` | Returns `*AgentLoop` | 25+ | Replace panic with `slog.Error` + return nil |
| 03-mcp | `mustMarshal()` needs error return path | Returns `json.RawMessage`, 2 callers (both inline `map[string]any` literals that can't fail) | 2 | Replace panic with `slog.Error` + return nil |
| 04-hashline | `om()` should return `(nil, ErrOddArgCount)` | Returns `*orderedMap` (single return value, not a tuple) | 11 (same file) | Replace panic with `slog.Error` + return `newOrderedMap()` |
| 05-session | `jsonMustMarshal()` is an "unconditional panic" needing investigation | Returns `[]byte`, single caller, simple `map[string]any` payload | 1 | Replace panic with `slog.Error` + return nil |

## How the Gaps Were Caught

Step 3a of the skill says "pre-read any existing source files." This session
went further: after reading each leaf, the orchestrator explicitly searched for
the actual function signatures and counted callers before writing dispatch
instructions.

**Batched verification calls (all in one turn):**

```
# Verify Publish signature
search_files pattern="func.*Publish" path="internal/bus/"

# Count Publish callers across the codebase
search_files pattern="\.Publish\(" file_glob="*.go"

# Verify NewAgentLoop callers
search_files pattern="NewAgentLoop\(" file_glob="*.go"

# Count mustMarshal call sites
search_files pattern="mustMarshal" path="internal/mcp/"

# Count om() call sites
search_files pattern="\bom\(" path="internal/tools/builtin/"

# Count jsonMustMarshal call sites
search_files pattern="jsonMustMarshal" path="internal/session/"
```

These 6 searches (batched in one turn) revealed that every single leaf had a
wrong assumption. The orchestrator corrected each dispatch context before any
subagent ran.

## What Would Have Happened Without Verification

If the orchestrator had trusted the plan:

1. **Leaf 01:** Subagent would have changed `Publish()` to return `(int, error)`,
   breaking 20+ call sites. Build fails. Multiple fix cycles to either revert
   or update all callers.
2. **Leaf 02:** Subagent would have changed `NewAgentLoop()` to return
   `(*AgentLoop, error)`, breaking 25+ call sites. Worse, some callers are in
   test files that would need assertions rewritten.
3. **Leaf 04:** Subagent would have tried to change `om()` to return a tuple,
   which is impossible in Go for a variadic function — the subagent would
   have flailed or invented a workaround.

Each would have required at least 2-3 fix cycles and possibly manual
orchestrator intervention to correct the cascading breakage. Total cost:
~30-45 minutes of wasted time across 5 leaves.

## Outcome With Verification

- All 5 subagents received corrected dispatch instructions with actual
  signatures inlined
- All 5 returned APPROVED on first review
- Zero fix cycles
- Total wall time: ~4 minutes (subagents ran in parallel, ~60-235s each)

## The General Rule

**Every factual claim in a plan leaf about existing code is unverified until
the orchestrator checks it.** Plans are written by LLMs that may be working
from memory, stale documentation, or inference. The pre-dispatch verification
pass is cheap (6 batched search_files calls) and prevents cascading failures
that cost hours to fix.

Claims to verify:
1. Function/method signatures (return types, parameter types)
2. Caller counts (determines whether signature changes are feasible)
3. Import state ("add import X if not present" — check if already imported)
4. Line numbers (code drifts between plan writing and execution)
5. Behavior descriptions ("the function currently does X" — verify it does)
