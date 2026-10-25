# Design Adjudication Sessions (Research → Amendment Plan → Forward-Port)

When the user raises a design-level problem ("X is wrong/balanced wrong", "we
need to add Y"), the fix is a GDD adjudication, not a code change. The
session shape that works, end to end:

## Procedure

1. **Answer feasibility first.** State what is researchable accurately and
   what is not, before any research. For belief/ideology content, distinguish
   documented history, documented period beliefs, and modern myth in the very
   first message — the user then steers scope with full information.
2. **Fan out research in parallel** (one subagent per topic group; per
   historical-source-verification Phase 0). Each writes findings files into
   the repo (`docs/research/`), NOT into the GDD. Research-only commits need
   no changelog row — Rule 1 covers GDD modifications only.
3. **Independently re-verify headline quotes/claims** before trusting child
   files (fetch the primary text, grep the cached file). Cite the check in
   the amendment plan.
4. **Write an amendment plan doc** (`docs/research/gdd-amendment-plan.md`):
   - State the confirmed defect with `path:line` citations from the current
     GDD (e.g. asymmetric ending specs).
   - List each amendment as B1..Bn with target file + concrete content shape.
   - Name a forward-port section (B-last) listing the downstream spec docs
     (sidecar wire/gossip/quest docs) the change must reach later.
   - End with the procedure block: apply → changelog same session → drift
     check → forward-port as separate tree.
5. **STOP for user review of the plan** (prepare-then-stop). Apply B1..Bn
   only on approval.
6. **Apply in one session:** GDD edits + Rule 1 changelog row (full
   verification column) + Rule 4 drift check (grep plan trees for the edited
   spec sources; mark STALE if referenced) — all in the same session.
7. **Commit docs** (pre-commit changelog-integrity gate parses the row).
8. **Forward-port as a plan tree:** author a tree whose leaves map the GDD
   change onto sidecar/Godot systems. Freeze contracts in master.md (ID
   namespaces, additive-only wire fields, depiction rules with grep gates);
   dispatch in waves with disjoint file ownership.

## Content-framing patterns that recur

- **Two-strata content rule** (documented-period vs modern/myth material):
  modern material enters as anachronism-class content through the project's
  existing anachronism/pipeline mechanisms with provenance labels — never
  as asserted world-fact. Prejudice appears as NPC belief, never game voice.
  Balance contracts ("every leaning item has an opposite-leaning mirror",
  1:1 print density) go in the GDD as testable design contracts, not prose
  aspirations.
- **Grep gates as contracts:** give each forbidden-scoped string an owner
  file list in the tree master, and enforce it in leaf tests.

## Pitfalls

- **Plan-tree numbers collide silently.** The plans directory shows gaps
  (retired dirs) but numbers are also consumed by cross-cutting trees
  registered only in the build-plan index. Grep the build-plan index rows
  AND list the directory before assigning a tree number; renumber the
  authored tree immediately if taken (do not ship a tree whose master.md
  and directory name disagree).
- **Register standalone trees in the build-plan index at authoring time** —
  a PLANNED tree absent from the index is invisible to every future Rule 2
  drift check, which defeats the governance layer.
- **Research files are not GDD edits.** Keeping findings under `docs/research/`
  avoids a changelog obligation for exploratory passes and keeps the GDD
  decision-only; the amendment plan doc is the bridge between them.
- **User-supplied media sources must be pulled in full before the plan is
  finalized** (see historical-source-verification pitfalls); the audit of a
  user-cited source belongs in `docs/research/` and is cited by the GDD
  content docs as the worked example of the stratum boundary.
