# Plan-tree authoring checklist (Pitfalls 21-29, 38-39, 42 quick run)


When to use: post-authoring review of any plan tree.
Lesson: quick run of pitfalls 21-29, 38-39, 42 as checkboxes alongside the compliance scan.
Run this checklist after authoring any tree, alongside
`scripts/check_template_compliance.py` (structural scan, Pitfall 20).
Companion files: `references/checklist-additions-session-tail.md`
(structural/dispatch/GDScript items merged from the deleted SKILL.md
session-diary tail, 2026-10-26).

- [ ] Frozen contracts (structs, constant tables, threshold enums) quote the spec source at the definition site (`// SPEC (file:line, [STATUS]): <text>`) so paraphrase-drift is diffable (Pitfall 21)
- [ ] For forests or plans with paraphrased contracts: contract-verification digest subagents dispatched post-authoring (Review Protocol §"Contract Verification Digests")
- [ ] On projects with an active changelog: changelog-review digest dispatched after contract-verification (Review Protocol §"Tier-3 Verification") to catch sibling-session design drift (Pitfall 22)
- [ ] For sweeping concept-replacement changes (perspective, rename, feature cut): parallel digest subagents categorize hits before batch application; verify post-application that intentionally-kept references survive (Pitfall 23)
- [ ] For pre-implemented trees (sibling-agent or prior-session work): dispatch a post-implementation review subagent with the full plan checklist before marking COMPLETE (Pitfall 24)
- [ ] For multi-forest projects: grep for cross-forest references (`grep -rn "plans-<sibling>" plans-<this>/`); replace with GDD spec citations — plan forests must be self-contained (Pitfall 38)
- [ ] For plans with a sibling implementation (e.g., Go sidecar + Godot client): dispatch a cross-implementation gap auditor alongside the completeness auditor to catch unconsumed data/capabilities (Pitfall 39)
- [ ] For subagent timeouts on large leaves: check disk for partial work before re-dispatching; complete missing pieces (tests, entry points, gofmt) directly if source compiles (Pitfall 25)
- [ ] For Go leaves with float-scored ranking/sorting: run determinism tests with `-count=10`; grep for `!=` in sort comparators (use epsilon) and `range` over maps in accumulation loops (sort keys first) (Pitfall 26)
- [ ] Plans that include wiring tasks (register route, call from handler, enqueue from ingest): the leaf's self-verification checklist must include "grep for production callers of each exported function" — prevents the "isolated islands" pattern where components compile but are never called (see `hierarchical-plan-execution` Pitfall 42)
- [ ] Before `git commit` on any Go leaf: remove ALL unused functions/variables/imports (run `go vet` + check pre-commit hooks for U1000 linter); do NOT rely on `//nolint` directives (pre-commit hooks may not honor them) (Pitfall 27)
- [ ] When reviewing subagent-produced Go code: grep for undefined references (`mathSqrt`, `pkgRand`, placeholder helper names); compile-check BEFORE writing tests to catch these early (Pitfall 28)
- [ ] When removing unused Go functions for U1000 lint: use `patch` with verbatim old_string, NEVER regex/sed/execute_code on multi-line function bodies (Pitfall 29)
- [ ] Binary/cross-language contracts: every consuming brief inlines the EXACT field order, widths, endianness, and struct definition; the leaf that WRITES the format round-trips its own output through an already-landed foreign reader before reporting done (see `references/parallel-sibling-leaf-contracts.md`)
