---
name: plan-tree-review
description: Review implementation plan trees for completion and correctness. Cross-references plan docs against GDD specs, checks implementation status, verifies tests, and updates tracking documents. Use when asked to "review plans", "audit plan tree", "verify completion", or "check plan drift".
tags: [documentation, planning, gdd, audit, consistency]
---

# Plan Tree Review

Use when asked to review, audit, or verify a plan tree for completion and correctness.

## Trigger Keywords

- "review plans" or "review plan tree"
- "audit plan" or "check plan"
- "review this project in entirety and fix any gaps/omissions/unwired code/stubs" on a docs-only tree — run the full audit→fix→verify pipeline in `references/docs-only-tree-audit-fix-pass.md`
- "verify completion" or "completion check"
- "plan drift" or "GDD drift"
- "STALE" — tree marked STALE because a GDD spec source changed; re-verify
  and close the loop (Phase 5 below)
- "is this plan done" or "what's still open"

## Workflow

### Phase 1: Gather Context (parallel reads)

1. Read the plan tree's `master.md` — understand stated scope and completion table
2. Read the GDD changelog (`docs/gdd/00-CHANGELOG.md`) — check for recent edits to the plan's GDD spec sources
3. Read the build-plan-index (`docs/gdd/09-pm/02-build-plan-index.md`) — find the tree's row in the Implementation Record
4. Check if the plan tree lives in `plans-glm/` (OBSOLETE per 2026-08-12 consolidation) or `plans-godot/` (current authority)
   - **meept repo exception (2026-09-01): plan forests live in `docs/plans/<forest>/`**
   (root `master.md` + `DECISIONS.md` + `SHARED-CONVENTIONS.md` + per-tree dirs
   `01-…/`…`05-…/` each with master + leaves). The build-plan-index / GDD
   surfaces in steps 2-3 above are rebellion-convention; meept forests track
   status in the forest root's own Completion Tracking table instead.
   Forests are often UNTRACKED (`??` in git status): git diff shows nothing
   for sibling edits, so `ls -la` mtimes are the drift signal — check them at
   session start and treat every patch tool "modified since read" warning as
   a sibling-edit alert (re-read before writing).

### Phase 1b: PLANNED Trees — Design Review Mode

When the tree's status is PLANNED (not yet implemented), the workflow inverts:
there is no code to check against the plan — verify the PLAN against the code
and spec it claims to build on. Proven 2026-08-16 (tree 24 review: 5 major +
5 minor findings caught pre-dispatch). Write-time twin: most of these defect
classes can be prevented at authoring time — see `hierarchical-planning` →
`references/authoring-from-brief.md` (anchor survey-verification, cross-leaf
symbol pinning, flag-off equivalence gates, state-slot surveys for
parallelization trees):

1. **Verify every "existing state" claim against the repo.** Grep each quoted
   symbol, function signature, wire field, and constant (`FogRangeCap`,
   `sidecar_client.gd` payload keys, line numbers). Plans that misstate
   current code produce leaves that patch the wrong thing. Confirm absent
   things are absent AND present things match exactly.
2. **Stress-test the design math at its operating point.** Recompute each
   formula with the input values where the feature actually fires. Classic
   failure: a cap stacked after a multiplier that already sinks the range
   below the cap — dead code exactly when the feature occurs (NPC fog range
   60·light·0.5 ≈ 9 m at night vs a 15–29 m "tier cap" that never binds).
   Fix pattern: neutralize the multiplier (set it to 1.0) when the tier/cap
   system is active so the cap does the limiting. Ask of every constant: at
   the realistic operating point, does it do work?
3. **Check formula sketches for behavioral bugs.** e.g. `exp(-fract(TIME*k))`
   damping is a sawtooth — it pulses back to full strength every 1/k s and
   never responds to state changes (player stopping). Damping must derive
   from the causal input (a CPU-side envelope from |velocity|), not clock
   phase.
4. **Cross-check the design against the cited GDD spec's own numbers.** If
   the plan's contract contradicts the spec (e.g. fog dominant seasons), the
   reconciliation leaf must be told to REWRITE the spec section — "fill the
   open table" language hides the contradiction and leaves the GDD
   self-inconsistent.
5. **Check spec-deferred hooks.** GDD open questions (e.g. "can a scripted
   scenario pin a weather state?") must either be implemented by the plan
   (pin API) or explicitly deferred — a plan that ignores them will fight
   the scripting layer later.
6. **Surface minor findings too** (undecided either/or left to leaves,
   missing sentinel values, dependencies on other trees' pending gates,
   config-pattern debt in files being edited) — they're cheap to fix at
   authoring time and expensive after dispatch.
7. **Report verdict + numbered problems (majors vs minors) first; fix only on
   explicit go-ahead** — same posture as STALE-tree reviews.

8. **Read EVERY leaf before issuing master-level findings.** The master's
   contract blocks lag its leaves: leaves are written later and in more
   detail, so a gap you would report from master.md alone is often already
   pinned in the leaf that owns the behavior (an empty-check ordering, a
   runner signature, the startup call site). Reporting it anyway burns a
   review round and invites a redundant patch. Read master + all leaves,
   then report; where the two disagree, fix the document the WORK lands in
   (usually the leaf) and make the master match it.
9. **Byte-verify canonical spellings across master + leaves before
   dispatch.** Field names, JSON keys, hook/function names, and literal
   fixture names drift between documents written in different sessions (a
   `Datasets`/`Dataset` field, a `forPath`/`exists` hook, a
   `case34-bkt`/`zbd34-bkt` fixture). A leaf dispatched against a drifted
   symbol fails at the WRING leaf, after its siblings shipped. Sweep with
   a regex pinned to EXACT canonical strings - and beware the inverse
   trap: a checker pattern loose enough to also match the CORRECT spelling
   reports the right answer as a violation and invites an identity no-op
   patch loop.
10. **Re-run the structural compliance scanner after any plan edit**
   (master or leaf text). Editing contract blocks or tables can break the
   template checks; per-file verdicts are the gate, and historical archive
   trees that predate the template are not yours to green.

**Repo-fact verification extensions (2026-09-01, proven on meept
llm-resilience-forest tree 04 — 3 majors + 4 minors caught pre-dispatch):**

- **Verify the causal claim, not just existence.** When a plan says "field X
  is maintained by Y" (e.g. "LastActivity is maintained by message
  activity"), grep ALL writers of X. The actual writers may be unrelated
  mutations (session ResumeSession/SetProject) — a signal helper built on
  the assumed semantics misfires. Also grep for an EXISTING primitive that
  already implements the plan's query (e.g. an orphan
  `ActivityTracker.HasRecentActivity(sessionID, window)`) — plans reinvent
  wired-or-unwired primitives when the docs never told the author they
  exist.
- **Read suggestively-named files before endorsing audit premises.**
  `inuse.go` sounded like request-concurrency tracking; one read showed it
  is boot-time startup gating. A single file read defeats a whole wrong
  audit premise the plan's Context section built on.
- **Diff plan-literal replacement strings against the FULL current
  statement.** A plan prescribing "the ORDER BY becomes X" silently deletes
  co-located terms (agent-affinity `CASE WHEN agent_id = ?` preceding
  priority DESC). Cite the correct composite ordering and demand a
  regression test for the term the literal would drop.
