# Plan Tree Dispatch Scaling — Rate Limits, Timeouts, Interface Conflicts


When to use: dispatching 4+ plan-writing subagents in parallel.
Lesson: sizing guidance, 429 recovery, interface-file ownership rules.
## Rate Limits When Writing Plan Trees (429)

Dispatching 4+ plan-writing subagents in parallel triggers rate limits on aggressive providers. Plan documents are write-heavy (10-30KB each, 6-10 per branch).

**Sizing guidance:**
- Branches with 5-6 leaf documents: reliable completion (~3-5 min)
- Branches with 8-10 leaf documents: high timeout risk at 600s. The subagent will typically write 7-9 files before timing out.
- Dispatching 4+ simultaneously: high 429 risk. Cap at 3 simultaneous, or dispatch in two waves.

**Recovery for timed-out plan-writing subagents:**
1. Check what was written: `search_files` for `*.md` in the branch directory
2. Write the missing files directly from the parent agent (you have the spec context loaded)
3. Do NOT re-dispatch — the subagent will re-read all context and likely timeout again

## Interface File Conflicts During Execution

When multiple branches define types feeding into a shared interface (e.g., a Go Store interface consumed by API, analysis, and dashboard subsystems), parallel implementation subagents may modify the interface file in conflicting ways.

**Real instance:** One subagent changed `InsertScreenshot` return from `error` to `(int64, error)`. Another subagent's mock store still expected `error`. Build failed across packages. The fix was to accept the better signature `(int64, error)` and update all implementations + plan contracts.

**Prevention:** In the master orchestrator, explicitly state which leaf owns each interface type. Tell subagents: "Do NOT modify types defined in leaf 01 — propose changes in notes."

**Detection:** After all parallel subagents return, run `go build ./...` before committing. Interface mismatches surface as compile errors.

**Fix:** Choose the better signature, update the interface and all implementations to match, update the contract in the plan documents to reflect the accepted change.

## Dispatch Sizing for Plan Tree Writing

When writing a full plan tree (master + N branches + M leaves), the bottleneck is output-token generation time per file. Each branch document is 15-25KB.

- **3-4 branches in parallel**: reliable if each has 5-6 leaves
- **5+ branches in parallel**: 429 risk. Split into two waves of 2-3.
- **Branch with 10+ leaves**: will timeout. Accept partial write, finish from parent.
