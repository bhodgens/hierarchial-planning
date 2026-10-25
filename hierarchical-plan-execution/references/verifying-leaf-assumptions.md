# Verifying Leaf Assumptions Before Implementation

Leaf/planning documents state facts about the codebase that were written at
planning time. Treat every such claim as a hypothesis. Run a discovery pass
(search_files / grep / targeted reads) BEFORE writing tests, and record each
confirmed-or-corrected finding in the deviation notes the leaf requires.

## Claim types to always verify

| Claim type | Why it drifts | Verify by |
|---|---|---|
| Namespace / prefix conventions (`computer.` style) | Naming decided by registration code, not the planner | Find where external items get registered/namespaced |
| Config/catalog field names (`id` vs `name`) | Template prose paraphrases the schema | Read the struct/loader, match sibling entries byte-style |
| Line-number anchors (`~512`, `lines 9-19`) | Code moves between planning and execution | Re-locate by symbol name, not line |
| "X lives in one place" | Most cross-cutting concerns have 2+ enforcement/validation layers | Trace the REAL runtime call path end-to-end |
| Test-count / rule-count assertions | Counts grow | Check the asserting test's tolerance before adding entries |
| Test read-paths ("load it back with GetByID") | Planner never EXECUTED the flow; a pinned production step (e.g. mark row non-current) can make the pinned test's loader return not-found by design | Trace the production flow's writes against the test's read filter; when red, see `leaf-pinned-test-impossible-read-path.md` |
| "No X exists in <pkg>" (empty-search conclusions, e.g. "no test fixtures") | The search itself may be malformed — a REGEX passed where file discovery needs a GLOB silently returns zero results (`search_files(target='files', pattern='.*_test\\.go$')` → 0, though the dir had 6 fixtures) | Re-run empty results with a plain glob (`*_test.go`) or `ls` before believing them; zero hits in a directory that should match is a tooling suspect, not a fact |
| Framework method signature quoted in leaf prose (`Execute(ctx, args json.RawMessage)`) | Prose paraphrases from memory; the in-tree interface the SAME spec cites is authoritative and may differ (`Execute(ctx, args map[string]any)` — real case, skill-authoring leaf 01, 2026-09-05) | Read the interface file the spec names and match ITS signature; record the prose mismatch as a documented deviation |
| Framework interface method SET summarized incompletely (master: "implement Name/Description/Parameters/Execute") | The interface may require more methods than the summary lists (IsReadOnly, IsConcurrencySafe, Category) | Embed the framework defaults struct (e.g. tools.ToolDefaults) and grep an existing sibling tool for the full required method set |
| Producer→consumer CHAIN behavior ("create then patch works"; "the agent can read the whole output") | Green unit tests prove leaf-local behavior, not the delivered chain; a tool's effective output bound is min(tool cap, agent-loop per-result cap), and write-side features may skip a registration the read side needs | After the tree closes, grep the delivered producer→consumer chain end-to-end (skill-authoring tree 2026-09-06: WriteSkill never Registered into the registry, so same-session create→patch failed until restart — and the leaf-05 wiring test MASKED it by hand-registering the skill before patching; a test that hand-feeds its dependency hides exactly that gap. Also: a size-bounded tool shipped a 100k output cap the loop's ~9k per-result cap made unreachable) |

## The multi-layer wiring trap (highest cost when missed)

Plans often name ONE subsystem ("the SecurityEngine") for a gating feature.
The live request path may flow through several layers, each with its own
default posture. If you gate only the documented layer, another layer's
fail-closed default (deny unknown actions / medium-default escalation) blocks
the feature entirely — the catalog entry exists, the rules exist, and nothing
ever reaches them.

Rule: before implementing rules/policies, trace the actual execution path
(e.g. executor → action-map → checker) and enumerate EVERY layer whose
decision can deny the call. Gate all of them; test all of them. Note the
extra layers as deviations if the leaf named only one.

Concrete instance (meept, containment leaf 08): "SecurityEngine risk rules"
meant BOTH `internal/security.Engine` (DB-backed seed tables, MEDIUM fallback
for unknowns) AND `pkg/security.PermissionChecker.BuiltinRules` (in-memory,
used by the agent Executor, hard-denies unknown actions). A dotted MCP tool
name hits the second layer first in production.

## API-semantics traps

Read return-value contracts from source, never infer from name shape:
- `lookupBaseRule`'s second return is the RULE-LEVEL `requires_confirmation`
  flag, not a "matched" bool. Returning `true` there escalates even LOW-risk
  actions through the confirmation gate via `needsConfirmation(risk) ||
  baseConfirm`.
- Consequence for tests: assert pipeline-visible behavior (`engine.Check(...)`
  → Allowed/RiskLevel/RequiresConfirmation) for gating semantics, and use
  internal-function tests only for classification values.

## Shared-classifier pattern that worked

Implement the classification ONCE in the lower/foundational package
(`pkg/security.ComputerUseRule`) and import it from the higher package
(`internal/security`, aliased `pkgsecurity` because both packages are named
`security`). Both layers then cannot drift apart, and table-driven tests exist
per layer plus one direct classifier test.

