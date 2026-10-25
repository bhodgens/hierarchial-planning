# Research-Gated Plan Trees

Pattern for hierarchical plans where PROJECT FEASIBILITY is unproven:
novel statistical hypothesis, many unverified external APIs, unknown
literature, or data availability that decides the architecture. Extends
writing-plans "Step 2b: Verify External API/Service Assumptions" from
one plan to a whole project.

## Spike-gated vendor adoption (lightweight variant)

When the plan adopts a third-party SERVICE (payment orchestrator, auth
provider, any self-hostable vendor) rather than testing a hypothesis, the
full research-gate machinery is overkill but a bare trust-the-docs plan is
reckless. Proven shape (2026-08-25, payment-processor shim, strategist-usa):

- **Phase 0 = one spike leaf, not a research branch.** Stand the vendor up
  in Docker OUTSIDE the repo (`/tmp/<vendor>-spike`), exercise the 3–4
  assumptions the whole architecture rests on (deployability, critical
  connector works, webhook shape, resource footprint), and write a
  GO/NO-GO report whose appendix captures REAL observed JSON/event-type
  strings — that appendix becomes the field-name ground truth for the
  adapter leaves, replacing remembered API shapes.
- **The gate is placement, not ceremony.** Master's dispatch protocol:
  adapter/deployment branches are BLOCKED on the gate leaf; a NO-GO flips
  to the recorded fallback vendor (decision table lives in master.md with
  fallback order) BEFORE adapter code exists. Keep gate + foundation
  (interface, resolver, migration) in the SAME concurrency group —
  vendor-neutral foundation is safe to build while the spike runs.
- **Fallbacks are named in the plan.** The decision matrix in master.md
  lists 2–3 candidate vendors with a recommendation, fallback order, and
  the note that the internal shim makes the vendor swap local to exactly
  two plan documents (adapter branch + deployment leaf). A mid-execution
  "actually, use vendor B instead" from the user then costs nothing —
  this was proven live when the user briefly requested a Primer pivot and
  reverted within the same session.
- **Verify the vendor EXISTED before planning around it.** One of three
  candidate names in the user's request ("Speedly") matched no real
  product; searches returned adjacent-but-different vendors. Surface the
  mismatch as an Open Question with the closest real alternatives ranked,
  never silently substitute.
