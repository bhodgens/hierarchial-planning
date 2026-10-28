# Authoring Session Learnings — multi-tree plan authoring


When to use: authoring plan forests against a large repo with active sibling sessions.
Lesson: ratify understanding with the user BEFORE authoring; record decisions in DECISIONS.md.
Class-level patterns for authoring plan forests against a large repo with
active sibling sessions. Worked example: meept llm-resilience-forest,
2026-08-31 (`references/meept-forest-authoring-2026-08-31.md`).

## 1. Ratify understanding BEFORE authoring (Step 0, user-directed)

When the user says "review the codebase and break these features into
plans," do NOT author trees first. Produce a per-feature briefing:

- what exists today (file:line evidence from real recon, not recall);
- what the proposal changes — current-vs-proposed IN PRACTICE, with a
  worked end-to-end example per mechanism;
- open design questions WITH recommendations and the impact of going the
  other way.

Get explicit per-item ratification before decomposing. Real corrections
that reshaped a forest (2026-08-31):

- "Per-agent, not just per-employee — employees are a type of agent; the
  coder agent is not an employee" → config surface moved to AgentSpec.
- A truncated user sentence ("not sure how to resolve this with regards
  to …") hid a whole requirement — ask for the rest; never guess.
- Terminology alignment: "Ralph loop" (meept's plan-execution verify loop)
  vs the verification hook vs `max_fix_loops` are different mechanisms;
  confirm which one the user means BEFORE picking an interception point.
- "Clearly describe current vs proposed with examples" — the user wants
  worked scenarios, not mechanism summaries, before ratifying.

Record ratified decisions in a `DECISIONS.md` forest sibling with stable
IDs (D1..Dn decisions, source-dated; Q1..Qn open questions with defaults).
Leaves cite decision IDs so review can diff plan against ratification.

## 2. Forest scanner mechanics

See `references/forest-root-scanner-compliance.md` (measured behaviors,
forest-root master.md skeleton, which root to scan). Summary:

- A forest of tree-subdirs + sibling docs needs a thin forest-root
  `master.md` carrying ALL required orchestrator sections.
- Every non-master .md is scanned as a LEAF: sibling docs (DECISIONS.md,
  SHARED-CONVENTIONS.md) must carry a "Do NOT commit" line and, under
  `--strict-leaves`, a self-verification checklist section.
- Dot-dirs and `archive/` must be skipped by the scanner (patch applied to
  `scripts/check_template_compliance.py` 2026-08-31: skip
  `d.startswith(".")` and `d == "archive"` in the tree list).
- Flat-tree repos: scan the PARENT dir; a direct tree-dir run skips leaf
  checks.

## 3. Repairing pre-existing non-compliant trees

A parent-dir scan fails on ANY sibling tree. Mechanical repair (~5 min,
worked on 20260824-unified-theming):

- Master: append missing orchestrator sections. Dispatch Protocol marked
  "COMPLETE — retained as historical record; no further dispatches".
  Integration Test Plan records the gates that ACTUALLY ran. Completion
  Tracking Table mirrors the tree's own historical rows (commits,
  timestamps) — never invent completion claims.
- Leaves: bulk-append Self-Verification Checklist + Review Checklist +
  "Do NOT commit" (template text, minimal risk).
- Distill any existing "Conventions" prose into a `## Coding Conventions`
  section (exact heading required).

## 4. Dispatched-audit loop for post-authoring fixes (user-directed)

When the user says "fix the issues from the observations using subagents
as well as any other architectural or functional issues":

1. Split the observation list: mechanical fixes in-session (scanner
   patches, compliance repair) vs investigations to dispatch (parser
   audits, citation-drift checks, architecture audits).
2. Dispatch ONE read-only subagent per investigation, each with: the
   exact question, files/lines to check, "verify against current HEAD —
   sibling sessions land commits mid-session", an explicit REPORT SHAPE,
   and rules (no edits, no commits, cite file:line, no read_file for
   source).
3. After digesting reports, run the verification yourself (re-run the
   scanner; grep that corrections landed) before reporting done.

## 5. Skill-maintenance note (2026-08-31)

SKILL.md exceeded the 100k patch limit — body patches are refused. New
class-level guidance goes into references/ files; keep this file as the
entry point. Also: `skill_manage write_file` requires `file_content=`
(not `content=`) and `file_path=` — a wrong kwarg silently writes
"placeholder" content or errors; verify the written file with
`skill_view(file_path=...)` after writing.
