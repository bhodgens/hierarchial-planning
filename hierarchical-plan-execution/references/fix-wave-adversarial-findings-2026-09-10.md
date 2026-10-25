# Fix wave: adversarial-review findings → parallel fix leaves (2026-09-10, openbot-parity)

Post-campaign close-out, the user asked to "fix associated issues and bugs found
using subagents." An adversarial-review leaf (read-only, confirmed-findings-only
mandate) produced 11 findings (2 HIGH, 5 MEDIUM, 3 LOW + 1 doc). This reference
records the fix-wave mechanics: what worked, what failed, and the triage rules.

## Dispatch pattern

- **Triage table first, then dispatch.** Each finding → one fix leaf with a
  severity + fix-sketch row. 7 leaves were planned but only 2 should ever run
  concurrently (see 429 below).
- **Per-finding file ownership, same as feature waves.** Each leaf's dispatch
  context named its files exactly ("you own ONLY database.py + crypto.py +
  test_crypto.py"); 7 leaves touched database.py/main.py/redaction.py with
  zero clobbers.
- **"You MAY modify tests you authored, do NOT weaken them"** is the right
  wording for waves that change behavior (e.g. the login-CSRF fix had to touch
  wave-8.2 OIDC tests; the invariant was "replay still 400, one-shot still
  enforced").
- **Regression bar = current count, not a number from context.** Say "all must
  pass (current: 690+1skip)" — counts drift between dispatch and leaf start.

## 429 mass failure: serial re-dispatch is the recovery

7 leaves dispatched simultaneously → 6 died at ~10s each with HTTP 429 (one
survived). The failures were INSTANT (10s), not mid-run — this is dispatch-storm
rate limiting, not leaf-side quota exhaustion. Recovery: re-dispatch each failed
leaf individually, serially (one → review → commit → next), with the ORIGINAL
context unchanged. All 6 serial re-dispatches completed first-try. Subagent
rate-limit mitigations live in references/subagent-rate-limit-mitigation.md.

## The findings (for pattern recognition, not re-fixing)

| ID | Sev | Class of bug | Fix shape |
|---|---|---|---|
| F1 | HIGH | ReDoS: policy `matches` regex, 30-char input → >60s CPU (serial worker queue stall) | parse-tree nested-quantifier rejection + 100ms thread bound + subject cap; deny-timeout must STILL deny |
| F2 | HIGH | Cross-tenant audit forgery: unbound shared worker key + body-supplied client_id trusted | 403 on unbound keys for audit-writing routes; keep deny-default GET policy contract |
| F3 | MED | URL-path injection via LLM-controlled id + TOCTOU tag check | regex guard pre-HTTP + honest "advisory" doc (n8n has no atomic call) |
| F4 | MED | last-admin guard TOCTOU (SELECT COUNT before write lock) | guarded single-statement UPDATE/DELETE, rowcount→409; barrier-concurrency test |
| F5 | MED | secrets in JSON-encoded strings bypass redaction | depth-bounded JSON reparse + key-variant regex + case-insensitive bearer; twins byte-identical |
| F6 | MED | "encryption at rest" defeated by retained plaintext column; rotation silently destructive | NULL plaintext post-backfill; unique index → hash column; keyid segment in token format |
| F7 | MED | SPIFFE aud shape mismatch (str vs list) — genuine SVIDs 401'd | accept str-or-list, SET must equal {aud} exactly |
| F8 | LOW | SVID replay window | ACCEPTED RISK — real fix is X.509/mTLS; documented in module |
| F9 | LOW | wildcard prefix matches bare prefix (`kb_*` matches `kb_`) | non-empty remainder check |
| F10 | LOW | audit posts lost on CP outage | ACCEPTED RISK — sqlite busy-timeout keeps window small |
| F11 | LOW | login CSRF (state not browser-bound) | hpo_state cookie == state-JWT jti, checked before one-shot consume |

## Classes worth recognizing next time

1. **Fail-closed can still be feature-breaking.** F7 rejected every genuine
   credential — "secure" but shipping nothing. Fail-closed bugs need the same
   priority as fail-open when they break the feature's core path.
2. **Dual-implementation drift is a bug surface.** The redaction twins and the
   vendored policy mirror both need cross-differential tests (same fixtures
   through both implementations in one process) — drift-guard alone isn't enough.
3. **"Write-only" encryption protects nothing.** If no code path decrypts a
   column, the ciphertext is decoration; the plaintext column decides the real
   security posture. Audit encrypt-decrypt symmetry.
4. **Shared/unbound credentials + body-supplied tenant IDs = forgery.** Any
   route that writes tenant-scoped rows must require a tenant-BOUND credential,
   not just any valid credential.
5. **Regex from user/admin input needs three layers**: parse-tree validation
   (reject nested quantifiers), runtime bound (thread + timeout), subject cap.

## Verification obligations for fix leaves

- Each leaf ran the FULL suite for its side (control 649→704, worker 170→201)
  plus its own new tests; the orchestrator ran whole-package mypy at the end
  (leaf-local typecheck passes lie — see SKILL.md section).
- Fixes that changed vendored/twin files required re-sync + drift-guard green
  BEFORE the leaf could report done.
- Accepted risks (F8/F10) were documented in module docstrings / commit
  messages, NOT silently dropped — the triage table records the decision.
