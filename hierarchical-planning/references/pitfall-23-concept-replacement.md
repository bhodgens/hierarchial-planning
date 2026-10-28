# Pitfall 23 - Cross-Corpus Concept Replacement (Perspective-Pivot Class)

When to use: the user makes a sweeping design change touching a concept across the entire corpus ("third-person now", "rename X to Y everywhere", "cut feature Z").
Lesson: naive find-and-replace misses semantic hits, over-corrects legitimate ones, and skips technical consequences; use parallel digests, then one verified batch.

A naive find-and-replace produces three failure modes:

(a) It changes the literal phrase but misses semantic equivalents ("FPS" as genre-shorthand, "through the eyes" as idiom, "viewmodel" as technical assumption).

(b) It over-corrects, changing references that should stay (a competitor's perspective in a comparison table, narrative-grammatical "first person" voice).

(c) It misses the technical consequences (FOV values, camera rig component tree, LOD chain scope, interaction-trace origin).

## Pattern that works

Dispatch 2 parallel read-only digest subagents - one scanning the GDD, one scanning the plans - each returning a structured report grouping hits by category: hard statements / gameplay assumptions / competitive comparisons / technical specs / out-of-scope false positives. Digest in-session, then apply all amendments in one `execute_code` batch (N find-and-replace edits with per-edit match verification). Verify post-application with a grep that distinguishes intentionally-kept references (e.g. genre labels) from stale ones.

This is the same parallel-digest-then-batch-apply shape as the contract-verification digests, but the "contract" is a semantic concept rather than a struct field. Full recipe and the first-person-to-third-person worked example: `references/cross-corpus-concept-replacement.md`.
