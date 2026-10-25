---
name: design-plan-consistency
description: "Maintain convergence between design documents (GDD, specs) and implementation plan trees. Governed by binding procedural rules at the project level (AGENTS.md) — changelog discipline, pre-plan drift checks, a central implementation record, and automatic plan-stale detection when the design moves under it."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [governance, consistency, gdd, plans, changelog, drift, workflow]
    related_skills: [hierarchical-planning, hierarchical-plan-execution, writing-plans, code-review]
---

# Design-Plan Consistency

## Overview

Projects with a separate design document corpus (GDD, specs, design docs) and
implementation plan trees suffer a recurring failure mode: **design drift.**
Someone edits a design doc, forgets to update the changelog, and the next agent
builds an implementation plan against a stale design. Or a plan tree reaches
COMPLETE, the GDD gets updated, and nobody marks the plan STALE.

This skill provides the governance layer that prevents that failure. It is the
*procedural* counterpart to `hierarchical-planning` (which covers *how* to
write a plan tree) — it covers *when and under what conditions* to create,
update, or flag a plan tree relative to the canonical design document.

The artifact is an `AGENTS.md` file at the project root: binding procedural
rules that every AI agent (Hermes, Claude, Codex, etc.) reads on entry.

## When to Use

Use this skill when:

- A project has a **design document corpus** (GDD, spec files, RFCs) and
  **implementation plan trees** (`plans/` directories) that must stay in sync
- You are setting up a **new project** and want the governance scaffold in
  place before the first plan tree is written
- An agent session reveals **inconsistencies** between design docs and
  implementation work suggesting drift
- You are **auditing plan trees** for staleness and need to cross-reference
  against the GDD changelog
- The plan tracking tables look stale **relative to code that already exists**
  ("reconcile the plan status against the code", "the tables don't reflect
  reality") — see the Code-Existence Reconciliation section
- A **new agent type** (Claude Code, Codex, etc.) is being onboarded to the
  project and needs explicit procedural instructions

Don't use this skill for:
- Writing a plan tree (use `hierarchical-planning` or `writing-plans`)
- Executing a plan tree (use `hierarchical-plan-execution`)
- Coding standards or conventions (those go in a separate doc like
  `SHARED-CONVENTIONS.md`)

## The Four Rules

These are the core of every `AGENTS.md`. They are framework-agnostic —
adapt the wording to the project's terminology (substitute "GDD" for
"specification", "design doc", "RFC", etc.).

### Rule 1: Design Change → Changelog (always)

> Every modification to a design document MUST be recorded in the changelog
> before the agent does anything else (plans, code, audit).

- The changelog is append-only — new entries go at the top.
- Each entry includes: date, session identifier, scope, a summary of changes
  (which files, old→new), and a verification column.
- Trivial exceptions: <5 lines of purely cosmetic whitespace/typo changes.
  Everything else — content, terminology, status upgrades, cross-refs — gets
  an entry.

**Verification:** `grep -c "$(date -I)" <changelog-path>` — if no entry dated
today, the agent forgot.

### Rule 2: Before Plan Work → Review Changelog

> Before authoring or updating any implementation plan tree, an agent MUST
> check for design drift by reading the changelog.

Procedure:
1. Read the changelog (full file).
2. Read the Implementation Record (Rule 3).
3. For each changelog entry since the last verification date for this plan
   tree, cross-reference against the plan's design-spec sources.
4. If any changelog entry touches a spec source for the target plan tree →
   the plan needs an **integration pass** (update to reflect the design
   change) before any code is written.

### Rule 3: Implementation Record (Drift Tracker)

> A central table tracking every plan tree's implementation date and last
> changelog check, enabling cross-document audit.

Columns:

| Plan Tree | Implemented Date | Agent / Session | Last Changelog Check | Drift Found | Action Taken |

- **Implemented Date** — date the plan tree reached COMPLETE.
- **Last Changelog Check** — date of most recent changelog cross-reference.
  Updated whenever the tree is verified (Rule 2 or Rule 4).
- **Drift Found** — YES or NO. YES means a design change occurred after the
  plan was implemented or last checked; the plan needs updating.
