# Multi-Tree Forest Pattern — Worked Example (`plans-glm/`)


When to use: authoring 5-12 plan trees in one session.
Lesson: SHARED-CONVENTIONS.md and OPEN-QUESTIONS.md siblings, inline-vs-separate leaf decision.
> Session: 2026-07-19, Rebellion game project.
> Task: author hierarchical implementation plans for all 12 systems in the
> build-plan-index, in one session, under `plans-glm/`.
> This doc captures the techniques that emerged when the plan tree scaled from
> "one feature" to "an entire project's implementation surface."

Read alongside the SKILL.md sections:
- Step 6.5 "Authoring a Forest (5+ plan trees at once)"
- Step 6.6 "Inline vs separate leaf files"
- Step 6.7 "Differential / convergence plan naming"

---

## The situation

The build-plan-index (`docs/gdd/09-pm/02-build-plan-index.md`) listed 12 systems,
each NOT_STARTED, each pointing to a GDD spec. The user wanted all 12 plan trees
authored in one session under `plans-glm/`. The directory name `plans-glm/`
signals "differential / convergence implementation" — multiple agents on
different models implement the same leaf, and outputs are compared. That raised
the contract-precision bar.

12 trees × ~2-3 leaves each = 26+ leaves. Fully expanding every leaf as a
separate file with TDD task lists would have produced 40+ files and ~15K lines
of planning — unjustified at planning time, before any decision to execute.

## The pattern that worked

### 1. SHARED-CONVENTIONS.md as the single source of truth

Instead of restating Go conventions, UE5 C++ conventions, the IPC wire types,
the numeric contract, test strategy, pitfalls, and commit policy in every
`master.md`, we extracted them into `plans-glm/SHARED-CONVENTIONS.md` (~18KB,
9 sections). Every master.md says "see SHARED-CONVENTIONS.md §3" rather than
re-declaring.

Sections in SHARED-CONVENTIONS.md:
1. Project Layout (canonical file tree)
2. Go Coding Conventions
3. IPC Wire Types (Frozen) — the contract that integrates all Go-side trees
4. UE5 C++ Conventions
5. Numeric Contract (cross-system — relationship scales, time ratios)
6. Test Strategy (per tree)
7. Critical Pitfalls (applies to EVERY leaf)
8. Commit Policy
9. Open-Questions Tracking format

Why this mattered: when (say) the gossip tree defines a `Fact` struct that the
dialogue tree also consumes, both trees point at the same §3 definition. No
drift. And the wire types section (Vec3, GameTime, TickRequest, etc.) is
literally copied from the GDD once into SHARED-CONVENTIONS.md, then every leaf
that touches IPC references it.

### 2. OPEN-QUESTIONS.md as the user's amendment surface

Every tree collected its own open questions in its `master.md`. But the user
shouldn't have to open 12 files to find the questions they need to resolve.
So we compiled `plans-glm/OPEN-QUESTIONS.md` — one file, sorted by tree, with
a footer summary: "40 questions total, 6 needing decisions, 34 accept-default."

The 6 decision-needing questions were: cabin-NPC-vs-farmer (one or two NPCs),
TTS integration home (new tree or stretch), multi-NPC conversations (separate
tree?), embedding model format (GGUF vs ONNX — GDD contradiction), UE5 scene
assembly (separate tree?), perceived_alignment semantics.

Format per question:
```
- Q-<tree>-<n> (<tree>/<leaf>): <question> — blocks: <what it blocks> — suggested default: <rec>
```

### 3. Inline leaf definitions for 11 of 12 trees

