# Multi-Agent Tree Contention

Patterns from concurrent plan-tree execution on a shared repo (meept
unified-theming session, 2026-08-25). Applies whenever another agent
session is committing to the same working tree while you execute a tree.

## Silent reverts of subagent work

A sibling session running `git restore` / `git checkout` can wipe files a
wave of parallel subagents just wrote. Signature: mtimes of many expected
output files cluster at the same instant (bulk revert), and predate the
subagent's completion report.

Detection:
```bash
stat --format '%y %n' <expected-output-files>
```

Response:
- Treat "done" reports as void; re-verify content on disk (`grep` for the
  marker symbol, e.g. the new function name) before accepting.
- For mechanical migrations, prefer re-running in-session with a
  deterministic script (python regex sweep with an explicit replacement map)
  over re-dispatching subagents — minutes vs hours.
- After any external-revert incident, suspect ALL prior uncommitted work,
  including your own earlier commits' siblings.

## Sibling commits sweep your files

Another session using broad staging (`git add .`, or committing while your
leaf's verified files sit unstaged) will absorb them into its commit with an
unrelated message.

Prevention:
- Stage + commit each leaf IMMEDIATELY after its review passes. Never leave
  verified work unstaged across a dispatch boundary.
- Always stage explicit paths; assume other sessions may have staged things —
  run `git diff --cached --stat | grep -v <your-paths>` before committing.

Recovery if it happens:
- Locate the absorbing commit: `git log --oneline -- <your-file>`.
- Record the mismatch in the plan tracking table ("landed in <sha> under
  unrelated message").
- Do NOT rewrite/revert the other session's history.

## Concurrent WIP breaks shared-package builds

The other session's half-landed edit in a dependency package blocks
`go build ./...` for your leaves even though your files are correct.

- Verify with narrowest-scope builds: `go build ./internal/tui/models/`.
- If the failing file is not yours: check its mtime. Progressing = wait ~2 min
  and retry. Stalled for a long time = report and route around.
- Run full-suite gates only when the dependency tree stabilizes.

## Small-file parallel dispatch for stalled leaves

Two full-leaf dispatches stalled for hours → re-split into four small
disjoint-file subagents completed in 6–22 min.

Splitting recipe:
1. Orchestrator commits the shared bridge/helper FIRST (foundation for all
   agents; also survives sibling reverts better).
2. Each agent gets: exact file list, exact replacement map (hex→role etc.),
   "touch NOTHING else", "do not run the shared package's test suite".
3. Exemption convention agreed up front (`// palette-exempt` style comments)
   so the lint/guard test passes without judgment calls.
4. Orchestrator writes the guard/lint test itself while agents run.

## Poll liveness, not just presence

Long sleep-poll loops on background subagents waste hours when agents died
quietly. Before each extended wait:
- `ps aux | grep <agent-process>` — is it alive?
- Check mtime of files the agent should be writing. No movement in >30 min =
  dead; take over in-session.
- User preference confirmed this session: give agents the time they need,
  BUT verify liveness first — waiting on dead agents is not patience.

## Transient mid-write parse errors in siblings' files

A sibling writing a file incrementally means your `go build ./...` can land
on a half-written snapshot: parse errors in a file you never touched
(`expected operand, found 'if'`, `expected '('`). This is a snapshot of
work-in-progress, not corruption.

- Confirm ownership first: the failing file is not in your leaf's file list
  → not yours to fix. NEVER "repair" a sibling's mid-write file; you'll
  clobber their in-flight buffer.
- Wait briefly (15–30 s) and retry the build. A progressing sibling resolves
  it themselves. Stalled >2 min with identical errors → route around
  (build/test only your packages).
- Don't conclude anything from a single failing full build in a contended
  tree; treat it as "retry after a beat", not "the tree is broken".

## Hardcoded-count tests vs. growing shared registries

When your leaf adds an entry to a shared registry (map of providers, handler
tables, plugin lists) that a sibling's leaf is ALSO extending in the same
wave, pre-existing tests asserting exact registry size (`len(providers) != 3`)
will fail through no bug in either change.

- Before adding the entry, grep the package's tests for `len(<Registry>)`,
  `expected N providers`, and similar count assertions; budget the test
  update as part of your leaf.
- After editing, count the registry's actual keys (`grep -c '": {'` on the
  map literal) — a sibling's entry may already be present, so the expected
  count may be N+2, not N+1. Update the assertion to the real number AND
  add a presence check for your own key (`seen["my-provider"]`).
- Presence-style assertions (`seen[...]`) age better than counts; prefer
  them when writing new tests against shared registries.
- Meept-specific walk-through of this exact case (xai-oauth leaf):
  `meept-design/references/oauth-provider-registry.md`.

## Attribute every failing test to an owner before touching it

In a contended tree the full-suite run will contain failures that are not
yours. Fix protocol:
1. Run your own tests by name first: `go test ./pkg/ -run 'TestMine|...' -v`.
   All green → your leaf is done; remaining failures are siblings'.
2. For each remaining failure, grep the failing test file for your symbols
   (your provider ID, your function names). Zero hits → sibling-owned; do
   not edit their test.
3. Report sibling-owned failures as such with evidence (file, symbol, error)
   instead of silently absorbing or "fixing" them — the orchestrator
  reconciles them when the sibling's leaf lands.

## Sequence leaf work: brand-new files before shared-file patches

When a leaf mixes new files (new flow module, new tests) with patches to
shared files (registry map, CLI switch), write the NEW files first and
leave shared-file patches for last:

- New files cannot conflict with siblings — they land clean and stay
  valid even if every later patch needs re-reading.
- Shared files drift while siblings work; every patch against them is a
  re-read + re-anchor. Doing patches last minimizes the window.
- Test the new files in isolation (`go test ./pkg/ -run 'MyTests'`)
  before touching shared state, so you enter the contended phase with a
  known-green core.

## Recovering from patch conflicts on sibling-drifted files

A fuzzy patch against a shared file fails with "Found 2 matches" (or
unique-match failure) when a sibling's concurrently-landed edit added a
second instance of your anchor text — e.g. two leafs both appending
registry entries after the same `},` boundary. Recovery that worked
(verify: all tests green after):

1. DON'T switch to write_file/overwrite — that discards the sibling's
   landed changes wholesale.
2. Re-read the file's current state (grep for your anchor, view the
   region) to see what the sibling added.
