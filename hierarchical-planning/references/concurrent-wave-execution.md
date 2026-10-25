# Concurrent Wave Execution — pitfalls from the 2026-09-05 meept tree

Session: meept `docs/plans/20260905-research-audit-tools/` (7 leaves, 3 waves,
config + pdf tool + spreadsheet tool branches; all 7 REVIEWED, 6 committed
in-session). Four class-level lessons that extend the SKILL.md pitfall list.

## Pitfall 43 — Same-package parallel leaves break each other's verification

TDD RED-phase test files reference not-yet-written impls. One sibling's WIP
therefore fails `go build` / `go vet` / whole-package tests for ALL siblings
in that package. Observed 3× in one wave:

- csv leaf's verification blocked by pdf leaf's `undefined: extractPDFText`
  (test file landed in RED phase, impl not yet).
- webfetch leaf hit a transient `undefined: rowIdx` from a sibling's partial write.
- xlsx leaf: "parallel agents repeatedly shared/broke the package build mid-run".

Prevention (put in dispatch contexts):
1. Same-package parallel leaves get this sentence: "siblings are adding files
   concurrently; package-level builds may transiently fail — if your own
   files are correct and your focused `-run` tests pass once the package
   settles, report and stop."
2. OWNERSHIP of shared new types is pre-assigned across sibling briefs:
   exactly one leaf defines it; the other may create a minimal placeholder
   (struct only) and MUST flag it in its report. The placeholder gets
   overwritten when the owner lands. (SheetSpec resolved cleanly this way —
   xlsx leaf created a placeholder, csv leaf's canonical file overwrote it,
   xlsx consumed the canonical one without touching it.)
3. The ORCHESTRATOR's own full-package test run AFTER the wave settles is
   the authoritative verification gate. Never mark a same-package leaf
   REVIEWED on the subagent's test output alone — it may have passed against
   a broken intermediate state, or its pass may not reproduce.
4. If RED-pollution outweighs the concurrency win (small package, tightly
   interleaved edits), serialize the leaves instead of dispatching parallel.

## Pitfall 44 — Library-API drift: briefs are wrong, go doc is truth, verify claims

Dispatch briefs that state a library's "known shape" are often wrong:

| Brief said | Actual (go doc) | Consequence / fix |
|---|---|---|
| `pdf.NewReader(r io.Reader)` | `NewReader(io.ReaderAt, int64)` | leaf buffers `io.ReadAll` internally to keep the io.Reader seam |
| `(*Reader).Page(n) (Page, error)` | `Page(n) Page` — no error | bounds-validate pages in the range parser instead |
| excelize `GetSheetIndex` error-returning | returns -1 for missing sheet | first-draft dedupe loop treating -1 as error **spun forever** — caught via hung test run |
| ledongthuc/pdf `@latest` → tag v0.3.0 | pseudo-version, no such tag exists | record actual pinned version in go.mod + report |

Rule for briefs: "verify the API with `go doc <pkg>` before writing code —
trust go doc over this brief; report any drift."

Rule for orchestrator review: re-check every drift claim with `go doc`
yourself before accepting it. The report-writer is the same model class that
wrote the code — do not take its word (this user explicitly expects
code-verified verdicts, not agent self-reports).

## Pitfall 45 — Dependency-license gate in the dispatch context, as a hard STOP

Any leaf that may add a dependency gets, verbatim:

> after `go get`, READ the LICENSE file in the module cache
> (`go env GOMODCACHE`); if GPL/AGPL, STOP and report — do not implement.

User rule behind it: GPL/AGPL is acceptable as subprocess deps (MCP servers,
CLI tools), never linked into shipped binaries. Executed 2026-09-05:
excelize v2.11.0 → BSD-3, agent reported pass — and the orchestrator still
independently read the LICENSE file in the module cache before accepting.

## Pitfall 46 — Single registration sites are serialization points

When multiple leaves each append a block to ONE shared file (meept
`internal/daemon/components.go`, ~8k lines, the only builtin-tool
registration site), do NOT parallel-dispatch them even when otherwise
independent:

1. Serialize registration leaves; commit each wave before dispatching the next.
2. Each later dispatch context says: "a prior agent just modified this file —
   re-read the registration region before editing" (Pitfall 19 stale
   read-state).
3. The leaf brief pins the exact anchor AND a fallback anchor if the first
   hasn't landed, with a note-the-placement instruction.
4. Concurrent appends to one file are how blocks get lost or land in the
   wrong scope; the commit cost of serialization is trivial by comparison.

## Subagent-reliability footnotes (same session)

- Subagents' background shell one-liners can exit 127/TERM mid-run with
  stray marker text (`notify_sent_marker_$?`). Their /tmp verification logs
  were still readable and informative (caught a real failing
  TestWriteXLSXHighlightStyle mid-flight, then its fix), but treat them as
  signals to check, not verdicts.
- One subagent report contained a self-contradiction (claimed file written;
  its own file-mutation verifier listed a mangled-path write failure). The
  orchestrator resolved it by reading the actual file on disk — the standard
  rule: verify claims with your own tool calls, not report wording.
