# Checklist Additions - Merged from Session Pitfall Additions Tail (2026-10-26)

When to use: post-authoring review of any plan tree, alongside `references/authoring-checklist.md`.
Lesson: these checklist items were appended to SKILL.md's session diary over time; they are merged here (and into authoring-checklist.md) so the SKILL.md diary could be deleted.

## Structural (mirror of Step 6 - keep verified by the compliance scan, not by eye)

- [ ] Every branch has interface contracts between its children (even single-leaf trees - Pitfall 33)
- [ ] Architecture Overview present in all orchestrators (even single-leaf trees - Pitfall 33)
- [ ] Every leaf estimated at 110K context or less (with headroom)
- [ ] No leaf splits a cohesive unit across documents
- [ ] Every document has embedded dispatch/review instructions
- [ ] Dependency graph has no cycles
- [ ] Concurrent leaves identified and batched in groups of 3
- [ ] Tracking tables present in all orchestrator documents (exact heading `## Completion Tracking Table` - Pitfall 36)
- [ ] Integration review planned at each branch level and at root (exact heading `## Integration Test Plan` - Pitfall 34)
- [ ] All leaf tasks follow bite-sized TDD format with exact paths and complete code
- [ ] No leaf task includes commit steps (orchestrators only)
- [ ] All child documents referenced in Child Index exist on disk (`references/partial-plan-trees.md`)

## Dispatch hygiene

- [ ] Every dispatch instruction tells implementation agents "Do NOT commit"
- [ ] Dispatch contexts inline relevant source code (no "read the file" instructions that lead to line-number corruption - Pitfall 12)
- [ ] Orchestrator documents include a coding-conventions block for style consistency across leaves (Pitfall 14)
- [ ] Review checklist includes "no debug artifacts, no TODOs, no placeholder values" (Pitfall 15)
- [ ] Post-integration plan includes format normalization (gofmt/prettier/ruff) and the line-number corruption check

## GDScript / Godot specifics

- [ ] GDScript subagent dispatches: expect ~40% timeout rate on 300+ line leaves; check disk with `git status --short` + `ls -la` before re-dispatching; complete missing pieces directly if files landed. Verify with `grep -cE 'TODO|FIXME|pass\s*#'` and `grep -rcE '^\s+[0-9]+\|'` (corruption check). Legitimate `pass # comment` in match/case is NOT a stub. `godot --check-only` can verify parse errors but may time out on projects with heavy imports (60s+). Detail: `references/godot-execution-notes.md`, `references/gdscript-bulk-dispatch.md`.
- [ ] Godot FBX-to-.tres pipeline requires a Blender intermediate (FBX-to-GLB-to-.tres), not direct FBX-to-.tres; skipping `Godot --headless --import` silently produces zero output. Detail: `references/godot-fbx-pipeline.md`.
- [ ] After each subagent batch completes: run `git status --short`; for GDScript also `git diff --stat HEAD` (event_bus.gd signal additions) and `git ls-files --others --exclude-standard` (untracked test files). Pitfall 40; detail in `references/gdscript-bulk-dispatch.md`.

## Recovery variants (cross-references kept from the diary)

- Orchestrator implements a leaf directly (rate-limit recovery): do NOT assemble code via execute_code string concatenation - use `write_file` or real tab characters; f-string `\\t` produces literal backslash-t (Pitfall 29 variant).
- Visual/coordinate fixes: use Godot MCP or computer_use screenshots to verify - do NOT guess iteratively (Pitfall 42).
