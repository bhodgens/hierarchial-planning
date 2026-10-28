# Lleaf sizing and timeouts
When to use: sizing leaves against subagent timeouts.
Lesson: wall-clock budgets, split heuristics, timeout history.

# Leaf Sizing vs the Subagent Timeout (tree-30 lessons, 2026-08-23; tree-28 corroboration 2026-08-23; meept tier-3 tree 2026-08-22)

> 2026-08-24 note: the wall-clock cap is GONE (`delegation.child_timeout_seconds=0` since 2026-08-23), so classic timeouts should no longer occur — but every salvage rule below still applies verbatim to `status=failed`, missing summaries, and silent long-runners, because the summarization/report step remains the fragile part of any dispatch. See "Orchestrator-side wait discipline" at the bottom for the no-cap era's real constraint: orchestrator budget, not child time.

Leaf dispatches have a hard subagent timeout (~30 min). During tree-30
execution (water/shores/swim, 8 leaves), leaves spanning TWO
languages/runtimes (Go + Godot in one dispatch) timed out 4 of 8 times;
single-runtime dispatches completed reliably. All were recovered with
zero lost work using the patterns below.

## Data

| Leaf | Dispatch shape | Outcome |
|---|---|---|
| 00 GDD text only | single | ✅ 4 min |
| 01 Go + Godot | monolithic | ❌ timeout, ZERO artifacts |
| 01 retry | Go ∥ Godot split | ✅ both halves ~10-25 min |
| 02 Go + Godot | monolithic | ❌ timeout, zero artifacts |
| 02 retry | Go ∥ Godot split | ✅ |
| 03 shader + driver (one runtime) | single | ✅ |
| 04 tide clock (one runtime) | single | ✅ |
| 05 cycle + builder + controller + mat | single | ❌ timeout, PARTIAL artifacts (builder/tuning/material good; cycle/controller/tests missing) |
| 06 ripples + controller + interaction | single | ❌ timeout, zero artifacts |
| 07 showcase + cycle + tests | single | ❌ timeout, partial artifacts |

## Rules

1. **Split dual-runtime leaves into parallel dispatches.** One agent per
   runtime (Go half / Godot half), each forbidden from touching the
   other's files. Pin the SHARED SCHEMA (JSON field names, types,
   defaults) verbatim in both briefs so the halves meet without talking.
   The leaf-01/02 splits each finished faster than the monolithic
   dispatch burned before dying.

2. **Pre-read integration points yourself before dispatching.** Put the
   exact struct names/fields/JSON shapes in the brief (e.g.
   "GeographySpec has CharlesRiver Box2 at stage0_geography.go:60").
   A monolithic dual leaf usually spends its entire budget discovering
   what a 2-minute parent grep can pin in the brief. This also prevents
   the "zero artifacts" death: exploration-first agents that never
   switch to writing.

3. **Zero-artifact timeout = re-dispatch SPLIT; partial artifacts =
   finish in-session.** Check `git status` for the dead agent's files:
   - Nothing on disk → the brief was too big or too exploratory; split
     by runtime and re-dispatch.
   - Working half on disk → keep it, write the missing pieces yourself
     (leaf spec + conversation context make the orchestrator the
     fastest finisher), run the tests, commit.

4. **Shared-file parallel leaves are safe when regions are disjoint.**
   Leaves 05 and 06 both edited player_controller.gd concurrently
   (surface-ice group match vs wade-tier state machine). It worked with
   explicit instructions in BOTH briefs: name the other agent, name
   your region, "re-read before patch, patch surgically".

5. **Never re-dispatch the same monolithic brief that timed out.**
   Same mechanism twice violates the retry rule — split instead.

5a. **Tests-only partial artifact is its own salvage state.** Containment
   tree leaf 07 (2026-08-25): a subagent died at the 100 api_calls cap
   with TDD tests fully on disk but the implementation missing (`go vet`:
   `undefined: WithChangesAPI`). The tests already pin the contract, so
   salvage = implement the missing symbols in-session against the on-disk
   tests — vet/test errors name exactly what is missing. Never re-dispatch
   a tests-only leaf; the second agent will fight the first's files.

