# Llive tool path smoke
When to use: newly wired tool fails live despite green tests.
Lesson: layered defects above a green tool path.

# Live Tool-Path Smoke — layered defects above a green tool

Worked example: meept transcript_fetch chain, 2026-09-07 (follow-up to the
skill-authoring-and-media-ingest + transcript-large-corpus trees). The
tool itself was unit-proven (22 fake-runner tests, wiring tests with
functional handle-liveness probes) — yet the FIRST live run through the
real agent loop failed, and unwinding it exposed FOUR defects, each in a
DIFFERENT layer above the tool. None was catchable by the tool's own
tests, by design.

## The core rule

A new tool's unit suite proves the TOOL. It cannot prove the PATH:
classifier routing → permission action map → schema visibility → model
arg-emission → subprocess environment. Budget a live smoke (orchestrator
plays the user, scratch daemon, real model) before declaring any
tool-chain tree done. Expect the smoke to find one defect per layer the
chain crosses; treat each as real, fix at its layer, re-run.

## The four defects (one per layer)

1. **Routing layer**: the LLM classifier scored "summarize this video:
   <youtube url>" as intent=code 0.95 (weak local model reads
   tool-shaped requests as code) → coder agent, which holds no
   transcript_fetch grant → tool unreachable. Fix: deterministic
   media_url_guard AHEAD of the LLM classifier (same pattern as the
   short-message guard) — a YouTube URL is an unambiguous structural
   signal; route it to the grant-holding agent by pattern, not by model
   opinion. Lesson: any tool whose trigger is a STRUCTURAL input pattern
   (URLs, file extensions, IDs) deserves a deterministic pre-LLM routing
   guard; small models misclassify these habitually.

2. **Permission layer**: ToolActionMap lacked the tool → checkPermission
   falls back to tool-name-as-action → no seeded rule matches → "Unknown
   action" denial. Fix: map the tool to its seed-rule action
   (network_request); assert in the existing TestToolActionMap. Lesson:
   a seeded security rule and an action-map entry are TWO separate
   registrations; registering a tool wires neither automatically. Note
   the asymmetry: tools whose seed-rule Action EQUALS their own name
   (skills_create) need no map entry — the fallback resolves by luck of
   naming. Document which case each new tool is.

3. **Schema-visibility layer**: indexed schema mode (the registry
   default via SetSchemaModeConfig) stubs non-core tools to a one-line
   description with an EMPTY parameter schema. The model literally had
   no `url` parameter to fill → called with {} → "no URL specified" →
   no-progress nudging → cycle abort. Fix: add the tool to
   DefaultAlwaysFullTools(). Lesson: multi-param tools with distinct
   types cannot live behind indexed mode; a one-liner description is
   fine for zero-arg tools only. Symptom signature: tool called with
   EMPTY/absent args repeatedly, then cycle-abort.

4. **External-dependency layer**: the embedded `python3 -c` script
   targeted the pre-1.0 static API (YouTubeTranscriptApi.get_transcript),
   removed in installed v1.2.4 (instance methods). The fake-runner tests
   are API-shape-agnostic BY DESIGN — so nothing ever validated the real
   script. Fix: instantiate the API (v1.x shape), normalize dict/object
   segments. Lesson: an embedded script that shells out to an external
   package needs a REAL-subprocess probe test (in-package _test.go with
   the real runner, no fakes) or its drift is invisible until production.
   The leaf's own Notes warned the CLI had churned — warnings don't
   execute.

## Layer-isolation probe pattern (how to unwind it)

When the live run fails, bisect the layers with probes instead of
guessing:

- **Direct-LLM probe**: call the model API directly with the tool's
  exact registry schema (temporary in-repo cmd/*-probe with
  internal-package access). Proves/disproves "the model emits correct
  args with this schema." Real result: glm-4.5-air emitted PERFECT args
  twice — so the daemon path, not the model/schema, was dropping them.
- **Direct-tool probe**: in-package test invoking the tool with the real
  runner (no fakes) — proves/disproves tool + subprocess + network.
  Real result: 8,960-char transcript fetched live; output_path wrote
  full bytes; preview 1,132 chars.
- **Daemon-log layer evidence**: `Dispatched request ... method=`
  (routing), `Tool blocked by security reason=` (permission), the
  tool's own error string (schema/args), subprocess exit codes
  (dependency).

Each probe eliminates a layer; whatever remains is the defect. This
turned "the chain doesn't work" into four one-line-root-cause fixes.

## Environment gotchas specific to live smokes

- **pip --user installs are $HOME-dependent**: user site-packages live
  under ~/Library/... (macOS), so a scratch daemon launched with an
  alternate HOME cannot import them. Fix: PYTHONPATH pointing at the
  real user site-packages in the daemon env, or a venv. Symptom:
  "No module named X: exit status 2" from the daemon while the same
  import works in your shell.
- **Agent-spec resolution is CWD-first**: resolveBundledPath("config/agents")
  checks CWD, then exe-dir, then gives up — a scratch daemon launched
  outside the repo with no config/ copy has NO custom agent roster
  (default roster only; your AGENT.md grants don't exist). Copy
  config/agents (+ skills) into the scratch dir in a config/ subdir.
- **Stale smoke binary**: after fixing + rebuilding, the scratch daemon
  may still run the OLD binary (dispatch kept logging the old
  classification_method). Verify binary mtime postdates the fix
  commits before interpreting a re-run; the same trap is documented in
  forensic-run-attribution.md and it STILL recurred here.
- **Session persistence across daemon restarts**: the CLI reuses the
  last session (per cwd/HOME), so a restarted daemon resumes a STALE
  conversation where the model is already committed to a failed
  strategy (kept web_searching a dead end). Use a fresh HOME (or
  session reset) to get a clean conversation before judging fixes.
- **Weak local models cannot emit tool calls**: the local MLX primary
  returned empty/reasoning-only content every iteration, tripping the
  streak terminator before any tool call. For a live TOOL-path smoke,
  point the smoke config's default model at a model known to emit
  tool-call JSON (cloud fallback in this case). A tool-path smoke
  against a model that can't call tools proves nothing about the tool.
  (Follow-up: the streaming-path LFM marker shim + the watchdog's
  disable-thinking rescue turn — see below — may now let local models
  clear this bar; re-test before assuming the cloud crutch is still
  needed.)
- **Smoke-daemon debris is consent-gated**: `rm -rf` of the smoke dir
  and probe commands may be denied repeatedly; leave the dir, name it
  in the report, and hand the removal command to the user. Do not
  count these denials as smoke failures.
- **User config changes under you**: the user may flip model slots
  (e.g. classifier primary) between your runs; pin smoke expectations
  to the scratch config copy you control, and re-check the live config
  before attributing behavior changes to your code.

## Success criterion: the loop-level chain, not just one live reply

The smoke above still ended in "max turns completed / stopped after
extended thinking" on local models — and the follow-up deep-dive found a
FIFTH layer plus a watchdog improvement:

5. **Streaming-path layer (deepest)**: the LFM2.5 marker-recovery shim
   (parseLFMToolCalls) had been wired only in the non-streaming `Chat`
   path. The agent loop ALWAYS streams — reasoningCycle passes a
   streamOnDelta for every turn, so every agent-side call goes
   `ChatWithDeltaCallback` → `doStreamRequest`, which never applied the
   shim. Markers reached the loop as unexecutable content; the loop
   nudged and died before any tool call. The classifier/summarizer
   (non-streaming) worked, which MASKED the gap. Lesson: any
   content-recovery/shim/normalization added to one LLM call path must
   be applied to BOTH `Chat` and `doStreamRequest` — in meept the agent
   loop never uses the non-streaming path, so a non-streaming-only fix
   covers nothing that matters. When a fix "works in probes but not the
   daemon", diff the two call paths.

   Companion improvement (same smoke): the reasoning-only watchdog
   (two consecutive reasoning-only replies → terminate) now runs one
   RESCUE turn with `llm.DisableThinking()` appended after the agent's
   reasoning opts (single reasoning pointer, last-apply wins) plus a
   firmer nudge — thinking-mode local models (LFM2.5 on mlx_lm) put the
   whole reply in reasoning_content by template default, and disabling
   thinking for the retry forces visible output. The rescue is once per
   turn; a reasoning-only reply from the rescue itself terminates
   immediately. General pattern: when a watchdog terminates for a
   DETERMINISTIC model-mode failure, retry once with that mode toggled
   off before giving up — retrying unchanged is guaranteed to re-fail.

Also note the config-drift tail: flipping the classifier alias primary
(lfm-8b-mlx, per the 86.8%-vs-54.4% A/B) updated config/models.json5 but
left `TestConfigLoads`' assertion pinning the old combined-sft primary —
config flips and their test assertions must land in the same commit.

## Sequence that worked (reusable)

1. Config: enable gates in the scratch config; copy models.json5 +
   config/agents + config/skills into the scratch layout.
2. Build scratch binaries fresh; launch daemon with the real env vars
   the config references (API keys) + any PYTHONPATH the tool needs.
3. Grep the daemon log for the tool's registration + any
   "summarize enabled"-style wiring lines BEFORE sending traffic.
4. Send the user-shaped message; on failure, run the probe pattern
   above; fix one layer at a time; rebuild + restart + re-send.
5. Success criterion: the daemon log shows the tool's own success
   evidence (args_summary with real args, success counters), and the
   chat reply reflects the tool's output.
