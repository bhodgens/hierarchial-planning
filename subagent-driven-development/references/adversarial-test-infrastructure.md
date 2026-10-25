# Adversarial Test Infrastructure Pattern

When a subsystem is too heavy to test directly (requires init, event loop, external processes), build a lightweight fixture that wraps the subsystem's public API, a trace collector that captures all output, and a deterministic evaluator that checks known invariants. Optionally add an LLM-driven adversary loop for edge-case discovery.

## Three-layer architecture

```
Layer 1: Fixture (SimulationFixture)
  - Wraps the heavy subsystem (HandleTick)
  - Self-contained: no external processes, no running engine
  - Seeds state (facts, events, quests, faction regard) in one call
  - Exposes Tick/TickN for running the loop
  - Exposes accessors for the evaluator to query state

Layer 2: Trace (SimPipelineTrace)
  - Aggregates all output across ticks: responses, transfer logs,
    faction regard snapshots, economy deltas, quest states, NPC
    alignments, knowledge confidence, perception states
  - Collected via CollectSimTrace(responses, fixture)
  - Formatted as human-readable text for LLM evaluation

Layer 3a: Deterministic evaluator (SimulationEvaluator)
  - Checks known violation patterns: event firing, fact injection,
    faction regard propagation, economy drift, quest expiry,
    alignment shift, memory decay, cross-faction damage, secret
    keeping, accuracy degradation, gossip event completeness
  - Each check is a standalone function returning []Violation
  - Severity: "error" for definite bugs, "warning" for suspicions
  - Runs in CI without any LLM dependency

Layer 3b: LLM evaluator (SimTeacherLLM)
  - Feeds the formatted trace + scenario to an LLM
  - LLM evaluates against expected behavior with precise formulas
  - Catches violations the deterministic checks miss
  - Requires cloud API key; optional in CI

Layer 4 (optional): LLM adversary loop (SimAdversarialRunner)
  - Adversary LLM generates SimulationScenarios targeting rules
  - Runner creates fixture → ticks → trace → evaluate → violations
  - Violations feed back to adversary for refinement
  - Fallback: stub scenarios + deterministic evaluator when no LLM
```

## Key design decisions

1. **Fixture is self-contained.** `NewSimulationFixture` calls `HandleInit` with a seed to generate NPCs, registers events/quests, injects facts. No IPC, no UE5 engine, no network. This is the difference between a 5-second test and an un-runnable one.

2. **Trace is comprehensive but lazy.** Collect everything in one pass — don't make the evaluator query the fixture directly. The trace is a snapshot; the evaluator is pure logic on that snapshot.

3. **Deterministic checks are formula-precise.** Don't say "accuracy should degrade" — say "accuracy must be ≤ 0.52 for SLOW-band first hop with compat=0.15." The LLM teacher prompt encodes the SAME formulas so it can spot even 1% deviations.

4. **JSON scenarios are the lingua franca.** Scenarios, traces, and violation reports all use JSON. This lets the LLM generate scenarios, the runner execute them, and the teacher evaluate them — all in the same wire format.

5. **Regression suite closes the loop.** When a violation is found, save the scenario JSON. A `--suite=regression` mode replays all saved scenarios and fails if any still produce violations. This proves bug fixes.

## Go-specific notes

- JSON tags are mandatory on all struct fields used for LLM-generated JSON parsing. Go's `encoding/json` does NOT auto-match `snake_case` JSON keys to `CamelCase` struct fields without explicit `json:"snake_case"` tags. A field named `FactType` will NOT match `"fact_type"` in JSON without a tag.
- Use `//go:embed prompts/*.txt` for embedded LLM prompt files — keeps prompt text out of Go source.
- The fixture pattern works because `HandleInit` and `HandleTick` are public methods that don't require a `Session` (IPC connection). Design your subsystem's public API with this testability in mind.
