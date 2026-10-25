# Contract Verification Digests — Recipe

> A post-authoring, pre-execution verification technique for hierarchical plan
> trees. Catches **paraphrase-drift** (Pitfall 21) — frozen contract values in
> the plan that contradict the source spec — which the structural compliance
> scan (Pitfall 20) cannot detect because the sections are present and
> well-formed; only the *values* are wrong.

Read alongside SKILL.md:
- Review Protocol §"Contract Verification Digests"
- Pitfall 21 (paraphrase-drift)

---

## When to run

Run contract-verification digest subagents after authoring a plan tree (or
forest) and BEFORE dispatching any implementation agents. Highest value when:

- The plan defines frozen wire types, shared structs, or constant tables that
  multiple trees consume. One wrong field breaks integration everywhere.
- The plan translates prose spec ("reputation is the durable aggregate") into
  a concrete type. This is where paraphrase-drift lives.
- The plan invents threshold bands, enum members, or formula coefficients
  "derived from the spec narrative" without an exact spec quote.
- You authored a forest (5+ trees). Integration surface is larger and drift
  compounds across trees.

Skip when: single-tree plan with trivial contracts, or every contract value is
a verbatim spec-table copy (no paraphrase risk).

### Three-layer audit stack when the source spec is the CODEBASE (meept llm-resilience-forest, 2026-09-01)

A feature-implementation forest has no GDD — its "source spec" is the actual
code. Run three read-only digest subagents in parallel after authoring; all
three paid off and each caught a class the others could not:

1. **Mechanism audit** — does the plan's core mechanism EXIST in source? The
   escalation tree assumed the verification hook influences the fix turn's
   model; the audit found `RunPrepareNextTurn` (hooks.go:267) had ZERO
   production callers — the whole tree was built on dead infrastructure. Plan
   gained a prerequisite "wire the pipeline" leaf before any hook-based leaf.
2. **Citation audit** — verify every `file.go:NNN` anchor in the plan docs
   against HEAD. Result: ~94 accurate / 13 drifted / 3 stale-concept / 0
   wrong. Drift was mechanical, but 3 were NAME corrections that would have
   sent implementers to the wrong symbol (`ContextLimit` vs `ContextWindow`;
   `Reflector` vs `Chatter`; a 5th retry loop keyed on a different constant).
   Bulk-fix anchors with sed; no re-review needed for pure line moves.
3. **Architecture audit** — designs that reference real code but cannot work:
   per-alias state that must be cross-alias; a planned resolver method name
   colliding with an existing different-signature method (compile error);
   config practice that defeats a host-only key (two providers sharing one
   host, one credential each). Each blocker became a plan amendment BEFORE any
   implementation subagent burned a dispatch on it.

Record amendments as dated decision rows in the forest's DECISIONS.md (meept
D16) so per-tree masters cite the resolution instead of restating it, and
write the full audit into a dated sibling file (e.g. `ARCH-AUDIT-<date>.md`)
with a disposition table — it doubles as the pre-dispatch review record.

---

## The recipe

### Step 1: Slice the plan's contracts by source spec

Group the plan tree's frozen contracts by which GDD/spec document they derive
from. Each slice becomes one subagent dispatch. For the `plans-glm/` 12-tree
forest, three slices covered everything:

| Slice | Source spec(s) | Contracts to verify |
|-------|----------------|---------------------|
| Gameplay/sandbox | `02-gameplay/*`, `09-pm/*` | movement speeds, stamina, portal items, stranger penalty, cover identity, save schema fields |
| NPC systems | `04-npc/*` | gossip Fact/NPCKnowledge/Standing, celebrity multiplier, perception ranges, attention weights, 8 needs, schedule schema |
| Technical architecture | `06-technical/*`, `03-world/03-*` | IPC wire types, LLM cascade thresholds, procgen constants, embedding model, save overlay sub-objects |

Batch the slices in parallel (`delegate_task` with `tasks=[...]`). Three
subagents running concurrently is well within the 3-child concurrency limit.

### Step 2: The dispatch prompt (template)

Each subagent gets:

```
Read <source GDD files> (use terminal cat or search_files, NOT read_file,
to avoid line-number corruption).

The plan tree at <plans-glm/X-name/master.md> defines these frozen contracts
that claim to derive from your source spec:
  <paste the frozen Go structs / constant tables / threshold enums verbatim>

YOUR REPORT (plain text, no code, ~800-1500 words):

For EACH contract, return:
  1. The spec's exact words/numbers (quote them, with file:line citation).
  2. Whether the plan's contract matches: MATCH / MISMATCH / NOT_IN_SPEC.
  3. If MISMATCH: the spec's correct value vs the plan's wrong value.
  4. If NOT_IN_SPEC: flag that the plan invented this — is the invention
     reasonable, or does it contradict the spec's intent?
  5. Cross-system dependencies the spec mentions that the plan should track.

Be concrete: quote exact numbers. Flag every ambiguity. Do NOT commit.
Do NOT modify any files. Read-only digest.
```