Fail-closed shape: known-safe names → LOW; everything else under the prefix —
including unknown future actions and degenerate bare-prefix names — → HIGH
(confirmation-gated). Never let unknown members of a gated family fall through
to a generic lower-risk default.

## TDD sequence

1. Write failing table-driven tests per layer covering: safe class, gated
   class, unknown-member fail-closed, non-member unchanged.
2. Implement shared classifier; wire each layer.
3. Run full package suites (not just new tests) — gating changes ripple into
   existing permission tests.

## Leaf-embedded test code is a hypothesis too (2026-09-05, meept auditlog leaf 02)

Leaves increasingly ship complete test files as "Step 1 — failing test".
Those fixtures carry the same planning-time drift as prose claims, because
the planner never RAN them:

- **Regex-matched fixture strings**: a leaf scrub test used
  `"connected with «redacted:sk-…» ok"` as its credential-looking string for
  internal/security's OutputMonitor — but the openai_key pattern needs
  `sk-` plus 32+ alphanumerics and the ellipsis defeats it, so
  `DetectAndRedact` returned `changed=false`. The test would fail against
  the CORRECT normative implementation. Verify every fixture that asserts
  "X must be detected / redacted / matched" empirically before trusting
  it — a RED-phase compile failure proves nothing about fixture validity,
  and a GREEN run against a fixture-adapted implementation would silently
  encode the broken fixture.
- **Leaf test code violating repo gates**: the same leaf contained
  `_ = Migrate(...)` (ignored error — pre-commit errcheck rejects it) and
  single-value map assertions `m["k"].(string)` (repo convention:
  two-value). Test files are linted too. Fix the TEST as a documented
  deviation; never relax the repo rule to match the leaf sketch.
- **"ADJUST to real enum" placeholders**: resolve against the actual
  constants before the first compile (search the enum block), not as a
  separate cleanup pass.
- **Claims the leaf marks pre-verified** ("no import cycle, verified"):
  re-check cheaply with `go build ./<pkg>/...` before building on them.

### Cheap empirical probe — where to put it

Probe contested fixtures with a one-off test run BEFORE Step 1. Prefer
APPENDING a temporary probe func to an existing `*_test.go` in the package
under test (patch in, run, patch-revert) over creating a scratch package
directory: `rm -rf` on scratch dirs inside the repo needs user shell
approval (denied twice mid-run 2026-09-05), and the leftover untracked dir
pollutes the orchestrator's `git status` staging review — the leaf's
review checklist expects changes ONLY in declared files.

### Denied commands propagate down the delegation chain (2026-09-05, skill-authoring tree)

A shell denial is a USER decision, and it binds the whole session tree.
Leaf-01's `rm -rf` of its own scratch dir was denied; its report told the
orchestrator "delete it before review"; the orchestrator — treating the
report's suggestion as new authorization — re-attempted the same `rm -rf`
and was blocked with an ESCALATED warning. A subagent's denial is not a
suggestion queue for the parent. When a leaf leaves an artifact you would
rather not have:

- NEVER re-attempt the denied command class, even via a different command
  with the same outcome, and even because a subagent report asked for it.
- The non-destructive alternative is staging exclusion, not deletion:
  leave the untracked dir in place, stage per-leaf file lists explicitly
  (never `git add -A`), and surface the leftover dir in the completion
  report's Observations so the user removes it on their own terms.

## Phantom referenced test scaffolding (2026-09-05, meept claim-temporal-validity leaf 02)

A leaf's "reuse the fake classifier / manager scaffolding from
`epistemic_detection_test.go` — do not invent a new harness" named a file
that contained NO fake classifier (only zero-value detector and JSON-parse
tests). The "do not invent" instruction presupposed a harness that
planning-time reading never confirmed. New claim-type row:

| Referenced test scaffolding ("reuse the fake X in Y_test.go") | The named helper may never have existed, or lives in a sibling test file | search_files for the type/interface name in the package before committing to the reuse plan |

If absent: create the minimal fake (one struct + one method satisfying the
interface) inside the leaf's own allowed test file, and record the deviation.
Do not silently expand scope into other files to "find" it.

## Leaf snippets vs the leaf's own pinned contracts

When a leaf's inline implementation snippet conflicts with its Interface
Contract section, the CONTRACT wins; treat the snippet as a sketch. Instance:
Task 3's snippet for `FindCanonicalFor` was a bare two-line exclusion, but
contract C3 mandated "Every exclusion the leaf adds is accompanied by an
slog debug line carrying `claim_id` and `reason: "expired"`". Correct
resolution: add the debug line to BOTH loops (capturing the manager's logger
under the existing RLock so no I/O runs under the mutex), and note it as a
deviation from the snippet. Scan the contract section BEFORE implementing —
it overrides per-task snippets, and deviations from snippets (never from
contracts) are legitimate, documented adjustments.
