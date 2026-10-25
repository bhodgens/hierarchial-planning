# Plan Tree Authoring Patterns — Codebase Review Session (2026-07-23)

**Session**: Two-subagent codebase review + hierarchical plan creation  
**Date**: 2026-07-23  
**Outcome**: 4 plan trees created, all implemented, documentation gaps identified

---

## Context

User requested hierarchical plan creation for 11 items identified in a two-subagent codebase review. Created 4 complete plan trees under `docs/plans/20260723-*` covering HIGH/MEDIUM priority items.

---

## Pattern: Multi-Tree Forest with Date Prefix

When authoring multiple related plan trees in one session, use date-prefixed directories under `docs/plans/`:

```
docs/plans/
  20260723-panic-replacement/
    master.md
    01-*.md ... 05-*.md
  20260723-dispatcher-stop-wiring/
    master.md
    01-*.md
  20260723-config-extraction/
    master.md
    01-*.md
  20260723-memorystore-compaction/
    master.md
  20260723-review-action-plans-index.md  # Index document
  20260723-execution-summary.md          # Post-implementation summary
```

**Benefits:**
- Chronological grouping makes it easy to find related plans
- Date prefix prevents naming collisions across sessions
- Index document provides overview of all trees in the batch

---

## Pattern: Single-Leaf Plan Trees

For simple tasks (<2 hours effort), use single-leaf structure:

```
plan-name/
  master.md       # Root orchestrator with all required sections
  01-task.md      # Single leaf with full TDD tasks
```

**Required sections in master.md (even for trivial trees):**
- Goal
- Architecture Overview (2-3 sentences explaining context)
- Interface Contracts (what the leaf exposes: errors, constants, behavior changes)
- Child Index
- Dispatch Protocol
- Review Checklist
- Coding Conventions
- Completion Tracking Table
- Integration Test Plan

**Common omissions (Pitfall 33):**
- Interface Contracts → add even if trivial (e.g., "Exposes: new config field X with default Y")
- Architecture Overview → add 2-3 sentences (e.g., "The meept daemon has hardcoded operational parameters...")

---

## Pattern: Pre-Existing Implementation Detection

When creating plans, check git history first to avoid planning already-completed work:

```bash
# Check if feature is already implemented
git log --oneline --all | grep -i "<keyword>"

# Check if specific file was modified recently
git log --oneline -p --all -S "<function_name>" -- <file_path> | head -40
```

**In this session:**
- Dispatcher stop wiring was already implemented in commit `d4260d9f` (before plan created)
- Plan still useful as documentation and verification checklist
- Updated tracking table to note "Already implemented" status

---

## Pattern: Compliance Scanner Usage

Run the structural compliance scanner AFTER authoring all documents but BEFORE committing:

```bash
python3 ~/.hermes/skills/software-development/hierarchical-planning/scripts/check_template_compliance.py docs/plans/20260723-panic-replacement --strict-leaves
```

**What it checks:**
- Required orchestrator sections (Dispatch Protocol, Interface Contracts, etc.)
- Leaf markers ("Do NOT commit", Self-Verification checklist)
- Reports missing sections with file paths

**In this session:**
- Panic replacement: 100% compliant (only missing recommended Open Questions)
- Other 3 trees: Missing Interface Contracts (and 1 missing Architecture Overview)
- Fix effort: ~5 minutes per missing section

---

## Pattern: Implementation Verification

After plans are executed, verify completeness by:

1. **Check git commits:**
   ```bash
   git log --oneline | grep -E "<plan-keyword>"
   ```

2. **Verify files changed:**
   ```bash
   git show <commit-hash> --name-only | grep -E "\.go$"
   ```

3. **Run affected tests:**
   ```bash
   go test ./internal/<package>/... -v
   ```

4. **Confirm functional requirements:**
   ```bash
   # Example: verify zero panics remain
   grep -rn 'panic(' --include='*.go' internal/ | grep -v '_test.go' | wc -l
   # Expected: 0
   ```

**In this session:**
- All 4 plans had corresponding commits
- Tests passed for all affected packages
- Zero production panics confirmed after panic-replacement execution

---

## Pattern: GitHub Issue Creation from Review Findings

When architectural review identifies systemic issues, create GitHub issues:

```bash
gh issue create --title "<concise title>" --body '<detailed body>'
```

**Good issue structure:**
- Problem statement with specific file/line references
- Impact assessment (blocking/significant/minor)
- Proposed solution with effort estimate
- Acceptance criteria (checkboxes)
- References to plan trees or audit findings

**In this session, created 4 issues:**
- #20: Import cycle forcing code duplication
- #21: MemoryStore lacks compaction methods
- #22: Uneven test coverage in critical packages
- #23: Employee manager lifecycle incomplete (BLOCKING)

---

## Lessons Learned

### What Worked Well

1. **Two-subagent parallel review** — Bug-focused and architecture-focused agents found complementary issues
2. **Hierarchical plan trees** — Clear structure made execution straightforward
3. **Compliance scanner** — Caught missing sections before they became problems
4. **Git history check** — Identified pre-existing implementation (dispatcher stop)

### What Could Be Improved

1. **Interface Contracts omitted** — Even in simple single-leaf trees, these add clarity
2. **Architecture Overview skipped** — 2-3 sentences provide important context
3. **Open Questions not added** — Not critical here (no ambiguities), but good practice
4. **Scanner run after creation** — Should run BEFORE first commit (Pitfall 32)

### Key Insight

**Single-leaf trees feel "too simple" for full template compliance, but the template exists for a reason:** future readers (including your future self) need consistent structure to understand what the plan does, what it exposes, and how to execute it. The 5-minute cost of adding Interface Contracts and Architecture Overview pays off in maintainability.

---

## Template Snippets for Common Omissions

### Interface Contract (Single-Leaf Example)

```markdown
## Interface Contracts

This plan exposes:
- **New error**: `bus.ErrNoSubscribers` — returned when Publish has no subscribers
- **Behavior change**: `Publish` now always returns error when no subscribers (previously only panicked in debug mode)
- **Config fields**: `SessionConfig.SQLiteBusyTimeoutMs`, `SummaryPromptTruncationLimit`
```

### Architecture Overview (Simple Example)

```markdown
## Architecture Overview

The meept daemon has hardcoded operational parameters (URLs, timeouts, limits) scattered across multiple packages. This reduces deployment flexibility and makes tuning difficult without code changes. This plan extracts these values into the config schema with backward-compatible defaults.
```

---

## Related Skills

- `hierarchical-planning` — Core skill updated with Pitfall 33
- `writing-plans` — For single-agent features (use instead when scope is small)
- `design-plan-consistency` — For changelog integration when plans touch design docs
