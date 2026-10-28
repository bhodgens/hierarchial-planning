# 02 - Rewrite hierarchical-plan-execution SKILL.md + INDEX - Implementation Leaf

## Meta

- **Parent:** master.md
- **Scope:** EX SKILL.md 53,657 -> <=12,000 chars; EX references/INDEX.md 59,768 -> <=8,000 chars; all extracted material preserved in reference files.
- **Dependencies:** 01 (canon exists; C1-WritePath governs this rewrite)
- **Estimated Context:** ~70K
- **Concurrency Group:** 2

## Goal

Turn EX from a campaign diary into a terse protocol. The durable rules stay; the 27 dated incident entries move out; the INDEX becomes a routing table.

## Context

Measured structure of the current file (read it in slices with read_file - it is 53,657 chars):
- `## Overview` 2,603 chars - a prose digest duplicating INDEX content. DELETE (INDEX owns lookup).
- `## MANDATE: Full-Tree Execution` 50,429 chars = 94% of file. Contains: the real mandate (~1,200 chars, numbered rules 1-N ending before the dated entries), then 27 `###` dated incident sub-headings (24 carry 2026-09-* dates), then the `**Core principle:**` line at char 50,230, then `## When to Use` (16 chars).
- One sub-heading is duplicated verbatim: "Drift-audit dispatch contexts pay for themselves (2026-09-06, dependency-visibility tree)" appears twice.

Verified anchors:
- Target: ~/.hermes/skills/software-development/hierarchical-plan-execution/SKILL.md
- INDEX target: ~/.hermes/skills/software-development/hierarchical-plan-execution/references/INDEX.md
- ~204 reference files already exist under references/; many incidents already have matching files (e.g. pitfall-54-late-429.md, quickplan-tree-execution-2026-09-09.md, mlx-local-runtime-2026-09-06.md). Where a dated entry's content already lives in a ref file, do NOT duplicate it - the INDEX line routes to the existing file.

## Interface Contracts (From Parent)

- C1 canon: link it, do not restate it.
- C3: pitfall/protocol registry entries <=500 chars: `**Name.** TRIGGER: ... ACTION: ... DETAIL: references/<file>.md`
- C4: every reference file you create starts with `# title` + `When to use:` + `Lesson:` lines.
- C5: INDEX bullets one line each <=200 chars.
- Budgets: SKILL.md <=12,000; INDEX <=8,000 (verify_sizes.py / verify_index.py are the gates).

## Tasks

### Task 1: Extract incident entries to reference files

**Objective:** For each of the 27 dated `###` entries under MANDATE: if a reference file already carries the lesson, note its filename; if not, create one at references/<slug>.md with the C4 header plus the full entry text (cleaned, hyphens not em-dashes). Produce a mapping list: entry title -> file.

**Verification:** every entry title appears exactly once in your mapping; no lesson text is dropped (spot-check: pick any 3 entries and confirm their key sentences exist in a file on disk).

### Task 2: Rewrite SKILL.md

**Objective:** New file <=12,000 chars with this structure:

1. YAML frontmatter (keep existing name/description/version - bump version to 1.17.0; tags, related_skills per Task 4).
2. `## Overview` <=6 lines: what the skill does + canon pointer line (from 01).
3. `## MANDATE: Full-Tree Execution` - keep ONLY the numbered mandate rules and the Core principle line (~1,500 chars max). The mandate text is load-bearing; preserve its wording.
4. `## When to Use` - 3 bullets.
5. `## Execution Loop` - the orchestrator loop: dispatch per C1-Dispatch, review per C1-Review, commit per C1-Commit, tracking per C1-State. <=15 lines total.
6. `## Pitfall Registry` - one registry line (C3 format) per incident cluster, grouped under at most 6 bold group names (dispatch failures, shared-repo races, sibling collisions, verification discipline, provider degradation, campaign closeout). Target <=4,000 chars.
7. `## Escalation` - when to read references/INDEX.md and grep references/ directly.
8. `## Maintenance` - the C1-WritePath rules restated in 4 lines with a pointer to the canon.

### Task 3: Rewrite INDEX.md

**Objective:** One bullet per reference file (C5 format). Cover every file that exists in references/ (all ~204). If 200-char lines cannot say enough, the trigger phrase carries the weight; the file's own C4 header carries the rest. Existing reference files created by OTHER skills' sessions may lack C4 headers - do NOT edit those files in this leaf; their INDEX lines still work as routing.

**Verification:** `python3 scripts/verify_index.py` exits 0 for this INDEX.

### Task 4: Trim related_skills

**Objective:** Reduce frontmatter related_skills to: hierarchical-planning, subagent-driven-development. (Local-ravenx-review-pipeline and requesting-code-review are referenced from the Execution Loop only when needed, via canon C1-Review rationale.)

### Task 5: Run the gates

Run verify_sizes.py, verify_index.py, verify_styles.py. All EX-related failures must clear. Archive outputs to /tmp/skill-refactor-backup-20261026/gate-2.txt.

## Self-Verification Checklist

- [ ] SKILL.md <=12,000 chars; INDEX <=8,000 chars (wc -c proof in report)
- [ ] Mandate numbered rules and Core principle preserved verbatim (diff the excerpt against the old file from the /tmp backup)
- [ ] Mapping list covers all 27 dated entries; every mapped file exists on disk
- [ ] verify_index.py exits 0
- [ ] No protocol text dropped without landing in a reference file
- [ ] Hyphens only; no em-dashes anywhere in authored files
- [ ] Canon linked, not restated

## Review Checklist (For Review Agent)

- [ ] Pick 4 random registry lines: DETAIL targets exist and the target file actually contains the lesson (grep a key phrase)
- [ ] The mandate section reads complete without the diary (an agent could execute a tree from SKILL.md alone)
- [ ] INDEX line count roughly equals reference file count (no silent eviction)
- [ ] Old file preserved at /tmp/skill-refactor-backup-20261026/ for diff

**DO NOT COMMIT.** Orchestrator archives after review.

## Notes

Do not edit reference files owned by other sessions beyond prepending C4 headers where the INDEX routing requires it; when in doubt, leave the file and write a richer INDEX line.
