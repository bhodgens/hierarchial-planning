# Sstall recovery and scripted migrations
When to use: stalled subagents + mechanical migrations.
Lesson: recovery patterns from unified-theming.

# Stall Recovery + Mechanical Migration (meept unified-theming, 2026-08-25)

Two lessons from executing the unified-theming plan tree; both belong in the
orchestrator's default playbook.

## 1. Subagents stall silently — verify liveness from disk

Observed: two wave-2 leaves dispatched in parallel went quiet. The
orchestrator burned ~2 hours in `sleep`-poll loops waiting for completion
reports that never came. The subagents had died without reporting.

### Liveness detection that works

- File mtimes: if NO file the subagent owns has changed in >30-60 min, it is
  dead regardless of "running" status:
  ```bash
  stat --format "%y %n" <files-the-subagent-owns>
  # identical timestamps on several files = one bulk external git operation
  ```
- Process check: `ps aux | grep <agent-process>` (empty = dead).
- Partial artifacts: bridge file exists but the test file doesn't = mid-flight death.

### Decision rule (user-endorsed)

When a leaf stalls past ~30-45 min with no disk activity, take over
in-session: grep what landed, finish the remainder yourself. Do not keep
sleep-polling for a report that will never arrive.

### Sizing lesson (user-directed)

When dispatching, split leaves into several SMALL single-file-group subagents
(3-4 files each) rather than one 17-file leaf. Small ones returned in 5-20
minutes; the big ones stalled. Also note the user's standing instruction:
"give them the time they need" means wait, BUT verify liveness from disk at
each poll instead of blind sleeping — and when the user later asks "are they
actually working?", answer with mtime/process evidence.

## 2. Deterministic scripted sweeps beat subagent re-dispatch for mechanical migrations

The straggler migration (~350 `lipgloss.Color("#hex")` replacements across 16
Go files) was redone in-session with a ~40-line Python script after the
subagent wave was lost:

```python
MAP = {"#F97316": "primary", "#10B981": "success", ...}
EXEMPT = {"#8B5CF6", "#EC4899"}  # no role exists → leave + // palette-exempt
for name in files:
    src = open(path).read()
    out = re.sub(r'lipgloss\.Color\("(#[0-9A-Fa-f]{6})"\)', hex_sub, src)
    out = re.sub(r'lipgloss\.Color\((Color(?:Gray|Amber|Red|Green))\)', const_sub, out)
```

Minutes of runtime, zero drift, per-file counts printed for the report.
Rule of thumb: **if the work is expressible as a deterministic find/replace
map, script it; reserve subagents for work requiring judgment per site.**

## 3. Write the lint-substitute regression test FIRST

`TestNoStrayColorLiterals` walks the package for raw `lipgloss.Color("#…)`
outside exempt files (`palette.go`, `styles.go`, test files) and outside
lines marked `// palette-exempt`. Written before finishing the migration,
it doubles as the review tool:

1. Run it → it enumerates exactly which literals remain, with line numbers.
2. Migrate / annotate intentional ones (`// palette-exempt: max-contrast literal`).
3. Iterate until green — the migration is then provably complete.

A fuzzy "migrate the literals" task becomes a measurable loop. Ship the
guard test in the same commit as the migration (issue #24 Phase 4).
