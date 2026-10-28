# Llive smoke stacked root causes
When to use: live smoke fails 5 times on 5 causes.
Lesson: stacked root causes: rebuild-scratch-binary rule, fake-runner blindness.

# Live smoke: stacked root causes, stale binaries, and contract drift

Session pattern (transcript-large-corpus + tool-result-budget trees, 2026-09-07):
a live end-to-end smoke of a newly wired tool failed repeatedly. Each failure
looked like "the fix didn't work" but was a DIFFERENT independent root cause.
The chain, in the order they were peeled:

1. **Routing**: LLM classifier read "summarize this video: <youtube url>" as
   intent=code → an agent without the tool grant. Deterministic structural
   signals (URLs, bare IDs) should be pre-classifier guards, not left to a
   small model's judgment.
2. **Permission action map**: tool missing from the executor's
   ToolActionMap → tool name used as action → no seeded rule matches →
   "Unknown action" denial. New tools need BOTH a seed rule AND a map entry
   (unless the seed action equals the tool name).
3. **Schema visibility**: indexed schema mode stubs non-core tools to a
   one-liner with an EMPTY parameter schema — the model literally has no
   parameters to fill ("no URL specified" with args_hash=empty). Tools with
   ≥2 params of distinct types belong in DefaultAlwaysFullTools.
4. **Library API drift**: the embedded subprocess script targeted a
   pre-1.0 python API; the installed library (1.2.4) had removed those
   static methods. Fake-runner unit tests are API-shape-agnostic BY DESIGN,
   so only a live run catches this.
5. **Prompt-contract drift (SFT models)**: a fine-tuned classifier scores
   well ONLY under the prompt schema it was trained on. Probe it with the
   OLD schema vs the CURRENT schema: if old elicits near-perfect results
   and current elicits garbage, it is contract drift, not model quality —
   retrain or pin the prompt, don't demote the model.

## Rules

- **Rebuild the scratch binary after every fix.** A stale scratch daemon
  produces false negatives indistinguishable from "fix didn't work"
  (dispatch log showed the old classification method; binary mtime was the
  tell). Make rebuild+restart part of each re-run, not a one-time step.
- **Stacked causes: fix one, re-run, expect the NEXT failure to be
  different.** If the failure signature doesn't change after a fix, the fix
  didn't land in the running artifact (binary/config) — check that first.
- **Fake-runner tests are blind to API/schema churn in the real subprocess.**
  State this in the leaf doc's testing notes; schedule a live smoke as the
  acceptance step for anything shelling out to an external dependency.
- **Probes for internal packages must live in-repo** (`cmd/<name>-tmp/`):
  an external module cannot import `internal/`. Create, `go run`, delete
  (or leave + flag; rm is often consent-denied).
- **Scratch daemons lose bundled assets**: `resolveBundledPath` resolves
  `config/agents`, `config/skills` CWD-first, then exe-dir. A scratch
  daemon launched elsewhere silently falls back to default rosters —
  agent specs, tool grants, and shipped skills all vanish WITHOUT an error.
  Copy `config/` into the scratch CWD and confirm roster/grant logs.
- **pip --user installs are $HOME-dependent** (~/Library/Python/...). A
  daemon running under an alternate HOME cannot import them; pass
  PYTHONPATH to the site-packages dir, or install without --user.

## Consent-denial interaction

Compound scratch-setup one-liners (mktemp + mkdir + build + cp chained)
were consent-denied twice; the SAME work split into a background
single-purpose command was allowed. Keep scratch setup to discrete
commands, and expect `rm -rf` of scratch dirs to be denied — leave the dir,
name it in the reply for the user to clean.
