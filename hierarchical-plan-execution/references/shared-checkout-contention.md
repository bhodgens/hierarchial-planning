# Sshared checkout contention
When to use: subagent file loss in shared checkouts.
Lesson: contention mechanics and prevention.

# Shared-Checkout Subagent File Loss (meept-proven)

When several Hermes sessions work the same repo checkout concurrently, subagent
work is not safe between "written" and "reviewed". Proven failure modes:

1. **Sweep commits** — a sibling session's `git add -A`-style commit captures
   your staged/untracked leaf files under its unrelated message.
2. **Restore deletion** — sibling `git restore`/`checkout` cycles delete your
   uncommitted files from disk outright (500+ line files, gone).
3. **Stash collisions** — sibling stash/pop captures or drops your in-flight edits.
4. **Broken-WIP lockout** — sibling's half-written file fails `go build`/vet
   repo-wide, blocking YOUR pre-commit hook on clean files.
5. **Dead subagents** — a subagent dies mid-task; its untracked WIP sits
   broken and blocks everyone else's builds.

## Rules

- **Commit each reviewed leaf IMMEDIATELY after review.** Verified-but-
  uncommitted work does not survive. Do not batch commits across leaves.
- **Re-check `git diff --cached --name-only` immediately before every
  commit.** Siblings stage into the shared index; your commit silently
  includes their files. Unstage non-leaf files with
  `git restore --staged <file>`.
- **Read the full per-file diff BEFORE staging (2026-08-26).** On a heavily
  contested file, `git diff <file>` can show FOREIGN hunks — sibling
  sessions' unrelated in-flight features — alongside yours. Staging the
  whole file commits their half-done work under your message. Decision path:
  (1) if the foreign work looks complete, let it ride and SAY SO in the
  commit body ("also lands sibling-session drain-timeout hunks in daemon.go");
  (2) if it looks half-done, coordinate/wait or unstage the whole file and
  commit your other files first; (3) post-commit, verify what actually went
  in with `git show <sha> -- <file>`. The pre-commit hook output listing
  "11 files changed" when you staged 6 is the tripwire.
- **staticcheck/vet hooks run repo-wide**, so a sibling's broken WIP blocks
  your commit of clean files. Either wait for them to stabilize (usually
  minutes) or fix trivial lint errors directly and note the fix in the
  commit message.
- **Re-read any shared file immediately before patching** — diffs go stale
  within minutes when siblings are active. Use targeted patches, never
  full-file rewrites, on shared files.
- **Never `git stash` in a shared checkout** — it captures siblings'
  in-flight edits and creates cross-session recovery nightmares.

## Mid-session HEAD detachment (strategist-usa, 2026-08-26)

New failure mode: a sibling session CHECKS OUT a different commit while you
are mid-leaf, silently re-pointing HEAD to detached-at-an-old-SHA. Your
working tree loses files that WERE committed moments ago (the sibling moved
the whole repo backwards), your in-flight edits now fail with
`undefined: X` for types that exist in git history, and nothing on disk or
in `git status` looks wrong at a glance.

Recovery WITHOUT touching anyone's state (do NOT `git checkout` back — you'd
detach the sibling the same way it detached you):

1. Confirm: `git reflog -12` shows `HEAD@{0}: checkout: moving from <branch>
   to <old-sha>` and your dependency's commit sitting right below in @{1..3}.
2. Diff reachability: `git diff --stat <old-detached-sha> <your-dep-commit>`
   scoped to your leaf's paths — often only the dependency files differ,
   so restoring them is provably safe.
3. Restore read-only from objects:
   `git show <dep-commit>:path/to/file.go > path/to/file.go` per file. This
   recreates them as UNTRACKED in your tree; commits/branches/index stay
   untouched for the sibling.
4. Sanity-check: `git status` shows only your (restored + new) files as
   untracked/modified and `git diff --cached --name-only` is empty.
5. Resume building your leaf atop the restored dependency as untracked
   files; if the leaf then commits, add BOTH the restored dep files and note
   the recovery in the commit message so reviewers see why an already-
   committed file reappears.

Prevention: before starting a leaf, record `git rev-parse HEAD` somewhere;
if compile errors reference symbols that grep says don't exist on disk but
DO exist in some commit, check `git log --oneline -3` FIRST — "everything
vanished" is almost always HEAD moving, not files being deleted.

## Dead-subagent recovery

- Distinguish active vs abandoned WIP by file mtime + running processes:

- Distinguish active vs abandoned WIP by file mtime + running processes:
  untouched >1h with no agent process = abandoned; safe to repair in-session.
- Untracked-but-broken WIP from a dead agent that blocks the build can be
  repaired in-session if small (missing fields/methods), or quarantined by
  moving it out of the build path.
- Files deleted before commit may be recoverable via
  `git ls-files --stage` + `git cat-file <blob>` if they were ever staged,
  or reconstructed from the committed `_test.go` contract — tests ARE the
  spec when the implementation is lost.

## Dispatch discipline for shared checkouts

- Partition leaves by disjoint file sets; give every subagent an explicit
  "touch ONLY these files" list and name the forbidden sibling-owned files.
- Warn every dispatch: "shared files are edited by other sessions
  concurrently — re-read right before patching; targeted patches only."
- Keep subagent scope SMALL. A 25-minute subagent is 25 minutes of exposure;
  several small ones reduce blast radius per loss.
- Never leave multiple leaves' worth of reviewed-but-uncommitted changes
  accumulated in one working tree.

## Parallel leaves over ONE shared file (same-tree, 2026-08-26 tree 32)

Distinct from cross-session contention: parallel leaves of the SAME tree all
wiring into one resolver.go/simulation.go. Failure modes observed:

1. **Cross-leaf transient test failures are not yours.** Leaf 01's suite
   failed on leaf 03's half-written file mid-flight; both green after both
   landed. Instruct every leaf: "run YOUR named tests; report sibling
   failures as out-of-scope." Parent re-runs the full `-short -race` suite
   only before commit.
2. **Commit per-leaf explicitly; `git add -p` on shared files drags sibling
   hunks into your commit** (leaf 03's wire Flags field sits beside leaf 01's
   spouse guard in the same struct). Commit NEW package files cleanly per
   leaf; let shared-file edits ride with the LAST leaf to land, message
   naming both leaves.
3. **Sequence later leaves' insertion points in the brief** ("insert BEFORE
   <sibling leaf>'s call site") so concurrent edits compose instead of
   conflicting.
4. **A failed/no-summary subagent may have landed complete files.** Before
   re-dispatching: check `git status` for its untracked files, run its named
   suite yourself, fix small compile errors directly (getter-name collision,
   parse error), then commit — saved a full re-dispatch twice in one tree.
5. **mutexio-style gates apply to TESTS:** snapshot state under the lock into
   locals, release, then assert — analyzer gates don't exempt test code.

## Hermetic fixtures mask runtime wiring (parent-review lesson)

Hermetic tests stage doubles at `/root/<Name>` while production resolves via a
different path (manager children, lazy first-frame wiring). Two compounding
cases in one session: (a) tests passed while the real New Game flow no-op'd —
the production resolver looked at a path the fixture didn't use; (b) lazy
CONNECT_ONE_SHOT wiring wasn't up when the test body ran. Countermeasures:
keep ONE live-chain integration test through the REAL boot path per migrated
system; insert an await-process_frame before driving lazy-wired flows; and
diagnose user reports via runtime-log ENTRY-vs-SUCCESS lines before touching
code (entry logged + success absent = the null-check between them is the bug).
