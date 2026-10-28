# Pitfall 27 - Pre-Commit Lint Hooks (U1000 Unused Code) Block Orchestrator Commits

When to use: committing leaf output in a repo with strict Go linters (golangci-lint, staticcheck U1000) wired into pre-commit hooks.
Lesson: remove unused code before staging; do not rely on //nolint directives; run staticcheck yourself before the first commit attempt.

Repos with strict Go linters in pre-commit hooks reject `git commit` if the staged files contain ANY unused function, variable, or import - even transitive ones (e.g. `mathAcosDeg` called only by `horizontalAngleBetween`, which itself is never called from production code). This repeated 5+ times across one forest's implementation waves (identity, llm, perception, schedule trees).

## Prevention

Before staging, run `go vet ./<package>/...` AND manually check for unused code. Remove unused helper functions entirely - do NOT rely on `//nolint:U1000` directives, as some pre-commit hook configurations do not honor them (the hook runs a fresh `staticcheck` pass that ignores inline nolint comments).

## The typical (wasteful) loop to avoid

(a) `go build ./<package>/...` succeeds.
(b) `go vet ./<package>/...` passes.
(c) `git commit` fails with `U1000: func X is unused`.
(d) Orchestrator removes the function.
(e) Commit succeeds.

Steps (c-e) can repeat 2-3 times for the same tree if multiple unused functions exist. Save the rounds: run `staticcheck ./<package>/...` (if available) before the first commit attempt.

Removing unused functions is itself a corruption hazard - see Pitfall 29 for the safe removal technique. More hook-interference patterns: `references/orchestrator-commit-hook-pitfalls.md`.
