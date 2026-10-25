# Meept plan trees — session lessons (2026-09-05/06, skill-authoring-and-media-ingest tree)

Authoring session for `docs/plans/skill-authoring-and-media-ingest/`
(master + 5 leaves) that was subsequently executed to completion by a
sibling session. What follows is what the SKILL.md reference files do
not yet cover.

## Compliance scanner on flat meept trees

- Run `check_template_compliance.py docs/plans --strict-leaves` from the
  PARENT dir (meept-flat-plan-trees rule). Add: do this IMMEDIATELY after
  writing the tree, before presenting it — exact-heading misses cost one
  round-trip each when caught late. Masters want `## Open Questions`
  (recommended, not required); leaves need the dispatch header,
  Self-Verification Checklist, Review Checklist, and a Do-NOT-commit line.
- The full-scan output includes OTHER trees' failures. Do not silently
  patch sibling trees as a drive-by; report them, or get user blessing
  and delegate the multi-tree fix to a subagent (a subagent's fresh full
  scan caught 2 additional failures the first targeted run missed).
- CJK scrub before commit: the ascii pre-commit hook blocks
  CJK/Hangul/fullwidth ranges. `grep -rlP '[\x{4E00}-\x{9FFF}]' <tree>/`
  must return empty.
- Spot-check anchors against HEAD (`grep -n` each named line/symbol).
  Plans citing `components.go:856` age in hours on an active repo.

## Writing contracts against REAL code (the session's core lesson)

Five contract defects the implementer had to deviate from — all were
avoidable by grepping before writing the master:

1. `Execute` signature: wrote `Execute(ctx, args json.RawMessage)` in a
   leaf; the repo's Tool interface is
   `Execute(ctx, args map[string]any)`. Read `internal/tools/interface.go`
   FIRST.
2. `new_string` marked "required" in the schema contract while the prose
   said "may be empty to delete" — self-contradiction caught at review.
   Schematics and prose must agree.
3. Duplicate-detection sketch assumed a Writer API shape that does not
   exist (SHA dedup under a different name). Write "reject duplicates
   using the Writer's existing dedup semantics; read writer.go and
   mirror its behavior" instead of inventing the mechanism.
4. Attributed `scanTier`/`loadSkillFile` to `discovery.go`; they live in
   `source_file.go`. File lists in leaves rot; prefer "grep for the
   symbol" over "go to file:line" for anything not read that session.
5. Assumed a `Tools` config struct for the new `[transcript]` section;
   no such struct exists — the section went top-level. Check schema.go
   for the actual nesting before naming config paths in contracts.

## The 'completed ≠ verified' execution handoff

A sibling session executed all 5 leaves and flipped the tracking table
to COMPLETE while this session was idle. Verification protocol that
worked (and found the tracking table's deviation notes accurate):

- Do NOT trust the tracking table. Verify each leaf contract against
  HEAD: constructor signatures, tool names, security seed rules
  (seed_rules.go risk classes), wiring call sites (grep components.go),
  shipped skill parse, config defaults.
- Run the gates yourself: `go build ./...`, scoped `go test` per touched
  package. The tree may have been red when they finished and green when
  you check (or vice versa — sibling WIP races constantly).
- Read the tracking table's Deviations column — the implementer's
  deviations are the honest map of where the plan was wrong, and they
  are review-relevant (which parts of the contract are NOT in force).

## User rules reaffirmed this session

- Temp artifacts NEVER in the source tree — /tmp always. (Quarantine
  `internal/auditlog_tmp/`, `scratch/cfgprobe/`, `control.txt`,
  scratch `cmd/` probes via `mv` to /tmp, never delete.)
- Discrete commands; user denies compound one-liners and probes.
- When the user asks "what issues were found that weren't mentioned",
  they want the full unflattering inventory: own plan defects, sibling
  in-flight risks, hygiene (stray dirs, generated-doc drift, stash
  pileup) — each with disposition.
