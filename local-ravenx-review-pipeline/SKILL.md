---
name: local-ravenx-review-pipeline
description: "Mandatory post-delegation review pipeline for local-only Hermes profiles: subagent work on one model gets reviewed by a stronger coding model before reporting to user."
version: 1.0.0
author: agent
platforms: [macos, linux]
metadata:
  hermes:
    tags: [hermes, local-models, code-review, delegation, multi-agent]
---

# Mandatory Review Pipeline for Local Profiles

When running Hermes with local models, enforce a review step where subagent work is validated by a stronger model before reporting to the user.

## Architecture

```
Primary (orchestrator) -> delegate_task -> Subagent (worker model)
                                                |
                                          returns summary
                                                |
                                        Review by specialist model
                                                |
                                    approved -> report to user
                                    changes_needed -> fix or re-delegate
```

## Prerequisites

- Two or more local model endpoints (e.g., llama.cpp servers)
- One model strong at code review (high LCB score)
- One model strong at tool use (high tau2 score) for subagent work
- Hermes profile with delegation configured

## Setup Steps

### 1. Create the review script

Place at `~/.hermes/profiles/<profile>/scripts/reviewer.py`. Key design points:

- Accepts `--task` (description) and `--file` or `--stdin` (work to review)
- Sends to review model with `chat_template_kwargs: {"enable_thinking": False}` for MTP models
- Returns JSON: `{"verdict": "approved"|"changes_needed", "issues": [...], "corrections": "..."}`
- Exit code 0 = approved, 1 = changes_needed
- Truncates work content to ~12K chars to stay within review model context
- Handles non-JSON responses gracefully (soft approval with low confidence)

### 2. Write SOUL.md enforcement

The SOUL.md (loaded fresh every message) must contain:

1. **Clear pipeline diagram** showing the mandatory review step
2. **Exact execute_code snippet** the model should use to call the review script
3. **Decision logic**: approved -> report; changes_needed -> fix or re-delegate
4. **Exemptions**: trivial tasks, pure lookups, user-specified skips
5. **Trust calibration**: note which benchmark the reviewer excels at (LCB for code, not tau2 for agentic)

### 3. GPU contention handling

If the reviewer and subagent share GPU resources:
- The pipeline naturally avoids contention: review runs AFTER subagent completes
- Set `delegation.max_concurrent_children` to 2 (not 3) to reduce sustained load
- Consider reducing `delegation.child_timeout_seconds` if the shared GPU is slow

## Verification

Test the pipeline with a deliberately buggy snippet:

```python
from hermes_tools import terminal, execute_code
# Write buggy code, run reviewer, confirm it catches the bug
```

Then test the full flow:
```
hermes -p <profile> chat -q "Write [task]. Have [reviewer] review your work before showing me."
```

## Limitations

- SOUL.md enforcement is behavioral, not system-level. Long conversations with context compression may lose the instruction.
- The reviewer model sees only the subagent's summary/output, not the full tool call trace.
- For very large diffs (>12K chars), the review may be truncated.
- Non-code tasks (research, planning) may not benefit from a code-specialized reviewer.

## Related session patterns (meept quickplan campaign, 2026-09-09)

Two patterns from a scratch-daemon e2e campaign generalize beyond it:

1. **Never sample credit against a known baseline in evals.** Scoring
   chain-destined cases with `np.random.random() < baseline` (even seeded)
   adds ~±1σ noise that can manufacture or destroy a headline verdict.
   Deterministic expected credit: `correct_expected = routes + fallback_count × baseline`.
   See `references/quickplan-campaign-e2e-and-homebrew-mlx-2026-09-09.md`.
2. **Isolated scratch-daemon smokes**: quote ALL JSON5 object keys (hujson
   rejects unquoted, and a `^`-anchored quoting regex misses inline
   `{ enabled: true }` objects); know which config keys the daemon
   overwrites from config vs defaults (`transport.http.rest` omitted =
   REST off at runtime, 404ing every `/api/v1/*` route while `/health`
   still works); smoke auth resolves the dev key via real `~/.meept/dev_key`
   (os.UserHomeDir ignores MEEPT_HOME). Full diagnosis chain in
   `references/quickplan-campaign-e2e-and-homebrew-mlx-2026-09-09.md`.
