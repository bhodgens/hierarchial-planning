# Adding a New Client to Tokscale — Onboarding Checklist

Class-level procedure: tokscale ingests token-usage records from 50+
AI-agent clients, each added the same way. The 2026-09-06 meept client
(feat/meept-ingest 75afca63, 8 files) is the reference implementation for a
SQLite-metrics client; use `sessions/hermes.rs` (SQLite) or
`sessions/kilo.rs` (SQLite) as the code template.

## The 8 touch points (let the compiler enumerate the exhaustive ones)

1. **Registry entry** — `crates/tokscale-core/src/clients.rs`, the
   `define_clients!` macro: next free `= N =>` index, id (lowercase),
   display, logo (None is fine; there is a committed-asset test only for
   hosted-logo URLs), `root:` (`PathRoot::Home` for `~/.x` layouts,
   `EnvVar` when the client supports relocation), `relative:` to the DB/dir,
   `pattern:`, `headless: false`, `parse_local: true`,
   `submit_default:` (true for agents the default report should include).
   Component-join comment in clients.rs explains why relative paths use `/`.
2. **Parser module** — `crates/tokscale-core/src/sessions/<client>.rs`:
   - open via `open_readonly_sqlite`, iterate via `sqlite_for_each_row_on`
     (both from `sessions::utils`; they handle WAL/readonly quirks);
   - project ONLY the needed columns; tolerate NULL via
     `row.get::<_, Option<i64>>(n)?.unwrap_or(0)`;
   - filter error/no-usage rows explicitly (behavior pinned, not incidental);
   - dedup key namespaced per client (`format!("<client>:{}", row_id)`) —
     never (timestamp, model): two calls in the same ms are distinct work;
   - provider resolution via `resolved_provider(provider_opt, model_id,
     "<client>")` — falls back to model-name inference, then the client id;
   - cost 0.0 when the source does not persist per-call cost — pricing is
     applied by the caller lane, do not invent estimates in the parser;
   - timestamps: parse the source's real format to epoch millis; fall back
     to 0 on garbage, never drop the row.
   - Unit tests: seed an in-memory `rusqlite` DB with the source's real
     schema; include the negative-schema test (missing columns → empty Vec,
     not error) for pre-migration producer DBs.
3. **Module registration** — `pub mod <client>;` in `sessions/mod.rs`
   (alphabetical).
4. **Scanner** — `crates/tokscale-core/src/scanner.rs`: add the client to
   the SQLite-DB skip list in the file-walk matcher (so the generic walker
   doesn't grab the DB), add `pub <client>_db: Option<PathBuf>` + Default,
   and an `if enabled.contains(&ClientId::X)` existence-probe block next to
   the kilo/zed blocks.
5. **Parse dispatch — two lanes** in `crates/tokscale-core/src/lib.rs`:
   the priced lane (next to hermes/goose; wrap with
   `apply_pricing_if_available(&mut msg, pricing)`) and the count lane (next
   to the hermes lane in the count function; `counts.set(ClientId::X, ...)`).
   Missing either lane = client parses but shows zero in one report mode.
6. **CLI filter** — `crates/tokscale-cli/src/main.rs` `ClientFilter`: enum
   variant + `as_filter_str` + `to_client_id` + `from_client_id` (the last
   is an exhaustive match — the compiler finds it).
7. **TUI** — `crates/tokscale-cli/src/tui/client_ui.rs` hotkey array (count-
   sized, compile error when short) + the display-name test array in
   `tui/data/mod.rs`. Hotkeys: lowercase mostly taken; check the comments in
   client_ui.rs for which globals are reserved (`s` = sources picker).
8. **Registry tests** — `clients.rs` tests: bump `test_client_id_count`,
   add a `test_<client>_registered_as_local_session_source` mirroring the
   omp test (path resolve, pattern, parse_local, submit_default).

## Gates

`cargo build` (exhaustive-match enumeration), `cargo test -p tokscale-core
--lib` + `-p tokscale-cli` (the display-name array test fails with
left=COUNT right=COUNT+1 if any array is short), `cargo clippy -p
tokscale-core -p tokscale-cli`, `cargo fmt --all --check`.

## Live verification

A real `<client>` DB on the dev machine is the e2e test: `sqlite3` the
source DB to confirm schema/rows, then run the CLI on the branch. If the
producer's deployed binary predates the schema the parser needs, the parser
correctly reports nothing — say so explicitly and hand the user the
producer-side rebuild/restart step; never restart the user's running
services unasked.

## Related

- `hierarchical-planning` skill → references/cross-repo-informational-
  contracts.md — when the client being onboarded is one you ALSO control the
  producer side of (own daemon/agent), pin the read surface as a contract in
  the producer's plan and ship the producer-side projection test first.
