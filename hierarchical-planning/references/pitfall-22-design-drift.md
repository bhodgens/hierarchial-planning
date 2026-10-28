# Pitfall 22 - Design Drift Between Sibling Sessions (Post-Authoring Spec Movement)

When to use: a project has an active changelog or parallel sessions that can change design docs after your plan was authored.
Lesson: contract digests read the spec as it exists TODAY; only a changelog-review digest catches drift that happened AFTER you read it.

On an active project, the design doc is a moving target. A parallel session (another agent, a human, a doc-completion tree) may ratify new constants, cut a system, or rename a field AFTER you read the spec but BEFORE you execute the plan. Your plan's contracts were faithful at authoring time but are now stale - and neither the structural scan (tier 1) nor the contract-verification digest (tier 2, which reads the current spec file) will catch it if you don't think to re-read.

Worked example: hill heights were ratified to different values (Pemberton 24m to 34m) by a primary-source-research commit that landed while the plan was being authored; a procgen condition label changed; an active-tier cap was unified across 4 docs. None were visible by re-reading the current spec file alone - the changelog was the only source of the drift.

## Prevention

After the contract-verification digests, run a changelog-review digest (Review Protocol section "Tier-3 Verification", full recipe in `references/changelog-review-digests.md`): one subagent reads the project changelog + recent commits and flags any entry touching a plan spec source. This is mandatory on any project with an active changelog (per the `design-plan-consistency` skill, Rule 2).

The cost is one subagent dispatch; the alternative is executing a forest against ratifiable-but-now-wrong values.
