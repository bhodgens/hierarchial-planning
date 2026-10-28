# Ttokscale client addition checklist
When to use: adding a client to an exhaustive registry.
Lesson: 15-touchpoint surface: 8 compiler-visible, 7 string-keyed the compiler cannot see.

# Adding a client to tokscale: the 15-touchpoint checklist

Session 2026-09-06 added `Meept` (54th client). The registry is an
exhaustive-macro design: adding a variant breaks the build in a handful of
obvious places and compiles cleanly while MISSING half the integration —
several touchpoints are string-keyed or data-driven and the compiler cannot
see them. This is the full surface. It generalizes to any Rust codebase with
an exhaustive-enum client/source registry (same shape as prior
tokscale-client sessions).

## Non-exhaustive (compiler helps)

1. `crates/tokscale-core/src/clients.rs` — registry entry in the
   `define_clients!` macro (id, display, logo URL, `PathRoot`, relative
   path, pattern, flags) + bump `test_client_id_count` + registry test
   (path resolution, parse_local/submit_default flags).
2. `crates/tokscale-core/src/sessions/<client>.rs` — the parser. Mirror the
   closest sibling (hermes.rs for SQLite stores). Prove it with an
   in-memory-DB test that seeds the exact contract schema, not a fixture
   VLM'd from imagination — include a legacy-schema probe test (parser
   returns empty, not an error, when the store predates the columns).
3. `crates/tokscale-core/src/sessions/mod.rs` — `pub mod`.
4. `crates/tokscale-core/src/scanner.rs` — `ScanResult` field (if
   DB-dispatched), Default impl, skip-list in the scan loop (SQLite DBs do
   NOT go through the file-walk path), existence-probe block next to
   Kilo/Hermes.
5. `crates/tokscale-core/src/lib.rs` — parse dispatch in BOTH lanes: the
   priced/unified lane (with `apply_pricing_if_available`) and the
   counted lane (with `unified_to_parsed` + `counts.set`).
5b. `crates/tokscale-core/src/message_cache.rs` — `parser_version(client)`
    arm. This match has NO `_ => 1` fallback ON PURPOSE: adding a client to
    `define_clients!` fails compilation here until it gets an explicit
    independent arm (or joins a shared family). Give the new client v1 with
    the standard "versioned from the start" comment so future parser changes
    have a local counter to bump. CAVEAT: this registry is newer than some
    long-lived branches — if your branch predates it, the missing arm only
    surfaces at the first `cargo build` AFTER rebasing onto moved main.
    Build after EVERY rebase, not just at branch time (2026-09-08: the
    meept PR rebased onto a Droid fix and only then hit E0004 here).
