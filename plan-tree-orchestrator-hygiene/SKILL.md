---
name: plan-tree-orchestrator-hygiene
description: "Use when reviewing leaf work in a plan-tree campaign."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [orchestration, plan-tree, delegation, verification, git-hygiene]
    related_skills: [hierarchical-plan-execution, hierarchical-planning, subagent-driven-development, plan-leaf-validation, systematic-debugging]
---

# Plan-Tree Orchestrator Hygiene

## Overview

Rules for the REVIEWING orchestrator (main model) in a plan-tree
campaign where leaf agents produce uncommitted work in a shared repo and
the orchestrator reviews, verifies, and commits. Every rule here comes
from a real failure or a real save in a long-running tree (a Python
runtime in Rust, 2026-10: plans 00-03, 50+ commits, dozens of dispatches).

Companion skills: `hierarchical-plan-execution` (dispatch loop and
mandate), `systematic-debugging` (root-cause discipline for anything a
probe turns up).

## Rule 1 — Never `git checkout --` against uncommitted agent work

Leaf agents are told not to commit; their finished work sits uncommitted
until your review. To undo YOUR OWN bad edit to their file, `git checkout
-- <file>` reverts the ENTIRE file to HEAD and erases the agent's work
with your edit. Real cost: a full file rebuild via emergency re-dispatch.

- To discard your own edit: reverse `patch` (your text as old_string,
  empty new_string) or `git stash push -- <file>`.
- Before ANY destructive git operation during review: `git status
  --short` first, always. If the path shows agent churn, checkout is
  forbidden.
- The recovery that works when it does happen: the agent's tests (which
  survive separately) pin the contract — re-dispatch a focused agent to
  rebuild the file against those tests. Cheap only because the tests
  survived; this is one more argument for tests-first trees.

## Rule 2 — Explicit-pathspec commits; never blanket `git add -A` in pipelines

Three sweep shapes from one tree:
- A background one-liner (`test && git add -A && git commit`) swept a
  regenerating `bench_report.json` timing-churn file into a leaf commit.
  It kept regenerating and re-committing until reverted and moved out of
  the tree.
- `git add -A` after a test run whose failure signal was swallowed by
  pipes committed unreviewed work.
- A generator/tool script inside a globbed corpus directory polluted the
  case count (34/35 vs 34/36 across two reports). Generator scripts live
  in a `tools/` subdirectory, never inside a globbed corpus dir.

Rules:
- Orchestrator commits use explicit pathspecs matched against the leaf's
  declared file list. `git add -A` is acceptable only at final review
  where the leaf file list is the whitelist and `git status --short` was
  checked immediately before.
- Any artifact that regenerates on every test run (bench reports, timing
  JSON, coverage HTML) is gitignored or written outside the tree.
- Before commit: `git status --short | grep '^[MARC]'` diffed against
  your intended paths (catches sibling staged-index sweeps too — see
  hierarchical-plan-execution's staged-index section).

## Rule 3 — Fresh-smoke probes: write NEW tests from spec reasoning

After a leaf reports green, run a handful of programs the agent never
wrote, derived from the SPEC's reasoning (edge orders, aliasing,
recursion, self-reference, cross-feature interaction), byte-compared
against the reference implementation. In one session this caught, across
three leaves, bugs every agent self-suite missed:

- Generators that never advanced past the first yield (resume path dead).
- An iterator/generator ID collision capping EVERY loop at 2 iterations.
- Self-recursion raising NameError (module-level fn bound to the wrong
  scope store).
