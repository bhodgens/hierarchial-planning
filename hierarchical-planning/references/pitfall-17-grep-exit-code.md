# Pitfall 17 - grep -c / grep -q Zero-Match Silently Aborts && Chains

When to use: chaining a verification grep with git add/commit (or any follow-up command) using &&.
Lesson: grep exits 1 on zero matches - which is success for a corruption check - and kills the rest of the && chain with no error surfaced.

A verification step like `grep -rcE '...' --include='*.go' . && git add . && git commit ...` BREAKS when the check correctly finds zero matches: `grep -c` exits 1 on no matches, so the `&&` chain stops and `git add`/`git commit` never run - the change is written but never committed, with no error surfaced. A commit was lost exactly this way.

## Fixes (prefer option a)

(a) Run the check separately and inspect its output, then commit unconditionally as a separate deliberate step.

(b) `grep -c ... ; git add . && git commit ...` - semicolon instead of `&&`, so the chain continues regardless of grep's exit code.

(c) Invert with `if ! grep -q ...; then :; fi`.

## General rule

Never gate `git add`/`git commit` behind a grep that may legitimately return zero matches. Verification and commit are separate steps; each is its own command with its own output inspection.
