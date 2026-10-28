# Ssubagent rate limit mitigation
When to use: 6+ parallel subagents get 429-throttled.
Lesson: mitigation: stagger, shrink, retry with original context.

# Subagent Rate Limit Mitigation

When dispatching many subagents in parallel (6+), the subagent model's API
provider may throttle with HTTP 429. The subagent returns `status=completed`
with zero files written — the summary says "API call failed after 3 retries."

## Detection

After a subagent returns, always check whether it actually produced output:

```bash
git status --short  # did any files land?
```

If the subagent reported "API call failed after 3 retries: HTTP 429" and
`git status` shows nothing new, **no work was done**.

## Mitigation: In-Session Fixes

Do NOT re-dispatch blindly (the rate limit window may not have cleared).
Instead, apply fixes in-session:

### Option 1: execute_code (batch string replacements)

```python
import os

base = "/path/to/project"

# Read the file, apply targeted replacements, write back
with open(f"{base}/some_file.py") as f:
    content = f.read()

content = content.replace("old_string", "new_string")
content = content.replace("another_old", "another_new")

with open(f"{base}/some_file.py", "w") as f:
    f.write(content)

print("Fixed: description of what changed")
```

This is the fastest approach when you have a clear list of search-and-replace
fixes from a review subagent's findings.

### Option 2: patch tool (targeted single edits)

```
patch(mode='replace', path='/path/to/file', old_string='exact old text',
      new_string='exact new text')
```

Better for single precise edits where the surrounding context matters.

## When It Happens

Most common during:
- Review-and-fix cycles: 5+ review subagents return, then 6+ fix subagents
  are dispatched simultaneously
- Large plan tree execution: 10+ leaf subagents dispatched in 3 waves
- Any time the subagent model provider has per-minute rate limits

## Pattern from HumanPlusOne Session (2026-08-04)

3 of 6 fix subagents hit 429 during the review-and-fix cycle. The orchestrator
applied 30+ fixes via `execute_code` batch operations while other subagents
were still running. Total time saved vs waiting for rate limit window: ~10 min.

## 5-hour quota windows are a DIFFERENT beast (quota-review session, 2026-08-31)

This file originally conflated two failure modes. Distinguish them:

1. **Per-minute 429 (transient)**: re-dispatch after a stagger works. The
   mitigations above apply.
2. **5-hour usage-window exhaustion** ("Usage limit reached for 5 hour.
   Your limit will reset at HH:MM"): NO amount of re-dispatching helps —
   every child call burns the same shared window. Observed 2026-08-31 quota
   docs subagent: 26 calls over 10 min, landed its most important edit
   (the master.md fix log), then died mid-task on the window.

**Window-exhaustion protocol:**
- On `status=completed` + "HTTP 429: Usage limit reached for 5 hour" →
  check disk FIRST (`git diff --stat` on the leaf's file set). Partial work
  is common and often covers the critical piece.
- Salvage in-session, do not re-dispatch: finishing 2-3 doc edits inline is
  cheaper than any retry that also re-reads context, and every retry burns
  the same window.
- Stagger wave size preemptively once any provider-429 has occurred: a
  5-wide fan-out lost 3 of 5 this session; dropping to 3 concurrent + 
  in-lining the smallest work kept the tree moving.
- Track which agent died on WHICH mode in the tracking table —
  "429 (window)" = do-not-re-dispatch-until-reset; "429 (rate)" =
  stagger-and-retry.

## Rule 5b corroboration at scale (skill-evolver tree, 2026-09-01)

Three of four leaf agents died at the REPORT step (one rate-429 after full
work, two window-429s); all three had complete, green, review-ready work on
disk. The report step is the most fragile call in the loop — treat
`status=completed` + 429 text as "check disk, assume done until proven
otherwise." Two of the three were committed verbatim from disk state; the
third needed zero salvage. Zero re-dispatches were needed for any of them —
re-dispatching would have burned the shared window for nothing and risked
duplicate edits against landed work.

Additional in-session corollary: when a leaf's work is fully landed and only
its SUMMARY was lost, the orchestrator can reconstruct the report from the
leaf doc's review checklist + the diff (commit message written from the
checklist items). The leaf doc IS the report template.

## Re-review dispatch note (2026-09-01, same tree)

A second adversarial wave (3 concurrent re-reviewers over already-committed
work) ran clean — reviews of COMMITTED work are immune to the sibling-revert
class because nothing is uncommitted. When planning a re-review pass, prefer
reviewing committed state: it also means reviewer-applied fixes are the only
dirty files in the tree, making them trivial to inventory and commit.
Reviewers of uncommitted work need the sibling-revert brief lines; reviewers
of committed work don't.
