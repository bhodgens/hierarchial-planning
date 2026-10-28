# Mmachine artifacts in repo
When to use: daemons writing into the checkout.
Lesson: machine-generated files vs human git hygiene.

# Machine-Generated Files in a Human Git Repo (daemon writes into the checkout)

Session class: a product's daemon runs with its CWD inside a git repo and
writes generated artifacts into the working tree. Two meept instances
(2026-08-31): (a) the skill evolver dropped 21 `skill-evolution-*.md` plan
files into `docs/plans/`; (b) plan files regenerating DURING a review pass —
a "modified since you last read it" warning fired on a doc mid-session.

## Diagnosis path (what actually identified the writer)

1. `git log -- <path>` on one file — commits exist, so they were swept into
   sibling agents' bulk commits, not written by the current session.
2. Content fingerprint: `plan_id: plan-20260901032324-0034` matched the
   product's own ID format (`plan.go:98` `plan-%s-%04d` with UTC timestamp)
   — proof the PRODUCT wrote them, not any agent.
3. Grepped the product source for the rationale string ("Low effectiveness")
   → found the writer (`evolver.go:604` → `planMgr.CreatePlan` →
   `resolvePlanDir` = `<daemon CWD>/docs/plans`).
4. Confirmed trigger in the user's runtime config
   (`~/.meept/meept.json5`: evolver enabled, run_on_start).

## Session-search limit

session_search did NOT find the writer (the daemon is not a chat session —
FTS over transcripts can't see process output). Evidence came from the
artifact format itself + product source greps. When hunting "who wrote
this file", try the product's own ID/format conventions before transcript
search.

## Migration pattern (user-directed: machine artifacts → user-scoped sink)

User's standing rule (2026-08-31): daemon-generated artifacts belong under
the user config dir (`~/.meept/...`), NEVER in a project checkout.

Steps that worked:
- `git mv` refuses destinations outside the repo → `cp` to the sink +
  `git rm --cached` the originals (content preserved both sides).
- Expect REGENERATION mid-migration: the daemon's tick re-created a moved
  file between the `cp` and the commit. Sweep `git status -- <dir>` AFTER
  the commit and repeat for stragglers; note in the commit message.
- Pre-create the sink dir by hand so the interim state is already the
  target state, then the plan-tree leaf that wires the config knob makes
  the fix permanent.

## The "explain/confirm/deny the user's mental model" step (2026-09-01)

When the user asks "what caused X / confirm my understanding", the answer
must TRACE the causal chain in code (config → trigger → writer → sink),
not summarize the artifact list. Here the user believed the plans were
"skills the evolver decided weren't good enough" — the direction was
inverted: they were PROPOSALS (archive/improve) parked for approval, i.e.
pending action items, not verdicts. Correcting that inversion required
reading the evolver's pass structure (Pass C prune / Pass A refine /
Pass D gap-fill each emit different plan title prefixes) and the
`auto_apply=false` → `CreatePlan` park path. Answer structure that worked:
(1) corrected polarity in one sentence, (2) code-traced cause, (3) what
each plan entails, (4) product gaps exposed — the user then explicitly
authorized the follow-up plan tree.

## Product-gap harvesting (same instance)

The artifact investigation exposed four real product gaps, each verifiable
with a grep: (1) approval dead end — `ApprovePlan` has no bridge to the
actuator; (2) writer root ≠ discovery root (`~/.meept/skills` didn't exist;
skills lived in `~/.claude/skills`); (3) machine plans in repo (this file's
subject); (4) verifier rubber-stamping empty-content archive proposals.
These became the four leaves of the governance plan tree — machine-artifact
investigations are plan-tree sources, not just cleanup tasks.


## Resolution (2026-09-01, follow-up tree shipped)

The four gaps were built as the skill-evolver-proposal-lifecycle tree and
landed: (1) `skills.evolver.plan_dir` config knob defaulting to
`~/.meept/plans/evolver/`, with a DEDICATED PlanManager for the evolver
(shared one untouched); (2) `Discovery.ResolveTierPath` + a `TierResolver`
seam on the Writer so archives/edits happen inside the skill's real
discovery tier; (3) an approval actuator — daemon-side bridge subscribing
`plan.approved`, dispatching `ApplyApprovedPlan` with provenance guard,
idempotency (`- applied:` Meta marker), and an exact audit line; (4)
per-action verifier gating with polarity derived from the selector (see
leaf-spec-gate-polarity.md).

Integration-review findings worth keeping for the NEXT such tree:
- **Approval rewrote plan files and silently stripped the provenance Meta**
  — a parse→write round-trip must preserve unknown Meta keys
  (`ParsedPlan.ExtraMeta`), or any marker stamped earlier is destroyed by
  the very approval flow that needs it.
- **SQLite DSN pragmas are driver-specific**: modernc.org/sqlite only
  honors `_pragma=...`; a `?_busy_timeout=` style DSN is silently ignored —
  WAL was OFF and a concurrent read could fail approval with SQLITE_BUSY.
- **Store-split visibility**: plans written to a dedicated sink store are
  invisible to surfaces that list the shared store — check every
  list/approve surface's store resolution when splitting stores.
- Approval surface gap: no TUI/CLI approve existed (HTTP/RPC only) — wire
  at the manager-event layer so future surfaces work unchanged, and report
  the missing surface rather than building UI inside the tree.

## Review-skill updates this session fed

The quota-review session's adversarial-review wave (leaves re-verified
against code, 12 defects) validated the audit pattern already documented
in the harness refs; the NEW durable lesson here is the two-instances
detection chain above, not the review loop itself.
