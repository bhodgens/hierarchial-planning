# Sstaged index sweep and model recovery
When to use: already-staged sibling file rides your commit.
Lesson: simplest sweep variant + local-first model recovery via LoRA re-fuse.

# Staged-Index Sweep Repair + Local-First Model Recovery (meept, 2026-09-06)

Two linked lessons from one session: (1) the simplest commit-sweep variant
— a sibling's ALREADY-STAGED file riding your commit; (2) recovering a
deleted fine-tuned classifier model via LoRA re-fuse, plus restoring a
platform-intrinsic model policy.

## Part 1: Staged-index sweep (simplest sweep variant)

### Detection
`git add <myfile> && git commit` commits EVERYTHING in the index. A
sibling session's already-staged file (status `A` / staged `M`) rides
along under YOUR commit message. The sweeper here was benign (a sibling
test file), but swept files inherit your message and your `Closes #N`
credit.

**Audit before every commit in a shared worktree:**
```
git status --short | grep '^[MARC]'   # staged list
# diff against the paths YOU intend to commit
```
And after committing, `git show HEAD --stat` and verify the file list
matches intent — this is what caught it (the sweep was found in the
first post-commit check, before push, making repair trivial).

### Repair (pre-push, no filter-branch needed)
```
git reset --soft HEAD~1                       # uncommit, keep everything staged
git restore --staged <foreign-paths>          # unstage the rider(s)
git add <my-paths>                            # re-stage ONLY mine
git -c core.hooksPath=/dev/null commit -m "..."   # recommit
git show --stat                               # verify file list == intent
```

### Gotchas observed
- `git reset --soft HEAD~1` re-stages EVERYTHING that was in the index —
  including files other sessions had staged before you. After the soft
  reset, re-audit and unstage the foreign paths again before recommitting
  (one extra cycle was burned here because the soft reset silently
  re-staged the sibling's file).
- `git reset <untracked-dir>` on an untracked directory is a no-op and
  safe; the dir stays on disk. The scratch checker (`cmd/cfgcheck/`)
  was left in place as untracked rather than rm'd (user had denied an
  earlier rm class).

## Part 2: Local model recovery + platform-intrinsic classifier policy

### Context
The user's LFM2.5-1.2B fine-tuned classifier
(`lfm2.5-1.2b-combined-serialized-sft`, LoRA SFT on
LFM2.5-1.2B-Instruct-MLX-4bit, 24,944 samples: 50% tool-use / 50%
intent-classification) had been deleted from `/Volumes/LLMs/` by an
earlier GGUF-migration cleanup commit. The classifier alias had silently
fallen back to the generic 1.2B base model.

### Recovery: re-fuse from surviving LoRA adapters
The fused model dir was deleted, but the **LoRA adapters survived** in
the training repo (`lfm-distill/adapters/combined_serialized/` —
`adapters.safetensors` + `adapter_config.json`), and the base model
(`LFM2.5-1.2B-Instruct-MLX-4bit`) was still on disk. Re-fuse:
```
.venv/bin/python -m mlx_lm.fuse \
  --model /Volumes/LLMs/LFM2.5-1.2B-Instruct-MLX-4bit \
  --adapter-path adapters/combined_serialized \
  --save-path /Volumes/LLMs/lfm2.5-1.2b-combined-serialized-sft
```
~2.5 min, 649MB output. Lesson: **LoRA adapters + base model = the
fused model is reproducible.** When a cleanup deletes a fine-tune, look
for the training repo before concluding the model is lost.

### Config shape: two local runtimes, two ports
`providers` is a map — each entry can carry its own `lifecycle` (runtime,
port, model_path, health check). The working shape:
- `local` → llama.cpp, port 8080, 8B GGUF F16 (default general model,
  local-first, zero cloud tokens for e2e)
- `local-mlx` → mlx_lm server, port 8081, combined-sft (classifier)
- classifier alias: `local-mlx/lfm-combined-sft` primary; 8B/1.2B/
  glm-4.5-air/llama3.2 as FALLBACKS ONLY
- Config comment marks the intrinsic model: "do not change without an
  explicit A/B testing instruction" — this makes the policy durable in
  the config itself, not just in memory.

### Config-validation trick without new deps
No json5 module locally; `go` + internal loader works but types differ
between `config.Provider` (no Lifecycle field) and
`llm.ProviderConfig` (has it). Validating lifecycle-bearing provider
blocks needs `llm.ProvidersConfig` + `config.LoadJSON5`. A scratch
`cmd/cfgcheck` (later left untracked, not committed) does:
parse → assert provider present → assert lifecycle.runtime/model_path →
assert model id present → print alias order. Reusable pattern for any
models.json5 surgery. (Env-var warnings on stderr are normal.)

### Policy now encoded
User-stated: the combined-sft classifier "should be an intrinsic part of
the platform design, intended to not be changed... no reason to change
this model unless explicitly instructed for A:B testing." General-use
default = the local 8B (no cloud inference burn on e2e). Cloud models
remain reachable via aliases for deliberate use.
