# 00T - Verification Gate Scripts - Implementation Leaf

## Meta

- **Parent:** master.md
- **Scope:** Four Python scripts in the plan dir that verify the refactor. No skill files change in this leaf.
- **Dependencies:** none
- **Estimated Context:** ~30K
- **Concurrency Group:** 1

## Goal

Produce executable RED checks. Each script scans ~/.hermes/skills/software-development/ and exits nonzero with a per-item failure list while the corpus is unrefactored. After later leaves land, the same scripts must exit zero. The orchestrator commits to nothing until these exist and demonstrably fail.

## Context

Target root: /Users/caimlas/.hermes/skills/software-development/
Relevant files (current sizes in chars): hierarchical-planning/SKILL.md 99,911; hierarchical-plan-execution/SKILL.md 53,657; subagent-driven-development/SKILL.md 99,998; hierarchical-plan-execution/references/INDEX.md 59,768; hierarchical-planning/references/INDEX.md 10,932; hierarchical-planning/templates/leaf-template.md 7,459; hierarchical-planning/templates/master-template.md 13,551.

Known corpus facts the scripts may rely on:
- EX SKILL.md contains dated sub-headings like "(2026-09-06" (24 of them) under a "## MANDATE" section.
- HP SKILL.md contains a "## Session Pitfall Additions" section (6,498 chars) and numbered pitfalls with entries over 500 chars.
- Both big INDEX.md files contain multi-line paragraphs starting "- " (entries longer than 200 chars).
- Current reference files lack the 3-line trigger header ("When to use:" / "Lesson:").

## Interface Contracts (From Parent)

- Scripts live in /Users/caimlas/plans/20261026-skill-token-refactor/scripts/
- Python 3 stdlib only. No third-party imports.
- Each script prints one line per failure: `FAIL <item>` then a final summary line `EXIT <n failures>`; exits 1 on any failure, 0 when clean.
- A `--root <dir>` flag overrides the default target root (used later to scan without hardcoding).
- Char budgets are constants at the top of verify_sizes.py, matching master.md's baseline table.

## Tasks

### Task 1: verify_sizes.py

**Objective:** Enforce file char budgets, pitfall registry entry format, and absence of diary sections.

**Files:**
- Create: `scripts/verify_sizes.py`

**Logic:**
1. Budget map (must FAIL today): HP SKILL.md <= 42,000; EX SKILL.md <= 12,000; SDD SKILL.md <= 25,000; writing-plans/SKILL.md <= 15,000; EX INDEX.md <= 8,000; HP INDEX.md <= 4,000; leaf-template.md <= 5,000; master-template.md <= 8,000.
2. Registry check: for HP and SDD SKILL.md, parse numbered pitfall entries (`N. **Name.**`); any entry block over 500 chars FAILs.
3. Diary check: FAIL if a SKILL.md contains the heading `## Session Pitfall Additions` or 3+ sub-headings matching `\((20\d\d-\d\d-\d\d`.

**Step 1: Write the script**
**Step 2: Run against the real root**

Run: `python3 scripts/verify_sizes.py`
Expected: FAIL lines for every budget (8 files over budget), registry entries over 500 chars in HP, `## Session Pitfall Additions` in HP, dated headings in EX and HP. EXIT > 0.

**Step 3: Self-test the checker itself**
Create a tiny fixture dir under /tmp with a compliant fake skill tree; run the script with `--root /tmp/fixture`; Expected: EXIT 0.

### Task 2: verify_index.py

**Objective:** Enforce INDEX.md one-line format, link integrity, and reference-file trigger headers.

**Files:**
- Create: `scripts/verify_index.py`

**Logic:**
1. For EX and HP `references/INDEX.md`: every line starting `- ` must be <= 200 chars (continuation lines of a paragraph count as a violation - detect by: a bullet line whose entry spans >1 line FAILs).
2. Every filename mentioned in an INDEX must exist in the same references/ dir.
3. Every .md file listed in the NEW-format INDEX must open with lines matching `When to use:` and `Lesson:` within its first 5 lines - SKIP this check while the INDEX still has multi-line entries (i.e. only enforce rule 3 when rule 1 passes for that INDEX).

**Run:** Expected today: FAIL on both INDEXes (multi-line entries). EXIT > 0.

### Task 3: verify_canon.py

**Objective:** Verify the canon file exists with frozen section IDs.

**Files:**
- Create: `scripts/verify_canon.py`

**Logic:**
1. Canonical path: <root>/hierarchical-planning/references/plan-tree-canon.md. FAIL if missing.
2. Required headings: `## C1-Nodes`, `## C1-Status`, `## C1-Commit`, `## C1-Dispatch`, `## C1-Review`, `## C1-Sizing`, `## C1-State`, `## C1-WritePath`.
3. Canon file <= 6,000 chars.

**Run:** Expected today: FAIL (file does not exist).

### Task 4: verify_styles.py

**Objective:** Style sweep over files authored by this refactor.

**Files:**
- Create: `scripts/verify_styles.py`

**Logic:**
1. Scan the four SKILL.md files + both INDEX.md + templates + canon for em-dashes (U+2014) - FAIL per hit.
2. Fail on ASCII art or line lengths over 500 chars in those files.
3. Today this may partially pass; that is fine. It must exit 1 if any authored file later introduces an em-dash. Verify the em-dash detector with an inline self-test: run with `--selftest` which checks the detector against a known-bad string and exits 0 only if the detector catches it.

## Self-Verification Checklist

- [ ] All four scripts exist in scripts/ and run with no third-party imports
- [ ] Each exits 1 against the current corpus (except verify_styles which may pass; its selftest passes)
- [ ] verify_sizes.py fixture test exits 0 on a compliant fake tree
- [ ] Each failure line names the offending file and rule
- [ ] No file under ~/.hermes/skills/ was modified
- [ ] Full outputs saved to /tmp/skill-refactor-backup-20261026/gate-0T-red.txt

## Review Checklist (For Review Agent)

- [ ] Budgets in verify_sizes.py match master.md baseline table exactly
- [ ] Canon section IDs match contract C1 exactly
- [ ] INDEX line-length logic actually catches a 2-line entry (fixture proof)
- [ ] Scripts are idempotent and read-only

**DO NOT COMMIT.** No git repo exists. The orchestrator archives state after review.

## Notes

RED evidence matters more than speed here: the orchestrator will paste gate output into the final report as proof the checks bind.
