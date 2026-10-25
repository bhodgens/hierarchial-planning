# Spec Test Expectation vs Implementation Mismatches

> Worked example for leaf implementation. When implementing from a spec that
> includes test pseudocode, the test EXPECTATIONS can be wrong even when the
> implementation correctly follows the spec's algorithm description. Two
> distinct failure modes: (1) semantic misunderstanding of what the algorithm
> produces, and (2) test data that produces more output than anticipated.

## Session

- **Date:** 2026-08-04
- **Project:** AgentAudit (Go backend, chi/SQLite)
- **Plan tree:** `docs/plans/phase1-mvp/04-analysis/02-ngram-pattern-miner.md`
- **Scope:** N-gram app sequence detection (bigrams + trigrams), time-of-day grouping

## Failure Mode 1: Transition Timestamp Semantics

### The mismatch

The spec's test pseudocode for `TestMine_ConfidenceAndTimes` asserted:

```go
assert.Equal(t, day1, p.FirstSeen)  // day1 = first event of the pair
```

But the implementation (correctly per spec algorithm) timestamps each bigram
transition at the **target** event — the moment the new app receives focus:

```go
transitions = append(transitions, appTransition{
    Apps:      []string{lastApp, ev.AppBundle},
    Timestamp: ev.Timestamp,  // THIS event, not the previous one
    TimeOfDay: types.ClassifyTimeOfDay(ev.Timestamp),
})
```

So `FirstSeen` was `day1.Add(time.Minute)` (when Safari got focus), not `day1`
(when Mail got focus). The test assertion was wrong; the implementation was right.

### The general rule

**A transition A→B is timestamped at B, not A.** This is universal for event-
sequence mining: the transition is *completed* when the target state is entered.
When writing tests for transition-extraction algorithms:

1. Read the algorithm description carefully to determine which event's timestamp
   anchors the transition
2. For "first seen" / "last seen" assertions, use the transition timestamp, not
   the source event timestamp
3. If unsure, trace through one example by hand before writing the assertion

## Failure Mode 2: N-gram Explosion from Continuous Chains

### The mismatch

A test expected exactly 2 patterns from events arranged as:
`A→B→C→D` across multiple days. But the sliding-window n-gram extractor produced
**5 patterns**: bigrams (A→B, B→C, C→D) plus trigrams (A→B→C, B→C→D).

### Why it happened

The spec defines both bigram AND trigram extraction from the same event stream.
A continuous chain of N distinct apps produces:
- `N-1` bigrams
- `N-2` trigrams
- Total: `2N-3` patterns (before dedup/grouping)

For a 4-app chain: 3 bigrams + 2 trigrams = 5 patterns, not 2.

### The fix

Design test data to produce a known, small number of patterns:
- Use **gap-separated sessions** within a day to avoid creating chains
- Or use exactly 2 apps per day (produces exactly 1 bigram, 0 trigrams)
- Or test bigrams and trigrams separately before testing the combined `Mine`

### Test data design pattern for n-gram tests

```go
// GOOD: Each day has exactly one transition, no chains
events := []types.Event{
    // Day 1: Mail→Safari only
    {Timestamp: day1, ..., AppBundle: "com.apple.Mail"},
    {Timestamp: day1.Add(time.Minute), ..., AppBundle: "com.apple.Safari"},
    // Day 2: Mail→Terminal only (2-hour gap = separate session, no chain)
    {Timestamp: day2.Add(2*time.Hour), ..., AppBundle: "com.apple.Mail"},
    {Timestamp: day2.Add(2*time.Hour + time.Minute), ..., AppBundle: "com.apple.Terminal"},
}

// BAD: Continuous chain creates unexpected extra n-grams
events := []types.Event{
    {Timestamp: day1, ..., AppBundle: "com.a.A"},
    {Timestamp: day1.Add(time.Minute), ..., AppBundle: "com.b.B"},
    {Timestamp: day1.Add(2*time.Minute), ..., AppBundle: "com.c.C"},
    {Timestamp: day1.Add(3*time.Minute), ..., AppBundle: "com.d.D"},
}
```

## The Meta-Lesson

When a spec provides test pseudocode:

1. **The algorithm description is authoritative; the test pseudocode is a sketch.**
   If a test assertion contradicts the algorithm semantics, fix the test.
2. **Count the output before asserting on it.** For extraction/mining algorithms,
   trace through the test data to count expected outputs before writing
   `require.Len(t, results, N)`.
3. **The first test run is a debugging tool.** When 16 of 18 tests pass and 2
   fail, check whether the failures are test-expectation bugs (this case) or
   implementation bugs. Read the diff carefully — the error message tells you
   exactly what the code actually produced.

