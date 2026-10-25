# Plan-Tree Audit Failure Modes — Catalog and Worked Example

## Overview

This reference catalogs the defect patterns discovered during a comprehensive
GDD consistency audit of 12 hierarchical plan trees under `plans-glm/`.
Each pattern is a class of inconsistency that the standard drift-digest procedure
(Rule 2) may miss — they are not about the GDD changing but about how the plan
tree relates to itself, its peer trees, and its own correction history.

**When to consult this reference:** when auditing plan trees for dispatch
readiness, run through these patterns as supplemental checks after the
standard drift-digest cross-reference (Steps 1-5 of the Drift Digest Procedure).

---

## Pattern 1 — Internal Plan-Tree Goal/Contract/Tests Misalignment

### Description
The tree's Goal section states one design, the Interface Contracts section
defines another, and the leaf test tasks exemplify a third. All three are
authoritative within the tree — different agents (or the same agent at different
times) wrote them without cross-referencing.

### Detection
Read the Goal → then the Contracts → then one representative leaf's Test section.
Do they all reference the same numeric counts, the same struct field lists, the
same thresholds? If any disagrees, the tree is not internally consistent.

### Worked Example
`plans-glm/08-schedule/master.md`:
- **Goal** (line 10-11): "8 needs decaying on 0-100 scale, the 8-priority
  resolution hierarchy (SAFETY > SLEEP > HUNGER > THIRST > DUTY > WORK >
  SOCIAL > FAITH)" — a pre-decision draft with HUNGER/THIRST still present.
- **Contracts** (line 39): Correctly shows 6 needs struct with fields
  `Sleep, Social, Work, Safety, Faith, Duty`.
- **Dispatch Protocol** (line 133): Still says "8-needs table."
- **Review Checklist** (line 161): Correctly says "6 needs (no HUNGER/THIRST)."

**Impact:** A leaf agent reading the Goal section (the first content they see)
implements an 8-need model — wrong per the canonical spec, wrong per the tree's
own Contracts. The tree contradicts itself before any GDD drift is involved.

**Fix:** Hard-edit the Goal to match the Contracts. Replace "8 needs" →
"6 needs", remove HUNGER/THIRST from the hierarchy, and audit every other
prose reference in the tree for the same staleness.

---

## Pattern 2 — Partial Correction Propagation (Master Fixed, Leaves Stale)

### Description
A subagent digest or post-authoring review identifies a frozen-contract error
in a plan tree. The `master.md` orchestrator is corrected — the struct
definition, constant table, or function signature gets the right values.
But the **leaf document's TDD test tasks and review checklist** are not updated;
they continue to assert old values, type signatures, and threshold boundaries.

### Detection
For every correction applied to a `master.md` contract, search every leaf
document that references that contract for stale type signatures, stale
threshold values, and stale test expectations. If the leaf tests pass `float64`
but the contract now takes `int`, the correction is incomplete.

### Worked Example
`plans-glm/02-gossip/03-reputation.md`:
- The contract text (lines 115-154) was correctly updated to use fact-count
  bands for `CelebrityMultiplier`: `0-5 → ×1.0 / 5-10 → ×1.2 / 10-20 → ×1.5 /
  20+ → ×2.0`, with signature `func CelebrityMultiplier(highImportanceFactCount int) float64`.
- But the **TDD test steps** (lines 204-211) still write `notoriety 0.05 → 1.0`,
  `notoriety 0.15 → 1.25`, etc. — passing `float64`, not `int`, with different
  thresholds (0.10/0.25/0.50/0.75) and different multipliers (1.25×/1.5×/2.0×/3.0×).
- The **leaf-level review checklist** (line 295-296) checks "Celebrity tier
  boundaries exactly at 0.10, 0.25, 0.50, 0.75" — still the old notoriety bands.

**Impact:** An agent following the leaf's TDD instructions writes tests that
don't match the master.md contract. Tests will either fail to compile (wrong
input type) or pass with wrong values (producing multiplier 1.25× when the GDD
specifies 1.2× for that fact-count band).

**Fix:** After every contract correction in a master.md, grep downstream leaves
for the old field names, type shapes, and numeric constants. Update tests and
review checklists to match. This is a separate pass from the correction itself.

---

## Pattern 3 — Cross-Tree Contract Omission Against Architecture Docs

### Description
A project-architecture or system-design document (not a plan tree) specifies a
message type, constant, protocol step, or interface that multiple plan trees
consume. But no plan tree declares it — not in the tree that "owns" the
contract surface (e.g., the IPC tree for wire types) and not in any consumer.
The contract exists in an authoritative reference document but has no plan
tree that will implement it.

### Detection
Read the architecture doc's contract sections (message type tables, protocol
sequences, configuration schemas). For **each contract** (each message type,
each protocol step, each shared constant), identify which plan tree should
own it and check whether that tree's interface contracts or message-type table
includes it. Create a cross-reference table and mark any ABSENT entry.

### Worked Example
`docs/gdd/06-technical/02-project-architecture.md` references a `cell_query` /
`cell_response` message type for World Partition cell transitions (NPC tier
promotion/demotion on cell boundary crossing).

Plans-glm/ Tree 03 (IPC) defines the message types table:
- `init` / `init_ack`
- `tick` / `tick_response`
- `dialogue_request` / `dialogue_response`
- `player_action`, `event`
- `ping` / `pong`, `exit_request`

**`cell_query` / `cell_response` is absent.** No plan tree implements it.
It was flagged in Q-amend-2 but never applied to the tree — the open question
was raised but the tree master.md was never amended.

