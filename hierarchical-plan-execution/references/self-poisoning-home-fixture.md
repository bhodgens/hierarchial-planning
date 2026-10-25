# Self-poisoning $HOME test fixtures (tier-resolved writers)

## The failure (meept skill_create_tool_test.go, 2026-09-06)

`TestSkillCreate_Execute_WritesViaLifecycleWriter` constructed
`lifecycle.NewWriter(t.TempDir(), nil)` and created a skill named
`learn-from-video`. The writer's DEFAULT tier resolver discovers
`$HOME`-derived tiers (`os.UserHomeDir()` → `~/.meept/skills` etc.) via
`sync.Once`. One run seeded the real `~/.meept/skills/learn-from-video/`
with test content; from then on `ResolveTierPath` FOUND that real-tier
entry (real user tier outranks the writer's temp root), every later test
run wrote the real file in the user's home and failed the temp-path
assertion. The test poisoned its own environment on first failure and
kept failing even on a clean checkout.

Diagnostic tells: assertion diff shows output path under `/Users/<you>/
.meept/skills/...` while `wantPath` is under `/var/folders/.../TempDir`;
file mtime == the test run's timestamp.

## The fix

Point `HOME` at the temp dir BEFORE the writer's first operation (the
resolver builds lazily; `sync.Once` freezes whatever HOME was at first
use):

```go
func newTestWriter(t *testing.T) (*lifecycle.Writer, string) {
    t.Helper()
    dir := t.TempDir()
    t.Setenv("HOME", dir) // tier discovery derives from os.UserHomeDir
    return lifecycle.NewWriter(dir, nil), dir
}
```

`t.Setenv` (Go 1.17+) also blocks parallel tests in the package — fine
for these suites, and it auto-restores.

## General rules

- Any fixture that constructs a component doing `$HOME`-derived
  discovery/resolution (meept skills writer/discovery, anything reading
  `~/.config`, `~/.claude`) must sandbox HOME, not just the paths it
  passes explicitly. Explicit temp paths do NOT sandbox implicit
  HOME-derived resolution.
- A fixture that WRITES through such a component is a one-way trap: first
  collision with a real name seeds the real tier, and the seed makes every
  later run fail (or worse, silently mutate user data). Check the user's
  real dirs when a test mysteriously fails with a home-directory path in
  the diff — the artifact is OUTSIDE the repo, so `git stash` /
  clean-checkout verification will still fail and prove nothing about the
  code.
- When classifying a failure: reproduce on a clean tree (stash the working
  diff) BEFORE blaming the in-flight leaf. This one predated the wave that
  surfaced it; the wave's only fault was running the test.
- Audit sibling test files for the same constructor pattern when you fix
  one (skill_patch_tool_test used synthetic names — safe by luck, not by
  construction; note it, fix only what is actually reachable).
