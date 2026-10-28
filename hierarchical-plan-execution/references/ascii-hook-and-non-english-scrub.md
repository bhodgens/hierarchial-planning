# Aascii hook and non english scrub
When to use: content-pattern hooks + non-English scrub.
Lesson: census before policy, staged-file scanning, one-for-one translations, grep your own hook.

# Non-English character scrub + ascii pre-commit hook (meept, 2026-09-05)

ADDENDUM (2026-09-08, classifier campaign): a multilingual TEST CORPUS is
the same allowlist case as unicode fixtures — an adversarial corpus with
an intentional Japanese/gibberish OOD case tripped the hook at commit
time (ascii-check FAIL naming the exact file:line). Fix in one step: add
the exact corpus path to the ALLOWLIST array in .githooks/pre-commit-ascii
(done: testdata/eval/classifier-adversarial-corpus.json5) and state in
the commit message WHY the non-English data is intentional. The hook
failure output alone is enough to discover both the file and the fix;
don't translate the fixture — the whole point of the case is that it is
non-English input.

Session context: user asked for a pre-commit hook that fails commits
containing non-ASCII/English characters, then to scrub the grandfathered
violations. Executed in the meept repo. The design decisions generalize
to any "block bad content pattern X in staged files" hook request.

## Design: census BEFORE policy

Run a full-tree census of the offending pattern FIRST and shape policy
from what actually exists. A blanket rule ("no byte >127") failed a
census with hundreds of legitimate hits (em-dashes, arrows, box-drawing
chars in docs and hook output). The hook that shipped targets CJK
ideographs/Kana/Hangul/fullwidth forms only — exactly the leak class
observed (non-string, 某些, 保持, 隐式状态).

Generalizes: the hook's deny-set should be the smallest set that covers
observed leaks, not the largest set the user's phrasing implies. Report
the census to the user and let the policy follow.

## Hook mechanics that worked

- Staged-files-only scanning (`git diff --cached --name-only
  --diff-filter=ACMR`): historical violations "fail only when next
  modified" — the debt cleans itself incrementally without a giant
  flag-day commit. Failure output names file:line:col + text.
- Binary skip via `git grep -I` heuristic; but ONE binary (a font TTF)
  passed text detection and tripped CJK ranges in its glyph-name
  metadata → fixed properly with `.gitattributes` marking
  fonts/images/db/minified data `binary` (also improves diff/merge).
- Allowlist array in the hook for reviewed CJK-legitimate files (unicode
  test fixtures, docs about unicode handling) + scraped external dumps
  (.firecrawl). Keep entries exact-path, minimal.
- The hook scans STAGED files; a `--all` mode exists for repo census
  (`pre-commit-ascii --all`).
- Wire as sub-hook into the repo's numbered pre-commit chain and renumber
  the `[N/15]` progress labels to `[N/16]` — forgetting the relabel is
  the kind of drift reviewers notice.
- Detection regex (python): ranges `\u1100-\u11FF \u2E80-\u9FFF
  \uAC00-\uD7AF \uF900-\uFAFF \uFF00-\uFFEF` with per-line
  file:line:col + snippet output.

## Scrub pass pattern

Translate one-for-one, not paraphrase: 隐式状态→"implicit state",
竞品→"competitor", 数据结构→"data structures", `base :=源`→`base := src`.
Re-run the affected packages' tests when Go comments change (here:
compress + preferences, both ok). Eat-own-dog-food pass: grep the new
hook's own header for the pattern it blocks — the first draft cited CJK
examples in its comment and tripped itself.

## End state

`--all` scans 4,391 tracked files, 0 violations, exit 0. Remaining CJK =
3 allowlisted files + binary assets (by design).

Commits: hook+wire ff6237be, scrub 33ab0bf7, gitattributes dd824068,
firecrawl allowlist d091da77, self-scrub 0c1034d3.
