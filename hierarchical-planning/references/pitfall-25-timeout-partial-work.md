# Pitfall 25 - Subagent Timeout Leaves Partial Work on Disk

When to use: a delegate_task returns status=timeout, or you are tempted to re-dispatch a timed-out leaf.
Lesson: check disk first - the subagent usually wrote the files and died on verification; completing in-session is faster than re-dispatching.

Subagents implementing large leaves (~90K+ context) can hit the timeout, especially on providers with slower inference. `delegate_task` returns `status=timeout` - but the subagent often created most or all files before timing out; it simply didn't finish the last steps (tests, entry points, formatting).

## Do NOT re-dispatch from scratch. Instead:

1. `find <package> -type f -name "*.go"` (or the language's extension) to see what landed.
2. `go build ./<package>/...` (or the language's equivalent) to check if the core compiles.
3. If it compiles, write the missing pieces (tests, entry points, gofmt fixes) directly as the orchestrator - faster than re-dispatching and burning another full timeout.
4. If the files DON'T compile or are clearly broken, THEN re-dispatch with narrowed scope (just the broken pieces).

This pattern occurred 3x in one forest's waves (IPC leaf, embed model leaf, identity leaf) - in all 3 cases the subagent had written all source files; the orchestrator completed tests/entry-points in under 5 minutes each.

## Related

- Pitfall 28: compile-check IMMEDIATELY on any subagent return - undefined placeholder references are a distinct failure mode even without a timeout.
- `references/wave-execution-patterns.md` (recovery pattern proven 7+ times), `references/subagent-failure-salvage.md` (full salvage decision tree incl. GDScript variants), `references/gdscript-bulk-dispatch.md` (600s GDScript timeout variants).
