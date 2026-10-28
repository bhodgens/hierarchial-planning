# Skill-Family Token Refactor - Implementation Orchestrator

## Meta

- **Plan dir:** /Users/caimlas/plans/20261026-skill-token-refactor/
- **Target:** ~/.hermes/skills/software-development/ (hierarchical-planning, hierarchical-plan-execution, subagent-driven-development, writing-plans, plan-leaf-validation)
- **Date:** 2026-10-26
- **Source analysis:** Hermes session 2026-10-26 token-efficiency report (measured numbers below are from that scan)

## Goal

Cut the skill family's trigger-time token cost by ~80% without losing any protocol. Refactor order: architectural fixes first (shared canon, write-path policy), then per-skill rewrites, then templates and wiring, then a gated final audit.

## Architecture

The family's bloat is accretion, not duplication (0-0.1% verbatim overlap measured). Two diseases:

1. SKILL.md files double as campaign diaries. hierarchical-plan-execution (EX) is 53,657 chars; 94% is one "MANDATE" section holding 27 dated incident entries. The durable protocol is one line at char 50,230, and the file ends right after it. hierarchical-planning (HP) has a 38.8K-char "Common Pitfalls" block plus a 6.5K-char "Session Pitfall Additions" log. subagent-driven-development (SDD) is 100K chars with the same pattern.
2. No write-path policy: appends go straight into SKILL.md, indexes are multi-paragraph digests (EX INDEX.md = 59.8K chars), and nothing consolidates or evicts.

Fix shape: each SKILL.md keeps a terse protocol + a one-line pitfall registry that routes to reference files. Reference files carry full narratives with 3-line trigger headers. INDEX.md files become one-line routing tables. A new shared canon file (nodes, status lifecycle, commit ownership, dispatch shape, sizing, write-path policy) removes concept-level duplication across the four skills. Templates move to a task-table format so every future plan tree spends fewer tokens per leaf. Verification is scripted (leaf 00T) and must fail RED before the refactor starts.

Execution order matters: architectural leaves (canon, write-path policy) land before rewrites, so rewrites only reference frozen contract IDs.

## Baseline inventory (measured 2026-10-26)

| File | Chars | ~Tokens | Target chars |
|---|---|---|---|
| HP SKILL.md | 99,911 | ~25,000 | <=42,000 |
| EX SKILL.md | 53,657 | ~13,400 | <=12,000 |
| SDD SKILL.md | 99,998 | ~25,000 | <=25,000 |
| writing-plans SKILL.md | 14,985 | ~3,700 | <=15,000 (trim only) |
| EX references/INDEX.md | 59,768 | ~15,000 | <=8,000 |
| HP references/INDEX.md | 10,932 | ~2,700 | <=4,000 |
| HP templates/master-template.md | 13,551 | ~3,400 | <=8,000 |
| HP templates/leaf-template.md | 7,459 | ~1,900 | <=5,000 |

Corpus: HP 101 files / 621KB (100 refs), EX 208 files / 1.24MB (204 refs), SDD 18 files / 175KB (17 refs), plan-leaf-validation 16 files / 78KB, writing-plans 1 file.

## Interface Contracts

### C1 - Canon file

Path: ~/.hermes/skills/software-development/hierarchical-planning/references/plan-tree-canon.md
Required section IDs (frozen; rewrites may link, never rename):

- C1-Nodes: master.md / orchestrator.md / leaf.md roles
- C1-Status: PENDING, TESTS_IN_PROGRESS, TESTS_VALIDATED, IN_PROGRESS, IMPLEMENTED, REVIEWED, COMPLETE, BLOCKED
- C1-Commit: only orchestrators commit; implementers never run git commit or git add
- C1-Dispatch: delegate_task batch shape (tasks[] with per-item goal + context)
- C1-Review: review in-session by main model, never delegated
- C1-Sizing: 128K context rule, 25-minute wall-clock budget, split at seams
- C1-State: tracking table is the single source of truth; volatile state stays out of protocol files
- C1-WritePath: skill write-path policy (see C2)

### C2 - Write-path policy (lives in canon as C1-WritePath)

