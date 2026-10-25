# Concurrent Leaves Touching Shared Files

> Session: 2026-08-26, meept multiuser-access plan tree (leaves 01/02/03/06
> running concurrently over a shared Go monorepo).
> Companion to: wave-execution-patterns.md (dispatch/review loop) and
> parallel-branch-authoring.md (plan-writing dispatch).

Leaf independence is about LOGIC, not file paths. Two leaves with zero data
dependencies can still collide on shared config schemas, daemon wiring
functions, go.mod, or AGENTS.md. Pre-commit gates run against STAGED files
but observe WORKING-TREE state — so another running leaf's uncommitted edits
to your staged files show up in your gate output.

## 1. Partition file ownership at DISPATCH time

Before dispatching a wave, list every file each leaf MIGHT touch (not just
the files in its spec). Any file claimed by 2+ leaves needs an explicit
ownership rule in BOTH dispatch contexts:

- One **primary owner** gets write access.
- Everyone else gets an explicit prohibition with a fallback:
  "do NOT modify X; report if you need a change and the orchestrator will
  apply it", or "keep edits strictly ADDITIVE within <named region>".

Worked guards from the meept session:

| Conflict surface | Guard wording used |
|---|---|
| config schema struct fields | "Do NOT touch RPCTransportConfig — leaf 06 owns it; you own HTTPTransportConfig + MultiUserConfig only." |
| existing package being extended | "internal/auth exists already (leaf 01 committed) — consume Store/Identity from it, do NOT recreate types. Pre-existing OAuth files inside that package are NOT yours." |
| shared package, disjoint files | "Your PRIMARY targets are the sync payload files under internal/backup/. If you must touch internal/rpc/backup_sync.go, keep edits additive and minimal." |
| dependency-free leaf | Dispatched EARLY alongside the first leaf of the blocker chain instead of waiting for the whole wave. |

Rule of thumb: every dispatch context gets (a) explicit primary targets,
(b) explicit prohibitions with fallback behavior, (c) the current state of
files OTHER leaves may have touched ("re-read before editing — siblings are
running").

## 2. Commit early so later dispatch contexts reference real code

Committing leaf 01 before dispatching 02/03 let their contexts say "READ
internal/auth/store.go first" instead of re-inlining contracts as prose.
Subagents matching real code drift less than agents matching prose. Don't
hold commits for batch integration; commit per leaf immediately after its
review passes.

## 3. Review discipline under overlap

1. **Commit per leaf immediately** after review passes — never batch. A
   staged-but-uncommitted leaf forces later reviews to disentangle hunks.
2. **Stage explicit paths** (`git add <paths>`), never `git add .`. Check
   `git diff --cached --stat` lists only that leaf's files before committing.
3. **Expect foreign hunks in gate output.** Pre-commit analyzers/linters
   report on working-tree state; be able to tell a sibling's unrelated-but-
   correct diagnostics from the leaf you are committing. If two leaves DID
   stage one file: hunk-split (`git add -p` semantics), or review line by
   line and note any foreign-but-correct lines riding along in the commit
   message.
4. **Re-read before orchestrator patches** (Pitfall 19) — doubly true while
   sibling leaves still run.

## What this made possible

Leaves 01 (auth store), 02 (HTTP identity + session ownership), 03 (cluster
pooling over peer sync), 06 (RPC peercred) ran concurrently with overlapping
footprints — config schema, rpc package, daemon wiring — across four
consecutive per-leaf commits with zero cross-leaf merge conflicts. All
partition decisions were made in dispatch text, not negotiated retroactively.

Related session quirks worth carrying:
- macOS unix sockets fail on paths >~104 bytes: socket-path tests need short
  temp dirs, not `t.TempDir()` defaults under deep module trees.
- `gofmt` diffs needed on subagent output nearly every time (server.go,
  schema.go); fold `gofmt -l` into pre-review always.
