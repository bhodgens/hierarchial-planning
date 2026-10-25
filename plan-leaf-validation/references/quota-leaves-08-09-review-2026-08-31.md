# Quota leaves 08+09 (TUI + Flutter quota status surfaces) — adversarial review evidence, 2026-08-31

Fourth audit cycle on the closed quota-reset-resilience plan. Scope: leaf 08
(internal/tui) and leaf 09 (ui/flutter_ui). Verdict: COMPLETE with bugs; all
fixed in-session by the reviewing agent.

## Verified-sound (do not re-audit without new cause)

- TUI wire path: `app.go` `case "agent.quota_wait"` parses exactly QuotaEvent's
  JSON tags (agent_id, unblock_at RFC3339, escalation, model_id, fallback_model,
  to); omitted/null/""/parse-error all degrade safely. Nil-guard added.
- Bus subscription: TUI subscribes `agent.*` (events.go DefaultEventStreamConfig);
  `matchWildcard` (bus.go:416) is single-segment — `agent.*` matches
  `agent.quota_wait`. WS server subscribes `agent.*` for the http-ws bridge.
- WS classification: `transformBusEventToWS` has `strings.HasPrefix(topic,
  "agent.quota")` → `agent_progress` (server.go ~707); AGENTS.md invariant.
- Flutter receive path: quota events carry no session_id → broadcast to all
  conns (server.go handleWSEvent: `eventSessionID == ""` → send to everyone);
  `_flattenWSMessage` unwraps `{type, data}` envelopes so `json['to']` is the
  discriminator; malformed payloads try/caught in agents_tab listener.
- Flutter provider transitions (quota_wait/blocked/running/`to==""` tier
  refresh) verified correct against classifyTiersLocked's emitted value set.
- Colors both sides from theme tokens (Current().Warning/ErrorC;
  CyberpunkColors.yellowWarning/redAlert ← theme/tokens.json5) — no hardcoded hex.
- Row clear latency: `to==running` drops episode state promptly both sides;
  stale entries vanish on next agents.list (TUI) — restart-mid-episode shows
  base status until next event, per AGENTS.md surfaces invariant.

## Defects found and fixed (three NEW classes — see plan-leaf-validation SKILL.md)

1. **Tested helper dead in the widget tree (leaf 09).** `quotaDetailLines`
   (quota_status.dart) had passing tests and was in the leaf contract, but no
   widget rendered it. Fixed: wired into `_buildGoalsPane` (agents_tab.dart),
   renders only when `fallbackModel` is set; token-colored; ellipsis-guarded.
   New widget test file: test/features/agents/quota_detail_wiring_test.dart
   (4 tests; must tap `ValueKey('agent-tile-<id>')` first — the goals pane
   renders only for the selected agent).
   Field twin: WS payload's `model_id` dropped by `AgentQuotaState` →
   Flutter detail shows `primary: unknown` (documented degradation).

2. **Badge parity drift (leaf 09 vs leaf 08).** TUI badge =
   `quota wait · quota resets in 3h 12m`; Flutter badge showed only the
   countdown. Fixed at composition site (QuotaStatusBadge Text.rich with
   bolded `quota wait` prefix) because the sibling agent owns
   test/quota_status_test.dart which pins quotaCountdownText's exact output
   (kept green: 32 pass).

3. **TUI countdown frozen at event time (leaf 08).** Agents table cells are
   plain strings baked by updateAgentsTable at event time; nothing rebuilt
   them, so "quota resets in 3h 12m" stayed literal for 3 hours. Fixed:
   gated self-perpetuating `quotaCountdownTickMsg` (30s; armed on episode
   entry via quotaStateMsg; disarms when hasQuotaEpisodes() goes false;
   clears countdownTick flag at tick fire so re-arm works). Test:
   TestQuotaCountdownTick. Companion fix: updateAgentsTable's unconditional
   GotoTop() → cursor-preserving SetCursor (the new 30s rebuilds would
   otherwise yank the user's selection every 30s).

## Parked observations (do NOT re-flag as broken; next plan note should record)

- `AgentQuotaState` (agent_provider.dart) drops the event's `model_id`:
  TUI detail shows the real primary model; Flutter shows `primary: unknown`.
  Fix when touched: persist modelId in AgentQuotaState + AgentQuotaPayload
  and pass through in _buildGoalsPane.
- Unblock-time rendering drift: TUI `15:04 MST` (local) vs Flutter UTC
  `HH:mm` substring of ISO8601. Cosmetic; parity decision owed.
- Pre-existing `unnecessary_import` info lint at agents_tab.dart:13 (import
  block owned by a sibling session; left untouched).
- `to==""` with BOTH escalation=="" and unblock_at absent: TUI clears the
  episode, Flutter ignores it (no episode exists case is same; divergence is
  for existing episodes). Not contract-tested either side.

## Verification evidence (this pass)

- `go build ./...` clean; `go test ./internal/tui/ -count=1` full suite ok
  (14.9s); gofmt clean on touched files; zero `N|` line-number corruption.
- `flutter analyze` — only pre-existing info; `flutter test` 32 (leaf suite,
  sibling-owned, kept green) + 4 (new wiring tests) pass.
- `python3 scripts/audit-dart-enum-name-shadow.py` → "OK: no Enum.name
  shadowing found."
- Mid-review concurrency note: sibling landed the to=="" tier-refresh in
  agents_panel.go mid-review (file mtime jumped between reads) — re-read
  files before patching on this shared tree; my patches were re-based on the
  sibling's version without conflict.
