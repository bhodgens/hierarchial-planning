# Leaf Close-Out Verification Recipes

Orchestrator-side checks that turn a leaf's green report into verified
committed state. Each recipe is independent of any specific tree.

## 1. New user-facing surface: binary smoke test from the committed state

A leaf can commit the implementation file while the one-line REGISTRATION
(`rootCmd.AddCommand(newXCmd())`, a route/subscription list append, a
handler `RegisterHandler` call) survives only as an unstaged working-tree
change — typically a sibling's. Package tests stay green because they call
constructors directly and never exercise the registration; HEAD ships a
dead file and the CLI fails "unknown command".

- Build from the committed tree and invoke the entrypoint:
  `go build -o /tmp/x ./cmd/<cli> && /tmp/x <newcmd> --help`.
- On failure: `git diff <registration file>` — if the missing line is a
  clean one-line fold with no entangled sibling hunk, commit it; verify
  with the binary smoke again.
- Prevention in the leaf contract: surface leaves MUST name the
  registration file in their file list, and their evidence must include a
  binary-level invocation, not only unit tests.

## 2. "Is this documented?" = per-surface grep audit, not assertion

`make docs-generate` / `docs-check` cover only generated dirs. HANDWRITTEN
reference pages (CLI quick-reference tables, HTTP route tables, RPC method
docs) silently miss new commands/routes/methods even when the workflow doc
fully describes the feature. For each added surface, grep its exact name
(command verb, route path, RPC method string) across `docs/reference/`;
every miss is fixed in the same session before the tree closes. Quote error
strings/tokens into docs only after grepping them from source — never from
the leaf report.

## 3. Staged-content hook: fix -> re-add -> rerun the hook, not the commit

Staged-diff gates (ignored-errors, gofmt, setters, manifest) evaluate the
STAGED content. Editing the file does not clear the block until `git add`
re-stages it. Loop: fix, re-stage, run the hook script directly
(`.githooks/pre-commit-<name>`) and attempt the commit only at 0 blocking.
Locate real blockers by grepping hook output for the blocking glyph —
informational notices bury the summary line.

## 4. Leaf-scope creep: extra files beyond the leaf's list

A leaf may land a real defect fix outside its stated scope (e.g. a
head-of-line-blocking fix in a transport it consumed during its own e2e).
Do not revert it and do not fold it silently into the leaf's commit: read
the full diff, verify locking/race correctness yourself (`go test -race`
the package), and commit it as its own concern with its own message. A
missing registration line is as dangerous as an unreviewed extra hunk.

## 5. Patch-tool corruption of Go escape sequences

Fuzzy patch matching can convert `\t`/`\n` escapes inside Go string
literals into real tab/newline bytes ("string literal not terminated").
After any edit touching such literals, verify with build + `gofmt -l` +
`grep -c '\\\t' <file>`. If corrupted: repair by rewriting the whole
function through a write_file-authored Python script that constructs the
replacement from explicit `chr(9)`/`chr(92)` — never regex-replace into
backslash-bearing Go strings (the replacement string re-interprets `\t`).
Prefer editing Go format strings by whole-block write, not fuzzy patch.
