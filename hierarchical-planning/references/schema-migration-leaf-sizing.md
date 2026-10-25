# Schema-Migration and Data-Contract Leaf Sizing (2026-09-06)

Session: meept→tokscale ingest tree. Both leaves landed REVIEWED with green
suites; TWO production bugs surfaced only when the real daemon touched the
real database. The planning failure was leaf-sizing, not implementation:
the leaves' verification scope covered the happy path only, and no task in
either leaf covered the failure classes that actually bit.

## Failure 1: fresh-install tests prove nothing for migrations

The leaf put a new index inside the CREATE TABLE/CREATE INDEX script while
the new columns were added via ALTER TABLE afterward in Go. On a fresh DB
(CREATE TABLE made the columns) everything passes. On the LIVE
pre-migration DB the script runs first, the index references a column that
does not exist yet, and the entire store fails to open:
`no such column: session_id`. Every test in the suite ran against a
leaf-created database — the failure class had zero coverage by construction.

**Sizing rule for any leaf that migrates a store other people/daemons
already hold:** a migration leaf is not done when the suite is green. Its
task list must include:

1. A legacy-fixture migration test — build a DB with the OLD schema and
   real rows, open the Store, assert new columns/indexes exist and old rows
   survive with defaults. This is a distinct TDD task, not a bonus.
2. One live end-to-end verification task: restart the real service on the
   new binary, perform one real user action, read the row back
   (`sqlite3 ... "SELECT id, <new cols> FROM <table> ORDER BY id DESC
   LIMIT 3"`). Old rows prove the migration applied; the new row proves
   the wiring. Budget ~15 min wall-clock for this task in the leaf.
3. Ordering guidance in the contract: ALTER TABLE additions FIRST
   (idempotent, tolerate-duplicate-column), CREATE INDEX on new columns
   AFTER, as separate statements.

## Failure 2: store-layer pin tests cannot see wiring gaps

The contract pin test wrote rows through the store and read the projection
back — green. Production interactive turns flow through a DIFFERENT path
(agent loop → chat client) that never passed the new session-id field; only
the task path did. Every real row had an empty session_id. The pin test
exercised the one path the fixture drove, so the gap was invisible.

**Sizing rule for data-contract leaves:**

1. The contract must name the FULL write path ("a row with X appears when a
   user does Y"), enumerating handler → loop → client → store, and include
   a task that greps the production caller chain to confirm the field
   survives every hop — especially the default/interactive path no test
   fixture drives.
2. Fixtures must cover every optional-field shape: ≥2 models, ≥2 sessions,
   ≥1 agent, ≥1 error row, ≥1 row with each nullable field EMPTY. Each
   shape gets a paired assertion (appears projected with zeros, or is
   legitimately dropped AND the count assertion accounts for it).
3. Include a count-parity assertion: seeded non-error rows == projected
   rows. Without it, rows can silently vanish and the pin still passes —
   a pin that only checks what IS present is a spot check, not a pin.
4. Zero-value semantics are contract text: 0 means "provider did not
   report," never a synthesized sentinel; error rows excluded explicitly.

Cross-reference: execution-side worked example with the exact SQL and the
live-validation recipe lives in the hierarchical-plan-execution skill,
`references/live-db-migration-and-ingest-contracts.md`. Both skills' rules
were derived from the same session; if you are EXECUTING a tree with such a
leaf, read that one; if AUTHORING, this file plus the sizing rules above
are what to fold into the leaf document at write time.
