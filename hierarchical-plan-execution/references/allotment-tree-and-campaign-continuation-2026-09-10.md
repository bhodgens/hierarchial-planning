# Allotment tree + campaign continuation (2026-09-09/10, meept classifier-iteration)

Session-specific detail for the capability-aware allotment tree and the
classifier-campaign continuation (Q1-Q4 decisions, architecture docs).
Durable lessons live in hierarchical-plan-execution SKILL.md sections;
this file is the session record.

## What shipped this session

- Q1-Q4 decision pass (35b3c512): double-confidence gate (user's idea,
  "both stages > 0.7") MEASURED on the 48-case adjudicated gold replay:
  84.56% vs 83.97% current — slightly better AND simpler. The mechanism:
  the probe's 12-class softmax ceiling (~0.21) means B never clears 0.7,
  so the gate collapses to "A routes, rest to chain" — correct while B's
  rescue precision (58-83%) is below the chain's 86.8%. ADOPTED.
- Q3 investigation (user hypothesis: "orchestrator should chunk work to
  fit each agent's context; classifier might be over-engineered").
  Finding: routing already goes through orchestrator (strategic →
  tactical) for plan/quickplan modes; the missing piece is that step
  allotments are COUNT-capped (MaxStepsPerPhase=8) with zero
  context-size awareness. The classifier is NOT the over-engineered
  part. Fix scoped as the allotment tree.
- Allotment tree authored + compliant (05b63ecc): docs/plans/allotment/
  - leaf 01 pure math committed (a4c1744e): AllotmentConfig defaults
    (usableRatio 0.75, reserve 4096, charsPerToken 4, minStepTokens
    512, maxBatchSteps 0), EstimateStepTokens (ceil, floored),
    AllotmentTokens ((contextLimit - reserve) * ratio, floor 0, 0 when
    window unknown), SplitStepsByAllotment (greedy fill preserving plan
    order, oversize step gets own batch, zero allotment = single legacy
    batch), ContinuationDescription ("[continuation k/N] desc").
  - leaf 02 (tactical wiring) dispatched: ContextWindowProvider on
    TacticalScheduler, continuation-step flattening in
    ScheduleReadySteps, PlanRequest.ExecutorModelRef, daemon closure
    from resolver.ResolveRef(ref).ContextLimit.
- Three-door architecture doc (054be4d9):
  docs/workflows/classification-architecture.md — door hierarchy
  diagram, per-door components/resources/timing, failure behavior, and
  the OBSERVABILITY answer: decisions are logged (structured
  "Dispatched request" line: agent/intent_type/confidence/
  classification_method; per-door counters via dispatcher.stats RPC;
  last-100 fallbacks) but OUTCOMES are not (no right/wrong feedback
  loop; accuracy improvement runs offline: harvest → adjudicate →
  rebuild → measure). Improvement path documented: persist dispatch
  lines to metrics DB + user-correction event + periodic centroid
  rebuild.
- intent-routing.md pipeline diagram relabeled to the door model with
  per-door timing/accuracy.

## User answers to park-with-user decisions

- P-constraint reinterpretation: user rejected all three options (a/b/c)
  and gave the real intent: "30%+ correct successful classification per
  stage, fallthroughs acceptable, whole chain succeeds at 100%" —
  i.e. per-stage route-share floors + chain-as-guaranteed-backstop,
  aggregate outcome over per-stage perfection.
- M3 ModernBERT: closed via the research-driven path — iter-14 diverged
  (head-lr underdose), iter-15 retrain worked (91.45%, under bar), raw
  embeddings rejected. M3 measured, not assumed.
- #26/#27 adjudication diffs confirmed intentional; "help me" phrasing
  documented as a quickplan signal in intent-routing.md.

## Session gotchas (environment-specific)

- The smoke daemon lingers (proc on :18096); stale background-exit
  notices from earlier failed launches arrive in a burst minutes later —
  check the live PID before reacting to exit notifications.
- 404-with-auth on every /api/v1 route while /health works =
  transport.http.rest missing/false (daemon.go overwrites the default).
- meept config: hujson quoted keys everywhere; `rest` is a bool;
  `require_auth: false` in scratch configs.
- Background terminal '&' is denied — use terminal(background=true).
