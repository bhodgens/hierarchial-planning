# Audit-Driven GDD Planning — Worked Example


When to use: decomposing a doc corpus from existing audit findings.
Lesson: group findings by problem class into ordered branches; worked GDD-completion example.
> Reference document showing the methodology from the July 2026 GDD completion session.
> See SKILL.md §Planning Process → "Alternative: Audit-Driven Decomposition" for the
> general method. This doc provides the concrete session-level detail.

## Context

- **Corpus:** ~90 GDD markdown files across `docs/gdd/` (9 sections, ~1.1MB total)
- **Input:** 5 audit documents totaling ~100 findings (12 BLOCKERS, 11 GAPS, 7 INCONSISTENCIES, 14 vision findings V1-V14, 19 gameplay findings G1-G19)
- **Target:** Make every doc IMPLEMENTATION-READY (all contradictions resolved, all gaps filled, all drafts upgraded)
- **Output tree:** `plans-ds4f/` — 25 docs, 5 branches, 19 leaves, 2,578 lines

## Workflow Sequence

### Phase 0: Context Gathering (Single Session)

1. **Read master outline** (`00-MASTER-OUTLINE.md`) to get the full doc inventory and status table
2. **Read all audit docs** — gather every finding. Key docs:
   - `00-AUDIT-IMPLEMENTATION-READINESS.md` — 12 BLOCKERS, 11 GAPS, 7 INCONSISTENCIES
   - `00-AUDIT-2026-07-19-VISION.md` — 14 findings (V1-V14)
   - `00-AUDIT-2026-07-19-02-gameplay.md` — 19 findings (G1-G19)
   - `00-AUDIT-2026-07-17.md` — 55 findings resolution table
   - `00-OPEN-ISSUES.md` — still-open / deferred items
3. **Selectively read key reference docs** — executive summary, design pillars, design decisions, milestone roadmap

### Phase 2: Exploration Subagents (Background + Parallel)

Dispatch 3 subagents in one turn, each responsible for one GDD section:

| Subagent | Scope | Instruction |
|----------|-------|-------------|
| Explorer 1 | 02-gameplay/ (20 docs) | Read ALL, report status, contradictions, gaps per doc |
| Explorer 2 | 03-world/ + 04-npc/ (21 docs) | Same, plus verify specific audit claims (B6, B8, G1, I7) |
| Explorer 3 | 06-technical/ + 07-assets/ + 08-testing/ + 09-pm/ + 10-appendix/ (~25 docs) | Same, plus check TODO files, stale engine terms, architecture drift |

Each returns a structured report with exact file:line evidence. Do NOT wait —
continue building the plan tree while they run. Their reports serve as
verification of your own reading, not as the primary decomposition input.

### Phase 3: Decompose by Problem Class (In-Session — Not Delegated)

While explorers run, decompose all ~100 findings into 5 branches by problem class:

| Branch | Class | Leaves | Example Leaves |
|--------|-------|--------|----------------|
| 01-contradictions/ | Doc-vs-doc conflicts | 7 | sleep-fatigue, housing-tiers, smartphone-intro, first-npc, key-figures-ages, npc-population, minor-inconsistencies |
| 02-missing-specs/ | Named-but-undefined systems | 5 | new-system-specs (bond NPC, romance, commitment, betrayer, forward-ref), gameplay-specs (stranger penalty, quest lifecycle, body search), first-hour-onboarding, mythological-reaction, protagonist-voice |
| 03-upgrade-drafts/ | [DRAFT] → [DECIDED] | 3 | vision-gameplay (17 docs), world-npc (11 docs), technical-pm (11 docs) |
| 04-todo-files/ | [TODO] stubs | 3 | frontmatter, pm-multiplayer, appendix |
| 05-audit-cleanup/ | Final verification | 2 | update-audits, terminology-crossrefs |

Each leaf resolves a GROUP of findings (e.g., "minor-inconsistencies" handles 6
separate G/I findings in one leaf). Do NOT create one leaf per finding — that's
pitfall #1 (splitting too aggressively). Merge related small fixes.

### Phase 4: Write the Plan Tree (In-Session)

Write documents in this order:
1. `master.md` — root orchestrator
2. Branch orchestrators — one per branch directory
3. Leaf documents — numbered implementation docs

Follow the hierarchical-planning templates, but adapt for docs:
- Interface contracts = file conventions, status markers, cross-ref format
- Review checklist = "cross-refs resolve" instead of "tests pass"
- Verify checklist = line-number corruption check on *.md too
- Dispatch order = phase ordering (contradictions → specs → upgrades → cleanup),
  not concurrency groups (though independent branches within a phase CAN run concurrently)

### Phase 5: Review the Plan Tree (Background + Parallel)

After the tree is written, dispatch 2 review subagents:

| Subagent | Focus |
|----------|-------|
| Coverage Reviewer | Read every leaf + every audit finding. List any finding not assigned to a leaf. |
| Compliance Reviewer | Read every leaf against template requirements. Check structure, dispatch protocol, "do NOT commit" instructions, interface contracts. |

## Leaf Sizing for Doc Work

| Metric | Code Leaf | Doc Leaf |
|--------|-----------|----------|
| Files touched | 15-20 (read + write) | 3-10 (read + edit) |
| Lines produced | 3,000-5,000 | 50-500 |
| Exploration cost | High (understand codebase) | Medium (cross-ref verification) |
| TDD cycles | Yes | No |
| Context budget | ~75-115K | ~30-60K |
| Typical scope | One subsystem | 1-3 related findings or 1 new doc |

A doc leaf of 30-60K is fine. A doc leaf under 15K is also fine if the
findings are truly independent — but consider merging into a "minor fixes" leaf.

## Common Anti-Patterns

- **One leaf per finding:** Creates 30+ leaves for a GDD. Merge related findings
  into composite leaves (e.g., "minor-inconsistencies" handles 6+ items).
- **Skipping exploration subagents:** On smaller corpuses (<30 docs), you may not
  need them — read everything yourself. The rule: if reading everything would
  exceed 40K of source material TOKENS (not bytes), dispatch explorers.
- **Audit items that say "RESOLVED" but aren't:** The July 17 audit claimed
  "1764/1768 year resolved" but the key figures doc still said 1768 in 11 places.
  Always verify RESOLVED claims against current source when writing the plan.
- **Wrong interface contracts:** Doc trees need file conventions and status markers,
  not type definitions. Writing Go struct definitions as interface contracts for
  GDD docs is wasted work.

## Output

The `plans-ds4f/` tree in the rebellion-the-game repo is the canonical worked
example of this methodology.
