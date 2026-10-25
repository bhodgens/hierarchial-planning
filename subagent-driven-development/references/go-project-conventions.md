# Go Project Conventions (jobforge / pgx / River)

Reusable patterns observed across a multi-phase Go implementation. These are
NOT project-specific — they apply to any Go monolith using pgx/v5, River queue,
and chi router. Cite this when dispatching Go subagents so they follow
conventions without rediscovering them.

## Postgres + pgx/v5 conventions

### UUID columns stored as TEXT

pgx scans UUID columns into `string`, not `uuid.UUID`. The pattern across the
codebase is: declare a `string` variable, scan into it, then
`uuid.MustParse(idStr)`.

```go
var idStr, userIDStr string
err := pool.QueryRow(ctx, `SELECT id, user_id FROM users WHERE id = $1`, id.String()).
    Scan(&idStr, &userIDStr)
record.ID = uuid.MustParse(idStr)
```

Queries pass UUIDs via `.String()`:
```go
pool.QueryRow(ctx, `INSERT INTO ... VALUES ($1)`, uuidVar.String())
```

### JSONB columns

Store as `map[string]X` or struct on the Go side. Marshal via `json.Marshal`
before insert, scan the JSONB column into `[]byte` and `json.Unmarshal`:
```go
breakdownBytes, _ := json.Marshal(job.ScoreBreakdown)
// INSERT ... score_breakdown, ... VALUES ($N, $N+1, ...)
// On read:
var raw []byte
rows.Scan(&raw, ...)
json.Unmarshal(raw, &job.ScoreBreakdown)
```

### Error wrapping convention

Every error gets wrapped with the package name + action:
```go
return fmt.Errorf("auth: find user by id: %w", err)
return fmt.Errorf("search: store job: %w", err)
return fmt.Errorf("resume: create derived resume: %w", err)
```

### nil slice → empty slice

Stores that return lists return `[]T{}` (not nil) when empty, so JSON
serialization produces `[]` not `null`:
```go
if list == nil { list = []DerivedResume{} }
```

## River queue (Postgres-backed job queue)

### Schema migration is NOT automatic

River manages its OWN schema (`river_job`, `river_leader`, `river_queue`
tables) separate from app migrations. A fresh database will fail with:
```
ERROR: relation "river_leader" does not exist (SQLSTATE 42P01)
```

Fix: call `rivermigrate.New(...).Migrate(ctx, DirectionUp, nil)` BEFORE the
first `client.Start(ctx)`. Do this in ONE process only (the web server is a
good owner — workers assume the schema exists):

```go
import "github.com/riverqueue/river/rivermigrate"

func Migrate(ctx context.Context, pool *pgxpool.Pool) error {
    migrator, err := rivermigrate.New(riverpgxv5.New(pool), &rivermigrate.Config{})
    if err != nil {
        return fmt.Errorf("jobs: create river migrator: %w", err)
    }
    if _, err := migrator.Migrate(ctx, rivermigrate.DirectionUp, nil); err != nil {
        return fmt.Errorf("jobs: run river migrations: %w", err)
    }
    return nil
}
```

### client.Start(nil) panics

River's `Start(ctx)` and `Stop(ctx)` REQUIRE a real context. Passing `nil`
panics with `cannot create context from nil parent`. Always derive from
`context.Background()`:
```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()
client.Start(ctx)
// ... on shutdown:
stopCtx, stopCancel := context.WithCancel(context.Background())
defer stopCancel()
client.Stop(stopCtx)
```

### Two processes racing the same River migration collide

If both web and worker call `Migrate` at startup, they race the same
`CREATE TYPE` / `CREATE TABLE` statements and one fails with:
```
duplicate key value violates unique constraint "pg_type_typname_nsp_index"
```
Migration ownership should live in ONE process. Web owns it; worker assumes
the schema is ready.

## chi router patterns

### Middleware order matters

Security headers → RequestID → RequestLogger → Recoverer → RateLimit →
**AuthMiddleware** (session-based, global).

