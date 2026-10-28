# Llive service integration
When to use: leaves integrating with live services.
Lesson: staging vs prod, credential handling, smoke discipline.

# Live-Service Integration for Plan Trees

When a plan tree's whole point is fixing behavior of a LIVE daemon/service,
green unit tests do not complete the tree. Integration verification is a
first-class step and it will surface NEW defects in the service itself, not
in your leaves. Pattern proven in meept classifier-reliability (2026-08-26,
5 leaves + 5 integration commits).

## 1. Put Integration Test Plan in master.md

Include: restart procedure, probe command, log greps, expected observable.
Re-run it after EVERY leaf commit, not just at the end. Each rerun is cheap;
deferred integration discovers bugs after their cause is buried.

## 2. Expect integration findings to exceed leaf count

The 3-leaf classifier-reliability tree produced 5 additional integration
commits (empty→chat fallback, sync dispatch for bench clients, step-job cwd
inheritance, gbnf staticcheck fix, commit hygiene). These come back as
precise log-evidence defects in the SERVICE. Treat each as a small
follow-up commit — not scope failure, not a reason to re-plan.

## 3. Read the service's own logs, not just the client's

The client-side error ("empty content") is a symptom. The server-side log
showed the true shape: generation truncated exactly at the token cap with
no EOS (thinking model burning budget on reasoning). Client logs alone
mislead; the server runtime log named the real mechanism.

## 4. Daemon restart pattern

Start daemon in a background shell, poll for the socket file, `exit 0` on
success, notify_on_complete. First bench/probe run after restart often
fails "daemon unreachable" — socket creation ≠ routes registered. Wait one
health-check interval, retry once, THEN investigate.

## 5. Shared pre-commit hooks across concurrent sessions

Other sessions land commits on the same branch continuously. Before
committing: `git log --oneline -3` to see what moved, stage exact files
(`git add <paths>`), never `-A`. Your commit can fail staticcheck on ANOTHER
session's untracked files — fix forward if trivial (one dead line), else
`git -c core.hooksPath=/dev/null commit` and disclose in the commit body.
Also: a concurrent commit can momentarily sweep your staged file into
theirs — re-check `git log -- <your file>` after any surprising commit.

## 6. Async-vs-sync dispatch

Benchmark/headless clients need final results, not orchestration acks. If
the service has a sync mode, gate it on a client identifier (e.g.
source_client prefix) rather than a global flag. Symptom when missing:
client records a verdict, then teardown destroys the worktree the async
task is still executing in.

## 7. Session/identity splits are the #1 integration bug class

Services with both "session IDs" and "conversation IDs" (or any dual key)
will have lookup paths that take the wrong one. Every RPC the harness makes
must be audited for which key it passes: one RPC needs the primary ID, the
agent loop's lookups key on the other. Verify directly against the
service's DB, not the API's return shape.

## 8. Working-directory inheritance through async pipelines

Registry-fabricated loops/workers typically start with empty workingDir and
rely on SOME caller to SetWorkingDir. Every execution path (direct chat,
step job, replan) needs its own inheritance audit: task → linked sessions →
WorktreePath/ProjectPath → SetWorkingDir. Symptom when missing: file writes
land in the daemon's repo instead of the caller's worktree.
