# Open-Questions Walkthrough — Worked Recipe


When to use: presenting a tree's OPEN-QUESTIONS.md to the user.
Lesson: mechanical-vs-user bifurcation, 10-or-fewer walkthrough batches, confirm terse answers.
Reference for `hierarchical-planning` Step 6.8. Worked example from the
Rebellion `plans-glm/` session (2026-07-19), where a 12-tree forest produced
~50 open questions; 9 needed user decisions, walked through in one batch.

## Pre-walkthrough gate: brainstorm BEFORE authoring

The walkthrough recipe handles questions that arise AFTER a tree exists.
A cheaper gate exists EARLIER: when the user hands you a feature list and
asks for plans, present a per-item understanding walkthrough FIRST —
what exists in the codebase (verified file:line), what the gap is, your
proposed design — and let the user correct it before ANY tree document
is written. Worked example (meept llm-resilience-forest, 2026-08-31):
five corrections reshaped the forest (per-agent not per-employee
escalation; endpoint-level not per-model timeout granularity; park/resume
for ALL turn types; 402 like 429 but minutes-longer initial timer; LM
Studio as first-class provider) plus requirements no codebase recon
surfaces (full RFC7231 Retry-After; keyword-bucketing 429s so spurious
provider-load 429s never inherit quota-length delays). Reshaping a
written forest costs re-authoring 20 documents; reshaping a walkthrough
costs one reply. Record ratified corrections in a DECISIONS.md sibling
with dated IDs (D#, Q#) that leaves cite.

## When to use

After authoring a plan tree or forest, you have an `OPEN-QUESTIONS.md` with:
- ~15-50 accept-as-default items (you picked a default, just need non-objection)
- ~8-15 user-decision items (genuine forks the user must decide)

Do NOT present all 50. Do NOT silently accept the 15 user-decision ones.

## Recipe

### 1. Bifurcate

Read every open question. Sort into two piles:

- **Mechanical (apply yourself, don't ask):** the spec is authoritative and
  your plan got a value wrong, OR your default is clearly correct given the
  spec. Example: "hill heights" — the GDD ratified primary-source values; your
  plan had stale numbers. Just fix them.
- **User-decision (walk through):** genuine forks with no spec authority.
  Scope cuts, format choices, separate-tree-vs-in-tree, semantic ambiguity.

Report the mechanical batch as "Applied N corrections" — no per-item user
review needed. The user trusts tool-backed verification.

### 2. Format each user-decision question

```
Q# — [one-line title]
- Rec: [your recommendation. User wants extrapolation, not just options.]
- Impact: [what breaks or changes if the decision goes the other way]
- Options: [(a) rec, (b) alt1, (c) alt2 — only when you have real alternatives]
```

Keep each question to ~3-5 lines. The user answers in shorthand:
`"1a 2b 3a 4a 5a 6a 7a 8a 9a"` for all-recs, or overrides individual ones.

### 3. Re-establish technical context for cold artifacts

If a question asks the user to decide between two technical artifacts they
may not recall (a file format, a library, a subsystem), START with 1-3
sentences orienting them:

- What the artifact IS (e.g. "MiniLM-L6-v2 is a sentence-embedding model,
  not a chat LLM")
- What it DOES in the system (3 jobs: NPC memory retrieval, gossip dedup,
  dialogue context)
- Why the format matters (ONNX = in-process; GGUF = subprocess, breaks arch.)

THEN give the rec. This session: asked "GGUF vs ONNX?" cold, user said
"I don't recall the role." Re-established, then user decided confidently.

### 4. Confirm terse answers before executing

User answers to framed blockers may propose a DEEPER change than the frame.

Example (this session): blocker framed as "save schema vs schedule doc —
which 8-needs list wins?" User answered "No hunger, thirst!" This is NOT
picking a source — it CUTS 2 needs entirely, producing a 6-needs model that
aligns with a prior no-starvation decision.

Before editing GDD docs + plan trees, read the interpretation back:
"I read this as cutting HUNGER + THIRST, giving 6 needs: SLEEP, SOCIAL,
WORK, SAFETY, FAITH, DUTY. Confirm?" One confirmation round costs nothing;
cutting the wrong thing across 5 trees costs the session.

meept 2026-08-31 variant: the user's item list contained a cut-off
sentence ("not sure how to resolve this with regards to"). Do NOT guess
the missing half — ask. The completed thought (spurious provider-load 429s;
providers not implementing the HTTP spec consistently) changed the
classification design for an entire tree.

### 5. Batch cap: ≤10 questions per walkthrough

The user can absorb ~10 decisions at once. More than that = fatigue, rushed
answers, mistakes. If you have 15 user-decisions, split into two rounds:
round 1 the 10 most blocking, round 2 the rest after round 1 is applied.

### 6. Apply decisions in parallel where independent

Once the user answers, apply all decisions whose targets don't overlap in one
batch (parallel patches). Serialize only when two decisions touch the same
file (rare). Follow AGENTS.md Rule 1: any GDD edit gets a changelog entry in
the same batch.

## Red flags (don't do these)

- **Don't present 50 questions unsorted.** The user will either batch-accept
  everything (losing real decisions) or tune out.
- **Don't ask "GGUF or ONNX?" without context.** Re-establish the artifact first.
- **Don't execute on a terse answer to a framed blocker without confirming scope.**
- **Don't ask one question at a time** when you have 9 independent decisions —
  batch them so the user can see the whole decision space and weigh tradeoffs.
- **Don't include mechanical corrections in the user walkthrough.** Apply them
  yourself; report the count. User time is for decisions, not confirmations.
- **Don't author trees before the understanding walkthrough** (see the
  pre-walkthrough gate above).
- **Don't trust a partial-scan failure count when delegating scanner fixes**
  (2026-09-05, meept compliance-scanner fix fan-out). The task brief said
  "exactly two failures," the subagent fixed both, and the full re-scan then
  surfaced TWO MORE identical defects in other trees (auxiliary docs missing
  leaf markers). The scanner reports only what it reaches; fix-count from a
  stale brief is never final. Put the terminal condition in the brief, not
  the intermediate count: "fix the named failures, then re-run the FULL scan
  and fix any identical defects it still reports; done = `ALL TREES
  COMPLIANT: True`." Parent verified the subagent's True verdict
  independently (re-ran the scan) before accepting — a subagent's
  self-reported pass is a claim, not evidence.
