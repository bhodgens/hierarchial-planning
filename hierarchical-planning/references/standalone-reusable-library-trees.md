# Standalone / reusable-library plan trees

Pattern for when the deliverable is a NEW repo or library that a SPECIFIC host
project will consume, and the user explicitly wants it decoupled ("implement it
independently so X or something else can use it"). Worked example: the
`classi-fly` forest (2026-09-11) - a Go fly-connectome reservoir classifier
built to be consumed by the meept agent daemon without depending on it.

## Why this needs its own pattern

The ordinary forest assumes one project's codebase. Here the tension is the
opposite: the library must NOT know about its consumer, yet it must be trivially
consumable by it. Getting this wrong produces either a leaky library (imports
the host) or an unusable one (no stable interface). The tree shape resolves it.

## The four rules

1. **Freeze the interface contract FIRST, in the root `master.md`.** Before any
   leaf is written, pin the things a consumer touches: the artifact/file format
   (exact field names), the public function signatures, and - if a process
   boundary is involved - the wire shape (HTTP paths + JSON keys). These are
   Contracts 1..N. Every leaf references them; no leaf may rename a field.
   This is what makes the "same core, two faces" design work: an in-process
   call and a sidecar call return the identical result.

2. **Name the consumer in exactly ONE leaf, as an example.** Split the surface
   into (a) a generic core + a generic integration leaf that documents the
   contract, and (b) an optional worked example naming the real host. Every
   other document must be consumer-agnostic. Add a review-checklist line that
   greps the module for the consumer's name and fails if it appears outside the
   example leaf. In `classi-fly` only `07-integration.md` named meept; the
   checklist asserted the library itself stayed generic.

3. **De-risk leaf first, with the license-free path.** Order the tree so the
   cheapest end-to-end proof runs before any external dependency: a synthetic /
   seed-generated input that exercises the full plumbing (build -> pack -> load
   -> classify -> score). Only after that do the leaves that pull real data. In
   `classi-fly` this was the synthetic-reservoir leaf plus the sparse-core
   branch, ahead of the connectome-ingest leaf. Special case worth encoding:
   when a data source carries a restrictive license, make the license-clean
   synthetic path the DEFAULT shipped artifact and demote the real data to a
   benchmark-only tier - then the license question cannot block shipping.

4. **Always include an independent-verification leaf.** Terminal leaf that
   re-derives the headline numbers from per-case data rather than trusting the
   harness summary, audits artifact provenance/licenses, and stress-tests any
   lossy encoding (e.g. int8 quantization vs the float reference). Make it a
   named leaf with its own group so the orchestrator dispatches it last.

## Sizing note

A reusable-library forest is usually ~8-13 documents: root master, a
SHARED-CONVENTIONS sibling, an OPEN-QUESTIONS sibling, one de-risk branch
(orchestrator + 2 leaves), and 5-7 single-purpose top-level leaves (ingest,
generate, train, evaluate, package/CLI, integration, verify). Inline leaf
definitions inside each orchestrator for the non-critical trees; separate leaf
files only for the de-risk branch.

## Compliance-scanner gotcha

Top-level leaf `.md` files in a forest are NOT checked by
`check_template_compliance.py --strict-leaves` (it reports the root and branch
directories, and only the leaves inside those). After the scan prints
`ALL TREES COMPLIANT: True`, hand-verify every flat top-level leaf for the
required elements: DISPATCH header, `## Self-Verification Checklist`,
`## Review Checklist`, and a `DO NOT COMMIT` line. A one-line shell loop over
the flat leaves greps for all four.

## Open-questions ledger

Collect genuine forks (interface shape, language split for offline tooling,
which data source first, default artifact) in one `OPEN-QUESTIONS.md` sibling
with a recommendation and an impact per item. The user resolves these before
dispatch; two or three of them usually gate the de-risk leaf directly (e.g.
"is the public API Go-import, sidecar, or both" fixes Contract 2).
