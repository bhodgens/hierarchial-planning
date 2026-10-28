# Same-package concurrent leaves — compiled-type sequencing (plan-compiler tree, meept 2026-09-06)


When to use: parallel leaves with compiled-type dependencies in one package.
Lesson: pin full struct definitions in the consumer's leaf; consumer codes blind and reports STOP.
Session: `docs/plans/plan-compiler/` — leaf 02 (CompileSealed, owns
CompiledPlan/PhaseSpec/StepSpec in compiler.go) and leaf 03 (EmitTree,
consumes those pinned signatures) dispatched in parallel against
internal/plan/. Extends Pitfall 43 (same-package parallel leaves) with
the type-dependency variant and the exact recovery that made both land
green on the first post-wave run.

## What happened

Leaf 03 finished its emitter first (~2950s) but leaf 02's compiler.go
had not landed — only its RED-phase compiler_test.go had. Leaf 03
correctly reported a STOP-item instead of defining the types itself:
its focused run failed with 22 identical `undefined: CompiledPlan/
PhaseSpec/StepSpec` errors, all in treeemit.go, zero errors of any other
class. Leaf 02's compiler.go landed ~35 minutes later; the orchestrator
ran the post-wave authoritative build and everything was green
immediately — no re-dispatch, no edits.

## Why it worked (the dispatch-context clauses that mattered)

1. **FROZEN-signature pinning in both briefs.** master.md Contract B
   pinned the exact struct fields + JSON tags; leaf 03's brief said
   "write your code against the pinned signatures; if compiler.go has
   not landed, note it; do NOT create compiler*.go". Leaf 03 coded to
   the contract, not to a file. The integration risk became zero —
   only the BUILD was blocked, never the interface.
2. **Type-ownership pre-assignment.** "CompiledPlan/PhaseSpec/StepSpec
   are YOURS (leaf 03 consumes the pinned signatures)" — one owner per
   type, stated in both briefs. This is the struct-only-placeholder
   rule from Pitfall 43 generalized to pure-type new files.
3. **Diagnostic-class self-check before STOP.** Leaf 03's report
   enumerated all 22 build errors and showed they were exactly the
   three expected undeclared names, with no fourth class — that is the
   evidence an orchestrator needs to trust "blocked, not broken"
   without re-reading the code.
4. **Orchestrator post-wave run is the gate, not leaf runs.** When
   compiler.go landed, one `go build ./internal/plan/ && go test -race
   -p 2 ./internal/plan/` greened both leaves. Neither leaf's claimed
   test output was taken on faith (Pitfall 44 rule: verify claims).

## Dispatch-context template (add to same-package parallel waves with type deps)

```
CAUTION (same-package sibling): leaf NN (<owner>) is being implemented
CONCURRENTLY in this same package. <Types> are defined in <owner's
file> per master.md Contract X — those signatures are FROZEN. If it has
not landed yet when you build, code against the pinned signatures and
note it; package builds may transiently fail from the sibling's
RED-phase test files — if your own files are correct and your focused
`go test ./internal/<pkg>/ -run <yourtests>` passes once the package
settles, report and stop. Do NOT create or modify <owner's files>.
```

## Sequencing guidance

- Type-producer and type-consumer CAN go in one wave when the contract
  pins the types precisely enough to code against blind (frozen struct
  fields + JSON tags in the plan doc). The consumer's leaf doc should
  restate the full struct definitions, not point at them.
- If the consumer ALSO needs behavior (methods, validation order) that
  is not pinned, serialize instead — behavior drift cannot be coded
  around blind.
- Gate function: "could the consumer's leaf doc be implemented against
  a header stub alone?" If yes, parallel is safe. If no, serialize.

## Review-side lesson: verify-with-your-own-golden

Leaf 02's own tests proved its compiler compiled ITS fixture; the
orchestrator additionally compiled the DIALECT SPEC's normative example
(section 8.1) as a throwaway in-repo test before committing — catching
the class "tests green but both sides drifted from the shared spec".
Cost: ~10 lines of temporary test. Rule: when two artifacts are both
derived from a third normative document, cross-check one against the
document, not against the other.