- **Action Taken** — what was done to resolve (e.g., "plan updated to match
  spec §4.3", "re-verified, no change needed").

**Audit method:** compare each row's `Last Changelog Check` date against the
changelog. Any entry dated *after* that check touching the plan's spec sources
= drift possible.

### Rule 4: Plan ↔ Design Consistency

> Plan trees and their design-spec sources must never diverge. If one changes,
> the other must be updated or a drift investigation recorded.

Concrete obligations:

- **Plan execution discovers a spec gap:** update the design doc (Rule 1)
  before or alongside the leaf execution. Record drift resolution in the
  Implementation Record.
- **Design spec edited after a plan tree reached COMPLETE:** the editing
  agent MUST:
  1. Record the change in the changelog (Rule 1).
  2. Check which plan tree(s) reference that spec.
  3. Mark each affected tree `STALE` (new status: "design changed after
     implementation, needs re-verification").
  4. Update the Implementation Record: set Drift Found to YES, document
     what changed.
- **Design spec edited mid-planning (tree not yet at COMPLETE):** the
  executing agent notes the change, integrates it into the plan before
  continuing, and records it.

## Workflow Diagram

```
        ┌──────────────────────────────────────────────────┐
        │                  AGENT ENTRY POINT                 │
        │  Read AGENTS.md, conventions, targeted design docs │
        └──────────────────────┬───────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
     ┌──────────────────┐          ┌──────────────────────┐
     │  Editing design  │          │ Implementing plans   │
     │  documents       │          │ / writing code       │
     └────────┬─────────┘          └──────────┬───────────┘
              │                               │
              ▼                               ▼
     ┌──────────────────┐          ┌──────────────────────┐
     │ 1. Make change   │          │ 1. Read changelog    │
     │ 2. Update        │          │    (Rule 2)          │
     │    changelog     │          │ 2. Read Implementation│
     │    (Rule 1)      │          │    Record (Rule 3)   │
     │ 3. If any plan   │          │ 3. Check for drift   │
     │    references    │          │    between changelog │
     │    this spec →   │          │    & plan's spec srcs│
     │    mark STALE    │          │ 4. Resolve drift     │
     │    (Rule 4)      │          │    or proceed         │
     └──────────────────┘          └──────────┬───────────┘
                                               │
                                               ▼
                                    ┌──────────────────────┐
                                    │ 5. Implement plan    │
                                    │ 6. Update status in  │
                                    │    build plan index  │
                                    │ 7. Update            │
                                    │    Implementation    │
                                    │    Record (Rule 3)   │
                                    │ 8. Commit            │
                                    └──────────────────────┘
```

## Status Value Taxonomy

Canonical statuses for plan trees (place in the build plan index):

### Execution Statuses (plan trees and branches)

| Status | Meaning |
|--------|---------|
| `DRAFT` | Tree outline exists, not yet ready for dispatch |
| `PLANNED` | Tree authored, dispatchable |
| `IN_PROGRESS` | One or more leaves being executed |
| `COMPLETE` | All leaves reviewed, tested, committed; plan matches current design |
| `STALE` | Design spec changed after plan reached COMPLETE; needs re-verification |
| `VERIFIED` | Changelog checked for drift since last review; no drift found |

Transition rules:
- `DRAFT → IN_PROGRESS` not allowed — must go through `PLANNED`.
- `STALE → COMPLETE` not allowed — must go through `IN_PROGRESS` (revision).
- Only `COMPLETE` or `VERIFIED` means the plan is safe to code against.

### Leaf-Level Reconciliation Verdicts (post-drift-digest)

When a drift digest reveals that external work (changelog sessions, design decisions, mechanical fixes) has covered some or all of a plan leaf's intended scope, assign a reconciliation verdict *per leaf* in the tracking table:

| Verdict | Meaning | Action |
|---------|---------|--------|
| `SUPERSEDED` | The leaf's planned work was completed by external means (changelog, design decisions, mechanical fixes). | Leaf does not need re-execution. Tracking table entry gets SUPERSEDED + a note referencing the changelog rows that covered it. |
| `PARTIAL` | Some of the leaf's planned scope was covered externally, but work items remain. | Split the leaf: document which tasks were SUPERSEDED, keep the remainder as STILL_NEEDED. Update the tracking table with a per-task breakdown. |
| `STILL_NEEDED` | The leaf's scope was not addressed by any external work. | Leaf remains actionable as originally written. The drift digest confirms no changelog entry covers its tasks. |

**Important:** Reconciliation verdicts are NOT execution statuses. A leaf marked SUPERSEDED was not "completed" by anyone executing its text — its intended outcome was achieved through *other* means (a changelog session, a sibling plan tree, a design decision). Keep execution statuses (Pending/In Progress/Complete) in a separate column if the tree is still operational. Use verdicts when the tree is being audited or retired.

**Transition rules:**
- `SUPERSEDED` is final — a leaf in this state should not be re-opened unless the changelog claim is later found incorrect.
- `PARTIAL` requires a split: document what's done, then either execute the remainder or leave it as an explicit STILL_NEEDED item.
- `STILL_NEEDED` means the leaf proceeds as-is; no changelog intervention found.

## How to Write AGENTS.md

1. **Identify the project's document ecosystem:**
   - Where do design docs live? (e.g., `docs/gdd/`)
   - Where does the changelog live? (e.g., `docs/gdd/00-CHANGELOG.md`)
   - Where do plan trees live? (e.g., `plans/` or `plans-glm/`)
   - Where is the build plan index? (e.g., `docs/09-pm/02-build-plan-index.md`)
   - Where do coding conventions live? (e.g., `SHARED-CONVENTIONS.md`)

2. **Establish the four rules** (use the template in `templates/AGENTS.md`
   as a starting point). Adjust terminology to match the project:
   - "GDD" → "specification", "design doc", "RFC"
   - "plan tree" → "implementation plan", "feature plan"
   - "changelog" → "change log", "revision history"

3. **Add the workflow diagram** (ASCII or markdown) as a quick-reference
   decision tree for entering agents.

4. **Add the status taxonomy** so every orchestrator and plan tree uses the
   same values.

5. **Add the enforcement section** — what should an entering agent check
   before proceeding? Typical: scan changelog for most recent session, scan
   Implementation Record for unresolved drift.

6. **Cross-reference existing documents** to show which file wins for which
   concern (e.g., "procedure: this file wins; coding conventions:
   SHARED-CONVENTIONS.md wins").

## Session Entry Protocol

Every agent entering a project with an AGENTS.md MUST:

1. Scan the changelog for the most recent session entries.
2. Scan the Implementation Record for any `Drift Found = YES` rows with a
   blank `Action Taken`.
3. Report any unresolved drift to the user before proceeding.

These checks are **not optional** — they are the minimum to prevent the
chain of agents from amplifying inconsistency.

## Drift Digest Procedure (Concrete Technique for Rule 2)

Rule 2 says "review the changelog before plan work." This section gives the
concrete cross-reference procedure for producing a **drift digest** — a
structured report of which plan trees need amendment because the design doc
moved under them. Use this whenever the user asks "review the changelog",
"what changed that affects my plans", "cross-reference findings against
the GDD", or any variant.

### Step 1 — Gather sources in parallel (one assistant turn)

Batch these reads; they are independent:

- `read_file` the changelog (e.g. `docs/gdd/00-CHANGELOG.md`) in full.
- `terminal` `git log --oneline --since="<date>" -- <gdd-path>` for recent commits.
- `terminal` `git log --pretty=format:"%h %ai %s" -<N> -- <gdd-path>` for dated hashes.
- `search_files` for the plan tree's tracker file (e.g. `plans-*/OPEN-QUESTIONS.md`).
- `read_file` the plan tree root `master.md` and `SHARED-CONVENTIONS.md`.

If the plan tree dir is untracked (`git status --short plans-*/` shows `??`),
note it — `git log -- plans-*/` returns empty and you must rely on filesystem
mtimes + the tracker's own compiled-date header.

### Step 2 — Per-commit file inventory

For each commit touching the design doc since the plan trees were authored:

- `git show <hash> --stat` — see which files moved.
- Cross-reference each touched file against the plan tree's "GDD Spec Source"
  column in its `master.md`. Any overlap = potential drift.

Skim commit messages for D-numbered decisions (D-28, D-29…), O-numbered
open-issue resolutions (O5, O6…), and status elevations (DRAFT→DECIDED).
These are the high-signal events; cosmetic edits can be skipped.

### Step 3 — Verify each tracked finding against CURRENT source

This is the step that catches the most drift. For each numbered finding in
the plan tree's tracker (OPEN-QUESTIONS.md, etc.):

- If the finding records a concrete value (e.g. "Beacon Hill 42m"), `grep`
  the CURRENT design doc for that value. Do NOT trust the finding's own
  number — it was captured at authoring time and the design may have moved.
- If the finding says "X is a BLOCKER", check whether the changelog claims
  to have resolved X, then verify the claim by reading the cited source
  file. **Changelogs resolve adjacent issues that sound similar but are
  distinct** — e.g. a changelog entry "D1: Tier-3 population reconciled"
  does NOT resolve a tracker blocker about "need_states list
  contradiction" even though both touch NPC population.
- If the finding's summary section lists "needs user decision" items,
  re-check each against the changelog — the summary itself goes stale.

### Step 4 — Classify findings

Output a structured report with these categories (the user scans by header):

- **🚫 Hard contradictions** — plan tree holds a value the design doc has
  changed. Must fix before dispatch. Cite old→new.
- **✅ Resolved** — changelog closed the issue; plan tree can cite the
  resolution. Note the commit hash and any D-number.
- **📋 New info** — changelog introduced content the plans should
  incorporate (new constants, new status elevations, new docs). Not a
  contradiction, but an amendment opportunity.
- **📝 Status changes** — design docs the plans depend on changed status
  (DRAFT→DECIDED, REVISED→DECIDED). Tabulate old→new→commit.
- **Still-open blockers** — items the changelog did NOT address. Surface
  these explicitly so the user knows they remain.

### Step 5 — Required-amendments summary

Close with a tiered action list:

1. **Must-fix before dispatch** (hard drift).
2. **Should-update** (info now authoritative).
3. **No action** (already incorporated or out-of-scope).
4. **Still-open blockers** (unchanged; flag for user).

For each must-fix, name the exact file and the old→new value. The user
should be able to act on the list without re-reading the report body.

### Pitfalls specific to drift digests

1. **Tracker-summary sections go stale.** The bottom of `OPEN-QUESTIONS.md`
   typically has a "Summary" restating which items are blockers vs
   accept-as-default. That summary was written at one point in time and is
   itself a plan-tree artifact subject to drift. Always re-verify against
   the changelog, never quote the summary as ground truth.

2. **Related ≠ resolved.** A changelog entry resolving "NPC population
   tier model" does not resolve a tracker blocker about "NPC need_states
   list" even though both live in NPC docs. Read the cited source range
   and confirm the *specific* contradiction is gone before marking a
   blocker cleared.

3. **Untracked plan dirs have no git history.** If `plans-*/` is untracked,
   `git log -- plans-*/` is empty and you cannot tell when a plan tree
   was last verified. Fall back to the tracker's compiled-date header and
   the master.md "Last Updated" column. Note this caveat in the report.

4. **Status elevations are silent authorizations.** When a doc goes
   DRAFT→DECIDED, plan trees that referenced it can now treat it as
   authoritative — but nothing in the plan tree flags the transition.
   Surface status changes as a distinct report section so the user knows
   which specs are now safe to code against.

5. **Primary-source research commits change concrete numbers.** A commit
   titled "ratify X via primary-source research" often **corrects** prior
   values that were in the plan tree as "confirmed constants". Always
   grep the current doc for the actual number; the plan tree's recorded
   constant may be the pre-research value.

6. **Internal protocol/terminology inconsistency across leaves.** A plan tree
   can have the correct architecture stated in its orchestrator while
   individual leaves still use wrong terminology from an earlier draft or a
   different engine target. Example: orchestrator says "NDJSON over TCP, NOT
   HTTP" but three leaves still say "send via HTTP POST" or "use HTTPClient."
   Or: project uses Godot MCP but leaves reference "Summer Engine MCP" tools
   (`summer_get_script_errors`, `summer_play`). These are not sibling-tree
   contamination — they are stale terminology within the tree itself.

   **Verification step (after any protocol/architecture correction):**
   Search the entire tree for the WRONG term, not just the file you fixed:
   ```
   search_files(pattern="HTTP|HTTPClient|http", path="<tree>/03-npc-systems/", file_glob="*.md")
   search_files(pattern="summer_|Summer Engine", path="<tree>/", file_glob="*.md")
   ```
   Fix ALL hits in one pass. The orchestrator stating the correct protocol
   does NOT propagate to leaves — each leaf must be individually corrected.

   **Pattern:** when you fix a protocol reference in one leaf, immediately
   search for the same wrong term across the entire branch (or tree). The
   error was likely copy-pasted during initial authoring and exists in
   multiple files. Batch-fix, then verify zero hits.

7. **Partial correction propagation — orchestrator contract fixed, leaf tests still stale.** When a digest or post-authoring review identifies a spec-contract error, it is common to fix the frozen contract in the `master.md` orchestrator but forget that the **leaf document's test tasks and review checklist** still reference the old values. In the `plans-glm/` session, the gossip tree's leaf had its `CelebrityMultiplier` contract signature correctly rewritten to use fact-count bands, but the leaf's TDD test steps still fed notoriety-float inputs at the old wrong thresholds, and the leaf-level review checklist still checked boundary values from the superseded approach. **Prevention:** after applying any contract correction in an orchestrator document, re-read every leaf document that defines tests or review-checklists consuming that contract. Search for the old value or type name — a function that now takes `int` should not have tests passing `float64`. Do not assume that fixing the master propagates to leaves; verify with a file scan. This pattern is visible in `references/plan-tree-audit-failure-modes.md`.

8. **Internal plan-tree contradictions (Goal vs Contracts vs Tests).** A plan tree can be internally inconsistent without any GDD drift — the Goal section may claim one design, the Interface Contracts define another, and the leaf test tasks exemplify a third. This is **not caught by external cross-references** (the drift-digest checks plan-vs-GDD, not plan-vs-itself). Discovered in the `plans-glm/` Tree 08 (schedule): the Goal said "8 needs... 8-priority resolution hierarchy (SAFETY > SLEEP > HUNGER > THIRST > DUTY > WORK > SOCIAL > FAITH)" — a pre-decision draft — while the Contracts section correctly showed 6 needs (HUNGER/THIRST cut). A leaf agent reading the Goal would implement the wrong needs model, despite the Contracts being correct. **Prevention:** after authoring any plan tree, run a holistic self-consistency check across Goal → Contracts → representative leaf Tests, confirming all three reference the same values, counts, and struct shapes. Any mismatch between Goal and Contracts is a dispatch-blocker until resolved. Do this as a deliberate scan pass, not by memory.

9. **Cross-tree contract drift against shared reference documents.** When a project-architecture or system-design document (not a plan tree) specifies a message type, constant, or interface that multiple plan trees consume, the absence of that contract in the relevant plan tree is invisible to per-tree drift digests (which check one tree against its GDD sources at a time). In the `plans-glm/` session, the project-architecture document referenced a `cell_query` / `cell_response` message type for World Partition cell transitions — but no plan tree (especially Tree 03 IPC, which owns the message types table) included it. An open question flagged it, but it was never applied. **Prevention:** when reviewing plan trees against a project-architecture doc that defines shared contracts (message types, IPC protocol tables, configuration schemas), read the arch doc's contract sections and check for **every defined contract** whether at least one plan tree declares it. Create a cross-reference table: arch-doc contract → owning plan tree → status (PRESENT / ABSENT / DEFERRED). ABSENT entries are blockers if the contract is required for integration. This catches contracts that exist at the architecture level but were never assigned to an implementation tree.

A worked example with all eight steps applied (a 12-tree forest cross-referenced against current GDD specs, changelog entries, resolved open questions, and shared contracts) is in
`references/plan-tree-audit-failure-modes.md`. The same session's 74-tracked-finding drift digest (five-step) remains at
`references/plan-tree-drift-digest.md`.

## Design Adjudication Sessions (Research → Amendment Plan → Forward-Port)

When the user raises a design-level problem (balance, missing content,
ideology/framing), the session shape is: parallel research fan-out into
`docs/research/` → independently re-verify headline claims → amendment plan
doc (B1..Bn with path:line defect citations + forward-port section) → STOP
for user review → apply B1..Bn with the Rule-1 changelog row and Rule-4 drift
check in the same session → forward-port as a registered plan tree with
frozen contracts. Tree-number assignment: grep the build-plan index AND list
the plans directory (numbers are consumed by trees registered only in the
index). Full procedure + content-framing patterns (two-strata rule, balance
contracts, grep gates): `references/design-adjudication-workflow.md`.

### Applying a Numbered Audit-Findings List to Plan Trees

When the user hands you an audit findings list (M1–M9 major / m1–m9 minor
style) and says "apply audit fixes to <tree>/", the efficient procedure is:
signature-term grep first (locate all affected files without full reads),
full-read + batch-patch per file, lockstep contract fixes across
orchestrator↔leaf↔checklist, then a zero-hit verification grep over the whole
tree including terms expected to be already-clean. Concrete finding→fix
patterns from the policy-market 02-data-platform session (wrong exception
types in TDD snippets, ambiguous `pl- or pa-Table` return types,
self-questioning spec text, YAML-string config fields, run_id formats, stub
workers vs make-target invariants, fixture provenance honesty, unverified
routes, partition-pruning claims, Makefile target ownership) are catalogued in
`references/audit-fix-application.md`.

## Plan Leaf Reconciliation Procedure (Post-Drift-Digest)

A drift digest identifies *which* leaves are affected and *how*. The
reconciliation procedure applies those findings to the plan tree's tracking
tables, producing a structured verdict per leaf. This is the step after the
digest is approved — turning analysis into actionable table updates.

### When to Use This

Use when:
- A drift digest or reconciliation report has been produced and approved
- The user asks "apply the reconciliation report to update all tracking tables"
- You need to update a plan tree's tracking table with SUPERSEDED/PARTIAL/STILL_NEEDED verdicts
- Cross-referencing a changelog against a multi-leaf plan tree and updating orchestrator files

### Step 1 — Gather the reconciliation source + all target documents

Read everything in one batch (they are independent):

- The drift digest or reconciliation report (the source of truth for verdicts)
- The plan tree's `master.md` (branch-level tracking table)
- Every branch orchestrator `orchestrator.md` (leaf-level tracking tables)

**Expected structure:** A plan tree has one `master.md` at the root and one
`orchestrator.md` per branch directory (e.g., `01-contradictions/orchestrator.md`,
`02-missing-specs/orchestrator.md`). Each contains a Completion Tracking Table.

### Step 2 — For each leaf, map the digest verdict to a tracking-table verdict

| Digest Finding | Leaf-Level Verdict | Details |
|---------------|-------------------|---------|
| Work was done by changelog / design decision / external agent | **SUPERSEDED** | Note the specific changelog row(s) that covered it (e.g., "A3 (Row 12)", "Row 14") |
| Some tasks done externally, some not | **PARTIAL** | List which tasks are SUPERSEDED and which remain STILL_NEEDED in the Review Notes |
| No changelog entry covers this leaf | **STILL_NEEDED** | Leaf remains actionable as-is |
| Mixed verdicts within a single leaf (e.g., Tasks 2-4 done, Task 1 not) | **PARTIAL** with per-task breakdown in Review Notes | |

### Step 3 — Update the tracking table in each orchestrator

For each branch orchestrator's Completion Tracking Table:

1. **Replace the Status column** (which previously held execution states like
   PENDING/IN_PROGRESS) with a **Verdict column** using SUPERSEDED/PARTIAL/STILL_NEEDED.
2. **Replace the Iterations column** (which tracked dispatch cycles) with a
   richer **Review Notes column** containing:
   - Which changelog row(s) covered the leaf (e.g., "A1+Row14")
   - What was actually done vs what remains
   - Any cross-cutting issues discovered (e.g., "A10 was no-op — verify X")
   - Structural bugs in the leaf itself (e.g., "G18 forging exception lacks Task block")
3. **Add a note about the verdict values** at the bottom of the table for clarity.

Table shape (old to new):

```
## Completion Tracking Table

| Child | Status | Iterations | Notes |       | # | Child | Verdict | Review Notes |
|-------|--------|------------|-------|  ->  |---|-------|---------|-------------|
| …     | PENDING| 0          | …     |       | 01 | foo    | PARTIAL | …            |

                                                  Status values: SUPERSEDED | PARTIAL | STILL_NEEDED
```

### Step 4 — Update the master.md branch-level tracking table

The root `master.md` typically has a higher-level branch tracking table.
Update it to reflect the reconciled state:

- Change Status values to reflect the *reconciliation outcome* (e.g., "RECONCILED" or
  just show the verdict tallies like "5 SUPERSEDED, 2 PARTIAL")
- Add a pointer to the detailed leaf table or per-orchestrator notes
- Add the verdict taxonomy to the table footer

If the master.md also has a *detailed leaf table* (listing every leaf across all
branches), replace or expand it to cover ALL leaves — the report may have found that the
existing table only covers a subset.

### Step 5 — Add reconciliation notes to each orchestrator

For each orchestrator that was updated, add a **Reconciliation note** in its
Notes section. This note should contain:

- **Branch-level summary:** How many leaves got each verdict (e.g., "5 SUPERSEDED, 2 PARTIAL")
- **Key discrepancies:** Any places where the reconciliation found that the changelog
  did something *different* from what the leaf proposed (e.g., changelog went to 6 tiers
  but leaf proposed 5)
- **Cross-cutting issues:** Items that affect multiple leaves and weren't captured by any
  single leaf's scope (e.g., "6-need NPC model (Row 18) not referenced by any leaf")
- **Caveats:** Any conditions under which a SUPERSEDED verdict should be downgraded
  (e.g., "if any changelog claim is later found incorrect")
- **Pointer to the reconciliation report:** So future readers know the source

### Step 6 — Verify the updates

After all patches are applied:

- Re-read key sections of the updated files to confirm patches applied correctly
- Check that every leaf from the reconciliation report has an entry in the
  tracking table (no leaf missed)
- Check that every verdict in the table matches the report's per-leaf instructions
- Verify that reconciliation notes mention cross-cutting issues from the report

### Worked Example

A full worked example (Rebellion GDD plans-ds4f, 2026-07-19, 20 leaves across
5 branches reconciled against a 19-row changelog) is in
`references/leaf-verdict-reconciliation.md`.

### Batch-Apply Fix Pattern

After reconciliation verdicts are assigned, apply all content fixes
(find-and-replace across multiple plan files) in one tight read-patch-verify
cycle rather than one-at-a-time. See `references/plan-fix-batch-apply.md`
for the worked example (19 files, 4 turns) and pitfalls (replace_all
over-match, parallel-same-file conflicts, changelog table formatting).

### Pitfalls specific to leaf reconciliation

1. **SUPERSEDED does not equal COMPLETE.** A superseded leaf was not executed — its intended
   outcome was achieved by other means. Never mark a leaf COMPLETE just because
   its tasks were done elsewhere; use SUPERSEDED so the history is clear that
   the leaf text itself was not the mechanism.

2. **PARTIAL leaves need task-level breakdowns.** A leaf with 10 tasks where 3
   were done by the changelog needs a per-task accounting in the Review Notes.
   Future agents reading the table need to know exactly which tasks remain without
   re-reading the whole leaf.

3. **Reconciliation verdicts and execution statuses coexist in the same table
   during transition.** When a leaf is PARTIAL, its remaining tasks may later be
   dispatched — the table should carry both the reconciliation verdict (what the
   changelog covered) and an execution status (what's still pending). If you
   replace execution statuses entirely with verdicts, add a note about what
   happens next for PARTIAL/STILL_NEEDED leaves.

4. **Cross-cutting issues that no leaf covers.** The reconciliation report may
   identify issues (like a 6-need NPC model change in Row 18) that no leaf in
   the plan tree addresses. These must be surfaced in the reconciliation notes
   as new work items — they won't appear in any leaf's verdict if no leaf
   mentioned them.

5. **Don't trust the report's verdicts blindly.** The reconciliation report is a
   cross-reference against the changelog at one point in time. If a subsequent
   verification finds a changelog claim incorrect, the corresponding verdict
   should be downgraded (e.g., SUPERSEDED to PARTIAL). The reconciliation notes
   should include a caveat about this.

## Code-Existence Reconciliation (Plan Tables vs Actual Code)

A distinct reconciliation type from the changelog-driven one above. Here the
plan tracking tables are stale **relative to code that already exists on
disk** — every cell says PENDING while a real implementation has accumulated.
The source of truth is a **file inventory**, not the changelog. Use when the
user says "reconcile the plan tables against the code that actually exists",
"the plan status doesn't reflect reality", or "make the tracking match what's
built." (Contrast: the SUPERSEDED/PARTIAL/STILL_NEEDED procedure above keys off
*changelog coverage*; this one keys off *files on disk*.)

### Procedure

1. **Inventory the code first (before reading any plan).** `search_files
   target=files` for the implementation extensions (`.gd`, `.py`, `.ts`,
   `.cpp`, `.tscn`...). Get per-area file counts + line counts via a shell
   loop. This rollup feeds the summary and tells you which subsystems are
   thick (real impl) vs thin (scaffold).

2. **Read the plan tables.** master.md completion table + every branch
   orchestrator's leaf table + leaf docs as needed to know each leaf's intent.

3. **Map files → leaves, then SKIM to confirm real content.** A matching
   filename is NOT evidence of completion. `head -N` each candidate file:
   does it have real logic matching the leaf's intent, or a stub/scaffold?
   Scaffolded-but-unverified = IN_PROGRESS, never COMPLETE.

4. **Assign statuses conservatively.** PENDING = nothing exists. IN_PROGRESS
   = real code present but not verified end-to-end (not run, no passing test
   suite). COMPLETE/REVIEWED = only with evidence of a real run/test. When in
   doubt, IN_PROGRESS. Add a Notes entry per row citing the concrete file(s)
   + line counts that justify the status.

5. **Probe for missing infrastructure that downgrades a leaf.** Check for the
   things a leaf *requires* but that live outside the obvious script: test
   framework addon (e.g. GUT), behavior-tree addon (e.g. Beehave), theme
   resources (`.tres`), export presets, a referenced subsystem (seed+overlay
   save, retargeting). `grep` the file for the spec's key terms — absence of
   `seed|overlay|sidecar` in a save script means the GDD model isn't done.

6. **Flag duplicate code generations in Notes, don't "fix" them.** A codebase
   often has a legacy prototype generation alongside a newer spec-aligned one
   (two inventory scripts, two grapple systems). Cite both as "duplicate, not
   reconciled" — reconciliation is code work, out of scope for a tables-only
   pass.

7. **Update tables + index + changelog, then verify the guardrail.** Edit
   master.md, each orchestrator leaf table, the build-plan-index row, and add
   a Rule 1 changelog entry. Then `git status --porcelain` to confirm only
   markdown changed (if the task forbade code edits) and `grep -c "$(date -I)"`
   on the changelog.

8. **Deliver the gap list as a first-class output.** The leaves with NO code
   are what the user plans next from — surface them explicitly, not buried in
   prose. Also report: files edited, branch-status rollup, and any
   missing-infra / duplicate-generation flags.

Worked example (Rebellion `plans-godot/`, 63 scripts reconciled across 14
branches with the exact inventory commands, status rubric, and guardrail
checks): `references/code-existence-reconciliation.md`.

## Branch History Reconciliation (Git Ancestry + Commit Analysis)

When assessing whether a feature branch's work is complete *and* merged, or
when determining how far a branch has progressed relative to a plan tree,
use git ancestry checks + commit-message analysis. This complements the
Code-Existence Reconciliation (which keys off files on disk) by keying off
commit history and branch topology.

### When to Use This

- "Is feat/X merged to main?" — determine merge status without trusting
  GitHub PR state or branch names.
- "Is the work on feat/X complete?" — assess coverage against a plan tree's
  task list by scanning commit messages and file diffs.
- "Does main contain the spike from feat/X?" — verify integration before
  dispatching dependent work.

### Technique

1. **Check ancestry:**
   ```bash
   git merge-base --is-ancestor <branch> main && echo "ANCESTOR: main contains branch" || echo "ANCESTOR: branch is NOT merged"
   ```
   If the branch is an ancestor of main → it IS merged.
   If main is an ancestor of the branch → the branch is strictly AHEAD (not merged).

2. **List commits on the branch but not on main:**
   ```bash
   git log --oneline main..<branch>
   ```
   Empty output = the branch has no commits main lacks (fully merged).
   Non-empty = the branch has unmerged work.

3. **Read commit messages for completion signals:**
   Scan for task markers: `PASS`, `DONE`, `complete`, `spike PASS`, or
   explicit task completion notes in commit bodies. A commit message like
   `docs(motion-matching): spike PASS — plugin loads + MMAnimationNode registers`
   is a completion signal for that specific task.

4. **Cross-reference against the plan tree's task table:**
   Read the plan tree's `master.md` tracking table. For each commit on the
   branch, find which plan task(s) it addresses. Mark tasks COMPLETE if the
   commit message + diff covers the full scope. Flag tasks as still PENDING
   if no commit touches them.

5. **Assess diff size for rebase artifacts:**
   ```bash
   git diff --stat main..<branch>
   ```
   Beware of inflated deletion counts (millions of lines) from LFS rebases
   or `.gitattributes` changes — these do NOT indicate real work volume.
   Focus on the commit list and file-level additions instead.

### Worked Example (Rebellion motion-matching spike, 2026-08-13)

User asked: "has feat/motion-matching-spike been merged to main?"

1. `git merge-base --is-ancestor feat/motion-matching-spike main` → **yes**
   (main is an ancestor of the spike; spike is strictly ahead, NOT merged).

2. `git log main..feat/motion-matching-spike` → the spike's top commits:
   - `6fc04d1 feat(anim): vendor godot-motion-matching GDExtension`
   - `d763af8 docs(motion-matching): spike PASS — plugin loads + MMAnimationNode registers`

3. `git diff --stat main..feat/motion-matching-spike` → showed ~9M deletions
   (LFS rebase artifact, NOT real work). The file-level diff was misleading.

4. Read `plans-godot/motion-matching/MASTER.md` task table. The spike
   commit `d763af8` explicitly marked Task 2 as PASS. Tasks 1 (config toggle)
   and 2 (plugin spike) were COMPLETE. Tasks 3–8 (mocap recording, DB bake,
   full wiring) remained PENDING — the plan tree was at PLANNED, not COMPLETE.

5. Conclusion: the **spike was PASS** but the **feature was not complete**.
   The toggle was OFF by default (blast radius = 0), but no mocap data was
   recorded, no pose database was baked, and the MM path was not wired into
   a character scene. The branch was a successful spike, not a shippable feature.

### Pitfalls

1. **Inflated diffs from LFS rebases.** A `git diff --stat` showing millions
   of deletions almost always means the branch was rebased against an
   updated `.gitattributes` or LFS pointer change, not that nine million
   lines of code were deleted. Always cross-check with the commit list and
   `git show <commit> --stat` for individual commits.

2. **Commit messages that claim completion but the plan tree says otherwise.**
   A commit titled "spike PASS" may only cover one task in a multi-task
   plan tree. Read the commit body and the plan tree's tracking table
   together.

3. **Trusting ancestry checks for partially-merged work.** If a branch was
   merged, then additional commits were added, `git merge-base --is-ancestor`
   will report "not merged" even though most of the work is in main. Always
   pair with `git log main..<branch>` to see what remains unmerged.

4. **Branch names that don't match their actual state.** A branch named
   `feat/motion-matching-spike` might contain unrelated asset/library work
   if it was used as a scratch space. Scan all commit messages, not just
   the tip.

### Quick Command Reference

A condensed command set for ancestry checks and diff analysis is in
`references/branch-history-reconciliation-commands.md`.

## Plan Branch Refactoring (Rewrite-to-Spec Procedure)

Drift detection (above) identifies *that* a plan branch is stale. This section
covers *how to rewrite it* — taking a stale or incomplete plan branch and
producing a new orchestrator + leaf set that matches the current design spec.
Use when the user says "refactor the plans to match the GDD", "the plans are
stale, rewrite them", or when a drift digest reveals gaps too large for
incremental patching.

### Step 1 — Read the GDD spec in full

Read the authoritative design document for the branch being refactored.
Do NOT skim — read every section. The GDD is the source of truth; the plan
must cover everything it specifies.

### Step 2 — Read all existing plan leaves

Read the orchestrator and every leaf in the branch. Build a mental map of
what's currently covered.

### Step 3 — Gap analysis (GDD → plans)

Compare section-by-section. For each GDD section, check:
- Is there a plan leaf that covers it?
- Does the leaf cover the full depth of the GDD section, or just a summary?
- Are GDD-specified values (hex colors, thresholds, key bindings, timings)
  present in the leaf, or does the leaf say "use Theme resources" without
  specifying what?

Classify gaps:
- **Missing entirely** — GDD section has no corresponding plan content
- **Shallow** — plan mentions the feature but lacks GDD-specified detail
- **Wrong** — plan contradicts the GDD (e.g., always-on HUD bars when GDD
  says default HUD is empty)
- **Stale orchestrator** — orchestrator lists N leaves but M exist

### Step 4 — Rewrite the orchestrator

The orchestrator gets a full rewrite when:
- Leaf count changes (3 → 8 leaves)
- Interface contracts change
- The engine translation table needs updating
- Concurrency groups change

Include in the orchestrator:
- **Engine translation table** (if porting between engines): map every
  source-engine concept to target-engine equivalent (e.g., UMG Widget →
  .tscn Control scene, CommonActivatableWidget stack → autoload singleton
  with priority stack, SetGlobalTimeDilation → Engine.time_scale)
- **Aesthetic system constants** frozen in the orchestrator (color hex
  values, font names, audio cues) so every leaf references the same values
- **Interface contracts** the branch exposes to other branches
- Updated child index, concurrency groups, completion tracking table

### Step 5 — Write new leaves

One leaf per coherent subsystem. Each leaf must:
- Reference the exact GDD section(s) it implements (by § heading)
- Include GDD-specified values inline (don't say "per GDD" — state the
  actual hex code, threshold, key binding, timing)
- List exact files to create/modify
- Have a self-verification checklist that maps 1:1 to GDD requirements
- Have a review checklist for the orchestrator

### Step 6 — Delete old leaves, update master.md

- `rm` the old leaf files that were replaced
- Update the parent `master.md` tracking table (leaf count, description)
- Do NOT commit — the orchestrator commits after review

### Step 7 — Dispatch parallel audits (for large refactors)

When refactoring one branch reveals that the whole plan forest may have
similar gaps, dispatch two parallel subagents:

1. **GDD completeness audit** — read every remaining branch's orchestrator
   + leaves, compare against corresponding GDD specs, report gaps by
   severity (CRITICAL/HIGH/MEDIUM/LOW)
2. **Cross-plan-tree gap review** — if the project has multiple plan trees
   (e.g., plans-glm for Go sidecar, plans-godot for engine client), check
   whether data/capabilities produced by one tree are consumed by the other.
   Report: sidecar feature → engine plan that should handle it → gap →
   severity → recommended fix

These run in parallel (independent reads). Integrate findings into the plan
files when they report back.

### Pitfalls specific to plan refactoring

1. **GDD implementation notes target the wrong engine.** When the GDD was
   written for Engine A (UE5) and the project uses Engine B (Godot), the
   GDD's "Implementation Notes" section will have Engine A code (C++, UMG,
   Common UI). The plan must translate these to Engine B patterns — but the
   *design intent* (what the player sees, how menus behave, what pauses)
   is engine-agnostic and MUST be preserved. Separate design intent from
   engine-specific implementation in every GDD section.

2. **Shallow leaves that say "use Theme resources" without specifying the
   theme.** A leaf that says "use Theme resources for consistent styling"
   without listing the actual colors, fonts, and button styles is not
   implementable. The GDD's aesthetic system (hex palette, font names,
   audio cues) must be inlined in the orchestrator and referenced by leaves.

3. **Orchestrator leaf count drift.** When leaves are added or removed, the
   orchestrator's child index, estimated context, and the parent master.md
   tracking table all need updating. Check all three.

4. **Leaves that cover the wrong scope.** A leaf named "quest-economy-ui"
   that covers quest journal + shop + faction display is three leaves
   pretending to be one. Split along subsystem boundaries: each leaf should
   be one coherent UI surface or system, not a grab-bag.

5. **Cross-plan-tree contamination (progress/status import from sibling trees).**
   When a project has multiple plan trees for different implementations
   (e.g., `plans-glm/` for a Go sidecar, `plans-godot/` for an engine
   client), the target plan tree MUST be self-contained. Three contamination
   patterns:

   **(a) Spec-source citations that include sibling tree paths.** Writing
   "Per GDD §04-npc/04-gossip-and-reputation.md and plans-glm/02-gossip/"
   imports a dependency on the sibling tree. Fix: cite ONLY the GDD spec.
   If the sibling tree's wire format is needed, inline the relevant struct
   or field list directly in the leaf.

   **(b) "Existing pipeline" / "adapt, don't reinvent" language.** Writing
   "Reference plans-glm/16-assets-generation/ for existing UE5 pipeline
   patterns" assumes the sibling tree's implementation exists and is
   available. Fix: document the pipeline patterns IN the target tree (or
   its GDD spec reference), not as a pointer to another tree.

   **(c) Progress/status leakage.** Tracking tables, "DONE" markers,
   "already implemented" language, or "completed" dates from the sibling
   tree must NEVER appear in the target tree. Each tree's tracking tables
   start at PENDING with blank dates/agents.

   **Verification step (mandatory after writing/patching plan files):**
   `search_files(pattern="<sibling-tree-name>", path="<target-tree>/", file_glob="*.md")`
   Zero hits = clean. Any hit must be evaluated and fixed.

   **What IS allowed:** referencing the GDD spec both trees derive from,
   the project's SHARED-CONVENTIONS.md (tree-local), and actual source
   code for wire types (e.g., `sidecar/internal/api/types.go`). These are
   source-of-truth references, not sibling-plan references.

   Discovered in the Rebellion session (2026-07-24): user corrected "the
   progress tracked in the plans-glm was from a different implementation.
   Make sure you did not port that information." 10 plans-glm references
   found across 8 plans-godot files and removed.

A worked example (Rebellion 06-ui-menus: 3 stale leaves → 8 leaves matching
a 473-line GDD spec, with UE5→Godot translation table) is in
`references/plan-branch-refactoring-example.md`.

## Plan Directory Consolidation (Engine Migration / Retirement)

When a project migrates from one engine to another (e.g., UE5 → Godot), the
old plan directory becomes a liability: agents may dispatch from superseded
trees, reference stale UE5 patterns, or re-implement work already done in the
new engine's plans. The fix is NOT to delete the old directory — historical
context is valuable. Instead, mark every file OBSOLETE with redirect headers
and establish a single authoritative directory.

Use when the user says "consolidate the plan directories", "mark the old
plans as obsolete", "plans-glm is dead, plans-godot is authoritative", or
when a migration leaves two parallel plan forests.

### Procedure

1. **Inventory both directories.** List every `master.md`, `orchestrator.md`,
   and leaf file in the legacy directory. Use `search_files target=files`.

2. **Categorize each legacy tree into one of three dispositions:**
   - **IMPLEMENTED** — the tree's code is done and lives elsewhere (e.g., Go
     sidecar code in `sidecar/`). The plan served its purpose. No successor
     plan needed; point to the code location.
   - **OBSOLETE (superseded)** — the tree targeted the old engine and has a
     direct replacement in the new directory. Point to the successor tree.
   - **OBSOLETE (stale)** — the tree used an approach that was rejected (e.g.,
     AccuRig for UE5 Mannequin when the project now uses MakeHuman+Rigify for
     Godot). No successor; point to the DECIDED replacement approach.

