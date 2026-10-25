# QuickPlan-Style Intent Addition — classifier routing recipe

Session-proven 2026-09-09 (meept quickplan-mode tree, 4 leaves, all first-pass).

## When a routing taxonomy needs a new intent

Signals: adjudicated real traffic shows a class that is >20% of messages
and absent from the taxonomy (quickplan was 42%); the label disagreement
cluster in user adjudication maps to ONE missing concept, not scattered
noise; after-the-look semantics (what happens next, who acts) differ.

## Decision rule for "look at X" intents

Resolve by what happens AFTER the look, and who acts:
- agents fix autonomously, many unknown sites → new orchestration intent
  (quickplan) or debug (one named defect)
- findings return to the user, guaranteed no changes → review
- understanding of something not necessarily broken → analyze

## The classifier cannot see session state

Iter-20 finding (adjudicated gold replay): quickplan-vs-code/git is
undecidable from message text alone — "Implement Tasks 7 and 8: Add
project fields..." is code vocabulary but quickplan because an approved
plan exists in session state. Consequences:
1. Anchor waves CANNOT fix a session-state boundary; the fix is
   orchestrator-side resolution at execution time (session context in
   the planning prompt, one-way upgrade rule).
2. Don't chase 100% per-message accuracy — record the ceiling as a
   finding. 100% collective (chain always answers + errors recoverable)
   is the achievable target.

## Implementation seams (meept dispatcher)

Adding an intent touches SIX places minimum:
1. intent.go: constant + 5 method switches (SuggestedMode, DefaultAgent,
   Category, RequiresPlanning, ShouldCreateTask) + ShouldDispatchAsync +
   Keywords + IsValidIntentType + SemanticIndex.BuildIndex +
   SteeringHeuristicTable
2. LLM classifier whitelist tables: DELIBERATE choice to add or exclude
   (exclude = assigned by post-chain cascade instead)
3. dispatcher: validModes + suggestMode (guard against short-input
   downgrade when the phrasing IS the signal) + final-fallback swap +
   ambiguity gate interaction (PendingMode on pendingClarification so
   ResumeAfterClarification re-enters in the new mode)
4. prefilter: cue regex (package-level compiled) + vote() guard (new-class
   prediction without cue evidence falls to chain) + centroid index
   examples via the builder script
5. docs: intent-routing reference + prefilter doc + AGENTS.md review
6. session-state override: orchestrator prompt gains session context
   (active plan/tasks) with a ONE-WAY upgrade rule (session evidence
   upgrades to the new intent; absence never downgrades an explicit one)

## Latent bugs this class of work surfaces (check for them)

- Ambiguity gate never recorded pending-clarification state (resume
  unreachable) — any new clarify-then-X mode inherits this.
- Analyzer category whitelist coerces unknown intent names to "other" —
  the new class must be whitelisted or the seed can never match.
- build_prefilter_centroids.py parses only the legacy corpus layout and
  chokes on // comments — keep it in sync with eval_harness.py's parser
  (comment stripping + dual layout: categories: and cases:).

## Scratch-daemon e2e smoke recipe

1. go build -o /tmp/<name>-daemon ./cmd/meept-daemon
2. Scratch config: QUOTE ALL JSON5 KEYS (hujson rejects unquoted at any
   nesting depth — top-level AND inline { enabled: false } shapes).
   transport.http keys: enabled/addr/require_auth/rest (rest is a BOOL —
   {"enabled": true} shape fails; the shipped default has REST off when
   omitted, contradicting DefaultServerConfig's comment).
3. Point the LLM provider at the user's LIVE runtime port if same model
   (adopt-external pattern; drop the lifecycle spawn block). Check
   lsof before choosing ports.
4. Auth: DevAPIKey() reads os.UserHomeDir()/.meept/dev_key — REAL home,
   not MEEPT_HOME. Bearer that key.
5. transport.http.rest must be explicitly true in config or /api/v1/*
   404s (daemon.go overwrites DefaultServerConfig's RESTEnabled=true
   with fullCfg value).
6. Kill stale daemons by PID from lsof/ps — "daemon already running"
   guard is PID-file based.
7. Smoke checks: cue-bearing message routes the new class without a
   clarification gate; ambiguous input clarifies; gibberish falls to
   chat; prefilter direct-route appears in logs
   (classification_method=embedding_prefilter).
