# Addendum A: Leaves 07/08 Wiring Audit (2026-08-30, second pass)

Follow-up to the first-pass report (restored at the bottom of this file).
Read-only audit
of leaves 07 (shadow-honesty) and 08 (trajectory-judge) in the pristine
worktree `/tmp/meept-harness-audit` (HEAD 5d31b720, clean).
`go test ./internal/{eval,shadow,selfimprove}` — all green with -race.

## Verdicts

- Leaf 07: **PARTIAL** (tasks 1-3 wired; task 4 buggy under defaults)
- Leaf 08: **PARTIAL** (judge + persistence live; promotion gate unwired)

## Leaf 07 findings

| Task | Verdict | Evidence |
|---|---|---|
| 1. Cost uses real tokens | WIRED | `internal/shadow/teacher.go:360-367` — `(PromptTokens*CostPerMillionInput + CompletionTokens*CostPerMillionOutput)/1e6`; `recordUsage` feeds `response.Usage` (teacher.go:373). Pinned by `TestTeacherClient_CostUsesRealTokenCounts` (teacher_test.go:31). |
| 2. Dedup threshold | WIRED | `exporter.go:162,221,278,346` → `newDedupState(e.config.DedupSimilarityThreshold)`; hash short-circuit first (:473-476); near-dup gated `if d.threshold > 0` (:487). Plumbed schema.go:2088/2686 → daemon components.go:4788 + CLI shadow.go:880. Default 0.95 (config.go:220). |
| 3. Quarantine auto-train | WIRED | No ticker/goroutine exists in shadow Manager (no Start, no autoTrain fields); warn-only at manager.go:148-152; structural-absence tests in manager_autotrain_test.go:15-40. Shadow `Trainer` (unsloth/axolotl/trl) constructed ONLY from CLI `cmd/meept/shadow.go:638` — never in daemon. NOTE: daemon runs a SEPARATE `learning`-package LoRA auto-train (components.go:5705 `go processPendingAutoTrains`), gated by `learning.training.manual_only` defaulting TRUE (schema.go:2615) — not a shadow violation. |
| 4. Scorer length trap | PARTIAL | Oracle hook exists (scorer.go:137-143) and completeness cap exists (scorer.go:66,154-156), BUT: (a) cap constant 0.3 vs default completeness weight 0.25 (config.go:197) — cap can never fire under DefaultConfig, dead in production; (b) heuristic correctness base is 0.7 (scorer.go:236), not the leaf's "conservative 0.5"; (c) `TestScorer_LengthTrap` holds only because the test itself sets `EvalPassed`, which has zero production writers (grep: only models.go:86-90 definition + scorer.go:137-138 read + scorer_trap_test.go sets). |

Fix shapes: set `maxCompletenessContribution` ≤ default completeness weight
(or scale by configured weight); lower correctness base to 0.5 per leaf or
wire a production writer for `EvalPassed`.

## Leaf 08 findings

| Task | Verdict | Evidence |
|---|---|---|
| 1. Judge + unit tests | WIRED | `internal/eval/judge.go:43-49` matches C7 field-for-field. `Judge` (:118-158): 1-based first failed tool step; `len(steps)+1` outcome-only sentinel; 0 on pass; fail-closed on oracle error (:139-142). All three mandated cases tested (judge_test.go:32-143). |
| 2. Persist judgment on eval run | WIRED (HTTP/RPC) | `comm/http/eval_handlers.go:167-183` `attachJudgment` → `SaveJudgment`, called at :237 (HTTP) and :314 (RPC); registered live at daemon/daemon.go:838 + daemon/eval_rpc.go:32. `replayOracle` (:189-207) replays the run's final recorded attempt — no double-execution. CLI skips (leaf-allowed). Traversal-guarded path judge.go:231-239; `ErrJudgmentNotFound` sentinel. |
| 3. Gate evolver input | MISSING | `OnlyJudged` (selfimprove/judged_filter.go:28) has ZERO production callers — only its own tests. Real promotion path `Evolver.passBPromote` (skills/lifecycle/evolver.go:362-429) filters on UseCount/Confidence/Status/CreatedAt only, never judgments. Same for daemon query components.go:5943 and agent/context_injector.go:180. Compounding: producers `parseDistillResponse` (learning.go:531) and `distillHeuristic` (learning.go:571) never write `Metadata["trajectory_id"]`, so even a wired gate would drop 100% of real patterns. C7 "feed evolver ONLY judged rows" is unenforced in production. |

Fix shapes: in `passBPromote`, load judgments for candidate trajectory_ids
(`LoadJudgment`) and wrap the loop with `OnlyJudged`; stamp
`Metadata["trajectory_id"] = trajectory.ID` at distill time.

## Unwired stubs (exported, zero production callers)

