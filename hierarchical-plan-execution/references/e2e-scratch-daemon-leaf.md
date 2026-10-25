# E2E Scratch-Daemon Leaves — Live-Run Lessons

Worked example: meept `scripts/e2e-naive-user-chat.sh` (chat-dispatch-ux
leaf 10, 2026-09-04) — a naive-user transcript replayed against a fully
sandboxed daemon (temp state dir/socket/probed port, fresh-built binaries).
Also the session-continuity tree's A5 verification runs.

## Budget for first-live-exercise iteration

An e2e leaf exercising a live daemon for the first time typically hits
3-6 script bugs across 4-8 runs before the suite is trustworthy. Budget
for it and treat each failure as a leaf bug (fix the script), an
environment gate (honest SKIP), or an integration finding (STOP and
report). Observed first-exercise bugs: unbound var under `set -u`
misreported as a provider SKIP; missing config gate; wrong
session-discovery assumption; macOS symlink path mismatch.

## macOS /var → /private/var: dual-path allow patterns

`mktemp -d` under $TMPDIR yields `/var/folders/...`, but the resolved
path is `/private/var/folders/...`. Security allow-path patterns matched
against EvalSymlinks'd file paths will DENY writes under the unresolved
form. Fix: compute `WORK_RESOLVED="$(cd "$WORK" && pwd -P)"` and allow
BOTH `"$WORK/**"` and `"$WORK_RESOLVED/**"`. Symptom: `access denied:
/private/var/...` on file_write while the config lists `/var/...`.

## Null-list JSON endpoints

List endpoints may return `{"key": null}` when empty. In embedded
python parsers use `data.get("sessions") or []` — a bare `for x in
data["sessions"]` crashes with TypeError and (under `set -e` pipelines)
misclassifies an infrastructure step as a provider failure.

## Feature gates create rosters

Registries/rosters often exist only behind config flags (meept:
`multiagent.enabled` gates AgentRegistry construction). Symptom:
`no agent available for "<agent>"` with `specs=0` in the daemon log.
That is a missing config gate in the scratch config, not a broken
daemon. Seed the scratch config from the repo template's gate settings.

## Lazy conversation IDs

Chat RPCs may accept bare conversation IDs lazily — the exchange
processes fine but NO session row is ever created. A
"list sessions then discover the id" step then finds nothing.
Forensics: sqlite the scratch sessions.db; if 0 rows but the log shows
`Processing chat message conversation=<bare-id>`, reuse the bare ID
directly instead of discovering.

## Canned replies = a gate ABOVE the agent

When a turn returns a template/clarification reply ("could you clarify
which file?") despite restored history, check for short-circuit gates
in the ROUTING pipeline above the agent before blaming the agent or the
restore path. Real case: dispatcher's intent-analyzer ambiguity gate
(`IsAmbiguous` → `buildClarificationResult`) returned canned text
without ever invoking the chat agent, so restored history was never
consulted. Distinguish with forensics, not guesses.

## Sqlite forensics before blaming code under test

Scratch daemons keep their DBs (`--keep` the workdir). To split
"plumbing failed" from "gate intercepted": query the scratch DB
(`sqlite3 "$WD/state/sessions.db" "SELECT ..."`). Real case: all four
task-path exchanges WERE mirrored into session_messages (leaves 01/02
hold); the interception happened downstream. This converted a vague
"continuity is flaky" into a one-line root cause with file:line.

## Guard escape hatches must not bypass unambiguous markers

Heuristic pass-through bars (e.g. "prose ratio > 40% → it's prose, let
it through") can be defeated by wrapping a dump in enough preamble
prose — observed as a FLAKY roster leak across e2e runs. Rule: if a
marker is unambiguous (`## Available Agents` appears in no legitimate
reply), it triggers unconditionally; escape hatches apply only to
headerless/ambiguous shapes.

## STOP-clause integrity

When a tightened assertion fails, verify upstream leaves forensically
before concluding they broke. If the upstream leaves hold, invoke the
leaf's STOP clause: commit the tightened assertion (it now documents
the real gap), write the root cause into the tracking table, and queue
the blocker as a follow-up design decision. Never weaken the assertion
to get green.

## Reliability gates

An assertion that was ever flaky needs TWO consecutive provider-
available green runs before claiming fixed. Provider-unavailable turns
are honest SKIPs with printed reasons and do NOT satisfy the gate —
wait for a window and re-run.

## One gate fixed reveals the next — stack the root causes

A single user-visible failure ("continuity is flaky") can have THREE
stacked independent root causes. The 2026-09-04/05 campaign fixed them
across three trees in sequence:

1. **Reply honesty** (chat-dispatch-ux): sync replies carried
   `Task <id> completed.` stubs; errored steps were auto-approved.
   Fixed: waitForTaskCompletion returns the terminal step's Result;
   ReviewStep gates on stepHasError before policy paths; failed steps
   fail the task with the error text in the payload.
2. **History write/restore gap** (session-continuity): task-path turns
   never wrote the session conversation (only the task-scoped step
   conversation), and persistence was write-only — persistExchange
   saved to DB but nothing restored from it. Fixed: task-path mirror +
   GetOrRestore wiring.
3. **Context-blind routing gate** (session-aware-intent-gate): the
   intent-analyzer judged messages in isolation. Fixed: a
   SessionContextDigest (most-recent task + terminal step result + last
   intent) is built per turn and passed to the analyzer; two
   context-conditioned rules in the prompt; contextless turns
   byte-identical (wire-proven).

Rule: when an e2e assertion fails after your fix lands, re-derive the
causal chain from scratch — the failure may now have a DIFFERENT cause
than the one you fixed. Run-to-run failure VARIETY (different
assertions failing each run) is the signature of a fixed root cause
with noisy dependencies, not of a broken fix.

## Residual-quality follow-ups are findings, not failures

After the mechanism is proven, remaining e2e failures often trace to
reply QUALITY (artifact path buried in evidence-JSON summary fields,
task_get-with-empty-args erroring then cycle-aborting, raw result
envelopes quoted as prose). These are legitimate follow-up leaves —
log them ordered in the tracking table with the reproduction run, and
close the tree honestly rather than expanding scope mid-verify.
