# Parallel dispatch: brief discipline + shared-repo git rules

Observed in one session (UpriSys site build, Sept 2026): four parallel delegate_task
waves against one repo. What worked, and what failed.

## Brief degradation

A very long delegate_task context parameter can degrade mid-generation the same way
a large write_file does: duplicated sentences, corrupted JSON in the tasks array, mixed-up
goals. A corrupted dispatch fails schema validation ("Task 0 must be an object, got str")
and dispatches nothing — no half-runs, but a wasted round-trip.

- Brief shape: goal + pinned plan path + task section + exact constraints + ONE verification
  command + ONE commit command. Nothing more.
- A corrupted dispatch is detected at the tool-call layer; re-dispatch clean with a shorter
  brief. Do not try to "fix" the corrupted call — reissue compact.
- The same degradation applies to writing large documents (see writing-plans, "Long-output
  degradation"). If it happened once in a session, keep every remaining long output extra
  compact.

## Shared-repo commit rules for parallel siblings

Every brief for a parallel wave that commits to one repo MUST pin:

1. Commit ONLY the task's own file paths: `git add site/css/style.css` — never `git add -A`
   or `git add .` (siblings sweep each other's staged files).
2. Retry on `.git/index.lock`: sleep 3, retry 3x. Parallel committers collide on the index.
3. Fixed identity via `-c` flags when the repo requires it:
   `git -c user.name="..." -c user.email="..." add <paths> && git -c ... commit -m "..."`.
4. One file per task where possible — file ownership is the collision boundary.

## What runs in-session vs dispatched

Mechanical single-script tasks with a known-good script (asset conversion, fixture
generation) run in-session: cheaper than a dispatch, and the orchestrator verifies the
artifact directly (e.g. composite the keyed logo on the dark background and look at it)
before the code waves land.

## Schema note

delegate_task `tasks` array items MUST be objects: `{"goal": ..., "context": ..., "role": ...}`.
Bare strings error with "Task N must be an object, got str".