## Distinguishing Test-Expectation Bugs from Implementation Bugs

When a test fails during leaf execution, apply this decision tree before
touching the implementation:

1. **Read the actual vs expected in the assertion error.** Does the actual value
   look correct per the algorithm's described behavior?
2. **Trace the algorithm by hand** on the test input to determine the *correct*
   output independently of both the spec's pseudocode and your implementation.
3. **If the implementation matches your hand-trace, the test is wrong.** Fix the
   test assertion, not the code. This is NOT "gaming the test" — the test was
   asserting something the algorithm was never supposed to produce.
4. **If the implementation does NOT match your hand-trace, the code is wrong.**
   Fix the code.

Step 2 is the critical one. Without an independent hand-trace, you have no
ground truth to adjudicate between a wrong test and wrong code.

### When most tests pass and a few fail

- If the failures are in edge-case or combination tests (sorting + filtering,
  timestamp tracking + day counting), the implementation is usually right and
  the test expectations didn't account for interaction effects.
- If the failures are in core extraction tests (basic bigram/trigram), the
  implementation is likely wrong.
- If ALL tests fail with the same category of error (off-by-one, wrong type),
  the implementation has a structural bug.

## Phase 3 Addendum: Set-Arithmetic and Tokenization Mismatches

> Same meta-lesson, different failure shapes. Confirms the pattern repeats
> across phases and algorithm families.

### Session

- **Date:** 2026-08-05
- **Project:** AgentAudit Phase 3, branch 12 (cross-user analysis)
- **Plan tree:** `docs/plans/phase3/12-cross-user-analysis/` (leaves 01–05)
- **Scope:** OCR Jaccard overlap, composite-skill name generation, window-title cleaning

Three spec test expectations were wrong in one leaf-execution run. All three
were caught by the decision tree above (hand-trace the algorithm, compare to
the assertion). The implementation was correct in all three; the test
expectations were fixed, not the code.

### Failure Mode 3: Jaccard Set-Size Miscalculation

Spec test `TestOCRSignatureOverlap_WeightedScore` asserted Jaccard = 2/5 = 0.4
for `A={h1,h2,h3}` vs `B={h2,h3,h4}`. The spec's *comment* double-counted the
intersection in the union:

- intersection = `{h2,h3}` → |∩| = 2
- union = `{h1,h2,h3,h4}` → |∪| = **4** (not 5)
- Jaccard = 2/4 = **0.5**

**Rule:** for Jaccard/Dice/Sørensen-Dice set-similarity assertions, write out
∩ and ∪ explicitly before computing. The most common arithmetic slip is
`|A|+|B|` instead of `|A|+|B|-|∩|` for the union.

### Failure Mode 4: Shared-Keyword Iteration Order

Spec test for `generateCompositeName("import-csv-to-excel", "excel-to-dashboard")`
expected `"csv-to-dashboard-pipeline"` (assuming "excel" is the shared keyword).
The algorithm scans tokens left-to-right and finds **"to"** first (it appears
in both names before "excel"), so:

- common word found: `"to"` (prefix in A: `"import-csv"`, suffix in B: `"dashboard"`)
- result: `"import-csv-to-dashboard-pipeline"`

**Rule:** when a "find shared keyword" heuristic iterates in source order,
the FIRST common token wins — which may be a filler word like "to", "and",
"the". To test the *intended* keyword, either (a) design inputs where the
intended keyword is genuinely first, or (b) filter stop-words out of the
candidate set before testing. Don't assume the "obvious" shared word is the
one the loop lands on.

### Failure Mode 5: Over-Aggressive String Truncation

Spec test expected `cleanWindowTitle("Q1_Report.xlsx")` → `"Q1 Report"`, but
the spec's own implementation used `strings.IndexAny(title, " -—|")` which
truncates at the **first space**, collapsing `"Q1 Report"` → `"Q1"`. Here
the implementation was genuinely too aggressive (not just the test), so this
was a code fix driven by hand-tracing the desired behavior, then correcting
the spec's pseudocode.

**Rule:** separator-based truncation should match **delimited** separators
(`" — "`, `" | "`, `" - "` — the app-suffix patterns like `"file.txt - AppName"`),
not single characters that appear inside the meaningful title. Test with a
multi-word title before asserting on the cleaned output; if the first word
survives but the rest doesn't, the truncation is too eager.

### Confirmation: the meta-lesson holds across phases

The decision tree (read diff → hand-trace → adjudicate) correctly classified
all three failures without modification. The new failure modes (set
arithmetic, token-iteration order, separator-vs-character truncation) are
additions to the catalog of "ways spec test expectations can be wrong," not
new categories of decision.

