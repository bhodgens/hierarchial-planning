# Parallel leaf execution: orchestrator commitments, hook interference, agent strays


When to use: orchestrator-side mechanics during parallel leaf execution.
Lesson: leaf-return fixes, commit procedure under hook interference, known-limitation ledger.
Condensed from the meept grok-bot-gap forest execution (2026-09-05): 4 trees,
12 leaves, 3 leaves in flight concurrently, ~20 commits. Read alongside
wave-execution-patterns.md — this covers the ORCHESTRATOR-side mechanics that
pattern's implementation notes leave out.

## Orchestrator-side fixes you will make on leaf returns

Leaf agents stop at scope boundaries by design (STOP protocol) and leave
orchestrator-owned gaps. Expected fixes on return, all quick:

1. **Registration/wiring lines outside the leaf's 3-file bound.** A leaf that
   adds a new Tool in package A cannot also register it in the daemon
   (package B, on the no-touch list). It reports the exact line and location;
   the orchestrator adds the one-liner, builds, commits with the leaf.
2. **Leaf-literal test fixtures that don't survive contact with reality.**
   Session examples: a redactor test fixture with `«redacted:sk-…»` that the
   real `sk-` pattern (32+ alphanumerics, no ellipsis) ignores; a test loading
   a superseded row via GetByID when the pre-existing `is_current` filter
   makes that impossible. Fix the test/mechanism per the report, keep pinned
   assertions, note it in the commit body.
3. **Errcheck/ignored-error blockers.** The pre-commit hook blocks NEW `_ =`
   sites including `defer func(){ _ = x.Rollback() }()`. House fix (from
   internal/agent/park_store_sqlite.go): check `rerr != sql.ErrTxDone`,
   log otherwise. Never nolint — hooks may ignore the directive.
4. **Stray artifacts**: probe directories agents created for empirical checks
   (`internal/auditlog_tmp/`), untracked and harmless. Delete before staging.
   NOTE: if the user denies the `rm`, leave the dir untracked and move on —
   do not retry or route around a denial; flag it in your report instead.

## Commit mechanics under hook interference

- The 16-check pre-commit hook builds STAGED packages but also runs repo-wide
  checks (setter nil-safety runs the builtin tools test binary). A PARALLEL
  SESSION landing its own commit mid-verify can break YOUR commit with an
  error in a package you never touched (session: pdfReadResult undefined
  appeared, then vanished when the owning session committed 49841775).
- Protocol: (a) confirm the failure is not in your staged files; (b) re-run
  your package tests; (c) commit YOUR files only with `--no-verify`; (d) say
  so in your report. This is sanctioned — do not sit blocked on someone
  else's transient.
- Stage exact file lists, never `git add .` — concurrent sessions make
  catch-all staging commit foreign work.

## Generated-docs churn

`make docs-generate` regenerates ALL 11 reference files, not just the one
your leaf touched — line-number drift in topology JSON from any code
movement. Commit only the file(s) belonging to the leaf
(`docs/reference/generated/<pkg>.md`); leave pre-existing working-tree
churn (`docs/generated/bus-topology.*`, research files) untracked/untouched
unless it is yours.

## Known-limitation ledger

When a tree deliberately defers a surface (RPC handler for a new CLI command,
Q4-style follow-ups), verify the shipped piece works end-to-end where
possible (session: live daemon round-trip proved flags parse and the daemon
answers method-not-found — expected until the handler lands), and record the
pending piece in the todo list as an explicit end-of-run follow-up item so it
survives the session.

## Shared-file serialization + review discipline (meept research-audit-tools tree, 2026-09-05)

Second session same day, 1 tree / 7 leaves / 5-agent Wave 1. Three patterns
that complement (not repeat) the sections above:

1. **Shared-file registration leaves serialize.** Leaves appending blocks to
   the SAME file (components.go registration) are NOT parallel even when
   logically independent — the earlier leaf's block defines the anchor point
   the later one is told ("immediately after `registry.Register(pdfReadTool)`",
   plus "a prior agent modified this file — read the current region first").
   Everything else stays parallel. Also: mid-wave the whole package is
   transiently red from a sibling leaf's TDD RED phase (`undefined:
   extractPDFText` from a landed test file whose impl hasn't landed) — gate
   per-leaf verification on targeted `-run` filters, full-package run only at
   review/integration.
2. **Trust nothing in the return summary — verify with primary sources.**
   (a) Re-run the targeted tests yourself (cheap; catches the "green at
   agent-exit, broken now" case). (b) When a leaf reports API drift from your
   brief, confirm via `go doc <pkg>` before accepting — once the brief was
   wrong and the agent right (pdf ReaderAt), but the check is what makes
   accepting it safe. (c) License gates: read the module-cache LICENSE
   yourself (`$(go env GOMODCACHE)/<mod>@<ver>/LICENSE`), never pass the
   verdict through. (d) Read the actual implementation file for frozen-seam
   conformance, not just the summary's word "verbatim".
3. **Incremental commits keep a mixed worktree legible.** Commit each leaf
   (or wave) as soon as REVIEWED — stage exact file lists. With a sibling
   session committing to main mid-run (3 foreign commits landed during this
   tree), small per-leaf commits make foreign-work triage a `git log` glance
   instead of an archaeology dig. When a foreign uncommitted file breaks the
   shared package build (their TDD RED), verify your scope builds+tests in
   isolation, do NOT touch their file, and note the transient in your status
   report.