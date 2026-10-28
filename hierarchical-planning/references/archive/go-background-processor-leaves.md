# Go Background Processor Leaves — TDD Patterns

**When to use:** Writing hierarchical-planning leaf documents for Go modules that run as periodic background goroutines inside a server process (analysis engines, background workers, cron-like processors, pipeline stages). These leaves read from a Store interface, process data, and write results back on a ticker.
Lesson: engine + per-tick processor architecture with Store-injected constructors for Go background-worker leaves.

## Architecture: Engine + Processors

A Go backend with background analysis has two layers:

1. **Engine** (`internal/analysis/engine.go`) — manages processor goroutine lifecycle
2. **Processors** (`internal/analysis/<module>/`) — each runs independently on its own ticker

```
Events table → [Processor A] → derived_table_a (every 5 min)
Events table → [Processor B] → derived_table_b (every 1 hour)
Sessions + stats → [Processor C] → summary_table (daily)
```

Each processor receives a Store interface at construction. They do NOT call each other directly.

## Engine Lifecycle Pattern

The Engine uses `context.Context` + `sync.WaitGroup` for graceful shutdown:

```go
package analysis

type processorFunc func(ctx context.Context)

type Engine struct {
    store      store.Store
    processors []processorFunc
    cancel     context.CancelFunc
    wg         sync.WaitGroup
}

func NewEngine(s store.Store) *Engine {
    return &Engine{store: s}
}

func (e *Engine) RegisterProcessor(fn processorFunc) {
    e.processors = append(e.processors, fn)
}

func (e *Engine) Start(ctx context.Context) error {
    childCtx, cancel := context.WithCancel(ctx)
    e.cancel = cancel
    for _, fn := range e.processors {
        e.wg.Add(1)
        go func(f processorFunc) {
            defer e.wg.Done()
            f(childCtx)
        }(fn)
    }
    return nil
}

func (e *Engine) Stop() error {
    if e.cancel != nil { e.cancel() }
    e.wg.Wait()
    return nil
}
```

**Test pattern:** Use `context.WithTimeout` to test Start/Stop without hanging:

```go
func TestEngine_StartStop(t *testing.T) {
    e := NewEngine(nil)
    ctx, cancel := context.WithCancel(context.Background())
    require.NoError(t, e.Start(ctx))
    time.Sleep(50 * time.Millisecond) // let goroutines start
    require.NoError(t, e.Stop())
}
```

## Processor Run Loop Pattern

Each processor has a `Run(ctx context.Context) error` method with a ticker. The signature `func(ctx context.Context) error` matches `processorFunc` so the Engine can register it directly.

```go
type Segmenter struct {
    store    store.Store
    interval time.Duration // override in tests
}

func (s *Segmenter) Run(ctx context.Context) error {
    if s.interval == 0 { s.interval = 5 * time.Minute }
    lastProcessed := time.Now().Add(-s.interval)

    ticker := time.NewTicker(s.interval)
    defer ticker.Stop()

    // Optional: do one immediate run at startup
    for {
        select {
        case <-ctx.Done():
            return nil
        case <-ticker.C:
            events, err := s.store.StreamEvents(ctx, lastProcessed)
            if err != nil { continue }
            if len(events) == 0 { continue }

            result, err := s.Process(ctx, events)
            if err != nil { continue }

            if err := s.store.SaveResult(ctx, result); err != nil { continue }
            lastProcessed = events[len(events)-1].Timestamp
        }
    }
}
```

**Test pattern:** Set `interval` to 50ms and use `context.WithTimeout(context.Background(), 200*time.Millisecond)`:

```go
func TestSegmenter_Run_ProcessesEvents(t *testing.T) {
    ms := &mockStore{events: seedEvents}
    s := NewSegmenter(ms)
    s.interval = 50 * time.Millisecond

    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()

    err := s.Run(ctx) // returns when ctx expires
    require.NoError(t, err)
    require.True(t, ms.saveCalled, "SaveResult was not called")
}
```

## Mock Store for Testing

Every leaf needs a mock implementing the full Store interface. Stub unused methods with `return nil`:

```go
type mockStore struct {
    events     []types.Event
    saved      []types.Session
    saveCalled bool
}

func (m *mockStore) StreamEvents(ctx context.Context, since time.Time) ([]types.Event, error) {
    return m.events, nil
}
func (m *mockStore) InsertSessions(ctx context.Context, s []types.Session) error {
    m.saved = s; m.saveCalled = true; return nil
}
// Stub ALL other Store methods...
func (m *mockStore) InsertEvents(ctx context.Context, e []types.Event) error { return nil }
func (m *mockStore) QuerySessions(ctx context.Context, f store.SessionFilter) ([]types.Session, error) { return nil, nil }
// etc.
```

## Two-Tier Test Strategy

Each processor leaf should have two levels of tests:

1. **Pure function tests** — test `Process()` / `Analyze()` / `Segment()` directly with in-memory data slices. No Store needed. These test the algorithm.
2. **Run loop test** — test `Run()` with a mock store and fast interval. These test the lifecycle and store interaction.

Pure function tests are the majority. Run loop tests are 1-2 per processor.

## Leaf Task Structure for Processors

A typical processor leaf has 5-7 tasks:

| Task | What it builds |
|------|---------------|
| 1 | Engine struct + Start/Stop lifecycle (if this is the foundation leaf) |
| 2 | Core processing function (pure, takes data slice, returns result) |
| 3 | Edge case handling (empty input, boundary conditions) |
| 4 | Classification/scoring logic (tiers, thresholds, filters) |
| 5 | Run loop with ticker + context cancellation |
| 6 | Engine registration wiring |

Tasks 2-4 are pure function tests (no Store). Task 5 uses the mock Store pattern.

## Contract Patterns

### Store Extension for Write-Back

The orchestrator should define Store write extensions as a named contract so the implementing leaf (branch 01-backend) knows exactly what to add:

```go
// Extensions to Store interface
InsertSessions(ctx context.Context, sessions []Session) error
UpsertPattern(ctx context.Context, p Pattern) error
UpsertShortcutStats(ctx context.Context, stats []ShortcutStat) error
```

### Processor Registration Contract

The Engine exposes `RegisterProcessor(func(ctx context.Context))`. Each processor's `Run` method matches this signature. The wiring happens in `cmd/server/main.go`:

```go
engine := analysis.NewEngine(store)
engine.RegisterProcessor(segmenter.Run)
engine.RegisterProcessor(miner.Run)
engine.Start(ctx)
```

## Common Pitfalls

1. **Don't make processors depend on each other.** Each reads from the Store independently. Cross-processor coupling breaks the concurrency model.
2. **Use `_ = lastTs` or similar** to suppress unused-variable errors in intermediate implementations during TDD — clean up before reporting completion.
3. **The mock store must implement the FULL Store interface**, even methods the leaf doesn't use. Missing methods = compile errors.
4. **Set `interval` to a short value in tests** (50ms). Never use the real 5-minute/hourly interval in tests.
5. **Run loops should `continue` (not `return`) on errors** during the tick — a transient Store error shouldn't kill the processor permanently.
6. **First-run lookback:** processors that need historical context (e.g., pattern mining across days) should look back further than one interval on first run. Use `time.Now().Add(-48 * time.Hour)` as the initial `lastProcessed`.
