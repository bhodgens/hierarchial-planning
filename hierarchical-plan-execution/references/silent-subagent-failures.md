# Silent Subagent Failures — Detection and Recovery

## The Inverse Failure: "FAILED/timeout" status but ALL files actually written

The mirror-image trap (rebellion leaves 01/02, 2026-08-07): a subagent hits
upstream model capacity (HTTP 503) or the 600s wall-clock timeout, and the
delegation result says `status=failed` / `status=timeout` with
`(no summary — API call failed after 3 retries)`. **Do NOT re-dispatch
blindly.** A subagent that "failed" on its FINAL SUMMARY call may have already
completed every file write, run the full test suite, and only died producing
the report — the leaf-01 subagent in that session created all 3 env .tres +
6 materials + the test file and the GUT suite went 183/183, all before its
summary call 503'd.

### Detection Protocol (run BEFORE re-dispatching)

```bash
git status --short          # new/modified files are the real progress signal
ls <expected dirs>          # e.g. resources/environments/, resources/materials/
git diff --stat <expected files>
```

- Files present + tests passing → the leaf is DONE; skip re-dispatch entirely.
  Verify the artifacts (run the suite, review the diff for scope creep), fix
  any small gaps yourself, and move to tracking updates.
- Files present but incomplete/flawed → finish the small remainder directly
  (main model), don't burn another dispatch round on a flaky provider.
- Nothing present → now re-dispatch.

### Why this matters

Re-dispatching after a successful-but-unreported run wastes a full delegation
round AND can collide: the fresh subagent sees the same files, rewrites or
duplicates them, and you get sibling-overwrite churn. The file tree is ground
truth; the status string is not.

### High API-call-count timeout = work was done (2026-08-07 rebellion tree 18)

A timeout with a HIGH API-call count (25-38 calls in 600s) almost always means
the subagent completed its file writes and got stuck on a slow operation —
typically a GUT headless test run (`godot --headless` can take 60-120s) or a
slow model response on its final summary. The files ARE on disk.

**Detection: API-call count is the signal.**
- 0-5 calls + timeout → likely stuck early, minimal work done. Check filesystem
  but expect to re-dispatch.
- 25-38 calls + timeout → almost all file writes completed. Salvage, don't
  re-dispatch. The timeout was on a late verification/summary step.

**Orchestrator salvage flow (validated on 2 timed-out leaves in one wave):**
1. `ls` all expected output files from the leaf spec.
2. Run pytest directly (seconds) — confirms the Python code works.
3. `grep` for stubs/TODOs/pass-bodies in the code files.
4. `grep` for key implementation signals (e.g., `sin|cos|phase|stride` for gait
   math — confirms the function body is real, not a stub).
5. If a test file is missing (common — the subagent ran out of time before
   writing the test), write it directly from the orchestrator context.
6. Run the test — if assertions mismatch the implementation's naming
   conventions (uppercase vs lowercase status strings, KeyError vs ValueError,
   field name casing), fix the TEST to match the implementation when the
   convention is cosmetic.

**Convention-mismatch fix pattern:** When the orchestrator writes a test for
subagent code, the test's assumptions about naming/casing/exception types may
not match what the subagent chose. Examples:
- Test asserts `status == "QUEUED"` but implementation uses `"queued"` → use
  `.lower() == "queued"` in the assertion.
- Test asserts `pytest.raises(ValueError)` but implementation raises `KeyError`
  → use `pytest.raises((KeyError, ValueError))`.
- These are cosmetic convention choices, not bugs. Fix the test, not the
  implementation, unless the convention violates a project-wide standard.

## The #1 Silent Failure: Rate-Limit (429) with Zero Output

Subagents that exhaust their API rate limit (HTTP 429 Too Many Requests) during delegation can return `status=completed` in the async delegation framework while having written **zero files**. The returned summary may contain plausible-sounding descriptions of what was "created."

### Detection Protocol

After every `delegate_task` returns with `status=completed`, run a file-existence check BEFORE reviewing:

```python
import os
expected_files = ["path/to/file1.py", "path/to/file2.sh", ...]
for f in expected_files:
    if not os.path.exists(f):
        print(f"MISSING: {f}")
```

Or via shell:
```bash
for f in expected/file1 expected/file2; do
    [ -f "$f" ] && echo "OK: $f" || echo "MISSING: $f"
done
```

### Red Flags

- Subagent summary says "All N files created" but directory is empty
- Subagent took unusually short time (under 30 seconds for a multi-file task)
- Subagent summary contains the phrase "API call failed" or "rate limit"
- File count on disk doesn't match the claimed count

### Recovery

1. Re-dispatch with the same context. The rate limit may have cleared.
2. If the re-dispatch also fails, wait 60 seconds and retry.
3. For large leaves, consider splitting into smaller tasks that complete within rate-limit windows.
4. Do NOT mark the leaf as implemented or commit based on the returned status alone.
5. **In-session fallback (humanplusone session, 2026-08-04):** If re-dispatch also fails with 429, the orchestrator (main model) can often do the fix directly using `execute_code` or `patch`. This is faster than waiting for rate limits to clear. The fixes are well-defined from the review/leaf spec — read the target file, apply targeted edits via Python string replacement, write back. This turned a rate-limit wait into a 5-second in-session fix for 19 provisioning issues and 10 Docker compose issues in one batch.
   - Works best when: the fixes are targeted edits (string replacements, config additions) not full module writes
   - Use `execute_code` with Python for multi-file batch edits (read → replace → write per file)
   - Run validation (pytest, bash -n, json.load) afterward to confirm correctness
   - Commit the same way you would after a subagent return

## Silent Death: NO notification at all (meept 20260829-harness-eval leaf 07)

A third variant beyond timeout and 429-zero-output: the subagent process dies
without ANY async batch message — no `status=completed`, no timeout report.
It may have landed a COMPLETE, test-green edit set before dying.

### Detection (when the expected notification never fires)

1. `process(action='list')` — empty means nothing is still running.
2. `git status --porcelain <leaf's owned paths>` — modified/untracked files
   matching the leaf's file list = work landed.
3. `go test <pkg> -race` (or the package's suite) — green means the work is
   whole, not partial.

### Recovery (orchestrator completes the leaf)

1. Read the diff file-by-file against the leaf spec — never commit landed
   code sight-unseen just because tests pass (missing-scope trap).
2. Run the package suite yourself.
3. Fix gate trips in-session (this instance needed a U1000 deletion — the
   dead function a hook refused, nolint or not).
4. Commit under the leaf's own message; tracking-table note:
   "subagent died silently; orchestrator verified+committed".

Do not re-dispatch: a fresh subagent would collide with the landed files.

## Other Silent Failures

### Subagent writes to wrong path
- Always verify files exist at the EXACT paths specified in the leaf document
- Subagents sometimes create files in their CWD instead of the project root

### Subagent writes partial output
- Some files exist but not all. Check the COMPLETE file list, not just one or two.
- Partial output is harder to detect — the subagent may have written 3 of 5 files before failing

### Subagent overwrites existing files
- Check `git status` after each subagent return. Unexpected modified files indicate the subagent touched files outside its scope.