3. Re-apply the patch with anchor context that includes the sibling's
   landed content (e.g. anchor on THEIR new entry's tail instead of the
   old boundary).
4. Expect the patch tool's "_warning: modified by sibling subagent"
   on shared files; it's advisory — the re-read in step 2 satisfies it.

Sibling placeholder cases (e.g. a `case FlowX: return errors.New("not
yet implemented")` another agent left in a shared switch) are ideal
anchors: replacing a placeholder is disjoint from the sibling's real
work and semantically exactly your leaf's job.

## Scope gofmt/lint checks to files you touched

`gofmt -l <dir>` in a contended tree lists many sibling WIP files; chasing
them wastes time and risks reformatting a sibling's in-flight buffer. Check
only your leaf's explicit file list: `gofmt -l file1 file2 ...`. Same for
any lint gate that takes directories. (Also: `gofmt` alignment of struct
literal keys depends on the longest key in the block — adding a longer key
like `ClientIDDefault` to a block re-aligns every sibling line; run gofmt
on the file right after such an edit, before build gates.)

## Parallel leaves editing the same shared file — commit separation

When parallel leaves of the SAME tree both extend one file (two Go leaves both
adding hunks to `resolver.go`), you cannot `git add <file>` for leaf A without
sweeping leaf B's in-progress hunks into A's commit. Worked options
(tree 32, 2026-08-26):

- **Delay the shared-file commit** until all sibling leaves land, then commit
  the whole file once with a combined message. New-file packages
  (`internal/household/`) can still commit early — they carry no sibling hunks.
- `git add -p` hunk-splitting works but is fragile under streaming; prefer the
  delay unless the file is huge.
- Sibling "failures" reported in summaries may be cross-agent test races (the
  suite ran while another leaf mid-edited the shared file). Re-run the failing
  suite yourself before believing the failure — in tree 32, leaf 01 reported
  leaf 02/03 tests as failing; all passed when re-run after their agents settled.
- A timed-out/failed-status subagent may still have FINISHED its work on disk.
  Check `git status` + run its target suite before re-dispatching — three leaves
  across tree 32 and plans-combat-audit were complete despite timeout status.

## The Docker daemon and host ports are shared machine state

A sibling session brought up its full dev stack (postgres, minio, clickhouse
— "Up 28 seconds") WHILE this session ran a Docker-based spike on the same
machine (hyperswitch Phase 0 gate, 2026-08-25). Two rules kept both alive:

- **Never touch the shared daemon to fix your own problem.** No
  `docker system prune`, no daemon restart, no stopping "stale-looking"
  sibling containers — a stale-looking stack is often a parallel session's
  live work mid-bring-up. Your only levers: your own project's
  `docker compose down`, remapping YOUR host ports, or a different
  machine/context.
- **Audit host ports before any local bring-up.** Cross-session port
  collisions are near-certain on a busy dev box (sibling stack claims
  9000/9001 and 5432; user processes claim 8080). Attribute each binding
  with `lsof -nP -iTCP:<p> -sTCP:LISTEN` + `docker ps`, then remap yours
  via a `docker-compose.override.yml` using `ports: !override` (the tag
  REPLACES the base list — without it lists merge and the old binding stays
  claimed; LSP flags `!override` as unknown YAML, false positive —
  `docker compose config` is the authority). Also patch browser-facing URLs
  in the app config (dashboard `api_url`, `[user] base_url`) to the remapped
  ports — container-internal service URLs (`host = "pg"`) must NOT change.
  Concrete worked example (Hyperswitch quickstart, ports 28080/29000/25432):
  `payments/hyperswitch-payment-router/references/local-docker-bringup.md`.
  If the daemon itself is down on macOS: `open -a Docker` can "succeed"
  without the daemon ever starting — launch
  `"/Applications/Docker.app/Contents/MacOS/Docker Desktop.app/Contents/MacOS/Docker Desktop" --unattended`
  in a background terminal session and poll `docker info`.


