# Mmultihost live verification
When to use: verification across multiple hosts.
Lesson: orchestrator-side reference compendium for live multihost runs.

# References for `hierarchical-plan-execution`

Support files for executing plan trees created by `hierarchical-planning`.
SKILL.md sits near its size cap — put new lessons in these files, not SKILL.md.

## Session-proven references

- **staged-index-hygiene.md** — parallel sessions sharing one repo: sweep
  commits, staged-set verification, hunk-splitting shared files, stash
  round-trip destruction, gate false-failures from unstaged context,
  sibling-commit theft of your staged hunks, `git clean -fd` approval gates.
- **shared-tree-recovery.md** — orchestrator-side recovery: pre-commit state
  ritual, phantom artifacts (subagent claims vs. disk), privileged-step
  denials, sibling workstream reconciliation, multi-commit regression review
  mechanics.
- **shared-checkout-contention.md** — leaf-agent view of the same
  environment: sweep/restore/stash failure modes, mid-session HEAD
  detachment recovery, dead-subagent WIP, parallel leaves over ONE shared
  file, hermetic fixtures masking runtime wiring gaps.
- **leaf-collab-dispatch-protocol.md** — dispatch-context templates for
  leaf collaboration.
- **shared-checkout-contention.md** includes the "hermetic fixtures mask
  runtime wiring" parent-review lesson.

## The class of failure this session family keeps proving

Integration tests written against REAL components (no mocks of the code
under test) are what surface dead wiring — exported functions that compile,
pass unit tests, and are never called by any production path. See
`meept-2026-08-27` notes in staged-index-hygiene.md and the wiring-audit
pattern in SKILL.md §"grep for production callers". Expect a multi-leaf
feature that wires new components into a large daemon to have 3+ dead-wiring
gaps that only a live end-to-end exercise finds; budget for a verification
phase AFTER the leaves, and treat each found gap as a bug fix commit, not a
test failure.

## Real-cluster verification (live multi-node test) — meept 2026-08-27/28

Running the integration test's scenarios against REAL daemons on real hosts
(totem PVE cluster) found four MORE defects that in-process tests cannot
see. The pattern generalizes to any plan whose feature spans multiple
processes/hosts:

1. **Survey the target hosts FIRST** (reachability, toolchain, existing
   installs) before planning deployment steps. `for h in ...; do ssh $h
   '<probe>'; done` — batch, parallel-safe.
2. **cgo binaries resist naive cross-compiles.** `GOOS=linux go build` fails
   on sqlite-vec/alsa deps even with zig as CC (missing sysroot headers).
   Budget for native builds on a target node (apt-get install golang-go
   git libsqlite3-dev libasound2-dev pkg-config gcc), then ship binaries or
   the repo to siblings — same-OS/glibc nodes can reuse one node's build.
3. **JSON5 config parsers in this repo class (hujson) reject bare keys** —
   generated configs must quote ALL keys. A bare-key config parses locally
   with comments-strippers but fails hujson at daemon load, and the daemon
   SWALLOWED the load error (`err == nil && loadedCfg != nil` gating) —
   config-load errors must be loud.
4. **Distributed member registries have heartbeat-liveness filters.**
   `Member.IsActive(<=timeout)` means hand-seeded member records (no
   last_heartbeat) are filtered out of discovery. Seed records must carry a
   fresh heartbeat or the node must run its own heartbeat loop before any
   peer resolution works.
5. **Deploying config with heredocs through ssh: double-escaping corrupts
   JSON.** `{ \"key\": ... }` inside `ssh host 'cat > file <<EOF'` lands as
   literal backslashes on disk; the daemon then treats every record as
   unparseable ("skip broken entries") and silently proceeds with an empty
   registry. Prefer `scp` of a locally-written file, or single-quoted
   heredoc delimiters, and VERIFY the remote file content after writing —
   `grep -c '\\\\' file` as a corruption tripwire.
6. **In-process integration tests cannot see cross-process wiring gaps.**
   Each of these (transport never started, heartbeat loop never started,
   sync handler never registered, component never assigned) passed unit
   tests because the units were correct and the WIRING was missing. The
   live-cluster phase exists precisely to catch these; treat "deploy to
   real hosts and exercise the real path" as a plan phase, not an optional
   extra.

### Executing the live phase

- Get explicit user approval for each new CLASS of mutating action on shared
  hosts (repo tarball transfer, member-registry rebuild, `git clean -fd`).
  A denied command means STOP that action and ask — never rephrase-and-retry.
- After each fix, the loop is: commit → push → apply patch on the primary
  build node (`git apply /tmp/fix.patch`) → rebuild → redeploy binaries →
  restart daemons in order → wait ≥2 cadence periods (heartbeat + exchange
  intervals) → re-verify. Latency is dominated by the cadence waits; batch
  observations.
- Watch daemon logs for the specific INFO line per fix
  ("users sync handler registered with cluster engine") — presence of the
  line is the proof the wiring fix is in the RUNNING binary, not just in
  git.
