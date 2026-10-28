# Mmlx local runtime 2026 09 06
When to use: MLX runtime restoration.
Lesson: remap EVERY fixed port (lsof first), LFM tool-call shim, health-gate spawns, LoRA adapters are the artifact.

# MLX Restoration: Local Runtimes, Port Collisions, LFM Tool-Call Parsing (2026-09-06)

Follow-up session to meept-execution-receipts.md. Covers the MLX platform
restoration on meept: runtime config, the two port/parsing failure modes
that masqueraded as provider degradation, and the smoke protocol.

## Platform design (user-held invariant, verbatim intent)

- MLX on Apple metal, llama.cpp on Linux/Windows. Per-provider `lifecycle`
  blocks in `config/models.json5` (`runtime: "mlx"` vs `"llama-cpp"`).
- `local-mlx` :8081 = classifier runtime. PRIMARY CHANGED 2026-09-06 by
  A/B evidence (86.8% vs 54.4% corpus accuracy): classifier alias primary
  is now `local/lfm-8b-mlx-4bit`; combined-sft stays registered as the
  A/B alternate in the fallback chain. (The earlier note "combined-sft,
  changed ONLY for explicit A/B testing" described the pre-flip policy —
  the flip happened in the A/B session and stuck per its evidence.)
- `local` :8082 = general model (LFM2.5-8B-A1B MLX 4-bit).
- Cloud providers stay configured but the active default/general/alias paths
  are fully local (zero tokens for e2e).

## Weight recovery: fused outputs are disposable, adapters are the artifact

The July GGUF migration deleted `/Volumes/LLMs/lfm2.5-1.2b-combined-serialized-sft`.
The weights were a LOCAL fine-tune — not on HuggingFace. Recovery:
`~/git/lfm-distill/adapters/combined_serialized/` (LoRA adapters + Makefile
fuse targets survived) →

```
mlx_lm.fuse --model /Volumes/LLMs/LFM2.5-1.2B-Instruct-MLX-4bit \
  --adapter-path adapters/combined_serialized \
  --save-path /Volumes/LLMs/lfm2.5-1.2b-combined-serialized-sft
```

Lesson: for locally fine-tuned models, the adapters + training repo are the
source of truth; never assume the fused directory will survive migrations.

## Failure mode 1: runtime-port collisions masquerade as provider degradation

`config/models.json5` hardcodes :8081/:8082. The e2e script isolates its
HTTP port but originally NOT the runtime ports. The scratch daemon spawned
mlx_lm on :8081 — already held by the USER'S LIVE daemon's old-config
llama-server — so the scratch classifier's health checks and traffic hit
the live 1.2B GGUF (or failed to bind). Symptoms: empty-content replies,
weak/wrong verdicts, reasoning-only streaks — identical to provider
degradation. 15 runs of misattribution before `lsof -i :8081` settled it.

Fix: the e2e script remaps both ports off the probed HTTP_PORT
(HTTP_PORT+1/+2) in the sandboxed models.json5 — rewriting BOTH the
`baseURL` and the `spawn_command` `"--port"` entries.

Rule: ANY scratch daemon must remap EVERY fixed port its providers declare,
not just HTTP. Diagnose port ownership first: `lsof -i :<port>` — whose
process, whose `--model` path?

## Failure mode 2: mlx_lm does not parse tool-call formats

LFM2.5 emits tool calls as native markers:

```
<|tool_call_start|>[file_write(path="hello.txt", content="hello")]<|tool_call_end|>
```

