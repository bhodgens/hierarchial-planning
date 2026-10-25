# Claim Temporal Validity — Leaf 03 implementation record (2026-09-05)

Session: implemented `docs/plans/claim-temporal-validity/03-surface-docs.md` in meept
(Go, TDD, "do NOT commit / do NOT git add"). Leaves 01+02 already in the working tree.
Kept so the future validation pass of this plan knows exactly what is landed vs parked.

## Landed (all green, uncommitted by design)

- `internal/tools/builtin/retain_typed.go`: `parseRFC3339Arg` helper (exact leaf error
  strings `invalid %s (want RFC3339)`); `RetainClaimTool` gains `valid_from` /
  `valid_to` / `observed_at` params (explicit three-block mapping, leaf-sanctioned);
  new `ListExpiredClaimsTool` (limit default 20, two-value metadata assertions,
  `reason: "expired"`) + interface assertion.
- `internal/tools/builtin/retain_typed_test.go`: `newTemporalTestManager` harness
  (mirrors `newVoteTestManager`: `NewManager` + sqlite `DataDir: t.TempDir()` +
  Episodic enabled); `TestRetainClaimTemporalParams` (6 cases incl. legacy-compat
  key-set-absence check and non-string arg errors); `TestListExpiredClaimsTool`
  (expired vs live vs unbounded, full output contract, `limit=0` fallback);
  nil-manager test. RED-first confirmed (`undefined: NewListExpiredClaimsTool`).
- `cmd/meept/memory.go`: `expired` subcommand mirroring the sibling RPC-client
  pattern (`connectDaemon` → `client.Call("memory.listExpired", {limit})`); parses
  both the tool-shaped `{claims:[...]}` and raw `MemoryResult` `{memories:[...]}`
  response shapes; prints `<id>  rev=<n>  valid_to=<RFC3339>  <text[:80]>` or
  `no expired claims`; `--limit` default 20.
- `docs/workflows/memory.md`: `### Claim Temporal Validity` under Behavior (after
  Personality Memory).
- `make docs-generate` run; generated `memory.md` contains `ListExpiredClaims` and
  the `ObservedAt/ValidFrom/ValidTo/Rev` fields. Not hand-edited.

## STOP items / open wiring — verify before calling this plan COMPLETE

1. **ListExpiredClaimsTool NOT registered.** One line pending in the
   `internal/daemon/components.go` epistemic block (~:5568):
   `registry.Register(builtin.NewListExpiredClaimsTool(memoryMgr))`
   Registration site was outside the leaf's 3-file scope AND on the
   concurrent-activity no-touch list, so the leaf's STOP-and-report fired.
   Until this lands the tool is built+tested but invisible to agents.
2. **RPC handler for `memory.listExpired` deliberately absent** (out of leaf scope;
   recorded as OPEN-QUESTIONS Q4). Live CLI proof of wiring:
   `./bin/meept memory expired --help` shows the default-20 flag; a live run
   completes the full daemon round-trip and returns
   `[-32601] method not found: memory.listExpired` (exit 1). That error is the
   CLI wiring proof, not a defect — blocked only on the Q4 handler.
3. `cmd/meept` has **no memory-command test harness** (leaf Task 3.2: noted, not
   built — out of scope per leaf).
4. `make docs-generate` regenerated **all 11** `docs/reference/generated/` files,
   not just `memory.md` — the shared tree already held leaves 01/02 code whose
   reference docs were stale. Build artifacts of the same target; orchestrator
   decides commit grouping.

## Verification evidence

`go build ./...` exit 0; `go vet ./internal/tools/builtin/ ./cmd/meept/` exit 0;
`go test -p 2 ./internal/tools/builtin/...` ok 5.3s; `go test -p 2 ./internal/memory/...`
ok (leaf 01/02 suites green on the shared tree). No commit, no `git add` (per leaf);
`bin/meept` is gitignored.
