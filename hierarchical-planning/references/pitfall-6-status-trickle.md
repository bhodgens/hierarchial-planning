# Pitfall 6 - Status Not Trickling Up

When to use: any child status transition in a running tree.
Lesson: update the tracking table after EVERY transition; unrecorded child completion blinds the grandparent.

If a parent doesn't record child completion, the grandparent has no visibility: integration planning, wave dispatching, and the root's completion verdict all read from tracking tables, and a stale row silently blocks or misreports all three.

## Rule

Update the tracking table after every child transition - dispatch (PENDING to IN_PROGRESS), return (to IMPLEMENTED), review pass (to REVIEWED), commit/integrate (to COMPLETE), failure (to BLOCKED). The parent determines completion; the child never self-assesses (canon C1-State).

The orchestrator's tracking table is the single source of truth for subtree status. Related hygiene: reset status to IN_PROGRESS on re-dispatch (Pitfall 10); for trees running long enough that status churn makes protocol files volatile, keep a separate STATE.md (canon C1-State).
