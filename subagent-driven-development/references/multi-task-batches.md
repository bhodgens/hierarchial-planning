# Multi-Task Batches With Independent File Sets

When to use: several distinct user workstreams run in one session via parallel subagents.
Lesson: batch by file set with one writer per file, queue follow-ups instead of touching a running agent files, and guard protected literals and sourced tables.

Pattern for orchestrating several distinct user workstreams (e.g. "update the
marketing site, rename product wording through the docs tree, and edit the
README") in a single session using parallel subagents.

## Dispatch as one batch

Send all workstreams as one `delegate_task` call with `tasks: [...]` rather
than sequential single dispatches. Each array entry gets its own isolated
subagent with its own terminal session. On this account the concurrent-child
limit is 10 and nested orchestration is enabled (max_spawn_depth=3).

## Race rule  -  one writer per file

Two subagents must never hold the same file open for writing.

- Before batching, partition work by FILE SET, not by topic. Two agents editing
  README.md concurrently = lost writes.
- If a follow-up user request lands on a file a RUNNING subagent owns, do not
  apply it inline. Sequence it:
  1. Read the target section now for planning (reads are safe).
  2. Tell the user the change is queued behind the running agent.
  3. Dispatch the edit as a new delegation after the owning subagent completes.
- Example (meept.dev session, 2026-09): site rebuild agent owned
  `meept.dev/*`, docs-rename agent owned `README.md` + `docs/`. A follow-up
  "add status icons to README's comparison table" arrived mid-run; it was
  planned immediately (read the section, choose glyphs, decide icon source)
  but deferred for application until the rename agent landed.

## Facts-to-subagents payload

Subagents have zero conversation memory. Every dispatch must carry in
`context`:

- Absolute file paths (never "the site files").
- The exact source-of-truth documents to read fully before writing.
- Literal URLs (repo remote, doc links)  -  do not make the subagent guess
  `github.com/<org>/<repo>`.
- Explicit DO-NOT-TOUCH lists: historical dirs (`docs/plans/`,
  `docs/auto-analysis/`, `docs/research/`, `docs/generated/`), binary/command
  literals, code paths, generated files.
- The verification commands to run and the exact pass criteria.

An under-specified subagent either guesses (wrong) or asks (round trip). Both
cost more than writing a precise brief.

## Wording-sweep guard (terminology renames)

For product renames (e.g. daemon → platform), sweep PROSE ONLY. Enumerate the
protected literal classes explicitly in the task text:

- Binary/command names (`meept-daemon`, `./bin/meept-daemon -f`)
- Code paths (`cmd/meept-daemon/`, `internal/...`)
- Go identifiers, package names, bus topic names, config keys
- Historical/generated records (plans, audits, auto-analysis, generated graphs)

Require the subagent to report every remaining hit of the old term with
file:line plus a one-word justification category (binary-name | code-path |
invariant | out-of-scope). That report is the acceptance test.

## Fabrication guard (comparison/marketing tables)

Marketing pages often contain plausible-looking comparison tables with no
traceable source. Rules:

- If a table's values cannot be traced to an audited source document, treat
  the table as FABRICATED. Never copy it into new work.
- Point the subagent at the audited source md and instruct: reproduce values
  EXACTLY, including parenthetical qualifiers ("X (6 tiers)"); include every
  category/section, not a flattering subset; render a legend for the symbols;
  add a provenance footer naming the source file and date.
- Same discipline applies to README tables: derive status judgments from the
  source matrix where products overlap; for products the matrix does not
  cover, derive from the cell's own prose (concrete shipped capability =
  complete; "optional"/"not implemented"/"no X" → partial/nonexistent) and
  never inflate the home column  -  mark the home product partial where the
  source matrix itself marks it partial.

## Verification sweep after both agents land

- Dead-reference check: `grep -rn "<removed-ref>" <site-dir>/` must be empty.
- Terminology check: `grep -rni "<old-term>"` over changed files; classify
  every remaining hit (allowed literals only).
- HTML validity: python `html.parser` feed + balanced-tag counts
  (`<table` == `</table`, `<section` == `</section`).
- Content spot-check: pick 5+ rows and diff them against the source md.