- **Two-level API verification.** Orchestrator verifies top-level claims
  via web_search (API exists, auth model, license) at PLAN time; leaf
  agents verify field-level shapes against live docs AND the spike
  appendix at IMPLEMENTATION time, recording deltas instead of
  force-fitting the contract sketch. The contract sketch is explicitly
  labeled as such ("field names verified during implementation, not from
  memory").

## When to use (any one)

- The core question is a hypothesis ("does X predict Y?") — the build
  only makes sense if prior art plus a pilot support it.
- 5+ external data sources whose endpoints/auth/history/limits are
  assumed, not verified.
- Key decisions (vendor, model provider) must be evidence-based
  comparisons, not defaults.

Do NOT use for ordinary features on a known stack — a Phase 0 branch
there is process overhead.

## Tree shape

```
master.md
  01-phase0-research/        # branch, dispatched FIRST
    01-literature-scan.md    # verified citations only; effect sizes,
                             # horizons, methods; OPEN QUESTION markers
    02-source-audit.md       # live-verified source-truth.yaml; every
                             # field carries an evidence URL
    03-pilot-study.md        # hand-built end-to-end proof on 1-2 sample
                             # domains; reference math, not product code
  02..0N build branches      # each consumes Phase 0 outputs
  0N+1 automation leaf       # kill criteria as an EXECUTABLE command
```

## Rules that make the gate real

1. HARD USER GATE after branch 01. Master's Dispatch Protocol says
   STOP: present deliverables, wait for approval before any build wave.
   No agent provisions paid keys or picks vendors at the gate — the
   user decides (record the decision in source-truth.yaml / .env).
2. source-truth.yaml is the authority contract. Build leaves read it
   at implementation time. Leaf seed assumptions LOSE to it;
   conflicts become OPEN QUESTIONs. Every field carries evidence: the
   URL that proves it.
3. Estimates labeled. Every volume/cost/latency number is "estimate"
   until the audit's sample_basis backs it.
4. Greppable unknowns. Leaves mark unverifiable facts with the literal
   string `OPEN QUESTION:` so the gate report can count them.
5. Kill criteria are commands. Later branches ship a check (e.g.
   `make kcheck`) with meaningful exit codes: 0 = signals survive,
   non-zero = kill criterion tripped. The daily automation report
   leads with the kill wording. Waves after the stats branch are
   CANCELLED when the kill trips — never tune parameters until
   significance appears.
6. No backfill during TDD. Testing uses fixtures and bounded pulls;
   multi-year backfills are explicit post-review background jobs the
   orchestrator runs.
7. Research leaves swap TDD for verification steps (asset-pipeline
   pattern): citations resolve, files parse, and the reviewing
   orchestrator recomputes ONE number by hand (math oracle at research
   scale).

## Phase 0 leaf specifics

- Literature scan: verify the seed list FIRST (every seed resolves to
  a real URL/DOI or is marked OPEN QUESTION — never silently
  substitute a similar paper), then extend to 20-30 items across
  distinct search axes. Extract effect sizes WITH horizons and sample
  sizes; end with an "Appendix: Implementable Specs" the stats branch
  implements against.
- Source audit: at least one live HTTP status code per source recorded
  in evidence; auth header names exact (the `Authorization-Key` trap);
  delisted-coverage and license text checked for market vendors; no
  API key written to any file the leaf produces.
- Pilot: fixed sample domains for reproducibility; every event date
  verified against a primary-source URL in a sidecar file; one CAR
  recomputed by hand by the reviewer.

## Artifact sweep (before first commit)

One session authoring 20+ documents leaks artifacts the compliance
scanner cannot see — the scanner checks required-section substrings
only, so a corrupted optional heading passes:

- stray markup in headings (`## Goal}`, `## Goal**`)
- bracketed drafting notes (`[Stray brace — Goal follows]`)
- typo'd code paths (`agent_ororge`)

Sweep procedure:

1. After the compliance scan, grep the tree for artifact signatures
   (`Goal}`, `Goal**`, `[Stray`, `[NOTE:`, obvious path typos) and
   skim every `## Goal` / `## Context` heading.
2. Fix via patch or one batched execute_code pass.
3. RE-GREP residuals. Do NOT trust the fix list — exact strings drift
   between what was written and what is remembered (2026-08-18: 3 of
   17 fixes missed on the first pass; the residual grep caught all
   three).
4. Re-run the compliance scan; commit only after both are clean.

## First-pass compliance trick

Read `references/compliance-headings.md` AND the scanner source
(`scripts/check_template_compliance.py`) BEFORE writing any headings,
and write the exact heading strings on the first pass. Worked example
(2026-08-18): 26 documents passed `--strict-leaves` on the first scan.

## Worked example

Policy-market correlation platform (2026-08-18, agent-orange repo):
26-doc tree, 5 branches + 1 automation leaf. Phase 0 = literature scan
(9 seed papers extended to 20-30), source audit (8 federal sources + 4
market vendors), pilot (FAA reauthorization + pharma pricing chains,
market-model CAR windows). Build waves: data platform (immutable raw
JSON → curated parquet → DuckDB), entity/exposure (Postgres +
deterministic candidates + LLM classifier behind a human review gate),
stats engine (event study with oracle tests, BH-FDR, walk-forward
holdout, Wilson calibration), dashboard (FastAPI + Streamlit). Kill:
no exposure-mapped signal survives q ≤ 0.10 on the holdout → stop
buildout, write up findings.
