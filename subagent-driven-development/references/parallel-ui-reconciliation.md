# Parallel Dispatch on One Feature: Blind-Write Reconciliation

When to use: parallel dispatch on one UI feature (HTML/CSS/JS split across siblings).
Lesson: blind selector mismatches are predictable - pin the markup/CSS contract on disk or in both briefs, or sequence the consumer into a later wave.

Validated in production: a 5-task static-site build (HTML + CSS + 2 JS + assets)
dispatched as parallel sibling leaves. Two integration bugs surfaced at review,
both structural and both predictable:

1. **Blind selector mismatch.** The CSS sibling wrote `header.site-header`,
   `.nav-links`, `.hero-ctas`  -  class names anticipated from the plan prose.
   The HTML sibling shipped bare `<header>`, `#navLinks`, `.hero-actions`.
   Every mismatch had to be reconciled after both landed.
2. **Orphaned integration.** Neither sibling's task spec included the
   `<script src>` tags that load the JS. No task owned the wiring, so the gap
   was only visible when both files existed.

## Prevention (do this at dispatch time)

- **Pin the class-name contract.** When siblings write files that reference
  each other's markup/symbols, put the EXACT names in every brief: selectors,
  ids, function signatures, event names. A sibling that knows the contract
  cannot guess. This is the same technique as the API-surface pre-read for
  integration tasks  -  extend it to CSS selectors and DOM ids.
- **Assign the wiring explicitly.** Add a final task (or reserve it for the
  orchestrator) that owns cross-file glue: script tags, imports, manifest
  entries, route registration. "Nobody's task includes it" is how it gets lost.
- **Sequence only the truly dependent pair.** If one file must match another's
  names and the contract can't be pinned, dispatch them serially instead  - 
  the second reads the first on disk.

## Cure (when the wave already ran blind)

Reconcile with a count-asserted scripted batch, not hand edits:

- Build an exact find/replace list mapping anticipated names to actual ones.
- In ONE scripted pass: assert `count(old) == expected` for every pattern;
  if ANY assertion fails, abort before writing (fail-clean, no partial state).
- One known trap: a validation hunk whose old-string assumes an earlier hunk
  already applied. Keep hunks anchored on the ORIGINAL file text and apply
  sequentially.
- Verify after write: brace/paren balance, zero leftovers of old names,
  syntax check (`node --check`) on JS.
- Commit the reconciliation as its own `fix(...)` commit naming the cause.

Blind CSS vs HTML on a static site reconciled in ~40 replacements this way.

## Related failure: long-write degradation during plan authoring

A plan document written in one large `write_file` call (~26KB with embedded
code blocks) degraded mid-generation: mangled sentences, duplicated section
headers, corrupted code fragments landed in the saved file. The same risk
applies to any long single write (plans, big files).

- **Recovery:** never patch on top of noise  -  rewrite the file WHOLESALE in
  one clean, compact write, then search for the known-mangled fragments to
  confirm zero remain.
- **Prevention:** cap embedded code in generated documents (~100 lines or
  less); larger artifacts get a precise spec (gates, structure, dials) plus at
  most a short skeleton. For plan documents this also keeps them readable.
- Mid-generation corruption can also hit `delegate_task` context strings  - 
  a corrupted dispatch fails schema validation client-side (that is the good
  case; nothing half-runs). Re-dispatch compact.
