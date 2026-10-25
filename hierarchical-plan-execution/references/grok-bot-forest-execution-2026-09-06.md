# Grok-Bot Blueprint Forest — Close-Out Session (2026-09-05/06)

Four plan trees authored + executed in one session (gap analysis → Q&A →
4-tree forest → sequential/parallel execution → follow-ups → live switch).
This file records what the generic skill + existing references did NOT
cover. Companion to meept-plan-tree-execution-2026-09.md and
plan-tree-execution-2026-09-05.md (meept-development umbrella).

## The full arc, compressed

1. **Gap analysis first, plans second.** Read the external article via
   fxtwitter API (web_extract on `api.fxtwitter.com/<user>/status/<id>`
   returns full article JSON incl. content blocks — no X account/API key
   needed; x.com direct extract fails). Extracted the article's
   capability checklist, then grep-swept the repo for each primitive
   (hash chain, DAG, idempoten*, source_ids...). Delivered a verdict
   with code-verified file:line anchors per gap. **A grep for absence is
   NOT proof of absence**: I claimed "no frontier scheduler" from a
   DAG/frontier grep that missed `ScheduleReadySteps` (tactical.go) —
   the user pushed back, re-exploration found task-level frontier
   already existed and only PHASE-level was serial. Scope the grep to
   the domain vocabulary ("ready", "pending→promote") before declaring
   a capability missing.

2. **Parallel authoring of the 4 trees** (delegate_task batch). Two
   authoring quirks: (a) batch shape requires `tasks[].goal` — a
   top-level `goal` with only `context` fails; (b) author agents
   VERIFIED my anchors and corrected them (git push lives in
   internal/backup, not internal/workspace; push service file names).
   Let authors verify; do not pre-freeze file:line in dispatch contexts
   without their own survey.

3. **Execution order: parallel across trees, serial within a tree.**
   Trees 1-3 ran their leaf-01s concurrently (disjoint packages), then
   leaf-02s concurrently, etc. Tree 4 (orchestrator hot path) ran fully
   sequential per its master. Global serialization is wasteful; per-tree
   dependency is the only real constraint.

4. **Contract-vs-reality conflicts are expected and good.** Every tree
   surfaced at least one: leaf test-table cases contradicting frozen
   rules (rules win, errata recorded in OPEN-QUESTIONS.md), pinned DSN
   keys silently ignored by modernc.org/sqlite (only `_pragma=` works),
   superseded claims unreachable via GetByID (is_current filter), Run()
   refusing re-claim so the reconciler must drive the state machine
   directly. Pattern: leaf REPORTS the conflict with evidence, keeps the
   pinned surface byte-identical, adapts only the mechanism/test;
   orchestrator records the resolution in OPEN-QUESTIONS so later leaves
   and readers see it. Never let a leaf "just fix" a contract.

5. **Errata flow.** When a leaf's OWN test table contradicts its own
   normative rules ("iff" text), the rules win; the adjudication goes to
   the tree's OPEN-QUESTIONS.md with case-by-case reasoning. Two
   independent leaf-01 runs (double-dispatch) reconciled to the SAME
   errata independently — convergent validation.

6. **Real bugs found by surveys, fixed in scope.** Leaf-03's single-slot
   survey found leaf-02's re-entrancy guard missed started-not-yet-
   scheduled steps (still StepPending) → double-start B→C→C→D. Fix
   (stamped ConversationID counts as started) landed in leaf 03's
   commit with the survey cited. Encourage leaves to fix in-scope
   defects the survey surfaces rather than deferring.

7. **Review-grade defects caught in-session (orchestrator duties):**
   - Racy test: duplicate-send test counted one session topic before
     the other drained (non-blocking bus fan-out). Fix: wait for ALL
     topics before counting; verify with N consecutive runs.
   - Hook fix-ups: leaf ignored errors (`_ = tx.Rollback()`) → commit
     blocked; repaired with the house park_store_sqlite rollback-log
     pattern BEFORE commit.
   - Untracked probe dirs left by leaf agents (auditlog_tmp) — never
     stage them; rm needs user consent (denied — see next).

8. **Consent-gated rm is a recurring dead end.** `rm -rf` of scratch
   dirs was denied twice across the session (and again for ~/git/meet —
   a leaf's typo'd repo path). Do NOT retry; list the paths in
   NEXT-STEPS.md as user-owned cleanup and move on. Same for compound
   one-liners and `mv` chains — issue discrete commands.

9. **Follow-up round ("do followups including X and verify/test").**
   The parked follow-ups (RPC handler, production provisioner, DSN
   landmine) were each one-session-sized and done directly in-session
   — no subagents needed; each had landed context. The provisioner was
   the largest: a pure function + daemon wiring + table tests with a
   real temp git repo (git worktree add --detach; idempotent on
   restart; degrade-to-empty for non-git projects).
   Verification: config.Load round-trip of the live user config via a
   temporary in-package test (rm after), daemon restart, and grep of
   the live log for the three wiring lines ("Orchestrator parallel
   phases configured" enabled=true / "Phase worktree provisioner
   wired" / "Effects RPC handlers registered").

10. **Live switch discipline.** Rebuild binaries to the INSTALL PATH
    (/Users/caimlas/go/bin), kill the old daemon PID, relaunch
    foreground-under-background-session. Note explicitly to the user
    that a daemon launched from the agent's background session dies
    with the agent session — their launcher must own long-lived runs.
    Config precedence: `data_dir` key overrides `state_dir`-derived
    paths per-field (uploads pattern) — mirror the existing per-field
    override convention when adding new data-dir-rooted paths.

## Frozen-contract hygiene that worked

- Contract quote-at-definition: leaves kept the pinned Go signatures
  verbatim and put deviations in OPEN-QUESTIONS with Q/Rec/Impact.
- "Deviation = STOP-and-report" in every dispatch context produced
  three high-quality conflict reports and zero silent contract breaks.
- Errata notes in tree OPEN-QUESTIONS.md (not buried in commit
  messages) kept the contract record where later leaves read.
