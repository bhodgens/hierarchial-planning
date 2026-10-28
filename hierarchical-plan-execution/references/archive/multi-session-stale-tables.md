# Mmulti session stale tables
When to use: tracking tables stale across sessions.
Lesson: stale-table audit and reconciliation.

# Multi-Session Stale Tracking Tables

## The Problem

Tracking tables in hierarchical plan trees drift badly in multi-session projects.
Code gets written and committed by other sessions, agents, or the user directly
without updating the plan's completion tracking table. A tree that says "all
IN_PROGRESS" may actually be 90% complete.

This is the single most common failure mode when resuming a hierarchical plan
tree across sessions: the orchestrator trusts stale tables, dispatches greenfield
implementation agents, and either (a) re-implements code that already exists,
creating duplicate files and merge conflicts, or (b) wastes hours of subagent
time re-discovering what was already built.

## Detection Signals

- The plan tree was authored or last updated >3 days ago.
- Multiple commits exist since the last "Implemented Date" in the tracking table.
- The `git log` shows commits from multiple agents/sessions.
- The tracking table says IN_PROGRESS but has no "Implemented Date" or agent
  session identifier filled in.
- The project has a test suite that runs and passes (indicating substantial
  working code).

## Assessment Procedure

Run this BEFORE dispatching any implementation agents:

1. **File inventory:** Count source files and total lines.
   ```bash
   # Godot/GDScript
   find <src-dir> -name '*.gd' -not -path '*/addons/*' | wc -l
   find <src-dir> -name '*.gd' -not -path '*/addons/*' -exec wc -l {} + | tail -1

   # Go
   find <src-dir> -name '*.go' -not -path '*/vendor/*' | wc -l
   ```

2. **Test baseline:** Run the project's test suite and record pass/fail counts.
   ```bash
   # Godot/GUT
   timeout 180 <godot-binary> --headless --path <project> \
     -s addons/gut/gut_cmdln.gd -gconfig=.gutconfig.json -gexit 2>&1 | tail -20

   # Go
   go test ./... -count=1 2>&1 | tail -10
   ```

3. **Check claimed-missing items:** The tracking table often says things like
   "Beehave addon NOT installed" or "no period .tres theme." Verify these claims
   directly with `find` / `search_files`. Claimed-missing items are frequently
   already present.

4. **Check claimed-present duplicates:** The table may say "two overlapping
   impls, not reconciled." Verify the duplicate was actually deleted by checking
   if the file exists.

5. **Compare actual file inventory against leaf specs:** If leaf 01 says
   "create player_controller.gd with movement, stamina, camera" and the file
   already exists at 2580 lines with all those features, that leaf is likely
   COMPLETE or near-complete.

## Decision: Implement Mode vs Audit-and-Verify Mode

| Signal | Implement Mode | Audit-and-Verify Mode |
|--------|---------------|----------------------|
| File count vs spec | <30% of described files exist | 50%+ of described files exist |
| Test suite | No tests or <50% passing | 80%+ passing with real coverage |
| Tracking table recency | Updated within last session | >3 days old, multiple sessions since |
| Claimed-missing items | Confirmed missing | Confirmed present (table was wrong) |
| Duplicate scripts | Still present | Deleted (remediation done) |

### Implement Mode
Dispatch implementation agents as the skill normally describes (Step 3b).

### Audit-and-Verify Mode

**Prefer in-session audit over dispatched audit agents.** The orchestrator
already holds the spec in context and can verify code in seconds via
`search_files` for specific constants/APIs. See
`references/audit-complete-branches.md` for the full in-session procedure.

When audit agents ARE dispatched, each agent gets:
- The leaf spec (tasks, files to touch, verification checklist)
- The actual file inventory for its branch (file paths, line counts)
- Instruction to VERIFY code matches spec, FIX GAPS — not write from scratch
- Report per-leaf status: COMPLETE or GAPS FOUND (with what was fixed)

Shape the goal as: "Audit and complete Branch X. Verify all N leaves against
existing code, fix gaps, report results."

### PITFALL: Parallel audit agents can timeout on shared test infrastructure

If the project has a slow test suite (Godot/GUT takes ~120s per run), do NOT
dispatch parallel audit agents that each independently try to run tests. They
will contend on the same process/import cache/binary and all timeout.

**Real failure (2026-08-07):** 4 parallel audit agents for rebellion-the-game
all timed out at 600 seconds with zero useful output because each tried to run
the same headless Godot GUT suite simultaneously. Four Godot processes
contending for the same project directory deadlocked.

**Fix:** Run the test suite ONCE in-session (before or after the audit), not
once per agent. If agents must run tests, use a single shared test run or
have agents skip test execution and report code-only findings.

### In-session audit procedure

1. Survey codebase: count files, list scripts by directory, check for
   claimed-missing items with `find` / `search_files`.
2. Run test suite once to get baseline (pass/fail counts).
3. Per-leaf: read spec checklist, `search_files` for the specific
   constants/APIs in the actual source. Each leaf takes ~30 seconds.
4. Implement genuine gaps directly via `write_file` / `patch`.
5. Run test suite once more, update tracking tables, commit.

## Cross-Tree Work Contamination