3. **Rewrite the legacy root `master.md` as a redirect page.** It should contain:
   - An OBSOLETE banner with the date
   - A migration map table: tree name → disposition → successor (or code location)
   - A "do NOT create new plans here" directive
   - A "for new work" pointer to the authoritative directory

4. **Patch each tree's `master.md` with a header block.** Insert immediately
   after the first `#` heading line. Each header:
   - States the disposition (OBSOLETE / IMPLEMENTED)
   - Names the successor or code location
   - Points to the legacy `master.md` migration map
   - For OBSOLETE trees: "Do NOT dispatch from this tree."

5. **Patch leaf files too.** Any `.md` file under a legacy tree's subdirectories
   gets the same header pattern. Agents search by filename, not by directory.

6. **Mark cross-cutting files as HISTORICAL.** Files like `SHARED-CONVENTIONS.md`,
   `OPEN-QUESTIONS.md`, `BUILD-PROGRESS.md`, and audit reports get a
   HISTORICAL header. If a conventions file retains reference value (e.g.,
   Go sidecar conventions), note that explicitly.

7. **Declare sole authority in the new directory's `master.md`.** Add a block
   at the top stating this is the sole authoritative plan source, the legacy
   directory is OBSOLETE, and all new plans go here.

8. **Update the build-plan-index.** Add a consolidation note at the top of the
   Implementation Plan Trees section. Update the "Plan tree location" footer
   to point to the authoritative directory only.

