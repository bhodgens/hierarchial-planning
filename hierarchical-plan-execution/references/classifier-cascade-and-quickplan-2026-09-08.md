# Classifier-iteration campaign — 3-stage cascade + quickplan (meept, 2026-09-08)

Session: meept branch `classifier-iteration`, 19 iterations. Evidence lives
in-repo: `docs/plans/classifier-iteration/ITERATION-LOG.md` and
`tools/classifier-eval/` (harness: `eval_harness.py`; per-iteration reports
under `tools/classifier-eval/results/iter-N/`). See also
`local-classifier-ab-and-embedding-prefilter-2026-09-06.md` for the prior
A/B round.

## User-directed architecture decisions (durable)

- **3-stage cheap-first cascade, not one stage fixing everything.**
  A = embedding centroid gate (microseconds) → B = ModernBERT linear probe,
  SetFit-style (milliseconds, CPU) → C = production LLM chain (seconds,
  measured 86.8% on the corpus). Objective = AGGREGATE system accuracy:
  a 90%-precision stage is net-positive when it replaces 86.8% chain calls.
  User explicitly rejected (a) per-stage "fix everything" framing and
  (b) reinterpreting the old global-P≥97% constraint — per-stage floors
  (A≥97%, B≥90%) + E2E bar is the accepted framing.
- **quickplan = new intent**: plan + clarify (up-front ONLY — the ambiguity
  gate stays) + execute autonomously, no plan-approval pause. Routes to the
  orchestrator (planning is orchestrator-owned, not the coder's). User
  decision: quickplan is the FINAL FALL-THROUGH after the LLM classifier
  (replaces chat-as-floor). It measured as the largest real-traffic intent
  (42% of the adjudicated replay).
- **Normative taxonomy boundary rules** (user-adjudicated 2026-09-09):
  - review-and-CORRECT (autonomous fixes) = quickplan
  - verdict-only, guaranteed no changes = review
  - execute-existing-plan (any phrasing) = quickplan
  - design-first-then-I-approve = plan
  - one named defect + fix = debug
  - research = survey without testable criteria; analyze = judge vs
    testable criteria ("compare A vs B for our stack")
  - search-verification ("search and make sure it works") = review
  - document edit producing a tracked artifact = code
- Routing doc shipped at `docs/workflows/intent-routing.md` (decision table
  + fall-through guarantee). Review intent routes to coder (findings-only
  contract); look-only reviewer agents are verification gates, not prompt
  destinations.

## Silver-label adjudication workflow (reusable)

1. Harvest user messages from the session transcripts THE USER NAMES
   (Hermes: `~/.hermes/sessions/session_*.json`; user said NOT meept —
   meept not functional yet). Ask data-provenance questions before
   harvesting; the user checks which corpora fed which numbers.
2. Verbatim text is OK ONLY IF the corpus file is gitignored (add the
   explicit path). Keep the harvester script tracked; keep data untracked.
   If a private file gets committed by mistake, `git rm --cached` it and
   note the history exposure for the end-of-campaign squash.
3. Pattern-label as SILVER (never mix into headline P/C — master-plan
   isolation rule). Then generate an adjudication sheet: every case + the
   cascade's second opinion (what A/B/C would do, B confidence) + a blank
   `your label:` line, disagreements sorted first. User labels in one pass
   (48 cases); promote to a gold file (still untracked).
4. Watch for stray commit risk: a private file was added+committed before
   its gitignore line landed; `git rm --cached` and flag the history note.

## Measurement integrity (iter-16 bug — caught in audit; never repeat)

- NEVER score a modeled cascade stage with seeded random draws
  (`np.random.random() < acc`): 109 draws at p=0.868 realized 89.9% (+1σ),
  which alone flipped a go/no-go verdict ("E2E 92.8% clears bar" →
  deterministic 91.44% FAILS the 91.78% bar). Always use deterministic
  expected credit: `correct += n_stage × baseline`;
  E2E = (Σ stage-correct + baseline × chain-n) / total.
- Correction protocol that worked: keep the wrong report unmodified, add
  `results/<iter>-corrected/report.md`, append a CORRECTION section to
  ITERATION-LOG superseding the row (retain the row as history).

## ML: fresh-head fine-tune failure + fix (iters 14-15)

- Symptom: training loss flat at ln(K) (K = #classes), test softmax pinned
  at uniform 1/K, forced accuracy = chance.
- Cause: single lr (2e-5) for backbone AND a freshly initialized linear
  head = ~50× head underdose (AdamW moves a zero-init head ~7.6e-4 over 38
  steps). NOT bad data — features proved informative at the right lr.
- Fix: separate LRs — head 1e-3 (30 epochs, class-balanced CE), backbone
  frozen or much lower; train on CPU (MPS BERT-finetune kernels have
  documented correctness issues — pytorch#82707 family).
- Calibration: max-softmax on K=12-13 classes with ~20 examples/class is
  severely underconfident (ceiling ~0.2). Fixed tau 0.7-0.9 routes NOTHING.
  Use train-side quantile tau (route the top-q fraction by confidence).
- Diagnostic sequence that worked: instrument ONE fold → confirm loss≈ln(K)
  and uniform confidence → linear-probe at head-lr to prove features carry
  signal (60% forced acc vs 8% chance) → quantile calibration.

## Corpus measurement dynamics (recurring patterns)

- New cases land in their TEST fold first: expect a coverage/accuracy dip
  the iteration a wave lands, recovery next iteration. Read frontiers, not
  single-iteration deltas.
- Corpus LABEL quality caps measurable accuracy: when misses look
  boundary-defensible both ways, hand-adjudicate the labels (sheet
  workflow above) before generating more anchor waves.
- Dedup guard for anchor waves: cosine > 0.95 vs existing corpus = reject
  (caught paraphrase dupes at 0.952-0.981).
- Class-boundary collisions (quickplan vs code sharing implement/add/wire
  vocabulary): fix with anchor waves weighted to the collision shapes plus
  orchestration-cue features (subagent/task/wave/leaf/plan.md markers).

## User collaboration notes (this user, this campaign)

- After a dense metrics summary the user asked "explain that again like
  I'm stupid": follow campaign metric talk with a jargon-free
  analogy-based restatement (shower-temperature lr analogy landed well)
  whenever the technical depth ramps.
- User directs research-before-retry: when an experiment fails, research
  the root cause (web sources + instrumented single-fold diagnostic)
  before offering reattempts — don't just list retry options.
- When the user proposes an architecture change mid-campaign ("3 stages,
  not 2", "quickplan as fall-through"), treat it as the new objective and
  restate the decision rules back for confirmation before implementing —
  one round of definition-locking prevented days of misdirected waves.
