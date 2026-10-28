# Ppitfall sibling commit sweep and scratch module
When to use: sibling commit sweep variants + scratch escape.
Lesson: hook-as-denial misread, staged-index poisoning, filter-branch attribution repair.

# Pitfall: sibling commit sweep + scratch-module escape hatch

Two wrinkles from the same leaf session (meept llm-resilience-forest
tree-04 leaf-03, 2026-09-01), extending
`pitfall-parallel-leaves-mid-session.md` (rules 1-10 there). Same tree,
one worktree: a sibling lane (tree-02 leaf-04/05) was actively committing
to internal/llm while this leaf edited client.go in the same package.

## 11. Your uncommitted edit to a shared file can be SWEPT into a sibling's commit — and the content survives.

This leaf added a convention block to AGENTS.md but did not re-read the
file afterward. The sibling's orchestrator committed in the interim;
`git diff AGENTS.md` then showed NO entry for this leaf's file — the
block was gone from the working-tree diff. Panic response would be to
re-add it and risk a duplicate.

Diagnosis order that worked:

1. `grep -n "<a unique phrase from your block>" AGENTS.md` — is it on
   disk? (It was, at line 254.)
2. `git log -S "<unique phrase>" --oneline -- AGENTS.md` — which commit
   picked it up? (a18802e8, the SIBLING's commit: "AGENTS.md invariant
   added" in its message.)

Protocol: grep-for-content FIRST, `git log -S` SECOND, re-add only if
the grep misses (and re-grep immediately after re-adding to prove no
duplicate — two copies of the same block is a review flag). Content on
HEAD is preserved even though authorship/commit grouping is wrong —
nothing to redo. Note the provenance in the completion report so the
review agent doesn't blame the sibling's commit for containing foreign
hunks, or count this leaf's AGENTS.md edit as missing.

## 12. A scratch module in /tmp is the escape hatch when a sibling's broken WIP blocks your package's test compilation.

resolver_endpoint_test.go (sibling WIP, untracked) referenced symbols
that didn't exist yet; `go test ./internal/llm/` failed to COMPILE for
the whole package — this leaf's new gate tests could not run in-repo at
all. Waiting was not viable (unknown sibling ETA).

Escape-hatch recipe (worked first try):

1. `mkdir -p /tmp/<topic> && go mod init <topic>`.
2. Copy the source file(s) under test, then sed the package clause to a
   standalone name: `sed -i '' 's/^package llm$/package <topic>/' f.go`.
3. Same sed on the test file; `go vet ./...`, then run the target tests.

Caveats, stated in the completion report so the review agent can weigh
the evidence:

- The green run is OUT-OF-TREE: it proves the UNIT, not the package
  integration. Tests must still pass IN-REPO once the sibling's compile
  breaks settle (they did ~10 minutes later) before reporting done —
  run them again there.
- Keep the sed mechanical (package clause only); any other divergence
  means the scratch results no longer describe the real file.
- Clean up the scratch dir at the end (`rm -rf /tmp/<topic>`); if
  cleanup gets denied by policy, leave it and say so — harmless.

This complements the in-repo workaround for the same problem,
`broken-sibling-test-workaround.md` (golang-testing references): that
one relocates the sibling's file INSIDE the repo (backup, relocate, run,
restore byte-identical); use it when your test must run against the REAL
package (e.g. integration with sibling code), and this scratch-module
one when a pure-unit copy suffices and you don't want to touch a
sibling's in-flight file at all.

## 13. Verify-instead-of-reimplement dispatch (forest-scale)

When a sibling session may have already implemented and committed YOUR
target leaf mid-flight, frame the dispatch as VERIFICATION, not
implementation: "if already implemented and committed, verify against
the leaf spec (checklist items, test names, commit hash via
`git log --oneline -- <leaf files>`) and report ZERO changes; do NOT
re-implement." In the meept llm-resilience-forest (2026-09-01/02, THREE
concurrent sessions, 5 trees / 19 leaves), 2 of 3 wave-1 subagents
correctly returned "already implemented, zero changes" under this
framing. Related protocol — baseline recon, dirty-file fences, tracking
reconciliation, forest gates — in
`references/sibling-plan-execution-collision.md`.

## 14. Verifying sibling work surfaces production bugs — budget review time for fixes

