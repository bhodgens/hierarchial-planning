# Aaudit complete branches
When to use: tracking tables say COMPLETE, branches disagree.
Lesson: audit table vs branch state before trusting completion.

# Audit-Complete Branches: When Tracking Tables Lie

> Pattern for Step 1.5 (Pre-Dispatch Already-Implemented Check), extended to
> the branch level. When tracking tables are stale and code is already written,
> do NOT dispatch subagents — audit in-session.

## Session

- **Date:** 2026-08-07
- **Project:** rebellion-the-game (Godot 4.7 port)
- **Plan tree:** `plans-godot/master.md` (14 branches, ~50 leaves)
- **Task:** "implement what remains with branches 01, 02, 03, 05"

## The Problem

The tracking table (set 2026-07-25, ~2 weeks old) listed all 4 target branches
as IN_PROGRESS with notes like:
- "Beehave behavior tree NOT installed (npc_controller references it)"
- "NO period .tres theme found"
- "not run end-to-end"

The actual codebase (audited at dispatch time) had:
- 174 .gd scripts (tracking said 63), 49.7K lines (tracking said 15.1K)
- Beehave addon fully installed at `addons/beehave/` with 6 BT action nodes
- Period theme at `resources/themes/period_theme.tres`
- 32 GUT test suites with 969/979 tests passing
- Legacy duplicates (redcoat_ai.gd, inventory.gd, world/grapple_system.gd) all
  deleted by prior remediation work

## The Failed Approach: Parallel Subagent Audit

4 subagents dispatched in parallel, one per branch. Each was told to:
1. Read the leaf specs
2. Verify code against spec
3. Fix gaps
4. Run GUT tests

**All 4 timed out at 600 seconds with zero useful output.**

Root cause: each subagent independently tried to run the same ~120s headless
Godot GUT suite (`/Applications/Godot.app/Contents/MacOS/Godot --headless ...`).
Four processes contending for the same Godot project, same import cache, same
test binary — they serialised or deadlocked, burning all 600s on test
infrastructure alone.

## The Correct Approach: In-Session Spec Audit

**Time: ~15 minutes across two rounds. Result: 40+ leaves audited across 8
branches (01-08 + 10), all marked COMPLETE, 3 files implemented for genuine gaps.**

Round 1 (branches 01-03, 05): 21 leaves, 18 COMPLETE, 3 new files for leaf 08.
Round 2 (branches 06-08, 10): 19 leaves, all COMPLETE, 0 new files needed
(cross-tree remediation had already filled save-overlay and retargeting gaps).

### Step 1: Survey actual codebase state (1 minute)

```bash
# Count files — compare against tracking table claims
find rebellion-godot -name '*.gd' -not -path '*/addons/*' | wc -l
find rebellion-godot -name '*.tscn' -not -path '*/addons/*' | wc -l

# List all scripts by directory to see what exists
find rebellion-godot/scripts -name '*.gd' -not -path '*/addons/*' | sort

# Check for specific items tracking says are "missing"
find rebellion-godot/addons/beehave -type d   # Was listed as NOT installed
find rebellion-godot -name '*theme*.tres'     # Was listed as not found
```

### Step 2: Run GUT suite once to get baseline (2 minutes)

```bash
timeout 180 /Applications/Godot.app/Contents/MacOS/Godot \
  --headless --path rebellion-godot \
  -s addons/gut/gut_cmdln.gd -gconfig=.gutconfig.json -gexit \
  2>&1 | tail -20
```

Parse the summary: "Passing Tests 969 / Failing Tests 2" — the 2 failures were
in uncommitted tree-18 code, not in scope.

### Step 3: Per-leaf spec audit (30 seconds per leaf)

For each leaf, read the spec's Self-Verification Checklist, then `search_files`
for the specific constants/APIs in the actual source:

```
# Leaf 01-movement-traversal spec says: WALK_SPEED=1.4, SPRINT_SPEED=5.5
search_files path=".../player_controller.gd" pattern="SPEED_WALK|SPEED_SPRINT"
# Result: SPEED_WALK: float = 1.4, SPEED_SPRINT: float = 5.5 → MATCH

# Leaf 05-stranger-penalty spec says: 80% initial penalty
search_files path=".../stranger_penalty_system.gd" pattern="80|INITIAL_PENALTY"
# Result: INITIAL_PENALTY: float = 80.0 → MATCH

# Leaf 01-sidecar-client spec says: StreamPeerTCP port 10909
search_files path=".../sidecar_client.gd" pattern="StreamPeerTCP|10909"
# Result: var _peer: StreamPeerTCP, const SIDECAR_PORT: int = 10909 → MATCH
```

### Step 4: Implement genuine gaps directly

When a gap is found, implement it in-session. In this session, leaf 08 had 3
missing files (reading_system.gd, clothing_system.gd, disguise_system.gd).
Each was ~100-150 lines with a clear spec. Implemented directly via write_file
in ~5 minutes total.

### Step 5: Run GUT once more, update tracking tables, commit

```
# Verify new code compiles + nothing broke
timeout 180 ... -s addons/gut/gut_cmdln.gd -gconfig=.gutconfig.json -gexit
# Result: 977/987 (was 969/979 — 8 new tests, no regressions)
```

Update the tracking tables in master.md + each branch orchestrator with
COMPLETE status, date, and audit evidence. Commit.

## Why This Works

1. **The orchestrator already holds the spec in context** from reading leaf
   docs. No subagent can match the orchestrator's understanding of what the
   spec requires.

2. **`search_files` is faster than reading entire files.** Pattern-matching
   for `SPEED_WALK|INITIAL_PENALTY|StreamPeerTCP` takes <1 second vs reading
   a 2580-line player_controller.gd to find a constant.

3. **One GUT run at the end, not N runs during.** The GUT suite takes ~120s.
   Running it once after all changes is 4x faster than 4 subagents each
   running it once (even without contention).

4. **Gaps found during audit are small.** In this case, 3 files totaling ~370
   lines — well within orchestrator capability. Dispatching a subagent for
   each would have taken longer than writing them directly.

## When to Use This Pattern

- Tracking table is >1 week old
- Codebase has significantly more files/lines than tracking claims
- GUT test suite exists and most tests pass
- The task is "implement what remains" or "complete these branches"
- **Forest/multi-tree plans authored days ago:** trees other sessions executed
  show up as commit-message evidence (`git log --oneline | grep "<tree name>"`)
  even when the forest root table still says PENDING everywhere. Per-tree
  tracking tables may be accurate while the ROOT is the stale one — read both
  directions of drift. (meept llm-resilience-forest, 2026-09-01: 3 of 5 trees
  COMPLETE via 16 sibling commits, one tree mid-flight with uncommitted leaf
  edits in the working tree, root table said all-PENDING.)
- **Dispatch verification-only subagents, not implementers, when uncertain:**
  "Verify this leaf against the spec; if already implemented and committed,
  report that and make ZERO changes." A correct verification return is a no-op
  report in ~3 minutes — dramatically cheaper than a duplicate implementation,
  and the report doubles as an independent audit of the sibling's work.

## When NOT to Use

- Tracking table is fresh (<2 days) — trust the status, dispatch normally
- No test suite exists — subagents can run their own compilation checks
- Branches genuinely need fresh implementation (no existing code)
- Test suite is fast (<10s) — contention is not an issue
