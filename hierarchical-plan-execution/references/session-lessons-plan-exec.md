# Session Lessons — Plan Execution Pitfalls (meept tier-3 tree, 2026-08-22)

## 1. Subagent "timeout" ≠ work lost

`delegate_task` leaf agents routinely hit the 600s wall and report
`status=timeout` with no summary — but their file edits are ALREADY ON DISK.
All three leaves of the meept tier-3 tree reported timeout; all three had
complete, passing work.

Before re-dispatching anything:
1. `git status --short` + `git diff --stat` on the leaf's target files.
2. Run the leaf's own verification commands (build, tests, analyzers).
3. If complete and passing: treat as done — review and commit normally.
   The timeout was only the report step.
4. Re-dispatch only genuinely incomplete work, scoped to the gap.

Re-dispatching a "timed out" leaf whose work landed wastes a full 10-minute
agent run per occurrence.

## 2. Staged-but-uncommitted WIP rides along

Implementation agents sometimes leave STAGED files beyond the leaf's scope.
In one case a follow-up commit briefly captured 23 unrelated modified files.

Rule: always `git add <explicit paths>` AND commit with explicit paths
(`git commit ... -- <paths>`), then verify with `git show --stat HEAD`.
If a wrong commit lands: `git reset --soft HEAD~1`, unstage everything,
re-add only the intended paths, recommit.

## 3. Pre-commit hooks: diagnose before bypassing

Pre-commit chains often pin analyzer versions that break on Go toolchain
upgrades (bodyclose built against go1.26 export data crashes under go1.27
with "failed prerequisites" / "export data version N > maximum supported").
When a hook fails:
1. Does the failure name project code locations or tooling-internal errors?
   Tooling-internal = broken analyzer, not bad code.
2. Run every other hook manually to confirm the code passes.
3. Fix what's fixable (`go install <analyzer>@latest`) or commit with
   `--no-verify` + a commit-message note documenting which hook was bypassed
   and why.

Never bypass a hook reporting real findings in project code. Also watch for
hook failures caused by earlier leaves (e.g. a test still referencing a
pre-refactor symbol) — fix-forward in a small follow-up commit with explicit
paths.

## 4. Review agents' work for phantom references

A leaf agent wrote a test referencing `employee.Tier2ConstitutionForTest()`
— a function that doesn't exist. Subagent self-reported tests-passing can be
wrong if it never ran the final state. The orchestrator review step must
actually run the package tests itself (`go test -count=1 -race ./pkg/...`),
not trust the agent's summary.

## 5. Config format gotchas discovered

- hujson (tailscale) = JWCC only: comments + trailing commas. It does NOT
  support unquoted keys, even though files in the repo use them. Employee
  JSON5 definitions must quote all keys.
- meept `autonomy_tier` must be the STRING form ("tier_2_propose"); numeric
  values silently fail decode → constitution rejected at hire time.
