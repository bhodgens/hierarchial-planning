# Mmulti session repo contention
When to use: concurrent sessions in one repo.
Lesson: contention survival guide for shared checkouts.

# Concurrent Sessions in the Same Repo — Contention Survival Guide

When other Hermes sessions/agents commit to the same repo while you execute a plan tree, these patterns are load-bearing. Real instances: meept unified-theming + loop-economics, 2026-08-25.

## Commit each leaf immediately

Never leave verified leaf work uncommitted while dispatching the next wave. Another session running `git restore`/`git checkout .` cleanup silently deletes uncommitted leaf files. Two waves of subagent edits were destroyed at a single timestamp in one session (~2h re-done). Also: other sessions sweep your uncommitted files into THEIR commits with unrelated messages — recoverable via `git log -S` but history becomes misleading.

Rule: review passes → `git add <exact leaf paths>` → `git commit` → update tracking table → then dispatch next.

## Their broken WIP breaks your builds

If `go build ./...` fails in packages you don't own, identify the owner first (check `git status` + `git log -1 -- <file>`). Verify your packages only (`go build ./cmd/mine ./internal/mypkg`) or wait for stabilization. Never "fix" another session's half-landed feature.

## Extracting only your hunks from an entangled shared file

When a shared file (e.g., config schema) contains both your changes and theirs:

```python
import subprocess, re
diff = subprocess.run(['git','diff','<file>'], capture_output=True, text=True).stdout
lines = diff.split('\n')
i = 0; header = []
while i < len(lines) and not lines[i].startswith('@@'):
    header.append(lines[i]); i += 1
out = header[:]
while i < len(lines):
    if lines[i].startswith('@@'):
        m = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@(.*)', lines[i])
        body = [lines[i]]; i += 1
        while i < len(lines) and not lines[i].startswith('@@'):
            body.append(lines[i]); i += 1
        if any('<YOUR MARKER>' in l for l in body):
            old_n = sum(1 for l in body if not l.startswith('+'))
            new_n = sum(1 for l in body if not l.startswith('-'))
            out.append(f'@@ -{m.group(1)},{old_n} +{m.group(3)},{new_n} @@{m.group(5)}')
            out.extend(body)
open('/tmp/mine.patch','w').write('\n'.join(out))
```

Then `git apply --cached /tmp/mine.patch`. Recomputing the hunk header counts after filtering is mandatory (`corrupt patch at line N` otherwise).

## Recovering deleted-but-staged work

Concurrent sessions reset the index or delete files from disk. Recovery ladder:

1. `git ls-files --stage | grep <name>` — index may still hold it; `git checkout-index -f -- <path>`.
2. `git fsck --lost-found` → grep dangling **trees** with `git ls-tree <tree>` for the filename, or dangling **blobs** by content (`git cat-file -p <blob> | head`).
3. Reconstruct from the committed test contract — tests pin exact type names, fields, method signatures, and behavioral semantics. A test file surviving is a full spec.
4. Check whether a concurrent commit already swept the content: `git log --all --oneline --source -S '<signature>' -- '**/<file>'`.

## Dead-subagent detection (before long waits)

Subagents stall silently without reporting failure (delegation timeout 0 = no cap). Before entering poll-sleep loops:

1. Process liveness: `ps aux | grep <agent-cmdline>`.
2. Disk activity: `stat` mtimes on target files. No movement >30min = dead, not slow.
3. Partial output is on disk — review directly, take over in-session. Do NOT sleep for hours waiting on a dead agent (real cost: 7 hours of poll loops; the user had to ask "are they still doing work?").
