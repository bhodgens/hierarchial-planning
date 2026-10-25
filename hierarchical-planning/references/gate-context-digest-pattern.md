# Gate/Classifier Context-Digest Pattern

**When to use:** A classifier, gate, or pre-routing analyzer judges user
messages IN ISOLATION (only {system prompt, raw input} reaches its LLM)
and misfires on follow-up turns whose referents live in prior turns
("did the change get made? where is the file?" → canned "which file?"
clarification). Worked instance: meept session-aware-intent-gate tree
(2026-09-04) — the dispatcher's intent-analyzer ambiguity gate
(dispatcher.go:665-668, threshold 0.6) short-circuited status-shaped
follow-ups before any agent saw the restored conversation history.

## Root cause shape

The gate is not broken — it is BLIND. The failure is an information
starvation at the analyzer call, not a threshold or keyword problem.
Check whether the session state the gate needs already exists one call
away: in meept, `buildMemoryContext` assembled LastIntent/memory
results ONE LINE before the analyzer call and dropped it on the floor,
and `taskStore.GetTasksForSession` /
`taskRegistry.StepStore().ListByTaskID` /
`sessionTracker.GetLastIntent` were the ready-made query seams.

## The fix: a compact session-state digest

1. **Digest builder on the dispatcher** (nil-guarded every store;
   any store error → Debug log + skip that field; never propagate;
   empty session → empty digest = byte-identical pre-fix behavior):
   - last task for the session (GetTasksForSession is updated_at DESC
     → tasks[0]), name capped 200 chars
   - terminal step result summary (highest-sequence completed/approved
     step with non-empty Result — mirror bestStepResult), first line,
     capped 400
   - last intent type from the session tracker
2. **Analyzer signature extension** with the digest parameter; nil or
   empty digest → prompt BYTE-IDENTICAL to pre-fix (test-proven, not
   asserted in prose). Non-empty digest appends a compact block to the
   USER message:
   ```
   [Recent session activity]
   Last task: <name> (state: <state>, agent: <agent>)
   Result summary: <summary>
   ```
3. **Two system-prompt rules** (present in every call — harmless
   without context): use recent activity to resolve pronouns/references
   ("the change", "the file", "it"); if the input is a short follow-up
   the activity makes clear, ambiguity is LOW — do not re-ask.
4. **Both call sites** build the digest BEFORE the analysis call.
   Post-clarification combined-input call sites need the digest built
   earlier than the adjacent buildMemoryContext — order matters.

## Design rules (what NOT to do)

- No threshold changes (0.6 stayed), no keyword/reference lists, no new
  config. The model decides from context; keyword hacks misfire.
- No "session default model" or session-owned agent state — the user's
  architecture principle: user-addressed agents QUERY session state at
  turn time (the stores ARE the seam); the session never passively
  absorbs agent transcripts. Task-scoped worker conversations remain
  isolated; only the final user-facing summary crosses the boundary.
- Analyzer LLM failure already fails open (turn proceeds) — preserve.
- Keep the digest format EXACT — downstream tests and e2e assertions
  pattern-match the block headers.

## Test shape

- Contextless prompt byte-identity test (fake chatter capturing
  messages; diff against the pre-fix prompt).
- Populated-digest test: user message contains input + block; partial
  digest omits empty-field lines.
- Call-site test: dispatcher with a linked completed task passes a
  non-empty digest; empty session passes empty.
- E2E: the follow-up turn must now reference the artifact (this was
  assertion A5, failing across two prior trees before this pattern).

## Cross-references

- session-continuity leaves 01/02 (meept) — prerequisites: history
  recording + DB restore. The gate fix completes the chain; without
  restore the analyzer context would still be empty on cache misses.
- verify-root-causes-before-followup-trees.md — the pre-tree
  verification that found the sharper fix surface.
