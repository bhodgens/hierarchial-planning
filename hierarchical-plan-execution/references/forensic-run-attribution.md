# Fforensic run attribution
When to use: e2e failures blamed on the provider.
Lesson: read-only forensics on the kept workdir; one case study overturned a 12-run attribution.

# Forensic verification of e2e failure attributions — run 10 case study

Session context: a 12+ run e2e campaign where failures were attributed to
"zai 429 quota degradation." An independent read-only subagent investigation
of ONE workdir overturned that attribution. This reference preserves the
technique and the finding pattern.

## The investigation recipe (what the subagent actually did)

1. Workdir forensics — the script uses `--keep`, so every run leaves
   `<scratch>/daemon.log`, `replies/t1..t4.txt`, `state/*.db`. Read the
   ACTUAL reply files, not the orchestrator's summary of them.
2. sqlite the state DBs:
   - `state/tasks.db`: `SELECT name,state FROM tasks` (did the task even
     get created?), `session_tasks` (was it linked to the session?),
     `task_steps` (did the step produce a Result?)
   - `state/metrics.db dispatch_log`, `state/routing.db
     routing_decisions` — per-turn intent/method/handler rows.
3. Timeline each LLM call from daemon.log: rotation lines
   ("Intent analyzer rotating to next alias candidate", model=...),
   alias-failure records, "Requesting clarification ... ambiguity=X"
   (analyzer returned a VERDICT, not an error), "Dispatched request ...
   classification_method=llm confidence=Y".
4. Distinguish failure classes:
   - transport error / 429 → turn never got a verdict
   - "empty content" → HTTP 200 with empty body (llm.ErrEmptyResponse)
     — a MODEL failure, not a rate limit
   - ambiguity>=0.6 verdict → the model ANSWERED with a misjudgment
   - capabilities/platform dump reply → ROUTER misclassification
     (intent=platform), analyzer may have been fine

## Run 10 finding (the overturned attribution)

- Parent (orchestrator) believed: quota window degraded the provider;
  only one 429 in log; T1 got a canned clarification.
- Artifact truth: T1's reply was the Platform Capabilities dump — the
  ROUTER classified "create a file named hello.txt..." as intent=platform
  confidence=1.0 (LLM classifier served by a weak local model after a
  rotation). Zero 429s in the log; the one 503 recovered via internal
  retry. T2/T3/T4 clarifications were SUCCESSFUL analyzer verdicts
  (0.6/0.9/0.8) from weak fallback models — misjudgments, not errors.
- Lesson: "provider degraded" and "model answered wrongly" look identical
  from the orchestrator seat. Only workdir forensics distinguish them.

## Structural facts worth remembering (meept classifier chain)

- One shared `*llm.Client` serves BOTH the intent analyzer and the LLM
  router; a rotation by one silently re-points the other
  (components.go classifier client → dispatcher.go:366-407 wiring).
- Analyzer has NO per-call timeout; T3 waited ~28s on a slow fallback.
- Alias chain order was weakest-first (1.2B → 8B → glm-4.5-air).
- Keyword fallback would have routed the imperative correctly, but
  fallbacks fire only on FAILURE, never on suspicious success (platform/
  1.0 on an imperative create-file request sailed through).
- Fallback chain when all classifier members fail: 60s cooldown →
  llm_empty_fallback_chat (deliberately skips keyword table) →
  keyword (>=0.3) → semantic → heuristicFallback → chat.

## Verification workflow rule

Before writing a fix against an "observed" failure: dispatch a READ-ONLY
subagent to reconstruct the failure timeline from artifacts (log + sqlite
+ reply files), with explicit instruction "document what the artifacts
show rather than assuming the orchestrator's premise is correct." The
subagent found the premise wrong; a fix written against the wrong premise
would have shipped.

## Epilogue: the forensics dead-ended at the model, so the user's question went to CONFIG history

The run-10 forensics correctly identified "the judge was a weak fallback
model" — but stopped there. The user then asked the right next question:
"why is it using those models for the classifier? It's supposed to be the
specialized LFM2.5 model." `git log -S` on config/models.json5 answered it:
a July 7 runtime-migration commit had (a) demoted the classifier primary
from the 8B to the 1.2B, (b) DELETED the custom SFT fine-tuned classifier
model (`lfm-combined-sft` = lfm2.5-1.2b-combined-serialized-sft, the model
the user remembered selecting) from the chain, and (c) dragged a misleading
"Best overall" accuracy comment onto the new primary. The weights were also
gone from /Volumes/LLMs. Two months of "flaky e2e" were downstream of that
unreviewed ride-along. Full timeline + recipe:
references/config-archaeology.md in this skill. Rule: forensics that
dead-end at "the model is weak" must continue into config/git history —
current config is a survivor of edits, not a record of decisions.
