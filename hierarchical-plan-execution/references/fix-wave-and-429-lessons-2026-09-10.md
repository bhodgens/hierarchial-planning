# Fix-wave dispatch, provider 429s, whole-package gates
## (humanplusone openbot-parity campaign, 2026-09-10)

10 GitHub issues → 9-wave / 16-leaf plan tree → executed to green CI on
GitHub. This file records the execution lessons that generalize beyond
what's already in SKILL.md Step 11.

## Parallel dispatch vs provider 429s

- A batch of 7 concurrent fix leaves: 6 died with "HTTP 429: Rate limit
  reached" inside ~10s each (1 completed). Re-dispatch SERIALLY — one
  leaf per batch. All succeeded serially (each 15–50 min).
- A leaf whose report says status=completed but whose body is "API call
  failed after 3 retries: HTTP 429" with ~10–20s duration and 1
  api_call did NOT run. Never count it as evidence — "review found
  nothing" from a 429'd reviewer is not a clean result. One
  runtime-hunt leaf 429'd twice and never started; the orchestrator ran
  its probe scripts directly instead.

## Leaf-local checks ≠ whole-package gates

Every fix leaf ran mypy on its own touched files: clean. The
orchestrator's integration gate ran WHOLE-PACKAGE mypy: 11 new errors
(no-any-return on helpers the leaf added, unused ignores, no-redef).
Per-file checking skips cross-module inference. The integration gate
must run package-level mypy/lint/full tests — then fix in-session (the
fixes were small: targeted `# type: ignore[code]`, annotation additions).

And CI is the final reviewer: the first push of a NEW workflow surfaces
what local `make ci` cannot — unverified action SHAs (404), renamed
install-script URLs (curl exit 22), hashed-lockfile installs that omit
the project package itself (ModuleNotFoundError in tests). Budget one
fix-push cycle for the first live run of a new workflow.

## Fix-wave pattern (review → triage → fixes → gate → close)

1. Dispatch an adversarial-review leaf: report-only, must cite file:line
   + concrete exploit + fix sketch, "no speculative findings". Empirical
   proof bar: the ReDoS finding was confirmed with a >60s CPU hang on a
   30-char subject, not hypothesized.
2. Orchestrator triages into a table: severity, fix-now vs accepted-risk.
3. Fix leaves: one owner per file region (7 leaves, 7 disjoint file
   sets, zero clobber), each carrying: finding id, the fix sketch,
   regression bar ("suite currently N passed — all must stay green"),
   TDD RED/GREEN requirement, do-not-commit.
4. Orchestrator: whole-package gate → per-leaf commits → close issues
   with implementation comments recording deliberate non-goals.
5. Accepted risks get their OWN GitHub issues with options tables —
   "accepted risk" without a tracked issue is how the next audit
   rediscovers them. The two deferred findings (SVID replay window,
   audit spool) became issues #12/#13 with option tables and acceptance
   criteria.

## Frozen contracts scale; evolution has a recipe

Contracts in master.md (owned schema + signature + semantics) let 7
leaves edit disjoint surfaces in parallel with zero divergence. When a
contract had to evolve (add tool.effect to the policy context), the rule
was: change the control-plane source first, re-vendor the worker mirror
byte-exactly, keep the drift-guard test green. One source of truth +
mirror + drift test beats two hand-synced copies.
