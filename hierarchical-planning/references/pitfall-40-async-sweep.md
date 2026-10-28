# Pitfall 40 - Sweep for Subagent Test Files and Side-Effects After Each Completion

When to use: any subagent completion notification (async or batch), before committing only the highlighted files.
Lesson: subagents under-report test files, signal additions, and .uid files; run git status + diff --stat + ls-files --others after EVERY notification and commit all relevant files.

Subagents often create files the orchestrator doesn't know about - test files, support files, EventBus signal additions, `.uid` files. When the orchestrator commits only the files the subagent highlighted in its summary, these extras are left uncommitted on disk. If a later subagent or orchestrator edit touches the same area, the uncommitted files are silently overwritten or orphaned.

## The cost of skipping it

One GDScript session caught, via post-notification sweeps: (a) 27 GUT tests (376 lines) from an async notification; (b) 11 tests PLUS 2 signals added to `event_bus.gd`, caught from `git diff --stat`; (c) 20 tests + 9 signals, caught from `git ls-files --others`; (d) 16 tests (172 lines); (e) 22 tests (296 lines). Total: 96 test functions (178+ assertions) that would have been lost.

## Sweep procedure

After EACH subagent async delegation notification arrives (and after each batch completes, not just at final commit):

```
git status --short
git diff --stat HEAD
git ls-files --others --exclude-standard
```

For GDScript projects specifically: also check `git diff --stat HEAD` for modifications to `event_bus.gd` (subagents commonly add signals) and `git ls-files --others` for untracked `test_<system>.gd` files.

Stage and commit all relevant files from each subagent's output before processing the next notification or moving to the next task.

Full procedure: `references/gdscript-bulk-dispatch.md` (Async Notification Sweep section) and `references/wave-execution-patterns.md`.
