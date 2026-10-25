# Config-gate wrong-reason RED (2026-09-06, metrics retention leaf)

## The shape

TDD leaf calls for testing behavior behind a config gate. First RED run
fails — but at the CONTROL assertion, not the target one. In this session:
retention test asserted (a) dispatch_log purged [control], (b) llm_calls
survived [target]. Run 1 failed at (a) with NEITHER table purged — because
the test store was built without `RetentionDays`, the constructor does NOT
apply the package default (only `DefaultStoreConfig()` does), so the entire
purge block (`if s.retentionDays > 0`) silently no-op'd. The target
behavior could not even execute.

## The rule

RED must fail at the TARGET assertion with the expected message. A
control/setup assertion failing first means the test cannot exercise the
behavior at all — diagnose setup (config defaults, fixtures, gate
polarity) and re-run RED before writing any implementation. Implementing
against a test that never reaches the target assertion "fixes" nothing
and can mask a real bug.

## The Go pattern behind it

Zero-value config gates: `type Config struct{ RetentionDays int }` with
`if cfg.X > 0` behavior — the default lives in `DefaultXConfig()`, not
the constructor, so `&Config{}` silently disables the feature. When a leaf
test must exercise gated behavior, construct the store/config EXPLICITLY
with the package default constant rather than reusing a minimal helper.
See also references/go-zero-value-traps.md and (meept-specific)
meept-development skill → references/metrics-store-retention-gotchas-2026-09-06.md.

## Triage recipe

1. Read WHICH assertion failed. Control first → setup problem, stop.
2. Grep the gate: what condition wraps the behavior? What does the test
   config actually pass? Is the default applied in the constructor or
   only the Default*Config() helper?
3. Fix the test setup (explicit default), re-run RED, confirm the target
   assertion now fails for the documented reason.
4. Then implement; GREEN; full suite.
