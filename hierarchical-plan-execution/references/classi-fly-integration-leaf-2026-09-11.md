# Cclassi fly integration leaf 2026 09 11
When to use: leaf needs a sibling not-yet-landed package.
Lesson: author verbatim to frozen contract signatures; close RED-BUILD-BLOCKED with the exact unblock command.

# Sibling RED-BUILD-BLOCKED leaf execution — classi-fly leaf 07 (2026-09-11)

Worked case: `classi-fly` leaf `07-integration.md` (sidecar + judge example +
INTEGRATION.md) executed directly (implementer role) while leaf 02's Go
surface — `reservoir.Load / reservoir.Reservoir / reservoir.Result / Info`
(Contract 2) — had NOT landed. `reservoir/` contained only the leaf-01 core
(`sparse.go`, `reservoir.go` CSR + tanh recurrence; no `fly.go`, no
`classify.go`, no `internal/flyformat/`). A related but distinct shape is in
`leaf-spec-conflicts-and-sibling-red-build.md` (sibling RED *test file*
breaks the package; here the sibling's *production* package is absent
entirely, so the build of any consumer leaf is red by construction).

## The shape: red build that is nobody's fault

Leaf contract exposes a face over symbols owned by an upstream sibling leaf.
The sibling hasn't landed. Consequences:

- `go build ./...` is red in YOUR files with `undefined: reservoir.Load`
  etc. — the compiler cannot distinguish "you wrote broken code" from "the
  type you were promised does not exist yet".
- TDD is structurally impossible: tests cannot compile without the contract
  types. There is no RED→GREEN within the leaf; the honest state is
  RED-BUILD-BLOCKED.
- Re-checking `ls reservoir/` after finishing your files confirmed the
  sibling was still absent — waiting inside the session does not help when
  nothing else is running in this repo.

## Protocol that worked

1. **Author verbatim to the frozen contract, not to what exists.** The
   master doc's Contract 2 signatures are normative: `Load(path string)
   (*Reservoir, error)`, `Classify([]float32) (Result, error)`, `Info()
   Info`, `Result{Class, Confidence, Margin, Abstained}`. Match them exactly
   — field names, types, error-returning signatures — so the sibling's
   landing compiles your leaf unchanged. (`serve.go` took `res.Classify` /
   `res.Info()` per contract; the `trace` request field is accepted in the
   request struct but, having no contract meaning, is not consumed.)
2. **Own only your file list.** Do not add `Result`/`Info` stubs to
   `reservoir/` — sibling-owned. Do not edit `go.mod` (all deps stdlib).
   The temp-compilation pattern from `leaf-spec-conflicts-and-sibling-red-
   build.md` (scratch `_*.go` shim to get type-checking) was considered and
   skipped: without `Result`'s field set, any shim just guesses the shape,
   proving little.
3. **Fixture discovery beats fixture invention.** The eval tooling had
   already produced `tools/eval/eval_fixture.fly` — 535 bytes, uncompressed
   `FLYRES01` container (generator: `make_fixture_fly.py`, documented
   deviation), header: 8 neurons / 3 classes (alpha, beta, gamma) /
   embed_dim 8. Read the generator, parse the header with a quick Python
   probe, and write tests against the fixture's real semantics (lane-d
   one-hot embeddings → class d; thresholds 0.0 so it never abstains).
   `t.Skipf` when the fixture file is absent so the suite degrades
   gracefully wherever it hasn't been generated.
4. **Verify everything the missing sibling does not gate.** `gofmt -l` on
   your four Go files (found one alignment fix); `grep -rn meept` over your
   outputs (leaf checklist item — zero hits); no TODO/debug prints; docs
   complete. Only the compile is blocked.
5. **Retry once after finishing** (the sibling may be landing concurrently
   — it was still absent), then **report RED-BUILD-BLOCKED** as an explicit
   status: which sibling leaf/symbols are missing (exact identifiers +
   files not on disk), what was verified green, the exact orchestrator
   unblock command (`go build ./... && go vet ./... && go test ./cmd/...
   ./examples/ -race -count=2`), and the contract-match claim that makes
   "no edits should be needed when it lands" a checkable assertion.
6. **Consistency divergence warning for the orchestrator**: the SKILL.md
   example contract in `master.md` (generic labels) diverges from the
   evaluated artifacts (alpha/beta/gamma). Harmless here, but any future
   leaf hard-coding "expected class" from the master example would fail
   against real fixtures — cross-check contract examples against actual
   fixture semantics when writing assertions.

## Durable rule

If a leaf consumes not-yet-landed sibling symbols: write exactly to the
frozen contract signatures, own your file list strictly, verify all
sibling-independent gates, retry once, and close with an explicit
RED-BUILD-BLOCKED report naming the missing symbols + files and the exact
unblock command. Never stub, never guess, never touch sibling files.

Related: `leaf-spec-conflicts-and-sibling-red-build.md` (sibling RED test
file variant, incl. the in-package shim escape hatch), `direct-single-leaf-
execution.md`, `pre-dispatch-drift-and-baseline.md` (record the baseline so
a red build is attributable BEFORE dispatch).
