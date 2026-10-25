# Research-Leaf Execution Mode (in-session, not delegated)

Learned 2026-08-19, agent-orange Phase 0 execution.

## When this applies

Plan-tree leaves whose work is web research — literature scans, source
audits, any web_search/web_extract-dominant leaf. This file is the
detail backing "Step 1.6" behavior; the SKILL.md dispatch guidance says
subagents implement leaves — research leaves are the exception.

## The failure

Both dispatched research leaves timed out at the 600s subagent ceiling:
- Literature-scan leaf: 10 API calls, 600.0s, ZERO files written.
- Source-audit leaf: 5 API calls, 600.06s, ZERO files written.

Search-heavy subagents burn their entire budget on sequential searches
(an unhedged `web_search` round inside a subagent is slow and serial)
and never reach the write phase. Re-dispatching hits the same wall.

## The recovery (proven)

The ORCHESTRATOR executes research leaves in-session:

1. Batch web_search calls 3-4 per message round — the runtime executes
   independent tool calls concurrently. A 27-item citation-verified
   literature scan finished in ~8 rounds (~4 min wall), versus 600s+
   timeout per subagent attempt.
2. Write the deliverable with write_file directly.
3. Run the leaf's normal review checklist: spot-check citations resolve,
   count OPEN QUESTION markers, verify section order.
4. Commit per the standard leaf-commit protocol (explicit paths only).

## Blocked-command protocol

If the user (or a permission prompt) BLOCKS a probe/search command
mid-leaf: do NOT re-attempt the same outcome via another command, and do
NOT try to route around it. Complete the deliverable from evidence
already collected; mark gaps with the leaf's OPEN QUESTION mechanism
(greppable literal string) so missing verification is explicit rather
than silently absent. (Observed: one follow-up curl batch blocked →
source-truth.yaml completed from the 12 probes already on disk, with 21
OPEN QUESTION markers for the unverified remainder.)

## Evidence habit for audit leaves

- One live HTTP status per claimed endpoint:
  `curl -s -m 15 -A "<ua>" -o /tmp/<name>.json -w "%{http_code}" "<url>"`
- Keep response bodies on disk: they are the evidence base when later
  probes get blocked, and they let each field state "VERIFIED live"
  (with the status code + body size) vs "OPEN QUESTION".
- `head -c 300` the bodies afterward to record response-shape notes
  (field names, date formats, cursor fields) without re-fetching.
