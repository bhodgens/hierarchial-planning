# LLM Resilience Forest — Full-Forest Pre-Dispatch Audit (trees 01/03/04 + tree-02 leaf 04, 2026-09-01)

Independent architecture+functionality audit of all five trees + root docs at
HEAD 90fd2afb. Prior passes covered root docs, tree 05, the citation sweep, and
the tree-02/03 fix wave. This pass: tree 01 (escalation), tree 03 (park/resume),
tree 04 (scheduling), tree 02 leaf 04 (endpoint timeouts). Verdict: 3 blockers,
5 risks, 4 minors — plus structural facts confirmed sound.

## Blockers

### B1 — Tree 01 builds on a dead hook pipeline (registration ≠ dispatch)
`HookRegistry.RunPrepareNextTurn` (internal/agent/hooks.go:267) has ZERO
production callers — the only invocation anywhere is hooks_test.go:89. loop.go
invokes only RunSessionStart (loop.go:2059) and RunSessionEnd (loop.go:2123).
The hook IS registered (loop.go:1771) but never fired; handleFail
(verification_hook.go:119) is reachable ONLY via PrepareNextTurn
(verification_hook.go:109). Nothing in loop.go reads
TurnModification.ExtraMessages at all (only ModelOverride via the separate
GetModelOverride seam, loop.go:3219). The plan's premise — "the hook gives up
to the user at verification_hook.go:119-141" — describes code that never
executes; escalation would wire onto dead infrastructure. The same gap
silently disables the security/secret hooks registered at
components.go:1245,1263 (out of scope, but evidence the dispatch gap predates
the plan).
Fix shape: preliminary leaf wires RunPrepareNextTurn into the reasoning cycle
and applies the returned modification (ExtraMessages prepend; ModelOverride →
existing SetModelOverride, loop.go:1334).

