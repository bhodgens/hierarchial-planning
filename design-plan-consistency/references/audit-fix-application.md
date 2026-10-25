# Applying Numbered Audit-Findings Lists to Plan Trees (Worked Example)

Worked session (2026-08-22): user said "Apply audit fixes to
plans/policy-market/02-data-platform/ docs." An earlier audit had produced a
findings list keyed M1–M9 (major) and m1–m9 (minor). This reference records
the procedure and the concrete finding→fix mapping patterns.

## Procedure

1. **Grep the target tree for each finding's signature term** before reading
   files — one `search_files` call per signature group (`auth: dict`,
   `AttributeError`, `pl- or pa-Table`, wrong protocol names, etc.). This
   locates every file needing edits without reading all of them first.
2. **Read each affected file in full** (they're short — leaves are ~150–200
   lines), then apply all fixes for that file in one or two `patch` calls.
3. **Fix cross-document contracts in lockstep**: when a schema field is added
   or renamed (e.g. `rin_registry` gains `statutory_authority`), update BOTH
   the branch orchestrator's Contract section AND the leaf doc that implements
   it AND its review checklist. Fixing only the orchestrator does not
   propagate (see SKILL.md pitfall 7 under drift digests).
4. **Close with a verification grep**: re-run the same signature search over
   the whole tree; zero hits = done. Also grep for terms you *expected not to
   need changing* (e.g. `federal.` / `sources.congress`) to confirm which
   findings were already clean — record those as verified-no-change rather
   than silently skipping.

## Finding→fix patterns seen (reusable)

- **Wrong exception type in TDD snippets:** frozen tuple assignment raises
  `TypeError`, not `AttributeError`. When a plan leaf's failing-test example
  asserts the wrong exception type, the implementer will write a test that
  can never pass as written. Also check the snippet imports `pytest`.
- **Ambiguous return types:** `-> pl- or pa-Table` prose in a code block must
  become a concrete annotation (`pa.Table`). Delete any "match leaf N's
  stack" sentence — it creates a false ordering dependency between
  concurrent-group siblings.
- **Self-questioning spec text:** text like `"Presented to President" →
  ENACTED (mapping choice ... ? NO — map to OTHER)` is a draft artifact.
  Rewrite as a clean decision rule plus a returned confidence flag
  (`map_stage(code) -> tuple[str, bool]`, bool = low_confidence).
- **Config fields that mirror YAML strings:** source-truth auth strings don't
  parse into `dict` cleanly — model as `auth_style: str ('none'|
  'query_param'|'header')` + `auth_param: str | None`; rate limits arrive as
  strings or numbers, so `str | float | None` with a load-time parse +
  conservative default warning on unparseable values.
- **Underspecified IDs:** if a manifest/run_id format is referenced but never
  defined, pin it inline (`{source}:{UTC YYYYMMDDTHHMMSSZ}`, minted by the
  fetch harness; duplicates raise) — otherwise each implementer invents one.
- **Stub workers vs make-target invariants:** stubs raising
  `NotImplementedError` from `run()` break a "make update completes with zero
  errors" invariant unless the registry's `run_all` catches worker exceptions
  and records statuses `{skipped: n}` instead of propagating. State this in
  the leaf task AND the review checklist.
- **Fixture provenance honesty:** if Phase 0 probes failed (403 without key),
  fixtures are hand-crafted, NOT captured live. Say so in the leaf context and
  flag them for replacement after the first live smoke — otherwise the
  implementer waits for captures that don't exist.
- **Unverified routes stay OPEN QUESTIONS in-plan:** where source-truth marks
  a URL route unverified, the leaf should cite the specific yaml path
  (`sources.agenda.routes.xml`), instruct filing an OPEN QUESTION, and name
  the fallback route.
- **Partition-pruning claims:** DuckDB parquet pruning keys off sort/order
  columns (e.g. as_of), not arbitrary filters. Reword tests claiming "ticker
  filter proves partition pruning" to correctness checks, noting ticker
  filters are row filters.
- **Makefile target ownership gaps:** if orchestrator says `make update &&
  make curate` is the full loop but no leaf owns wiring `update:`, assign it
  explicitly (e.g. leaf 06 wires both `update:` → ingest `__main__` and
  `curate:`).

## Session stats

6 files patched (01-scaffold, 02-common-framework, 03-congress-worker,
04-regulatory-workers, 06-curate-duckdb, orchestrator), ~15 patch calls,
final verification grep = 0 hits on all changed signatures.
