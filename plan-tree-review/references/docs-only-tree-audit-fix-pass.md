# Auditing + fixing a DOCS-ONLY plan tree (no code exists — the docs ARE the deliverable)

Proven 2026-08-22 on `agent-orange` (policy–market platform plan tree, 30 md
files, zero source code). Full pass: 5 parallel audit subagents → orchestrator
fixes → 4 parallel fixer subagents → verification subagent.

## Why docs-only is different

- "Unwired code" means **cross-branch contract drift**: leaf A consumes a
  field/route/file that no leaf produces, or a late pivot (e.g. a vendor
  decision recorded in one deliverable) was never propagated back into the
  contracts, sibling leaves, or master's open questions.
- The highest-value check is the **producer/consumer matrix** across branch
  boundaries: every field, route, make target, CLI, parquet dataset, env var —
  produced somewhere AND consumed somewhere. Orphans on either side are majors.
- The authority file (source-truth.yaml or equivalent) gets audited against
  its own contract schema FIRST and fixed FIRST, because fixer dispatches
  reference it.

## Audit wave

1. One audit subagent per section (root+research / per-branch), all parallel,
   each with: read-master-first context, numbered MAJOR/MINOR output format,
   exact file+line + quote + concrete proposed fix required, and "do NOT edit".
   Concrete-proposed-fix matters: it makes fixer dispatch nearly mechanical.
2. Truncated subagent summaries are saved to
   `~/.hermes/cache/delegation/subagent-summary-*.txt` — read_file the omitted
   middle before acting; findings live there.
3. Expect overlap (two auditors flagging the same root cause from different
   sides). Dedupe by root cause when writing fixer instructions.

## Fix wave

- Fix the ROOT/master files directly yourself first (contracts, authority
  yaml, status tables) so branch fixers build on corrected ground truth.
  Machine-check what's checkable: e.g.
  `uv run --with pyyaml python -c "...assert all 8 C7 keys per source..."`.
