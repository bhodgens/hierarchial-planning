# LLM-Generated JSON Leniency

LLMs (especially quantized/small models) produce JSON with type violations.
When consuming LLM output, add lenient parsing that handles:

## Common LLM JSON Quirks

| Quirk | Example | Fix |
|-------|---------|-----|
| String IDs instead of numbers | `"id": "npc1"` | Custom UnmarshalJSON: try number first, then parse string as number, then auto-assign |
| Objects where strings expected | `"location": {"name": "tavern"}` | Try string first, then object.name |
| Numbers where strings expected | `"subject": 0` | Try string first, then number → format as string |
| Out-of-range values | `"importance": 8` | Clamp, or normalize (divide by 10 if > 1) |
| Truncated JSON | LLM hits max_tokens | Set generous MaxTokens (2048), retry on parse failure |
| Missing fields | LLM omits optional fields | Set sensible defaults in the struct (zero-value for bools, "player" for subject) |

## Pattern: Custom UnmarshalJSON with Fallback

```go
type ScenarioNPC struct {
    ID uint64 `json:"-"`
    // ...
}

type scenarioNPCRaw struct {
    ID json.RawMessage `json:"id"`
    // ...
}

func (s *ScenarioNPC) UnmarshalJSON(data []byte) error {
    var raw scenarioNPCRaw
    json.Unmarshal(data, &raw)
    
    // Try numeric first.
    var idNum uint64
    if json.Unmarshal(raw.ID, &idNum) == nil {
        s.ID = idNum
        return nil
    }
    // Try string that parses to number.
    var idStr string
    if json.Unmarshal(raw.ID, &idStr) == nil {
        if _, err := fmt.Sscanf(idStr, "%d", &s.ID); err == nil {
            return nil
        }
    }
    // Non-numeric string: auto-assign 0, caller renumbers.
    s.ID = 0
    return nil
}
```

## Post-Unmarshal Normalization

After JSON parsing succeeds, run a normalization pass to fix remaining issues:

```go
func ParseScenario(data []byte) (*Scenario, error) {
    var s Scenario
    json.Unmarshal(data, &s)
    // Auto-assign IDs for NPCs with non-numeric IDs.
    for i := range s.NPCs {
        if s.NPCs[i].ID == 0 {
            s.NPCs[i].ID = uint64(i + 1)
        }
    }
    // Normalize importance: if > 1 and ≤ 10, treat as 0-10 scale.
    for i := range s.Facts {
        if s.Facts[i].Importance > 1 && s.Facts[i].Importance <= 10 {
            s.Facts[i].Importance /= 10.0
        }
    }
    return &s, nil
}
```

## Retry on Parse Failure

For adversarial/critical paths, retry once with a fixup prompt:

```go
resp, err := client.Generate(ctx, req)
scenario, err := ParseScenario(resp.Text)
if err != nil {
    // Retry: include the failed output and ask for a fix.
    retryReq := buildRetryRequest(originalPrompt, resp.Text,
        "Invalid JSON, please fix. Output ONLY valid JSON.")
    resp2, _ := client.Generate(ctx, retryReq)
    scenario, err = ParseScenario(resp2.Text)
}
```

Real-world use: adversarial gossip harness, rebellion-the-game session 2026-07-20.
Gemini Flash Lite generated string IDs, object locations, number subjects, and
out-of-range importance values in ~30% of responses. Lenient parsing + retry
brought parse success rate to >95%.
