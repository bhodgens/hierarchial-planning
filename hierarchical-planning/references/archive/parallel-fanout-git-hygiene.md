# Parallel Fan-Out Git Hygiene + Live-Deployment Verification


When to use: parallel implementation subagents in ONE shared repo/working tree.
Lesson: shared git index is the #1 failure mode; live-deployment verification patterns.
Patterns from executing a plan forest with multiple parallel implementation
subagents in ONE shared repo/working tree (meept multiuser session,
2026-08-26/28: 6 leaves + security fixes + live 3-node cluster verification,
7 production wiring bugs found). Read alongside wave-execution-patterns.md.

---

## 1. The shared git index is the #1 operational failure mode

Multiple sibling sessions and subagents share one repo, one index, one
working tree. Six distinct failure shapes were hit in one session:

| Shape | What happened |
|-------|---------------|
| Swept staging | Sibling ran `git add <their files>`; your earlier `git add` was silently included in THEIR commit (or wiped by their `git reset`) |
| Foreign files in your staged set | Pre-commit gate scans staged files only; sibling's half-done work in the index fails YOUR commit with errors in code you never touched |
| Shared-file hunks | daemon.go carried your wiring fix AND a sibling's drain-timeout work; committing the file commits both |
| Sibling commit sweeps your hunks | Their commit message, your code — content fine, attribution mixed |
| Stash dance hazards | `git stash pop` during sibling activity reverted their newer work; recover via the dangling stash commit (`git fsck` / `git show <sha>`) |
| Patch-tool stale read-state | "file was modified by sibling subagent" — your old_string no longer matches disk |

### Rules that held up

1. **Stage only explicitly-named paths. Never `git add .` / `-A` in a
   shared tree.** After staging, `git diff --cached --stat` must match your
   leaf's file list exactly. Anything extra: `git restore --staged <path>`.
2. **Foreign code in the index → unstage, don't fix.** Their WIP failing
   the gate is not your bug to fix mid-leaf.
3. **Commit per leaf with explicit paths; verify `git diff --cached --stat`
   immediately before `git commit`.**
4. **Shared files (daemon.go, schema.go, components.go): surgical staging.**
   Extract only your hunks: `git diff <file> > full.patch`, filter to your
   hunks (python line-split on `@@`), `git apply --cached yours.patch`.
   Leave sibling hunks unstaged for their owner. If the gate then fails on
   THEIR unstaged lines, re-run after they commit or coordinate.
5. **Re-read every file before patching if any subagent touched it** — the
   patch tool warns; heed it the first time.
6. **If a sibling's commit swept your hunks:** verify content correctness,
   note the attribution mix in your report, move on. Do not rewrite history.
7. **Pre-commit gates run against the WORKING TREE, not the index.** If the
   gate fails on lines you didn't stage (e.g. staticcheck U1000 on a
   sibling's half-finished file), the fix is sequencing with the sibling,
   not code changes.

## 2. Live deployment catches wiring bugs every test tier misses

Seven production bugs in one feature (multiuser cluster pooling) passed:
unit tests, `-race`, integration tests, compliance scans, staticcheck.
All seven were the same class: **code exists, is correct, is tested — but
is never invoked in the running system.**

| Bug class | Live symptom |
|-----------|-------------|
| Handler built, `RegisterHandler` never called | Inbound events silently dropped |
| Setter (`SetUsersSync`) exists, no caller | Config never reaches the component |
| Component stored in struct, field never assigned | `nil` at use site, silent no-op branch |
| Provider/option (`WithMembersProvider`) never passed | Transport starts local-only |
| Loop starter (`GitSync.Start`) never wired | Background loop never runs |
| Push without prior fetch/merge on shared remote | Only fastest node's writes land |
| Config comment documents behavior the code doesn't have | Port derived from a different field than documented |

### Detection checklist (add to leaf self-verification)

For every new component, option, setter, and RPC method:
- `grep` production callers (not tests) of each exported symbol
- Trace the chain: config parsed → struct field → constructor →
  registration → runtime invocation. Every arrow must exist in code.
- Boot the REAL daemon with the REAL config and check the startup log line
  you added actually prints.

### The verification ladder (cheap → expensive, run all)

1. Unit/component tests (isolated seams)
2. In-process integration test (two real components, fake transport)
3. **Real multi-process deployment** (the only tier that catches
   never-registered / never-started wiring, port derivation, and
   config-key typos)

Tier 3 is where all seven surfaced. Budget for it; script it so teardown +
reprovision is one command (`make totem-provision|start|stop|status`,
`scripts/totem-cluster.sh sync <user>`), because you WILL cycle the cluster
multiple times while chasing wiring bugs.

## 3. Remote process control: pkill -f self-match

`ssh host "pkill -f <pattern>"` kills the remote shell carrying the pattern
(the `-f` full-command-line match includes your own `bash -c`), so ssh
exits 255 and the loop aborts mid-flight. Fix: kill matching PIDs excluding
the current shell:

```bash
ssh host 'for pid in $(pgrep -f meept-daemon); do [ "$pid" = "$$" ] || kill "$pid" 2>/dev/null; done; true'
```

Related gate traps hit the same session:
- Pre-commit hook shebang `#!/bin/bash` on macOS resolves to bash 3.2
  (no `mapfile`, no `declare -A`). Pin hook shebangs to the newest bash
  (`/opt/homebrew/bin/bash`).
- Gates that reject `_ = f()` (ignored-error) block subagent output
  constantly. Fix pattern in generated code: `if err := f(); err != nil {
  slog.Debug("...", "error", err) }` — checked, not discarded.

## 4. 429 rate limits: subagents can die before writing anything

Mid-size leaves (~40-60K) can hit provider 429 in the initial read phase —
zero files written, unlike the timeout case (most files written). If the
leaf brief was authored as a file (e.g. `/tmp/leaf-X-brief.md`) it survives
the subagent's death: the orchestrator implements directly from the brief
plus accumulated context. Do not re-dispatch into the same rate-limit
window; check when the limit resets first.
