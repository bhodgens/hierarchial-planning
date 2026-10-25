# Subagent Dispatch Sizing & Shared Files

Hard-won from executing tree 30 (water/shores/swim, 8 leaves) in the
rebellion-the-game repo: 4 of 7 implementation-leaf dispatches timed out
at the 1800 s subagent cap. The pattern that fixed all of them.

## The 30-minute cap failure mode

A leaf that spans BOTH sides of a cross-language boundary — e.g. a Go
procgen stage that emits a JSON schema PLUS the Godot builder that
consumes it PLUS wiring PLUS tests on both sides — reliably blows the
cap mid-leaf. Worse: the timed-out agent usually leaves NOTHING on disk
(it spent the whole budget reading; `git status` shows zero of its
target files). Retry-same-shape also fails; the shape is the problem.

## The fix: split halves with a pinned contract

1. **One dispatch per side** (Go half ∥ Godot half), running in parallel.
2. **Pin the shared contract in BOTH contexts, in full**: struct fields,
   JSON tags, types, units, and axis mapping (e.g. "the JSON `y` in a
   polygon point is the 3D Z axis"). With the schema pinned, neither
   half needs to wait for or read the other, and they meet byte-exact
   at the JSON boundary.
3. **Cap reading in the context**: "max 8–10 min reading, then WRITE".
   Leaf agents over-explore otherwise — this one line rescued two leaves.
4. Name the exact files each half may touch and the files FORBIDDEN
   (the other half's + parallel siblings').

## Timeout triage

| Timed-out leaf state | Action |
|---|---|
| Zero artifacts on disk (`git status` clean of its files) | Re-dispatch SPLIT. Do not retry the same shape. |
| Partial artifacts (some target files present) | Keep the good half; finish the remainder in-session. The orchestrator's context on "what's missing" is fresher than a re-dispatch can be. Read the surviving files first, verify with the leaf's own test commands, then write the missing pieces. |

Single-side leaves (one language, one subsystem, ≤4 files) fit the cap
fine — no split needed. Leaf 00 (docs-only, 4 files) and leaf 03
(shader + driver + tests) completed in 6–20 min.

**Tree-28 counter-example (2026-08-23):** "single-side fits the cap" has
a size limit, not just a runtime limit. A single-runtime Go leaf
(new package + resolver integration + save/load + unit tests + GDD
section + changelog ≈ 80 API calls) timed out at 1800 s with partial
artifacts — recovered in-session per the triage table. Count task GROUPS,
not languages: >4 groups (impl/tests/persistence/docs) = oversize even
in one runtime. For such leaves either pre-commit per milestone
("commit after impl+tests green, before docs") so a timeout leaves
committed work, or carve the docs half off for the orchestrator.

## Salvage pattern for a timed-out leaf with partial artifacts (tree-28, 2026-08-23)

The dead agent left: new package + tests green, but a stale call in an
existing test file (`buildNPCStates` gained an arg), one test asserting
behavior the impl doesn't have (JSON `omitempty` does NOT drop an
explicitly-written empty slice from a map — the test's "empty venues are
omitted" expectation was wrong, not the code), and zero docs. Recovery
sequence that worked:

1. `go build ./...` first — if it builds, run only the touched packages.
2. Fix compile-level test rot mechanically (add the missing arg).
3. For a failing assertion, check whether CODE or TEST is wrong before
   editing either — here the Go JSON contract proved the test wrong;
   rewrote the test to pin actual behavior with a comment explaining why.
4. Grep for the leaf's unfinished deliverables (GDD section present?
   changelog row? leaf status flipped?) and do them yourself — Rule 1/3
   obligations don't lapse because a subagent died.

**Salvage gotcha — pre-commit U1000 gate on dead code:** the timed-out
agent had left an unused wrapper func (`resolveLocationToken`) that its
own integration superseded. The repo's commit hook blocked on U1000 with
no fix guidance; resolution was to delete the orphaned wrapper (its body
was a 1-line delegation to the real function) rather than nolint it —
dead wrappers from a half-finished refactor should be removed, not
suppressed.

**Docs-completion checklist for salvaged leaves** (what the parent must
author when the subagent dies pre-docs): GDD subsection matching the
landed code's actual behavior (not the spec's aspiration), changelog row
(re-read tail first — parallel leaves append concurrently), leaf-file
status flip NOT_STARTED→DONE, and build-plan-index status update only
when ALL tree leaves are done.

## Shared-file parallel dispatch

Two leaf agents CAN concurrently edit the same file when their regions
are provably disjoint. Real case: `player_controller.gd` — leaf 05
owned the surface-group modifier lines, leaf 06 owned the wade-tier
block ~300 lines away. In BOTH dispatch contexts:

