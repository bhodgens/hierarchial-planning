# Harness-eval leaves 09/10/11 audit — evidence (2026-08-30, commit 5d31b720, repo /tmp/meept-harness-audit)

Verdicts: 09 WIRED (2 deny-set omissions) · 10 WIRED · 11 CODE WIRED / PRODUCTION INTEGRATION UNWIRED.

## Leaf 09 — trusted root

Wired core (applier.go @5d31b720):
- Deny order: `applyFix` calls `denyTrustedRoot` at **:115** BEFORE `createBackup` (**:121**) and `os.WriteFile` (**:159**). Approve path re-checks (`Approve`→`applyFix` :199); proven by `TestApply_ApprovePathAlsoDenied` (applier_test.go:411).
- Symlink/absolute/`..`: denyTrustedRoot :390-464 — absolute rejected :400-402, `..` segments :403-407, deepest-existing-ancestor EvalSymlinks for target AND root :420-462. Tests: `TestDenyTrustedRoot` (:146), `TestDenyTrustedRoot_SymlinkEscape` (:196, incl. chain a→b→outside and inside-symlink control).
- Backup dest: `createBackup` :282-310 — isWithinDir guard :287, sanitized ID + `Base()` join :300-302. Test `TestCreateBackup_BackupDestStaysInBackupDir` (:353).

Gaps vs C5 contract:
1. `testdata/eval/` oracle fixtures (`classifier-test-corpus.json5`, `smoke-test-corpus.json5`) NOT in `trustedRootPrefixes` (:34-42). C5 says "deny edits to ... eval oracle fixtures". Fix: add `"testdata/eval/"`.
2. Gate-command immutability partial: `config/employees/` + `config/meept.json5` denied, but per C2 `gate.command` lives in `config/agents/*/AGENT.md` frontmatter and `config/agents/` is NOT denied — applier can patch the gate command; `meept agents set-gate` (cmd/meept/agents_cmd.go:1031) is not the only mutator. Fix: deny `config/agents/` frontmatter paths or strip gate keys pre-patch.
3. fence/tirith ~/.meept config: no explicit denial; only implicitly unreachable via absolute/`..`/symlink rejection. Document or add explicit entry.
Nit: `backupDir` itself never symlink-resolved (:73).

## Leaf 10 — isolation: PASS

Spawn-path census (all ArtifactOnly, nil parent, zero transcript copies in production):
- dispatcher handoff: buildHandoffSpawnContext dispatcher.go:2071-2091, consumed :1746
- orchestrator step handoff: orchestrator.go:1276 (legacy 500-char fallback tactical.go:1363 = step-result brief, not transcript)
- delegate_task: platform.go:363
- pair driver/observer: collaboration_pair_driver.go:283, :319
- registry: fresh conversation per spawn, registry.go:545-559
- isolation.go:65-101 matrix + fail-closed warn-once; tests isolation_test.go:31,116,129,164,190,201,245,280,301,318,342,362,376 — all pass (-race).
Minor: `shared_transcript` has no external surface — handler.go:1799 / team_orchestrator.go:258 always pass DefaultSessionConfig(); opt-in only reachable programmatically.

## Leaf 11 — speak router

Present and tested green: ClassifyRun matrix (speak_test.go:46), Deliver empty-text/nil-safety, reply_to_user tool + registration (components.go:1998) + executor category (executor.go:283), loop Deliver site loop.go:2356-2383, loop dedup replyToolNotifiedThisTurn loop.go:6622-6640, GoalLoop notifySpeakRound goal_loop.go:462-500 + deliver site :944, GoalLoop round dedup flag, WS bridge subscribes `employee.*` (server.go:515-522) and classifies it `"event"` never chat_message (server.go:727; tested server_test.go:2684-2686). Full -race pass: agent/employee/comm/http/selfimprove/tools-builtin.

UNWIRED (zero production callers, internal/ + cmd/ grep, tests excluded):
1. `NewSpeakRouter`, `BusSpeakPublisher`, `agent.WithSpeakRouter`, `GoalLoop.WithSpeakRouter` — the daemon GoalLoop registration block (components.go:3763-3859) wires gates/executor/planner/reflector/metrics but never a router; `agentLoopBotExecutorAdapter.ExecuteBot` (employee_service_adapter.go:293-305) runs goal turns through the shared `c.AgentLoop` (components.go:1250) which has neither router nor `WithSessionAttached(false)`. Net: detached goal-round text notifies nothing in production.
2. `GoalLoop.SetSpeakContext` — payload IDs always empty AND `speakNotifiedRound` resets only via SetSpeakContext (goal_loop.go:458); docstring credits a `BeginRound` that does not exist. Once wired, first notify silences all later rounds.
3. employee.notify consumers: ONLY the WS bridge. No subscriber bridges to `services.PushService` (push_service.go publishes `push.<sessionID>` topics; push channels Telegram/TUI/menubar never see goal-round notifications) despite the plan naming internal/services/push.
4. `ErrIsolatedSpeak` / `ReplyCarrier` SpeakParent branch: zero test references; the tool test (reply_to_user_test.go:67) uses a fake carrier string, not the real carrier.
5. `DeliverIsolatedNotify` (speak.go:159): exported, zero callers. `SpeakParent` deliveries no-op everywhere (no parent-report channel — documented deferral).

Fix sites for the wiring session:
- components.go GoalLoop registration block: `loop = loop.WithSpeakRouter(agent.NewSpeakRouter(agent.BusSpeakPublisher(bus, "employee-goal-loop")))`
- Executor path: `WithSessionAttached(false)` (or a dedicated detached loop) on the loop the adapter drives
- Manager.triggerViaGoalLoop (employee/manager.go:1415): call `loop.SetSpeakContext(...)` per round (session/conversation IDs) — also fixes the latch reset
- New subscriber on `employee.notify` → `PushService.Push` in components wiring

## Test runs (-race -count=1)
```
ok  github.com/caimlas/meept/internal/agent        17.192s
ok  github.com/caimlas/meept/internal/employee      4.802s
ok  github.com/caimlas/meept/internal/comm/http    51.212s
ok  github.com/caimlas/meept/internal/selfimprove   1.641s  (deny/apply/backup/rollback subset)
ok  github.com/caimlas/meept/internal/tools/builtin 1.732s
```
