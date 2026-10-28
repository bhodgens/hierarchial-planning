# Cclassifier observability decisions vs outcomes
When to use: can accuracy improve from logs?.
Lesson: decisions are logged, outcomes are not; improvement is offline-only until both persist.

# Classification accuracy logging — decision-vs-outcome gap (meept, 2026-09-10)

Context: user asked "do we keep details in logs on failures/successes so
the accuracy can be improved?" after the three-door classifier docs were
written. The honest answer shaped a doc section AND an improvement path.
Session record for the meept repo (meept-development reference has the
config gotchas; this file is the observability pattern).

## The pattern: decisions vs outcomes are different data

A classifier pipeline logs DECISIONS cheaply (what was decided, by which
door/stage, with what confidence) but OUTCOMES (was the decision RIGHT)
require either human labels or downstream signals. Conflating them
overstates system quality.

meept's actual state (verified in dispatcher.go):

LOGGED (decisions):
- One structured line per dispatch: agent=, intent_type=, confidence=,
  classification_method= (embedding_prefilter | llm | keyword |
  fallback | short_message_guard | ...) — regression-tracking record
- Aggregate counters in Dispatcher.stats: total_dispatched, by_method,
  by_agent, by_intent, fallback_count; exposed via dispatcher.stats RPC
- Last 100 fallback entries (timestamp, input prefix, method,
  confidence, routed-to) — in-memory, capped, lost on restart

NOT LOGGED (outcomes):
- No right/wrong feedback: a user re-routing ("no, I meant review")
  leaves no correction trace
- No near-miss capture: Door-1 abstentions with margin just under the
  threshold (harvest candidates) only visible in debug logs
- Fallback inputs capped at 100 in-memory

Consequence: accuracy improvement is OFFLINE-ONLY (the campaign loop:
harvest → adjudicate → rebuild → measure), not in-loop.

## The improvement path (documented in the shipped doc)

1. Persist the already-structured dispatch lines to the metrics DB —
   per-door traffic + misroute investigation nearly free.
2. Add a user-correction event (re-route within N turns → negative
   example for the next centroid rebuild).
3. Periodic centroid rebuild from the accumulated log — the build
   script already accepts any corpus file.

## Lesson for future classifier/pipeline work

When asked "can we improve accuracy from logs?", FIRST split the answer
into decisions vs outcomes and audit which exists. "We log everything"
is usually false at the outcome level, and the outcome level is the one
that drives accuracy. A decision-log-only system needs a labeling loop
(human adjudication or downstream signals) before any online learning
claim is honest.

Shipped doc: docs/workflows/classification-architecture.md
(observability section) in the meept repo.
