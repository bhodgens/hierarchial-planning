# Pitfall 10 - Reset Status on Re-dispatch

When to use: a leaf is re-dispatched after a review failure.
Lesson: reset the leaf's tracking-table status to IN_PROGRESS on every re-dispatch - never leave it at IMPLEMENTED.

When a leaf is re-dispatched after review failure, its old status (IMPLEMENTED) no longer describes reality: implementation is being redone, not awaited. Leaving it at IMPLEMENTED makes the tracking table lie in both directions - the parent cannot see the leaf is mid-flight, and a grandparent polling the table cannot distinguish "returned, awaiting review" from "re-running after failure."

## Rule

On every re-dispatch, in the same step as the dispatch itself, set the leaf's status to IN_PROGRESS in the orchestrator's Completion Tracking Table. Add a note recording what the review found, so the re-dispatch context (and the history) carries the reason.

The tracking table is the single source of truth for subtree status (canon C1-State); status hygiene is what makes trickle-up reporting (Pitfall 6) trustworthy.
