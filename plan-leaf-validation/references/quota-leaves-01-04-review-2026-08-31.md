# Quota plan leaves 01–04 adversarial re-review (meept, 2026-08-31)

Post-fix verification pass over the CLOSED quota-reset-resilience plan
leaves 01 (error type/client), 02 (config), 03 (resolver blocks),
04 (direct-call wait). Supersedes the "unwired/compile-broken" state in
references/quota-leaves-01-03-04-audit.md and the open findings in
references/quota-reset-resilience-post-audit.md for the items listed here.

## Verdict per leaf

- **01: PASS after fixes this session.** Producer classification landed in
  both clients (client.go doRequest 429 via classifyQuotaDecision + 402;
  anthropic.go both doRequest + doStreamingRequest) and quota early-exits
  landed in Chat/ChatWithProgress/anthropic loops. Two NEW defects found
  and fixed this session (see below). QuotaCredentialKey: no `:env:`
  branch (ModelConfig has only APIKey/OAuthProvider) — accepted deviation.
- **02: PASS after fix this session.** Struct/defaults/getters/template
  correct, BUT NormalizeQuotaRetryDefaults had zero production callers.
- **03: PASS after fix this session.** Prior audit's Bugs A/B/C fixed
  (isQuotaBlocked for current model, all-blocked error with %w wrap,
  quota-aware RotateToNextModel), readers/Block methods on Resolver,
  lazy-clear on RecordAliasSuccess, PM persistence + probe re-block/clear
  + getOrderedProviders filtering all verified. One NEW gap fixed
  (sticky-pin path).
- **04: PASS (accepted deviation).** quotaWaitChatter correct (one
  wait+retry, ctx wins, DefaultEstimate only when ResetAt zero AND
  RetryAfter<=0, MaxWait + deadline guards, both Chat methods).
  Still wired only via ModelBroker.ChatterForModel (dead in production);
  production wait is leaf 06's turn-parking QuotaResumeWatcher —
  documented accepted deviation in master.md.

## Prior-audit findings verified LANDED

- ConfigFromSchema + SetQuotaConfig production-wired
  (daemon/components.go:634-635); PM SetQuotaMaxWait (components.go:787).
- loop.go quota branch: BlockQuotaEntry + BlockQuotaCredential then
  RETURN — RecordAliasFailure fall-through GONE; branch precedes the
  rate-limit handler. Tracker Enter/Clear wired (success path Clear at
  the RecordAliasSuccess site).
- ChatHandler SetQuotaResumeConfig wired from QuotaRetry.MaxWait
  (components.go:2291/2550); watcher Start/Stop in handler lifecycle.

## New defects found THIS session (all fixed)

1. **Fifth retry loop missed (client.go ChatWithDeltaCallback :1269).**
   Prior audit said "all three retry loops"; grep `for attempt` across
   the package shows FIVE (client.go :426/:586/:1269, anthropic.go
   :281/:448). The delta-callback loop had no quota classification in
   doStreamRequest AND no early-exit — QuotaResetError wraps
   APIError{429} which isRetryableStreamingError matches → 3 burned
   attempts on the path the agent loop uses for streaming. Fix: quota
   classification in doStreamRequest's error-status path (preserving
   RateLimitError for short-cycle retriable) + early-exit first in the
   loop. Test TestQuotaClient_DeltaCallbackQuotaErrorNoShortRetry pins
   hit-count==1 for quota 429/402 and streamMaxRetries for plain 429.
2. **UserMessage() dispatch missed QuotaResetError (errors.go :134).**
   Wrap chain (→APIError{429}) made quota errors render via the coarse
   APIError branch. Fix: quota branch FIRST in the dispatch chain.
3. **NormalizeQuotaRetryDefaults dead code (config).** Defined + tested +
   never called by Load (TOML) or LoadJSON5Config. Fix: normalize at both
   load boundaries (mirrors NormalizeRuntimeDefaults precedent).
4. **resolveStickyCaller bypassed quota checks (resolver.go :505).**
   The sticky fast-path returned before the quota-aware rotation block:
   BalancedStickyRequests aliases kept serving pinned callers the
   blocked model forever. Fix: releaseQuotaBlockedPin drops blocked pins
   + re-pin scan skips blocked candidates (rotation-head fallback with
   Warn when all blocked, since sticky resolve can't return error).
   Test TestResolverQuota_StickyPinSkipsBlockedModel.

## Open observations (do NOT treat as wired; re-flag candidates)

- **llm.quota_retry.defer_check_interval is a silent no-op.**
  QuotaResumeWatcher hardcodes DefaultQuotaResumePollInterval (10m,
  quota_resume.go:31); SetQuotaResumeConfig accepts only maxWait
  (handler.go:1524). Config knob is plumbed to ConfigFromSchema but no
  consumer reads the value. Follow-up: widen SetQuotaResumeConfig or add
  a SetQuotaResumeInterval setter + wire from cfg.LLM.QuotaRetry.
- ActiveQuotaBlocks entry rows omit CredentialKey (only credential rows
  carry it) — consumers key episodes separately; consistent, left as-is.
- QuotaDeferralManager dead-code finding from the post-audit NOT re-checked
  this session; check before assuming still present.

## Verification evidence (2026-08-31)

- go build ./... clean
- go test ./internal/llm/ -count=1 → ok (full suite, 42.6s)
- go test ./internal/config/ -count=1 → ok; ./internal/agent/ -run Quota → ok
- go test -race ./internal/llm/ -run 'TestResolverQuota|TestQuotaWait|
  TestChatterForModelQuota|TestQuotaClient' -count=1 → ok
- gofmt clean on touched files; no `N|` corruption patterns
