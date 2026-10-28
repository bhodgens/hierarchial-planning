# Meept plan trees (flat dir)


When to use: executing or authoring meept-style flat plan directories.
Lesson: scanner skips dot-dirs and archive/; flat trees need hand-verified leaf headings.
Meept stores plan trees in **one flat directory**:

`docs/plans/<tree>/master.md` plus `NN-name.md` leaves.

No per-leaf subdirectories. The compliance scanner may warn `no subdirectories found` and still print `ALL TREES COMPLIANT: True`. That warning is expected.

Headings: `## Child Index` (not Child Document Index). See `references/compliance-headings.md`.

Canonical location is `docs/plans/`, not only `.hermes/plans/`. A short pointer in `.hermes/plans/` is optional.

If the user says implement / implement the plan and this tree does not exist yet, **author the tree**. Do not start feature files. Halt on "stop" / "we're planning". Leave aborted WIP for leaf 01. Details: meept-development `references/plan-before-implement.md`.

## Compliance scanner on flat trees: run it on the PARENT dir

Running `check_template_compliance.py docs/plans/<tree>` directly treats the tree
as a "forest root" and prints `(forest root): OK` while SKIPPING all leaf checks.
Flat meept trees must be scanned from the parent so the tree is a subdirectory:
`python3 .../check_template_compliance.py docs/plans --strict-leaves | grep <tree>`.
Verified 2026-08-29 (wikiskill-skill-state: the direct run reported compliant with
zero leaf rows scanned; the parent run checked all 6 leaves for real).

Invoke the scanner with an absolute script path and run it from the repo
root in the SAME command (`cd <repo> && python3 ~/.hermes/.../check_template_compliance.py docs/plans --strict-leaves`).
The persistent shell cwd drifts across a long session — each terminal call
keeps the previous `cd` — and a relative `docs/plans` then fails with
`ERROR: docs/plans is not a directory` even though the path is correct
relative to the repo (observed 2026-09-04, chat-dispatch-ux).

## Unexported-type wiring contracts block the wiring leaf

When a leaf's contract requires another package to CONSTRUCT a type your package
keeps unexported (real case: `agent.TraceWriter` takes the unexported
`traceRecordMirror`, so the daemon wiring leaf cannot build an adapter), the wiring
leaf is structurally blocked. Pick one AT AUTHORING TIME: (a) plan an exported
setter/adapter seam in the owning package's leaf, (b) define the interface over
exported shapes, or (c) explicitly accept the gap and document it in the wiring
leaf's Deviations — never widen the owner's API mid-execution.

## Forest-level reference docs inside docs/plans

`docs/plans/llm-resilience-forest/` (2026-08-31) introduced a FOREST:
`master.md` root + `<tree>/` subdirectories + forest-level siblings
(`DECISIONS.md`, `SHARED-CONVENTIONS.md`). The scanner treats every
non-master .md in a tree dir as a leaf, so the siblings need leaf markers
("Do NOT commit" line + Self-Verification checklist) to pass, and the root
master needs full orchestrator sections (Interface Contracts, Child Index,
Dispatch Protocol, Review Checklist, Coding Conventions, Integration Test
Plan) even though it delegates execution to per-tree masters. Doing this
keeps a forest scannable from the parent dir in one pass. Before that
forest, forests would either live outside `docs/plans/` or fail the scan.
Full recipe: `references/forest-root-scanner-compliance.md`.

## Scanner skips (2026-09-01)

`check_template_compliance.py` now skips dot-directories (`.claude/` etc. —
tooling state, not trees) and `archive/` (historical plans kept deliberately
non-template; archived plans are cross-referenced by docs elsewhere, e.g.
`docs/implementation-gaps-review-2026-06-10.md` links archive paths). Don't
"fix" docs in those dirs to satisfy the scanner; the skip is intentional.
Audit-record docs that land INSIDE a forest (e.g. `ARCH-AUDIT-<date>.md`)
still need leaf markers to pass the scan — give them a "Do NOT commit
independently" line and a short Self-Verification Checklist stating they
are documentation, not dispatchable leaves.