- Escaping closures losing captured cells (cell storage tied to the
  maker's frame lifetime).
- A builtin method unreachable through a newly added attribute-protocol
  layer (routing regression from an earlier leaf).
- Live class objects garbage-collected (root-scoping gap).

Procedure:
1. Read the leaf's Expose/Gate sections.
2. Write 5-10 programs from spec reasoning, not from the implementation's
   docs.
3. Run against the shipped binary; byte-compare vs the reference
   implementation where one exists (for a Python runtime: `python3.14`).
4. Any DIFF becomes a fix-pass dispatch with the probe as its acceptance
   test, or a documented divergence.

Mid-run steering with reproduced failures works: concrete repros ranked
by criticality fixed generator resumption, an ID-collision loop cap, and
traceback line numbers in one campaign.

See `references/fresh-smoke-probe-patterns.md` for the probe families.

## Rule 4 — Duplicate async deliveries: verify, never re-act

Background dispatch completions can arrive twice (delivery + batch echo
after a context rebuild). Before acting on a duplicate:
1. `git status --short` — clean, or only known in-flight work.
2. The commit from your first action contains the deliverable
   (`git show --stat`).
3. The duplicate's summary adds nothing actionable — grep proves claimed
   files are already committed.

A real duplicate's only new information was a fuller shim/vendoring list;
grep showed every item already inside committed files. Re-acting would
have double-dispatched a leaf.

## Rule 5 — Salvage protocol when an agent dies mid-leaf

Provider/network deaths kill agents with hours of uncommitted work.
Protocol (proven: 90 minutes of GC-collector work salvaged after a
'cannot reach model provider' death):
1. Build the salvage FIRST. If it compiles, commit it as WIP immediately
   — before diagnosis. Nothing else protects it.
2. Probe with your own smoke tests; write the exact defect list (e.g.
   'live enum classes swept by the collector: NameError on module-level
   class').
3. Re-dispatch a CONTINUATION agent: the salvage is in the worktree, the
   defect list IS the acceptance test, the original brief covers the
   never-started parts. Never re-dispatch from scratch.
4. Keep any orchestrator-made interim patches and tell the continuation
   agent they exist and must be preserved.

Corollary: a truncated or wrong-language final report (model artifact
under attempt-limit pressure) still counts if its claimed fixes verify by
your own probes. Verify claims, not prose.

## Rule 6 — Spec-firewalled test authorship

Test agents given ONLY the spec pack + contract (never implementation
source, never git history), writing xfail-gated suites before the
implementation exists:
- Caught three hand-derivation errors in expected-output goldens by
  cross-checking the reference implementation's own introspection tool.
- Filed contract gaps as first-class deliverables instead of silently
  choosing semantics.
- Flipped from xfail to green to certify the implementation — the flip
  IS the certification.
The protocol costs one dispatch rule. The payoff: tests that can catch
'implementation and tests agree but both are wrong'. When a test agent
probes the reference implementation for pinned bytes, that is allowed —
the reference is not the implementation.

## Rule 7 — Vendoring a mature implementation is a stress test

Copying a mature project's pure-source files (license permitting) and
running them on your runtime surfaces bugs synthetic corpus never will:
metaclass `__new__` dict-instance semantics, `__prepare__` namespaces,
descriptor chains, an issubclass metaclass-query arity bug — all found by
vendored pathlib/enum/unittest, none by the synthetic corpus.
- The vendoring leaf's gate is 'vendored files run green'; every failure
  they surface is a root-level conformance bug fixed at the source.
- Decide vendored-vs-native resolution order IN WRITING before vendoring
  (native-registry-wins avoided shadowing in this tree).
- License groundwork first: license text in LICENSES/, a README covering
  redistribution, and a notices-generator extension for non-crate files.

## Rule 8 — Known-gap ledger

Every leaf defers something. Deferred items go into a running ledger in
the plan's PROGRESS file with the blocking leaf named ('V048 needs
02.03 classes'), not into commit messages alone. The ledger lets any
later session answer 'can we run target X yet?' by diffing X's dependency
list against it, and stops the same gap being rediscovered and re-triaged
by three consecutive leaves. When a target project is named as a goal,
write the dependency analysis (what X imports, what breaks, which leaf
unblocks it) into docs/ and commit it — it becomes the sequencing
backbone.

## Rule 9 — Root-cause a failure BEFORE accepting the agent's framing

A GC agent's 'done' state swept live class objects; the obvious framing
was 'MRO cycle false-positive' (an earlier bug's shape). The real root
cause was different (collector root-scoping missing module namespaces).
When a fix pass reports a root cause identical to a previous bug's, be
suspicious — verify the mechanism with your own probe before accepting
it, and keep the actually-fixed root cause in the ledger (it becomes a
standing rule: e.g. 'user `__new__` is implicitly static; every new
metaclass dispatch path must preserve this').

## Quick reference

| Situation | Action |
| --- | --- |
| Undoing your edit to agent's uncommitted file | Reverse patch or stash, never checkout -- |
| Committing leaf work | Explicit pathspecs from the leaf file list |
| Regenerating artifacts | gitignore or move out of tree |
| Leaf reports green | Write 5-10 fresh spec-derived probes, byte-compare vs reference |
| Same completion message twice | Clean worktree + commit contains it = done, don't re-act |
| Agent died mid-leaf | Build, WIP-commit salvage, defect list, continuation dispatch |
| Deferred item | Ledger entry in PROGRESS with blocking leaf named |
| Vendored file fails | Conformance bug; fix at root, gate = vendored files run green |

## References

- `references/fresh-smoke-probe-patterns.md` — probe families that found
  real bugs past green self-suites: generator resume, name-resolution
  chains, cross-feature interactions, alias/lifetime, byte-exactness
  spot checks; plus the probe procedure and corpus-promotion step.
