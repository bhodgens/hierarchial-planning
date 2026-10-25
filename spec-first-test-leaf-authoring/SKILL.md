---
name: spec-first-test-leaf-authoring
description: "Dispatch spec-pack test leaves that gate impl leaves."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [orchestration, testing, delegation, spec-pack]
    related_skills: [hierarchical-plan-execution, subagent-driven-development]
---

# Spec-First Test Leaf Authoring

Use when a plan tree gates implementation leaves on separate-authorship test
leaves (T-xx) written from a spec pack BEFORE implementation lands. Tests cite
clause ids and never read impl code. Companion to
`hierarchical-plan-execution`, which owns general orchestration; this skill
owns the separate-authorship test track specifically.

## Ordering (binding)

1. Spec/contract docs first, reviewed and committed, THEN the test wave.
Dispatching spec-writers and test-writers in one wave makes tests cite clause
ids that may not survive review.
2. Test leaves depending on a not-yet-written spec doc (e.g. a later plan's
representation spec) stay BLOCKED until that doc lands. Do not substitute
prose guesses for the missing doc.

## Dispatch context template (per test-leaf writer)

Hard-list in every context:

- ALLOWED inputs: named spec/contract docs + master contracts + the gated impl
leaf's Expose/Gate section + ONE existing suite as format exemplar.
- FORBIDDEN: implementation source (e.g. `crates/*/src`) — the point of the
track — and every other leaf's output dirs; enumerate forbidden paths.
- NO git commands; the orchestrator commits after review.
- Runnability floor today: impl does not exist, so every impl-behavior test is
`xfail(strict=False)` with reason, but the suite MUST collect zero errors under
the repo runner — the report must quote a real `pytest -q` summary line.
- Citation rule: every test/corpus-case header cites clause ids; ambiguities
go into a CONTRACT-GAPS section of the leaf doc, assertions written to the
STRICTEST reading, never weakened.
- Invocation-seam honesty: when the gated leaf exposes a library fn but no
CLI, tests invoke a PROPOSED bin seam (subprocess, path absent) and record the
proposal in CONTRACT-GAPS G-1 so the impl leaf must land the bin.

## Differential corpus cases (byte-exact gates)

- Expected stdout/stderr/exit-code per case come from REAL reference-impl runs
at authoring time, checked in — never hand-written or remembered values.
- UNSPECIFIED outputs (memory addresses, salted hashes, unordered iteration):
REWRITE the script to sort/mask before printing. Never weaken the comparison.
- Split each suite: (a) fixture self-check — re-run the reference and
byte-compare against checked-in expectations — green TODAY, catching
expectation rot; (b) impl-side gate — xfail until the impl leaf lands. A
100%-xfail suite tests nothing yet; class (a) is what makes the corpus
trustworthy now.

## Orchestrator review of a spec wave

- Clause-id census before trusting writer reports: grep cited ids vs defined
ids. Definition syntax varies per writer — match heading form (`### C-01`) AND
bold list-item form (`- **C-01 (MUST)**`) or a compliant doc reads as "all ids
undefined". Flag only ids with no definition anywhere; reconcile cross-file
references and placeholder ids (`C-??`) the impl must not ship.
- Re-run at least one quoted reference-output block per doc against the live
reference binary — writers can transcribe stale output.
- Adjudicate unexpected files (stray notes, your committed docs showing as
modified) via `git show --stat`, not commit messages — a parallel session may
have absorbed or revised the wave.

## Seam-landing: flipping the xfail wave (orchestrator step)

When the gated seam finally lands (the proposed bin, the impl leaf), the
xfail wave must flip - and the flip has a polarity trap:

1. Flip = REMOVE the xfail marker so the test reports as a real pass.
   NEVER convert stale markers to `xfail(strict=True)` to "promote" them:
   strict-xfail on a PASSING test reports XPASS-strict as a FAILURE, so a
   suite whose tests all run green suddenly shows dozens of reds.
2. Measure the still-failing set with `pytest --runxfail` per suite; keep
   `strict=False` markers ONLY on the measured known-fail cases, with the
   reason naming the owning leaf/finding. Never guess the fail set from
   prose, and never weaken a failing assertion instead.
3. A fixture name can pass in one test function and fail in another
   (e.g. accept/reject arms vs position pins of the same input) - the
   known-fail list must be EXACT nodeid tails, not fixture-name
   substrings; coarse fragment matching over-kills greens into fake
   xfails and leaks reds.
4. If the flip is done via `pytest_collection_modifyitems` in a per-suite
   conftest, scope the hook by nodeid prefix
   (`item.nodeid.startswith("tests/<suite>/")`) - a directory conftest
   fires for the WHOLE collected session, and two sibling suite conftests
   otherwise clobber each other's known-fail sets.
5. Record a post-flip combined tally (passed / xfailed / xpassed / failed
   must be 0 xpassed 0 failed on the flipped subset) in the tracking doc,
   and lower any XPASS-ceiling baseline file in the same commit - a flip
   that grows the xpass count breaches the ceiling gate.

## Pitfalls

- Never issue two delegate_task calls in one turn targeting the SAME files;
parallel-call batching applies only to independent calls. If a duplicate wave
fires, stop it immediately (`action='stop'`) and verify interrupted writers
left ZERO files (`git status --short`) before trusting the surviving batch.
- Repo state can be hours stale when a parallel session already implemented
plan branches. Re-run `git log --oneline` before scoping any wave; diff
`git status` against dispatch file-lists before each commit.
- Terminal cwd persists across execute_code/terminal calls and sibling agents
can leave it inside a subdirectory; use `workdir` or absolute paths in shared
sessions.
- Reference-binary patch level vs pinned contract version (installed 3.14.7
  vs a pin of 3.14.0): writers record it as an open question and must not spec
  behavior off patch-level differences; the orchestrator keeps it as a review
  item.
- The test track itself carries harness bugs that only surface when the seam
  lands: a fixture that resolves the real bin may return it in a shape the
  test bodies cannot call (e.g. a bare Path handed back where every body
  calls `.run(args)`), so the whole suite fails AttributeError under
  --runxfail while reading as "impl failures" in its report. Triage
  --runxfail failures by exception TYPE before routing any as impl findings;
  a fixture-shape bug is fixed test-side, one small wrapper class, and
  belongs in the flip commit with the marker removals.
- Baseline numbers for a ceiling gate must never be recorded while sibling
  WIP hangs the impl binaries (affected tests degrade to timeout-xfail and
  the count reads 0 - an interference artifact). Use the last VALID
  complete run plus documented partition probes, and annotate the provenance
  in the baseline file itself.
