# Lleaf spec drift line refs
When to use: leaf line references went stale.
Lesson: verify line anchors before patching.

# Leaf Spec Drift: Verifying Line References Before Patching

Leaf docs in plan trees frequently embed pre-computed line references, e.g.
"swap site at funding.go:770" or "struct field :74". These are snapshots taken
at planning time and go stale the moment ANY sibling leaf lands in the same
file — even a few inserted lines shift every later ref.

## Rule: locate by content, not by line number

1. Re-locate each documented site with a symbol/content grep before patching:
   `grep -n "h\.StripeClient" backend-api/internal/handlers/*.go`
2. Confirm the MATCH COUNT against the leaf's claim ("14 call sites"). If the
   count differs, stop and reconcile: either a sibling leaf already touched
   some sites (re-read the leaf's dependency list) or the leaf under-counted.
3. Treat the leaf's site list as an INVENTORY OF LOGICAL SITES (function name +
   operation), never as literal offsets.

## Reporting drift

Record shifted refs in the completion report under "Deviations from spec",
numbered, e.g.: "Line refs shifted ~15-30 lines from spec due to sibling-leaf
edits upstream in funding.go; all 14 logical sites covered." Review agents
checking "line-site list fully covered" then have an audit trail.

## Test-construction updates ("update construction only, never assertions")

When a leaf says existing tests must pass UNCHANGED but constructor signatures
change:

- Check whether nil args are type-compatible with the new signature FIRST.
  Swapping `*StripeClient` for `*payments.Router` keeps `nil` valid — suite
  files may need NO edit at all.
- A no-op edit is safer than a cosmetic one: a patch that collapses two lines
  into one (missing newline) produces a syntax error in a file you "didn't
  change". If you must touch a suite file, diff it afterward and expect the
  diff to be empty or purely mechanical.

## Mechanical-swap hygiene in large files

- For 1k+-line files (funding.go was ~5.8k lines), use grep to find sites, read
  ±40 lines of context per site, then patch with unique surrounding context so
  fuzzy matching can't hit the wrong occurrence of near-identical code blocks
  (e.g. three handlers each containing the same EnsureCustomer error-handling
  stanza).
- When several INSERT/SELECT statements look alike across handlers, include
  enough neighboring comment text in old_string to guarantee uniqueness.
