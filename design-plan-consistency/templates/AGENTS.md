# Procedural Rules for AI Agents

> **Status: [DECIDED]** — Binding procedural rules for every AI agent working
> on this repository. These rules govern *workflow sequencing*, *documentation
> hygiene*, and *cross-document consistency* between the design documents, the
> changelog, and implementation plans.
>
> Read this file first. It is the single source of truth for *what order to do
> things in*. Coding conventions and interface contracts live in their own
> documents (see §1).

---

## 1. Relevant Documents

| Document | Path | Purpose |
|----------|------|---------|
| **Design docs (canonical specs)** | `<path>` | The design. All implementation derives from here. |
| **Changelog** | `<path>` | Chronological record of every design-doc change. |
| **Build plan index** | `<path>` | Master index of plan trees with status, spec sources, and the Implementation Record. |
| **Plan trees** | `<path>` | Hierarchical implementation plans (one tree per system). |
| **Shared conventions** | `<path>` | Coding conventions, interface contracts, test strategy. Binding for every plan leaf. |

---

## 2. Four Procedural Rules

### Rule 1: Design Change → Changelog (always)

> Every design-doc modification MUST be recorded in the changelog before the
> agent does anything else (plans, code, audit).

- Changelog is append-only — new entries at the top, newest date first.
- Each entry: date, session identifier, scope, summary of changes (files,
  sections, old→new), verification column.
- Exception: <5 lines of purely cosmetic whitespace/typo. Everything else
  gets an entry.

**Verify on commit:**
```
grep -c "$(date -I)" <changelog-path>
```
If no entry dated today, you forgot.

### Rule 2: Before Plan Work → Review Changelog

> Before authoring or updating any implementation plan tree, read the changelog
> and check whether recent design changes create a consistency gap with existing
> or planned work.

1. Read the changelog (full file).
2. Read the build plan index's Implementation Record.
3. For each changelog entry since the last verification date for this plan
   tree, cross-reference against the plan's spec sources.
4. If any entry touches a spec source → update the plan before writing code.
5. If none → proceed.

### Rule 3: Implementation Record (Drift Tracker)

> A central table in the build plan index tracks every plan tree's
> implementation date and last changelog check.

| Plan Tree | Implemented Date | Agent / Session | Last Changelog Check | Drift Found | Action Taken |

**Audit:** compare each row's `Last Changelog Check` against the changelog.
Any entry dated *after* that check that touches the plan's spec sources means
drift is possible.

### Rule 4: Maintain Plan ↔ Design Consistency

> Plan trees and design specs must never diverge. If one changes, the other
> must be updated or a drift investigation recorded.

- **Plan execution discovers a spec gap:** update the design doc (Rule 1)
  before or alongside the leaf execution.
- **Design spec edited after a plan is COMPLETE:** record in changelog,
  check which plan tree references that spec, mark it STALE, update the
  Implementation Record.
- **Design spec edited mid-planning:** integrate the change into the plan
  before continuing.

---

## 3. Status Values (Canonical)

| Status | Meaning |
|--------|---------|
| `DRAFT` | Tree outline exists, not yet ready |
| `PLANNED` | Tree authored, dispatchable |
| `IN_PROGRESS` | Leaves being executed |
| `COMPLETE` | All leaves done; plan matches current design |
| `STALE` | Design changed after COMPLETE; needs re-verification |
| `VERIFIED` | Changelog checked for drift; clean |

Transitions: DRAFT→PLANNED→IN_PROGRESS→COMPLETE. STALE→IN_PROGRESS (revision).
Only COMPLETE or VERIFIED means safe to code against.

---

## 4. Enforcement

When entering a session:

1. Scan the changelog for the most recent session.
2. Scan the Implementation Record for any `Drift Found = YES` rows with a
   blank `Action Taken`.
3. Report unresolved drift to the user before proceeding.

These checks are not optional.
