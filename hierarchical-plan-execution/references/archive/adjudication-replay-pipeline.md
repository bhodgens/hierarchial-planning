# Aadjudication replay pipeline
When to use: user-adjudicated gold replay of real traffic.
Lesson: the honest accuracy ruler; sheet workflow, disagreements sorted first; ceiling findings are deliverables not failures.

# Adjudication-driven classifier evaluation (quickplan campaign, meept 2026-09-09)

How the 48-case Hermes-transcript replay set was built, adjudicated by
the user, and used as the acceptance ruler — replacing synthetic-only
measurement.

## Why synthetic-only measurement lied

The synthetic corpus measured the cascade at 92.8% E2E; the adjudicated
real-traffic replay measured 79-84%. The gap was 100% distribution:
real traffic had whole intents (quickplan plan-execution, doc-writing)
absent from the synthetic corpus. Synthetic numbers are only valid
within the taxonomy+distribution they were built on; real replays are
the acceptance ruler.

## Harvest → adjudicate → promote pipeline

1. **Harvest** (harvest pattern): scan session transcripts for
   user-role messages, 15-280 chars, skip slash-commands/paste-
   markers/URLs/acknowledgments, label by pattern heuristics (silver).
   Include an OOD filter (e.g. document-writing ≠ code intent).
2. **Verbatim OK only if untracked.** Private transcript text must be
   in a gitignored file (`.local.json5` suffix); the harvester script
   itself IS tracked. Aggregate metrics + miss lists go in tracked
   reports; per-case verbatim text stays local.
3. **Dedup guard on every wave**: reject new cases with cosine > 0.95
   to any existing case (embed once, matrix-multiply, threshold).
4. **Adjudication sheet**: for each case show the message, the silver
   label, what the current cascade would do (per-stage routes +
   confidence), and a blank "your label" line. Sort DISAGREEMENTS
   first. Deliver untracked. User answers keep-or-correct.
5. **Promote**: apply adjudicated labels, mark `silver: false,
   adjudicated: true`, keep the file untracked, and record the
   decision rules as normative (they become the labeling spec).

## Decision-rule capture (the real deliverable)

The user's keep/correct answers encode intent boundaries no pattern
can infer. Capture them as explicit rules with worked examples, e.g.:
"review-and-correct (autonomous) = quickplan, not review";
"research = open survey, analyze = judge against testable criteria".
These rules then drive future anchor authoring AND the daemon's
routing docs.

## Coherence audit before applying

Parse the sheet back, diff adjudicated vs silver labels, and flag:
(a) missing labels, (b) labels that contradict the campaign's own
decision rules (e.g. review-and-fix labeled review), (c) rule
conflicts between cases. Present the 3-item decision list, get
answers, apply, and re-run the acceptance ruler immediately.

## Measured outcome (this campaign)

- Synthetic 92.8% E2E → real-traffic 79-84%: the gap was taxonomy
  absence (quickplan) + label noise, both fixed by adjudication.
- After adjudication the remaining misses were label-defensible
  either way — at that point stop tuning the model and freeze labels.
- Reporting: separate silver table, never mixed into headline P/C
  without explicit promotion (master-plan silver-isolation rule).

## Gotchas hit while running this pipeline

- The tracked corpus gains `//` comment headers and dual layouts
  (categories: vs cases:) as it grows — every tool that parses it
  (centroid builder, harness, sweep scripts) must strip line comments
  and accept both `expected_intent` and `ood: true` compound-abstain
  entries, or it crashes on the newest wave while older waves parse.
- `.gitignore` rules do not untrack already-committed files; untrack
  with `git rm --cached` AND note the text stays in history until the
  branch squash.
- Sheet callbacks: when the user answers with a rule ("research vs
  analyze hinges on testable criteria"), capture it as a normative
  decision-rule line immediately — the next anchor wave authors
  against rules, not against the individual labels.
