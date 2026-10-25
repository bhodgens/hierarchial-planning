# Leaf-Execution Pitfalls: Leaf-Doc Overrides, Shared Checkouts, TDD RED

Lessons from executing plan-tree leaves (originally leaf 06,
containment-and-computer-use) that generalize to any leaf run.

## Leaf-doc overrides beat house defaults

A leaf document may override your default tooling and impose hard rules:
- "Do NOT use read_file on existing source — search_files/terminal cat only."
- "DO NOT COMMIT." (leave everything staged/untracked)
Honor these literally for the whole leaf, including during verification.
Also mine the leaf's Context section for conventions before writing code
(driver choice, command shape, ID generation) — it usually names the exact
file whose pattern you should copy.

## Parallel sibling sessions share the checkout

Multiple Hermes sessions may work the same repo concurrently:
- If write/patch warns "modified by sibling subagent but you never read it",
  re-read the file (via terminal, per leaf rules if any) before further edits.
  The warning can also ride along on a SUCCESSFUL patch as a `_warning` field
  (late-arriving concurrent-modification notice) — same response: re-read the
  affected region before your next edit and confirm your hunk landed intact
  (`git diff -- <file>`), rather than assuming either edit was lost.
- Build breaks in files you never touched (unexplained undefined symbols) are
  almost always a sibling mid-write. Diagnose with `git status --porcelain`
  to attribute files, wait ~30–90s, rebuild, retry. Do NOT debug, fix, or
  revert their code, and stay out of their paths.
- Keep your own edits narrow and re-verify builds right after each wiring
  change so your failures stay attributable.

## TDD RED phase without running go test

Write failing tests first referencing the planned API. write_file returns LSP
diagnostics listing every undefined symbol — that transcript is your RED
evidence without spending a go-test cycle. Then implement to green.

## Long positional-arg functions

Daemon-style registration functions take 10+ positional args. When adding one:
update BOTH the definition and every call site in the same pass, then build
immediately (`go build ./<pkg>/`). Registry iteration is `registry.List()`,
not `.All()`.

## Verification battery per leaf

1. `go test -race -count=1 -short` on each touched package
2. `go build ./...`
3. `go vet` on cmd packages touched
4. Repo analyzers on touched packages (mutexio, predid): mutexio flags I/O by
   method name under lock — `Exec/Query/QueryRow`, `ReadFile`, `WriteFile`,
   `Close`, even `Get`/`Load` unless receiver is mutex-guarded struct.
   Prefer no-mutex designs over nolint comment farms.

## Blocked verification commands

If the user denies a live binary smoke-run command, do NOT retry or rephrase
it (a denial is consent-withheld, not a flake). Fall back to command-level
tests as evidence and state the substitution explicitly in your report.

## Docs placement

User-facing feature docs go in `docs/workflows/<topic>.md` with runnable CLI
examples (table column headers lowercase). Check whether a nearest-topic page
exists before creating a new one; the leaf will say which it wants.

## gofmt realignment after inserting a documented field mid-struct

Contract-style leaf edits often insert a field + doc comment into the
MIDDLE of a gofmt-aligned struct (e.g. after `Category`, before the
rate-limit fields). gofmt treats an embedded comment line as an
alignment-group separator: fields before the comment form one group and
fields after it must realign separately, so the raw insertion leaves the
struct misformatted and `gofmt -l` flags the file even though every line
looks aligned to the eye. Fix is deterministic, not hand-editing: review
with `gofmt -d <file>`, apply with `gofmt -w <file>`, then re-run
build/vet/tests — formatting-only, but siblings may share the file.
Add `gofmt -l` on touched dirs to the leaf verification battery whenever
the leaf checklist says "gofmt clean".

## Patch tool mangles the line after old_string when a trailing newline is included

A replace-mode patch whose old_string ends with a trailing newline
(e.g. `func TestX(t *testing.T) {\n`) can splice the NEXT line onto the
signature: `func TestX(t *testing.T) {	logger := ...`. The unified diff
in the patch result shows it immediately — read the diff before moving
on. Fix: re-patch with the mangled single line as old_string, restoring
the newline break. Prevention: never include the trailing newline in
old_string; anchor on the line's own text. gofmt also catches this class
of mangling, so run gofmt before declaring a test-file edit done.

## Catalog loader tests: regression fence + anti-vacuous guard

When a leaf adds a required field to every entry of a data-file catalog
(json5/yaml), the loader test is the fence for FUTURE entries: loop the
parsed file, fail naming the offending entry, and classify entries by
type/transport so a new entry kind can't sneak past unclassified. Always
include an anti-vacuous guard — fail when ZERO entries match the class
being asserted (e.g. stdio count == 0) — so a renamed key, moved file, or
wrong path fails loudly instead of passing trivially. TDD order still
applies: the test fails to compile before the field exists (RED
evidence), passes after (GREEN).