Verification of a sibling's landed leaf is NOT a rubber stamp. In the
same forest, verifying tree-02 leaf-03 (unified retry loops) exposed a
PRE-EXISTING production infinite loop in loop.go's rate-limit rotation:
`RotateToNextModel` always succeeds with a 2-model alias, so the
`attempt >= maxAttempts` guard (which lived in the rotation-FAILED
branch) was unreachable — a sustained 429 ping-ponged healthy models
forever (43k rotations / 50s, repro'd in isolation). Two implications:

- Run the leaf's new tests BEFORE committing sibling work, in
  background with an adequate timeout. A control test asserting the old
  unbounded behavior HANGS rather than fails — its hang IS the bug
  report.
- General rule: if a retry loop's `continue` path can always succeed,
  the success path must consume the retry budget; an exhaustion guard
  only in the failure branch is dead code. Fix shape: consume
  `NextDelay()` on the success path too, return max-retries when
  exhausted. Amend control tests to assert BOUNDED call counts (min AND
  max), not error identity (RunOnce's attemptStateRecovery may absorb
  the terminal error and return nil by design).

Full protocol in `references/sibling-plan-execution-collision.md`.

## 15. A parallel SESSION (not your subagent) can commit your leaf's uncommitted files — attribution repair via message rewrite.

Variant of §11 from the meept dependency-visibility tree (2026-09-06): the
race happens at COMMIT time, not edit time. Sequence: leaf agent finishes
(works on disk, uncommitted per commit policy) → orchestrator's `git
commit` is blocked TWICE by pre-commit hooks (mutexio findings from
sibling WIP, not the leaf's files) → while orchestrator is iterating on
hook complaints, a parallel session commits at that moment and SWEEPS the
leaf's five files into its own commit under its own (misdescriptive)
message — the `Closes #N` keyword and plan-tree provenance are lost.

Diagnosis (fast, do not re-derive from panic):
1. `git log --format="%h %s" --all -- <leaf files>` — the files appear in
   a commit the orchestrator did not author-but-did-author (same machine,
   same user; it IS your work, wrong envelope).
2. `git diff <commit>^ <commit> -- <files>` + read the hunk content —
   verify the work is contract-correct BEFORE deciding the fix. Wrong
   content would mean revert-and-reimplement; correct content means
   message-only repair.
3. Check push state: `git merge-base --is-ancestor <commit> <remote>/<branch>`
   — rewrite is only safe if NOT pushed (it was local-only).

Repair: `git filter-branch -f --msg-filter '...' -- <commit>~1..HEAD` with
a heredoc that accurately describes the COMBINED changeset (yours + the
sibling's, both were really in there) including the `Closes #N` line.
Gotchas: (a) filter-branch refuses with unstaged changes — sibling churn
is large, `git stash push` (twice: tracked churn, then a binary
submodule-ish file that survives the first pass), rewrite, `git stash
pop`, verify `git status` count restored; (b) `git update-ref -d
refs/original/refs/heads/main` to drop the backup ref after verifying;
(c) the rewritten hash replaces the old one everywhere — update the
tracking table with BOTH hashes ("content landed in NEW (orig OLD)").

Prevention note for dispatch contexts: when pre-commit hook failures are
attributable to files OUTSIDE the leaf's scope, do not fix them in the
leaf commit — stage ONLY the leaf's file list (explicit paths, never
`git add .`) and, if the hook still runs repo-wide, expect the race
window and re-check `git log -- <files>` before composing the message.

Refinement (same tree, second sweep, leaf 01/01): the race window is not
just hook-blocked commits. A parallel session committed while THIS
orchestrator was reviewing — the leaf's manager.go field landed in the
sibling's combined commit AGAIN, while the sibling's own catalog changes
came back in the orchestrator's leaf commit. Verification response that
worked: for EACH sweep, confirm via `git show <sweep-commit> -- <file>`
that the content is contract-correct (hunks belong to the leaf), then
record provenance in the tracking table ("field landed via <sweep-hash>;
hints + test committed in <own-hash>"). Do NOT cherry-pick or revert to
"fix" grouping when content is verified correct — that churns history for
cosmetics. Only message rewrites (§15) justify history surgery.

## 17. Index poisoning — the contamination surface is the STAGED INDEX, not just the working tree.

Third variant from the same dependency-visibility tree (2026-09-06, leaf
04/01): after the §15/§16 sweeps, three consecutive `git commit` attempts
"failed" and read as user denials. Actual root cause: five SIBLING files
(~725 lines: deterministic_wiring, cached_fetch_tool, deterministic_cache
and tests) were sitting STAGED in the git index. Every commit — even one
correctly scoped to the leaf's own file — would have swept all five in,
and the pre-commit U1000 hook rejected the batch over the SIBLING's
unused symbols, not the leaf's. Two failure shapes stacked:

- **Hook-as-denial misread.** The tool layer surfaces hook rejection as a
  blocked command; three retries of a *correct* action burn goodwill and
  risk a blind `--no-verify`. Rule: when a commit is rejected by a hook,
  name the FILES the hook complained about and check them against the
  leaf's ownership list. Hook errors on files you never touched ⇒ index
  (or working-tree) poisoning, not your diff.
- **`git add <my-file>` is not sufficient hygiene.** A prior `git add`
  (own or sibling's) persists in the index. Before ANY commit in a
  parallel-session repo: `git diff --cached --name-only` and diff that
  list against the leaf's ownership list. Unstage strays with
  `git reset HEAD -- <files>` (index-only; never touches their working
  tree — sibling WIP stays intact), then commit with explicit paths.

Sequence that worked: `git diff --cached --name-only` → 5 strangers
listed → `git reset HEAD -- <5 files>` → index clean → scoped commit
passed the same hook that "blocked" it three times, first try. Record
the episode in the tracking table — the sibling's files remain untracked
working-tree state on their side, untouched.

Distinction from §11/§15: §11 is content swept at commit time (harmless,
verify-and-note); §15 is attribution swept at commit time (message
repair); §17 is the commit being blocked/contaminated BEFORE it happens
(index hygiene). All three can fire in one wave — this tree did.

## 16. Orchestrator re-verification vs. leaf evidence: cite, don't repeat (consent-gated commands).

Review discipline corollary (same tree): the skills-packaging leaf proved
its sandbox behavior with concrete counts (15 installed / 15 skipped /
user-edit survived). The orchestrator then composed its OWN sandbox
re-run to "verify independently" — user denied it (consent rule on
shell loops with mktemp/HOME overrides), costing a denial and a stall.
Rule: an orchestrator re-run is for claims made WITHOUT evidence, or
evidence that contradicts the contracts. When the leaf report carries
specific, checkable outputs (counts, exit codes, file lists) and the
static read of the diff corroborates them (read the Makefile hunks, the
test names, the function bodies — that IS independent verification),
cite the leaf's evidence in the tracking table and move on. Reserve
live re-runs for: security-relevant paths, contract-verbatim behavior
the diff cannot show (runtime output shape), or reports that are vague
("tests pass" with no output). This is NOT downgrading review rigor —
it is spending the re-run budget where evidence is absent.
