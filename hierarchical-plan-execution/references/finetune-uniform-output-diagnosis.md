# LLM fine-tuning failure: frozen-output / underdose diagnosis

Session-proven 2026-09-09 (meept quickplan classifier, ModernBERT-base
+ linear head on macOS MPS, 3 epochs).

## Symptom

Fine-tuned head produces a UNIFORM distribution regardless of input:
- loss pinned at ln(n_classes) across all epochs (no downward trend)
- test confidence = 1/n_classes exactly on every query
- forced accuracy = chance level

## Root-cause checklist (ordered by likelihood)

1. **Head learning-rate underdose (most common).** A freshly initialized
   classification head trained at a backbone-tuned lr (e.g. 2e-5) moves
   ~lr × steps in weight space — orders of magnitude too little to
   escape random init. Arithmetic: AdamW at 2e-5 over 38 steps ≈ 7.6e-4
   total movement. Fix: SEPARATE lrs — head at 1e-3, backbone at 2e-5
   (or freeze backbone entirely; linear probe at 1e-3 on frozen features
   both diagnoses and often suffices — SetFit recipe).
2. **MPS (Apple Silicon) training-kernel correctness.** Documented
   BERT-family failures: infinite loss, NaNs, silently wrong gradients
   (pytorch/pytorch#82707). Fix: train on CPU; at small-data scale the
   cost is minutes. Keep MPS for inference only.
3. **Data genuinely insufficient** — check LAST: small-data linear probes
   work at ~17 examples/class (GLUE RTE trains on 2.5k). If a probe at
   lr 1e-3 reaches well above chance, features are fine and data was
   never the problem.

## Diagnostic that settles it in one run

Train a linear probe (frozen features, head-only lr 1e-3, 20-30 epochs,
class-balanced loss) on one fold:
- probe reaches well above chance → features fine; the joint fine-tune
  was underdosed → retrain with split lrs
- probe also at chance → features carry no signal → different embedder
  or more data needed

## Calibration on small-data multi-class

Max-softmax on n classes with tiny data is severely UNDERCONFIDENT
(observed ceiling 0.21 on 12 classes even when correct). Fixed
absolute tau (0.7-0.9) routes NOTHING. Use train-side QUANTILE
calibration: tau = quantile(train max-softmax, 1-q), sweep q ∈
{0.3, 0.4, 0.5} and pick by downstream acceptance metric.

## Cascade routing policy

Per-class exit rules beat a global confidence bar: e.g. a quickplan
prediction requires orchestration-cue evidence (regex on the input) OR
confidence ≥ a second threshold; other classes use tau alone. Sweep the
policy grid (tau × guard mode) — the best policy is often "high-precision
classes route freely; the confusable class needs extra evidence."

## Two-stage cascade accounting pitfalls

- NEVER score the always-answers backstop stage with a sampled Bernoulli
  draw — use deterministic expected credit (n × accuracy). A seeded draw
  realized +1σ luck and manufactured a false "clears bar" verdict
  (caught in post-hoc audit).
- The pre-router cannot see session state; misroutes that are
  recoverable downstream (chain re-classifies) are acceptable — score
  the SYSTEM, not each stage.
- Class-imbalance: oversample the new class ×2 in the loss AND apply
  class-balanced weights; a 20-vs-35 anchor imbalance hands the boundary
  to the majority class on shared vocabulary.

## ModernBERT notes

- Small-task fine-tunes from the BASE checkpoint underperform the
  paper's numbers because paper checkpoints for RTE/MRPC/STS-B start
  from the MNLI mid-checkpoint (AnswerDotAI issue #225).
- Official GLUE hyperparams: lr 8e-5 full fine-tune, batch 32, 2 epochs,
  adamw_torch, linear schedule, bf16.
- Raw mean-pooled ModernBERT-base embeddings are a WEAK intent-clustering
  space (6% kNN coverage vs 36% for qwen3-embedding-0.6B on the same
  corpus) — supervised training is required to make it usable.
- config.classifier_pooling: mean is default; cls did not help.
- On MPS pass attn_implementation="eager" or "sdpa"; flash-attn does
  not exist on Apple Silicon.