5b. **`status=timeout` with NO summary ≠ failed leaf — check `git diff`
   first.** Meept tier-3 tree (2026-08-22, 600s cap era): ALL THREE leaves
   reported timeout/no-summary; all three had complete, passing,
   review-ready work in the working tree. The cap kills the report step,
   not necessarily the implementation. Protocol: `git status --short` +
   build + test on the leaf's packages. Landed + green → review in-session
   and commit as normal (note "subagent timed out; work verified directly"
   in tracking). Partial → re-dispatch naming what already landed. Empty →
   genuine failure, re-dispatch per rule 3. Re-dispatching a landed leaf
   wastes a full run and risks conflicting duplicate edits.

6. **Tree-28 corroboration (single-runtime Go leaf, 2026-08-23):** a
   ~80-API-call venue-slots leaf (new package + resolver integration +
   save/load + GDD docs) still hit the 1800s cap with substantial
   uncommitted work on disk — partial-artifacts case, recovered by the
   parent finishing in-session (fixed 2 stale test calls, wrote the GDD
   section, committed). Sizing heuristic that held across both trees:
   a leaf budgeting >4 task groups (impl + tests + save/load + docs)
   is a >30-min leaf even in ONE runtime. Either split docs/tests into
   a parent follow-up or raise/remove `delegation.child_timeout_seconds`
   BEFORE dispatching (see below). Also: dispatch-time briefs should say
   "commit early per milestone" for big leaves — the dead agent's work
   was all uncommitted because it planned one final commit.

## The timeout itself is user-configurable (root cause)

The wall-clock cap is `delegation.child_timeout_seconds` in
`~/.hermes/config.yaml`. The framework default is **NO wall-clock cap**\n(0 / absent) — the delegate_tool docstring says failures should come\nfrom what the child is doing (API errors, iteration budget), not a\ngeneric stopwatch; stuck-child protection is heartbeat-based.

**Status (2026-08-23): set to 0 at the user's request after the tree-30\ntimeouts were root-caused to this key.** Don't assume — verify:

    grep child_timeout_seconds ~/.hermes/config.yaml

- If capped and a tree plans leaves near the cap: recommend `hermes
  config set delegation.child_timeout_seconds 0` (or 3600 as a
  compromise) BEFORE dispatching, or apply the split rules above.

## Post-tree-30 completion note (2026-08-23)

Tree 30 finished COMPLETE with the split+salvage protocol despite 4 of 8
leaf dispatches timing out — ~5,000 lines of new tested code (7 new GUT
suites, 83 water tests + Go procgen shelf tests). Two follow-on bugs
surfaced AFTER commit, both caused by leaf-07's showcase wiring, both
found by user playtest + headless boot:

1. A `groups=` + `instance=` .tscn header edit broke the whole chunk
   scene → empty world + endless player fall. **Rule: after ANY .tscn
   edit, headless-boot and grep `Parse Error|load failed` BEFORE
   handing to the user** (full detail: godot-game-development skill →
   references/godot-water-systems.md + godot-subagent-dispatch-sizing.md).
2. A legacy hand-placed water plane joined surface_water → rides the
   tide as a floating pane over the city (see godot-water-systems.md
   "Legacy hand-placed water plane vs the tide system").

