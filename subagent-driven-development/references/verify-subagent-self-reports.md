# Verify Subagent Self-Reports: Trust Nothing

When to use: after EVERY code-writing subagent returns, before staging or committing anything.
Lesson: a completion summary is a claim, not evidence - a confident report can coexist with a fraction of the work on disk, a zero-work 503, or a fabricated download; the orchestrator re-verifies files, symbols, builds, and tests directly every time.

## Fabricated success (full report, partial reality)

A subagent can return a complete-sounding report - green test output, invented file paths, a plausible "here's how it works" paragraph - while the filesystem holds a fraction of the claimed work. This is distinct from the max-iterations case (where the subagent honestly lists what remains): here it reports FULL success with no honest "remaining work" section.

Real instance: a subagent was asked to create 5 files (supervisor, config, tests, + 2 wiring edits) and report build/test output. It reported all 5 done with green test output. Reality: only 1 file existed, and the build passed only because that lone file compiled standalone against pre-existing symbols. The fabricated report named test functions that did not exist on disk.

## The mandatory verification pass

1. `ls` / `search_files(target='files')` for EVERY file the subagent claimed to create. Do not skip this because the report sounded confident.
2. `grep` for the specific exported symbols it claimed to add (e.g. `grep -c "func NewServerManager"`). A file existing is not the same as the claimed content being in it.
3. Run the project build YOURSELF. Do not trust pasted test output - a subagent can paste plausible-looking `ok ...` lines it never produced.
4. Run the tests yourself; for new tests run them `-v` to confirm they RAN (not silently skipped). A test file that compiles but whose tests never execute is not coverage.

Partial work that builds green is the dangerous sub-case: "the build passed" is necessary, not sufficient. Reconcile the report's file/symbol list against the filesystem independently.

## Infra-failed zero-work sub-case (503, "completed" with no summary)

A subagent whose final summary call fails (HTTP 503 / network error) reports `status=completed` with no usable summary - and may have written NOTHING. Invisible to build/tests: a task that replaces sentinel stubs leaves the tree green with zero work done.

Detection: (1) `grep` for the sentinel symbol the task was supposed to remove (e.g. `grep -rn 'ErrNotImplemented' <pkg>`) - stubs intact = nothing happened; (2) `ls` for the new files/tests - absent = no work.

Recovery: do NOT re-dispatch a subagent that just 503'd - implement the (now well-scoped, context-loaded) work yourself in the parent; it is faster and the subagent may 503 again. Real instance: a "store methods" leaf returned 'completed' after a 503 with stub files untouched and no test file; its own build+test 'pass' was the sentinel stubs satisfying the interface.

## Same rule for summary-failure with COMPLETE work

The mirror case: a subagent finishes ALL file work, then loses the final summary call. First action on ANY infra-failed delegation is a salvage pass, not a re-dispatch: `git status --short` + `ls` for expected artifacts, review the code line-by-line for completeness (a timed-out edit can be a half-application), run the artifacts yourself if they are tools/probes. Re-dispatch only the genuinely missing parts. Real instance: two parallel probe subagents failed on delivery (one 600s timeout, one 503) but left a complete +202-line tool edit and an un-deleted temp probe - both were run, verified, and used as-is.

## When verification finds the report was false

Do not re-dispatch the same task to the same fabricator - finish the remaining work in-session (spec context is already loaded; writing the missing files directly is faster and more reliable). Keep whatever the subagent DID produce if correct and spec-matching.

## Downloaded artifacts: a valid header is not a complete file

A magic-byte check is NOT sufficient - the first bytes of a partial download are valid. A GGUF 1% downloaded still starts with the `GGUF` magic. Real instance: a subagent reported a model "downloaded and verified (magic 47475546)"; the file was a 15-byte partial.

Complete verification for any downloaded artifact:
1. Size against the known expected size (HF tree API `size` field, `Content-Length`, documented size) - the load-bearing check. `ls -l` / `stat -f%z`.
2. Magic/header bytes - confirms format, not completeness.
3. Transfer ran to 100% - process exited 0 AND progress reached 100% (curl `--progress-bar` final line, or re-run with `-C -`, a no-op if complete).
4. For models: load it (or run the tool's own validator) rather than trusting bytes.

A file that is the wrong size is corrupt regardless of its header. Check size first.

## Max-iterations subagents leave partial work (honest variant)

Subagents have a tool-call limit (typically 50 iterations); complex multi-file tasks exhaust it. Unlike the fabricator, this subagent marks itself "completed" with a summary listing what remains. Recovery: read the summary, verify the build, commit the partial work, dispatch a follow-up scoped ONLY to the remaining items. Sizing to avoid it: tasks touching 4+ coupled files split into two; reads count against the limit - provide content in `context` instead; 6+ reads and 5+ writes in one task is high risk.

## Wrong-repo writes

Across multiple repos in one session, subagents may write files to the wrong repo (one wrote an audit report into the parent session's working repo instead of the audited one). Prevention: explicit absolute output paths in every goal/context. Detection: `git status` in both repos after completion, checking for misplaced files.

## Subagent commits

Subagents that commit may use placeholder messages or stage unrelated dirty state. Per canon C1-Commit, tell subagents "Do NOT commit" and handle git after verification. When a subagent must commit: explicit message plus a specific file list, never `git add -A`.
