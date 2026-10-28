# Compliance Scanner — Exact Required Headings


When to use: authoring docs that must pass check_template_compliance.py.
Lesson: exact required heading strings; near-synonyms fail and cost a fix round-trip.
`scripts/check_template_compliance.py --strict-leaves` matches section
headings by EXACT string. Plausible near-synonyms fail and cost a fix
round-trip (observed 2026-08-18, rebellion tree 26: "Completion Tracking",
"Integration Review Plan", and a bare "Children" table all flagged).

Forest-level scanner mechanics (forest-root master.md requirements,
sibling docs scanned as leaves, dot-dir/archive skip patched into the
script 2026-08-31): see `references/forest-root-scanner-compliance.md`.

## master.md / orchestrator.md — REQUIRED sections

- `## Dispatch Protocol`
- `## Child Index` (a plain "Children" heading is NOT accepted)
- `## Coding Conventions`
- `## Completion Tracking Table` (NOT "Completion Tracking")
- `## Integration Test Plan` (NOT "Integration Review Plan")
- `## Review Checklist`
- `## Interface Contracts` (also matches singular "## Interface Contract")
- `## Test Gate` (tests-first gate; added 2026-10-24. Docs-only/ops trees keep
  the heading and write `N/A — <tree type>` + the substitute verification,
  so the omission is always deliberate)
- Recommended: `## Open Questions`

## Leaves — required elements

- DISPATCH INSTRUCTION header (tells any agent to implement it, do NOT commit)
- Parent / scope / dependencies / estimated context
- Complete tasks (TDD, exact file paths)
- Interface contract section (what the leaf exposes to siblings)
- `Self-Verification Checklist`
- `Review Checklist` (for the review agent)
- `Do NOT commit` instruction

## Workflow

Write headings to these exact strings on the FIRST pass, then run:

```bash
python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py plans/<tree> --strict-leaves
```

until it prints `ALL TREES COMPLIANT: True`. Branch orchestrators are the
most common miss — they inherit master.md habits (tracking tables, review
plans) under slightly different names.
