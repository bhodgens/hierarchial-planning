# Ssingle leaf decomposition
When to use: requested parallelism on one leaf.
Lesson: decompose or refuse: single-leaf shapes.

# Single-Leaf Decomposition for Requested Parallelism

> Worked example for Step 2.5 / Pitfall 29 in hierarchical-plan-execution.
> When the user requests N subagents but the plan has one leaf, decompose
> the leaf by file ownership into parallel units.

## Session

- **Date:** 2026-07-23
- **Project:** meept Go daemon
- **Plan tree:** `docs/plans/20260723-config-extraction/`
- **Plan shape:** Single leaf (`01-extract-hardcoded-configs.md`) covering 5
  hardcoded values across 5 independent files
- **User request:** "use 5+ subagents"

## The Problem

The plan's single leaf touched 5 files across 4 packages:

| # | Hardcoded value | File | Package |
|---|----------------|------|---------|
| 1 | HTTP base URL `"https://localhost:8081"` | `transport/client.go` | transport |
| 2 | SQLite busy timeout `5000ms` | `session/store_sqlite.go` | session |
| 3 | Prompt truncation limit `8000` chars | `session/summarizer.go` | session |
| 4 | Ollama endpoint `"http://localhost:11434"` | `memory/vector/embedding.go` | memory/vector |
| 5 | TLS min version `tls.VersionTLS12` | `transport/http_client.go` | transport |

A single subagent could do all 5, but that wastes the user's requested
parallelism. The default reflex (one leaf = one subagent) also wastes it.

## The Decomposition

### Wave 0: Shared Dependency (Orchestrator, In-Session)

The config schema (`internal/config/schema.go`) is the shared dependency —
all 5 new options need corresponding config fields and defaults. The
orchestrator did this directly:

1. Added `SessionConfig.SQLiteBusyTimeoutMs` (default 5000) + default in
   `DefaultConfig()`
2. Added `SessionConfig.SummaryPromptTruncationLimit` (default 8000) +
   default in `DefaultConfig()`
3. Added `EmbeddingConfig` defaults (Ollama endpoint, model, dimension) to
   `DefaultConfig()` — the fields already existed, just no defaults

Verified `go build ./internal/config/...` before dispatching any subagents.

**Key principle:** The orchestrator owns shared types. Subagents own leaf-level
implementation files. The orchestrator commits the green-tree baseline (Wave 0)
before any Wave 1 subagent runs, so siblings inherit a compiling tree.

### Wave 1: 5 Parallel Subagents (File-Partitioned)

Each subagent owned exactly ONE non-overlapping file set:

| Subagent | File | Change pattern |
|----------|------|---------------|
| 1 | `transport/client.go` | Extract string literal → exported `DefaultHTTPBaseURL` constant |
| 2 | `session/store_sqlite.go` | Add `busyTimeoutMs` field, `WithBusyTimeoutMs` option, restructure DSN construction |
| 3 | `session/summarizer.go` | Add `SummarizerOption` type, `WithPromptTruncationLimit` option, backward-compatible signature change |
| 4 | `memory/vector/embedding.go` | Extract `DefaultOllamaBaseURL` and `DefaultOllamaModel` constants |
| 5 | `transport/http_client.go` | Add `tlsMinVersion` field, `WithTLSMinVersion` option, `DefaultTLSMinVersion` constant |

**Dispatch context for each subagent included:**
- The exact inlined source code for the file being modified (from orchestrator's
  pre-reads — subagents never `read_file` source)
- The project's functional option pattern (`type Option func(*Struct)`)
- Explicit file ownership: "ONLY modify these files"
- Build verification command for the specific package
- Standard rules: no commit, no plan-file edits, no read_file on source

**Subagents 2 and 3 co-own the `session` package** — but they touch different
files (store_sqlite.go vs summarizer.go). Since neither imports or references
the other's changes, the package compiles independently of sibling completion
state. No sibling-package-collision issue (cf. Pitfall 22).

### Wave 2: Daemon Wiring (Orchestrator, In-Session)

After all 5 subagents returned and were reviewed, the orchestrator wired the
new config fields to the new options in `internal/daemon/components.go`:

```go
// SQLite store construction (line 1363):
if cfg.Session.SQLiteBusyTimeoutMs > 0 {
    storeOpts = append(storeOpts, session.WithBusyTimeoutMs(cfg.Session.SQLiteBusyTimeoutMs))
}

// Summarizer construction (line 1394):
summarizerOpts := []session.SummarizerOption{}
if cfg.Session.SummaryPromptTruncationLimit > 0 {
    summarizerOpts = append(summarizerOpts, session.WithPromptTruncationLimit(cfg.Session.SummaryPromptTruncationLimit))
}
summarizer = session.NewSummarizer(summarizerLLM, logger.With("component", "summarizer"), summarizerOpts...)
```

The TLS min version and HTTP base URL wiring was already handled by existing
code paths (daemon.go for server-side TLS, cmd/meept/main.go for client-side
transport config). No additional wiring needed.

## Results

| Metric | Value |
|--------|-------|
| Total subagents dispatched | 5 (Wave 1) |
| Subagent wall time range | 21s – 87s |
| Subagent fix cycles | 0 |
| File collisions | 0 |
| Review iterations | 0 (all APPROVED on first review) |
| Tests | All passing (config, session, transport, memory/vector, daemon) |
| Pre-commit hooks | All 11 passed (staticcheck, gosec, bodyclose, vet, mutexio, U1000) |

## Why This Worked

1. **File partitioning guarantees zero patch-tool collisions.** Each subagent
   owns a non-overlapping file set. No `patch` tool sibling-modification
   warnings possible.

2. **Wave 0 (shared types) done first by the orchestrator.** All subagents
   inherited a compiling config schema with the fields they need already
   present.

3. **Inlined source code in dispatch context.** Subagents never need to
   `read_file` source files — they get the exact code to modify in their
   context. This prevents line-number corruption and saves 3-5 internal
   tool calls per subagent.

4. **Backward-compatible signature changes.** The summarizer's
   `NewSummarizer` signature changed from `(llmClient, logger)` to
   `(llmClient, logger, opts ...SummarizerOption)` — the variadic parameter
   means existing callers in tests and daemon wiring compile unchanged.

5. **Pre-dispatch signature verification (Pitfall 27).** Before dispatching,
   the orchestrator verified that `Dispatcher.Stop()` was `func (d *Dispatcher)
   Stop()` (no return value) — the plan's template assumed `error` return.
   The corrected dispatch contexts prevented compile failures.

## When to Apply This Pattern

- User explicitly requests N subagents for a single-leaf plan
- The leaf touches 3+ independent files/packages
- Each file's changes are self-contained
- A shared dependency (types, config schema) can be done first as Wave 0

## When NOT to Apply

