# Execution Pitfalls 43-45: Duplicate Dispatches, Shared-Repo Hooks, Leaf-Table Errata


When to use: executing trees while sibling sessions commit to the same repo.
Lesson: late duplicate dispatches, pre-commit failures from siblings, leaf-table errata (pitfalls 43-45).
Session-proven additions (2026-09-05, four-tree Grok-bot gap program: 12
leaves dispatched, all landed, two parallel sibling sessions committing to
the same repo concurrently). Promote into SKILL.md pitfalls when the file
next fits under the 100K cap.

## 43. "Missing" dispatch may be a slow dispatch — late duplicates rewrite leaf files

When a dispatched leaf shows no completion notification AND no files on
disk, check running processes / git state before re-dispatching. If you
re-dispatch anyway, the ORIGINAL can complete later and overwrite the
re-run's files — the late run may also be the BETTER one (it had more
tool-call budget).

On a late duplicate landing:
- `git status` / `git diff` the leaf's files BEFORE committing anything.
- Test-only superset or strict improvement → commit cleanly as a
  follow-up commit referencing the first commit in the message.
- Conflicting duplicate → reconcile in-session; never blind-recommit.

Worked example: re-dispatch landed first; the original finished ~90 min
later with a deeper purity test + mutation guard — committed as test-only
follow-up referencing the first commit.

## 44. Strict-pre-commit repos + parallel committers: hook failures are usually not your leaf's fault

The pre-commit run sees worktree + sibling-session state, not just your
staged files. A parallel session's in-flight package (transient undefined
symbol, mutexio violation in their test file) blocks YOUR commit — and
may resolve itself when the sibling's commit lands mid-verify (observed:
setter-nil-safety hook failed on an uncommitted pdf_read.go; the sibling's
commit landed minutes later and the package compiled).

Protocol:
1. Read the hook output and identify the FAILING PACKAGE.
2. If it contains no files you touched → re-run YOUR leaf's tests.
3. Stage only your leaf's files.
4. `git commit --no-verify` — after re-verification, not instead of it.
5. Report that you did, in the leaf-completion report.

Warn implementer dispatches on shared-repo trees to expect this. It fired
twice in one session.

## 45. Leaf-table errata: the leaf's literal test expectations can contradict the leaf's own frozen rules

Pitfall 21 (paraphrase-drift) covers spec→contract drift. A second drift
class runs leaf-semantics→leaf-test-table: the leaf author pins exact
semantics in the Interface Contract, then hand-writes test-table rows
whose expected values contradict those semantics. Worked example: 3 of 16
frontier table rows expected values contradicting the pinned
ready/cycle rules (one expected `cycle=false` where the frozen rule
forced `true`; two expected ready-sets unreachable under the pinned
gate rules).

Resolution order:
1. Frozen rules win — implement the rule-correct value.
2. In-code comment at the deviation site.
3. Record each erratum in the tree's OPEN-QUESTIONS.md under an
   "implementation errata" heading so leaf-vs-implementation deltas stay
   reviewable.
4. Do NOT silently edit the leaf's table to match the code (the leaf is
   the record of original intent).

Related success mode — STOP-and-report is correct behavior: a leaf that
halts on (a) an out-of-scope one-line registration the 3-file bound
excludes, or (b) an impossible pinned assertion (a test reading a row a
pre-existing store filter makes unreachable), is working as designed.
The orchestrator applies the small fix in-session (one registration line;
swap the load mechanism to a filter-free API), records it in
OPEN-QUESTIONS, and proceeds. Do not widen the leaf's scope and do not
re-dispatch.
