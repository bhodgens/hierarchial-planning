# Pitfall 21 - Inventing Spec Values That Contradict the Source (Paraphrase-Drift)

When to use: translating prose specs into frozen structs, threshold tables, or enums.
Lesson: quote the spec verbatim at every frozen contract; never invent derived values; verify authored contracts against the source with digest subagents.

Translating prose specs into frozen structs/threshold tables invites paraphrase. Worked failures from one forest session: a plan invented a single `Regard int` where the GDD specified 5 float dimensions, and fabricated tier thresholds where the GDD keyed on fact counts. Both survived the structural scan (sections present, values wrong).

## Prevention

(a) Quote the spec verbatim in a `// SPEC (file:line, [STATUS]): <text>` comment at every frozen contract.
(b) Never invent threshold tables/enum members "derived from the narrative" - record the derivation as an OPEN-QUESTION with a documented default.
(c) After authoring, dispatch contract-verification digest subagents (Review Protocol, "Contract Verification Digests") that re-read the source spec and diff it against the frozen contracts.

Full recipe: `references/contract-verification-digests.md`. Companion authoring checklist: `references/authoring-checklist.md`. Related drift class (spec moves AFTER authoring): Pitfall 22.
