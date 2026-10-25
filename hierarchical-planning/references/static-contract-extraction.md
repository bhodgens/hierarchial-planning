# Static Contract Extraction (runtime gate blocked)

When a plan's Phase-0-style runtime validation spike is blocked (operator
denial at the approval prompt, no Docker, no credentials), a GO/NO-GO gate
does not have to end as a dead stop. Extract the contracts STATICALLY from
the pinned upstream checkout and let the runtime evidence move to staging.

## When to use

- The gate leaf is blocked but the source checkout already succeeded (a git
  clone needs no approval; `scripts/setup.sh` / docker up does).
- The alternative is dispatching adapter code against remembered API shapes.

## Recipe

1. **Pin the checkout.** Record the upstream commit SHA of whatever you
   cloned (`git -C /tmp/checkout rev-parse HEAD`). All downstream contracts
   cite "pinned commit <sha>". Never say "current docs" without a date.
2. **Grep the source for wire truth.** In Rust/Go/Terminal services, wire
   shapes live in serde/JSON tags and route tables:
   - Request/response field names: `grep -rn 'rename = "' crates/` or the
     Go `json:` tags in the API-models package. These override whatever the
     hand-written docs say.
   - Webhook signature headers + schemes: grep for the header name and
     `hmac`/`sha256`/`sha512` in the webhook-verification module. Record
     file:line for each.
   - Event-type strings: grep the enum whose variants are the emitted
     event names. Watch for MISLEADING names (real example:
     Hyperswitch's `dispute.failed` fires when a dispute is OPENED).
3. **Prefer compat layers.** Large processors often ship a
   Stripe-compatibility webhook scheme byte-identical to Stripe's
   (`Stripe-Signature: t=...,v1=...`). If your platform already validates
   Stripe signatures, reuse that validator verbatim — record the native
   scheme as fallback only.
4. **Record deltas vs the plan's sketch.** The plan contract was written
   from memory; the source is truth. Table every delta
   (`payment_id` not `id`; dotted `created.gte` query keys; lowercase
   refund status enums). Where local checkout and live docs conflict, the
   local pin wins (it's what you deploy) and the delta is logged as a
   staging smoke-test item.
5. **Write the gate report honestly.** Gate: INCOMPLETE/BLOCKED (not GO).
   Unverified items tabled with reasons. Static findings section carries
   the file:line provenance. Paths forward: consented re-run / hosted
   sandbox / static-go — with static-go's risk stated (runtime evidence
   deferred to staging smoke).
6. **Make adapter code safe under static-go.** Code compiled against static
   contracts should be INERT until configured (env-gated registration), so
   shipping it carries zero production risk while staging proves the
   runtime.

## Worked example

Hyperswitch spike blocked at `scripts/setup.sh` (operator denial, twice).
Static pass over the pinned checkout yielded: `payment_id` (not `id`) in
PaymentsResponse; HMAC-SHA512 native webhook scheme + a byte-identical
Stripe-compat scheme; the misleading `dispute.failed` = opened mapping;
port-conflict remap prepared for a later consented re-run. Adapter code
shipped env-gated; runtime evidence deferred to the staging deployment
smoke test.
