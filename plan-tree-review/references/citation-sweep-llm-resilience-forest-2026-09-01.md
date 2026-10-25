# Citation sweep — llm-resilience-forest @ HEAD 90fd2afb (2026-09-01)

Task: verify every file:line citation in `docs/plans/llm-resilience-forest/` against
current HEAD. 26 files, ~94 citations. Read-only; corrections reported for a later
fix session, NOT yet applied to the plan docs.

Verdicts: ~94 ACCURATE · 13 DRIFTED · 0 WRONG · 3 STALE-CONCEPT.
Every cited symbol still exists; nothing was renamed away or deleted.

## Flags worth surfacing to implementers (not just line numbers)

1. **The "five loops" grep recipe undercounts.** `grep "for attempt := 1"` in
   client.go/anthropic.go finds only 4 loops (client.go:426, 586; anthropic.go:281,
   448). The fifth (streaming-delta, client.go:1269) is
   `for attempt := range streamMaxRetries` — a separate constant (`streamMaxRetries`),
   not `maxRetries`. Affects "locate via grep `maxRetries`" instructions in
   02-failure-policy/03-client-unification.md:25/:48. The five-loop count itself is
   confirmed correct.
2. **`ModelConfig` has no `ContextWindow` field — it's `ContextLimit`**
   (internal/llm/models.go:220, line correct, name wrong; catalog entries use
   `ContextWindow`, config consumer uses `ContextLimit`). 01-context-discovery.md:52.
3. **goal_loop's stub seam is named `Reflector`, not `Chatter`**
   (internal/employee/goal_loop.go:197–200 — line range correct; it's *satisfied by*
   llm.Chatter). 03-goalloop-queue-coverage.md:50. Grepping `` `type Chatter` `` in
   internal/employee finds nothing.
4. **Two semaphore construction sites**: client.go:249 (`WithConcurrencyLimit`
   option) and client.go:269–270 (NewClient). 03-model-slot-fairness already says
   "find every construction site," so no design change.

## Drift table (exact corrections to apply)

| File | Citation | Correction |
|---|---|---|
| SHARED-CONVENTIONS.md:174 | `loop.go:~4226` rate-limit branch | loop.go:4298 (`errors.As` RateLimitError; loop.go is 6773 lines) |
| 01-escalation/master.md:25 | `verification_hook.go:119-141` | handleFail now 119–170 |
| 01-escalation/02-hook-wiring.md:26 | `verification_hook.go:119-141` | 119–170 |
| 01-escalation/02-hook-wiring.md:118 | "handleFail, lines 127-141" | 127–170 |
| 02-failure-policy/01-classification.md:53 | `client.go:1442-1460` | 1442–1461 (comment at 1442 ✓, close brace 1461) — trivial |
| 02-failure-policy/03-client-unification.md:55 | `loop.go:~4226` | loop.go:4298 |
| 02-failure-policy/03-client-unification.md:25,48 | grep `maxRetries`/`for attempt := 1` for 5th loop | 5th loop = `for attempt := range streamMaxRetries`, client.go:1269 (stale-concept, see flag 1) |
| 02-failure-policy/04-endpoint-timeouts.md:50 | `models.go:322-359` AliasEntry | 322–328; `Timeout` field at :324 |
| 02-failure-policy/04-endpoint-timeouts.md:54 | resolver.go `~line 376-428` rotation | quota-block rotation walk ~406–433 |
| 03-turn-lifecycle/02-throttle-parking.md:48 | `loop.go:~4226` | loop.go:4298 |
| 03-turn-lifecycle/04-states-visibility-docs.md:24,55 | `agent_state.go:263-278` transition table | entries ~268–282; `StateQuotaWait` entry at :282 (both occurrences) |
| 04-scheduling/master.md:40 | `client.go:268` semaphore | 269–270 (make at :270; also :249 via option) |
| 04-scheduling/03-model-slot-fairness.md:26 | `client.go:268-269` quoted make-line | 269–270 |
| 05-catalog/01-context-discovery.md:52 | "ModelConfig.ContextWindow" at models.go:220 | field is `ContextLimit` (stale-concept, see flag 2) |
| 03-turn-lifecycle/03-goalloop-queue-coverage.md:50 | "how to stub — Chatter interface (line ~198-200)" | interface is `Reflector`, goal_loop.go:197–200 (stale-concept, see flag 3) |

DRIFTED rows: 13 citation sites; STALE-CONCEPT rows: 3.

## Clean files — all citations accurate, no action needed

SHARED-CONVENTIONS.md (except :174), DECISIONS.md, root master.md (self-check grep
only), 01-escalation/01-spec-config.md (all 7 accurate: registry.go:836 exact,
spec.go:74–119 exact, Model:98 / EnhancerModel:101, agents/models.go:190,
registry_test.go:326), 01-escalation/03-resolution-lifecycle.md (resolver.go:269
"Escalated to model for skill" exact, registry.go:375–376, SpawnVerifier hook:84,
timeout handling ~:84), 02-failure-policy/master.md, 02-retryafter-schedule.md
(errors_quota.go 131/235/290/331 all exact; client.go:25–27), 02-failure-policy/
05-adaptive-pacing.md (GetRateLimitSummary ~725: func :726, comment :725),
03-turn-lifecycle/01-generalize-parker.md (quota_resume.go 47/150/208/40-42/65 all
exact), 03-turn-lifecycle/02-throttle-parking.md (except :48; errors_quota.go:41
UserMessage, loop.go:4375 both exact), 03-goalloop-queue-coverage.md (except :50;
633/1049, store.go 351/779 exact), 03-turn-lifecycle/master.md (prose only),
04-scheduling/01-session-signal.md (session.go:65–103, LastActivity:71,
AttachedClients:72), 04-scheduling/02-queue-priority.md (store.go 379/390/624/684,
734, 351, 301, DDL 63–77, job.go:44–67), 04-scheduling/03-model-slot-fairness.md
(except :26; providers.go:54 ×2, client.go:265–275, inuse.go exists),
04-scheduling/master.md (except :40), 05-catalog/master.md, 05-catalog/
02-docs-and-config.md, 05-catalog/01-context-discovery.md (except :52; pricing_sync
62/74, models_catalog 8/246, model_picker.go:37), 05-catalog/03-lmstudio-provider.md
(all 5 accurate: reasoning_translate.go:65, ProviderIDOllama const :17, registry
entry :110 in 100–120, catalog entries 87–101).

## Explicitly-asked non-line claims

- "Five client retry loops" — CONFIRMED: client.go:426, 586, 1269 (delta/stream);
  anthropic.go:281, 448. Caveat: 5th loop's constant is `streamMaxRetries`.
- `maxRetries = 3` at client.go:25-27 — accurate (:25).
- Queue ORDER BY at store.go 379/390/624/684 — all four verified.
- LastActivity at session.go:71 — accurate.

## Method note

Inventory via two multi-syntax greps over the docs dir, batched verification (~10
terminal calls for ~94 citations), semantic anchoring (leading anchor must match;
trailing bound = block close ±1 line; `~N` anchors verified against the described
region). Full method encoded in the SKILL.md Phase 1b "Citation-sweep audits"
subsection.
