# Recon-Baked Leaves & Orchestrator Contract Review


When to use: leaves porting or re-implementing existing code.
Lesson: bake recon into leaves before dispatch; orchestrator contract review before waves.
Lessons from F-101b wave 3 (2026-08-09): porting 11+ TS/tRPC endpoints to a Go
backend with parallel leaf agents. Applies to any plan tree whose leaves port
or re-implement existing code from a deleted/legacy reference.

## 1. Bake recon into leaves BEFORE dispatch — recon-heavy leaves blow their call cap

Observed failure: leaf 06 (compliance list-use-cases) was dispatched with
"read the TS procedure, find findActiveOnboardingCampaign, verify schema
columns, then write the handler." The agent spent all 14 tool calls on recon
(TS extraction, helper lookup, schema verification, frontend consumer check)
and returned with **zero code written**. The re-dispatch with recon baked in
(exact SQL, exact column list from the drizzle schema, exact route
registration line, auth-group verdict, response struct field names) completed
in 7 calls.

Rule: for port/recon-dependent leaves, the ORCHESTRATOR runs the exploration
at authoring time and writes the findings INTO the leaf as concrete spec:
- table + column names (verified against the schema file, not guessed)
- the exact SQL query (or a precise recipe)
- route registration line + auth group (verified against sibling routes)
- frontend call-site method/path/params (read the actual apiClient call)
- response struct field names (from the TS return block / frontend consumer)

The implementer then writes code from the recipe instead of discovering it.
A "HARD CAP: N calls" dispatch note is only safe when the leaf is write-only.

Cap scaling (observed same session): after recon-baking, the two heaviest
leaves (a ~620-line TS port and an 8-handler funding batch) still needed
**20-24 call caps** — recon-baking removes the discovery calls but the
write+verify cycle for large leaves (extract TS chunk → write handler →
schema re-check → gofmt/build/vet/test/lint) legitimately needs more than 14.
Rule: cap ≈ 14 for single-handler leaves, 20-24 for multi-handler or
600-line-TS-port leaves; if a leaf caps out with code unwritten, re-dispatch
with the recon it gathered baked into the context (the recon is the asset,
not the failure).

## 2. Orchestrator review must read the diff AND the frontend call site — never trust self-reports

Subagents report "all tasks complete, build green" while shipping contract
mismatches the compiler cannot see. Two real cases from this session:

- **GET vs POST mismatch**: TS `job.listByType` was ported as
  `GET /job/list-by-type` reading query params. The frontend actually POSTs
  `{jobType, organizationId, limit}` as a JSON body (tRPC always body-carries
  input; the ported frontend kept POST+body). A GET-only route 405s the
  caller. Fix: read the frontend call site's `method:` BEFORE writing the
  handler; register the route with the frontend's verb.
- **Rename ≠ same contract**: leaf author classified
  `/funding/providerReconciliation` as a rename to Go's
  `/phone-numbers/provider-reconciliation`. The Go endpoint is a DIFFERENT
  contract (Telnyx phone-number sync, body-based request) vs the TS procedure
  (provider_message_logs aggregation, query params, computed delta fields).
  Path existence is not contract equivalence. When contracts differ, it is a
  PORT (new handler), and the frontend caller stays on the old path until the
  real port lands.

In-session review of a port leaf = read the new handler, then grep the
frontend call site and confirm method / path / params / response fields line
up, then run gofmt + build + vet + test + lint. Include `golangci-lint run`
(staticcheck QF1001/QF1007 flags style the compiler won't). Also check the
diff for stray artifacts: subagents may leave editor backups
(`provider-reconciliation-tab.tsx.bak`, 1600 lines) or untracked files in the
worktree — `git status --short` + `git ls-files | grep '\.bak$'` after each
review, and flag tracked backups to the user as a cleanup decision (they may
predate the wave; deleting is the user's call).

## 3. Route-parity "0 missing" claims need a frontend-derived sweep

An audit re-sweep AND a delegated subagent both said "0 missing / essentially
fully ported" while 11+ endpoints with live admin callers had no Go route.
Both derived the expected list from a curated page set + a ~12-path
spot-check. The sweep that works extracts ALL apiClient paths from the
frontend (both `"..."` and backtick template literals — template-literal
callers hide from double-quote greps), normalizes `${...}` → `{id}`, diffs
against every Go route (main.go + all RegisterRoutes), and classifies each
as PORTED / RENAMED / MISSING. See `codebase-audit` skill →
`references/endpoint-port-verification.md` for the full sweep recipe.

## 4. A 503/failed final call does NOT mean the deliverable is missing — check the output file first

Observed (nextjs-api prune, 2026-08-09): the keep-list leaf reported
`API call failed after 3 retries: HTTP 503` on its LAST call — but the
deliverable (`keep-list.md`, 11KB) had been written to disk minutes earlier.
The 503 killed only the summary message, not the work.

Rule: when a delegated leaf reports a 503 / timeout / cap-exhaustion on its
final call, BEFORE re-dispatching check whether the expected output artifact
exists on disk (`ls -la <output path>` / `head <file>`). If it's there, the
leaf effectively succeeded — review the artifact in-session and proceed to the
next phase. Only re-dispatch when the artifact is genuinely missing or
incomplete. This also applies to code leaves: a 503 on the summary doesn't
undo committed-to-disk file writes; verify with `git status`/`git diff --stat`
before assuming nothing landed.
