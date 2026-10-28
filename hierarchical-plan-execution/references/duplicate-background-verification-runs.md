# Duplicate background verification runs

When to use: before scheduling another cooldown retry or background verification run in a long campaign.
Lesson: long-cooldown retries stack silently - list and kill stale background runs first, and keep run numbering explicit so every workdir maps to exactly one run.

Long-cooldown retries stack silently: a 90-min sleep launched before a
newer run with a different timeout var remains queued and fires AFTER
the newer one, confusing run numbering and burning a provider window on
a stale binary/config. Before scheduling another cooldown retry, list
background processes for prior e2e/sleep pipelines and kill stale ones;
tell the user explicitly WHICH run (script + env + workdir) is live -
they will lose track ("what are we running precisely?") across a long
campaign. Each `--keep` run leaves a scratch workdir; keep the numbering
explicit (script log file ↔ workdir mapping) or runs become
indistinguishable.