- **Cross-tree contracts: grep the named CONSUMER tree for the contract's
  key term.** §4.4 declared "tree 04 → 03"; tree 03's docs had zero
  mentions of "interactive". A frozen contract whose consumer never
  references it is aspirational, not landed — fix the consumer leaf or
  amend the contract, and check both trees' ownership of any shared file
  (store.go) the contract touches.
- **Verify the plan's grep hints name real symbols and that claimed
  stamping sites carry the needed identifier.** `EnqueueJob` did not exist;
  the "dispatcher" was a job consumer not a producer; the payload struct
  had no session provenance, so the plan's stamping site could not exist
  without prior schema work. Enumerate real producers by grepping the
  constructor (e.g. `NewJob(`), not by trusting the plan's hints.

**Root/sibling-doc extensions (2026-09-01, second pass on the same forest —
this time the ROOT docs themselves: 3 ship-blocking majors in master.md +
SHARED-CONVENTIONS.md + one tree master; evidence in
`references/llm-resilience-forest-root-audit-2026-09-01.md`):**

- **Audit forest ROOT docs with leaf-grade skepticism.** master.md /
  DECISIONS.md / SHARED-CONVENTIONS.md summarize every leaf and are read by
  every dispatch, so an error there multiplies. Per frozen contract symbol:
  (a) verify directional consumer arrows ("§4.1 X (02 → 01/03/04)") by
  grepping each NAMED consumer tree for the symbol — an arrow naming a tree
  with zero references is fiction, and the contract block's own header
  restated the same wrong set, so check both places; (b) verify each
  contract's Owner line against the owning leaf's task list — a master
  contract that merges two leaves' artifacts under one Owner line sends the
  dispatch to a leaf whose brief omits the other artifact; (c) grep D#/Q#
  decision IDs per tree so no ratified decision is left without an owner.
- **Grep stale code anchors forest-wide before calling one fixed.** A wrong
  file:line is almost never alone — the proven case had `loop.go:~4226`
  (actual :4298) in a shared-conventions pitfall AND two leaf cites.
  Fixing the first grep hit is not a fix.
- **Verify identifier-named claims for set-completeness.** "hardcoded
  `maxRetries = 3`" was three constants (`maxRetries`, `streamMaxRetries`,
  `anthropicMaxRetries`); a leaf executing the plan literally greps the
  singular name and declares victory at 1/3. Grep the shape (`Retries`)
  and enumerate the full constant set in the plan text.
- **Verify cited tooling exists**: every make target, script path, and
  `-run` test pattern the plan's verification gates cite must exist on
  disk.

**Tree-05 catalog audit extensions (2026-09-01, third pass on the same
forest — 5 majors + 4 minors caught pre-dispatch; evidence in
`references/llm-resilience-forest-tree05-audit-2026-09-01.md`):**

- **Homonym-name trap: a claim can grep-validate against the WRONG
  struct.** The plan's precedence rule said "models.json5 explicit
  context_window" — that key EXISTS in the codebase (an unrelated
  epistemic-memory config struct) while the actual models.json5 key is
  `context_limit`. A naive grep for the plan's name confirms a false
  claim. When a plan references a config/field name, grep the struct
  tags of the SPECIFIC file format or struct the plan describes, and
  reconcile the name chain it may be conflating (json5 key → catalog
  struct field → runtime struct field can each differ:
  `context_limit`/`ContextWindow`/`ContextLimit`).
- **Verify the cited PRECEDENT exhibits the cited PROPERTY.** D12 said
  LM Studio gets "the Ollama treatment: registry entry, discovery,
  catalog" — Ollama in meept has no discovery at all (grep /api/show,
  /api/tags → zero); the real discovery precedent is PricingSyncer.
  Same class: a leaf said "reuse the id-validation precedent in
  register_local_model.go" — that file has only a rename transform, no
  validation. Both "treat Y like X (which does Z)" and "reuse/extend
  X's validation" are factual claims about X; read X and confirm Z
  before the leaves inherit the fiction. A same-purpose-but-weaker
  function (transform) masquerades as the cited capability
  (validation).
- **Check internal consistency between a contract's values and the
  copy-this-entry instruction.** Contract 2 said `AuthType: AuthNone` —
  no such enum constant exists — while the same leaf's checklist
  demanded "field-for-field matches Ollama's shape" and Ollama is
  AuthEnvVar. Two requirements that cannot both hold = guaranteed
  implementer improvisation. Verify enum values exist AND reconcile
  them with the sibling entry the leaf is told to copy.
- **External-provider API claims are repo-fact claims too.** The plan
  said LM Studio /api/v0/models carries `context_length` (actual field:
  `max_context_length`; `context_length` only lives nested in
  loaded_instances[].config) and that /v1/models carries context length
  (it carries none). Wrong json tags parse silently as zeros — no
  compile error, and hand-built test fixtures encode the same wrong
  name so tests stay green. Verify endpoint + field names against
  upstream docs before dispatch, same as you'd grep a repo symbol.
- **"Modify:" file paths in leaf Tasks must exist.** Leaves told to
  modify docs/workflows/llm.md and a docs/configuration/ providers
  page — neither exists (provider docs live in
  docs/configuration/llm.md). Either name the real file or say
  "Create:" — an unresolvable Modify is an unforced dispatch failure.
  Extends the tooling bullet: leaf Task Files: paths are verifiable
  claims too.