9. **Add a changelog entry** (Rule 1). Record the consolidation: which
   directory is authoritative, which is obsolete, how many files marked.

### Patching technique (batch)

When patching 15-25 files with headers, do NOT hand-write each patch. Use
`execute_code` to read the first line of each file (the heading), then loop
through and call `patch` with the exact heading string as `old_string` and
the heading + header block as `new_string`. This avoids fuzzy-match failures
from guessed headings.

If a heading does not match (file was renamed or restructured), re-read the
first 2 lines with `read_file limit=2` to get the exact text before retrying.

### Pitfalls

1. **Do NOT delete the legacy directory.** Historical plans contain interface
   contracts, design decisions, and open-question resolutions that are
   valuable for understanding why the code is shaped the way it is. Mark
   OBSOLETE, do not remove.

2. **Leaf files are discoverable by search.** An agent running
   `search_files pattern="gossip"` will find `plans-glm/02-gossip/01-fact-and-knowledge.md`
   even if the master.md says OBSOLETE. Every leaf file must carry its own
   header — the master.md redirect is not enough.

3. **Cross-cutting conventions files may retain value.** A Go sidecar
   SHARED-CONVENTIONS.md documents wire types and package boundaries that are
   still live code. Mark it HISTORICAL (not OBSOLETE) and note "retains Go
   sidecar reference value."

