# Cconcurrent shared file race
When to use: sibling leaves reverting each other changes.
Lesson: shared-file race shapes and one-writer-per-region fixes.

# Concurrent Shared-File Race — Sibling Leaves Reverting Your Changes

> When parallel leaves co-own shared files (interfaces, store implementations,
> test mocks), sibling leaves can silently revert your changes back to the old
> signature. Your edits land, pass tests, then a sibling's commit overwrites
> them. The fix cycle is: re-apply, verify, repeat until stable.

## Recognition Signal

You apply a change (e.g., updating a Store interface method signature from
`error` to `(int64, error)`), run tests — they pass. Minutes later, `go vet`
or `go build` fails with the *exact same* error you already fixed:

```
vet: internal/store/sqlite_store_test.go:130:8: assignment mismatch:
  1 variable but s.InsertScreenshot returns 2 values
```

You check the file: your change is gone. The signature reverted to the old
form. You re-apply, pass tests, and it reverts again. This cycle repeats 2-3
times before stabilizing.

## Why This Happens

Multiple parallel leaves are modifying overlapping shared files:

- **Leaf 05 (this leaf):** Changes `Store.InsertScreenshot` signature to
  `(int64, error)`, updates interface + implementation + test.
- **Leaf 04 (WebSocket, concurrent):** Changes `NewRouter` signature,
  `makeEventsHandler` signature, adds `InsertSessions` to store interface —
  and in doing so, re-reads + re-writes `store.go` and `sqlite_store.go` from
  its working copy, which still has the old `InsertScreenshot` signature.
- **Leaf 02/03 (other concurrent leaves):** May also touch store files.

Each sibling's patch is internally consistent with its own view of the file.
The problem is that the siblings don't know about each other's signature
changes. When sibling B rewrites `store.go`, it includes its own new method
(`InsertSessions`) but preserves the old `InsertScreenshot` signature because
that's what B's context had.

## The Recovery Loop

1. **Apply your changes** (interface + implementation + tests).
2. **Run your tests** → pass.
3. **Run `go vet ./...`** → if it fails with your *already-fixed* error,
   a sibling has reverted your change. Re-apply.
4. **Repeat** until `go vet`, `go build`, and `go test` all pass in the same
   terminal invocation with no intervening sibling commits.
5. **Final verification:** Run `go vet`, `go build ./...`, and `go test` in
   a single batched command. If all pass, you're stable.

## Mitigation: Minimize Shared-File Footprint

When you control the leaf design, minimize the number of shared files your
leaf touches:

- **Prefer a new file** for your handler/implementation rather than appending
  to a shared `handlers.go`. (e.g., `screenshot_handler.go` not a section in
  `handlers.go`.)
- **If you must change a shared interface**, make that change atomic: update
  the interface, all implementors, and all test mocks in a single turn.
- **Route mounting** is inherently a shared-file edit (router.go). Accept that
  this one file may need re-application.

## Detection: The Stale-LSP Tell

When you write a file and the LSP reports errors for symbols you *know* exist
(e.g., "undefined: MakeScreenshotHandler" when you just wrote
`screenshot_handler.go`), the LSP has a stale cache. But if `grep` confirms
the symbol exists on disk and `go build` still fails, the issue is that a
sibling has overwritten a *dependency* file, not your file.

Check with:
```bash
grep 'func.*YourMethod' shared_file.go
grep 'YourMethod' interface_file.go
```

If the signatures don't match between interface and implementation, a sibling
has created a divergence.

## Real-World Instance

**Session:** AgentAudit leaf 05 (screenshot handler), 2026-08-04.

The leaf needed to change `Store.InsertScreenshot` from `error` to
`(int64, error)`. Three files needed coordinated changes: `store.go`
(interface), `sqlite_store.go` (implementation), `sqlite_store_test.go` (test).

| Cycle | What happened | Detection |
|-------|--------------|-----------|
| 1 | Applied all 3 changes. Tests passed. | `go test` green |
| 2 | `go vet` failed: interface says `(int64, error)`, impl says `error` | `go vet` caught signature mismatch |
| 3 | Re-applied impl change. `go vet` failed again: test says `err = s.InsertScreenshot()` (1 return value) | Sibling had reverted test file too |
| 4 | Re-applied test change. All green. | `go vet && go build && go test` all pass |

**Root cause:** A parallel WebSocket leaf was modifying `store.go` to add
`InsertSessions`, and each time it re-wrote the file, it included the old
`InsertScreenshot` signature from its context. The WebSocket leaf was also
modifying `router.go` and `handlers_test.go`, which reverted the screenshot
route registration and mock fields.

**Resolution:** After 3 re-application cycles, all parallel leaves finished
and the shared files stabilized. Final `go vet`, `go build ./...`, and
`go test ./internal/api/ ./internal/store/ -v` all passed cleanly (42/42 tests).

## Key Distinction from Sibling-Package-Collision

- **Sibling-package-collision** (references/sibling-package-collision.md):
  Your files compile fine, but the *combined package build* fails because a
  sibling is still in flight. The fix is isolation verification — your work
  is correct, wait for the sibling.

- **Concurrent-shared-file-race** (this document): Siblings are *overwriting
  your already-completed changes*. Your work was correct but gets reverted.
  The fix is re-application until the sibling leaves stop modifying the file.

The two patterns can co-occur: a sibling may be both in-flight (causing build
failures from new symbols) AND reverting your changes (overwriting shared
files). In that case, wait for the sibling to finish, then do a final
re-application + verification pass.
