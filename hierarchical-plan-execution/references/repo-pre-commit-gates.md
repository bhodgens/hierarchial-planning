# Repo Pre-Commit Gate Survival & Shared-Tree Commit Hygiene

Lessons from meept containment/loop-economics tree execution (2026-08-24/25, ~18 leaf dispatches into a repo with an 11-gate pre-commit hook). Generalizes to any repo with heavy client-side commit gates.

## Gates that block agent commits, and the fixes that pass

- **U1000 unused symbols** — test scaffolding written then abandoned (helper funcs, fixture types). Fix: delete them. `//nolint:unused` works but dead code accumulates. **meept's hook specifically ignores `//nolint:U1000`** (2026-08-29, two blocked attempts): there is no annotation escape — delete the function and move any contract note into a plain comment on a surviving symbol. A "greppable anchor" for a contract does not need to be a function; the comment IS the anchor.
- **SA1029 builtin type as context key** — `context.WithValue(ctx, "session_id", v)`. A type ALIAS (`type k = string`) does NOT satisfy it. Working fix: a tiny dedicated file with a typed key struct + constructor helper (`ContextWithSessionID(ctx, id)`), then migrate BOTH producer and consumer call sites — a typed key invisible to a legacy `ctx.Value("session_id")` reader silently drops the value.
- **Ignored errors (`_ = f()`)** — cleanup paths (`_ = db.Close()`, `_ = os.Remove(tmp)`). The hook greps ADDED lines for literal `_ = `. Fix that passed: per-line `//nolint:errorcheck // best-effort cleanup; primary error takes precedence`. Keep reasons specific.
- **Feature-docs gate** — new packages (especially under `pkg/`) demand `docs/workflows/<pkg>.md`. Fix: write a short REAL doc (How It Works / Configuration / Edge Cases). Satisfies the gate and is useful. Do not reach for --no-verify.
- **staticcheck runs on STAGED packages only** — partial staging passes/fails differently than the full tree; always `go build ./... && go vet ./...` first so the verdict isn't a surprise.
- **Commit latency** — the full gate gauntlet (build + analyzers + staticcheck + gosec + docs scan) can exceed a 60s tool-call timeout on large trees. Wrap: `timeout 170 git commit -q -m "..." > /tmp/c.txt 2>&1; echo exit=$?` and read the temp file for the verdict.

## Parallel leaves sharing one working tree

- Stage EXPLICIT paths per leaf. Never `git add .` — sibling agents' unrelated WIP (media tools, theming, model aliases) sits modified in the same tree and will be swept into your commit.
- Over-staged sibling files: `git restore --staged <path>` immediately. If a shared file (e.g. config/schema.go) carries BOTH your hunk and theirs, unstage it entirely and split your feature across two commits rather than committing their half-finished work.
- Sibling concurrent edits cause TRANSIENT build breaks (undefined symbols from half-landed sibling work). Re-run the build before diagnosing; these usually self-resolve as siblings converge. Corollary: a failing `go build ./...` may be nobody's fault in your leaf — scope the build to your packages for triage.
- A sibling's broken package blocks YOUR commit (hooks build whole staged packages). Options: wait for sibling convergence, or commit only paths whose packages build clean and defer the rest.

## Failed-summary dispatches (rule 5b corroborated a third time)

Three more dispatches reported status=failed or produced no summary (provider 503 during the summarization step); ALL THREE had complete, green, review-ready work on disk. The protocol held every time: `git status --short` + scoped build + scoped tests → review in-session → commit with explicit paths. Never re-dispatch before checking disk — re-dispatching risks duplicate/conflicting edits over already-landed work.

See also: `references/leaf-sizing-and-timeouts.md` (sizing rules, rule 5b protocol, orchestrator wait discipline).
