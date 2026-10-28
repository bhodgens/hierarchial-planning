# Aadversarial re review of committed work
When to use: post-landing re-review of a finished tree.
Lesson: reviewing COMMITTED state is immune to sibling reverts; parallel reviewers with fix authority.

# Post-landing adversarial re-review of committed plan-tree work

(meept skill-evolver-proposal-lifecycle tree, 2026-09-01 — the wave that ran
after all four leaves were committed. This file is the dispatch pattern; the
attack lists that caught real issues are at the bottom.)

## Why re-review committed work specifically

- **Immune to the sibling-revert class.** Nothing under review is
  uncommitted, so reviewers can't destroy each other's or the leaves' work
  (see pitfall-sibling-git-restore-revert.md).
- **Reviewer fixes are the only dirty files in the tree**, so
  post-wave inventory is `git status` on the touched packages — trivial.
- **The commit message is NOT evidence.** Every brief says so explicitly:
  "do NOT trust the commits' messages — verify claims in code." Commit
  messages were written by agents under pressure; the re-review's job is to
  be the adversarial pass the original per-leaf review might have missed.

## Scope carve-up that worked (3 reviewers, disjoint)

1. **Leaf-pair correctness reviewer** — takes the leaves that share a
   package (here: 01 sink/provenance + 04 verifier gating, both in
   `internal/skills/lifecycle/`). Attacks: round-trips through OTHER
   components' rewrites, boundary math at both thresholds, dispatch holes
   (can a proposal reach the wrong gate with nil payload?), concurrency
   guards, real-HOME test contamination.
2. **Leaf-pair correctness reviewer #2** — the other pair (02 tier
   resolution + 03 approval actuator). Attacks: read-path/write-path
   symmetry (WriteSkill vs ArchiveSkill targeting the SAME resolved tier —
   split-brain check), idempotency across daemon restart, bus topic
   exact-string match both sides, concurrent write races on the same file
   (approval status write vs applied-marker write), driver-specific
   behaviors (SQLite DSN pragmas), name-recovery parsing worst cases
   (dashes inside segment names).
3. **Integration/wiring reviewer** — crosses ALL leaves. Attacks: bus
   payload SHAPE match (field names, not just topic), generated topology
   freshness (does the new bus edge actually appear in
   docs/generated/bus-topology.md?), config knob end-to-end paper-walk
   (config file → normalize → construction → sink), daemon shutdown
   lifecycle (store close, cancel funcs, unsubscribe, double-shutdown),
   and CLI/UI visibility — the store-split trap (below).

## The brief template per reviewer

- Scope: exact commits + exact files + the plan leaf docs.
- "FIX AUTHORITY for real defects; report-only for judgment calls."
- "Do NOT trust commit messages — verify claims in code."
- Numbered ATTACKS list (8-9 specific, checkable attacks; each phrased as
  a question with a falsifiable answer).
- Known/accepted decisions spelled out so reviewers don't re-flag them
  ("the leaf doc still shows the OLD gate polarity — code is source of
  truth; do not 'fix' the code to match the doc").
- Verify command battery scoped to touched packages.
- DO NOT COMMIT (orchestrator owns the post-wave commit).
- Report format: per attack — verdict OK/BUG; defects (file:line, what,
  why); fixes applied + evidence; judgment calls; observations.

## Attacks that caught real issues this wave (reuse these)

- **Provenance stripped by approval rewrite**: the plan parse→write
  round-trip (UpdatePlanStatus) dropped unknown Meta keys — destroying the
  provenance stamp the actuator reads. Fix: `ParsedPlan.ExtraMeta`
  preservation + regression test. Any stamped-in-file marker must be
  tested against every writer that touches the file.
- **Driver-specific DSN pragmas silently ignored**: modernc.org/sqlite
  only honors `_pragma=...`; `?_busy_timeout=` style params are no-ops —
  WAL/busy-timeout were OFF and a concurrent read could fail with
  SQLITE_BUSY. When a store fix touches connection strings, verify the
  actual driver's accepted parameter forms.
- **Store-split visibility**: plans in a DEDICATED sink store are
  invisible to list/approve surfaces that resolve the SHARED store —
  the approval dead-end reborn at the UI layer. Every surface's store
  resolution must be traced when a feature splits stores.
- **WriteSkill tier split-brain** (verify even when it passes): trace
  read-path and write-path resolution separately — archive may resolve the
  tier while refine writes to the legacy root, and both suites stay green
  if fixtures only exercise one direction.
- **Shutdown lifecycle**: bridge subscriptions need an unsubscribe/stop
  path tied to the component cancel func, and a test that shutdown order
  can't half-apply a plan.
- **Legacy backlog fate**: pre-migration artifacts (plan files with ids in
  the old store's id-space) — trace what list/approve do with them; if
  unreachable, document precisely as a known limitation rather than
  half-fixing.

## Orchestrator close-out

After the wave: run the full gate battery (build, all touched package
suites, generated-graphs check, downstream consumer suites), commit
reviewer fixes in one commit referencing the wave, update the tracking
table, then report. If reviewers fixed nothing, that is a valid outcome —
the wave's value is the verified-in-code claim.
