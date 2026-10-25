# Verification-Leaf Pattern (E2E Acceptance Leaves)

The last leaf of a tree is often a verification leaf: run the e2e suite,
prove the fix chain works end-to-end. Two meept trees (chat-dispatch-ux
leaf 10, session-aware-intent-gate leaf 03) produced these patterns.

## 1. The STOP clause is the leaf's most important feature

A verification leaf that can weaken its own assertions to pass is worse
than no leaf. The leaf must say: "If <core assertion> FAILs, STOP and
report verbatim — do NOT touch code, do NOT weaken the assertion." The
orchestrator decides re-dispatch. Both meept verification leaves
invoked this clause correctly, and both times it surfaced REAL
findings (a stale-script failure misattributed to a provider; a
pre-existing dispatcher ambiguity-gate short-circuit).

The STOP report shape: run summaries verbatim + the failing reply text
+ daemon.log path (--keep preserves the scratch world) + root-cause
evidence if gathered + explicit "leaves 01/02 hold — culprit is X".

## 2. `--keep` + sqlite forensics

Verification leaves run against a scratch daemon (temp state dir).
`--keep` preserves the workdir, which lets the leaf (or orchestrator)
prove/disprove root causes from the scratch DBs directly:
- sessions.db: was the exchange mirrored? (session_messages row count)
- state/tasks.db: did the task/step carry the expected Result text?
Worked example: session-continuity leaf 03 disproved "leaves 01/02
don't work" via `SELECT count(*) FROM session_messages WHERE
session_id=...` — the mirror held; the real blocker was upstream.

## 3. Honesty semantics for provider flakiness

Free-tier providers 429 intermittently. Rules:
- A SKIP on the target assertion does NOT satisfy a verification leaf.
  Wait 2-5 minutes, re-run. Only provider-available runs count.
- Never report a green run that included a skipped target assertion as
  "A5 PASS" — report it as "SKIP (provider), not satisfied."
- Distinguish degraded-window failures (fallback model produced roster
  dumps / no file) from code failures: check the daemon log for which
  model served each turn.

## 4. Stale concurrent runs

If a background e2e run completes AFTER the script it ran was patched,
its result is stale. Note it, extract any durable signal (e.g. it
independently caught a nondeterministic leak), but do not act on its
FAIL as if current. Check the run's workdir timestamp against the
script's last edit before triaging.

## 5. Two-runs-green is the reliability bar

Single-pass green on a live-LLM e2e is not proof (model nondeterminism:
one run leaked a roster, the next didn't). Verification leaves that gate
a behavior fix require TWO consecutive provider-available green runs of
the target assertion, reported verbatim.