- **Cross-check concurrency-group disjointness against the union of the
  leaves' Files: lists, and check deviation-recording duties.** The
  master claimed group-A leaves touch "disjoint files" while leaf 01
  Task 3 creates the daemon wiring and leaf 03 Task 3 modifies the same
  site. Separately: a leaf that consciously deviates from a D# decision
  (discovery-only catalog vs D12's "…catalog") needs a line telling the
  orchestrator to record it per the DECISIONS footer rule.

**Citation-drift sweep extensions (2026-09-01, sweep of ALL file:line
citations across the forest vs HEAD — 26 files, ~94 citations: ~94
accurate / 13 drifted / 0 wrong / 3 stale-concept; full drift table in
`references/citation-sweep-llm-resilience-forest-2026-09-01.md`):**

1. **Inventory with one grep before verifying** — multi-syntax, both plan
   conventions at once: `path.ext:N(-M)` cites via
   `grep -rnoE '[A-Za-z0-9_/.-]+\.(go|ts|dart|py):[0-9]+(-[0-9]+)?'`, plus
   `~line N|line N|lines N-M` for prose cites. Dedupe against source-line
   context (short cites like `client.go:426` recur across files by design).
2. **Batch verify per TARGET file, not per citation** — one sed/grep pass
   per source file covers its 5–15 cites; ~94 cites ≈ 10 calls. Always
   `wc -l` the target: a file shorter than the cited line means the anchor
   moved out of the file entirely (worst drift class).
3. **Verify semantics, not just numbers.** Leading bound of a range must
   match (declaration line); the trailing bound of a struct/func range is
   the closing `}` — ±1–2 is drift, not error (find real block ends: awk
   `NR>=X && /^}/ {print NR; exit}`). `~N` fuzzy cites are honest
   estimates: grade whether the described region starts near N.
4. **Verdict taxonomy: ACCURATE / DRIFTED / WRONG / STALE-CONCEPT.** DRIFTED
   = right target, shifted numbers (report exact correction). WRONG =
   symbol doesn't exist. STALE-CONCEPT = the *name* is stale while the line
   is right (`ContextWindow` vs actual `ContextLimit`; a `Reflector`
   interface cited as "Chatter interface") — most implementer-hostile,
   because the line checks out and the name does not.
5. **Run the doc's prose grep recipes literally** and reconcile hit counts
   against the doc's own claims — see the root/sibling-doc block above
   (five-loop census found 4 of 5 because the fifth loop uses
   `streamMaxRetries` and a `for attempt := range` shape). Recipes that
   grep ONE constant rot; grep the shape.
6. **A fully-clean file is a finding too.** Name which files are 100%
   accurate so a fix session edits only the drift table. Read-only
   posture: report corrections, don't edit, unless asked.

**Tree-02/03 client-internals audit + fix-wave extensions (2026-09-01,
fourth pass on the same forest — 13 confirmed findings, ~24 edits
applied; the two auditors for these trees died on HTTP 429s so the
audit ran in-session — see the rate-limit pitfall below):**

- **Grep the package for a planned type/function NAME before freezing a
  contract.** The forest's §4.5 contract declared `ParkedTurn` while
  `internal/agent/budget_resume.go:27` already declared it — a
  duplicate-type compile error on the first leaf run. Inverse of the
  homonym trap: not greps landing on the wrong struct, but invented
  names colliding with a sibling in the same package. The fix renamed
  the contract type (`ParkedTurnRecord`) everywhere plus the prose.
- **Verify mechanism→leaf credit in BOTH directions.** Root audits
  check a contract's Owner line against the owning leaf; also check
  every "X planted/created by leaf N" claim against the NAMED leaf's
  Files: lists. Tree 03's master credited the `ThrottleBackoffError`
  loop branch to "tree 02 leaf 04" — leaf 04 never touches loop.go;
  leaf 03 Task 4 plants it.
- **Config knobs are producer/consumer contracts inside one tree.**
  Leaf 03 consumed `failure_policy.short_retries` and leaf 05
  `pacing.max_interval` — neither appeared in the schema leaf's config
  task. Grep every config key a leaf READS against the leaf whose
  Files: list includes the schema file, and move field creation to the
  earliest consumer's dependency.
- **Fix wave under concurrent writers (sibling agents editing the same
  untracked forest mid-session):** re-grep the target region
  immediately before EACH patch — one patch reintroduced a stale value
  (`loop.go:4226`) a sibling had already corrected to `:4298` in the
  same file's siblings. Always read the returned unified diff for
  regressions, and re-run the fence-parity scan after every markdown
  patch: one patch split a ```go block and the following block lost
  its opening fence; another mangled bullet indentation when
  old_string spanned reflowed lines. Repair immediately, don't defer
  to the verification wave.
- **Two-sided join at the PLAN level: every "What This Leaf Consumes"
  entry must trace to some leaf's "What This Leaf Exposes" block or to
  existing code.** Tree 03 leaf 03 consumed an `AsThrottleBackoffError`
  accessor that no tree-02 leaf created (only `IsQuotaResetError`
  exists today) — a consumed-but-never-created symbol surfaces as a
  compile error in the CONSUMING tree, after the producing tree
  shipped. Fix shape: assign creation to the producing tree's earliest
  leaf in the consuming tree's dependency chain, inside its Exposes
  block, with a NOTE explaining why (2026-09-01: added to tree 02
  leaf 03 beside the type it accessor-izes).
- **Patch reflow is a damage class beyond broken fences.** A
  replace-mode patch whose old/new_string spans fixed-width wrapped
  lines can merge the replacement into one over-long line or silently
  re-nest bullets: one pass produced a 130-char paragraph line and a
  demoted bullet in SHARED-CONVENTIONS §7. After each markdown patch,
  re-read the changed region (not just the returned diff) and check
  fence parity AND line wrapping/bullet depth; fix in a follow-up
  patch before moving on.

**Full-forest interaction audit (fifth pass on the same forest, 2026-09-01 —
trees 01/03/04 + tree-02 leaf 04: 3 blockers + 5 risks; evidence in
`references/llm-resilience-forest-trees-01-03-04-audit-2026-09-01.md`):**

- **Trace a premise's DISPATCH chain, not just its registration.** When a
  plan's premise is "today X happens at site S" (the hook gives up to the
  user at verification_hook.go:119), verify S actually EXECUTES: grep the
  dispatch method (`RunPrepareNextTurn`) for non-test callers, not the
  Register call. Registered-but-never-dispatched hooks are green in tests
  that invoke components directly — and the plan then wires new features
  onto dead infrastructure (blocker B1). When one dispatch path is dead,
  enumerate everything ELSE registered on it (the security/secret hooks
  were silently dead too).
- **Simulate composed mechanisms for two iterations, not one.** Plans that
  combine two existing mechanisms (reset fixCount on escalation × the
  loop's one-shot auto-clearing model override) verify fine per-mechanism
  and break in combination: the escalated budget silently shrinks to ONE
  turn (risk R1). For any "feature uses existing X plus existing Y"
  design, hand-trace iteration 2 — the second use is where
  one-shot/persistent/latch semantics diverge.
- **A "mirror precedent X's write path" claim needs X's write verified as
  RUNTIME-mutable and consumer-reaching.** PricingSyncer writes only its
  own cache; enrichment into resolver models happens once at wiring
  (SetPricingSyncer), so mirroring it yields wiring-time-only values.
  Same pass: the leaf's "trace one ContextWindow read" hint pointed at the
  DISPLAY catalog (model_picker) while the runtime consumer is
  ModelConfig.ContextLimit in context_firewall. Extends the tree-05
  precedent bullet: verify the precedent's WRITE path (who consumes it at
  request time), and trace the read the FEATURE depends on, not the first
  same-named read.
- **Contract fields that need origin data: check availability IN SCOPE at
  the stamping sites, and the freshness of the evaluation.** Tree 04's
  `Interactive` flag had no session available at any real enqueue site
  (Job/StepJobPayload carry no session; the worker has none), and the
  flag is evaluated once at enqueue — a job enqueued while idle never
  upgrades when the user returns before claim. For any "stamp X from the
  originating session" contract: grep producers for what's in scope, name
  the plumbing work (payload field or TaskID→LinkedSessions lookup), and
  state the evaluation-time semantics explicitly.
- **A frozen contract with an opaque `json.RawMessage` payload needs its
  encoding DECLARED when behavior/tests depend on round-trip.** §4.5's
  ParkedTurnRecord.TurnPayload had no declared shape, yet the
  byte-identical wrapper tests and the re-park path (needs
  ProviderID/CredentialKey, absent from the frozen struct) depend on it.
  Verify the resume path re-sends the STORED payload (it does —
  RunOnceWithParts from stored fields, handler.go:1594), then demand the
  encoding in the contract.
- **Cross-entity invariants cannot live on per-entity state.** endpoint
  shared fate (block models across sibling aliases) was specced onto
  per-alias AliasHealth — structurally impossible. Check the state's home
  struct vs the SCOPE of the invariant, not just that a field slot
  exists; the frozen conventions themselves named the right home
  ("on the Resolver next to entryBlocks").

**Execution-phase extensions (2026-09-01, dispatching the reviewed forest —
the review skill's job does not end when the verdict is issued):**

- **File-ownership carve-outs belong IN the dispatch context, per leaf.**
  Each tree-orchestrator dispatch named: owned files, SHARED files
  (schema.go, resolver.go) with "patch-only on unique anchors, never
  write_file whole", and an explicit DO-NOT-TOUCH list naming the other
  running trees' files. Sibling orchestrators are as real a collision
  surface as sibling leaf agents.
- **Stagger contested files even when the forest root says "parallel."**
  Two leaves rewriting different parts of client.go (retry loops vs
  concurrency semaphore) was resolved by HOLDING one: a tracking-table
  note ("held: client.go conflict; green-light after tree 02 leaf 03
  lands") plus the parent holding the dispatch until the predecessor
  landed. Contested-file holds beat merge-detective work every time.
- **When even a hold can't serialize (two leaves must land in the same
  file set), defer the contested wiring to a WRITTEN PLAN.** The pacing
  leaf implemented pacing.go + metrics + docs and produced the exact
  client.go wiring (site file:line, call shape, typed-nil guard) as a
  report section instead of editing the contested file; the orchestrator
  applied it after the slot-gate leaf landed. "Implement everything
  except the contested seam; hand the orchestrator the wiring recipe" is
  a clean decomposition.
- **Late-arriving verification subagents predate your fix wave.** A
  verifier dispatched before the fixes applied re-reports FAILs already
  landed. Re-run each reported FAIL check against the current tree;
  commit only the genuinely-missing residuals (two were: a bare
  not-created-yet test-file cite and a wrong test function name), and
  say explicitly which findings were already fixed. Never re-apply a fix
  a stale report flags.
- **Reject audit findings that don't survive a fresh re-read — about 1 in
  6 late findings was an outright misread.** One "owner misattribution"
  conflated a contract's endpoint-state block with a ThrottleBackoffError
  type defined elsewhere in the same leaf; the quoted block contained no
  throttle content. Grep the exact quoted text; if the evidence doesn't
  survive, reject with file:line evidence rather than "fixing" a
  non-problem (rejections are real work products).
- **After review lands, keep a tree-level dispatch state table** (tree →
  leaves done/committed shas/holds/next-gate) in the todo list — with
  staggered trees plus mid-tree deaths, "what dispatches next" is a
  tracked state machine, not something to re-derive from git log each
  time.

### Phase 2: Check Implementation

1. List files on disk matching the plan's claimed deliverables
2. Run relevant tests: `go test ./... -short -race` for Go, GUT headless for Godot
3. Grep for TODO/FIXME/stub markers in the implementation package
4. Verify determinism contract (no `time.Now()`, single RNG stream, no map iteration in output order)

### Phase 3: Cross-Reference GDD

1. Read the GDD spec docs cited in the plan tree
2. Check for 2026-08-13+ revisions that may have introduced drift (common: Stage 5 facades, Stage 9 lighting, Stage 6 wallpaper changes)
3. Compare plan's "not implemented" items against actual GDD scope — some "open" items may be intentionally deferred

### Phase 4: Update Tracking

1. Update the build-plan-index row if status or notes changed
2. Update the plan tree's `master.md` state section if needed
3. Add Implementation Record entry if tree reached COMPLETE
4. If GDD changed post-last-check, mark tree STALE per AGENTS.md Rule 4

### Phase 5: STALE Close-Out (re-verify → COMPLETE)

When a tree was marked STALE because a GDD spec source changed, closing it
is a DOCUMENTATION PASS + CODE RE-VERIFICATION — not a code rewrite. The
code may already conform (the GDD change and the implementation often land
in the same session). Proven 2026-08-13 (trees 04-world-streaming +
11-rendering-vfx, GDD §07 seasonal solar model + shadow-depth-ramp):

1. **Re-verify the CODE against the new spec, line by line.** Grep the new
   constants in the implementation (`shadow_opacity 0.85→1.0`, `SSAO
   0.5→1.6`, `200 m` sun distance, moon at sun+180°). Check single-writer
   ownership: the ramp properties must be written by ONE system per frame —
   a sibling manager that also writes them is a property fight, not drift.
2. **Run the tests that pin the spec** (e.g. `test_solar_cycle.gd` 14/14).
   Tests written in the same session as the GDD change ARE the verification
   evidence — cite them in the record.
3. **Update the LEAF docs that encode the OLD spec.** This is the part most
   agents skip: leaf content (fixed phase windows, task lists, checklists)
   silently contradicts the GDD until someone reads it. Rewrite the leaf to
   the new contract and add a dated re-verification note at the top.
4. **Update ALL FOUR tracking surfaces consistently** — leaving any one of
   them at STALE while the others say COMPLETE is the drift this pass is
   supposed to eliminate:
   - `plans-godot/master.md` branch index table (the `| 04 | ... | STALE |` row)
   - `plans-godot/master.md` completion tracking table (the `| 04-world-streaming | STALE |` row)
   - branch orchestrator child index (the `| 01 | 01-lighting-rendering.md | ... | STALE |` row)
   - branch orchestrator completion table (the `| 01-lighting-rendering | STALE |` row)
5. **Close the Implementation Record row**: Drift Found stays **YES** (it
   is the historical record of what happened); update Action Taken to
   document the re-verification result + tests + leaf-doc updates; update
   Last Changelog Check to today.
6. **Respect the status transition rule** (AGENTS.md §4): STALE → COMPLETE
   directly is forbidden. The path is STALE → IN_PROGRESS (revision) →
   COMPLETE. Record the intermediate step in the Action Taken text.
7. **Add a changelog row (Rule 1)** for the close-out pass itself — a new
   session touching plan docs + GDD-adjacent content needs its own entry,
   even when no GDD file changed.

## Executing a Forest ("dispatch the trees")

Forest-root dispatch (2026-09-01 meept llm-resilience-forest): the
orchestrator dispatches each TREE as one `role=orchestrator` subagent, not
leaf-by-leaf itself. Rules proven there:

- **Per-tree ownership map in every orchestrator dispatch context**: owned
  files, SHARED files (schema.go, resolver.go) = "patch-only on unique
  anchors, never write_file the whole file", and an explicit DO-NOT-TOUCH
  list naming the other running trees' files. Sibling sessions AND sibling
  orchestrators both exist in this repo — same collision surface.
- **Stagger trees that touch the same implementation file** even when the
  forest root calls them "parallel" (forest root said 01+02+04+05
  parallel, but 01 and 02 both edit resolver.go/agent files → sequential;
  04 leaf 03 rewrites client.go's semaphore, which 02 leaf 03 also
  rewrites → that leaf is HELD with a tracking-table note until the other
  tree's conflicting leaf lands).
- **Keep the stagger queue in the todo list** so the next dispatch is
  mechanical when a predecessor reports; check `git log` before
  committing — a sibling session may have committed the shared directory
  already (verify your fixes are IN its commit instead of committing).
- **Committing a docs-only tree**: run the pre-commit gates
  (fence parity, corruption grep, check_template_compliance) BEFORE the
  commit attempt; docs-only commits pass trivially but the hook suite
  still runs 15 checks.

**Forest CLOSE-OUT gates (2026-09-02, meept llm-resilience-forest — all
5 trees COMPLETE → root Integration Test Plan execution). The root's
Review Checklist + Integration Test Plan are gates, not ceremony:**

1. **Full internal suite: run with `-p 4` (or re-run failed packages
   serialized).** The maximal-parallel run produces load-timing flakes
   (acp session timeouts, comm/http MCP tests, TestSpecialistShadow) that
   all pass isolated and in a `-p 4` re-run — 86 packages green. A FAIL
   is a regression only if it reproduces serialized; check that before
   diagnosing.
2. **lint-ci failures at close-out: scope by ownership before fixing.**
   Extract the lint findings' file list, `comm` it against the
   forest-touched file list (`git diff --name-only <pre-forest>..HEAD --
   internal/`), and fix ONLY findings in forest files (this pass: 2
   staticcheck hits — a `var x bool = true` and an initial value dead
   because both switch arms assign it). Surface pre-existing debt in
   other packages as an observation; do not fix drive-by. Beware the
   wastedassign false lead: `complete := false` re-assigned by both
   switch arms — the fix is dropping the initializer, not a `_ =`.
3. **Decision reconciliation needs evidence, not assertion.** For each
   open question, grep the shipped code for its outcome (config default
   line, the comment citing the Q-id, the frozen constant list) and
   record file:line in DECISIONS.md — "defaults became law or were
   overridden" is the root plan's explicit gate, and per-question
   evidence is what makes it auditable.
4. **Root tracking tables drift under sibling sessions — re-read before
   bulk edit.** A python replace on the tracking table failed its
   assertion because the sibling had already updated the rows (its rows
   also carry richer notes). Read current state, merge (sibling notes +
   your hashes), and expect the pre-existing row text to differ from
   what you remember.
5. **Duration-string config fields vs duration-rewriting loaders
   (integration bug caught only at close-out — the leaf's deviation note
   predicted it).** meept's json5 loader rewrites ANY quoted
   Go-duration-looking value to ns integers (`quotedDurationToNanos`),
   so a plan-added STRING field whose default looks like a duration
   (`queue.interactive_window: "5m"`) round-trips as an int; the schema
   validator then rejects the reload and configui save/load fails with
   "type mismatch: found number, expected string". Fix shape: key-aware
   rewrite exemption set in the loader (skip declared-string keys) +
   a regression test pinning BOTH sides (exempt key stays a string;
   real duration keys still convert). When any leaf adds a config field,
   check the loader/normalizer pass for value-shape rewrites before
   freezing the field's type.

**Orchestrator death/pause mid-tree — recovery protocol (2026-09-01,
llm-resilience wave 1: tree 01's orchestrator died after leaf 03; tree
05's paused on a git commit gate):**

1. **Detect**: signs are (a) last tree-scope commit predates the
   orchestrator's expected runtime, (b) the tree master's Completion
   Tracking table still shows PENDING rows for leaves whose commits
   exist in `git log`, (c) leaf-implied files absent. TrackING TABLES
   LAG when orchestrators die — never trust them post-mortem; reconcile
   against `git log -- <tree scopes>` + `ls` of leaf-implied files.
2. **Recover a missing leaf by dispatching ONE implementer** scoped to
   that leaf, with the dispatch context listing what ALREADY landed
   (commit shas + the artifacts the earlier leaves created — e.g.
   "DecideEscalation exists in verification_escalation.go; do not
   duplicate; extend it"). The dead orchestrator's leaves 01..N-1 are
   the new implementer's dependency context, not something to redo.
   No-commit contract; the parent reviews + commits.
3. **A paused-on-gate orchestrator's work is parent-committable**: when
   an orchestrator stops at a git-commit permission gate and reports,
   the parent reviews the work (build/tests/analyzers) and commits the
   paused leaf itself under the user's standing no-pause preference —
   by explicit path list, one leaf per commit, noting in the body that
   the orchestrator prepared it. A clarify-timeout is not a veto.
   (Commit-mechanics detail: multi-agent-git-coordination pitfall (x).)
4. **A leaf session may keep writing after you commit its sibling
   files.** After committing a leaf by path list, re-check `git status`
   for NEW dropped files over the next minutes: a leftover that fails
   to build (references a field not yet landed) = in-flight; poll
   mtimes for quiescence (~2 quiet windows). The leaf session often
   commits its own remainder — waiting beat committing a red half
   (proven: tree-04 leaf-02 landed `35c79887` + tracking `081898f8` on
   its own while the parent stood down).
5. **Fix the stale tracking tables in the recovery commit** (statuses +
   commit hashes + what the orchestrator repaired), and fold any
   deviation rows the dead orchestrator owed (e.g. a D12 deviation
   line per the DECISIONS footer rule) into the same pass.
6. **Concurrency note on step 4 (proven tree-04 leaf-02):** the leaf
   session's continued writes may collide with YOUR partial commit of
   the same leaf — `d7d2cddc` (parent's Task 1+2 commit) was flagged
   by the leaf's own orchestrator as an anomaly because it appeared
   mid-flight. Resolution: the leaf session finished and committed the
   remainder (`35c79887`) itself; parent accepted both commits as one
   leaf and said so in tracking. Lesson: when a leaf spans multiple
   commits, the parent's early partial commit is SAFE only if the
   remaining work lands as a strict follow-up — verify the remainder's
   commit exists before recording the leaf COMPLETE, and record the
   two-sha shape in the tracking row.

**Tree-02 dispatch (the forest's risk tree) — invariants to gate review
on (2026-09-01, dispatch context that was proven necessary):** when a
tree rewires shared live machinery (the five client retry loops), put
the quota invariants IN the dispatch context as explicit review gates:
(a) `*llm.QuotaResetError` never reaches RecordAliasFailure; (b) no
retry loop short-retries a quota error (errors.As quota early-exit
placement unchanged); (c) `ErrAllModelsQuotaBlocked` stays distinct;
(d) `classifyQuotaDecision`'s existing tests stay green unmodified.
Name the specific SIBLING-landed code the tree must not disturb (tree
01's ResolveEscalationRef in resolver.go, tree 05's registry/catalog
files) in the DO-NOT-TOUCH list, and require a clean `go build ./...`
BEFORE dispatch — a dirty tree at orchestrator start means a previous
tree's work is still in-flight.

**Contested-file wiring design: pick a seam that survives sibling
children (2026-09-01, WithPriority wiring).** The obvious wiring —
`WithPriority(true)` at the loop's chat call site — was wrong because
`SpawnVerifier` builds a CHILD AgentLoop that re-enters the same call
path: verifier turns would have been marked interactive. The fix was a
LOOP-LEVEL flag (`WithInteractiveTurns` LoopOption, default false =
byte-identical) that only the daemon chat loop opts into, with
ConfigSnapshot propagation to session clones. When wiring a priority/
tier flag through a path that recurses into itself (parent → child
loop), discriminate at the LOOP level, not the call level, and decide
explicitly which recursion (verifier children) stays background.

**Recovering a half-done leaf from an interrupted orchestrator (2026-09-01,

- **Validate the WIP against the leaf doc instead of rewriting.** The
  interrupted run had left all five loops ~90% rewired and structurally
  correct. Grep the invariant placements (quota early-exit BEFORE
  Classify in every loop), the branch placement (ThrottleBackoffError
  branch before the RateLimitError branch), and the config plumbing
  (constants gone, `ShortRetries` nil-safe default) — then fix forward.
- **Hunt collateral damage outside the leaf's file scope.** The dead run
  had cut `errors_test.go` from 23 tests to 3, deleting tests for
  functions that STILL EXIST (ParseRateLimitBody, BackoffWithJitter,
  extractInnerJSON, the UserMessage suite) — collateral of a sloppy
  in-file rewrite, not intentional. Restore from
  `git show HEAD:<path>` and re-add only the genuinely new tests
  (the new error type's Error/Unwrap/errors.As trio) in the same file.
  Diff test-function lists (`git show HEAD:f | grep 'func Test'` vs
  current) to enumerate exactly what vanished and check each for a
  replacement home before restoring.
- **Dead symbols trip the unused-code pre-commit gate.** The refactor
  superseded `isRetryableStreamingError` (Classify replaces it) and left
  an unused test var — the gate blocks the commit naming them. Remove
  rather than `--no-verify`.
- **New scripted tests against real transport semantics expose latent
  reader bugs that unit tests hide.** The leaf's new 429-retry-then-SSE
  test failed with "two hits, empty content" while every strings.Reader
  fixture passed: `sseScanner.Scan()` checked `err == io.EOF` BEFORE
  consuming `n` bytes, discarding data delivered together with EOF
  (the normal http.Response.Body pattern), and separately dropped the
  byte at each read-chunk boundary. Diagnosis chain that pinned it in
  four probes: deterministic fail → scanner over strings.Reader = 5
  events OK → scanner over httpResp.Body = 0 → iotest matrix
  (OneByte/HalfReader = 5, DataErrReader = 0). Fix: append `chunk[:n]`
  BEFORE honoring EOF; iterate by index keeping the unconsumed
  remainder. Pin with regression tests across
  iotest.OneByteReader/HalfReader/DataErrReader — a parser that passes
  only strings.Reader fixtures is untested against production readers.
- **Renamed-constant assertion updates are legit; wholesale test-file
  rewrites are not.** The WIP's `wantAttempts: maxRetries` →
  `defaultShortRetries` edits were correct mechanical renames; the same
  rewrite's deletion of 15 unrelated tests was not. Judge each diff
  hunk in a test file separately when recovering interrupted work.
- **A concurrent stash-pop sweeps other agents' WIP into your diff**
  (2026-09-01: compress/memory/scheduler fixes from a sibling's
  codebase-review session appeared after popping a stash). Split
  `git status` against the leaf's ownership; save out-of-scope diffs to
  /tmp, `git checkout --` them, and surface them to the user — never
  commit another session's in-flight work inside your leaf's commit.



When the user says to implement a branch, follow the branch orchestrator's
dispatch protocol exactly (groups A→B→C→D, max 3 parallel):

1. **Dispatch context is the contract.** Each implementer gets: its leaf doc
   path + master contracts INLINED by reference, hard rules (no git commands,
   no network in tests, scoped formatters only), explicit owned-file list,
   existing test count it must not break, and required verification commands.
2. **Review in-session before committing**: run `make test` + `ruff check`,
   diff against the leaf's review checklist, grep for hardcoded values the
   spec forbids (vendor names, endpoints), verify contract field-for-field.
   Commit per leaf with exact paths; sweep `git status --short` for strays.
3. **Timeouts are expected** — see Pitfalls below. Budget roughly half your
   effort for in-session repair of interrupted subagent output.
4. **After Group D lands**, run the branch Integration Test Plan verbatim,
   then update BOTH tracking tables (branch orchestrator + master) with
   COMPLETE status and commit hashes.

Pitfalls specific to execution (beyond review-mode pitfalls above):
- Subagents will not wire shared entry points you forbade them from touching
  — keep a merge checklist of deferred wiring (`__init__.py` imports,
  CLI flags, manifest schema extensions) and apply them yourself before
  integration tests.
- Injected-clock run_id collisions: workers that pin `now=` for deterministic
  run_ids must advance the clock per `run()` call or a second run on the same
  instance raises duplicate-run_id. Test second-run idempotency explicitly.
- pyarrow `Table.take([])` on an empty table with null-typed columns raises
  ArrowNotImplementedError — guard sort-by-column take paths with a
  `num_rows > 0` check and write the empty table directly.
- Stub transport responses: real `FetchClient.get()` parses JSON, but test
  stubs often return response-like objects. Workers must normalize
  (call `.json()` if callable) so both work.
- Auth param names from source-truth are generic ("api_key") but env vars are
  specific ("CONGRESS_API_KEY") — workers need a secret_lookup mapping at
  registration time, and registration must be fault-tolerant (skip + warn
  when the env var is missing rather than breaking module import).

## Verify-Fixes Pass ("verify fixes part A/B/…")

When asked to VERIFY that a previous fix pass landed (read-only, no edits):

1. **Verify each claimed fix against its own success criterion, mechanically
   where possible.** Schema claims → parse with `python3 -c "import yaml…"`
   and assert required keys per entry (catches a missing key far more
   reliably than eyeballing). Cross-branch wiring claims → grep both the
   producer file and every consumer file for the exact artifact name/path/
   signature. Count-consistency claims → grep ALL numeric-count words
   ("five|six|eight|nine") plus the noun, branch-wide.
2. **Stale counts hide OUTSIDE the count statements.** A fix that updates the
   pinned route table + orchestrator count paragraph + leaf acceptance
   criteria can still leave a contradiction in prose nobody thinks of as a
   "count location": Integration Test Plans ("curl smoke of all five GET
   endpoints"), task objectives, UI checklist wording. Grep for old-count
   words across the whole branch before declaring consistency.
3. **Validate dangling cross-references mechanically.** Any leaf that cites
   an artifact by name/number ("per Dispatch Protocol Phase 2", "Contract
   B2-4", "seven endpoints") must have its target confirmed to exist in the
   file it names — grep both sides. A reference whose target section was
   renamed or never written reads fine in isolation and only fails when
   followed. Also scan global leftovers: terms from the pre-fix vocabulary
   ("pl-/pa-" prefixes, old route names) anywhere in plans/ or docs/.
4. **Fence-parity scan before declaring a docs tree consistent.** A single
   unbalanced ``` fence silently swallows half a document's content into a
   code block, hiding contradictions from any reader (and from you). Run:
   `for f in $(find plans docs -name "*.md"); do n=$(grep -c '^\x60\x60\x60' "$f"); [ $((n%2)) -ne 0 ] && echo "ODD $f"; done`
   Cheap, deterministic, catches what eyeballing misses.
5. **Report per-section PASS/FAIL with file:line evidence**, then an overall
   verdict line. Read-only posture unless explicitly asked to fix.
6. **ALWAYS emit the report text in the same turn your last tool call
   returns.** Ending the turn on a tool call with no accompanying prose
   leaves the user staring at nothing and forces them to prompt again
   ("you executed tools but returned an empty response"). The verdict IS
   the deliverable of a verify pass — write it, don't assume the tool
   output speaks for itself.

## Pitfalls

- **"Don't trust the plan's stated completeness" means verifying the plan's OWN
  named deliverables, not just the code it describes.** 2026-08-30 (meept
  model-alias-enhancements): the Completion Tracking table said "Tests pass",
  the call-site wiring was genuinely correct — but every test file the leaf
  spec'd by filename (`providers_test.go`, `resolver_caller_test.go`,
  models_test.go additions) had never been created. The table records the
  implementer's CLAIM. When a leaf contains TDD steps naming explicit files,
  `ls`/`git ls-tree` each named path before accepting COMPLETE.
