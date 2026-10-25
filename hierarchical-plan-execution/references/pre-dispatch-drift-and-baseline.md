# Pre-Dispatch Drift Audit + Baseline Snapshot

Leaf docs are written at planning time; the codebase moves before execution.
Two orchestrator-side checks before each wave dispatch prevent the two
recurring failure shapes: leaves chasing stale symbol references, and
unattributable test failures during the wave.

## 1. Symbol drift audit (~5–10 min per tree)

For each leaf doc, grep the key files/symbols the doc names BEFORE
dispatching. Planning-time docs drift: functions move files, rules tables
move, accessors change shape. Real examples from one tree
(docs/plans/skill-authoring-and-media-ingest/, 2026-09-06):

- Leaf said `internal/skills/discovery.go` scanTier/loadSkillFile — they
  actually live in `internal/skills/source_file.go`.
- Leaf said security rules in `internal/security/engine.go` — the seed
  table actually lives in `internal/security/seed_rules.go` (SeedRules →
  seedToolRules()).
- Master said "writer wired at initializeSkills" — true, but the leaf's
  ordering claim needed the actual call-chain grep (components.go:2237
  registerBuiltinTools runs before initializeSkills at :869/:6914), which
  decided WHERE the wiring leaf must register tools.

Fold each correction directly into that leaf's dispatch context: "X lives
in <file> (the leaf doc's <file> reference is stale)". A drift-corrected
dispatch costs one sentence; a leaf that discovers the drift itself costs
a review cycle or a wrong-file implementation.

Also verify any "register/extend <init function>" leaf's ordering claims
by grepping the actual init call chain before wave B dispatches — do not
trust the master's line numbers across sessions.

## 2. Baseline build + scoped test before wave dispatch

Record green/red state of exactly the packages the tree will touch, before
any leaf writes:

    go build ./internal/<pkg1>/... ./internal/<pkg2>/...
    go test  ./internal/<pkg1>/... ./internal/<pkg2>/... -count=1

Then any red DURING the wave is attributable: leaf-introduced vs
pre-existing. Without the snapshot, a wave of 4 parallel leaves in one
package turns one flaky/sibling failure into a misattributed review loop.

## 3. Repo-wide build breaks owned by sibling WIP

Untracked sibling scratch files can break `go build ./...` while every
tree package builds clean (real case: untracked cmd/skillparse_main.go
referencing a nonexistent exported symbol). Response:

- Scope all build/test verification to tree packages for the whole tree
  execution; do not run bare `go build ./...` as a gate.
- Note the pre-existing break (file + error) as an Observation in the
  session report. Never fix or delete sibling scratch files.

## 4. Dispatch-context sibling-contention lines (what worked)

For N parallel leaves landing in one Go package:

- "Your diff is <files> ONLY. Another agent is concurrently adding
  <sibling files> to this package — do not touch or be surprised by them."
- For the leaf whose sibling is its convention-mirror source (patch tool
  mirrors create tool): "mirror the conventions stated in YOUR leaf's
  Context section; do NOT reference sibling symbols; do NOT touch
  sibling files."
- For a leaf owning a whole package alone (e.g. internal/skills): say so
  explicitly — "You own this package this wave; no other agent touches it."
