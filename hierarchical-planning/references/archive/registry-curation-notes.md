# Pitfall 46 (tests-first gate variant) and the two registry checklists

When to use: writing the SKILL.md pitfall registry lines for Pitfall 12, Pitfall 13, and the Step 5.5 test gate.
Lesson: the two longest pitfalls keep their checklists inline when they fit the 500-char budget; the tests-first-gate "Pitfall 46" citation maps to the recipe file.

## Registry-line budget notes (for the curator)

- Pitfall 12 (line-number corruption): the three-part prevention (inline snippets / search_files or cat / write-once) fits a 500-char entry with the corruption-check grep compressed to its pattern. The worked post-run verification command and the docs-tree glob extension live in `references/pitfall-12-line-number-corruption.md`.
- Pitfall 13 (rate limits): the TRIGGER/ACTION line covers both phases (parent-side dispatch 429 - retry individually; subagent-side 429 - rich-context retry, narrow scope, then direct fallback). The three recovery strategies are enumerated in `references/pitfall-13-rate-limits.md`.
- The historical "Pitfall 46" citation on the tests-first gate (Step 5.5 / Dispatch Protocol step 0) does not collide with the registry: the skipping-the-test-gate lesson is the final section of `references/tests-first-gate.md`, and the single-registration-site "Pitfall 46" lives in `references/concurrent-wave-execution.md` (mirrored in `references/pitfall-46-registration-serialization.md`).

## Pitfall 13 sub-letters

The registry keeps one line for Pitfall 13; the sub-strategies are cited as 13a (rich-context retry), 13b (narrow scope), 13c (direct fallback) - matching the historical cross-references "Pitfall 13c" in Pitfall 4's exception text.
