# Authoring a Plan Tree from a Task Brief


When to use: authoring a tree from a task brief referencing prior context.
Lesson: recover context via session_search first, then author with frozen contracts.
The write-time counterpart to `plan-tree-review` Phase 1b (which catches
these defect classes in already-written trees). Do them at authoring time
and the design review passes. Worked example: meept phase-frontier-parallel
(2026-09-05 — master + 4 strictly-sequential leaves + OPEN-QUESTIONS,
docs-only, five frozen contracts A–E).

## 0. Recover the context first

When the task says "per the context" or references a prior discussion
without inlining it, run session_search for the topic BEFORE writing
anything. The prior session holds the DECISIONS the tree must encode (flag
name, policy calls, scope boundaries, rejected alternatives); the repo only
shows where prior decisions landed. Inferring decisions from repo state
alone produces a plausible tree that quietly contradicts what the user
already settled.

## 1. Survey-verify every anchor before it enters a doc

File:line cites, symbol names, struct fields, defaults, and "X maintains Y"
causal claims in a plan are all factual claims. Verify each one THIS
session with batched content searches (`search_files`, context=2-3, several
patterns per call), not from recall — the brief's own anchors are leads,
not facts. Verification routinely RESHAPES the plan: in the worked example,
looking for `checkPhaseReady` moved it from orchestrator_phases.go to
strategic.go:1615; hunting phase-state slots found the single-slot
`BudgetHierarchy.currentPhase` (budget_hierarchy.go:306) which became an
entire leaf task; `resolveStepWorkingDir` lived in internal/daemon/
components.go:7240, not where the brief said. A wrong anchor inherited from
the brief propagates into every leaf that cites it.

## 2. Correct wrong anchors in the artifact AND the report

When a user-supplied or brief-supplied anchor is wrong, fix it in the plan
docs and list the correction explicitly in the session summary ("corrected
from the brief where needed" + the file:line). Silent propagation is how a
stale anchor survives three review cycles; a spoken correction lets the
user veto your reading.

## 3. Pin cross-leaf symbol names explicitly

Contracts written for human readability (capitalized `ComputePhaseFrontier`)
diverge from what the implementing leaf must declare (unexported
`computePhaseFrontier`, same package). Pin the mapping IN the leaf that
creates the symbol ("identifiers are X and Y — the capitalized names in the
contract are presentation only"), or the consuming leaf compiles against
the wrong name and the break surfaces one leaf later, attributed to the
wrong leaf.

## 4. Shared files ⇒ strictly sequential leaf chain

When each leaf edits files a previous leaf touched, order leaves strictly
and SAY SO in the Dispatch Protocol ("01 → 02 → 03 → 04; each leaf edits
files the previous one touched, so no parallel batching"). Concurrency-wave
language on an overlapping-file tree invites parallel dispatch and merge
friction. Reserve waves for genuinely disjoint leaves.

## 5. Flag-gated behavior changes need a flag-off equivalence gate

Any tree that changes behavior behind a config flag must REQUIRE, in the
leaf that flips the dispatch: (a) a table-driven test proving flag-off
reproduces today's exact transition sequence, and (b) the rule "the
existing suite passes UNMODIFIED after the refactor — if any existing test
needs editing, STOP and fix the refactor, not the test." This converts
"we kept the old path" from a claim into a gate. Pair it with a config
contract pinning the key, tags, and zero-value default so serial behavior
survives until the flag is flipped deliberately.

## 6. Parallelization trees need a state-slot survey task

Turning a serial mechanism parallel requires finding every SINGLE-SLOT
piece of state that assumed one-active-at-a-time. Add an explicit survey
task to the leaf that owns cross-component state: fix confirmed slots
(worked example: `currentPhase` misattributes usage under two active
phases), RECORD verified non-slots so future audits don't re-litigate them
(per-phase conversationID stamping, per-phase store columns, keyed maps are
not slots), and REPORT new findings without expanding the leaf's scope
(orchestrator files the follow-up). The survey output belongs in the leaf's
completion report.

## 7. OPEN-QUESTIONS.md: Q / Rec / Impact, leaf-gated

Forks you must not silently decide (default flips, reject-vs-skip policy,
prompt teaching timing, boundary questions) go in a sibling
OPEN-QUESTIONS.md. Each entry: Q (the question), Rec (your recommendation
with the reason), Impact (what changes depending on the answer). Gate the
forks that block a leaf: "resolved by the orchestrator before dispatching
leaf NN; if still open, implement the Rec side and note the deviation."
This keeps leaf implementers from improvising policy while keeping every
decision reversible by the user.

## 8. Prevent authoring artifacts instead of sweeping them

Never author file content by piping `read_file`'s line-numbered output into
`write_file` — the `NNN|` prefixes corrupt the target. Take context via
`search_files` / `cat`, then write from clean source. Bake the prevention
into every leaf's review checklist as a verification grep
(`grep -rcE '^\s*[0-9]+\|' <touched files>` = empty). This is the
prevention half of the post-hoc artifact sweep in
`research-gated-plan-trees.md` — do both.

## 9. Match house format from the newest sibling tree

Before writing the first doc, read the repo's most recent completed plan
tree as the format exemplar (headings, contract style, dispatch protocol,
tracking table shape). Conventions drift between repos and between years;
the newest sibling is the current house style, not the skill's generic
template.

## 10. Close with a mechanical self-scan

After authoring all docs, grep-verify structure before reporting done: the
master's required section headings, per-leaf DISPATCH INSTRUCTION /
Interface Contract / Self-Verification Checklist / Review Checklist
presence, and cross-references (leaf names in master's Child Index match
actual filenames). Cheap greps catch the truncated-heading class of defect
while the tree is still uncommitted.
