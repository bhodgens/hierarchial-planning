# Ddirect single leaf execution
When to use: dispatched onto ONE leaf as implementer.
Lesson: leaf-doc guardrails as contract, TDD RED evidence, verbatim contract sourcing, no-commit rule.

# Direct single-leaf execution (implementer role)

When the dispatch puts YOU on one leaf — "Implement ALL tasks from
<leaf>. Do NOT commit." — the leaf doc's own guardrails replace the
orchestration loop. Distilled from the transcript-large-corpus leaf 03
execution (catalog-test TDD + skill rewrite + two workflow docs), which
landed clean first pass with zero re-dispatches.

## The guardrails ARE the contract

Leaf headers carry hard constraints that override orchestrator habits:

- "Do NOT commit" — the orchestrator owns all git after review. Never
  `git add` either; leave the worktree dirty and report.
- "Do NOT use read_file on existing source files — explore with
  search_files or terminal cat" + "after writing, do NOT read it back
  to verify — write once and stop." Context-budget discipline for
  parallel leaves; the patch tool's returned diff IS the verification.
- "Concurrency Group A — another agent concurrently edits X and Y. Do
  NOT touch any .go files." The leaf's named test file is yours even
  when it is .go; the exclusion scopes to production code. Read the
  carve-outs literally.

## TDD ordering is leaf-mandated, not stylistic

For test-covered rewrites: patch the test FIRST to assert the new
markers — keeping EVERY pre-existing assertion (they are the contract
for what must survive the rewrite) — run it, and capture the RED
output as evidence (exact failure lines). Then rewrite the target,
then run to GREEN. Add a negative assertion too: assert the OLD
phrasing is GONE (e.g. body must not contain "40k"), not only that
new markers exist. Note: if the old test never asserted the old
phrasing, "replace the old-chunking assertion" is vacuous — the new
marker assertions + a negative guard fulfill the intent.

## Source verbatim contract text from the plan docs, not the leaf's summary

When the leaf says docs must "match the leaf-01/02 contracts
verbatim", grep master.md's Interface Contracts section AND the
sibling leaf docs for exact strings (error messages, result-map keys,
write modes, caps, window sizes) BEFORE authoring. The leaf's prose
summary is lossy; contract blocks are normative. Some details live
ONLY in sibling leaf task lists, not in master. Grep by content
(`chunk_count`, `0o644`, `4000`, `summarize_enabled`), not by trust.

## Repo-wide grep gates collide with plan self-references

A gate like `grep -rn "40k chunks" docs/ config/` — zero hits — will
hit the plan docs themselves: docs/plans/... quotes the phrase in
order to mandate its removal. Do not scrub the plan docs (they are
the spec record) and do not silently pass a failing gate either.
Adjudicate by deliverable surface: run the literal gate, note its
hits, re-run scoped to shipped surfaces (docs/workflows/, config/) —
those must be zero — and report the judgment call under
"Deviations" with one line of reasoning. The orchestrator owns the
repo-wide enforcement at integration.

## Sibling-write warnings are advisory — adjudicate with git diff

In a shared worktree, patch/write tools emit
"_warning: <file> was modified by sibling subagent ... this agent
never read it". That is a heads-up, not proof of collision. This
session all three writes warned while `git diff` showed ONLY the
agent's own hunks. Protocol:

1. Do not overwrite blindly — but do not redo work either.
2. `git diff --stat <file>` + read the diff: if every hunk is yours,
   proceed (the warning fired on stale mtime/state, not content).
3. If foreign hunks appear, STOP and reconcile per the collision
   protocol (see sibling-plan-execution-collision.md — read-before-
   write, one writer per file, flag loudly).

Adjudicate per-file at the moment of the warning; a blanket re-read
violates the leaf's no-read-back rule for no benefit.

## Additions from leaf-01 execution (file-backed transcript output, same tree, 2026-09-06)

- **t.TempDir() once per distinct dir.** Table-driven fixtures that call
  t.TempDir() inside both a config field and the `want` value get two
  different temp roots and fail with baffling path mismatches. Hoist to
  named vars BEFORE the table literal.
- **"Omitted when not given" result-key contracts need an explicit
  absence test** (`_, has := m["path"]; if has { fail }`). Seeding the
  map with `"path": ""` passes every value-equality test while violating
  the contract — only the absence assertion catches it. Build result
  maps conditionally, not with empty-value defaults.