## Cosmetic Convention Mismatches (Orchestrator-Written Tests for Subagent Code)

When the orchestrator salvages a timed-out subagent by writing the missing test
file directly, the test's assumptions about naming/casing/exception types may
not match what the subagent chose. These are NOT algorithm-semantic mismatches
(the section above) — they are cosmetic convention choices where the
implementation is correct and the test needs adjusting:

- **Status string casing:** test asserts `status == "QUEUED"` but implementation
  uses `"queued"`. Fix: `.lower() == "queued"` in the assertion.
- **Exception type:** test asserts `pytest.raises(ValueError)` but implementation
  raises `KeyError`. Fix: `pytest.raises((KeyError, ValueError))`.
- **Field naming:** test reads `data["props"]` but manifest is a bare JSON array
  (no wrapper key). Fix: read `data` directly as the array.

**Rule:** When the orchestrator writes a test for code it didn't write, run the
test, read the failures, and adjust the TEST to match the implementation's
cosmetic conventions — UNLESS the convention violates a project-wide standard.
The implementation author's choices for casing/exception types are valid; the
test should conform, not impose.

## Failure Mode 6: The Spec Conflicts With Itself (case table vs. frozen normative text)

> 2026-09-05, meept `docs/plans/phase-frontier-parallel/01-frontier-compute.md`.
> New flavor: not spec-pseudocode-vs-implementation, but TWO PARTS OF THE SPEC
> DISAGREEING — a leaf's per-case expectations table vs. the master doc's
> "frozen" semantics section.

A pure-function leaf pinned its semantics normatively (master.md: "Semantics
(all pinned; **deviations go to OPEN-QUESTIONS.md**)", with an explicit
**iff** on the cycle rule), then listed 16 case rows. Three rows contradicted
the frozen text:

- **Case 5** wanted `cycle=false` for an all-blocked graph; frozen rule: cycle
  **iff** `len(ready)==0 && len(nodes)>0` → the row must read `true`.
- **Cases 3/7/14** implied busy phases drop out of `ready`; frozen rule 2 has
  NO busy-exclusion clause — and the leaf's OWN case 12 proved the opposite
  ("A busy → but A must still be READY → [A]"). The table was internally
  inconsistent.
- **Case 14** was still salvageable under the frozen rule by re-gating the
  fixture (give the busy phase a missing required consume), preserving the
  row's literal `[C] only` while keeping the tested property (low Sequence
  never outranks an edge block).

**Resolution rule:** the normative section wins — especially when marked
frozen, "pinned", or stated with **iff**. Case tables are illustrative
examples and are the least reliable part of a plan doc. Extended decision
tree: when a test fails against a table expectation, (1) hand-trace from the
FROZEN semantics, not the case row; (2) before adjudicating test-vs-code,
grep the parent/master doc for the same rule — the spec may self-conflict;
(3) when the row's intent can be honored under the winning semantics, adjust
the FIXTURE rather than the expectation; (4) report every deviation in the
leaf report with the winning rule cited verbatim, so the orchestrator can
route it to OPEN-QUESTIONS.md. Never silently "fix" the table — the
doc-vs-code discrepancy is information the orchestrator needs.

## Failure Mode 7: The Leaf's Test Sketch Contradicts the DEPENDENCY's Real Contract

> 2026-09-05, meept skill-authoring tree leaf 02. Failure Mode 6 is the spec
> disagreeing with ITSELF (case table vs frozen text); this mode is the spec
> disagreeing with a DEPENDENCY the leaf calls into.

The leaf's Task 3 sketch said: "create same name again -> error mentioning
the existing skill (writer's dedup)". Reading the actual dependency
(lifecycle/writer.go) showed same-name writes are legitimate OVERWRITES —
SHA dedup only rejects byte-identical content registered under a DIFFERENT
name. Encoding the sketch's premise literally would have pinned wrong
behavior in a passing test: the second create of the same name is a valid
overwrite, not an error.

**Rule:** before writing a leaf test whose premise lives in a dependency's
behavior ("the writer's dedup", "the registry's Get", "the parser's
rejection rules"), read the dependency's source and derive the premise from
IT, not from the sketch prose. Then adapt the FIXTURE to hit the real path
the sketch intended: seed byte-identical content under a DIFFERENT name →
the real duplicate-content rejection fires → error naming the existing
skill. That honors the sketch's INTENT (duplicate rejection with a helpful
message) under the dependency's actual contract. Report the premise
correction as a deviation with the dependency file cited — the orchestrator
may want the plan doc's sketch fixed too.
