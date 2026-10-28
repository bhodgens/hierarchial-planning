# Lleaf spec gate polarity
When to use: gate polarity vs producer predicate.
Lesson: authoring pitfall: selection predicate inversion.

# Authoring pitfall: gate polarity vs the producer's selection predicate

(meept skill-evolver tree leaf 04, 2026-09-01)

## The bug class

A plan leaf specified a gate with one comparison direction while the
upstream producer that FEEDS the gate selects with the opposite direction:

- Producer: `GetLowPerformers(threshold, min)` selects skills with
  `effectiveness < threshold` (they are candidates FOR pruning).
- Leaf contract (wrong): "archive passes when effectiveness >= threshold."
- Literal implementation result: every producer-selected candidate is
  gate-rejected — the pipeline the leaf was meant to fix could never fire
  in production. Internally consistent, fully tested, and dead on arrival.

The implementer implemented it literally (correct behavior for an
implementer) and flagged the consequence — which is exactly right. The
defect was in the ORCHESTRATOR's leaf authoring, not the implementation.

## The rule for gate/verify specs

When a gate re-verifies or double-checks a selection made elsewhere, the
gate's predicate must be DERIVED from the selector's, not written from the
author's mental model of "what a good candidate looks like":

1. Find the producer's actual predicate (read the query/selector).
2. Decide the gate's job: re-confirm the selection (gate predicate mirrors
   the selector — catches stale stats between select and act) or vet
   quality beyond it (gate adds NEW criteria).
3. State the polarity explicitly in the leaf contract with the producer's
   file:line: "selection is effectiveness < T (usage.go:NNN); the gate
   RE-VERIFIES: reject when effectiveness >= T (recovered since selection)."
4. The canonical accept case in the test table is "still matches the
   selector"; the canonical reject case is "stopped matching the selector."

## Authoring checklist addition

Before dispatching any leaf whose contract contains >= or <:
grep the producer's selection predicate and put BOTH predicates side by
side in the leaf doc. If they point the same direction for "pass", stop
and re-derive — a confirm-gate that passes everything the selector picked
is a no-op, and one that passes the opposite set has killed the pipeline.

## Test-fixture corollary (hit twice in the same tree)

Downstream evolver tests that need an archive ACCEPTED must fixture a genuine
low performer (eff below threshold, injections >= min). Tests that need a
REJECTION can use either a recovered fixture (reject reason "recovered") or
an under-injected fixture (reason "injection") — pick the one matching the
behavior under test, and name the polarity in the fixture comment. When a
polarity correction lands AFTER fixtures were written for the wrong
direction, grep the test file for the old-direction fixtures: they will now
fail with the gate rejecting their "should-pass" cases (three fixture flips
were needed here), and a test named like a rejection path
(TestEvolver_VerifierRejects_NoArchive) may become the natural home for a
genuine gate-rejection exercise.

## Credit

Detected by the implementer subagent post-implementation ("spec-level
issue for the orchestrator"), which is the system working — but the
two-grep check at authoring time costs minutes and the post-implementation
discovery cost a completed-leaf revert cycle.