- Then dispatch one fixer subagent per branch, all parallel, each with an
  explicit numbered fix list (M#/m# ids carried over from the audits),
  allowed-file scope, "search_files to locate, patch to edit", "no git",
  and "report applied changes with file:line".
- Cross-boundary fixes that span two branches: assign to ONE fixer with an
  explicit carve-out ("you may edit this one file in branch X for this single
  addition") rather than splitting it — split ownership causes conflicts.

## Recurring defect classes found (check these explicitly next time)

- Contract owner refs pointing at renamed/nonexistent files (`01-project-scaffold.md` vs `01-scaffold.md`).
- Status tables lagging disk reality (deliverables committed but rows still PENDING).
- Decisions recorded in one artifact but not propagated to master OQs/Architecture.
- Contract-required keys silently absent instead of explicit OPEN QUESTION placeholders.
- Test specs asserting the wrong exception type (tuple assignment = TypeError, not AttributeError).
- Arithmetic windows short by the buffer (±250td pull can't supply a 250td estimation window ending t−11).
- Exit-code vocabularies disagreeing between the stage tool and the pipeline driver.
- Endpoint counts drifting between master contract / branch contract / leaf prose ("seven" vs eight vs nine).
- Parallel leaves both told to edit the same shared file (client.py) — restructure to a new file or sequence them.
- Unclosed markdown code fences in contract blocks (a ```python block whose closing fence is missing swallows the next section into the code sample — breaks downstream parsers AND readers).
- Phantom command/API names in Integration Test Plans (e.g. a query against a table/function no leaf ever builds) — every CLI/module/table named in an integration step must trace to a contract owner.
- Contract fields referenced by consumers but absent from the producer's schema block (e.g. ticker-side CFR metadata used by candidate generation but missing from B3-1's tickers DDL).

## Patch-tool pitfalls during direct application

- **Escape-drift rejection**: if `patch` rejects with "escape-drift detected" (`\\"` present in your strings but not the file), it's a serialization artifact — do NOT hand-edit the file; just re-issue the identical edit with quotes unescaped. One retry resolves it.
- **Re-read the diff, not your intent**: a patch can succeed while introducing duplication when `new_string` repeats context lines that were also part of `old_string` (this session produced a doubled path `data/exports/data/exports/`). Always scan the returned unified diff for accidental doubling before moving to the next edit; fix immediately with a follow-up patch rather than deferring to verification.
- **Concurrent-writer regression trap in a shared repo**: between your audit and your fix wave, a sibling agent may fix the same docs. Re-grep each target region immediately before patching, and scan the returned unified diff for stale values YOU reintroduced (proven 2026-09-01, llm-resilience-forest: a patch restored a `loop.go:4226` anchor a sibling had already corrected to `:4298`). After every markdown patch, re-run the fence-parity scan — an inserting patch once split a ```go block so the next block lost its opening fence, and another mangled bullet indentation when `old_string` spanned reflowed lines. Repair immediately; don't defer to the verification wave.

## Verification wave

Dispatch a separate verification subagent over all touched files AFTER fixers
land: re-run the producer/consumer matrix checks plus spot-check each applied
fix landed as specified. Do not let a fixer verify itself.

- **Split large verifications — a single verifier WILL time out.** One
  verifier covering 9 sections of a 30-file tree died at 600s (48 API calls
  in). Split into two parallel verifiers with disjoint section lists and an
  explicit "be efficient: targeted grep, not full file reads" instruction;
  both completed in 3–7 min.
- **Expect one residual per fixer wave.** Fixers miss count-words in prose
  ("all five GET endpoints" in an Integration Test Plan while every pinned
  table says six). Budget for orchestrator-direct touch-ups after the
  verify report; grep the exact stale phrase before patching (the fixer may
  have reworded the surrounding line since the audit).

## Applying fixes directly (orchestrator-as-fixer variant, proven 2026-08-22)

When the fix list is small enough (≤ ~15 targeted edits), skip fixer subagents
and apply directly with `patch` per edit, carrying M#/m# ids into your report.
Notes:

- **Concurrent-writer warning is benign but act on it**: if a sibling subagent
  modified a file after your last read, `patch` warns and still applies against
  current content — fine for non-overlapping hunks, but re-read before any
  further writes to that file rather than trusting stale context.
- **Cross-boundary single-line additions** (e.g. adding a CLI spec line to a
  branch-03 leaf so branch 06 has something to consume) are safe to do
  yourself even outside your nominal scope, provided they're purely additive.
- Report per-file with M#/m# ids + approximate line anchors; don't paste full
  diffs back.

**Rate-limit-collapse variant (proven 2026-09-01, llm-resilience-forest —
5 of 6 auditors died on HTTP 429):** when the audit wave itself collapses,
the fix wave follows it in-session. ~40 direct edits across 17 files is
manageable; the discipline that keeps it clean:

- Sequence: shared/contract files first (SHARED-CONVENTIONS, forest root,
  tree masters), then leaves — leaf edits build on corrected ground truth.
- Re-grep the exact target text immediately before EVERY patch when any
  other writer (sibling session, background agent) touches the same tree;
  one patch in this run reintroduced a stale `loop.go:4226` a sibling had
  already corrected to `:4298`. Read every returned unified diff for
  self-introduced regressions (fence splits, bullet re-indentation,
  reflowed lines) and repair in a follow-up patch before moving on.
- Late-arriving "dead" auditors return real findings 5-15 min later —
  disposition each: re-verify against source (reject misreads with
  file:line evidence), skip ones your fixes already cover, apply the rest.
- End-of-pass sync when a sibling restructures leaves mid-review: verify
  your fixes survived any file renames, then update derived surfaces
  (forest-root leaf counts, dependency tables, cross-refs to old names).
- Verification wave still runs: in-session mechanical re-scans (fence
  parity, line-number corruption, template compliance) + one fresh
  read-only verifier subagent briefed with every applied fix and the
  expected end-state on both sides of each cross-reference.
