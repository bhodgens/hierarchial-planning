# Encoder classifier fine-tuning recipe (linear probe over frozen embeddings)

Proven on meept's quickplan classifier campaign (ModernBERT-base, 13 intents, ~200-370 training cases, macOS).

## Setup

- Backbone: transformers AutoModel, frozen, eval mode. Embedding = mean-pool last hidden state over attention mask, L2-normalized. Feature dim = hidden_size (768 for base).
- Head: fresh `torch.nn.Linear(hidden, n_classes)`. This head starts at ZERO knowledge — its learning-rate needs are ~50-100× the backbone's.
- Device: **CPU for training**. MPS BERT-family training has documented correctness bugs (loss can silently not descend; pytorch#82707 family). CPU is fast enough for ≤1000 examples × ≤50 epochs.

## The failure signature (memorize this)

- Loss pinned at ln(K) (K = class count; e.g. 2.48 for 12 classes)
- Softmax confidence ≈ 1/K on EVERY input, train and test
- Forced accuracy ≈ chance

This means the head never learned. With class-balanced AdamW at head-lr the loss MUST drop within a few epochs; if it doesn't, suspect (in order): (1) head lr too low, (2) features uninformative, (3) labels broken. Diagnose with a linear probe at lr 1e-3, 20-30 epochs, before anything else.

## The recipe

```python
torch.manual_seed(42)
head = torch.nn.Linear(hidden, n_classes)
counts = np.bincount(y, minlength=n_classes)
w = torch.tensor(len(y) / (n_classes * np.maximum(counts, 1)), dtype=torch.float32)
lossf = torch.nn.CrossEntropyLoss(weight=w)          # class-balanced
opt = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-2)
for ep in range(30):                                  # full-batch minibatch sweep
    perm = torch.randperm(len(Xt))
    for i in range(0, len(perm), 16):
        idx = perm[i:i+16]
        opt.zero_grad()
        lossf(head(Xt[idx]), yt[idx]).backward()
        opt.step()
```

- 30 epochs @ lr 1e-3 took forced accuracy from 12.5% (chance) to 60.4% on the same features that "failed" at lr 2e-5. When labels are contested, 60% forced accuracy is still enough for a useful abstain-gated route.

## Calibration: quantile tau, never absolute tau

Max softmax probability on small-K small-data problems is severely underconfident (observed ceiling 0.21 with 12 classes / 200 examples). A fixed tau of 0.7-0.9 routes literally nothing. Calibrate on TRAIN-side predictions:

```
tau = np.quantile(train_max_probs, 1 - q)   # q = fraction you want routing
```

Sweep q ∈ {0.3, 0.4, 0.5} and pick by downstream (cascade/system) accuracy, not probe precision alone. Expected result at q=0.4-0.5: route share +10-20pts at rescue precision ~90%.

## Guard rails for production use

- If one class is "execution-flavored" and easily confused with concrete classes (quickplan vs code), gate that class's route on a lexical cue (orchestration keywords). A cue-gated route decision beat cue-features-in-probe by 16pts — cue bits in the feature vector dominate the probe and cause over-routing.
- Class-imbalance: oversample the new/thin class 2× IN ADDITION to balanced loss weights when it collides with a 3× larger class on shared vocabulary.
- Iterate: anchors targeting the exact collision surface (same verbs, same nouns, orchestration framing) → retrain → re-validate on the held-out human-adjudicated set. Expect the first retrain after adding a class to score WORSE on the validation set (boundary re-forming); the wave-2 anchors are what recover it.

## Data sizing

Linear probes learn from ~15-20 examples/class. Contested-boundary cases need anchor waves, not more epochs. If forced accuracy at proper lr is still near chance, THEN suspect features/labels — never before.

## Architecture ceiling — stop sweeping when you see this signature

If residual misroutes all share "text indistinguishable from the competing class, but the true label depends on conversational state" (e.g. quickplan vs code: an approved plan exists in session state), more anchors/sweeps/tune cycles will NOT help — the signal is not in the message. Route the decision to the component that holds the state (orchestrator/session tracker) and record the ceiling as a finding. Signature check after each wave: are the remaining misses' competing labels decided by context the message doesn't contain? Then stop; three waves + a 13-combo policy sweep without movement confirmed this on the meept campaign (plateau 83.97%, all residuals context-decided).

## Companion-parser drift

When the campaign corpus gains `//` comments or a second layout (`cases:` vs `categories:`), EVERY parser reading it drifts — the eval harness was patched first and the centroid builder broke silently later. Rule: when the corpus format evolves, grep the repo for other readers of the same file and patch them in the same commit.
