# Pitfall 39 - Dual-Audit Pattern for Plan Completeness

When to use: auditing a plan forest against its spec, especially with a sibling implementation.
Lesson: dispatch two parallel auditors - completeness (plan vs spec) and cross-implementation gaps (plan vs the other half's outputs); neither alone is sufficient.

When auditing a plan forest against its spec, dispatch TWO parallel subagents:

**(a) Completeness auditor** - reads every plan leaf against the GDD spec; reports missing features, wrong architecture, stale references. Answers: "does the plan cover the GDD?"

**(b) Cross-implementation gap auditor** - reads the sibling implementation's plan trees (e.g. the Go sidecar's plans) and identifies data/capabilities the target implementation must consume but has no plan for - GossipEvents, QuestUpdates, OcclusionData, NPC identity. Answers: "does the plan cover what the OTHER half of the architecture produces?"

Neither audit alone is sufficient.

## Worked evidence

One session: the completeness audit found 3 CRITICAL + 9 HIGH gaps; the gap audit found 4 CRITICAL + 7 HIGH gaps - only 2 overlapped. Together they caught 21 unique issues.

## Related

- `references/post-authoring-audit-trio.md` - adds a third read-only audit (domain ambiguity) plus citation-drift and architecture audits.
- `references/pre-execution-feasibility-and-citation-audits.md` - the feasibility/citation pair for pre-dispatch.
- Pitfall 24 covers auditing pre-IMPLEMENTED trees; this pitfall covers auditing authored-but-unexecuted plans.
