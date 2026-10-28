# Llive seal validation and revision deadlock
When to use: live validation of sealed-plan execution.
Lesson: three stacked live-only bugs; re-verify the premise before fixing symptoms.

# Live validation of sealed-plan execution: the reviewer revision seam

Session 2026-09-07, meept plan-compiler tree, live validation of the new
seal→compile→execute pipeline (post-tree, pre-fix). The tree shipped green
(88 pkgs, race-clean, integration test green), and the LIVE run still
deadlocked — the gap was in an interplay between the NEW wiring and the
EXISTING reviewer/revision machinery that no in-repo test exercised.
Three sequential runs (0003, run3, run4) surfaced THREE stacked bugs; each
fix was verified live in the next run.

## What live validation proved (do it for opt-in pipelines)

Flipping the config flag and driving one real draft through `chat` →
`plans edit-draft` → `plans seal` validated in ~10 minutes what the tree's
integration tests could not:

- The problems-as-result UX: seal with a bad `version:` returned a
  problems list WITH line numbers and left the draft editable (exit 0 on
  the draft). One round-trip fixed it.
- Scaffold seeding (no LLM, no interview) round-tripped through
  show-draft/edit-draft.
- Daemon-side flag wiring ("Plan compiler pipeline enabled" log line),
  persistence via PlanManager, and task→executing transition all worked.
- Provider-side failures (Agnes 429 storms) correctly poisoned 3/5 steps
  AND the reviewer correctly REJECTED the junk planner output — the gate
  works; the failures were upstream, not pipeline bugs.

Rule of thumb carried forward: a tree whose whole point is a NEW user
pipeline (opt-in flag → new CLI → new RPC → existing executor) is not
done at suite-green; budget one live smoke where the orchestrator plays
the user. Cheap: one scratch draft file + the CLI.

## Bug 1: self-clobbering state write — SetState then stale full-row Update

**Symptom.** Task stalls at 67% indefinitely. DB shows the original step
`state=reviewing` forever, plus a revision row `state=pending` whose
`depends_on` points AT the original. Scheduler never promotes the
revision (dependency non-terminal); nothing ever moves the original out
of reviewing. No error logged — a silent deadlock.

**Log-vs-DB reconstruction recipe (worked first-try):**

1. Grep daemon.log for the step id: found
   `Review completed status=rejected` → `Created revision step
   revision_id=...rev-1001 original_id=...` at 23:20:12.751.
2. sqlite the tasks DB for the two rows: original STILL `reviewing`, but
   the `task_state_transitions` table showed `reviewing → rejected`
   followed by a silent `rejected → reviewing` — recorded by the code
   itself. The rejection DID land; a later write undid it.
3. Root cause: `HandleReviewResult` rejected path called
   `SetState(step.ID, StepRejected)` and then `stepStore.Update(step)`
   with the step object loaded BEFORE the SetState. The full-row Update
   carries the stale `reviewing` state and writes it back. The revision
   depends on the non-terminal original → stranded.

**Fix shape (00551f63):** ONE full-row write carries both the state change
and the revision-count bump (mutate the loaded object's fields, then a
single Update). Rule: after a targeted write, audit the rest of the
function for later full-row Updates of the same object.

**Sibling in the same path:** the execution-error gate fails the step and
returns ReviewRejected — but HandleReviewResult then created a revision
depending on a FAILED terminal dep, un-promotable by design. Fix in the
same commit: failed steps get feedback only, never revisions.

## Bug 2: promotion gate didn't know about revisions

After bug 1's fix, the chain STILL stalled: `CreateRevision` appends the
original's ID to DependsOn BY DESIGN, but `PromoteReadySteps` requires
`IsSuccessfullyTerminal` deps and `rejected` never qualifies. Revisions
were structurally unschedulable — creation alone doesn't make a redo
entity schedulable.

