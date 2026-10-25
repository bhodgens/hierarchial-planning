# Chat-Harness UX Comparison Recipe — naive-user transcript vs a reference harness (2026-09-04, meept vs hermes)

Live-service QA for a chat-harness product: roleplay a NON-TECHNICAL user,
drive the SAME transcript through your product and a reference harness on
the SAME model, and audit where your product's replies stop being
user-shaped. The findings root-cause into the dispatch pipeline, not the
model — the comparison isolates the harness as the variable.

## Method

1. **Same model both sides.** Meept's default chat model lives in
   ~/.meept/models.json5 (`model` key; agnes/agnes-2.5-flash). Hermes'
   custom_providers in config.yaml already had the same Agnes endpoint —
   pin with `-m agnes-2.5-flash --provider Agnes-AI`. Verify before
   claiming a fair comparison; if no shared provider exists, the
   comparison is directional, not evidentiary.
2. **Sandbox everything.** `--cwd /tmp/<dir>` (meept) vs a /tmp workdir
   (hermes). Check the sandbox after every turn — "the file was never
   created" is the sharpest finding you can produce. Never let a
   harness-under-test write into its own repo (meept's step jobs resolved
   relative paths against the daemon cwd and wrote INTO the meept repo —
   that failure is invisible without an ls).
