# hierarchial-planning

A bundle of **Hermes Agent skills** that implement plan-tree (hierarchical)
planning and execution for features too large for one agent's context. Each
leaf of the plan tree is sized to fit a single subagent's 128K context; a
main-model orchestrator dispatches subagents to implement leaves, reviews in
session, and closes a leaf only when the committed state proves the work.

Every lesson in this bundle is distilled from real long-running campaigns
(2026-08 through 2026-10): adversarial audits, 429 rate-limit storms,
sibling-plan races, and live-service integration. The `references/`
directories are where the distilled failures live (pitfall-49 through
pitfall-55, concurrent-leaf dispatch patterns, clean-worktree closeout
recipes).

## The workflow

```
author a tree              ->  hierarchical-planning
   (or a flat single plan)->  writing-plans        (routes to hierarchical-planning when work is concurrent)
gate impl leaves on tests  ->  spec-first-test-leaf-authoring
dispatch + review loop     ->  hierarchical-plan-execution
police closeouts           ->  plan-leaf-validation, plan-tree-orchestrator-hygiene
audit a finished tree      ->  plan-tree-review
keep design <-> plan in sync->  design-plan-consistency
alternate orchestration    ->  kanban-orchestrator, parallel-report-generation
local-only review pipeline ->  local-ravenx-review-pipeline
```

How they link: `writing-plans` or `hierarchical-planning` produce the tree,
`hierarchical-plan-execution` drives the dispatch loop,
`spec-first-test-leaf-authoring` adds the separate-authorship test track,
`plan-leaf-validation` + `plan-tree-orchestrator-hygiene` police the
closeout, `plan-tree-review` audits the finished tree, and
`design-plan-consistency` keeps the GDD/specs from drifting under the plan.

## Skills in this bundle

All 12 are shipped flat at the repo root. Each is a self-contained skill
directory (`SKILL.md` plus `references/`, `templates/`, and `scripts/` where
present) and installs independently.

| Skill | Version | Role |
|---|---|---|
| `hierarchical-planning` | 1.3.0 | Write the tree: master + leaf docs sized to one agent's context. 90+ campaign lessons in `references/`. |
| `hierarchical-plan-execution` | 1.16.0 | Execute the tree: main model orchestrates + reviews, subagents implement. 150+ distilled failures in `references/`. |
| `plan-leaf-validation` | - | Before a leaf closes, prove it against committed state: `git show --stat` file-list check, binary smoke test, clean-worktree re-run. |
| `plan-tree-orchestrator-hygiene` | 1.0.0 | Rules for the *reviewing* orchestrator when leaf work lands uncommitted in a shared repo. |
| `spec-first-test-leaf-authoring` | 1.0.0 | Test leaves (T-xx) written from a spec pack *before* impl lands; tests cite clause ids, not code. |
| `plan-tree-review` | - | Audit a tree for completion + correctness against GDD specs; knows the meept `docs/plans/<forest>/` exception. |
| `writing-plans` | 1.1.0 | Flat single-file plans; routes to `hierarchical-planning` for concurrent work. Adapted from obra/superpowers. |
| `subagent-driven-development` | 1.1.0 | Fresh subagent per task, two-stage review (spec, then quality). Bridge between flat and hierarchical. Adapted from obra/superpowers. |
| `kanban-orchestrator` | 3.0.0 | Decomposition playbook for orchestrator profiles routing work through Kanban. |
| `parallel-report-generation` | 1.0 | Generate long-form reports by fanning work across parallel subagents, then assembling. |
| `design-plan-consistency` | 1.0.0 | Keep GDD/specs and plan trees convergent: changelog discipline, pre-plan drift checks, auto plan-stale detection. |
| `local-ravenx-review-pipeline` | 1.0.0 | Mandatory post-delegation review pipeline for local-only profiles: subagent work gets reviewed by a stronger model before it reaches the user. |

## Installing

Hermes discovers any directory containing a `SKILL.md`. Drop each skill into
your skills tree (flat, or under a category of your choice):

```bash
# per skill:
cp -R hierarchical-planning   ~/.hermes/skills/software-development/
cp -R writing-plans           ~/.hermes/skills/software-development/
cp -R plan-tree-review        ~/.hermes/skills/documentation/
cp -R kanban-orchestrator     ~/.hermes/skills/devops/
cp -R parallel-report-generation ~/.hermes/skills/productivity/
# ... the rest, or simply:
cp -R */ ~/.hermes/skills/
```

You can also register each skill through Hermes' `skill_manage` tool. The
bundled `SKILL.md` `related_skills` fields already cross-link the whole
family, so Hermes will surface the right companion skill when one is loaded.

## Notes on the paths

Some `references/` files quote real campaign logs that mention example repo
paths (e.g. `github.com/caimlas/meept`, a Go module path, or `/Users/caimlas/...`).
These are illustrative examples showing the absolute-path worktree convention,
not machine-specific instructions. The repo is private; the examples are
kept verbatim so the lessons read the way they did when they were learned.

## License

MIT. `writing-plans` and `subagent-driven-development` are adapted from
[obra/superpowers](https://github.com/obra/superpowers) (MIT); the bundle
remains MIT-compatible. See [LICENSE](LICENSE).
