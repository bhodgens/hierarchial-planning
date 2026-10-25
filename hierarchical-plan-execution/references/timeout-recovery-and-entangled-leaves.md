# Timeout recovery + entangled-leaf commits (2026-08-23, plans-combat-audit)

Worked instance backing the SKILL.md rule: 18-leaf combat remediation tree,
6 branches, parallel subagent dispatch with in-session parent review.

## Timeout ≠ lost work

3 of ~8 dispatched leaves returned `status=timeout` or `status=failed`
("subagent did not produce a response") — but in EVERY case the subagent had
fully landed working code + passing tests in the working tree before dying
(often while running final verification passes).

**Protocol before ANY re-dispatch of a timed-out leaf:**
1. `git status --short` — check what landed.
2. Run the LEAF'S OWN verification command (the headless test invocation from
   its dispatch brief).
3. Green → review in-session against contracts, then commit. Done.
4. Red but close (e.g. 13/15) → dispatch a SMALL fix-only subagent scoped to
   the specific failures, not a full re-implementation.
5. Nothing landed → re-dispatch.

A blind re-dispatch risks corrupting finished work and burns the entire leaf
budget again (~30 min each).

## Entangled leaves commit together

Two leaves editing the SAME file (here: clinch state + skill-bonus checks both
in grapple_system.gd) cannot be committed separately without file-section
surgery. Protocol:
- Let both land; run BOTH leaf test suites.
- Commit in one commit citing both leaf IDs
  (`feat(combat): clinch state + techniques; skill bonuses consumed [...03-04 + 05 leaf 05-01]`).
- Dispatch briefs for concurrent same-file work must say which sections each
  agent owns ("do NOT touch the enum / state machine").

## GUT quirks that cost iterations this session

- `-gtest=res://tests/foo.gd` can silently skip the named script (runs other
  suites instead). Use `-gselect=foo` (substring match) and verify the
  "All tests passed!" tail line.
- `before_each()` containing ONLY comments is a GDScript parse error — add `pass`.
- `set()` works only on DECLARED properties: a bare `Node.new().set("_x", v)`
  stores nothing. Mock script state by instantiating the real controller class
  (`.new()` WITHOUT add_child when `_ready` needs scene siblings).
- Source-scan assertions must strip comment lines or the fix's own explanatory
  comment trips the assertion.
- Static funcs on Object scripts can't call get_node_or_null — resolve via
  `Engine.get_main_loop().root.get_node_or_null(...)`.
