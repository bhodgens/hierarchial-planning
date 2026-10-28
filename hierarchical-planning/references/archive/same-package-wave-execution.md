# Same-Package Wave Execution — pinned types, live leaf sessions, orchestrator golden checks


When to use: same-package wave execution with type producers and consumers.
Lesson: consuming leaf defines nothing; orchestrator golden-check is the only gate needed.
Session source: meept plan-compiler tree (2026-09-06), leaves 02 (compiler)
+ 03 (tree emission) dispatched in parallel into `internal/plan/`, leaf 02's
type package consumed by leaf 03. Extends SKILL.md Pitfall 43 (same-package
parallel leaves) with the type-dependency and session-lifetime variants.

## 1. Type-dependency pins: consuming leaf defines NOTHING

When leaf B consumes types leaf A owns (CompiledPlan/PhaseSpec/StepSpec),
the master's frozen contract must carry the EXACT Go definitions, and both
briefs must reference them:

- Consuming leaf's brief: "the types are defined in compiler.go per the
  frozen contract — if the sibling has not landed yet, write against the
  pinned signatures, do NOT define them yourself."
- LSP diagnostics on the consuming leaf showing ONLY the expected
  `undefined: CompiledPlan`-class errors = correct-by-contract. Anything
  else is that leaf's bug.
- The consuming leaf should end in a STOP-item ("awaiting sibling's
  compiler.go") rather than a fake-green run. Expected and correct.
- The ORCHESTRATOR's post-wave full-package `go test -race` is the
  authoritative gate. Neither leaf's focused `-run` proves the pair;
  leaf 03's focused run was impossible (build-failed on the missing
  types) yet the wave was healthy.

## 2. A committed leaf's session can outlive your commit

The orchestrator committed leaf 02 from its mid-run report (a snapshot);
the leaf's session kept working and returned ~30 minutes later with two
REAL post-snapshot fixes: `maxPhases` parsed but never enforced, and
needs references classified step-ref-first (misreporting Phase1.S9 as
later-step instead of missing-step).

Reconciliation protocol:
1. Diff the late report against the committed state — is anything new?
2. Real fixes → separate fix commit (do not amend a referenced commit).
3. Spec-drift findings → the tree's OPEN-QUESTIONS.md errata, never
   silently reconciled (here: DependsOn ordinals-vs-zero-based wording
   conflict resolved by "normative doc wins over leaf sketch").
4. Re-run the full package suite — the follow-ups grew the suite
   27 → 43 cases.
Corollary: before treating a late leaf report as duplicate work, check
whether its changes are already in your commit.

## 3. Orchestrator golden check: verify against the SPEC, not the leaf's tests

A leaf's own tests can share its blind spots. To verify the
implementation against the NORMATIVE document directly: extract the
spec's worked example to /tmp, drop a temporary in-repo test that
compiles/runs it asserting spec-derived expectations (phase count,
artifact Required flags, hash shape), `go test -run <Golden>`, then
REMOVE the temp test. Five minutes, and it proves the spec→impl link
the leaf's own goldens may have paraphrased. Worked example: compiling
the dialect doc's §8.1 example through the just-committed CompileSealed.

## 4. go:embed testdata extracted byte-verbatim from the spec

Golden documents (worked examples, fixtures) belong in `testdata/`
extracted byte-verbatim from the normative spec and loaded via
`go:embed` — not inline string constants. The leaf's final form did
this, making spec↔test drift structurally impossible: editing the spec
without the testdata (or vice versa) is a visible diff. Prefer over
`const golden = ...` for any doc-shaped fixture.

## 5. Name the conversion seam at dispatch when formats differ

When leaf A's output feeds leaf B's consumer under DIFFERENT conventions
(here: compiler emits 1-based phase ordinals and 1-based step numbers;
the legacy plannerStep contract is 0-based), name that conversion seam
EXPLICITLY in the later wave's dispatch brief and review it first. It
was flagged before leaf 04 dispatched, and it proved to be exactly where
the real integration risk lived (PhaseSpecsFromPlan decrements, pinned
by the integration test). Errata for the convention conflict itself
belong in OPEN-QUESTIONS.md with the resolution rule stated.

## 6. Integration tests writing through relative-default-path managers

An integration test that persists through a manager whose default path
is relative ("docs/plans") writes fixtures into the SOURCE TREE
(observed: `internal/daemon/docs/plans/sealed-plan.md`), surviving the
run as untracked noise — and cleanup `rm` hits the user's shell-approval
gate. Rule: tests exercising such managers must chdir to `t.TempDir()`
or inject an absolute path; never let the manager's default resolve
inside the package directory.