4. **The build-plan-index "Plan tree location" footer is easily missed.** It
   typically names the legacy directory as the plan location. Update it to
   point to the authoritative directory, or agents will be directed to the
   obsolete forest.

5. **Decision logs and GDD docs that reference the old engine.** A
   consolidation pass marks plans obsolete, but the GDD and decision log may
   still reference the old engine's tooling (e.g., "MetaHuman for hero NPCs"
   as a DECIDED entry). These need separate superseding entries or status
   changes — they are NOT plan files and are out of scope for the directory
   consolidation, but should be flagged as follow-up work. The follow-up pass
   (marking stale spec docs OBSOLETE, superseding decision-log entries,
   fixing tier-table references) should be done immediately after the
   consolidation — see
   `references/decision-log-supersede-and-stale-spec-cleanup.md` for the
   worked example.

### Stale Implementation Sections with Valid Migration Notes

> A GDD doc may have a valid "Migration Notes" or "Godot Implementation Note"
> section (added in a prior changelog entry) while the core "Implemention"
> section is still fully the old engine. Do NOT rewrite the old implementation
> section — that destroys historical lineage. Instead: insert a new Godot
> implementation section (with a UE5→Godot mapping table) immediately before
> the old section, then re-title the old section as STALE with a redirect
> pointer. The migration note was the diagnosis; the new Godot section is the
> authoritative replacement.

