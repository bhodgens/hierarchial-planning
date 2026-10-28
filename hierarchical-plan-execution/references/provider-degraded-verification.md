# Pprovider degraded verification
When to use: verification during provider quota degradation.
Lesson: symptom signatures, escalating cooldowns, degraded-is-not-green, no assertion weakening.

# Verifying chat-harness fixes when the provider quota-degrades (zai / agnes free tier)

## 2026-09-06 correction: "degradation" includes successful-but-wrong verdicts

The signature list below undercounts one class that run-10 forensics
surfaced: **successful HTTP responses with wrong judgments from weak
fallback models.** No error is logged because no error occurred —
ambiguity=0.8 on a fully concrete create-file instruction, or the router
scoring that same request as intent=platform confidence=1.0 (reply
became a capabilities dump). Signs to check for:

- Earlier `empty content` rotation lines (the alias moved to a weak model),
  then misjudged turns with clean logs
- Alias order weakest-first in config/models.json5 — "failover succeeded"
  often meant "downgraded to a worse judge"
- Shared-client hazard: one `*llm.Client` served analyzer AND router; a
  rotation by one silently re-pointed the other — reconstruct which model
  the CLIENT was on at each call, not which model each component
  "should" use

Full recipe + run-10 case study: references/forensic-run-attribution.md.
Rule of thumb after ~3 consecutive externally-attributed FAILs: dispatch
a read-only forensics subagent on the newest kept workdir before cycling
further.

## Original playbook

## Symptom signature (distinguish from code failure)

- zai: `HTTP 429 code=1302 "Rate limit reached for requests"` persisting
  60-120 minutes (not minutes).
- Classifier alias chain rotations: local LFM2.5-1.2B/8B returning
  "empty content", glm-4.5-air 429ing, 503 "Loading model" from a cold
  llama-cpp runtime.
- Degraded fallback models (1.2B-8B locals) ignore prompt-level rules the
  primary model follows — e.g. a fully concrete instruction ("create a
  file named hello.txt ... containing the word hello ... tell me the full
  path") still scores ambiguity=0.8.

## Diagnosis recipe (before blaming the code)

1. Confirm the binary under test was built AFTER the fix commits
   (`ls -la <scratch>/bin/` vs `git log --format='%h %ci'`).
2. Sqlite the scratch DB: did the precondition actually land?
   (e.g. `SELECT ... FROM session_tasks WHERE session_id=...` — if the
   link row exists and the task is completed, the digest builder had
   material to work with.)
3. Grep daemon.log at the failing turn's timestamp for model rotations —
   identify WHICH model served the failing call.
4. Reproduce the exact SQL by hand against the kept scratch DB.
5. The same wording that fails during an outage gets
   `intent=code confidence=0.9` when the provider is healthy — wording
   wasn't the variable, provider health was.

## Policy

- Degraded run = neither green nor STOP. Escalating cooldowns between
  runs: 10 → 15 → 25 min. Long quota windows need long waits; short
  retries burn attempts.
- A verifier that returns quota-text as the reply is itself evidence the
  quota-honesty fix works (user sees real harness state, not a fake
  apology) — log it as a positive signal even while A-style assertions
  remain unmet.
- If the analyzer/classifier is served by weak fallback models during
  outages, they will ignore prompt-level rules (LOW-ambiguity
  instructions). That is a provider-stability problem; a follow-up
  "prefer a stronger model for this seam" is the fix, not rewriting the
  rules text.
- Do not weaken assertions to force green. The assertion is the
  regression net for the next session.

## 2026-09-05 A5 verification wave (worked example)

6 runs across ~2.5h, every failure attributed to provider degradation:
run-to-run variation included quota text as reply (leaf-06 fix working),
a degraded-model clarification, and one roster leak with atypical shape
(re-evaluate the reply guard after provider stabilizes if it repeats).
Mechanism layer fully verified by unit + wire-level tests (httptest
capture server proving [Recent session activity] block reaches the wire
and contextless requests stay byte-identical). Acceptance runs remained
IN_PROGRESS pending a stable provider window, honestly recorded in the
tracking table with per-run evidence.

## Provider windows open on their own schedule

Provider windows open on their own schedule (overnight); a bounded number of
escalating cooldowns beats infinite short cycles, and after ~3
same-attribution failures the attribution itself must be audited (see
references/forensic-run-attribution.md).
