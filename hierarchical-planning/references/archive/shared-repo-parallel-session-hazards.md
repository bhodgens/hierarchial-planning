# Shared-Repo Parallel Session Hazards — meept multiuser execution (2026-08-26)


When to use: five leaves executing while other sessions commit to the same repo.
Lesson: hazard catalog: staged-work sweeps, hook failures, foreign hunks (backs pitfalls 44-46).
> Worked example backing SKILL.md pitfalls 44–46. Five plan leaves executed
> concurrently while OTHER sessions (loop-economics, containment,
> classifier-reliability) committed to the same repo and working tree.

## Hazard 1: Sibling commits sweep your staged work

A sibling session's plain `git add <files>` + `git commit` will happily
include YOUR staged-but-uncommitted entries if their staging pass touches
the index broadly, and their `git reset` will silently unstage yours.
Observed twice in one day:

- Sibling commit `10a0b89a` swept in 10 lines of orchestrator wiring
  (components.go multiuser hunks) under its own message.
- A sibling `git reset` unstaged a fully-prepared leaf commit; the next
  `git add` from either side then interleaves.

**Protocol that worked:**

1. Before every commit: `git diff --cached --stat` — confirm staged set ==
   exactly the leaf's paths. Reset foreign entries (`git restore --staged`).
2. When one file carries two sessions' changes (daemon.go carrying both
   multiuser wiring AND a sibling's drain-timeout work): extract only your
   hunks into a patch file and `git apply --cached`. Never whole-file `git add`.
3. After any stash/reset dance around shared files: verify content survived
   (`grep` for the symbols you expect), and treat a dropped stash as
   recoverable — `git stash apply <sha>` / dangling-commit recovery works
   until the next working-tree churn.
4. Commit messages should note when foreign hunks were deliberately excluded,
   so the sibling session knows its work is still uncommitted.

**Better convention to propose:** each session commits only paths it names
explicitly; never `git add .`; never bare `git reset` without pathspec.

## Hazard 2: The pre-commit gate scans added-lines of STAGED files but lint
tools scan the WORKTREE

The gate reported "unused function" for a helper whose CALLERS lived in an
unstaged sibling hunk. Root cause split: gate checks staged diff; staticcheck
sees whole package on disk. Resolution order that worked:
(a) confirm whether the flagged symbol's callers are part of another
session's pending work — if yes, do NOT delete anything; (b) get the caller
hunks back onto disk (restore from stash/dangling commit) so the package is
self-consistent; (c) commit only your hunks via cached-patch staging.

Also: hooks are bash scripts using bash-4 features (`mapfile`,
`declare -A`). macOS `/bin/bash` is 3.2 — when the hook shebang resolves
there it dies with "mapfile: command not found". Permanent fix applied:
repoint hook shebangs to Homebrew bash (`#!/opt/homebrew/bin/bash`).
If a repo you touch shows flaky "command not found" hook failures, check the
shebang before suspecting the toolchain.

## Hazard 3: Nil-injection seams survive all unit tests

Leaf 03 shipped `NewUsersSync(cfg, nil /* store wired later */, ...)`, leaf
02 built its own store instance instead of sharing one, nothing ever called
`RegisterHandler(usersSync)` or `SetUsersSync(...)`. Every package test
passed. Three dead wires in the production daemon, found only by writing the
cross-leaf integration test.

Detection rules for branch review:
- Grep every constructor argument that is `nil // wired by leaf NN` and every
  exported `Set*/Register*` the tree introduced; each needs a LIVE call site
  in daemon/startup code before the branch is COMPLETE.
- The branch-closing integration test must wire two REAL instances over the
  REAL channel (real stores + real gossip engine publish/dispatch here), not
  mock the code under test. Mocks reproduce the same dead-wire blindness.

Worked test: `tests/integration/multiuser_users_sync_test.go` — two stores +
two pools publishing through real engines onto the shared bus topic,
replayed via OnEvent; scenarios cover cross-node key validation, expiry
travel, node-departure eviction, local-authority protection, disabled no-op;
repeatability `-race -count=10` as `make test-multiuser`.

Writing that integration test immediately surfaced the three dead wires plus
one more setter never called — cheaper than any amount of unit review.

## Gate-trip quick fixes (Go)

| Blocked pattern | Smallest legal fix |
|---|---|
| `_ = json.NewEncoder(w).Encode(x)` | extract checked helper: `if encErr := ...; encErr != nil { slog.Debug(...) }` |
| `_ = f()` where failure must not abort | `if err := f(); err != nil { slog.Warn("context", "error", err) }` |
| `_ = p.Signal(...)` inside another session's staged work | unstage that file; never delete sibling code to pass a gate |
| `fmt.Errorf` without `%w` (informational) | fine to leave; only fix if gate blocks |
