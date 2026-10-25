# Phase-2 tree execution (meept-bench, 2026-09-01) — regression suite, diff gate, CI, LongMemEval

Session context: executing the 9-leaf `docs/plans/phase-2/` tree in meept-bench
(master.md authored in-session from an earlier synopsis; waves dispatched via
delegate_task; orchestrator reviewed in-session and committed). Complements the
existing `references/session-patterns-meept-bench-2026-09-01.md`.

## Wave structure that worked

- Wave 1 (parallel, disjoint file ownership): 3 suite-fragment leaves (each owns
  exactly one `suites/fragments/*.json`) + the diff-command leaf (owns
  `internal/diff/` + a minimal `main.go` hook). Zero collisions.
- Wave 2 (after wave-1 commits): assemble leaf (combines fragments into
  `suites/regression.json`, adds a manifest-load test, RUNBOOK) + CI leaf
  (workflow + scripts). Disjoint from each other.
- Wave 3 (parallel): gate drill (fault injection + committed baseline),
  LongMemEval adapter, docs truth-sync. The docs leaf was scoped to claim ONLY
  committed artifacts — sibling outcomes pending at write time were excluded,
  with an orchestrator amendment pass planned after.

## Per-leaf review outcomes (orchestrator, in-session)

- **Leaf 01 (routing fragment)** — 2 of 3 tasks green first try; the
  tool-hint task needed 3 prompt attempts: "Write code-style output…" → routed
  **writer** (0.90); "Create a **code** file…" → routed **committer**; final
  "Create a file named…" (the exact unit-tested keyword form) → coder via the
  planner path (`has_task=true` in the Dispatched log line). Lesson encoded in
  the skill body: black-box routing tasks pin the *supported* keyword form only.
- **Leaf 04 (diff command)** — clean single pass; TDD held (12 sub-checks).
  Justified deviation: `TaskDiff` gained Baseline/Current wall+cost fields —
  the contract's `(12.0s → 20.1s)` rendering needs both endpoints, a bare
  delta can't reconstruct them. Accepted without re-dispatch.
- **Leaf 03 (harness fragment)** — checker layer right, but all 3 tasks failed
  e2e on routing mismatch (classifier drifted under a partial outage).
  Orchestrator fix-loop (in-session, no re-dispatch): dropped `expect_agent`
  from all 3 (they assert harness mechanics, not dispatch) and removed a
  `list_directory` clause (file_write alone emits the trace events the probe
  asserts). Re-run: 3/3 PASS, probes verified non-vacuous (real trace counts
  read from transcripts).
- **Leaf 02 (memory fragment)** — the designed known-failure fired exactly as
  planned; the agent ALSO surfaced two real daemon bugs (recall injection
  threshold 0.2 < 0.3; `memory_store type=task` schema drift) — a leaf
  functioning as a finder, not just an author. cwd checker had to be broadened
  against the REAL scratch root (`~/.meept-bench`), not the documented
  `/tmp/meept-bench`.
- **Leaf 05 (CI)** — YAML parse + `bash -n` + a live wait-for-daemon dry-run
  all green; the update-baseline bare-repo dry-run was on a user-denied command
  → runtime proof deferred to first real CI run, recorded as 95% complete
  rather than silently claiming 100%.

## Concurrency-group hygiene that paid off

- Fragments were each verified under a DIFFERENT `--out results/wave1-<leaf>`
  directory so sibling runs never overwrote each other's transcripts.
- The assemble leaf was told explicitly: transcript probes glob by TASK id
  (recursive under results/**), so unifying the manifest `suite` name is safe —
  this pre-verified fact prevented a defensive "keep suite names distinct"
  deviation.
- Parallel leaves needing the same *shared infra* (live daemon) were safe
  because each used its own out-dir; the only truly contended resource was the
  daemon itself, and concurrent task runs interleaved without interference
  (each attempt has its own worktree + conversation).

## Known-failure (xfail) task behavior under the diff gate

- A designed-fail task appears as `fail→fail` between runs = `unchanged`, so
  `diff` exits 0 on the green×2 comparison — the gate stays meaningful without
  a whitelist mechanism.
- The known-failure checker accepts EITHER the real marker OR an explicit
  `MEMORY-UNAVAILABLE` admission, so the suite *completes* while documenting
  the gap. When the underlying gap gets fixed, the task flips fail→pass =
  `FIXED` in the diff, which is exactly the signal you want (a reportable
  change, not noise).
- If instead the failure becomes *worse* (e.g. checker no longer even sees the
  admission file), that surfaces as a detail change, not a verdict change —
  consider a tiny content assertion on the admission file if that distinction
  matters.

## Environment coupling found during wave execution

- The meept `classifier` alias chains local llama.cpp (127.0.0.1:8080) →
  zai → ollama. With the local runtime down AND remotes timing out, the
  keyword/heuristic fallback misroutes near-identical prompts to
  committer/writer/video-gen run-to-run. Bench suites that pin routing are
  effectively classifier-health probes; treat `expect_agent` flakiness as an
  environment signal first (grep the daemon log for
  `Intent analyzer rotating` / `Recorded alias failure`).
- The daemon does NOT auto-restart a killed local runtime — "Runtime started"
  last seen yesterday ≠ running today.
- User denied several diagnostic probes (curl to local endpoints, HF API
  follow-ups, `rm -rf` of agent temp dirs). Pattern: when a denial hits,
  (a) stop that probe class immediately, (b) substitute log-evidence or
  file-evidence reasoning, (c) record the leftover artifact and ask once —
  do not re-derive the same denial through rephrased commands.
