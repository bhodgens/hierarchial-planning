# Quota Reset Resilience — Post-Fix-Session Audit

Date: 2026-08-31
Plan: `docs/plans/quota-reset-resilience/master.md` (10 leaves)
Status: All leaves IMPLEMENTED or PARTIAL; two build-breaking gaps remain.

## Build Failures (block all `go test`)

### 1. `internal/agent/loop.go:2063-2064`
```
unknown field UserMessage in struct literal of type SessionLifecycleResult
unknown field AssistantMessage in struct literal of type SessionLifecycleResult
```
`SessionLifecycleResult` (hooks.go:350-355) has only:
- `Success bool`
- `Error error`
- `EndTime time.Time`

Loop references two fields that don't exist. Either add them to the
struct or remove the references. The comment at :2055 says
`AssistantMessage reads the named return` — this was planned but never
implemented on the struct.

### 2. `internal/llm/resolver_quota_test.go`
```
resolver.quotaCfg undefined
resolver.ActiveQuotaBlocks undefined
resolver.BlockQuotaEntry undefined
resolver.BlockQuotaCredential undefined
resolver.QuotaBlockedUntil undefined
```

`AliasHealth` in `models.go:353-358` has the maps (`entryBlocks`,
`credentialBlock`) but they are private. The test expects public methods
on `*Resolver` that don't exist. `broker.go:504-511` has stub methods
on `ModelBroker` returning zero values — but the plan and loop code
target `Resolver`, not `ModelBroker`.

Fix approach: add methods to `*Resolver` that delegate to the
`AliasHealth` maps under `r.mu`:
- `BlockQuotaEntry(alias, providerID, modelID, unblockAt)`
- `BlockQuotaCredential(alias, credentialKey, unblockAt)`
- `ActiveQuotaBlocks() []QuotaBlockStatus`
- `QuotaBlockedUntil(credentialKey) time.Time`
- `isQuotaBlocked(health, m) bool` (already partially exists as inline
  logic in ResolveForAlias — extract to method)

## Other Gaps

### QuotaResumeWatcher lifecycle not driven
`internal/agent/handler.go:1521` creates the watcher.
`handler.go:177-178` calls `Start(ctx)` inside the handler's own
context, but nothing in `internal/daemon/components.go` calls
`Start()` on the handler's watcher during daemon bootstrap, and nothing
calls `Stop()` on shutdown. The watcher's goroutine never starts in
production.

Site to wire: `components.go` around line 1100 where `quotaTracker` is
constructed. After creating the `ChatHandler`, call
`handler.QuotaResumeWatcher().Start(ctx)` and register a `Stop()` on
daemon shutdown.

### QuotaDeferralManager is dead code
`internal/agent/quota_deferral.go` defines `QuotaDeferralManager` with
`RecordDeferral`, `GetPending`, `Remove`, `CheckQuotaError`,
`FormatQuotaDeferralMessage`, `durationStr`. Zero instantiation sites
in the entire repo. Zero tests. The parallel fix wave that created it
duplicated the `QuotaResumeWatcher` role without connecting it.

Action: delete the file, or if the deferral-manager concept is still
wanted, wire it to the dispatcher path. Recommendation: delete —
`QuotaResumeWatcher` covers the same surface with turn-level semantics
that match how budget deferral works.

### Escalation vocabulary stale in plan docs
Master.md `task 8` sketch says escalation values are `12h/20h/24h`.
Implementation uses `""` / `"warn"` / `"action_recommended"` /
`"blocked"`. The `post-completion deviations` section at master.md:396
acknowledges this but the tracking table and leaf docs are inconsistent.

Action: update leaf 05 and master.md tracking table to reflect actual
vocabulary.

### Flutter `to==""` tier-escalation events unhandled
`ui/flutter_ui/lib/providers/agent_provider.dart:94-107` handles
`to=="quota_wait"` and `to=="blocked"`. Events with `to==""`
(tier-escalation warnings at 12h/20h) fall through silently — no UI
update, no badge change. This is not a correctness bug (the tracker
still emits the bus event and the notifier still pushes), but the GUI
is silent on escalation tiers.

Action: add a case for `to==""` that updates the badge text to show
escalation level without changing the blocked/wait state.

## Wiring That IS Correct (verified)

- `QuotaResetError` + `ParseQuotaResponse` in `errors_quota.go` — complete
- `QuotaWaitConfig` + `newQuotaWaitChatter` in `resolver_direct.go` — complete
- `QuotaEpisodeTracker` with reaper goroutine in `quota_episode.go` — complete
- Tracker wired to bus publisher in `loop.go:1692-1702` — complete
- Tracker wired to state setter in `loop.go:1711-1720` — complete
- `StateQuotaWait` + `StateBlocked` in transition table — complete
- `agent.quota_wait` → `agent_progress` WS classification in `server.go:703-709` — complete
- `QuotaNotifier` subscription in `components.go:1347` — complete
- TUI quota status badge in `agents_panel.go:83-97` + `quota_status.go` — complete
- Flutter quota payload model + provider + badge — complete
- Loop quota branch at `loop.go:4375-4399` terminates (no fallthrough to
  RecordAliasFailure) — correct
- Success path calls `quotaTracker.Clear()` at `loop.go:4291-4293` — correct

## Test Status (at audit time)

```
go test ./internal/agent/     → FAIL (loop.go:2063-2064 build break)
go test ./internal/llm/       → FAIL (resolver_quota_test.go build break)
go test ./internal/services/  → PASS
go test ./internal/tui/       → PASS
go test ./internal/comm/http/ → PASS
go test ./internal/config/    → PASS
```