When one plan tree's leaves fill gaps in a DIFFERENT plan tree's branches, the
second tree's tracking table is never automatically updated. This is invisible
stale-table drift that even a careful audit can miss. The inverse also happens:
per-tree masters get faithfully updated by sibling sessions while the FOREST
ROOT table stays all-PENDING (meept llm-resilience-forest, 2026-09-01 — see
§ Sibling-Session Collision above). Reconcile BOTH directions when adopting a
forest: root table from tree tables, tree tables from code.

When one plan tree's leaves fill gaps in a DIFFERENT plan tree's branches, the
second tree's tracking table is never automatically updated. This is invisible
stale-table drift that even a careful audit can miss.

**Real instance (rebellion-the-game, 2026-08-07):**
- Plan tree 15-remediation-completion had a leaf "02-save-completion" that added
  13 overlay sub-objects to `save_system.gd` and a leaf "03-animation-retargeting"
  that created `retargeting_helper.gd` + `bone_name_map.gd`.
- These are the SAME files tracked by plan tree 18-godot-port branches 07-save-load
  and 10-animation.
- The godot-port tracking table stayed at "IN_PROGRESS: seed+overlay NOT implemented"
  and "retargeting leaf has NO code" for TWO WEEKS after remediation completed them.
- Only discovered when the in-session audit searched for the actual functions.

**Fix for orchestrators:** When you complete a remediation/cross-tree leaf that
touches another tree's tracked files, search the build-plan-index for any tree
whose GDD spec source matches the files you changed. If found, update that tree's
tracking table too — not just your own tree's. Set Drift Found = YES in the
Implementation Record if the other tree was at COMPLETE, or update its status
if it was at IN_PROGRESS.

## Sibling-Session Collision on Multi-Tree Forests

meept llm-resilience-forest, 2026-09-01: a five-tree forest was authored and
committed; on the NEXT session's "implement the full forest" the baseline recon
found sibling sessions had already executed THREE trees to COMPLETE (16 commits)
while the forest root tracking table said PENDING everywhere — and tree 02 was
mid-flight with leaf 03's edits sitting UNCOMMITTED in the working tree. The
stale-table problem here runs in the opposite direction from the usual case:
the tables were stale not because workers forgot to update them, but because
sibling sessions wrote to the per-tree masters (their own tracking tables said
COMPLETE, with honest commit hashes) and never touched the forest ROOT.

Detection procedure before any forest-scale dispatch:

1. `git log --oneline -40 | grep -i "<tree>"` per tree — commit messages naming
   tree/leaf numbers are ground truth; tracking tables are claims.
2. Read EVERY tree's tracking table, not just the root's.
3. `git status --short` — dirty files belong to an IN-FLIGHT sibling leaf.
   These files are fenced: your leaves must not touch them, and any leaf whose
   scope overlaps a dirty file waits for the sibling to land. The real dispatch
   order is the DIRTY-FILE dependency graph layered on top of the plan's
   declared dependency graph.
4. When uncertain whether a leaf is done, dispatch a VERIFICATION-ONLY subagent
   with an explicit "verify against spec; if already implemented and committed,
   report that and make ZERO changes." The correct outcome is a no-op report —
   this happened verbatim (context-discovery leaf) and cost 3 minutes instead
   of a duplicate implementation.
5. After committing on such a repo, `git show --stat` your own commit: an
   aggressive pre-commit hook auto-staged a sibling's WIP files (new command +
   its generated docs) into an otherwise docs-only commit. Content was the
   sibling's and reviewed sound — flag it, do not rewrite history.
6. Trees a sibling owns are NOT yours to gate or finish: record their state in
   the forest root ("COMPLETE", "IN_PROGRESS — leaf N in flight by parallel
   session"), hold your gated trees on their completion signals, and take only
   the work they have not claimed (leaf 04 was marked HELD by the sibling itself
   with the reason: conflict with tree 02's client.go).

Related: `references/multi-session-repo-hazards.md`,
`references/shared-repo-parallel-agents` guidance in devops skills.

## Real-World Instance

rebellion-the-game Godot port, 2026-08-07 (two sessions):

**Session 1 (parallel agents — FAILED):** 4 parallel audit agents dispatched
for branches 01, 02, 03, 05. All 4 timed out at 600s due to Godot process
contention on the shared GUT test suite. Zero useful output.

**Session 2 (in-session audit — SUCCEEDED):** Same 4 branches audited
in-session in ~10 minutes. 21 leaves verified, 18 marked COMPLETE, 3 files
implemented for genuine gaps. Then extended to branches 06, 07, 08, 10 — all
verified COMPLETE. Total: 11 MVP branches marked COMPLETE across two commits.

**Tracking table said** (set 2026-07-25): All branches IN_PROGRESS, "not run
end-to-end," specific claims like "Beehave addon NOT installed," "no period
.tres theme," "two overlapping grapple implementations not reconciled."

**Actual state**: 174 GDScripts (49.7K lines), 40 scenes, 32 test suites,
977/987 tests passing, Beehave addon installed with 6 BT action nodes, period
theme present at `resources/themes/period_theme.tres`, all remediation duplicates
deleted (redcoat_ai.gd, legacy inventory.gd, world/grapple_system.gd). 8 Piper
TTS voices deployed.
