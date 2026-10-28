# Changelog-Review Digests (Tier-3 Verification)


When to use: tier-3 verification for design drift caused by sibling sessions.
Lesson: one subagent cross-references changelog entries against plan spec sources before execution.
> Recipe for the post-authoring, pre-execution verification tier that catches
> **design drift caused by sibling sessions**. Run AFTER the structural
> compliance scan (tier 1) and the contract-verification digests (tier 2).
> See SKILL.md Review Protocol §"Tier-3 Verification" and Pitfall 22.

## Why this tier exists

Tier 2 (contract-verification digests) diffs your plan's frozen contracts
against the source spec *as the spec file exists today*. But on a long-running
project with an active changelog, the spec may have drifted *after* you read
it. A parallel session may have:

- Ratified new constants (a primary-source research commit changed hill heights)
- Cut a system (HUNGER/THIRST needs removed)
- Renamed a field or label (`derelict` → `ruined`)
- Elevated a doc's status (`[DRAFT]` → `[DECIDED]`)

Your plan inherited the *old* values. Re-reading the current spec file won't
reveal the drift — the file just shows the new value, and you'll assume your
plan matches. The **changelog** is the only record that the design moved.

## When to run

**Mandatory** when:
- The project has an active changelog (per the `design-plan-consistency` skill
  / AGENTS.md Rule 1).
- You authored the plan in a different session than the one that last modified
  the spec.
- The spec corpus is large (50+ docs) and actively maintained.

**Skip** when:
- No changelog exists (small / personal project).
- You are the only agent and the plan was authored in the same session as the
  latest spec edit (you already know the current state).

## Dispatch prompt template

One subagent (this is a single-slice verification, not a fan-out):

```
Read the project changelog at <changelog_path> and recent commits affecting
the spec corpus:
  cd <repo> && git log --oneline -30 -- <spec_dir>/

Also read the plan's OPEN-QUESTIONS tracker (if any) at <plan_dir>/OPEN-QUESTIONS.md.

YOUR JOB: Find any spec changes that affect the plan trees under <plan_dir>/.
Cross-reference every changelog entry dated AFTER the plan's last verification
date against the plan's spec sources (listed in <build_plan_index>).

For each changelog entry that touches a plan spec source, report:
1. HARD CONTRADICTIONS — the plan holds values the spec has since changed
   (quote both: the plan's value + the spec's current value + the changelog
   entry that changed it). These MUST be amended before execution.
2. RESOLVED OPEN QUESTIONS — the changelog closed something the plan still
   lists as an open question. Mark these resolved.
3. NEW INFO — the changelog introduced constants/contracts/status changes the
   plan should incorporate but currently doesn't mention.
4. STATUS CHANGES — a doc the plan treats as [DRAFT] is now [DECIDED] (or
   similar). The plan can now treat it as authoritative.

Return a structured report. Be concrete: quote exact numbers/values from the
changelog. Do NOT modify files. Do NOT commit. Read-only digest.
```

## Report shape the subagent returns

```
## HARD CONTRADICTIONS — Plan trees currently hold wrong values
### H1. <concept> (tree #NN, <question-id>)
- Plan value: <X>
- GDD change (commit <hash>, <decision-id>): <Y>
- Impact: <what breaks>
- Action required: amend <plan_file>; flag <question-id> as superseded.

## RESOLVED OPEN QUESTIONS
### R1. <question> (was implicitly referenced) — <status> (decision <id>)
...

## NEW INFO
### N1. <change> (commit <hash>, <decision-id>)
...

## STATUS CHANGES
| Doc | Old status | New status | Plans affected |
...

## Summary of Required Plan-Tree Amendments
**Must-fix before dispatch (hard drift):** ...
**Should-update (info now authoritative):** ...
**No action:** ...
```

## Worked example: the `plans-glm/` session

After authoring 12 plan trees, the orchestrator dispatched a changelog-review
subagent against `docs/gdd/00-CHANGELOG.md` + recent commits. The subagent
found:

**Hard contradictions caught (both survived tiers 1 and 2):**
- **H1 (hill heights):** Q-amend-10 in OPEN-QUESTIONS listed "Pemberton 24m,
  Mt Vernon 23m." The changelog showed commit `e5ab06e` (D11) had ratified
  primary-source research: Pemberton ~34m, Mt Vernon ~34-37m, plus added
  Fort Hill and Copp's Hill. The plan's terrain constants were wrong by
  ~10-14m. Caught ONLY because the changelog recorded the ratification —
  re-reading the current geo-foundation doc would have shown the new values
  without flagging that the plan held different ones.
- **H2 (condition labels):** tree #10 referenced condition levels as
  "pristine/clean/lived_in/worn/ruined" (an older draft). The changelog
  (D5) ratified the canonical labels as `pristine, good, worn, damaged, ruined`.

**Resolved open questions (10 items):** D-29 fire CUT, D-30 disease CUT,
D13 build-plan-index rewrite, D2/D6/D8/D11 status upgrades, D1 Tier-3
population, etc. These were marked resolved without plan edits.

**Status changes:** 7 docs elevated (geo-foundation [REVISED]→[DECIDED],
navmesh [DRAFT]→[DECIDED], first-hour →[DECIDED], stranger-penalty →[DECIDED],
timeline-pacing →[DECIDED], cpu-only-llm-path →[DECIDED], boston-hills
NEW→[RESEARCH]).

**Outcome:** 6 amendments applied to the plan trees; the 2 hard contradictions
would have caused procgen terrain generation against wrong hill heights and
interior condition-level lookup failures.

## Integration with AGENTS.md Rule 1

If the changelog-review surfaces a contradiction that requires editing a GDD
doc (not just a plan doc) to resolve, record a changelog entry for that edit
in the same batch. The changelog-review digest may surface the *need* for a
GDD fix; the fix itself is a new changelog entry. Do not silently edit the
GDD without recording it — that creates the exact problem this tier exists
to catch.
