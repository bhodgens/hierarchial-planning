# Parked-commit liability: consent-blocked commits

When to use: a commit is consent-blocked and the leaf's files sit uncommitted in a shared worktree.
Lesson: parked files are maximum sweep exposure - state what is parked in every update, re-attempt once per user touchpoint, and after two denials hand over the manual command and mark the leaf COMPLETE-in-worktree, commit-pending.

When a commit is consent-blocked (user denies at the gate), the leaf's
files sit uncommitted in a shared worktree - maximum sweep exposure (see
the collision sections above; the parked Makefile hunk survived two
blocked attempts and then its docs sibling got swept into e2adcf1b).
Protocol: state exactly what is parked and the one-line manual command in
every status update; re-attempt ONCE per user touchpoint (the user
answering anything is fresh consent context); if denied twice on the same
action, stop retrying entirely, hand the user the exact manual command,
and mark the leaf "COMPLETE-in-worktree, commit-pending" in the tracking
table. Never mark such a leaf COMPLETE without the commit or an explicit
user decision.
