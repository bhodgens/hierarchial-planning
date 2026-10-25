# LLM Resilience Forest — Root-Docs Audit (2026-09-01, READ-ONLY)

Design review of `docs/plans/llm-resilience-forest` ROOT docs (master.md,
DECISIONS.md, SHARED-CONVENTIONS.md) + 5 tree masters, pre-dispatch.
Verdict: structurally sound; 3 ship-blocking majors + 3 minors. Do not
dispatch any leaf until the majors are fixed.

## Majors

1. **Stale anchor `loop.go:~4226`** — actual RateLimitError branch is
   `internal/agent/loop.go:4298` (~72 lines drift). Propagated to THREE sites:
   SHARED-CONVENTIONS.md §7 (:173-174), 02-failure-policy/
   03-client-unification.md:55 and :155.
2. **Contract-3 owner misattribution** — 02-failure-policy/master.md:134
   says "Owner: 04-endpoint-timeouts.md" but merges two leaves' artifacts:
   `ThrottleBackoffError` is defined + owned by 03-client-unification.md
   (:35 type, :52 "Modify internal/llm/errors.go"); leaf 04 owns only
   `EndpointKey` + `endpointBlocks`.
3. **Forest-root consumer arrows wrong** — master.md:49-51:
   §4.1 "PolicyVerdict (02 → 01/03/04)": tree 01 never references
   PolicyVerdict anywhere → should be (02 → 03/04). §4.4 "Interactive job
   flag (04 → 03)": tree 03 never references Interactive/§4.4 → consumer is
   tree 04's own leaves only. SHARED-CONVENTIONS.md §4.1 header (:73) has the
   same wrong consumer set.

## Minors

4. `01-escalation/03-resolution-lifecycle.md:45-46` — "ResolveForAlias line
   ~85 timeout handling": func is resolver.go:352; timeout defaulting :84-89.
5. "hardcoded `maxRetries = 3`" (SHARED-CONVENTIONS §7:170-171; 02 master
   checklist :194) — actually THREE constants: client.go:25 `maxRetries`,
   client.go:28 `streamMaxRetries`, anthropic.go:25 `anthropicMaxRetries`.
   Literal-name grep catches 1/3.
6. SHARED-CONVENTIONS.md:130 `//internal/queue/job fields` — missing space
   after `//`; file is `job.go`.

## Verified clean (true 2026-09-01; re-grep before trusting)

D1–D15 each owned by ≥1 leaf; Q1–Q4 defaults carried into the right leaves;
§4 field shapes identical across all restatements; leaf counts 3/5/4/3/3
match disk; `lint-ci`/`analyzers`/`graphs`/`graphs-check` Makefile targets
exist; retry loops client.go:426/586 + anthropic.go:281/448;
classifyQuotaDecision errors_quota.go:131; reflector.Chat goal_loop.go:633 +
1049; "01 and 02 both touch internal/llm + internal/agent" stagger rule
correct; 03-gated-on-02 dependency consistent in 3 places; AgentSpec
spec.go:74-119 (yaml tags, no toml); entryBlocks / CooldownUntil /
resolveStickyCaller all in resolver.go; `h.fixCount` verification_hook.go;
SpawnVerifier at :84 via `h.config.EffectiveModel(state.ModelRef)`;
routing_log.go exists; LastActivity session.go:71; claim SQL store.go
:379/:390/:624/:684; MaxConcurrency semaphore client.go:268;
GetRateLimitSummary metrics/store.go:724; capability-escalation precedent
resolver.go:269; inuse.go exists; AGENTS.md carries the quota invariants
(:199/:205/:213).

## Status

Findings reported, not fixed (READ-ONLY mandate). Once the user lands the
fixes, this file is historical record — do not re-audit from it, re-grep.
