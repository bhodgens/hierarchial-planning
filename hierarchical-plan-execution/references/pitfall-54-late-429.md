# Ppitfall 54 late 429
When to use: subagent lands work then dies before reporting.
Lesson: verify files on disk before re-dispatch; late-429 signature.

# Pitfall 54: late-429 — subagent lands work, then dies before reporting

Real instance: meept wikiskill-state tree, leaf 05 (2026-08-29). Subagent ran
~47 min, wrote ALL files, ran TWO green `-race` suite runs (logs in /tmp), then
its final API call 429'd and the delegation returned:

    API call failed after 3 retries: HTTP 429: Usage limit reached for 5 hour

with NO summary. A sibling leaf (06) died the same way but in 3 min with ZERO
files — first-call 429, the already-known variant.

## The failure mode of misreading this

The existing rule says "429 subagent = zero files, orchestrator implements from
briefs." Applying it blindly to leaf 05 would have REDONE ~47 minutes of
reviewed-quality work that was already sitting on disk and already verified.

## Decision protocol on any 429 delegation return

1. `git status --porcelain` the leaf's DECLARED file scope (from the leaf doc's
   Files sections) — new files and modified files.
2. Check for background-process completion pings that arrived after the
   delegation notification (proc_*): the subagent's verification commands write
   to /tmp log files named in the command; those logs ARE the test evidence.
   `tail` them.
3. Files exist → treat as IMPLEMENTED: orchestrator reviews the diff against
   the leaf contract in-session (same as a normal return), runs the leaf's
   test commands, commits if green. The dispatch brief doubles as the review
   checklist.
4. Files absent → existing rule: orchestrator implements directly from the
   brief (no re-dispatch into the exhausted provider).

## Why the rate limit resets later than you need

Both leaves 429'd against the same provider within an hour ("limit resets at
... +5h"). Re-dispatching ANY leaf into that provider before reset fails the
same way — orchestrator-direct work is the only path forward in the window.
Plan the remaining waves assuming provider capacity is zero until reset.

## Corollary: dispatch briefs are the recovery contract

The leaf-05 recovery worked because the dispatch brief contained the frozen
interface contracts, verified line numbers, and task list — everything needed
to REVIEW on-disk work without the subagent's report. The weaker the brief,
the more a late-429 costs: you cannot review what you cannot specify. See
meept-development skill's "write briefs YOU could execute" rule.
