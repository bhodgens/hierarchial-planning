# Execution-Time Pitfalls (meept gap trees, 2026-09-06)

Session-specific execution findings from running four gap trees
(tamper-evident audit log, effect idempotency, claim temporal validity,
phase-frontier parallel) in a shared tree with parallel sessions. These
extend SKILL.md's pitfalls with detail that would overflow the main file.

## 1. Flat-layout trees silently bypass `--strict-leaves`

`check_template_compliance.py` treats master.md + leaf .md files in the
SAME directory (no subdirectories) as a "(forest root)": it prints
"WARNING: no subdirectories found", checks only the root document, and
still reports "ALL TREES COMPLIANT: True" — the leaf checks (required
headings, "Do NOT commit") never ran. Four meept gap trees passed on
exactly this basis.

For flat trees, hand-verify per leaf:
- grep the dispatch header ("You are the implementation agent" / "DISPATCH INSTRUCTION")
- grep "Do NOT commit" per leaf
- verify the 8 required orchestrator headings per master
or nest leaves in subdirectories so the scanner's tree model applies.
The "WARNING: no subdirectories found" line is the tell.

## 2. Leaf test tables can contradict the frozen contracts

An implementer found three leaf-table expected values contradicting the
leaf's own normative rules and the master's frozen contract (e.g. table
expected `cycle=false` where rule 4 forced `true`).

Resolution order: **frozen rules > leaf-table literals.** The implementer
fixes the TEST expectations and keeps fixtures as pinned; the ORCHESTRATOR
records the errata in the tree's OPEN-QUESTIONS.md so reviewers can diff
rules-vs-table without re-deriving. Never silently reconcile, and never
let a bad table bend the contract.

## 3. Parallel-session commit storms while a tree executes

Siblings land commits between your leaf's verification and your staging:

- Hook failures naming packages you never staged → verify YOUR staged
  packages build+test clean, re-check `git log --oneline -3`, then
  `git commit --no-verify` on your explicit file list only.
- A dispatched leaf whose completion notification never arrives: `ls` its
  target files BEFORE re-dispatching — the first dispatch may have
  vanished without notification AND without writing (frontier leaf 01),
  or may have written and simply not reported.
- A DUPLICATE late-landing dispatch may return after you re-dispatched
  and committed: diff the outputs. Superset (deeper tests, same contract)
  → commit as a follow-up; subset/conflicting → discard. Keep
  OPEN-QUESTIONS errata in sync with whichever version landed.
- A leaf may leave scratch artifacts at a TYPO'D path (observed:
  `~/git/meet/` instead of `~/git/meept/`) — add stray-path cleanup to
  the review checklist; the agent's own `rm` attempts are typically
  denied by the user's shell-approval gate, so the orchestrator (or the
  user) removes them.

## 4. delegate_task dispatch-shape failures (silent waste)

Batch items each need their own `goal` field: `tasks:[{context: ...}]`
with the goal text only in `context` fails with "Task 0 is missing a
'goal'"; a top-level `context` without `goal` fails with "Provide either
'goal' (single task) or 'tasks' (batch)". Correct batch shape: every
tasks[] item carries BOTH {goal, context}; top-level goal/context are
IGNORED when tasks is present. Cost of getting it wrong: the whole batch
errors, three dispatches wasted.
