# Pitfall 55: subagent reports "completed" but files did not land

Real instance: meept quota-reset-resilience leaf 06 subagent (deleg_923f3356,
2026-08-30). Subagent returned status=completed with a summary claiming
`quota_deferral_test.go` was written — file did NOT exist in the working tree.
Similar pattern on leaves 03/05 via deleg_eb5996ef and deleg_4cfc58cd:
"completed" status but zero observable source files.

## Why this is different from pitfall 54

Pitfall 54: subagent DID write files, then the reporting API call 429'd.
Pitfall 55: subagent NEVER wrote files — it may have run in an isolated
sandbox, crashed silently, or its write path pointed elsewhere. The "completed"
status is misleading.

## Decision protocol on any "completed" delegation return

1. `find . -name "*<feature>*" -type f | grep -v '.git\|scratch\|docs/plans'` — verify the DECLARED output files exist.
2. `git diff --stat HEAD` — check if any modifications appear.
3. `go test ./... -run '<Feature>' -count=1` — run the leaf's tests; if they pass, files are likely correct.
4. If files are absent AND tests fail: implement directly from the brief (do NOT re-dispatch — the provider is rate-limited or the subagent environment is broken).
5. If files are absent AND tests pass (already implemented by another path): mark complete, document the ghost completion.

## Why re-dispatching fails

When a subagent hits 429 during execution, the provider remains throttled
for the reset window (~5h). Re-dispatching into the same provider will
repeat the failure. Plan remaining leaves assuming that provider's capacity
is zero until reset.

## Corollary: "completed" is a status, not a guarantee

Always verify filesystem state before accepting a delegation as done.
Subagent reports are not authoritative for file presence.
