# Encoder Classifier Fine-tuning Recipe (SetFit-style, small data)

Distilled from the quickplan/classifier campaign (2026-09-09) where a
13-class intent classifier was fine-tuned over a frozen 768-d encoder on
~200-370 labeled examples, validated against a user-adjudicated
real-traffic replay.

## The core bug this recipe prevents

A freshly initialized linear head trained with the backbone's learning
rate (2e-5) will NOT learn: loss pins at ln(K) (uniform guessing), softmax
confidence pins at 1/K on every input, and forced accuracy equals chance.
AdamW at 2e-5 moves a zero-init head ~7.6e-4 in weight space over 38
steps — ~50x underdose. Symptom cluster: flat loss + uniform confidence +
chance accuracy = TRAINING failure, diagnose before touching data.

## Recipe

1. **Split learning rates.** Head: 1e-3 (AdamW, weight_decay 1e-2).
   Backbone (if unfrozen at all): 2e-5 with the head at 1e-3 — or simply
   freeze the backbone for the first attempt.
2. **CPU before MPS.** PyTorch MPS BERT-family training has documented
   correctness bugs (infinite loss, NaNs, degraded metrics vs CPU).
   pytorch/pytorch#82707. For <=400 examples, CPU epochs cost seconds.
3. **Diagnose before retuning.** Flat loss at ln(K) + confidence pinned
   at 1/K = broken training. Probe: retrain JUST a linear head at 1e-3
   for ~10-20 epochs on the same features; if forced accuracy jumps far
   above chance, features are fine and the original run's optimizer/lr
   was the failure.
4. **Class-balanced loss** for skewed classes:
   `weight_c = N / (K * max(count_c, 1))`.
5. **Quantile tau, never fixed tau.** Small-data softmax over K classes
   is underconfident (max prob ~0.15-0.25 even when correct; 1/K floor).
   Calibrate abstention as a train-side quantile: tau = quantile(train
   max-probs, 1 - q), q in 0.3-0.5. Fixed taus like 0.7-0.9 route nothing.
6. **Deterministic everything**: torch.manual_seed, full-batch or
   seeded-permutation minibatching, CPU device in the seed path.

## Feature choices

- Mean-pool the last hidden state over the attention mask, L2-normalize.
- MLP head or LLM large-vocab head at 256 max_length tokens.
- 13-way softmax over 768-d frozen features reaches ~60% forced accuracy
  at ~200 train examples; per-class margin gates + quantile tau lift
  system accuracy further.
- Cue-gate at decision time (not feature time): append-nothing, but if
  the predicted class is quickplan/multi-step, require an orchestration
  cue (subagent/task/wave/leaf/plan.md markers) or abstain. Cue
  FEATURES (concat bit vectors) poison the probe — 13-way accuracy
  dropped from 84% to 67.5% when a cue bit was concatenated.

## Validation discipline

- Never sample credit for probabilistic stages: use deterministic
  expected credit (`routes_correct + fallback_count x baseline_accuracy`).
  A seeded Bernoulli draw at p=0.868 realized 89.9% over 109 draws and
  flipped a pass/fail verdict.
- User-adjudicated gold replay (48 real messages, untracked verbatim
  file) is the honest ruler; adjudication sheet format: message, silver
  label, cascade answer + per-stage confidences, blank `your label`
  line, disagreements sorted first.
- Session-state signals (an approved plan exists / tasks are tracked)
  are invisible to per-message classifiers — route those cases to an
  orchestrator that can read session state at dispatch time.
