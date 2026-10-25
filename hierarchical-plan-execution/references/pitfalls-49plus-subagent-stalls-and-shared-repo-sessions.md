# Pitfall 49+: Subagent Stalls, Small-Subset Recovery, and Shared-Repo Concurrent Sessions

Session-derived pitfalls from meept unified-theming (2026-08-25). These
extend the numbered pitfalls in the main SKILL.md.

## 49b. Passive sleep-polling hides dead subagents

A subagent with `child_timeout_seconds=0` (no cap) can stall silently
forever — no completion report ever arrives, and orchestrator sleep-loops
waste hours. When waiting on a background delegation, periodically verify
liveness directly instead of only sleeping:

- `ls -l` mtimes of the files the agent was assigned — writes stopped hours
  ago = likely dead;
- process table for the agent's runtime;
- whether its completion message arrived.

If mtime is stale by more than one expected iteration (~20–30 min), declare
it stalled, take over in-session, or re-dispatch smaller units.

Real-world instance (meept unified-theming, 2026-08-25): two wave-2
subagents stalled without reports; the orchestrator slept in poll loops for
~4 hours before checking process liveness. Disk timestamps showed the last
write was hours old. User feedback: passive waiting without liveness checks
was the orchestrator's fault, not the agents'.

## 49c. On stall/takeover, re-dispatch SMALLER disjoint subsets

User-endorsed pattern: after the first L4 attempt stalled, recovery split
17 files / ~350 mechanical edits across 4 parallel agents (2–3 files each),
all completing in 6–22 minutes. Rules that made it work:

1. **Disjoint file ownership per agent** — zero overlap, stated explicitly
   ("You own EXACTLY these files; siblings own X and Y").
2. **Shared helper pre-built by the orchestrator first** (the palette
   bridge existed and compiled before any dispatch).
3. **Explicit replacement maps** inlined into each dispatch so agents do no
   design work.
4. **Verification scoped to owned files** — `go build` + `go vet` +
   `gofmt -l` on owned files only; NO shared-package test runs mid-flight
   (they break when a sibling is mid-edit).
5. **Judgment-call policy stated up front** (e.g. "keep #FFFFFF literals,
   annotate with a marker comment") so parallel agents decide identically.

## 49d. Concurrent Hermes sessions sharing one repo eat uncommitted work

Two distinct hazards observed in one day:

**(a) Tree-wide revert by another session.** Five files being migrated all
reverted at the identical second (mtimes equal to the second = automated
git operation, not human editing). Subagent output destroyed mid-task;
agents reported their edits "vanished".

**(b) Commit sweep under the wrong message.** Another session committed its
own feature with broad staging and swept the orchestrator's uncommitted
leaf files into that commit. Code was intact but history mixed concerns.

### Countermeasures

- **Commit each reviewed leaf IMMEDIATELY with explicit paths** — never let
  verified work sit uncommitted across a wait boundary.
- Before staging, re-check `git status` for files you didn't touch; if
  foreign changes appear in your target dirs, stop and identify the writer
  first.
- If a sweep already happened: locate the swallowing commit
  (`git show <commit> --stat`), verify your content landed intact, and
  document the message-mismatch in plan tracking notes rather than
  rewriting history.
- Detection signature for hazard (a): multiple unrelated files whose mtimes
  are identical to the second.
- If the user runs concurrent sessions in one repo, surface the risk early:
  "another session is committing to this repo; I'll commit my work at each
  review gate to avoid sweep damage."
