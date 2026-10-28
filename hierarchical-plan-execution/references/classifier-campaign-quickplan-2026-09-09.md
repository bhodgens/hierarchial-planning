# Cclassifier campaign quickplan 2026 09 09
When to use: 4-leaf quickplan tree + 40-iteration campaign.
Lesson: taxonomy touchpoint inventory, cue-guard pattern, adjudicated gold replay workflow.

# Classifier Campaign + QuickPlan Tree — 2026-09-09 session

Worked example for `hierarchical-plan-execution` / `hierarchical-planning`:
40-iteration classifier campaign + a 4-leaf Go feature tree executed
end-to-end in one session. Key transferable lessons below; session
artifacts live in meept `tools/classifier-eval/` and
`docs/plans/quickplan-mode/`.

## 1. Baseline-row forensics before trusting prior numbers

The campaign's iter-0 row (14.7% C / 100% P) was not reproducible under
any held-out protocol. It matched only a warm-index, self-inclusive
measurement. Rule: before building on a prior session's baseline
number, reproduce it under the documented protocol FIRST. If it only
reproduces under a different (sloppier) protocol, correct the record in
the same commit that establishes the honest baseline.

## 2. Data repair beats gate tuning (measured, repeatedly)

Two corpus label repairs produced +2.0 E2E points; ALL gate/embedder
permutations combined produced +1.1. When hand-audited wrong-routes are
label-defective ("create a scheduled job for cleanup" filed as code;
fix-shape vs write-shape conventions), fix the corpus, not the
threshold. Threshold tuning is the LAST lever, corpus repair the first.

## 3. Fine-tune flat-lining = head-lr underdose, not bad data

Symptom: loss pinned at ln(n_classes), softmax confidence uniform 1/n,
forced accuracy = chance. Diagnosis arithmetic: AdamW at lr 2e-5 moves a
zero-init linear head ~7.6e-4 over ~38 steps — a ~50x underdose vs the
standard 1e-3 head lr; the head never escapes uniform output. Fix:
split learning rates (head 1e-3, backbone 2e-5), train on CPU (MPS
BERT-finetune correctness bugs are documented: pytorch#82707). Also:
max-softmax on many classes with tiny data is severely underconfident
(ceiling ~0.21 on 12 classes/202 examples) — calibrate with TRAIN-side
QUANTILE tau, never fixed absolute tau.

## 4. Per-message classifiers cannot see session state (architecture
ceiling, not a tuning gap)

Residual misroutes were all quickplan-shaped ("implement the plan
using subagents") whose TEXT is identical to code/git. The
distinguishing signal (an approved plan exists, tasks are tracked)
lives in session state. After 3 anchor waves + 13 policy combos the
plateau held. Resolution is architectural: the orchestrator (which HAS
session state) resolves quickplan-vs-code at execution time; the
pre-router defers. When a user asks for "100% accuracy", reframe to
system-level: chain backstop makes misroutes recoverable; per-stage
100% on text alone is information-theoretically out of reach — record
it as a finding, stop sweeping.

## 5. Multi-stage cascade = cheapest-first with aggregate objective

Design per user directive: ModernBERT probe (SetFit recipe: frozen
embedder + trained linear head) rescues embedding-gate abstains; LLM
chain is the completeness floor (always answers, modeled at its
measured accuracy). Each stage's precision only needs to beat the stage
it replaces, not the global bar. Sweep B-exit tau as a TRAIN-side
quantile, and evaluate the CASCADE by total system accuracy.

## 6. Silver-label corpora: harvest → audit → promote workflow

- Harvest with pattern heuristics + explicit OOD filters (doc-writing
  filter: "write sections N../report/.md" is NOT code).
- Keep verbatim private text in an UNTRACKED file (gitignore the exact
  path); commit only the harvester + aggregate metrics.
- Adjudication sheet format that worked: markdown, disagreements sorted
  first, each case shows silver label + cascade answer + blank
  `**your label:**` line. User fills labels inline.
- Post-adjudication, promote to a second untracked gold file with
  `adjudicated: true` and record the decision rules as normative
  (they become the spec for new intents).

## 7. Known-broken environment: brew python3.14 mlx half-install

Symptom: `import mlx.core` → no attribute / missing
`core.cpython-314-darwin.so` in /opt/homebrew/lib/python3.14/site-
packages. Fix sequence: `brew reinstall mlx && brew link --overwrite
mlx` (unlink/link alone insufficient when stale dirs exist). Secondary
crash (transformers "Unable to compare versions for numpy>=1.17
found=None"): orphaned `numpy-<ver>.dist-info` husks (license-only,
no METADATA) shadow importlib.metadata — quarantine them to
~/.hermes/quarantine-* rather than delete. Working runtime for
mlx_lm + embed servers: /opt/homebrew/opt/python@3.12/bin/python3.12.

## 8. gitignore negation for campaign evidence

Blanket `results/` ignores hid iteration evidence. Pattern that works:
keep the blanket, add `!tools/<tool>/results/` + `!tools/<tool>/results/**`
negations, and treat fold-assignment caches (fixed-seed splits) as
campaign-critical tracked state, not regenerable artifacts.

## 9. User-defined routing taxonomy (meept, normative 2026-09-09)

- review = verdict ONLY, no changes (human decides after)
- quickplan = look + plan + execute autonomously (clarify-if-ambiguous
  up front; no approval pauses after clarification)
- debug = ONE named defect, fix follows directly
- analyze = understanding/judgment vs testable criteria; research =
  open survey without testable criteria
- execute-existing-plan = quickplan (bare verb or orchestrated alike)
- review intent routes to coder (executor) in the daemon; look-only
  reviewer agents are verification gates, not routing destinations
- quickplan is the final classifier fall-through (clarify-first)
- Full user-facing map: meept docs/workflows/intent-routing.md