**Fix shape (2ac27b1f):** promotion lets a REVISION step (ID contains
`-rev-`) pass a rejected dep; failed deps still block everything
including revisions; non-revision steps unchanged. Match
`AreAllCompleted`'s existing "rejected resolves via successful revision"
semantics — the completion checker and the promotion gate must AGREE or
the entity is born dead. Lesson: when adding a redo/revision entity,
extend creation + promotion + finalization together.

## Bug 3: counter drift — and the re-diagnosis discipline

Task finalized "2/1 completed, 200%". Initially read as "finalizer must
consult the revision chain" — WRONG premise. Re-reading the data: the one
failed step was a real upstream Agnes 400/429, and execution failures
intentionally get no revision (bug 1's own fix). status=failed was
CORRECT honest completion. Only the counters were wrong.

Real root cause: revision creation bumped TotalJobs via Get→IncrementJobs→
full-row Update (concurrent completions' full-row Updates wrote stale
snapshots back over it); OnJobFailed used the same RMW shape for
FailedJobs.

**Fix shape (02e952f9):** atomic single-statement
`IncrementTotalJobs`/`IncrementFailedJobs` in the store (extend the
existing A-08 IncrementCompletedJobs pattern — don't reinvent), plus
`RecountJobs(taskID)` recomputing all three counters from step rows; BOTH
finalization paths recount + reload before emitting task.completed/
task.failed events.

Discipline: re-verify the premise against the data before fixing a
second-order symptom. The first plausible fix would have added dead
complexity to the finalizer.

## Debug moves that worked (all three bugs)

- The signal was always the DISCREPANCY between log and DB — logs alone
  looked correct, DB rows alone were just rows. Build the timeline:
  correlate log timestamps with `task_state_transitions.timestamp`.
- sqlite the state DBs directly — CLI task get can lag or aggregate what
  row-level truth shows.
- One live run per fix: rebuild binaries → pkill daemon → relaunch →
  grep the startup marker ("Plan compiler pipeline enabled") → re-run
  the seal flow. A daemon running old binaries verifies nothing; check
  binary mtime vs fix commit when in doubt.
- Do NOT loop grep-only "checks" (this session burned dozens of
  near-identical greps in the deadlocked run); write the sequence down
  once and reason from it.

## Test shape the tree lacked

The integration test exercised flag-on → seal → executing with happy-path
steps. Nothing tested "reviewer rejects a step mid-task → revision
schedules → task finalizes with truthful counters". When a pipeline hands
off to an EXISTING subsystem (reviewer/revision here), the live-validation
plan should include one forced-rejection scenario, or the leaf should pin
the state-transition sequence in a unit test.

## Honest-run accounting across runs

- 0003: stalled at 67% — bug 1 (this repo) + Agnes 429s (upstream).
- run3: revision loop verified (rev steps pending→ready→scheduled→
  approved, 0 stranded rows) — but counter drift exposed bug 3; one step
  lost to Agnes 400 `messages[2]: missing field 'content'` (upstream,
  intermittent).
- run4: counters truthful (6/5/1, 83%); one step lost to Agnes 429 (real
  quota, honestly reported as failure).

Separate per-run the meept bugs (fix, commit, verify next run) from Agnes
degradation (429 storms / intermittent 400 — paid tier or stronger
planner model is the documented answer; never "fix" these in repo code).

## Daemon operational notes

- Restarts under `terminal(background=true)`: multiple PIDs for one
  logical daemon (launcher + child); the socket file mtime is the
  readiness signal, and `meept task get` erroring with connection
  refused means the daemon is still coming up (wait, don't restart
  again — double-restart orphans the first).
- A "stray test artifact" dir in the repo (daemon wrote into the repo
  workdir during an integration test) may vanish on its own when the
  owning process exits — check before asking the user to clean it.
- When the user's own scratch cleanup (`rm -rf`) was consent-denied
  earlier, re-checking whether the artifact still exists (read-only
  `ls`) is allowed and often resolves the todo without any rm.
