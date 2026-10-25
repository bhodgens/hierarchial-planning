# Classifier cascade campaign — meept classifier-iteration (2026-09-08)

Distilled technique for building and evaluating staged LLM message
classifiers. Campaign state lives in the repo, never in session memory:
docs/plans/classifier-iteration/ (master.md, ITERATION-LOG.md),
tools/classifier-eval/ (harness + specs + results/, tracked), and
replay-corpus.local.json5 (gitignored silver corpus).

## Reporting style (user preference, learned mid-campaign)

After a dense metrics-heavy status, the user asked "explain that again
like I'm stupid." For campaign updates: lead with the MECHANISM in
plain language (e.g. the fine-tune failure is "one knob set 50x too
small" — a shower-temperature analogy), keep the tables, and offer the
simple version instead of making the user ask. Numbers stay exact;
prose gets simpler.

User steering patterns to expect mid-campaign (all hit this session):
- "explain that again like I'm stupid" → simplify the last answer.
- Architectural redirection mid-flight ("3 stages not 2: cheapest to
  most expensive, aggregate result") → reframe the objective from
  per-stage maximization to system-level accuracy; the existing
  harness accommodated this with a one-script change because each
  stage was independently measurable.
- Constraint reinterpretation requests ("None of those describe the
  intent") → the user restates the constraint in operational terms
  (per-stage ≥30% correct-route share, fallthroughs fine, chain
  succeeds 100%); encode the restated form, not the original prose,
  and keep fixing/testing rather than waiting.
- Direct environment orders ("fix homebrew", "kill the 8090 service
  and spawn your own") authorize that repair class for the session —
  act immediately, verify, and report what changed.

## Harness mechanics that worked (tools/classifier-eval/eval_harness.py)

- Embedding disk cache: ~/.meept/classifier-eval-cache/<model|instruction-hash>/<text-hash>.npy.
  Threshold sweeps then run offline in-process over cached vectors — never re-embed.
- Fold assignment persisted to a TRACKED file (fold-assignment.json): the
  seed-42 5-fold split IS campaign state. Silent reassignment invalidates
  every cross-iteration comparison. New cases get hash-derived folds;
  existing folds never move.
- Dedup guard for harvested cases: reject cosine > 0.95 to any existing case
  (same embedder).
- OOD handling (two bugs worth remembering): OOD cases must be EXCLUDED
  from the train index — the production gate has no OOD class, so included
  OOD cases vote "OOD" unanimously and never abstain. And pooling must
  count a skipped OOD row as an abstain, else OOD-R reads 0% with 0 abstains.
- Compound inputs: gold label is abstain, never one half-intent.
- Mechanical sweeps (threshold grids, head families) run in-process over the
  cache; dispatch subagents only for judgment work (harvest authoring,
  misclassification audits).

## Fine-tune failure diagnosis (iter 14 → 15 — the headline lesson)

Symptom: trained classifier head with loss pinned at ln(K) (= uniform
guessing over K classes), test confidence uniform 1/K, forced accuracy =
chance, zero routes at every threshold.
Root cause: ONE learning rate (2e-5, sized for the pretrained backbone)
applied to a freshly-initialized linear head. AdamW at 2e-5 moves a
zero-init head ~7.6e-4 over ~38 steps — ~50x underdose vs the ~1e-3 a
fresh head needs. Research confirmation: pytorch/pytorch#82707 (MPS BERT
training correctness bugs incl. infinite loss), AnswerDotAI GLUE notebook
(lr 8e-5 for FULL fine-tune), ModernBERT issue #225 (small-task fine-tunes
from base underperform; the paper's RTE/MRPC checkpoints start from MNLI).
Fix: head lr 1e-3, backbone frozen (or much smaller lr), train on CPU
(MPS BERT training kernels are a documented hazard), 30 epochs,
class-balanced CrossEntropyLoss.
Diagnostic first: a linear probe at proper lr cheaply proves/disproves
feature quality before any backbone fine-tune. Data was fine; the
technique was not.

## Calibration for small-data K-class softmax

Fixed tau (0.7-0.9) is structurally wrong: max softmax with K=12 classes
and ~200 examples tops out ~0.2 even when correct. Use train-side
QUANTILE tau: tau = quantile(max-softmax on train predictions, 1-q); q
directly controls route share. Train the head per fold to avoid leakage.

## Cascade design (user architecture: cheapest-first, aggregate objective)

User directive verbatim intent: not one stage fixing everything — a
cheapest-first cascade with aggregate superior accuracy. Stage A:
embedding + centroid margin gate (microseconds). Stage B: frozen embedder
+ trained linear head (SetFit recipe; milliseconds, CPU). Stage C: the
production LLM chain, MODELED at its measured corpus accuracy (86.8%) —
it always answers, so cascade coverage is 100% and E2E = total system
accuracy. Key result shape: stage-B rescue at ~90% precision beats the
86.8% chain call it replaces, so letting B route MORE can raise E2E even
as global precision drops. Per-stage precision floors (A >= 97%, B >= 90%)
are the enforceable form of the "no confident-wrong stage" invariant; a
global 97% precision bar is unreachable by construction once the chain is
inside the cascade.

## Silver-label replay validation (the reality check)

Harvest real transcripts (harvest_hermes.py scans ~/.hermes/sessions/*.json,
pattern heuristics + explicit OOD filters, e.g. doc-writing is not "code";
hermes.db itself may be EMPTY — the JSON session files are the store).
Keep the verbatim corpus UNTRACKED (user directive: private text OK if
gitignored). Labels are silver — never mixed into headline gold P/C.
Validate models-trained-on-gold against held-out silver. Finding: synthetic
E2E does NOT transfer (92.8% -> 84.7%) when the real message mix contains
intents the taxonomy lacks (plan-execution, document writing). The fix is
corpus/taxonomy expansion, not gate tuning. Wiring gate: no daemon
enablement until silver accuracy exceeds the chain baseline with margin.

Silver expansion loop (iter 17→18): dispatch a leaf to author cases
against the MISSED shapes with explicit labeling rules (plan-EXECUTION
of an existing plan = code, not plan; doc-writing = code only if it
produces a tracked artifact; balanced multi-intent = compound abstain),
a splice MARKER in the corpus file (leaf writes a scratch file,
orchestrator splices — avoids two writers), dedup-guard, then PER-MISS
replay: rerun only the known silver misses through the retrained gate.
Per-miss replay shows what pooled numbers hide — after wave 4 a
confident wrong ("implement the plan using subagents" → platform)
became a CORRECT ABSTAIN (margin 0.018 < 0.030) while aggregate E2E
stayed flat. And when silver accuracy stays flat after a targeted
wave, the measurement is likely LABEL-limited (two of three "misses"
were label-defensible either way): hand-adjudicate the silver labels
before authoring more anchors.

User-constraint mapping for cascades: the user's actual intent was
"each stage ≥30% correct successful classification share, fallthroughs
acceptable, the whole chain succeeds at 100%" — per-stage route-share
floors with the chain as the guaranteed backstop, NOT a global
precision percentage. When a written constraint doesn't match the
architecture (a global P≥97% is unreachable once an 86.8% chain is
inside the cascade), present the candidate reinterpretations and ask
rather than picking one.

Double-confidence gate (user's Q1 idea, measured 2026-09-09): requiring
BOTH stage-A margin pass AND stage-B prob > 0.7 collapsed stage B to
zero routes — correct, because B's rescue precision (58-83%) is below
the chain's 86.8% it would replace. Measured 84.56% vs 83.97%
single-gate (simpler AND better). General rule: when a rescue stage's
precision is below the backstop it feeds, gate it with the BACKSTOP's
confidence, not its own — the collapse is the right outcome.

Chunking-vs-classifier scoping (user's Q3, 2026-09-09): when long
executor runs die on budget, ask whether the ORCHESTRATOR should have
chunked the work to the executor's context size before suspecting the
classifier. meept's tactical scheduler caps steps by COUNT (8/phase),
not by estimated token footprint vs the executor model's
context_length — capability-aware allotment is the missing piece and
belongs in the scheduler, not the router. The campaign classifier
(20 iterations) was appropriately sized; the budget failure was an
orchestration gap.

## Campaign-level findings

- Data repair > gate tuning: hand-audited corpus relabels moved E2E +2.0
  points; ALL head/embedder permutations combined moved +1.1. Audit every
  wrong route by hand before touching thresholds.
- Corpus growth places new cases in TEST folds first (adversarial holdout
  rule), so a mechanical E2E dip in the iteration right after a harvest
  wave is expected — judge the precision-compliant frontier, not raw
  iteration-over-iteration E2E.
- Rejected permanently at qwen3-0.6B-4bit EOS pooling: instruction-prefix
  embeddings (lowers kNN precision), k-majority heads (E2E-negative),
  logistic/softmax head (probability ceiling ~0.54), per-class margins
  (complexity without E2E gain), word-count/absolut-sim micro-guards
  (margin rule subsumes them). Centroid + uniform margin 0.030 was the
  stage-A champion.

## Ops gotchas hit this session

- brew python3.14 mlx was a broken half-install (core .so missing from the
  site-packages copy). Working stack: /opt/homebrew/opt/python@3.12 with
  mlx + mlx_lm + transformers. Repair path: brew reinstall mlx && brew
  link --overwrite mlx.
- Empty licenses-only numpy-*.dist-info husk dirs shadow importlib.metadata
  (version("numpy") -> None) and crash transformers' dependency check with
  "Unable to compare versions for numpy>=1.17". Fix: quarantine the husk
  dirs out of site-packages (no formula owned them).
- Port already bound: an embed server from a prior session can still hold
  :8090 — lsof -nP -iTCP:<port> -sTCP:LISTEN before spawning; kill the
  stale PID only after confirming what it is.
- Pre-commit ascii hook: intentional non-English test data (Japanese OOD
  cases) needs an ALLOWLIST entry in .githooks/pre-commit-ascii.
- A blanket `results/` gitignore entry hides campaign evidence; un-ignore
  via negation for the eval tool's results dir, and TRACK the fold
  assignment file — it is state, not output.
- Commit campaign evidence (results/iter-N/) in the SAME commit as the
  log rows that cite it. Untracked evidence dirs make the iteration
  history non-reconstructible from git alone (a later audit had to
  write an EVIDENCE-STATUS.md manifest of untracked artifacts).
- Concurrency etiquette in a shared worktree: harvest waves authored by
  subagents go to a scratch file that the orchestrator splices with an
  explicit-path commit — sibling sessions had large in-flight Go WIP
  in the same tree, and explicit pathspecs kept the campaign commit
  from sweeping it.
- Score probabilistic stages (an "always answers at accuracy p" LLM
  stage) DETERMINISTICALLY: each case adds exactly p to the correct
  count. A sampled draw (`random() < p`) let ±1σ luck (98/109 = 89.9%
  realized on p=0.868) flip a "FAILS the bar" into a committed "CLEARS
  bar" headline — withdrawn by recomputing from per-stage route counts
  (E2E is linear in them; a hand-check is one multiplication per
  stage). Also confirmed by silver replay: the corrected synthetic
  verdict did not transfer to real traffic anyway.
- Campaign evidence must be committed in the same commit as the log
  rows that cite it. An untracked `results/iter-N/` dir makes the
  iteration history non-reconstructible from git alone (an audit later
  had to write an EVIDENCE-STATUS.md manifest of untracked artifacts).
