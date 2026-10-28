# Plan-Authoring Verification & Snippet Quality


When to use: flat-leaf trees, snippet quality, scanner blind spots.
Lesson: treat '(forest root): OK' as a no-op; plan snippets must be final-form, not drafts.
Home for hierarchical-planning lessons that postdate the SKILL.md pitfalls
list. SKILL.md is over the 100K patch limit, so new pitfalls land here until
a curator pass splits the file. Cross-reference: `anchor-verification-sweep.md`
(same directory) for the pre-authoring anchor checklist.

## Pitfall A — Flat-leaf trees defeat the compliance scanner

`scripts/check_template_compliance.py` walks for `master.md`/`orchestrator.md`
files. When a single tree stores leaves as FLAT files in the plan root
(`master.md` + `01-x.md` + `02-y.md`, no subdirectories — the recommended
shape for small features), the script reports:

```
WARNING: no subdirectories found under <plans-root>
  (Is this a plan-tree root? ...)
(forest root): OK (recommended but missing: [...])

ALL TREES COMPLIANT: True
```

…having scanned ZERO leaves, even with `--strict-leaves`. Verified in the
meept tamper-evident-audit-log session (2026-09-05).

**Rule:** treat `(forest root): OK` as a no-op result, not a pass. Hand-grep
the literal headings instead:

- Orchestrator (master.md): `## Architecture Overview`, `## Interface
  Contracts`, `## Dispatch Protocol`, `## Child Index`, `## Review
  Checklist`, `## Coding Conventions`, `## Completion Tracking Table`,
  `## Integration Test Plan` — exact strings, case matters for the scanner
  equivalents (`## Integration Test Plan` and `## Completion Tracking Table`
  especially, see SKILL.md pitfalls 34/36).
- Each leaf: DISPATCH INSTRUCTION header, `## Scope`, `## Dependencies`,
  estimated-context line, `## Interface Contract`, Self-Verification
  Checklist, `## Review Checklist`, and the literal line
  `Do NOT commit. Do NOT run git add.`

One `for f in …; do grep -qiF "$pat" "$f" …; done` loop over the plan dir
covers all of it in a second. Also keep the line-number corruption grep
(`grep -rcE '^\s+[0-9]+\|' <plans-dir>`) — it applies to plan docs too.

## Pitfall B — Plan code snippets must be final-form, not annotated drafts

Never paste a snippet that contains an intentionally-wrong line plus a
"delete this branch" note, or convoluted logic with a "simplify this" note.
Drafting shortcuts in plan code cause the leaf agent to (a) implement the
note instead of the code, (b) ship the dead code because notes get skimmed,
or (c) burn review cycles explaining a diff-vs-spec mismatch.

**Rule:** if you wouldn't commit the snippet as written, rewrite it BEFORE it
enters the leaf. Implementer notes are for genuine unknowns (real enum names
to confirm, signatures to adapt) — marked `ADJUST:` — never for "my example
is deliberately wrong, fix it." Worked example (meept session): a
`case string:` branch holding dead `json.Marshal` code under a delete-me
note was self-caught post-write and rewritten to the final one-liner; the
VerifyChain sketch's convoluted genesis/link logic got the same treatment.

## Known SKILL.md debt (for the curator)

- SKILL.md is 103K chars — over the 100K patch limit — so it cannot accept
  new content until pitfalls are moved out to references/. Candidates to
  move first: pitfalls 40-42 (session-specific sweeps/visual-verification
  detail) and the longest worked-example parentheticals.
- Pitfall 41 ("check disk for partial work before re-dispatching") is a
  near-duplicate of Pitfall 25 ("Subagent timeout → partial work on disk →
  orchestrator completes directly") — consolidation candidate.
