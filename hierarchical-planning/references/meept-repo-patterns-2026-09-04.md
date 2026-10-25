# Meept repo patterns — testing, hooks, concurrency (2026-09-04 session)

Durable, repo-level patterns observed/established while executing the
chat-dispatch-ux and session-continuity trees. These generalize beyond
any one tree.

## Pre-commit hooks (.githooks/)

- Main dispatcher: `.githooks/pre-commit` — runs 16 numbered sub-hooks;
  each sub-hook is a standalone script sharing the house style:
  `#!/opt/homebrew/bin/bash` shebang (macOS /bin/bash is 3.2 — no
  mapfile), RED/YELLOW/GREEN/NC colors, `|| exit 1` wiring, numbered
  `\e[34m[N/16]\e[0m` progress labels. Adding a check = new sub-hook
  file + one dispatcher line + relabel all [N/16] counters.
- `pre-commit-ascii` (2026-09-04): fails commits introducing CJK/Hangul/
  fullwidth characters in staged TEXT files (user mandate — CJK leaked
  into comments/docs repeatedly). Scope decisions baked in:
  * Staged files only (grandfathered historical hits fail only when the
    file is next modified — incremental cleanup, no big-bang).
  * Binary files skipped via `git grep -I` heuristic (no false hits on
    images/fonts/db).
  * Typographic punctuation (em-dash, arrows, box-drawing) is OUT of
    scope — it pre-exists repo-wide legitimately. Only CJK scripts are
    blocked.
  * Minimal reviewed ALLOWLIST array for legit CJK (unicode test
    fixtures, docs about unicode handling).
  * Modes: staged (default) / `--all` (census) / explicit file list.
- Bypass for emergencies: `git commit --no-verify` — when used, the
  commit message MUST note the bypass + reason + what was verified
  manually (house rule, followed 9x during parallel tree execution).

## Test conventions that paid off

- Meept full-sweep on macOS MUST use `-p 2` (ephemeral port exhaustion)
  — every dispatch context repeated this and it held.
- Flaky suite FAILs: rerun `-count=1` twice before believing them. One
  leaf's single FAIL was flake (two clean reruns); record the flake call
  in the tracking table rather than "fixing" a passing test.
- `git log -L <line>,<line>:<file>` is the fastest attribution tool for
  lint findings — run it on each finding's file:line to separate
  "introduced by my tree" from "pre-existing/sibling" before fixing.
  During chat-dispatch-ux integration, all 6 findings in leaf-touched
  files attributed to sibling/pre-tree commits; zero were ours.

## Sibling-session concurrency patterns (2-4 sessions on one repo)

- Pre-commit hooks gate on the WHOLE repo: sibling WIP breaks your
  commit's build check. Pattern: commit with
  `git -c core.hooksPath=/dev/null commit`, after manually running the
  scoped checks the hook would have run, and note the bypass in the
  commit message.
- Working-tree hunks from sibling sessions interleave with yours in
  shared files. When forced to commit a file carrying foreign hunks
  (leaf deadline), name them in the commit message ("carries AUDIT FIX
  H1/C2 from sibling bughunt session") so the owning session can
  reconcile.
- `go.sum` conflict markers from stash dances: resolve with
  `git checkout HEAD -- go.sum` then `go mod download`; never commit a
  go.sum you didn't intend.
- git stash is DANGEROUS in multi-session trees — one stash pop
  produced `UU go.sum` conflicts that broke three sessions for minutes.
  Prefer worktree-scoped checks (`git stash push -- <paths>`) or just
  don't stash; test siblings' claims of "transient breakage" with
  `go build ./internal/<pkg>/` scoped runs.

## Scratch-daemon e2e pattern (scripts/e2e-naive-user-chat.sh)

Full recipe in the script itself; the non-obvious bits:

- Sandbox: `mktemp -d` for state+HOME+project; free HTTP port probed at
  runtime (never 18099/8081); daemon cwd deliberately != project dir so
  cwd-resolution bugs are observable; trap-based cleanup with SIGTERM→
  SIGKILL escalation; `--keep` flag for post-mortem sqlite forensics.
- Config gates: grep `if cfg.<X>.Enabled` in components.go and set
  every gate the transcript path needs (`multiagent.enabled` gates the
  whole AgentRegistry — without it: `specs=0`, "no agent available").
  A MINIMAL config is not a VALID config.
- Sync-dispatch trigger: `source_client` prefix `meept-bench` forces
  the sync path (handler.go ~722) — benchmark/e2e clients need FINAL
  results, not acks.
- Assertion hygiene: honest SKIP with printed reason for provider
  unavailability (never silent exit 0); distinct FAIL reason strings
  per assertion; "build failed → FATAL with log tail" so a broken tree
  fails at step 1 instead of producing false assertion results.
- macOS `/var` → `/private/var` symlink: path allowlists must include
  BOTH forms (`pwd -P` resolved + as-written) or security fences deny
  writes. Bit us once (file_write "access denied" on the project dir).

## Tool/skill authoring anchors (verified 2026-09-05, skill-authoring tree)

Recon-before-authoring checklist that produced a first-pass-compliant
tree (zero line-anchor drift at authoring):

- Read the target package's OWN test files for fixture patterns
  (discovery_test.go, registry_test.go, executor_test.go,
  setters_test.go) and cite them in the leaf: "mirror them, never
  invent a third fixture style." Kills fixture drift at the source.
- Verify anchors by grep BEFORE writing the leaf that cites them
  (webSearchTool := NewWebSearchTool at components.go:5490;
  initializeSkills call at :856; Skill struct at models.go:29). Leaves
  then carry "read X for the pattern" instead of "read X:NN" — line
  numbers rot, file+symbol anchors survive.
- Subprocess-backed tools (STT/whisper precedent): config-gated OFF by
  default, injectable command runner (Set* + nil guard) so tests never
  exec real Python/binaries, actionable install-guidance error strings.
- Agent self-modification tools = HIGH risk (require_confirmation_high
  gates them); observation tools = LOW. Classification is the security
  engine's job — the tool stays a pure capability, no confirmation
  logic inside the tool.
- Daemon construction order (tools init BEFORE initializeSkills) is a
  plan-time decision, not an implementation discovery: state the
  tolerance contract on the tool leaves and ONE preferred resolution
  on the wiring leaf, gated on a wiring test.
- When a leaf's "read the sibling leaf's file for conventions" would
  break parallel dispatch, pin the shapes in the master contracts
  instead (constructor style, test style) so both leaves mirror a
  SPEC, not each other's WIP.

## Operator-environment facts (2026-09-06 sessions, still current)

- The user's shell exports `AGNRES_API_KEY` (no second E) in
  ~/.bashrc:162; `AGNES_API_KEY` is commented out. Config files
  referencing `${AGNES_API_KEY}` get empty tokens → provider 401
  "未提供令牌". An "expired credential" verdict on a provider 401
  must first grep the shell rc files for the ACTUAL var name and diff
  it against what the config interpolates — a name mismatch presents
  identically to an expired key.
- The daemon's phase-dispatch/budget subsystems live behind
  `plans.parallel_phases` and `plans.plan_compiler_enabled` (JSON5,
  default false both). The live-run verification order: config parse
  check → rebuild+install binaries to ~/go/bin → restart daemon →
  grep startup log for the per-subsystem "wired/configured enabled="
  lines BEFORE believing a config edit took effect.
- Agnes free tier 429s under parallel load and intermittently 400s on
  handoff-continuation messages ("missing field `content`"); quota
  parking defers correctly. local/lfm-8b-q4 cannot emit valid
  multi-phase JSON — unusable as a spec_plan planner.
