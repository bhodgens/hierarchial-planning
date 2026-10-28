# Aadversarial harness pitfalls
When to use: wiring an adversarial harness into CI.
Lesson: wiring lessons: async verdict collection, flaky-seed isolation, timeout budgeting.

# Adversarial Harness Wiring — Lessons from rebellion-the-game

These pitfalls were discovered when wiring an LLM-driven adversarial test harness against the gossip engine. The harness compiled clean, all 37 tests passed, vet/fmt clean — but the gossip engine never propagated a single fact through 10 rounds of LLM-generated scenarios. The teacher LLM found "no transfers occurred" violations every round.

## Silent Propagation Failures

Three fields on `Fact` default to zero values that silently disable propagation:

### 1. ExpiresAt defaults to year=0 → immediately expired

```go
// BAD: Fact without ExpiresAt — expires immediately.
f := &Fact{Type: FactPlayerCrime, Subject: "player", Importance: 0.7}
g.Register(f)  // ExpiresAt is zero → year=0 → now.Year=1764 > 0 → expired

// GOOD: Set far-future expiry.
f := &Fact{
    Type: FactPlayerCrime, Subject: "player", Importance: 0.7,
    ExpiresAt: world.GameTime{Year: 1780, Month: 1, Day: 1},
}
```

The `CreateFact` method sets ExpiresAt via `addDays(now, calculateLifespanDays(importance))`. But code paths that call `Register` directly bypass this. Any fixture or scenario injector that creates facts via `Register` rather than `CreateFact` MUST set ExpiresAt explicitly.

### 2. MaxHops defaults to 0 → shareable filter rejects immediately

```go
// shareable.go filter rule 8:
if fact.PropagationDepth >= fact.MaxHops { continue }
// MaxHops=0, PropagationDepth=0 → 0 >= 0 → true → SKIP
```

Same root cause: `CreateFact` calls `calculateMaxHops(importance)` but `Register` does not. Any code path that calls `Register` directly must set MaxHops.

### 3. GossipThreshold + neutral social relationships → never gossip

With `StubSocialReader` returning `Relationship=0, Trust=0.5, FactionRelationship=0`, the default `GossipThreshold=0.3` blocks propagation between most NPC pairs because alignment similarity drives the entire compatibility score. For fixture-testing with generated NPCs, either:
- Set a lower threshold (`0.15` or `0.01`)
- Or provide positive default relationships

## LLM-Generated JSON Is Not Well-Formed

When an LLM generates scenario JSON, expect:
- String IDs: `"id": "npc1"` instead of `"id": 1`
- Number subjects: `"subject": 0` instead of `"subject": "player"`
- Object locations: `"location": {"name": "tavern"}` instead of `"location": "tavern"`
- Out-of-range importance: `"importance": 8` (0-10 scale) instead of `"importance": 0.8` (0-1 scale)
- Non-numeric `witnessed_by`: `"witnessed_by": "npc_witness_1"` instead of `"witnessed_by": 1`

**Pattern:** Every struct field that should be a numeric ID or scalar needs a custom `UnmarshalJSON` that accepts both the correct type and common LLM mistakes, with graceful fallbacks (auto-assign IDs, clamp values, default strings).

**Retry with fixup prompt:** When JSON parsing fails, retry the LLM call with the assistant's response included and a fixup instruction: "Invalid JSON, please fix." Lower temperature (0.4 vs 0.8) on retry. This catches ~20% of initially-malformed responses.

## Detection Pattern: Silently Zero Transfers

When a test harness runs scenarios and reports violations, check whether the violations are all the same class: "no transfers occurred." If every round produces the same "no propagation" finding despite varied scenarios, the fixture injection is broken, not the system under test.

Diagnostic test:
```go
g := NewNetwork(DefaultConfig())
// Inject a fact manually with explicit ExpiresAt and MaxHops
f := &Fact{Type: FactPlayerCrime, Subject: "player", Importance: 0.7,
    MaxHops: 20, ExpiresAt: world.GameTime{Year: 1780, Month: 1, Day: 1}}
g.Register(f)
// Seed one NPC with knowledge
mem.Add(f.ID, NPCKnowledge{FactID: f.ID, AccuracyAsKnown: 1.0, Confidence: 0.9})
// Run one tick with two NPCs
result := Tick(ctx, g, pop, social, now)
// Expect TransfersThisTick > 0
```

If this test passes but your harness produces no transfers, the harness's fact injection is missing fields.
