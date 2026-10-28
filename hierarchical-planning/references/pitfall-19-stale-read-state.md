# Pitfall 19 - Orchestrator Patching a Subagent-Edited File (Stale Read-State)

When to use: the orchestrator is about to patch or rewrite a file a subagent just wrote.
Lesson: re-read the whole file in-session before any orchestrator-side edit; patching against a pre-dispatch read can silently mismatch.

After concurrent leaf agents return, the orchestrator often does a small follow-up edit (fixing a stray comment, tightening one line) on a file a leaf just wrote. The patch tool warns: "subagent modified files the parent previously read - re-read before editing." Patching against your OLD read (read_file pagination or a pre-dispatch read) CAN mismatch and silently fail or corrupt.

## Rule

Before any orchestrator-side `patch`/`write_file` on a file a subagent touched, RE-READ THE WHOLE FILE IN-SESSION (full read_file, not offset pagination) so your old/new strings match the current on-disk content.

This is separate from Pitfall 12: Pitfall 12 is about line-number prefixes baked into files; this is about stale parent read-state vs subagent writes.

## Serialization

When multiple leaves touch the same doc (rare but possible for adjacent sections), serialize: review each leaf's output, then apply orchestrator edits only after re-reading the merged result. Single registration sites (one shared file every leaf appends to) are serialization points - see Pitfall 46 in `references/concurrent-wave-execution.md`.
