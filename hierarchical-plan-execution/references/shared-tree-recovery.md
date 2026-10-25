# Shared-Tree Recovery Recipes (orchestrator side)

Companion to `references/shared-checkout-contention.md` (leaf-agent view of the
same environment; read that one for mid-edit HEAD-detachment recovery and
hunk-level staging discipline). This file holds the MAIN-MODEL/ORCHESTRATOR
lessons from running a 12-leaf tree through parallel background delegates in
one working tree.

> Tip: SKILL.md sits at the 100K char limit — put new execution lessons HERE
> (or in a new references/ file), never in SKILL.md.

## Pre-commit state ritual (every post-wave commit)

Run BEFORE any commit in an orchestrated tree:

```
git branch --show-current        # empty == detached; check branch ref still correct
git log --oneline -3             # tip matches your last known orchestrator commit?
git status --short | grep -v '^??'   # staged set = EXACTLY the leaf files you intend
```

Real catches from one session:
- Repo found detached 3 commits behind while branch ref was fine — nothing lost,
  but committing from detached HEAD would have orphaned subsequent work.
- An agent doing baseline renders/stash dances caused it; another leaf caught its
  OWN dependency vanishing mid-edit and self-recovered via
  `git show <sha>:<path>` — worth passing that technique into dispatch context
  whenever tree state may shift under a long-running leaf.

Untracked files shadowing committed paths block branch checkout. Compare each
against the committed version (`git show <sha>:<path> | diff - <file>`):
identical → safe to rm; differing → mv aside, checkout, mv back, review as a
normal modification. Never `checkout -f`; differing outputs are usually real
work-in-flight matching a documented deviation — verify before preserving.

## Phantom artifacts (trust-then-verify)

A spike agent's summary asserted "Report written at docs/plans/.../00-phase0-report.md".
The file did not exist. Full summaries persist at
`~/.hermes/cache/delegation/subagent-summary-*.txt`.

**Orchestrator rule:** after every leaf report, stat/read each named deliverable
path BEFORE acting on or committing summary content. If absent, reconstruct from
the cached full summary yourself (it contained all findings) instead of
re-dispatching the leaf — saved a full 15-minute cycle.

## Privileged-step denials are valid outcomes

Leaves running docker compose / unknown setup scripts can be DENIED at the
terminal-approval prompt (shared machine, operator away). Denials terminate the
step; sideways retries (`docker compose up` directly) violate the denial terms.

Dispatch-context pattern:
1. Pre-warn in the dispatch brief: "X may need an operator approval click; if
   denied, stop that step and write UNVERIFIED markers per affected item — a
   blocked run with honest markers is a COMPLETE outcome, not failure."
2. Salvage the run regardless: clone/port-prep/source-derived static findings can
   replace several runtime checks outright (signature schemes, field names,
   event-type tables came out of reading pinned upstream source).
3. Gate flow when the item gated downstream branches: record a reasoned fallback
   in the plan tree's Open Questions (e.g. "STATIC-GO: build code inert behind
   env-var config; runtime proof deferred to staging smoke"), update dependent
   branch docs to match, and surface the decision to the user rather than
   silently assuming GO.

## Sibling workstream reconciliation (review/fix phases)

When a review-then-fix pass runs in a tree another agent is actively editing:

1. **Detect active editing before touching anything.** `stat --format '%y'`
   over the dirs you intend to modify; any file written in the last ~5
   minutes means an agent is editing NOW. Poll until quiescent (no repo
   source file modified in the window) before patching, fixing, or
   committing. Real case: `funding.go` modified 42 seconds before a planned
   edit.
2. **Their uncommitted fixes are fixes.** If another wave's uncommitted
   edits already resolve a finding your reviewer reported, verify the
   combined tree (build + full tests across affected modules) and attribute
   the fix in the review record — do NOT double-fix, and do NOT commit
   their wave; landing it belongs to that workstream.
3. **One mechanism, two claims.** Two waves discovering the same bug class
   (e.g. fail-closed guards) will both try to fix it. Attribute by who
   already wrote the fix, not who reported first.

## Subagent attrition

Reviewer/leaf subagents occasionally die mid-run on provider rate limits
(HTTP 429) AFTER doing real work. Re-dispatch unchanged with the same brief;
treat the failure as retryable infrastructure, not a verdict.

## Multi-commit regression review mechanics

- **Scope by merge-base, not HEAD~N:** `git diff $(git merge-base
  origin/<branch> HEAD)..HEAD`; exclude docs already reviewed; split into
  per-area reviewer dispatches (money-path vs DB/infra/UI, etc.) rather
  than one reviewer for a huge diff.
- **Baseline worktree separates pre-existing from regression:** when a
  test fails in the reviewed range, `git worktree add /tmp/baseline-<sha>
  <merge-base>` and re-run there. Fails identically at baseline =
  pre-existing (harness gap, older bug) — record it, do not fix in this
  wave; fails only at HEAD = true regression, fix now.
- **Secrets/debug quick-scans before dispatching reviewers:**
  `git diff <base>..HEAD | grep '^+' | grep -iE '(api_key|secret|password)'
  ` (filtering obvious test/placeholder hits), plus `gofmt -l` / debug-print
  greps on changed Go files. Cheap catches leave the expensive reviewers
  fewer distractions. Note: a struct-field addition can break gofmt tag
  alignment — always gofmt-scan changed files, whitespace-only fixes commit
  separately.
