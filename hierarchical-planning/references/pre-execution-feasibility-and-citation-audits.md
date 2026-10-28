# Pre-Execution Audits: Feasibility + Citation Drift (+ Sibling Baseline)


When to use: pre-dispatch verification of mechanisms and anchors.
Lesson: feasibility audit finds dead seams; citation audit corrects drifted file:line anchors.
Run these read-only audit dispatches AFTER authoring a plan tree/forest and
BEFORE dispatching implementation agents. Proven 2026-09-01 on the meept
`llm-resilience-forest` (5 trees, 18 leaves): the feasibility audit found 3
blockers (one a total mechanism failure), the citation audit corrected 16
anchors. Both fit in parallel subagent time (~10-35 min) and caught an
execution that would have been built on dead infrastructure.

## Audit 1: Mechanism-feasibility audit (the high-value one)

Plans assume mechanisms exist. Verify each tree's CORE mechanism against
source via one read-only subagent answering pointed questions:

1. **Is the mechanism REACHABLE in production?** Find the entry point's
   callers. Worked example: `HookRegistry.RunPrepareNextTurn` had ZERO
   production callers — the loop ran only SessionStart/SessionEnd hooks.
   Every leaf building on that hook pipeline was dead code; a new
   "wire the pipeline" leaf had to be inserted before the trigger leaf.
2. **Do new symbol names COLLIDE?** grep the receiver for the planned
   method name. Worked example: planned `Resolver.ResolveRef(ref string)
   (string, error)` vs existing `ResolveRef(ref string) *ModelConfig`
   with 3 live callers — duplicate-method compile error; renamed before
   dispatch.
3. **Can the state LOCATION deliver the semantics?** Worked example:
   endpoint-block state planned on per-alias `AliasHealth`, but the
   requirement was CROSS-alias shared fate — impossible; moved to the
   Resolver struct.
4. **One-shot vs persistent semantics.** Planned model override was
   cleared after first application; the requirement (escalated model
   serves a full fix budget) needed the persistent variant.
5. **Write-back path.** Does "sync into the registry" have a mutable
   runtime target, or is it built-once + per-call copies (needing a new
   setter under the existing lock)?
6. **Data plumbing.** Do the payloads/records carry the fields the
   resume/stamp path needs, or must upstream structures gain them first?
7. **Import-cycle sweep** for any new cross-package calls.

**Dispatch shape:** one subagent, read-only, given 5-7 pointed questions
plus the plan file list; report BLOCKERS / RISKS / MINOR, each with
file:line evidence + a one-sentence fix. Digest in-session (never delegate
the amendment decision), fold EVERY finding into the tree docs with its
disposition, and keep the audit as a dated record file
(`ARCH-AUDIT-<date>.md` sibling) with a findings→disposition table.

**Blocker classes worth probing** (all four appeared in one forest):
unwired pipeline (no production callers), method name collision, wrong
state granularity for a cross-cutting requirement, one-shot semantics
where a budget is required, missing payload provenance for a resume path.

## Audit 2: Citation-drift audit

Sibling sessions shift lines while you plan. Dispatch one read-only
subagent: extract EVERY file:line / `~line` / range citation from the plan
docs, verify each against current HEAD (`search_files` / terminal grep,
NEVER `read_file` for source), and verdict each ACCURATE / DRIFTED (give
current line) / WRONG / STALE-CONCEPT. Stale-concept findings (renamed
symbols, wrong surface) go at the TOP of the report — they change designs,
not just anchors. Worked-example outcome: ~94 accurate, 13 drifted, 0
wrong, 3 stale-concept (e.g. a retry-loop count constant named
`streamMaxRetries`, not `maxRetries` — the plan's grep recipe undercounted
the loops it needed to rewire). Apply corrections per file with targeted
edits; annotate concept renames with "(audit <date>)" so future readers
know the name is verified against source.

## Sibling-session baseline (before Wave 1 dispatch)

`git log --oneline -5` — commits naming YOUR plan's trees mean a sibling
session is executing the same forest right now. `git status` — dirty
source files are FENCED OUT of every dispatch context you write. Take
sibling-committed leaves as done (verify + run gates; do not
re-implement), re-order your concurrency waves around in-flight files,
and state the fence in each dispatch context ("do NOT touch X.go — a
sibling session owns it"). Worked example: wave 1 was re-planned from
{tree-01, tree-02} to {tree-01 leaves 01, tree-05} because tree 02 was
mid-flight and loop.go/client.go/anthropic.go/errors.go were all dirty.
