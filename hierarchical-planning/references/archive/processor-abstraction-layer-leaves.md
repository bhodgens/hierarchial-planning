# Processor-Abstraction (Anti-Corruption) Layer Leaves


When to use: inserting a vendor-neutral interface before an entrenched processor.
Lesson: anti-corruption layer contract set; vendor toggle without rewrites.
> Pattern reference for plan trees that insert a vendor-neutral interface
> between an application and a single entrenched external processor
> (payment processor, SMS/email provider, storage backend, LLM provider).
> Generalizes the 2026-08-25 strategist-usa payment shim: Stripe-only code
> in three Go services, user wants multiple processors behind a platform
> toggle. Same shape as Go's `narrow-storer-interface-pattern` but at the
> vendor boundary, not the store boundary.

## The contract set that makes the tree work

Five contracts in master.md, each with ONE owning leaf and named consumers:

1. **Processor interface + neutral types.** Neutral structs are
   field-for-field mirrors of the incumbent vendor's shapes (JSON tags
   included), so the incumbent adapter is a PURE translation layer and
   existing call-site code keeps its shape. Method set = exactly the
   incumbent client's methods that real call sites use — enumerate them
   by grepping call sites FIRST (`StripeClient\.[A-Z]` style), not by
   reading the client. Mark client methods that are `//nolint:unused` as
   out-of-contract.
2. **Resolver + Router.** Resolver reads a platform settings key with a
   short TTL cache (60s) and FAILS CLOSED to the incumbent on missing
   key / SQL error / unknown value. Storage error after a good read
   keeps the last-good value; a missing key is a definitive answer
   (cache it as incumbent). Router maps provider→processor:
   `ForAuthorizations(ctx)` = new-money dispatch via resolver;
   `ForRecord(p)` = processor-of-record dispatch for refunds/webhooks/
   reconciliation. Constructor rejects duplicate providers and a missing
   incumbent (guarantees `ForRecord` can never return nil).
3. **Processor-of-record columns.** Every money row records its
   processor, backfilled to the incumbent. Toggle affects NEW
   authorizations ONLY; refunds/recon dispatch on the stored column,
   never on the toggle. This is THE invariant reviewers check.
4. **Normalized webhook envelope.** Second provider's events normalize
   onto the incumbent-derived internal types so the existing queue
   worker processes them with ZERO changes — one provider marker in
   metadata carries processor-of-record into the rows the worker writes.
   JobID dedupe prefix becomes `"<provider>-<evtID>"` with the
   incumbent's existing prefix byte-compatible.
5. **Toggle API.** One GET, one PUT, superuser-only, validates against
   REGISTERED processors (router.Available()), audited.

## Fail-closed everywhere

Test names say it explicitly: resolver fail-closed on every error path;
router fail-closed when toggle names an unregistered provider (startup
warning + serve incumbent); webhook worker defaults to incumbent when the
envelope carries no provider marker (backfill-compat). An unknown enum
value from the NEW vendor (e.g. unmapped payment status) maps to the
failure state + a log line, never silent success.

## Deliberate no-data policies

Second vendors often don't surface the incumbent's full API surface
(disputes, invoices, balance for an orchestrator that never holds funds).
Make the absence a DOCUMENTED contract, not a silent gap: List* methods
return empty+false, GetBalance returns zero, each with a doc comment
saying why, and the polling workers guard on `Processor.Name()` to skip
that provider. A call-counter test proves the stubs make no HTTP calls.

## Card-data boundary

Stored payment methods stay on their processor — cross-processor token
reuse is a PCI project, not a shim feature. Phase 1 keeps the incumbent's
tokenization untouched; the new rail re-collects. State this in master.md
so no leaf "helpfully" migrates tokens.

## Leaf order that de-risks

```
A: [interface+types] [DB migration]        (parallel, vendor-neutral)
A: [vendor spike → GO/NO-GO gate]           (parallel with foundation)
B: [resolver+router] [incumbent adapter]    (both need interface only)
B: [vendor deployment]                      (needs gate GO only)
C: [handler rewiring] [webhook pipeline]    (parallel; need adapter branch)
C: [worker guards] [toggle API+UI]          (parallel)
D: [failure drills + runbook]
```

Dispatch B-leaves the moment the interface leaf is COMMITTED green — the
wave doesn't wait for the spike or migration. The incumbent adapter is the
highest-regression-risk leaf: reviewer diffs the incumbent client file and
confirms the only change is a test-only base-URL injection seam.

## Verification gates the orchestrator runs itself

- `go build ./... && go test ./...` whole-tree, plus `-race` on the new package.
- Grep gate: zero direct incumbent-client uses left in rewired handlers.
- Existing handler/worker tests pass UNCHANGED (proof of zero drift on the
  incumbent path); where a test constructs the old client, update the
  construction only — never the assertions.
- Toggle flip in staging visible ≤ TTL seconds; refund of a pre-migration
  transaction still hits the incumbent while toggle = new vendor.
