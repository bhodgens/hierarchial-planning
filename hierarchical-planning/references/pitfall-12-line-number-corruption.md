# Pitfall 12 - Line-Number Corruption from read_file

When to use: dispatching leaf agents that will inspect or write existing source files.
Lesson: read_file output carries `     N|` prefixes; if a leaf feeds it into write_file, those prefixes are baked into source. Inline source snippets in the dispatch context instead.

Leaf agents that use `read_file` to inspect existing code and then feed that output into `write_file` bake `     N|` line-number prefixes into source files. This is catastrophic in code (not just reports) and compounds when the orchestrator assembles outputs from multiple leaves.

## Three-part prevention

1. **Inline the relevant source snippets in the dispatch context** instead of telling agents to read files. If source material is too large to inline, the orchestrator reads it once and extracts the relevant portion, then passes the extracted content as context.
2. **If agents must explore**, instruct them to use `search_files` (returns clean content) or `terminal("cat file")` rather than `read_file`.
3. **Tell agents: "After writing a file, do NOT read it back to verify - write once and stop."**

## Post-run verification

After all leaves complete, verify no corruption:

```
grep -rcE '^\s+[0-9]+\|' --include='*.go' --include='*.py' --include='*.ts' --include='*.md' .
```

should return zero hits. For docs-only trees the glob must include `*.md` (Pitfall 18).

Related: Pitfall 19 (stale orchestrator read-state vs subagent writes - a different failure mode), `references/dispatch-scratch-rig-mlx-pitfalls.md` (grep anchors survive; line numbers rot).
