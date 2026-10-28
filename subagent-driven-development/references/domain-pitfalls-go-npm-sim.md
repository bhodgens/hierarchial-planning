# Go and Domain-Specific Subagent Pitfalls

When to use: dispatching subagents into Go monorepos, npm projects, simulation code, or projects with embedded resources and pre-commit hooks.
Lesson: domain-specific failure modes (JSON tags, embedded-count tests, node_modules staging, sim-phase ordering) are invisible at compile time and surface only in full test runs - bake the countermeasure into the dispatch context.

## Go: JSON tag pitfall

Go's encoding/json does NOT auto-match snake_case to CamelCase without explicit tags. Fields consumed by LLM-generated JSON MUST carry `json:` tags. A struct field `MaxResults int` silently marshals as `MaxResults`, and code expecting `max_results` reads zero. See `references/adversarial-test-infrastructure.md` for the fixture/evaluator pattern that catches this class.

## Go: unused var + init() dead code

Subagents that change implementation mid-task leave unused `var` + `init()` pairs (computing a weight by init() then selecting via a different function). Pre-commit U1000 blocks the commit. Always remove the dead block entirely - never `//nolint:U1000`. Scan after every Go subagent before attempting commit.

## Go: subagents creating new files can DELETE committed files

When told to create `internal/rpc/dispatch.go` and a committed file with that name already exists, the subagent may overwrite it - or rename its new file AND delete the original (real instance: 247 lines of committed cluster-dispatch types lost, caught only by `git diff --stat` showing `dispatch.go | 247 ----`).

Prevention: before dispatching any task that creates a new file, check whether the filename exists; if it does, specify the exact alternative filename in the context. Detection after every creating subagent:

```bash
git diff --name-status | grep "^D"
```

## Go: embedded-resource count tests

Projects with `//go:embed migrations/*.sql` or fixture directories often have a guard test with a hardcoded `const expectedCount = 10`. A subagent adding a migration or fixture compiles fine - the failure only surfaces in `go test`. When dispatching a task that adds files to an embedded/auto-discovered directory, instruct: search for count-based tests (`grep -rn "expectedCount" internal/db/*_test.go`) and bump the constant in the same change.

## Go: secure-defaults refactoring breaks test helpers

After refactoring server defaults to secure (TLS on, auth required), every test file creating servers via `DefaultServerConfig()` breaks on plain-HTTP connects. Pattern: search all tests for the default-config constructor and add explicit overrides (`cfg.UseTLS = false; cfg.RequireAuth = false`). Systemic: failures spread across packages and may not appear until the full `go test ./...`.

## npm: git add -A after subagent install commits node_modules

A subagent runs `npm install`; the parent's `git add -A` commits thousands of node_modules files (5,441 in one real commit); cleanup via `git rm -r --cached` was then blocked by the pre-commit hook mid-cleanup. Prevention: create `.gitignore` (`node_modules/`, `dist/`, `*.tsbuildinfo`) BEFORE dispatching any install-running subagent. Recovery: `git rm -r --cached <dir>` with `--no-verify`, or run cleanup commits before installing pre-commit hooks.

## Simulation: ID-derived fake coordinates

A `computeCentroid()` deriving positions from NPC IDs (`id % 100`) gives spatially-coincident candidates wildly different positions (two NPCs both at origin placed 50 units apart), silently failing proximity checks. Rule: if the candidate map key IS a position/bucket, pass it directly to the centroid function; never recompute from member IDs. Sanity check: `vecDistance(a.pos, b.pos)` for members sharing a cluster key must be ~0.

## Simulation: dispersed entities must clear member maps

When `Entity.Tick()` returns a dispersion event, the entity stays in the manager's list with old members intact - `prune()` sees 12 members and never removes the ghost. Fix: after `e.disperse()`, set `e.members = nil` so `MemberCount() == 0` and prune removes it. Otherwise the crowd entity persists silently forever, wasting a pointer and producing stale data.

## Simulation: per-alignment crowd entity pattern

Faction-gated group behavior via alignment bands (plus/minus threshold on a political axis): each band gets its own crowd entity with independent mood/morale/tension; opposing bands at one location accumulate cross-band tension; same-band groups merge. O(1) per crowd regardless of size. Injection: wire the subsystem tick as Phase N+0.5 BETWEEN existing phases (crowd dispersal facts must exist before perception resolves for newly-dispersed NPCs), never at the end. Debugging silently-failing tension: verify at three points - entity positions after formation, tension-pair iteration (`band.Opposing()`), proximity threshold; a failing step 3 usually means step 1 (wrong centroid derivation, above). A targeted debug test printing positions/distances/opposition catches it in minutes.

## Review-phase additions for external-API integrations

When reviewing code that integrates with an external API nobody has hit live this session, add to spec/quality review: (1) were endpoint URL, auth headers, and response field shapes verified against live docs or a live curl? (2) does the test fixture copy real API output, or the plan's (possibly stale) description? (3) for auth-bearing sources, is there a live verification step - if not, flag it. See `references/external-api-contract-verification.md` for the full 3-stage pipeline and real bugs mock-server tests cannot catch.
