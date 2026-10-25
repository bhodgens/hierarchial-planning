# Case study: classifier-reliability tree (2026-08-25)

A small 3-leaf tree authored and executed against meept. Notes on what
generalizes beyond the skill's core templates.

## Tree shape

```
.hermes/plans/classifier-reliability/
  master.md                  # root: verified root cause, contracts, dispatch order
  01-disable-thinking.md     # leaf (~30K ctx)
  02-token-caps.md           # leaf (~25K ctx)
  03-alias-failover.md       # leaf (~35K ctx)
```

Flat tree (no branch dirs) was correct — three independent leaves, no
subsystem big enough to warrant an orchestrator layer.

## What worked

1. **Pre-registered expectations in master.md.** Writing predicted outcomes
   BEFORE execution ("leaf 01 should eliminate >90% of empty-content
   warnings; if empties persist, suspect whitespace-only content") kept
   diagnosis honest when the first rerun still failed.
2. **Root-cause evidence embedded in master.md** with exact log citations
   (token counts matching caps, truncated=0 flags). Leaves could cite it
   without re-deriving.
3. **Serialization rule for overlapping files**: two leaves edited the same
   classifier/analyzer files. Master.md declared "01+02 concurrent, 03
   serialized after" and instructed concurrent agents to keep shared-file
   changes additive. No merge conflicts resulted.

## Pitfalls hit

4. **Pre-commit hooks reject commits over findings in UNRELATED untracked
   files.** A staticcheck error in a file belonging to another session's
   in-flight work blocked the leaf commit. Resolution: fix the trivial
   finding (dead append), include it in the commit with a note, and warn
   the user that a foreign file landed under the commit. Check
   `git status` for untracked files BEFORE dispatching leaves on a shared
   worktree.
5. **Subagents may edit files the parent has read** — re-read before any
   parent-side patch to those paths.
6. **Template compliance checker wants specific section names**
   (`## Dispatch Protocol`, `## Review Checklist`,
   `## Completion Tracking Table`, `## Integration Test Plan`). Run
   `check_template_compliance.py <plans-root>` after authoring; it names
   missing sections exactly.

## Commit policy note

Only orchestrators commit (per skill). With concurrent leaves touching
shared files, stage per-leaf file lists explicitly (`git add <leaf files>`)
— `git add -A` would sweep sibling leaves' partial work into one commit.
