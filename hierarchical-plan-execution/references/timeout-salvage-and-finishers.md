# Ttimeout salvage and finishers
When to use: salvaging timed-out leaves.
Lesson: finisher dispatch pattern.

# Timeout Salvage & Finisher Dispatch

Pattern proven across the 2026-08-23 rebellion sessions (plans-combat-audit,
plans-sandbox): subagents ending status=timeout or "did not produce a
response" frequently LAND their complete work in the working tree anyway.
4 of 6 timeouts across those two sessions were salvageable without
re-dispatch.

## Salvage procedure (before ANY re-dispatch)

1. `git status --short` — look for the leaf's expected files (new files or
   modifications matching its task list).
2. Run the leaf's own verification command from its document (test suite,
   build, grep checks).
3. Decide:
   - **Green** → review + commit as normal. Do NOT re-dispatch; a fresh run
     duplicates work, conflicts with landed edits, or corrupts finished code.
   - **Partial (N failures remain)** → dispatch a FINISHER: a small-scope
     agent briefed with ONLY the remaining failures ("these 2 tests fail:
     X, Y — fix to green"), never the full leaf again. Proven twice: clinch
     landed 13/15 and a finisher took it 15/15; intro-director landed 13/16
     with a known signal-arity bug and a finisher fixed it 16/16.
   - **Nothing landed** → re-dispatch normally.

## Why timeouts still produce complete work

The 1800 s wall clock usually expires during the final SUMMARY generation,
not the implementation. API calls completed = work happened. Check the
subagent's api_calls count in the completion notice: high counts (20+) with
a timeout almost always mean real output on disk.

## Concurrent sibling agents

When two leaves touch overlapping territory, later dispatches must be told:
"file X is being edited by another agent — confine your edits to functions
A/B/C." Proven safe: clinch + skill-bonus leaves both edited grapple_system.gd
concurrently with explicit confinement instructions; changes composed cleanly
and committed together.

## 2026-08-24 sandbox branch 03–04 data (4 more dispatches)

- **Salvage rate held**: 2 of 2 "failed/no-summary" dispatches had landed
  substantial work (neck_approach scene + scripts; south_end_stub scene +
  POI controller). In both cases the parent wrote the missing test file
  itself (~15 min), aligned it to ACTUAL node names/flag constants in the
  landed code, and committed. Re-dispatch would have cost an hour+ and
  risked conflicting with landed files.
- **Parent-authored tests must match landed reality, not the brief.** The
  brief says "Road"/"Marsh"; the agent built "RoadDirt"/"MudBand". The
  brief says "set flag X"; the code sets flag Y with a better name.
  Review-fix direction: fix the TEST to assert real behavior — unless the
  code's behavior is genuinely wrong (then note why in the commit).
- **Honest-behavior alignment beats forcing green**: the street-seller POI
  deliberately stays OPEN when the player has no inventory ("bring me a
  trinket") instead of setting its flag. First test draft asserted the
  flag; correct fix was asserting the OPEN state — degraded-but-real
  semantics beat fake success flags (AGENTS.md §12).
- **Pre-commit gates catch leaf leftovers**: the material-audit gate
  blocked a scene with duplicate inline materials; `audit_materials.py fix`
  extracted shared .tres — but VERIFY its output parses (it once wrote
  properties before the `[resource]` header). Also delete the .bak files
  it leaves before committing.
- **Watch for sibling-session commits mid-tree**: exterior_street.tscn was
  deleted by another session while our Director pointed at it; the
  HANDOFF retarget got folded into the next leaf's scope rather than a
  panicked hotfix. Check `git log --oneline -5` before committing to see
  what else moved underneath you.

## Heavy pre-commit gates (meept containment/loop-economics trees, 2026-08-24)

Repos whose hook runs 8-11 checks (mutexio, U1000/staticcheck, setter
nil-safety, bodyclose, gosec, error-pattern, feature-docs) make every leaf
commit a gauntlet:

1. **Long-timeout every commit**: `timeout 170 git commit -q -m ... >
   /tmp/c.txt 2>&1`. The suite exceeds the 60s terminal default; exit 124 =
   killed with nothing landed. Read /tmp/c.txt for the blocking check.
2. **Group staged paths per leaf** from `git status --porcelain`; parallel
   leaves interleave edits in one tree. Never `git add -A`.
3. **SA1029 (string ctx key) — fixes that do NOT pass**: `any("key")` cast,
   type alias, nolint at the test call site. staticcheck resolves aliases and
   checks staged packages wholesale. Passing fix: dedicated key type +
   helper in the PRODUCTION package, production readers migrated in the same
   commit; then avoid a leftover typed-but-unused var (trips U1000).
4. **U1000 on dead helpers**: delete them; suppression still trips.
5. **Analyzer failures may be compile errors underneath** (sibling-leaf
   signature drift, pointer/value mismatch). Fix arity first; analyzers pass.
6. **New Go package ⇒ feature-docs gate demands docs/workflows/<pkg>.md**
   and blocks interactively. Author it before the first commit touching that
   package.
