# Live multi-session repos — shared-file serialization and sibling breakage


When to use: trees running while sibling sessions commit to the same repo.
Lesson: serialize shared-file leaves; treat sibling breakage as read-only; verify claims yourself.
Observed 2026-09-05 (meept, dependency-visibility tree): while the tree
ran, a sibling session committed three times to main, including one
commit that was mid-TDD (test file referencing a not-yet-written symbol
from their own next leaf), which broke the shared package build.

## Rule 1: Serialize leaves that touch the same file

Two leaves editing one file (e.g. a daemon components.go registration
block) run SEQUENTIALLY even when the dependency graph marks them
parallel. Concurrent edits to one file are how integration bugs happen;
the wall-clock win is not worth the merge. Note the serialization
explicitly in the master's Child Index, e.g.:

    | 03-registration.md | ... | Wave 3 (serialized after 02/02: both edit components.go) |

The dependency graph says what MUST be ordered; the file-touch map says
what SHOULD be. Re-read the shared file region right before each
dispatch — the prior leaf's block may have shifted line numbers.

## Rule 2: Sibling breakage is read-only background

If the package build breaks from an UNRELATED in-flight leaf (test file
referencing a not-yet-written symbol from another plan tree), do not fix
or touch their files. Verify your own scope in isolation:

- `go build ./<your-packages>/...`
- `go vet ./<your-packages>/...`
- targeted `go test -run <YourPatterns>` filters

Defer the full-package green to integration; it resolves when the
sibling lands their implementation half (observed: package went green
~15 min later with no action from this session).

## Rule 3: Independent verification of subagent claims

Async leaf returns are self-reports. Before marking REVIEWED:

- Re-run the tests yourself (do not accept "all green" verbatim).
- Verify API-drift claims against `go doc <pkg>` — an agent correcting
  the brief is exactly where you must not take its word (observed: pdf
  NewReader(ReaderAt) drift claim was correct, confirmed in one call).
- License claims (MIT/BSD/AGPL) are consent-gated for this user: read
  the LICENSE file in GOMODCACHE yourself before allowing the dep.
- Registration/wiring blocks: read the actual file region, not the diff
  summary.

## Rule 4: Commit granularity on shared repos

Commit each reviewed leaf (or tight leaf group) immediately after
in-session review, not in one giant integration commit — a sibling
session is committing concurrently, and small commits rebase cleanly.
Never `git add .`; stage the leaf's exact file list so sibling churn in
the working tree stays out of your commit.
