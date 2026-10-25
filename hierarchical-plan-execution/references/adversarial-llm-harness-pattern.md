# LLM-Driven Adversarial Test Harness for Simulation Validation

Pattern proven in the rebellion-the-game gossip engine adversarial harness
(plans-glm/13-adversarial-harness, 2026-07-20). Uses two LLM roles — adversary and
teacher — to find bugs in a deterministic simulation engine.

## Architecture

```
Adversary LLM (high temp, creative)     Teacher LLM (low temp, precise)
        |                                         |
        | generates probe scenario                | evaluates trace
        v                                         v
    [Harness Runner] --injects--> [Simulation Engine] --collects--> [Trace]
                                              |
                                     finds real violations?
                                              |
                                     yes --> fix engine
                                     no  --> teacher false positive?
                                              |
                                     yes --> improve trace data / prompt
```

## When to Use

- Testing a deterministic simulation engine (gossip, physics, economy, combat)
- The engine has formal rules that can be verified mathematically
- You need to find edge cases that static scenarios won't catch
- You want CI to continuously probe for regressions

## Critical Prerequisites

Before the adversary/teacher LLMs can find real bugs, the harness scaffolding must be
correct. These are the most common failure modes:

1. **Stub data must be realistic.** A `StubSocialReader` returning fixed values
   (trust=0.6, relationship=30 for ALL pairs) means every threshold check passes at
   exactly the boundary. No real violations will ever be found. Use a seeded reader
   with varied values.

2. **Injected facts must be viable.** LLMs generate facts, but the harness injects
   them. If `ExpiresAt` defaults to year=0, all facts are immediately expired. If
   `MaxHops` defaults to 0, no fact can propagate. Always set these explicitly.

3. **LLM output is unreliable.** Models generate string IDs ("npc1"), object-typed
   locations, out-of-range importance values. Custom JSON unmarshalers with lenient
   fallbacks (auto-assign IDs, clamp values, parse string numbers) are mandatory.

4. **Debug data must be in the trace.** The teacher LLM cannot verify math it can't
   see. Add per-hop input values (compatibility, trust, alignment similarity, band)
   to the trace format. Without these, the teacher guesses and produces false
   positives.

## Debugging Flow When Violations Appear

```
Teacher finds violation
  -> Is it a real engine bug?
       yes -> fix engine
       no  -> Is the trace missing data the teacher needs?
                yes -> add debug fields to trace
                no  -> Is the scenario misaligned with actual inputs?
                         yes -> improve adversary prompt (add formulas, recipes)
                         no  -> Teacher false positive (hallucination)
```

## Model Selection

| Role | Requirements | Example |
|------|-------------|---------|
| Adversary | Fast, creative, can follow JSON schema | Gemini Flash Lite |
| Teacher | Mathematically precise, can compute expected values | DeepSeek Chat, Claude |

Small free models (Cohere North) often can't handle the prompt complexity — they
return empty responses or malformed JSON. Test each model with a single round before
committing to it.

## Key Metrics

After each adversarial run, track:

- Parse failures (scenarios that couldn't be parsed) — should trend to zero
- Teacher evaluation failures (LLM errors) — should be rare
- Violation count — should decrease over time as real bugs are fixed
- Violation type distribution — shift from "no transfers occurred" (broken harness) to
  specific numeric violations (real bugs) to false positives (teacher hallucination)

A healthy harness: 0 parse failures, 0 teacher errors, small number of violations
that are all category "teacher's expected value differs from actual by < epsilon"
(false positives from rounding).
