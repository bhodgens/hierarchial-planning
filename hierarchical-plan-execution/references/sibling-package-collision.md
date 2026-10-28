# Ssibling package collision
When to use: two leaves co-own one package.
Lesson: build collision pattern and ownership resolution.

# Sibling Leaf in the Same Package — Build Collision Pattern

> When two plan-tree leaves co-own one Go (or otherwise same-package) directory
> and a sibling lands mid-flight referencing symbols it hasn't defined yet, your
> own verification path fails through no fault of your own. This note captures
> the recognition signal, the isolation recipe that proves your work is correct,
> and the right way to report the situation upstream.

## Recognition signal

You finish your leaf implementation, run your tests, and see:

```
# github.com/rebellion-the-game/sidecar/internal/embed [github.com/rebellion-the-game/sidecar/internal/embed.test]
internal/embed/embed.go:76:12: undefined: newONNXBackend
internal/embed/embed.go:86:7: undefined: newStubBackend
FAIL    github.com/rebellion-the-game/sidecar/internal/embed [build failed]
```

The undefined symbols are in a *different file* (`embed.go`, owned by sibling
leaf 01) — not your files. Your files compile cleanly on their own; the
combined-package build fails because Go compiles at package granularity.

This is not your bug. It's a scheduling artifact: the orchestrator dispatched
two leaves that share `internal/embed/` concurrently, and the sibling is still
in flight.

## What NOT to do

- **Don't block on the sibling completing.** That wastes your turn. Your
  deliverable is your leaf; if your files are complete, you're done.
- **Don't implement the missing symbols yourself.** Defining `newONNXBackend`
  or `newStubBackend` from leaf 02 is scope creep into a sibling you don't
  own. When the sibling's author finishes, your stub will collide with theirs.
- **Don't delete or rename the sibling's file.** Even if it's clearly
  half-written. It's the sibling's author's work in progress.
- **Don't report "build failed, can't verify."** That misattributes the
  failure to your work and triggers an unnecessary fix cycle.

## Isolation verification recipe

Copy *only your files* to a scratch module outside the project, give it a
throwaway `go.mod`, and run your tests there. The scratch module has no
sibling files, so it compiles and tests your work in pure isolation.

```bash
SCRATCH=/tmp/leaf02_check
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
cp internal/embed/{meta,index,index_test}.go "$SCRATCH"/
cd "$SCRATCH"
go mod init leaf02check
go test -short -race -v ./...
```

If green: your work is complete and correct. The combined-package build
failure is purely the sibling's incomplete state and will resolve itself
when the sibling leaf finishes.

## How to report to the orchestrator

State both facts explicitly:

> All 19 tests pass under `-short -race -v` when my files are verified in
> isolation (scratch module copy). The combined-package build fails because
> leaf 01's `embed.go` references `newONNXBackend` and `newStubBackend` that
> aren't defined yet — that's leaf 01's in-flight state, not a defect in
> leaf 02. My files compile and test green independently; the package-level
> build will resolve when leaf 01 lands its backend implementations.

This gives the orchestrator everything it needs: (a) your leaf is done,
(b) the failure is known and owned by the sibling, (c) no action required
from you. The orchestrator can mark your leaf COMPLETE and continue.

## When this pattern does NOT apply

- **Your files alone don't compile.** If copying just your files to a
  scratch module fails, that's a real defect in your work — fix it.
- **The sibling is COMPLETE and you're the one with missing symbols.**
  Then the undefined references are your problem; don't reach for the
  isolation trick, go implement the symbols.
- **The package has a single owner (no sibling leaf).** Then any build
  failure is by definition yours.

## Real-world instance

rebellion-the-game, Tree 11-embed, 2026-07-19. The `internal/embed/` package
was split across two leaves dispatched concurrently:

| Leaf | Files owned | Status when leaf 02 verified |
|------|-------------|------------------------------|
| 01 — ONNX/stub backend | `embed.go` (Model, LoadModel, Embed, EmbedOne, Dim, Source, Close) + backend implementations | In flight: `embed.go` referenced `newONNXBackend` and `newStubBackend` with no definitions yet |
| 02 — Vector index | `meta.go`, `index.go`, `index_test.go` (Index, Add/Remove/Query/SaveTo/LoadFrom/Size + 19 tests) | Complete; needed verification |

Leaf 02 hit the combined-package build failure, ran the isolation recipe
above, saw all 19 tests pass under `-race`, and reported the situation to
the orchestrator with both facts. Orchestrator marked leaf 02 COMPLETE
without a fix cycle; leaf 01 finished its backends shortly after and the
combined build went green.