> **Pattern (concrete technique):**
> 1. Insert a new `## Godot X.Y Implementation` section before the old
>    `## UE5.X Implementation` heading.
> 2. In the Godot section, include: status marker ("IN PROGRESS — UE5 section
>    below is STALE"), the actual Godot source files (script paths, scene
>    paths), and a UE5→Godot mapping table (e.g., "Lumen GI → SDFGI",
>    "Niagara → GPUParticles3D", "Sky Atmosphere → ProceduralSkyMaterial").
> 3. Re-title the old heading: `## UE5.X Implementation (STALE — see Godot
>    section above)`.
> 4. Add a changelog entry documenting the doc update (Rule 1).

> This preserves the old section's historical detail (valuable for engineers
> understanding why a design decision was made a certain way) while making it
> clear which section is authoritative. Discovered in the Rebellion session
> (2026-08-13): `docs/gdd/03-world/07-day-night-and-weather.md` had a Godot
> implementation note (line ~142, added 2026-08-13) but a fully-stale UE5.8
> implementation section (lines ~181–285). Rather than rewriting 100+ lines
> of UE5 Blueprint/C++ that were never ported, a new Godot section with a
> mapping table was inserted and the old section was re-titled STALE.

Worked example (Rebellion `plans-glm/` → `plans-godot/` consolidation,
2026-08-12, 26 files marked across 17 trees + 4 cross-cutting files):
`references/plan-directory-consolidation.md`.

