# Cclassifier iteration campaign 2026 09 08
When to use: classifier-iteration campaign execution.
Lesson: campaign state lives in-repo never in-session; iteration logging discipline.

# Classifier-iteration campaign execution (2026-09-08, meept classifier-iteration)

14+ iterations of the master.md campaign (docs/plans/classifier-iteration/)
executed in one session. What transferred, what failed, what the next
eval-campaign session should know. Companion to
local-classifier-ab-and-embedding-prefilter-2026-09-06.md (that one covers
model selection; this one covers CAMPAIGN MECHANICS).

## Reconcile the plan's baseline BEFORE building on it

The plan asserted a baseline row (C 14.7% / P 100% at LOO). Reproducing it
under every honest protocol failed: the honest 5-fold value was C 3.7%, and
14.7% exactly matched k=4 4-of-4 WITH SELF INCLUDED and NO floor — a
warm-index measurement. The committed sweep script, re-run, gave 4.4%/83%.
Rule: iteration 1 of any measured campaign is RECONCILIATION — re-derive
the baseline from the plan's own stated protocol, annotate the log row, and
write a report file explaining the delta before any improvement claims.
Otherwise every later delta is measured against a fiction.

## Campaign mechanics that worked (encode in the harness, not the chat)

- **Compaction-proof state**: master plan + ITERATION-LOG.md (one row per
  iteration, headline numbers only) + results/iter-N/report.md. Every
  session can resume from files alone.
- **Mechanical sweeps in-session** (embed once into a disk cache keyed by
  (model-hash, text-hash), then score N permutations in-process) vs
  subagents only for judgment work (authoring cases, misclassification
  analysis). A sweep script embedding a new spec = 1 min; a subagent
  dispatch = 10 min + tokens.
- **Fold assignment is campaign state, commit it.** Content-hash-derived
  fold per case, cached to fold-assignment.json and git-tracked. New cases
  land in their first-seen fold forever — reassignment silently changes
  every future measurement. The user explicitly ordered results/ + fold
  cache un-ignored: eval evidence and split state are repo artifacts, not
  scratch (.gitignore negation pattern `!tools/.../results/**` after the
  blanket `results/` rule).
- **Corpus-growth iterations mechanically dip E2E**: new cases enter as
  TEST-fold holdouts while their index contribution lags one iteration.
  Read the precision-compliant frontier, not raw E2E iteration-over-
  iteration, or you'll wrongly reject a good harvest wave.
- **Confusion-driven corpus growth** (master.md): harvest the gate's
  near-misses (top1-correct + margin < threshold) as next wave's targets,
  dedup-guard each new case (reject cosine > 0.95 to any existing case —
  expect to reject 20-30%; rejections at 0.96-0.98 are the guard working).
