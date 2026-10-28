# Ffallback model masquerade
When to use: quota window dressed as assertion failure.
Lesson: weak fallback models produce wrong-but-green verdicts; forensics before STOP clauses.

# Fallback-model masquerade: quota window dressed as assertion failure

How a provider quota window makes a live e2e suite FAIL in ways that mimic
product regressions — and the forensics protocol to run BEFORE invoking a
leaf's STOP clause ("if it still fails, the deps didn't hold; do not weaken
the assertion"). From the meept session-continuity leaf 03 dispatch
(2026-09-04, scripts/e2e-naive-user-chat.sh), where 4 full runs were needed
to separate plumbing-health from provider-health.

## The masquerade

Suites with honest-SKIP semantics assume: provider unavailable ⇒ send fails
(rc=2) ⇒ SKIP, exit 0. But the meept daemon layers fallbacks that defeat
that assumption:

- A 429 on the default provider can be RECORDED as the assistant reply
  ("quota limit reached on <model> Rate limit reached...") — the turn
  "succeeds" from the harness's point of view.
- The daemon can re-route to `small_model` (local LFM-1.2B), which ANSWERS —
  producing canned clarification loops, agent-roster dumps, and "no record
  of creating any files" nonsense. No SKIP fires; assertions FAIL.

So a quota window masquerades as: broken session continuity (A5), broken
artifact behavior (A4), broken reply shaping (A2) — anything.

## Detection signature

- daemon.log: `HTTP 429 ... code=1302 "Rate limit reached"`,
  `Quota exceeded, episode tracked`, `Quota exceeded` + later turns with
  NO 429 but suspiciously instant replies (fallback answered locally).
- `session_messages` assistant rows containing "quota limit reached on".
- The SAME rigid reply template across different turns and sessions —
  template boilerplate is daemon-generated, not model output variety.
- Conversely: artifact assertions (file created) may PASS while the reply
  assertions FAIL — server-side agent work succeeded while the sync reply
  timed out (socket i/o timeout). Work and reply are independent channels.

## Forensics before STOP (the protocol)

1. Re-run once with `--keep`; never conclude from the PASS/FAIL surface
   alone. The kept workdir is the evidence locker.
2. `sqlite3 $WORK/state/sessions.db "SELECT id, role, entry_type,
   substr(replace(content, char(10), ' '), 1, 110) FROM session_messages
   ORDER BY id;"` — did the mirror/restore plumbing record what the landed
   leaves were supposed to record, in order, with correct roles? This
   verifies deps INDEPENDENT of reply quality (garbage fallback replies
   still prove the mirror works).
3. Grep daemon.log for 429 / quota / fallback / per-turn model attribution.
4. Grep the Go source for a distinctive string from the offending reply
   (e.g. "not quite sure what you're asking for"). A hit means a DAEMON
   code path (classifier / intent gate / template builder) produced the
   reply — no LLM saw the restored history at all, so no amount of
   context-plumbing fixes it and no re-run will.
5. Only then disposition: (a) deps broken → STOP per the leaf rule and
   report; (b) provider window degraded → wait it out and re-run; (c)
   pre-existing product behavior (gate short-circuit) → report with
   file:line and propose a FOLLOW-UP leaf. Never weaken the assertion.

## Real outcome (2026-09-04)

Leaf 03's tightened A5 tripped its own STOP clause (bare-clarification
FAIL) on a provider-live run — but forensics showed leaves 01/02 HELD
(mirror rows correct in sqlite) and the canned clarification came from
`internal/agent/dispatcher.go` `buildClarificationResult` (~:1184, string
literals ~:1194-1198): `ClassifyAndRoute` runs
`intentAnalyzer.AnalyzeTrueIntent` and returns `ClarificationNeeded`
BEFORE the chat agent is invoked, so restored session history never
reaches a model on that turn. Correct disposition was (c): report +
propose a follow-up leaf (bypass/lower the ambiguity gate when the session
has an adjacent task result), with the assertion left intact.

Also: waiting out the window is legitimate (one `sleep 300` unblocked the
zai quota and produced the clean provider-live run), but run forensics
FIRST — otherwise you burn runs hoping instead of knowing.

## Related

- hierarchical-plan-execution → references/pitfall-54-late-429.md
  (subagent-dispatch-side 429s — different layer, same provider reality)
- hierarchical-plan-execution → references/rate-limit-recovery-and-review-fix-pattern.md
- hierarchical-plan-execution → references/live-e2e-leaves-and-gate-attribution.md
  (honest-SKIP / STOP-not-weaken non-negotiables this extends)
- meept-development → references/session-continuity-task-turn-record-2026-09-04.md
  (the leaf whose live verification produced this protocol)
