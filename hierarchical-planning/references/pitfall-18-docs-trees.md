# Pitfall 18 - Docs Trees: Extend the Corruption Check, Drop Code-Only Steps

When to use: authoring or reconciling a plan tree whose deliverables are documents (.md specs, GDDs, audits) rather than code.
Lesson: the same tree structure works, but the corruption-check glob gains *.md and test/build/format steps are replaced by cross-reference verification.

When the plan tree authors or reconciles DOCUMENTS (e.g. a GDD of .md files) rather than code, the same structure works with two adjustments:

1. **The line-number corruption check (Pitfall 12) must include `*.md`:**
   `grep -rcE '^\s+[0-9]+\|' --include='*.md' <tree> .`
   `write_file`/`patch` on markdown can still bake `  N|` prefixes if a leaf agent feeds `read_file` output into a doc.

2. **TDD, build/test runs, and `gofmt`/`prettier`/`ruff` normalization do NOT apply.** Replace "run tests" with:
   - verify cross-references resolve to existing files (loop the cited paths, confirm each exists)
   - confirm no broken relative links

Leaves still must NOT commit; the orchestrator reviews in-session and commits. Review checklists in doc trees swap "tests pass" for "cross-references resolve" and "no contradictions introduced."
