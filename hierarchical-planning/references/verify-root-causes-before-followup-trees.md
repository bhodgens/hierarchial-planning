# Verifying Subagent Root-Cause Reports Before Follow-Up Trees

When an e2e or integration leaf returns FAIL and the implementing subagent
reports a root cause, treat the report as a HYPOTHESIS. Verify against
source before authoring the follow-up tree — wrong root causes produce
wrong trees that burn a full execution cycle.

## The pattern that worked (session-continuity, 2026-09-04)

Leaf 03 (e2e) reported: "intent-analyzer ambiguity gate blocks A5 — canned
clarification fires before the chat agent sees restored history."

Orchestrator verification steps, in order:

1. **Re-derive the mechanism from source.** `AnalyzeTrueIntent`
   (intent_analyzer.go:106) sends only `{system prompt, raw user input}` —
   the analyzer is structurally blind to session history. The dispatcher
   builds `buildMemoryContext` (dispatcher.go:661 — LastIntent, intent
   counts, task store) one line BEFORE the analyzer call and drops it.
   Subagent's claim: CONFIRMED, plus a sharper fix surface than reported.
2. **Prove the earlier leaves' plumbing with forensics, not reruns.**
   The `--keep` scratch workdir preserves the e2e daemon's sqlite state.
   Direct queries (`sqlite3 $WORK/state/sessions.db "SELECT ..."`) proved
   leaf 01's mirrored exchanges existed in `session_messages` — so the
   leaves held and the blocker was genuinely downstream. Rerunning the
   suite would have proven nothing new.
3. **Simulate pure functions before planning.** For keyword/decision
   logic (topic detector scoring), replay the failing inputs through a
   copy of the logic in python — 30 seconds, definitive answer on which
   branch fires.

## Outcomes of proper verification

- The follow-up tree gets the RIGHT design (pass session context into the
  analyzer), not the reported one (skip/lower the gate).
- An architectural principle from the user ("agents that address the user
  query session state; the session never absorbs agent transcripts") maps
  onto concrete seams: `taskStore.GetTasksForSession(sessionID)` +
  `StepStore.ListByTaskID` (step.Result) + `SessionTracker.GetLastIntent`
  already exist as the query surface. No new storage, no session-wide
  "default model," no context pushing.
- Leaves 01/02 get CLOSED as verified-working even though the suite still
  fails — the failure belongs to a third, pre-existing mechanism.

## Anti-pattern

Authoring the follow-up tree from the subagent's prose alone. In this
session the subagent's report was accurate, but the verification also
surfaced (a) the exact existing query seams that make the fix small and
(b) the user's architecture principle that reshaped the design. Both were
lost in the subagent summary.
