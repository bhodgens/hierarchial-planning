# Quota-reset-resilience audit — leaves 01/03/04 (meept, 2026-08-31)

Read-only audit of internal/llm quota implementation vs plan leaves
01-quota-error-type, 03-resolver-quota-blocks, 04-direct-call-wait and
master Contracts 1/2/4/5. Verdict: scaffolded, tests green, ZERO
production producers AND zero production consumers of quota state.

## Per-leaf verdicts

### Leaf 01 (error type + parsing): PARTIAL
- errors_quota.go: type + helpers match Contract 1; ParseQuotaResponse
  (:132) gates 429/402, structured-body-first, header fallback,
  MaxWait-clamped RetryAfter, 500-char truncation. Tasks 1-3 OK.
- Task 4 UNIMPLEMENTED: no client ever calls ParseQuotaResponse (sole
  callers = errors_quota_test.go:139/142/147). client.go doRequest: 429 →
  RateLimitError only (:989-1023); 402 → generic APIError (:1027-1031),
  and 402 ∉ retryableStatusCodes (:32-39) → hard fail. anthropic.go: 429 →
  buildRateLimitError (:994-996, :1143-1145); 402 → generic APIError
  (:1011-1025).
- COUPLED GAP: NonRetryable() implemented (:69-73) but all three retry
  loops (client.go:408-449 Chat, :561-605 streaming, anthropic.go:256-284)
  branch only on RateLimitError/APIError. Vacuously safe today ONLY
  because nothing produces the type; fixing the producer without an
  explicit quota/non-retryable branch FIRST in each loop makes 429 quota
  errors re-enter the 3-attempt loop (QuotaResetError unwraps to
  APIError{429}).
- Minor: :env: fingerprint branch missing (Contract 2) — ModelConfig has
  only APIKey/OAuthProvider (models.go:211,238), env creds collapse to
  ":default". parseQuotaBody second raw["error"] branch (:237-249) is
  unreachable (first returns at :233). QuotaBlockStatus lacks AliasName /
  uses ResetAt vs spec'd BlockedUntil.

### Leaf 03 (resolver quota blocks): PARTIAL
- Present: entryBlocks/credentialBlock on AliasHealth (models.go:353-358),
  init in getOrCreateHealth (resolver.go:600-612), isQuotaBlocked checks
  entry-then-credential (:800-815), HasHealthyModels quota-aware both
  multi- and single-model (:651-688), readers QuotaBlockedUntil/
  ActiveQuotaBlocks (:843-889).
- Bug A: ResolveForAlias current-model check reads health.entryBlocks
  DIRECTLY (:377) not isQuotaBlocked → credential-blocked current model
  (entry clear) is returned instead of rotated.
- Bug B: all-blocked rotate loop (:380-391) leaves CurrentIndex on the
  blocked model and returns it; no "all candidates blocked" error exists.
- Bug C: RotateToNextModel (:693-731) quota-blind — returns blocked model.
- Lazy-clear absent: RecordAliasSuccess (:590-597) never touches blocks;
  expired entries never deleted (unbounded growth, minor); no probe/re-block.
- CRITICAL wiring: quotaCfg written ONLY by tests (resolver_quota_test.go
  :16/54/91/111 — direct field assignment, no setter exists);
  NewResolver (components.go:612) passes none. BlockQuotaEntry/
  BlockQuotaCredential (:818/:826) have zero non-test callers. Blocks are
  read by isQuotaBlocked but written by nothing → join-dead.

### Leaf 04 (direct-call wait): PARTIAL
- quotaWaitChatter (resolver_direct.go:30-148) is a faithful Contract 5
  implementation: exactly one wait+retry (:91,:124), timer+select, ctx
  deadline wins (:69-82), MaxWait cap, both Chat and ChatWithProgress.
- WIRED INTO THE WRONG (DEAD) COMPONENT: only caller is
  ModelBroker.ChatterForModel (broker.go:462-475); NewModelBroker
  (broker.go:70) has zero production callers — master.md Notes itself
  declares the broker dead. Contract 5 names Resolver ChatterForModel;
  Resolver has no such method. Test file resolver_direct_test.go exists.
- ConfigFromSchema (:40-47): ZERO callers incl. tests; parameter
  interface demands GetEnabled/GetMaxWait/GetDefaultEstimate/
  GetDeferCheckInterval but config.QuotaRetryConfig (schema.go:758-771)
  has plain fields, no getters → bridge uncallable by its named source.
  Schema→resolver config plumbing severed end-to-end; every quota gate
  (resolver.go:375/669/685, broker.go:471) permanently false.

### Cross-cutting: loop.go violates RecordAliasFailure exclusion
- Quota branch (loop.go:4338-4352) tracks episode via l.quotaTracker then
  FALLS THROUGH (no return) to :4355-4356 RecordAliasFailure — the exact
  call Contract 4 forbids ("quota is not a health failure"). Burns alias
  health / arms cooldown / releases sticky pins. Also branch order
  inverted vs spec (quota after rate-limit :4264; harmless only because
  types are disjoint). WithQuotaTracker (loop.go:1307) has zero
  production callers → tracker always nil → episode tracking dead too.

### ProviderManager (leaf 03 Task 4): rotate-only, no persistence
- Quota branches in Chat (:276-284) and ChatWithProgress (:425-434) log +
  continue, correctly skipping recordFailure — but no block is stored, so
  getOrderedProviders (:465-512) re-ranks the quota'd (still-Healthy)
  entry first on every request → repeated 429s. runHealthCheck
  (:886-927): probes Unhealthy only, no quota re-block/clear. Its quota
  branches are currently dead code (no producer).

## Fix order (top 5)
1. Both clients call ParseQuotaResponse (client.go 429 w/ Retriable-true
   && RetryAfter<5m RateLimitError carve-out, + 402; anthropic.go both
   doRequest sites) AND add explicit quota early-exit FIRST in all three
   retry loops — one coupled change.
2. Arm quotaCfg in production: fix ConfigFromSchema's interface (accept
   config.QuotaRetryConfig directly), set from components.go:612,
   enabled-with-defaults on zero-value.
3. loop.go quota branch: BlockQuotaEntry+BlockQuotaCredential (computed
   wait) then RETURN before the RecordAliasFailure fall-through.
4. Resolver semantics: isQuotaBlocked for current model (:377);
   RotateToNextModel quota-aware; distinct all-blocked error.
5. ProviderManager: persist credential-level block (skip in ordering
   across requests) + quota probe handling in runHealthCheck; relocate
   the Contract 5 decorator onto the Resolver's direct path.

## Verification commands that worked
- go build ./... clean; go test ./internal/llm/ -run 'TestQuota|
  TestResolverQuota|TestParseQuotaResponse|TestQuotaCredentialKey'
  -count=1 → ok (tests pass on self-wired state, proving nothing about
  production).
- Producer grep: grep -rn ParseQuotaResponse --include='*.go' . (minus
  _test) → definition only.
- Dead-constructor grep: grep -rn NewModelBroker --include='*.go' . →
  definition only.
- Bridge satisfiability: grep the source type for the interface's exact
  methods → none exist on config.QuotaRetryConfig.