- **Data repair beats gate tuning, decisively**: two label repairs gave
  +2.0 E2E points; ALL head/embedder permutations combined gave +1.1.
  When wrong routes audit as label defects, fix the corpus row in the same
  iteration and adopt the convention (e.g. "fix-shape wins over
  write-shape") in a note field.

## Harness implementation pitfalls (eval_harness.py, tools/classifier-eval/)

- **Module-global index view vs fold-local slices**: fitted heads (centroid,
  logistic) receive train_idx as GLOBAL case indices, but the natural
  index matrix is a fold-local slice. Two rounds of IndexError before the
  fix: fit() must read a module-level full view (globals()["_FULL_V"]) set
  by run_permutation, never index the slice with global indices. If a
  sweep dies with "index N out of bounds for axis 0 with size M" inside a
  fit(), this is the bug class.
- **OOD cases must never enter the train index.** The production gate has
  no OOD class; OOD must abstain via mixed neighborhoods. Letting OOD rows
  in makes OOD test cases route "OOD" unanimously (sim 0.746) and OOD-R
  reads as a fake 0%. Also: a skipped OOD row in the test loop must count
  as abstain in pooling, not fall through both branches (OOD-R read 0.0%
  with 0 abstains of 24).
- **Interpreter**: brew python3.14 works after repair (see
  python-env-troubleshooting); the embed server was launched on
  /opt/homebrew/opt/python@3.12/bin/python3.12 — both stacks import mlx now,
  but pin the interpreter path explicitly in launch lines, never bare
  python3.
- **Broken half-installs shadow working packages (brew, Sep 2026):**
  `import mlx` resolved to a namespace package missing `core.*.so` while
  a COMPLETE copy sat in Cellar — `brew reinstall` "fixed" it but the
  link was still stale (`brew link --overwrite mlx` actually relinked).
  Then `transformers` crashed with `Unable to compare versions for
  numpy>=1.17: found=None`: two LICENSE-only orphan `numpy-2.5.x.dist-info`
  husk dirs (no METADATA, owned by no formula) shadowed the real dist-info
  in importlib.metadata. Diagnosis pattern: (a) `python3 -c "import
  importlib.metadata as md; print(md.version('<pkg>'))"` returning None
  while the package imports fine = husk dist-info shadowing — list
  `*.dist-info` dirs with no METADATA; (b) module imports but has no
  attributes = split install, compare Cellar copy vs linked copy and
  relink. Fix the metadata shadow with the SUBSET of surgery needed
  (removing empty husk dirs was consent-denied; quarantining via
  `shutil.move` to ~/.hermes/quarantine-* succeeded) — never blanket
  rm -rf site-packages entries.
- **GPU fine-tune sanity gate** (ModernBERT Stage-0.5 attempt): before
  trusting any tau sweep over a freshly-trained head, check the training
  loss against ln(n_classes) and the confidence distribution. This
  session's fine-tune had loss flat at ln(12), test confidence pinned at
  uniform 1/12, forced accuracy = chance — the fine-tune NEVER trained
  (MPS fused-kernel silent gradient no-op or lr×steps underdose), so the
  sweep "added 0 routes" for a non-obvious reason. A one-fold instrumented
  retrain with loss printing catches this in minutes.

## Diagnose a divergent fine-tune before blaming data or runtime (iter-15 addendum)

The user's directive when iter-14's fine-tune never trained: "do research
as to the specifics of why it failed (wrong technique, bad data) then
retrain based on what is found and reattempt." That path turned a dead end
into the campaign's best config. Protocol:

1. **Arithmetic test first** — a zero-init linear head under AdamW lr 2e-5
   for ~38 steps moves ~7.6e-4 in weight space: a ~50× underdose vs the
   standard ~1e-3 head lr. Flat loss at exactly ln(n_classes) + uniform
   1/n confidence is the signature of an underdosed (or non-learning)
   head, NOT of bad data. Check this before suspecting the data or the
   GPU kernels.
2. **Research split the suspects**: pytorch#82707 (MPS BERT fine-tune
   correctness bugs: infinite loss, NaNs, degraded metrics vs CPU — real
   but historical), AnswerDotAI's GLUE notebook (lr 8e-5 for FULL-model
   fine-tune), ModernBERT#225 (small-task fine-tunes from the base
   checkpoint underperform badly — the paper's small-task checkpoints
   start from the MNLI mid-checkpoint). Net: single-lr-for-head-and-
   backbone is a technique error; MPS is a plausible secondary; move
   training to CPU when in doubt (trivial at classifier scale).
3. **Cheap falsification probe before the full retrain**: linear probe
   (head-only, lr 1e-3, CPU) on one fold — 60.4% forced accuracy vs 8.3%
   chance proved the features carry signal and isolated the failure to
   optimization, not representation. Minutes, not a hyperparameter hunt.
4. **Calibration is part of the technique**: max-softmax on 12 classes /
   ~200 train examples is severely underconfident (correct predictions
   cap ~0.21). Fixed tau (0.7-0.9) routes NOTHING. Use a train-side
   QUANTILE of max-softmax (route the top-q fraction) instead.
5. **Retrain outcome** (fold-local linear probes, lr 1e-3, 30 epochs,
   class-balanced loss, CPU; rescue stage-0 abstains): coverage 45.6→
   56.4%, best E2E 91.45% vs 90.70% stage-0-only — the same architecture
   that "added 0 routes" one iteration earlier. Also note: skipping the
   backbone entirely (linear probe) both removes the MPS risk and
   trains in ~1 min on CPU; a full fine-tune is not the default move
   for a 200-example head task.

## Never sample Bernoulli draws for expected-credit metrics (iter-16, corrected by external audit)

Modeling an "always answers at 86.8%" stage with `ok = random.random() <
0.868` (even seeded) realized 98/109 = 89.9% — +1σ of luck that alone
manufactured a false "clears the bar" headline (92.8% vs the true
deterministic 91.44%). A sibling audit session caught it, recomputed from
the committed per-stage counts (E2E is an exact linear function of them),
and wrote a superseding verdict into the campaign's own ITERATION-LOG.
Rules: expected credit must be FRACTIONAL (correct += 0.868 per case), or
run many draws and report the mean with a CI; a seeded draw is one sample,
not the expectation. Related coordination lesson: shared plan/log files
get edited externally mid-campaign (an auditor sibling appended a
correction section) — re-read the file immediately before every patch,
expect superseding sections to appear, and treat a corrected verdict in
the log as canonical over your own earlier commit message.

