# Iintegration gate lint attribution
When to use: repo-wide lint gate reports sibling debt.
Lesson: scope lint attribution to your files; record sibling findings, do not fix silently.

# Integration-Gate Lint Attribution (shared repos with sibling debt)

## Problem

A repo-wide lint gate (`make lint-ci`, golangci-lint) at the integration
gate reports findings across files your tree touched AND files sibling
sessions own. Repo convention: a leaf commit carries only its own scope;
lint debt in files another session introduced belongs to that session.
Blindly fixing everything sweeps sibling work into your commit and buries
real regressions.

## Attribution protocol (before fixing anything)

1. Bucket findings by file:
   `golangci-lint run internal/<pkg>/ 2>&1 | grep -E '^[a-z/]+\.go:[0-9]+' | awk -F: '{print $1}' | sort | uniq -c | sort -rn`
2. For findings in files YOUR commits touched, attribute the introducing
   commit:
   - `git log --format='%h %s' -1 -L <line>,<line>:<file>` (precise)
   - `git log --format='%h %s' -S '<distinctive snippet>' -- <file>` (when
     the line moved between commits)
3. Decide:
   - Introducing commit is YOURS -> fix in this tree, before the final
     integration commit.
   - Introducing commit is a sibling's or predates the tree -> leave it.
     Note it in the completion report; the owning session applies the
     repo's "minimal fix + separate commit" convention.
4. Large category totals (modernize 50, staticcheck 45...) are usually
   repo-wide debt accumulated by parallel sessions. Verify none of the NEW
   findings fall inside hunks YOUR commits added — that is the only part
   the gate holds this tree responsible for.

## Worked example (meept chat-dispatch-ux, 2026-09-04)

lint-ci failed; internal/agent findings attributed via `git log -L`:
handler.go:652 (c6dd6ce7 dispatch-audit — sibling), :854 (cfb863d6 budget
errors — pre-tree), :1610 (bc8afada quota-resilience — pre-tree), :2003
(c4531b54 PTY — pre-tree), tactical.go:551 (1a5cea06 agentic pairs —
sibling). All introduced by commits NOT in this tree -> zero fixes;
documented in the completion report.

## Gate-order notes

- Run generated-docs regen (`make graphs && make graphs-check`) AFTER the
  last code commit: generated docs scan the working tree and drift if
  regenerated early. Schedule the rerun at the integration gate (leaf 09
  lesson).
- Full package suites with `-count=1` and `-p 2` (macOS) run after the
  regen so the final green state is on record.
- Custom analyzers (mutexio/predid/selflock/fieldguard) are cheap — run
  them per-leaf AND at the gate.

## Line-number drift across the session's OWN commits

`git log -L` attributions can be stale by gate time because YOUR tree's
commits shifted the lines. The 2026-09-04 gate pass attributed findings
via `-L` from the CURRENT line number; verify the attributed commit is
plausible for the finding (does the function/feature match?) before
trusting it. If attribution looks wrong (finding sits in a hunk your
tree added but `-L` names a pre-tree commit), re-anchor via
`git log -S '<distinctive snippet from the finding line>'`.

## Guard escape-hatch bypasses (companion lesson, same gate pass)

Any sanitizer/heuristic guard with a pass-through branch (e.g. a
"reply is >40% prose → pass through" escape hatch on a catalog guard)
will eventually be bypassed by model output wrapped in enough
legitimate-looking prose — observed flaky: an agent-roster dump with a
friendly preamble cleared the prose bar and reached the user. When a
flaky leak is confirmed: tighten to an ABSOLUTE trigger for unambiguous
markers (a roster/status header cannot appear in a legitimate reply),
keep the ratio hatch only for ambiguous shapes, and add the exact
bypass as a named regression test case (meept commit 26f276fd,
"prose-wrapped roster still sanitizes").
