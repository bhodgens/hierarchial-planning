# Ppre existing implementation recovery
When to use: an aborted pass already wrote the files.
Lesson: recover instead of redo; verify what exists.

# Pre-existing implementation recovery (aborted pass already on disk)

Pattern: a plan tree is authored, an implement pass starts, gets interrupted, and a later execution session finds some leaf targets ALREADY DONE on disk. Do not re-dispatch subagents over them; audit and claim them.

Proven 2026-08-29, meept harness-literature-tracker (leaf 01 catalog): the aborted session had written a complete 38-technique JSON catalog that passed every leaf-01 check. Also applies to partially-done trees (leaf 02 script missing while leaf 01 catalog valid → dispatch only leaf 02).

## Protocol

1. **Run the leaf's own verification commands in-session** — the exact commands the leaf prescribes, not grep vibes. For a data catalog: `json.load` + existence check per evidence path + `must_contain` byte check. Record outputs as the review record.
2. **Verify the plan's "known risks / known errors" list against disk before trusting it.** In the worked example, two of three flagged risks were themselves stale (FilteredToolRegistry WAS in executor.go:1693 as the catalog claimed; internal/browser existed). Plan-doc risk notes age as fast as tracking tables.
3. **If all checks pass:** review in-session (orchestrator review checklist), commit as that leaf with scoped `git add <exact paths>`, and mark the tracking table COMPLETE with a note: "pre-existing on disk; audited in-session; committed <sha>". Zero subagent dispatches.
4. **If partially done:** dispatch a subagent ONLY for the missing leaf, with the full interface contract inlined (CLI shape, exit codes, output paths, determinism requirements) and the explicit rule set (no commit, no plan-file edits, no read_file-on-source, write-once).
5. **Commit boundaries stay per-concern even when work pre-exists:** data/catalog → script + generated output → wiring (Makefile/AGENTS.md) → plan-tree tracking updates. Four green commits in the worked example (f2490d88, f898fb7e, a13d7bb3, 17f6b7fd).

## Determinism gate for generated outputs

A `--check` freshness gate is only trustworthy if the generator is byte-deterministic: sort categories and row ids explicitly, never rely on map/dict insertion order; write atomically (tempfile + os.replace). Prove it with two consecutive renders + `shasum` match, then a doctor-then-restore negative test (append one char → `--check` exits 1 → regenerate → exits 0). Run these gates yourself in-session after the implementer returns; do not accept the implementer's word.

## Never hand-edit generator output

A generated file with a "do not edit" banner (e.g. harness-techniques.md) gets fixed in the generator or its input catalog, then regenerated. A hand edit silently breaks the --check freshness contract. To undo a bad hand edit, regenerate; to change output, change the source.

## Related

- hierarchical-planning Step 1.5 (Pre-Dispatch Already-Implemented Check) and Pitfall 28 — this reference is the worked version for docs/data leaves.
