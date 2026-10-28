# E2E Leaves — Authoring and Execution Pattern

**When to use:** A plan tree includes a leaf whose deliverable is an
Lesson: budget 3-6 post-green fix runs; e2e leaves find seams unit leaves cannot.
end-to-end script driving a live daemon/service (scratch instance, real
provider, real transcript). Worked instance: meept chat-dispatch-ux leaf 10
(2026-09-04) — scratch-daemon e2e replaying a naive-user chat transcript;
six runs to first green, every failure a script/config bug the unit-level
leaves could not have caught.

## Budgeting (authoring side)

E2E leaves consume 3-6 fix iterations AFTER all implementation leaves are
green. The script is the first thing ever to exercise the whole feature
stack against a real process, so it finds integration seams no leaf test
saw. Author the leaf with an explicit deviations ledger and tell the
orchestrator to expect multiple runs; run-count is not leaf failure.
Dispatch only after ALL code leaves are REVIEWED — an e2e run against a
moving tree produces unattributable failures.

## Failure classes observed (each cost one run)

1. **Minimal scratch config missing a construction gate.** The code path
   under test was inside `if cfg.MultiAgent.Enabled` in the daemon setup;
   the hand-written minimal config omitted it, the registry never built
   (`Agent registry initialized specs=0` in the log was the tell), and
   every turn failed `no agent available for "chat"`. Rule: grep the
   construction site for its gating conditions
   (`grep -n 'if cfg\.' <setup file> | grep -i enabled`) and set every
   gate the transcript's path needs. (Also recorded as Hazard 8.)
2. **Discovering a lazily-created conversation.** The script sent chat to
   a bare conversation ID (daemon accepts these lazily — chat keys on
   conversation_id; no session row is created), then tried to "discover"
   the session row. There is none. Either create a real session first
   (session.create / CLI `chat --project`, which goes through
   createFlaggedSession) or address the conversation ID directly and skip
   discovery.
3. **Wrong-row selection on name lookup.** The store's `List()` returns
   `ORDER BY archived ASC, last_activity DESC`; a selector that `break`s
   on the FIRST name match can return an older row and shadow the fresh
   one — downstream `project.set` then fails `session not found`. Take
   the LAST matching row (most recent), not the first, and remember the
   CLI's tabular `session list` prints a literal "No sessions found."
   under the same conditions where `--json` prints `{}`.
4. **`set -u` unbound variable masquerading as a provider skip.** An
   unset variable passed into a heredoc python argv crashed after the
   tool call was attempted; the nonzero rc was classified as a
   "provider unavailable" SKIP. Initialize every variable before first
   use, and make the SKIP path print the provider's ACTUAL error text so
   a script traceback cannot hide behind it.

## Run/debug recipe (execution side)

- Add a `--keep` flag that preserves the scratch workdir. On failure,
  debug from: `<workdir>/daemon.log` (tail; grep the feature's log
  lines), `sqlite3 <workdir>/state/*.db` (the scratch DB is the ground
  truth for what actually got created), and `replies/*.err` (cobra/CLI
  errors land on stderr there).
- `go build ./...` before each run: in a shared working tree sibling
  sessions commit continuously and a transient foreign syntax error will
  FATAL the e2e build step. That FATAL is correct (never run against a
  stale binary) — wait/retry after the tree builds; do not rewrite the
  script for a foreign breakage. Expect 1-2 such retries per wave.
- Classify honestly: infrastructure failure (daemon dead, session
  missing) = FAIL; provider-unavailable = SKIP with the printed reason.
  A SKIP whose "reason" is actually a script traceback is a leaf bug.
- Provider latency: free-tier models 429/stall; give each turn a generous
  timeout (300s) with exactly one retry, then SKIP that assertion group —
  the structural assertions (no stubs, no catalog dumps, file landed in
  the right cwd) still hold on error replies.

## Cross-references

- Scratch-config gate enumeration + SKIP classification: shared-tree-hazards
  Hazard 8.
- Working-tree-drift builds and generated docs: shared-tree-hazards
  Hazards 6-8.
- Worked assertion-contract template: chat-dispatch-ux leaf 10 doc in the
  meept repo's docs/plans/chat-dispatch-ux/ (transcript turns mapped to
  assertion IDs A1-A6 with honest SKIP semantics).
