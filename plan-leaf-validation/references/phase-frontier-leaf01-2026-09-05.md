# phase-frontier-parallel leaf 01 — implementing-leaf record (2026-09-05)

TDD implementation of `ComputePhaseFrontier` (pure frontier function, NO wiring).
Files landed (uncommitted at session end — orchestrator commits): `internal/agent/phase_frontier.go`,
`internal/agent/phase_frontier_test.go` (package `agent`, identifiers intentionally
UNEXPORTED per leaf Task 2 + master conventions; Contract A's capitalized names are
presentation only). gofmt/vet clean; targeted + full `go test -p 2 ./internal/agent/...`
green (26s, 4 pkgs); no-wiring grep empty; line-number-corruption grep 0.

## STOP-items for the orchestrator / validation pass

1. **Three leaf-table errata** (leaf 01 doc `01-frontier-compute.md` vs its own frozen
   rules; each encoded in the test file with a comment, tests green):
   - **Case 5**: leaf cell says `cycle=false`; frozen rule 4
     (`cycleDetected = (len(ready)==0 && len(nodes)>0)`, identical in leaf semantics +
     master Contract A) forces `true` for the pinned fixture
     (`B requires x`, no producer, available={}). Test asserts TRUE per the rule.
   - **Case 9**: leaf cell says ready `{A,C}` with pinned inputs
     (`available={}`, `busy={B}`) — unreachable: C's required consume `a` fails gate 2a,
     and B/C are gate-identical. Rule-correct ready set is `{A}`. Fixture inputs kept
     exactly as the leaf pinned them.
   - **Case 4**: leaf cell says `{A,B}` (A busy, B consumes x-optional), but that
     contradicts the leaf's OWN case 7 and rule 1 (optional consumes DO create edges;
     gate 2b then blocks B on busy A). Rule-correct: `{A}`.
   - Route: leaf header says deviations go to `OPEN-QUESTIONS.md` — record there if
     leaf 04 hasn't already.
2. **Leaf 02 must call the unexported names** (`phaseNode`, `computePhaseFrontier`)
   from within package `agent`. If leaf 02 was drafted against Contract A's exported
   names, its code needs renaming — this was the documented mapping, not a deviation
   from the leaf (Task 2 + self-checklist pin unexported explicitly).

## Technique notes (generalized in SKILL.md items 18–20)

- Example-table-vs-rules reconciliation protocol (rules normative, inputs pinned,
  errata surfaced as STOP-items with rule citation).
- Same-batch impl+test writes → phantom LSP undefined floods; compiler is ground truth.
- Purity-test anti-vacuity: corrupt a copied input and assert the comparison FAILS.
