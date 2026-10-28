# Pre-Dispatch Checks: API Surfaces, Source Paths, Schema Collisions

When to use: before dispatching any integration, port, or migration task to a subagent.
Lesson: five minutes of orchestrator-side verification (signatures, source paths, table names) prevents a wasted dispatch round-trip and a context-heavy mid-execution fix cycle.

## 1. API surface reading for integration tasks

For wiring tasks (a subagent connects existing packages: a tick loop calling subsystem packages, an adapter layer between two modules, a stubbed pipeline), pre-read the exact API surfaces and embed the signatures in the `context` parameter. This applies to the INITIAL dispatch, whether or not rate limits are a concern.

Applies when:
- Wiring a simulation/event loop to existing subsystem packages
- Building an integration layer between two or more existing modules
- The subagent must match exact struct field names, function signatures, or type shapes across package boundaries
- Frozen/immutable public types are involved (wire protocols, API contracts, IPC schemas)

Technique:
1. Read every target file's types and signatures in parallel BEFORE writing the prompt (batch read_file calls - independent, concurrent).
2. Embed exact signatures, field names, and constraint notes in `context`, not just file paths.
3. Flag frozen types explicitly: "Package X types are FROZEN per <spec> - do not change field names, types, or signatures. If the API does not match what you need, ADD a thin adapter in the integration layer; do NOT modify the package."

Why: a subagent that does not know exact field names guesses them; guesses fail compile checks and burn iterations. Embedded signatures turn 10-15 exploratory reads into 0 and reduce 429 exposure on aggressive providers.

## 2. External source verification (port / cross-repo tasks)

When a plan ports logic FROM another repo or directory ("port engine.py from ~/other-project"), verify source paths exist and are readable BEFORE dispatching:

1. `ls` every cited source path (source files, data files, sample outputs).
2. If the plan does not say where the source lives, or a cited path is missing, STOP and ask the user. Do not let subagents guess or search the whole filesystem (a `find /` for a 2000-line file timed out at 60s in practice).
3. Embed absolute source paths in every relevant subagent's `context`.

A full clarification round-trip was lost in one session because the plan assumed source material at an unverified path. A 5-second `ls` before dispatch would have caught it.

## 3. Migration and schema-name collision check

Before dispatching any task that creates new DB tables or migrations, grep existing migrations for EVERY table name the plan introduces:

```sh
grep -h 'CREATE TABLE' internal/db/migrations/*.sql   # or project equivalent
```

Plans are written without knowledge of the current schema and routinely collide. Real instance: a plan specified `CREATE TABLE jobs (...)` but migration 008 had already created a `jobs` table; `CREATE TABLE IF NOT EXISTS` was a no-op against the pre-existing table, then the index creation referenced a column the old table did not have - runtime failure.

If a collision exists: decide the rename BEFORE dispatching and bake the new name into every downstream subagent's context (store SQL, model structs, handlers, routes, the migration itself). Document the deviation as a SQL comment in the migration file.

## 4. URL and asset references come from manifests only

When a task involves downloading from URLs, the subagent MUST read the manifest/file containing the verified URLs. Subagents that guess or search for URLs invent plausible-looking but non-existent ones (404s). Always pass URLs from the authoritative source file in `context`.

## 5. Dependency-graph wave analysis

When a task list has cross-task dependencies, map the graph before dispatching: independent tasks are Wave 1 (parallel, capped by the user's stated limit or `max_concurrent_children`, whichever is lower); tasks depending on Wave 1 outputs are Wave 2; continue until covered. Present the wave structure to the user before dispatching so they can confirm sequencing and catch missing dependencies.
