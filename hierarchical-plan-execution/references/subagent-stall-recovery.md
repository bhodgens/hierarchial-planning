# Ssubagent stall recovery
When to use: stalled wave subagents.
Lesson: small-subset re-dispatch and salvage.

# Subagent Stall Recovery & Small-Subset Dispatching

Source: meept unified-theming execution (2026-08-25). Two wave subagents —
a 17-file mechanical migration and a settings-panel widget-test leaf — went
silent after landing only 5–10% of scope: no completion report, no live
process, for 4+ hours while the orchestrator sleep-polled `git status`.

## Detect stalls with liveness probes, not blind sleep-polling

After each wait cycle, check PROGRESS SIGNALS, not just tree state:

- File mtimes of the leaf's target files:
  `stat --format "%y %n" <files>` — all files sharing ONE identical
  timestamp = a bulk revert/checkpoint landed, not incremental work.
- Expected output paths appearing (`ls` the new files the leaf promised).
- Marker greps: `grep -c <new-helper-name> <target-file>`.

Rule of thumb: two consecutive checks with zero movement = stalled. Declare
it, tell the user, and take over (or re-dispatch smaller) — don't keep
waiting silently.

## Split mechanical migrations into small disjoint leaves

Pattern that worked after the stall:

- Wave 0 (orchestrator, committed first): the shared bridge/helper +
  replacement map, so every leaf imports something stable.
- Wave 1: N parallel leaves, each owning EXACTLY 2–4 files (~50–100
  replacements), dispatch naming its file list verbatim + the map + which
  sibling owns what ("do not touch X — sibling agent owns it").
- Result: four agents completed in 6–22 min vs. the monolithic leaf
  stalling indefinitely.

Constraints per leaf: build+vet only its own package (siblings share Go
packages mid-edit), gofmt on its files, no git commands.

## Scripted sweeps beat re-dispatch for mechanical swaps

When a revert/stall destroys mechanical work (e.g. color-literal → role-call
migration), a deterministic python regex sweep over the committed map redoes
it in minutes:

```python
import re
MAP = {"#F97316": "primary", "#10B981": "success", ...}
for name in files:
    src = open(path).read()
    out = re.sub(r'lipgloss\.Color\("(#[0-9A-Fa-f]{6})"\)',
                 lambda m: f'paletteColor("{MAP[m.group(1)]}")'
                 if m.group(1) in MAP else m.group(0), src)
    open(path, "w").write(out)
```

More reliable than fresh subagents re-deriving context; keep exempt markers
(`// palette-exempt`) so one-off accents survive future sweeps.

## First widget tests surface latent production bugs

When a leaf adds the FIRST widget test over an existing complex form panel,
expect to fix real bugs it exposes, e.g.:

- int initialValue fed to a String? TextField → `type 'int' is not a subtype
  of type 'String?'` thrown on EVERY production build of the panel (fix:
  coerce at initialValue; keep the field's valueTransformer converting back).
- Two FormBuilder fields registering the same name → tolerated at register
  with a warning but asserts at dispose ("Failed to unregister a field").
- Unbounded-width InputDecorator inside a bare Row → wrap in SizedBox;
  ListTile under a colored Container without a Material ancestor → wrap in
  Material.

Budget a fix-loop iteration for these rather than treating test failures as
test-authoring errors.
