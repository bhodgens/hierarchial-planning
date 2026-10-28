# Plan Execution-Readiness Audits (pre-dispatch)


When to use: dispatching against a tree authored in an earlier session.
Lesson: failure-class library for pre-dispatch readiness audits plus correction mechanics.
## Overview

Before dispatching implementation agents against a plan tree authored in an
earlier session (or hours earlier the same day), run 2-3 parallel READ-ONLY
audit subagents. Plans decay: sibling sessions land commits, line numbers
drift, symbols rename, and conditional instructions left in leaves ("if X
turns out to be the parser...") are unresolved ambiguity that implementation
agents resolve badly. Auditing is cheap (one subagent each); wrong anchors
and dead seams waste implementation context budgets and cause silent
misimplementation.

## The three audits (dispatch in parallel — disjoint, read-only)

### 1. Citation-drift audit
- Input: the plan-tree files + instruction to verify EVERY file:line anchor
  against current HEAD.
- Verdict taxonomy per citation: ACCURATE / DRIFTED (old→current, symbol
  unchanged) / WRONG (symbol not found — describe what is there instead) /
  STALE-CONCEPT (renamed or removed).
- Also verify non-line claims: loop/loop-site counts, constant locations,
  "N sites" inventories, struct field names on the CONSUMING type.
- Report: summary counts + per-file table listing only drifted/wrong/stale
  entries, plus any finding that changes DESIGN (flag at top).

### 2. Ambiguity audit
- Target every conditional instruction and open "which X is real" question
  the plan left for dispatch time (e.g. "if internal/agents turns out to be
  the parser, add it there"). Grep the claimed alternatives in source,
  produce a definitive verdict with file:line evidence.
- Record the outcome as a dated decision row (DECISIONS.md D#) and rewrite
  the leaf's Context/Tasks so no conditional remains.

### 3. Architecture-seam audit
- For each tree's core mechanism, verify the mechanism EXISTS and is WIRED
  in source: does the hook/struct/interface the plan mutates actually
  influence the behavior the plan claims, AND is it invoked on a live
  production path? (meept 2026-09-01: `HookRegistry.RunPrepareNextTurn`
  existed with tests but had ZERO production callers — the plan's whole
  first tree was built on dead infrastructure. An "it has tests" signal is
  not "it runs"; grep for production call sites.)
- Also: name collisions on planned additions (a same-name,
  different-signature method on the target type = compile error — grep the
  receiver's methods first); state placed on the right granularity owner
  (per-alias struct cannot deliver cross-alias shared fate); import-cycle
  checks for cross-tree contracts, config keys declared in two places,
  states added without transition-table entries, bus topics without WS
  classification, and payload structs missing fields a downstream
  re-park/retry path reads.

## Auditor dispatch rules

- Read-only: no edits, no commits; cite file:line against current HEAD.
- Source inspection via search_files / terminal grep/cat — NEVER feed
  read_file output into reports (line-number prefix corruption).
- Report shape fixed up front (see SKILL.md Review Protocol patterns);
  truncated subagent summaries: read the saved cache file to recover the
  middle before digesting.
- Orchestrator digests in-session and applies corrections to the plan docs
  itself — never delegate doc edits to the auditors.

## Recurring failure classes (worked examples, meept 2026-09-01)

1. **Grep-recipe undercount.** "Five retry loops, locate via grep
   `for attempt := 1`" found only 4 — the fifth was
   `for attempt := range streamMaxRetries` with a DIFFERENT constant.
   Retry-loop/site inventories must grep the loop shape AND every constant
   name. Same for review checklists that grep to verify removal.
2. **Same-name, different-surface fields.** Catalog entries use
   `ContextWindow`; the per-model config struct uses `ContextLimit`. Verify
   field names on the consuming struct, not the catalog or the plan's
   memory of it. Line-hit greps also match NESTED struct fields: a grep
   for `CWD` hit `session.go:56` inside `type DetectionContext struct`,
   and the plan recorded a nonexistent top-level `Session.CWD`; the
   implementer nil-guarded `sess.DetectionContext.CWD` instead (meept
   chat-dispatch-ux leaf 03, 2026-09-04 — accepted as a deviation; the
   orchestrator recorded the corrected anchor in Review Notes).
   Audit rule: after a grep hit, read ±5 lines to confirm the OWNING
   struct before writing the anchor.
3. **Interface name vs satisfying type.** goal_loop's stub seam is the
   `Reflector` interface (satisfied by llm.Chatter) — grepping `type Chatter`
   in the consumer package finds nothing. Plans must name the DECLARED
   interface at the consumer.
4. **Two-conversion-site pipelines.** Roster AGENT.md keys parse into
   `agents.AgentMetadata` (yaml) then convert to `agent.AgentSpec` at BOTH
   `definitionToSpec` AND `mergeSpec` (registry.go). Wiring only one site
   drops the field on re-load. Any parser→spec pipeline needs both sites
   enumerated in the leaf. Known pre-existing gap: mergeSpec skips
   Verification/Gate — mirror-or-document, consciously.
5. **Conditional instructions are unresolved ambiguity.** They read as
   flexibility but force the implementation agent to make design decisions
   without authority. Close them at planning/audit time.
6. **Coordinate with CONCURRENT sibling execution, not just stale state.**
   When another session is executing the same forest right now (check
   `git log` for per-tree commit messages and `git status` for dirty
   files), re-scope audits and dispatches: already-committed leaves get
   VERIFICATION-only dispatches (correct outcome: no-op report), leaves
   touching sibling-dirty files are HELD with the conflict reason, and
   scoped test commands replace package-wide suites. Full procedure:
   hierarchical-plan-execution `references/sibling-forest-concurrent-execution.md`.

## Outcome accounting (why this pays)

Worked session: 5-tree forest, 20 docs. Citation audit: ~94 accurate /
13 drifted / 0 wrong / 3 stale-concept — all corrected in minutes, before
any implementation agent burned context chasing moved lines. Ambiguity
audit: closed a dual-parser question that would have produced a third
parsing path. Architecture audit: caught THREE blockers a compliant-looking
plan carried — (a) the first tree's entire mechanism was UNWIRED
infrastructure (`HookRegistry.RunPrepareNextTurn` had zero production
callers; only its own test invoked it), (b) a planned resolver method
collided by name+signature with an existing one (duplicate-method compile
error), (c) per-alias state could not deliver a contract that required
cross-alias shared fate (moved to the owner struct). Plus 5 risks: a
one-shot override that would serve exactly one turn of a promised budget, a
host-only cache key that over-blocks across credentials sharing a host, a
"registry the resolver reads" that does not exist at runtime, jobs with no
originating-session field to stamp, and provider identity dropped into an
untyped payload blob. Total cost: 3 read-only subagents, ~10–35 min
wall-clock, vs. a first implementation wave that would have shipped dead
infrastructure and a non-compiling contract.

## Applying audit corrections to plan docs

- Batch mechanical line-number fixes with `sed -i ''` over the affected
  plan files (plan docs, not source — safe), then grep the forest for the
  old anchors to confirm zero remain (e.g. grep for `4226\|322-359` minus
  the new values).
- Stale-CONCEPT fixes need prose edits, not just numbers: name the real
  interface/field inline with an "audit 2026-09-01" attribution so the
  next reader knows the anchor was verified, not guessed.
- Add a dated decision row to the forest's DECISIONS.md for every
  ambiguity the audit CLOSED (e.g. D16: parser is internal/agents +
  internal/agent two-half pipeline) so the leaf no longer carries a
  conditional.

## Post-completion follow-up wave (2026-09-02 addition)

The completion report's follow-up items are themselves dispatchable audit
targets. Meept llm-resilience-forest follow-ups, all closed via parallel
fenced subagents:

1. **Slow-suite root cause is often a POLICY landing between test
   authorship and test run.** Tree 02 made in-loop backoff steps real
   30s waits; pre-existing retry tests then burned them on wall clock
   (suite 308s; the 300s window failed — a timeout, not a regression).
   Fix via the test-only seam production already shipped
   (`SetFailurePolicyConfig`, unexported field so constructors cannot
   inline it): fast policy in tests, assertions unchanged, production
   defaults pinned by a defaults-untouched guard test. 308s → 14s.
2. **A seam landed without coverage invites a guard pair.** Wherever a
   follow-up wires a test seam, add (a) defaults-untouched (nil config
   resolves package defaults) and (b) propagation (injected config
   reaches the chatters) tests.
3. **Resource-bound flake fixes need dose-response.** Ephemeral-port
   exhaustion: unbounded 17 failures → -p 4 → 1 → -p 2 → 0 twice. The
   first clean run is not proof; record the ladder in the fix comment.
4. **Twin-site parser pipelines leave twin gaps.** The D16 mergeSpec
   Verification/Gate omission surfaced AFTER leaf 01 wired the new key
   through both sites — audit old fields' site coverage, not just the
   new one.

## Authoring-time recon patterns that paid (2026-09-04, chat-dispatch-ux)

The tree executed 10/10 leaves with zero wrong-anchor re-dispatches partly
because authoring-time recon went beyond reading the cited file. Patterns
worth repeating when authoring from a test/finding transcript:

1. **Grep the symptom string in the LOG, not just the code.** The
   comparison test's findings were log lines ("Skipping review — step has
   execution error", "Approaching conversation token budget"). Grepping
   those exact strings in `~/.meept/meept.log` located the emitting code
   paths directly and revealed SECOND bugs at the same sites (failed steps
   never reaching finalization; a specialist-loop context burn).
2. **Query the session DB for what the user actually saw.** The
   session_messages table is ground truth for UX findings — the log shows
   internals, the DB shows the reply transcript (stub messages, catalog
   dumps, truncated assistant text). Findings framed as "the user saw X"
   need this table as evidence, and the same session_id yields the tool
   path in between.
3. **Recon the FIX-TYPE neighbors, not just the bug site.** For the
   schema-wiring leaf, grepping `SetSchemaMode` found the primary-loop
   wiring site AND the registry schema_test asserting stub shapes — the
   leaf told the implementer to reuse that assertion style, which is why
   its tests matched the real wire shape on the first pass.
4. **Read the caller of the broken function to size the contract.** For
   waitForTaskCompletion, reading the sync-dispatch branch before
   authoring revealed the async path formats the same data differently —
   the leaf could scope to "sync branch only, async untouched" instead of
   leaving that decision to the implementer.
5. **Verify the leaf's own verify commands exist.** One leaf cited
   `go test -run Schema` against a package with no such test. Grep each
   named test/function for existence before publishing the leaf; a wrong
   verify command reads to the implementer as "skip verification."
6. **Pre-existing-behavior gates between two fixed components are their
   own finding.** When continuity leaves verifiably landed (DB rows
   correct) but the e2e still failed, the culprit was the dispatcher's
   intent-analyzer ambiguity gate short-circuiting into a canned
   clarification BEFORE the restored history reached any model
   (dispatcher.go:667 buildClarificationResult). When authoring trees
   that fix user-visible symptoms, grep the FULL request path between
   the broken surface and the component you're fixing for gates/filters
   that fire earlier — a mid-path policy is neither of your leaves' bugs
   but will read as their failure in the e2e. Surface it as a named
   design decision for the user, not something an implementation leaf
   quietly works around.
7. **Recon the pipeline's write-only seams.** `persistExchange` saved
   every exchange to session_messages but nothing loaded them back
   (ConversationStore.GetOrRestore had zero callers; WithPersistence
   never wired). The "write-only seam" pattern — a persistence function
   whose read-side counterpart exists but is unwired — is a recurring
   bug class. Audit each SaveX/WriteX in the finding's data path for a
   matching LoadX/ReadX with production callers.
