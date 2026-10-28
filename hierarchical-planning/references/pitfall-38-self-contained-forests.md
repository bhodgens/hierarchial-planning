# Pitfall 38 - Plan Forests Must Be Self-Contained (No Cross-Forest References)

When to use: a project has multiple plan forests for different implementation targets (e.g. a Go sidecar forest and a Godot client forest).
Lesson: each forest references only the shared spec, never a sibling plan tree; grep and replace after authoring.

NEVER reference one forest from another. Each forest should reference only the shared source of truth (the GDD/spec), not sibling plan trees.

## Three failure modes

(a) **Progress contamination** - referencing `plans-glm/02-gossip/` from `plans-godot/` can imply the gossip engine's implementation status carries over, when the Godot plans are all PENDING.

(b) **Coupling** - if `plans-glm/` is archived or restructured, every cross-reference in `plans-godot/` breaks.

(c) **Scope confusion** - an implementer reading `plans-godot/` shouldn't need to open `plans-glm/` to understand their task.

## Prevention

After authoring or auditing a plan forest, grep for sibling forest references:

```
grep -rn "plans-glm\|plans-godot\|plans-<other>" plans-<this>/
```

Replace each with a GDD spec citation (e.g. "Per GDD §04-npc/04-gossip-and-reputation.md" instead of "Per plans-glm/02-gossip/"). The GDD is the shared contract; plan trees are implementation-specific. Worked example: 10 cross-references removed from plans-godot in one session, all replaced with GDD citations.
