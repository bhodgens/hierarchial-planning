# Late Subagent Report Protocol

Seen 2026-08-29 (meept 20260829-harness-eval tree, leaves 05/07/12).

## The shape

A leaf subagent can look dead and still be alive:

- **First-call 429, zero files** — status "completed", summary is just
  "API call failed after 3 retries: HTTP 429". `git status` on its paths
  is clean. Per the rate-limit exception, the orchestrator implements
  the leaf in-session from its own dispatch brief.
- **Silent overrun** — no report for 30+ minutes while the orchestrator
  implements, fixes gate trips, and commits the same leaf.

Then the LATE report arrives (this session: 31 min after dispatch), and
its claims diverge from what is now in HEAD. Example: the report said
"checkAutoTrain kept as a private no-op anchor"; the U1000 gate had
already forced its deletion during the commit, replaced by a NOTE
comment.

## Protocol

1. **Do NOT re-commit or re-dispatch.** The committed, gate-passing
   state wins. The late report is provenance, not instruction.
2. **Diff claims vs HEAD:** grep the disputed symbols
   (`grep -rn 'checkAutoTrain' internal/shadow/`), `git log -1 --stat`
   for the leaf's commit, `git status --porcelain` to confirm nothing
   half-applied is lying around.
3. **Re-verify green:** scoped `-race` test run on the package.
4. **Record the divergence** in the tracking-table row's Review Notes
   ("late report reconciled; HEAD diverges at <symbol> — gate-forced").
5. If the late report reveals a REAL defect in the committed work (not
   just divergence), open a fix cycle per the normal review loop — do
   not silently accept either version.

## What made the outage a non-event

The 429'd leaves (05, 12) were implemented in-session in ~30–60 min
each because the dispatch briefs were written at execute-quality:
exact struct definitions, function signatures, test case lists, file
scopes. "The brief is the implementation" — if you could hand the
brief to yourself and code from it, a provider outage only changes WHO
types the code.

## Related hazards in the same window

- **Staged-index sweep risk grows with delay.** Between `git add` and
  `git commit`, a sibling can stage into the shared index; a sibling's
  commit can also carry YOUR staged files (leaf 09's plan tree landed
  inside the sibling's 63be84ce). Stage → verify
  (`git diff --cached --name-only`) → commit in ONE terminal turn.
- **Sibling staged files block your commit.** The pre-commit gates
  scan the shared index/worktree: a sibling's half-landed package
  blocks the build gates and their `_ = x` sites trip the errors gate
  even when your staged set is clean. `git restore --staged <their
  files>` for the index, but their untracked broken files still break
  the worktree compile — you cannot fix files you don't own; wait or
  report.
- **U1000 gate ignores `//nolint:U1000`.** When a deliberately-kept
  no-op anchor gets flagged, delete the function and carry the
  contract in a NOTE comment instead.
- **mutexio nolint placement.** `//nolint:mutexio` must sit ON the
  flagged call line, not above it; and the cleaner fix is structural
  (drop the Go mutex, use a SQLite transaction for the close+insert
  pair — single-writer mode serializes for you).
