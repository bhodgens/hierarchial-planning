# Llive e2e leaves and gate attribution
When to use: live e2e leaves + gate attribution.
Lesson: patterns from chat-dispatch-ux leaf 10.

# Live-E2E Plan Leaves + Integration-Gate Lint Attribution

Two patterns from executing the meept chat-dispatch-ux tree (2026-09-04,
leaf 10 e2e + integration gates) that generalize to any plan tree whose
final leaf boots a live service, and to integration gates in repos with
concurrent sessions.

## Pattern 1: Live-E2E leaves — expect 3-5 script-iteration bugs

A leaf that boots a live daemon and replays a transcript WILL iterate.
Budget 2 orchestrator review rounds. Bugs found in one real run (all
fixed in-session, none were assertion-weakening):

1. **`set -u` unbound variables masquerade as provider failures.** A
   crash inside a `$(...)` capture returned rc=1 and the script
   classified it as "no provider reply → SKIP". Fix: initialize every
   variable before first use under `set -u`; classify crashes (python
   traceback / unbound) as FATAL, not SKIP.
2. **Feature flags the minimal config omits.** The daemon's agent
   roster only registers under `multiagent.enabled: true` — without it
   every turn fails `no agent available for "chat"`, which looks like a
   provider problem but isn't. Diff the scratch config against the
   user's real config for behavior-gating flags.
3. **Session-ID discovery vs bare conversation IDs.** The daemon accepts
   a bare conversation_id on chat and processes it lazily WITHOUT
   creating a session row — so "create session, then discover its ID
   via session list" can find nothing. Either create the session
   explicitly and use its real ID, or use the conversation ID directly
   end-to-end. Check which one the code path actually keys on before
   writing discovery logic.
4. **macOS /var → /private/var symlink defeats single-form allow-path
   globs.** `mktemp -d` under $TMPDIR gives /var/folders/...; the
   security layer resolves write targets to /private/var/folders/...
   and the allow pattern `/var/.../**` no longer matches. Fix: compute
   both forms and allow both:
   `WORK_RESOLVED="$(cd "$WORK" && pwd -P)"` +
   `"allowed_paths": ["$WORK/**", "$WORK_RESOLVED/**"]`.

Non-negotiable script properties (they saved the run):
- **FATAL on broken build** — never run a stale binary; a concurrent
  session's syntax error must stop the e2e, not produce garbage.
- **Honest SKIP with printed reason** — provider-unreachable turns are
  SKIP + reason + exit 0, never silent; a SKIP must never be reachable
  from a script bug.
- **FATAL/STOP when an assertion that should now pass still fails** —
  that is an integration bug report, not an assertion to weaken.

## Pattern 2: Attribution of lint findings at integration gates

In a repo with concurrent sessions, `make lint-ci` at the integration
gate WILL fail on findings that are not yours. Before fixing or
reporting:

1. For each finding, attribute it: `git log --format='%h %s' -1 -L
   <line>,<line>:<file>` — the commit that last touched the line owns
   the finding.
2. Findings owned by commits outside your tree = sibling debt. Record
   them (file:line + owning commit) and move on; do NOT fix other
   sessions' lint mid-tree (their WIP may be mid-flight).
3. Only findings on lines your tree's commits introduced are your
   blockers.
4. State the attribution method in the completion report so the next
   reader trusts (or re-verifies) the triage.

Worked example: `handler.go:652` → sibling commit c6dd6ce7;
`tactical.go:551` → 1a5cea06; `components.go:3313+` → 9b0c647b. Zero
findings on chat-dispatch-ux's own lines; the repo-wide counts
(modernize 50, staticcheck 45) were pre-existing debt.

## Related

- Guard escape-hatch bypasses need a regression case: any heuristic
  with a pass-through branch (e.g. a prose-ratio escape hatch on a
  catalog guard) WILL eventually be bypassed by model output wrapped in
  enough legitimate-looking prose. When a flaky leak is observed,
  tighten to an absolute trigger for unambiguous markers and add the
  bypass as a named regression test case (meept commit 26f276fd).
