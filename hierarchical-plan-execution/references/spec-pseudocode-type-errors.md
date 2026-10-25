# Spec Pseudocode Type Errors — When the Leaf's Go Stubs Don't Compile

> Worked example for leaf implementation. A leaf spec contained Go pseudocode
> stubs with type mismatches and signature incompatibilities that would not
> compile as written. The implementer must treat spec pseudocode as a design
> sketch, not copy-paste-ready code — and must verify type compatibility
> against the actual interface contracts before writing.

## Session

- **Date:** 2026-08-04
- **Project:** AgentAudit (Go backend, chi/SQLite)
- **Plan tree:** `docs/plans/phase1-mvp/04-analysis/01-session-segmenter.md`
- **Scope:** Session segmenter state machine + analysis Engine goroutine manager

## The Three Type Errors in the Spec

### Error 1: Appending wrapper struct to base-type slice

The spec's `Segment` pseudocode showed:

```go
var sessions []types.Session  // base type
current := seg.startSession(ev)  // returns *sessionExt
// ...
sessions = append(sessions, *current)  // ❌ *sessionExt is not types.Session
```

`sessionExt` embeds `types.Session` via composition, but `append(sessions, *current)`
does NOT extract the embedded struct — it tries to append the wrapper type itself.
This fails to compile: `cannot use *current (type sessionExt) as type types.Session`.

**Fix:** Append the embedded field explicitly: `sessions = append(sessions, current.Session)`.

### Error 2: processorFunc signature vs Run() error mismatch

The spec defined:
```go
type processorFunc func(ctx context.Context)  // no return value
```

But `Segmenter.Run` was specified as:
```go
func (seg *Segmenter) Run(ctx context.Context) error  // returns error
```

These signatures are incompatible. You cannot register `seg.Run` as a `processorFunc`
without an adapter wrapper.

**Fix:** Register via wrapper at the call site:
```go
engine.RegisterProcessor(func(ctx context.Context) { _ = seg.Run(ctx) })
```

### Error 3: Mock store referencing non-existent interface methods

The spec's test mock implemented methods not in the `Store` interface:
```go
func (m *mockStore) InsertPatterns(ctx context.Context, patterns []types.Pattern) error { return nil }
func (m *mockStore) UpsertPattern(ctx context.Context, p types.Pattern) error { return nil }
// ... types.Pattern doesn't exist in this project phase
```

If you copy-paste the mock, you get unused method warnings and the mock references
types that don't exist. The mock should implement ONLY the actual Store interface.

**Fix:** Strip the mock down to exactly the Store interface methods. For methods
not used by the segmenter (InsertEvents, QuerySessions, etc.), return zero values.

## The General Rule

**Spec pseudocode is a design sketch, not compilable code.** Leaf specs are written
by LLMs that may infer types incorrectly, especially when:
- Internal wrapper structs are introduced mid-algorithm (the spec describes `sessionExt`
  but then forgets to use `.Session` when appending)
- Function signatures span different design tiers (Engine's `processorFunc` vs
  Segmenter's `Run` were designed in separate sections of the same leaf)
- Mock objects are specified with methods from a future phase's expanded interface

Before writing the implementation, verify:
1. Every `append(slice, value)` where `value` is a wrapper struct — extract the
   embedded base type
2. Every function registration (`RegisterProcessor(seg.Run)`) — check that
   signatures match exactly, plan for an adapter wrapper if they don't
3. Every mock store — implement only the methods in the current interface definition,
   not methods the spec mentions from future phases

## Concurrent Sibling Interface Modification

During the same session, a sibling subagent changed `InsertScreenshot` in the
shared `store.Store` interface from returning `error` to returning `(int64, error)`.
This broke the mock store's interface conformance mid-session.

**Symptom:** LSP diagnostic: `*mockStore does not implement store.Store (wrong type
for method InsertScreenshot) have InsertScreenshot(context.Context, types.Screenshot)
error want InsertScreenshot(context.Context, types.Screenshot) (int64, error)`

**Fix:** Update the mock to match the current interface. When sibling subagents
modify shared interfaces concurrently:
1. Watch for patch warnings: `_warning: file was modified by sibling subagent`
2. Re-read the interface definition before fixing mock compilation errors
3. Align mock stubs to the current (sibling-modified) interface signature

This is a variant of the Go interface cascade (see go-interface-cascade.md) but
happens at mock-implementation time rather than at the production-code level.

## Test Mock Drain Pattern for Periodic Processors

When testing a periodic processor (ticker-based `Run` loop) with a mock store:

**Problem:** If `StreamEvents` always returns the same events, the processor
inserts duplicate sessions on every tick. The test sees N copies of the same session.

**Fix:** The mock's `StreamEvents` should drain events on first read, mirroring
real store behavior where events are consumed once:

```go
func (m *mockStore) StreamEvents(ctx context.Context, since time.Time) ([]types.Event, error) {
    m.mu.Lock()
    defer m.mu.Unlock()
    ev := m.events
    m.events = nil  // drain
    return ev, nil
}
```

This prevents duplicate processing and makes the test deterministic.

## Graceful Shutdown Contract for Processor Run Loops

When a processor's `Run(ctx)` is registered with an Engine that manages lifecycle
via context cancellation:

**Problem:** If `Run` returns `ctx.Err()` on cancellation, tests that cancel the
context see `context.DeadlineExceeded` as an error return, failing `require.NoError`.

**Fix:** `Run` should return `nil` on context cancellation — this is graceful
shutdown, not an error condition:

```go
func (seg *Segmenter) Run(ctx context.Context) error {
    // ...
    for {
        select {
        case <-ctx.Done():
            return nil  // graceful shutdown, not an error
        case <-ticker.C:
            // process
        }
    }
}
```

The Engine's `Stop()` calls `cancel()` on the shared context; processors should
treat that as a normal exit signal.