1. `selfimprove.OnlyJudged` — the entire C7 promotion gate
2. `eval.StepsFromMessages` — stored-trajectory→judge-steps adapter
3. `eval.DiskStore.LoadJudgment` — judgments written, never read back
4. `ShadowRecord.EvalPassed` — scorer hook with no production writer

Also noted: judge input for real trajectories requires an external client to
inline `trajectory` steps into `POST /api/v1/eval/runs`; nothing judges
trajectories from the shadow store.

## Addendum A correction to the first-pass report

The first-pass table row for leaf 07 listed
"shadow/classifier.go, eval_gate.go" as key files — those are leaf 04/06
adjacent files, not the leaf 07 task files (teacher.go, exporter.go,
manager.go, scorer.go). The first pass validated the wrong target and
reported PASS. Lesson encoded in SKILL.md: check the leaf's "Files:" lines
map to what you actually inspected.

---

# First-Pass Validation Report (2026-08-30) — superseded for 05/07/08

Original sweep over all 18 leaves from docs/plans/20260829-harness-eval/master.md.
Leaves 05, 07, 08 were later demoted by Addenda A/B; 13/18 PASS stands.

## Results

| Leaf | Status | Key Files | Tests |
|------|--------|-----------|-------|
| 01-eval-core | PASS | record.go, oracle.go | TestShellOracle*, TestRunRecord* |
| 02-eval-cli | PASS | cmd/meept/eval.go, command_eval.go | TestEvalListPayload |
| 03-eval-http | PASS | comm/http/eval_handlers.go | TestEvalRunCreatesRecord |
| 04-coder-gates | PASS | config/agents/coder/AGENT.md | gate.command present |
| 05-verify-breaker | PARTIAL (Addendum B) | agent/tool_breaker.go | Tests pass; ZERO prod wiring |
| 06-shadow-capture | PASS | agent/loop.go:3393, registry.go:390 | shadow_specialist_test.go |
| 07-shadow-honesty | PARTIAL (Addendum A) | teacher.go, exporter.go, manager.go, scorer.go | shadow tests pass; cap dead under defaults |
| 08-trajectory-judge | PARTIAL (Addendum A) | eval/judge.go | judge live; promotion gate unwired |
| 09-trusted-root | PASS | selfimprove/applier.go:390 | denyTrustedRoot, ErrTrustedRoot |
| 10-isolation | PASS | agent/isolation.go | ContextIsolation, BuildSpawnContext |
| 11-speak-router | PASS | agent/speak.go | SpeakKind, ClassifyRun, Deliver |
| 12-memory-facts | PASS | memory/fact_store.go | MemoryFact, Upsert, GetActive |
| 13-status-bar | PASS | agent/status_bar.go | TurnStatus, StatusBar golden tests |
| 14-event-rewake | PARTIAL | scheduler/rewake.go, loop_rewake.go | 1 test fails |
| 15-docs-flags-metrics | PARTIAL | docs/workflows/eval.md | Docs gap |
| 16-tui-parity | PASS | tui/command_eval.go | TestEvalListPayload |
| 17-flutter-parity | PASS | eval_runs_panel.dart (193 lines) | N/A (Flutter) |
| 18-menubar-parity | PASS | EvalBadgeManager.swift (71 lines) | N/A (Swift) |

## Failures

### Leaf 14: TestRewake_JobCompletionLandsInDrain
- FAIL: internal/scheduler (5.587s)
- rewake_test.go:148: timeout waiting for hook.async_rewake publish after job completion
- Other rewake tests pass (TestRewake_SourceIsMetadataNotFilter, TestRewake_PrimaryLoopArmedOnRunOnce)

### Leaf 15: Documentation Gap
- docs/workflows/eval.md exists but contains 0 references to harness-eval concepts
- File describes HALO trace analysis, not the new eval harness

## Verified Contracts

### C1: Eval RunRecord (leaf 01)
- internal/eval/record.go: RunRecord, Attempt
- internal/eval/oracle.go: OracleResult, Oracle interface, ShellOracle

### C3: Speak routing (leaf 11)
- internal/agent/speak.go: SpeakKind, ClassifyRun, Deliver

### C4: Context isolation (leaf 10)
- internal/agent/isolation.go: ContextIsolation, SpawnContext, BuildSpawnContext

### C5: Trusted root (leaf 09)
- internal/selfimprove/applier.go: ErrTrustedRoot, denyTrustedRoot

### C6: MemoryFact (leaf 12)
- internal/memory/fact_store.go: FactKind, MemoryFact, Upsert, GetActive

