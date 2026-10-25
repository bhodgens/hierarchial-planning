# Leaf Testability Seams: Making Legacy Handlers Testable Without Rewrites

Plan-tree leaves routinely say "write handler tests" against code whose
constructors demand live infrastructure (a `*pgxpool`-backed settings cache,
a concrete Redis stream producer, a real tracer). The leaf's real deliverable
is behavioral coverage, not a test harness rewrite — so add the MINIMAL seam
and stop.

## Case study: go-web-hooks HandleHyperswitch (2026-08-25)

`NewHandler(producer *redis.StreamProducer, ...)` plus
`settingsCache.Get(ctx, key)` hitting Postgres meant no handler test could
run without Redis + a settings DB. Two seams fixed it with ~20 lines:

### Seam 1: narrow the concrete dependency to the methods actually used

The Handler only ever called `producer.Produce(ctx, key, id, payload)`.
Replace the field/param type with a one-method interface:

```go
type streamProducer interface {
    Produce(ctx context.Context, streamKey string, eventID string, payload interface{}) (string, error)
}
// field: producer streamProducer; NewHandler takes streamProducer too.
```

Concrete types still satisfy it unchanged (implicit interface), so ALL
production call sites compile without edits. This is safe when the type is
used in exactly one consumer file — check first:
`grep -rn "TypeName" --include=*.go | grep -v _test`.

Do NOT instead comment out sibling fields to "simplify" — one session nearly
commented out `cvLookupMu/cvLookupCache` in a shared struct and broke 17
references. Revert immediately if lint shows MissingFieldOrMethod errors from
your edit; the seam must be purely additive.

If you can't change the shared constructor, fall back to an unexported
package-level override var with a nil check on the production path:

```go
var hsSecretOverride func(ctx context.Context) string // tests only; prod never sets
```

with the lookup as: override → error-if-nil-cache → cache.Get. Guarded by
t.Cleanup restore so parallel tests can't leak it. This is weaker (global
state) but zero-touch on legacy files.

### Seam 2: stub via context, not middleware

Handlers that read the body from `r.Context().Value(bodyContextKey)` (set by
BodyBufferMiddleware) can be tested by injecting directly:

```go
ctx := context.WithValue(req.Context(), bodyContextKey, []byte(body))
req = req.WithContext(ctx)
```

Same-package test = access to unexported keys. No httptest server needed for
handler-level assertions; use `httptest.NewRequest` + `httptest.NewRecorder`.

### Stubbing a concrete-type field you CAN'T change

When a field stays concrete (`*redis.StreamProducer`) but tests need a fake,
same-package embedding works: define the stub with the concrete type embedded
(nil) and shadow the method on the wrapper. BUT this only helps if the field
is an interface or the stub is passed where the concrete type is expected —
embedding does NOT make the wrapper assignable to the concrete type. If the
field is concrete and untouchable, the only options are the override-var seam
above or a live miniredis. Prefer widening the field to an interface; the
one-method-narrowing diff is small and review-friendly.

## HMAC webhook signature testing recipe

For Stripe-style schemes (`t=<ts>,v1=<hex hmac of "{t}.{body}">`):

```go
tsStr := strconv.FormatInt(time.Now().Unix(), 10)
mac := hmac.New(sha256.New, []byte(secret))
mac.Write([]byte(tsStr + "." + string(body)))
header := fmt.Sprintf("t=%s,v1=%s", tsStr, hex.EncodeToString(mac.Sum(nil)))
```

Cover the matrix: valid accept / tampered body reject / wrong secret reject /
unsigned reject / stale timestamp (>5min) reject — per provider scheme. For
dual-scheme providers (Stripe-compat header preferred + native fallback),
test each scheme independently AND that tampering under one scheme fails even
when the other header is present.

## Normalization-map table tests

Provider→internal event maps should be tested table-driven with three
classes of rows: every mapped entry (assert internal type AND that the shaped
payload keeps every field the downstream worker's parse struct reads — copy
the worker's struct fields into the assertion list), gotcha entries
(misleading names like "dispute.failed fires on dispute OPENED"), and at
least two unmapped entries asserting ok=false. Unknown-event handling must be
ACK-and-drop (200), never 5xx — test that explicitly at the handler level.

## Deterministic JobID/dedupe conventions

When a leaf pins a JobID convention (`"<provider>-<evtID>"`): unit-test the
prefix function for (a) all providers, (b) empty/legacy provider mapping to
the historical default byte-for-byte (dedupe compatibility with pre-change
jobs is a hard invariant), (c) same-ID-twice → identical JobID, (d)
cross-provider IDs never collide. The Redis-level atomic rejection itself is
integration territory; the Go-level test pins the deterministic mapping.
