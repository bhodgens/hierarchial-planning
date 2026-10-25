# QuickPlan 3-Stage Classifier Cascade — classifier-iteration campaign (iters 1-20, 2026-09-07/09)

Worked example: 20-iteration measurement campaign + quickplan intent/mode tree on meept's Stage-0 classifier. All numbers below are from the committed evidence chain (tools/classifier-eval/results/, ITERATION-LOG.md).

## Campaign arc (what was measured)

- Baseline (iter 0) was WRONG: 14.7% C / 100% P matched only a warm-index self-included measurement. Honest 5-fold value: C 3.7%. Re-measure every inherited baseline before building on it.
- Champion config: qwen3-embedding-0.6B-4bit EOS pooling + nearest-centroid, floor 0.60, uniform margin 0.030 → C 34-36%, P up to 100% (synthetic), E2E 91.3% vs 86.8% chain-only.
- REJECTED with evidence: instruction-prefixed embeddings (lowers kNN P 93→88%), all k-majority heads (E2E-negative — precision bought with coverage loses to the chain baseline), logistic head (softmax prob ceiling ~0.54 at 4-bit 0.6B embedder; τ≥0.6 routes nothing), per-class margins (complexity, no E2E gain), word-count floors (removes easy coverage, wrongs survive), absolute-sim floors (margin rule subsumes).
- ModernBERT-base: raw mean-pool embeddings as Stage-0 embedder REJECTED (6% coverage, ~6× worse). Fine-tuned Stage-0.5 head WORKS after technique fix (see below).

## Technique fixes that changed results (iter 14→15)

Divergent fine-tune (loss pinned at ln(K), confidence uniform 1/K, forced accuracy = chance) was diagnosed as **head learning-rate underdose**: a fresh linear head needs lr ~1e-3; using the backbone's 2e-5 for both is a ~50× underdose — AdamW moves a zero-init head ~7.6e-4 over 38 steps. Same fixed-dose bug produces exactly-uniform outputs at any model size. Fix: separate head lr (1e-3) from backbone lr, train head-only (linear probe) on CPU, class-balanced loss, 30 epochs. Secondary suspects documented: MPS BERT-training kernel correctness bugs (pytorch#82707), ModernBERT small-task-from-base weakness (issue #225 — paper's small-task checkpoints start from MNLI mid-checkpoint).

## Quantile calibration beats absolute tau (iter 15)

Max-softmax on K=12 classes with ~200 training examples is severely underconfident (max prob ~0.21 even when correct). Fixed absolute tau (0.7-0.9) structurally routes nothing. Use train-side quantile: tau = quantile(train max-probs, 1-q), sweep q ∈ [0.3, 0.5]. This turned Stage-0.5 from 0 routes to +10-21pts coverage at 90-92% rescue precision.

## Real-traffic validation findings (iters 17-20)

- Synthetic E2E does NOT transfer: 92.8% synthetic → 84.7% first silver replay → 79.4% after adding the quickplan class (first honest baseline) → 83.97% after wave 2 + policy sweep. Each drop was real signal, not noise.
- Corpus expansion is the biggest lever, but only when the taxonomy matches reality. Data repairs (+2.0 E2E across two iterations) beat all gate permutations combined (+1.1).
- Adjudicated labels (user hand-labels) are the prerequisite for meaningful measurement — pattern-heuristic silver labels capped achievable score (review-vs-quickplan compounds were unresolvable under silver).
- **Ceiling finding**: quickplan-vs-code/git is not decidable from message text (surface form identical: "Implement Tasks 7 and 8: Add project fields..." reads code but is quickplan). The distinguishing signal is SESSION STATE (approved plan exists, tasks tracked). Any per-message classifier hits this ceiling; resolution belongs to a session-state-aware component (orchestrator) at execution time.

## Orchestration-cue guard pattern

QuickPlanCuePattern regex (subagents?/tasks? N/waves?/leaves?/plan.md/handoff/checklist/"and correct them"/"then run"/"as you find"/"no check-ins"...) gates quickplan predictions: prediction without cue support falls through to the LLM chain. Failed variant: appending cue bits to probe FEATURES (cue dominates, 67.5%). Working variant: plain features, cue gates the ROUTE DECISION only. Sweep tau × guard mode; best was tau 0.152 + conf-guard 0.15.

## 3-stage cascade architecture (user-directed)

Stage A (centroid, microseconds, P 97.8%) → Stage B (ModernBERT linear probe, milliseconds) → Stage C (production LLM chain, always answers). Model stage C at its MEASURED accuracy (deterministic expected credit), never a sampled draw — a seeded Bernoulli realized 89.9% vs true 86.8% and manufactured a false "clears bar" verdict (caught in audit; see pitfall below). Aggregate accuracy is the objective; a 90%-precision stage that replaces 87% chain calls is net-positive even when "less precise" than a stricter gate.

## Campaign pitfalls (session-proven)

