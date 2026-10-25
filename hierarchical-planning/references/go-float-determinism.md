# Observations extracted from hierarchical-planning SKILL.md pitfalls (2026-09-05 slimming pass)

Condensed from Pitfall 26 (float determinism) prose to keep the SKILL.md
under the 100K budget. The pitfall entry in SKILL.md now points here.

## Go float determinism — the two silent failure modes

**(a) `sort.SliceStable` with exact `!=` on float scores.** A comparator
like `if ranked[i].score != ranked[j].score` is unreliable — two scores
computed via different float addition orders can differ by 1 ULP, causing
the tie-break branch to fire nondeterministically. Fix: epsilon
comparison:

```go
if diff := a - b; diff > 1e-12 || diff < -1e-12 {
    // not equal
}
```

Symptom when unfixed: intermittent `TestSelectBond_TieBreak` failures
(passed 4/5 runs).

**(b) Map iteration order → nondeterministic float accumulation.** Go
randomizes map iteration order. A scoring loop

```go
for trait, w := range weights {
    score += w * value
}
```

produces slightly different `score` values per run because float addition
is non-associative. Fix: extract map keys, sort them, iterate in sorted
order. Symptom when unfixed: intermittent
`TestScoreBondCandidate_Determinism` failures on specific archetypes.

## Both bugs are invisible on a single test run

They pass once, then fail under `-count=5+` or CI.

## Review checklist for Go leaves that compute scores/rankings

- Run determinism-sensitive tests with `-count=10` to surface
  intermittent float-ordering failures.
- Grep for `!=` in sort comparators (use epsilon instead).
- Grep for `range` over maps in accumulation loops (sort keys first).