### B2 — Resolver.ResolveRef name collision (compile error + interface unsatisfiable)
Tree-01 leaf 03's contract adds `func (r *Resolver) ResolveRef(ref string)
(string, error)` but internal/llm/resolver.go:294 already defines
`func (r *Resolver) ResolveRef(ref string) *ModelConfig` with live callers
(loop.go:3220, model_parser.go:410, registry.go:1237). Same receiver + name +
different signature = duplicate-method compile error, and *llm.Resolver can
never satisfy agent.ModelResolver as specced.
Fix: rename the new method (e.g. ResolveEscalationRef) in the contract before
dispatch.

### B3 — endpointBlocks on AliasHealth cannot deliver D10 cross-alias shared fate
Leaf 04 places `endpointBlocks map[string]time.Time` ON AliasHealth
(02-failure-policy/04-endpoint-timeouts.md:30-31,76) — a per-alias struct
(models.go:337-359, one per alias via getOrCreateHealth). D10/§4.3 requires a
timeout in alias "medium" to skip models in alias "thinkhard" — impossible
from per-alias state. SHARED-CONVENTIONS §7 itself says the state "lives on
the Resolver next to it" — the leaf contradicts the frozen conventions.
Fix: resolver-level map keyed by endpoint (+ credential, see R2), checked in
the same rotation walk as isQuotaBlocked (resolver.go:894+).

## Risks

### R1 — Q2 reset × one-shot override: the escalated budget silently shrinks to ONE turn
Escalation resets fixCount=0 (leaf 02 Task 2); subsequent verifier FAILs then
emit NORMAL fix-loop modifications carrying no model marker; and the loop's
SetModelOverride is one-shot (auto-cleared after first application unless
persistent, loop.go:3244-3246) while fresh model refs rebuild from spec.Model
(registry.go:1237). Leaf 03's "override applies only to the pending iteration"
therefore serves exactly ONE turn of the max_fix_loops budget Q2 promises the
escalated model. Fix: SetPersistentModelOverride (loop.go:1344) held for the
escalated budget + cleared on fresh-turn detection, or an escalation-active
window on the hook.

### R2 — host-only endpoint key over-blocks across providers/credentials
Config practice: gala-mlx and gala-llama are distinct providers/runtimes
sharing host `gala` (config/models.json5:186,205); xai and xai-oauth share
api.x.ai (:251,:275). A timeout on xai would block the unrelated OAuth
credential. The repo's quota logic already separates this via credentialBlock
keyed on credential fingerprint (models.go:356-358).
Fix: key = host + credential fingerprint (or provider+host), documented as a
§4.3 amendment.

### R3 — "mirror PricingSyncer's write path" yields no runtime updates; the plan's trace target was the display layer
Resolver.allModels is built ONCE at construction (resolver.go:61);
alias/default/small models are independent per-call copies via
ResolveModelRef→modelConfigFrom (providers.go:316-343,365+). The leaf's
suggested trace target, model_picker.go:37, reads the static DISPLAY catalog
(ModelCatalogEntry.ContextWindow, models_catalog.go:8) — the TUI picker, not
runtime. The real runtime consumer is ModelConfig.ContextLimit (models.go:220)
in context_firewall.go:353 etc. PricingSyncer writes only its own cache
(pricing_sync.go:161-169); enrichment into resolver models happens ONCE at
wiring (SetPricingSyncer, resolver.go:873-905; components.go:668). Mirroring
it = wiring-time-only values, never refreshed.
Fix: require a Resolver.SetContextLimits-style method mutating all four
pointer sets under r.mu (the SetPricingSyncer precedent); trace
context_firewall, not model_picker.

### R4 — queue jobs carry no session provenance; the interactive flag is frozen at enqueue
Job (queue/job.go:44-67) and StepJobPayload (tactical.go:32-40) have no
session field; the worker has zero session/conversation context (no matches
in internal/worker/worker.go); the enqueue sites (tactical.go:310,532;
services/queue_service.go:54; queue.go:598) have no *Session in scope. Origin
is recoverable only via Task.LinkedSessions (task.go:146, linked in dispatcher
createTask) and only for task jobs — one_off jobs have none. Also: the flag
is evaluated ONCE at enqueue; a job enqueued while the session is idle never
upgrades when the user returns before claim — weakening the forest E2E
expectation (master.md:99-100).
Fix: SessionID on StepJobPayload/Job (or TaskID→LinkedSessions lookup in
scheduleStep); document/enforce the enqueue-time-only semantics.

### R5 — ParkedTurn drops provider/credential identity into an untyped blob
Verified: resume re-sends the STORED payload, not a history reconstruction —
resumeQuotaParkedTurn re-runs RunOnceWithParts(ctx, turn.Message, turn.Parts,…)
(handler.go:1594-1595) from fields stored on QuotaParkedTurn
(quota_resume.go:18-20). So TurnPayload is genuinely needed (the plan's
assumption holds), but §4.5 has no home for ProviderID/CredentialKey
(quota_resume.go:22-23) which the re-park path (handler.go:1566-1586) needs;
they must ride inside the RawMessage with no declared encoding, while the
"byte-identical" wrapper tests depend on it.
Fix: declare the quota payload's JSON shape in §4.5 (or add optional identity
fields to ParkedTurn).

## Minors
- M1: "hook must NOT import llm if it does not already" (02-hook-wiring.md:52)
  — it already imports llm (verification_hook.go:12); the stated constraint is
  moot (the ModelResolver indirection is harmless).
- M2: tree-05 contract block says `ModelConfig.ContextWindow`
  (01-context-discovery.md:90) while its own Context section (:52) documents
  the field is ContextLimit — self-contradiction inside one leaf.
- M3: SHARED-CONVENTIONS §7 cites loop.go:~4226 for the RateLimitError branch;
  actual is loop.go:4298.
- M4: Classify sees only HTTP responses; transport timeouts (leaf 04's other
  cooldown trigger) have no status/body — no leaf names the transport-error
  classification path into RecordAliasFailure.

## Confirmed sound (no action)
- Classify(statusCode, header, body, now): header+body co-located at all three
  call-site families (client.go doRequest 1022-1049, doStreamRequest
  1434-1448; anthropic.go 1037-1061). Signature implementable everywhere.
- Import cycles: none (internal/llm imports no agent/queue/employee; queue
  imports only bus+stdlib; session imports bus/config/llm, not queue;
  employee imports agent+llm).
- Queue claim sites: exactly four ORDER BY priority DESC queries
  (store.go:379,390,624,684), matching leaf 02's claim.
- Tree 03 states: leaf 04's default (reuse StateQuotaWait + reason) needs no
  new transition-table entries (agent_state.go:268-282).
- agent.model_escalated would fall to eventType "event" today (server.go:703
  matches only the agent.quota prefix), but tree-01 leaf 03 explicitly
  instructs adding the prefix case — covered.
