# Multi-Source Plan Authoring (Direction Docs + Vendor Selection + Codebase)


When to use: inputs are a direction doc, vendor research, and the codebase.
Lesson: treat direction docs as non-literal; verify vendors; anchor everything in the codebase.
Writing a plan tree when the inputs are: (1) a direction/design document the user
does NOT want followed literally (often authored by another model), (2) external
vendor/tool research, (3) the actual codebase. Reference execution: the
2026-08 strategist payment-shim tree (`docs/plans/2026-08-25-payment-processor-shim/`).

## When to use this pattern

- User supplies a plan/architecture doc "for direction only"
- The task bundles a which-vendor decision ("Hyperswitch, Primer, or Speedly —
  help us decide") with implementation planning
- Success criteria exist in prose, but integration points must be discovered in
  the repo

## Handling a rejected-but-directional source document

- Mine it for: objective, risk rationale (e.g. "processor reserve traps operating
  cash"), success criteria, failure-scenario list, business/contract actions.
- Mirror the success criteria and failure scenarios into the VERIFICATION leaf's
  drill suite and runbook — they are the acceptance bar.
- Drop its implementation specifics (named processors, table designs, module
  splits) — re-derive those from the actual codebase.
- Keep the risk rationale in master.md Goal prose so leaf agents and reviewers
  know WHY the invariants exist.

## Vendor selection inside a plan tree

1. EXISTENCE-CHECK every named vendor before any comparison. Names recalled from
   memory are often wrong: "Speedly" (payment router) does not exist — searches
   return Spreedly (hosted vault SaaS) and speedy.io (wallet PSP), both different
   product classes. Search the bare NAME first.
2. Surface a misremembered name as an Open Question + closest-match analysis in
   the decision matrix; EXCLUDE the phantom from scoring; never silently
   substitute a near-named product (Spreedly ≠ Speedly ≠ speedy.io).
3. Decision matrix lives in master.md as its own section. Criteria rows include
   license (check against the user's licensing rule), deployment-model fit with
   existing infra, connector coverage, pricing transparency, ops cost, risk.
   State the recommendation AND a fallback order explicitly.
4. Make the decision reversible-by-construction: name which leaves/branches get
   re-executed if the vendor changes (typically: adapter branch + deployment
   leaf). This converts the decision from architecture lock-in into a swappable
   branch.
5. Gate the vendor-specific branch behind a Phase 0 spike leaf (see
   `research-gated-plan-trees.md`). One agent, produces a GO/NO-GO report
   artifact with observed data — deployability, one real sandbox transaction,
   webhook signature scheme, resource footprint — not production code. NO-GO
   flips to the fallback vendor BEFORE adapter code exists. Require an
   "appendix: exact observed API field names" in the gate report; it becomes
   ground truth for the adapter leaves and replaces doc-memory guessing.

## Codebase contract extraction (before writing leaves)

- Map the FULL method surface of the thing being abstracted (e.g. every method
  on the client struct) AND every call site with file:line refs. Pin both in the
  branch orchestrator's Notes.
- Exclude `//nolint:unused` methods from the new interface — dead surface.
- Record existing patterns to reuse verbatim: settings-read SQL shape, webhook
  JobID conventions, queue names, seed-script `INSERT..ON CONFLICT` shape. Leaves
  must extend existing patterns, never invent parallel ones.
- Where a test seam is needed (e.g. hardcoded upstream base URL), make the leaf
  CHECK for an existing env/override hook first; any added seam is a reviewable
  deviation, and reviewers diff the original file to confirm seam-only changes.

## Invariants as named rules

State invariants in master.md Architecture as numbered rules (e.g. "fail-closed:
unknown resolver value ⇒ current behavior", "processor-of-record: refunds and
webhooks dispatch on the stored column, never on the toggle"). Then repeat them
in Review Checklists — an invariant not in a checklist does not survive leaf
dispatch.

## Compliance-scan loop

After authoring the whole tree, run
`scripts/check_template_compliance.py <plans-root> --strict-leaves`, then fix
what it flags. The common gap is orchestrators missing `## Open Questions`
("recommended but missing") — add the section with the REAL open decisions
(phantom vendor identity, unpinned cross-leaf signaling mechanism, unverified
API field shapes), not boilerplate.

## Research-paper-backed trees: citations as frozen content (2026-08-29)

When a plan tree implements a research paper (real case: meept
wikiskill-skill-state, arXiv:2608.27454 + 2608.26263), the user expects the
provenance to survive into the repo:

- master.md opens with a "Research References" section: full title, arXiv id,
  authors/org, and the specific mechanisms adopted (with section numbers, e.g.
  "§5.1 ablation: never give the worker the wiki").
- Every leaf's Meta names its paper reference and states the commit message
  MUST cite the id; master.md's Dispatch Protocol pins ONE commit message per
  leaf with the citation embedded, so orchestrators copy verbatim instead of
  re-deriving.
- A docs leaf (last in the tree) adds a README "Research references" note and
  feature docs — the user asked for this explicitly ("noted in the readme.md
  as well as in the commit messages").
- Pin ablation findings as REVIEW GATES, not prose: e.g. "if any diff makes
  the wiki reachable from an inference prompt builder, REJECT the leaf" turned
  a paper finding into an enforceable checklist item.

## Related reference

For the sibling pattern — turning a PRODUCT capability comparison
(external product can do Y, our repo can't) into a gap-closing plan tree —
see `references/capability-gap-plan-pattern.md`. It covers the two-sided
source-anchored comparison, capability-chain decomposition
(HAS/GAP/HALF grading per node), and the compatibility-layer boundary
question ("we're not using their agent directly, right?").