- The leaf touches the same file in multiple places (intra-file dependencies)
- Changes are sequential (file B needs file A's types to compile)
- The work is genuinely tiny (1-2 file edits — just do it directly)

## Subagent 429 Rate-Limit Failure (Zero-Output Dispatch)

When a subagent hits a provider rate limit (HTTP 429), it may return a
"completed" status with ZERO files written. The summary will say something
like "API call failed after 3 retries: HTTP 429: Rate limit reached."

**Detection:** Always verify file existence after a subagent returns,
especially when the dispatch was large (10+ files) but the subagent ran
for an unusually short time (<60s). Run `os.path.exists()` on the expected
output paths immediately — do not trust the "completed" status alone.

**Recovery:** Re-dispatch a fresh subagent with the same context. Add a
note to the dispatch context: "Write ALL files in this single dispatch.
Do not re-read files after writing." Rate limits are transient — the
re-dispatch will succeed if spaced a few minutes from the original.

This pattern (verify file existence → re-dispatch on zero output) is
the correct response to 429 failures. Do NOT mark the leaf as BLOCKED
or report failure to the user until at least one re-dispatch attempt
has completed.

Real-world instance (humanplusone AI Employee platform, 2026-08-04):
golden template leaf dispatched, hit 429, returned with 0/10 files written
in 38 seconds. Re-dispatched with same context, completed successfully
in 110 seconds with all 10 files.

## Subagent Timeout on Large Leaves — Partial Output Recovery

When a single subagent is dispatched for a large leaf (8+ tasks, 10+ files) and
hits the 600s timeout, it may have written SOME files before timing out. The
timeout status gives no summary.

**Detection:** After a timeout, check `git status --short` in the worktree to
see what was actually written. The files present represent the subagent's
partial progress.

**Recovery — two options:**

1. **Orchestrator finishes the remaining files directly** (fastest if <50% of
   files remain). Read each partially-written file for syntax errors (timed-out
   subagents leave half-baked code), fix them, then write the remaining files
   yourself. This was the pattern used for rebellion-the-game leaf 05
   (foliage): subagent wrote only `grass_blade.gdshader` (with GLSL syntax
   errors — GDScript-style `float x: float =` annotations in shader code)
   before timing out. Orchestrator fixed the shader, then wrote the remaining
   6 files directly + tests.

2. **Re-dispatch a fresh subagent for the remaining files only** (better if
   >50% remains). List the files already written in the dispatch context so
   the new subagent doesn't redo them.

**Why option 1 is often faster for Godot projects:** Godot files require
headless GUT verification (import + test run, ~20-30s each cycle). The
orchestrator can run the test loop directly, while a subagent would need
multiple tool calls to iterate on failures. The orchestrator also has the
SHARED-CONVENTIONS pitfalls in context (no `class_name`, no `:= with Variant`,
etc.) which subagents repeatedly violate.

**Common partial-output bugs in timed-out subagent code:**
- GLSL shaders with GDScript syntax (`float x: float =` — the `: type`
  annotation is GDScript, not shader language; use `float x =`)
- Wrong Godot enum names (`SHADOW_CAST_ONLY_SETTING_OFF` →
  `SHADOW_CASTING_SETTING_OFF`)
- `class_name` declarations that break cross-script resolution in GUT
- `var x: Type = expr as Type` (invalid typed declaration pattern)

Real-world instance (rebellion-the-game leaf 05, 2026-08-07): subagent timed
out at 600s with only 1/7 files written (the shader, with syntax errors).
Orchestrator fixed the shader and wrote the remaining 6 files + tests in
~5 minutes. All 157 tests passed on first full run after orchestrator fixes.

## Concurrent Subagent GUT Contention — All Agents Timeout (2026-08-07)

When dispatching 4+ subagents that each need to run the Godot headless test
suite (GUT), ALL subagents may timeout at 600s because they contend for the
same Godot process. The Godot binary (`/Applications/Godot.app/Contents/MacOS/Godot
--headless`) is a single-process tool — running 4 GUT invocations concurrently
causes 4×120s test runs to serialize, each agent waiting on the others' I/O.

**Detection:** All N subagents return status=timeout with ~15-19 API calls each
(showing they were alive and working, just blocked on GUT). No files written
because they never got past the test-verification step.

**Recovery — do NOT re-dispatch the same batch.** Instead:

1. **Audit in-session.** The orchestrator reads the key files directly
   (search_files + read_file), checks API signatures, verifies constants
   against specs. This is faster than subagent dispatch for audit-only tasks
   (no code to write, just verify).
2. **Run GUT ONCE centrally** after all in-session changes are done.
3. **Dispatch subagents ONLY for code-review** (read + grep, no test runs).
   Subagents that only read code don't contend for the Godot process.

**For code review specifically:** dispatch subagents with explicit
instructions: "Do NOT run Godot, GUT tests, or any build commands." This
prevents the contention entirely — multiple agents can read/grep code in
parallel without blocking. But 6 of 8 such agents may still hit provider
rate limits (429) if the provider is under load — design for partial success
and plan to cover the gap in-session.

**Pattern that works for Godot codebase-wide review:**
1. Dispatch 8+ subagents with file-ownership partitioning, NO test commands.
2. Accept that some will 429 (rate limit) — those branches get in-session coverage.
3. The 2-3 that complete find real bugs the automated scanner missed (config
   mismatches, re-entrant races, inverted guards — bugs that require reading
   two files together to detect).
4. Orchestrator runs a single automated pattern scan (`execute_code` with
   grep for common bug signatures) to cover the branches subagents missed.
5. Orchestrator runs GUT once centrally to verify all fixes compile + pass.

Real-world instance (rebellion-the-game, 2026-08-07): 8 review subagents
dispatched. 2 completed (found 10 real bugs in UI + foundation code). 6 hit
429 rate limits. Orchestrator's `execute_code` pattern scan covered the
remaining 6 branches, finding 1 additional bug (AudioStreamWAV.FORMAT_FLOAT
parse error). All fixes committed, GUT 964/972 pass, 0 regressions.
