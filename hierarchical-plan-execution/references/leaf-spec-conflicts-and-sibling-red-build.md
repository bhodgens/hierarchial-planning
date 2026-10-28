# Lleaf spec conflicts and sibling red build
When to use: spec conflicts + sibling RED builds.
Lesson: bare-heading compliance, pinned-case sizing math, LSP-filtered verification, blocked-leaf reports.

# Leaf-spec conflict adjudication + sibling-RED build transients (plan-compiler leaf 03, 2026-09-06)

Session: implemented EmitTree (leaf 03 of meept `docs/plans/plan-compiler`) in
direct single-leaf implementer role while sibling leaf 02 (CompileSealed) was
IN FLIGHT in the same package. Four durable patterns, all reusable.

## 1. Exact-line compliance scans force BARE headings

Leaf contract: "EmitTree output passes sectionPresenceCheck" where the check
is exact `## <name>` per line, and the test pins bare names
(`"## Interface Contracts"`, `"## Review Checklist"`). House style decorates
headings: `## Interface Contracts (frozen)`, `## Review Checklist (root)`,
`## Interface Contracts (From Parent)`. A first draft using decorated
headings FAILS the pinned exact-line list even though a human reads the
section as present.

Adjudication: the testable compliance guarantee wins. Decorations move into
body text ("Frozen. One contract per phase..." / "From parent, frozen:" as
the first body line). Rule for any emitter/doc-generator leaf: grep the
leaf's pinned section list FIRST and emit every scanned heading as the bare
pinned string; qualifiers and prose go below the heading. Cross-ref:
spec-test-expectation-mismatches.md Failure Mode 6 (normative text wins) —
this is the heading-specific flavor of it.

## 2. Hand-simulate sizing/partition math against the PINNED cases before implementing

The leaf pinned a ceil-formula "per-leaf share" AND test cases that contradict
its literal reading:

- 2 steps, MaxLeavesPerPhase 3 ⇒ FLAT (pinned). Literal ceil says per-leaf
  share = ⌈2/3⌉ = 1 < 2 ⇒ "tree". Contradiction.
- "3+2+1-step fixture ⇒ 6 leaves" was a first-draft intuition; the sizing
  formula actually yields 3 leaves ([3],[2],[3]).

Resolution that satisfies ALL pinned cases, written into the code as comments:

- Gate "phase fits" = steps ≤ MaxLeavesPerPhase (one leaf under the sizing).
- Partition share = min(n, ⌈n/cap⌉): a ≤cap phase stays ONE leaf; larger
  phases spread over exactly cap leaves.

Lesson: before writing the emitter, run the formula on paper for every pinned
case and pick the interpretation consistent with all of them; leave the
derivation as a comment so review can re-check. Fixture leaf-counts come from
the formula, never from intuition.

## 3. Sibling's RED test file breaks the package build through no fault of yours

Symptom: `go test ./internal/plan/` fails with ONLY
`undefined: CompiledPlan / PhaseSpec / StepSpec` — the sibling leaf's pinned
Contract B types, which the leaf's CAUTION clause says NOT to define
yourself. Their `compiler_test.go` (RED) landed minutes before their
`compiler.go`; the package is unbuildable in the interim.

Verification fallbacks that need no sibling types:

- `gofmt -l <files>` + `gofmt -e <file> >/dev/null` — formatting + SYNTAX
  validation without type resolution.
- LSP `go diagnostics` per file, filtered by error class: every diagnostic
  must be `undefined: <sibling type>`; ANY other diagnostic is your bug.
  Derive the sibling-symbol list from the leaf doc's contract block.
- `go build` / `go test` remain AUTHORITATIVE — LSP diagnostics were observed
  STALE once this session (reported clean while go build still failed).

Then: bounded poll for the sibling's file (two ~2-min polling loops here),
and if it does not land, close with the leaf's blocked-run report (below)
rather than improvising workarounds.

## 4. Do NOT build an out-of-repo overlay sandbox to unblock yourself

Tempting move: copy your two files to /tmp with stub sibling types + a mini
go.mod and run the suite there. This session the user DENIED that command
(consent class: temp verification harnesses outside the repo — consistent
with the standing denial pattern in the SKILL.md body). Protocol holds: stop
the command class, no rephrase-and-retry. Substitute §3's static checks plus
an honest blocked-run report; the sibling landing is the real unblock and
the overlay proves nothing the in-repo run won't.

## 5. Blocked-leaf finish report shape (worked; reuse verbatim)

- Status line: implementation complete; final run blocked by sibling's
  in-flight pinned types (documented transient, leaf CAUTION anticipated it).
- Files created (exact list, nothing staged/committed).
- Final test output VERBATIM (the undefined-symbol build failure is itself
  evidence — every error is a sibling type name, zero own-code errors).
- LSP diagnostic class-filter result as corroborating evidence.
- Deviations list with rationale (bare headings per §1; gate threshold read
  from the task brief over the leaf's Contract D phrasing — flag for review;
  budget-beats-cap split semantics).
- STOP item naming the exact unblock condition ("sibling's compiler.go").

Related: direct-single-leaf-execution.md, leaf-verbatim-contract-messages.md,
sibling-plan-execution-collision.md (inverted-collision addendum).