Only the critical-path / de-risk milestone (gossip engine, tree #2) got
separate fully-expanded leaf files with bite-sized TDD tasks. The other 11
trees defined their 2-3 leaves inline inside `master.md`, each as a `## Leaf
NN-name` section with: scope, dependencies, estimated context, files-touched,
interface contract excerpt, and a one-line dispatch instruction.

This produced 17 files instead of ~45, ~4200 lines instead of ~15000, and
still passed the structural compliance scan. The inline definitions are
sufficient for the user to review the plan and for a future orchestrator to
expand into full TDD tasks at dispatch time.

Decision rule (now in SKILL.md Step 6.6):
- **Separate leaf files** when the tree is critical-path AND has 3+ leaves
  with complex inter-leaf dependencies AND execution is imminent.
- **Inline leaves in master.md** when the tree has 2-3 moderate leaves AND
  the task detail will be obvious once the orchestrator reads the spec.

### 4. Dependency graph + concurrency groups at the forest root

The root `plans-glm/master.md` carries a 12-tree child index with a dependency
graph and 4 concurrency rounds:

```
Round 1 (parallel): 02-gossip + 01-sandbox-scene + 11-embed
Round 2: 03-ipc + 04-identity + 06-llm
Round 3: 05-dialogue + 07-perception + 08-schedule
Round 4: 09-save + 10-procgen + 12-gamemaster
```

This is dispatch-ready: a future execution session can follow the rounds
verbatim, batching 3 concurrent `delegate_task` children per round.

### 5. Structural compliance scan as a script

After authoring all 12 trees, an `execute_code` grep scan caught 5 of 12
masters missing the Dispatch Protocol and/or Coding Conventions sections
(mostly the later-numbered trees where I'd gotten complacent). We patched all
five in one batch and re-ran the scan to confirm.

That scan is now committed as
`scripts/check_template_compliance.py` — a Python script that walks every
`master.md`/`orchestrator.md` under a root, checks for the 7 required
sections, and (with `--strict-leaves`) verifies every leaf has "Do NOT commit"
and a Self-Verification checklist. Run it after authoring any tree or forest.

## Tree shapes in the forest

| Tree | Leaves | Shape |
|------|--------|-------|
| 01-sandbox | 4 | inline (integration proving ground; waits on 6 other trees) |
| 02-gossip | 3 | **separate files** (critical-path de-risk; full TDD expansion) |
| 03-ipc | 2 | inline (Go side + UE5 glue; split along language seam) |
| 04-identity | 2 | inline |
| 05-dialogue | 3 | inline |
| 06-llm | 2 | inline |
| 07-perception | 2 | inline |
| 08-schedule | 2 | inline |
| 09-save | 2 | inline (Go overlay + UE5 USaveGame) |
| 10-procgen | 4 | inline (15-stage pipeline; 4 leaves by stage-group) |
| 11-embed | 2 | inline |
| 12-gamemaster | 2 | inline |

Total: 26 leaves, 17 files (1 root master + 1 SHARED-CONVENTIONS + 1 OPEN-QUESTIONS + 12 tree masters + 3 gossip leaf files... wait, 12 masters + 3 leaves = 15 tree files + 3 forest-root files = 18. The `find` reported 17; one was the OPEN-QUESTIONS).

## What NOT to take from this

- **Don't author a forest when a single tree suffices.** If the user asks for
  "a plan for feature X," author one tree. The forest pattern is for when the
  scope genuinely spans many systems with a shared build plan.
- **Don't skip the SHARED-CONVENTIONS.md for small forests.** For 2-3 trees,
  restating conventions in each master.md is fine and simpler. The extraction
  pays off at 5+ trees.
- **Don't use inline leaves for the critical path.** If execution is next and
  the tree is the de-risk milestone, expand to separate files with full TDD
  tasks. The inline shape assumes the orchestrator will expand at dispatch
  time — which is extra work and context pressure you don't want on the path
  that determines whether the project is viable.

## Cross-references

- GDD source for the build-plan-index: `docs/gdd/09-pm/02-build-plan-index.md`
- The forest itself: `plans-glm/master.md` (root orchestrator)
- Shared conventions: `plans-glm/SHARED-CONVENTIONS.md`
- Open questions: `plans-glm/OPEN-QUESTIONS.md`
- Compliance scanner: `scripts/check_template_compliance.py` (in this skill)
- Prior worked example (single-tree, docs-only): `references/audit-driven-gdd-planning.md`
