# E2E-Script Leaf Bugs — First-Live-Run Iteration Pattern

A plan-tree leaf that authors an e2e script exercising a live scratch
daemon for the first time will iterate — expect 2-4 script bugs and
several fix-rerun cycles before green. Observed 2026-09-04
(chat-dispatch-ux leaf 10: six runs, three script bugs, plus
sibling-session transient build breaks that masqueraded as leaf bugs).

## Recurring bug classes (dispatch context should warn about these)

1. **`set -u` unbound variable crashing a branch that reports SKIP.**
   A crash inside the warmup/turn path fell into the SKIP handler,
   converting a script bug into a false "provider unavailable." Rule:
   initialize every variable the heredoc python reads BEFORE the branch;
   SKIP must fire only on the named environmental condition, never on a
   nonzero rc from the script's own machinery.

2. **Scratch config missing a flag the real config has.** The minimal
   temp `meept.json5` omitted `multiagent.enabled: true` — the AgentRegistry
   is constructed only under that flag (components.go), so the roster was
   empty and every turn failed "no agent available for chat." When porting
   a config, diff against the repo template `config/meept.json5` and carry
   over every flag the exercised path reads.

3. **Discovery steps for rows the daemon never creates.** The script
   queried `session list --json` for a session row, but the daemon keys
   chat on bare conversation IDs lazily — no row is ever created. Querying
   for rows that "should" exist is wrong; use the actual identifier the
   flow uses. Also: list order is `last_activity DESC` — never
   break-on-first-match when picking "the session just created"; take the
   LAST match.

## Diagnosis technique — the scratch workdir is forensic evidence

`--keep` preserves the workdir: `daemon.log`, `state/sessions.db`,
`state/audit.db`, `replies/*.txt|err`. Before editing the script:

- grep `daemon.log` for the dispatch path ("Dispatched request",
  "Sync dispatch", "no agent available") — shows which branch actually
  ran;
- sqlite the DBs to verify what the daemon actually persisted
  (e.g. `SELECT id,name FROM sessions` proved a discovery step could
  never succeed);
- read `replies/*.err` — CLI error text often names the failing RPC.

## Correct behaviors to preserve (do not "fix" these away)

- FATAL on broken build — never run the suite against a stale binary
  (sibling-session WIP breaks `go build` transiently; wait/retry, or run
  the script again once HEAD is green).
- SKIP with printed reason + exit 0 is correct for provider-unreachable
  turns — but it must be the PROVIDER that is unreachable, not the
  script crashing. Grep SKIP reasons for rc values and empty reasons;
  route infrastructure failures to FAIL.
- `bash -n` before every rerun; never weaken an assertion to make a run
  pass.

## Sibling-session interference is expected, not a leaf bug

Parallel sessions commit continuously: transient undefined-symbol errors
(a call site committed, its helper still WIP in another file), go.sum
conflict markers from stash dances, mid-edit syntax errors. The script
correctly FATALs. Re-check `git log`/`git build` and rerun — do not
re-dispatch the leaf or touch foreign hunks.
