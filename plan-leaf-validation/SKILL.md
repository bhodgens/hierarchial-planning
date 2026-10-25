---
name: plan-leaf-validation
description: Validate plan-tree leaves for completion claims before closing them out
---

# Plan Leaf Validation

Before closing a plan-tree leaf, the orchestrator verifies the leaf's claims
against the committed state, not the report. Minimum checks: (1) `git show
--stat <leaf commit>` contains the leaf's full file list — a registration
line or wiring hunk left unstaged means the surface is dead at HEAD; (2) a
new user-facing surface (CLI verb, RPC method, HTTP route) gets a
binary-level smoke invocation built from the committed state, because unit
tests call constructors and never exercise registration; (3) completion
claims that reference generated artifacts (graphs, docs) are re-run in a
clean worktree at HEAD and diffed — never regenerated from the dirty shared
tree. A leaf report's file list and evidence are claims; the committed tree
is the proof. Step-by-step recipes for each check:
references/closeout-verification-recipes.md (binary-registration smoke,
handwritten-reference grep audit, staged-hook loop, leaf-scope-creep
handling, Go escape corruption in fuzzy patches).

Additional checks by leaf shape:

- GATE/GUARD leaves (error paths, rejection policies, byte-exact error
  texts): re-probe the CONTRACT firsthand with 5-10 fresh shapes
  covering BOTH accept and reject arms, diffed against the live
  reference — never accept the leaf's own probe battery as proof. A
  guard commit is approved only when the orchestrator's own minimal
  scripts reproduce the pinned bytes through the built binary.
- HARNESS/FUZZ leaves ("the suite can detect divergence"): the claim
  needs a machine proof of RED — run the strict/negative lane once and
  verify it genuinely fails with a shrunk repro. A fuzz or differential
  harness reporting zero findings on a fresh hand-written engine is
  more likely blind (compare arms inverted, skip-everything seam,
  whitelist swallowing) than lucky; audit the comparator before
  crediting green. Conversely, findings a fuzz leaf reports are only
  trustworthy if each carries a minimal repro the orchestrator re-runs
  once against the reference and the impl side by side.
- BASELINE-RECORDING leaves (pass counts, ceilings, tallies quoted into
  committed files): verify the run that produced them was uncontended
  and on a WORKING stack. Count live suite processes first — N
  competing full differential runs (orchestrator + leaves + handoffs)
  contend on binaries/temp dirs and none finish; kill all, run one
  clean solo. A count measured while sibling WIP hangs the impl is
  fiction; the honest committed artifact is last-valid-tally + written
  provenance of why today's measurement is unusable.