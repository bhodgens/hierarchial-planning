# Leaf E2E Verification — Binary Smoke Tests (Go CLIs)

Lessons from leaf implementations whose self-verification includes running the
compiled binary (e.g. meept `cmd/meept` plan leaves, 2026-08-29 eval CLI).

## Rebuild the binary IMMEDIATELY before every smoke test

Never trust a pre-existing repo-root binary in a shared tree — sibling
sessions, orchestrators, or earlier work may have built it from a different
source state.

Real incident (2026-08-29, meept): after writing `cmd/meept/eval.go` and an
early `go build`, I patched main.go to register the command, then ran the
repo-root `./meept eval run --task ...` — it failed with
`Error: unknown flag: --task`. I nearly started debugging flag wiring, but the
binary on disk was stale (built BEFORE the registration patch, and possibly
from a different tree state entirely; `git log` showed no committed eval code
matching it). A fresh `go build -o meept ./cmd/meept/` made every command work
first try.

Rules:
- `go build -o <bin> ./cmd/<pkg>/` in the SAME terminal step as the smoke
  test (or immediately before it). Cheap insurance.
- Symptom signature: a command you just wrote reports `unknown flag` /
  `unknown command` → suspect binary staleness FIRST, not your cobra wiring.
  Cross-check `grep -rn 'Use:.*"<cmd>"' cmd/` (source has it) + binary mtime
  vs your edit time.
- `go build ./cmd/meept/` (no `-o`) does NOT update a repo-root `./meept` —
  it writes to the package dir or discards the artifact. If the smoke test
  runs `./meept`, build WITH `-o meept`.

## Clean up real-store artifacts after E2E

If the leaf's E2E writes into the user's real state dir (e.g.
`~/.meept/eval/*.json`), snapshot the record count before, run the smoke
test, then `rm` the demo records and confirm the count is restored. Demo
records in a real store pollute the user's `eval list` output.

## Differentiated exit codes (0 / 1 / 2) with cobra

Recurring leaf-spec pattern: exit 0 on success, 1 on domain failure (the
thing being tested did not pass), 2 on usage error.

Constraint: cobra's root `Execute()` exits 1 for ANY error returned from
`RunE` — it cannot by itself distinguish "domain failure" from "bad usage".

Pattern that worked (`cmd/meept/eval.go`):
- Domain-failure sentinel, returned by the run function itself (so its
  contract encodes the outcome and tests can `errors.Is` it):
  `var errEvalNotPassed = errors.New("eval run did not pass")`
- Typed usage error with `Unwrap`:
  `type evalUsageError struct{ err error }` → returned for missing required
  flags/args, so it flows out of the pure function too.
- One wrapper at the cobra boundary:
  ```go
  func handleEvalError(err error) error {
      if err == nil { return nil }
      var usage *evalUsageError
      if errors.As(err, &usage) { fmt.Fprintln(os.Stderr, "Error:", usage); os.Exit(2) }
      if errors.Is(err, errEvalNotPassed) { os.Exit(1) }
      return err // root Execute() exits 1
  }
  ```
- `os.Exit` skips defers — acceptable ONLY at the final command boundary;
  keep the `runX(ctx, io.Writer, options)` core pure and inject the store dir
  so tests never execute the exit path and never touch `$HOME`.

## Test-shape notes that paid off

- Helper that tolerates the domain-failure sentinel (`errEvalNotPassed`) is
  essential — treating "run completed but failed" as test-fatal forces every
  negative-path test through awkward special-casing.
- For list/ordering tests, write records directly via the store with
  hand-set `CreatedAt` values instead of racing real timestamps.
- Unique test IDs: a tiny hex `pad16(i)` helper beats hoping timestamps differ.
