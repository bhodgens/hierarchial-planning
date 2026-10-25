# Subagent Dispatch Discipline — lessons from live tree execution (trees 29/30)

Orchestrator-side rules for dispatching implementation subagents against
plan-tree leaves. These came from real failures and successes in the
rebellion-the-game repo (Godot 4.7 + Go sidecar), 2026-08-22.

## 1. Pin context, not just goals

A leaf dispatch that says "inspect X first" invites a read-only stall. One
leaf agent burned its ENTIRE 1800 s timeout (37 API calls) reading the
codebase and wrote zero files. Every dispatch prompt must include:

- **Exact struct/record/JSON shapes copied INTO the prompt.** Both halves of
  a cross-language leaf must receive the same schema verbatim — keys, units,
  axis conventions (e.g. "polygon `y` = the 3D Z axis", "level_m default
  0.0"). Do not make agents reverse-engineer the contract.
- **A reading budget**: "10 min budget for reading, then WRITE."
- **DONE criteria as runnable commands**: grep markers, test commands with
  `-gselect=<suite>`, build commands. The agent reports their verbatim
  output.

Rule of thumb: if the orchestrator already knows the answer to an "inspect
this" instruction, paste the answer instead.

## 2. Split cross-language leaves per language

A leaf spanning Go + Godot timed out as a single dispatch. The split that
worked:

- **Go half**: work ONLY in `sidecar/`, contract pasted, testify suite.
- **Godot half**: work ONLY in `rebellion-godot/`, same contract pasted,
  GUT suite.
- Both dispatched **in parallel**, each explicitly forbidden from touching
  the other's directories.
- The orchestrator verifies both halves against each other (schema meeting
  point) before committing the leaf as one unit.

## 3. Carve file ownership for concurrent leaves

When sibling leaves run in parallel, list the files each agent owns inside
EVERY prompt: "PARALLEL AGENTS own <files>. DO NOT touch those." Include
this even when the leaves look disjoint — leaf 03 (shader) and leaf 04
(cycle) both wanted `harbor_water.gd`; ownership listing ran 3 concurrent
leaves with zero edit collisions.

## 4. Verify, never trust reports

Subagent summaries are self-reports. Before committing a leaf:

- Re-run the suites yourself (`go test ./internal/procgen/`, GUT
  `-gselect=<suite>.gd -gexit`, `--headless --import`).
- Read the full diff of every touched file — spot-check for stubs, TODOs,
  style drift, debug leftovers, and un-requested drive-by edits.
- Check `git status` for footprint: the agent should have touched ONLY its
  owned files.

## 5. Commit per leaf, explicit paths

Sibling sessions share the working tree. Stage only the leaf's files
(`git add <explicit paths>`), never `git add -A` or `.`. If a parallel leaf
is still editing a file your regression suite covers, verify what you can
and HOLD the commit until that leaf lands — ordering over blocking. Never
stash to isolate (shared tree; stash steals siblings' work).

## 6. Godot/GUT gotchas that recur in leaf work

- Typed `Array[float]`/`Array[int]` literals need explicit typed locals
  before assignment to exported properties.
- Runtime-added `CollisionShape3D` needs an explicit `name` — auto
  `@CollisionShape3D@` names break `get_node_or_null`.
- `await worldspec_loaded` + `add_child_autofree` needs one extra frame
  before teardown ("Object is locked").
- Full-suite headless Bus errors are usually pre-existing order-dependent
  flakes: reproduce on a clean baseline (or run per-suite) before chasing
  them; per-suite `-gselect` runs are the reliable signal.

## 7. Timeout triage

When a leaf dispatch times out: check `git status` FIRST. Zero artifacts =
the agent never got to writing → re-dispatch with the context pinned
(schema in prompt, reading budget) or split per language. Partial artifacts
= finish in-session rather than re-dispatching (the agent's context is
lost; yours isn't).
