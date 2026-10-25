# Classifier Campaign + QuickPlan Session (2026-09-08/09, meept)

Session-level lessons from the 20-iteration classifier campaign and the
quickplan-mode implementation tree (branch classifier-iteration,
commits 30f697da..49036388 + quickplan tree 049afe73..ebfc7a2b).

## 1. Scratch-config authoring against meept's hujson parser

meept config files are hujson: comments and trailing commas OK, but ALL
object keys MUST be quoted (top-level AND inline `{ enabled: true }`
fails). The ^-anchored regex quote-pass misses inline keys after `{` or
`,` — quote with `([{,]\s*)([A-Za-z_]\w+)(\s*:)` instead. Verify with a
zero-unquoted-keys check before starting the daemon.

Schema facts that cost three daemon restarts to learn:
- `transport.http.rest` is a **bool**, not an object (`"rest": true`).
  Omitting it = REST routes 404 (DefaultServerConfig() sets
  RESTEnabled=true, but daemon.go OVERWRITES with the config value —
  line ~1104 `httpCfg.RESTEnabled = fullCfg.Transport.HTTP.REST`).
  Omitted key parses as false. Same overwrite pattern applies to every
  field daemon.go copies — "default true" comments lie once the config
  key exists in the struct.
- `transport.http` keys are `addr`/`require_auth`/`api_keys` — NOT
  `listen_addr`/`auth{}` (that shape is a different config surface).
- Dev API key lives at `~/.meept/dev_key` via
  `pkg/constants.DevAPIKey()` — os.UserHomeDir(), NOT MEEPT_HOME. A
  scratch daemon with MEEPT_HOME=/tmp/... still authenticates against
  the REAL home's dev_key. Smokes should read that file for the
  Bearer token.
- REST route 404s with CORS headers present = auth passed but
  RESTEnabled=false. 404 WITHOUT CORS headers = mux-level miss.
  Distinguish with `curl -v` (response headers tell you which layer
  rejected).

## 2. Agent-definition overrides: discovery tiers ignore MEEPT_HOME

`agents.DefaultTiers()` uses os.UserHomeDir() — real `~/.meept/agents`
plus `~/.config/meept/agents`. A scratch daemon with MEEPT_HOME=/tmp/...
still discovers agent definitions from the USER'S real ~/.meept/agents.
You CANNOT ship per-scratch agent overrides via MEEPT_HOME.

Options that work:
- `max_conversation_tokens` in an AGENT.md frontmatter (parsed via
  internal/agents/parser.go altMeta, merged in
  registry.mergeAgentDefinition when > 0) — but place the AGENT.md in a
  discovered tier (user data; ask before writing) or copy
  `config/agents/` into the daemon's CWD (resolveBundledPath stats CWD
  first).
- Raising `llm.context_firewall.conversation_budget_ratio` (0.50
  default) in config scales the effective budget without touching agent
  files.
- The observed failure mode when the override doesn't reach: coder
  dies at `DefaultConversationTokenBudget = 50000` mid-review —
  "conversation token budget exhausted" at exactly 50-51k = budget not
  raised, not a code bug.

## 3. Classifier campaign technique wins (iter 14-20 arc)

- **Multi-class softmax ceiling**: a 12-class linear/softmax head on
  ~200 examples pins max-prob at ~1/12 (uniform). Any absolute tau
  >= 0.5 routes nothing. Fix: train-side QUANTILE calibration (route
  when conf >= the (1-q) quantile of train confidences), never fixed
  tau.
- **Per-component learning rates**: fine-tuning a fresh head at the
  backbone lr (2e-5) is a ~50x underdose -> loss flat at ln(n_classes),
  confidence uniform. Head lr 1e-3, backbone lr 2e-5 (or frozen). Symptom
  signature: loss == ln(K) exactly + uniform predictions.
- **Research-driven retrain beats re-dispatch**: before declaring a
  model "can't learn", run a one-fold diagnostic with corrected
  hyperparameters (fold 0, forced-route accuracy vs chance). If forced
  acc >> chance, features are fine — it's an optimization bug.
- **Anchor waves for class imbalance**: when a new class collides with
  a dominant one on shared vocabulary (quickplan 20 anchors vs code 35),
  author collision-shape anchors (same vocabulary, correct label) plus
  boundary negatives (verdict-only, design-first) to fence the boundary.
- **Dedup guard**: reject new corpus cases at cosine > 0.95 to any
  existing case (same embedder). Prevents label-flip noise from
  paraphrase floods.

## 4. QuickPlan semantics (normative, user-adjudicated)

- review-and-CORRECT (autonomous, multi-site) = quickplan
- verdict-only, guaranteed no changes = review
- execute-existing-plan (any phrasing, incl. bare) = quickplan
- "help me ..." phrasing = quickplan signal (compound work);
  purely informational help = analyze
- research = open survey without testable criteria; analyze = judge
  against testable criteria
- quickplan-vs-code/git from message text alone is information-limited:
  the distinguishing signal (active plan, tracked tasks) is SESSION
  STATE. Architecture answer: orchestration-cue regex guard on
  quickplan predictions + orchestrator session-context block for the
  one-way upgrade at execution time. Never "fix the classifier harder".

## 5. Gate policy measurement shape

Sweep B-route policies (tau x guard) as a matrix, not one-at-a-time:
cue-gate, conf-gate, cue-or-conf at 3 tau levels each. Best policy in
iter-20 was tau 0.152 + conf-guard 0.15 (83.97%). The sweep converts a
subjective "which guard feels right" into a table. Cost: one script run
against cached embeddings.

## 6. Capability-aware allotment (follow-up tree authored)

User conceptualization: the orchestrator chunks work to fit each
agent's context window — multiple coder agents instead of one grinding
through compaction. Investigation: the orchestrator pipeline already
exists (quickplan routes through it); the gap is that tactical
scheduling is COUNT-capped only (MaxStepsPerPhase=8) — nothing reads
the executor model's context window. The window source already exists:
llm.Resolver ResolveRef/ResolveGeneration -> ModelConfig.ContextLimit
(populated from models.json5 context_limit + ContextDiscovery).

Tree authored: docs/plans/allotment/ (2 leaves). 01: pure math
(AllotmentConfig usableRatio .75/reserve 4096/charsPerToken 4/
minStep 512; AllotmentTokens floors at 0; SplitStepsByAllotment greedy
fill, oversize step own batch, zero allotment = single batch legacy).
02: ContextWindowProvider func(agentID) int on TacticalScheduler
(nil-safe 0), continuation TaskSteps chained via DependsOn,
PlanRequest.ExecutorModelRef, daemon wiring mirroring SetPlanManager.

## 7. Double-confidence gate (user idea) — measured, adopted

Route only when BOTH stages clear 0.7: measured 84.56% vs 83.97%
current on the gold replay. Collapses to "A routes, rest to chain"
because the probe's 12-class softmax ceiling (~0.21) can never reach
0.7 — and that is the CORRECT behavior while B's rescue precision
(58-83%) sits below the chain's 86.8%. User gates can be simpler AND
better; measure before defending the complex policy.