- name the other agent and its exact region ("leaf 05's surface_ice
  match in _get_movement_speed; leaf 06's wade block near _enter_water"),
- instruct: "re-read the file before patching; patch surgically".

This beat serializing the leaves and produced a clean merge — the
orchestrator commits each leaf separately afterward anyway.

## Commit choreography around parallel leaves

- Commit a leaf ONLY when its full contract is verified (both halves
  green + regressions). Holding one leaf's commit while a sibling that
  touches the same regression suite is still in flight is fine — verify
  the held leaf's own suite, wait, then commit.
- If a pre-commit gate fails mid-orchestration (e.g. attribution
  registry rejects an "adapted" shader), the FIX may pull in files from
  a DIFFERENT leaf's staged set — check `git show --stat` after the
  commit and amend the message if two leaves landed in one commit.

## Pre-commit attribution gate gotcha (Godot projects)

Upgrading a shader from "original" to "adapted" (even for borrowed fbm
octave weights) flips the attribution audit from pass to
UNREGISTERED/INCOMPLETE. The auto-fix (`audit_attribution.py fix` from
the REPO ROOT, not the script dir) writes a registry entry but leaves
`license_url` empty — the gate still fails. Fix the registry JSON
directly: full source URL, license name + URL, and a `changes` line.
Check where the pre-commit hook invokes the script from; running it from
the wrong cwd reports a bogus "shaders dir not found".

## 24-dispatch corroboration + new failure classes (2026-08-23, plans-combat-audit + plans-sandbox)

The combat tree (18 leaves) plus the first sandbox branch ran ~24 leaf
dispatches in one session with zero lost work. New failure classes and
their fixes, beyond tree-30's:

1. **"status=failed / no summary" usually means the SUMMARY died, not the
   work.** Three dispatches reported failure or summarization-503; all
   three had complete, passing implementations on disk. Always inventory
   `git status` + run the suite before re-dispatching — a failed-report
   salvage costs one review pass vs a full re-run.
2. **Concurrent leaves sharing one file: sequence the COMMITS, not the
   dispatches.** Two agent pairs interleaved edits in grapple_system.gd
   and intro_director.gd. Clean outcome recipe: fence each brief ("name
   the sibling + your exact region"), hold both until the later finishes,
   commit combined work tagging both leaves, run the shared suite after
   the last writer.
3. **Await discipline across delegation hops** (`wrapper(): inner()`
   without its own await → callers see only the intermediate state,
   e.g. beat stuck at PORTAL_TRANSIT never reaching ROOFTOP). Put an
   explicit "await every async hop" line in any brief touching
   coroutines.
4. **Rapier headless pairs don't process** (rebellion): Area3D overlap /
   body_entered never fire under GUT even for point-blank minimal pairs;
   `Engine.get_physics_frames()` ticking makes it LOOK like physics runs.
   Briefs for trigger-driven scenes should say: test handlers directly,
   leave overlap wiring to the windowed gate. Full probes:
   godot-game-development → references/godot-headless-import-and-gut-pitfalls.md #10.
5. **GUT `wait_until` polling can hang the whole suite** where a direct
   coroutine await completes deterministically — especially when the
   awaited state depends on a runtime-added node's `_process` (and note
   `CanvasLayer.new()` + `set_script()` nodes never get `_process`
   callbacks headless; construct via `OverlayScript.new()` instead).
6. **Signal handler arity counts bound args**, and freeing an emitter
   mid-emit errors at GUT teardown. Fixes: two-arg handlers matching
   `(signal_arg, bound_arg)`; capture emitted params via lambda-connected
   arrays rather than post-await `get_signal_parameters()` reads.

Small foundation modules (<150 lines, pure static funcs, one test file)
are faster authored in-session than dispatched — dispatch overhead
exceeds implementation time when the shape is already fully known.

## Tree-28 five-leaf orchestration (2026-08-23) — docs-leaf concurrency + gate plumbing

1. **A docs-only leaf is the safe concurrent filler.** When the code
   leaves are chained by shared files (01→02 sequential), a documentation
   leaf (04: ownership contract, zero sidecar writes) can run alongside
   the first implementation leaf — fence it read-only on the code tree.
   It also front-loads an audit (BT/NPCState ownership trace) whose
   findings (engine combat targets never reported to sidecar → gh issue)
   would otherwise surface late.
2. **Fan-out point:** dispatch parallel leaves only after the LAST
   shared-file leaf lands. For 03+05 the fences were explicit package
   exclusions ("do NOT touch internal/events* or internal/smarte*") plus
   a scope carve-out ("event scenarios belong to leaf 03's smoke test —
   omit and note, don't duplicate").
3. **Reconciliation pattern for contracts written mid-flight:** a leaf 04
   contract documenting pre-01/02/03 reality should ship with a "pending
   reconciliation" subsection listing exactly what to re-check; the
   orchestrator appends a dated reconciliation record after the code
   leaves land. No invented semantics in either direction.
4. **Feature demo/gates need IPC plumbing that plan leaves skip.** Leaf
   03's SpawnSmartEvent had NO production caller — the engine couldn't
   spawn events over IPC at all. User-facing acceptance gates ("watch 10
   minutes of NPC daily life") require bridging wire envelopes to new
   subsystems + a debug overlay scene; budget this as real work (one
   commit: bridge + send_event() client method + Label3D-per-NPC overlay
   + hotkey triggers) rather than discovering it live at the gate.

**Input-key disambiguation bug found during gate work** (belongs in a
gameplay skill, recorded here because it surfaced via the gate):
context-shared keys (E = interact/lean/climb) must check INTERACTABLE
first — climb's "any vertical surface" fallback hijacks doors, lean's
side-ray hijacks doorframes into camera shifts. Fix shape:
`_interactable_in_reach()` (raycast hit has `interact()` method) wins
before climb/lean heuristics run.
