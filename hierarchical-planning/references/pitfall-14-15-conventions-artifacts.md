# Pitfalls 14-15 - Cross-Leaf Convention Drift and Stray Artifacts

When to use: reviewing output from multiple independent leaf agents.
Lesson: conventions drift and artifacts accumulate; prevent with a dispatch-time conventions block, catch with a review-checklist item plus a global normalizer.

## Pitfall 14 - Inconsistent code conventions across leaves

Independent leaf agents will produce code with different naming styles, import organizations, error-handling patterns, and file headers. Interface contracts cover the API surface but not internal style.

**Prevention:** include a brief coding-conventions block (naming, imports, error handling) in every orchestrator document and pass it in every dispatch context. After integration, run `gofmt`/`prettier`/`ruff` globally to normalize. (For docs-only trees, format normalization does not apply - see Pitfall 18.)

## Pitfall 15 - Stray artifacts from leaf agents

Implementation agents leave debug print statements, TODO comments, placeholder values, commented-out code, and "End of Task" markers in their output.

**Prevention/catch:** add "no debug artifacts, no TODOs, no placeholder values" to the review checklist. Useful greps: `grep -rn 'print(' <pkg>` (should be 0 in Go), `grep -rnE 'TODO|FIXME|not_implemented'` on the leaf's files. For deeper prose-level checks beyond the compliance scanner, see `references/prose-artifact-sweep.md`.
