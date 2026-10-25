# Adversarial Test Harness for Simulation Engines

Pattern proven in rebellion-the-game (Go gossip engine). An LLM-driven adversarial test harness
that probes a simulation engine for correctness defects by generating edge-case scenarios,
injecting them, running the simulation, and having a stronger "teacher" LLM evaluate the trace.

## Architecture

Three LLM roles in a feedback loop:

1. **Adversary LLM** (high temperature, 0.8) — invents probe scenarios targeting specific rules.
   Given the full rule set, generates JSON scenarios with NPCs, facts, and expected behavior.
2. **Teacher LLM** (low temperature, 0.1) — evaluates simulation traces against expected behavior.
   Formats the trace as a narrative (one sentence per event), scores plausibility, outputs structured violations.
3. **Harness runner** (deterministic, in-process) — the loop controller. Injects adversary scenarios,
   runs N ticks, collects the full trace, feeds it to the teacher, accumulates violations.

```
Adversary LLM → scenario JSON → runner → simulation engine → trace → Teacher LLM → violations
     ↑                                                                                    │
     └──────────────────── violations feed back for next round ───────────────────────────┘
```

## Critical Setup Pitfalls

### 1. Simulation defaults can silently prevent any behavior

When injecting scenarios into a simulation engine, every default that gates behavior must be set explicitly:

- **MaxHops must be > 0.** In a gossip engine, facts with MaxHops=0 are immediately filtered
  by the shareable-filter rule `propagation_depth >= max_hops` (0 >= 0 → true → skip).
  LLM-generated scenarios won't set MaxHops — the harness must default it to a generous value (e.g. 20).

- **Thresholds must be low enough for scenarios to exercise.** In a gossip engine, the default
  GossipThreshold=0.3 can silently prevent all propagation when NPCs have varied/opposite alignments.
  Lower it for adversarial testing (e.g. 0.15) so the simulation actually runs.

- **Relationships must be non-zero.** A stub SocialReader returning all zeros means
  NPCs have no reason to interact. Use reasonable defaults (relationship=30, trust=0.6,
  same-faction bonus=50) so scenarios exercise the engine.

### 2. LLM-generated JSON is never clean

Models will produce every possible JSON quirk. The harness parser must handle all of them silently:

| Quirk | Example | Fix |
|-------|---------|-----|
| String IDs | `"id": "npc1"` | Auto-assign sequential numeric IDs on parse failure |
| Number subject | `"subject": 0` | Accept int/float, convert to string |
| Object location | `"location": {"name": "tavern"}` | Extract `.name` field |
| Out-of-range importance | `"importance": 10` | Divide by 10 if >1 (0-10 scale assumption) or clamp |
| Markdown-wrapped JSON | `` ```json ... ``` `` | Strip fences before parsing |
| Truncated JSON | `{"npcs": [` | MaxTokens cap on response; retry once |

Implementation: custom `UnmarshalJSON` methods on scenario types that accept both
string and numeric forms, falling back to defaults on failure.

### 3. Cloud LLM integration via httpAdapter

When the local model isn't fast enough, use an `httpAdapter` that satisfies the
existing `llmbridge.Client` interface for any OpenAI-compatible endpoint:

```go
type httpAdapter struct {
    name     string
    endpoint string
    apiKey   string
    model    string   // model name in request body (required by OpenRouter/OpenAI)
    client   *http.Client
}

func (a *httpAdapter) Generate(ctx context.Context, req GenerateRequest) (*GenerateResponse, error) {
    body := map[string]interface{}{
        "model":       a.model,       // cloud providers need this
        "messages":    req.Messages,
        "temperature": req.Temperature,
        "max_tokens":  req.MaxTokens,  // ALWAYS set to prevent runaway generation
    }
    // ... POST to a.endpoint+"/v1/chat/completions" with Bearer auth
}
```

Key points:
- Always set `max_tokens` on the request — unset allows runaway generation
- Always set `model` in the request body for cloud providers
- Bearer auth: `Authorization: Bearer <key>` header
- Implement `HealthCheck()` returning nil, `ModelInfo()` returning name+active
- 120s timeout on the HTTP client, with a shorter per-round context deadline (3-5 min)

### 4. Trace formatting for LLM consumption

The teacher LLM needs a narrative trace, not raw struct dumps. Format each event as a
readable sentence:

```
At tick 47, NPC#3 (Sarah) told NPC#7 (Mary) about fact#2 (theft at market, importance=0.70).
  Teller accuracy: 0.80. Listener received at accuracy: 0.59.
  Alignment similarity: -0.3 (SLOW band — accuracy penalized ×0.60).
```

Include: facts summary, transfer log (one sentence per transfer), per-NPC knowledge
entries with accuracy, confidence, and emotional valence.

## Run Modes

| Mode | Use |
|------|-----|
| CI (deterministic) | `--seed=N --max-rounds=N` — reproducible, exits 0/1 |
| Fuzz (infinite) | `--mode=fuzz` — runs until ctx cancelled or max rounds |
| Interactive (REPL) | `--mode=interactive` — `ask "why didn't NPC#5 learn?"`, `trace fact 2`, `repr`, `inject "..."` |