**Impact:** When the cell-querying code needs to exist (during World Partition /
NPC tier transition implementation), there is no plan leaf that builds it, no
contract that defines its payload shape, and no IPC wire type that the UE5
side and Go side can agree on. Integration fails silently or the cell query
is patched in ad-hoc, bypassing the frozen-contract discipline.

**Fix:** After plan-tree authoring, run a cross-reference pass against the
project-architecture document. For each architecture-level contract, confirm
at least one plan tree's Interface Contracts section declares it. If the
contract exists in the architecture but no plan tree covers it, either add it
to the appropriate tree or create a DEFERRED note with a trigger condition.

---

## Pattern 4 — Stale Correction Carrier (Q&A says Fixed, Body Text Doesn't)

### Description
An open-question entry in OPEN-QUESTIONS.md correctly states a user decision,
changelog resolution, or subagent finding — "DECIDED — ONNX" or "RESOLVED per
changelog D9" — but the tree's **body text** (Goal section, Constants section,
dispatch protocol) still contains the old, superseded value. The Q&A section is
the trace of the fix; the executable content of the tree is the body text. If
only the Q&A is updated, the tree is not actually fixed.

### Detection
For every open question that was resolved with a concrete value, search the
tree's body text (Goal, Constants, Dispatch, inline code blocks) for the old
value. If the old value still appears in any body-text section, the correction
is incomplete regardless of the Q&A entry.

### Worked Example
`plans-glm/11-embed/master.md`:
- Q-embed-2 at line 161: "DECIDED — ONNX. GDD §7 fixed: all-MiniLM-L6-v2.onnx.
  GGUF removed from the doc. Tree #11 uses ONNX format throughout." **Correct.**
- But the **Goal** (line 11): "MiniLM-L6-v2 (384-dim, **Q8_0 GGUF**, ~22MB)
  loaded via ONNX Runtime" — still contains "GGUF."
- The **Constants** (line 65): "Model: all-MiniLM-L6-v2, **Q8_0 GGUF**, ~22MB."
- The **Dispatch** (line 89): "384 dims, **Q8_0**."

**Impact:** An agent searching the tree for the model format finds "GGUF" in
the body text and loads a GGUF model into ONNX Runtime — which fails (GGUF and
ONNX are different model formats loaded by different runtimes). The Q&A entry
is correct but invisible to an agent that reads the executable content.

**Fix:** After resolving an open question with a concrete format/constant
decision, grep the tree's body text (not just the Q&A section) for the old
term. Replace every occurrence. Add this to the "resolved question → apply"
checklist: the Q&A entry is the resolution record; the body text is what agents
actually read.

---

## Pattern 5 — Preemption Threshold Drift (Commuted Value in Plan)

### Description
A GDD subagent digest pins an exact numeric threshold (e.g., "preemption
threshold: <2s → allow completion, ≥2s → abandon") but the plan tree
translates it to a different value ("GM task completes via deterministic
fallback within 100ms"). The plan commutes the design-intent meaning ("fast
preemption") into a numeric shortcut of its own invention, losing the
state-dependent behavior the spec requires.

### Detection
For every threshold, cadence, or limit in the plan that claims to be "from
the GDD" but uses a round number (100ms, 50%, 3 seconds) check the source
spec for the exact wording. If the spec says "if remaining < 2s, allow
completion; if ≥2s, abandon" and the plan says "within 100ms," the plan has
commuted the meaning — 100ms is a flat wall-clock value with no time-remaining
check, not the GDD's stateful behavior.

### Worked Example
`plans-glm/12-gamemaster/master.md` line 118: "in-flight GM tasks complete
via deterministic fallback within 100ms; Model 1 switches to conversation."

The GDD (Q-amend-4 from `08-gamemaster-agent.md`) specifies: "When player
initiates conversation, any in-flight GM task is resolved (preempted):
<2s remaining on GM task → allow completion then yield; ≥2s → abandon +
deterministic fallback."

**Drift:** The plan's "100ms" is a wall-clock timeout (how long to wait for
failback). The spec's preemption is state-dependent: it checks remaining
time on the GM task, not a wall-clock deadline. The plan commutes
"state-dependent gating" into "flat timeout."

**Fix:** Replace "within 100ms" with the spec's stateful logic: check
`remaining_time < 2s` on the in-flight task. If true, allow completion and
then yield; if false, abandon immediately with fallback. Document the 2s
threshold at the rule definition site.

---

## Summary Table

| # | Pattern | Detection Method | Scope | Seen In |
|---|---------|-----------------|-------|---------|
| 1 | Goal/Contracts/Tests misalignment | Read all three sections sequentially | Within one tree | `08-schedule` |
| 2 | Partial correction propagation | After master fix, grep leaf tests for old values | Across master + leaves | `02-gossip/03-reputation.md` |
| 3 | Cross-tree contract omission | Read arch doc, enumerate every contract, check owning tree | Across trees + arch doc | `03-ipc` (cell_query missing) |
| 4 | Stale correction carrier | After Q&A fix, grep body text for old value | Within one tree | `11-embed` (GGUF stale) |
| 5 | Preemption threshold drift | Diff plan's numeric thresholds against spec's behavioral spec | Within one tree | `12-gamemaster` |

## Session Provenance

These patterns were identified during a read-only GDD consistency audit of the
Rebellion `plans-glm/` forest (12 plan trees, 3 leaf documents, 5 core
reference files) on 2026-07-19. The audit produced a structured per-tree
report with scores (PASS / NEEDS_UPDATE / DRIFT / BROKEN), a consolidated
priority-fix list (10 items), and cross-cutting findings. This reference
abstracts the specific session findings into reusable detection patterns.
