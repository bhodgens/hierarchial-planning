# Self-Poisoning Test Fixtures (tier/env-derived resolution in unit tests)

Signal class: a test that PASSED for weeks starts failing with
"path does not mention the temp dir" — and rerunning it writes files
into the USER'S REAL home-directory tree.

Mechanism: any fixture that constructs a component whose default
resolution walks `$HOME`-derived paths (os.UserHomeDir) — meept's
`lifecycle.NewWriter` default tier resolver discovers
`~/.meept/skills`, `~/.config/meept/skills`, `~/.claude/skills`,
`~/.hermes/skills` — is only sandboxed if HOME itself is sandboxed.
Temp-diring the component's ROOT is not enough: resolution can find a
name in a REAL tier (which outranks the root fallback) and write there.

## The two-phase poisoning (why it appears "random")

1. SEED: one run resolves a name to the real tier (e.g. the writer's
   fallback tier IS the real user tier, or a partially-resolved path
   escapes) and writes a fixture-named skill/file into `~/...`. The
   test still passes at this stage (it only asserts the write
   happened, not where).
2. LOCK-IN: every later run's resolution FINDS the seeded real-tier
   entry, prefers it (higher priority than the fallback root), writes
   there, and the temp-path assertion fails — permanently, on every
   machine where the seed exists. Re-running never heals it; the test
   now depends on global mutable state it created.

Real case (2026-09-06): `TestSkillCreate_Execute_WritesViaLifecycleWriter`
seeded `~/.meept/skills/learn-from-video/` (a fixture name that later
COLLIDED with a real shipped skill name — fixture names that are
plausible product names maximize the blast radius), then failed with
"output should mention created path /var/folders/.../SKILL.md".

## Fix

`t.Setenv("HOME", dir)` in the fixture helper BEFORE the component's
first operation (the writer builds its discovery lazily via sync.Once
precisely to allow this). Check the component's docs/source for the
sanctioned isolation hook — meept's writer_test.go documented the
HOME-adjustment pattern in a comment before any test used it.

```go
func newTestWriter(t *testing.T) (*lifecycle.Writer, string) {
    t.Helper()
    dir := t.TempDir()
    t.Setenv("HOME", dir) // sandbox $HOME-derived tier discovery
    return lifecycle.NewWriter(dir, nil), dir
}
```

## Detection checklist

- Grep the component for `UserHomeDir|os.Getenv("HOME")|filepath.Join(home`
  — any hit means HOME-sandboxing is REQUIRED in its tests.
- Test names/fixtures using plausible product names ("learn-from-video",
  "code-review") — these collide with real artifacts; synthetic names
  ("s", "locked-skill") are lower-risk but still not exempt.
- A failure saying the output path "should mention <tmpdir>" while the
  actual path is under the real home = the smoking gun.
- Baselining: `git stash` the working tree and re-run — if the failure
  reproduces at HEAD, it is PRE-EXISTING, not the current wave's
  regression. Attribute and fix forward as its own commit.
- After fixing, also clean the seeded real-tree debris (hand the rm to
  the user — orchestrator rm is consent-gated).

## Confirmed recurring (2026-09-06, second same-day instance)

Found AGAIN in the tool-result-budget wave-A review: a DIFFERENT
fixture (`newTestWriter` in skill_create_tool_test.go) with the same
shape — root temp-dired, HOME not sandboxed — had seeded
`~/.meept/skills/learn-from-video/` and failed at HEAD. Two same-day
instances of one fixture-shape means: when you find one, grep sibling
fixtures constructing the SAME component and patch every instance in
the same pass (`NewWriter(` in *_test.go was the grep that found both
safe and unsafe variants — the safe ones used synthetic names, which
is luck, not safety). The stash-baseline step is what correctly
attributed the failure as pre-existing (reproduced at HEAD) instead
of blaming the in-flight wave — do that step before touching the
fixture. Standing user decision from this session: the real-tree
debris (`~/.meept/skills/learn-from-video/`) was left in place for
the user to remove; orchestrator rm stayed denied on every attempt.
