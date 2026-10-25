# QuickPlan intent + 3-stage cascade (meept 2026-09-09, commits 4870fc98..ebfc7a2b)

QuickPlan is now a first-class intent + planning mode in meept's
dispatcher: plan → clarify-if-ambiguous up front → execute autonomously
to completion. It is ALSO the final classifier fallback (replacing the
plain-chat floor at classifyIntent Step 5). Routing doc:
docs/workflows/intent-routing.md.

## Decision rules (user-adjudicated, normative — results/adjudication-record.md)

1. review-and-CORRECT (autonomous) = quickplan, NOT review
2. verdict-only, guaranteed no changes = review
3. execute-existing-plan: ANY phrasing ("implement the plan", "implement
   the plan using subagents") = quickplan. plan = designing/creating the
   approach only. The earlier bare-verb-vs-subagent split is DEAD.
4. research (open survey, no testable criteria) vs analyze (judge
   against testable criteria)
5. search-verification ("search and make sure it works") = review
6. document edit producing a tracked repo artifact = code; conversational
   summary = report

quickplan was 42% of adjudicated real traffic (20/48) — the largest
class. When a new class dominates real traffic, add it to the taxonomy
even if late.

## Architecture answer to the classification ceiling

Per-message text classification CANNOT decide quickplan-vs-code/git:
the distinguishing signal (an approved plan exists, tasks tracked) is
SESSION STATE. Proven by plateau: after 2 anchor waves + 13-combo
policy sweep, replay accuracy plateaued ~84% with all residual misses
being quickplan-labeled messages reading as code/git. The design
answer: classifier routes quickplan WITH an orchestration-cue guard
(QuickPlanCuePattern — subagents/task N/waves/leaves/plan.md/"and
correct them"/then-chains); an uncued quickplan prediction falls to the
LLM chain; the orchestrator makes the final session-state call at
execution time. 100% collective accuracy = chain always answers +
misroutes recoverable downstream, NOT 100% first-stage accuracy.

## Fine-tune failure post-mortem (ModernBERT + linear head)

Symptom: loss flat at ln(12) (= uniform guessing for 12 classes),
softmax confidence pinned at exactly 1/12, forced accuracy = chance.
NOT bad data, NOT harness bug. Cause: SINGLE lr 2e-5 for both backbone
layers and a freshly-initialized linear head. AdamW at 2e-5 moves a
zero-init head ~7.6e-4 over 38 steps — ~50× underdose; the head never
escapes uniform output. Fix: head-appropriate lr (1e-3) for the probe;
backbone keeps the small lr. General rule: a fresh head needs its own
lr 1-2 orders of magnitude above the backbone's; check head-init drift
arithmetic (lr × steps) BEFORE blaming features or data.
Secondary hazard (documented, pytorch#82707): MPS BERT fine-tuning has
correctness bugs (infinite loss/NaNs) — train on CPU when the run is
small; also check transformers' dependency version check against
orphaned *.dist-info husks (numpy-2.5.x license-only dirs shadow
importlib.metadata → version None → transformers explodes).

## Small-data probe recipe that worked (quickplan 65%, review 86%)

- ModernBERT-base frozen mean-pool, L2-normalize, CPU.
- Linear head, lr 1e-3, 30 epochs, batch 16, class-balanced CE weights.
- Calibration: train-side quantile of max-softmax (NOT fixed tau —
  12-way softmax on ~200 examples tops out ~0.21 even when correct).
- Cascade: centroid gate first, probe rescues abstains at 90-92%
  precision on adjudicated labels.

## Latent bugs fixed as prerequisites (found only when wiring for real)

- The ambiguity gate never recorded pending-clarification state at all —
  ResumeAfterClarification was unreachable for EVERY intent, not just
  quickplan. Clarify-first modes need: pendingClarification struct gains
  PendingMode; gate seeds it; resume reads it before clear and re-sets
  SuggestedMode so the post-clarification turn re-enters the same mode.
- Intent analyzer had a category whitelist that coerced unknown labels
  to "other" — a new intent is invisible to the LLM chain until added
  there, not just to intent.go.
- New-intent checklist (meept): intent.go constant + 5 method switches
  (SuggestedMode/DefaultAgent/Category/RequiresPlanning/
  ShouldCreateTask/ShouldDispatchAsync), SemanticIndex.BuildIndex,
  SteeringHeuristicTable, IsValidIntentType, Keywords, analyzer
  category whitelist, validModes + suggestMode, final-fallback swap,
  prefilter cue guard, centroid index rebuild, docs. Deliberate
  exclusions: llm_classifier whitelist (post-chain cascade concern),
  keywordPatterns (sparse by design), strategic_routing tables.

## E2E smoke configuration gotchas (scratch daemon)

- hujson requires ALL object keys quoted, including inline
  `{ "enabled": false }` — the ^-anchored key-quoting regex misses
  same-line keys after `{` or `,`.
- transport.http.rest is a BOOL in the schema but
  http.DefaultServerConfig() sets RESTEnabled=true — an explicit
  `rest: false` or omitted key silently disables /api/v1/* routes
  while /health still responds (auth passes, mux 404s). Symptom:
  auth OK + everything 404 = REST flag off.
- The scratch daemon adopted the USER'S live :8082 runtime ("observed,
  not owned" log line) — diff adopted PIDs against expected ports before
  attributing failures to config.
- Dev API key: pkg/constants.DevAPIKey() uses os.UserHomeDir()
  (real HOME, not MEEPT_HOME) → key lives in ~/.meept/dev_key even when
  MEEPT_HOME is isolated. Smokes must send it as Bearer auth; the
  legacy "meept_dev_default_key_CHANGE_ME" string is BANNED (418 teapot).
- Agent constraint overrides (max_conversation_tokens in AGENT.md
  frontmatter) load from discovery tiers anchored to real
  os.UserHomeDir() (~/.meept/agents), not MEEPT_HOME and not the daemon
  CWD — an override in the scratch tree silently does not apply.
- Coder default conversation budget 50k exhausts on any real
  review-and-fix run (105s, 51k tokens) — raise
  max_conversation_tokens in the coder AGENT.md frontmatter before
  e2e smokes of long executor work.

## Smoke-test checklist for intent-routing changes (meept)

1. Rebuild the scratch daemon binary AFTER the last behavior commit —
   a stale /tmp binary produced misleading route-404s for an hour.
2. Scratch daemon: isolated MEEPT_HOME, own HTTP port, prefilter URL
   at the shared embed server, `transport.http.rest: true` explicit.
3. Three smokes through POST /api/v1/chat with Bearer dev key:
   (a) cue-bearing quickplan — expect the coder executor to run real
   file reads (grep daemon log for file_read on real paths); (b)
   ambiguous bare verb ("fix it") — expect clarify; (c) gibberish
   longer than the short-guard — expect chat-style or clarify, never
   a confident route.
4. The full quickplan execute loop (coder reading project files) runs
   ~105s / ~51k tokens; raise the budget first or the run aborts at
   50k with "conversation token budget exhausted".
