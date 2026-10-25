# Capability-gap → plan-tree pattern (meept)

Session-proven recipe (2026-09-05, skill-authoring-and-media-ingest tree):
turning an external-product capability comparison into a dispatchable
hierarchical plan tree. This is the class of task: "product X can do Y
that we can't — build the gap-closing plan."

## 1. The comparison must precede the plan, and the comparison must be
## two-sided and source-anchored

- External side: fetch the OFFICIAL doc set (not blog coverage) — for the
  Grok Bot comparison that was docs.x.ai/grok-bot/* (overview, bots,
  computer-and-apps, chat-and-collaboration, skills-routines,
  approvals-security, teams, mobile, faq, troubleshooting). Web-search
  results alone give marketing claims; the official docs give limits,
  failure modes, and honest caveats ("Teach a task is browser-only,
  10-minute cap, gradual rollout").
- Internal side: verify every internal claim at file:line BEFORE writing
  it into a comparison table. Read docs/workflows/<pkg>.md AND grep the
  implementation (e.g. "skills agent-facing write path" → grep
  internal/skills + internal/daemon/components.go initializeSkills).
  The user's standing rule: "user issues hedged claims but expects
  code-verified verdicts at file:line."
- Deliverable shape that worked: full report written to a repo file
  (GROKBOT-COMPARISON.md), chat reply = summary + ASCII contrast chart.
  Chart rows: capability | external | internal | edge (one of
  comparable/meept/grokbot). The "comparable" column is where plan
  material hides — gaps the user will ask to close next.

## 2. The capability-decomposition step

"Does X have Y?" decomposes into a CHAIN of primitive capabilities.
Worked example — Hermes' "paste a YouTube URL, get a skill" decomposed to:
1. transcript/media ingest (URL → text) — tool
2. generic command execution — tool (meept already had shell_execute)
3. skill read surface — meept already had skills.get/list RPC
4. skill AUTHORING surface (agent-facing write) — GAP
5. skill library + linked assets (SKILL_DIR convention) — half gap
Plus the model doing synthesis (meept beats Hermes there via capability
resolution).

Grade each chain node HAS / GAP / HALF against the codebase. The plan
tree's leaves = one per gap. Order by unblocking value, not by novelty:
the authoring surface (4) unblocks everything else; the ingest tool (1)
is the most demo-visible. State both orderings and let the user pick.

## 3. Contract-first recon before authoring the tree

Before writing the master, verify every seam the leaves will touch:
- The Tool interface (internal/tools/interface.go) and one canonical
  builtin to mirror (web_fetch.go: constructor, Set* nil guards, schema,
  Execute).
- The existing machinery the leaves must REUSE (lifecycle.Writer tier
  resolution + versioning + SHA dedup; discovery tiers; parser) — write
  "do NOT reimplement, constructor-inject" into master Notes. This kills
  the classic multi-agent drift of four leaves building four writers.
- Construction-order hazards: daemon inits tools BEFORE skills, so a
  tool taking a writer handle must tolerate nil-at-construction and the
  wiring leaf must resolve ordering with a wiring TEST, not an
  assumption. This went in master Interface Contracts + Open Questions.
- Security classification per tool (LOW observation vs HIGH
  self-modification → confirmation flow) decided AT PLAN TIME in the
  contract, not left to the implementing agent.

## 4. Tree shape that worked (5 leaves, one wiring leaf)

- Leaves 01-04: pure leaf-scoped, no shared files → concurrency group A,
  single parallel batch.
- Leaf 05 (wiring + agent grants + docs + shipped composition skill):
  depends on 01-04 COMMITTED, group B, alone. Single-writer discipline
  for shared files (components.go, schema.go) stated in the master.
- The composition skill (learn-from-video) is CONTENT, not code — it
  ships inside the wiring leaf and encodes the user's review preference
  ("show draft, confirm before writing") as workflow steps.
- Every leaf carries: exact constructor signatures in the contract,
  fake-runner/injectable-dependency test pattern for anything
  subprocess-based, and a "what this does NOT do" line in the Review
  Checklist (no RPC handler, no evolver changes, no coder grants).
- Non-goals section in master Notes prevents the most likely scope
  creep (here: evolver, wiki, RPC surface).

## 5. The framing question that reshapes the plan: "are we using their
## stack?"

When the gap analysis touches a compatibility layer (meept's hermes_compat
tier/tool-mapper), the user WILL ask "we're not using hermes directly,
right? we shouldn't be." Answer precisely and audit the boundary:
- Ingesting a FILE FORMAT is not depending on the product (meept reads
  Hermes SKILL.md frontmatter; runs nothing of theirs).
- Any tool-name translation shim (hermes_compat.go HermesToolMapper) is
  in-repo code with tests — cite file:line, call it a maintained
  compatibility layer, and offer the decoupling levers (stop auto-
  discovering ~/.hermes/skills; drop the tool mapper) as SEPARATE product
  decisions, out of the current plan's scope.
- Withdraw lossy-framing observations: "strips Hermes fields" implied a
  loss when the behavior was correct (meept-native writes emit
  meept-native frontmatter). Say "the behavior is correct; my framing
  was wrong" — the user respects verdict reversals stated plainly.

## 6. Execution-order notes

- Author tree → run the compliance scanner from the PARENT dir
  (docs/plans --strict-leaves, absolute script path, cd in the same
  command) → CJK scrub → anchor spot-checks (grep the named anchor
  lines still exist at HEAD) → commit tree separately from unrelated
  scanner fixes.
- The comparison report and the plan tree commit together naturally
  (same session, same motivation), but scanner fixes for OTHER trees are
  a separate concern — separate commit, explicit path lists (see
  multi-agent-git-coordination for the shared-tree rules).
