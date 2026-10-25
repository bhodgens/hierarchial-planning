# Executing a Leaf Branch with Subagents (field notes, 2026-08-22 branch-02 run)

Companion to `hierarchical-plan-execution` and the branch orchestrator's own
Dispatch Protocol. Records what actually happened when a 6-leaf Python
monorepo branch was executed end-to-end, for calibration.

## Timeline reality

- 5 of 6 leaf subagents hit the ~600s delegation timeout. One died mid-TDD
  (RED phase only), one died on lint nits after all tests passed, three died
  mid-implementation. Only leaf 06 completed cleanly.
- Orchestrator repaired/finished roughly half the code in-session. Total
  elapsed still far below sequential execution.
- Commits: 8b81dbe (leaf01), 509c79a (leaf02), 9fc234e (leaf03),
  393cfb9 (leaf04), 0e668aa (leaf05), e658c8a (strays), 65d3f7e + e959bdd
  (leaf06 + guard fix), 395faf7 (tracking docs).

## Dispatch context that worked

Each implementer received:
1. Leaf doc path + "read the FULL spec first" + master contracts by reference.
2. Hard rules block: no git commands; no network in tests; never run repo-wide
   formatters (`ruff format src tests` scoped only); do not break existing N
   passing tests.
3. Explicit owned-file list AND explicit forbidden-file list (`__init__.py`,
   `__main__.py`, Makefile) with the merge-time wiring expectation stated.
4. Existing test count to preserve.
5. Verification commands to run before reporting (`uv run pytest -q`,
   `uv run ruff check .`) and required report format (files created, test
   count, deviations).

## Coordination patterns

- Self-registration: each worker module registers into the shared registry at
  import from its own file; shared `__init__.py` untouched until merge.
- Fault-tolerant registration: `_try_register(name, factory)` catching
  ConfigError (missing env secret) so bare test environments can import the
  module without breaking; CLI runs fail loudly later.
- Secret mapping: source-truth auth params are generic ("api_key") but env
  vars are specific ("CONGRESS_API_KEY"); workers pass an injectable
  `secret_lookup` mapping generic→specific at FetchClient construction.
- Contract extensions two leaves need: assign ONE owner in dispatch contexts
  (the manifest "skipped" statuses key was assigned to leaf 04's run_all).

## Repair classes hit while finishing interrupted work

1. JSON-response normalization: real FetchClient.get parses JSON; test stubs
   return response-like objects. Workers must call `.json()` if callable.
2. Fixture routing drift: substring URL matchers break when the worker builds
   paths differently than the fixture author assumed — reproduce with the
   actual transport and read the recorded URLs before rewriting routes.
3. Pinned-clock run_id collisions: deterministic `now=` injection must advance
   per `run()` call or second-run idempotency tests raise duplicate-manifest.
4. Numeric rate-limit parsing: "10 req/s documented" should extract the leading
   number, not fall to the conservative default.
5. Cursor-vs-offset pagination: source-truth pagination strings are prose;
   detect style via substring ("cursor" in lowered string) not equality.
6. pyarrow empty-table take: `Table.take([])` with null-typed columns raises;
   guard sort-take with num_rows > 0 and write empty tables directly.
7. Config selector entries: top-level non-dict entries (e.g. an active-vendor
   marker string) must be skipped by config loaders, not treated as sources.
8. Self-contradictory TDD specs: if one test demands exclusion and another
   demands raise on the same fixture entry, split fixtures rather than adding
   leniency hacks to production code.

## Integration smoke without credentials

Stage committed fixtures into a temp raw-store tree matching production
layout → run the real pipeline → build the analytics DB → assert:
per-source counts >0, PK uniqueness (event_id+as_of), view rows ≤ total,
and rebuild determinism (delete DB, rebuild twice, compare content hashes).
Record "live smoke pending API key" in tracking tables; do not block COMPLETE.
