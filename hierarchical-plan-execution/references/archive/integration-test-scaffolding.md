# Iintegration test scaffolding
When to use: integration-test leaves.
Lesson: scaffolding pitfalls: fixtures, teardown, port allocation.

# Integration-Test Scaffolding Pitfalls

These are project-agnostic patterns discovered while building the adversarial
gossip test harness for rebellion-the-game. They apply to any situation where
you're injecting scenario data into a game/simulation engine from an external
source (LLM, JSON file, API).

## 1. Zero-default fields silently break core behavior

When a struct has fields that default to zero in Go (`int`, `float64`,
`time.Time`), and you construct instances via `Register()` or `SomeStruct{...}`
without explicitly setting derived fields, the engine appears to work but core
behavior is silently broken.

**Real case:** Facts injected via `gossip.Register()` had `MaxHops=0` (never
propagate) and `ExpiresAt=year-0` (immediately expired). Every test passed
because tests created facts with these fields explicitly set. The harness ran
30 rounds and found "no transfers" — but the engine was fine; the injected
facts were dead on arrival.

**Detection:** After running the scenario, query the engine's state directly:
`g.Facts()[0].MaxHops`, `g.Facts()[0].Expired(now)`. If every fact is expired
at tick 0, your injection is missing derived fields.

**Fix:** Prefer `CreateFact()` (which computes MaxHops + ExpiresAt) over
`Register()`. If you must use `Register()`, explicitly set:
- `MaxHops` (default: use `calculateMaxHops(importance)` or a generous constant)
- `ExpiresAt` (default: far-future sentinel like `Year: 9999`)
- `PropagationDepth` (default: 0)
- `Secret` (default: from scenario data)

## 2. Stub social infrastructure must be realistic

If your test harness uses stub implementations of social/relationship
interfaces, zero-default relationships mean NPCs never interact because they
fall below the gossip threshold.

**Real case:** `StubSocialReader{Relationship: 0, Trust: 0.5,
FactionRelationship: 0}`. Two opposite-aligned NPCs had compatibility=0.16 <
threshold=0.3 — never gossiped. Teacher LLM correctly reported "no transfers"
but couldn't explain why.

**Fix:** Use realistic defaults:
```go
Relationship(a,b) int { return 30 }        // slightly positive, not zero
Trust(a,b) float64 { return 0.6 }           // above common thresholds
FactionRelationship(fa,fb) int {
    if fa == fb { return 50 }               // same faction bonus
    return 0                                // different faction neutral
}
```

## 3. Lenient JSON parsing for LLM-generated scenarios

LLMs (especially smaller/cheaper models) produce JSON with quirks that
standard `json.Unmarshal` rejects. Custom `UnmarshalJSON` is essential for
robust integration.

**Common LLM JSON quirks:**

| Field type | LLM output | Fix |
|-----------|-----------|-----|
| `uint64` ID | `"npc1"`, `"scout"` | Auto-assign sequential IDs |
| `uint64` ID | `1.0` (float) | Accept both int and float |
| `string` field | `{"name": "tavern"}` | Extract from object |
| `string` field | `42` (number) | Convert to string |
| `float64` | `"0.7"` (string) | Parse float from string |
| `float64` | `10` (0-10 scale) | Normalize by /10 |
| `bool` | omitted entirely | Default to false |

**Pattern:** Define a `raw` struct with `json.RawMessage` for problematic
fields, implement `UnmarshalJSON`, try multiple parse strategies, fall back
to defaults. Never `return err` on a single field — degrade gracefully.

## 4. LLM provider quirks

- **Cohere (free tier):** rejects `system` and `assistant` role messages.
  Merge everything into a single `user` message.
- **Gemini Flash Lite:** works well with system+user but sometimes produces
  truncated JSON (fix: `MaxTokens=2048`).
- **Q2-quantized local models:** very slow (~2 min/prompt), use cloud for CI.
- **Message format compatibility:** single-user-message with `\n\n---\n\n`
  delimiter between system prompt and user message works on all tested
  providers.