6. `crates/tokscale-cli/src/main.rs` — `ClientFilter` enum variant +
   `as_filter_str` + `to_client_id` + `from_client_id` (all four or
   `--client` silently can't select it).
7. `crates/tokscale-cli/src/tui/client_ui.rs` — CLIENT_UI hotkey entry.
   Hotkeys are nearly exhausted: check every prior entry's comment for
   which letters are taken and why before picking.
8. `crates/tokscale-cli/src/tui/data/mod.rs` — display-names test array.

## String/data-driven (compiler is BLIND — checklist before declaring done)

9. `packages/frontend/src/lib/types.ts` — add to `SUPPORTED_CLIENT_TYPES`.
   Missing this makes the frontend build fail with a misleading error
   pointing at whatever Record<ClientType, …> the next person touches.
10. `packages/frontend/src/lib/constants.ts` — FOUR Record<ClientType,…>
    maps: SOURCE_DISPLAY_NAMES, SOURCE_LOGOS, SOURCE_COLORS, plus the
    display-name map (search `Record<ClientType` to get all of them —
    new ones get added over time).
11. `packages/frontend/public/assets/logos/<client>.png` + repo
    `.github/assets/client-<client>.png` — the same file in BOTH places.
    The registry test `test_hosted_logo_urls_have_a_committed_asset`
    greps the frontend dir; if it doesn't exist there, CI fails even
    though the Rust side is fine.
12. `README.md` — five separate sites: client table (top, with logo img),
    platform/path table (bottom, 4-column format), the multi-platform
    prose list, the `--client` possible-values line, the source-filtering
    prose list. Grep for the previous client's name to find every list.
    PLUS the localized READMEs — CONTRIBUTING step 7 requires mirroring
    `README.ko.md`, `README.ja.md`, `README.zh-cn.md` (each has its own
    client table, multi-platform list, source-filtering list, and
    `--client` values line, in-language). The localization pass is the
    most-forgotten touchpoint: grep all four READMEs for the previous
    client's name, not just the English one. Translate the one-line data
    description; keep paths/ids/code spans verbatim.
13. Logo sourcing: scale the source art to 400×400 (repo convention is
    200–400 px square). Portrait art needs a center-crop first (`sips -c
    <h> <w> --cropOffset <y> <x>`, then `-z 400 400`); VISION-CHECK the
    result (ears cut off = bad crop). Hero/wrapped pages read from
    `.github/assets/`; the frontend reads from its own public dir.

## Verification order that pays

Run `cargo build` FIRST after the core crates (catches all non-exhaustive
matches in one pass), then `cargo test -p tokscale-core --lib clients::`,
then the full CLI suite (the display-names test is the one that catches a
missing entry in 8), then frontend `bun run build` (catches 9–10), then
`./target/debug/tokscale clients` against the live machine (catches 4's
probe wiring) and one real report command against real data. Before
declaring PR-ready, read the repo's CONTRIBUTING client-integration
checklist and run its named gates verbatim — for tokscale that includes
the frontend registry contract test
(`bun run --cwd packages/frontend test -- __tests__/lib/clientRegistry.test.ts`,
which reads the Rust `define_clients!` list and validates every id
against the submit schema, logo assets, and colors) and
`bun run --cwd packages/frontend typecheck`, plus
`cargo clippy --locked --workspace --all-features -- -D warnings` (CI
gates on ZERO warnings, not just clean build). Contributing guides
encode steps the compiler and this checklist can drift from — the
localized-README requirement lived only there.

## Contract pinning across repos

When the client's data lives in ANOTHER repo's store (here: meept's
metrics.db), pin the read contract with a test in the SOURCE repo too
(meept: `internal/metrics/tokscale_ingest_test.go` pins the exact
projection column-for-column). Comment in both files pointing at each
other. When one side changes, the other's test fails loudly instead of
silently mis-parsing.

## Contract with the source repo (meept): zero-value semantics

`0` reasoning/cache tokens means "provider did not report," NOT "zero
occurred" — parsers treat 0 as absent, never synthesize sentinels.
Error rows carry no usage and must be excluded by `error = 0` explicitly
(even if they're currently always zero) so a schema change that starts
recording partial usage on failures can't inflate totals. Dedup keys off
the store's monotonic row id, never (timestamp, model) — two calls in one
millisecond are distinct work. Parser reads the DB read-only (WAL mode:
concurrent readers are safe while the daemon writes).

## Re-validation is re-run, not assumed (2026-09-08)

The user explicitly asked to "re-validate that it works against meept's
format" after the work looked done. The live DB had grown 355 → 3,550 rows
(two days of daemon work, new session-id shapes: `step-task-*`,
`plan-task-*`, `conv-*`). The right move is reconciliation against SQL
ground truth, not re-running the same report and eyeballing it:

1. Compute expected values directly in SQLite: row count with the same
   filter the parser applies (`error=0`), per-column SUMs.
2. Run the product's reports and diff the numbers.
3. Check the *composition* too, not just totals: distinct provider/model
   pairs, agent-id distribution, and NEW session-id shapes (a task-scoped
   id format the fixture never covered proves the session pass-through
   works on real data).
4. Re-run the parser unit tests after any rebase — code that passed on
   branch-day can drift against a moved main.

## PR flow when origin is not yours (fork + rebase + gate re-run)

`origin` pointed at `junhoyeo/tokscale` (push denied, 403). Sequence that
worked: `gh repo fork <upstream> --clone=false` → `git remote add fork
<fork-url>` → `git rebase origin/main` (main had moved) → build+test AFTER
the rebase (this is what surfaced the message_cache gap in 5b) → `git push
-u fork <branch>` → `gh pr create --repo <upstream> --head <user>:<branch>
--body-file /tmp/pr-body.md`. Write the PR body to a file per AGENTS.md
(no heredoc backtick-escaping). Check `gh api repos/<upstream>/<repo>
--jq .permissions` first to know whether a fork is needed instead of
discovering it via a denied push.
