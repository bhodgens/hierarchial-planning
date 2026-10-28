# Ppipeline composition leaf
When to use: pipeline-composition leaves.
Lesson: fixture staging, pyarrow/DuckDB pitfalls.

# Pipeline-Composition Leaf: Fixture Staging + pyarrow/DuckDB Pitfalls

> Worked example for a "compose existing modules into one pipeline + build
> artifact" leaf (curators → parquet → DuckDB). The individual modules had
> their own tests and fixtures; the composition layer is where the new
> failures appear.

## Session

- **Date:** 2026-08-22
- **Project:** agent-orange, `plans/policy-market/02-data-platform/06-curate-duckdb.md`
- **Scope:** `run_curate` composing 4 curators into unified parquet;
  deterministic DuckDB build with a point-in-time view; Makefile wiring; CLI.

## Pitfall 1: Derive composition fixtures from the module's INPUT contract, not its fixture files

Existing per-module tests stage fixtures in whatever shape is convenient
(human-facing CSVs like `Date,Open,High,Low,Close,AdjClose,...`). But the
module under composition reads the **raw store payload** — the JSON that the
*ingest* layer writes (lowercase keys: `date`, `adj_close`, `div_cash`,
`split_factor`). Feeding CSV-header-shaped rows straight in produced
`KeyError: 'date'` deep inside the curator.

**Rule:** when composing modules that already have tests, read one module
test's `raw_root` fixture builder and replicate THAT shape — the ingest
output contract — not the repo's human-readable fixture files. When the
source is a fixture file (CSV), transform headers explicitly
(`AdjClose → adj_close`) before staging.

## Pitfall 2: Empty pyarrow tables break concat/cast/take

Curators return `pa.Table.from_pylist(rows, schema)` — with zero matching
rows this is a valid **0-column** table (schema is dropped), not a
0-row table with columns. Composition code that assumes a schema
(`t.cast(schema)`, `pa.concat_tables`) then raises
`ValueError: Target schema's field names are not matching ... []`.

**Rule:** filter `[t for t in tables if t.num_columns > 0]` before
concat/cast. Also: `table.take(sorted_indices)` fails with
`ArrowNotImplementedError: array_take ... (string, null)` when any column
is null-typed; sorting via `rows = table.to_pylist(); rows.sort(key=...);
pa.Table.from_pylist(rows, schema)` is the robust path for small tables and
is also what gives byte-stable parquet for idempotency tests.

## Pitfall 3: Deterministic DuckDB rebuild test pattern

- Build = drop file + `CREATE TABLE ... AS SELECT * FROM read_parquet(...)` +
  `ALTER TABLE ... ADD PRIMARY KEY (event_id, as_of)` + `CREATE VIEW` with a
  correlated max(as_of) subquery. Never migrate; the db is disposable.
- Determinism assertion: snapshot each table/view as
  `(row_count, sha256(repr(rows ORDER BY all columns)))`, rebuild, compare.
- Uniqueness test: `pytest.raises(duckdb.ConstraintException)` on a duplicate
  INSERT — use the specific exception, not blind `Exception` (ruff B017).
- Read-only check on inputs: hash curated parquet before/after the build.

## Pitfall 4: Error-isolation tests need a payload that fails LATE

To prove one failing curator doesn't abort the others, stage a raw payload
that parses as gzip-JSON (so RawStore.write succeeds) but fails during
curation (e.g. `{"format": "xml", "body": "<not-xml"}`). A payload that
fails at write time doesn't exercise the isolation path. Assert the failing
source's name appears in `report.errors` and that the report still has rows.

## Workflow notes that went well

- Explore existing module tests (`grep def curate_`, read one test fixture
  builder per module) BEFORE writing the composition test — the whole
  fixture-staging design falls out of that.
- `uv run ruff check .` after `ruff format` caught 4 issues (unused import,
  unused var, zip strict, blind except) — run both, fix, then re-run the
  targeted tests.
- Manual smoke (inline python heredoc staging fixtures → run pipeline →
  build db → print counts) substitutes for a network integration test when
  the env has no network; note it as a deviation in the leaf report.