- SKILL.md files are curated. Never append dated session entries to them.
- New lessons: one line appended to the owning skill's references/INDEX.md + full lesson in a reference file with a 3-line trigger header (filename - when to use - one-line lesson).
- Consolidation pass each quarter: merge related incident entries into terse invariants, delete superseded narratives.
- Eviction: an entry not referenced or fired for 2 quarters gets demoted to an archive dir.
- Repo-specific lessons live in that repo's skill or repo docs; global skills hold invariants only.

### C3 - Pitfall registry entry format

`N. **Name.** TRIGGER: one clause. ACTION: one clause. DETAIL: references/<file>.md`
Each entry <=500 chars. Full narrative (if any) goes in the referenced file.

### C4 - Reference file header format

Every reference file created or listed by a rewritten INDEX starts with:

```
# <title>
When to use: <one clause trigger>
Lesson: <one sentence>
```

### C5 - INDEX.md format

One bullet per reference file: `- <filename> - <trigger> - <one-line lesson>`. Each line <=200 chars. No multi-paragraph digests.

### C6 - Frozen leaf docs

Leaf documents in this plan are frozen at dispatch. Corrections ride the dispatch context as dated addenda. Files are never edited mid-execution.

## Child Document Index

| Leaf | Scope | Est. context | Depends on | Wave |
|---|---|---|---|---|
| 00T-gate.md | Verification scripts (must fail RED on current corpus) | ~30K | none | 1 |
| 01-canon.md | Canon file + write-path policy | ~30K | 00T (scripts exist) | 1 |
| 02-execution-skill.md | EX SKILL.md rewrite + INDEX + incident extraction | ~70K | 01 | 2 |
| 03-planning-skill.md | HP SKILL.md pitfalls registry + INDEX + extraction | ~80K | 01 | 2 |
| 04-dispatch-skill.md | SDD SKILL.md rewrite + INDEX | ~60K | 01 | 2 |
| 05-templates-wiring.md | Template redesign + related_skills trim + integration tables | ~50K | 02, 03 | 3 |
| 06-final-audit.md | Full gate run + before/after report + maintenance doc | ~40K | 00-05 | 4 |

## Dispatch Protocol

Phase 0 (orchestrator, before any dispatch):
1. Backup: `cp -R ~/.hermes/skills/software-development /tmp/skill-refactor-backup-20261026/`
2. Record baseline: `find <target dir> -name '*.md' -size +1k | xargs wc -c > /tmp/skill-refactor-backup-20261026/baseline-bytes.txt`

Phase 1: dispatch 00T, review, then 01. Gate scripts must fail RED against the current corpus before any rewrite lands, and pass GREEN against the canon state after 01.

Phase 2: dispatch 02, 03, 04 in parallel. Each brief inlines: its target file inventory (sizes above), contracts C1-C6, and the rule that no git exists (orchestrator snapshots state dirs instead of committing).

Phase 3: dispatch 05 after 02 and 03 are REVIEWED (template headings must match the landed SKILL.md text).

Phase 4: dispatch 06. Gate scripts green, report produced.

No git repository exists at ~/.hermes/skills. Replace every "commit" step with: orchestrator copies the touched subtree to /tmp/skill-refactor-backup-20261026/post-<leaf>/ after REVIEWED. The backup dir is the rollback path.

## Review Checklist

- [ ] Leaf output matches its Self-Verification checklist
- [ ] No protocol text was dropped without a reference file receiving it (spot-check 3 deletions per skill: text must exist in a ref)
- [ ] Contracts C1-C6 respected (canon IDs not renamed; registry and INDEX formats match)
- [ ] Target char budgets met (baseline table)
- [ ] No em-dashes in authored files (user convention: hyphens only)
- [ ] Gate scripts run clean for finished leaves

## Completion Tracking Table

