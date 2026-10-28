# Iintent taxonomy extension checklist
When to use: adding a member to an enum-ish Go taxonomy.
Lesson: leaf contracts under-count touchpoints; record a reason per exclusion.

# Intent-taxonomy extension checklist (Go enum-ish type + method switches)

Class: adding a member to a taxonomy type where a plan-leaf contract names
the "official" touchpoints, but the package has MORE intent-method surfaces
than the contract lists. Sibling of `tokscale-client-addition-checklist.md`
(client registry): some touchpoints are compiler-visible, but table-shaped
ones (string-keyed maps, slice lists, keyword functions) are invisible to
the compiler and to a contract written from memory.

Worked case: `quickplan` (13th intent) in meept `internal/agent/intent.go`,
leaf 01 of docs/plans/quickplan-mode, 2026-09-09. Contract named 5 switches;
sweep found 5 more surfaces, of which 5 needed edits and several needed
deliberate EXCLUSION with recorded reasons.

## The inventory

Contract switches (always check all five, even if the contract only pins some):

1. `Category()` — routing category (inline/defer).
2. `SuggestedMode()` — planning mode string.
3. `DefaultAgent()` — agent routing.
4. `RequiresPlanning()` — orchestration gate.
5. `ShouldCreateTask()` — tracked-task gate.

Contract-omitted surfaces (found by sweep, not by the contract):

6. `ShouldDispatchAsync(requiresPlanning)` — contract had NO guidance.
   Adjudicate by in-file precedent: `IntentSchedule` returns
   `requiresPlanning`; copy the closest semantic precedent and note why
   (quickplan always has RequiresPlanning=true, so `return requiresPlanning`
   is behavior-preserving vs. `return true` today, correct if the flag
   semantics ever change).
7. `Keywords()` — exhaustive switch with `default: return nil`. A nil return
   for the new intent CORRUPTS consumers: `buildIntentText` (SemanticIndex)
   does `strings.Join(keywords, ", ")` and a keyword test asserts non-nil.
   Add a case with real trigger phrases even when "no keyword table was
   required" by the contract.
8. `IsValidIntentType()` — validity whitelist; omitting the new value means
   classifier output for it fails validation downstream.
9. `SemanticIndex.BuildIndex()` `allIntents` slice — include with a comment
   saying where gating/disambiguation happens (downstream), so a future
   reader doesn't remove it as "unused".
10. `SteeringHeuristicTable` (dispatcher.go) — map lookup with a default, so
    omission is silent; an explicit entry documents the steer policy.

## Deliberate exclusions need recorded reasons too

Sweeping surfaces without editing them is fine — but write down WHY, or the
next taxonomy extension re-litigates each one:

- `keywordPatterns` (dispatcher keyword classifier): best-match table,
  deliberately SPARSE (many intents have no row) — not exhaustive, no edit.
- `llm_classifier.go` tables (intentThresholds, agentMapping,
  isValidIntent, buildClassificationPrompt intents): the LLM whitelist is a
  PRODUCTION GATE the new intent must not short-circuit when the master plan
  assigns the new intent to a later stage (post-chain cascade / dispatcher
  layer). Adding it here would change routing before the owning leaf lands.
- `intentTypesForDefaultAgent` (inverse agent→intent map) and
  `strategic_routing` actor/reviewer tables: new intent routes to an agent
  outside that table's purpose (orchestrator, not actor/reviewer pipeline).

## Method

- Sweep by grepping a SIBLING intent constant
  (`grep -rn "IntentReview" internal/agent/ --include="*.go"`), NEVER by
  trusting the contract's switch list — the contract was written from
  memory and missed surfaces.
- Every include/exclude gets a one-line reason (code comment referencing the
  adjudication record, or a line in the completion report).
- TDD shape: contract test FIRST (RED = undefined symbol proves the test
  exercises the new constant), table-row additions to existing table tests,
  gofmt BEFORE build (a new constant line breaks the const-block alignment
  and the build error is a red herring).
- In shared worktrees: the patch tool may emit a sibling-write warning on a
  file you own a region of — adjudicate by `git diff <file>` hunk scope, not
  whole-file re-reads (see direct-single-leaf-execution.md).
