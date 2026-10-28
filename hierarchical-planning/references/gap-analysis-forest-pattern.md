# Gap-Analysis-Driven Forest Pattern


When to use: external engineering report to triage then build.
Lesson: parallel per-area analysis, SUPERIOR/PARITY/GAP verdicts, pre-authoring Q&A, then a forest.
## When to Use

User provides an external engineering report (competitor analysis, leaked source
reconstruction, feature comparison) and asks: "which of this can we add, and how
much value would it provide vs. what we already have?"

## Workflow

### Phase 1: Parallel Codebase Analysis (9 subagents, ~70s)

Dispatch one subagent per subsystem area. Each gets:
- The relevant section of the external report (verbatim, as context)
- A list of specific files to read in the existing codebase
- A structured question: "What exists? What's missing? What's architecturally
  different? What's SUPERIOR in the existing code?"

Subagent count: match the report's major sections (typically 6-10). Don't
over-slice — one subagent per cohesive subsystem, not per feature.

### Phase 2: Gap Analysis Synthesis (in-session)

For each area, assign a verdict:
- **SUPERIOR** — existing approach produces better results. Do not port.
- **PARITY** — functionally equivalent, different mechanism. Skip unless cheap.
- **GAP-HIGH** — missing, would meaningfully improve output quality
- **GAP-MED** — missing, moderate improvement
- **GAP-LOW** — missing, marginal improvement

**Critical:** assess "superior" on likelihood of producing superior RESULTS
(cleaner, more consistent builds), NOT on complexity or feature count. A
simpler approach that produces more consistent output is superior to a complex
one that doesn't.

Present as priority tiers:
- DO NOW (high impact, low effort)
- DO NEXT (high impact, medium effort)
- LATER (moderate impact)
- SKIP (existing is superior)

### Phase 3: Pre-Authoring Q&A (BEFORE any plan documents)

Collect all ambiguous design decisions. Format:
```
Q1: [TITLE]
Rec: [recommendation with rationale]
Impact: [what changes if decision goes the other way]
```

Rules:
- ≤10 questions per batch
- Do NOT write any plan documents until ALL are answered
- User may override any recommendation
- Terse answers may hide scope changes — read back and confirm
- **"I agree with the gaps, make the plan" is not How.** Stay in Q&A.
- **"Extrapolate" / "I'm still not sure" is not an answer.** Restate that one item as A/B/C with pros/cons. Ask for a letter.
- **Overloaded product nouns:** do not ask the user to classify types (`agent` vs `employee`). Ask who routes the behavior (the run). Meept 2026-08-29: harness-routed speak — session-attached bubble, detached notify, isolated child reports to parent.
- **"What other questions are there?"** List remaining tree-shape blockers. Do not hide them.
- **"Cover all significant points, not just the summary"** — plan inventory is the full do-now/do-next/later/skip list.
- **Model switch mid-Q&A (same user, same session):** the replacement model may lack prior-turn context beyond the transcript. Re-read the last user message + your last assistant message before answering; never reference "as I said above" details that are not actually in the visible transcript. Meept 2026-08-29: glm flash took over mid-Q&A and answered correctly by re-reading the visible turns only.
- **"Continue until the plan is complete"** = standing directive, not one wave. Do not stop after the current batch to report status: verify in-flight subagents (process list + git status sweep for silent deaths), review/commit finished leaves, dispatch the next wave, and keep the loop running. Each cycle: check disk → review landed work → commit → update tracking table → dispatch next concurrency group.

Example decisions from the meept session:
- Verification agent: independent agents vs. alternate front matter on existing
  definitions (answer: alt front matter, configurable model override, per-agent
  enable/disable)
- Anti-pattern scope: all agents vs. code-only (answer: all, but role-specific)
- Security scope: which of 4 gaps to address (answer: bash injection + secret
  discovery only)
- Model selection: hardcoded vs. resolver (answer: resolver with capability tier)

### Phase 4: Forest Decomposition

Default rec is a forest. **If the user says "1 tree," honor it.** One
`master.md` + numbered leaves in a flat dir. Do not still emit N masters.

Group by natural architectural seams:
- Large features (3+ leaves) → own tree (or own leaf group under the one master)
- Small related fixes → combined tree/leaf with multiple tasks
- Assign concurrency waves based on dependencies
- Serial-file ownership (one 6k-line `loop.go`) is a wave constraint, not a second tree

Typical shape for a 10-improvement gap analysis:
- 2-3 large trees (verification, prompt cache, etc.)
- 1 combined tree for 5-6 small improvements
- 1 leaf-only tree for trivial additions

### Phase 5: Author Forest

Standard forest pattern: SHARED-CONVENTIONS.md + master.md + per-tree
orchestrators + leaves. See Step 6.5 in SKILL.md.

## Worked Example: meept × Claude Code (2026-07-24)

Input: 1,693-line Claude Code v2.1.88 engineering report (20 sections,
~35,850 words covering system prompt architecture, prompt caching, verification
agents, tool orchestration, context compaction, hooks, memory, security, file
edit safety, command semantics).

Analysis: 9 parallel subagents reading ~50 source files across 7 internal
packages. Duration: 71s.

Gap analysis: 12 areas assessed. 6 SUPERIOR (tool orchestration, compaction,
memory, security, file editing, hooks). 2 GAP-HIGH (verification, anti-pattern
prompts). 1 GAP-HIGH strategic (prompt caching). 3 GAP-MED/LOW.

Q&A: 7 questions, all resolved in one round.

Forest: 5 trees, 14 leaves:
- Tree 01: Adversarial verification (3 leaves) — Wave 1
- Tree 02: Anti-pattern prompts (1 leaf) — Wave 1
- Tree 03: Prompt cache (2 leaves) — Wave 1
- Tree 04: Compaction user messages (1 leaf) — Wave 1
- Tree 05: Combined improvements (4 leaves) — Wave 2

Key design decisions encoded in the forest:
- Verification uses alternate front matter on existing agent definitions
  (not independent agents), with per-agent model override and enable/disable
- Anti-patterns are role-specific (coder gets code anti-patterns, planner gets
  planning anti-patterns) via conditional prompt components
- Prompt cache: Anthropic gets explicit cache_control markers; OpenAI-compatible
  relies on prefix stability. One boundary marker serves both.
- Explore agent uses model resolver with "fast" capability tier
- Inline skill feedback feeds into existing selfimprove pipeline
- Command semantics: pure Go implementation (no external grep dependency)
