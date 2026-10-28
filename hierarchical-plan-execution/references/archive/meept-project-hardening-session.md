# Mmeept project hardening session
When to use: project-hardening session record.
Lesson: hardening leaf shapes and gate outcomes.

# meept Project-Hardening Session (2026-07-29)

> Three pitfalls discovered during project-hardening plan execution.
> See SKILL.md pitfalls #43, #44, #45 for the canonical descriptions.
>
> 2026-08-24 additions from the unified-theming tree:
> - Const-removal sweeps in Flutter leave `decoration:  BoxDecoration(`
>   double-space artifacts. After any leaf that strips `const` keywords,
>   run `dart format <touched .dart files>` before analyze/commit — same
>   class as Pitfall 30's gofmt rule, Flutter side.
> - Orchestrator stash hazard: verifying "are these gofmt failures
>   pre-existing?" via `git stash -q` + check + `stash pop` risks a pop
>   conflict against in-flight subagent edits landing mid-check. Safer
>   equivalent: `git stash show` nothing — instead compare against HEAD
>   with `git show HEAD:<file>` piped to gofmt, or accept pre-existence
>   when the files are outside the leaves' ownership. NEVER stash on this
>   user's repos while subagents are running (user standing rule: never
>   stash at all).
> - hujson `.json5` gotcha: Standardize rejects unquoted object keys;
>   quoted keys + comments is the supported subset.

## Session Context

- **Plan:** `.hermes/plans/project-hardening/` — 5 post-review fixes
- **6 leaves** across 4 items (2 branches + 2 standalone)
- **Result:** 100% complete, 3 commits, all gates passed

## Pitfall 43: Subagent Interface Cascade Blocks Orchestrator Commit

### What Happened

The orchestrator implemented 4 hardening leaves in-session (loop.go, manager.go,
server.go) while a worktree subagent was adding `SetWorktree` to the `Store`
interface in `internal/session/store.go`.

The orchestrator attempted to commit its hardening fixes. The pre-commit hook
builds the ENTIRE tree, not just staged files. The build failed:

```
*SQLiteStore does not implement Store (missing method SetWorktree)
```

The subagent had added the interface method but hadn't yet written the
SQLiteStore implementation. The orchestrator's unrelated files triggered the
build failure because Go's type system is package-transitive.

### Recovery

1. `git reset HEAD` — unstaged the failed commit
2. Checked if subagent was still running — it was
3. Waited for subagent to finish (landed SQLiteStore.SetWorktree)
4. Verified `go build ./...` passed
5. Committed the combined tree

### General Rule

When holding commits for an in-flight subagent that modifies shared interfaces:
- Stage ONLY files in packages that don't import the modified interface
- Or hold ALL commits until `go build ./...` passes on the combined tree
- The pre-commit hook builds the whole project, not just your staged files

## Pitfall 44: mutexio False Positive on IIFE Collect-Then-Operate

### What Happened

`GetOrCreateWired` needed to call `loop.Close()` before evicting a stale loop.
`Close()` calls `wg.Wait()` (blocking I/O — violates mutex scope rule).

First attempt: called `Close()` inside the `m.mu.Lock()` region. `mutexio`
correctly flagged it.

Second attempt: restructured to IIFE collect-then-operate:

```go
var staleLoop *AgentLoop
func() {
    m.mu.Lock()
    defer m.mu.Unlock()
    // ... collect staleLoop under lock
}()
// IIFE released the lock above
if staleLoop != nil {
    staleLoop.Close() // mutexio STILL flags this — can't see IIFE boundary
}
```

`mutexio` is static — it sees `.Close()` inside a function that has
`m.mu.Lock()` elsewhere and flags it, even though the lock was released by
the IIFE's `defer`.

### Fix

Suppress with `//nolint:mutexio` and a comment explaining the scope separation.
Also documented the pattern in CLAUDE.md's mutex scope section so future
developers recognize the false positive.

## Pitfall 45: Flutter Freezed Model Field Addition Workflow

### What Happened

Adding `worktreeId` and `worktreePath` to the `Session` freezed class in
`api_models.dart`. The LSP immediately showed errors because the generated
`.freezed.dart` and `.g.dart` files didn't have the new fields.

### Fix Workflow

1. Edit `api_models.dart` — add fields with `@JsonKey` annotations
2. Run: `cd ui/flutter_ui && dart run build_runner build --delete-conflicting-outputs`
3. Verify: `flutter analyze lib/` shows no new errors
4. Stage generated files alongside source

Build runner took 16.7s with 1316 outputs. All generated files committed
alongside the source change.

### Key Detail

The `--delete-conflicting-outputs` flag is important — without it, build_runner
may skip regeneration when it thinks outputs are up-to-date but the source has
drifted.

## Bonus: Pre-Existing Bug Found (rpc.go Type Assertion)

The pre-commit hook's error output initially included LSP diagnostics about
`CreateWorktree` using `result.(map[string]any)` on `json.RawMessage` — a
`[]byte` slice, not an interface. The type assertion would always fail at
runtime. The subagent independently fixed this by switching to
`json.Unmarshal` returning `*types.WorktreeResponse`.

The orchestrator then dispatched an audit subagent to check ALL other RPC
client methods for the same bug pattern. This is a good example of fixing the
class of bug, not just the instance.