llama.cpp ships an LFM2.5 extractor (GGUF agentic turns work); mlx_lm
server returns the markers as plain `content` with `tool_calls: null`. The
agent loop sees an unexecutable tool call → "LLM returned empty content" →
"Reasoning-only streak breached" → graceful give-up ("stopped after
extended thinking without producing output") — while the task still
finalizes `completed` with that non-answer as the result.

Fix: `internal/llm/lfm_tool_calls.go` `parseLFMToolCalls` — regex-recover
markers, parse Python-style kwargs (quote-aware comma split, typed numbers/
booleans), strip markers, merge into Response.ToolCalls BEFORE the
empty-content check in `parseResponse`. Tests:
`internal/llm/lfm_tool_calls_test.go`. Direct-probe recipe to confirm this
class of failure: curl the runtime's `/v1/chat/completions` WITH `tools`
and check whether `tool_calls` is null while `content` contains the
markers.

## Startup race: runtimes spawn asynchronously

The daemon registers runtime configs at boot but spawns/serves lazily. A
classification ~2s after daemon-ready hits connection-refused / partial
load, burning resolver cooldowns and rotating to fallbacks (including
GGUF-paths-on-MLX → HTTP 404 "Not a directory: .../config.json"). The e2e
script now polls each remapped runtime's `/health` up to 120s before T1.
Any harness driving a local-runtime daemon needs the same health gate.

## Smoke protocol that worked (end-to-end, ~15 min)

1. Temp HOME; copy repo `config/models.json5` into `$HOME/.meept/`; remap
   runtime ports (avoid live daemons AND leftover smoke servers —
   `pgrep -fl mlx_lm` first).
2. Build daemon+CLI from a `git worktree` at HEAD (main worktree may carry
   sibling WIP breaking `go build`).
3. Seed `config/agents/.` into `$HOME/.meept/agents/` and RESTART the
   daemon after seeding (the agent registry loads specs at boot; specs=0
   means you seeded too late).
4. Verify: log shows `Resolved model alias ... model=<expected path>` for
   the classifier; both `mlx_lm server` processes spawn on their remapped
   ports; `/health` returns `{"status":"ok"}`; one `meept chat` turn logs
   `classification_method=llm` with zero alias failures.

## Open item: combined-sft routing instability

Run-to-run variance: identical create-file prompts scored `intent=code`
in one run and `intent=schedule` in another; schedule misroutes land in
the scheduler agent, which accepts tasks and leaves them `pending`
forever (silent death — it queues, never executes). The May 2026
benchmark (`meept-parity/docs/eval/classifier-comparison-report.md`)
rated combined-sft worst (36.8% acc). User owns the model choice
(platform-intrinsic); open options: benchmark re-run with an updated
corpus, a dispatcher guardrail on schedule-vs-imperative-verb verdicts,
or SFT round 2 with the failure categories.

## Resolution update (2026-09-07, second pass): watchdog rescue turn + stale-test tail

Two more items closed after the streaming hole was patched:

1. **Reasoning-only watchdog now rescues with thinking disabled
   (eb5563ff)** — instead of terminating on the second consecutive
   reasoning-only reply, the loop runs ONE rescue turn with
   `llm.DisableThinking()` appended after the agent's reasoning opts
   (single reasoning pointer, last-apply wins) plus a firmer nudge.
   Thinking-mode local models (LFM2.5 on mlx_lm) put the whole reply in
   `reasoning_content` by template default; the 2026-09-03 probe proved
   `enable_thinking=false` yields clean output. The rescue is once per
   turn: a reasoning-only reply FROM the rescue terminates immediately
   (rescued=true also leaves streakBreach=true, so the post-rescue
   breach sees both and terminates — do not reset streakBreach in the
   rescue branch, or the post-rescue reply reads as a fresh streak and
   nudges forever). Tests: guards_test.go
   `TestGuards_ReasoningWatchdog_Integration` (updated to the
   rescue-succeeds sequence) + `..._RescueFails_Terminates`.
   General pattern: when a watchdog terminates for a DETERMINISTIC
   model-mode failure, retry once with that mode toggled off before
   giving up — retrying unchanged re-fails identically.

2. **Stale classifier assertion** — `TestConfigLoads` still pinned
   combined-sft as classifier primary after the A/B flip to
   lfm-8b-mlx; fixed (ccc93f62) to track the flipped primary with the
   A/B rationale in a comment. Rule: a config flip and its pinning
   test assertion land in the same commit.

## Resolution update (2026-09-07): shim had a streaming hole — closed

The A/B session (2026-09-06) flipped the classifier primary to
`local/lfm-8b-mlx-4bit` per benchmark evidence (86.8% vs 54.4%);
`providers_config_test.go` `TestConfigLoads` still expects
combined-sft and now fails against the live user config — pre-existing
drift, not a regression when seen failing (subsequently fixed,
ccc93f62).

The tool-call shim (483fffe5) covered ONLY the non-streaming `Chat`
path. The agent loop ALWAYS streams — `reasoningCycle` passes a
`streamOnDelta` for every turn → `ChatWithDeltaCallback` →
`doStreamRequest` — so every agent-side tool call from an MLX-served
LFM2.5 model still reached the loop as unexecutable marker text: empty
content, nudge streak, "stopped after extended thinking". This is why
classification kept working while agentic tool use kept failing.

Fix (5e7625d1): `doStreamRequest` applies `parseLFMToolCalls` to the
accumulated streamed content and appends recovered calls, mirroring the
non-streaming path. Test: `client_lfm_stream_test.go` streams markers
as SSE deltas and asserts the recovered call + stripped content.

Lesson for shims generally: when a recovery shim guards a response-
parsing contract, enumerate EVERY transport variant of that contract
(streaming AND non-streaming, per-provider request shapes) and wire each,
or the unfixed variant keeps producing the original symptom through the
most common code path.
