# Pitfall: Cross-Repo Bench↔Daemon Failure Chains (meept-bench ↔ meept)

The bench harness lives in one repo (meept-bench) and drives a live daemon
built from another (meept). A failing bench task is a daemon symptom until
proven otherwise; a daemon fix often needs a bench-side assertion updated.
This file records the failure classes found in the 2026-09-01/03 meept-bench
phase-2 sweep so the next session diagnoses by pattern instead of re-deriving.

## Daemon-side failure classes (all found via bench tasks failing)

1. **Silent schema-migration abort via NULL PRAGMA scan.**
   `PRAGMA table_info` returns NULL `dflt_value` for columns without a
   DEFAULT clause; scanning it into a plain `string` errors on the first
   such column, so `addColumnIfMissing` aborted before its ALTER and EVERY
   column migration silently never ran (no error at INFO level; the Warn was
   later added). Symptom: `table X has no column named Y` on insert while
   migrations appear registered. Fix: scan into `*string`. Lesson: a
   migration helper that logs at Debug is invisible in production logs —
   migration failures belong at Warn minimum.

2. **CREATE TRIGGER/TABLE IF NOT EXISTS keeps stale legacy shapes.** Adding
   a column + new trigger SQL does not update an existing trigger body or
   rebuild an FTS virtual table. If on-disk triggers predate a schema change
   (body lacks the new column marker), the migration must DROP + recreate
   the trigger/FTS pair and reindex. Detection: read `sqlite_master.sql` and
   grep for the new-column marker.

3. **`exec.CommandContext` bound to a transient ctx kills the subprocess at
   cancel.** The daemon started llama-server inside a goroutine with
   `defer cancel()` — StartAll returned right after WaitForHealthy, the
   goroutine exited, cancel fired, and the freshly-loaded model was SIGKILLed
   ~1s after "healthy". macOS logs NOTHING for third-party SIGKILL (no
   jetsam, no XProtect, no crash report) — a silent userspace kill looks
   exactly like an OS kill in `ps`/logs. Diagnosis: the process died 1s
   after the health transition; the only code running at that instant was
   the goroutine's deferred cancel. Fix: spawn with
   `context.WithoutCancel(ctx)`; lifetime is governed by explicit Stop and
   the health checker. Rule: never bind a long-lived subprocess to a
   request-scoped or goroutine-lifetime ctx.

4. **ProviderManager missing StreamingChatter → streaming bypasses
   failover.** `AsStreamingChatter(pm)` failed (no `ChatWithDeltaCallback`
   on the manager), so the agent loop fell back to a single-provider call
   with zero rotation: a 5xx on the primary failed the turn while a healthy
   fallback sat idle. Fix: implement `ChatWithDeltaCallback` on the manager
   with the same ordered-provider rotation as Chat (quota blocks
   credential+rotates; rate-limit rotates; client errors don't; server
   errors record failure+rotate). Rule: every multi-provider manager needs
   BOTH `Chat` and `ChatWithDeltaCallback`, or `AsStreamingChatter` checks
   silently drop streaming calls out of failover. Also: a 429 with a
   quota-shaped body classifies as `QuotaResetError`, not `RateLimitError`
   — the quota branch must rotate too (block credential, skip on next
   resolve), or quota errors never rotate.

5. **Recovery helper returning nil after absorbing an error = worker
   marks no-op turns as success.** `attemptStateRecovery` reset
   StateError→Idle and returned nil; `RunOnce` returned `("", nil)`; the
   job worker recorded success with an empty response; the planner advanced
   past a step that did zero work (observed: step "completed" in 324ms with
   no tool call). Fix: recovery still resets state but returns the original
   error (recovery is state hygiene, not success), plus defense-in-depth at
   the worker: reject empty agent responses instead of marking success.
   Lesson: a `("", nil)` return from a turn that did no work is a lie that
   compounds upward through every scheduler.

6. **Keyword-extraction quality gates dispatch before the LLM classifier.**
   Capability keywords were extracted from agent prose purposes ("You
   produce long-form writing...") lifting generic words (`write`, `text`,
   `file`, `content`). Length-weighted scoring then piled up writer@0.77 on
   any file-write prompt — above the 0.7 dispatch gate — stealing dispatch
   from the LLM classifier before it ran. Fix at the ROOT (extend the
   extractor's stopword list with cross-agent verbs/nouns), not in scoring
   policy: scoring guards (multi-keyword requirements, runner-up margins)
   broke legitimate short-keyword matches (`hello`→chat, `commit`→committer)
   in three iterations. Rule: when dispatch gating misfires, check WHAT the
   keywords are before HOW they're scored; generic words in capability sets
   are data defects, not scoring defects. Interim matcher guards built on a
   misdiagnosis cost three test-fix cycles and were reverted.

7. **`git rm --cached`-style untrack is required for gitignore to take
   effect on TRACKED files.** Appending to .gitignore does nothing for
   already-tracked paths (`results/` vs `internal/results/` package —
   anchor the pattern: `/results/` not `results/`, or the rule eats source
   trees). And a glob entry `suites/X.generated.json` misses variants
   (`X-memory.generated.json`) — use `suites/X-*.generated.json`.

## Bench-side lessons

- **`expect_agent` pins are routing contracts; only pin where dispatch is
  the contract.** On a degraded classifier, pins flip across unrelated
  tasks — that's environmental, not a suite bug (document the signature:
  `routing mismatch: expect_agent=coder routed=<other>` across many tasks
  in one run). Tasks whose checkers need file_write effectively require a
  file-capable agent (chat has no file_write — "Unknown tool requested" in
  the daemon log is the tell), so prompt leads with the file-write
  imperative to make coder routing the natural classification.
- **The diff gate must be proven with an injected fault** (flip one checker
  pattern, expect exit 1 with REGRESSED, restore, expect exit 0) before
  anyone trusts it — a gate that has never failed is decoration.
- **`--ignore-tags`** (comma-separated, ANY-match) replaces the manual
  two-pass workaround for known-failure/flaky exclusion.
- **Cost rows from daemon-wide `daily_used` are cumulative, not per-task** —
  snapshot status before/after the task and diff. Free-tier providers
  report $0.00; the mechanism is still correct.

## Live-probe technique (when logs don't explain it)

A tiny `go run` probe in the target repo that subscribes to the daemon's
bus, sends a minimal chat, and polls is the decisive instrument: it
reproduced `subscription not found` (bus-subscription lifetime bug) in one
run after log-grepping failed. Denials to watch: direct curl probes of
local model endpoints were denied twice — prefer repo-native probes or
daemon RPC over hand-rolled curl when the operator has denied curl.