## Executing a tree authored in a prior session

Run the execution-readiness audits first — see
`references/execution-readiness-audits.md`. Plans decay (line drift, renamed
symbols, unresolved "if X..." conditionals); a 3-subagent read-only audit
pass before dispatch is cheaper than implementation agents chasing dead
anchors. The 2026-08-31 llm-resilience-forest pass caught 16 line-anchor
drifts, a same-name/different-signature method collision that would not
have compiled (Resolver.ResolveRef), per-alias state that could not deliver
a cross-alias contract, and an UNWIRED production pipeline the whole first
tree depended on (HookRegistry.RunPrepareNextTurn had zero production
callers). Fold verified corrections into the plan docs BEFORE dispatch, and
record the audit itself as a sibling doc in the forest (e.g.
`ARCH-AUDIT-<date>.md`).

## Multi-session execution: reconcile tracking from git, fence dirty files

If sibling sessions may be executing the same forest concurrently (meept
2026-09-01/02: THREE sessions ran one 5-tree forest), read
hierarchical-plan-execution
`references/sibling-plan-execution-collision.md` before dispatching.
Key rules: baseline recon (`git log` leaf-name match + dirty-file
inventory), fence any file a sibling holds modified, frame
possibly-landed dispatches as VERIFY-against-spec (2 of 3 dispatches
correctly returned "already implemented, zero changes"), and reconcile
tracking tables from `git log` commit hashes — a PENDING row does not
mean the work is not on HEAD.

## English-only repos: scrub CJK from plan docs before committing (2026-09-04)

Some models drop CJK fragments into generated English text ("非-string",
"某些", "base :=源"). Meept's ascii pre-commit hook
(`.githooks/pre-commit-ascii`, CJK/Hangul/fullwidth class scan, committed
2026-09-04) fails such commits. Before committing a plan tree: scan the
tree docs for CJK ranges and translate one-for-one — comments, error
strings in test snippets, doc headers ("##所有 Issues" → "## All Issues",
"base :=源" → "base := src"). Commit the scrub with the tree or
separately. Also check the hook's own source: a hook written to block CJK
must not carry CJK examples in its header comment (eat own dog food).
Note for the hook author: a blanket >127-byte ban fails hundreds of
legitimate files (em-dashes, arrows, box-drawing in hook output); target
the CJK/Hangul/fullwidth Unicode classes and allowlist genuine unicode
fixtures instead. Mark binary assets (fonts/images/db/minified data) in
.gitattributes — a font TTF whose glyph-name metadata contains CJK passes
git grep -I as text otherwise. Scraped external dumps (.firecrawl/) get
allowlisted, never translated.

## Parent-referencing leaves: pin relative dependencies at authoring time

Trees whose leaves depend on SIBLING leaves' output (e2e leaf asserting
prior leaves' behavior) must state the dependency direction in the Child
Index and dispatch strictly in commit order. A leaf asserting another
leaf's behavior cannot run until the dependency is COMMITTED, not just
IMPLEMENTED — uncommitted WIP in the dependency's files makes the
assertion verify against a moving tree (observed 2026-09-04,
chat-dispatch-ux leaf 10 vs leaves 01-06 WIP: transient build breaks,
two-phase bugs that resolved themselves).

## Ordering hazards: resolve at authoring time with a verified resolution

When a tree's leaves depend on daemon construction ORDER (e.g. a tool
needing a writer that initializeSkills builds AFTER the tools init runs),
the hazard must be resolved IN THE PLAN, not left to the implementing
agent. Pattern (observed 2026-09-05, skill-authoring-and-media-ingest):
state the verified current order in master Notes, give leaves a
tolerance contract (constructor accepts nil dependency, Execute returns
a clear "unavailable" error), give the wiring leaf ONE preferred
resolution (e.g. register at the end of the later init function) gated
on a passing wiring test — "preferred but never assumed". Put it in
master `## Open Questions` too so reviewers look for the test evidence.

## SKILL.md size limit blocks additive patches to huge skills

