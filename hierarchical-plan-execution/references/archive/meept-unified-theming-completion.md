# Mmeept unified theming completion
When to use: unified theming completion record.
Lesson: pitfalls-49+ source session.

# Meept Unified Theming (2026-08-25) — Completion Record

Tree: `docs/plans/2026-08-24-unified-theming/` in the meept repo.
Executed by orchestrator session with 2 first-wave leaves, 7 small-subset
leaves for L4, and 3 in-session fixes. All committed to main.

## What shipped

- W0: `theme/tokens.json5` (3 variants x 18 frozen roles) + Go `theme`
  package (embed + hujson parse + validate). Commit 5e3e9d9d.
- L2: TUI runtime palette (`SetPalette`/`Current`, `rendering.ui_theme`
  config key, NewApp wiring, viz bridge). Commit 660227b4.
- L1: Flutter AppPalette behind CyberpunkColors static-getter forwarding
  (1,076 call-sites untouched), Riverpod providers. Commit 2d6124d1.
- L3: settings dropdown midnight/solarized, live swap via applyTheme,
  ui_theme persistence. Commit 78db4f98 (+2 latent panel bug fixes).
- L4: ~350 straggler literals migrated; palette bridges per sub-package;
  TestNoStrayColorLiterals guard test. Landed inside foreign commit
  86af507c (swept — see H1 hazard).
- L5: docs/configuration/theming.md + Dart<->Go tokens parity test +
  AGENTS.md pointer. Commit c1fd91d5.

## Key design decisions worth reusing

1. **No code generation** — hand-written palette layer reading an embedded
   JSON5 file beat build_runner/chroma generators on risk and complexity.
2. **Static-forwarding shim** (`CyberpunkColors.X => _active.X`) let 1,076
   const-context call-sites keep compiling with only ~27 mechanical
   `const` removals. Do NOT convert widgets to watch providers when a shim
   achieves runtime selection.
3. **Sub-package cycle rule**: internal/tui/models and components cannot
   import parent tui (parent imports them). Each got its own tiny bridge
   over the shared `theme` package with hardcoded cyberpunk fallbacks so
   parse failure never panics at render time.
4. **Parity tests as drift guards**: tokens_data.dart is a const copy of
   tokens.json5; a Dart test diffs them byte-for-byte. The one allowed
   duplication, held by CI.
5. **Lint-substitute scan test**: TestNoStrayColorLiterals walks the package
   regex-scanning for raw hex literals outside exempt files/lines marked
   `// palette-exempt`. Cheaper than a custom analyzer, same guarantee.

## Latent bugs surfaced by new tests (fixed same-commit)

- daemon_port int fed to String? FormBuilder TextField → cast threw on
  every settings-panel build. Fix: stringify at initialValue; the field's
  valueTransformer converts back on save.
- FormBuilderSwitch double-registered 'stt_enabled' with its outer
  FormBuilderField → dispose-time assert in form_builder 9.x. Switch now
  owns a private key seeded from the field value.
- Settings panel lacked a Material ancestor → dropdown ListTile ink
  assertions. Wrapped panel root in Material.

## Verification pattern

go build ./... && go test ./internal/tui/... ./theme/ ; cd ui/flutter_ui &&
flutter analyze (0 errors) && flutter test (322 pass).

Note: gofmt -l flags pre-existing unformatted files across internal/tui and
cmd/meept on HEAD — not introduced by this tree; check only your touched
files.
