# Lleaf collab dispatch protocol
When to use: two agents collaborating on one leaf.
Lesson: collaboration protocol and ownership split.

# Leaf Collaborative Dispatch Protocol

> **Status:** companion file. The refined dispatch-context recipe
> (fresh-state overrides, escalation valves, wave-3 client parity last,
> follow-through-commit budget, dangling-merge-stash recovery details)
> now lives in `references/leaf-collision-dispatch-protocol.md` — read
> both. This file keeps the per-leaf review checklist and the gate-trip
> catalog; the newer one owns what goes into each dispatch context.

Proven end-to-end on the meept multiuser tree (2026-08-26): 6 leaves,
4 dispatched concurrently in two waves, all landed via per-leaf
orchestrator commits through an aggressive pre-commit gate. The full
recipe for the "orchestrator dispatches leaves, fixes gate trips, commits
per leaf" loop.

## Wave structure that worked

- Dependencies: leaf 01 (foundation package) gated 02/03/04/05; leaf 06 was
  dependency-free → dispatched IMMEDIATELY alongside 01 rather than waiting.
  State this exception explicitly in master.md's child index ("may dispatch
  before 01").
- Dispatch budget: keep ≤2 implementation leaves + 1 running from a prior
  wave concurrently. Each subagent runs 16–46 min wall-clock; reviews of
  completed leaves fill the wait.

## File-collision guards (put in EVERY dispatch context when siblings run)

When multiple leaves run at once on one checkout, each dispatch context must
carry: (a) which packages are YOURS, (b) which shared files (schema.go,
daemon.go) another leaf is touching and what to do instead ("do NOT touch;
report if you need it"), (c) for leaf agents writing into a package a
committed sibling owns — read the sibling's committed files first, don't
recreate types. This prevented every cross-leaf merge conflict in the tree.

Also warn about PRE-EXISTING files sharing the new package name — e.g.
meept's internal/auth already contained OAuth files (anthropic.go,
pkce.go); an unwary leaf would clobber or misread them.

## Per-leaf review checklist (orchestrator, in-session)

1. Verify claim vs disk: `git status --short <leaf-paths>`, count files,
   `go build ./...`.
2. Re-run the leaf's test suite yourself (`-race`) — never trust a summary.
3. Contract diff: signatures vs master.md frozen contract.
4. gofmt -l on touched files (subagents miss it ~30% of the time).
5. Analyzers the repo ships (mutexio/predid/selflock per repo convention).
6. Read the diff for stray artifacts, TODOs, debug prints, unused exports.

## Gate-tripping patterns and their real fixes

Full catalog with the shared-tree variants (staged-diff contamination,
worktree-scoped staticcheck) now lives in
`references/leaf-collision-dispatch-protocol.md`. Core fixes:

Pre-commit hooks with error-handling linters flag newly-added `_ = expr()`
discards. Subagent code produces these constantly. Do NOT fight with
comments (`_ = encErr // reason` still blocks). Fixes that passed:

- Best-effort JSON error bodies in HTTP middleware → extract
  `writeAuthError(w, status, kind, msg)` helper that checks the encoder
  error and `slog.Debug`s failure.
- Deliberately non-fatal side-calls ("exchange users, never fail the pull")
  → `if err := call(); err != nil { slog.Warn(...) }` at the call site.
- U1000 on ANOTHER session's committed-but-unreferenced symbols → gates
  scan the WORKTREE; restoring the missing callers to the worktree (see
  recovery section) unblocks without deleting their code.

## Committing leaves without sweeping sibling work

Shared-file contamination class: daemon.go carried BOTH a multiuser wiring
hunk and a sibling session's drain-timeout work (with its own gate-flagging
`_ = p.Signal(syscall.SIGTERM)`).

Recipe (worked twice):
1. Classify hunks: build a filtered patch containing ONLY your hunks
   (header + wanted hunks verbatim), `git apply --cached <filtered.patch>`.
   Watch for an UNWANTED hunk riding along inside your filtered patch —
   verify `git diff --cached | grep SIGTERM`-style marker greps BEFORE
   committing, not after the gate blocks.
2. If you temporarily stash a mixed file to rebuild its index entry:
   content-addressed restoration works even after stash drop — stashes
   survive as dangling commits (`git diff <dropped-sha>^1 <dropped-sha> --
   <path>` produces a re-appliable patch; `git apply --3way`). Note the SHA
   printed when you drop. Gotcha: `git show <stash-sha>` emits combined
   `diff --cc` format that git apply REJECTS — always use the two-dot
   `git diff <sha>^1 <sha>` form.
3. After ANY staging manipulation, re-run the gate fresh — evicting a file
   changes what scans see; earlier red/green is void.
4. `git restore --staged <path>` evicts foreign index entries without
   touching the working tree — the safe default when a foreign staged hunk
   blocks the hook.

## Sentinel-error + optional-wiring patterns that passed review

- Store.Validate wrapping sentinel errors (`fmt.Errorf("...: %w",
  ErrExpiredKey)`) lets middleware choose status/message via errors.Is —
  no string matching.
- "Banned public default keys refused at startup": constant-time compare
  configured keys against a banned list; constructor returns nil server;
  daemon turns nil into a fatal startup error with a remediation hint.
  Regression-test BOTH reject and legitimate-still-passes paths.
- Nullable owner column + nil-viewer-means-unfiltered keeps single-user
  mode byte-identical while enabling scoping later.

## Wall-clock reality

- Leaf durations observed: 17–46 min (1011–2764 s), api_calls 42–140.
- Async batch notifications arrive as their own messages; do not sleep-poll.
- A "completed" notification ≠ green tree: always build+test before commit.
