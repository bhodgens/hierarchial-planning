# Skill Maintenance - Write-Path Policy Operations

When to use: before adding any lesson to this skill family, and at each quarterly consolidation pass.
Lesson: SKILL.md files are curated; lessons enter via INDEX + reference file, consolidate quarterly, evict after two unfired quarters; the verify scripts are the regression suite.

Operational loop (canon: plan-tree-canon.md C1-WritePath):

1. Appends. A new lesson = one line in this skill's `references/INDEX.md` (`- <file> - <trigger> - <one-line lesson>`, <=200 chars) plus the full lesson in a reference file opening with `# title` / `When to use:` / `Lesson:`. Never append dated entries, campaign narratives, or worked examples to SKILL.md.
2. Quarterly consolidation. Merge related incident reference files into terse invariants. Registry entries stay <=500 chars; INDEX lines stay one line.
3. Eviction. A reference file not fired or cited for 2 quarters moves to `references/archive/` with a line in that archive's `MANIFEST.md` and its INDEX line removed. Content is never deleted.
4. Regression suite. Run the four verify scripts (sizes, index, canon, styles - see `plans/20261026-skill-token-refactor/scripts/`) after any skill edit. Budgets are refactor triggers, not caps to raise. Repo-specific lessons belong in that repo's skill or docs, never in these global skills.
5. Hard failure signal. A SKILL.md near the ~100K `skill_view` cap means the write-path policy already failed - consolidate immediately. (Observed 2026-10-26: hierarchical-planning persisted to a 106K spill file instead of loading.)
