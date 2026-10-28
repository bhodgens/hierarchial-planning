# Godot/GDScript lessons condensed out of hierarchical-planning SKILL.md (2026-09-05 slimming pass)


When to use: Godot/GDScript execution detail backing the SKILL.md pitfalls.
Lesson: MCP plugin install, corruption greps, 40% timeout expectations for large GDScript leaves.
Full text of the entries slimmed in SKILL.md. SKILL.md keeps one-line
pointers; this file keeps the working detail.

## From Pitfall 42 — Godot MCP plugin install (kept detail)

If MCP servers aren't installed for visual verification, install the
Godot AI plugin: `hi-godot/godot-ai` on GitHub → copy `addons/godot_ai`
into the project → enable in Project Settings → Plugins. This gives
programmatic access to node properties, transforms, and screenshots.

User quote that settled the pattern: "would this be something that's done
easier visually in godot than having reiterative attempts to 'guess'
visual equivalence on your part?" — the answer is yes, always prefer
visual verification for spatial/visual fixes.

## From the Verification Checklist — GDScript corruption greps

- Stub check: `grep -cE 'TODO|FIXME|pass\s*#'` — but a legitimate
  `pass # comment` inside match/case is NOT a stub.
- Line-number corruption: `grep -rcE '^\s+[0-9]+\|'`.
- Parse check: `godot --check-only` — may time out on projects with heavy
  imports (60s+); not a reliable gate on large projects.

## GDScript subagent timeout expectations

Expect ~40% timeout rate on 300+ line leaves (GDScript files are large
and subagents spend many calls reading existing files). Check disk with
`git status --short` + `ls -la` before re-dispatching; complete missing
pieces directly if files landed.

## Godot FBX → .tres pipeline

Separate file: `references/godot-fbx-pipeline.md`.
