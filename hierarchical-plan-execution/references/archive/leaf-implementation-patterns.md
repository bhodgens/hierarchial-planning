# Lleaf implementation patterns
When to use: implementing leaves in shared Go modules.
Lesson: sibling leaves, worker e2e harness patterns.

# Leaf Implementation Patterns (shared Go modules, sibling leaves, worker e2e harness)

Durable lessons from implementing plan-tree leaves that touch shared Go
modules. Example session: 2026-08-25 payment-processor-shim
(03-wiring/03-runner-workers, strategist-usa).

## 1. Sibling leaf not implemented yet → code to the pinned contract

- When your leaf depends on a sibling leaf's output (e.g. a webhook
  publisher that isn't built yet), do NOT wait and do NOT invent your own
  mechanism. The branch orchestrator's PIN (e.g. "payload
  metadata.processor is source of truth; JobID prefix is dedupe-only") is
  the interface. Implement and test against synthesized payloads matching
  the contract exactly. Disclose in your report that the sibling is absent
  and you coded to the pin. Leaves saying "do not invent a second
  signaling mechanism" mean it.
- Write one test that deliberately OMITS the optional transport signal
  (e.g. a prefixless BullMQ JobID) to prove the code never consults it.

## 2. Write-site audits must trace service-layer indirection

- Grepping raw SQL (`INSERT INTO funding_transaction`) finds only direct
  writes. Deposit/credit writes flowed through
  `BillingService.AddFundsInTx → insertFundingTransaction`, invisible to
  the SQL grep. Audit = grep raw SQL AND grep the service-helper call
  sites; tag at the choke point.
- When the choke point lacks the capability (no `Processor` field on the
  row struct / options), adding it is REQUIRED PLUMBING, not scope creep —
  but it must default fail-closed (empty → 'stripe') so every legacy
  caller stays backfill-compatible. Disclose the extra files in the
  deviation section.
- Import-cycle guard: `pkg/services` cannot import
  `pkg/services/payments` (payments imports services). Duplicate provider
  string consts at the services layer with a MUST-stay-in-sync comment
  rather than breaking the cycle.

## 3. Shared-module changes → build EVERY dependent module

- Multi-module repos (pkg, backend-api, go-global-runner, go-web-hooks,
  go-shard-runner, auth — each with `replace ../pkg`) mean a pkg/... change
  can break any sibling. Gate = `go build ./...` in EACH dependent module,
  not just your own.
- `git status`/`git diff` will show a parallel agent's uncommitted edits in
  OTHER modules (concurrent leaves). Leave them alone; build against
  current disk state; name in your report which diffs are not yours.

## 4. Worker e2e harness (testcontainers) — running a BullMQ worker processor against real Postgres

Working pattern (`go-global-runner/internal/workers/
stripe_webhook_processor_integration_test.go`, `//go:build integration`):

- `integration.NewSuiteWithSchema` + `integration.CreateDefaultSchema`
  (pkg/bullmq/integration) → Postgres+Redis containers + base DDL.
- Single-DB master==shard: insert a `shards` registry row with
  `database_url = suite.PostgresDSN()`, build
  `sharding.NewShardRouter(dsn, ...)`, register the org with `shard_id`,
  then call the real processor fn with a hand-built `types.Job`.
- GOTCHA 1: the `shards` row MUST have non-NULL `redis_url` — loadShards
  scans into plain strings; NULL fails the whole row scan and every lookup
  dies with "shard shard-1 not found". Insert a dummy `'redis://unused'`.
- GOTCHA 2: test DDL must cover the FULL column list of the real INSERT.
  The suite DDL lacked `original_transaction_id` (and needed `processor`
  added); the insert failed but the webhook handler swallows non-transient
  DB errors into a success-with-audit-log result — the failure surfaced
  only as "no rows in result set" on the assertion query. When an e2e
  assertion finds no row, suspect a swallowed insert error and check DDL
  parity first.
- GOTCHA 3: `t.Cleanup(router.Close)` doesn't compile (Close returns
  error) — wrap: `t.Cleanup(func() { _ = router.Close() })`.
- GOTCHA 4 (test authoring): `json.Unmarshal` MERGES into an existing map
  — unmarshalling a second event into the same struct variable keeps the
  first event's metadata keys (a "native" event test read as
  hyperswitch). Use a fresh variable per event.
- Assert beyond the new column: the downstream money effect (org balance
  moved by the expected amount) and idempotency (event redelivery → same
  row count, unchanged balance).

## 5. "Verify X stays unchanged" leaves → document WHY at the named site

- When a leaf says "verify watermark keys remain X", the deliverable is a
  code comment at the named location explaining the invariant (e.g.
  watermark keys stay stripe-scoped because the workers poll ONLY Stripe;
  the second provider's money arrives via webhooks and has no polling
  watermark). Without the why, a future agent will "fix" the scoping.
