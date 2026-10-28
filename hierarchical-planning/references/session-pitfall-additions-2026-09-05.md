# Session Lessons - Meept Research-Audit-Tools Tree (2026-09-05)

When to use: executing trees where leaves run long background verifications, siblings share a package or file, or leaf reports contradict briefs.
Lesson: background notifications are telemetry not failure; serialize shared-file leaves; verify drift claims against primary sources; license-gate deps in the brief and re-verify at review.

Extracted from SKILL.md "Session Pitfall Additions" during the 2026-10-26 refactor. Homes: same-package concurrency and Pitfall 45/46 detail live in `references/concurrent-wave-execution.md` and `references/pitfalls-same-package-concurrency-and-api-drift.md`; this file keeps the four bullets that had no other home.

## Background-process notifications from in-flight subagents are progress telemetry, NOT failures

Long leaves run their own shell verifications; the orchestrator sees `proc_*` exit notifications (possibly exit 127 from a malformed trailing echo in the subagent's own command). Do NOT re-dispatch on this signal alone. `tail` the log file named in the command (usually `/tmp/*.log`): it holds mid-flight test results (a test failing at iteration N, passing at N+1). The verdict remains the subagent's return PLUS the orchestrator's own re-run.

## Serialize leaves that edit the same shared file

Two leaves appending registration blocks to one `components.go` run as separate waves; the second dispatches only after the first is committed. Concurrent edits to one file are how integration bugs happen (Pitfall 19 covers stale read-state; this prevents the collision). Full rules: `references/live-multi-session-repos.md` Rule 1, `references/concurrent-wave-execution.md` Pitfall 46.

## Verify agent API-drift claims via primary sources before accepting

A leaf reporting "the brief's library API is wrong" may be right - confirm each claim with `go doc <pkg>` before amending contracts. Worked example: a leaf correctly overrode a brief's `pdf.NewReader(io.Reader)` with the real `io.ReaderAt` signature; the orchestrator confirmed via go doc and recorded drift in the tracking table. Full table of drift cases: `references/concurrent-wave-execution.md` Pitfall 44.

## License-gate new deps in the dispatch brief; re-verify at review

Put in the leaf brief: "read LICENSE under `go env GOMODCACHE`; if GPL/AGPL STOP and report." The orchestrator re-reads the LICENSE file itself at review (trust but verify, same as API drift). Full rule: `references/concurrent-wave-execution.md` Pitfall 45.
