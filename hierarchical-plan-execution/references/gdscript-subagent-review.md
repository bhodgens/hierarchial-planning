# GDScript Subagent Review Patterns

> Patterns for reviewing GDScript subagent output in hierarchical plan execution.

## godot --check-only Timeout

`godot --headless --path <project> --check-only` can time out (60s+) on
first run because Godot imports ALL project resources before checking
syntax. For per-leaf review, use grep-based checks instead:

```bash
# No TODO/FIXME/placeholders
grep -rnE 'TODO|FIXME|not_implemented|pass\s*#|return\s+""' --include='*.gd' <files>

# No line-number corruption (from read_file → write_file pipelines)
grep -rcE '^\s+[0-9]+\|' --include='*.gd' <files>

# Verify EventBus signals exist
grep -c 'signal_name' scripts/core/event_bus.gd
```

Run the full `--check-only` once at the end of each wave if time permits,
but don't block leaf-level review on it.

## class_name Rescan

Subagents that create new `.gd` files with `class_name Foo` produce files
that are invisible to other scripts until Godot rescans its global class
cache. Other subagents referencing `Foo` will report:
`Parse Error: Identifier "Foo" not declared in the current scope`

Fix: trigger the rescan from CLI:
```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --editor --quit --path rebellion-godot/
```

This boots the editor briefly, updates `global_script_class_cache.cfg`,
and exits. After that, cross-file class references resolve correctly.

## Wave-Level git status Sweep

After each wave of GDScript subagents completes, run:
```bash
git status --short rebellion-godot/
git diff --stat HEAD
git ls-files --others --exclude-standard rebellion-godot/
```

GDScript subagents commonly:
- Create `.gd.uid` files alongside new scripts (Godot UID tracking)
- Add signals to `event_bus.gd` without reporting it
- Create test files (`test_*.gd`) alongside implementations
- Modify `project.godot` to add input actions

Commit ALL files from each subagent's output before processing the next.

## Legitimate `pass` in Match Statements

GDScript `match` (switch) statements require a body for every branch.
Empty branches use `pass` — this is CORRECT, not a stub:

```gdscript
match _state:
    GrappleState.FREE:
        pass  # input-driven; detection happens in _unhandled_input
    GrappleState.TAKEDOWN_ANIM:
        pass  # resolves on animation completion (timer-free)
```

When reviewing, check whether the `pass` has a comment explaining WHY it's
empty. A bare `pass` with no comment may be a missing implementation.

## `return ""` as Fallback

A `return ""` at the end of a lookup function is a legitimate fallback for
unknown keys, NOT a placeholder:

```gdscript
static func get_cost(attack_type: String) -> float:
    if STRIKES.has(attack_type):
        return STRIKES[attack_type]["cost"]
    # ...
    return -1.0  # unknown attack type
```

Flag `return ""` only when it replaces a computation that should produce a
real value — not when it's the error/unknown path.

## Large-Scale Code Review: In-Session Scanning Beats Subagent Dispatch

When the user asks to "review all code for bugs" across a large codebase
(10K+ lines, 50+ files), do NOT dispatch parallel code-review subagents.
Each subagent reads many files and performs reasoning per file — with 10-23
files per agent, the agent exhausts its 600s timeout before finishing even
half its files. All 8 agents return zero useful output.

**Real failure (2026-08-07):** 8 parallel review agents for rebellion-the-game
(174 GDScript files, ~28K gameplay lines). Agents were scoped to 3-23 files
each. ALL 8 timed out at 600s. Two retries, same result. Zero bugs found,
zero fixes applied, 24 minutes of subagent compute wasted.

**Correct approach — automated scan + targeted read:**

1. Run a regex-based pattern scan via `execute_code` across all source files.
   This catches the common bug classes in seconds:
   - `:=` on Variant sources (get_node, .get(), JSON.parse)
   - `print()` in production code (vs tests/tools)
   - Missing return types on public functions
   - `get_node()` without null check
   - Format string arg-count mismatches (`%s` count vs `% [...]` arg count)
   - TODO/FIXME markers
   - `Engine.time_scale` set without restore
   - Signal `.connect()` without corresponding `.disconnect()`
   - Per-frame Array/Dictionary allocations in `_process`/`_physics_process`

2. For each scan hit, read the surrounding context (5-10 lines) to determine
   if it's a real bug or a false positive. Most pattern hits are false
   positives from multi-line function signatures, test files, or intentional
   patterns.

3. For logic-level review (state machine transitions, algorithm correctness,
   physics delta usage), read the specific hot-path functions directly —
   `_physics_process`, state machine handlers, IPC message parsers. These
   are typically 30-80 lines each and take seconds to review.

4. For performance assessment, check every `_process`/`_physics_process`
   function body size and look for per-frame allocations, unbounded pool
   growth, or O(n) loops over all entities. Most gameplay code is fine; the
   hot paths are perception systems, crowd physics, and VFX pool management.

This approach reviews 28K lines in ~3 minutes (scan + targeted reads) vs
24+ minutes of failed subagent dispatches that produce zero output.