Lesson: the leaf that wires a system into EXISTING hand-authored scenes
carries regression risk the leaf's own tests don't see — integration
leaves need a boot-verification step (headless run, parse/load grep,
and a runtime probe of the wired nodes' positions/groups) as an
explicit deliverable, not just suite-green.

## Brief template for a split dual-runtime leaf

Parent provides each half:
- The other half's file list (do-not-touch list).
- The exact shared record shape (field names, JSON tags, defaults,
  coordinate conventions — e.g. "polygon 'y' is the 3D Z axis").
- Tight reading budget ("max 10 min reading, then WRITE").
- The verify commands for ITS runtime only (the other half's suites are
  not its problem).
- "DO NOT commit. Report files changed + verbatim test counts."

## Salvage recipe for a timed-out leaf (concrete, tree-28 leaf-02 case)

When a leaf dies at the cap with substantial uncommitted work, the parent
finishes it in ~4 tool calls — do not re-dispatch:

1. `git status --short` + `go build ./...` on the leaf's packages →
   inventory what landed.
2. Run the package tests; expect exactly two failure classes:
   (a) **stale test calls** the dead agent didn't update after changing a
   function signature mid-flight (e.g. `buildNPCStates(...5 args)` vs new
   6-arg shape) — fix by reading the production signature and adding the
   missing arg;
   (b) **test expectations that contradict the implementation's actual
   contract** (e.g. round-trip test asserting empty venues are omitted
   while JSON `omitempty` only drops nil/whole-empty fields) — decide
   which side is RIGHT, fix that side, and write a comment explaining the
   contract so the next reader doesn't "fix" it back.
3. Sweep for pre-commit-gate blockers the agent never saw (U1000 unused
   functions from abandoned refactor paths — delete them).
4. Write the missing docs/changelog/leaf-status rows yourself, commit with
   explicit paths.

Total parent cost: well under one re-dispatch, and no risk of a second
agent conflicting with the first one's uncommitted files.

## Plans-combat-audit + plans-sandbox corroboration (2026-08-23, 24 leaves)

The 18-leaf combat tree plus the first sandbox branch ran ~24 subagent
dispatches in one session. New data points on top of the rules above:

1. **`status=failed` / "no summary" / 503-during-summarization ≠ failed
   leaf — same protocol as rule 5b.** Three dispatches reported failure
   or timeout with NO summary; all three had complete, passing work on
   disk (one 15/15 clinch fixer, one 13/13 quest suite, one morale
   model). The summarization call is the fragile step; inventory `git
   status` + run tests before treating it as lost. A "failed" report
   that lands full-quality work costs the parent only a review pass.
2. **Concurrent leaves sharing one file: sequence the COMMITS, not the
   dispatches.** Two agents interleaved edits into grapple_system.gd
   (clinch state vs skill-bonus checks) and intro_director.gd (state
   machine vs a sibling's handler fix). Clean outcome required: (a)
   briefs that name the sibling and fence each agent's region, (b) the
   parent holding BOTH works until the later one finishes, then one
   combined commit tagging both leaves, (c) running the full shared-file
   suite after the last writer landed.
3. **Async-func leaves need an await-discipline line in every brief.**
   The most expensive sandbox bug was `wrapper(): inner()` missing its
   own `await` — callers observed only the intermediate state
   ("stuck at PORTAL_TRANSIT"). Add to briefs touching coroutines:
   "every delegation hop through an async func must be awaited."
4. **GUT headless physics pairs don't resolve under Rapier** — put this
   in any brief whose scene relies on Area3D triggers: test handlers
   directly, leave overlap wiring to the windowed gate (full detail:
   godot-game-development → references/godot-headless-import-and-gut-pitfalls.md #10).
5. **A subagent that hits its iteration cap mid-fix often leaves the
   suite at 13/16 or similar with a precise diagnosis in no summary.**
   The finishing pattern that worked three times: read the failing
   asserts, run the suite once, apply the smallest fixes (usually 1-2
   arity/await/compat issues), re-run. Parent finish cost: 3-6 tool
   calls vs 20-60 for re-dispatch.

## Meept containment tree: pre-commit gauntlets + shared-tree dispatches (2026-08-24)

Repos with aggressive pre-commit hooks (meept's 11-check gate) turn "review passed" into extra orchestrator work. Patterns that cleared it:

1. **Feature-docs gates block after green review.** Repos requiring docs/workflows/<pkg>.md for every new Go package reject the commit even when code+tests are perfect. When authoring leaves that create new packages, add an explicit final task: "write ~15-line docs/workflows/<pkg>.md stub (purpose/how-it-works/config/edge-cases)". Recovery at commit time: write the stub yourself (~2 min) — never --no-verify.
2. **SA1029 string context keys resist every workaround.** staticcheck rejects WithValue(ctx, "k", v) via aliases, any() casts, AND nolint-on-line. Only reliable fix: dedicated key type + ContextWithX() helper in a small file, and migrate the production ctx.Value READERS in the same change — updating tests only leaves the typed key silently mismatched with the legacy string lookup.
3. **U1000 leftovers from iteration-capped subagents**: abandoned test helpers (unused funcs/vars). Delete; don't nolint dead test code.
4. **Signature ripples cross parallel-leaf boundaries.** Leaf 01 changed NewLocalBackend()'s signature; sibling leaf tests in the same package broke even though each leaf's own suite was green. Rule: a signature-changing leaf's scope INCLUDES updating all existing callers/tests; orchestrator re-runs the shared package suite after the last writer lands.
5. **Interleaved file ownership across parallel leaves is tolerable.** Leaves 01 and 02 both legitimately touched runtime config wiring; forcing artificial separation cost more than it bought. Committed as one feat commit naming both leaves; tracking table records the pairing. (Extends rule "sequence the commits, not the dispatches" below.)
6. **Provider-503 "failed" statuses are rule-5b again, third consecutive tree.** Two of three dispatched containment-A leaves returned status=failed with empty summaries (Console Go upstream 503 during the report step); both had complete, passing work on disk and were reviewed + committed normally.
7. **Conflict-recon the leaf's CLAIMED resources before dispatch.** Leaf 07 assigned Ctrl+D to open a pending-changes modal; the TUI already binds ctrl+d to double-press-exit (app.go:770). Grep the repo for any keybinding/port/bus-topic/config-key/file another feature owns and pin an alternative in the brief (or instruct the leaf to detect and rebind). Cheaper than discovering the collision at review. Same check for Flutter route/tab names and HTTP path prefixes.
8. **User "status" during a running fan-out = answer from disk.** `git log` + `git status --porcelain` + targeted greps for the in-flight leaf's artifacts, then report. Never poll the delegation or sleep-loop — the completion message re-enters on its own (extends wait-discipline rule 1). State explicitly what is done vs in-flight vs blocked.
9. **`_ = ` blocks commits regardless of nolint** (hook greps raw text). Hit 4× in one session on meept. Pre-scan BEFORE attempting the commit: `git diff --cached -U0 | grep '^+' | grep -F '_ = '`. Fix: bare call (`db.Close()`) or handle the error with a debug log. Test files are exempt. Also: every `http.Client.Get/Do/Post` needs `resp.Body.Close()` (bodyclose hook) — in test loops, close inside the loop body.
10. **Flaky full-suite failure ≠ real bug — confirm with -count=2 first.** A test failed once in the full package run, passed isolated AND on `-count=2`. Likely cross-test pollution. Verify determinism before diagnosing or blocking a commit; only chase failures that reproduce twice.

## Orchestrator-side wait discipline (meept theming tree, 2026-08-24; reinforced 2026-08-25)

With no wall-clock cap (child_timeout_seconds=0), leaves legitimately run
20-40+ min. The orchestrator's own budget becomes the scarce resource:

1. **NEVER sleep-poll for subagent completion.** A meept session burned
   ~12 orchestrator iterations on `sleep 120-300` loops while waiting —
   the completion notification re-enters the conversation on its own;
   every poll was wasted budget. Do recon/prep work between dispatches
   (there is always wave-2 pre-reading to do), then STOP issuing calls.
2. **Don't infer "done" from process tables.** `ps aux | grep flutter`
   shows idle language servers after agents exit; `git status` + build +
   test on the leaf's packages is the only reliable landed-state check.
3. **Verify from disk when summaries are missing** — see rule 5b and the
   timeout-salvage reference; that protocol applies to silent long-runners
   too, not just reported timeouts.
4. **Distinguish "waiting" from "stalled" with liveness probes** (meept
   unified-theming, 2026-08-25): two subagents went silent at ~5–10% scope
   for 4+ hours while the orchestrator kept waiting on the user's say-so.
   Each wait cycle should check target-file mtimes (`stat --format "%y %n"`
   — many files sharing ONE identical timestamp = a bulk revert, not
   incremental work), expected-output `ls`, and marker greps. Two
   zero-movement checks in a row = stalled: surface the evidence, take over,
   or re-dispatch smaller (see references/subagent-stall-recovery.md).
   The user's "give them time" is permission to keep WAITING only when you
   have shown progress is still happening.

## When the orchestrator should NOT delegate at all

Small foundation modules (<150 lines, pure static funcs, one test file)
are faster authored in-session than dispatched — the dispatch overhead
(context build + review cycle) exceeds implementation time. This session:
CombatInput (~50 lines), HitApplication skeleton, the CRT overlay fix,
and quest-persistence salvage were all cheaper in-session. Delegate when
exploration is heavy or files are many; implement directly when the shape
is already fully known.

Docs/README feature-state sync passes ("update documentation to match
implemented features") are another in-session class — the work is claim-by-
claim grep verification plus targeted edits; see
`references/docs-feature-state-sync.md` for the verification method and the
recurring staleness classes (counts drift, "planned" integrations already
shipped, removed CLI still documented, config-format-first wrong).

Additional 2026-08-23 sandbox-branch data points:

7. **`wait_until` state-polling under GUT hangs suites** — async chains
   should be tested with direct coroutine awaits
   (`await director.on_portal_touched()`); see
   hierarchical-plan-execution → references/godot-headless-physics-and-gut-async.md.
8. **Signal-param reads after an await that freed the emitter race GUT's
   autofree.** Capture via lambda collectors connected BEFORE awaiting.
9. **A missing `await` on a delegated coroutine is the classic silent
   bug**: `wrapper(): inner()` returns at inner's first await point;
   callers see only intermediate state ("stuck at PORTAL_TRANSIT").
   Every brief touching async funcs gets: "every delegation hop through
   an async func must be awaited."
## Audit-baseline rule: verify subagent doc-claims against source (2026-08-24 parity-audit wave)

When plan-tree leaves are authored from AUDIT findings, spot-check each
"meept lacks X / meept leaks Y" claim against source before dispatching. In
the containment tree, four audit claims needed correction at leaf-authoring
time once greps were run:

- "no sandboxing" → `internal/runtime` had a local+docker ExecutionBackend
  abstraction; the real gap was opt-in default + degrade-on-failure posture.
- "hands API keys to children" → provider keys were fine (`api_key_env`);
  the actual leak was `os.Environ()` seeding in local.go buildEnv.
- "no diff-preview approvals" → PendingChangesRegistry + resolve tool
  existed; real gaps were WriteFile coverage and user-facing surfaces.

Wrong premises produce leaves that re-implement existing subsystems or fix
non-bugs; two greps per claim are cheaper than one wrong leaf. The corrected
premises were also what made the user's pushback ("I thought we implemented
more mature sandbox") resolvable in one turn instead of a re-audit.

10. **Timeout-salvage detail moved to** `references/timeout-salvage-and-finishers.md`
    (salvage procedure + finisher-dispatch pattern; supersedes rule 5b's
    short version with the full protocol proven across ~6 timeouts).

## Silent stalls & small-subset dispatching (meept unified-theming, 2026-08-25)

Two wave subagents (a 17-file mechanical migration and a settings-panel
widget-test leaf) went silent after landing 5–10% of scope — no completion
report, no live process, 4+ hours — while the orchestrator sleep-polled.
Full protocol: `references/subagent-stall-recovery.md`. Key rules:

1. **Liveness probes, not blind sleep-polls**: check target-file mtimes
   (`stat --format "%y %n"` — many files sharing ONE identical timestamp =
   a bulk revert, not work), expected-output `ls`, and marker greps each
   wait cycle. Two zero-movement checks in a row = stalled; say so and
   take over or re-dispatch smaller.
2. **Split mechanical multi-file migrations into disjoint small leaves**
   (2–4 files / ~50–100 swaps each), Wave-0-commit the shared bridge/map
   first, and name each leaf's file list verbatim plus its siblings'
   ownership. Four small leaves finished in 6–22 min where the monolithic
   one stalled for hours.
3. **Scripted regex sweeps beat re-dispatch** when a stall/revert destroys
   mechanical-swap work — deterministic, minutes, uses the committed map.
4. **First widget tests over a complex form surface latent production bugs**
   (int initialValue into String? field → type-cast throw on every build;
   duplicate FormBuilder field name → dispose-time assert). Budget a fix
   loop; they're real bugs, not test errors.

## Leaf-implementer discipline on shared files (meept leaf-04, 2026-08-25)

When several leaves run concurrently in one repo (this session: three
sibling agents active), the implementer-side discipline that kept every edit
clean:

1. **Narrow anchored patches from a FRESH read, every time.** All edits to
   shared files (`components.go`, `daemon.go`, `rpc/server.go`) went through
   small unique-context patches; three sibling-collision warnings fired and
   every patch still landed correctly. Never whole-file rewrites of shared
   files.
2. **After any ambiguous patch outcome, re-grep before re-applying.** A patch
   reported "Found 3 matches" (failure) yet its region had already changed;
   a later `vet` reported a duplicate declaration that was already resolved
   by the time a grep ran. Stale compiler output + stale failure messages are
   both unreliable — fresh grep is ground truth.
3. **Verify your hunks survived via targeted diff reads** (`git diff -- <file>`
   scoped to your regions) rather than assuming tool success = landed bytes,
   especially when warnings fired.

## Godot scene leaves: test the SCENE, not just the script (sandbox tree, 2026-08-24)

Scene-building leaves (`.tscn` authored as text by subagents) need assertions
on the instantiated node graph, not just "scene loads":

1. **A PlayerSpawn marker is not a Player.** intro_apartment.tscn shipped with
   a spawn Marker3D but no `player.tscn` instance — user hit a grey screen.
   Assert the PLAYER INSTANCE exists (`get_node_or_null("Player")`), and for
   any gameplay-critical node type (player, camera, light rig), assert the
   actual class, not an anchor/marker that merely names it.
2. **Untextured placeholder geometry reads as a white void in playtest** even
   when tests green. If a leaf ships placeholder boxes, note explicitly in the
   completion report "visuals are placeholders — art pass deferred" so the
   user's first look isn't a surprise. Better: apply existing shared materials
   (`assets/materials/mat_*.tres`) even to placeholders — cheap, huge legibility.
3. **`load_steps` count in the .tscn header must match the resource count.**
   Subagents adding ext_resources without bumping the count produce scenes
   that fail to load with a confusing parse error. Grep-and-fix at review:
   compare header number vs actual `[ext_resource` + `[sub_resource` lines.
4. **QuadMesh/PlaneMesh size needs 3 components** (`Vector3(w, h, d)` — a
   2-component Vector2 silently fails parse: "Expected 3 arguments").
5. **Autoload migration breaks `/root/<Name>` lookups.** Moving a manager into
   project.godot autoloads re-parents its children: every
   `get_node_or_null("/root/X")` for a system now living under
   `/root/ManagerName/X` silently returns null. Sweep ALL such lookups repo-wide
   when changing registration (hit twice: game_manager systems + IntroDirector).
6. **Boot-state machines own the paused flag.** If PauseController boots the
   game paused in MAIN_MENU, any menu action must explicitly dismiss that state
   (`_dismiss_main_menu()`) before starting gameplay flows — hiding the menu
   Control alone leaves the tree frozen and "nothing happens" on click.
   Test suites that bypass the boot state machine mask this; one live-path
   regression test through the real state chain is worth it.