## GDD Revision → Code Audit (Planned-vs-Implemented)

Use when the user says "we revised some things in planning but I don't think it
was implemented" — or any variant suspecting a design revision never reached
code. This is the inverse of a drift digest: instead of checking plans against
the changelog, it checks the CODE against a changelog revision.

### Procedure

1. **Locate the revision in the changelog.** Find the dated entry (or entries)
   matching the user's description. Extract: which GDD files/sections changed,
   and the distinctive new terms the revision introduced (new function names,
   new keywords, new constants — e.g. "belt courses", "fire baskets",
   "wavy crown glass").
2. **Grep the codebase for those distinctive terms** (target=content, the
   implementation file globs: `.gd`, `.go`, `.ts`...). Zero matches = the
   revision was never implemented. Partial matches = partially implemented —
   check which sub-items exist (manifest entries + ref PNGs but no runtime
   code is the classic partial state).
3. **Distinguish planning artifacts from implementation.** A revision often
   produces plan-tree notes, manifest JSON entries, and generated reference
   images WITHOUT any runtime consumer. Those are not implementation. Verify
   the consumer: grep for the term in controller/instantiator/manager scripts,
   not just manifests.
4. **Report a planned-vs-implemented table** to the user before dispatching
   any fix work: one row per revision sub-item, GDD-done / code-done columns.
   The user confirms scope before agents run.
5. **Mark the affected plan tree STALE in the Implementation Record** (Rule 4)
   — the planning session that edited the GDD should have done this. Record
   Drift Found = YES with the changelog date and the action (integration pass).
   Update `Last Changelog Check` to today.
6. **Run the integration pass** (implement the revised spec), then close the
   Implementation Record entry and write the Rule 1 changelog row.

### Pitfall: the Rule 4 mark-STALE step is the most-skipped step

Discovered in the Rebellion procgen session (2026-08-14): the 2026-08-13
planning session edited the GDD (Stage 5 modular accents, Stage 9 street
lighting, wavy glass, wallpapers) AND wrote a correct changelog entry — but
never marked the dependent 10-procgen tree STALE, and no later session re-ran
the Rule 2 check. The revisions sat unimplemented until the user noticed by
symptom. A changelog entry alone does not propagate; the STALE marking +
Implementation Record update is the mechanism that makes the next session see
the drift. When auditing, treat "GDD edited, changelog written, Implementation
Record untouched" as the signature of this failure.

### Concrete worked example

Rebellion 10-procgen (2026-08-14): user asked "for the procgen process, what's
next? we revised some things in planning to make the procgen more realistic but
I don't think it was implemented." Audit path: session_search (no hit — the
revision happened in a sibling session) → search_files for the GDD spec doc →
read the changelog's 2026-08-13 entry → grep the implementation tree for each
revised term (belt_course|cornice|quoin|door_surround|sash → 0 hits in
`rebellion-godot/scripts/world/*.gd`; fire_basket|cresset|lantern → 0 hits in
sidecar procgen; no glass shader in shaders/) → planned-vs-implemented table →
Rule 4 STALE marking on the tree → three parallel implementation subagents.
The table also surfaced partial states: fire_basket_01/oil_lantern_01 existed
as props_manifest.json entries + generated ref PNGs with no GLBs and no
placement code — manifest entries are not implementation.

## STALE Close-out Loop (Re-verify → CONFORMS → COMPLETE)

A tree marked STALE because its GDD spec source changed does NOT mean the code
is wrong. The GDD edit and the code rewrite often land in the SAME session —
the STALE flag then means "confirm against the new spec", and the re-verification
can conclude CONFORMS with ZERO code changes. This is the close-out loop that
turns STALE back into COMPLETE (worked fully on rebellion trees 04-world-streaming
+ 11-rendering-vfx, 2026-08-13/14):

1. **Read the changelog row that caused the STALE flag.** Extract the exact new
   contract values (constants, formulas, thresholds) — not the summary, the
   numbers.
2. **Read the Implementation Record row.** It names the leaf(s) and spec
   sources to re-verify.
3. **Verify the code against each new value line-by-line.** Grep the constants,
   trace the ramp/curve functions, confirm single-writer ownership (one system
   per per-frame property). Cite `path:line` for every check.
4. **Run the spec's test suite** (e.g. `-gselect=solar`) and record pass counts
   as evidence. If a regression test for the changed behavior exists, name it
   in the record.
5. **Update the LEAF docs, not just the tracking.** A leaf that still describes
   the OLD spec (fixed phase windows, old constants, missing systems) is the
   actual drift — the code may be fine while the plan text lies. Rewrite the
   leaf's tasks/checklists to the new contract, mark obsolete sections with
   strikethrough, and note the re-verification date.
6. **Update BOTH tracking layers in lockstep**: the branch orchestrator's leaf
   status AND master.md's branch table AND the Implementation Record row.
   Status path: `STALE → IN_PROGRESS (revision) → COMPLETE` (direct
   STALE→COMPLETE is forbidden). Keep Drift Found = YES as historical record;
   write the verification result into Action Taken.
7. **Rule 1 changelog row** for the doc pass itself, with the verification
   evidence (test names + counts) in the Verification column.

### Pitfalls in the close-out loop