### Step 3: The report shape (what subagents return)

Each subagent returns a structured report. The `plans-glm/` session's three
digests produced findings in this shape:

```
### ⚠️ CORRECTION — Celebrity multiplier bands (tree #02 leaf 03 WRONG)

Tree `plans-glm/02-gossip/03-reputation.md` invented celebrity bands keyed on
notoriety 0.10/0.25/0.50/0.75 → 1.25×/1.5×/2.0×/3.0×. The GDD
(`04-gossip-and-reputation.md:328-339`) specifies fact-count bands instead:

| High-importance facts about player | Celebrity level | Effect |
| 0–5  | ×1.0 | baseline |
| 5–10 | ×1.2 | "talked about" |
| 10–20| ×1.5 | "well known" |
| 20+  | ×2.0 | "celebrity/infamous" |

The trigger is COUNT of high-importance facts, not a 0-1 notoriety float.
Action: rewrite CelebrityMultiplier to take fact_count int.
```

### Step 4: Digest in-session; do NOT delegate amendment

The orchestrator (main model) reads each report and amends the plan contracts
directly. Do NOT re-dispatch a "fix the contracts" subagent — the amendment
decision requires the orchestrator's view of cross-tree integration (e.g. the
`Standing` struct fix in tree #02 must propagate to tree #05 dialogue, tree #09
save, tree #12 gamemaster).

Amend via `patch`/`write_file` against the affected plan files. Re-read each
file fully before patching (Pitfall 19 — stale parent read-state).

### Step 5: Record findings in OPEN-QUESTIONS.md

Every mismatch and NOT_IN_SPEC finding goes into the forest's
`OPEN-QUESTIONS.md` under a "Subagent-Digest Amendments" section, with:

```
### ⚠️ CORRECTION — Q-amend-NN: <what was wrong>
<spec quote> vs <plan's wrong value>. Action: <fix applied / deferred>.
```

This gives the user an audit trail of what the digests caught and what was
amended vs deferred. The `plans-glm/` session recorded 34 amendment findings
(10 tech + 15 NPC + 9 gameplay); 18 were plan corrections the orchestrator
applied directly, 8 were user decisions, the rest were confirmations.

---

## Worked examples (from `plans-glm/`, 2026-07-19)

### Error 1: reputation struct shape

**Plan authored:** `Standing { Subject string; Scope string; Regard int(-100..+100); Notoriety float64(0..1) }`

**Spec actually says** (`04-gossip-and-reputation.md:§Reputation Layer`): five
aggregate dimensions, each `float(-1..+1)`: Trust, Danger, Political,
Notoriety, Criminal. Computed never stored.

**How caught:** the NPC-systems digest subagent re-read the gossip spec,
compared the spec's "five aggregate dimensions" table against the plan's
single-int struct, flagged MISMATCH with the correct 5-field shape.

**Impact if uncaught:** trees #02, #05, #09, #12 all consume `Standing`. Wrong
shape = integration failure across 4 trees.

### Error 2: celebrity multiplier bands

**Plan authored:** `CelebrityMultiplier(notoriety float64)` with bands
0.10/0.25/0.50/0.75 → 1.25×/1.5×/2.0×/3.0×.

**Spec actually says** (`04-gossip-and-reputation.md:328-339`): keys on count
of high-importance facts, bands 5/10/20 → 1.2×/1.5×/2.0×.

**How caught:** same digest subagent. The spec has a concrete table; the plan
had invented different numbers "derived from the narrative."

**Root cause of both:** the orchestrator summarized prose ("reputation is an
aggregate", "notoriety raises a multiplier") instead of quoting the spec's
exact table. Paraphrase-drift.

---

## Cost vs benefit

- **Cost:** 3 subagent dispatches, ~2-3 min each (concurrent), ~15K tokens of
  subagent context each. Plus the orchestrator's in-session amendment pass
  (~30 min for 18 corrections across 8 files).
- **Benefit:** caught 2 contract errors + 1 blocker contradiction
  (save-vs-schedule need_states) + 8 user-decision questions + ~30 confirmed
  constants, all before any code was written. Executing the forest against
  the wrong `Standing` shape would have cost days of integration debugging.

The digest pass is cheap insurance against the most expensive class of plan
error (wrong frozen contract propagating across a forest).

---

## Integration with the skill's other review passes

The full review sequence for a plan forest:

1. **Structural compliance scan** (Pitfall 20) — `check_template_compliance.py`.
   Catches missing sections.
2. **Dual-track review** (coverage + compliance subagents) — catches missing
   findings and template violations.
3. **Contract verification digests** (this doc) — catches paraphrase-drift in
   frozen contract values. The only one of the three that catches *wrong
   values* as opposed to *missing structure*.

Run them in that order. Each catches a different class of error; skipping any
one leaves a known gap.
