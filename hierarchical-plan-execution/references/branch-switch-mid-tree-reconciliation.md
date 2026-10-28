# Bbranch switch mid tree reconciliation
When to use: sibling flipped the shared checkout mid-tree.
Lesson: reconcile without stomping: ancestry checks, cherry-pick at gate.

# Branch Switch and Shared-Index Hazards Mid-Tree (2026-09-06)

Session evidence: transcript-large-corpus tree executed while a sibling
session switched the shared checkout from main to feat/tokscale-ingest
between waves. All four leaf commits landed on the sibling's branch.
Reconciled cleanly; protocol below. Also covers two adjacent
shared-checkout hazards hit the same day.

## 1. Sibling switches the branch mid-tree

Signal: `git commit` output says `[feat/whatever ...]` when you expected
main. A sibling owns the same checkout and ran `git checkout <branch>`.

Protocol:
1. Do NOT checkout back immediately — the working tree is shared; if
   the sibling has in-flight edits, switching stomps them. Check
   `git status --short` (tracked modifications) first. Empty = safe.
2. Map the topology: `git log --oneline main..<branch>` and
   `git log --oneline <branch>..main`. Interleaved sibling commits on
   the branch are NORMAL — identify YOUR commits by message.
3. Cherry-pick only your commits onto main, in original order:
   `git checkout main` then `git cherry-pick <c1> <c2> ...`.
4. Re-run the integration gate ON MAIN after the picks — the gate
   result on the sibling's branch does not transfer (different base).
5. Leave the duplicates on the sibling branch; note in the completion
   report that the branch carries to-be-dropped duplicates.
6. Prevention: state `git branch --show-current` in every commit-step
   todo, or check it once per wave. Multi-session checkouts drift.

## 2. Pre-commit analyzer gate blocks on files you never touched

Signal: commit blocked with a mutexio/lint violation in files that are
already committed at HEAD (e.g. `orchestrator_*_test.go` at 637cdeb9),
pulled into the gate's analysis because a SIBLING staged foreign files
into the shared index (`git status` shows them staged, staged-not-
committed, from another session).

Fix: commit by explicit path — `git commit <your-files> -m "..."` —
which commits only the named paths regardless of what else the shared
index holds. Never `git rm`/unstage the sibling's staged files; their
session staged them deliberately.

Corollary: after ANY commit on a shared checkout, `git status` again —
staged-foreign-file state persists and pollutes your next commit.

## 3. Subagent working tree committed by a sibling

Signal: a leaf subagent reports "not committed" per instructions, but
minutes later the work exists as a commit authored by the user's
identity — a sibling session ran `git add -A && git commit` and swept
the subagent's working-tree state up.

Handling: diff the landed commit against the subagent's reported file
list and deviations (`git show <sha>`). If they match, treat it as
landed — do not re-commit. If they diverge, fix forward on main. Record
the true hash in the tracking table either way; the subagent's report
of "uncommitted" is stale the moment it prints.

## 4. rm cleanup is consent-gated even with verbal approval

Leaf scratch dirs (probe packages, scratch mains) survive when the leaf
subagent's own rm was denied. The orchestrator's later rm — even when
the user verbally said "do that" — is STILL denied by the permission
layer (denial is consent-withheld at the tool layer, not a flake; do
not retry or rephrase, per the deny contract).

Protocol: hand the exact commands to the user in the completion report
as the "next step" block, and list the scratch paths under Observations
so they are deletable later. Do not attempt alternate deletion routes.