1. **Sampled chain credit fabricates verdicts.** np.random.random() < 0.868 over 109 draws realized 89.9% (+1σ), flipping a FAIL to a PASS. Always use deterministic expected credit: sys_acc = (stage_correct + chain_acc × chain_routes) / total. Withdraw the verdict, recompute, and record the correction in the log (rows are history; corrections are separate sections).
2. **"NEVER enters train index" claims decay as the corpus grows.** First-seen folds are TEST for that sweep, but later-added cases train on earlier ones. State the guarantee precisely (fold cache = stable per case) or an audit will retract it.
3. **OOD handling has three distinct bugs waiting**: OOD cases in the train index (vote "OOD" unanimously — production gate has no OOD class), OOD rows skipped in test but counted in neither abstain nor routed pools, and compound-gold encoding (encode as ood:true = abstain-or-chain). Each silently corrupts OOD-R.
4. **Intent tables are exhaustive switches scattered across the package.** Adding a 13th intent requires grepping every switch (Keywords, IsValidIntentType, SemanticIndex.BuildIndex, SteeringHeuristicTable, ShouldDispatchAsync, DefaultAgent table test, Category, RequiresPlanning, ShouldCreateTask, SuggestedMode). Rule for leaf agents: when semantics are unclear, EXCLUDE the new intent and leave TODO(newintent) rather than guessing; explicitly list which tables were deliberately NOT touched and why (LLM-whitelist tables may short-circuit the cascade).
5. **Session-state-dependent intents cannot be classified per-message.** If the distinguishing signal is "an approved plan exists / tasks are tracked", route the final decision to the component holding that state (orchestrator at dispatch time), and reflect it as a one-way session-evidence upgrade in the prompt, never as a classifier feature.
6. **Fall-through vs wrong-route accounting**: when a boundary case flips from confident-wrong to correct-abstain, that's the invariant working — log it per-miss, not just as aggregate E2E.
7. **quickplan-vs-plan rule (user-ratified)**: execute-existing-plan = quickplan regardless of phrasing; plan = designing the approach before building. Review-and-correct (autonomous) = quickplan; verdict-only = review. Research = open survey; analyze = judgment against testable criteria.

## Measurement infrastructure (tools/classifier-eval/)

eval_harness.py: 5-fold cross (seed 42, fold-assignment.json cache COMMITTED — reassignment silently changes every future number), embedding cache (~/.meept/classifier-eval-cache/<model-hash>/<text-hash>.npy), heads (knn_unanimity/knn_majority/centroid/logistic/two_stage/prototype_hybrid), OOD/compound handling, confusion harvest for corpus growth, E2E = (correct + 0.868×abstained)/total. Adjudicated replay corpus is UNTRACKED (replay-gold.local.json5) — verbatim private text never enters git; the harvester (harvest_hermes.py) and aggregate metrics are tracked.

## Go runtime note

Homebrew python3.14 mlx install was broken (missing core .so); the working pair was python3.12 + mlx-lm. When an import-level version check returns None for an installed package, look for orphaned LICENSE-only .dist-info husks shadowing the real metadata — quarantine them (reversible) rather than reinstalling the real package.

## Post-adjudication follow-up (Q1-Q4, 2026-09-09) — decision rules settled

1. **Double-confidence gate measured and ADOPTED (user's idea).** Requiring BOTH stage-A margin pass AND stage-B prob > 0.7 collapsed stage B to zero routes on this data (probe softmax ceiling ~0.21 << 0.7 honest) — which is correct: B's rescue precision (58-83%) is below the chain's 86.8%, so B SHOULD stay silent until retrained past chain precision. Measured 84.56% vs 83.97% single-gate — simpler AND better. General rule: when a rescue stage's precision is below the backstop it feeds, gate it with the BACKSTOP's confidence, not its own — the collapse is the right outcome, not a failure.
2. **Plan-execution taxonomy settled (user-confirmed, supersedes earlier split):** ALL execute-existing-plan phrasing ("implement the plan", "implement the plan using subagents") = quickplan. The earlier bare-verb-vs-orchestration-hint split is DEAD. `plan` = designing the approach before building.
3. **"Help me…" phrasing = quickplan signal** (compound/complex work: investigation + action). Purely informational help ("help me understand X", no artifact) = analyze. Documented in docs/workflows/intent-routing.md QuickPlan section.
4. **E2E smoke gate learnings (scratch daemon, HTTPS :18096):** hujson rejects unquoted keys at ALL depths (inline `{ enabled: false }` included); `transport.http.rest` is a BOOL — omission means RESTEnabled=false and every /api/v1/* route 404s while /health still answers (auth+route confusion); dev-key auth resolves the REAL ~/.meept/dev_key via os.UserHomeDir, not MEEPT_HOME — use the real key in the smoke client or copy it into the scratch home; the coder execution budget for quickplan review runs needs `max_conversation_tokens` in coder AGENT.md frontmatter (50k default aborts mid-review at real-file reading; 400k completed the loop live). Full Q1-Q4 response: results/q1-q4-response.md.
