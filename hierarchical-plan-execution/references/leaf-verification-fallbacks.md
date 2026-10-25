# Leaf verification fallbacks when the target environment is unavailable

Class of problem: an implementation leaf's verify step says "apply to the dev
DB / hit the dev service / run the e2e path", but that environment is down
(DB not listening, Docker daemon off, tunnel dead). The implementation is
done; only verification is blocked. What to do — and what NOT to do.

## Hard rule first

**Never create or drop scratch databases on the user's local Postgres (or
any shared instance) to verify a migration.** In one session the agent
attempted `DROP DATABASE IF EXISTS <scratch>; CREATE DATABASE <scratch>` on
localhost:5432 and the user DENIED the command. Destructive/naming ops
(CREATE/DROP DATABASE, creating objects in the `postgres` maintenance DB)
require explicit consent. If the dev DB is down, report the blocker and
verify a weaker invariant — do not escalate to inventing your own database.

## Escalation ladder (strongest first, take the strongest available)

1. **Real target**: apply with the repo's command (`pnpm db:migrate` or
   equivalent) and verify with psql against the intended dev DB.
2. **Scratch DB — only with consent**: if the user explicitly approves a
   throwaway database, build it from the baseline schema + migration under
   test, run the migration TWICE (idempotency proof).
3. **Pure parser (no DB at all)**: parse the migration with `pglast`
   (libpg_query — the actual PostgreSQL grammar) and assert the AST matches
   the leaf's contract DDL semantically. This is the default fallback; it is
   non-destructive, needs no consent, and catches far more than eyeballing.

## The pglast contract-check pattern

```bash
python3 -m venv /tmp/leaf-venv && /tmp/leaf-venv/bin/pip install -q pglast
/tmp/leaf-venv/bin/python - <<'EOF'
import pglast
from pglast import ast
tree = pglast.parse_sql(open('migration.sql').read())
# assert stmt classes, column defs, constraints per the leaf contract
EOF
```

Assert per contract: statement kinds and order (BEGIN/COMMIT wrap),
relation names, column names/types/nullability/defaults, UNIQUE key lists,
ON CONFLICT targets, and update column lists. A migration verified this way
earned a "29/29 semantic checks passed" record with zero DB access.

### pglast v8 API gotchas (cost ~6 debug iterations to learn)

- Enums live in `pglast.enums.parsenodes` (`AlterTableType`, `ConstrType`)
  and `pglast.enums.nodes` (`OnConflictAction`) — NOT `pglast.ast`.
- Parse-tree attrs are camelCase snake-mix: `col.typeName` (not
  `type_name`), `col.is_not_null` exists but is False — NOT NULL arrives as
  a `ConstrType.CONSTR_NOTNULL` constraint; PRIMARY KEY as `CONSTR_PRIMARY`
  (implies not-null).
- Default expressions: `constraint.raw_expr` — a string default is
  `raw_expr.val.sval`; a function default is the `FuncCall` itself
  (`raw_expr.funcname[-1].sval`), not wrapped.
- `IF NOT EXISTS`: `AlterTableCmd.missing_ok` for ADD COLUMN,
  `CreateStmt.if_not_exists` for CREATE TABLE.
- UNIQUE-constraint key entries are `String` nodes — use `k.sval`.
- INSERT upsert clause is `InsertStmt.onConflictClause` (not
  `onConflict`); conflict target via `occ.infer.indexElems[i].name`, update
  list via `occ.targetList`.
- `TransactionStmt.kind` vs `stmt_kind` — compare against
  `TransactionStmtKind.TRANS_STMT_BEGIN/COMMIT`.

## Verify the pattern you are copying, not just that you copied it

Session case: the leaf said "follow the exact INSERT..ON CONFLICT pattern of
`sibling seed script`". The sibling used quoted camelCase `"seedValue"` —
but the live `settings` table column is `seed_value` (snake_case) per the
baseline 0000 DDL, the Drizzle table def, AND the Go schema file. The
sibling script was latently broken; copying it verbatim would have errored.

Rule: when a leaf says "follow sibling file X's pattern", copy the
*structure* (ON CONFLICT DO UPDATE shape, idempotency approach) but verify
*identifiers* (column names, constraint names) against the canonical DDL —
the baseline migration file and/or the other first-party schema
definitions in the repo. Document the deviation in-file with a comment.

## Migration-convention discovery (split dirs)

When a leaf says "check BOTH migration dirs and follow the newer
convention": repos accumulate a legacy `migrations/` and a newer
`drizzle/` dir. Signals of the newer convention: sequentially numbered
files (`000N_descriptive_name.sql`), a `meta/_journal.json` that lists each
tag, and recent DDL dates. Two obligations when adding a handwritten
migration there:

1. Follow file shape of recent siblings (idempotent guards, `BEGIN;`/
   `COMMIT;` wrap, header comment naming the plan/audit doc).
2. **Manually append the journal entry** (`idx`, `version: "7"`, `when`,
   `tag` matching the filename without `.sql`, `breakpoints: true`) —
   drizzle-kit migrate reads the journal; an unjournaled file will not run.

Also mirror in the ORM layer: table file in `src/tables/` (snake_case
column names in the pgTable def), export in `schema.ts`, relation in
`relations.ts` (soft FK pattern for cross-DB refs — copy the nearest
existing table that shares the reference style). Verify with the package's
`tsc --noEmit` + build, and check `git status` to confirm the change set
is exactly leaf-scoped.

## Recording the outcome

When the strongest available rung is below the real target, say so
explicitly in the completion report: which rung was used, what it proved,
and that live-DB application is deferred (never imply the migration ran
against the dev DB when it didn't). Fabricated or implied-success
verification is worse than an honest "deferred".

## Hermetic test setups can mask live-path bugs — keep one live-chain test

A sandbox-tree lesson (2026-08-24): test suites that stage fake systems at
`/root/<Name>` and call `start_intro()` directly all passed while the REAL
game path was broken three ways in sequence (menu controller never emitted
the signal; PauseController held the tree paused; the director lookup used a
stale `/root` path after an autoload migration). Each fix was only found by
user playtest because every suite was hermetic.

Rule: for any user-facing flow (boot → menu → action), keep ONE end-to-end-ish
test that exercises the real chain — real menu controller class, real state
machine, real resolution paths — even if most suites stay hermetic. Assert on
observable outcomes ("signal X emitted", "state == Y"), not just that no
exception fired. When a user reports "nothing happens", grep their runtime log
for your flow's log lines FIRST: the last line that appears marks where the
chain broke (e.g. "new_game_requested" present but "start_intro" absent =
resolution bug between them). Runtime logs under
`~/Library/Application Support/Godot/app_userdata/<Game>/logs/` are the
authoritative trace.
