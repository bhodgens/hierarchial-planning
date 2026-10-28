# Cconcurrent leaf dispatch
When to use: dispatching leaves while one is in flight.
Lesson: concurrency-group rules and safe overlap conditions.

# Concurrency: dispatching additional leaves while one is in flight

When the user says "continue on additional leaves concurrently", do NOT wait
for the in-flight leaf to finish. Instead:

1. Read the tree's Concurrency and Shared-file warnings sections (in
   `master.md`) and identify which NOT_STARTED leaves have NO file overlap
   with the running leaf AND no unmet dependency.
2. Dispatch only the safe ones. For each, add hard constraints to the
   subagent context: which paths are read-only for it, that shared files
   (e.g. a changelog another agent appends to) must be re-read immediately
   before writing and appended to, never rewritten, and that any
   reconciliation with in-flight leaves must be recorded as a "pending"
   subsection rather than invented.
3. Docs-only leaves are almost always safe to parallelize with code leaves —
   they touch disjoint trees. Say explicitly why blocked leaves stay blocked
   (shared files, unmet deps) so the user can see the plan.

Example (rebellion-the-game tree 28): leaf 01 running on
sidecar/internal/schedule; leaf 04 docs-only dispatched concurrently with a
no-sidecar-writes constraint plus a pending-reconciliation section; leafs
02 (shared resolver.go) and 03/05 (depend on 02) held back.

## Wave-1 batch dispatch: shared-package + shared-config contention (2026-09-05)

meept `docs/plans/20260905-research-audit-tools/` dispatched 5 leaves in
parallel across 2 branches. Contention surfaces and the dispatch-context
lines that handled them:

1. **Same Go package, different files.** Four leaves wrote into
   `internal/tools/builtin/` concurrently. Disjoint file lists are
   necessary but NOT sufficient — sibling `go build`/`go test` runs see
   each other's half-written files. Bake into each dispatch context:
   "Your diff is <files> ONLY" + "Another agent is concurrently adding
   <sibling files> to this package — do not touch or be surprised by
   those files." Never let a leaf fix package-wide breakage; that is
   in-session review work.
2. **One config file, two logical entries.** Both mcp-catalog entries
   went in ONE leaf. Two agents editing the same file concurrently is a
   lost-update race no scope fence prevents. Rule: one file → one leaf.
3. **A seam one leaf needs is owned by a parallel leaf.** xlsx leaf
   consumes `SheetSpec` from the csv leaf, both in Wave 1. Conditional
   protocol in the dispatch context: check with search_files whether the
   sibling file landed; if not, create a MINIMAL placeholder containing
   ONLY the missing struct, flagged in the report for orchestrator
   reconciliation. Contrast with the pdf branch: leaf 02 needs leaf 01's
   BEHAVIOR, so that is a true dependency → Wave 2, no placeholder.
   Distinction: missing type stub → placeholder; missing behavior →
   sequential wave.

Orchestration notes: 5 background dispatches return independent
delegation_ids — continue other work, review each notification as it
lands, no polling. Encode wave assignment in the master's Child Index
so dispatch order is re-derivable from plan docs alone. Size-annotate
each leaf; when notifications arrive, review the largest leaf's output
first (highest timeout/quality risk).
