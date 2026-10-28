# Mmlx restoration model archaeology 2026 09 06
When to use: silently degraded classifier config.
Lesson: git archaeology, LoRA re-fuse, per-runtime provider isolation.

# MLX Restoration & Model-Config Archaeology (meept, 2026-09-06)

Session record for: restoring the platform-intrinsic classifier after a
migration commit silently degraded it, and switching the general model to
MLX. The class-level recipe lives in SKILL.md ("Config-faithfulness gates
for model/runtime changes"); this file is the session detail.

## What the config archaeology found

- **Pre-July 7** (`c1a6b1b1~1`): classifier alias primary was
  `local/lfm-8b-4bit` (LFM2.5-8B-A1B-MLX-4bit). The 1.2B was Fallback 1
  carrying the "Best overall (69.1% accuracy)" comment. The chain also
  contained `lfm-combined-sft` (the custom SFT classifier) and
  `lfm-thinking-claude`.
- **July 7** (`c1a6b1b1`, "MLX runtime fixes and switch to llama.cpp
  GGUF"): MLX→GGUF runtime swap. Side effects nobody decided: classifier
  primary demoted 8B→1.2B; the "Best overall" comment MOVED onto the 1.2B
  line (it described the 1.2B's benchmark role as fallback, so the comment
  was accidentally accurate but the demotion wasn't deliberate);
  `lfm-combined-sft` dropped from the chain; its fused weights
  (`/Volumes/LLMs/lfm2.5-1.2b-combined-serialized-sft`) later deleted from
  disk.
- **Why the runtime swap happened at all**: `mlx_lm server` managed by the
  daemon received SIGKILL ~10s after healthy (doc:
  `docs/issues/2026-07-07-mlx-runtime-sigkill-issue.md`). Root cause found
  Sep 3 (`a5312a64`): `StartAll` goroutine's ctx was cancelled on return;
  `exec.CommandContext` bound to it killed the freshly-loaded runtime.
  Fix: `context.WithoutCancel` in `runtime_process.go` — applies to ALL
  runtimes. MLX was never broken; its supervisor was.
- **The May 22 eval** (`8d953c81`, benchmark in
  `meept-parity/docs/eval/classifier-comparison-report.md`, 136 examples):
  combined-sft scored WORST (36.8% acc, 29.4% err) vs thinking-claude
  (58.8%) and 1.2b-instruct-4bit (69.1%). So the 1.2B promotion was
  evidence-backed for *intent classification accuracy* — but (a) the
  benchmark never measured ambiguity judgment, and (b) the user's standing
  decision is that the fine-tuned classifier is platform-intrinsic;
  changes require explicit A/B instruction. User decision overrides the
  old eval; re-benchmarking on restore is the honest follow-up.

## What was done to restore

1. **Weights**: no HF repo (it's a local fine-tune). Found the LoRA
   adapters in `~/git/lfm-distill/adapters/combined_serialized/`
   (adapters.safetensors + adapter_config.json; base =
   `/Volumes/LLMs/LFM2.5-1.2B-Instruct-MLX-4bit`, still on disk).
   Re-fused: `mlx_lm.fuse --model <base> --adapter-path
   adapters/combined_serialized --save-path
   /Volumes/LLMs/lfm2.5-1.2b-combined-serialized-sft` (649MB, ~2.5min).
2. **Config** (`config/models.json5`):
   - New `local-mlx` provider: runtime mlx, port 8081,
     model_path = the re-fused dir, `mlx_lm server` spawn command,
     auto_start + health check + restart policy. Model id:
     `local-mlx/lfm-combined-sft`.
   - `gala-mlx` removed from `disabled_providers`.
   - classifier alias: combined-sft PRIMARY; 8B → 1.2B → glm-4.5-air →
     llama3.2 as fallbacks only.
   - General default model → `local/lfm-8b-mlx-4bit`: second provider
     block (`local`) switched runtime llama-cpp→mlx, port 8080→8082,
     model_path → `/Volumes/LLMs/LiquidAI/LFM2.5-8B-A1B-MLX-4bit`.
     One runtime process = one model, so two local models need two
     provider blocks on distinct ports.
   - All `local/lfm-8b-f16` references replaced with the new id
     (default model line + classifier/summarizer alias slots).
3. **Verification** (no e2e): throwaway `cmd/cfgcheck` main using
   `config.LoadJSON5` + `llm.ProvidersConfig` (note: config.Provider
   struct has NO Lifecycle field — llm.ProviderConfig does). Then a
   scratch-daemon boot: grep "Registered runtime config" (both providers,
   distinct ports), "Resolved model alias component=classifier-llm" →
   fused dir; trigger a chat → `mlx_lm server` spawns lazily,
   `/health` on 8081 returns ok, dispatch line shows
   `classification_method=llm` with ZERO alias failures/rotations.
4. Cleanup: `git worktree remove --force` the HEAD worktree used to build
   a clean binary (main worktree had sibling WIP breaking `go build`),
   pkill the smoke mlx_lm process, rm the scratch dir.

## Pitfalls hit

- `go build ./cmd/meept-daemon` failed on sibling WIP
  (`provider_manager.go` undefined symbols). Workaround: build from a
  `git worktree add /tmp/... HEAD` checkout.
- `config.Provider` (internal/config) lacks Lifecycle; the lifecycle-aware
  struct is `llm.ProviderConfig` (internal/llm/providers.go). Use
  `llm.ProvidersConfig` for config verification.
- `mlx_lm fuse` deprecation warning: use `python -m mlx_lm fuse` form.
- A sibling's staged test file rode into the first config commit (staged-
  index sweep, simplest variant): `git reset --soft HEAD~1` → `git reset`
  (unstage all) → re-add ONLY the intended path → recommit. Verify with
  `git show HEAD --stat` immediately.
- User memory of model selections was CONFIRMED by git archaeology even
  though current config contradicted it — trust the archaeology, not
  current config, when the user says "we chose X".

## Open items

- Re-run the May benchmark harness against restored combined-sft
  (esp. the weak categories: platform 0%, review 25%, recall 33%) if the
  user wants fresh evidence.
- A5 e2e certification under the new local-first config (parked, user's
  call on the `?`-heuristic).
- Update `docs/issues/2026-07-07-mlx-runtime-sigkill-issue.md` with the
  Sep 3 root cause + resolution.
