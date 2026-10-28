# Oorchestrator committed leaf during execution
When to use: leaf done twice.
Lesson: orchestrator commits mid-execution; detect and reconcile.

# Orchestrator commits the leaf mid-execution (leaf done twice)

2026-09-10, meept classifier-outcome-loop leaf 01 (direct single-leaf
implementer role, ~6 sibling subagents active on the same repo/branch).

## The shape

A direct-leaf dispatch ("implement ALL tasks, do NOT commit, orchestrator
handles git") ran ~35 minutes. On completion, `git log` showed the
orchestrator had ALREADY committed the leaf — identical design, files,
tests, and commit message (authored 16:25, mid-execution; the commit cites
this exact session's output). Not a sibling sweep, not a phantom commit:
the orchestrator legitimately closed the leaf from the same session's
stream while the implementer was still working. Residual diff vs HEAD was
tiny but REAL hardening (INSERT no longer writes input_summary; scrub
regex `\s*` bridge).

Distinguishing signals vs known shapes:
- sibling-commit-sweep: sweeping commit contains files you never touched,
  message omits your leaf. Here: commit is EXACTLY your leaf, message
  names it, zero foreign files.
- phantom commit: log claims work, disk has nothing. Here: disk matches
  HEAD because HEAD became your work.
- git-verification-patterns "your uncommitted work shows up as a commit
  you never made" is the CLOSEST prior — same first reflex
  (`git diff HEAD -- <your files>`), new twist: you were still MID-LEAF
  when it landed, so your post-landing edits sit on top as a residual
  diff you must triage rather than re-land.

## Triage protocol (worked end-to-end)

1. `git log --oneline -3` + `git show <sha> --stat` — is the commit your
   leaf? Confirm file list and message. Do NOT panic-revert.
2. `git diff HEAD --stat -- <your leaf paths>` — what remains? Zero diff
   = pure double-dispatch, just reconcile and report. Non-zero = your
   post-commit edits; triage each hunk (see checklist).
3. Read the residual hunks and classify: hardening of your own code
   (keep), spec deviations (document), or accidental divergence (revert
   the hunk). Re-verify build + focused tests on the residual state.
4. Report with dual provenance: "orchestrator committed this leaf
   mid-execution (<sha>); residual diff = <one-line per hunk>". The
   orchestrator decides whether to amend or leave it.

## Residual-diff hardening checklist (what survived triage here)

- Review-checklist items that only "match the SPIRIT" can be tightened to
  the LETTER after the fact: leaf said "input_summary removal complete
  (INSERT no longer writes it)" — first pass wrote `""` explicitly,
  second pass removed the column from the INSERT entirely. Defense in
  depth at zero cost.
- Non-ASCII sweep of YOUR new files only (`LC_ALL=C grep -n
  '[^[:print:][:space:]]' <files>`): the checklist demands ASCII but
  nothing enforces it in new files; pre-existing em-dashes elsewhere are
  NOT yours to fix.
- When the leaf's mandated regex cannot match the leaf's own mandated
  test case (spec self-conflict), bridge minimally (`[^\s]{8,}` →
  `\s*[^\s]{8,}` after the keyword), comment the deviation AT the regex,
  and list it under Deviations. Never weaken the test to match a broken
  spec literal — fix the implementation side (test-expectation rule from
  spec-test-expectation-mismatches: the leaf's own test case is
  normative over its prose).

## Do NOT

- Do NOT re-land or re-commit — the commit is correct and attributed.
- Do NOT `git stash` your whole tree to "prove" the baseline: on a
  branch where HEAD references sibling WIP symbols (e.g. a method a
  sibling's uncommitted change defines), `git stash` (all) breaks the
  build — HEAD alone does not compile. Scope any stash-based A/B to YOUR
  file list, or better, run the suspicious tests A/B/A (current / your
  diff stashed / restored) before attributing failures to yourself.
- Do NOT treat a one-off suite failure in a parallel-load window as your
  regression: full suites running concurrently with sibling rebuilds
  flake. Two consecutive green focused runs of the exact failing tests =
  flake; record it and move on. If it recurs on the focused re-run, THEN
  do the A/B stash on your file list.

## Also this session: sibling-edit warnings are advisories, not stop signs

The patch tool flagged "file was modified by sibling subagent but this
agent never read it" mid-edit. Protocol: re-read the target region
immediately, confirm your hunk is disjoint, proceed. The sibling's edit
was in a different region of the same file; re-reading the specific
region beats re-reading the whole 3k-line file. Corollary: after several
sibling edits, `gofmt -l` may flag lines you never touched — attribute
the hunk (`git diff` + region knowledge) before reformatting; never
gofmt a sibling's WIP region.
