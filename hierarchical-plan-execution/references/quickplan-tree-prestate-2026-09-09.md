# QuickPlan tree — pre-implementation state (meept 2026-09-09)

Tree at `docs/plans/quickplan-mode/` (committed 049afe73): master.md +
4 leaves. Compliance scan: ALL TREES COMPLIANT. Execution NOT started —
dispatch gate was reached at session end; wave A (leaf 01) is the next
action.

## What the tree implements (contracts frozen in master.md)

1. **Contract 1 — intent constant**: `IntentQuickPlan IntentType =
   "quickplan"`; SuggestedMode → "quick_plan"; DefaultAgent →
   "orchestrator"; Category → defer; RequiresPlanning/ShouldCreateTask
   → true.
2. **Contract 2 — mode**: `"quick_plan"` in validModes; suggestMode
   returns it BEFORE the short-input downgrade (the explicit execution
   phrasing IS the signal — never downgraded to direct).
3. **Contract 3 — orchestration-cue regex** (`quickplan_cue.go`,
   `QuickPlanCuePattern`): subagent/task-N/wave/leaf/plan.md/handoff/
   "and correct them"/"then run"/autonomy markers. Full verbatim
   pattern pinned in master.md AND validated empirically in
   `tools/classifier-eval/iter20c_sweep.py` (ORCH regex) — copy from
   either; both are frozen.
4. **Contract 4 — ambiguity interaction**: the gate fires BEFORE
   execution; pending-clarification state gains PendingMode so the
   answer resumes with mode=quick_plan (clarification completes the
   plan, never downgrades to chat).
5. **Contract 5 — final fallback swap**: classifyIntent Step 5 →
   IntentQuickPlan/orchestrator/confidence 0.3/method "fallback".
   The short/simple guard EARLIER still routes to chat (regression-
   protected by test).
6. **Contract 6 — session-state override**: orchestrator context block
   (active plan, open tasks, prior waves) + prompt instruction:
   session evidence upgrades code/git → quickplan ONE-WAY; absence
   never downgrades an explicit quickplan.
7. **Contract 7 — prefilter index**: classes are data; the Go change
   is only the cue guard on quickplan votes (leaf 03).

## Leaf map + hazards

- 01-intent-type (~45K, wave A, alone): five switches in
  intent.go + test. Greps other exhaustive intent tables and adds
  quickplan or a TODO(quickplan) note (unclear semantics → exclude,
  don't guess).
- 02-dispatcher-routing (~85K, wave B): validModes, suggestMode early
  return, fallback swap, PendingMode resume, session-state context
  block in the orchestrator prompt. Pins current line numbers:
  validModes ~1157, suggestMode :1241, fallback ~1143-1153,
  ambiguity gate :830, buildClarificationResult :1380,
  clearPendingClarification :1509, short/simple guard ~961 (DO NOT
  change). RE-VERIFY line numbers at dispatch — sibling WIP was live
  in dispatcher.go at authoring time.
- 03-prefilter-index (~50K, wave B, parallel with 02): cue file +
  vote() guard (signature change vote(vec) → vote(vec, input); one
  call site) + centroid-builder verification via `--sweep` (do NOT
  write the store — deployment action). Cue-positive/cue-negative
  table tests from the adjudication rules.
- 04-docs (~35K, wave C): intent-routing.md QuickPlan section,
  classifier-prefilter.md cue-guard note, AGENTS.md review (likely
  no-op — record the check), fallback-claim sweep across user-facing
  docs only.

## Validation chain (Integration Test Plan, from master.md)

Full suite `-p 2` → analyzers → prefilter smoke with quickplan-shaped
message (no clarification loop, no approval pause, execution report) →
ambiguity smoke ("fix it" clarifies; answer resumes quickplan) →
fallback smoke (gibberish ≥ short-guard length → quickplan) →
48-case adjudicated gold replay ≥ 86.8% system accuracy.

## Out of scope (recorded in master.md Notes)

- Centroid-champion head wiring (k=5-unanimity ships today; centroid
  margin 0.030 is the campaign champion) — that is the classifier-
  iteration campaign's M4 deliverable, separate from this tree.
- Programmatic session-tracker → classifier feature integration
  (deeper than the orchestrator-prompt block) — follow-up if quickplan
  traffic demands it.
- History exposure note: adjudication sheet (verbatim transcript text)
  was briefly committed at 59efdb1d and untracked at 7eada6dd; text
  remains in branch history until the planned end-of-campaign squash.
