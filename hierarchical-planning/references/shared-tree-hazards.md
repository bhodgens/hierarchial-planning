# Shared-Tree Hazards — Multi-Session Working Trees

**When to use:** Executing hierarchical plan trees in repos where OTHER
sessions/agents are concurrently committing, editing shared files, or
adding untracked files. Lessons measured 2026-08-26 (classifier-reliability
tree) and 2026-09-04 (chat-dispatch-ux parallel fan-out).

## Hazard 1: `git add <file>` sweeps sibling work into your commit

Leaves that share files (dispatcher.go, components.go wired by multiple
leaves) mean `git add <file>` stages EVERYTHING in that file — including
another leaf's or another session's uncommitted hunks.

**Fix: stage and split at commit time.**

```bash
git diff <file> > /tmp/f.diff          # full working diff
# keep only hunks matching YOUR contract keywords; drop the rest
python3 /tmp/split_hunks.py            # filter by hunk content
git apply --cached /tmp/f.filtered.diff
```

Hunk-filter heuristic used successfully: keep hunks containing your leaf's
contract identifiers (field names, function names from the interface
contract), plus pure gofmt realignment lines (they must ride along when the
contract touches a struct — new longer field names force realignment of the
whole struct block).

**Real instance:** components.go gained 79 diff lines but only 8 were
semantic (`ClassifierModelConfig` field + resolver block + pass-through);
the rest was gofmt padding after the longer field name. Filtering kept the
commit honest.

**Real failure mode when skipped:** one commit swept another session's
untracked 383-line gbnf.go under our commit message; it only got committed
because a pre-commit staticcheck gate flagged a dead append inside it.

