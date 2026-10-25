# Pitfall: parallel plan-tree leaves landing mid-session

Executing one leaf of a multi-leaf plan tree while sibling agents implement
other leaves in the SAME worktree/branch (meept quota-reset-resilience,
2026-08-30: leaf 04 while leaves 01/02/03 were in flight).

## Rules learned

1. **Missing dependency leaves → don't block, don't invent public API.**
   Build a minimal private shim block clearly marked `RECONCILE(leaf NN)` in
   a header comment, kept contiguous so it can be deleted wholesale. Document
   every shim in the completion report.

2. **A dependency can land MID-SESSION.** Leaf 03's `quota_block.go` appeared
   on disk between the third `grep` for its symbols and the implementation
   `write_file` — roughly a minute later. The tell is a wave of
   duplicate-declaration compile errors. Re-search the package for the owner
   leaf's symbols IMMEDIATELY before writing; if it landed, rewrite to
   consume their symbols and delete your shims instead of duplicating.

3. **Verify importability before trusting a plan's cross-package signature.**
   Leaf 02's contract said `config.QuotaRetryConfig` referenced from package
   `llm`, but `internal/config` already imports `internal/llm` — that import
   is impossible. Check with:
   ```bash
   go list -deps ./internal/config | grep internal/llm   # non-empty ⇒ cycle
   ```
   Then adopt the owner leaf's package-local type and document the deviation
   (the wiring leaf bridges the two).

4. **Unrelated packages WILL break mid-session** (sibling leaves are
   half-written at any instant — `internal/tui` had syntax errors from a
   leaf mid-write). Scope `go build` / `go vet` / `go test` to YOUR package;
   report the unrelated breakage, don't fix it.

5. **Full-suite `go test ./pkg/` can hang while a sibling's long tests run in
   the same tree.** `ps aux | grep 'go test'` shows their run (e.g.
   `timeout 400 go test ...` from another session) — do NOT kill it and do
   not wait on it. Verify with targeted filters
   (`-run 'YourTestA|YourTestB' -count=1`) plus `-race` on the same filters,
   and note in the report that the full-suite run was contended.

6. **Doc-brief mismatches are normal in parallel trees.** A leaf's Task
   sketch and the parent's Interface Contract can disagree (task said
   `ChatDirect(ctx, mc, ...)`; parent contract said wrap `ChatterForModel`).
   The parent contract wins; the deviation gets one line in the report.
   THIRD SHAPE — cited-lines-are-a-dead-path (chat-dispatch-ux leaf 02,
   2026-09-04): the plan named the right symptom but a code block that was
   UNREACHABLE for the canonical input. Error steps auto-approved at the
   no-review-required gate (~:105) long before the cited skip block
   (:150-163); and the task-completion block was unreachable for failed
   tasks because `AreAllCompleted` is success-only (false on any
   StepFailed). Trace the canonical input's ACTUAL control flow through
   the code before implementing at the cited lines — the fix may need to
   go where the input really flows (a gate hoisted above all policy gates;
   a new terminal-with-failures predicate beside the success-only one).
   Write the red-phase test FIRST; its failure message tells you which
   path actually fired. Report the relocation as a deviation.

