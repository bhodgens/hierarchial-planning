# Ddocs feature state sync
When to use: docs/README lag shipped features.
Lesson: fold doc regeneration into leaf dispatch contexts.

# Docs/README Feature-State Sync (meept, 2026-08-25)

Task class: "review the project and update documentation to match which
features are implemented." The failure mode of this task is TRUSTING THE
DOCS — README/docs routinely lag or lead the code. Every claim gets a grep
or file-existence check before it survives an edit pass.

## Method: claim-by-claim verification

1. Read the README's claims list first (Feature Status table, "clients
   available", agent counts, project structure). Each row = one claim to
   verify.
2. Verify each with cheap greps:
   - "planned" integrations → `grep -rln <feature> internal/ | head` +
     check daemon wiring (`grep -rn <pkg> internal/daemon/components.go`).
     Telegram was documented "planned" but fully implemented + wired.
   - agent counts → count actual definition files AND their frontmatter
     roles:
     ```bash
     for d in config/agents/*/; do id=$(basename $d);
       role=$(grep -m1 "^role:" $d/AGENT.md | awk '{print $2}'); echo "$id:$role"; done \
       | awk -F: '{print $2}' | sort | uniq -c
     ```
     Counts drift as agents are added; never copy the number from the old
     doc. Recount roles so "22 executor-role + 6 reviewers = 28" actually
     adds up (dispatcher/conversational have their own role strings).
   - removed commands → run `<cmd> --help`; meept printed "meept bots was
     removed; see `meept agents --help`" — docs still showed 6 bots
     subcommands.
   - config format claims → read the loader (`internal/config/config.go`
     preferred json5, TOML legacy fallback; three docs said TOML-first).
   - new features absent from docs → `ls internal/` for packages with no
     doc mention (stt/, tts/, theme/ tokens, employee/), plus recent
     commits for features shipped since the last doc pass.
3. Fix each stale spot at every place it appears — counts especially live
   in 3–4 files (README comparison table + status table + section body,
   docs/index.md ×2, getting-started). Grep the whole docs tree for the
   old number/name after fixing one site.

## Recurring staleness classes found

| Stale claim type | Example found |
|---|---|
| Counts (agents, tiers, reviewers) | "8 specialists" vs actual 28 |
| Integration status ("planned") | Telegram marked planned, fully wired |
| Removed CLI still documented | `meept bots` subcommand block |
| Config format/format-first | TOML-first docs vs JSON5-preferred loader |
| New feature undocumented | unified theming, STT/TTS missing entirely |
| Project-structure tree missing dirs | no theme/, ui/, employee/, stt/ |

## Shared-tree discipline during doc passes

Other sessions often have uncommitted edits to OTHER docs files (security,
secrets, tools reference) plus ~50 internal files. Stage ONLY your own doc
files by explicit path (`git add README.md docs/... AGENTS.md`) — if the
index already holds another session's staged internal/* work, `git reset`
first then re-add only yours, and verify with
`git diff --cached --stat | grep -v <your-files>` being empty.