3. **Transcript shape** (each turn = one bounded user ask):
   T1 build ("remind me to drink water every 30 min")
   T2 modify ("too quiet — add sound, pop up a window")
   T3 status ("did the change get made? where is the file?")
   T4 artifact inventory ("what files did you make and what does each do?")
   Plus: an undo pair (install a service → remove it) exercising
   destructive-action hygiene, and a liveness probe ("say yes if you can
   hear me") after any suspicious turn.
4. **Re-run T1 3x.** Variation across identical prompts is itself a
   finding: meept returned a 75-tool catalog, a "Task ... completed."
   stub, and a 28-agent roster (with system-prompt bodies) for the SAME
   prompt across three runs.
5. **Evidence beyond the transcript:**
   - `sqlite3 ~/.meept/sessions.db` session_messages shows what the model
     ACTUALLY stored vs what the CLI printed (CLI printed stubs; DB held
     both stubs AND honest "I cannot save files" messages).
   - `~/.meept/meept.log` gives the dispatch chain: "Skipping review —
     step has execution error" followed by "Step approved" is the smoking
     gun for completion lies.
   - Raw oneshot output to a file (`> /tmp/run1.txt 2>&1`) — the same
     command re-run prints different things; you need the receipts.

## Assertion contract (what the product harness must satisfy)

- Replies are user-shaped prose: no `^Task .* completed\.$` stubs, no raw
  platform_* JSON dumps, no agent rosters, no tool catalogs.
- Claims match disk: "completed" implies the artifact exists in the
  session cwd (never the daemon cwd).
- Failures state the harness cause ("provider rate-limited until HH:MM"),
  never "my tools aren't working" (a 429 quota error surfaced as
  self-harm; the user nearly pasted code manually).
- Status turns reference prior artifacts (continuity survives the
  orchestrator's stub-ification).
- Destructive actions ask first; undo is complete (plist unloaded AND
  deleted; launchctl list confirms).

## Findings → fix tree pattern

Every transcript failure maps to a pipeline defect with a file:line root
cause (grep the log line → find the producer → read the code). The
2026-09-04 wave's map, executed as docs/plans/chat-dispatch-ux/ (10
leaves, all landed same-day): sync-wait stub discarded the specialist's
summary (waitForTaskCompletion returned a format string — fix: return
bestStepResult from the step store); errored steps auto-approved (review
skip path returned ReviewApproved — fix: error gate hoisted ABOVE the
policy paths, red-phase proved the contract was unsatisfiable at the
literal anchor; task with failed steps finalizes StateFailed via a new
allStepsTerminalWithFailures, since AreAllCompleted is success-only and
left failed tasks hanging forever); step jobs resolved cwd against daemon
cwd (fix: resolveStepWorkingDir falls back to Session.DetectionContext.CWD
— NOT a top-level session CWD field, the master's anchor was imprecise);
task-scoped loops missed the indexed-schema config (full 75-tool catalog
burned 49k/50k context — fix: registry SetSchemaModeConfig applied to the
shared PARENT tool registry, because FilteredToolRegistry delegates
GetDefinitions and has no SetSchemaMode of its own; wired at registry
construction, NOT the primary-loop site where the registry field is still
nil); no reply guard for machine-shaped output (fix: sanitizeCatalogReply
with a LINE-SHAPE prose-ratio — the spec's char-count version failed its
own test cases); quota escapes unclassified (fix: publish the EXISTING
agent.quota_wait + wrap the error so the tactical failure path stores the
quota sentence as the step Result — Task 2 then needed zero code);
skill discovery matched go-linter-save-hook-revert (0.72) to a
water-reminder ask (fix: domainAgrees gate reusing the shared stopword
list via a new accessor); the Claude skill parser rejected comma-separated
`allowed-tools:` scalars (12,760 identical WARNs/day — fix: stringList
UnmarshalYAML + warning dedupe WARN-once-per-path); an orphan bus topic
unannotated in the generated connectivity graph (annotated_orphans +
regen).

### Authoring lessons from this tree (for the planning skill's authors)

- **Anchors rot in hours, not weeks.** Roughly a third of the leaf
  anchors were wrong by execution: line drift (siblings committing), a
  field that lives at DetectionContext.CWD not session.CWD, a nil
  receiver at the documented wiring site, and a review-skip block that
  was unreachable from the documented entry point. Every one was caught
  by the implementer's TDD red phase or fixed by re-grepping HEAD — the
  dispatch-context practice of inlining VERIFIED anchor snippets plus
  "re-verify before trusting" beats pretending anchors are stable.
- **Let the red phase overrule the plan.** Two leaves (02, 05) proved
  their spec's literal mechanism couldn't satisfy the spec's own
  contract and implemented the minimal correct alternative (gate hoist,
  line-shape ratio) with the deviation documented. This is the system
  working: plans carry intent + contracts; implementers own mechanism.
- **E2E leaves iterate; budget for it.** Leaf 10 needed 8 runs to green:
  three harness bugs of its own (unbound var under `set -u` reading as a
  provider SKIP; missing `multiagent.enabled` config gate; session-list
  selection hitting a stale row), plus sibling-session build breaks that
  FATALed correctly. An e2e leaf is a debugging session, not a
  transcription exercise — don't treat its first FAIL as a broken fix.
- **A5 continuity held as a known-thin even after the tree landed**: the
  final live run passed 16/17; cross-turn artifact memory after a
  sync-dispatched task stayed lossy (status turns came back as
  clarification requests). Record such residuals as follow-up leaf
  candidates in the completion report instead of weakening the assertion
  to force green — the assertion IS the regression net for the follow-up.
- **A5 follow-up tree executed (session-continuity, same day)**: two
  real plumbing defects landed — task-path turns never mirrored the
  exchange into the session conversation (fix: recordOnTaskPath-gated
  recorder, direct path excluded since RunOnce already records), and
  persistence was write-only (fix: RunOnceWithParts acquires via
  ConversationStore.GetOrRestore with a DB-reading restoreFn; watch
  GetMessages(id,0,0)=ZERO rows in both production stores — fetch
  MaxInt32 then tail-cap in memory; per-session loop CLONES must inherit
  the wiring or the switch is dead in production). Remaining blocker
  after both: a PRE-EXISTING routing gate above the agent — the
  intent-analyzer ambiguity short-circuit (dispatcher.go:667) returns
  canned clarifications for status-shaped turns before restored history
  is ever consulted. Diagnostic leaf pattern: sqlite-forensics proved
  leaves 01/02 held (all exchanges mirrored), attributing the residual
  failure to the gate with file:line; the gate adjustment is a design
  decision (skip/lower-threshold/feed-history) owned by the user.
- **Full outcome of the wave** (for anyone re-running the comparison):
  10/10 leaves landed same-session as commits 39884594, b3eb4878,
  892efbe3, aca55f78, 845f9efa, 93a11911, c3b334cd, b5c0fd1e, 6ad221a0,
  95aa327a (+ graphs regen b6f3f1bf, AGENTS.md invariant block
  f445b8f6). Integration gates: suites + custom analyzers green;
  lint-ci findings attributed via `git log -L` to sibling/pre-tree
  commits (see integration-gate-lint-attribution.md).

## Reference-harness behaviors worth copying (hermes, same model)

Every turn ends with what-was-done + how-to-run + one next step; asked
before installing a launchd service; removed it cleanly and verified;
"which file does what" summary table; session title + resume command
after EVERY turn; tool calls visible but compact during the turn, final
message = distilled answer. (Cosmetic flaw noted: MCP asyncio "Event loop
is closed" traceback at exit — report-only.)

## Layered blocker chains: fix one layer, the next becomes visible

The A5 gap needed THREE sequential trees/leaves, each revealing the next
blocker only after the previous layer stopped failing first:

1. chat-dispatch-ux (10 leaves): reply honesty, cwd, guard, quota — but
   A5 still failed.
2. session-continuity (2 leaves): task-path exchange mirroring + DB
   restore — sqlite forensics proved both held; A5 STILL failed.
3. Root cause moved UP the stack: the intent-analyzer ambiguity gate
   (dispatcher.go:667) judged raw messages in isolation and
   short-circuited status-shaped follow-ups before any agent ran.

Diagnostic pattern that cracked it: reproduce the digest SQL by hand
against the scratch DB (did the precondition land?), grep daemon.log for
the analyzer's verdict at the failing turn, check WHICH model served it
(classifier alias rotations: LFM2.5-8B "empty content", glm-4.5-air 429).
A fully concrete T1 instruction also scored ambiguity=0.8 in that window
— proving model degradation, not wording, was the variable. And a later
healthy-provider run showed the gate NOT firing (intent=report routed
straight to chat) — the ambiguity fix worked; the residual A5 fail moved
to an unrelated pre-existing `task_get` empty-args → cycle-detector bug.

Lesson: in layered systems, an assertion can fail for a DIFFERENT reason
after each fix. Re-diagnose from scratch each time instead of assuming
the original cause persisted; capture each layer's fix as its own
commit/leaf so the archaeology is preserved.

## Design-decision gates owned by the user

When the remaining blocker requires a DESIGN choice (not a mechanism
fix) — e.g. "should the ambiguity gate skip, lower threshold, or receive
history?" — present the options with a recommendation and STOP. A5's fix
was option-3-shaped: pass a SessionContextDigest (last task
name/state/agent, terminal step result summary, last intent) into
AnalyzeTrueIntent; non-empty digest appends a `[Recent session activity]`
block and two context-conditioned rules ("resolve pronouns against
recent activity"; "short follow-up about clear recent activity → LOW
ambiguity"); contextless turns byte-identical; threshold unchanged; no
keyword lists; no config. User's architectural principle that decided it:
user-addressed agents QUERY session state at turn time; the session
never passively absorbs worker transcripts; only final user-facing
summaries mirror into the session conversation.

## Third wave executed: classifier-observability (2026-09-06)

The gate fix landed (digest + rules in AnalyzeTrueIntent) but the A5
campaign ran 13 e2e attempts without two certified green runs, and the
run-10 forensics subagent OVERTURNED the orchestrator's attribution:
zero 429s in the log. Real failures: (a) "empty content" from local
fallback models rotating the SHARED classifier client onto weak weights,
which then misrouted a concrete create-file request as intent=platform
confidence=1.0 (reply = capabilities dump); (b) successful analyzer
verdicts (ambiguity 0.6-0.9) from those weak models — misjudgments, not
errors. Run 11 (best run) proved the chain end-to-end: gate did NOT
fire, the agent answered from restored history, T4 named the exact file
path — but T3 failed the script's `?`-heuristic because the answer both
answered AND offered follow-up help.

Landed fixes (user-selected from an ideation set, on the "fallbacks hide
problems" insight): #1 provenance on replies (Intent.Model +
ChatResponse.Meta: method/model/ambiguity/digest-used; servedModel
tracked in BOTH analyzer and LLM classifier because one rotation
silently re-points both); #2 classifier_fail_fast config (default off —
primary failure fails honestly, no rotation, for honest testing); #5
digest gains WorkingDirectory (WorktreePath > ProjectPath >
DetectionContext.CWD, matching resolveStepWorkingDir; IsEmpty
unchanged — cwd is enrichment, not activity).

Follow-up stack surfaced by forensics (user-owned prioritization):
suspicious-success cross-check (platform/1.0 on an imperative request
should trigger the keyword/heuristic cross-check — fallbacks currently
fire only on FAILURE, never on suspicious success), analyzer per-call
timeout (none today; T3 waited ~28s), alias reorder (chain was
weakest-first), client split (analyzer rotation re-pointing the router).

Assert-heuristic lesson: an A5-style "not a bare clarification" check
that fails ANY reply containing '?' will fail correct answers that end
with an offer ("want me to verify?"). When an answer demonstrably
references the artifact AND answers the question, the `?` signal alone
must not fail it — decide present/absent of the artifact reference
first, treat trailing offers as prose.
