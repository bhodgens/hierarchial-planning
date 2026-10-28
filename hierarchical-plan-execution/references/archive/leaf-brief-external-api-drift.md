# Lleaf brief external api drift
When to use: leaf briefs cite external API docs.
Lesson: verify the docs before writing tests; versions drift.

# Leaf Brief External-API Drift — Verify the Docs Before You Write the Tests

Leaf briefs that cite an EXTERNAL dependency's API from the plan-author's
memory get signatures wrong in one specific, recurring way: omitted error
returns. The brief usually contains a "verify API from source / trust go
doc over this brief" task — but under TDD the tests get written FIRST,
from the brief text, inheriting the drift before any go doc check runs.

## Session evidence (2026-09-05, meept research-audit-tools tree, xlsx writer leaf)

- Test cases written from the brief implicitly used
  `f.GetCellValue(sheet, cell)` returning a bare string and
  `f.GetCellStyle` returning a bare int. Actual excelize v2.11.0: both
  return `(value, error)`. Seven test call sites needed rework after the
  first compile.
- Brief named the fill type `StyleFill` — no such symbol; it's the
  `Fill` struct (`Style.Fill`).

**Rule:** the brief's "trust go doc over this brief" instruction applies
to the TESTS, not just the implementation. Sequence fix: run
`go doc <pkg>.<Symbol>` for every external function the test cases will
touch BEFORE writing the test file. RED-from-the-brief is fine for
behavior and count expectations; signatures come from the doc, never
from the brief.

## The sentinel-return trap (worse than a compile error)

Some Go APIs signal "not found" with a sentinel VALUE and a nil error.
Code that checks only `err` compiles clean and then spins or misbehaves
forever.

Real case: excelize `(*File).GetSheetIndex(sheet string) (int, error)`
returns **-1** when the sheet doesn't exist — WITH a nil error (the doc
text says so; the signature does not). A sheet-name dedupe helper written
as `if _, err := f.GetSheetIndex(name); err != nil { return name }`
compiles, reads plausibly, and produces an INFINITE LOOP hunting for a
free name (every candidate "exists" because err is always nil). Caught
only because the test binary hung burning CPU (6:50) on a single test
case.

**Rule:** for every existence check against an external API, read the
not-found contract in go doc and assert the sentinel explicitly, e.g.
`if idx, _ := f.GetSheetIndex(name); idx < 0`. Never infer "absent" from
`err == nil`. A test that hangs (not fails) on one case is the symptom
signature of this class.

## Brief row-mapping ambiguity: contract beats the brief's arithmetic

The brief's highlight case implied "HighlightRows=[1] → assert the row-2
cell", but the contract defines HighlightRows as 0-based indices into
Rows, and with headers on sheet row 1 that lands on sheet row 3. The
first test asserted row 2 and failed — the IMPLEMENTATION was correct.

**Rule:** when a concrete cell/row expectation in a brief conflicts with
the contract's own index semantics, pin the test to the CONTRACT
(here: "highlighted style differs from BOTH neighbors and spans the used
width") rather than a magic row number, and comment the index→row
mapping in the test. Diagnose which side is wrong before editing either:
a failing round-trip test can be a test bug, and the neighbor-comparison
form is robust to exactly this ambiguity.

## Parallel-dispatch caveat: sibling owns the shared file

When a leaf brief depends on a type owned by a parallel sibling leaf
(here: SheetSpec from the CSV leaf), the sibling lands MID-SESSION and
overwrites any placeholder you created. After the canonical definition
lands, that file is read-only for you — even if it looks broken (it may
be mid-edit; one sibling file showed transient syntax errors twice
before its final state was clean). Scope discipline for the
implementation leaf: build against the live SheetSpec, never "fix" the
sibling's in-flight file, and run the final gate only after sibling
churn settles (poll `go build ./...` until green rather than fighting
transient breaks).
