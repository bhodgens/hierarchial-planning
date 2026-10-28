# Forest-Root Scanner Compliance (multi-tree forests)


When to use: authoring multi-tree forests that must pass the compliance scanner.
Lesson: forest-root master needs ALL orchestrator sections; sibling docs are leaf-checked.
The template compliance scanner (`scripts/check_template_compliance.py`)
has three behaviors that bite when you author a FOREST — a directory of N
tree subdirs plus sibling reference docs — rather than a flat tree.

## Scanner behavior (measured 2026-08-31, meept llm-resilience-forest)

1. **A forest without a root `master.md` fails.** Running the scanner on
   the forest's parent reports:

   `<forest>: ERROR no master.md or orchestrator.md — files: [...]`

   Fix: write a thin forest-root `master.md`. The scanner then checks it
   as an orchestrator, so it must contain EVERY required section even
   though most are one-line delegating stubs (contracts → point at
   SHARED-CONVENTIONS.md; dispatch protocol → per-tree masters;
   conventions → "delegated"). ~40-60 lines total is enough. A stub with
   only Goal/Index/Tracking fails with:
   `MISSING required sections: ['## Dispatch Protocol', '## Interface
   Contracts', '## Child Index', '## Review Checklist', '## Coding
   Conventions', '## Integration Test Plan']`.

2. **Sibling reference docs are scanned as LEAVES.** Any `.md` that is
   not `master.md`/`orchestrator.md` gets `check_leaf` — so
   `DECISIONS.md` and `SHARED-CONVENTIONS.md` fail `--strict-leaves`
   with `MISSING leaf markers: ['Do NOT commit', 'Self-Verification
   checklist']`. Fix: give each sibling (a) a "Do NOT commit ... the
   forest orchestrator commits it with the tree dispatches" line and
   (b) a short "## Self-Verification Checklist (forest-level)" section.
   Both read naturally in these documents; this is not contortion.

3. **Per-tree masters missing `## Open Questions` produce a WARNING,
   not a failure** (`OK (recommended but missing: [...])`). Centralizing
   open questions in the DECISIONS.md sibling is a valid pattern; accept
   the warning and note why.

## Which root to run the scanner on

- **Flat tree** (master.md + leaf files in one dir): run on the PARENT
  (see `meept-flat-plan-trees.md`) — a direct run skips leaf checks.
- **Nested forest** (per-tree subdirs each with master.md + leaves):
  run on the FOREST DIR directly once the root master.md exists. The
  parent run then reports ERROR lines for UNRELATED pre-existing trees
  (archive/, abandoned dirs) and `ALL TREES COMPLIANT: False` from
  their noise — that failure is not yours.

Recommended: run BOTH — the parent run grepped for your forest's name,
and the direct run for the authoritative `ALL TREES COMPLIANT: True`.

## Repairing PRE-EXISTING non-compliant trees (2026-09-01 pattern)

A parent-dir scan surfaces OLD trees failing compliance (e.g. meept
`20260824-unified-theming`: master missing 5 orchestrator sections, 6
leaves missing leaf markers). When the user asks to fix "the issues":
1. Check whether the tree is COMPLETE first (tracking table / STATUS
   header). If complete, add the missing orchestrator sections as a
   HISTORICAL RECORD — a `> This tree is COMPLETE` note above the
   Dispatch Protocol, conventions lifted from what the tree actually
   did, and the tracking table copied from the historical rows. Never
   fabricate process sections that imply future dispatches.
2. Leaves get the standard Self-Verification + Review checklists and the
   Do-NOT-commit marker appended (bash heredoc loop over the leaf files
   is fine — they are plan docs, not source).
3. Scanner skips for non-tree dirs (dot-dirs, `archive/`) were added to
   the script itself (2026-09-01) — the `archive/` skip is intentional;
   archived plans are not held to the template.

## Audit-record siblings are scanned as leaves too

An audit record written into the forest dir (e.g.
`ARCH-AUDIT-2026-09-01.md`) is a non-orchestrator `.md`, so
`--strict-leaves` demands the leaf markers from it as well. Two-line fix
that reads naturally: a "Do NOT commit this file independently" line and
a short "## Self-Verification Checklist (audit-record)" stating it is
documentation, not a dispatchable leaf. Confirmed passing 2026-09-01.

## Forest-root master.md skeleton (copy and fill)

- **Meta:** Role "Forest root (structural wrapper)"; children = tree dirs.
- **Child Tree Index:** table of tree / scope / depends-on / leaf count.
- **Interface Contracts:** one paragraph pointing at SHARED-CONVENTIONS
  §4 (frozen cross-tree contracts live there, not here).
- **Dispatch Protocol:** numbered — read siblings first; dispatch
  independent trees in parallel; the gating rule (e.g. tree 03 after
  tree 02); the stagger rule for trees touching the same package.
- **Review Checklist:** tracking-table gates, full-suite commands
  (`go build ./... && go test ./...`, `make lint-ci`), line-number
  corruption grep, AGENTS.md same-commit rule.
- **Coding Conventions:** "Delegated — see SHARED-CONVENTIONS §1-§3".
- **Integration Test Plan:** forest-level E2E + lint + graphs +
  open-question reconciliation.
- **Completion Tracking Table:** one row per TREE (the tree masters
  track leaves).
- **Open Questions:** one pointer line to the DECISIONS.md sibling.

## Why the root master is worth it anyway

Beyond scanner compliance, the forest root is where cross-tree dispatch
order, package-stagger rules, and forest-level review gates live — the
per-tree masters cannot see each other. Worked example: meept
llm-resilience-forest (2026-08-31) — 5 trees / 18 leaves; root master
encodes "trees 01/04/05 parallel, 01 and 02 staggered (shared packages),
03 gated on 02 COMPLETE".

Scanner rule of record (script, `is_orchestrator`): a file is an
orchestrator iff its name is exactly `master.md` or `orchestrator.md`;
every other `.md` in the tree is checked as a leaf.
