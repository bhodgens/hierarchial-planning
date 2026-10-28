# Ssequential file edit clobber
When to use: scripted edits clobber concurrent writes.
Lesson: execute_code edit races and read-modify-write hygiene.

# Sequential same-file edit clobber (execute_code / scripted edits)

## The failure mode

Making TWO sequential content replacements on the same file inside ONE
script (execute_code or a shell heredoc chain) where the second replace
reads the file content ONCE at script start and writes the whole file back:

1. Replacement A mutates the file (read src → replace → write).
2. Replacement B was prepared against the ORIGINAL src string and writes
   the ENTIRE file back — silently reverting A.

Result: A appears applied (tool reported success), is then destroyed by B,
and nothing errors. Detected only when a later test panics on exactly the
guard A was supposed to add.

Real case (2026-09-01, skill-evolver tree): nil-guard fix applied to
verifyUsage() via read-modify-write, then a second read-modify-write in the
same script for a different hunk used the stale pre-guard read and
rewrote the file, dropping the first fix. The nil-guard regression test
then panicked at the exact line A had guarded.

## Rules

1. ONE content mutation per script invocation per file. If you need two
   hunks, either (a) do both replacements against a single fresh read and
   write ONCE, or (b) split into separate script calls, re-reading from
   disk between them.
2. NEVER write a whole file from a string that was read before an earlier
   write in the same script. `src` captured at t0 is stale at t1.
3. After ANY scripted write, VERIFY the intended bytes are on disk
   (`grep` for the new marker) before moving to the next dependent change
   — tool success means the syscall succeeded, not that the content
   survived later steps in the same script.
4. When a regression test panics on a guard you "already added", check the
   file content FIRST before assuming the guard logic is wrong — the guard
   may have been clobbered, not faulty.
5. The patch tool (anchored old/new strings) is safer than scripted
   whole-file writes for multi-hunk work: each patch re-reads current disk
   state and fails loudly when the anchor is gone instead of silently
   reverting siblings.

## Related

- hierarchical-plan-execution → references/pitfall-sibling-git-restore-revert.md
  (a DIFFERENT revert actor: sibling agents, not your own script).

## Patch-tool backslash fidelity — the diff display is NOT byte evidence (2026-09-04)

Rule 5 above says anchored `patch` beats scripted whole-file writes — still
true, with one large caveat learned editing a bash grep pattern
(`'hello\.txt\|hello\\.\\.txt'` in scripts/e2e-naive-user-chat.sh):

The patch tool transmits `old_string`/`new_string` backslashes LITERALLY
(what you type must byte-match the file), but the DIFF rendered in the
tool RESULT over-escapes backslashes (doubles them). The diff display
therefore CANNOT be used to count backslashes or confirm a pattern line
is correct. Two consecutive "successful" patches landed wrong variants
(over-escaped: pattern required literal backslash chars in the reply
text; then one hunk under-escaped) — each looked fine in its own diff.

Byte-level verification protocol (what actually worked):

1. Authoritative ORIGINAL bytes: `git show HEAD:<path> | grep -n <anchor> | cat -A`
2. Working-tree bytes: `awk 'NR==<line>' <path> | od -c` — od renders each
   backslash as an individual `\` character; count them, don't eyeball.
3. Final proof: `git diff <path>` — a pattern-bearing line that appears as
   CONTEXT (no +/- prefix) is byte-identical to HEAD. If your edit was
   supposed to CHANGE that line and it shows as context, the change did
   not land; if you were restoring HEAD's exact bytes, context is success.
4. Never conclude byte fidelity from the patch result's diff rendering.

Applies to any regex/backslash/escape-heavy line: shell grep patterns,
JSON-escape fixtures, sed replacements, string literals with quoted
backslashes.

