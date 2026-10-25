# Plan Trees Targeting Live Services

Companion guidance for `hierarchical-planning` / `hierarchical-plan-execution`
when the plan tree's whole purpose is changing how a LIVE daemon/service
behaves (vs. adding self-contained features). Proven on meept
classifier-reliability (2026-08-26): 3 planning leaves → 5 additional
integration commits, all discovered by rerunning against the live service.

## Why these trees are different

Unit tests go green while the service still misbehaves. The defect is in
the interaction between your change and the service's runtime state (log
levels, loaded models, session stores, spawn lifecycle). Integration
verification is not a final checkbox — it is a per-commit feedback loop
that generates follow-up work.

## master.md requirements (beyond the standard template)

Add an **Integration Test Plan** section:
- exact daemon/service restart procedure
- the probe command(s) and expected observable output
- which log files to grep and for what strings
- success criteria phrased as observables ("zero 'empty content' warnings
  in the daemon log for one request"), not as "tests pass"

Rerun it after EVERY leaf commit. Cheap reruns catch regressions while the
causing diff is one commit deep.

## Expect integration findings to exceed leaf count

3 planning leaves produced 5 integration commits in the reference tree.
Each came back as a log-evidence defect in the service itself (truncation
at token caps, dead alias failover, ack-vs-result dispatch, missing cwd
inheritance). Do not treat these as scope failure and do not re-plan;
author each as a small follow-up commit with its own tests where feasible.

## Debug discipline: read the service's own logs

The client-visible error is usually a symptom. In the reference case the
client saw "empty content"; the server runtime log showed generation
truncated exactly at the token cap with no EOS — a thinking model burning
its budget before emitting content. Server logs name the mechanism; client
logs name the symptom. Grep both, and prefer the server's timeline.

## Restart + probe pattern

- Start the service in a background shell; poll for its socket/port; `exit
  0` on first success; notify_on_complete.
- Socket up ≠ routes registered: the first post-restart probe often fails
  with "unreachable". Wait one health-check interval, retry once, then
  investigate.
- Log to a file you control (`nohup ... >> /tmp/svc.log 2>&1`), but check
  whether the service ALSO writes its own structured log — that one is
  usually richer (meept: ~/.meept/meept.log vs /tmp redirect).

## Concurrency: other sessions share the branch

- `git log --oneline -3` before every commit; HEAD moves without you.
- Stage exact paths, never `git add -A`; other sessions' untracked WIP sits
  in the tree and WILL trip shared pre-commit hooks (staticcheck on their
  files fails YOUR commit).
- When the hook finding is not yours: fix forward if trivial, else
  `git -c core.hooksPath=/dev/null commit` and disclose in the body.
- A concurrent commit can sweep your staged file into theirs — after any
  surprising commit, `git log -- <your file>` to confirm ownership.
- Pre-commit hook scripts may themselves be broken by a sibling session
  (bash-3.2 `mapfile` errors). Same bypass, same disclosure.

## Client-contract findings to check on any live-service tree

- **Dual identity keys**: services with both session IDs and conversation
  IDs will have lookup paths that take the wrong one. Audit every RPC the
  harness makes for which key it passes; verify against the service DB.
- **Async-vs-sync dispatch**: benchmark/headless clients need final
  results, not orchestration acks. Gate sync mode on a client identifier,
  not a global flag. Symptom of missing this: the client records a verdict,
  then teardown destroys the worktree the async task still runs in.
- **Working-dir inheritance**: registry-fabricated loops start with empty
  workingDir. Every execution path (direct chat, step job, replan) needs
  task → linked sessions → WorktreePath/ProjectPath → SetWorkingDir.
  Symptom: file writes land in the service's repo instead of the target.
- **Thinking models + token caps**: a reasoning model burns the cap before
  emitting content; truncated generation returns empty. Send
  enable_thinking:false (`chat_template_kwargs`) for classification-class
  calls, and derive caps from the model's declared max_output with a floor.
- **Alias/failover chains are dead unless reported to**: health rotation
  only happens if the failing component calls the resolver's failure hook.
  Check that the component actually has the resolver wired.