- **The plan's own spec test can pass with the bug present.** That tree's
  Task 5 test (`Models: ["b","a","c"], default "a"`) passed under the broken
  implementation because plain rotation lands on "a" anyway. For any
  "instead of X, do Y" feature, check the plan's test places its expected
  outcome where X alone cannot reach it; if not, the test proves nothing —
  rewrite it during review (e.g. put the default model LAST).
- **Review resolver/state-machine code by tracing order of operations within
  each function, not block-by-block in isolation.** Two real bugs there were
  invisible per-block: (1) a reversion check reading `CooldownUntil` that an
  earlier block in the same function had already cleared (dead on every path
  where the feature matters); (2) a sticky pin-release branch placed after
  the rotation that zeroed its trigger. Fix shapes: arm a durable
  flag/deadline at the failure site (transient expiry state cannot carry a
  "has expired once" fact); hoist the feature block above the block whose
  side effects invalidate its predicate. Detail in `meept-development`
  skill → `references/alias-failover-patterns.md`.

- **The orchestrator says COMPLETE while the index says STALE** — the most
  common tracking inconsistency found during close-out. The 2026-08-13 pass
  found master.md + Implementation Record correctly marked STALE but BOTH
  branch orchestrators still claiming COMPLETE. Grep ALL FOUR surfaces for
  the status word before declaring the tracking consistent.
