# Dispatching contract-coupled sibling leaves (classi-fly tree, 2026-09-11)

Session-proven additions to the pitfalls list. Context: a Go runtime package
plus Python tooling, four leaves touching adjacent files of one module,
dispatched as one concurrency wave. SKILL.md was over the 100K cap when this
was written, so this block lives here instead of the pitfalls list.

## RED-BUILD-BLOCKED as a valid leaf-return state

When leaf B compiles against leaf A's not-yet-landed types (e.g. B is the CLI,
A owns the loader's public API):

- Brief B to author to the frozen contract signatures, build its own test
  fixtures from the contract spec (hand-crafted bytes, not A's loader), and
  return RED-BUILD-BLOCKED if the tree still does not compile after one retry.
- Explicitly forbid B from touching A's package. Reconciling edits then happen
  in exactly one place: the orchestrator's in-session review.
- Outcome on this tree: three leaves finished in parallel that would otherwise
  have serialized on one shared Go package. B's code needed zero contract
  changes when A landed.

## Parallel leaves drift on shared assumptions

One three-leaf wave produced three cross-leaf conflicts:

1. A Go container loader that rejected the Python side's uncompressed
   fixtures (each side assumed the other's payload framing).
2. A sidecar handler omitting `format`/`version` header fields that a
   sibling's contract test asserted.
3. A decision function with a semantic hole (empty-label agreement) exposed
   only once the sibling's real types existed.

Pattern: each is small, none is a leaf failure, and all are fixed by the
orchestrator in-session, committed with the wave, and disclosed in the commit
message. Budget review time for this; parallel dispatch trades leaf conflicts
for wall-clock.

## Verification leaves must refute, not confirm

Brief verification leaves to empirically test the orchestrator's own hand-off
claims, not just the code. On this tree the verify leaf disproved the
orchestrator's "orientation bug only wrong when N==K" exception with a
seed-pinned repro (wrong at N==K too - a fitted W is not symmetric). Hand-off
claims are paraphrases; a verifier that only confirms them inherits the drift
(Pitfall 21 applied to the orchestrator itself).

## Orchestrator mid-execution debugging protocol (owner constraint)

The owner denies compound shell commands, /tmp probe scripts, and mid-run
heredoc probes. Accepted pattern for diagnosing leaf failures in-session:

1. Write a throwaway test INSIDE the package under investigation
   (`probe_x_test.go`, `probe_test.py`) that calls the suspect function and
   `t.Logf`s the distilled result.
2. Run it with one single command; read the distilled output.
3. Delete the probe before committing anything.

Diagnose-by-test beats diagnose-by-script: it uses the package's own imports,
runs under `go test`, and leaves nothing behind.

## Cross-language artifacts need a byte-level interop test

The Go artifact writer and Python readers agreed on paper but disagreed on
payload field order; a leaf caught it by writing a Go artifact and parsing it
with the Python reference implementation in one test - which then exposed a
second, real bug (a swapped read order) for free. Rule: any shared binary or
JSON contract consumed from two languages gets one producer-writes /
consumer-parses round-trip test in the leaf that builds the producer.