## Build Status
- go build ./... → BUILD OK
- go test ./internal/eval/... → ok
- go test ./internal/agent/... → ok
- go test ./internal/memory/... → ok
- go test ./internal/selfimprove/... → ok
- go test ./internal/shadow/... → ok
- go test ./internal/comm/http/... → ok
- go test ./internal/tui/... → ok
- go test ./internal/scheduler/... → FAIL (1 test)

## No Debug Artifacts
Searched all implementation files for: TODO, FIXME, print(), fmt.Print
Result: Clean

---

# Addendum B: Leaves 05/06 Wiring Audit (2026-08-30, second pass)

Read-only audit of 05-verify-breaker and 06-shadow-capture against their plan
docs, in the same pristine worktree `/tmp/meept-harness-audit`
(HEAD 5d31b720, clean). `go test ./internal/agent/ ./internal/shadow/ -race -count=1`
→ both ok (18.4s / 3.7s).

## Verdicts

- Leaf 05: **PARTIAL** (task 1 wired; tasks 2-3 built but UNWIRED)
- Leaf 06: **PASS** (confirmed; "plumb pre-existed" claim verified true)

## Leaf 05 findings

| Task | Verdict | Evidence |
|---|---|---|
| 1. ToolRetryBreaker tests + impl | WIRED (self-contained) | `internal/agent/tool_breaker.go` complete: canonical JSON keys (:53-78), zero-value defaults warn 3 / veto 5 (:39-48), mutex-guarded Observe with slog AFTER unlock (:86-111). Tests incl. concurrency + map-order identity. All pass. |
| 2. Wire Observe on tool failure in loop.go | UNWIRED | Zero production callers: `rg "ToolRetryBreaker\|NewToolRetryBreaker\|Observe" -g '!*_test.go'` → only definitions. loop.go never references the breaker. Commit e8eb57df message: "Loop wiring arrives with leaf 11 per the serial loop.go plan" — leaf 11 (ed9916c0) IS an ancestor of HEAD and delivered no breaker wiring. |
| 3. Structured-verify guard | UNWIRED (+ spec drift) | VerifyFromToolResults (tool_breaker.go:120) + TestVerifyFromToolResults_IgnoresProse (tool_breaker_test.go:215) exist and pass, but nothing hooks the existing verification path; zero production callers. Spec'd verify_structured_test.go is absent — tests live in tool_breaker_test.go instead. |

Plan's proving scenario ("mutating turn + success claim + no test run ⇒
blocked") exists as NO test anywhere; the pre-existing verification system
(verification_hook.go, Tree-01 work) is nudge/spawner-based and never
consults VerifyFromToolResults. Master.md tracking row "COMPLETE / 15/15
hooks" counted unit tests only.

Fix shapes: init breaker beside verificationTracker (loop.go ~1709); Observe
after tool-execution error, veto ⇒ skip re-invoke + system note; register a
PrepareNextTurn hook beside verification_auto_trigger (loop.go ~1720) for
claim-vs-evidence blocking; add the proving-scenario test.

## Leaf 06 findings

| Task | Verdict | Evidence |
|---|---|---|
| 1. Failing→passing specialist test | WIRED | shadow_specialist_test.go:147 exercises the REAL chain (NewAgentRegistry(RegistryConfig{ShadowManager}) → r.Get → createLoop → NewAgentLoop opts); mock Chatter injected only at the LLM boundary (loop.llm, :164); asserts task_type=tool_use record via require.Eventually. Nil-manager negative control included. |
| 2. Thread shadowMgr into registry loops | WIRED (pre-existing, honestly reported) | components.go:2072 ShadowManager → registry.go:181 shadowMgr → registry.go:390-392 WithShadowManager → registry.go:473 NewAgentLoop(opts). Plumbing commit ad0eaa60 (Feb 2026) predates the plan (Aug 2026); leaf commit 86e14393 touches only 2 test files. docs/implementation-gaps.md item 2 was stale, as master.md claimed. |
| 3. Tool-turn persist | WIRED | capture_persist_test.go:54 uses a real Manager+store (t.TempDir): TotalRecords==1, tool_use bucket, tool-call content in row. manager.go CaptureToolInteraction (:640-689) forces TaskTypeToolUse unconditionally and encodes ToolCalls into record content — empty-Content tool-only responses stored, not dropped. |

Other production NewAgentLoop sites surveyed: daemon primary
(components.go:1089) ✓; handler.go:1723 GetOrCreateWired clones the daemon
template via ConfigSnapshot ✓; loop.go:5819 spawn inherits ✓. Observation:
SpawnVerifier's child loop (verification_hook.go:283) gets no
WithShadowManager — verifier turns uncaptured; likely intentional for an
ephemeral verifier, worth a comment.

Review checklist clean: no SetShadow* accessor exists at all (nothing dead);
capture runs on a l.wg goroutine outside loop/registry locks (loop.go:3385);
no os.Getwd in daemon/agent/shadow.