- **Leaf docs rot silently.** The index being STALE is visible; the leaf
  content encoding the pre-change spec is invisible until read. When closing
  a STALE tree, always read the leaves the changelog row names as affected —
  they are the ones with the stale numbers.
- **STALE marking alone does not update leaf content.** Marking the tree
  STALE (Rule 4) and CLOSING it (Phase 5) are two separate passes; a tree
  can sit STALE for days with correct index rows and wrong leaf docs.
- **OBSOLETE directory trap**: Plans in `plans-glm/` are historical reference only. The build-plan-index is the single source of truth for current tracking. Do not create new plans there.
- **Tracking tables corrupt structurally.** A hand-edited build-plan-index / tracking table can have rows with the wrong pipe count, an embedded bare `|` inside a Notes cell, columns grafted from the wrong table, or a missing cell. They still render but mis-align. Before trusting "the index says X", verify the row's pipe count matches its table (7-col → 8 pipes, 6-col → 7 pipes). See `references/markdown-table-repair.md` for the scan-fix-re-scan procedure.
- **Subagent rate limits**: Delegating plan review to subagents can hit HTTP 429 limits — in one 6-auditor parallel dispatch (2026-09-01 llm-resilience-forest), 5 of 6 died within minutes. Plan for the fallback instead of re-dispatching (re-dispatch hits the same wall): audit the dead auditors' scopes directly in-session (read the tree's leaves, grep each code claim). The direct audits are reliable and found 3 majors the surviving scopes did not cover. Deaths are STAGGERED (some lanes die in seconds, others return at 4-18 min) — audit dead lanes' scopes directly while live ones run, and treat late reports as stale snapshots (see next bullet). Full playbook for concurrent sibling-session reviews + the orchestrator-level ownership map for dispatching multiple tree orchestrators at once: `references/concurrent-forest-review.md`.
- **Late-arriving auditors must be DISPOSITIONED, not ignored** (2026-09-01): the "dead" auditors returned 5-15 min later with real findings, including 3 majors the in-session fallback had not covered (LastActivity writer-path misstatement, inuse.go premise error, §4.4 consumer with zero references). When late results re-enter: re-verify each finding against source BEFORE applying (about 1 in 6 was an outright misread — e.g. an "owner misattribution" that conflated Contract 3's endpoint-state block with a ThrottleBackoffError type defined elsewhere in the same leaf; reject with file:line evidence), then apply the confirmed ones. A finding already covered by your earlier fixes gets marked "already fixed", not re-fixed (the re-fix risk is real: one late patch reintroduced a stale `loop.go:4226` a sibling had corrected to `:4298`).
- **Direct orchestrator fixing beats fixer subagents when the wave is rate-limit-fragile** (2026-09-01, ~40 edits applied in-session across 17 files): sequence root/shared-convention files FIRST so leaf fixes build on corrected ground truth; re-grep the exact target text immediately before EVERY patch in a dir a sibling session is also editing; read each returned unified diff for self-introduced regressions (fence splits, bullet re-indentation, reintroduced stale values) and repair immediately; at the end, spot-check that your EARLIEST fixes still stand. Verification wave = in-session mechanical re-scans (fence parity, line-number corruption, `check_template_compliance.py docs/plans --strict-leaves`) + one fresh verifier subagent briefed with EVERY applied fix and the expected end-state on BOTH sides of each cross-reference.
- **If a sibling session restructures the tree mid-review** (renames/splits leaves — 2026-09-01: tree 01 went 3→4 leaves, `03-resolution-lifecycle.md`→`04-`, new `02-hook-pipeline.md`), verify your fixes survived the rename (grep the fixed content in the renamed files), then sync every DERIVED surface: forest-root leaf-count row, dependency tables, cross-references to the old filenames, and any tracking table row counts. Count claims drift the moment leaves move.
- **Changelog vs actual code**: A changelog entry may claim implementation but the code may not exist yet (work-in-progress). Always verify on disk.
- **Headless tests cannot verify shaders**: compute/fragment .glsl is never compiled in `--headless` GUT runs — a tree can be "all green" and still ship a shader that fails pipeline_create at runtime (silent feature-off). When a review covers shader edits, grep the shader source for stale identifiers (half-done renames) and require a named in-game smoke gate.
- **Orphan APIs pass review**: grep every new public setter for production callers. Tests that exercise an API directly make it LOOK wired (2026-08-16 tree-24 review: `set_fog_tier()` had zero production callers — the render-side tier contract was never applied in-game; fixed by wiring through the single-writer resolver). Generalized 2026-08-30 into a full wiring-audit checklist in the `plan-leaf-validation` skill: pure functions with zero callers, hook FIELDS with zero writers (a test setting the field itself hides the gap), two-sided join-key checks (filter reads a key producers never write), and cap/clamp constants that can never fire under DefaultConfig weights.
- **Delegation timeouts leave partial work**: a timed-out/interrupted subagent may still have written files (or even still be running) — check `git status` + file mtimes, not just the delegation status message. Re-dispatching blind races two writers on the same file; for trees ≤6 leaves, direct orchestrator implementation beats re-rolling delegation.
- **Continuation dispatch beats restart** when an implementer died mid-TDD: the surviving RED-phase artifacts are usually GOOD (tests written first). Inspect them (`git status`, cat the tests), then dispatch a continuation agent scoped to "GREEN phase only — do NOT modify existing tests". Two failure modes found 2026-08-22: (a) the dying agent leaves a broken workaround hack for a genuinely self-contradictory spec/test — e.g. a "lenient first load" module flag to paper over one test expecting an entry present while another expects load() to raise on it; fix by splitting the fixture (valid entries in `<name>.yaml`, invalid entry in its own `<name>-broken.yaml`) rather than adding leniency to production code; (b) half-finished edits with unbound names — run `ruff check` + pytest before trusting anything the interrupted agent left.
- **Subagents running repo-wide `ruff format .` mangle markdown code fences** inside plans/*.md / docs/*.md — re-indents comment-aligned contract blocks and breaks pipe alignment in fenced YAML/python blocks. Always instruct leaf agents to scope formatters to code dirs only (`uv run ruff format src tests`). After every leaf lands, run `git diff --stat plans/ docs/` before committing; revert plan-doc churn with `git checkout -- plans/`.
- **Parallel leaf dispatch needs explicit file-ownership boundaries** (2026-08-22 branch-02 run): name each implementer's owned files in its dispatch context and forbid shared files (`__init__.py`, `__main__.py`, Makefile). Have each leaf register contributions from its OWN module (e.g. `ingest/regulatory.py` calling `register()`), then wire imports into shared entry points yourself at merge time. Pre-decide contract extensions two leaves both need (e.g. adding a `skipped` statuses key to a manifest schema) and assign exactly one owner — otherwise both patch it and collide.
- **Fixture-based integration smoke replaces live smoke when credentials are absent**: stage committed fixtures into a temp raw-store tree shaped like production layout, run the real pipeline + DB build, assert per-source counts >0, PK uniqueness, view ≤ total rows, and rebuild determinism via content-hash comparison across two full rebuilds (delete DB → rebuild → same hashes). Record "live smoke pending API key" in the tracking note rather than blocking COMPLETE.
- **Orchestrator finishing subagent work is normal, not failure** — but log it: update the branch Completion Tracking table rows with leaf commit hashes, iteration counts, and what the orchestrator repaired (e.g. "timeout post-work; lint fixes in-session; <hash>"), and mirror the row into master.md. Future sessions need to know which code was agent-written vs orchestrator-finished.
- **Common repair classes when finishing interrupted leaf work** (all hit 2026-08-22 branch-02): injected-clock workers must advance `now=` per `run()` call or second runs collide on run_id (duplicate-manifest raise); pyarrow `Table.take([])` on an empty table with null-typed columns raises ArrowNotImplementedError — guard sort-take paths with `num_rows > 0` and write the empty table directly; test stub transports return response-like objects where real clients parse JSON, so workers should normalize (call `.json()` if callable); generic auth_param names from source config ("api_key") need env-var mapping via injectable secret_lookup ("CONGRESS_API_KEY"); module-level worker registration must be fault-tolerant — skip + warn on missing secret rather than breaking module import.
- **WorldSpec→NPC identity gap**: A known open item in tree 10-procgen — WorldSpec emits spawn specs without npc_id; sim generates NPCs independently via `identity.Generator`. Offset of 1,000,000 avoids collision.
- **Stage 1 terrain deferred**: `WorldSpec.Terrain` remains zero-valued; no `stage1_terrain.go` exists. This is intentional deferral, not a bug.

## Reference Files

- `references/procgen-checklist.md` — Procgen pipeline completeness checklist with open items and test counts
- `references/markdown-table-repair.md` — fix structurally-corrupt tracking tables (wrong pipe counts, embedded `|` in prose cells, grafted columns, missing cells). Scan pipe counts programmatically, classify the failure mode, splice cells surgically, re-scan clean. Use when a hand-edited build-plan-index / tracking table has mis-aligned columns or a row looks "merged".
- `references/docs-only-tree-audit-fix-pass.md` — full audit→fix→verify playbook for DOCS-ONLY plan trees (no code yet): parallel audit subagents with MAJOR/MINOR + concrete-proposed-fix output, cross-branch producer/consumer contract matrix, fix master/authority files first then parallel branch fixers. Includes the recurring defect-class checklist (status tables lagging disk, decisions not propagated to master OQs, exit-code vocab drift, parallel leaves editing one shared file, …).

- `references/subagent-branch-execution.md` — field notes from executing a 6-leaf branch via subagents (timeout calibration, dispatch context template, parallel-leaf coordination patterns, repair classes for interrupted output, credential-free integration smoke).
- `references/llm-resilience-forest-tree05-audit-2026-09-01.md` — tree-05 catalog pre-dispatch audit (5 majors + 4 minors): homonym config-key trap, nonexistent enum value vs copy-instruction, misstated precedent, invented validation precedent, wrong external API field name, nonexistent Modify: doc paths, false disjoint-file concurrency claim.
- `references/llm-resilience-forest-root-audit-2026-09-01.md` — root/sibling-doc audit evidence (master.md, DECISIONS.md, SHARED-CONVENTIONS.md): 3 ship-blocking majors in the files every dispatch reads.
- `references/citation-sweep-llm-resilience-forest-2026-09-01.md` — full file:line citation drift table (~94 cites: accurate/drifted/wrong/stale-concept verdicts per cite).
- `references/llm-resilience-forest-trees-01-03-04-audit-2026-09-01.md` — fifth-pass full-forest audit (trees 01/03/04 + 02 leaf 04): 3 blockers (dead RunPrepareNextTurn dispatch pipeline, ResolveRef duplicate-method collision, cross-alias shared-fate state on per-alias struct) + 5 risks (one-shot-override budget shrink, host-key over-block, wiring-time-only precedent writes, enqueue-site session provenance, undeclared RawMessage payload encoding).
- `references/concurrent-forest-review.md` — playbook for reviewing a plan forest while a SIBLING agent session edits the same tree, and for dispatching multiple tree orchestrators concurrently: sibling-edit signals (mtime drift, patch warnings, leaf renames), re-read-before-every-patch discipline, disposition-late-findings workflow, per-tree file-ownership carve-outs for shared files, stagger/hold rules, final-sweep authority.
- `references/leaf03-recovery-sse-scanner-2026-09-01.md` — recovering a half-done leaf from an interrupted orchestrator: WIP validation by invariant-grep, the four-probe diagnosis of a latent SSE scanner bug (data-with-EOF + chunk-boundary byte loss → empty streaming parses), collateral test-deletion repair, concurrent-stash hygiene.

## Completion Criteria Checklist

A plan tree reaches COMPLETE when ALL of:
- [ ] All implemented stages have corresponding source files on disk
- [ ] Unit tests exist and pass (determinism verified)
- [ ] No TODO/FIXME/stub markers remain in implementation
- [ ] Integration with sim/engine is wired and tested
- [ ] GDD spec sources checked against changelog — no drift, or drift is documented and resolved
- [ ] Build-plan-index Implementation Record updated with date, agent, drift status
