# Pitfall 46 - Single Registration Sites Are Serialization Points

When to use: multiple leaves each append a block to ONE shared file (a daemon's components registration site, an init/wiring file).
Lesson: serialize registration leaves, commit each wave before the next, and pin exact-plus-fallback anchors in the brief.

When multiple leaves each append a block to ONE shared file (e.g. an ~8k-line `internal/daemon/components.go`, the only builtin-tool registration site), do NOT parallel-dispatch them even when otherwise independent:

1. Serialize registration leaves; commit each wave before dispatching the next.
2. Each later dispatch context says: "a prior agent just modified this file - re-read the registration region before editing" (Pitfall 19 stale read-state).
3. The leaf brief pins the exact anchor AND a fallback anchor if the first hasn't landed, with a note-the-placement instruction.
4. Concurrent appends to one file are how blocks get lost or land in the wrong scope; the commit cost of serialization is trivial by comparison.

Source: `references/concurrent-wave-execution.md` (Pitfall 46 section); companion rules in `references/live-multi-session-repos.md` Rule 1 and `references/concurrent-shared-file-leaves.md`.

Note: the SKILL.md previously cited "Pitfall 46" as the tests-first-gate "skipping or weakening the test gate" number; that lesson lives in `references/tests-first-gate.md` and is covered by Step 5.5 / Dispatch Protocol step 0.
