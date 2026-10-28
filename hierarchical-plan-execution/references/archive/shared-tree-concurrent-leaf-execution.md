# Sshared tree concurrent leaf execution
When to use: concurrent leaves in one shared tree.
Lesson: overlap rules and status coordination.

# Concurrent Leaves in One Shared Tree

When several agents execute leaves of the same plan tree (or adjacent plans)
in one working tree, editing and verification discipline changes.

## Sibling-edit warnings are informational

`write_file`/`patch` may warn: "*<file> was modified by sibling subagent
'<id>' but this agent never read it.*" Your anchored edit already applied —
the warning only means you hold no fresh copy of the file. Do not
reflexively re-read-and-overwrite. Do re-read before making a SECOND edit
to that same file, so your next old_string reflects reality.

## Transient build breaks are usually not yours

With live siblings, a whole-tree build can fail inside files you never
touched: mid-edit undefined symbols, untracked helper files referencing
code that appears seconds later. Protocol:

1. Name the failing package/files. If none are yours, the break is a
   sibling's in-flight state — not your bug.
2. Retry once after a short delay (30–60s); mid-edit breaks often resolve
   on their own.
3. Scope final verification to the packages your leaf actually touched and
   report those results explicitly, noting the unrelated failure.
4. NEVER fix, revert, or finish a sibling's half-written code — that races
   their next write and corrupts their leaf.

## Orchestrator seat: commit isolation under sibling traffic

When you are the orchestrator reviewing a completed leaf while other leaf
agents are still writing in the same tree:

- **Commit ONLY the completed leaf's explicit file paths.** Never `git add .`,
  never `git add <dir>` — a sibling's uncommitted in-flight work can sit in
  the same directory (e.g. its modified `stripe_client.go` next to the
  resolver's new files). Listing exact paths is the only safe form.
- **Re-run the verification yourself before committing.** A subagent's
  "tests green" report is a claim; `go test -race ./pkg/...` in your own
  terminal is evidence. Read the produced files too — at minimum the ones
  defining contracts other leaves compile against.
- **Sibling-modified files in a completion report are not yours to commit.**
  Completion notes may flag files a sibling touched mid-flight ("NOTE:
  subagent modified files the parent previously read"). Check
  `git status`/`git diff --stat` for those paths: if the diff belongs to a
  still-running sibling's leaf, leave it unstaged and review it when THAT
  leaf reports.

## Dependency-gated wave dispatch

Waves don't have to finish as units. Dispatch a downstream leaf the moment
its SPECIFIC upstream dependency is committed and green — not when the whole
wave completes. Example: interface leaf committed → resolver + adapter
(siblings of each other, both depending only on the interface) dispatch
immediately while the unrelated spike and migration leaves keep running.
This keeps the pipeline full; the only serialization is the real dependency
edge, per the plan tree's concurrency table.

## Spike isolation for external-software validation leaves

Leaves that validate third-party software by running it (docker bring-up of
an external repo, vendor sandbox spikes) must clone/build OUTSIDE the repo
(`/tmp/<name>-spike`) — never inside, even untracked. Docker or daemon
unavailability is not a failure: the leaf writes its report with explicit
UNVERIFIED markers for the blocked items plus the reason, and the gate
decision accounts for them. Launch the dependency (e.g. `open -a Docker`)
in the orchestrator session so the spike agent doesn't stall on it.

## Verify artifacts through their real consumer

For generated or config-like artifacts (bundled skills, schemas, templates,
scene files), prove them with the repo's own loader rather than eyeballing:
write a throwaway test that parses the artifact through the production
entry point, assert the exact fields downstream code will read (name, risk
fields, tool lists…), run it, then delete the test. Example: Go repo with a
skill parser → temporary `_test.go` calling the exported Parse function on
the new SKILL.md.

## Leaf hygiene

- A leaf marked **DO NOT COMMIT**: leave everything unstaged, commit
  nothing, and report the modified/untracked paths in the handoff instead.
- When a leaf ships an artifact that other docs referenced by plan position
  ("see leaf 09"), sweep the docs for that phrasing and replace it with the
  concrete shipped path, so documentation never points at plan internals.
