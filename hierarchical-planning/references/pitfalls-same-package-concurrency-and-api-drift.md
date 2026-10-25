# Pitfalls 43-44: Same-Package Concurrency + Leaf-Reported API Drift

Session-derived additions (2026-09-05, meept research-audit-tools tree) that
exceeded the SKILL.md size cap. Numbering continues the SKILL.md pitfalls list.

## Pitfall 43 — Concurrent same-package Go leaves transiently break each other's builds (TDD RED phase)

When two or more leaves write into the SAME Go package concurrently and any
leaf works test-first, its RED phase (test file referencing not-yet-written
symbols) makes `go build ./<pkg>/...`, `go vet`, and even sibling test runs
fail package-wide with `undefined: X`. Observed live: the pdf-core leaf's
landed test file broke the web_fetch sibling's verification mid-flight, and
the CSV leaf's independent re-run was blocked the same way.

Prevention:
1. Include in every Go-leaf dispatch context: "If `go build`/`go vet` fails
   on symbols in files you did NOT create, another leaf owns them — do NOT
   create stubs, do NOT fix, scope your own verification to
   `go test -run <YourSymbolPrefix>` and report the cross-leaf build state
   in your summary."
2. The orchestrator DEFERS whole-package verification (full test run, gofmt
   sweep, U1000 check) until every in-package leaf has returned, then runs
   it ONCE in-session. Per-leaf review before that point is code-read +
   scoped `-run` tests only.
3. If a leaf must compile the package to proceed and a sibling's RED files
   block it, finish the sibling's missing implementation file directly
   (Pitfall 25 completion pattern) rather than stalling — but ONLY the
   missing file, never edits to landed sibling code.

## Pitfall 44 — Verify leaf-reported API drift via `go doc` before accepting it

Dispatch briefs are often authored from memory and can state wrong library
signatures. A leaf agent that reports "the brief's known API shape was
wrong" has produced a hypothesis, not a fact — but it is also frequently
RIGHT. Live example (pdf extraction leaf, ledongthuc/pdf): the brief claimed
`pdf.NewReader(r io.Reader, size)`; the leaf reported `io.ReaderAt`, that
`Page()` returns no error, and that `@latest` resolves to a pseudo-version.
All three were confirmed via `go doc github.com/ledongthuc/pdf.NewReader`
etc. before the leaf was marked REVIEWED. (The lib needs ReaderAt; the leaf
buffered the io.Reader into bytes.NewReader so the frozen seam stayed valid
— the correct resolution pattern.)

Procedure:
1. Run `go doc <pkg>.<Symbol>` for each drift claim. Trust neither the brief
   nor the leaf on authority alone.
2. If confirmed: record the correction in the orchestrator's tracking-table
   notes so the plan documents the REAL API, not the brief's guess.
3. If refuted: re-dispatch the leaf with the go doc output quoted verbatim.

Related: Pitfall 21 (paraphrase-drift) covers plan-vs-spec drift; this
covers brief-vs-reality drift at implementation time.