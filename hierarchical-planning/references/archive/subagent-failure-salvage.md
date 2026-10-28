# Orchestrator Salvage Playbook — Failed/Timeout Subagents (2026-08-25)


When to use: a leaf reports failed/timeout/no summary.
Lesson: salvage decision tree: a third of failed subagents landed usable work.
Written from plans-combat-audit + plans-sandbox execution: 18-leaf and 9-leaf
trees run largely via background leaf dispatch. Roughly a third of "failed"
subagents had actually landed usable work; the failure was in their final
summary call, not the work.

## Decision tree when a leaf reports failed / timeout / no summary

1. `git status --short` — look for the leaf's expected untracked files.
2. Run its named GUT suite: `-gselect=<test_name>` (with `-gconfig=` to skip
   config-dir merge if defined).
3. Green or near-green → fix small defects in-session (typical classes below),
   commit as parent reviewer. Do NOT re-dispatch what already exists.
4. Files absent but partial edits visible in tracked files → assess whether
   finishing in-session is cheaper than a fresh dispatch (usually yes for
   <50% remaining; re-dispatch with "work exists, continue" context otherwise).

## Parent-review defect classes seen repeatedly (fix in minutes each)

- **Node-name mismatches**: test asserts names from the task brief ("Road",
  "Marsh") that differ from the landed .tscn ("RoadDirt"/"RoadCobble",
  "MudBand"). Fix the TEST after grepping real node names.
- **Getter/var name collisions**: `var x` + `func x()` is a parse error that
  nukes every suite preloading the script ("Could not resolve script"
  cascades). Rename getter `get_x()`.
- **Two-stage creation APIs driven only through stage 1**:
  `begin_stage_1` without `begin_stage_2` leaves `has_identity()` false;
  persistence asserts fail downstream.
- **watch_signals AFTER the emit** resets history — move it before the action,
  or capture via lambda-connected array.
- **Lazy first-frame wiring raced by immediate test calls**: insert one
  `await get_tree().process_frame` before driving the flow, or call an
  explicit `_wire()`.
- **Frame-stepped timeout logic flaky headless**: call the tick function
  directly with delta instead of awaiting frames.
- **Signal arity vs bound args**: `done.connect(h.bind(o))` means handler
  takes (signal_args..., o) — mismatch errors at emit time only.
- **Missing await on delegated async funcs**: caller observes intermediate
  state exactly (e.g. PORTAL_TRANSIT never reaching ROOFTOP).

## Entangled parallel leaves

When two leaves edit one file concurrently (clinch state + skill bonuses in
grapple_system.gd), commit them TOGETHER once both suites are green rather
than trying to split hunks — splitting risks shipping a broken intermediate.

## Status=completed still requires verification

Run the named suite + regression greps yourself before every commit. Two
observed cases: a completed report whose tests didn't all pass at commit time
(11/15), and a completed report whose "fixed" files contained a latent parse
error found only by running the sibling suite.

## Commit hygiene

- Explicit paths only (repo rule); siblings share the tree.
- One concern per commit; salvage commits name the leaf they close so the
  tree's tracking tables can be updated honestly.
