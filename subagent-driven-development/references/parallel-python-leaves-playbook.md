# Orchestrating parallel implementation leaves (Python/uv plan-tree execution)

When to use: executing parallel implementation leaves of a Python/uv plan tree.
Lesson: plan for partial work on timeout, keep fault-tolerant module self-registration, never run repo-wide formatters, and run the cross-worker contract-drift checklist.

Lessons from executing a 6-leaf branch of a Python monorepo with background
delegation (agent-orange branch 02, 2026-08-22). Applies to any
plan-tree/orchestrator doc that says "dispatch leaf agents in concurrency
groups."

## 1. Subagents WILL time out mid-run  -  plan for partial work

Leaf agents implementing full TDD specs routinely hit the 600s delegation cap
after writing RED-phase tests but before GREEN-phase code, or mid-edit.

Protocol when a leaf times out:
1. Do NOT blind re-dispatch the full spec  -  check `git status --short`, run
   the test suite, inspect what exists.
2. If work is coherent-but-unfinished, dispatch a CONTINUATION prompt:
   "previous agent completed X (tests exist, do not modify them); your job is
   Y." This preserves the RED phase and roughly halves the remaining work.
3. If work is small and mechanical (lint fixes, one broken function), finish
   it directly instead of re-delegating  -  a second 600s timeout costs more
   than doing it yourself.
4. After finishing anything a timed-out agent started, grep for its half-done
   hacks: unbound module flags, "lenient first load" workarounds around
   self-contradictory tests, unclosed code fences. Timeouts corrupt mid-edit.

## 2. Self-contradictory test specs from interrupted agents

A timed-out agent may paper over a spec contradiction with a runtime hack
(e.g., a module-global `_FIRST_LOAD_DONE` flag making one test see lenient
loading and another strict raising). Resolution order:
- Fix the TESTS to match the contract, not the code to match both tests.
- Split fixtures: valid fixture + deliberately-broken fixture beats one
  fixture that must simultaneously pass and raise.
- Delete the workaround; document the contract in the loader docstring.

## 3. Parallel leaf groups need explicit file ownership

When dispatching concurrent workers into ONE working tree:
- Assign each leaf an exclusive file list in the dispatch context ("you own
  ingest/market.py; do NOT create/modify *congress*").
- Shared merge points (`__init__.py`, `__main__.py`, registries) get one
  owner: have each worker register itself from ITS OWN module
  (`_register_default()` / `regulatory.py`); orchestrator wires imports after
  merge.
- Registration must be fault-tolerant: wrap default registration in
  try/except ConfigError so missing .env secrets don't break imports in bare
  test environments; CLI runs fail loudly later.
- Never let two agents edit the same manifest/validation module concurrently;
  assign that change to one leaf and say so explicitly.

## 4. Forbid repo-wide formatters in subagent prompts

`ruff format .` run by a subagent reformatted python code fences INSIDE
plans/*.md docs. Phrase it: "only `uv run ruff format src tests`, never
repo-wide"  -  then verify with `git diff plans/ docs/` before commit and
`git checkout -- plans/ docs/` if touched.

## 5. Cross-worker contract drift to check at review

- Response normalization: workers must accept both parsed JSON and
  response-like objects (.json() callable) from injectable transports/stubs.
- rate_limit strings: parse leading numeric token ("10 req/s documented" ->
  10.0) before falling back to conservative default + warning.
- pagination style: source-truth stores prose ("cursor via next_page_url"),
  match with substring `"cursor" in style.lower()`, not equality.
- Selector entries in YAML config (e.g. `market: "<active vendor>"`) are not
  dicts  -  loaders must skip non-dict sources, not raise.
- Manifest statuses keys are a frozen contract ({new, unchanged, error});
  extensions like "skipped" need coordinated updates to write_manifest
  validation AND its tests  -  assign to exactly one leaf.
- event_id formats are frozen contracts: suffix schemes (-eff, -N index) must
  still match the master regex; check curated rows round-trip through
  PolicyEvent.validate().
