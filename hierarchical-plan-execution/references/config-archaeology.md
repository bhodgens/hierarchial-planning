# Config archaeology: when today's quality problem was shipped months ago

Companion to forensic-run-attribution.md. That reference covers attributing
individual e2e failures; this one covers the case where the ROOT CAUSE of a
long-running quality problem is a CONFIG REGRESSION from a months-old,
unrelated-looking commit — found via `git log -S` after normal debugging
exhausted.

## Real case (meept classifier chain, 2026-09-06)

15-run e2e campaign failing on "provider instability." Forensics showed the
ambiguity gate was being judged by a 1.2B model that scored fully-concrete
instructions ("create a file named hello.txt... tell me the full path") at
0.6-0.8 ambiguity. User asked: "why is this using those models? classifier is
supposed to be the specialized LFM2.5 model."

`git log --format='%h %ad %s' --date=short -S '<model-name>' -- config/models.json5`
revealed a July 7 commit ("MLX runtime fixes and switch to llama.cpp GGUF") that:
1. Demoted the classifier primary from the 8B model to the 1.2B
2. DELETED a custom SFT-fine-tuned classifier model (`lfm-combined-sft`) from
   the chain entirely — the model the user remembered selecting
3. Carried a "Best overall (69.1% accuracy)" comment onto the new primary line
   where it was misleading (it had described the 1.2B as a FALLBACK)

The commit's stated purpose (runtime migration: MLX SIGKILL workaround) had
nothing to do with classifier quality — the model changes rode along, and the
quality regression surfaced two months later as "flaky e2e."

## The recipe

```bash
# 1. When did this value/model enter or leave the config?
git log --format='%h %ad %s' --date=short -S '<model-or-value>' -- path/to/config

# 2. What did the config look like BEFORE the suspicious commit?
git show <commit>~1:path/to/config | sed -n '/"alias": {/,/}/p'

# 3. What was REMOVED (deletions are the memory-hole)?
git show <commit> -- path/to/config | grep '^-' | head -30

# 4. Do referenced paths still exist on disk?
ls /Volumes/LLMs/<model-dir>  # deleted-from-disk models silently break fallback order
```

## Signals that the current config is not what anyone chose

- Config comments that describe a DIFFERENT line than the one they sit on
  (copied during an edit; e.g. a fallback's accuracy comment now on the primary)
- An alias whose primary is the SMALLEST model in the chain ("fast" primacy
  usually means a migration artifact, not a choice)
- Test/eval aliases (`classifier-test-a`) that reference models no longer in
  the main alias — an abandoned evaluation
- Model registry entries pointing at paths that no longer exist
- The user remembering a model name that exists nowhere in current config —
  trust the memory and search history; they chose it for a reason

## Handling the finding

1. Present the timeline table (date → commit → what changed) to the user.
   They will usually recognize the decision or confirm it was never theirs.
2. Separate the runtime migration (may have been necessary) from the model
   quality changes (rode along unreviewed). Reverting the latter is NOT
   reverting the former.
3. Check whether deleted custom models still exist on disk/backup before
   planning restoration.
4. The stale comment is a standing lie — fix it in the same commit as the
   config restoration.