| Leaf | Status | Notes |
|---|---|---|
| 00T-gate | REVIEWED (2026-10-26 orchestrator, in-session) | RED proven: sizes 12, index 67, canon 1, styles 14 failures vs corpus; fixture GREEN; selftest PASS; archived gate-0T-red.txt. Scripts authored by orchestrator per plan (00T output reviewed against leaf checklist) |
| 01-canon | REVIEWED (2026-10-26 orchestrator, in-session) | Canon 4,317 chars, verify_canon GREEN; 4 pointer lines (+121 chars each) only mods; diff scope clean |
| 02-execution-skill | REVIEWED (2026-10-26 orchestrator, in-session) | 11,937 chars; INDEX 7,978; mandate+Core principle verbatim; 116-file archive intact w/ MANIFEST; 0 EX gate failures. Budget conflict resolved via canon eviction - flagged to 06 |
| 03-planning-skill | REVIEWED (2026-10-26 orchestrator, in-session) | 41,834 chars; INDEX 3,991; numbering 1-42 preserved (41 absent in source too); verify_index EXIT 0; archive 76 files + MANIFEST (written by orchestrator) |
| 04-dispatch-skill | REVIEWED (2026-10-26 orchestrator, in-session) | 13,051 chars; INDEX 27/27 files, all <=200 chars; 28 registry entries; overlap vs HP 13 8-grams (no copying); INDEX added to styles scan |
| 05-templates-wiring | REVIEWED (2026-10-26 orchestrator, in-session) | leaf-tpl 4,984 / master-tpl 6,714 / writing-plans 14,924; scanner fixture ALL COMPLIANT (re-run by orchestrator); all 4 gates EXIT 0; write-once rule present (wording reflowed, rules intact) |
| 06-final-audit | COMPLETE (2026-10-26, in-session - subagent blocked by denied compound command; orchestrator completed per gap-fix protocol) | All gates GREEN (re-archived post-pointer); REPORT.md written; archives lossless (0 data loss); 15/15 routing spot-checks; pitfall-41 absence confirmed in source; skill-maintenance.md + 4 pointers wired, budgets hold (EX headroom 14, WP 27) |

## Test Gate

| Check | Script | Applies to |
|---|---|---|
| Char budgets | verify_sizes.py | all SKILL.md + INDEX.md + templates |
| Registry format (<=500 chars/entry) | verify_sizes.py | HP, SDD pitfall sections |
| No dated diary headings in SKILL.md | verify_sizes.py | EX, HP |
| INDEX one-line format | verify_index.py | EX, HP INDEX.md |
| INDEX entries point to existing files | verify_index.py | EX, HP INDEX.md |
| Trigger headers on listed refs | verify_index.py | refs listed in new INDEXes |
| Canon file + C1 section IDs present | verify_canon.py | canon file |
| Em-dash sweep | verify_styles.py | all authored files |

RED definition: against the pre-refactor corpus, every script exits nonzero with a per-item failure list. GREEN definition: zero failures. 06 re-runs all four and archives output.

## Integration Test Plan

1. Run all four scripts in plan-dir scripts/ against ~/.hermes/skills/software-development/ - expect zero failures after 06.
2. Before/after table: wc -c on every file in the baseline manifest, diffed against post-refactor; report bytes and tokens (bytes/4) saved per file.
3. Functional spot-check: skill_view(name='hierarchical-plan-execution') returns full content under the tool cap (it persisted to a spill file pre-refactor at 106K chars).
4. Routing spot-check: pick 5 INDEX lines at random; confirm each target file exists and opens with a trigger header.
5. Cross-skill: grep the four SKILL.md files for "plan-tree-canon.md" links resolve to the canon file.

## Coding Conventions

- Plain language. Short sentences. Define any term an agent would not know.
- Hyphens, never em-dashes.
- Imperative voice for rules; declarative for facts.
- Every rule that a script can check gets a script (C1-WritePath enforcement, budgets, formats).
- Worked-example narration (session dates, campaign names) lives in reference files, not SKILL.md. One-line evidence notes are allowed next to a rule.

## Structural Completeness Check

Run scripts/verify_sizes.py + verify_index.py + verify_canon.py after each wave; archive outputs to /tmp/skill-refactor-backup-20261026/gate-<wave>.txt.

## Notes

- Source analysis found zero verbatim duplication across the corpus; all reduction here is extraction and compression, never deletion of unique lessons.
- writing-plans SKILL.md (15K chars) is healthy; leaf 05 only trims its related_skills list and adds the canon link.
- plan-leaf-validation needs no changes; it models the target shape.
- The 100K skill_view cap bit this very session (HP SKILL.md persisted to a spill file). Post-refactor, both big skills must load inline.
