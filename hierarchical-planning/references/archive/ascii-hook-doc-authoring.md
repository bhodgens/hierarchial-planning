# Non-English Characters in Authored Docs (ASCII-Hook Interaction)


When to use: repos enforce English-only via a pre-commit ascii hook.
Lesson: scan plan docs for CJK fragments before dispatch; authored snippets are English-only.
Repos may enforce an English-only policy via a pre-commit ascii hook
(meept: `.githooks/pre-commit-ascii`, wired as pre-commit step 16/16;
policy born 2026-09-04 after CJK leaks like `非-string`, `某些`, `保持`,
`隐式状态` were found in Go comments and plan docs).

## The trap for plan authors

The hook scans STAGED files at commit time AND the whole tracked tree in
`--all` mode — which includes `docs/plans/**/*.md`. Plan trees authored
with stray CJK characters (or CJK inside code snippets / test-expectation
strings) will fail the commit LATE — at commit time or the next --all
scan — not at write time. The author never sees it during authoring.

## Rules for authoring in ascii-hook repos

1. NEVER use CJK characters in plan prose, code comments inside
   snippets, or test-expectation strings — not even as "examples of
   what to avoid." Worked example: leaf 06's test snippet carried
   `t.Errorf("unblock_at missing/非-string: ...")` — the example itself
   became a violation and had to be scrubbed post-hoc (meept commit
   4e5462c3).
2. Before committing a plan tree, run the repo's ascii check over the
   new files. If the hook supports it, use --all mode and grep the
   output for your tree's directory.
3. If a snippet legitimately needs non-ASCII (unicode-handling tests),
   the FILE belongs on the hook's ALLOWLIST — flag it in the leaf's
   Deviations section and let the orchestrator decide. Don't silently
   include it.
4. Transcription artifacts: delegated subagent summaries sometimes
   arrive with stray CJK glyphs injected mid-sentence (corrupted tool
   output, not authored content). Re-derive any quoted text from source
   before embedding it in plan docs.

## Detection recipe (repos without a hook yet)

```bash
# CJK/Hangul/fullwidth scan over tracked text files
git ls-files | grep -vE '\.(png|jpg|gif|ico|woff|ttf|pdf|zip|db|bin|mv2)$' | xargs -I{} python3 -c "
import sys, re
cjk = re.compile('[\u1100-\u11FF\u2E80-\u9FFF\uAC00-\uD7AF\uF900-\uFAFF\uFF00-\uFFEF]')
for n, line in enumerate(open(sys.argv[1], encoding='utf-8', errors='replace'), 1):
    m = cjk.search(line)
    if m: print(f'{sys.argv[1]}:{n}:{m.start()+1}: {line.strip()[:100]}')
" {}
```

Census of a live repo found 40k+ distinct non-ASCII chars — almost all
in binary-ish tracked files (minified animation data, .firecrawl
scrapes, font metadata) or legitimate typography (em-dashes, arrows,
box-drawing). A blanket `>127` ban is wrong; target the CJK/Hangul/
fullwidth SCRIPT ranges. Binary detection: `git grep -I -e '' -- <file>`
(rc 0 = text, rc 1 = binary).
