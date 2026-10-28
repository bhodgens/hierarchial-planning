# Concurrency Races: Sibling Collisions, Parent Races, Stale Reads

When to use: any dispatch where two or more agents (or the parent and a subagent) write to the same package, file, or repo concurrently.
Lesson: one writer per file; after any sibling-modification warning or concurrent edit, re-read the file before the next patch - stale reads produce corrupted files, false build errors, and silently resurrected bugs.

## Patch tool + sibling subagent = file corruption

When two agents edit the same file concurrently, the patch tool emits a distinct warning: "... was modified by sibling subagent 'sa-X-...' after this agent's last read. Re-read the file before writing."

This warning is NOT advisory. Applying a second patch from stale content matches a shifted region and produces duplicated function bodies, orphaned code blocks, or invalid syntax.

Recovery:
1. Re-read the corrupted file end-to-end (no pagination). Corruption signature: a function body appearing twice with different content, orphaned `return` after a closing brace, a loop reduced to its header line.
2. Replace the entire corrupted function with ONE large patch (multiple small patches re-trigger the pattern on a shifted file).
3. Run the project build immediately; if it fails, re-read again and re-apply against fresh content.

Prevention: assign non-overlapping file sets to siblings touching the same package. Shared files (evaluators, orchestrators) are serialized: complete agent A, verify, then dispatch B.

## Parent agent racing a still-running subagent

The parent editing files while a dispatched subagent is STILL RUNNING interleaves writes in real time. Symptoms: a grep says a symbol is absent, so the parent writes it, then the build fails "method already declared" because the subagent wrote it moments after the grep; files appear or shift between reads; sibling-modification warnings name a subagent that "already finished."

Prevention - one writer per file:
- Do not edit any file a running subagent owns. Wait for return, verify, then fill genuine gaps.
- If concurrency is required, partition strictly: subagent owns {A,B,C}, parent owns {D,E}, zero overlap.
- Never write a file the subagent was also told to create.

Key insight: while a subagent runs, every file in its scope is concurrently mutable; your grep is a snapshot of the past.

## Sibling stale build errors reported as "pre-existing"

Two parallel siblings in one module: the slower one's build may run after the faster sibling committed but before the commit is visible to it. It then reports a build error in a file it did not own and flags it "pre-existing, out of scope."

This is a false signal: the error was real in the window when the build ran, and the sibling's commit fixed it. Detection: the reported error names a file the subagent did not modify, and the final orchestrator-side build passes. Prevention: tell siblings in their briefs that concurrent siblings exist, build errors in files they did not touch are likely transient - note them, do not fix them, do not block.

## Timed-out subagent clobbers a parent hotfix

A timed-out subagent is not necessarily dead - its last tool calls can land after the batch timeout report. Real instance: the parent fixed a bug pattern in a file at T+20min; the timed-out subagent rewrote the same file at T+44min, silently re-introducing the exact bug class.

Rule: after any fix inside a still-running or timed-out subagent's scope, re-grep the file for the fixed pattern when the delegation result arrives. Until a completion message arrives, treat its files as concurrently mutable.

## Compile-fixing concurrent sibling code in the same Go package

Distinct from stub-first (preparing for UPCOMING waves): a concurrently running sibling writes files in YOUR package referencing symbols in YOUR files that do not exist yet. Build fails with `undefined: X` pointing at the sibling's files.

Technique - add the missing symbols to YOUR files; do NOT modify the sibling's code:
1. After writing your types file, build the whole package (`go build ./internal/yourpkg/...`), not just vet on your file.
2. Add the minimal type/field/stub method to your file, matching the sibling's call-site signature exactly (grep the symbol in their files first).
3. Return `ErrNotImplemented` from stub methods so placeholders are obvious.
4. Watch for import-block overwrites: after ANY sibling-modification warning, re-read and verify your imports survived.

Real instance: the parent wrote `types.go` while a sibling wrote `enricher.go` and `generator.go` referencing an undefined `Library` type and `SkillCandidate.SourcePattern` field. Adding a `Library` stub with the expected signature plus the missing field resolved it; a concurrent import-block overwrite required re-adding `context` and `errors`.

## Interface contract signature drift during parallel implementation

When siblings implement code sharing an interface (one writes the Store interface, another the SQLiteStore implementation, a third the consumers), a sibling may change the interface signature to suit itself, breaking all consumers: `*SQLiteStore does not implement Store (wrong type for method X)`.

Fix: revert the implementation to the interface defined in the foundation files. The interface IS the contract; signature changes are negotiated in the orchestrator, never made silently. Prevention: every implementation brief carries "Do NOT modify interface signatures defined in the foundation files. Need a different return type? Add a NEW method."
