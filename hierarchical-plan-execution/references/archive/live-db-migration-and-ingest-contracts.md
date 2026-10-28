# Llive db migration and ingest contracts
When to use: green tests, broken production.
Lesson: test migrations against legacy fixtures; contracts name the FULL write path.

# Live-DB schema migrations and ingest contracts: green tests, broken production

Session 2026-09-06, meept→tokscale ingest tree (leaves landed green, two
production bugs surfaced only when the real daemon touched the real DB).
Both failures share one root shape: **every test ran against a database the
leaf itself had just created with the new schema.**
Addendum 2026-09-08: the consumer-side re-validation pattern (reconcile
reports against live SQL ground truth before PR) is at the bottom.

## Failure 1: index-before-column migration ordering (commit 088f8214)

Leaf 01 put the new index inside the big CREATE TABLE/CREATE INDEX script:

```sql
CREATE TABLE IF NOT EXISTS llm_calls (...);          -- fresh installs: has session_id
CREATE INDEX idx_llm_calls_session_ts ON llm_calls(session_id, ...);
-- later, in Go:
ALTER TABLE llm_calls ADD COLUMN session_id TEXT NOT NULL DEFAULT '';  -- legacy DBs
```

On a fresh DB this is fine (CREATE TABLE made the column). On a live
pre-migration DB the whole script runs first, the index references a column
that does not exist yet, `initSchema` fails, and the metrics store never
opens: `Failed to create metrics store error="no such column: session_id"`.
Every leaf test passed because every test DB was fresh.

**Rule:** migration correctness must be tested against a fixture shaped like
the WORST pre-existing database, not like the new schema. For SQLite stores:

1. Put ALTER TABLE append-column statements FIRST (idempotent,
   tolerate-duplicate-column pattern), then `CREATE INDEX IF NOT EXISTS` on
   new columns as separate statements AFTER the ALTERs.
2. Add a migration test that (a) builds a legacy-shaped DB (old columns
   only, some rows), (b) opens the Store on it, (c) asserts the new columns
   and indexes exist and old rows survive with defaults.
3. In dispatch contexts: "fresh-install tests prove nothing for pre-existing
   DBs — the leaf must include an apply-to-legacy-fixture task."

## Failure 2: fixture blindness + silent degradation + wiring gap

Three stacked issues around the Contract D pin test (commit cbf0b775 fixed
the production half):

- **Fixture blindness.** All fixture rows used ONE model id. The contract's
  projection filters `WHERE model_id != ''`-adjacent conditions, so a row
  with an empty model silently vanishes — and no assertion could ever
  notice, because every row that SHOULD appear does.
- **Silent degradation.** The pin test asserted the error-row exclusion but
  had no assertion for "every seeded non-error row appears in the
  projection." A contract pin that only checks what IS present cannot see
  rows silently dropped.
- **Wiring gap.** The leaf tested the store layer (llm.go → llm_calls) but
  production interactive turns flow through agent/loop.go's RunOnceWithParts
  → chatWithFailover, which never passed session ID (chatOptions.sessionID
  was only set on the task path). Store tests green; every real row had an
  empty session_id.

**Rules for plan contracts and ingest-pinning tests:**

1. **Diverse fixtures are part of the contract.** Require ≥2 models, ≥2
   sessions, ≥1 agent, ≥1 error row, AND ≥1 row with each nullable/optional
   field empty (empty model, empty agent, empty session). Each "absent"
   variation needs a paired assertion: either it appears projected with
   zeros, or the projection legitimately drops it AND the row count
   assertion accounts for it exactly.
2. **Assert "no silent drops":** seeded non-error row count (possibly
   filtered) == projected row count, per group. A projection test without a
   count-parity assertion is not a pin, it's a spot check.
3. **Contracts must name the full write path**, not just the store layer:
   "row is written when a user does X" — enumerate the call chain
   (handler → loop → client → store) and pin the field's presence at the
   ENTRY point, not only at the DB. When a leaf's spec says "thread X
   through all record sites," require the leaf to grep the production
   caller chain and confirm the field survives every hop, including the
   default/interactive path that no test fixture exercises.
4. **Planning-side sizing rule** (mirrored in hierarchical-planning): a
   schema-migration leaf is NOT done when the suite is green. It is done
   when (a) suite green on fresh DB, (b) suite green on a legacy-fixture
   DB, (c) one live end-to-end write observed with the new fields
   populated. Budget the extra verification task into the leaf.

Live validation pattern that caught both bugs (cheap, reusable): restart the
real service on the new binary, do one real user action, then read the row
back (`sqlite3 ... "SELECT id, session_id, reasoning_tokens FROM llm_calls
ORDER BY id DESC LIMIT 3"`). Old rows prove the migration applied; the new
row proves the wiring.

## Consumer-side corollary: re-validate against the LIVE store before PR (2026-09-08)

The same shape recurs on the CONSUMING side. The tokscale parser passed all
its tests and one live spot-check at implementation time, but the user's
"re-validate" ask came days later — the live DB had grown 355 → 3,550 rows
with session-id shapes the fixtures never covered (`step-task-*`,
`plan-task-*`). The re-validation that satisfies this class of ask is
reconciliation, not re-eyeballing:

1. Compute expected values in the source DB directly with the SAME filter
   the parser applies (`SELECT COUNT(*), SUM(col)... WHERE error=0`).
2. Run the product's reports; diff numbers exactly (row count, per-bucket
   sums). 21,993,205 in the SQL must be 21,993,205 in the report.
3. Check composition, not just totals: distinct providers/models,
   agent-id distribution, and NEW id shapes — a `plan-task-*` session
   appearing correctly under `--group-by session` proves pass-through on
   real data in a way the fixture cannot.
4. Re-run the parser's unit tests after any rebase (branch code drifts
   against moved main; see the message_cache parser_version trap in
   tokscale-client-addition-checklist.md — the missing arm only compiles
   once main's newer registry arrives via rebase).

When a user asks to "re-validate that it works," treat the live store as
having MOVED since implementation day — it always has.

References to this file elsewhere in the skill say "contracts.md" — that
name is stale; this is the file (live-db-migration-and-ingest-contracts.md).
Keep this note until the stale pointers are cleaned up.