- **Contract-shaped strings get full-string equality tests, not
  strings.Contains.** The pointer-line suffix lost its leading "\n" on
  the first pass; only exact equality against the spec'd
  `text + "\n...[full transcript at <path>]"` caught it. Same failure
  family as leaf-verbatim-contract-messages.md: byte-level composition
  is invisible to substring checks.
- **Reuse-don't-copy hits unexported walls.** config.expandPath is
  unexported, so "~ expansion" reused the nearest in-package precedent
  instead (os.UserHomeDir in media_client.go resolveMediaOutputPath).
  When the leaf says "find the helper; reuse, don't copy", grep for the
  closest in-package consumer of the pattern and mirror it.
- **Plan-decomposition gaps get flagged, not silently filled.** This
  leaf added TranscriptConfig.FallbackOutputDir but the daemon
  registration threading (components.go) was outside scope ("no config
  wiring" clause). Make the contract hold regardless (tool-side default
  equals the config default) and flag the unowned wiring line under
  Deviations for the reviewer — one leaf must eventually own that line.
- **LSP diagnostics can be stale mid-flight in shared worktrees**
  (phantom "undefined: X" right after a sibling touched the file).
  `go build <pkgs>` is the arbiter of compilability, not editor LSP
  state; re-check with the compiler before diagnosing.

## Additions from leaf-3.2 execution (openbot-parity, 2026-09-09)

- **Formatter runs on shared files violate hunk ownership.** "Own ONLY
  the added call lines" also means do NOT reflow neighbors — but
  `ruff format` reflows pre-existing lines wholesale. Protocol: run
  the formatter, then `git diff <file>` and REVERT every reflow of a
  line you don't own (restore original wrapping); your own added
  lines stay formatted. Remaining `format --check` deviations: `git
  stash`, run the check at HEAD, `git stash pop` — if HEAD fails the
  same check, the deviation pre-dates you; note it, don't fix it.
  Prove ownership with `git diff | grep '^-'` empty (purely additive).
