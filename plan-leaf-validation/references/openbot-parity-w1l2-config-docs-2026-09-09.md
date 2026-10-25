# openbot-parity wave1 leaf 1.2 — generated config docs + freshness tests (2026-09-09)

Implementing-leaf session, humanplusone repo (shared tree; sibling leaf 1.1
work present and untracked: README badge + `.github/` — not ours, own-diff
verified by scoping `git status`/`git diff` to own files). No commit made.

## Landed
- `scripts/gen-config-docs.py` — importlib file-direct settings import (no
  playwright), markdown tables to `docs/configuration.md`, GENERATED header,
  deterministic output (verified: two runs byte-identical).
- `docs/configuration.md` — generated: 34 control-plane + 28 worker fields.
- `control-plane/tests/test_docs_freshness.py` — 8 tests: byte-compare
  freshness, GENERATED-header presence, README route parity (one-directional,
  prefix-tolerant), env-key test vs both settings classes (leaf's prefix
  allowlist + justified exact-name allowlist for embedded-shell locals),
  2 allowlist meta-tests, `.env.example` key check.
- Makefile `docs` target only (`ci` untouched per leaf).

## Deviations from the leaf text (documented, not silent)
1. "description from field description/docstring" → the codebase documents
   settings fields with `#` comments, not `Field(description=...)`.
   Extracted comments via `tokenize` (ast drops them entirely) + AST
   assignment spans, with three attribution fixes (adjacent-field leak when
   no blank line; `noqa` filter; whole-statement-span scan for comments
   inside parenthesized multi-line defaults).
2. Machine-anchored absolute-path defaults (DATABASE_PATH,
   GENERATED_ENV_PATH, PLANS_JSON_PATH) normalized to repo-relative form —
   determinism prerequisite for the byte-compare test.
3. FastAPI 0.141.1 `_IncludedRouter` layout: full paths =
   `include_context.prefix` + original route path; walker handles both
   layouts + Mounts and asserts a non-empty discovered set.

## RED/GREEN evidence (leaf acceptance)
- RED: deleted the `STRIPE_SECRET_KEY` row from the generated doc →
  `test_generated_doc_matches_generator_output` FAILED naming the missing
  row (1 failed, 7 passed).
- GREEN: restored (regenerated) → 8 passed. Full suite: 221 passed,
  92.58% coverage (85% gate met) — no regressions.
- ruff check + format clean on new files; codespell clean; `make docs`
  runs clean; Makefile diff verified purely additive (fuzzy patch had
  nudged an adjacent section header by one character — caught by re-diff).

## Notes for future passes
- KEY= grep over prose-heavy docs is unsatisfiable without the exact-name
  allowlist (embedded shell locals: CTID, IP_OCTET, RED/GREEN/YELLOW,
  ZPOOL_DEVICES; product flags: ENABLE_KB_EXEC) — pattern captured in
  repo-quality-gates-setup `references/docs-freshness-gate.md`.
- macOS `sed -i '/pattern/d'` extra-argument failure → use the patch tool
  for surgical single-line deletions in RED demonstrations.
