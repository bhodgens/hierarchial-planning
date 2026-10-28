# Ppitfall 55 stale orchestrator reads
When to use: orchestrator reads stale state after dispatch.
Lesson: re-read files after subagent writes; cache invalidation discipline.

# Pitfall 55: Stale Orchestrator Reads After Subagent Dispatch

## Problem

When an orchestrator dispatches a subagent to implement a leaf, the subagent may return with STALE information — it read files earlier in the session (or in a prior session) and its context doesn't reflect changes made by other concurrent work. The orchestrator then acts on outdated state, leading to:

1. Failed patches because the old_string no longer matches
2. Incorrect diffs that don't apply cleanly
3. Build failures from pre-existing WIP in unrelated packages

## Example

Session flow:
1. Orchestrator reads `internal/llm/providers.go` lines 92-97 (struct definition)
2. Orchestrator dispatches subagent to implement changes
3. While subagent runs, another process or session modifies the file
4. Subagent returns with stale context, tries to patch using old line numbers
5. Patch fails because the file has drifted

Or even simpler:
1. Orchestrator reads a file at offset 92-97
2. Orchestrator patches the file based on that read
3. Patch tool warns: "subagent modified files the parent previously read"
4. Orchestrator proceeds anyway, patch applies against stale content
5. Result: wrong edits or failed patches

## Prevention

### Before Dispatching

1. **Note what you've read.** Keep a mental (or scratchpad) list of files read in this session.
2. **Use exact content for patches.** When you know you'll need to patch a file you've read, capture the EXACT content you're patching against in your context. Don't rely on line numbers alone.
3. **Dispatch with full context.** Include the relevant source snippets inline in the dispatch context so the subagent doesn't need to read files.

### After Subagent Returns

1. **Re-read before acting on stale data.** If a subagent returns with potentially stale information, re-read the affected files with `read_file` (full file, not paginated) before making any edits.
2. **Check git status first.** Before committing, run `git diff --name-only` and `git status --short` to see what actually changed vs. what you expected.
3. **Build before committing.** Run `go build ./<package>/...` for each package you touched before attempting to commit. Catch compile errors early.

### Handling Pre-Existing WIP

When committing, you may encounter build failures from UNRELATED packages that have pre-existing WIP (e.g., `internal/tools/builtin/` with signature changes from another session). This blocks the pre-commit hook even though YOUR changes compile correctly.

**Pattern:**
```bash
# 1. Check if your package builds
go build ./internal/llm/... ./internal/agent/...  # Should pass

# 2. Check what's failing
git diff --name-only  # See what you touched

# 3. If unrelated packages fail, stash them
git stash push -m "pre-existing WIP" <unrelated-package>/

# 4. Commit your changes
git add <your-files> && git commit

# 5. Restore the stash
git stash pop
```

**Key insight:** The pre-commit hook checks ALL packages, not just staged ones. Unrelated WIP in unstaged files can block your commit. Stashing the unrelated WIP temporarily lets you commit your clean changes.

### When Subagent Times Out or Returns Stale

If a subagent times out or returns with incomplete/stale work:

1. **Check disk for partial work.** Run `find <dir> -name "*.go" -newer <marker>` or `git status --short` to see what landed.
2. **Compile check.** Run `go build ./<package>/...` to see if core compiles.
3. **If it compiles, complete missing pieces directly.** Write the missing tests or fixes as the orchestrator — faster than re-dispatching.
4. **Don't blindly re-dispatch.** Each retry burns API calls on re-reading stale context.

## Recovery

If you've already acted on stale data:

1. **Abort the commit.** Run `git reset HEAD~1` if you already committed.
2. **Re-read the current state.** Use `read_file` on the affected files.
3. **Re-apply patches correctly.** Use the current content, not what you read earlier.
4. **Verify with build and tests.** Don't skip this step.

## Related Pitfalls

- **Pitfall 19:** Orchestrator patching a file a subagent already edited = stale read-state mismatch
- **Pitfall 25:** Subagent timeout → partial work on disk → orchestrator completes directly
- **Pitfall 54:** Late 429 after work lands — check disk + /tmp test logs before re-doing