`skill_manage` patch/create REFUSES when the resulting SKILL.md exceeds
~100,000 chars — meept-development is over the line, so EVERY additive
patch fails (even net-negative rewrites fail while over). When a target
skill is that large, do not burn retries on the body: route new learning
into `skill_manage action=write_file` with a `references/<topic>-<date>.md`
support file instead (allowed while over the limit), and note the
skill-needs-splitting situation for the curator. Diagnose by reading the
error text — it names the character count.

## Auxiliary tree docs need leaf markers; read the strict scan UNFILTERED

Non-master .md files inside a tree dir (OPEN-QUESTIONS.md, audit
records, decision siblings) must carry leaf markers or `--strict-leaves`
fails: a "Do NOT commit independently" line plus a "## Self-Verification
Checklist" stating the doc is reference documentation, not a dispatchable
implementation leaf. Read the scan's FULL output — do not grep it to your
own tree: with your tree "OK", `ALL TREES COMPLIANT: False` still means a
SIBLING tree fails, and failing aux docs may only surface on the
unfiltered pass (2026-09-05: four OPEN-QUESTIONS.md docs across four
trees; two invisible in the target-scoped run).

## Sibling sessions execute your authored tree; pathscope your commits

Trees get implemented by OTHER live sessions between your turns
(2026-09-05: skill-authoring-and-media-ingest leaves 01-05 implemented,
wired, and committed by a sibling while the authoring session was still
answering questions). On "was it implemented?": reconcile from
`git log --grep <leaf-keywords>` + the plan's Completion Tracking Table,
then verify code presence independently (symbol grep + scoped
`go test`) before answering — tracking tables and session memory both
lag reality.

Commit hygiene in that shared tree: stage and commit YOUR files in ONE
pathspec-scoped command (`git add <paths> && git commit -m ... --
<paths>`); it lands only the named paths even when a sibling's files sit
staged in the index, leaving theirs untouched. Beware the pre-commit
build hook's downstream sweep: it builds the whole working tree, so an
UNTRACKED sibling scratch file with a compile error fails YOUR
docs-only commit — check whether the failing file is staged or untracked
before touching anything. Execution-side collision rules:
hierarchical-plan-execution
references/sibling-plan-execution-collision.md.

## Scoped commit pitfall: pathspec commit FAILS on untracked files

The pathspec form `git commit -m ... -- <paths>` commits only paths git
already knows (staged or tracked); naming an UNTRACKED path errors with
"pathspec did not match any file(s) known to git" and commits NOTHING
(observed 2026-09-05: new plan-tree dir + report file). Sequence that
works: `git add <paths>` FIRST, then the pathspec-scoped commit. After
any failed attempt, verify with `git log --oneline -1` AND
`git status --short` — a failed pathspec commit is a no-op, but the
staged set may still hold sibling files from earlier; `git restore
--staged <foreign paths>` to drop them (keeps their worktree content).

## Stash cycles contaminate the staged index (shared tree)

`git stash -u` / `git stash pop` on a shared tree sweeps the sibling's
mid-edit files into your worktree AND, if staged after a pop, into your
index — a sibling's torn WIP (syntax error mid-edit) nearly rode into a
commit this way (2026-09-06 meept). Rules: after ANY stash cycle,
re-run `git status --short` + `git diff --cached --name-only` and
`git restore --staged <not-mine>` before committing. A dropped stash is
recoverable while dangling: `git stash apply <SHA-from-the-drop-output>`.
Full pattern:
shared-repo-parallel-agents
references/staged-index-contamination-and-no-verify-2026-09-06.md.

## --no-verify with in-message rationale when hooks fail on foreign code

Pre-commit gates can fail on COMMITTED sibling code (mutexio flagged
`t.Run` in test-table files from cb7d3e36 as I/O-under-mutex — analyzer
false positive; violation pre-existed at HEAD). When your staged delta
is trivial and verified (run the touched test yourself), and the hook
failure provably originates in foreign/committed code (confirm by
stashing everything and re-running the hook), commit `--no-verify` and
put the rationale IN the commit message: which hook, which files own
the violation, which commits introduced them, what you verified.
Silent bypasses are not OK; documented ones are the established
pattern on this repo (2026-09-06).
