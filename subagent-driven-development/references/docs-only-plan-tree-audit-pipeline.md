# Docs-Only Plan-Tree Audit-Fix-Verify Pipeline

When to use: a full audit-fix pass over a docs-only plan tree (no code exists).
Lesson: 5 parallel audits, dependency-ordered fixes, then SPLIT verifiers separate fixing from judging.

Full-project review where the deliverable IS the documentation (plan trees,
orchestrator docs, research YAML)  -  no code exists. Proven end-to-end on a
30-file plan tree: 5 parallel audits → direct + delegated fixes → 2 parallel
verifiers, all majors resolved.

## When to Use

- "Review this project in entirety and fix any gaps/omissions/unwired code"
  when the repo is plan/spec docs rather than source.
- Pre-dispatch audit of a plan tree before executing it (cheaper than fixing
  leaf agents that built against contradictory specs).

## Phase 1  -  Parallel Audits (one subagent per section)

Split by tree section (root+research, branch A, branch B, ...), one
delegate_task each. Every audit context MUST say:
- "Do NOT edit files. Report numbered MAJOR/MINOR findings with exact
  file:line, evidence quote, concrete proposed fix."
- What to check: cross-references resolve on disk; contract schemas match
  reality field-by-field; status tables vs actual deliverables ("marked done
  that isn't"); contradictions between files; placeholders/TBDs; make-target
  or CLI defined-by-nobody / consumed-but-never-produced fields.

Typical yield: ~1 major finding per file. Highest-yield checks are
(1) authority-file schema vs contract (e.g. yaml top-level keys don't match
what every consumer reads), (2) decisions recorded in one file but never
propagated to contracts/open-questions upstream, (3) handoffs where branch N
writes only to a store branch N+1 is forbidden to read.

## Phase 2  -  Fix Ordering

Fix in dependency order:
1. **Root contract + authority files directly** (master.md, source-truth.yaml)
    -  everything depends on them; verify mechanically after (yaml parse +
   required-keys script).
2. **Branch fixers in parallel**, each with: the exact numbered fix list from
   the audits (file:line, old→new), the already-fixed upstream facts ("do not
   touch master.md/source-truth.yaml; they now say X"), and explicit
   file-ownership boundaries when two fixers touch adjacent branches.
3. Accept cross-branch single-line additions (a fixer may add one CLI spec to
   a sibling branch's doc if named explicitly).

## Phase 3  -  Verification (split to avoid timeout)

A monolithic verifier over 30 files WILL time out at 600s (~50 tool calls).
Dispatch TWO verifiers with disjoint checklists and instruct targeted grep,
not full-file reads. Verifier checklist should include: each fix landed with
evidence lines; counts stated identically everywhere (endpoint inventories,
schema key lists); leftover-contradiction grep for the OLD strings; markdown
code-fence parity (even ``` count per file).

Expect one residual per verifier; fix directly (<10 lines) and confirm by grep.

## Recurring Finding Classes (watch for these)

- **Late decision never propagated**: vendor/approach DECIDED in one artifact;
  master contract + open questions + leaf dispatch contexts still describe the
  old choice.
- **Contract schema drift**: authority YAML renamed/restructured without
  updating the contract that specifies it (or vice versa).
- **Cross-boundary store mismatch**: producer writes to Postgres while
  consumer's architecture says "parquet/DuckDB inputs only"  -  needs an export
  step assigned to a named leaf.
- **Status tables lag reality**: deliverables committed but tables say PENDING.
- **Arithmetic at operating point**: window sizes that can't feed the estimation
  windows a later task requires (±250td pull vs 261td estimation need).

## Update Tracking After

Bump the plan-tree's own tracking tables (status, review notes incl. process
deviations like "leaf completed in-session after subagent timeout") as part of
the fix pass, or the next audit re-finds them.
