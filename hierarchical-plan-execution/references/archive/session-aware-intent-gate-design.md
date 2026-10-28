# Ssession aware intent gate design
When to use: session-aware intent gate design.
Lesson: user-addressed agents query session state; forensics-derived follow-up stack.

# Session-Aware Intent Gate (meept, 2026-09-05) — Design Record

The reference implementation for context-conditioned ambiguity gating.
Tree: docs/plans/session-aware-intent-gate/ (3 leaves, all COMPLETE:
f1b50205, 6bcb53c2, + leaf 03 e2e verify).

## Problem

Chat follow-ups like "did the change get made? where is the file?" got
canned clarification requests ("Which specific change? What file?") even
immediately after a task created the file. The dispatcher's intent
analyzer (dispatcher.go:667 → AnalyzeTrueIntent → IsAmbiguous(0.6) →
buildClarificationResult) judged each message IN ISOLATION: its LLM call
sent only {system prompt, raw input}. Restored conversation history (the
session-continuity fix) never reached the model because the gate fired
BEFORE any agent was invoked.

## User's architectural principle (verbatim intent)

"Agents that directly interact with the user do need to have context of
the session, but the session itself should not have any context for what
other agents are doing unless they provide it (or they're queried to
provide it)."

Mapping: the intent analyzer IS a user-addressed agent (its clarifying
questions go to the user), so it QUERIES session state at turn time.
Task-scoped worker loops stay isolated — the session absorbs only the
final user-facing summary (already mirrored by session-continuity leaf
01). No session-default model: the analyzer keeps its small classifier
model; only its INPUT changes.

## Design

1. SessionContextDigest (session_digest.go): {LastTaskName, LastTaskState,
   LastTaskAgent, LastResultSummary, LastIntentType}. Built per turn from
   existing stores: TaskStore.GetTasksForSession (updated_at DESC → [0] is
   most recent), TaskRegistry.StepStore().ListByTaskID → terminal step
   Result (reuse bestStepResult), SessionTracker.GetLastIntent. Caps: name
   200, result first-line 400. All store access nil-guarded; errors →
   Debug log + empty field; NEVER propagate.
2. AnalyzeTrueIntent(ctx, input, sessionContext *SessionContextDigest):
   nil/empty digest → byte-identical contextless messages (wire-proven
   via httptest capture server). Non-empty → append to user message:
   "\n\n[Recent session activity]\nLast task: <name> (state: <state>,
   agent: <agent>)\nResult summary: <summary>" (empty segments/lines
   omitted — no dangling newlines). System prompt (EVERY call) gains:
   resolve pronouns against recent activity; short follow-ups about that
   activity → ambiguity LOW, don't re-ask.
3. Both dispatcher call sites (~665 fresh input, ~1266 post-clarification)
   build the digest BEFORE the analysis call.

## Deliberately NOT done (user-approved non-goals)

- No threshold change (stays 0.6). No keyword lists ("the change", "it").
  No new config. The model decides from context.
- Task-scoped loop transcripts never enter the session conversation
  beyond the final summary.

## Testing pattern that worked

IntentAnalyzer holds a concrete *llm.Client (not stubdable), so:
- factor message-building into buildAnalysisMessages(input, digest)
  []llm.ChatMessage and unit-test it directly (hermetic), AND
- prove wire behavior with an httptest capture server behind a real
  *llm.Client (pattern from classifier_failover_test.go) — this is what
  makes the "byte-identical contextless" claim test-proven.
- Dispatcher has a real analyzer seam (ClassifierClient), so its test
  seeded the task store and asserted the activity block appears in the
  SENT user message — stronger than argument-capture.

## Production evidence from the 15-run e2e campaign (2026-09-06)

Supersedes the design-only record above; every claim is from a `--keep`
workdir (daemon.log + sqlite + replies), not unit tests.

- Gate fix confirmed twice live (runs 3, 11): T3 "did the change get
  made? where is the file?" routed as `intent_type=report` with NO
  `Requesting clarification` line. Survives production, not just
  httptest.
- Digest + restored history reached the model: run 11 T3 cited the task
  by name and completion state; run 8 T4 cited "a file named hello,
  from the task tracker... marked completed"; run 11 T4 produced the
  full artifact answer — exact absolute path, byte size, contents,
  originating task.
- After the fix, NO A5 failure was attributable to the gate. Residual
  families: (1) provider windows — zai 429s and `empty content`
  rotations; (2) weak-fallback misjudgments — ambiguity 0.6-0.9 on
  concrete instructions from 1.2B/8B locals; (3) sync latency —
  plan-mode + slow model exceeded the 300s MCP turn timeout (env
  `MEEPT_E2E_TURN_TIMEOUT` exists for this); (4) once, the assertion
  heuristic — a correct answer containing '?' FAILed the
  `contains '?'` rule (relaxing when artifact reference present is
  parked with the user).
- Cross-tree payoff same-session: `meta.session_digest_used=true`
  visible in captured replies the day classifier-observability leaf 01
  (cb8031f3) landed.

## Forensics-derived follow-up stack (user-aware, not scheduled)

