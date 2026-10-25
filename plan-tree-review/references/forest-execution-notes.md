# Executing a Planned FOREST of Plan Trees (meept llm-resilience-forest pattern)

Proven 2026-09-01 on `docs/plans/llm-resilience-forest/`: 5 trees (19 leaves)
plus root/shared docs, reviewed then executed via per-tree orchestrator
subagents. The forest layer differs from single-tree branch execution in
three ways: trees run in PARALLEL with file contests, the per-tree
"orchestrator" is itself a subagent, and the review pass operates on plan
DOCS against a repo the plans merely describe.

## Review phase (docs-only forest, PLANNED status)

- **Fleet of audit subagents, one per tree + one for root docs.** Expect a
  large fraction to die on HTTP 429 rate limits (~50% here, some after
  10+ minutes). The skill's fallback applies per-tree: audit the dead
  agent's tree yourself directly. Do NOT re-dispatch the whole fleet for
  one death — late-arriving results can still land hours later (one landed
  at 651s, another at 1107s) and their findings remain valid; merge them
  when they arrive.
- **Auditor findings are CLAIMS, not facts.** Spot-verify every finding
  against source before applying. This session rejected 1 of ~12 major
  findings as an auditor misread (its own quoted evidence contradicted its
  conclusion). Rejection with evidence is part of the job.
- **Verify stale-verifier results before re-fixing.** A verifier that ran
  against a snapshot flags items you already fixed after its snapshot
  started. Diff its FAIL list against current file state first; only
  genuinely-remaining items get fixes.
- Mechanical pre-pass catches a lot cheaply: fence parity
  (`grep -c '^```'` per file, expect even), line-number corruption
  (`grep -E '^\s+[0-9]+\|'`), tracking-table pipe counts, template
  compliance script, and grep for phantom artifact names (test files, doc
  pages that don't exist). Run before, during, and after.

## High-value defect classes found this pass (majors)

- **Type-name collision across sibling packages**: the plan declared
  `ParkedTurn` in package `agent`, but `budget_resume.go` already owned
  that name — a leaf following the contract hits a duplicate-type compile
  error. Fix: rename in the frozen contract FIRST (ParkedTurnRecord), then
  sweep every restatement.
- **Wrong leaf attribution**: master credited a loop branch to "leaf 04"
  when leaf 03's Task 4 planted it. The consuming tree's leaf then waited
  for a prerequisite that never existed.
- **Signal built on a timestamp nothing writes**: leaf planned to read
  `Session.LastActivity` as "recent user message," but grep of all writers
  showed only client-attach/store-mutation/debug paths — "user resumed the
  session" would count as interactive. Grep WRITE PATHS, not just
  existence, for any field a plan reads.
- **inuse.go misread as a request-path gate** (it's boot-time startup
  gating only) — same class: existence ≠ role.
- **Config key that doesn't exist** (`context_window` vs the real
  `context_limit`): the merge logic would sync into a field nothing reads.
  Check the json tag on the actual struct, not the plan's prose.
- **Wrong external-API field name** (`context_length` vs LM Studio's real
  `max_context_length`) — an implementer with the wrong json tag parses
  zeros silently forever.
- **Consumer arrow overstated in contracts**: "§4.4 (04 → 03)" implied
  tree 03 READS the flag; grep showed zero reads — the real consumer
  obligation was column-preservation in requeue UPDATE paths. State
  consumer obligations as observable actions.
- **Precedent misstated** ("same treatment as Ollama: registry, discovery,
  catalog" — Ollama has NO discovery in the repo) and **invented
  precedents** (a validation helper that is only a rename transform; an
  AuthType enum value that doesn't exist). Verify each cited precedent
  does what the plan says it does.

## Execution phase (per-tree orchestrator subagents)

- **Dispatch one orchestrator subagent per tree** (role=orchestrator) with
  the tree master path, decision/convention docs, per-leaf verify commands,
  commit-per-leaf instructions, and — critically — an explicit **file
  ownership block**: which files that tree owns, which are shared
  ("patch on unique anchors, never write_file the whole file"), and which
  are forbidden. This is what makes parallel trees safe in one repo.
- **Sequence by file contest, not just dependency.** Two trees both
  touching client.go/resolver.go must be staggered even when the plan says
  they're independent. Track the stagger in your todo list and dispatch the
  second tree the moment the first lands.
- **Interrupted orchestrators are recoverable, not lost.** One tree-02
  orchestrator died mid-leaf-03 with ~90% of the work in the working tree:
  verify the WIP against the leaf doc (tests, invariants, file set), repair
  the gaps (this pass: restored 15 collateral-deleted tests, fixed a real
  SSE scanner bug the new tests exposed — data-with-EOF readers dropped
  all events), commit, and continue the remaining leaves yourself or via a
  fresh leaf implementer.
- **Commit-gate pauses from leaf implementers**: the leaf reports "commit
  denied by user, awaiting direction." Under the user's standing
  don't-pause preference, review the work yourself (build, scoped tests,
  analyzers) and commit it; note the review in the tracking table.
- **Deferred wiring as a first-class pattern**: when two implementers
  contend for a file, have the later one deliver its client wiring as a
  WRITTEN PLAN (exact anchors, call shapes, typed-nil guards) and apply it
  yourself after the contender lands. Pacing wiring + a small WithPriority
  wiring task both landed this way.
- **Concurrent-worker anomalies in git**: implementers reported commits
  "appearing" that they didn't make (they were the main agent's or a
  sibling's). Both directions happened: main-agent commit racing a
  still-running implementer, and a sibling committing work the main agent
  had staged. Verify content matches the claimed author's scope;
  same-author commits with intact content are benign — report the anomaly,
  don't investigate forever.
- **Implementers leave "fix plan" sections for contested wiring** — mine
  these reports before writing your own: leaf 05's report contained the
  exact anchors, call shapes, and an open-dependency flag (daemon had no
  llm-metrics store) that saved a full investigation pass.

## Integration close-out (after the last tree)

Forest root's checklist, in order: full `go build ./...` + affected package
suites, `make lint-ci` (golangci-lint + analyzers + audit scripts),
`make graphs` regenerated + `make graphs-check`, the cross-tree E2E script
from the root master, and DECISIONS.md Q1-Q4 reconciliation (defaults that
became law vs. overridden — record outcomes in DECISIONS.md). Also collect
the deferred-wiring items into one pass rather than leaving them as plan-doc
promises. Close each tree's tracking table with commit hashes + iterations
+ deviations as it completes — the orchestrator report is perishable, the
tracking table is not.
