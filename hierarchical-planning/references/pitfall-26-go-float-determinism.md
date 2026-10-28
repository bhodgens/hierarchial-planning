# Pitfall 26 - Go Floating-Point Determinism: Two Silent Failure Modes

When to use: reviewing Go leaves that rank, sort, or score with float arithmetic.
Lesson: exact float comparison and map-iteration-order accumulation both pass once and fail under -count=N or CI; run determinism tests with -count=10 and grep for the two patterns.

Subagent Go code with float arithmetic can pass once but fail under `-race`/`-count=N`.

## The two patterns

**(a) `sort.SliceStable` with exact `!=` on float scores.** Two scores from different float addition orders can differ by 1 ULP. Use epsilon comparison: `diff > 1e-12 || diff < -1e-12`.

**(b) Map-iteration-order float accumulation.** Go randomizes map iteration order and float addition is non-associative, so `for trait, w := range weights { score += w * value }` yields run-to-run drift. Extract and sort map keys first.

Both hit real intermittent failures (`TestSelectBond_TieBreak`, `TestScoreBondCandidate_Determinism`). Both are invisible when running tests once but surface under `-count=5+` or in CI.

## Review checklist for Go leaves that rank/sort by float scores

1. Run determinism-sensitive tests with `-count=10`.
2. Grep for `!=` in sort comparators - require epsilon comparison.
3. Grep for `range` over maps in accumulation loops - require sorted keys.

Condensed reference: `references/go-float-determinism.md`.
