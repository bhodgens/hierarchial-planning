# Adversarial Test Harness — Architecture Reference

Built in the `rebellion-the-game` project (plans-glm/13-adversarial-harness, 2026-07-20).
Reusable pattern for AI-driven simulation testing where an adversary LLM generates
edge-case probes and a teacher LLM evaluates correctness.

## Architecture

Three LLM roles in a feedback loop:

```
ADVERSARY LLM (high temp, 0.8)        TEACHER LLM (low temp, 0.1)
       │ generates scenario                   │ evaluates trace
       ▼                                       ▼
  ┌─────────┐    inject    ┌──────────┐    collect    ┌──────────┐
  │ Scenario │ ──────────► │ Sim Engine│ ───────────► │  Trace   │
  │  JSON    │             │ (N ticks) │              │ (facts,  │
  └─────────┘             └──────────┘              │knowledge,│
                                                     │transfers)│
                                                     └──────────┘
```

The adversary is given the full rule set and told "invent a scenario that breaks
rule X." The teacher is given expected behavior + simulation trace and asked
"did any rule fail?"

## Three Run Modes

| Mode | Seed | Rounds | Use |
|------|------|--------|-----|
| `ci` | Deterministic | N | CI gate — exits 0/1 |
| `fuzz` | Random | Infinite | Generative adversarial — mutates on violations |
| `interactive` | Any | REPL | Developer interrogation — `ask`, `trace`, `why`, `inject` |

## Key Implementation Decisions

1. **Stub fallback**: The runner works without LLMs connected — `generateScenario()`
   returns hardcoded 3-NPC scenarios, teacher evaluation is skipped. This means
   `make test` passes without a running LLM. LLM clients are injected via
   `WithAdversary()` / `WithTeacher()` builder methods.

2. **Trace formatter**: Converts the gossip engine's internal state (facts,
   transfer log, NPC knowledge) into an LLM-readable narrative before sending
   to the teacher. One sentence per transfer: "At tick 47, NPC#3 told NPC#7
   about fact#2, accuracy degraded to 0.59."

3. **Scenario persistence**: Every violation-producing scenario is saved to
   `testharness/scenarios/adversarial/` as a regression fixture.

## Remote LLM Wiring (httpAdapter Pattern)

The `llmbridge.LlamaClient` hardcodes `http://localhost` — it can only talk to
local llama.cpp instances. For remote endpoints (e.g., `http://socrates:8081`),
a minimal adapter satisfies the `llmbridge.Client` interface:

```go
type httpAdapter struct {
    name     string
    endpoint string
    client   *http.Client
}

func (a *httpAdapter) HealthCheck(ctx context.Context) error { return nil }
func (a *httpAdapter) ModelInfo() llmbridge.ModelInfo {
    return llmbridge.ModelInfo{Name: a.name, IsActive: true}
}
func (a *httpAdapter) Generate(ctx context.Context, req llmbridge.GenerateRequest) (*llmbridge.GenerateResponse, error) {
    // POST to a.endpoint + "/v1/chat/completions"
    // Parse the OpenAI-compatible JSON response
    // Return &llmbridge.GenerateResponse{Text: content}
}
```

This avoids modifying the llmbridge package while supporting any OpenAI-compatible
endpoint. The adapter lives in the CLI binary (`cmd/adversarial/main.go`) since
it's a deployment concern, not a library concern.

## Files

- `sidecar/internal/testharness/adversarial/runner.go` — loop controller
- `sidecar/internal/testharness/adversarial/adversary.go` — adversary LLM prompt + parser
- `sidecar/internal/testharness/adversarial/evaluator.go` — teacher LLM prompt + parser
- `sidecar/internal/testharness/adversarial/tracefmt.go` — state → narrative formatter
- `sidecar/internal/testharness/adversarial/interactive.go` — REPL shell
- `sidecar/internal/testharness/adversarial/scenario.go` — scenario injection
- `sidecar/cmd/adversarial/main.go` — CLI + httpAdapter

## Cloud Model Wiring (OpenRouter)

When using cloud models via OpenRouter (or any OpenAI-compatible API):

```
Endpoint:   https://openrouter.ai/api         ← NOT /v1 (adapter appends /v1/chat/completions)
Model:      google/gemini-2.5-flash-lite       ← fast, cheap (~5-10s per call)
Auth:       Authorization: Bearer $OPENROUTER_API_KEY
Body:       {"model": "google/gemini-2.5-flash-lite", "messages": [...], ...}
                                          ↑ must include model in request body
```

Key gotchas:
1. The `model` field must be in the request body — OpenRouter rejects requests without it
2. `MaxTokens` must be set (2048 for adversary, 1024 for teacher) — otherwise generation times out
3. LLM-generated JSON often has string IDs (`"id": "npc1"`) instead of ints — auto-assign IDs on parse
4. Witness NPC IDs may not match auto-assigned IDs — skip knowledge injection for unknown witnesses
