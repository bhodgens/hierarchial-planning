# Zero-file "completed" timeouts

`delegate_task` can return **status=completed** with a body like:

```
API call failed after 3 retries: Non-streaming API call timed out after 240s with no response
```

That is **not** a finished leaf. 2026-08-29 meept `plans/acp-agent-runtime` leaf 03: 6 API calls, 829s wall, **zero files**.

## First check

```
git status --porcelain <leaf-paths>
ls the expected new files
```

Empty → implement from the dispatch brief in-session. Do not re-dispatch into the same 240s timeout.

This is distinct from Pitfall 25 (timeout **with** files on disk). Same first check; different recovery.

## Sibling stub types

If a parallel leaf in the **same Go package** stubbed types the failed leaf owns (leaf 04 put `Session`/`Start` in `manager.go` because `session.go` was missing), strip those stubs in the same pass or the package duplicate-defs when the real files land.

## Briefs must be executable

Write dispatch contexts complete enough that the orchestrator can implement the leaf without the subagent: frozen signatures, file ownership, test names, fake-agent modes. That is what made the in-session fill of leaf 03 possible.
