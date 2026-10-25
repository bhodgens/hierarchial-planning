# Attribution-Gate Commit Failures After Shader Edits (2026-08-22)

Session: rebellion-the-game tree 30 leaf 03/04 commits.

## The failure mode

A subagent upgrades a self-authored shader by adapting a *technique snippet*
from another project shader (here: fbm octave weights from
`sky3d_sky_material.gdshader`, TokisanGames/sky3d). The subagent correctly
updates the shader's ATTRIBUTION_HEADER to say "adapted from" — and the
repo's pre-commit attribution audit then HARD-FAILS the orchestrator's
commit with `UNREGISTERED: <shader> (adapted from: ...)`.

Worse failure: the failed commit can leave the NEXT leaf's files staged from
an earlier `git add`, so a subsequent `git commit` for leaf N silently
includes leaf N+1's files. Detection: `git show --stat HEAD` after every
commit in a multi-leaf session — if the file list exceeds what the message
describes, `git commit --amend` the message to credit both leaves (safe when
local + unpushed; never amend pushed commits).

## The fix sequence (works from repo root)

1. The audit script runs from the REPO ROOT with an explicit root argument —
   `python3 rebellion-godot/scripts/audit_attribution.py check .` — running
   it from inside rebellion-godot/ fails with "shaders dir not found".
   (The pre-commit hook invokes it correctly; manual invocation needs `.`.)
2. `python3 rebellion-godot/scripts/audit_attribution.py fix .` —
   auto-registers the shader from its header. Output: "wrote
   ./rebellion-godot/shaders/attribution.json" but STILL reports
   `INCOMPLETE: missing registry field 'license_url'`.
3. The auto-fix cannot invent URLs. Patch
   `rebellion-godot/shaders/attribution.json` by hand: registry entries are
   keyed by `"file"` (e.g. `"res://shaders/harbor_water.gdshader"`), NOT by
   `"name"`. Fill `license_url` + `source_url` (upstream repo LICENSE link)
   and clean up truncated `adapted_from` strings the header parse produced.
4. Re-run `check .` → `OK — all adapted shaders registered.`
5. Commit the shader + registry together in one leaf commit.

## Rule for dispatch briefs

Any brief that touches a `.gdshader` must say: "if you adapt ANY code from
another project shader (even a few lines of fbm weights), the attribution
registry entry must gain license_url/source_url — put the upstream LICENSE
URL in your summary so the orchestrator can complete registration." The
subagent cannot run the repo-root audit script reliably; the orchestrator
owns gate repair.

## Rule for multi-leaf commit trains

After every per-leaf commit: `git show --stat HEAD | tail` and compare the
file list against the leaf's Files-to-Touch. Any extra files from a FAILED
earlier commit attempt mean the staging area leaked — amend the message
(credit both leaves) rather than trying to split the commit; history purity
loses to correctness when both changes are verified green.