From run-10 READ-ONLY forensics (zero 429s despite the quota narrative;
see SKILL.md attribution rule):
1. Suspicious-success cross-check — weak model returning intent=platform
   conf=1.0 on an imperative create-file request should trigger a
   keyword/heuristic cross-check before dispatching. Keyword fallback
   alone would NOT catch it: length-normalized score 0.8×13/109 ≈ 0.12
   < 0.3 threshold (dispatcher.go:2195).
2. Analyzer per-call timeout — none (raw ctx, intent_analyzer.go:186);
   28s waits observed on slow fallbacks.
3. Alias order is quality-worst-first: 1.2b-q8 → 8b-f16 → glm-4.5-air
   (models.json5:24-34). Reorder or route per-call.
4. Split the shared classifier *llm.Client — analyzer rotation silently
   re-points the ROUTER (components.go:813-835 → dispatcher.go:366-407).
   Root cause of the T1 platform-misroute.
5. Path-in-summary — task-result summary carries evidence JSON, not the
   artifact path; sharpest residual A5 blocker.
6. task_get with empty args should return a session listing, not
   error → 3× repeat → cycle-abort (killed report turns twice).

## MLX restoration (2026-09-06, post-campaign) — config archaeology payoff

The campaign's "weak 1.2B classifier" dead-end led to config archaeology
(git log -S on models.json5): the July 7 GGUF-migration commit (c1a6b1b1)
had DEMOTED the classifier primary 8B→1.2B and DELETED the user's custom
SFT fine-tune (lfm2.5-1.2b-combined-serialized-sft, trained in
~/git/lfm-distill: LFM2.5-1.2B-Instruct-MLX-4bit base + combined_serialized
LoRA adapters, 24,944 samples, 5k iters). The July switch itself was a
workaround for an MLX SIGKILL whose true root cause (StartAll context
cancellation killing fresh runtimes) was only fixed 2026-09-03 (a5312a64,
context.WithoutCancel) — the same bug had hit llama.cpp, confirming MLX
was never inherently broken. User decision: MLX is the platform runtime on
Apple metal; combined-sft is the intrinsic classifier (change only for
explicit A/B); e2e/general default is LFM2.5-8B MLX 4-bit (local-first, no
cloud tokens).

Restoration sequence that worked:
1. Weights "lost" = fused output deleted; LoRA adapters + adapter_config.json
   survived in the training repo. Re-fuse: `mlx_lm.fuse --model <base>
   --adapter-path adapters/combined_serialized --save-path
   /Volumes/LLMs/lfm2.5-1.2b-combined-serialized-sft`.
2. Config: new `local-mlx` provider (:8081, runtime mlx, combined-sft) as
   classifier alias primary; `local` provider re-pointed to 8B MLX 4-bit on
   :8082 as general default (commit 812a0555, later 277ae1f8). Verify with
   a throwaway cmd/cfgcheck probe using llm.ProvidersConfig (config.Provider
   lacks the Lifecycle field) + LoadJSON5.
3. Scratch-daemon smoke: grep "Resolved model alias ... classifier ... /
   Volumes/LLMs/lfm2.5-1.2b-combined-serialized-sft", confirm the mlx_lm
   process spawns, /health answers, send one chat, check
   `classification_method=llm` with zero rotations.

### NEW failure class the MLX switch exposed: runtime-port collision

mlx servers bind FIXED ports (:8081 classifier, :8082 general). The user's
LIVE daemon holds :8081 with its old-config llama-server — so the e2e
scratch daemon's mlx_lm either failed to bind or its health/requests hit
the LIVE 1.2B. Symptom identical to provider degradation (empty content,
weak verdicts) and it reproduced across runs until port forensics
(lsof :8081 vs the scratch config) caught it. Fix: e2e script remaps MLX
ports off the probed HTTP_PORT (af797c03) — the same isolation it already
did for HTTP. Rule: any config with fixed local runtime ports needs
per-instance port remapping in scratch/test harnesses, and leftover smoke
runtime processes must be killed before runs (they hold ports).

### LFM2.5 on mlx_lm: native tool-call markers unparseable (fixed in meept)

mlx_lm 0.31.3 server has NO tool-call extractor: LFM2.5 emits
`<|tool_call_start|>[file_write(path="hello.txt", content="hello")]
<|tool_call_end|>` as plain content with tool_calls null. Agent loop sees
an unexecutable string → nudge ladder → "stopped after extended thinking"
non-answers wrapped in raw job envelopes (that reply-shaping issue is the
envelope, distinct from this). llama.cpp HAS an LFM2.5 extractor — why
GGUF agentic turns worked. meept fix: parseLFMToolCalls in
internal/llm/lfm_tool_calls.go (client.go parseResponse, pre-empty-check;
quote-aware kwarg parsing, markers stripped, merged into ToolCalls;
483fffe5). NOTE: the first post-fix e2e still failed — because of the
port collision above, NOT the parser. Verify one layer at a time before
re-attributing.

### Final acceptance state (2026-09-06, post-restoration)

First fully-clean-stack e2e in flight at session end (make e2e-chat,
commit af797c03): 8B MLX general + combined-sft classifier + isolated
ports + marker parser. All prior A5 confounders (cloud quota, 1.2B judge,
wrong-server collision) structurally eliminated. A5 `?`-heuristic
relaxation (answer + '?' but names artifact) still parked with the user;
envelope reply-shaping (follow-up #5 above) still the known cosmetic gap.
