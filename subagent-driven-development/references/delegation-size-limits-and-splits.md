# Delegation size limits, split dispatches, and salvage (2026-08-23, rebellion tree 30)

When to use: a dispatch nears the delegation time cap or spans two language trees.
Lesson: split into parallel single-half dispatches with the shared schema pinned in both briefs, and salvage timed-out partial work from disk before re-dispatching.

Session evidence for dispatch-shape rules that apply to ANY multi-language
plan-tree execution. Observed across 9 leaf dispatches in one session.

## The 30-minute subagent cap and dual-half leaves

Leaf dispatches that span BOTH the Go sidecar and the Godot project timed out
at the delegation cap (1800 s) with ZERO artifacts written - twice:

- Tree 30 leaf 01 (Go procgen stage + Godot builder): timeout, nothing on disk.
- Tree 30 leaf 02 (Go shelf samples + Godot ribbon builder): timeout, nothing on disk.

Both completed in 6-25 min after being split into two PARALLEL single-half
dispatches with the shared JSON schema pinned in both briefs.

Single-domain dispatches in the same session, same repo, same model:
- GDD docs leaf (4 files, text only): 4 min.
- Shader v2 + driver + tests (one shader, one .gd, one test file): 19.5 min.
- Tide clock + cycle integration + config + tests: 27.5 min.
- Winter ice leaf: timed out, but see salvage below.

Rule: a leaf touching more than one language tree MUST be split at authoring
or dispatch time. Pin the exact JSON record shape in BOTH briefs so the
halves meet without negotiation - e.g.:

    { "id": String, "kind": "harbor"|"river",
      "polygon": [{"x": float, "y": float}, ...],  # "y" = Z axis in 3D
      "level_m": float, "chop_m": float, "foam_width_m": float }

## Salvaging timed-out dispatches

On `status=timeout`, check `git status` BEFORE re-dispatching. Timed-out
agents often leave partial work. Tree 30 leaf 05 timed out but had already
written a correct builder extension (_add_ice_surface), a complete IceTuning
config block, and the mat_ice_river.tres material - only the cycle
integration, controller hook, and test suite were missing. Salvage + finish
in-session beat re-dispatching (which risks the replacement agent re-writing
or conflicting with the surviving partial work).

Zero-artifact timeouts (nothing on disk) = clean re-dispatch, but SPLIT first.

## Parallel-leaf file ownership

When dispatching leaves concurrently, every brief gets:
1. An OWNED-files list (only these may be edited).
2. A must-NOT-touch list (other agents' files + shared infra).
3. For shared files two leaves must both extend: state the disjoint edit
   regions and require "re-read before patching" in both briefs.

This session ran 3 concurrent leaf dispatches (02/03/04) and 2 more (05/06)
with zero collisions under this scheme. player_controller.gd was shared
between 05 and 06 (different regions: surface-group match vs wade-tier
block) - both landed cleanly.

## Commit hygiene under interleaved sibling work

- Explicit paths only on git add - sibling sessions leave unrelated modified
  files everywhere.
- A FAILED pre-commit gate stages the files it validated. The next git
  commit silently sweeps them into whatever commit runs next. After any
  failed commit: git diff --cached, then reset or amend the message to
  credit what actually landed (verify with git show --stat).
- Attribution/registry gates: run the audit script from the repo ROOT with
  the root as the argument (python3 rebellion-godot/scripts/audit_attribution.py fix .)
  - the script resolves paths relative to its arg, not its own location.
  fix auto-registers from shader headers but leaves required fields
  (license_url) blank - patch the JSON directly, re-run check until OK.
- Committing one leaf while another's suite would regress? Verify the
  sibling-owned file is untouched and run only the suites your leaf owns;
  defer shared-file regressions to the leaf that owns them.

## Orchestrator verification loop (per leaf)

1. Subagent reports: TRUST NOTHING - re-run the suites yourself.
2. Read the diff of files it edited (especially shared ones).
3. Check for cross-schema breakage the halves cannot see individually.
4. Commit per leaf with explicit paths; keep the leaf's test counts verbatim
   in the commit message (audit trail).

## Same-wave contract consumers (2026-09-09, uprisys site build)

Wave of 4 parallel leaves (index.html / style.css / sea.js / main.js, one repo).
The style.css leaf shipped while its contract did not exist: index.html was
written by a sibling in the same wave, so the CSS leaf GUESSED class names from
plan prose (`.nav-links`, `.logo-link`, `.site-footer`...) while the HTML used
different ones (`#navLinks`, `.brand`, `footer`). Spec-valid per its brief,
still wrong: cost a 40-selector reconciliation pass in review.

Rule: if two same-wave tasks reference each other's outputs BY NAME (CSS
selectors vs HTML classes, import paths vs file names, field names vs
payloads), the contract must exist on disk or be pinned verbatim in BOTH
briefs before the wave dispatches. Otherwise sequence the consumer into a
later wave, or write/commit the contract skeleton first.

## Brief-shape pitfalls (same session)

- Compact briefs only. One long brief degraded mid-generation and failed
  dispatch schema validation (`tasks` items arriving as strings, zero
  dispatched). Re-dispatch clean and shorter; never retry the corrupted text.
- Verification steps must be single simple commands. The operator denies
  compound commands (`a && b` chains): a leaf whose verify step was
  `python3 -m http.server -d site 8901 (background), curl ... , kill` got
  consent-blocked, halted WITHOUT committing, and had to report a partial.
  One command per check; optional checks should be skippable with parent
  verification in-session instead.
- Pin per-file `git add <path>` (never `-A`) plus index.lock retry guidance
  in every sibling brief sharing a repo.
