# Vverify with your own golden
When to use: sibling artifacts drift from a shared spec.
Lesson: cross-check against your own golden fixture; zz_-prefixed in-package test probe is the consent-safe form.

# Verify-with-your-own-golden: cross-checking sibling artifacts against the shared spec (plan-compiler tree, meept 2026-09-06)

Session: `docs/plans/plan-compiler/` — leaf 02 compiled markdown to
PhaseSpec; leaf 03 rendered PhaseSpec to trees; both derived their
fixtures independently from the same normative spec
(docs/workflows/plan-dialect.md). Each leaf's own tests proved its code
against ITS fixture — which proves nothing about whether both sides
drifted from the shared document in the same way.

## The technique

Before committing either leaf, the orchestrator wrote a throwaway
in-repo test that fed the SPEC's OWN normative example (section 8.1,
the "two phases, three steps" markdown) through leaf 02's compiler and
asserted the spec-stated outcomes:

```go
// internal/plan/zz_orchestrator_golden_test.go (deleted after the run)
func TestOrchestratorGoldenExample81(t *testing.T) {
    raw, _ := os.ReadFile("/tmp/example81.md") // extracted from the spec
    cp, err := CompileSealed(string(raw), 8)
    // assert: 2 phases; Hash is 64 hex chars; the artifact the spec says
    // becomes Required (consumed by a later phase) IS Required
}
```

Extraction itself was a python one-liner pulling the first ```markdown
fence after "### 8.1". Result: PASS on the first run — evidence that
leaf, tests, and spec agree — and the throwaway was removed in the next
command. Cost: ~10 lines, one test run.

Extracted with a python one-liner pulling the first ```markdown fence
after the section heading. PASS first run; throwaway removed.

## Why the leaves' own tests were not enough

- Leaf 02's fixtures were derived FROM the spec by the implementer —
  the same model class that wrote the code. A shared misreading of the
  spec passes every leaf test and fails only at integration (or worse,
  in production).
- The normative document is the THIRD party in the room. When two
  artifacts (code, tests) are both derived from it, cross-check one
  against the DOCUMENT, not against the other artifact. "Tests green"
  only means code agrees with tests.

## Generalized rule

Whenever a plan tree has a shared normative document (dialect spec,
wire-format spec, contract doc) and ≥2 leaves implement different sides
of it (producer/consumer, compiler/renderer, writer/parser):

1. At review time, before committing, extract one normative example
   from the spec verbatim.
2. Feed it through one side's implementation as a temporary in-package
   test; assert the outcomes the SPEC states (not the outcomes the
   leaf's tests state).
3. Delete the throwaway in the follow-up command.
4. Record in the tracking table: "orchestrator golden check against
   spec §N: PASS" — so the evidence class is named.

This pairs with the leaf-side lesson in leaf-spec-conflicts-and-
sibling-red-build.md (pinned cases vs formulas) — that one catches
spec-vs-leaf-table drift at authoring time; this one catches
code-vs-spec drift at review time.

## Note on the throwaway mechanics

The in-package `zz_*_test.go` + `go test -run` + `rm` pattern is the
consent-safe probe form (see SKILL.md's denial-class addendum: /tmp
`go run` scratch programs are denied; in-repo test probes through the
normal gate are not). Keep the file name `zz_`-prefixed and top-of-file
commented as an orchestrator probe so a parallel session never
mistakes it for leaf work.

## Implementer-side variant: hand-computed goldens are not goldens (2026-09-11, classi-fly leaf 04)

The leaf-side twin of the orchestrator check above: a leaf asking for a
"self-consistent golden generated in the test" invites the implementer
to hand-compute the expectation — and hand arithmetic is itself a
derived artifact. Real case: reservoir recurrence
`s = tanh(decay*s + W*s + win*x)`, hand-derived golden 0.2925/0.1354 vs
true 0.8049/0.5262 (the mental chain dropped the recursive term). The
implementation was right; the "expected" literals were wrong. Rule:
compute every golden with a throwaway INDEPENDENT script (fresh
transcription of the recurrence, separate process) and paste its repr;
when code and a hand-derived expectation disagree, arbitrate with the
independent computation before "fixing" either side. Two artifacts by
one author agreeing proves nothing — that includes code vs your own
mental math. Worked example + the related field-order signature:
references/classi-fly-training-leaf04-2026-09-11.md.
