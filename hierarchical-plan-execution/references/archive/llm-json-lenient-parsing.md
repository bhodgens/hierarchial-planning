# Lllm json lenient parsing
When to use: parsing LLM JSON robustly.
Lesson: lenient parsing strategy for structured data.

# Lenient JSON Parsing for LLM-Generated Structured Data

LLMs frequently produce JSON that is structurally correct but uses wrong types:
string IDs instead of ints, objects instead of strings, values outside valid
ranges. Rather than fighting this with prompt engineering, accept it at the
parser boundary.

## The Pattern

For every struct field that the LLM populates, write a custom `UnmarshalJSON`
that normalizes the most common type quirks. The normalization should never
reject valid data — only expand what's accepted.

## Common LLM Type Quirks and Fixes

### 1. Numeric IDs as strings or names

LLMs generate `"id": "npc1"`, `"id": "scout"`, `"id": "npc_witness_1"` instead
of `"id": 1`.

```go
// Fix: accept number, numeric string, or non-numeric string → assign 0.
// Then a post-parse pass auto-numbers all zero-ID items sequentially.
func (s *ScenarioNPC) UnmarshalJSON(data []byte) error {
    // First try numeric.
    var idNum uint64
    if err := json.Unmarshal(raw.ID, &idNum); err == nil {
        s.ID = idNum
        return nil
    }
    // Then try string that parses as number ("1", "42").
    var idStr string
    if err := json.Unmarshal(raw.ID, &idStr); err == nil {
        if _, err := fmt.Sscanf(idStr, "%d", &s.ID); err == nil {
            return nil
        }
    }
    // Non-numeric string: set to 0, caller auto-assigns.
    s.ID = 0
    return nil
}
```

Post-parse auto-assignment:
```go
func ParseScenario(data []byte) (*AdversarialScenario, error) {
    var s AdversarialScenario
    json.Unmarshal(data, &s)
    for i := range s.NPCs {
        if s.NPCs[i].ID == 0 {
            s.NPCs[i].ID = uint64(i + 1)
        }
    }
    return &s, nil
}
```

### 2. String fields as objects

LLMs generate `"location": {"name": "tavern"}` instead of `"location": "tavern"`.

```go
// Accept string directly, or object with "name" field.
var locStr string
if err := json.Unmarshal(raw.Location, &locStr); err == nil {
    s.Location = locStr
    return nil
}
var locObj struct{ Name string `json:"name"` }
if err := json.Unmarshal(raw.Location, &locObj); err == nil && locObj.Name != "" {
    s.Location = locObj.Name
    return nil
}
s.Location = "unknown"
```

### 3. String fields as numbers

LLMs generate `"subject": 0` instead of `"subject": "player"`.

```go
var subjStr string
if err := json.Unmarshal(raw.Subject, &subjStr); err == nil {
    s.Subject = subjStr
} else {
    var subjNum float64
    if err := json.Unmarshal(raw.Subject, &subjNum); err == nil {
        s.Subject = fmt.Sprintf("%.0f", subjNum)
    } else {
        s.Subject = "player" // sensible default
    }
}
```

### 4. Out-of-range numeric values

LLMs generate `"importance": 8` (0-10 scale) when the spec expects 0.0-1.0.

```go
// Normalize 0-10 scale to 0-1, then clamp.
importance := rawValue
if importance > 1 && importance <= 10 {
    importance = importance / 10.0
}
if importance < 0 { importance = 0 }
if importance > 1 { importance = 1 }
```

### 5. Truncated JSON (max_tokens exceeded)

The LLM runs out of tokens mid-generation, producing truncated JSON.
The adversary's retry pattern handles this:

1. First attempt: parse the response
2. If parse fails: send the response back to the LLM with "Invalid JSON, please fix"
3. If retry also fails: fall back to stub/hardcoded scenario (never crash)

## When to Use Custom Unmarshalers vs Prompt Engineering

**Use custom Unmarshalers when:**
- The LLM model is weak/quantized and consistently produces type mismatches
- You're calling the LLM in a loop where each failed parse costs a full round-trip
- The JSON schema is complex and exact adherence is unlikely

**Use prompt engineering when:**
- The model is strong enough to follow typing instructions
- Each LLM call is expensive (API cost) and you want clean first attempts
- You control both the prompt AND the model selection

**The real-world rule:** if you're using free-tier or quantized models, always add
lenient parsers. The cost of the parser code (~30 lines per struct) is trivial
compared to the cost of re-prompting or losing rounds to parse failures.

## Go Implementation Pattern

For each struct with LLM-populated fields:

```go
// Public type — excludes fields from default JSON marshaling.
type MyType struct {
    ID    uint64 `json:"-"`
    Name  string `json:"name"`
}

// Raw type — mirrors public type but uses json.RawMessage for tricky fields.
type myTypeRaw struct {
    ID    json.RawMessage `json:"id"`
    Name  string          `json:"name"`
}

func (m *MyType) UnmarshalJSON(data []byte) error {
    var raw myTypeRaw
    if err := json.Unmarshal(data, &raw); err != nil {
        return err
    }
    m.Name = raw.Name
    // ... lenient parsing of raw.ID ...
    return nil
}
```

Avoid importing these into the public API. They're internal parsing helpers,
not part of the package's interface contract.