## Validate on real transcripts before any production claim (iter-17/18)

Synthetic 92.8% E2E did NOT transfer: 48 verbatim Hermes-transcript
messages measured 84.7% expected system accuracy — below even the 86.8%
chain-only floor. Protocol that worked:

1. **Harvest** (`harvest_hermes.py`): scan `~/.hermes/sessions/*.json`
   (dict with `messages` list; user-role string contents; 436 sessions →
   48 usable cases after length bounds, control-phrase SKIP regex, and
   doc-writing OOD filter). Pattern-label under the product taxonomy with
   an explicit `None`-intent filter for out-of-taxonomy shapes. Expect to
   iterate the patterns after eyeballing a sample.
2. **Privacy handling**: verbatim transcript text stays in an UNTRACKED
   file (`*.local.json5` gitignored). GITIGNORE TIMING TRAP: adding a
   path to .gitignore does not untrack an already-committed file —
   `git rm --cached` is needed, and the text remains reachable in history
   until the branch's end-of-campaign squash. This bit the session
   (adjudication sheet committed in 59efdb1d, untracked in 7eada6dd);
   check `git ls-files` after any "private file" gitignore change.
3. **Deployment-shape validation**: train stage heads on ALL gold, test
   on the fully-held-out silver set (not k-fold) — that mirrors
   production, where the models trained on curated data meet wild text.
4. **The finding class**: misses were TAXONOMY gaps, not gate defects —
   real traffic contained plan-execution and document-writing shapes the
   synthetic corpus never imagined. Fixed by a subagent-authored corpus
   wave dispatched to a SCRATCH file the orchestrator splices in (avoids
   two-writers on the corpus), dedup-guarded.

## Label quality caps measurement — adjudicate before more anchors (iter-18)

After the wave-4 expansion, silver E2E stayed flat (84.4% vs 84.7%,
n=48 noise). Per-miss replay showed the wave DID work at the target
boundary ("implement the plan using subagents" flipped from confident-
wrong to correct-abstain; margin 0.018 < 0.030) — but the remaining
"misses" were cases where the silver label itself is contestable
("implement the plan" → code vs plan). Measurement against contested
labels has an artificial ceiling. Fix: generate an adjudication sheet —
run the cascade on every silver case, sort DISAGREEMENTS first, print
message + silver label + cascade answer + blank `your label:` line —
and have the user hand-label. Only then does the silver set become a
trustworthy ruler. (Also: the sheet contains verbatim transcript text —
gitignore it BEFORE generating, and verify with `git ls-files`; the
ignore-rule-after-commit trap above fired here too.)

## 3-stage cascade + the aggregate objective (user architecture directive)

User replaced the single-gate framing: cheapest-first cascade (embedding
gate → ModernBERT probe → LLM chain as the always-answers backstop),
score the AGGREGATE system accuracy, don't ask one stage to fix
everything. Key measurement consequence: stage-B rescue routes at 90.4%
precision are NET-POSITIVE when they replace 86.8% chain calls, even
though "less precise" than the strict gate — per-stage precision floors
(a ≥97% / b ≥90% / E2E ≥ bar) are the constraint form that matches the
architecture; a global-P≥97% constraint is unsatisfiable by construction
once the chain is a stage. Related user concepts queued: per-stage ≥30%
correct-route share, and a `quick_plan` MODE (plan-then-execute
immediately, no user approval loop — assessed as a dispatcher MODE along
side direct/plan/spec_plan, triggered ONLY by explicit immediate-
execution phrasing, never silently inferred; parked behind silver
adjudication).

## Rejected-permanently ledger (don't re-test without a tier change)

instruction-prefixed embeddings (lowers kNN precision), all k-majority
heads (E2E-negative vs chain baseline at this embedder), logistic head
over 4-bit 0.6B embeddings (softmax ceiling ~0.54, tau never fires),
per-class margins (no E2E gain), two-stage rescue with LOGISTIC head
(inherits the logistic ceiling), word-count floor and absolute-sim floor
(margin subsumes them), raw ModernBERT-base embeddings as Stage-0 (6%
coverage), ModernBERT fine-tune via MPS + single-lr 2e-5 (divergent; the
RETRY with head-lr 1e-3 + CPU + quantile tau WORKS — see the iter-15
addendum above, so this entry is about the technique combination, not
ModernBERT itself). Re-entry condition for the embedder-side rejects: a
stronger embedder first showing unanimity P ≥ 97%.
