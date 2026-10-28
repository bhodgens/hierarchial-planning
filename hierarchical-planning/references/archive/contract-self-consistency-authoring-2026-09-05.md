# Contract Self-Consistency in Pinned Interfaces (2026-09-05)


When to use: pinned interface contracts that cannot satisfy their own state machine.
Lesson: source-anchor verification is necessary but not sufficient; check self-consistency.
Authoring-session lesson from `docs/plans/effect-idempotency/` (meept):
source-anchor verification (every `file:line` grep-verified before pinning)
is NECESSARY but not SUFFICIENT. The task brief's own pinned contract can be
internally incomplete — a spec that could not satisfy its own state machine.

## The failure mode

The external-article protocol required: reconcile every claimed-but-
incomplete effect on resume; auto-retry only when the provider accepts the
same idempotency key; else surface for human reconciliation (CLI `--abandon`
was also pinned). Yet the brief's pinned API had two gaps no amount of
code-verification would catch:

1. **No `payload` storage.** Schema had no payload column, `EffectMeta` no
   Payload field — but reconcile's auto-retry needs the stored request to
   re-execute after a daemon restart. Without it, auto-retry is
   unimplementable, not merely inconvenient.
2. **Unreachable state.** State machine pinned `abandoned` (the CLI
   `--abandon` target) but the pinned Ledger interface had no transition
   INTO it — no method could ever produce that state.

## The rule (add to authoring protocol as Step 7)

After verifying contracts match the CODE, verify contracts match
THEMSELVES: **for each pinned state/behavior, trace the pinned API member
that produces or supports it. If none exists, extend the pinned surface
pre-dispatch and record the deviation as a RESOLVED FORK (R#) in
OPEN-QUESTIONS.md — never silently.** Distinguish resolved forks (R#, with
the fix already applied to the pinned contract) from open questions (Q#,
genuine forks left for the orchestrator/user).

Mechanical check that catches both gap classes before dispatch:

- Enumerate every pinned state constant → for each, name the method(s) that
  create it and that transition out of it.
- Enumerate every pinned behavior ("reconcile auto-retries X") → name the
  data + method that make it possible post-restart.
- For any gap: extend the contract in master.md AND note it in
  OPEN-QUESTIONS.md's resolved-forks table with impact on downstream leaves.

## Why pre-dispatch matters

Both gaps would have surfaced as implementer confusion or deviation reports
in leaf 01/02 (auto-retry impossible; CLI abandon with no target method) —
a review cycle burned per gap, or worse, an implementer silently
reinterpreting the pinned contract and diverging from master.md's pinned
signatures (byte-for-byte rule makes that a conflict).

## Worked example

`docs/plans/effect-idempotency/OPEN-QUESTIONS.md`: resolved forks R3
(payload column + EffectMeta.Payload/EffectRecord.Payload added to Contracts
1/3) and R4 (Abandon(key, reason) + Get(key) added to the pinned Ledger
interface) sit ABOVE open questions Q1-Q6, so implementing agents see which
deviations-from-the-brief are already adjudicated. Companion survey record:
meept-development `references/effect-ledger-plan-survey-2026-09-05.md`
(two wrong task-brief anchors caught by source verification: no push in
`internal/workspace/git_ops.go` per `manager.go:341`; push service lives in
`internal/services`, not `internal/services/push`).
