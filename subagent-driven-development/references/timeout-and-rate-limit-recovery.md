# Timeout and Rate-Limit Recovery: Salvage Before Re-Dispatch

When to use: any subagent dispatch times out or fails with HTTP 429; before any re-dispatch decision.
Lesson: a timeout means scope was too large (split and salvage), a 429 means quota is contended (serialize and enrich context) - in both cases salvage partial work from disk first, and after two failed rounds write the deliverable in-session.

## Salvage pass before any re-dispatch

1. `ls -la` + mtime on every file the subagent was supposed to write. mtime BEFORE the dispatch = zero work; during it = partial/complete.
2. Skim artifacts for the load-bearing symbols (grep the key function names from the spec). Presence + sensible length = likely complete.
3. Run the artifact's tests yourself - the subagent timed out during exactly this step; its non-report is not evidence of failure.
4. Re-dispatch ONLY zero-work tasks; finish small gaps in-session.
5. Budget one fix-up round: salvaged code averaged 3-4 real bugs per deliverable (wrong skip conditions, unreachable caps, unhandled error paths) that the timed-out verification never caught.
6. If salvage reveals test-expectation drift, check the FIXTURE's arithmetic before debugging the code: a synthetic grid fixture miscounted its own cells (claimed 3 mud, spec had 2), producing off-by-one failures attributed to the implementation. Also expect group-accumulation in fixtures (a determinism test building twice without clearing sees 2x counts) - fix the test flow, not the code.

Real divergence case: three subagents timed out simultaneously (three Godot test suites competing for CPU). Salvage showed task 2 and 3 complete, task 1 untouched (11 API calls, zero writes). A blanket re-dispatch would have duplicated two finished deliverables.

## The two-round rule

When a SECOND round of delegations on the same task also times out (both cut mid-verification, ~60% of work on disk), stop delegating. Finishing the known-remaining pieces directly (one test file, one consumer, one getter - ~15 min) beats a third 10-minute dispatch that will also time out. After two timeout rounds, brief-writing overhead exceeds the remaining work: switch to direct completion with the salvage as the starting point.

## Timeout sizing (code subagents)

- Reading 12 files / ~6K lines + fixes: completes reliably.
- Reading 30+ files / ~10K lines + fixes: timeout risk.
- Reading 60+ files / ~47K lines: will almost certainly time out.
- Target ~5-8K lines of Go per audit subagent.
- New-file generation: 6-8 new files reliable; 10-13 high timeout risk (wrote 11/12 and 8/13 before dying in one session). Recover by finding what persisted (`find -newer <marker>`), verifying each file's last line for truncation, then writing the remaining 2-5 files directly.
- Bug fixes: 8-10 per subagent max; fixes + test writing: 6-8 combined.
- Long downloads (a 10MB file over a slow link is 60-90s): batches of 2-3 per dispatch or serial from the parent.
- Long server-side operations (e.g. ~90-minute image generation) NEVER fit a subagent: use cron/background/remote script.
- Benchmark runs loading multi-GB models (2 models x (45-90s load + 20 calls) = 5-8 min of babysitting plus server churn): run in the parent session via background terminal. A timed-out benchmark subagent leaves its first llama-server running - `pgrep -fl llama-server` and reuse before killing.
- Research/writing subagents: they burn the budget on web_search/web_extract and never write (two of three doc subagents timed out with 20-30 calls each, zero output). Constrain research (5-8 searches max), set a line-count target, or split research from writing.

Post-timeout file check before commit: `find <dir> -name "*.ext" -newer <known-good-marker>` then `tail -1` each file to catch mid-function truncation. Always `ls` every expected path - parent-written files have also gone missing at staging time.

## Timeout recovery: split and retry smaller

Do NOT retry the same scope. Diagnose which subagents succeeded (they may have applied partial fixes or written partial files), split each failed scope into 2-3 smaller targeted subagents (e.g. "handlers A-M" + "handlers N-Z" + "middleware + tests"), re-dispatch only failed groups, and verify build + diff after each batch.

## Rate-limit (HTTP 429): serialize, enrich, fall back

429 is NOT scope-too-large - it is quota consumed by aggregate parallel calls. Never "parallelize harder"; the fix order is:

(a) Serial retry. Most common trigger: 3 subagents launched simultaneously on aggressive providers. After a batch where ALL hit 429, retry ONE AT A TIME - a single serial subagent stays under the per-request limit.

(b) Rich-context retry. A subagent that cats 20 files and runs 10 searches makes ~30+ internal API calls, each able to hit the limit. On re-dispatch, provide full source quotes in `context` instead of file paths - every avoided read is one less call in the quota window.

(c) Fall back to direct work in the parent. If serial retries also 429: the subagent fails before any output, you already read enough to write the deliverable yourself, the work is read-only, or the deliverable fits one write_file (~600 lines). In one session, 3 serial read-only audit re-dispatches all hit 429 before the parent wrote all 3 reports directly from accumulated file reads.

(d) Check partial persistence: some subagents finish write_file calls before the 429 - the partial work may need only a small follow-up.

## Pure writing tasks: write directly

Even with web research forbidden, writing-heavy subagents can time out on generation speed alone (a 400-line doc timed out at 600s with 6 API calls - five consecutive times on different docs).

Write directly when: pure knowledge synthesis, source material already loaded, under ~600 lines, no iterative exploration. Delegate when: multiple independent docs (parallel throughput), research you lack, or very long (>800 lines) output that would pollute parent context. Decision rule: one re-dispatch with tighter constraints after a writing timeout; if it times out again, write it yourself.

## Small code leaves and hybrid foundation

When a leaf is small (3-5 files, types/config, no complex logic) and the spec is loaded, direct writing takes 2 minutes vs 6+ minutes for dispatch+return. If the TDD cycle is under 5 tool calls, do it yourself.

Hybrid foundation pattern (validated): the parent writes the foundation leaf (types, schema, config - ~5 small files) directly, then dispatches larger leaves in parallel. The foundation is the highest-risk dispatch (everything depends on its types) but the lowest-risk direct write (pure definitions, no logic), and committing it gives siblings a green tree with real types to compile against. Decision rule: only types/interfaces/migrations/config = write directly; any logic (queries, handlers, state machines) = dispatch.
