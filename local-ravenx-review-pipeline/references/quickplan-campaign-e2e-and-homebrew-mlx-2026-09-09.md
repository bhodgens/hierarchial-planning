# Campaign Session Notes — classifier-iteration run (2026-09-09)

Session-specific detail backing the pattern additions in SKILL.md.
Environment: meept repo, branch classifier-iteration, macOS, scratch
daemon e2e on localhost HTTPS.

## Homebrew MLX broken-install diagnosis (python3.14)

Symptom: `python3 -c "import mlx.core"` → ModuleNotFoundError, while
`mlx.nn` partially imports. `pip`-side looked fine.

Diagnosis path that worked:
1. `brew list mlx | grep site-packages` — compare Cellar contents vs the
   linked `/opt/homebrew/lib/python3.14/site-packages/mlx/` tree. The
   Cellar copy had 41 files; the live tree had 0 (plus orphaned numpy
   husk dist-info dirs that shadowed numpy metadata — `importlib.metadata
   .version('numpy')` returned None, crashing transformers'
   `require_version` check with "Unable to compare versions").
2. Fix sequence: `brew reinstall mlx` → `brew unlink mlx && brew link
   --overwrite mlx` (58 symlinks created). The plain `link` refused
   (existing files); `--overwrite` is required.
3. numpy metadata husks: two license-only `numpy-2.5.x.dist-info` dirs
   with no METADATA sat in site-packages from an interrupted pip
   operation. Quarantined them under `~/.hermes/quarantine-numpy-husks/`
   rather than deleting. After removal: mlx.core, mlx_lm, transformers,
   sklearn all import cleanly on python3.14.

Lesson: when `import mlx` half-works, diff Cellar contents against the
live site-packages tree before touching anything else. A metadata-only
dist-info husk is enough to break transformers' version check even when
the real dist-info is intact.

## Scratch-daemon e2e for quickplan smokes

Config gotchas (meept):
- hujson requires ALL object keys quoted — a `^`-anchored key-quoting
  regex misses inline `{ enabled: true }` objects. Regex must match keys
  after `{` or `,` too.
- `transport.http.rest` is a BOOL in the schema (`HTTPTransportConfig
  .REST`), not an object. Omitting it → `RESTEnabled=false` at runtime →
  every `/api/v1/*` route 404s while `/health` still works. `DefaultServer
  Config()` sets RESTEnabled=true but daemon.go unconditionally overwrites
  from config (`httpCfg.RESTEnabled = fullCfg.Transport.HTTP.REST`).
- `require_auth: false` + no `api_keys` → server falls back to the
  per-installation dev key (`~/.meept/dev_key`, via
  `pkg/constants.DevAPIKey()`), which `os.UserHomeDir()` resolves to the
  REAL home, not MEEPT_HOME. Read the real `~/.meept/dev_key` for smoke
  auth. The legacy string `meept_dev_default_key_CHANGE_ME` is banned and
  returns 418.
- LFM2.5-8B runtime on the user's :8082 can be adopted rather than
  spawned: drop the `lifecycle` block and point the provider baseURL at
  the live port.

Smoke design:
- Smoke 1 (cue-bearing quickplan): the full plan-execute loop ran live
  (coder read real project files) but aborted at the coder's 50k
  conversation-token budget — default
  `DefaultConversationTokenBudget = 50000` (internal/agent/loop.go).
  Raise via `max_conversation_tokens` in the coder AGENT.md frontmatter
  (parsed by internal/agents/parser.go, merged in registry.go:968).
- Smoke 2 (ambiguous "fix it"): clarify path is real but LLM-chain
  nondeterministic — one run asked "describe what needs to be fixed",
  another executed directly. Classify variance as chain, not gate.
- Smoke 3 (gibberish): chat-style fallback response is CORRECT for
  content-free input; don't write checks that demand clarification.

## Two persistent-daemon bg processes kept dying mysteriously

Reference: a long-needed diagnostic for repeated unexplained daemon
deaths — the SFT prompt-contract (internal/agent/loop.go) and the daemon
build timestamp. "SFT prompt contract drift" was a red herring; the real
causes were unrelated to the daemon.

## Classifier-campaign state carried into this session

- Gold corpus: testdata/eval/classifier-adversarial-corpus.json5 (~370
  cases; 44+ quickplan anchors from iters 19-20).
- Adjudicated 48-case gold replay: untracked
  tools/classifier-eval/replay-gold.local.json5 (verbatim Hermes text —
  never commit). Distribution: quickplan 20 (42%), review 10, git 5,
  code 4, plan 3, analyze 3, debug 2, platform 1.
- 6 normative labeling rules in
  tools/classifier-eval/results/adjudication-record.md.
- Acceptance bar for M4 e2e replay: ≥ 86.8% (chain-only floor).
- iter-16's sampled-draw E2E (92.8%) was corrected to deterministic
  expected-credit (91.44%, fails bar) — see
  tools/classifier-eval/results/iter-16-corrected/report.md and the
  ITERATION-LOG correction note. Lesson: never `np.random.random() <
  baseline` for chain-destined credit; use deterministic
  `expected = count × baseline`.

## Queued decision: 100%-accuracy target

User asked to iterate to 100% collective accuracy. iter-20's finding:
the remaining replay misses all carry session-state signal (an approved
plan exists / tasks tracked) invisible to per-message classification —
100% first-stage accuracy is information-theoretically out of reach.
The architectural answer (shipped): quickplan cue guard + chain
fall-through + orchestrator session-state resolution at execution time.
