# Parallel sibling-contract leaves (dispatch pattern)


When to use: later leaves compile against siblings' in-flight contracts.
Lesson: file-ownership partitioning and the RED-BUILD-BLOCKED protocol.
From the classi-fly forest (2026-09-11): 8 leaves, Go + Python mixed, wave-based
dispatch where later leaves compiled against siblings' in-flight contracts.
All patterns below proven in that run.

## File-ownership partitioning

When multiple leaves touch one package (e.g. cmd/classi-fly owned by both the
CLI leaf and the sidecar leaf), every dispatch brief lists the EXACT files that
leaf owns and names sibling files as forbidden. Partition by file, never by
"yours to write, theirs exists too". Zero collisions occurred under this rule.

## RED-BUILD-BLOCKED protocol

When leaf B compiles against sibling A's not-yet-landed types:

1. Brief says: author to the frozen contract (signatures pinned in the brief),
   retry `go build` once after finishing all files, and if still red report
   RED-BUILD-BLOCKED without touching sibling files.
2. Orchestrator compiles the whole tree after both land; residual mismatches
   are orchestrator fixes, not re-dispatches.

Worked 2/2 (CLI leaf and sidecar leaf both landed RED-BUILD-BLOCKED and needed
zero changes to their own files once the format leaf landed).

## Expect 2-3 cross-leaf fixes at integration

Parallel siblings honoring the same frozen contract still produce mechanical
mismatches. Observed in one forest: (a) Go loader rejected Python-written
raw-payload fixtures (see interop below), (b) sidecar /info response missing
header fields a contract test expected, (c) judge example routing on an empty
label. The orchestrator's integration pass must run the FULL test suite and
fix contract-level gaps in-session before committing.

## Cross-language binary-contract interop

When Go writes and Python reads one frozen binary format (or vice versa):

- Dispatch a cross-language round-trip verification inside the format leaf
  itself: Go WriteFile output parsed by the Python reference reader, outputs
  compared. This caught a payload-order bug that intra-language tests missed.
- Optional compression libraries (zstd) may be absent on one side. Readers
  must auto-detect raw vs framed payloads: zstd frame magic is 28 B5 2F FD;
  a payload not starting with that magic is stored raw. Both readers and the
  Go container need the fallback, and the deviation must be documented.

## Contract evolution is append-only and master-owned

Adding a field (e.g. a `decay` header extension discovered necessary because
the Python trainer and Go runtime must agree on the leak term):

- Edit the master.md contract section, not leaf files silently.
- Document the extension in the Header/type doc comment.
- Give every consumer a safe default so older artifacts keep loading.

## Compliance scanner flat-layout blind spot (reminder)

`--strict-leaves` scans master.md and branch directories only. Top-level leaf
files sitting flat in the tree directory are NOT scanned. Hand-verify each
with grep for "DO NOT COMMIT", "## Self-Verification Checklist",
"## Review Checklist" before committing the plan.