**Addendum (2026-09-04, chat-dispatch-ux): when hunk-splitting is too risky,
sweep deliberately and flag in the message.** Mid-wave, the only buildable
state of a shared file may include a sibling session's self-applied hunks
(e.g. an audit session that self-fixed its findings and left them
uncommitted in the same file you must commit). Unraveling via stash/checkout
in a live parallel tree causes Hazard 3/6; waiting blocks your leaf. Working
reconciliation: stage the file whole, but BEFORE staging grep the working
diff for markers your leaf never wrote (`AUDIT FIX`, another tree's contract
identifiers, comment styles you didn't author). If found, expect the sweep
and write a deliberate reconciliation flag into the commit message: name the
hunks by their marker IDs, name the owning session's tracking doc
(`.hermes/audits/<date>.md` ledger, plan tracking table), and state the
owner should reconcile. A real leaf commit carried a sibling audit session's
`AUDIT FIX H1`/`C2` hunks in loop.go; the audit doc already listed them as
self-fixed-in-scope, so the message pointer plus that ledger gave the owner
full recovery. Do NOT silently absorb foreign hunks without the message
flag — silent sweeps are how the gbnf.go failure above happens.

## Hazard 2: Pre-commit hooks gate on files you never touched

Hooks running repo-wide staticcheck/vet will fail on OTHER sessions'
untracked or modified files (in-flight WIP with syntax errors). Also watch
for hook breakage itself: `#!/bin/bash` on macOS Homebrew resolves to bash
3.2 which lacks `mapfile`.

**Options in order:**
1. Fix the offending line if trivial (one dead append = legitimate).
2. Commit with `git -c core.hooksPath=/dev/null commit ...` IF package
   tests were already run manually — and SAY SO in the commit body.
3. Never silently bypass; note the bypass and reason in the message.

## Hazard 3: Trust-but-verify subagent "unrelated failures" claims — but NEVER stash in a shared repo

Subagents report "test X fails, unrelated to my changes." Verify each such
claim by running the test WITHOUT the subagent's changes — but never via
`git stash` in a repo other sessions commit to. Measured 2026-09-04: a
`stash push -- <paths>` / `pop` raced a sibling commit and left `UU go.sum`
unmerged; a following `go mod download` mutated go.sum again. Recovery:
`git checkout HEAD -- go.sum` (generated files: HEAD is truth), `git stash
drop` the half-popped entry, re-stage only own paths. Use
`git worktree add /tmp/wt HEAD` for "does HEAD pass without my changes?"
checks — stash assumes you own the worktree.

Verification recipe (single-owner repo only):
```bash
git stash push --keep-index   # or stash specific paths
go test ./pkg/ -run TestSuspect
git stash pop                 # verify pop restores cleanly; check git status
```

Beware: `git stash pop` can silently drop staged state on conflict — always
re-check `git status --short | grep '^[MA]'` afterwards.

## Hazard 4: Struct realignment inflates diffs — read semantic delta, not line count

Adding one long-named field to a Go struct gofmt-realigns every sibling
line. A "49-line change" may be an 8-line semantic change. Before judging a
leaf's diff size (or writing its review), normalize whitespace:

```python
def norm(l): return l[1:].replace(' ','').replace('\t','')
added_n = {norm(l) for l in added}
semantic = [l for l in added if norm(l) not in removed_norms]
```

Report both numbers in review: raw diff vs semantic delta.

## Hazard 5: Concurrent commits to main between your commits

Other sessions commit continuously. Your three clean leaf commits can be
separated by unrelated feature commits in `git log`. Don't panic; use
`git log --grep=<your-scope-keyword>` to enumerate YOUR commits, and confirm
ancestry with `git branch --contains <sha>`. Never assume log position =
ownership.

## Hazard 6: Parallel leaf fan-out — pre-commit package builds break on sibling WIP (measured 2026-09-04, chat-dispatch-ux)

**During parallel leaf execution, pre-commit "build staged packages" hooks
fail on sibling WIP, not on your files.** `go build ./internal/<pkg>`
compiles the whole package plus transitive imports, so a sibling leaf's
half-written file (e.g. a helper referenced before its definition landed,
in a package your commit transitively imports) fails the hook on YOUR
commit of a different file. Real case: leaf 03's commit of internal/daemon
files blocked by leaf 05's in-flight internal/agent/reply_guard.go
(`undefined: proseLineRatio`).

Protocol (do NOT fix the sibling's in-flight code, do NOT wait for it):
1. Verify YOUR package manually: `go build ./<pkg>`, `go vet ./<pkg>`,
   scoped `go test -p 2 ./<pkg>/ -count=1`, analyzers, `gofmt -l ./<pkg>`.
2. Commit with `git -c core.hooksPath=/dev/null commit` and a message note
   naming the sibling WIP and the manual checks run (Hazard 2 option 2,
   applied to leaf fan-out).
3. Generated files churned by concurrent tooling (go.sum): on conflict,
   `git checkout HEAD -- <file>` — HEAD is truth for generated files — and
   commit only your leaf's real paths.

**Wave sequencing when leaves share a file:** components.go ran
03→04→06 and loop.go ran 05→07 — Wave-B leaves sharing a file with a
Wave-A leaf are dispatched sequentially AFTER the earlier leaf's commit,
never in parallel with it or each other. Dispatch contexts for later
leaves carry the earlier commit hash so implementers re-check shifted line
numbers, plus an explicit "keep hunks tight; a sibling leaf edits this
file after you" warning.

**Foreign-hunk interleave with sibling self-fix sessions.** When an
audit/fix session runs alongside implementation waves, its self-fix hunks
(AUDIT FIX H1/C2/H3 tags) interleave with leaf hunks in the same file.
When hunk-splitting cannot cleanly separate them: verify `go build ./<pkg>`
green with everything in place, commit together, and FLAG — the commit
message names the foreign hunks and their owner ("carries sibling AUDIT
FIX H1/C2 hunks — flagged for that session to reconcile") and the tracking
table's Review Notes records the carry. The owning session reconciles from
`git log`.

**Pre-authorize sibling-WIP retries in dispatch contexts.** Another
writer's mid-edit state briefly breaks package compilation (~40s windows
observed). Tell implementation agents: "a compile error in files you did
NOT touch is sibling WIP — wait ~60s and retry the scoped test; report
failure only after 3 retries." Without this, implementers burn cycles
diagnosing another session's in-flight edit.

**Judging leaf "deviations": re-read the anchor before judging.** Same
tree, leaf 03: the implementer reported a deviation because the master
cited a top-level `session.CWD` at session.go:56 — the real shape is
`Session.DetectionContext.CWD` (field at :79, struct at :55-59). The
implementer was right; the master's anchor was imprecise. Verdict:
re-verify the anchor in source, and when the implementer's adaptation is
the correct one, APPROVE and record the corrected anchor in the tracking
table's Review Notes instead of re-dispatching. A deviation note is often
the plan getting fixed, not the leaf failing.

## Hazard 7: Generated/CI-checked docs regenerated against a dirty tree bake in sibling WIP (measured 2026-09-04, leaf 09)

`make graphs` scans the WORKING TREE, not HEAD. Committed regenerated docs
therefore carry sibling in-flight edits' line numbers and file entries
(untracked leaf files, sibling park fixes). The commit is still correct to
make — the annotation itself is right and graphs-check passes — but
freshness will drift again the moment the siblings commit. Protocol: commit
with a message note ("scanned against working tree holding in-flight
X/Y/Z; regeneration rerun scheduled at integration gate"), and actually
rerun `make graphs && make graphs-check` as part of the final integration
gate after ALL leaves land. Symmetric rule for any CI freshness gate
(gen-docs, OpenAPI, dashboards): last regen must postdate the last code
commit it scans.

## Hazard 8: A "minimal" scratch config is not a valid config — enumerate the construction gates (measured 2026-09-04, leaf 10 e2e)

An e2e leaf's scratch daemon booted fine but every chat failed
`no agent available for "chat"`: the hand-written minimal json5 omitted
`multiagent.enabled`, and components.go only constructs AgentRegistry
inside `if cfg.MultiAgent.Enabled` — the entire specialist roster,
including the `chat` fallback agent, registers through it
(`Agent registry initialized specs=0` in the log was the tell). Before
authoring a scratch config, grep the construction site for its gating
conditions (`grep -n 'if cfg\\.' internal/daemon/components.go | grep -i
enabled`) and set every gate the transcript's path needs. Second failure
in the same leaf: `set -u` + a variable referenced before assignment
crashed the warmup, and the error was initially misread as a provider
SKIP — classify "provider error" vs "script crashed" BEFORE emitting
SKIP, since the SKIP path is exactly what masks script bugs.

Third failure in the same leaf — identifier wiring (2026-09-04): the MCP
warmup passed a bare conversation ID (`oneshot_responses`); the daemon
processed it lazily WITHOUT creating a session row (DB count 0), so a
"discover the session by name" step found nothing. When the row DID
exist, `--project` turns still needed the REAL row id because
`project.set` rejects bare IDs. And `session list` orders by
`last_activity DESC`, so "first match by name" can pick a STALE row —
iterate all matches and take the last (newest). General rule: verify
which identifier each RPC actually keys on (conversation_id vs session
row id) before scripting turns, and capture the id at creation time
rather than discovering it afterwards.

## Hazard 9: E2E leaves that assert behavior across components will surface a THIRD bug that belongs to neither leaf (measured 2026-09-04, session-continuity leaf 03)

When leaves 01+02 (continuity plumbing) verifiably hold — sqlite
forensics confirm the DB rows — but the e2e assertion still fails, the
culprit is usually a PRE-EXISTING component sitting BETWEEN the fixed
parts that neither leaf touched. Real case: T3 follow-ups still got
canned clarifications because the dispatcher's intent-analyzer ambiguity
gate short-circuits into `buildClarificationResult` BEFORE the chat
agent (with restored history) is ever invoked. Protocol for the e2e
leaf: (a) verify the upstream leaves' mechanisms directly against
storage (sqlite query, not the LLM's behavior), (b) if those hold,
trace the full request path for a gate/filter that fires before the
fixed component, (c) invoke the leaf's STOP clause — report the
pre-existing blocker with file:line evidence, commit the tightened
assertion so the gap is DOCUMENTED not hidden, and flag the gate
decision to the user (gating policy is a design decision, not
something an implementation leaf sneaks in). Never weaken the
assertion to make a stale gate look like success.

**Tighten assertions against flaky LLM output with shape guards, not
determinism assumptions.** When an assertion like "reply references the
artifact" passes/flakes across runs, tighten by adding a NEGATIVE
condition on the failure signature (e.g. "and is not a bare
clarification request: contains '?' without the artifact mention") with
a distinct FAIL reason — rather than loosening the positive check. The
distinct reason string is diagnostic: "continuity gap" points at
context loss; "rate limited" points at provider window.

## Hazard 10: Spec-internal conflicts — the leaf's Task snippet vs the master's Interface Contract (recurring 2026-09-04, session-continuity leaves 02/06)

When a leaf's inline code snippet disagrees with the parent's Interface
Contract section (real cases: contract said "quota wait:
<provider>/<model> is rate-limited until <time>..." while the task
snippet had a shorter sentence; contract said "call GetMessages(id, 0,
0)" while that literal call returns ZERO rows in both production
stores), instruct implementers to resolve IN FAVOR OF THE CONTRACT and
record it as a deviation — but ALSO teach implementers to verify
contract claims against production store semantics before implementing
(`SELECT ... LIMIT 0` returns nothing; a "get all" semantic needs
MaxInt32 + in-memory tail-cap). An implementation leaf that catches its
own spec's bug and documents the resolution is a SUCCESS, not a
deviation problem — record the correction in the tracking table so the
master gets fixed for the next tree.