# Fforest followups session 2026 09 02
When to use: completion-report follow-ups via subagents.
Lesson: F1-F4 fix shapes for forest close-out.

# Forest Follow-Ups Session — 2026-09-02 (llm-resilience-forest close-out)

The four completion-report follow-ups (F1–F4) were fixed via parallel
delegated subagents. This file records what was durable beyond the commits
themselves.

## F1+F2: llm suite real-sleep slowness (308s → 14s)

- **The seam already existed.** Tree 02 leaf 03 shipped a nil-safe
  `Client.SetFailurePolicyConfig` (unexported field, production
  constructors cannot set it inline). Before adding any new seam, grep for
  `SetFailurePolicyConfig` / `WithFailurePolicy` in the package — the fix
  was test-only wiring of an existing seam, zero new production surface
  beyond `ProviderManager` gaining the same setter.
- **Diagnosis beat the brief.** The dispatch guessed the ~90s quota test
  waited in a quota wait-loop. Wrong: the quota cases exit on one hit
  instantly — the cost was the *plain-429 sibling subtest* in the same
  table sleeping through 30s/60s throttle steps. Always trace the actual
  wait source (log-timestamp deltas: attempt=1 → attempt=2 30s apart =
  real backoff steps) before designing the fix.
- **Guard tests pin both directions**: tiny-config applies (throttle loop
  <5s wall) AND untouched-manager resolves package defaults (30s/1h/24h/3).
  A seam without a defaults-pin test can silently change production
  behavior for unconfigured callers.
- Real sleeps remain in a few provider_manager tests only as
  `TestProviderManager_ContextCancellation`'s server-side sleep — bounded,
  cancellable, no longer the suite bottleneck.

## F3: ephemeral-port exhaustion on full sweeps

- **Two-layer fix, dose-response verified** (unbounded → 17–23 failures;
  `-p 4` → 1; `-p 2` → 0): layer 1 = invocation bound
  (`TEST_PACKAGE_PARALLELISM ?= 2` in Makefile, mirrored in CI + AGENTS.md);
  layer 2 = comm/http's shared test client (singleton, MaxIdleConnsPerHost=1,
  1s IdleConnTimeout, t.Cleanup drain via startTestServer) plus a DialContext
  retry scoped EXACTLY to EADDRNOTAVAIL ("assign requested address" substring
  via errors.As chain through net.OpError → os.SyscallError). Every other
  dial error still fails fast.
- **The failing dial is the CLIENT, not the server.** The readiness probe in
  startTestServer had JUST connected successfully — the server was up; the
  outbound dial hit EADDRNOTAVAIL at the burst moment. Don't debug the
  server when the signature is a client dial error.
- **Each test building a fresh `http.Client` = fresh Transport = fresh
  connection pool** parked in keep-alive up to 90s after the test ends.
  27 tests × pooled conns × parallel packages = the exhaustion multiplier.
  A shared package-level test client with bounded pooling is the generic
  cure (unified_http_test.go `insecureHTTPClientOnce`).
- **macOS 26 diagnostics gotchas**: `netstat` output is lsof-style with no
  TCP state column; user-level `lsof` cannot see kernel-held TIME_WAIT.
  Reliable signal = failure-signature counting in the test log
  (`grep -c "can't assign requested address"`), sampled per run.
- **Post-fix verification ran at BOTH levels**: the F3 subagent verified
  `-p 4` (its dispatch-time default) and the orchestrator verified `-p 2`;
  the final stress proof was a full `-p 4` sweep AFTER the layer-2 dial
  retry (86 ok, EXIT:0, zero port errors). A bound that only works at the
  tighter setting is untested headroom, not a fix.

## F4: mergeSpec Verification/Gap omission (D16 closed)

- `mergeSpec` (registry.go ~:850) handles Model/EnhancerModel/
  EscalationModel but had zero Verification/Gate handling — re-loads of a
  registered agent silently dropped those frontmatter blocks. Fix mirrors
  definitionToSpec semantics: present block converts (verificationFromMetadata
  / NormalizeGateDefaults), omitted block preserves current (gate
  shallow-copied to avoid aliasing). Gate cannot be CLEARED via re-load
  (same as definitionToSpec).
- **Fixture trap**: `NormalizeGateDefaults` re-normalizes a
  programmatically-set `SkipWhenUnchanged: false` back to `true` (the
  `skipExplicit` flag is YAML-parse-only, models.go:136-141 caveat). The
  override test must parse real frontmatter via `agents.ParseAgentText` —
  which also exercises the realistic re-load path.
- TDD held: both new tests were RED before the fix (the gap predicts
  exactly their failure mode).

## Process notes

- **Commit race is benign when the orchestrator verifies first**: the F1+F2
  subagent's work landed as 70638e01 while the subagent was still running
  (orchestrator verified the diff then committed). The subagent detected
  HEAD moved, confirmed the content was its own, and reported cleanly
  instead of reverting. Dispatch contexts for subagents on shared trees
  should say: "if your exact work already appears committed, verify and
  report rather than re-implement or revert."
- **Parallel leaf dispatch needs surface fencing** (leaf 02 inside loop.go
  vs leaf 03 in employee/queue) AND a note for read-only consumption of
  shared new files (parked_turn.go): "if you need an exported helper from
  it, note it in Deviations instead of editing."
- The leaf-04 double-implementation collision (parallel session committed
  3eb6a3e3 while our subagent explored) resolved cleanly because the
  subagent pivoted to verify-and-fill-gaps — and found a REAL gap
  (SetParkEventBus never wired in the daemon; park events invisible in
  production despite docs claiming otherwise). "Already implemented" is
  the start of review, not the end.
