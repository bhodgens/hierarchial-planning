# Parallel fan-out partitioning on ONE repo

Learned 2026-08-31 from a successful 4-agent concurrent fan-out on one Go repo
(bench harness: judge tests / runner helper tests / runner feature work /
routing-assertion wiring across 3 packages). Distinct from per-task sequential
dispatch: when N agents run CONCURRENTLY on the same repo, file-level collision
is the primary failure mode.

## Zero-conflict rules

1. **Partition by file, not by feature.** Each brief states: "Edit ONLY <files>.
   Do NOT create, edit, or delete <other agents' files>." Name exact paths —
   e.g. the test-file author was told the feature agent owns runner.go, and the
   feature agent was told not to touch any `*_test.go`.

2. **Shared-schema edits happen in the parent BEFORE dispatch.** Two agents both
   needed a new suite-schema field (`ExpectAgent`); the parent added it first
   and each brief referenced it as existing fact. Concurrent agents adding the
   same field = clobber or duplicate-symbol build failure.

3. **Reserve integration wiring for the parent.** The file that composes
   everyone's components (runner.go wiring) was excluded from ALL briefs; the
   parent wired it after results landed, in one coherent edit. Do not split the
   integration file between agents "by section" — merge conflicts there are the
   worst kind to resolve.

4. **Read agents' skip notes.** One agent correctly declined to fix a gitignore
   bug outside its file scope and flagged it in its report ("on disk and
   compiling but invisible to git"); the parent fixed it. "Not my scope" reports
   are findings, not noise.

5. **Verify per-agent, integrate once.** Run each agent's tests as its result
   arrives (grep its symbols too — confirm the work actually landed), then the
   parent runs: combined `go build ./...` + full `go test ./...` + one live
   end-to-end run exercising the new paths → single consolidated commit.

## Brief template (per agent)

- Goal: one sentence.
- Context: repo path, module name, files to READ first, payload/struct shapes.
- Scope: "Edit ONLY <paths>. Do NOT touch <other agents' files> / any *_test.go."
- Verification: exact test/build commands that must pass.
- Constraints: "Do NOT git commit." (parent consolidates).

## Related

- SKILL.md § "Committing safely when a CONCURRENT agent shares the repo" —
  same repo, longer horizon (other sessions committing between your writes).
- SKILL.md § "Salvage pass on timed-out code subagents" — when fan-out members
  time out instead of colliding.