1. **The plan tree's own files may not carry the STALE marker.** The
   Implementation Record row and master.md can say STALE while the branch
   orchestrator still shows COMPLETE — the earlier session marked the tracking
   but never touched the tree files. Grep ALL FOUR layers before declaring
   status consistent: build-plan-index row, Implementation Record row,
   master.md branch table, branch orchestrator completion table.

2. **"Fixed phase windows" in leaves are the drift that matters.** A leaf
   with hardcoded windows/constants that the GDD replaced with computed
   values will mislead the next implementer even after the code is correct.
   Search the leaf for the OLD numbers, not just the section title.

3. **Concurrent changelog edits duplicate rows.** A sibling session appends to
   the same changelog mid-pass. When inserting your row, NEVER include
   existing rows in `old_string`/`new_string` — include only the table header
   line + your new row, and anchor on the header. If a patch's new_string
   carries another session's row (even truncated), you duplicate it.
   After any changelog edit: `grep -c "\[truncated\]" <changelog>` (0) and
   count today's rows vs expected. Sibling edits can also move the header
   separator line — re-read the file top before patching.

4. **Concurrent scene/tscn edits sweep unrelated work into your diff.** When a
   sibling is mid-edit on a shared file (e.g. showcase_map.tscn growing 1300+
   diff lines from THEIR building-kit work while your edit is 1 line), do NOT
   commit that file — commit the safe files and leave the shared one to
   whoever finishes first. Check `git diff --stat` before staging; a file's
   diff size way beyond your edit is the tell.

5. **Spec-wording ambiguity is a user decision, not an agent fix.** When the
   GDD's parenthetical contradicts its own model section (e.g. "opacity 1.0
   below 12°" vs "falloff to 0 at the horizon"), the subagent evidence should
   recommend ONE option with costs, but the user approves. In the 2026-08-14
   case the code's horizon-anchored ramp was correct and the GDD wording was
   tightened to match — the fix was a one-word spec edit, zero code change.

## Integration with Existing Skills

| Skill | Relationship |
|-------|-------------|
| `hierarchical-planning` | This skill governs WHEN a plan tree should be authored/updated; hierarchical-planning governs HOW. Its Plan Reconciliation section should reference this skill for the pre-work changelog check. |
| `hierarchical-plan-execution` | Before dispatching leaves from a plan tree, check for drift against the changelog (Rule 2 of this skill). If the plan is STALE, do NOT dispatch — first update the plan. |
| `writing-plans` | Before writing a flat plan, apply Rule 2 (read changelog, check for drift). This skill is the pre-condition; writing-plans is the action. |
| `code-review` | When reviewing implementation output, verify that the code matches the design spec the plan tree references. If a gap is found, update the design doc (Rule 4) before merging. |

## Common Pitfalls

1. **Writing AGENTS.md but never updating it.** AGENTS.md is a living document.
   Add new status values, workflow refinements, or document paths as the
   project evolves. Stale AGENTS.md is worse than no AGENTS.md — it gives
   false confidence.

2. **Skipping the Implementation Record.** Without it, you cannot determine
   whether a plan tree is current or stale. The Implementation Record is the
   pivot table for cross-document audit. If it's empty, populate it with a
   disclaimer: "Implementation Record created [date], populating as trees
   reach COMPLETE."

3. **Forgetting to add STALE to the status vocabulary.** Every project
   initially has only DRAFT/PLANNED/IN_PROGRESS/COMPLETE. STALE is the
   status that prevents agents from implementing against an outdated plan.
   It must be in the status list, transition rules, and every plan tree's
   tracking table.

4. **Changelog entries without verification.** An entry that says "fixed
   various bugs" with no tool-backed verification is not reviewable. Every
   changelog entry needs a verification column (e.g., "patch applied —
   unified diff OK", "subagent report confirmed", "all 5 files read and
   verified").

5. **Not cross-referencing from plan tree documents.** Each plan tree's
   `master.md` should reference AGENTS.md in its header so leaf agents know
   the governance layer exists. Add a one-line pointer: "Procedural workflow
   rules: AGENTS.md (repo root)."

6. **Plan tracking tables go stale when code is committed without updating them.** This is the inverse of drift: code exists and tests pass, but the plan tree tracking tables still say PLANNED/PENDING. Future agents surveying the plan forest see "these trees need implementation" and waste time re-implementing or re-dispatching what is already done. Prevention: when a leaf reaches COMPLETE, update the tracking table in the same commit that contains the code. If an agent discovers stale tables, run a batch update (read every master.md, update every tree whose code exists and tests pass, add a changelog entry). See `subagent-driven-development` skill's "Cross-Plan State Assessment (Forest Surveys)" section for the detection pattern.

7. **Status values in plan trees diverging from the canonical list.** If
   `hierarchical-planning` skill's tracking table uses different status
   values than the build plan index, agents get confused. Keep one canonical
   list (in AGENTS.md or a shared conventions doc) and reference it from
   every tracking table.

8. **Correct EVERY falsely-COMPLETE item, not just the one you came to fix.** When the user says "fix the plan tree to match state," the primary mismatch is rarely the only one. A tree can claim "15 stages implemented" while a stage has no source file (`stage1_terrain.go` absent despite `WorldSpec.Terrain` listed DONE); an orchestrator can mark all leaves COMPLETE while the bridge to a consumer system is unwired; the build-plan-index row and the Implementation Record can lag the `master.md` you just corrected. **Audit the whole tree and its sibling/consumer documents for every COMPLETE claim that code or wiring doesn't back, and correct them all in the same pass — then update the master.md, the build-plan-index row, AND the Implementation Record in lockstep.** Stopping at the first fix draws the correction "items not complete should be marked as incomplete as well." Two concrete checks that catch the subtle cases: (a) verify a claimed-implemented stage by confirming its source file exists (e.g. `find stage*.go`), not by trusting the tree's own notes; (b) verify a claimed-wired bridge by checking the consumer actually loads the data (e.g. `grep load_worldspec` callers — a node can exist in the scene yet never be triggered, leaving the "wired" claim false). Discovered in the Rebellion procgen session (2026-08-12): a tree marked IMPLEMENTED with all leaves PENDING in its own completion table, a missing Stage 1 terrain file, and a Godot loader node that nothing called.

## Closing the Last Tree Leaves: Machinery vs Manual Gate

When a plan tree's final open leaves mix CODE work with HUMAN-gated data
work (verification gates, external downloads, manual digitization), do not
leave the tree IN_PROGRESS indefinitely. Split the closure:

1. Implement ALL machinery (loaders, parsers, manifest schema, graceful
   no-data fallbacks) and mark the tree COMPLETE for the machinery, with
   the manual steps recorded explicitly in the Implementation Record's
   Action Taken column AND in the tracking artifact itself (e.g. a
   reference_manifest.json whose rows carry `verification: unverified` +
   `status: pending`). The manifest IS the worklist — the next agent reads
   it and knows exactly what remains and who does it (the human).
2. Determinism guard: when a pipeline stage gains an optional external-data
   path, the absent-data output must stay byte-identical to the
   pre-integration output (TestPipelineDeterminism passes UNMODIFIED).
   Prove it with a t.Setenv pointing the reference dir at /nonexistent.
3. Changelog wording: state "COMPLETE (machinery; manual gate noted)" and
   name the manual steps — future sessions must not rediscover them by
   symptom (that is the exact failure mode the Rule 4 pitfall describes).

## Verification Checklist

- [ ] AGENTS.md exists at the project root
- [ ] AGENTS.md defines all four rules
- [ ] AGENTS.md includes a status value taxonomy with STALE and VERIFIED
- [ ] AGENTS.md cross-references the changelog, build plan index, and conventions docs
- [ ] Changelog exists and follows the append-only + verification-column format
- [ ] Build plan index has a Changelog Check column and an Implementation Record
- [ ] Every plan tree's master.md references AGENTS.md
- [ ] Every plan tracking table uses the canonical status values
- [ ] Implementation Record is populated (or has a creation-date disclaimer)
- [ ] No stale plan trees without an STALE marker
