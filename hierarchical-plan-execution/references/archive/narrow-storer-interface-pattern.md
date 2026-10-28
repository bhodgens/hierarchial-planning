# Nnarrow storer interface pattern
When to use: analysis subpackages need storage.
Lesson: narrow Storer interface pattern.

# Narrow Storer Interface Pattern for Analysis Subpackages

> Pattern reference. When implementing analysis processors (segmenter, shortcut
> analyzer, pattern miner) that depend on store methods, define a narrow Storer
> interface in EACH analysis subpackage rather than depending on the full
> store.Store interface. This follows the Interface Segregation Principle and
> makes each processor independently testable with a minimal mock.

## Session

- **Date:** 2026-08-04
- **Project:** AgentAudit (Go backend)
- **Leaf:** 02-ngram-pattern-miner (bigrams/trigrams, pattern persistence)

## The Pattern

Each analysis subpackage defines its own `Storer` interface containing only the
methods it actually calls:

```go
// internal/analysis/patterns/miner.go
package patterns

type Storer interface {
    StreamEvents(ctx context.Context, since time.Time) ([]types.Event, error)
    UpsertPattern(ctx context.Context, p types.Pattern) error
}
```

```go
// internal/analysis/shortcuts/analyzer.go
package shortcuts

type Storer interface {
    StreamEvents(ctx context.Context, since time.Time) ([]types.Event, error)
    UpsertShortcutStats(ctx context.Context, stats []types.ShortcutStat) error
}
```

```go
// internal/analysis/session/segmenter.go
// (uses full store.Store because it needs InsertSessions which is already on the interface)
```

The full `store.Store` interface satisfies each narrow Storer automatically (Go
structural typing). When the full Store doesn't yet have a needed method (e.g.,
`UpsertPattern`), the analysis package still compiles — only the wiring layer
(cmd/server/main.go) needs the method added to the concrete `SQLiteStore`.

## Why Not Depend on Full store.Store?

1. **Forward compatibility:** The spec for the pattern miner referenced
   `InsertPatterns` and `UpsertPattern` on `store.Store`, but those methods
   don't exist yet on the real interface. Defining a narrow `Storer` in the
   analysis package lets the package compile and test independently.

2. **Minimal mocks:** Tests create a mock with 2-3 methods instead of stubbing
   all 8+ methods on the full Store interface. Less boilerplate, fewer places
   to make mistakes.

3. **Clear dependency surface:** Reading the `Storer` interface tells you
   exactly what store operations the processor performs — no need to scan
   the entire implementation.

4. **Established convention:** The shortcuts analyzer already uses this pattern
   in the same project. Following it keeps the codebase consistent.

## When to Use Full store.Store Instead

- When the processor needs 4+ store methods (the narrow interface becomes noise)
- When the processor is the only consumer of a new method and that method is
  simple enough to add directly to the Store interface + SQLiteStore
- For segmenters/processors that are tightly coupled to the store lifecycle

## Migration Table Pattern

New tables for analysis output are added as numbered SQL files in
`internal/store/migrations/`. The existing `embed.FS` migration runner
(`migrations.go`) automatically discovers and applies them:

```
internal/store/migrations/
  001_initial.sql      # events, sessions, keystroke_log, shortcut_stats, screenshots
  002_patterns.sql     # patterns table (added by this leaf)
```

No code change to `migrations.go` is needed — the `//go:embed migrations/*.sql`
directive picks up new files automatically. The migration runner tracks applied
versions in `schema_migrations` and skips already-applied migrations.

### Migration file conventions

- `NNN_descriptive_name.sql` — zero-padded version number prefix
- Use `CREATE TABLE IF NOT EXISTS` for idempotency
- Add indexes with `CREATE INDEX IF NOT EXISTS`
- Include a `UNIQUE()` constraint for upsert-friendly tables (e.g.,
  `UNIQUE(machine_id, app_sequence, typical_time)` on patterns)
- Add a `status` column with a default ('active') for soft-delete workflows
