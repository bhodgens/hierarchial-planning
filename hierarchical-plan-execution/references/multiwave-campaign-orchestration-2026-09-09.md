# Mmultiwave campaign orchestration 2026 09 09
When to use: 10-issue campaign in 4 waves.
Lesson: frozen contracts beat prose, serialize-on-consumption, leaf report anatomy, action-SHA pinning.

# Multi-Wave Campaign: 10-Issue Platform Parity (humanplusone, 2026-09-09)

Worked case: user asked for 10 GitHub issues → "systematically, create
hierarchical implementation plans for each of those github issues then
execute them." Executed waves 1-4 with zero re-dispatches. This file
captures the orchestration decisions that made it work, distinct from the
openbot-parity-campaign-shape.md reference (issue/planning anatomy).

## 1. Issue → plan-tree conversion: frozen contracts beat prose

Ten issues were converted to one master.md + 10 wave docs + 16 leaves in a
single session. The load-bearing decision: **contracts, not descriptions**.
master.md carried five FROZEN artifacts — exact CREATE TABLE DDL
(audit_log), exact scrubber replacement format string, exact policy JSON
schema, exact control-state endpoints, exact MCP tool naming
(`mcp__<server>__<tool>`). Every leaf said "Contract A, frozen" and cited
the master. Result: four leaves written by four independent subagents over
four waves produced mutually-compatible code with zero integration fixes.
A contract column is testable (PRAGMA table_info == contract); a prose
description is not.

## 2. Parallelize within a wave ONLY when file sets are disjoint; serialize on output dependency

- Wave 1: two leaves, disjoint files (workflows vs scripts/tests) → parallel,
  landed clean.
- Wave 2: two leaves, ONE shared file (ci.yml) → parallel with explicit hunk
  ownership ("you own ONLY the install step; do not touch the rest") → clean.
- Wave 3: leaf 3.2 imports/writes through 3.1's write_audit → **sequential**,
  with the dispatch context stating "3.1 is ALREADY LANDED at <commit>, read
  its API before use." Rule: a leaf that CONSUMES a prior leaf's new API must
  dispatch after that leaf's commit, never concurrently — the sibling-RED
  class of failure, prevented instead of repaired.
- Wave 4: same — 4.2 queues behind 4.1 because both touch config.py regions.

Say WHY in the tracking table when serializing. ("Sequential by design — 3.2
consumes 3.1's writer.")

## 3. Action-SHA pinning: model memory 404s — verify or install-script

A leaf pinned `hashicorp/setup-tofu@32fffe55...` from model memory;
`gh api repos/hashicorp/setup-tofu/commits/<sha>` → 404. Never write an
action SHA without a live verification. Verification recipe that worked:
resolve tag→commit via `gh api repos/<owner>/<repo>/commits/<tag>` (or
`git ls-remote` equivalent) and cite the resolved commit date in the report.
When verification fails or is denied, do NOT fall back to memory — fall back
to the vendor's version-pinned install script in a `run:` step (OpenTofu:
`get.opentofu.org/setup-opentofu.sh --opentofu-version X`), with a comment
naming why the action was avoided. The corrected workflow (pinned SHAs for
checkout/setup-python + install-script for tofu) is in the repo's
.github/workflows/ci.yml.

## 4. Leaf report structure that made review fast

Every leaf report carried, in order: RED evidence (test failure output),
GREEN evidence (suite counts + coverage %), files-touched list, and
"issues hit & resolved". Two leaves self-reported latent bugs they hit and
fixed (UTF-8 orphaned-lead-byte truncation; webhook error-path audit commit
before rollback) — the "issues hit" section is where review value clusters.
Orchestrator verification pass per leaf (kept to minutes): `git diff --stat`
for ownership boundaries, one direct probe of the new API (schema PRAGMA, one
scrubber call), full suite re-run. Three of four leaves were accepted on
leaf evidence + static diff review alone; consent gates denied live re-runs
on two others and leaf evidence was cited instead.

## 5. Consent-gate interaction: /tmp artifacts stay

`rm -f /tmp/verify-audit-*.db` was denied (rm class). Protocol applied:
stopped immediately, no rephrase, flagged the leftover path to the user in
the status reply, moved on. Scratch verification DBs in /tmp are disposable
by the user later; do not burn a second denial on cleanup.

## 6. Commit granularity: one commit per leaf, contracts named

One commit per leaf, never batched, each citing the leaf doc path and the
frozen contract it implements. This kept every revert surface leaf-sized and
made the per-wave review trivially attributable. CI-related leaves (#7, #8)
carried `Closes #N`; mid-campaign leaves carried `Refs #N` — close issues
only at the campaign gate when the FULL issue scope is demonstrably done.