**DeveloperAuthMiddleware must NOT be in the global chain.** Scope it to the
`/api/*` route group only, inside the group's `r.Use(...)` block. If it runs
globally, a developer token can authenticate browser session endpoints
(`/app/account/delete`, `/app/developer-tokens`) that were designed for
cookie-auth + CSRF only — making tokens session-equivalent credentials,
which is more than the feature intends.

```go
// Global: session auth only
r.Use(middleware.AuthMiddleware(sessionStore, userStore))

// API group: developer token auth + session fallback
r.Group(func(r chi.Router) {
    r.Use(middleware.DeveloperAuthMiddleware(devTokenStore, userStore))
    r.Use(middleware.AuthMiddleware(sessionStore, userStore))
    r.Use(middleware.RequireAuth)
    r.Use(middleware.RequireDeveloper)
    r.Post("/api/search/jobs", ...)
})
```

AuthMiddleware should short-circuit (skip session check) if a user is already
in context — set by the developer middleware that ran first in the group.

### Shared context key for user

The context key type is private to the middleware package:
```go
type contextKey string
const contextKeyUser contextKey = "auth_user"
```
Both developer-token and session middleware write to the SAME key, so handlers
read via a single `GetUser(ctx)` helper.

## Makefile + background process patterns

### Don't background with `&` inside Makefile recipes

Make runs each recipe line in a separate shell. A backgrounded process (`&`)
becomes orphaned when that line's shell exits, and may receive SIGHUP. The
`$$!` PID capture also doesn't reliably propagate across make's per-line
shells.

**Fix:** put the launch + readiness-check logic in a standalone shell script
(`scripts/dev-run.sh`) and invoke it from the Makefile:
```makefile
dev: setup-db build
	@scripts/dev-run.sh $(BIN_DIR) $(PORT) $(DEV_DIR)
```
The script handles: port-in-use check, `nohup ... &` launch, readiness polling
via `lsof -nP -iTCP:$PORT -sTCP:LISTEN`, PID file management, and clear error
output on early exit.

### Wait for readiness, don't sleep

For servers that run migrations before listening, poll the port with a bounded
loop rather than a fixed `sleep 2`:
```bash
for _ in $(seq 1 30); do
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1 && break
  kill -0 "$(cat "$PID_F")" 2>/dev/null || { echo "exited early"; tail -15 "$LOG"; exit 1; }
  sleep 0.5
done
```
This also catches the case where the process died during startup (migration
failure, port conflict) — the `kill -0` check fails and you get the log tail
instead of a silent hang.

## go:embed migration directories

Migrations are embedded via `//go:embed migrations/*.sql`. New migration files
are picked up automatically at compile time — BUT guard tests that count
migrations must be updated:
```go
// internal/db/db_test.go
const expectedCount = 13  // bump when adding a migration
```
A subagent adding a migration will compile fine but break this test on the
next `go test ./internal/db/`.

## String truncation: runes, not bytes

When truncating strings that may contain multi-byte UTF-8 characters (émoji,
CJK, curly quotes, accented text from job postings or LLM output), Go's
`str[:N]` slices by BYTES and can split a multi-byte sequence mid-character,
producing invalid UTF-8. This causes: (a) score divergence when porting
Python (which slices by code points), (b) pgx rejecting the string on
INSERT to a TEXT column, (c) replacement characters in stored data.

**Always truncate by runes when the source is external:**
```go
// WRONG — splits multi-byte UTF-8
if len(desc) > MaxDescriptionLen {
    desc = desc[:MaxDescriptionLen]
}

// CORRECT — truncates at a valid rune boundary
if runes := []rune(desc); len(runes) > MaxDescriptionLen {
    desc = string(runes[:MaxDescriptionLen])
}
```

This applies to any function that caps description/synopsis/bio length before
storage. Review subagents flag the byte-slice pattern as Critical.

## Subagent dispatch context for Go tasks

When dispatching a Go subagent, embed in `context`:
- Exact struct field names and types from the target file (pre-read it)
- The package's error-wrapping convention (e.g. `fmt.Errorf("auth: ...: %w", err)`)
- UUID scan pattern (string → MustParse) if the package uses it
- Any frozen signatures ("DO NOT change the signature of X.ChatCompletion")
- The commit message + exact `git add` file list (never `git add -A`)
