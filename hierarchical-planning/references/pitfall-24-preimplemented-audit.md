# Pitfall 24 - Pre-Implemented Trees Need Audit, Not Just Dispatch

When to use: a tree was implemented by a parallel agent or a prior session - not dispatched by you.
Lesson: dispatch a post-implementation review subagent with the full plan checklist before marking COMPLETE; tests passing does not prove spec coverage.

When a tree was implemented externally, do NOT assume it's complete just because the files exist and tests pass.

## The review subagent

Dispatch a post-implementation review subagent that:

(a) reads every source file against the plan's checklist (1-N, each item PASS/FAIL with file:line evidence);

(b) runs `go test ./... -short -race`, `go vet`, `gofmt -l`, and the repo's analyzers;

(c) checks for stray artifacts (fmt.Println, TODO, FIXME, placeholder values);

(d) checks for line-number corruption (Pitfall 12 grep);

(e) returns a structured verdict (APPROVED / NEEDS_FIXES / BLOCKED) with specific issues.

## Why the checklist comparison matters

Worked catch: a gossip engine had 125 passing tests and passed 16/17 checklist items - but an entire spec'd function was missing, so facts never lost confidence or got pruned. The missing function was in the plan spec's review checklist but the sibling agent's leaf scope didn't cover it. The structured checklist comparison surfaced it; test counts did not.

## After the verdict

Fix critical gaps directly (the orchestrator can implement missing functions - faster than re-dispatching for small gaps). Minor contract drifts (extra Config fields, changed function signatures with sensible rationale) can be noted without blocking.