- **Attribute foreign worktree state via HEAD, never assume.** A dirty
  hunk in a shared test file (leaf 3.1's uncommitted
  `test_scheduler.py` job-set fixup) can predate your session —
  stash/pop round-trips preserve it. `git show HEAD:<path>` tells you
  whether the committed source accounts for it (job registration was
  committed; the test fixup wasn't). Report it flagged as "not mine,
  left untouched"; never commit, revert, or "fix" foreign WIP.
- **Error-path writes die to dependency rollback.** With a commit-on-
  success / rollback-on-exception `get_db` dependency, an audit/
  ledger write inside a route's `except` block followed by `raise
  HTTPException` is SILENTLY DISCARDED. The leaf's added lines need
  an explicit `db.commit()` after the write, before the raise — and
  the proving test must read through a SEPARATE connection to prove
  the row survived. (Details + test recipes:
  python-test-suite-authoring skill,
  references/humanplusone-audit-endpoint-coverage.md.)

## Additions from classifier-outcome-loop leaf 03 execution (2026-09-10, Go/metrics outcome capture — clean first pass)

- **The leaf's Interface-Contract block beats the leaf's own prose.** The
  test-scenario prose ("second resolves 'ok' when the third lands on the
  same agent") contradicted the leaf's normative SQL contract (each
  dispatch resolves its IMMEDIATELY PRIOR row — review→code is a
  different-agent pair, so both prior rows resolve 'corrected').
  Implement the contract, pin the prose's intended case (same-agent 'ok')
  in a dedicated test, and report the discrepancy as a deviation. Same
  family as leaf-verbatim-contract-messages.md: normative blocks are
  authoritative over paraphrase, even when the paraphrase is in the same
  leaf doc.
- **Your leaf can invalidate a PRIOR leaf's pinned assertions — update
  the stale sibling test.** Leaf-01's test asserted "all rows pending";
  leaf-03's Signal A deliberately changes that. The move is: update the
  sibling test to the new contract with a comment naming the leaf that
  changed the behavior ("Was 'both pending' under leaf 01") — never
  revert behavior to keep an old test green, and never leave the suite
  red. Cross-leaf test evolution is expected in a tree, not a collision.
- **sqlx maps untagged struct fields by lowercased name only, never
  snake_case** (`AgentID` → `agentid`, which does not match column
  `agent_id`): runtime failure "missing destination name agent_id".
  Any `db.Get`/`db.Select` into a local/anonymous struct needs explicit
  `db:"snake_case"` tags on every column — compiler and go vet cannot
  see it; only running the query does.
- **Forcing a failure path: nil deps can panic before reaching the error
  return the leaf assumed.** `planSinglePhase` with a nil registry
  SIGSEGV'd inside `registry.Get` instead of returning "planner agent
  not available". Reach the intended fallback with an empty-but-non-nil
  construct instead (`NewAgentRegistry(RegistryConfig{})` with no
  planner spec registered → clean "agent spec not found" error). Also:
  same-package tests may assign unexported fields directly when no
  setter exists (`ts.escalationManager = NewEscalationManager(...)`) —
  don't add production setters just for tests that share the package.
- **A leaf-cited wiring point can predate the dependency's existence.**
  "Wire it at the same point leaf 02 used" pointed inside NewComponents,
  where the metrics store doesn't exist yet (components are constructed
  before daemon.go creates it). Actual wiring belongs in daemon.go's
  post-construction metricsStore block — which may require new
  accessors (Orchestrator.Tactical() didn't exist; added mirroring
  Strategic()) and a nil-guarded setter on the second component
  (StrategicPlanner.SetMetricsStore — its config field alone can't
  cover late wiring). Before copying a cited wiring pattern, verify that
  site can actually SEE the dependency; note setter/accessor-name
  deviations in the leaf report (the leaf's Deviations clause expects
  them).
- Leaf-doc line numbers drift (cited tactical.go:1440 → actual ~:1629,
  dispatcher.go:3024 → :3099): grep by symbol/content as usual
  (pre-dispatch-drift-and-baseline.md), but also grep the callsite's
  enclosing condition — "at the Escalate call" meant INSIDE the
  `escalationManager != nil` block, not after it — hook placement
  changes which invocations fire, and tests pin the difference.

## Python single-leaf TDD addendum (2026-09-11, classi-fly connectome-ingest leaf 02 — clean pass, 37 tests)

The leaf directives are language-neutral; the mechanics differ from Go:

- **Python sibling modules don't import by default under pytest.** Go
  leaves get the package system for free; Python test files importing
  sibling modules (`from larval import ...`) only resolve because of
  cwd. Ship a `conftest.py` that prepends the leaf dir to sys.path, so
  `python3 -m pytest tools/<leaf> -q` passes from any cwd.
- **Batched write_file calls can cross content and path.** Two writes
  issued in one batch landed as (a) module A's content under a stray
  non-repo path and (b) module B's content overwriting module A.
  Detection is free: every write result carries resolved_path + lint
  status — READ them before moving on. A lint error naming content you
  didn't intend, or a resolved_path outside the repo, means stop and
  rewrite the target in full in a follow-up call (the corrupted file
  still passes byte-similar skims; lint is what catches it). Prefer
  one write per batch per file when contents differ per path.
- **License-guard class of leaf (NC-gated source):** central registry
  of exact source/license/attribution strings + a guard() that raises
  unless explicitly acknowledged + every ingest path assembling output
  THROUGH the registry + CLI ack flag (rc=2, error message names the
  flag) + tests for refusal, ack, and unknown-source KeyError. Exact
  strings come from master's frozen Contract block, tested verbatim —
  same discipline as leaf-verbatim-contract-messages.md.
- **Network-gated CLI leaves: default is dry-run (rc=0, no file); the
  real query lives behind --live.** Keep the network import (urllib)
  LOCAL to the fetch function so no test can even load it; tests cover
  transform-on-fixture + dry-run-only. The leaf Notes gate real
  downloads behind an open question — respect it, fixtures only.
- **Environment check once, up front:** python3/pytest versions + ruff
  presence. Leaf gates phrased "clean if present" mean skip when
  absent — never install software mid-leaf to satisfy a gate.
- **Denied rm of a stray file is final for the session.** Leave it,
  name the exact path under Deviations, hand cleanup to the
  orchestrator (leaf-side consent-denial propagation; user-denied-probe
  protocol — no alternate-command retry).

## Report shape

End with: what was done per task, files touched, verification evidence
(command + outcome for every gate: test RED→GREEN transcript, grep
exit codes, gofmt), and an explicit "Deviations: none" or the list
with rationale. The orchestrator reviews against the leaf's Review
Checklist — mirror its checkboxes in your evidence so review is a
diff, not an investigation.
