# Classifier Campaign → QuickPlan Tree: measured findings feeding a plan tree (meept 2026-09-08/09)

Worked example of the full arc: measurement campaign → adjudicated
labels → architecture finding → plan tree whose contracts encode the
finding. The tree (`docs/plans/quickplan-mode/`, meept branch
`classifier-iteration`) is the deliverable; this reference captures the
transferable patterns.

## Campaign → tree pipeline

1. **Measure until the plateau, then identify its CLASS.** 20 iterations
   of cascade measurement plateaued at 83.97% real-traffic accuracy.
   Every residual miss had the same shape: quickplan-labeled messages
   whose text is indistinguishable from code/git ("Implement Tasks 7 and
   8: Add project fields to Session struct"). The signal is SESSION
   STATE (an approved plan exists), not message text — an
   information-theoretic ceiling for per-message classification.
2. **Write the finding into the plan as a contract, not prose.** The
   orchestrator-resolves-at-execution-time design became Contract 6
   (session-state context block, one-way upgrade rule) in the tree's
   master.md. Findings that only live in a report get re-derived wrong
   by the next session; findings frozen as contracts get implemented.
3. **Adjudicated labels beat silver labels before ANY retraining.** 48
   user-adjudicated cases (30 min of user time) converted a noisy
   silver set into a trustworthy ruler and produced 6 normative
   taxonomy rules. Do not iterate against contested labels — each
   iteration's numbers are then meaningless.

## Taxonomy decision rules (normative, from adjudication)

- review-and-CORRECT (autonomous, multi-site) = quickplan
- verdict-only, guaranteed no changes = review
- execute-existing-plan (ANY phrasing) = quickplan (supersedes
  bare-verb vs orchestration-hint split — user ruled #45 = quickplan)
- research (open survey, no testable criteria) vs analyze (judging
  against testable criteria)
- search-verification ("search and make sure it works") = review
- document editing with tracked artifact = code

## Fine-tuning failure → research → fix (the 50× lr underdose)

ModernBERT probe trained flat (loss pinned at ln(12), confidence
uniform 1/12, forced accuracy = chance). Diagnosis path that worked:
reproduce minimal (single fold, instrumented), compute what the loss
WOULD be for uniform output, compare. ln(K) == measured loss ⇒ the head
never learned ⇒ check head learning rate FIRST when head + backbone
share one lr. A fresh linear head needs ~1e-3; backbone-tuned 2e-5 is
a ~50× underdose. Sources: pytorch#82707 (MPS BERT correctness),
AnswerDotAI GLUE notebook hyperparameters, ModernBERT#225 (small-task
from base underperforms — paper checkpoints start from MNLI mid-
checkpoint). Additional calibration finding: max-softmax on many
classes + tiny data tops out far below 1.0 (0.21 at 12 classes) — use
train-side QUANTILE tau, never fixed absolute thresholds.

## Cascade measurement conventions

- Chain stage credit: DETERMINISTIC expected value (count × chain
  accuracy), NEVER a seeded Bernoulli draw — a sampled draw realized
  +3.1pt luck over the true rate and manufactured a false "clears bar"
  verdict (caught in audit, verdict withdrawn, log corrected).
- OOD/intent class accounting: excluded-from-index classes must be
  excluded at BOTH the test loop and the pooling loop or abstain-rate
  reads as 0.0% with 0 abstains.
- Per-message classifier misroutes in a cascade are RECOVERABLE (the
  chain runs afterward) — the aggregate objective, not single-stage
  precision, is the acceptance bar.

## Known measurement traps hit this session

- Baseline numbers in a pre-existing log may be warm-index artifacts
  (iter-0's 14.7% was self-inclusive k=4; not reproducible under any
  held-out protocol). Re-derive before building on them.
- Corpus growth mechanically dips replay accuracy: new cases land in
  TEST folds while their index contribution lags. Read the frontier,
  not iteration-over-iteration deltas.
- gitignored results directories: campaign evidence must either be
  force-added or the ignore rule negated BEFORE the campaign runs —
  retrofitting after 10 iterations loses nothing only if the files are
  still on disk.
- Verbatim transcript corpora: keep UNTRACKED via explicit .gitignore
  entries; if a private file gets committed by mistake, `git rm
  --cached` + note that history rewrite (squash) is the follow-up.
