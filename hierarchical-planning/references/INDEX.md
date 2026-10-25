# SKILL.md pointer index (SKILL.md is at the 100K patch-tool limit — the
# refs line cannot be edited in place; new references are cataloged HERE.
# Apply the pending edit whenever SKILL.md is next restructured below 100K.)

## References added since v1.1.0

- post-authoring-audit-trio.md — NEW (2026-09-01, meept llm-resilience-forest):
  the parallel read-only audit trio run AFTER authoring a tree/forest and
  BEFORE dispatching implementation agents — citation-drift audit (every
  file:line anchor vs current HEAD), architecture audit (does the plan's
  mechanism actually exist: production callers, name collisions, state
  cardinality, import cycles), and domain-ambiguity audit (closes "which
  of two implementations is real" conditionals). Includes the
  understanding-first brainstorm arc for feature-list sessions (recon →
  restate understanding with worked examples → user corrections →
  DECISIONS.md D# rows → author → audit trio) and the risk taxonomy every
  architecture audit must probe (one-shot vs persistent effects; join keys
  too coarse; missing provenance fields; untyped payload blobs; error
  classes bypassing the new classifier). Worked outcome: 3 blockers, 5
  risks, 13 drifted citations caught before any implementation agent ran.
- execution-readiness-audits.md — companion: failure-class library from
  the same audit wave (grep-recipe undercounts; same-name/different-surface
  fields; declared-interface vs satisfying-type; two-conversion-site
  pipelines; conditional instructions as unresolved ambiguity) plus
  correction-application mechanics.
- forest-root-scanner-compliance.md — authoring multi-tree forests that
  pass check_template_compliance.py: forest-root master.md needs ALL
  orchestrator sections; sibling .md files (DECISIONS.md,
  SHARED-CONVENTIONS.md, audit records) are leaf-checked and need
  "Do NOT commit" + Self-Verification checklist; per-tree Open Questions
  warning is acceptable when centralized; repairing pre-existing
  non-compliant trees as historical records; scanner skips dot-dirs and
  archive/ (2026-09-01).
- meept-flat-plan-trees.md — UPDATED (2026-09-01): scanner now skips
  dot-dirs and archive/; executing a prior-session tree starts with the
  execution-readiness audits.
- shared-tree-hazards.md — UPDATED (2026-09-04, chat-dispatch-ux): Hazard 1
  addendum — mid-wave, when the only buildable state of a shared file
  includes a sibling session's self-applied hunks (audit session
  self-fixing in scope), hunk-splitting may be riskier than the sweep:
  grep the working diff for foreign markers before staging, sweep the file
  whole, and write a reconciliation flag into the commit message naming
  the hunks' marker IDs and the owning session's ledger doc. Also that
  session measured: pre-commit "build staged packages" hooks fail on
  sibling WIP transitive imports (protocol + wave sequencing for
  shared-file leaves in Hazard 6 territory), `git stash` is forbidden in
  live parallel trees (UU go.sum poisoned all six running subagents), and
  a leaf "deviation" report was the plan's anchor being wrong, not the
  implementer failing — re-verify the anchor in source before judging.
- e2e-leaf-pattern.md — NEW (2026-09-04, meept chat-dispatch-ux leaf 10):
  authoring + executing the tree's e2e leaf (scratch daemon/service, real
  provider, scripted transcript). Budget 3-6 post-green fix runs; failure
  classes each costing a run: scratch config missing a construction gate
  (`if cfg.X.Enabled` around the feature's wiring — logs tell, specs=0),
  "discovering" a lazily-created conversation (bare conversation IDs never
  create session rows), first-match name lookup shadowing the fresh row
  (List is last_activity DESC — take the LAST match), and a `set -u`
  unbound variable masquerading as a provider SKIP (print the provider's
  actual error in every SKIP). Debug recipe: --keep workdir + daemon.log +
  sqlite scratch DB + replies/*.err; build-gate FATALs on sibling WIP are
  correct — retry after `go build ./...` greens, don't rewrite.
- chat-dispatch-reply-contracts.md — NEW (2026-09-04, meept): contract
  notes for agent-harness reply paths — the meept-vs-hermes failure
  taxonomy (stub replies, laundered failures, wrong cwd, context burn,
  machine-shaped replies, quota-as-self-harm) with the fixed seams any
  future reply-path work must respect (RunOnceWithParts assembly order,
  step-Result → reply data flow, FilteredToolRegistry parent-delegation
  for schema mode, cfg.MultiAgent.Enabled gate, session List ordering).
- authoring-pitfalls-from-execution.md — UPDATED (2026-09-04): added
  pitfalls 10-15 from chat-dispatch-ux + session-continuity execution —
  contract text taken literally by implementers (site the fix where it
  CAN satisfy the contract; grep leaf verify-commands for test-name
  existence), anchor precision (pointer-field access paths, construction
  gates nil at cited lines, wrapper types lacking the method), anti-
  findings ("do not change" lines preventing scope creep), e2e/config
  leaves as highest-post-dispatch-bug-rate (plan 2-4 fix cycles),
  authoring-time root-cause claims needing runtime-order gate tracing
  (pre-existing short-circuits above the fix), and plan docs/snippets
  are ENGLISH-ONLY (CJK fragments = defects; scan tree with python
  unicode-class regex before dispatch; repo now has
  .githooks/pre-commit-ascii enforcing this at commit time).
- meept-repo-patterns-2026-09-04.md — NEW (2026-09-04): durable meept
  repo patterns — .githooks house style (16 sub-hooks, /opt/homebrew/
  bash, adding a check), pre-commit-ascii policy (staged-only,
  grandfathering, binary skip, allowlist), test conventions (-p 2,
  flake-rerun discipline, git log -L lint attribution), sibling-session
  concurrency (hooks-bypass-with-note, foreign-hunk sweep commits, go.sum
  conflict recovery, stash avoidance), and the scratch-daemon e2e
  sandbox recipe (config gates, sync-dispatch trigger, honest SKIPs,
  /var→/private/var dual-form path allowlists).
- verify-root-causes-before-followup-trees.md — NEW (2026-09-04,
  session-continuity): subagent root-cause reports are hypotheses —
  re-derive them from source before authoring the follow-up tree. Worked
  example: leaf 03 blamed the ambiguity gate; verification confirmed it
  AND found the sharper fix surface (AnalyzeTrueIntent gets no session
  context; buildMemoryContext output dropped one line earlier), proved
  leaves 01/02 held via --keep sqlite forensics instead of reruns, and
  surfaced the user's architecture principle (user-addressed agents
  QUERY session state — GetTasksForSession/GetLastIntent exist as the
  seam; the session never absorbs agent transcripts) that reshaped the
  design. Simulation of pure decision functions (topic-detector scoring
  replayed in python) settles which branch fires in seconds.
- e2e-script-leaf-bugs.md — NEW (2026-09-04): the recurring first-run
  bug classes for e2e-script leaves (set -u crashes misreported as
  provider SKIPs; scratch config missing construction-gate flags;
  discovery steps for lazily-keyed rows) with the --keep forensics
  recipe (daemon.log grep + sqlite state DBs before touching the
  script) and the correct-vs-misreported SKIP distinction.
- gate-context-digest-pattern.md — NEW (2026-09-04, meept
  session-aware-intent-gate): fixing a gate/classifier that judges
  messages in isolation by passing a compact session-state digest into
  the analyzer call — signature extension with a contextless
  byte-identity guarantee (nil/empty digest → prompt unchanged,
  test-proven), both call sites building the digest BEFORE the
  analysis call, and the user's architecture principle: user-addressed
  agents QUERY session state at turn time
  (GetTasksForSession/GetLastIntent are the seams); the session never
  absorbs agent transcripts. No threshold changes, no keyword lists,
  no new config — the model decides from context.
- meept-skill-authoring-tree-2026-09-06.md — NEW (2026-09-06, meept
  skill-authoring-and-media-ingest): writing leaf contracts against
  REAL code — five contract defects caught at review (wrong Execute
  signature vs interface.go, schema/prose contradiction on required
  fields, invented Writer dedup semantics, stale file attribution,
  assumed config nesting), each with the grep-first prevention rule.
  Plus: scanner/anchor/CJK authoring-time checks, subagent-delegated
  multi-tree scanner fixes, and the verify-a-sibling-executed-tree
  protocol (trust tracking tables only after re-verifying contracts
  against HEAD; the Deviations column is the honest map of which
  contract clauses are not in force).
- schema-migration-leaf-sizing.md — NEW (2026-09-06, meept→tokscale
  ingest tree): two leaf-sizing rules born from "leaves green, two
  production bugs." (1) A schema-migration leaf is NOT done when the
  suite is green — fresh-install tests prove nothing; require a
  legacy-fixture migration test (old schema + real rows → Store opens,
  columns/indexes exist, rows survive) and one live e2e verification
  task in the leaf's task list; ALTERs before index creation. (2) A
  data-contract pin test at the store layer cannot see a wiring gap one
  level up (the interactive path that never passes the field) — require
  full-write-path caller-chain grep, per-shape fixtures, and
  count-parity assertions. Cross-linked to the execution-side recipe in
  hierarchical-plan-execution references/live-db-migration-and-ingest-
  contracts.md.
- same-package-type-dependency-waves.md — NEW (2026-09-06, meept
  plan-compiler tree): parallel leaves with type dependencies —
  type-producer + type-consumer CAN share a wave when the plan pins the
  full struct definitions (frozen fields + JSON tags restated in the
  consumer's leaf doc, not pointed at); consumer codes against the
  contract blind, reports STOP with an error-class enumeration (all
  errors must be exactly the expected undeclared names), and the
  orchestrator's post-wave build is the only gate needed. Includes the
  dispatch-context template, the "header-stub alone?" sequencing
  decision rule, and the verify-with-your-own-golden review technique
  (compile the shared spec's normative example before committing either
  leaf).

## Pending SKILL.md edit (apply when SKILL.md is next restructured below 100K)

In "Skill Package Contents → References (read for deep guidance)", change:
  `- See \`references/\` for additional pattern guides on wave execution, gap analysis forests, bulk leaf generation, audit-driven planning, and more.`
to:
  `- See \`references/\` for additional pattern guides — incl. post-authoring-audit-trio.md (parallel citation-drift/architecture/ambiguity audits, run after authoring before dispatch), execution-readiness-audits.md, forest-root-scanner-compliance.md, meept-flat-plan-trees.md.`