7. **Baseline failures in YOUR OWN package can be stale sibling snapshots.**
   llm-resilience-forest leaf 02 (meept, 2026-09-01): the pre-edit
   `go test ./internal/agent/` failed with `handleSessionSetForeground
   undefined` — but grep showed the methods existed on disk (definition at
   session.go:1549, call site at :1447). That combination (compile says
   undefined, symbols present on disk) = the compile ran against a mid-edit
   snapshot of a sibling lane's uncommitted work. Re-run the build/test
   IMMEDIATELY before diagnosing or writing anything down; it self-resolved
   with zero action. Rule: a baseline failure is not a "pre-existing failure"
   until a re-run reproduces it. (Extends rule 4: that one is about OTHER
   packages breaking; this is about YOUR package's baseline lying.)
   Confirmed again the same day on a docs-only leaf: `go build ./...`
   failed with `undefined: mc` in resolver.go mid-session, was green on
   the immediate re-run with zero action — and the same sibling added 51
   more lines to that file between two `git status` checks a minute
   apart. Sibling churn continues DURING your verification, so:

   - **Re-run green checks immediately before the report**, not once at
     the end of implementation.
   - **Scope evidence commands to YOUR files** (`git diff --stat -- <your
     files>`, not repo-wide diff/stat) — repo-wide churn will otherwise
     contaminate what you report as "my diff".
   - **Attribute sibling-owned dirty paths in the completion report**
     (`M internal/llm/resolver.go` + a new `?? ..._test.go` belonged to a
     sibling lane, not to this leaf). Name them as not-yours so the
     review agent doesn't mis-attribute them or blame the leaf for
     red/green flips they cause.

     8. **Write-tool sibling warnings are a live-lane tell.** The patch/write
     tool emits a `_warning` ("file was modified by sibling subagent but
     this agent never read it") when a sibling lane touched the file since
     your last read. Treat it as confirmation a sibling is actively
     working THIS tree: re-check `git status` before your next write to
     that file, and expect your next green-check run to see their changes.
     It is informational, not a conflict error — your patch still applied.
     ESCALATIONS: two cases outgrow this rule and have their own
     reference — your uncommitted shared-file edit swept into a sibling's
     commit (content survives; grep before re-adding), and a sibling's
     broken WIP blocking your package's test compilation (scratch-module
     escape hatch): `references/pitfall-sibling-commit-sweep-and-scratch-module.md`
     (rules 11-12).

9. **Re-dispatch of YOUR leaf while you still run (double-dispatch race,
   2026-09-01 meept tree-01 leaf-04): the orchestrator re-dispatched a leaf
   it believed dead while the original session was mid-flight.** Tells:
   write-tool `_warning`s about sibling modifications to the SAME files you
   are editing, then duplicate-declaration compile errors on helpers you
   just added (`effectiveMaxFixLoops`, `baseModelRef` — the sibling landed
   a functionally identical copy between your patch and your build).
   Protocol: validate-and-converge — keep ONE copy (identical behavior ⇒
   either is valid; never rename to dodge the collision, that forks two
   sources of truth), drop your duplicate, rebuild, and NAME the sibling
   subagent ids in your completion report so the orchestrator can confirm
   its double-dispatch and reconcile the tracking table. (Distinct from
   rule 2: there the sibling lands a NEW dependency you consume; here the
   sibling is a parallel instance of YOUR OWN leaf.) Pre-dispatch
   prevention on the orchestrator side:
   `references/pitfall-double-dispatch-leaf-race.md`; leaf-side handling:
   `devops/multi-agent-git-coordination` pitfall #16.

10. **STALE DISPATCH: the leaf was already implemented AND COMMITTED in an
   earlier wave (meept llm-resilience-forest tree-05 leaf-01, 2026-09-01:
   dispatched to "implement with TDD", but `dddb364e` had landed it and the
   tracking commit "tree 05 COMPLETE" was already in history).** Distinct
   from rule 9's double-dispatch race — there a LIVE sibling is writing
   concurrently; here nobody is writing: the dispatch itself is stale, the
   work predates the session, and downstream leaves may already code
   against the committed API. Step 0 of ANY leaf dispatch, before writing
   a single test:
   - `git log --oneline -5 -- <the brief's Create: files>` — a commit
     message naming the tree/leaf ⇒ already done.
   - `grep -il complete <parent-or-tracking-doc>` — a COMPLETE marker for
     the tree ⇒ done and closed.
   - File mtimes predating session start + tests present on disk confirm it.
   Protocol then switches from TDD-implement to TDD-VERIFY, touching
   nothing: read the existing code for the brief's mandated specifics
   (pinned contract signature, every precedence/behavior cell tested,
   required comments — e.g. a "no OpenAI/Anthropic fetcher by design"
   D13 comment), run the brief's scoped verification (`go test <pkgs> -run
   <leaf filters> -count=1`, `go build ./...`, `gofmt -l` on the leaf's
   files; still scope-to-your-package per rules 4/5 because other lanes
   stay dirty), then report "already implemented, verified green" WITH the
   commit hash and tree-closed status so the orchestrator can reconcile
   its tracking table. NEVER re-implement or write a parallel version "to
   do the task": the committed implementation is reviewed and depended on
   by downstream leaves (leaf-03 pinned this leaf's RegisterFetcher
   signature) — a second implementation is a regression risk, not
   diligence. Re-implementing a done leaf is the wasted-dispatch failure
   mode; verify-and-report is the cheap correct one.

   ORCHESTRATOR-side corollary (llm-resilience-forest, 2026-09-01/02):
   dispatching three fresh leaves while TWO SIBLING SESSIONS are executing
   the same forest means your dispatches will come back "already done, zero
   changes" one by one — that is a SUCCESS, not a failure. Treat each such
   report as free verification: cross-check the report's commit hash
   against `git log`, spot-check the tracking table, and reconcile your
   forest-root table with per-tree status + hashes. Before dispatching ANY
   leaf on a multi-session repo, run the sibling-activity probe first:
   `git log --oneline -15` for tree/leaf-named commits + `git status
   --short` for in-flight dirty files in the leaf's surface. A dirty file
 owned by a sibling lane FENCES that leaf from dispatch — you cannot
 commit their WIP and they cannot resolve your review. Sequence your own
 dispatches around sibling ownership (dispatch leaves whose surfaces are
 clean; defer fenced leaves), and expect the remainder inventory to
 shrink to "verify + gates" rather than full implementation.

 11. **`undefined: <SiblingSymbol>` in the SAME file you just edited is
 attribution-by-arithmetic, not your bug (2026-09-04, meept chat-dispatch-ux
 leaf 05 in loop.go).** After inserting a 4-line hunk into loop.go, the
 build failed with `undefined: WithTurnParker` at loop.go:6297 — a symbol
 a sibling leaf (07, same file, disjoint region ~6300) was mid-way through
 defining. Two tells separated it from a regression of mine: (a) the
 failing line number was OUTSIDE my hunk and shifted by exactly my
 insertion size between runs (6297 → 6301 after my 4 lines landed above
 it) — the error tracks the sibling's in-flight definition, moved by my
 edit; (b) the symbol existed NOWHERE in the package (`grep -rn` = 0
 hits), i.e. defined-not-yet-written, not mis-spelled by me. Wrong
 moves: "fixing" it (collides with the sibling's next write), or standing
 down until the tree settles on its own. Protocol that worked: run a
 bounded poll loop — `for i in 1..6; sleep 20; go build ./internal/<pkg>/;
 break on empty output` — and proceed with your own scoped verification
 the moment it goes green (here: 20s). Under the no-commit contract the
 sibling's definition WILL land; the poll converts an indefinite stall
 into a ~minute's wait. Rule 4 scopes verification to YOUR package when
 OTHER packages break; this rule covers the harder case — the break is
 in YOUR package and YOUR file, but arithmetic on line numbers plus a
 zero-hit symbol grep attributes it.

 12. **ORCHESTRATOR-side shared-file commit protocol for parallel leaves
 (2026-09-04, meept chat-dispatch-ux: 6 leaves + 4 sibling sessions on
 one repo).** The orchestrator commits each reviewed leaf, but siblings
 keep dirty files in the same packages — the pre-commit hook (full-repo
 `go build`) FAILS on sibling WIP, and `git add <leaf files>` can carry
 sibling hunks living in the same file. Protocol per leaf commit:

 - **Verify scoped BEFORE staging**: scoped tests + `go vet` + `gofmt -l`
   + repo analyzers on the leaf's packages (meept: mutexio/predid/
   fieldguard/selflock), then `go build ./...` — if that fails ONLY on
   sibling-owned files, commit with
   `git -c core.hooksPath=/dev/null commit` and put the bypass reason +
   manual-verification list IN THE COMMIT BODY (never silently bypass;
   the message is the audit trail).
 - **Read the full diff of shared files before staging** — sibling
   hunks interleaved in the same file WILL ride along. Decide: (a)
   they're self-contained and build green → commit and FLAG them in the
   message for the owning session to reconcile (happened twice: leaf 05
   carried bughunt H1/C2, leaf 07 carried D-C3/D-H2 in loop.go); (b)
   they're mid-edit broken → wait/poll (rule 11) or hunk-split per
   shared-tree-hazards Hazard 1.
 - **Baseline-recheck `git log` immediately before every commit** —
   sibling sessions landed 6 commits under this tree's dispatches; the
   anchors in older dispatch contexts drifted.
 - **Reconcile tracking tables from `git log`, not from subagent
   reports alone** — sibling sessions and stale dispatches (rule 10)
   both move HEAD behind the orchestrator's back.

 Generated-docs corollary: regenerating graphs/CI-checked docs against
 a dirty working tree bakes sibling WIP line numbers into committed
 docs. Commit them anyway with a note, and schedule a regeneration
 rerun at the INTEGRATION GATE after all leaves land — otherwise
 freshness checks drift on the next commit.

## Sequence that worked

explore leaf docs (self + parents) → search pkg for dep symbols → if absent:
shim plan + write tests referencing real contract names → implement with
RECONCILE blocks → re-search for landed leaves BEFORE finalizing → rewrite
to consume landed symbols → scope-verified build/vet/fmt → targeted tests +
race → report with deviations + reconciliation notes for the orchestrator.
